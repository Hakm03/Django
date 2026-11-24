# ventas/tasks.py
"""Tareas asíncronas de la app ventas — W16/W17.

Descubiertas por app.autodiscover_tasks() (core/celery.py).

Estado:
    W16: infraestructura Celery (tareas como placeholders).
    W17: correo real vía django-anymail + SendGrid, con idempotencia
         (Pedido.correo_enviado) y alerta de stock al administrador.
    W18: tareas programadas con Celery Beat.
"""
import logging

from decimal import Decimal, InvalidOperation

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


def _items_para_correo(snapshot) -> list:
    """Convierte items_snapshot en filas con subtotal para el recibo HTML.

    Tolera datos incompletos: un item con precio inválido se muestra con
    subtotal 0.00 en vez de romper el envío del recibo.
    """
    filas = []
    for i in snapshot or []:
        try:
            precio = Decimal(str(i.get('precio', '0')))
            cantidad = int(i.get('cantidad', 1))
        except (InvalidOperation, ValueError, TypeError):
            precio, cantidad = Decimal('0'), 1
        filas.append({
            'nombre':   i.get('nombre', '?'),
            'cantidad': cantidad,
            'precio':   f'{precio:.2f}',
            'subtotal': f'{precio * cantidad:.2f}',
        })
    return filas


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name='ventas.enviar_confirmacion_pedido',
)
def enviar_confirmacion_pedido(self, pedido_id: int) -> dict:
    """Envía el recibo del pedido al cliente (una sola vez por pedido).

    Recibe el ID (no el objeto) porque los argumentos deben ser JSON.
    Idempotente: si Pedido.correo_enviado ya es True no vuelve a enviar.
    Si el proveedor falla, se reintenta (hasta max_retries).
    """
    from ventas.models import Pedido   # import local: evita circularidad

    try:
        pedido = Pedido.objects.select_related('cliente').get(pk=pedido_id)
    except Pedido.DoesNotExist:
        logger.error('[Tarea enviar_confirmacion] Pedido %s no existe.',
                     pedido_id)
        return {'estado': 'error', 'pedido_id': pedido_id}

    if pedido.correo_enviado:
        logger.info('[Tarea enviar_confirmacion] Pedido %s ya tenía recibo '
                    'enviado; se omite.', pedido.numero_pedido)
        return {'estado': 'omitido', 'pedido_id': pedido_id}

    destino = pedido.cliente.correo
    if not destino:
        logger.warning('[Tarea enviar_confirmacion] Pedido %s: el cliente '
                       'no tiene correo.', pedido.numero_pedido)
        return {'estado': 'sin_correo', 'pedido_id': pedido_id}

    lineas = [
        f"  - {i.get('nombre', '?')} x{i.get('cantidad', 1)}"
        f" — ${i.get('precio', '0.00')} c/u"
        for i in (pedido.items_snapshot or [])
    ]
    detalle = ("Detalle:\n" + "\n".join(lineas) + "\n\n") if lineas else ""
    cuerpo = (
        f"Hola {pedido.cliente.nombre},\n\n"
        f"¡Gracias por tu compra! Recibimos el pago de tu pedido "
        f"{pedido.numero_pedido}.\n\n"
        f"{detalle}"
        f"Total pagado: ${pedido.total_pagado}\n\n"
        "Este es un recibo automático. Conserva este correo como "
        "comprobante.\n"
    )

    html = render_to_string('ventas/email/recibo.html', {
        'pedido': pedido,
        'items':  _items_para_correo(pedido.items_snapshot),
    })

    try:
        send_mail(
            subject=f'Recibo de tu pedido {pedido.numero_pedido}',
            message=cuerpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[destino],
            html_message=html,
            fail_silently=False,
        )
    except Exception as exc:
        logger.exception('[Tarea enviar_confirmacion] Falló el envío del '
                         'pedido %s.', pedido.numero_pedido)
        raise self.retry(exc=exc)

    # Marca atómica: si otra tarea ya lo marcó, no pasa nada.
    Pedido.objects.filter(pk=pedido.pk, correo_enviado=False).update(
        correo_enviado=True)
    logger.info('[Tarea enviar_confirmacion] Recibo del pedido %s enviado. '
                'Timestamp: %s', pedido.numero_pedido,
                timezone.now().isoformat())

    return {
        'estado':    'ok',
        'pedido_id': pedido_id,
        'numero':    pedido.numero_pedido,
        'cliente':   destino,
    }


def _agrupar_por_proveedor(productos: list) -> list:
    """Agrupa productos con stock bajo por proveedor (sin proveedor al final)."""
    grupos = {}
    for p in productos:
        clave = (p.get('proveedor_nombre') or '', p.get('proveedor_correo') or '')
        grupos.setdefault(clave, []).append(
            {'nombre': p['nombre'], 'stock': p['stock']})
    ordenados = sorted(grupos.items(), key=lambda kv: (kv[0][0] == '', kv[0][0]))
    return [
        {'proveedor': nombre or 'Sin proveedor asignado',
         'correo': correo, 'productos': items}
        for (nombre, correo), items in ordenados
    ]


@shared_task(
    bind=True,
    max_retries=1,
    name='ventas.verificar_stock_bajo',
)
def verificar_stock_bajo(self, umbral: int = 5) -> dict:
    """Detecta productos activos con stock < umbral y avisa al admin.

    El correo se envía solo si hay productos bajos y ADMIN_EMAIL existe.
    """
    from django.db.models import F

    from productos.models import Producto   # import local

    productos_bajos = list(
        Producto.objects
        .filter(activo=True, stock__lt=umbral)
        .values('pk', 'nombre', 'stock',
                proveedor_nombre=F('proveedor__nombre'),
                proveedor_correo=F('proveedor__correo'))
        .order_by('stock')
    )

    if productos_bajos:
        logger.warning(
            '[Tarea verificar_stock] %s producto(s) con stock < %s: %s',
            len(productos_bajos), umbral,
            [p['nombre'] for p in productos_bajos],
        )
    else:
        logger.info('[Tarea verificar_stock] Todos con stock >= %s. OK.',
                    umbral)

    correo_enviado = False
    if productos_bajos and settings.ADMIN_EMAIL:
        grupos = _agrupar_por_proveedor(productos_bajos)
        bloques = []
        for g in grupos:
            cab = g['proveedor'] + (f" <{g['correo']}>" if g['correo'] else '')
            bloques.append(cab + ':\n' + '\n'.join(
                f"  - {i['nombre']}: {i['stock']} unidad(es)"
                for i in g['productos']))
        texto = (f'Productos activos con stock menor a {umbral}, '
                 f'agrupados por proveedor:\n\n'
                 + '\n\n'.join(bloques) + '\n')
        html = render_to_string('ventas/email/alerta_stock.html', {
            'grupos': grupos, 'umbral': umbral,
            'total': len(productos_bajos)})
        try:
            send_mail(
                subject=(f'Alerta de stock bajo '
                         f'({len(productos_bajos)} producto(s))'),
                message=texto,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                html_message=html,
                fail_silently=False,
            )
            correo_enviado = True
        except Exception as exc:
            logger.exception('[Tarea verificar_stock] Falló el envío de '
                             'la alerta.')
            raise self.retry(exc=exc)

    return {
        'umbral':          umbral,
        'productos_bajos': productos_bajos,
        'total':           len(productos_bajos),
        'correo_enviado':  correo_enviado,
    }


# ── W18: reporte diario (Celery Beat) ─────────────────────────────────────

def _top_productos_del_dia(dia, pedidos) -> list:
    """Top 5 productos por ingreso del día, sumando las dos fuentes de venta.

    Ventas internas (DetalleVenta, agregadas en SQL) y compras de la tienda
    en línea (Pedido.items_snapshot): el checkout crea Pedido, nunca Venta,
    así que sin la segunda fuente las compras web no aparecerían.
    """
    from django.db.models import DecimalField, ExpressionWrapper, F, Sum

    from ventas.models import DetalleVenta

    acumulado = {}   # nombre → {'unidades': int, 'ingreso': Decimal}

    internas = (
        DetalleVenta.objects
        .filter(venta__fecha__date=dia)
        .values(nombre=F('producto__nombre'))
        .annotate(
            unidades=Sum('cantidad'),
            ingreso=Sum(ExpressionWrapper(
                F('cantidad') * F('precio_unitario'),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )),
        )
    )
    for fila in internas:
        dato = acumulado.setdefault(
            fila['nombre'], {'unidades': 0, 'ingreso': Decimal('0.00')})
        dato['unidades'] += fila['unidades'] or 0
        dato['ingreso'] += fila['ingreso'] or Decimal('0.00')

    for pedido in pedidos.only('items_snapshot'):
        for item in _items_para_correo(pedido.items_snapshot):
            dato = acumulado.setdefault(
                item['nombre'], {'unidades': 0, 'ingreso': Decimal('0.00')})
            dato['unidades'] += item['cantidad']
            dato['ingreso'] += Decimal(item['subtotal'])

    top = sorted(acumulado.items(), key=lambda kv: kv[1]['ingreso'],
                 reverse=True)[:5]
    return [{'nombre': n, 'unidades': d['unidades'],
             'ingreso': f"{d['ingreso']:.2f}"} for n, d in top]


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=120,
    name='ventas.reporte_ventas_diario',
)
def reporte_ventas_diario(self, forzar: bool = False) -> dict:
    """Revisa las ventas de AYER y avisa al administrador si hubo alguna.

    Beat la ejecuta todos los días a settings.REPORTE_DIARIO_HORA (hora de
    México). El correo solo se envía si hubo al menos un pedido pagado
    ayer: así un fin de semana sin actividad no genera correos (cuida el
    límite gratuito de SendGrid y evita que Gmail marque como spam).

    Args:
        forzar: True envía el correo aunque no haya ventas (para demos).

    Returns:
        dict con fecha, total_pedidos, total_facturado, top_productos y
        correo_enviado (todo serializable a JSON).
    """
    from datetime import timedelta

    from django.db.models import Sum
    from django.urls import reverse

    from configuracion.models import ConfiguracionERP
    from ventas.models import Pedido

    dia = timezone.localdate() - timedelta(days=1)
    pedidos = Pedido.objects.filter(fecha_pedido__date=dia, estado='pagado')
    total_pedidos = pedidos.count()
    total_facturado = (pedidos.aggregate(t=Sum('total_pagado'))['t']
                       or Decimal('0.00'))
    top_productos = _top_productos_del_dia(dia, pedidos) if total_pedidos else []

    resultado = {
        'fecha':           str(dia),
        'total_pedidos':   total_pedidos,
        'total_facturado': f'{total_facturado:.2f}',
        'top_productos':   top_productos,
        'correo_enviado':  False,
    }

    if not total_pedidos and not forzar:
        logger.info('[Tarea reporte_diario] %s: sin ventas; no se envía '
                    'correo.', dia)
        return resultado
    if not settings.ADMIN_EMAIL:
        logger.warning('[Tarea reporte_diario] ADMIN_EMAIL vacío; no se '
                       'envía el reporte de %s.', dia)
        return resultado

    config = ConfiguracionERP.get_instance()
    fecha_txt = dia.strftime('%d/%m/%Y')
    url_admin = (f"{settings.SITE_URL.rstrip('/')}"
                 f"{reverse('admin:ventas_pedido_changelist')}"
                 if settings.SITE_URL else '')
    contexto = {
        'fecha': fecha_txt, 'config': config, 'url_admin': url_admin,
        'total_pedidos': total_pedidos,
        'total_facturado': f'{total_facturado:.2f}',
        'top_productos': top_productos,
    }
    lineas = [
        f"  {n}. {p['nombre']}: {p['unidades']} unidad(es), ${p['ingreso']}"
        for n, p in enumerate(top_productos, start=1)
    ]
    texto = (
        f"Reporte de ventas del {fecha_txt} — {config.nombre_empresa}\n\n"
        f"Pedidos pagados: {total_pedidos}\n"
        f"Total facturado: ${total_facturado:.2f}\n\n"
        + ("Top productos:\n" + "\n".join(lineas) + "\n\n" if lineas else "")
        + (f"Panel de administración: {url_admin}\n" if url_admin else "")
    )

    try:
        send_mail(
            subject=f'Reporte de ventas del {fecha_txt} — '
                    f'{config.nombre_empresa}',
            message=texto,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],
            html_message=render_to_string('ventas/email/reporte_ventas.html',
                                          contexto),
            fail_silently=False,
        )
    except Exception as exc:
        logger.exception('[Tarea reporte_diario] Falló el envío del '
                         'reporte de %s.', dia)
        raise self.retry(exc=exc)

    resultado['correo_enviado'] = True
    logger.info('[Tarea reporte_diario] Reporte de %s enviado (%s pedidos).',
                dia, total_pedidos)
    return resultado

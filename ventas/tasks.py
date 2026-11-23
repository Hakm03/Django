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


@shared_task(
    bind=True,
    max_retries=1,
    name='ventas.verificar_stock_bajo',
)
def verificar_stock_bajo(self, umbral: int = 5) -> dict:
    """Detecta productos activos con stock < umbral y avisa al admin.

    El correo se envía solo si hay productos bajos y ADMIN_EMAIL existe.
    """
    from productos.models import Producto   # import local

    productos_bajos = list(
        Producto.objects
        .filter(activo=True, stock__lt=umbral)
        .values('pk', 'nombre', 'stock')
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
        detalle = "\n".join(
            f"  - {p['nombre']}: {p['stock']} unidad(es)"
            for p in productos_bajos
        )
        try:
            send_mail(
                subject=(f'Alerta de stock bajo '
                         f'({len(productos_bajos)} producto(s))'),
                message=(f'Productos activos con stock menor a {umbral}:'
                         f'\n\n{detalle}\n'),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
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

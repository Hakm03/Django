# catalogo/views.py
"""Vistas del catálogo público y carrito en sesión — W13.

Estructura de request.session['carrito']:
    {'<pk como str>': {'nombre', 'precio' (str), 'cantidad' (int), 'imagen'}}
"""
import logging
from decimal import Decimal

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import ListView

from productos.models import Producto
from ventas.models import Pedido

from .checkout_utils import (
    a_centavos,
    armar_items,
    calcular_totales,
    crear_pedido_pendiente,
    dentro_del_limite,
    firma_carrito,
    obtener_o_crear_cliente,
    validar_carrito,
)
from .filters import ProductoFilter

logger = logging.getLogger(__name__)

CANTIDAD_MAXIMA = 99

# Claves de sesión del checkout (W14)
SESSION_PEDIDOS = 'pedidos_checkout'   # ids de pedidos creados en ESTA sesión
SESSION_ACTIVO  = 'checkout_activo'    # {'pedido_id': n, 'firma': '...'}
SESSION_INTENTS = 'intents_checkout'   # {'<pedido_id>': 'pi_...'} para verificar

# Límite de intentos de pago por usuario (anti-abuso): 10 cada 10 minutos
MAX_INTENTOS_CHECKOUT = 10
VENTANA_INTENTOS      = 600

# Clave secreta de Stripe (vacía si no está configurada; ver _stripe_configurado)
stripe.api_key = settings.STRIPE_SECRET_KEY


class CatalogoView(ListView):
    """Catálogo público (sin login) con filtros y paginación."""

    model = Producto
    template_name = 'catalogo/catalogo.html'
    context_object_name = 'productos'
    paginate_by = 12

    def get_queryset(self):
        qs = (
            Producto.objects.select_related('categoria', 'proveedor')
            .filter(activo=True).order_by('nombre')
        )
        self.filtro = ProductoFilter(self.request.GET, queryset=qs)
        return self.filtro.qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filtro'] = self.filtro
        return ctx


# ── Carrito ────────────────────────────────────────────────────────────────

def _obtener_carrito(request) -> dict:
    return request.session.get('carrito', {})


def _guardar_carrito(request, carrito: dict) -> None:
    request.session['carrito'] = carrito
    request.session.modified = True


def _leer_cantidad(request, defecto: int = 1) -> int:
    """Lee 'cantidad' del POST; si no es un entero válido usa el defecto."""
    try:
        return int(request.POST.get('cantidad', defecto))
    except (TypeError, ValueError):
        return defecto


def _url_segura(request):
    """Devuelve 'next' solo si apunta a este mismo sitio (evita open redirect)."""
    destino = request.POST.get('next') or request.META.get('HTTP_REFERER')
    if destino and url_has_allowed_host_and_scheme(
        destino, allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return destino
    return None


def ver_carrito(request):
    """Muestra el carrito; convierte precios str → Decimal para el total."""
    items, total = [], Decimal('0.00')
    for prod_id, datos in _obtener_carrito(request).items():
        precio = Decimal(datos['precio'])
        cantidad = int(datos['cantidad'])
        subtotal = precio * cantidad
        total += subtotal
        items.append({
            'prod_id': prod_id, 'nombre': datos['nombre'],
            'precio': precio, 'cantidad': cantidad,
            'subtotal': subtotal, 'imagen': datos.get('imagen'),
        })
    return render(request, 'catalogo/carrito.html',
                  {'items': items, 'total': total})


def agregar_al_carrito(request, producto_id: int):
    """Agrega un producto (solo POST). Respeta stock y máximo por línea."""
    if request.method != 'POST':
        return redirect('catalogo:catalogo')

    producto = get_object_or_404(Producto, pk=producto_id, activo=True)
    carrito = _obtener_carrito(request)
    clave = str(producto_id)
    cantidad = max(_leer_cantidad(request), 1)

    actual = carrito[clave]['cantidad'] if clave in carrito else 0
    limite = min(CANTIDAD_MAXIMA, producto.stock)
    nueva = min(actual + cantidad, limite)

    if nueva <= 0:
        messages.error(request, f'"{producto.nombre}" no tiene stock.')
    else:
        carrito[clave] = {
            'nombre': producto.nombre,
            'precio': str(producto.precio),
            'cantidad': nueva,
            'imagen': producto.imagen.name if producto.imagen else None,
        }
        _guardar_carrito(request, carrito)
        if actual + cantidad > limite:
            messages.warning(
                request,
                f'Solo hay {limite} unidad(es) disponibles de '
                f'"{producto.nombre}".')
        else:
            messages.success(
                request, f'"{producto.nombre}" agregado al carrito.')

    return redirect(_url_segura(request) or 'catalogo:catalogo')


def remover_del_carrito(request, producto_id: int):
    """Elimina un producto del carrito (solo POST)."""
    if request.method != 'POST':
        return redirect('catalogo:carrito')
    carrito = _obtener_carrito(request)
    nombre = carrito.pop(str(producto_id), {}).get('nombre', 'Producto')
    _guardar_carrito(request, carrito)
    messages.warning(request, f'"{nombre}" eliminado del carrito.')
    return redirect('catalogo:carrito')


def actualizar_cantidad(request, producto_id: int):
    """Cambia la cantidad (solo POST). 0 o menos elimina la línea."""
    if request.method != 'POST':
        return redirect('catalogo:carrito')
    carrito = _obtener_carrito(request)
    clave = str(producto_id)
    cantidad = _leer_cantidad(request)

    if clave in carrito:
        if cantidad > 0:
            stock = (Producto.objects.filter(pk=producto_id)
                     .values_list('stock', flat=True).first() or 0)
            carrito[clave]['cantidad'] = min(
                cantidad, CANTIDAD_MAXIMA, max(stock, 1))
        else:
            carrito.pop(clave)
    _guardar_carrito(request, carrito)
    return redirect('catalogo:carrito')


def vaciar_carrito(request):
    """Vacía el carrito (solo POST)."""
    if request.method == 'POST':
        _guardar_carrito(request, {})
        messages.info(request, 'Carrito vaciado.')
    return redirect('catalogo:carrito')


# ── Checkout con Stripe (W14) ──────────────────────────────────────────────

def _stripe_configurado() -> bool:
    """True si hay claves de Stripe reales (no vacías) en la configuración."""
    return (settings.STRIPE_SECRET_KEY.startswith('sk_')
            and settings.STRIPE_PUBLISHABLE_KEY.startswith('pk_'))


def _pedido_reutilizable(request, cliente, total, firma):
    """Devuelve el Pedido pendiente de ESTE carrito, si ya existe.

    Evita crear un Pedido nuevo por cada recarga/doble clic. Solo se reutiliza
    si el contenido del carrito (firma) y el total no cambiaron.
    """
    activo = request.session.get(SESSION_ACTIVO)
    if not activo or activo.get('firma') != firma:
        return None
    return Pedido.objects.filter(
        pk=activo.get('pedido_id'), cliente=cliente,
        estado='pendiente', total_pagado=total,
    ).first()


def _recordar_pedido(request, pedido, firma) -> None:
    """Registra en la sesión que este usuario creó el pedido (autorización)."""
    ids = request.session.get(SESSION_PEDIDOS, [])
    if pedido.pk not in ids:
        ids.append(pedido.pk)
    request.session[SESSION_PEDIDOS] = ids[-20:]
    request.session[SESSION_ACTIVO] = {'pedido_id': pedido.pk, 'firma': firma}
    request.session.modified = True


@login_required
def checkout(request):
    """Proceso de pago: muestra resumen y crea PaymentIntent de Stripe.

    GET:  Muestra resumen del carrito con IVA calculado.
          No crea Pedido ni PaymentIntent (espera a POST).

    POST: Revalida carrito → crea (o reutiliza) Pedido → crea PaymentIntent →
          retorna client_secret al template para que Stripe.js
          confirme el pago del lado del cliente.

    Redirige a /catalogo/ si el carrito está vacío.
    """
    carrito = _obtener_carrito(request)
    if not carrito:
        messages.warning(request, 'Tu carrito está vacío.')
        return redirect('catalogo:catalogo')

    # ── 0. Revalidar contra la BD (precio, stock, producto activo) ─────────
    carrito, avisos = validar_carrito(carrito)
    if avisos:
        # Si algo cambió NO se cobra en silencio: se muestra y el usuario
        # revisa el resumen actualizado antes de pagar.
        _guardar_carrito(request, carrito)
        for aviso in avisos:
            messages.warning(request, aviso)
        return redirect('catalogo:checkout' if carrito else 'catalogo:catalogo')

    totales         = calcular_totales(carrito)
    items           = armar_items(carrito)   # subtotal por línea
    publishable_key = settings.STRIPE_PUBLISHABLE_KEY

    if request.method != 'POST':
        # GET — solo mostrar resumen (sin Pedido ni PaymentIntent)
        return render(request, 'catalogo/checkout.html', {
            'carrito':         carrito,
            'items':           items,
            'totales':         totales,
            'client_secret':   None,          # se genera en POST
            'publishable_key': publishable_key,
        })

    # ── POST ───────────────────────────────────────────────────────────────
    # Límite de intentos: evita crear pedidos y llamar a Stripe sin parar.
    if not dentro_del_limite(f'checkout:{request.user.pk}',
                             MAX_INTENTOS_CHECKOUT, VENTANA_INTENTOS):
        logger.warning('Checkout: límite de intentos excedido (usuario=%s).',
                       request.user.pk)
        messages.error(request, 'Demasiados intentos de pago. '
                                'Espera unos minutos e inténtalo de nuevo.')
        return render(request, 'catalogo/pago_error.html', status=429)

    if not _stripe_configurado():
        logger.error('Checkout: faltan STRIPE_SECRET_KEY / STRIPE_PUBLISHABLE_KEY.')
        messages.error(request, 'El pago en línea no está disponible por ahora.')
        return redirect('catalogo:pago_error')

    pedido, es_nuevo = None, False
    try:
        # 1. Vincular usuario con Cliente del ERP
        cliente = obtener_o_crear_cliente(request.user)

        # 2. Reutilizar el pedido pendiente de este carrito o crear uno nuevo
        firma  = firma_carrito(carrito)
        pedido = _pedido_reutilizable(request, cliente, totales['total'], firma)
        if pedido is None:
            # Snapshot del carrito: pago_exitoso() vacía la sesión, así que el
            # webhook (W15) necesita esta copia para saber qué stock descontar.
            snapshot = [
                {
                    'producto_id': int(prod_id),
                    'nombre':      datos['nombre'],
                    'cantidad':    int(datos['cantidad']),
                    'precio':      str(datos['precio']),
                }
                for prod_id, datos in carrito.items()
            ]
            pedido   = crear_pedido_pendiente(
                cliente, totales['total'], items_snapshot=snapshot)
            es_nuevo = True
        _recordar_pedido(request, pedido, firma)

        # 3. Crear PaymentIntent en Stripe (monto en centavos)
        centavos = a_centavos(totales['total'])
        intent = stripe.PaymentIntent.create(
            amount               = centavos,
            currency             = 'mxn',
            # Las cuentas nuevas de Stripe ya no aceptan payment_method_types:
            # los métodos se administran en el Dashboard. 'never' evita métodos
            # con redirección, que el Card Element no soporta.
            automatic_payment_methods = {'enabled': True,
                                         'allow_redirects': 'never'},
            metadata             = {
                'pedido_id':  pedido.pk,
                'pedido_num': pedido.numero_pedido,
                'cliente':    cliente.nombre,
            },
            # La llave incluye el monto: misma llave + mismos datos = mismo
            # PaymentIntent (sin cobros duplicados).
            idempotency_key = f'pedido-{pedido.pk}-{centavos}',
        )

        # Recordar el PaymentIntent de este pedido: pago_exitoso lo consultará
        # en Stripe para comprobar que el pago ocurrió de verdad.
        intents = request.session.get(SESSION_INTENTS, {})
        intents[str(pedido.pk)] = intent.id
        request.session[SESSION_INTENTS] = dict(list(intents.items())[-20:])
        request.session.modified = True

        # 4. Retornar client_secret al template
        return render(request, 'catalogo/checkout.html', {
            'carrito':         carrito,
            'items':           items,
            'totales':         totales,
            'pedido':          pedido,
            'client_secret':   intent.client_secret,
            'publishable_key': publishable_key,
        })

    except Exception as exc:        # StripeError y cualquier imprevisto
        # El detalle va al LOG (visible en Render), nunca al usuario.
        logger.exception('Checkout: fallo al iniciar el pago (pedido=%s)',
                         getattr(pedido, 'pk', None))
        # Solo se cancela un pedido recién creado en esta petición: nunca se
        # tocan pedidos reutilizados, que podrían tener un pago en curso.
        if pedido is not None and es_nuevo:
            Pedido.objects.filter(pk=pedido.pk, estado='pendiente') \
                          .update(estado='cancelado')
        if isinstance(exc, stripe.error.StripeError):
            messages.error(request, 'No pudimos conectar con la pasarela de '
                                    'pago. Intenta de nuevo en unos minutos.')
        else:
            messages.error(request, 'Ocurrió un error al iniciar el pago. '
                                    'Tu carrito sigue intacto.')
        return redirect('catalogo:pago_error')


def _pago_verificado(request, pedido) -> bool:
    """Pregunta a Stripe si el pago de este pedido ocurrió de verdad.

    True solo si el PaymentIntent guardado en la sesión:
      - existe y Stripe responde,
      - está 'succeeded' (pagado) o 'processing' (el banco aún lo procesa),
      - pertenece a este pedido (metadata) y tiene el monto del pedido.
    Cualquier otra cosa (sin intent, error de Stripe, otro estado) → False.
    """
    intent_id = request.session.get(SESSION_INTENTS, {}).get(str(pedido.pk))
    if not intent_id:
        return False
    try:
        intent = stripe.PaymentIntent.retrieve(intent_id)
    except Exception:                       # StripeError, red, clave inválida…
        logger.exception('Verificación de pago falló (pedido=%s)', pedido.pk)
        return False

    metadata = getattr(intent, 'metadata', None) or {}
    return (
        intent.status in ('succeeded', 'processing')
        and str(metadata.get('pedido_id')) == str(pedido.pk)
        and intent.amount == a_centavos(pedido.total_pagado)
    )


@login_required
def pago_exitoso(request, pedido_id: int):
    """Vista posterior al pago: vacía el carrito y muestra el pedido.

    Solo accesible para quien creó el pedido en esta sesión (evita que un
    usuario revise pedidos ajenos cambiando el número en la URL).

    Antes de vaciar el carrito se CONSULTA a Stripe el estado del pago: no
    basta con abrir esta dirección. Si el pago no está 'succeeded' o
    'processing' (o no coincide el pedido o el monto), el carrito queda intacto
    y se regresa al checkout.

    ⚠️ Aun así, la fuente de verdad del estado del pedido es el webhook (W15).
    Por eso el texto dice "pago recibido", no "pedido confirmado".
    """
    if pedido_id not in request.session.get(SESSION_PEDIDOS, []):
        raise Http404('Pedido no encontrado.')
    pedido = get_object_or_404(Pedido, pk=pedido_id)

    if not dentro_del_limite(f'exito:{request.user.pk}', 30, VENTANA_INTENTOS):
        return render(request, 'catalogo/pago_error.html', status=429)

    if not _pago_verificado(request, pedido):
        messages.warning(request, 'No pudimos confirmar tu pago todavía. '
                                  'Tu carrito sigue intacto.')
        return redirect('catalogo:checkout')

    _guardar_carrito(request, {})     # vaciar carrito
    request.session.pop(SESSION_ACTIVO, None)
    request.session.modified = True

    return render(request, 'catalogo/pago_exitoso.html', {'pedido': pedido})


def pago_error(request):
    """Vista de error de pago — muestra mensaje y permite reintentar."""
    return render(request, 'catalogo/pago_error.html')

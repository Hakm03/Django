# catalogo/webhook_views.py
"""Endpoint de webhook para recibir eventos de Stripe — W15.

Seguridad:
    Stripe firma cada evento con STRIPE_WEBHOOK_SECRET.
    stripe.Webhook.construct_event() verifica la firma.
    Firma o payload inválido -> 400. Secreto sin configurar -> 500.

Eventos manejados:
    payment_intent.succeeded      -> Pedido 'pagado' + descuento de stock
    payment_intent.payment_failed -> Pedido 'cancelado' (solo si 'pendiente')

Idempotencia:
    El cambio a 'pagado' es un UPDATE condicional (exclude estado='pagado')
    dentro de una transacción. El stock solo se descuenta si ese UPDATE
    modificó una fila, así un evento duplicado no descuenta dos veces.
"""
import logging

import stripe
from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from productos.models import Producto
from ventas.models import Pedido

from .checkout_utils import a_centavos

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def stripe_webhook(request) -> HttpResponse:
    """Recibe, verifica y despacha eventos de Stripe."""
    secreto = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
    if not secreto:
        logger.error('Webhook: STRIPE_WEBHOOK_SECRET no está configurado.')
        return HttpResponse('Webhook no configurado.', status=500)

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    try:
        event = stripe.Webhook.construct_event(
            payload=payload, sig_header=sig_header, secret=secreto,
        )
    except ValueError:
        logger.warning('Webhook: payload inválido recibido.')
        return HttpResponse('Payload inválido.', status=400)
    except stripe.SignatureVerificationError:
        logger.warning('Webhook: firma inválida.')
        return HttpResponse('Firma inválida.', status=400)

    # stripe >= 15 devuelve StripeObject (sin .get()): convertir a dict.
    if hasattr(event, 'to_dict'):
        event = event.to_dict()

    tipo = event['type']
    logger.info('Webhook recibido: %s', tipo)

    if tipo == 'payment_intent.succeeded':
        _manejar_pago_exitoso(event['data']['object'])
    elif tipo == 'payment_intent.payment_failed':
        _manejar_pago_fallido(event['data']['object'])
    else:
        logger.debug('Evento ignorado: %s', tipo)

    return HttpResponse(status=200)


# ── HANDLERS INTERNOS ──────────────────────────────────────────────────────

def _manejar_pago_exitoso(payment_intent: dict) -> None:
    """Marca el pedido como pagado y descuenta stock (una sola vez)."""
    pedido_id = _extraer_pedido_id(payment_intent)
    if pedido_id is None:
        return

    try:
        pedido = Pedido.objects.get(pk=pedido_id)
    except Pedido.DoesNotExist:
        logger.error('Webhook: Pedido %s no encontrado.', pedido_id)
        return

    # Verificar que Stripe cobró exactamente lo que vale el pedido.
    if payment_intent.get('amount') != a_centavos(pedido.total_pagado):
        logger.error(
            'Webhook: monto distinto en pedido %s (Stripe=%s, pedido=%s). '
            'No se marca como pagado.',
            pedido.numero_pedido, payment_intent.get('amount'),
            a_centavos(pedido.total_pagado),
        )
        return

    with transaction.atomic():
        cambiadas = (
            Pedido.objects
            .filter(pk=pedido.pk)
            .exclude(estado='pagado')
            .update(estado='pagado')
        )
        if not cambiadas:
            logger.info('Pedido %s ya estaba pagado — sin cambios.',
                        pedido.numero_pedido)
            return
        _descontar_stock(pedido)

    logger.info('Pedido %s actualizado a "pagado".', pedido.numero_pedido)


def _manejar_pago_fallido(payment_intent: dict) -> None:
    """Cancela el pedido solo si sigue 'pendiente'."""
    pedido_id = _extraer_pedido_id(payment_intent)
    if pedido_id is None:
        return

    cambiadas = (
        Pedido.objects
        .filter(pk=pedido_id, estado='pendiente')
        .update(estado='cancelado')
    )
    if cambiadas:
        logger.info('Pedido %s cancelado por pago fallido.', pedido_id)
    else:
        logger.info('Pedido %s no estaba pendiente — sin cambios.', pedido_id)


def _extraer_pedido_id(payment_intent: dict) -> int | None:
    """Obtiene pedido_id del metadata del PaymentIntent (o None)."""
    metadata = payment_intent.get('metadata') or {}
    pedido_id = metadata.get('pedido_id')

    if not pedido_id:
        logger.warning('Webhook: PaymentIntent %s sin pedido_id en metadata.',
                       payment_intent.get('id'))
        return None
    try:
        return int(pedido_id)
    except (ValueError, TypeError):
        logger.error('Webhook: pedido_id inválido: %r', pedido_id)
        return None


def _descontar_stock(pedido: Pedido) -> None:
    """Descuenta stock con F() (atómico). Si falta stock, avisa en el log."""
    for item in pedido.items_snapshot or []:
        producto_id = item.get('producto_id')
        try:
            cantidad = int(item.get('cantidad', 0))
        except (ValueError, TypeError):
            continue
        if not producto_id or cantidad <= 0:
            continue

        filas = Producto.objects.filter(
            pk=producto_id, stock__gte=cantidad,
        ).update(stock=F('stock') - cantidad)

        if filas:
            logger.info('Stock decrementado: producto %s -%s.',
                        producto_id, cantidad)
        else:
            logger.warning(
                'Pedido %s: stock insuficiente para producto %s (-%s).',
                pedido.numero_pedido, producto_id, cantidad,
            )

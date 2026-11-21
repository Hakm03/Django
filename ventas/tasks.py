# ventas/tasks.py
"""Tareas asíncronas de la app ventas — W16.

Descubiertas por app.autodiscover_tasks() (core/celery.py).

Estado:
    W16: placeholders (solo registran en el log).
    W17: correo real con SendGrid (+ idempotencia con correo_enviado).
    W18: tareas programadas con Celery Beat.
"""
import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name='ventas.enviar_confirmacion_pedido',
)
def enviar_confirmacion_pedido(self, pedido_id: int) -> dict:
    """Confirmación de pedido al cliente (W16: solo log).

    Recibe el ID (no el objeto) porque los argumentos deben ser JSON.
    """
    from ventas.models import Pedido   # import local: evita circularidad

    try:
        pedido = Pedido.objects.select_related('cliente').get(pk=pedido_id)
    except Pedido.DoesNotExist:
        logger.error('[Tarea enviar_confirmacion] Pedido %s no existe.',
                     pedido_id)
        return {'estado': 'error', 'pedido_id': pedido_id}

    logger.info(
        '[Tarea enviar_confirmacion] Procesando pedido %s para %s. '
        'Total: $%s. Timestamp: %s',
        pedido.numero_pedido, pedido.cliente.correo,
        pedido.total_pagado, timezone.now().isoformat(),
    )

    return {
        'estado':    'ok',
        'pedido_id': pedido_id,
        'numero':    pedido.numero_pedido,
        'cliente':   pedido.cliente.correo,
    }


@shared_task(
    bind=True,
    max_retries=1,
    name='ventas.verificar_stock_bajo',
)
def verificar_stock_bajo(self, umbral: int = 5) -> dict:
    """Detecta productos activos con stock < umbral (W16: solo log)."""
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

    return {
        'umbral':          umbral,
        'productos_bajos': productos_bajos,
        'total':           len(productos_bajos),
    }

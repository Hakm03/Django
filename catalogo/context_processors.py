# catalogo/context_processors.py
"""Inyecta el contador del carrito en todos los templates — W13."""
from typing import Any


def carrito_info(request) -> dict[str, Any]:
    """Devuelve total de unidades y de productos distintos del carrito."""
    carrito = request.session.get('carrito', {})
    try:
        total_items = sum(int(i.get('cantidad', 0)) for i in carrito.values())
    except (AttributeError, TypeError, ValueError):
        carrito, total_items = {}, 0
    return {
        'carrito_total_items': total_items,
        'carrito_total_productos': len(carrito),
    }

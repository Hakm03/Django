# catalogo/views.py
"""Vistas del catálogo público y carrito en sesión — W13.

Estructura de request.session['carrito']:
    {'<pk como str>': {'nombre', 'precio' (str), 'cantidad' (int), 'imagen'}}
"""
from decimal import Decimal

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import ListView

from productos.models import Producto

from .filters import ProductoFilter

CANTIDAD_MAXIMA = 99


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

# catalogo/checkout_utils.py
"""Funciones auxiliares para el proceso de checkout — W14.

Separadas de views.py para facilitar las pruebas unitarias.
"""
import logging
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.core.cache import cache
from django.db import IntegrityError, transaction

from clientes.models      import Cliente
from configuracion.models import ConfiguracionERP
from productos.models     import Producto
from ventas.models        import Pedido

logger = logging.getLogger(__name__)


def dentro_del_limite(clave: str, maximo: int = 10, ventana: int = 600) -> bool:
    """Limita cuántas veces se puede hacer algo en una ventana de tiempo.

    Cuenta intentos en la caché de Django (sin instalar paquetes).

    Args:
        clave:   identifica quién y qué, p. ej. 'checkout:7' (usuario 7).
        maximo:  intentos permitidos dentro de la ventana.
        ventana: duración de la ventana, en segundos (600 = 10 minutos).

    Returns:
        True si este intento está permitido; False si ya se pasó del límite.

    Nota: con la caché por defecto (memoria) el contador es por proceso del
    servidor. Con Redis (W16+) será compartido entre procesos.
    """
    cache.add(clave, 0, ventana)         # crea el contador solo si no existe
    try:
        intentos = cache.incr(clave)
    except ValueError:                   # expiró justo ahora
        cache.set(clave, 1, ventana)
        intentos = 1
    return intentos <= maximo


def validar_carrito(carrito: dict) -> tuple:
    """Revalida el carrito de sesión contra la BD.

    Quita productos inexistentes/inactivos, ajusta cantidades al stock real y
    refresca el precio. NUNCA cobra datos desactualizados en silencio: si algo
    cambia, devuelve avisos para que el usuario lo revise.

    Returns:
        (carrito_limpio, avisos): dict con la misma estructura de sesión y
        lista de textos para mostrar con messages.
    """
    ids = []
    for clave in carrito:
        try:
            ids.append(int(clave))
        except (TypeError, ValueError):
            pass
    productos = Producto.objects.in_bulk(ids)

    limpio, avisos = {}, []
    for clave, datos in carrito.items():
        try:
            pk       = int(clave)
            cantidad = int(datos['cantidad'])
        except (TypeError, ValueError, KeyError):
            avisos.append('Un artículo inválido se quitó de tu carrito.')
            continue

        prod = productos.get(pk)
        if prod is None or not prod.activo:
            avisos.append(
                f'"{datos.get("nombre", "Producto")}" ya no está disponible '
                f'y se quitó de tu carrito.')
            continue
        if prod.stock <= 0:
            avisos.append(f'"{prod.nombre}" se agotó y se quitó de tu carrito.')
            continue
        if cantidad > prod.stock:
            avisos.append(
                f'Solo quedan {prod.stock} unidad(es) de "{prod.nombre}"; '
                f'ajustamos tu carrito.')
            cantidad = prod.stock
        if str(prod.precio) != str(datos.get('precio')):
            avisos.append(
                f'El precio de "{prod.nombre}" cambió a ${prod.precio}.')

        limpio[clave] = {
            'nombre':   prod.nombre,
            'precio':   str(prod.precio),      # str, regla del carrito
            'cantidad': cantidad,
            'imagen':   datos.get('imagen'),
        }
    return limpio, avisos


def firma_carrito(carrito: dict) -> str:
    """Huella del contenido del carrito (productos, cantidades y precios).

    Sirve para saber si un Pedido pendiente sigue correspondiendo al carrito
    actual y puede reutilizarse sin crear otro.
    """
    return '|'.join(
        f'{clave}:{datos["cantidad"]}:{datos["precio"]}'
        for clave, datos in sorted(carrito.items())
    )


def calcular_totales(carrito: dict) -> dict:
    """Calcula subtotal, IVA y total del carrito.

    Args:
        carrito: dict de sesión con estructura
                 {str(pk): {precio: str, cantidad: int, ...}}

    Returns:
        dict con subtotal, iva_pct, iva_monto, total (todos Decimal).
    """
    config   = ConfiguracionERP.get_instance()
    iva_pct  = config.iva_porcentaje / Decimal('100')

    subtotal = sum(
        (Decimal(datos['precio']) * int(datos['cantidad'])
         for datos in carrito.values()),
        Decimal('0.00'),
    )
    iva_monto = (subtotal * iva_pct).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )
    total = subtotal + iva_monto

    return {
        'subtotal':  subtotal,
        'iva_pct':   config.iva_porcentaje,
        'iva_monto': iva_monto,
        'total':     total,
    }


def a_centavos(monto: Decimal) -> int:
    """Convierte un monto en pesos a centavos enteros (lo que exige Stripe).

    Redondea con ROUND_HALF_UP; `int(monto * 100)` truncaría y podría cobrar
    un centavo de menos.
    """
    return int((monto * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def armar_items(carrito: dict) -> list:
    """Convierte el carrito de sesión en una lista con el subtotal por línea.

    Los templates de Django no pueden multiplicar (precio × cantidad),
    por eso el cálculo se hace aquí.

    Returns:
        list de dicts con nombre, precio, cantidad y subtotal (Decimal).
    """
    items = []
    for datos in carrito.values():
        precio   = Decimal(datos['precio'])
        cantidad = int(datos['cantidad'])
        items.append({
            'nombre':   datos['nombre'],
            'precio':   precio,
            'cantidad': cantidad,
            'subtotal': precio * cantidad,
        })
    return items


def obtener_o_crear_cliente(user) -> Cliente:
    """Obtiene o crea un Cliente del ERP vinculado al usuario Django.

    Busca por correo sin distinguir mayúsculas (Cliente.correo es único y
    'Ana@x.com' vs 'ana@x.com' provocaría IntegrityError).

    ⚠️ NUNCA modifica los datos de un Cliente que ya existe. El registro
    de usuarios no verifica el correo (ACCOUNT_EMAIL_VERIFICATION='none'):
    cualquiera podría registrarse con el correo de un cliente real y, si
    este código actualizara el nombre, estaría reescribiendo sus datos.
    """
    correo = (user.email or f'{user.username}@erp.local').strip().lower()
    nombre = user.get_full_name() or user.username

    cliente = Cliente.objects.filter(correo__iexact=correo).first()
    if cliente is None:
        try:
            with transaction.atomic():
                cliente = Cliente.objects.create(
                    correo=correo, nombre=nombre, activo=True)
        except IntegrityError:      # otra petición lo creó al mismo tiempo
            cliente = Cliente.objects.get(correo__iexact=correo)
    return cliente


def crear_pedido_pendiente(cliente: Cliente, total: Decimal, **extra) -> Pedido:
    """Crea un Pedido 'pendiente' con número único PED-YYYY-NNNN.

    El siguiente número se calcula con el MAYOR existente del año (no con
    count()+1, que repite número si se borra un pedido) y se reintenta si dos
    peticiones simultáneas eligen el mismo (numero_pedido es unique).

    Args:
        extra: campos adicionales del Pedido (W15 pasará items_snapshot).
    """
    prefijo = f'PED-{date.today().year}-'
    for _ in range(5):
        sufijos = [
            int(n.rsplit('-', 1)[1])
            for n in Pedido.objects.filter(numero_pedido__startswith=prefijo)
                                   .values_list('numero_pedido', flat=True)
            if n.rsplit('-', 1)[1].isdigit()
        ]
        numero = f'{prefijo}{max(sufijos, default=0) + 1:04d}'
        try:
            with transaction.atomic():
                return Pedido.objects.create(
                    numero_pedido=numero, cliente=cliente,
                    estado='pendiente', total_pagado=total, **extra)
        except IntegrityError:
            continue
    raise RuntimeError('No se pudo generar un número de pedido único.')

# Guía de Laboratorio — W14
## ERP Django · Espiral 5 · Semana 14 de 24
### Técnico en Programación (SEP 3061300006-23) · UTEC Celaya
### Asesor: MC. Román Fernando López González

---

| Campo | Detalle |
|---|---|
| **Semana** | W14 de 24 |
| **Espiral** | E5 — E-commerce y Pagos |
| **Sprint Scrum** | Sprint 4 — Desarrollo |
| **Hito** | Sin hito propio · Avance hacia M5 (W15) |
| **Horario** | 16:45 – 19:45 (180 min) |
| **Nivel Schmelkes** | 4 — Funcionalidades Avanzadas |
| **Hilo conductor** | "W13 llenó el carrito. W14 cobra: checkout real con Stripe sandbox." |

---

## Respuesta a la tarea de investigación de W13

> **¿Qué es un `PaymentIntent` y qué estados puede tener?**
>
> Un `PaymentIntent` es el objeto central en la API de Stripe que
> representa una intención de cobrar dinero a un cliente. Encapsula
> el monto, la moneda y el estado del proceso de pago.
>
> | Estado | Significado |
> |---|---|
> | `requires_payment_method` | Esperando que el cliente proporcione tarjeta |
> | `requires_confirmation` | Datos proporcionados, esperando confirmación |
> | `requires_action` | Requiere autenticación 3D Secure |
> | `processing` | Stripe está procesando el pago |
> | `succeeded` | Pago completado exitosamente ✅ |
> | `canceled` | Cancelado — no se puede reactivar |
> | `payment_failed` | Pago rechazado |
>
> **Tarjetas de prueba Stripe:**
>
> | Tarjeta | Resultado |
> |---|---|
> | `4242 4242 4242 4242` | Pago exitoso |
> | `4000 0000 0000 9995` | Fondos insuficientes (rechazado) |
> | `4000 0025 0000 3155` | Requiere autenticación 3D Secure |
>
> Para todas las tarjetas de prueba: vencimiento cualquier fecha futura,
> CVC cualquier número de 3 dígitos, CP cualquier código de 5 dígitos.
>
> **¿Carrito persistente más allá de la sesión?**
> Tres opciones:
> 1. **Base de datos:** modelo `CarritoItem(user, producto, cantidad)` —
>    persiste indefinidamente, sincronizable entre dispositivos.
> 2. **Cookie firmada:** `set_signed_cookie('carrito', data, max_age=604800)` —
>    persiste 7 días sin BD, pero limita el tamaño.
> 3. **Sesión con `SESSION_COOKIE_AGE`** (actual) — persiste hasta expirar
>    la cookie, por defecto 2 semanas si `ACCOUNT_SESSION_REMEMBER=True`.

---

## Objetivos de la sesión

Al terminar W14, el estudiante será capaz de:

1. Instalar y configurar `stripe-python` con claves de sandbox desde `.env`
2. Implementar `CheckoutView` que crea un `Pedido` y un `PaymentIntent`
3. Renderizar el formulario de pago con Stripe.js y el Card Element
4. Manejar el resultado del pago (éxito, error, 3D Secure)
5. Vincular usuarios de Django con el modelo `Cliente` del ERP
6. Escribir tests con `unittest.mock.patch` para simular llamadas a Stripe
7. Verificar con Stripe que un pago ocurrió antes de confirmarlo al usuario
8. Limitar los intentos de pago para evitar abusos del endpoint

---

## Stack tecnológico de W14

| Herramienta | Novedad en W14 | Descripción |
|---|---|---|
| `stripe` 16.1.0 (Python) | ✅ Nuevo | SDK de Stripe para crear PaymentIntents desde el backend |
| Stripe.js | ✅ Nuevo | Librería JS para mostrar el formulario de tarjeta de forma segura |
| Card Element | ✅ Nuevo | Componente Stripe para capturar datos de tarjeta (no pasan por nuestro servidor) |
| `unittest.mock.patch` | ✅ Nuevo | Reemplaza `stripe.PaymentIntent.create` en tests |
| `idempotency_key` | ✅ Nuevo | Previene cargos duplicados si la petición se reintenta |
| `PaymentIntent.retrieve` | ✅ Nuevo | Pregunta a Stripe el estado real de un pago (no se confía en la URL) |
| `django.core.cache` | ✅ Nuevo | Cuenta intentos por usuario para limitar el checkout (sin instalar nada) |

---

## Mapa de tiempo (180 min)

| Parte | Actividad | Tiempo |
|---|---|---|
| Arranque | Daily Scrum + verificar W13 | 10 min |
| Parte 1 | Instalar `stripe` + configurar claves | 10 min |
| Parte 2 | Lógica de checkout: totales, cliente, pedido y límite de intentos | 15 min |
| Parte 3 | `CheckoutView` + `pago_exitoso` (con verificación en Stripe) + `pago_error` | 25 min |
| Parte 4 | Template `checkout.html` con Stripe.js | 25 min |
| Parte 5 | Templates `pago_exitoso.html` + `pago_error.html` | 15 min |
| Parte 6 | Actualizar `catalogo/urls.py` | 10 min |
| Parte 7 | Tests W14 (28 pruebas con mock) | 20 min |
| Cierre | Commit · `finalizar_sesion.bat` · hilo → W15 | 10 min |
| Buffer | | 20 min |
| **Total** | | **180 min** |

---

## ARRANQUE — Daily Scrum (10 min)

```cmd
E:\iniciar_sesion.bat
```

### Daily Scrum

```
1. ¿Qué hice en W13?
   → Creé el catálogo público filtrable con django-filter
     y el carrito de compras con sesiones Django.

2. ¿Qué haré en W14?
   → Implementaré el checkout con Stripe sandbox:
     checkout.html con Card Element, creación de PaymentIntent
     y manejo de éxito/error del pago.

3. ¿Tengo algún impedimento?
   → (registrar aquí)
```

### Verificar estado

```powershell
git branch --show-current      # debe mostrar: w14
git status --short             # anota qué archivos sueltos ya existían
python manage.py check
python manage.py test tests --verbosity=0
```

**Resultado esperado:** `System check identified no issues` · `Ran N tests … OK`,
donde **N es tu base actual**. En el repositorio de referencia fueron
**204 tests (skipped=5)**; los "131" de versiones anteriores de esta guía ya no
aplican porque W12 y W13 agregaron pruebas. **Anota tu N**: todas las cifras de
esta guía son *N + nuevos*.

> 🧰 **¿`git` no se reconoce en la terminal?** En la PC de la escuela el Git
> portable vive en la USB y `iniciar_sesion.bat` solo agrega su carpeta al PATH
> de *esa* ventana. En cualquier otra terminal (VS Code, Claude Code) hay que
> agregarlo manualmente, por ventana:
>
> ```powershell
> $g = Get-ChildItem E:\ -Recurse -Filter git.exe -Depth 4 -ErrorAction SilentlyContinue |
>      Where-Object FullName -like '*\cmd\git.exe' | Select-Object -First 1
> $env:Path = "$($g.DirectoryName);$env:Path"
> git --version
> ```
>
> (Cambia `E:\` si tu USB tiene otra letra.)

---

## PARTE 1 — Instalar Stripe y Configurar Claves (10 min)

### 1.1 Instalar el SDK de Stripe

```powershell
pip install "stripe==16.1.0"
python -c "import stripe; print('stripe', stripe.VERSION)"
```

Debe mostrar `stripe 16.1.0`.

> 🚫 **NO uses `pip freeze > requirements.txt` en PowerShell.** PowerShell 5.1
> guarda la redirección en **UTF-16**; Render no puede leer el archivo y el
> deploy falla. Además reemplaza las versiones fijadas del proyecto por todo lo
> que haya en tu entorno.
>
> **Forma correcta:** abre `requirements.txt` en VS Code, agrega una línea
> `stripe==16.1.0` (en orden alfabético o al final) y guarda en **UTF-8**.
> Verifica:
>
> ```powershell
> Select-String -Path requirements.txt -Pattern '^stripe=='
> [IO.File]::ReadAllBytes('requirements.txt')[0..1]
> ```
>
> Si los dos bytes son `255 254`, el archivo quedó en UTF-16 (dañado): restáuralo
> con `git restore requirements.txt` y repite la edición manual.

### 1.2 Obtener claves de sandbox de Stripe

1. Ir a `https://dashboard.stripe.com` → crear cuenta gratuita
2. Activar el **modo de prueba**. Según la versión del panel se llama *Modo de prueba*,
   *Sandbox* o *Entorno de prueba*: debe verse un aviso de que los cambios no afectan
   pagos reales. Si el asistente de bienvenida te pide datos del negocio, puedes
   saltarlo (*Skip*); no hace falta activar la cuenta ni dar datos bancarios.
3. Ir a **Desarrolladores** → **Claves de API**
4. Copiar:
   - **Clave publicable:** `pk_test_...`
   - **Clave secreta:** `sk_test_...`

> ℹ️ Otras pantallas del panel (Perfiles, Facturación, Connect…) no se usan en esta guía.
> Los métodos de pago se administran desde el Dashboard; por eso el código **no**
> envía `payment_method_types` (ver Parte 3 y el apéndice, riesgo 20).

> 🔐 El repositorio es **público**. Las claves solo van en `.env` (que está en
> `.gitignore`) y en las variables de entorno de Render. Nunca en el código,
> capturas, chats ni commits. Usa **únicamente** claves `sk_test_` / `pk_test_`;
> una clave `sk_live_` cobraría dinero real.

### 1.3 Agregar claves al `.env`

```bash
# .env — agregar (nunca subir al repositorio)
STRIPE_SECRET_KEY=sk_test_XXXXXXXXXXXXXXXXXXXXXXXXXX
STRIPE_PUBLISHABLE_KEY=pk_test_XXXXXXXXXXXXXXXXXXXXXXXXXX
STRIPE_WEBHOOK_SECRET=whsec_XXXXXXXXXX   # se obtiene en W15
```

> Pega cada clave justo después del `=`, **sin espacios ni comillas**. Django lee el
> `.env` solo al arrancar: después de guardarlo, **detén `runserver` (Ctrl+C) y vuelve
> a iniciarlo**. Verifica sin mostrar las claves:
>
> ```powershell
> python manage.py shell -c "from django.conf import settings as s; print(s.STRIPE_SECRET_KEY[:8], s.STRIPE_PUBLISHABLE_KEY[:8])"
> ```
>
> Debe imprimir `sk_test_ pk_test_`.

### 1.4 Agregar configuración en `core/settings.py`

```python
# core/settings.py — agregar al final (antes de JAZZMIN_SETTINGS):

# ── STRIPE (Pasarela de pago) ──────────────────────────────────────────────
# Default vacío a propósito: si falta la variable, el checkout lo detecta y
# muestra un error controlado en lugar de intentar cobrar con una clave falsa.
STRIPE_SECRET_KEY      = env('STRIPE_SECRET_KEY',      default='')
STRIPE_PUBLISHABLE_KEY = env('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_WEBHOOK_SECRET  = env('STRIPE_WEBHOOK_SECRET',  default='')
```

> `core/settings_prod.py` hereda de `settings.py` (`from .settings import *`),
> por lo que **no hay que tocarlo**: basta con definir las variables en Render.

### 1.5 Actualizar `.env.example`

Verifica que existan **las tres** líneas (con valores de ejemplo, nunca reales):

```bash
STRIPE_SECRET_KEY=sk_test_TU_CLAVE_SECRETA_AQUI
STRIPE_PUBLISHABLE_KEY=pk_test_TU_CLAVE_PUBLICABLE_AQUI
STRIPE_WEBHOOK_SECRET=whsec_TU_WEBHOOK_SECRET_AQUI
```

### 1.6 Variables en Render (hazlo ahora, evita sorpresas en el deploy)

En Render → tu servicio → **Environment** agrega `STRIPE_SECRET_KEY` y
`STRIPE_PUBLISHABLE_KEY` (claves **de prueba**). `STRIPE_WEBHOOK_SECRET` se
agrega en W15. Sin las dos primeras, el checkout en Render mostrará
"El pago en línea no está disponible" (comportamiento esperado, no un error 500).

---

## PARTE 2 — Funciones Auxiliares del Checkout (15 min)

### 2.1 ¿Por qué separar la lógica en funciones auxiliares?

```
CheckoutView sin separación → función de 80 líneas difícil de testear
CheckoutView con separación → cada función tiene UNA responsabilidad:
    validar_carrito()         → revalidar precio/stock/activo contra la BD
    calcular_totales()        → matemática del IVA
    a_centavos()              → Decimal → entero que exige Stripe
    obtener_o_crear_cliente() → vincular User con Cliente del ERP
    crear_pedido_pendiente()  → número de pedido único, sin colisiones
    armar_items()             → subtotal por producto (precio × cantidad)
    dentro_del_limite()       → limitar intentos por usuario (anti-abuso)
    checkout()                → orquestar todo
    _pago_verificado()        → preguntar a Stripe si el pago ocurrió (views.py)
```

> 🔎 **Principio de esta parte: el carrito de la sesión NO es fuente de verdad.**
> Guarda el precio y la cantidad del momento en que se agregó el producto. Si el
> precio cambia, el producto se desactiva o se agota después, el checkout
> cobraría datos viejos. Por eso `validar_carrito()` vuelve a leer la BD.

---

### 2.2 Crear `catalogo/checkout_utils.py`

```python
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
```

---

## PARTE 3 — `CheckoutView`, `pago_exitoso` y `pago_error` (25 min)

### 3.1 Agregar imports y configurar Stripe en `catalogo/views.py`

`views.py` ya importa `messages`, `get_object_or_404`, `redirect` y `render`.
Agrega al bloque de imports:

```python
# catalogo/views.py — agregar imports al inicio:
import logging

import stripe
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404

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

logger = logging.getLogger(__name__)

# Claves de sesión del checkout
SESSION_PEDIDOS = 'pedidos_checkout'   # ids de pedidos creados en ESTA sesión
SESSION_ACTIVO  = 'checkout_activo'    # {'pedido_id': n, 'firma': '...'}
SESSION_INTENTS = 'intents_checkout'   # {'<pedido_id>': 'pi_...'} para verificar

# Límite de intentos de pago por usuario (anti-abuso): 10 cada 10 minutos
MAX_INTENTOS_CHECKOUT = 10
VENTANA_INTENTOS      = 600

# Configurar la clave secreta de Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY
```

---

### 3.2 Agregar `checkout`, `pago_exitoso` y `pago_error` a `catalogo/views.py`

```python
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
            pedido   = crear_pedido_pendiente(cliente, totales['total'])
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
```

> 💡 **Por qué `except Exception` y no solo `StripeError`:** si la BD falla
> *después* de crear el Pedido o Stripe devuelve algo inesperado, el usuario
> debe ver una pantalla controlada (no un error 500) y el pedido huérfano debe
> quedar `cancelado`. El detalle técnico se registra con `logger.exception`.

---

## PARTE 4 — Template `checkout.html` con Stripe.js (25 min)

### 4.1 Crear `catalogo/templates/catalogo/checkout.html`

> ⚠️ **Ubicación y nombre exactos.** Guarda este archivo (y los de la Parte 5)
> dentro de `catalogo\templates\catalogo\`, no en `catalogo\`, y con extensión
> `.html` (no `.htm`). Si no, Django lanza
> `TemplateDoesNotExist at /catalogo/checkout/`. Verifica con:
>
> ```cmd
> dir catalogo\templates\catalogo
> ```
>
> Deben aparecer `checkout.html`, `pago_exitoso.html` y `pago_error.html`.

```html
{% extends "base.html" %}
{% block title %}Checkout · Proceso de pago{% endblock %}

{% block extra_css %}
<style>
    /* Estilos para el Card Element de Stripe */
    #card-element {
        background: var(--clr-surface);
        border: 1.5px solid var(--clr-border);
        border-radius: 8px;
        padding: .75rem 1rem;
        transition: border-color .2s;
    }
    #card-element.StripeElement--focus {
        border-color: var(--clr-sky);
        box-shadow: 0 0 0 3px rgba(74,144,217,.18);
    }
    #card-element.StripeElement--invalid {
        border-color: var(--clr-danger);
    }
    #card-errors {
        color: var(--clr-danger);
        font-size: .85rem;
        margin-top: .4rem;
        min-height: 1.2rem;
    }
    #submit-btn:disabled {
        opacity: .7;
        cursor: not-allowed;
    }
</style>
{% endblock %}

{% block content %}
<div class="erp-page-title">
    <h2>💳 Proceso de pago</h2>
    <a href="{% url 'catalogo:carrito' %}"
       class="btn-erp-primary ms-auto">← Volver al carrito</a>
</div>

<div class="row g-4">

    <!-- Resumen del pedido -->
    <div class="col-md-5">
        <div class="erp-card">
            <div class="erp-card-header">🛍️ Resumen de tu pedido</div>
            <table style="width:100%;border-collapse:collapse;margin-top:.5rem;">
                {% for item in items %}
                <tr>
                    <td style="padding:.4rem 0;font-size:.9rem;">
                        {{ item.nombre }}
                        <span style="color:var(--clr-muted);
                                     font-size:.82rem;">
                            × {{ item.cantidad }}
                        </span>
                    </td>
                    <td style="text-align:right;font-weight:600;
                               font-size:.9rem;padding:.4rem 0;">
                        ${{ item.subtotal }}
                    </td>
                </tr>
                {% endfor %}
                <tr style="border-top:1px solid var(--clr-border);">
                    <td style="padding:.5rem 0;color:var(--clr-muted);
                               font-size:.88rem;">
                        Subtotal
                    </td>
                    <td style="text-align:right;color:var(--clr-muted);
                               font-size:.88rem;">
                        ${{ totales.subtotal }}
                    </td>
                </tr>
                <tr>
                    <td style="padding:.3rem 0;color:var(--clr-muted);
                               font-size:.88rem;">
                        IVA ({{ totales.iva_pct }}%)
                    </td>
                    <td style="text-align:right;color:var(--clr-muted);
                               font-size:.88rem;">
                        ${{ totales.iva_monto }}
                    </td>
                </tr>
                <tr style="border-top:2px solid var(--clr-gold);">
                    <td style="padding:.6rem 0;font-weight:700;font-size:1rem;">
                        TOTAL
                    </td>
                    <td style="text-align:right;font-weight:700;
                               font-size:1.2rem;color:var(--clr-gold);">
                        ${{ totales.total }}
                    </td>
                </tr>
            </table>
        </div>

        {% if pedido %}
        <div class="erp-alert-info" style="margin-top:1rem;">
            <strong>Pedido creado:</strong> {{ pedido.numero_pedido }}<br>
            <small style="color:var(--clr-muted);">
                Completa el pago para confirmar tu pedido.
            </small>
        </div>
        {% endif %}
    </div>

    <!-- Formulario de pago -->
    <div class="col-md-7">
        <div class="erp-card">
            <div class="erp-card-header">🔒 Datos de pago</div>

            {% if client_secret %}
            <!-- Formulario de tarjeta con Stripe.js -->
            <p style="color:var(--clr-muted);font-size:.85rem;margin-bottom:1rem;">
                Tus datos de pago son procesados de forma segura por Stripe.
                Nunca pasan por nuestros servidores.
            </p>

            <div class="mb-4">
                <label class="erp-label">Número de tarjeta</label>
                <div id="card-element"></div>
                <div id="card-errors" role="alert"></div>
            </div>

            <button id="submit-btn" class="btn-erp-gold"
                    style="width:100%;padding:.6rem;font-size:1rem;">
                🔐 Confirmar pago de ${{ totales.total }}
            </button>

            <p style="text-align:center;margin-top:.75rem;
                      color:var(--clr-muted);font-size:.78rem;">
                Tarjeta de prueba: <code>4242 4242 4242 4242</code>
                · cualquier fecha futura · cualquier CVC
            </p>

            {% else %}
            <!-- GET: iniciar proceso con POST -->
            <p style="margin-bottom:1.5rem;color:var(--clr-muted);">
                Haz clic en "Proceder al pago" para generar
                tu pedido e introducir los datos de tu tarjeta.
            </p>
            <form method="post">
                {% csrf_token %}
                <button type="submit" class="btn-erp-gold"
                        style="width:100%;padding:.6rem;font-size:1rem;">
                    Proceder al pago →
                </button>
            </form>
            {% endif %}
        </div>
    </div>

</div>
{% endblock %}

{% block extra_js %}
{% if client_secret %}
{# json_script escapa el valor de forma segura (no se concatena en el JS) #}
{{ client_secret|json_script:"stripe-client-secret" }}
{{ publishable_key|json_script:"stripe-publishable-key" }}
<script src="https://js.stripe.com/v3/"></script>
<script>
(function () {
    'use strict';

    const leer = (id) => JSON.parse(document.getElementById(id).textContent);
    const stripe       = Stripe(leer('stripe-publishable-key'));
    const clientSecret = leer('stripe-client-secret');
    const urlExito     = "{% url 'catalogo:pago_exitoso' pedido.pk %}";
    const elements     = stripe.elements();

    // Crear el Card Element con estilos AzulERP
    const card = elements.create('card', {
        style: {
            base: {
                fontFamily: "'Inter', 'Segoe UI', sans-serif",
                fontSize: '15px',
                color: getComputedStyle(document.documentElement)
                            .getPropertyValue('--clr-text').trim() || '#1A1A2E',
                '::placeholder': { color: '#8AA0B8' },
            },
            invalid: { color: '#C0392B', iconColor: '#C0392B' },
        },
    });
    card.mount('#card-element');

    const errorDiv = document.getElementById('card-errors');

    // Mostrar errores en tiempo real (p. ej. número inválido)
    card.on('change', function (event) {
        errorDiv.textContent = event.error ? event.error.message : '';
    });

    // Manejar el clic del botón de pago
    const btn           = document.getElementById('submit-btn');
    const textoOriginal = btn.textContent;
    btn.addEventListener('click', async function () {
        btn.disabled    = true;                 // evita doble clic = doble cobro
        btn.textContent = '⏳ Procesando…';

        const { error, paymentIntent } = await stripe.confirmCardPayment(
            clientSecret,
            { payment_method: { card: card } }
        );

        if (error) {
            // Tarjeta rechazada, 3D Secure fallido, etc.
            errorDiv.textContent = error.message;
            btn.disabled    = false;
            btn.textContent = textoOriginal;
        } else if (paymentIntent.status === 'succeeded' ||
                   paymentIntent.status === 'processing') {
            // 'processing': Stripe aún confirma; el webhook (W15) cerrará el ciclo
            window.location.href = urlExito;
        } else {
            // Cualquier otro estado: no dejar el botón bloqueado para siempre
            errorDiv.textContent =
                'El pago no se completó (estado: ' + paymentIntent.status + '). ' +
                'Intenta de nuevo.';
            btn.disabled    = false;
            btn.textContent = textoOriginal;
        }
    });
})();
</script>
{% endif %}
{% endblock %}
```

> 💡 **¿Por qué no usar `{% widthratio %}` para el subtotal?** `widthratio`
> sirve para calcular anchos de barras (`a / b × c`), no para multiplicar.
> Convierte su último argumento a entero, y el precio del carrito está guardado
> como texto (`"123.45"`), así que falla con
> `TemplateSyntaxError: widthratio final argument must be a number`. Además
> redondea el resultado y se pierden los centavos. Los templates de Django no
> multiplican: el subtotal se calcula en Python con `armar_items()` (Parte 2.2)
> y la vista lo envía como `items`.

---

## PARTE 5 — Templates `pago_exitoso.html` y `pago_error.html` (15 min)

### 5.1 `catalogo/templates/catalogo/pago_exitoso.html`

> ℹ️ Esta pantalla dice "pago **recibido**", no "pedido confirmado": en W14 el
> estado del pedido sigue en `Pendiente de pago` hasta que el webhook de W15
> lo cambie a `Pago confirmado`. Prometer "confirmado" antes sería engañoso.
> Tampoco se enlaza a `ventas:detalle`: esa URL espera el id de una **Venta**
> (otro modelo) y mostraría la venta equivocada con el mismo número.

```html
{% extends "base.html" %}
{% block title %}Pago recibido{% endblock %}

{% block content %}
<div style="display:flex;justify-content:center;align-items:center;
            min-height:60vh;">
    <div class="erp-card" style="max-width:520px;text-align:center;">
        <div style="font-size:4rem;margin-bottom:1rem;">✅</div>
        <h2 style="font-family:'Playfair Display',serif;
                   color:var(--clr-navy);margin:0 0 .5rem;">
            ¡Pago recibido!
        </h2>
        <p style="color:var(--clr-muted);margin-bottom:1.5rem;">
            Estamos verificando tu pago con el banco. El estado de tu pedido
            se actualizará en unos instantes.
        </p>

        <div class="erp-card" style="background:var(--clr-ice);
                                     border-left:5px solid var(--clr-ok);
                                     text-align:left;margin-bottom:1.5rem;">
            <dl style="margin:0;">
                <dt class="erp-label">Número de pedido</dt>
                <dd style="font-size:1.2rem;font-weight:700;
                           color:var(--clr-navy);margin:.2rem 0 1rem;">
                    {{ pedido.numero_pedido }}
                </dd>

                <dt class="erp-label">Total</dt>
                <dd style="font-size:1.2rem;font-weight:700;
                           color:var(--clr-gold);margin:.2rem 0 1rem;">
                    ${{ pedido.total_pagado }}
                </dd>

                <dt class="erp-label">Estado</dt>
                <dd style="margin:.2rem 0 0;">
                    <span class="badge-erp-active">
                        {{ pedido.get_estado_display }}
                    </span>
                </dd>
            </dl>
        </div>

        <a href="{% url 'catalogo:catalogo' %}" class="btn-erp-primary">
            Seguir comprando
        </a>
    </div>
</div>
{% endblock %}
```

---

### 5.2 `catalogo/templates/catalogo/pago_error.html`

```html
{% extends "base.html" %}
{% block title %}Error en el pago{% endblock %}

{% block content %}
<div style="display:flex;justify-content:center;align-items:center;
            min-height:60vh;">
    <div class="erp-card" style="max-width:480px;text-align:center;">
        <div style="font-size:4rem;margin-bottom:1rem;">❌</div>
        <h2 style="font-family:'Playfair Display',serif;
                   color:var(--clr-danger);margin:0 0 .5rem;">
            Error en el pago
        </h2>
        <p style="color:var(--clr-muted);margin-bottom:1.5rem;">
            No pudimos procesar tu pago. Tu carrito sigue intacto —
            puedes intentarlo de nuevo.
        </p>

        <div class="erp-alert-danger" style="margin-bottom:1.5rem;
                                             text-align:left;">
            <strong>Posibles causas:</strong>
            <ul style="margin:.5rem 0 0;padding-left:1.2rem;font-size:.9rem;">
                <li>Fondos insuficientes en la tarjeta</li>
                <li>Datos de tarjeta incorrectos</li>
                <li>Tarjeta bloqueada por el banco</li>
                <li>Problema temporal de conexión con Stripe</li>
            </ul>
        </div>

        <div class="d-flex gap-2 justify-content-center">
            <a href="{% url 'catalogo:carrito' %}"
               class="btn-erp-primary">
                ← Volver al carrito
            </a>
            <a href="{% url 'catalogo:checkout' %}"
               class="btn-erp-gold">
                Reintentar pago
            </a>
        </div>
    </div>
</div>
{% endblock %}
```

---

## PARTE 6 — Actualizar `catalogo/urls.py` (10 min)

```python
# catalogo/urls.py — versión W14 (reemplaza el placeholder de W13)
"""URLs del módulo catálogo — W14."""
from django.urls import path

from . import views

app_name = 'catalogo'

urlpatterns = [
    # Catálogo público
    path('',
         views.CatalogoView.as_view(),
         name='catalogo'),

    # Carrito (W13)
    path('carrito/',
         views.ver_carrito,
         name='carrito'),
    path('carrito/agregar/<int:producto_id>/',
         views.agregar_al_carrito,
         name='agregar'),
    path('carrito/remover/<int:producto_id>/',
         views.remover_del_carrito,
         name='remover'),
    path('carrito/actualizar/<int:producto_id>/',
         views.actualizar_cantidad,
         name='actualizar'),
    path('carrito/vaciar/',
         views.vaciar_carrito,
         name='vaciar'),

    # Checkout con Stripe (W14)
    path('checkout/',
         views.checkout,
         name='checkout'),
    path('pago-exitoso/<int:pedido_id>/',
         views.pago_exitoso,
         name='pago_exitoso'),
    path('pago-error/',
         views.pago_error,
         name='pago_error'),
]
```

### Verificar en el navegador

```cmd
python manage.py check
python manage.py runserver
```

**Flujo de prueba manual (con claves reales de Stripe sandbox):**

```
1. Agregar 2 productos al carrito desde /catalogo/
2. Ir a /catalogo/carrito/ → verificar items y total
3. Clic en "Proceder al pago" → login si no está autenticado
4. GET /catalogo/checkout/ → muestra resumen + botón "Proceder"
5. POST /catalogo/checkout/ → Card Element de Stripe aparece
6. Ingresar: 4242 4242 4242 4242 · 12/26 · 123 · CP: 12345
7. Clic en "Confirmar pago" → procesando…
8. Redirige a /catalogo/pago-exitoso/<id>/ → ✅ confirmación
9. Carrito queda vacío
10. Verificar en /admin/ que el Pedido existe con estado 'pendiente'
    (cambia a 'pagado' en W15 vía webhook)
11. Verificar en el Dashboard de Stripe (modo prueba → Pagos / Transacciones)
    que aparece el cobro de prueba
```

**Pruebas de seguridad (hazlas, no solo la compra feliz):**

```
A. Pago sin completar: haz POST al checkout (aparece el Card Element) y, SIN pagar,
   abre a mano /catalogo/pago-exitoso/<id>/ → debe devolverte al checkout con un
   aviso y el carrito debe seguir lleno.
B. Pedido ajeno: con otro usuario abre /catalogo/pago-exitoso/<id>/ de un pedido
   que no creó → 404.
C. Tarjeta rechazada 4000 0000 0000 9995 → error bajo el campo y botón reactivado.
D. 3D Secure 4000 0025 0000 3155 → ventana de Stripe; elige "Complete".
E. Recargar el campo de tarjeta varias veces → en /admin/ no se duplican pedidos.
F. Cambiar el precio del producto en /admin/ con el carrito lleno y pulsar
   "Proceder" → aviso del precio nuevo, sin cobrar en silencio.
```

### Si el pago falla: dónde mirar

La pantalla solo muestra un mensaje genérico a propósito. **El detalle real está en la
terminal donde corre `runserver`** (línea `Checkout: fallo al iniciar el pago` seguida
del error de Stripe).

| Lo que ves | Causa probable | Solución |
|---|---|---|
| "El pago en línea no está disponible" (en pantalla) | Faltan las claves o no empiezan con `sk_` / `pk_` | Revisa el `.env` y reinicia `runserver` |
| `AuthenticationError` / `Invalid API Key` (terminal) | Clave mal copiada, con espacios o de otra cuenta | Cópiala de nuevo desde Desarrolladores → Claves de API |
| `InvalidRequestError … payment_method_types … no longer supported` | Código con el parámetro antiguo | Usa `automatic_payment_methods` (Parte 3) |
| `InvalidRequestError … amount must be at least…` | Total menor al mínimo de Stripe (≈10 MXN) | Prueba con un producto de mayor precio |
| `ConnectionError` | Sin internet | Reintenta; los tests no la necesitan (usan mock) |
| HTTP 429 / "Demasiados intentos" | Pasaste de 10 intentos en 10 min | Espera unos minutos |

---

## PARTE 7 — Tests W14 (20 min)

### 7.1 ¿Por qué usar `unittest.mock.patch`?

```python
# SIN mock: los tests llaman a la API real de Stripe
# → requieren internet en el aula
# → son lentos (latencia de red)
# → dependen de que las claves de Stripe estén configuradas

# CON mock: reemplazamos stripe.PaymentIntent.create con un objeto falso
# → sin internet, sin claves
# → rápidos (sin latencia)
# → predecibles (sabemos exactamente qué devuelve)

from unittest.mock import patch, MagicMock

@patch('catalogo.views.stripe.PaymentIntent.create')
def test_post_checkout(self, mock_stripe):
    mock_stripe.return_value = MagicMock(client_secret='pi_test_secret')
    # Ahora stripe.PaymentIntent.create() devuelve el mock
    r = self.client.post(...)
```

---

### 7.2 Crear `tests/test_w14_checkout.py`

```python
"""Suite de pruebas W14 — Checkout y proceso de pago con Stripe.

Usa unittest.mock.patch para simular stripe.PaymentIntent.create
sin requerir claves reales ni conexión a internet.

Ejecutar con:
    python manage.py test tests.test_w14_checkout --verbosity=2

Resultado esperado:
    Ran 28 tests in X.XXXs
    OK
"""
from decimal import Decimal
from unittest.mock import MagicMock, patch

import stripe
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from catalogo.checkout_utils import (
    a_centavos, crear_pedido_pendiente, obtener_o_crear_cliente,
)
from clientes.models        import Cliente
from configuracion.models   import ConfiguracionERP
from productos.models       import Categoria, Producto
from ventas.models          import Pedido

# Claves falsas SOLO para tests: el checkout exige que empiecen con sk_/pk_.
# (No se usa ninguna clave real ni se llama a Stripe: PaymentIntent.create
# está mockeado.)
CLAVES_FALSAS = dict(STRIPE_SECRET_KEY='sk_test_fake',
                     STRIPE_PUBLISHABLE_KEY='pk_test_fake')


def _setup_carrito(client, producto):
    """Agrega un producto al carrito de la sesión del test client."""
    client.post(
        reverse('catalogo:agregar', args=[producto.pk]),
        {'cantidad': 2}
    )


def _total_esperado(subtotal: Decimal) -> Decimal:
    iva = ConfiguracionERP.get_instance().iva_porcentaje / 100
    return (subtotal + subtotal * iva).quantize(Decimal('0.01'))


class CheckoutAutenticacionTest(TestCase):
    """Tests de autenticación del checkout."""

    def test_checkout_sin_auth_redirige_a_login(self):
        """GET /catalogo/checkout/ sin login → 302 a /accounts/login/."""
        r = self.client.get(reverse('catalogo:checkout'))
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r['Location'])

    def test_checkout_carrito_vacio_redirige_a_catalogo(self):
        """Checkout con carrito vacío → redirect al catálogo."""
        user = User.objects.create_user('empty', password='pass')
        self.client.force_login(user)
        r = self.client.get(reverse('catalogo:checkout'))
        self.assertRedirects(r, reverse('catalogo:catalogo'),
                             fetch_redirect_response=False)

    def test_checkout_get_con_carrito_devuelve_200(self):
        """GET /catalogo/checkout/ con carrito → 200 y NO crea Pedido."""
        ConfiguracionERP.get_instance()
        cat  = Categoria.objects.create(nombre='Cat')
        prod = Producto.objects.create(
            nombre='P', precio=Decimal('100.00'),
            stock=5, categoria=cat
        )
        user = User.objects.create_user('userco', password='pass',
                                        email='userco@test.com')
        self.client.force_login(user)
        _setup_carrito(self.client, prod)
        r = self.client.get(reverse('catalogo:checkout'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Pedido.objects.count(), 0)


@override_settings(**CLAVES_FALSAS)
class CheckoutPagoTest(TestCase):
    """Tests del proceso POST de checkout con Stripe mockeado."""

    def setUp(self):
        cache.clear()
        ConfiguracionERP.get_instance()
        cat       = Categoria.objects.create(nombre='Cat')
        self.prod = Producto.objects.create(
            nombre='Laptop', precio=Decimal('500.00'),
            stock=5, categoria=cat
        )
        self.user = User.objects.create_user(
            'payer', password='pass', email='payer@test.com'
        )
        self.client.force_login(self.user)
        _setup_carrito(self.client, self.prod)   # 2 × 500 = 1000

    @patch('catalogo.views.stripe.PaymentIntent.create')
    def test_post_checkout_crea_pedido(self, mock_pi):
        """POST /catalogo/checkout/ → se crea un Pedido en BD."""
        mock_pi.return_value = MagicMock(id='pi_test_1', client_secret='pi_test_secret')
        self.client.post(reverse('catalogo:checkout'))
        self.assertEqual(Pedido.objects.count(), 1)

    @patch('catalogo.views.stripe.PaymentIntent.create')
    def test_post_checkout_pedido_estado_pendiente(self, mock_pi):
        """El Pedido creado debe tener estado 'pendiente'."""
        mock_pi.return_value = MagicMock(id='pi_test_1', client_secret='pi_test_secret')
        self.client.post(reverse('catalogo:checkout'))
        self.assertEqual(Pedido.objects.first().estado, 'pendiente')

    @patch('catalogo.views.stripe.PaymentIntent.create')
    def test_post_checkout_calcula_iva(self, mock_pi):
        """El total del Pedido debe incluir el IVA configurado."""
        mock_pi.return_value = MagicMock(id='pi_test_1', client_secret='pi_test_secret')
        self.client.post(reverse('catalogo:checkout'))
        self.assertEqual(Pedido.objects.first().total_pagado,
                         _total_esperado(Decimal('1000.00')))

    @patch('catalogo.views.stripe.PaymentIntent.create')
    def test_post_checkout_crea_cliente_erp(self, mock_pi):
        """Se debe crear (o encontrar) un Cliente ERP para el usuario."""
        mock_pi.return_value = MagicMock(id='pi_test_1', client_secret='pi_test_secret')
        self.client.post(reverse('catalogo:checkout'))
        self.assertTrue(
            Cliente.objects.filter(correo=self.user.email).exists()
        )

    @patch('catalogo.views.stripe.PaymentIntent.create')
    def test_post_checkout_llama_stripe_con_monto_correcto(self, mock_pi):
        """Stripe debe recibir el monto en centavos."""
        mock_pi.return_value = MagicMock(id='pi_test_1', client_secret='pi_test_secret')
        self.client.post(reverse('catalogo:checkout'))
        centavos = int(_total_esperado(Decimal('1000.00')) * 100)
        mock_pi.assert_called_once()
        self.assertEqual(mock_pi.call_args.kwargs['amount'], centavos)

    @patch('catalogo.views.stripe.PaymentIntent.create')
    def test_post_repetido_reutiliza_pedido(self, mock_pi):
        """Recargar / doble POST con el mismo carrito → UN solo Pedido."""
        mock_pi.return_value = MagicMock(id='pi_test_1', client_secret='pi_test_secret')
        self.client.post(reverse('catalogo:checkout'))
        self.client.post(reverse('catalogo:checkout'))
        self.assertEqual(Pedido.objects.count(), 1)

    @patch('catalogo.views.stripe.PaymentIntent.create')
    def test_precio_cambiado_no_se_cobra_en_silencio(self, mock_pi):
        """Si el precio cambia tras agregar al carrito: aviso + sin Pedido;
        al confirmar de nuevo se cobra el precio NUEVO."""
        mock_pi.return_value = MagicMock(id='pi_test_1', client_secret='pi_test_secret')
        Producto.objects.filter(pk=self.prod.pk).update(
            precio=Decimal('600.00'))

        r = self.client.post(reverse('catalogo:checkout'))
        self.assertEqual(r.status_code, 302)           # a revisar el resumen
        self.assertEqual(Pedido.objects.count(), 0)
        mock_pi.assert_not_called()

        self.client.post(reverse('catalogo:checkout'))  # ya revisado
        centavos = int(_total_esperado(Decimal('1200.00')) * 100)
        self.assertEqual(mock_pi.call_args.kwargs['amount'], centavos)

    @patch('catalogo.views.stripe.PaymentIntent.create')
    def test_stock_insuficiente_ajusta_carrito_sin_pedido(self, mock_pi):
        """Stock menor a lo pedido → ajusta carrito, no crea Pedido ni cobra."""
        Producto.objects.filter(pk=self.prod.pk).update(stock=1)
        r = self.client.post(reverse('catalogo:checkout'))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Pedido.objects.count(), 0)
        mock_pi.assert_not_called()
        carrito = self.client.session['carrito']
        self.assertEqual(carrito[str(self.prod.pk)]['cantidad'], 1)

    @patch('catalogo.views.stripe.PaymentIntent.create')
    def test_error_de_stripe_cancela_pedido_nuevo(self, mock_pi):
        """Stripe falla → redirect a pago_error y el Pedido queda 'cancelado'."""
        mock_pi.side_effect = stripe.error.StripeError('boom')
        r = self.client.post(reverse('catalogo:checkout'))
        self.assertRedirects(r, reverse('catalogo:pago_error'),
                             fetch_redirect_response=False)
        self.assertEqual(Pedido.objects.get().estado, 'cancelado')

    @patch('catalogo.views.stripe.PaymentIntent.create')
    def test_error_inesperado_no_filtra_detalle_al_usuario(self, mock_pi):
        """El texto de una excepción interna NO debe mostrarse al usuario."""
        mock_pi.side_effect = Exception('DETALLE-INTERNO-123')
        r = self.client.post(reverse('catalogo:checkout'), follow=True)
        self.assertNotContains(r, 'DETALLE-INTERNO-123')


class PagoExitosoTest(TestCase):
    """Tests de pago_exitoso: autorización + verificación real con Stripe."""

    def setUp(self):
        cache.clear()
        ConfiguracionERP.get_instance()
        cli = Cliente.objects.create(nombre='C', correo='c@t.com')
        self.pedido = Pedido.objects.create(
            numero_pedido='PED-2025-0001', cliente=cli,
            estado='pendiente', total_pagado=Decimal('116.00')
        )
        self.user = User.objects.create_user('dueno', password='pass')
        self.url  = reverse('catalogo:pago_exitoso', args=[self.pedido.pk])

    def _autorizar(self, con_intent=True):
        """Simula que ESTE usuario creó el pedido (y su PaymentIntent)."""
        self.client.force_login(self.user)
        sesion = self.client.session
        sesion['pedidos_checkout'] = [self.pedido.pk]
        if con_intent:
            sesion['intents_checkout'] = {str(self.pedido.pk): 'pi_test_1'}
        sesion['carrito'] = {'1': {'nombre': 'P', 'precio': '100',
                                   'cantidad': 1}}
        sesion.save()

    def _intent(self, status='succeeded', pedido_id=None, amount=11600):
        return MagicMock(
            status=status, amount=amount,
            metadata={'pedido_id': str(pedido_id or self.pedido.pk)})

    def test_sin_login_redirige_a_login(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r['Location'])

    def test_pedido_ajeno_devuelve_404(self):
        """Un usuario NO puede ver un pedido que no creó (cambiando la URL)."""
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.url).status_code, 404)

    @patch('catalogo.views.stripe.PaymentIntent.retrieve')
    def test_pago_verificado_devuelve_200_y_vacia_carrito(self, mock_get):
        mock_get.return_value = self._intent('succeeded')
        self._autorizar()
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(self.client.session.get('carrito', {}), {})

    @patch('catalogo.views.stripe.PaymentIntent.retrieve')
    def test_pago_en_proceso_tambien_se_acepta(self, mock_get):
        mock_get.return_value = self._intent('processing')
        self._autorizar()
        self.assertEqual(self.client.get(self.url).status_code, 200)

    @patch('catalogo.views.stripe.PaymentIntent.retrieve')
    def test_sin_pagar_no_vacia_carrito(self, mock_get):
        """Abrir la URL de éxito SIN haber pagado no sirve de nada."""
        mock_get.return_value = self._intent('requires_payment_method')
        self._autorizar()
        r = self.client.get(self.url)
        self.assertRedirects(r, reverse('catalogo:checkout'),
                             fetch_redirect_response=False)
        self.assertNotEqual(self.client.session.get('carrito', {}), {})

    def test_sin_payment_intent_registrado_no_vacia_carrito(self):
        self._autorizar(con_intent=False)
        r = self.client.get(self.url)
        self.assertRedirects(r, reverse('catalogo:checkout'),
                             fetch_redirect_response=False)
        self.assertNotEqual(self.client.session.get('carrito', {}), {})

    @patch('catalogo.views.stripe.PaymentIntent.retrieve')
    def test_error_de_stripe_al_verificar_no_vacia_carrito(self, mock_get):
        mock_get.side_effect = stripe.error.StripeError('boom')
        self._autorizar()
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 302)
        self.assertNotEqual(self.client.session.get('carrito', {}), {})

    @patch('catalogo.views.stripe.PaymentIntent.retrieve')
    def test_intent_de_otro_pedido_se_rechaza(self, mock_get):
        mock_get.return_value = self._intent('succeeded', pedido_id=999)
        self._autorizar()
        self.assertEqual(self.client.get(self.url).status_code, 302)

    @patch('catalogo.views.stripe.PaymentIntent.retrieve')
    def test_monto_distinto_se_rechaza(self, mock_get):
        mock_get.return_value = self._intent('succeeded', amount=100)
        self._autorizar()
        self.assertEqual(self.client.get(self.url).status_code, 302)

    @patch('catalogo.views.stripe.PaymentIntent.retrieve')
    def test_llegar_a_pago_exitoso_no_marca_pagado(self, mock_get):
        """Solo el webhook (W15) puede pasar el pedido a 'pagado'."""
        mock_get.return_value = self._intent('succeeded')
        self._autorizar()
        self.client.get(self.url)
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'pendiente')


@override_settings(**CLAVES_FALSAS)
class LimiteDeIntentosTest(TestCase):
    """El checkout limita los intentos de pago por usuario."""

    def setUp(self):
        cache.clear()
        ConfiguracionERP.get_instance()
        cat  = Categoria.objects.create(nombre='Cat')
        prod = Producto.objects.create(
            nombre='P', precio=Decimal('500.00'), stock=5, categoria=cat)
        user = User.objects.create_user('spam', password='pass',
                                        email='spam@test.com')
        self.client.force_login(user)
        _setup_carrito(self.client, prod)

    @patch('catalogo.views.stripe.PaymentIntent.create')
    def test_el_intento_11_recibe_429(self, mock_pi):
        mock_pi.return_value = MagicMock(
            id='pi_test_1', client_secret='pi_test_secret')
        url = reverse('catalogo:checkout')
        for _ in range(10):
            self.assertEqual(self.client.post(url).status_code, 200)
        r = self.client.post(url)
        self.assertEqual(r.status_code, 429)
        self.assertEqual(mock_pi.call_count, 10)    # el 11.º no llegó a Stripe

    def test_dentro_del_limite_cuenta_y_corta(self):
        from catalogo.checkout_utils import dentro_del_limite
        resultados = [dentro_del_limite('prueba:1', maximo=3) for _ in range(5)]
        self.assertEqual(resultados, [True, True, True, False, False])


class CheckoutUtilsTest(TestCase):
    """Tests de las funciones auxiliares."""

    def test_numero_pedido_no_se_repite_tras_borrar(self):
        cli = Cliente.objects.create(nombre='C', correo='u@t.com')
        crear_pedido_pendiente(cli, Decimal('10.00'))
        p2 = crear_pedido_pendiente(cli, Decimal('10.00'))
        Pedido.objects.exclude(pk=p2.pk).delete()      # se borra el primero
        p3 = crear_pedido_pendiente(cli, Decimal('10.00'))
        self.assertNotEqual(p3.numero_pedido, p2.numero_pedido)
        self.assertTrue(p3.numero_pedido.endswith('-0003'))

    def test_a_centavos_redondea_hacia_arriba(self):
        self.assertEqual(a_centavos(Decimal('10.005')), 1001)
        self.assertEqual(a_centavos(Decimal('1160.00')), 116000)

    def test_no_modifica_cliente_existente(self):
        """Un usuario con el correo de un Cliente real NO puede renombrarlo."""
        Cliente.objects.create(nombre='Cliente Real', correo='real@t.com')
        intruso = User.objects.create_user(
            'intruso', email='REAL@t.com', first_name='Otro', password='x')
        cliente = obtener_o_crear_cliente(intruso)
        self.assertEqual(cliente.nombre, 'Cliente Real')
        self.assertEqual(Cliente.objects.count(), 1)
```

### 7.3 Ejecutar los tests

```powershell
python manage.py test tests.test_w14_checkout --verbosity=2
```

**Resultado esperado:** `Ran 28 tests in X.XXXs` · `OK`

> *Si tu implementación difiere ligeramente, el número puede variar; lo
> importante es que cubra los 5 grupos: autenticación, pago con mock,
> autorización y verificación de `pago_exitoso`, límite de intentos y funciones auxiliares.*

### 7.4 Suite acumulada

```powershell
python manage.py test tests --verbosity=0
```

**Resultado esperado:** `Ran (N + 28) tests … OK`. Con la base de referencia
(204): **232 tests, skipped=5**.

---

## CIERRE — Commit y Respaldo (10 min)

### Actualizar `sprint4_planning.md`

```markdown
## Sprint Backlog — actualización W14

| Tarea | Estado |
|---|---|
| Catálogo + carrito + context processor | ✅ W13 |
| pip install stripe | ✅ W14 |
| STRIPE_* en settings.py y .env | ✅ W14 |
| checkout_utils.py (calcular_totales, obtener_cliente) | ✅ W14 |
| CheckoutView (GET/POST) con PaymentIntent | ✅ W14 |
| Template checkout.html con Stripe.js Card Element | ✅ W14 |
| pago_exitoso: vaciar carrito + template | ✅ W14 |
| pago_error: template con causas y reintento | ✅ W14 |
| Tests con unittest.mock.patch | ✅ W14 |
| Webhooks + actualizar estado pedido | ⏳ W15 |
| Descontar stock al confirmar pago | ⏳ W15 |
```

### Commit de cierre W14 (SIN push)

> 🛑 **Reglas de este cierre** (distintas a las versiones anteriores de la guía):
> - **No uses `git add .`**: en tu carpeta puede haber archivos sueltos
>   (`guides/`, notas, `.env`…) que no deben entrar al commit. Agrega solo los
>   archivos de W14, por nombre.
> - **No hagas `git push origin main`.** El trabajo se queda en la rama `w14`.
>   El push y el merge a `main` los decides tú después de validar.
> - Antes de confirmar, **revisa que no se cuele ninguna clave** (el repositorio
>   es público).

```powershell
git branch --show-current          # debe decir: w14

git add catalogo/checkout_utils.py catalogo/views.py catalogo/urls.py
git add catalogo/templates/catalogo/checkout.html
git add catalogo/templates/catalogo/pago_exitoso.html
git add catalogo/templates/catalogo/pago_error.html
git add core/settings.py requirements.txt .env.example
git add tests/test_w14_checkout.py sprint4_planning.md

git status --short                 # solo deben aparecer archivos de la lista

# Búsqueda de claves de Stripe en lo que se va a subir (no debe imprimir nada):
git diff --cached | Select-String -Pattern 'sk_(test|live)_[A-Za-z0-9]{10,}|whsec_[A-Za-z0-9]{10,}|pk_live_'

git commit -m "Sprint 4 W14: checkout Stripe sandbox + PaymentIntent + 224 tests OK"
```

Si la búsqueda de claves imprime algo, **no hagas el commit**: quita esa línea
del archivo (`git restore --staged <archivo>`), muévela a `.env` y repite.

### Ejecutar `finalizar_sesion.bat`

```powershell
E:\finalizar_sesion.bat
```

---

## CHECKLIST FINAL W14

### Técnico

```
STRIPE SDK
[ ] pip install "stripe==16.1.0" → sin errores
[ ] requirements.txt editado A MANO (UTF-8) con stripe==16.1.0 — sin pip freeze
[ ] STRIPE_SECRET_KEY / STRIPE_PUBLISHABLE_KEY en .env y settings.py (default '')
[ ] .env.example con las 3 variables (valores de ejemplo, no reales)
[ ] Variables STRIPE_* de PRUEBA agregadas en Render
[ ] stripe.api_key = settings.STRIPE_SECRET_KEY en views.py

CHECKOUT UTILS
[ ] validar_carrito(): revalida precio, stock y activo contra la BD
[ ] calcular_totales(): precio str → Decimal, IVA con ROUND_HALF_UP
[ ] a_centavos(): ROUND_HALF_UP (no int(monto*100))
[ ] dentro_del_limite(): contador en caché por usuario (10 intentos / 10 min)
[ ] obtener_o_crear_cliente(): busca con correo__iexact y NO modifica clientes existentes
[ ] crear_pedido_pendiente(): número = MAYOR del año + 1, con reintento (no count()+1)
[ ] armar_items(): subtotal por línea = Decimal(precio) × cantidad

CHECKOUTVIEW
[ ] Sin auth → redirect /accounts/login/?next=/catalogo/checkout/
[ ] Carrito vacío → redirect /catalogo/ con mensaje warning
[ ] Si el carrito cambió (precio/stock) → aviso + redirect, NO se cobra en silencio
[ ] Sin claves Stripe → mensaje controlado (no error 500)
[ ] GET → template sin client_secret y SIN crear Pedido
[ ] POST → crea Pedido 'pendiente' + PaymentIntent; doble POST reutiliza el pedido
[ ] PaymentIntent con automatic_payment_methods (sin payment_method_types)
[ ] Intento 11 en 10 min → HTTP 429 sin llamar a Stripe
[ ] El id del PaymentIntent se guarda en la sesión (intents_checkout)
[ ] idempotency_key incluye pedido y monto
[ ] Error de Stripe/imprevisto → pedido nuevo 'cancelado', pago_error, detalle solo en el log

PAGO_EXITOSO
[ ] @login_required y solo para pedidos creados en la sesión (si no → 404)
[ ] Verifica con Stripe (retrieve): estado succeeded/processing, pedido y monto correctos
[ ] Sin pago verificado → redirect al checkout y el carrito NO se vacía
[ ] No marca el pedido como pagado y su texto dice "pago recibido"
[ ] Sin enlace a ventas:detalle (era otro modelo)

TEMPLATES
[ ] Templates en catalogo/templates/catalogo/ con extensión .html
[ ] checkout.html: client_secret y publishable_key vía json_script (no concatenados)
[ ] checkout.html: URL de éxito con {% url %}; maneja succeeded / processing / otros estados
[ ] checkout.html: botón deshabilitado durante el pago y re-habilitado si falla
[ ] checkout.html: Stripe.js CDN solo cuando client_secret existe

URLS
[ ] checkout/, pago-exitoso/<int:pedido_id>/, pago-error/ (reemplazan el placeholder)

TESTS (con mock)
[ ] test tests.test_w14_checkout → 28 tests OK
[ ] test tests → N + 28 OK acumulados (referencia: 232, skipped=5)
[ ] Clases decoradas con @override_settings(CLAVES_FALSAS) donde se hace POST
[ ] test: pedido ajeno → 404 · precio cambiado → sin cobro en silencio
[ ] test: error de Stripe → pedido cancelado · doble POST → un solo pedido
[ ] test: pago_exitoso sin pagar / intent ajeno / monto distinto → no vacía el carrito
[ ] test: el intento 11 del checkout recibe 429
[ ] Pruebas de seguridad A–F de la Parte 6 hechas en el navegador

GIT (rama w14, SIN push)
[ ] sprint4_planning.md actualizado
[ ] git add por archivo (NO git add .) y git status revisado
[ ] Búsqueda de claves en git diff --cached → sin resultados
[ ] .env NO aparece en git status
[ ] Commit en la rama w14 · push y merge a main: decisión del desarrollador
[ ] finalizar_sesion.bat → archivos en USB
```

---

## DIAGRAMA: Flujo completo del checkout (W14)

```
USUARIO → GET /catalogo/checkout/
    │ @login_required → sin auth → /accounts/login/
    │ carrito vacío → /catalogo/
    ▼
checkout(request) GET
    ├── calcular_totales(carrito)
    │       → subtotal + IVA + total
    └── render checkout.html (sin client_secret)
            → botón "Proceder al pago"

USUARIO → POST /catalogo/checkout/
    ▼
checkout(request) POST
    ├── dentro_del_limite('checkout:<user>')  → si se pasó: HTTP 429
    ├── validar_carrito() → si algo cambió: aviso y NO se cobra
    ├── obtener_o_crear_cliente(request.user)
    │       → Cliente(correo=user.email)
    ├── crear_pedido_pendiente(...)  (o reutiliza el pendiente del mismo carrito)
    │       → Pedido pk=5, numero_pedido='PED-2025-0005'
    ├── stripe.PaymentIntent.create(
    │       amount=116000,          ← centavos (1160.00 MXN × 100)
    │       currency='mxn',
    │       automatic_payment_methods={'enabled': True, 'allow_redirects': 'never'},
    │       metadata={pedido_id: 5},
    │       idempotency_key='pedido-5-116000'
    │   )
    │       → {id: 'pi_xxx', client_secret: 'pi_xxx_secret_yyy'}
    ├── sesión['intents_checkout']['5'] = 'pi_xxx'
    └── render checkout.html (CON client_secret)
            → Stripe.js monta el Card Element

USUARIO ingresa: 4242 4242 4242 4242 · 12/26 · 123
    ▼
stripe.confirmCardPayment(client_secret, {payment_method: {card: cardEl}})
    │
    ├── error → mostrar mensaje en #card-errors + habilitar botón
    │
    └── succeeded → redirect /catalogo/pago-exitoso/5/
            │
            ▼
        pago_exitoso(request, pedido_id=5)
            ├── ¿el pedido es de esta sesión? no → 404
            ├── _pago_verificado(): stripe.PaymentIntent.retrieve('pi_xxx')
            │       status succeeded/processing + pedido + monto correctos
            │       → si no: redirect al checkout, carrito INTACTO
            ├── _guardar_carrito(request, {})  ← vaciar carrito
            └── render pago_exitoso.html
                    → ✅ PED-2025-0005 · $1,160.00 · Pendiente
```

---

## HILO CONDUCTOR → W15

**¿Qué entrega W14?**
El checkout completo con Stripe sandbox: el usuario puede pagar,
el `Pedido` se crea en estado `pendiente` y el carrito se vacía
tras verificar el pago con Stripe. Los tests (con mocks) cubren el flujo completo,
la verificación del pago y el límite de intentos.

**¿Qué abre W15 / Hito M5?**
Stripe llama al webhook para confirmar el pago. W15 implementa
el endpoint `/catalogo/webhook/` que recibe el evento de Stripe,
verifica la firma y actualiza el pedido a estado `pagado`,
descontando el stock de los productos vendidos.

**¿Qué necesita W15 de W14?**

| Artefacto de W14 | Uso en W15 |
|---|---|
| `Pedido.metadata['pedido_id']` en PaymentIntent | W15 lo lee del evento webhook para saber qué pedido actualizar |
| `STRIPE_WEBHOOK_SECRET` (placeholder en .env) | W15 lo configura con `stripe listen` o desde el dashboard |
| `Pedido.estado = 'pendiente'` | W15 lo cambia a `'pagado'` al recibir `payment_intent.succeeded` |
| `Producto.stock` | W15 lo decrementa por las cantidades del pedido |

**Tarea de investigación para W15:**
> Lee la documentación de Stripe sobre webhooks:
> `https://stripe.com/docs/webhooks`
>
> ¿Qué es `stripe.Webhook.construct_event()`?
> ¿Por qué es crítico verificar la firma del webhook?
> ¿Qué sucede si un atacante envía un evento falso al endpoint?

**Pregunta de reflexión:**
> "En W14 creamos el `Pedido` con `estado='pendiente'` cuando el
> usuario hace POST al checkout, ANTES de que Stripe confirme el pago.
> ¿Qué pasaría si el usuario cierra el navegador justo después del POST
> pero antes de que Stripe confirme? ¿El pedido queda en `pendiente`
> para siempre? ¿Cómo lo resolvería W15 con webhooks?"

---

## Referencia rápida de comandos W14

```powershell
# SESIÓN
E:\iniciar_sesion.bat
E:\finalizar_sesion.bat

# DJANGO
python manage.py check
python manage.py runserver

# TESTS (sin claves Stripe reales — usa mock)
python manage.py test tests.test_w14_checkout --verbosity=2
python manage.py test tests --verbosity=0      # N + 20 (referencia: 224)

# STRIPE CLI (para probar webhooks en W15)
# Instalar de: https://stripe.com/docs/stripe-cli
# stripe listen --forward-to localhost:8000/catalogo/webhook/

# GIT (rama w14; sin push ni merge a main)
git branch --show-current
git status --short
git add <archivos de W14, por nombre>
git commit -m "Sprint 4 W14: Stripe checkout + 224 tests OK"
git log --oneline
```

---

## APÉNDICE — Riesgos detectados en la versión original y su corrección

Esta versión de la guía corrige problemas encontrados al revisar el código
contra el proyecto real. La columna **Alcance** indica si el problema le ocurre
a **cualquiera** que siga la guía (universal) o solo bajo ciertas condiciones.

| # | Problema en la versión original | Consecuencia | Alcance | Corrección |
|---|---|---|---|---|
| 1 | `pip freeze > requirements.txt` | En PowerShell 5.1 el archivo queda en UTF-16 y Render no puede instalar; además pisa las versiones fijadas | **Universal** (todo el que use PowerShell 5.1) | Edición manual en UTF-8 (1.1) |
| 2 | `git add .` + `git push origin main` | Sube archivos sueltos (o un `.env` mal ignorado) a un repo **público** y salta el flujo de ramas | **Depende del alumno** (solo si hay archivos sin ignorar), pero muy probable | `git add` por archivo, escaneo de claves, sin push |
| 3 | `pago_exitoso` sin login ni dueño | Cualquiera ve el pedido de otro cambiando el número en la URL | **Universal** | Solo para pedidos de la sesión + `@login_required` |
| 4 | Link a `ventas:detalle` con `pedido.pk` | Esa ruta es de `Venta`: muestra una venta distinta con el mismo id | **Universal** | Se quita el enlace |
| 5 | Mensaje "¡Pago exitoso! … pedido confirmado" | El estado sigue "Pendiente" hasta el webhook; confunde y puede mentirle al cliente | **Universal** | Texto "pago recibido" |
| 6 | `obtener_o_crear_cliente` renombra al Cliente existente | `ACCOUNT_EMAIL_VERIFICATION='none'`: quien se registre con el correo de un cliente real puede cambiarle el nombre | **Universal** (por la configuración del proyecto) | Nunca se modifica un Cliente existente |
| 7 | Búsqueda de Cliente por correo exacto | `Ana@x.com` vs `ana@x.com` → `IntegrityError` (500) | **Universal** | `correo__iexact` + normalizar |
| 8 | `generar_numero_pedido` = `count()+1` | Si se borra un pedido o hay 2 peticiones simultáneas, se repite el número y falla el checkout | **Universal** (aparece en cuanto se borra un pedido) | Mayor del año + reintento |
| 9 | Cada POST crea un Pedido nuevo | Recargar o doble clic deja pedidos pendientes huérfanos | **Universal** | Reutilizar pedido por firma del carrito |
| 10 | Se cobra el precio guardado en la sesión | Si el precio cambia, el producto se agota o se desactiva, se cobra dato viejo y se vende sin stock | **Universal** | `validar_carrito()` contra la BD |
| 11 | `messages.error(f'… {exc}')` | Se muestran errores internos (BD/Stripe) al usuario | **Universal** | Detalle solo al log |
| 12 | Falla de Stripe deja Pedido pendiente | Pedidos huérfanos que nunca se pagarán | **Universal** | Pedido nuevo → `cancelado` |
| 13 | `'{{ client_secret }}'` pegado en el JS | Frágil si el valor trae caracteres especiales | Bajo riesgo | `json_script` |
| 14 | Botón queda bloqueado si el estado no es `succeeded` ni error (p. ej. `processing`) | Usuario atascado en "Procesando…" | **Universal** (ocurre con 3D Secure/bancos lentos) | Manejo de todos los estados |
| 15 | URL de éxito escrita a mano `/catalogo/pago-exitoso/…` | Se rompe si cambia el prefijo de la URL | Bajo riesgo | `{% url %}` |
| 16 | Claves por defecto `sk_test_placeholder` | Sin variable en Render el checkout intenta cobrar con clave falsa y falla con 500 | **Depende del alumno** (si olvida la variable en Render) | Default vacío + mensaje controlado |
| 17 | `int(total * 100)` | Trunca; puede cobrar 1 centavo de menos | Bajo riesgo | `a_centavos()` con ROUND_HALF_UP |
| 18 | "131 tests" como base | La base real es mayor (W12/W13 agregaron pruebas) | **Universal** | Cifras relativas a N |
| 19 | Comandos en `cmd` | El proyecto trabaja en PowerShell | **Depende del entorno** | Bloques en PowerShell |
| 20 | `payment_method_types=['card']` al crear el PaymentIntent | Las cuentas nuevas de Stripe lo rechazan (error 400 `InvalidRequestError`): el checkout siempre falla aunque las claves sean correctas | **Universal** (cualquier cuenta de Stripe creada recientemente) | `automatic_payment_methods={'enabled': True, 'allow_redirects': 'never'}` |
| 21 | `pago_exitoso` vacía el carrito y dice "pago recibido" con solo abrir la URL | Quien crea un pedido puede abrir `/pago-exitoso/<id>/` **sin pagar**: se vacía su carrito y ve un mensaje de pago | **Universal** | `_pago_verificado()` consulta el PaymentIntent en Stripe (estado, pedido y monto) antes de vaciar el carrito |
| 22 | Sin límite de intentos en el checkout | Cada POST crea pedidos y llama a Stripe: se puede abusar del endpoint o gastar la cuota de la API | **Universal** | `dentro_del_limite()`: 10 intentos por usuario cada 10 min (HTTP 429) |

**Pendiente para W15** (ya anticipado por `crear_pedido_pendiente(**extra)`,
que acepta `items_snapshot`): el webhook debe procesar el pago dentro de
`transaction.atomic()` con `select_for_update()`, verificar que el monto
cobrado coincide con `total_pagado` y avisar si el stock no alcanza.

---

*Guía de Laboratorio W14 · ERP Django*
*Espiral 5 · Sprint 4 Desarrollo · Checkout + Stripe PaymentIntent*
*SEP 3061300006-23 · UTEC Celaya · MC. Román Fernando López González*

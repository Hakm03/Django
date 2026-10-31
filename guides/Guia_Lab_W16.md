# Guía de Laboratorio — W16
## ERP Django · Espiral 6 · Semana 16 de 24
### Técnico en Programación (SEP 3061300006-23) · UTEC Celaya
### Asesor: MC. Román Fernando López González

---

| Campo | Detalle |
|---|---|
| **Semana** | W16 de 24 |
| **Espiral** | E6 — Celery e Integraciones |
| **Sprint Scrum** | Sprint 5 — Planning |
| **Hito** | Sin hito propio · Avance hacia M6 (W18) |
| **Horario** | 16:45 – 19:45 (180 min) |
| **Nivel Schmelkes** | 4 — Funcionalidades Avanzadas |
| **Hilo conductor** | "W15 completó la venta. W16 la hace eficiente: tareas pesadas fuera del ciclo HTTP." |

---

## Respuesta a la tarea de investigación de W15

> **¿Qué es un `broker` en Celery?**
> El broker es el intermediario de mensajes: Django escribe una tarea
> en una cola (el broker) y el worker de Celery la lee y ejecuta.
> Es como un buzón de correo: el remitente (Django) deja el mensaje
> y el cartero (worker) lo recoge y entrega.
>
> **¿Por qué Redis en lugar de PostgreSQL como broker?**
>
> | Aspecto | Redis | PostgreSQL |
> |---|---|---|
> | Velocidad | Microsegundos (en memoria) | Milisegundos (en disco) |
> | Propósito | Almacén de mensajes temporal | Base de datos relacional |
> | Persistencia | Opcional | Siempre persistente |
> | Uso ideal | Colas de tareas, caché | Datos transaccionales |
>
> Para colas de tareas que se procesan en segundos, la velocidad
> de Redis es esencial. PostgreSQL como broker añade latencia y
> carga a la BD principal del negocio.
>
> **¿Diferencia entre `.delay()` y `.apply_async()`?**
>
> ```python
> # .delay() — forma abreviada, equivale a apply_async sin opciones
> enviar_confirmacion_pedido.delay(pedido_id)
>
> # .apply_async() — forma completa con opciones adicionales
> enviar_confirmacion_pedido.apply_async(
>     args=[pedido_id],
>     countdown=30,       # esperar 30 segundos antes de ejecutar
>     retry=True,
>     retry_policy={'max_retries': 3, 'interval_start': 5},
>     queue='high_priority',
> )
> ```
>
> **¿Idempotencia del stock con el webhook?**
> El código actual garantiza idempotencia con `if pedido.estado != 'pagado'`
> antes de llamar a `_descontar_stock()`. Si llega el mismo webhook dos
> veces, la segunda vez el pedido ya está `'pagado'` → no se decrementa
> el stock de nuevo. El `F()` protege contra race conditions *simultáneas*;
> la condición `if` protege contra *reintentos* de Stripe.

---

## Objetivos de la sesión

Al terminar W16, el estudiante será capaz de:

1. Explicar el patrón productor-broker-consumidor de Celery
2. Crear y configurar la aplicación Celery en el proyecto Django
3. Definir tareas asíncronas con `@shared_task`
4. Conectar las tareas al flujo de pago (webhook y vista de éxito)
5. Arrancar el worker de Celery y verificar la ejecución de tareas
6. Monitorear tareas con Flower
7. Escribir tests que verifican la invocación de tareas asíncronas

---

## Stack tecnológico de W16

| Herramienta | Novedad en W16 | Descripción |
|---|---|---|
| `celery` | ✅ Nuevo | Framework de tareas asíncronas distribuidas |
| `redis` (Python) | ✅ Nuevo | Cliente Python para Redis (broker de mensajes) |
| `flower` | ✅ Nuevo | Interfaz web para monitorear workers y tareas |
| `@shared_task` | ✅ Nuevo | Decorador para definir tareas portables entre apps |
| `core/celery.py` | ✅ Nuevo | Configuración central de la app Celery |
| `.delay()` | ✅ Nuevo | Envía una tarea al broker para ejecución asíncrona |

---

## Mapa de tiempo (180 min)

| Parte | Actividad | Tiempo |
|---|---|---|
| Arranque | Daily Scrum + Sprint 5 Planning + verificar W15 | 15 min |
| Parte 1 | Instalar Celery + Redis + Flower | 10 min |
| Parte 2 | `core/celery.py` + `core/__init__.py` | 15 min |
| Parte 3 | Configurar Celery en `settings.py` | 10 min |
| Parte 4 | Actualizar `docker-compose.yml` con worker + Flower | 15 min |
| Parte 5 | `ventas/tasks.py`: las 2 tareas placeholder | 20 min |
| Parte 6 | Conectar tareas en `pago_exitoso()` y webhook | 15 min |
| Parte 7 | Arrancar worker + Flower + verificación manual | 15 min |
| Parte 8 | Tests W16 (8 pruebas) | 20 min |
| Cierre | Commit · `finalizar_sesion.bat` · hilo → W17 | 10 min |
| Buffer | | 15 min |
| **Total** | | **180 min** |

---

## ARRANQUE — Daily Scrum + Sprint 5 Planning (15 min)

```cmd
E:\iniciar_sesion.bat
```

### Daily Scrum

```
1. ¿Qué hice en W15?
   → Implementé el endpoint webhook con verificación de firma Stripe,
     actualicé el estado del pedido y decrementé el stock con F().
     Declaré el Hito M5.

2. ¿Qué haré en W16?
   → Instalaré Celery con Redis, crearé las tareas asíncronas
     y las conectaré al flujo de pago.

3. ¿Tengo algún impedimento?
   → (registrar aquí)
```

### Verificar estado

```cmd
python manage.py check
python manage.py test tests --verbosity=0
```

**Resultado esperado:** `System check identified no issues` · `Ran 147 tests … OK`

---

### Sprint 5 Planning

**Sprint Goal del Sprint 5:**
> *"Al finalizar el Sprint 5, el ERP enviará correos transaccionales
> de confirmación de pedido, notificaciones de stock bajo, y ejecutará
> reportes diarios automáticos, todo de forma asíncrona con Celery
> y Redis sin bloquear las peticiones HTTP."*

**Duración:** W16 (Celery setup) · W17 (SendGrid correo) · W18 (Celery Beat · M6)

Crear `sprint5_planning.md`:

```markdown
# Sprint 5 Planning — ERP Django
## Semanas W16–W18 · Espiral 6: Celery e Integraciones

**Sprint Goal:**
Al finalizar el Sprint 5, el ERP ejecutará tareas pesadas de forma
asíncrona con Celery+Redis: correos de confirmación, alertas de
stock bajo y reporte diario de ventas.

## HUs seleccionadas

| ID | Historia | Puntos | Semana |
|---|---|---|---|
| HU-E6-01 | Como dev, quiero infraestructura Celery+Redis funcional | 3 | W16 |
| HU-E6-02 | Como sistema, quiero ejecutar tareas sin bloquear HTTP | 2 | W16 |
| HU-E6-03 | Como cliente, quiero correo de confirmación post-pago | 5 | W17 |
| HU-E6-04 | Como admin, quiero correo cuando el stock es bajo | 3 | W17 |
| HU-E6-05 | Como admin, quiero reporte diario de ventas a las 8 AM | 3 | W18 |
| HU-E6-06 | Como dev, quiero monitorear tareas con Flower | 2 | W16 |

**Total Sprint 5:** 18 puntos

## DoD — Sprint 5
- celery -A core worker → procesa tareas sin error
- POST /catalogo/checkout/ → tarea de correo en la cola (no espera)
- Correo de confirmación recibido en < 30 s (W17)
- Alerta de stock enviada cuando stock < umbral (W17)
- Reporte diario ejecutado a las 8:00 AM (W18)
- python manage.py test → ≥ 155 tests OK
```

---

## PARTE 1 — Instalar Celery, Redis y Flower (10 min)

### 1.1 Instalar paquetes

```cmd
pip install "celery==5.3.6" "redis==5.0.1" "flower==2.0.1"
pip freeze > requirements.txt
```

Verificar instalaciones:

```cmd
python -c "import celery; print('Celery', celery.__version__)"
python -c "import redis; print('redis', redis.__version__)"
python -c "import flower; print('flower OK')"
```

**Resultado esperado:**
```
Celery 5.3.6
redis 5.0.1
flower OK
```

### 1.2 Verificar Redis disponible

```cmd
:: Si Redis está corriendo vía Docker:
docker-compose up -d redis

:: Verificar conexión:
python -c "import redis; r=redis.from_url('redis://localhost:6379/0'); print('PING:', r.ping())"
```

**Resultado esperado:** `PING: True`

---

## PARTE 2 — `core/celery.py` y `core/__init__.py` (15 min)

### 2.1 Crear `core/celery.py`

```python
# core/celery.py
"""Configuración de la aplicación Celery para el proyecto ERP Django.

Este archivo debe importarse ANTES de cualquier tarea (@shared_task)
para que Celery esté configurado correctamente.

Uso desde la línea de comandos:
    # Iniciar worker (procesa tareas)
    celery -A core worker -l info

    # Iniciar worker + Beat (procesa tareas + tareas programadas)
    celery -A core worker -B -l info

    # Monitorear con Flower
    celery -A core flower --port=5555
"""
import os

from celery import Celery

# Establecer el módulo de settings de Django antes de crear la app Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Crear la aplicación Celery con el nombre del proyecto
app = Celery('core')

# Leer la configuración desde Django settings
# El prefijo CELERY_ distingue las variables de Celery de otras de Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-descubrir tareas en todos los archivos tasks.py de las apps instaladas
# Django buscará: clientes/tasks.py, productos/tasks.py, ventas/tasks.py, etc.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Tarea de diagnóstico — muestra el request de la tarea.

    Ejecutar para verificar que el worker está funcionando:
        from core.celery import debug_task
        debug_task.delay()
    """
    print(f'Request: {self.request!r}')
```

---

### 2.2 Actualizar `core/__init__.py`

Asegura que la app Celery se cargue cuando Django arranca,
lo que permite usar `@shared_task` en cualquier app:

```python
# core/__init__.py
"""Inicialización del paquete core del proyecto ERP Django.

Importa la app Celery para que se registre al arrancar Django.
Sin esta importación, @shared_task no encontraría la app Celery.
"""
from .celery import app as celery_app

__all__ = ('celery_app',)
```

### 2.3 Verificar que Celery puede importar el proyecto

```cmd
celery -A core inspect ping
```

**Si Redis no está disponible (aula sin Docker):**
```
Error: No nodes replied within time constraint.
```
→ Esto es normal si el worker no está corriendo. La importación es lo que importa.

**Si hay errores de importación:**
```cmd
python -c "from core.celery import app; print('Celery app OK:', app)"
```

**Resultado esperado:** `Celery app OK: <Celery core at 0x...>`

---

## PARTE 3 — Configurar Celery en `settings.py` (10 min)

### 3.1 Agregar variables de Celery al `.env`

```bash
# .env — agregar:
REDIS_URL=redis://localhost:6379/0
```

### 3.2 Agregar configuración al final de `core/settings.py`

```python
# core/settings.py — agregar al final (después de JAZZMIN_SETTINGS):

# ── CELERY — Cola de tareas asíncronas ────────────────────────────────────
# Broker: Redis almacena los mensajes de las tareas pendientes
CELERY_BROKER_URL = env('REDIS_URL', default='redis://localhost:6379/0')

# Backend: Redis almacena los resultados de las tareas (opcional)
CELERY_RESULT_BACKEND = env('REDIS_URL', default='redis://localhost:6379/0')

# Formato de serialización (JSON es seguro y portable)
CELERY_ACCEPT_CONTENT    = ['json']
CELERY_TASK_SERIALIZER   = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Zona horaria (heredar de Django)
CELERY_TIMEZONE = TIME_ZONE   # 'America/Mexico_City'

# Reintentos automáticos ante fallos de conexión al broker
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# Tiempo máximo que puede correr una tarea antes de ser terminada (segundos)
CELERY_TASK_SOFT_TIME_LIMIT = 300   # 5 minutos
CELERY_TASK_TIME_LIMIT       = 360  # 6 minutos (hard limit)

# Prefijo para las colas (útil si se comparte Redis entre proyectos)
CELERY_TASK_DEFAULT_QUEUE = 'erp_django'

# Para tests: ejecutar tareas sincrónicamente (sin worker)
# Se activa en tests con @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
CELERY_TASK_ALWAYS_EAGER         = False
CELERY_TASK_EAGER_PROPAGATES     = True
```

### 3.3 Actualizar `.env.example`

```bash
# .env.example — agregar:
REDIS_URL=redis://localhost:6379/0
```

### 3.4 Verificar

```cmd
python manage.py check
```

**Resultado esperado:** `System check identified no issues (0 silenced).`

---

## PARTE 4 — Actualizar `docker-compose.yml` (15 min)

### 4.1 Agregar servicios de Celery worker y Flower

Abrir `docker-compose.yml` y agregar los nuevos servicios:

```yaml
# docker-compose.yml — versión W16 completa
version: '3.9'

services:

  # ── Base de datos PostgreSQL ────────────────────────────────────────
  db:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB:       erp_db
      POSTGRES_USER:     erp_user
      POSTGRES_PASSWORD: erp_pass_local
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U erp_user -d erp_db"]
      interval: 5s
      timeout: 5s
      retries: 5

  # ── Broker de mensajes Redis ────────────────────────────────────────
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  # ── Aplicación Django ───────────────────────────────────────────────
  web:
    build: .
    restart: unless-stopped
    command: >
      sh -c "python manage.py migrate &&
             python manage.py collectstatic --no-input &&
             gunicorn core.wsgi --bind 0.0.0.0:8000 --workers 2 --log-file -"
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      DJANGO_SETTINGS_MODULE: core.settings_prod
      SECRET_KEY:             dev-clave-docker-no-usar-en-produccion
      DEBUG:                  "False"
      DATABASE_URL:           postgres://erp_user:erp_pass_local@db:5432/erp_db
      REDIS_URL:              redis://redis:6379/0
      ALLOWED_HOSTS:          localhost,127.0.0.1
      STRIPE_SECRET_KEY:      sk_test_placeholder
      STRIPE_PUBLISHABLE_KEY: pk_test_placeholder
      STRIPE_WEBHOOK_SECRET:  whsec_placeholder

  # ── Worker de Celery — W16 ──────────────────────────────────────────
  celery_worker:
    build: .
    restart: unless-stopped
    command: celery -A core worker -l info -Q erp_django
    volumes:
      - .:/app
    depends_on:
      redis:
        condition: service_healthy
      db:
        condition: service_healthy
    environment:
      DJANGO_SETTINGS_MODULE: core.settings_prod
      SECRET_KEY:             dev-clave-docker-no-usar-en-produccion
      DATABASE_URL:           postgres://erp_user:erp_pass_local@db:5432/erp_db
      REDIS_URL:              redis://redis:6379/0
      # Variables de correo (se completarán en W17)
      SENDGRID_API_KEY:       placeholder

  # ── Flower — Monitor de Celery — W16 ───────────────────────────────
  flower:
    build: .
    restart: unless-stopped
    command: celery -A core flower --port=5555 --broker=redis://redis:6379/0
    ports:
      - "5555:5555"
    depends_on:
      - redis
      - celery_worker

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

---

## PARTE 5 — `ventas/tasks.py`: Las 2 tareas placeholder (20 min)

### 5.1 ¿Por qué `@shared_task` y no `@app.task`?

```python
# @app.task — crea una dependencia directa a la instancia de Celery
from core.celery import app

@app.task
def mi_tarea():
    ...
# Problema: si ventas importa core.celery e core importa ventas,
# podría haber una importación circular.

# @shared_task — desacoplado de la instancia de Celery
from celery import shared_task

@shared_task
def mi_tarea():
    ...
# Ventaja: ventas/tasks.py no importa nada de core/
# La app Celery se asigna automáticamente cuando Django arranca
```

---

### 5.2 Crear `ventas/tasks.py`

```python
# ventas/tasks.py
"""Tareas asíncronas de la app ventas — W16.

Las tareas con @shared_task son descubiertas automáticamente
por celery.autodiscover_tasks() definido en core/celery.py.

Estado de implementación:
    W16: Estructura base — las tareas solo registran en el log.
    W17: Se agrega SendGrid para envío real de correos.
    W18: Se agregan tareas programadas con Celery Beat.

Uso:
    # Desde una vista (asíncrono — no bloquea la respuesta HTTP):
    enviar_confirmacion_pedido.delay(pedido_id)

    # Desde la línea de comandos (síncrono — para depuración):
    python manage.py shell
    >>> from ventas.tasks import enviar_confirmacion_pedido
    >>> result = enviar_confirmacion_pedido.apply(args=[1])
    >>> result.get()
"""
import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,      # esperar 60s antes de reintentar
    name='ventas.enviar_confirmacion_pedido',
)
def enviar_confirmacion_pedido(self, pedido_id: int) -> dict:
    """Envía el correo de confirmación de pedido al cliente.

    W16: Solo registra en el log (placeholder).
    W17: Enviará correo real con SendGrid.

    Args:
        pedido_id: ID del Pedido confirmado.

    Returns:
        dict con estado y pedido_id procesado.
    """
    from ventas.models import Pedido   # import local evita circularidad

    try:
        pedido = Pedido.objects.select_related('cliente').get(pk=pedido_id)
    except Pedido.DoesNotExist:
        logger.error(
            f'[Tarea enviar_confirmacion] Pedido {pedido_id} no existe.'
        )
        return {'estado': 'error', 'pedido_id': pedido_id}

    # W16: Placeholder — solo registra en el log
    logger.info(
        f'[Tarea enviar_confirmacion] Procesando pedido '
        f'{pedido.numero_pedido} para {pedido.cliente.correo}. '
        f'Total: ${pedido.total_pagado}. '
        f'Timestamp: {timezone.now().isoformat()}'
    )

    # W17 implementará aquí:
    #   from django.core.mail import send_mail
    #   o envío via SendGrid API

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
    """Verifica productos con stock por debajo del umbral.

    W16: Solo registra en el log (placeholder).
    W17: Enviará alerta por correo al administrador.
    W18: Se programa para ejecutarse automáticamente cada hora.

    Args:
        umbral: cantidad mínima de stock antes de alertar (default: 5).

    Returns:
        dict con lista de productos con stock bajo.
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
            f'[Tarea verificar_stock] {len(productos_bajos)} producto(s) '
            f'con stock < {umbral}: '
            f'{[p["nombre"] for p in productos_bajos]}'
        )
    else:
        logger.info(
            f'[Tarea verificar_stock] Todos los productos tienen '
            f'stock >= {umbral}. OK.'
        )

    return {
        'umbral':          umbral,
        'productos_bajos': productos_bajos,
        'total':           len(productos_bajos),
    }
```

---

## PARTE 6 — Conectar Tareas en Vistas (15 min)

### 6.1 Actualizar `pago_exitoso()` en `catalogo/views.py`

Agregar la importación y la llamada a la tarea:

```python
# catalogo/views.py — agregar import al inicio:
from ventas.tasks import enviar_confirmacion_pedido


# Actualizar la función pago_exitoso():
def pago_exitoso(request, pedido_id: int):
    """Vista de confirmación post-pago exitoso — W16.

    Cambios respecto a W14:
        Dispara la tarea asíncrona de correo con .delay().
        La tarea se encola en Redis y el worker la procesa
        en segundo plano, sin bloquear esta respuesta HTTP.
    """
    from django.shortcuts import get_object_or_404
    pedido = get_object_or_404(Pedido, pk=pedido_id)

    # Vaciar el carrito de la sesión
    _guardar_carrito(request, {})

    # ── NUEVO W16: disparar tarea asíncrona de confirmación ───────────
    # .delay() envía la tarea al broker Redis de forma no bloqueante.
    # El worker la ejecutará en segundo plano.
    enviar_confirmacion_pedido.delay(pedido.pk)
    # ──────────────────────────────────────────────────────────────────

    messages.success(
        request,
        f'¡Pago exitoso! Tu pedido {pedido.numero_pedido} '
        f'está confirmado. Recibirás un correo de confirmación pronto.'
    )

    return render(request, 'catalogo/pago_exitoso.html', {
        'pedido': pedido,
    })
```

---

### 6.2 Actualizar el webhook en `catalogo/webhook_views.py`

En `_manejar_pago_exitoso()`, agregar la llamada a la tarea:

```python
# catalogo/webhook_views.py — agregar import al inicio:
from ventas.tasks import enviar_confirmacion_pedido


# En la función _manejar_pago_exitoso(), después de save():
def _manejar_pago_exitoso(payment_intent: dict) -> None:
    # ... (código existente) ...
    pedido_id = _extraer_pedido_id(payment_intent)
    if pedido_id is None:
        return

    try:
        pedido = Pedido.objects.get(pk=pedido_id)
    except Pedido.DoesNotExist:
        logger.error(f'Webhook: Pedido {pedido_id} no encontrado en BD.')
        return

    if pedido.estado != 'pagado':
        pedido.estado = 'pagado'
        pedido.save(update_fields=['estado'])
        logger.info(
            f'Pedido {pedido.numero_pedido} actualizado a "pagado".'
        )
        _descontar_stock(pedido)

        # ── NUEVO W16: disparar tarea de confirmación ─────────────────
        # El webhook es el lugar más confiable para disparar el correo:
        # se ejecuta incluso si el usuario cerró el navegador antes de
        # llegar a pago_exitoso().
        enviar_confirmacion_pedido.delay(pedido.pk)
        # ─────────────────────────────────────────────────────────────
    else:
        logger.info(
            f'Pedido {pedido.numero_pedido} ya estaba pagado — '
            f'idempotente, sin cambios.'
        )
```

> **Nota:** La tarea se dispara desde el webhook (fuente confiable)
> Y también desde `pago_exitoso()` (para el caso en que el webhook
> llegue tarde). La tarea debe ser **idempotente**: si se ejecuta
> dos veces para el mismo pedido, el segundo correo puede verificar
> si ya se envió antes. Esto se implementará en W17.

---

## PARTE 7 — Arrancar Worker y Flower (15 min)

### 7.1 Arrancar Redis (si no está corriendo)

```cmd
:: Con Docker (recomendado):
docker-compose up -d redis

:: Verificar:
docker-compose ps redis
```

### 7.2 Arrancar el worker de Celery

Abrir una **segunda terminal** (manteniendo el servidor Django activo):

```cmd
:: Activar el entorno
cd C:\Temp_Workspace_ERP
call env_erp\Scripts\activate

:: Arrancar el worker (mantener esta terminal abierta)
celery -A core worker -l info -Q erp_django
```

**Resultado esperado:**
```
[config]
.> app:         core:0x...
.> transport:   redis://localhost:6379/0
.> results:     redis://localhost:6379/0
.> concurrency: 4 (prefork)
.> task events: OFF

[tasks]
  . ventas.enviar_confirmacion_pedido
  . ventas.verificar_stock_bajo
  . core.celery.debug_task

[2025-01-15 17:00:00,000: INFO/MainProcess]
    celery@PC-AULA ready.
```

> **Importante:** si el worker muestra `[tasks]` con las tareas,
> el autodiscovery funciona correctamente.

---

### 7.3 Verificar con la tarea de diagnóstico

```cmd
:: En una tercera terminal (o el shell de Django):
python manage.py shell
```

```python
from core.celery import debug_task
result = debug_task.delay()
print('Task ID:', result.id)
```

En la terminal del worker debe aparecer:
```
[INFO/ForkPoolWorker] Request: <Context: {'lang': 'py', 'task': 'core.celery.debug_task', ...}>
```

---

### 7.4 Arrancar Flower (monitor visual)

Abrir una **cuarta terminal**:

```cmd
cd C:\Temp_Workspace_ERP
call env_erp\Scripts\activate
celery -A core flower --port=5555
```

Abrir en el navegador: `http://localhost:5555`

```
[ ] Dashboard de Flower visible con 1 worker activo
[ ] Pestaña "Tasks" → lista de tareas ejecutadas
[ ] Pestaña "Workers" → el worker aparece en verde (online)
```

---

### 7.5 Prueba de extremo a extremo

Con el servidor Django, el worker y el Stripe CLI activos:

```
1. Completar una compra (tarjeta 4242)
2. Al llegar a pago_exitoso → en la terminal del WORKER aparece:
   [INFO] [Tarea enviar_confirmacion] Procesando pedido PED-2025-0001...
3. El webhook también dispara la tarea → aparece una segunda vez
4. En Flower → /tasks → se ven ambas ejecuciones de la tarea
```

---

## PARTE 8 — Tests W16 (20 min)

### 8.1 Estrategia para tests de Celery

```python
# OPCIÓN A — CELERY_TASK_ALWAYS_EAGER (ejecuta sin worker)
# Las tareas se ejecutan sincrónicamente en el mismo proceso
# Útil para verificar la LÓGICA de la tarea

@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
def test_tarea_registra_en_log(self):
    enviar_confirmacion_pedido.delay(pedido_id)
    # La tarea se ejecutó sincrónicamente

# OPCIÓN B — Mock del método .delay()
# Verifica que la tarea SE LLAMA (no que se ejecuta)
# Útil para tests de integración de vistas

@patch('catalogo.views.enviar_confirmacion_pedido.delay')
def test_pago_exitoso_dispara_tarea(self, mock_delay):
    self.client.get(url)
    mock_delay.assert_called_once_with(pedido_id)
```

Usaremos **ambas opciones** en los tests de W16.

---

### 8.2 Crear `tests/test_w16_celery.py`

```python
"""Suite de pruebas W16 — Celery worker y tareas asíncronas.

Verifica la configuración de Celery, la definición de las tareas
y su invocación desde las vistas.

Ejecutar con:
    python manage.py test tests.test_w16_celery --verbosity=2

Resultado esperado:
    Ran 8 tests in X.XXXs
    OK
"""
from decimal import Decimal
from unittest.mock import call, patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from clientes.models      import Cliente
from configuracion.models import ConfiguracionERP
from productos.models     import Categoria, Producto
from ventas.models        import Pedido
from ventas.tasks         import (
    enviar_confirmacion_pedido,
    verificar_stock_bajo,
)


class CeleryConfigTest(TestCase):
    """Verifica que Celery está correctamente configurado."""

    def test_celery_app_importable(self):
        """La app Celery debe poder importarse sin errores."""
        from core.celery import app as celery_app
        self.assertIsNotNone(celery_app)
        self.assertEqual(celery_app.main, 'core')

    def test_tareas_registradas_en_celery(self):
        """Las tareas de ventas deben estar registradas en Celery."""
        from core.celery import app as celery_app
        tareas = celery_app.tasks.keys()
        self.assertIn('ventas.enviar_confirmacion_pedido', tareas)
        self.assertIn('ventas.verificar_stock_bajo', tareas)


class EnviarConfirmacionTareaTest(TestCase):
    """Tests de la tarea enviar_confirmacion_pedido."""

    def setUp(self):
        ConfiguracionERP.get_instance()
        cat         = Categoria.objects.create(nombre='Cat')
        prod        = Producto.objects.create(
            nombre='P', precio=Decimal('100.00'), stock=5, categoria=cat
        )
        cli         = Cliente.objects.create(nombre='C', correo='c@t.com')
        self.pedido = Pedido.objects.create(
            numero_pedido = 'PED-2025-0001',
            cliente       = cli,
            estado        = 'pagado',
            total_pagado  = Decimal('116.00'),
        )

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_tarea_ejecuta_y_retorna_ok(self):
        """La tarea debe ejecutarse y retornar estado 'ok'."""
        resultado = enviar_confirmacion_pedido.delay(self.pedido.pk)
        data = resultado.get()
        self.assertEqual(data['estado'], 'ok')
        self.assertEqual(data['pedido_id'], self.pedido.pk)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_tarea_con_pedido_inexistente_retorna_error(self):
        """La tarea con pedido inexistente debe retornar estado 'error'."""
        resultado = enviar_confirmacion_pedido.delay(9999)
        data = resultado.get()
        self.assertEqual(data['estado'], 'error')

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_verificar_stock_bajo_detecta_productos(self):
        """verificar_stock_bajo debe detectar productos con stock < umbral."""
        Producto.objects.filter(nombre='P').update(stock=3)
        resultado = verificar_stock_bajo.delay(umbral=5)
        data = resultado.get()
        self.assertGreaterEqual(data['total'], 1)
        nombres = [p['nombre'] for p in data['productos_bajos']]
        self.assertIn('P', nombres)


class TareaInvocadaDesdeVistaTest(TestCase):
    """Verifica que las vistas invocan las tareas con .delay()."""

    def setUp(self):
        ConfiguracionERP.get_instance()
        cat  = Categoria.objects.create(nombre='Cat')
        cli  = Cliente.objects.create(nombre='C', correo='test@test.com')
        self.pedido = Pedido.objects.create(
            numero_pedido = 'PED-2025-VISTA',
            cliente       = cli,
            estado        = 'pendiente',
            total_pagado  = Decimal('100.00'),
        )
        self.user = User.objects.create_user('viewer', password='pass')

    @patch('catalogo.views.enviar_confirmacion_pedido.delay')
    def test_pago_exitoso_llama_a_delay(self, mock_delay):
        """pago_exitoso() debe llamar a .delay() con el pedido_id."""
        self.client.force_login(self.user)
        self.client.get(
            reverse('catalogo:pago_exitoso', args=[self.pedido.pk])
        )
        mock_delay.assert_called_once_with(self.pedido.pk)

    @patch('catalogo.webhook_views.enviar_confirmacion_pedido.delay')
    @patch('catalogo.webhook_views.stripe.Webhook.construct_event')
    def test_webhook_succeeded_llama_a_delay(
        self, mock_event, mock_delay
    ):
        """El webhook payment_intent.succeeded debe llamar a .delay()."""
        mock_event.return_value = {
            'type': 'payment_intent.succeeded',
            'data': {
                'object': {
                    'id': 'pi_test',
                    'metadata': {'pedido_id': str(self.pedido.pk)},
                }
            }
        }
        self.pedido.items_snapshot = []
        self.pedido.save()

        self.client.post(
            reverse('catalogo:webhook'),
            data=b'{}',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=1,v1=ok'
        )
        mock_delay.assert_called_once_with(self.pedido.pk)
```

### 8.3 Ejecutar los tests

```cmd
python manage.py test tests.test_w16_celery --verbosity=2
```

**Resultado esperado:**
```
test_celery_app_importable ... ok
test_pago_exitoso_llama_a_delay ... ok
test_tarea_con_pedido_inexistente_retorna_error ... ok
test_tarea_ejecuta_y_retorna_ok ... ok
test_tareas_registradas_en_celery ... ok
test_verificar_stock_bajo_detecta_productos ... ok
test_webhook_succeeded_llama_a_delay ... ok

Ran 7 tests in X.XXXs
OK
```

### 8.4 Suite acumulada

```cmd
python manage.py test tests --verbosity=0
```

**Resultado esperado:** `Ran 155 tests in X.XXXs · OK` (147 + 7–8)

---

## CIERRE — Commit y Respaldo (10 min)

### Actualizar `sprint5_planning.md`

```markdown
## Sprint Backlog — actualización W16

| Tarea | Estado |
|---|---|
| pip install celery redis flower | ✅ W16 |
| core/celery.py + core/__init__.py | ✅ W16 |
| CELERY_* en settings.py | ✅ W16 |
| docker-compose.yml con worker + flower | ✅ W16 |
| ventas/tasks.py (2 tareas placeholder) | ✅ W16 |
| pago_exitoso: .delay() al vaciar carrito | ✅ W16 |
| webhook: .delay() al confirmar pago | ✅ W16 |
| Worker corriendo + Flower en :5555 | ✅ W16 |
| SendGrid correo transaccional real | ⏳ W17 |
| Alerta de stock bajo por correo | ⏳ W17 |
| Celery Beat + tareas programadas | ⏳ W18 |
```

### Commit de cierre W16

```cmd
git add .
git status

:: Verificar que incluye:
::   core/celery.py (nuevo)
::   core/__init__.py (actualizado)
::   core/settings.py (CELERY_* config)
::   ventas/tasks.py (nuevo)
::   catalogo/views.py (pago_exitoso con .delay())
::   catalogo/webhook_views.py (webhook con .delay())
::   docker-compose.yml (worker + flower)
::   tests/test_w16_celery.py
::   sprint5_planning.md

git commit -m "Sprint 5 W16: Celery+Redis+Flower + tareas async + 155 tests OK"
git push origin main
```

### Ejecutar `finalizar_sesion.bat`

```cmd
:: Detener: servidor Django (Ctrl+C) + worker (Ctrl+C) + flower (Ctrl+C)
E:\finalizar_sesion.bat
```

---

## CHECKLIST FINAL W16

### Técnico

```
INSTALACIÓN
[ ] pip install celery redis flower → sin errores
[ ] requirements.txt actualizado con los 3 paquetes

CELERY APP
[ ] core/celery.py: os.environ.setdefault antes de Celery('core')
[ ] core/celery.py: app.config_from_object con namespace='CELERY'
[ ] core/celery.py: app.autodiscover_tasks() registra ventas/tasks.py
[ ] core/__init__.py: from .celery import app as celery_app

SETTINGS
[ ] CELERY_BROKER_URL = env('REDIS_URL', ...)
[ ] CELERY_RESULT_BACKEND = mismo que BROKER
[ ] CELERY_ACCEPT_CONTENT = ['json']
[ ] CELERY_TASK_SERIALIZER = 'json'
[ ] CELERY_TASK_ALWAYS_EAGER = False (True solo en tests)
[ ] python manage.py check → 0 issues

DOCKER COMPOSE
[ ] Servicio celery_worker con command: celery -A core worker
[ ] Servicio flower con command: celery -A core flower --port=5555
[ ] depends_on redis con condition: service_healthy

TAREAS
[ ] ventas/tasks.py: @shared_task (no @app.task)
[ ] enviar_confirmacion_pedido: max_retries=3, import local de Pedido
[ ] verificar_stock_bajo: umbral configurable, import local de Producto
[ ] Las tareas reciben IDs (int), no objetos (no JSON serializable)

CONEXIÓN EN VISTAS
[ ] pago_exitoso(): enviar_confirmacion_pedido.delay(pedido.pk)
[ ] webhook _manejar_pago_exitoso(): .delay() después de save()

WORKER
[ ] celery -A core worker -l info → muestra las tareas registradas
[ ] debug_task.delay() → worker ejecuta y muestra Request: en log
[ ] Flower en :5555 → worker verde, tareas visibles

TESTS
[ ] test tests.test_w16_celery → 7/7 OK
[ ] test tests → 155/155 OK acumulados
[ ] test_celery_app_importable → celery_app no es None
[ ] test_tareas_registradas → nombres exactos en app.tasks
[ ] @override_settings(CELERY_TASK_ALWAYS_EAGER=True) en test de tarea
[ ] @patch('.delay') para verificar invocación desde vistas

GIT
[ ] sprint5_planning.md con 6 HUs y Sprint Goal
[ ] Commit con mensaje descriptivo
[ ] git push → GitHub con core/celery.py y ventas/tasks.py
[ ] finalizar_sesion.bat → archivos en USB
```

---

## DIAGRAMA: Patrón productor-broker-consumidor (W16)

```
Django (Productor)                   Worker Celery (Consumidor)
──────────────────                   ──────────────────────────
pago_exitoso(request)
    │
    ├─ _guardar_carrito({})
    │
    └─ enviar_confirmacion_pedido
           .delay(pedido_id)
           │                    Redis (Broker)
           │    ┌──────────────────────────────┐
           └───►│ Cola: erp_django             │
                │ Mensaje: {                   │
                │   "task": "ventas.enviar...",│
                │   "args": [42],              │
                │   "kwargs": {}               │◄───── Worker lee
                │ }                            │       el mensaje
                └──────────────────────────────┘
                                                    │
                                                    ▼
                                         enviar_confirmacion_pedido(42)
                                             │
                                             ├─ Pedido.objects.get(pk=42)
                                             ├─ logger.info("Procesando...")
                                             └─ return {'estado': 'ok', ...}

HTTP Response: 200 inmediato ✅    (tarea en cola, worker la procesa después)
Usuario no espera el correo ✅     (se enviará en < 30s en W17)

Flower (:5555) monitorea:
    Workers: [celery@PC-AULA: online]
    Tasks:   [ventas.enviar_confirmacion_pedido: SUCCESS × 3]
```

---

## HILO CONDUCTOR → W17

**¿Qué entrega W16?**
La infraestructura completa de Celery: worker funcionando, tareas
registradas, llamadas desde las vistas y el webhook. Las tareas
aún son placeholders que solo registran en el log.

**¿Qué abre W17?**
Con la infraestructura en su lugar, W17 reemplaza los `logger.info()`
de las tareas con envíos reales de correo usando **SendGrid**.
El correo de confirmación de pedido llegará al cliente en < 30 segundos.

**¿Qué necesita W17 de W16?**

| Artefacto de W16 | Uso en W17 |
|---|---|
| `ventas/tasks.py` con placeholder | W17 reemplaza `logger.info()` con `send_mail()` + SendGrid |
| `max_retries=3` en la tarea | Si SendGrid falla, Celery reintenta automáticamente |
| `enviar_confirmacion_pedido.delay()` ya en vistas | W17 no toca las vistas — solo modifica la tarea |
| Docker service `celery_worker` | W17 agrega `SENDGRID_API_KEY` como variable de entorno |

**Tarea de investigación para W17:**
> Lee la documentación de SendGrid para Python:
> `https://github.com/sendgrid/sendgrid-python`
>
> ¿Qué es un `Dynamic Template` de SendGrid?
> ¿Cómo se envía un correo con `send_mail()` de Django usando
> el backend `AnyMailBackend` de `django-anymail`?
> ¿Qué diferencia hay entre `EMAIL_BACKEND` y el SDK de SendGrid directo?

**Pregunta de reflexión:**
> "En W16 la tarea se dispara tanto desde `pago_exitoso()` como
> desde el webhook. ¿Podría el cliente recibir DOS correos de
> confirmación para el mismo pedido? ¿Cómo evitarías eso en W17?"

---

## Referencia rápida de comandos W16

```cmd
:: SESIÓN
E:\iniciar_sesion.bat
E:\finalizar_sesion.bat

:: REDIS (con Docker)
docker-compose up -d redis
docker-compose ps redis

:: DJANGO (terminal 1)
python manage.py check
python manage.py runserver

:: CELERY WORKER (terminal 2)
celery -A core worker -l info -Q erp_django

:: FLOWER MONITOR (terminal 3)
celery -A core flower --port=5555
:: → Abrir http://localhost:5555

:: DEPURACIÓN DE TAREA (shell de Django)
python manage.py shell
>>> from ventas.tasks import enviar_confirmacion_pedido
>>> result = enviar_confirmacion_pedido.apply(args=[1])   # síncrono
>>> print(result.get())

:: TESTS
python manage.py test tests.test_w16_celery --verbosity=2
python manage.py test tests --verbosity=0   (155 tests)

:: GIT
git add .
git commit -m "Sprint 5 W16: Celery+Redis+Flower + 155 tests OK"
git push origin main
git log --oneline
```

---

*Guía de Laboratorio W16 · ERP Django*
*Espiral 6 · Sprint 5 Planning · Celery + Redis + Tareas Asíncronas*
*SEP 3061300006-23 · UTEC Celaya · MC. Román Fernando López González*

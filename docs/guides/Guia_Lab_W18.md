# Guía de Laboratorio — W18
## ERP Django · Espiral 6 · Semana 18 de 24
### Técnico en Programación (SEP 3061300006-23) · UTEC Celaya
### Asesor: MC. Román Fernando López González

---

| Campo | Detalle |
|---|---|
| **Semana** | W18 de 24 |
| **Espiral** | E6 — Celery e Integraciones |
| **Sprint Scrum** | Sprint 5 — Review + Retrospectiva |
| **Hito** | **★ M6: Celery activo + correo recibido + alertas + Beat programado** |
| **Horario** | 16:45 – 19:45 (180 min) |
| **Nivel Schmelkes** | 4 — Funcionalidades Avanzadas |
| **Hilo conductor** | "W17 enseñó al ERP a enviar correos. W18 lo hace autónomo: trabaja mientras nadie lo mira." |

---

## Respuesta a la tarea de investigación de W17

> **¿Qué es `CELERY_BEAT_SCHEDULE`?**
> Es un diccionario en `settings.py` que define las tareas programadas.
> Cada entrada especifica: qué tarea ejecutar, con qué argumentos y
> con qué frecuencia (timedelta o crontab).
>
> ```python
> CELERY_BEAT_SCHEDULE = {
>     'nombre-tarea': {
>         'task':     'app.tasks.nombre_funcion',
>         'schedule': timedelta(hours=1),   # cada hora
>         'args':     (umbral,),
>     },
> }
> ```
>
> **¿Por qué Beat debe correr como proceso SEPARADO?**
>
> | Escenario | Problema |
> |---|---|
> | `worker -B` (combinado) | Si el worker se cae, el scheduler también se cae |
> | Beat separado | Si el worker se cae, el Beat sigue enviando tareas a la cola |
>
> En producción con recursos: siempre dos procesos independientes.
> En desarrollo: `worker -B` es aceptable por comodidad.
>
> ⚠️ **En nuestro despliegue (Render Free) se usa `worker --beat`:** el plan
> gratuito no tiene Background Workers, así que worker y Beat viven dentro
> del contenedor web (igual que el worker de W16). Es una decisión
> consciente: si el contenedor se reinicia, ambos se reinician juntos.
> Lo importante es que exista **una sola instancia** del servicio.
>
> **¿Riesgo de usar SendGrid real en CI/CD?**
> Sí: cada ejecución del pipeline enviaría correos reales a las
> direcciones de los datos de prueba, podría agotar el límite
> gratuito (100/día), generar costos inesperados y marcar los
> correos como spam si se repiten. Por eso usamos `locmem.EmailBackend`
> que captura todo en `mail.outbox` sin salir del proceso.

---

## Objetivos de la sesión

Al terminar W18, el estudiante será capaz de:

1. Agregar la tarea `reporte_ventas_diario` con agregación SQL
2. Crear el template HTML del reporte de ventas
3. Configurar `CELERY_BEAT_SCHEDULE` con `crontab` y `timedelta`
4. Embeber Beat en el worker de Render (`docker-entrypoint.sh`)
5. Verificar Beat en los Logs de Render y recibir el reporte por correo
6. Ejecutar el Sprint 5 Review y declarar el Hito M6
7. Completar la ficha Schmelkes E6

---

## Stack tecnológico de W18

| Herramienta | Novedad en W18 | Descripción |
|---|---|---|
| `celery.schedules.crontab` | ✅ Nuevo | Programa tareas en horas exactas (como cron de Unix) |
| `CELERY_BEAT_SCHEDULE` | ✅ Nuevo | Diccionario de tareas periódicas en `settings.py` |
| Celery Beat (`worker --beat`) | ✅ Nuevo | Scheduler embebido en el worker de Render |
| `REPORTE_DIARIO_HORA` | ✅ Nuevo | Hora del reporte configurable desde Render (HH:MM, hora MX) |
| `annotate` + `Sum(F())` | ✅ Nuevo | Agregación SQL para totales de ventas |
| `django.utils.timezone.now()` | ya usado | Fecha/hora actual en zona horaria configurada |

---

## Mapa de tiempo (180 min)

| Parte | Actividad | Tiempo |
|---|---|---|
| Arranque | Daily Scrum + verificar W17 | 10 min |
| Parte 1 | Template `reporte_ventas.html` + `.txt` | 20 min |
| Parte 2 | Tarea `reporte_ventas_diario` en `ventas/tasks.py` | 25 min |
| Parte 3 | `CELERY_BEAT_SCHEDULE` en `settings.py` | 15 min |
| Parte 4 | Beat embebido en Render + dependencias | 10 min |
| Parte 5 | Verificar en local (EAGER) y en Render | 15 min |
| Parte 6 | Tests W18 (12 pruebas) | 20 min |
| **Commit parcial** | Punto de control seguro | 5 min |
| Parte 7 | Sprint 5 Review ante el asesor | 20 min |
| Parte 8 | Sprint 5 Retrospectiva + Ficha Schmelkes E6 | 20 min |
| Cierre | Commit final [M6] · `finalizar_sesion.bat` · hilo → W19 | 10 min |
| Buffer | | 10 min |
| **Total** | | **180 min** |

---

## ARRANQUE — Daily Scrum (10 min)

```cmd
E:\iniciar_sesion.bat
```

### Daily Scrum

```
1. ¿Qué hice en W17?
   → Instalé django-anymail, actualicé las tareas Celery para
     enviar correos reales con SendGrid y garanticé idempotencia
     con el campo correo_enviado.

2. ¿Qué haré en W18?
   → Agregaré la tarea de reporte diario de ventas, configuraré
     Celery Beat para tareas programadas y cerraré el Sprint 5
     con el Hito M6.

3. ¿Tengo algún impedimento?
   → (registrar aquí)
```

### Verificar estado

```cmd
python manage.py check
python manage.py test tests --verbosity=0
```

**Resultado esperado:** `System check identified no issues` · `Ran 159 tests`

> 🐳 **Sin Docker Desktop:** igual que en W16–W17, en el laboratorio no hay
> Redis ni worker: con `REDIS_URL` vacía todo corre en modo **EAGER**.
> Beat solo existe en Render. Si la suite muestra fallas en W01/W02/W03/
> W08/W12, ver la sección 6.4 (se corrigen en esta semana).

---

## PARTE 1 — Template HTML del Reporte de Ventas (20 min)

### 1.1 Crear `templates/emails/reporte_ventas.html`

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Reporte de ventas — {{ fecha }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, Helvetica, sans-serif;
            font-size: 14px;
            background: #F5F7FA;
            color: #1A1A2E;
        }
        .wrapper {
            max-width: 640px;
            margin: 24px auto;
            background: #FFFFFF;
            border-radius: 12px;
            overflow: hidden;
        }
        .header {
            background: #0A2342;
            padding: 26px 32px;
            border-bottom: 4px solid #B8860B;
        }
        .header-title {
            color: #D4AF37;
            font-size: 20px;
            font-weight: bold;
        }
        .header-sub {
            color: rgba(255,255,255,.72);
            font-size: 13px;
            margin-top: 4px;
        }
        .body { padding: 26px 32px; }
        /* KPI cards */
        .kpi-grid {
            display: table;
            width: 100%;
            border-collapse: separate;
            border-spacing: 8px;
            margin-bottom: 24px;
        }
        .kpi-row { display: table-row; }
        .kpi-card {
            display: table-cell;
            background: #E8F0FB;
            border-radius: 8px;
            padding: 14px 16px;
            text-align: center;
            width: 50%;
        }
        .kpi-valor {
            font-size: 22px;
            font-weight: bold;
            color: #0A2342;
        }
        .kpi-label {
            font-size: 12px;
            color: #5A6A7E;
            text-transform: uppercase;
            letter-spacing: .05em;
            margin-top: 3px;
        }
        .kpi-card.gold .kpi-valor { color: #B8860B; }
        /* Tabla top productos */
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
        }
        th {
            background: #0A2342;
            color: #FFFFFF;
            padding: 10px 14px;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: .05em;
            text-align: left;
        }
        th.num { text-align: right; }
        td {
            padding: 9px 14px;
            border-bottom: 1px solid #E8F0FB;
            font-size: 13px;
        }
        td.num { text-align: right; }
        .sin-ventas {
            background: #FDF8E8;
            border: 1px solid #B8860B;
            border-radius: 8px;
            padding: 16px;
            text-align: center;
            color: #5A6A7E;
            font-size: 14px;
            margin: 16px 0;
        }
        .footer {
            background: #F5F7FA;
            border-top: 1px solid #C8D8EC;
            padding: 14px 32px;
            font-size: 11px;
            color: #5A6A7E;
            text-align: center;
        }
    </style>
</head>
<body>
<div class="wrapper">

    <!-- ENCABEZADO -->
    <div class="header">
        <div class="header-title">📊 Reporte de ventas del día</div>
        <div class="header-sub">
            {{ config.nombre_empresa }} · {{ fecha }}
        </div>
    </div>

    <!-- CUERPO -->
    <div class="body">

        <!-- KPIs -->
        <div class="kpi-grid">
            <div class="kpi-row">
                <div class="kpi-card">
                    <div class="kpi-valor">{{ total_pedidos }}</div>
                    <div class="kpi-label">Pedidos pagados hoy</div>
                </div>
                <div class="kpi-card gold">
                    <div class="kpi-valor">${{ total_facturado }}</div>
                    <div class="kpi-label">Total facturado</div>
                </div>
            </div>
        </div>

        {% if top_productos %}
        <p style="font-weight:600;color:#0A2342;margin-bottom:8px;">
            Top {{ top_productos|length }} productos del día
        </p>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Producto</th>
                    <th class="num">Unidades vendidas</th>
                    <th class="num">Ingreso ($)</th>
                </tr>
            </thead>
            <tbody>
                {% for prod in top_productos %}
                <tr>
                    <td>{{ forloop.counter }}</td>
                    <td>{{ prod.nombre }}</td>
                    <td class="num">{{ prod.unidades }}</td>
                    <td class="num">${{ prod.ingreso }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <div class="sin-ventas">
            Sin ventas registradas hoy. ¡Hay oportunidad de mejorar! 🎯
        </div>
        {% endif %}

        <p style="color:#5A6A7E;font-size:12px;margin-top:12px;">
            Panel de administración:
            <a href="{{ url_admin }}" style="color:#0A2342;">
                {{ url_admin }}
            </a>
        </p>
    </div>

    <div class="footer">
        <p>Generado automáticamente por ERP Django a las {{ hora_programada }} (hora de México)</p>
        <p>{{ config.nombre_empresa }}</p>
    </div>

</div>
</body>
</html>
```

> El pie muestra `{{ hora_programada }}` (la hora configurada en
> `REPORTE_DIARIO_HORA`) en lugar de un "8:00 AM" fijo.

---

### 1.2 Crear `templates/emails/reporte_ventas.txt`

```
📊 REPORTE DE VENTAS DEL DÍA — {{ fecha }}
{{ config.nombre_empresa }}
═══════════════════════════════════════════

RESUMEN:
  Pedidos pagados hoy: {{ total_pedidos }}
  Total facturado:     ${{ total_facturado }}

{% if top_productos %}
TOP PRODUCTOS:
{% for prod in top_productos %}
  {{ forloop.counter }}. {{ prod.nombre }}
     Unidades: {{ prod.unidades }} | Ingreso: ${{ prod.ingreso }}
{% endfor %}
{% else %}
Sin ventas registradas hoy.
{% endif %}

Panel de administración: {{ url_admin }}

───────────────────────────────────────────
Generado automáticamente a las {{ hora_programada }} (hora de México)
ERP Django · {{ config.nombre_empresa }}
```

---

## PARTE 2 — Tarea `reporte_ventas_diario` (25 min)

### 2.1 ¿Qué es `annotate` + `Sum(F())`?

```python
# Sin annotate — N+1 queries en Python:
for pedido in Pedido.objects.filter(hoy):
    total += pedido.total   # @property: 1 query por pedido

# Con annotate — 1 sola query SQL con SUM():
from django.db.models import Sum, F, ExpressionWrapper, DecimalField

DetalleVenta.objects.filter(
    venta__fecha__date=hoy
).values('producto__nombre').annotate(
    unidades=Sum('cantidad'),
    ingreso=Sum(
        ExpressionWrapper(
            F('cantidad') * F('precio_unitario'),
            output_field=DecimalField()
        )
    )
).order_by('-ingreso')[:5]
```

`F('campo')` referencia un campo de la BD sin traerlo a Python,
permitiendo que la multiplicación ocurra directamente en SQL.

---

### 2.2 Agregar `reporte_ventas_diario` a `ventas/tasks.py`

Agregar al final del archivo `ventas/tasks.py` (después de `_enviar_alerta_stock`).
Reutiliza `_url_absoluta()` e `_items_con_subtotal()` de W17:

```python
# ── W18: reporte diario (Celery Beat) ─────────────────────────────────────

@shared_task(
    bind=True,
    max_retries=2,
    name='ventas.reporte_ventas_diario',
)
def reporte_ventas_diario(self) -> dict:
    """Genera y envía el reporte diario de ventas al administrador.

    Se ejecuta automáticamente todos los días a la hora de
    settings.REPORTE_DIARIO_HORA (default 08:00, hora de México)
    mediante Celery Beat (configurado en CELERY_BEAT_SCHEDULE).

    Cálculos realizados en SQL (no en Python) para máxima eficiencia:
        - Total de pedidos pagados hoy
        - Total facturado (suma de total_pagado)
        - Top 5 productos por ingreso del día

    Returns:
        dict con total_pedidos, total_facturado y top_productos.
    """
    from decimal import Decimal

    from django.db.models import (
        DecimalField, ExpressionWrapper, F, Sum,
    )
    from django.utils import timezone

    from configuracion.models import ConfiguracionERP   # import local
    from ventas.models        import DetalleVenta, Pedido  # import local

    hoy    = timezone.localdate()
    config = ConfiguracionERP.get_instance()

    # ── 1. KPIs del día ───────────────────────────────────────────────
    pedidos_hoy = Pedido.objects.filter(
        fecha_pedido__date=hoy,
        estado='pagado'
    )
    total_pedidos   = pedidos_hoy.count()
    total_facturado = pedidos_hoy.aggregate(
        total=Sum('total_pagado')
    )['total'] or Decimal('0.00')

    # ── 2. Top 5 productos por ingreso del día ─────────────────────────
    # Dos fuentes: ventas internas (DetalleVenta) y compras de la tienda
    # en línea (Pedido.items_snapshot). El checkout NO crea Venta, así
    # que sin la segunda fuente las compras en línea nunca aparecían.
    acumulado = {}   # nombre → {'unidades': int, 'ingreso': Decimal}

    internas = (
        DetalleVenta.objects
        .filter(venta__fecha__date=hoy)
        .values(nombre=F('producto__nombre'))
        .annotate(
            unidades=Sum('cantidad'),
            ingreso=Sum(
                ExpressionWrapper(
                    F('cantidad') * F('precio_unitario'),
                    output_field=DecimalField(max_digits=12, decimal_places=2)
                )
            )
        )
    )
    for fila in internas:
        dato = acumulado.setdefault(
            fila['nombre'], {'unidades': 0, 'ingreso': Decimal('0.00')}
        )
        dato['unidades'] += fila['unidades'] or 0
        dato['ingreso']  += fila['ingreso'] or Decimal('0.00')

    for pedido in pedidos_hoy.only('items_snapshot'):
        for item in _items_con_subtotal(pedido.items_snapshot):
            dato = acumulado.setdefault(
                item.get('nombre', '¿?'),
                {'unidades': 0, 'ingreso': Decimal('0.00')},
            )
            dato['unidades'] += item['cantidad']
            dato['ingreso']  += item['subtotal']

    top_productos = sorted(
        (
            {'nombre': nombre, 'unidades': d['unidades'],
             'ingreso': str(d['ingreso'].quantize(Decimal('0.01')))}
            for nombre, d in acumulado.items()
        ),
        key=lambda x: Decimal(x['ingreso']),
        reverse=True,
    )[:5]

    logger.info(
        f'[reporte_diario] {hoy}: {total_pedidos} pedidos, '
        f'${total_facturado} facturados, '
        f'{len(top_productos)} productos top.'
    )

    # ── 3. Enviar correo al admin si está configurado ──────────────────
    if settings.ADMINS:
        _enviar_reporte_ventas(
            hoy, total_pedidos, total_facturado, top_productos, config
        )

    return {
        'fecha':           str(hoy),
        'total_pedidos':   total_pedidos,
        'total_facturado': str(total_facturado),
        'top_productos':   top_productos,
    }


def _enviar_reporte_ventas(
    fecha, total_pedidos, total_facturado, top_productos, config
) -> None:
    """Envía el reporte diario al primer administrador configurado.

    Args:
        fecha:           Objeto date del día reportado.
        total_pedidos:   Número de pedidos pagados.
        total_facturado: Decimal con la suma total.
        top_productos:   Lista de dicts con nombre, unidades, ingreso.
        config:          Instancia de ConfiguracionERP.
    """
    url_admin = _url_absoluta('admin:ventas_pedido_changelist')
    fecha_str = fecha.strftime('%d/%m/%Y')

    contexto = {
        'fecha':           fecha_str,
        'config':          config,
        'total_pedidos':   total_pedidos,
        'total_facturado': total_facturado,
        'top_productos':   top_productos,
        'url_admin':       url_admin,
        'hora_programada': settings.REPORTE_DIARIO_HORA,
    }

    asunto      = f'Reporte de ventas del {fecha_str} — {config.nombre_empresa}'
    texto_plano = render_to_string('emails/reporte_ventas.txt',  contexto)
    html_body   = render_to_string('emails/reporte_ventas.html', contexto)

    admin_nombre, admin_correo = settings.ADMINS[0]

    mensaje = EmailMultiAlternatives(
        subject    = asunto,
        body       = texto_plano,
        from_email = settings.DEFAULT_FROM_EMAIL,
        to         = [admin_correo],
    )
    mensaje.attach_alternative(html_body, 'text/html')

    try:
        mensaje.send()
        logger.info(f'[reporte_diario] Reporte enviado a {admin_correo}.')
    except Exception as exc:
        logger.error(f'[reporte_diario] Error al enviar reporte: {exc}')
```

> ⚠️ **Correcciones respecto a la versión anterior de la guía:**
> - **Top 5 con dos fuentes.** El checkout de la tienda (W13–W15) crea un
>   `Pedido`, **nunca** una `Venta`. Si el Top solo consulta `DetalleVenta`,
>   las compras en línea no aparecen jamás. Las ventas internas se agregan
>   en SQL (`annotate` + `Sum(F() * F())`); las de la tienda vienen de
>   `items_snapshot` (JSON) y se suman en Python con `Decimal`.
> - `ingreso` se devuelve como texto (`'199.50'`): el resultado viaja como
>   JSON por Redis y así no hay problemas con `Decimal`.
> - **Sin URL fija** `erp-django-utec.onrender.com`: `_url_absoluta()` usa
>   `SITE_URL` (en Render, `RENDER_EXTERNAL_URL`).
> - El reporte resume el **día en curso**. Si se programa a primera hora,
>   casi siempre saldrá en cero: para un corte del día anterior habría que
>   usar `hoy - timedelta(days=1)`.

---

## PARTE 3 — `CELERY_BEAT_SCHEDULE` en `settings.py` (15 min)

### 3.1 Imports al inicio de `core/settings.py`

```python
# core/settings.py — junto a los demás imports, al inicio del archivo:
from celery.schedules import crontab
from datetime import timedelta   # ← necesario para CELERY_BEAT_SCHEDULE
```

> Los imports van **al inicio** (PEP 8), no a mitad del archivo como
> sugería la versión anterior.

### 3.2 Agregar después del bloque `CELERY_*` de W16

```python
# Hora del reporte diario (hora de México), configurable sin tocar código:
#   Render → Environment → REPORTE_DIARIO_HORA=10:00
REPORTE_DIARIO_HORA = env('REPORTE_DIARIO_HORA', default='08:00')
try:
    _rep_h, _rep_m = (int(x) for x in REPORTE_DIARIO_HORA.split(':'))
except ValueError:
    _rep_h, _rep_m = 8, 0

CELERY_BEAT_SCHEDULE = {

    # Verificar stock bajo cada hora
    'verificar-stock-bajo-cada-hora': {
        'task':     'ventas.verificar_stock_bajo',
        'schedule': timedelta(hours=1),
        'args':     (5,),   # umbral = 5 unidades
        'options':  {'queue': 'erp_django'},
    },

    # Reporte de ventas diario (default 8:00 AM hora México)
    'reporte-ventas-diario-8am': {
        'task':     'ventas.reporte_ventas_diario',
        'schedule': crontab(hour=_rep_h, minute=_rep_m),
        'options':  {'queue': 'erp_django'},
    },

}

# Necesario para que Beat use la zona horaria de Django (no UTC)
CELERY_BEAT_TIMEZONE = TIME_ZONE   # 'America/Mexico_City'
```

> **`crontab(hour=8, minute=0)`** equivale a la expresión cron `0 8 * * *`:
> ejecutar exactamente a las 8:00 AM todos los días, **hora de México**
> gracias a `CELERY_TIMEZONE = TIME_ZONE`.
>
> **`REPORTE_DIARIO_HORA`** permite probar sin esperar al día siguiente:
> en Render se pone `10:00` (o la hora actual + 10 min) y se guarda.
>
> **`timedelta(hours=1)`** es un intervalo: cuenta una hora desde que Beat
> arranca, no "en punto".

### 3.3 Verificar

```cmd
python manage.py check
python -c "import django,os;os.environ['DJANGO_SETTINGS_MODULE']='core.settings';django.setup();from django.conf import settings as s;print(s.CELERY_BEAT_SCHEDULE['reporte-ventas-diario-8am']['schedule'])"
```

**Resultado esperado:**
```
System check identified no issues (0 silenced).
<crontab: 0 8 * * * (m/h/dM/MY/d)>
```

---

## PARTE 4 — Beat embebido en Render + Dependencias (10 min)

> La versión anterior de esta guía agregaba un servicio `celery_beat` a
> `docker-compose.yml` con `django_celery_beat` (paquete que el proyecto
> **no** tiene instalado). Sin Docker Desktop y con Render Free, Beat se
> arranca dentro del worker embebido de W16.

### 4.1 `docker-entrypoint.sh` — worker con `--beat`

Reemplazar el bloque del worker embebido de W16 por:

```sh
# ── W16: worker de Celery embebido (opción gratuita de Render) ───────
# Render Free no ofrece Background Workers: el worker corre en segundo
# plano dentro del mismo contenedor que Gunicorn.
#   --pool=solo           → un solo proceso (cabe en 512 MB)
#   --without-gossip/mingle/heartbeat → menos conexiones a Redis
# Se activa con CELERY_EMBEDDED_WORKER=1 y requiere REDIS_URL.
#
# W18: Beat (tareas programadas) también va embebido con --beat, porque
# Render Free no tiene Background Workers. Solo debe existir UN Beat:
# el servicio web debe tener 1 instancia. Se desactiva con
# CELERY_EMBEDDED_BEAT=0. El archivo del schedule va a /tmp (disco efímero).
if [ "${CELERY_EMBEDDED_WORKER:-0}" = "1" ] && [ -n "${REDIS_URL:-}" ]; then
    BEAT_OPTS=""
    if [ "${CELERY_EMBEDDED_BEAT:-1}" = "1" ]; then
        BEAT_OPTS="--beat --schedule=/tmp/celerybeat-schedule"
        echo "==> [entrypoint] Celery Beat embebido ACTIVADO (reporte diario ${REPORTE_DIARIO_HORA:-08:00} hora MX)."
    fi
    echo "==> [entrypoint] Iniciando worker de Celery embebido (cola erp_django)..."
    # shellcheck disable=SC2086
    celery -A core worker \
        --loglevel=info \
        --queues=erp_django \
        --pool=solo \
        --without-gossip --without-mingle --without-heartbeat \
        $BEAT_OPTS &
else
    echo "==> [entrypoint] Worker de Celery embebido DESACTIVADO."
fi
```

> `--schedule=/tmp/...`: el archivo donde Beat recuerda la última ejecución
> va en `/tmp` porque el disco de Render es efímero.

### 4.2 `render.yaml` — variables de W18

```yaml
      # W18: Celery Beat embebido (tareas programadas). UNA sola instancia.
      - key: CELERY_EMBEDDED_BEAT    # 1 = worker arranca con --beat
        value: "1"
      - key: REPORTE_DIARIO_HORA     # HH:MM hora de México (crontab)
        value: "08:00"
```

### 4.3 ⚠️ Dependencias: `kombu` compatible con `redis==5.0.1`

Si `requirements.txt` se regeneró con `pip freeze`, puede traer
`kombu==5.7.0`, que exige `redis>=6.1`. En Render **ninguna tarea llega a
Redis** y el webhook registra:

```
kombu.exceptions.VersionMismatch: Redis transport requires redis-py
versions 6.1.0 or later. You have 5.0.1
```

En el laboratorio no se nota (modo EAGER no usa Redis). Corrección:

```cmd
pip install "kombu==5.3.7"
pip check
```

y en `requirements.txt` dejar `kombu==5.3.7` (editar a mano, en UTF-8).
La prueba `tests/test_w18_dependencias.py` (Parte 6) detecta este error.

### 4.4 Variables de entorno en Render (Environment)

| Variable | Valor | Error frecuente |
|---|---|---|
| `CELERY_EMBEDDED_WORKER` | `1` | — |
| `CELERY_EMBEDDED_BEAT` | **`1`** | Poner la hora aquí (`10:00`): Beat **no arranca** |
| `REPORTE_DIARIO_HORA` | `08:00` (pruebas: `10:00`) | Formato distinto de `HH:MM` → vuelve a 08:00 |
| `REDIS_URL` | Internal Key Value URL | — |
| `SENDGRID_API_KEY` | `SG....` | Sin ella el correo solo se imprime en los Logs |
| `DEFAULT_FROM_EMAIL` | `ERP Django <correo-del-From-verificado>` | Usar el **Reply-To** del Sender → SendGrid 403 |
| `ADMIN_EMAIL` | correo que recibe reporte y alertas | Errores de dedo en el dominio |

### 4.5 Render Free se duerme

El servicio gratuito se suspende tras ~15 min sin tráfico. **Dormido, Beat
no dispara** y Celery no recupera una ejecución perdida. Para el reporte
diario crear un monitor gratuito (UptimeRobot o cron-job.org) que haga
`GET https://TU-SERVICIO.onrender.com/` cada 10 minutos.

### 4.6 `docker-compose.yml` (opcional — solo con Docker Desktop)

En el laboratorio **no se usa**. Si algún equipo tiene Docker Desktop, el
stack local de W16 se completa con un servicio `celery_beat`, después de
`celery_worker`:

```yaml
  # ── Celery Beat — Scheduler de tareas programadas — W18 ────────────
  # Beat NUNCA debe tener múltiples réplicas (un solo scheduler).
  # Scheduler por defecto (archivo), igual que en Render: el proyecto no
  # instala django_celery_beat. En Render, Beat va embebido en el worker
  # (docker-entrypoint.sh, CELERY_EMBEDDED_BEAT=1); aquí es un servicio aparte.
  celery_beat:
    build:
      context: .
      dockerfile: Dockerfile
    restart: unless-stopped
    command: celery -A core beat -l info --schedule=/tmp/celerybeat-schedule
    volumes:
      - .:/app
    depends_on:
      redis:
        condition: service_healthy
      db:
        condition: service_healthy
    env_file:
      - .env                             # REPORTE_DIARIO_HORA, ADMIN_EMAIL...
    environment:
      DJANGO_SETTINGS_MODULE: core.settings_prod
      DATABASE_URL: postgresql://${POSTGRES_USER:-admin}:${POSTGRES_PASSWORD:-12345}@db:5432/${POSTGRES_DB:-erp_db}
      REDIS_URL: redis://redis:6379/0
```

> ⚠️ La versión anterior de esta guía usaba
> `--scheduler django_celery_beat.schedulers:DatabaseScheduler` (paquete
> **no instalado** → Beat no arranca), credenciales `erp_user/erp_pass_local`
> que no coinciden con el servicio `db` (`.env`) y no cargaba `.env`
> (sin `SENDGRID_API_KEY` ni `ADMIN_EMAIL`). Se corrigió con el mismo
> patrón que `celery_worker`. El servicio `web` mantiene
> `CELERY_EMBEDDED_WORKER: "0"`, así que nunca hay dos Beat.

---

## PARTE 5 — Verificar en Local (EAGER) y en Render (15 min)

### 5.1 En el laboratorio: ejecutar las tareas sin worker

```cmd
python manage.py shell
```

```python
from ventas.tasks import reporte_ventas_diario, verificar_stock_bajo

# Modo EAGER: se ejecutan en el mismo proceso; el correo sale en la terminal
print('Reporte:', reporte_ventas_diario.delay().get())
print('Stock bajo:', verificar_stock_bajo.delay(100).get()['total'])  # umbral alto
```

No se arrancan worker ni Beat en el laboratorio (no hay Redis).

### 5.2 En Render: Logs al desplegar

```
==> [entrypoint] Celery Beat embebido ACTIVADO (reporte diario 10:00 hora MX).
==> [entrypoint] Iniciando worker de Celery embebido (cola erp_django)...
[... INFO/Beat] beat: Starting...
[... INFO/MainProcess] Connected to redis://red-xxxxxxxxxxxx:6379//
[... INFO/MainProcess] celery@srv-xxxxxxxx ready.
```

Si aparece `Celery Beat embebido` pero no `beat: Starting...`, revisar
`CELERY_EMBEDDED_BEAT=1`. Si aparece `VersionMismatch`, ver 4.3.

### 5.3 Probar el reporte sin esperar al día siguiente

1. Render → Environment → `REPORTE_DIARIO_HORA` = hora actual + 10 min
   (p. ej. `10:00`) → **Save** (Render redespliega).
2. Mantener el servicio despierto (4.5).
3. A la hora indicada, en los Logs:
   ```
   Scheduler: Sending due task reporte-ventas-diario-8am (ventas.reporte_ventas_diario)
   Task ventas.reporte_ventas_diario[...] succeeded in 1.2s: {'fecha': '...', ...}
   ```
4. El correo *"Reporte de ventas del DD/MM/AAAA — Mi Empresa ERP"* llega a
   `ADMIN_EMAIL` (revisar Spam).
5. Regresar `REPORTE_DIARIO_HORA` a `08:00`.

### 5.4 Recuperar correos de confirmación no enviados

Si un pedido quedó **pagado** sin correo (p. ej. Redis caído o la falla de
4.3), el webhook no lo reenvía (ya estaba pagado). En
**Admin → Pedidos** filtrar *Correo de confirmación enviado = No*,
seleccionar y elegir la acción **"Enviar correo de confirmación
(pagados sin correo)"**. Render Free no tiene Shell, así que esta es
la vía de recuperación.

Agregar en `ventas/admin.py` (clase `PedidoAdmin`):

```python
    list_display   = ['numero_pedido', 'cliente', 'estado',
                      'fecha_pedido', 'total_pagado', 'correo_enviado']
    search_fields  = ['numero_pedido', 'cliente__nombre']
    list_filter    = ['estado', 'correo_enviado']
    readonly_fields = ['fecha_pedido']
    actions        = ['reenviar_confirmacion']

    @admin.action(description='Enviar correo de confirmación (pagados sin correo)')
    def reenviar_confirmacion(self, request, queryset):
        """Encola el correo de los pedidos pagados que aún no lo recibieron.

        Útil si el envío falló (p. ej. Redis/SendGrid caídos): Render Free
        no tiene Shell. La tarea es idempotente (correo_enviado).
        """
        from django.contrib import messages
        from ventas.tasks import enviar_confirmacion_pedido

        pendientes = queryset.filter(estado='pagado', correo_enviado=False)
        encolados, errores = 0, 0
        for pedido in pendientes:
            try:
                enviar_confirmacion_pedido.delay(pedido.pk)
                encolados += 1
            except Exception as exc:   # Redis caído, etc.
                errores += 1
                self.message_user(
                    request, f'{pedido.numero_pedido}: {exc}', messages.ERROR
                )
        omitidos = queryset.count() - pendientes.count()
        self.message_user(
            request,
            f'Correos encolados: {encolados}. Errores: {errores}. '
            f'Omitidos (no pagados o ya enviados): {omitidos}.',
            messages.SUCCESS if not errores else messages.WARNING,
        )
```

### 5.5 Flower

`flower==2.0.1` está instalado, pero en Render Free no se expone (sería un
segundo servicio web). En producción las tareas se monitorean con los
**Logs** del worker (`Task ... succeeded`).

---

## PARTE 6 — Tests W18 (20 min)

### 6.1 Crear `tests/test_w18_beat.py`

```python
"""Suite de pruebas W18 — Celery Beat y tarea de reporte diario.

Verifica la configuración del schedule, la ejecución de la tarea
y el envío del correo de reporte.

Ejecutar con:
    python manage.py test tests.test_w18_beat --verbosity=2

Resultado esperado:
    Ran 8 tests in X.XXXs
    OK
"""
from decimal import Decimal
from datetime import timedelta

from django.conf import settings
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from clientes.models      import Cliente
from configuracion.models import ConfiguracionERP
from productos.models     import Categoria, Producto
from ventas.models        import DetalleVenta, Pedido, Venta
from ventas.tasks         import reporte_ventas_diario, verificar_stock_bajo

EMAIL_SETTINGS = {
    'EMAIL_BACKEND':               'django.core.mail.backends.locmem.EmailBackend',
    'CELERY_TASK_ALWAYS_EAGER':    True,
    'CELERY_TASK_EAGER_PROPAGATES': True,
    'ADMINS':           [('Admin Test', 'admin@test.com')],
    'DEFAULT_FROM_EMAIL': 'test@erp.com',
}


class BeatScheduleConfigTest(TestCase):
    """Verifica la configuración de CELERY_BEAT_SCHEDULE."""

    def test_beat_schedule_tiene_verificar_stock(self):
        """El schedule debe incluir verificar_stock_bajo."""
        schedule = settings.CELERY_BEAT_SCHEDULE
        tareas   = [v['task'] for v in schedule.values()]
        self.assertIn('ventas.verificar_stock_bajo', tareas)

    def test_beat_schedule_tiene_reporte_diario(self):
        """El schedule debe incluir reporte_ventas_diario."""
        schedule = settings.CELERY_BEAT_SCHEDULE
        tareas   = [v['task'] for v in schedule.values()]
        self.assertIn('ventas.reporte_ventas_diario', tareas)

    def test_reporte_usa_crontab(self):
        """El reporte diario debe usar crontab (no timedelta)."""
        from celery.schedules import crontab
        schedule = settings.CELERY_BEAT_SCHEDULE
        for nombre, config in schedule.items():
            if config['task'] == 'ventas.reporte_ventas_diario':
                self.assertIsInstance(
                    config['schedule'], crontab,
                    "reporte_ventas_diario debe usar crontab, no timedelta"
                )
                break

    def test_verificar_stock_usa_timedelta(self):
        """verificar_stock_bajo debe usar timedelta (intervalo)."""
        schedule = settings.CELERY_BEAT_SCHEDULE
        for nombre, config in schedule.items():
            if config['task'] == 'ventas.verificar_stock_bajo':
                self.assertIsInstance(
                    config['schedule'], timedelta,
                    "verificar_stock_bajo debe usar timedelta"
                )
                break


@override_settings(**EMAIL_SETTINGS)
class ReporteVentasTest(TestCase):
    """Tests de la tarea reporte_ventas_diario."""

    def setUp(self):
        mail.outbox = []
        ConfiguracionERP.get_instance()
        cat      = Categoria.objects.create(nombre='Cat Rep')
        self.prod = Producto.objects.create(
            nombre='Producto Reporte', precio=Decimal('500.00'),
            stock=10, categoria=cat
        )
        cli        = Cliente.objects.create(
            nombre='Cliente Rep', correo='rep@test.com'
        )
        # Crear una venta de HOY
        venta = Venta.objects.create(cliente=cli)
        DetalleVenta.objects.create(
            venta=venta, producto=self.prod,
            cantidad=3, precio_unitario=Decimal('500.00')
        )
        # Crear un pedido pagado de HOY
        Pedido.objects.create(
            numero_pedido = 'PED-REP-001',
            cliente       = cli,
            estado        = 'pagado',
            total_pagado  = Decimal('1500.00'),
        )

    def test_reporte_envia_correo_al_admin(self):
        """La tarea debe enviar correo al administrador."""
        reporte_ventas_diario.delay()
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('admin@test.com', mail.outbox[0].to)

    def test_reporte_asunto_contiene_fecha(self):
        """El asunto debe contener la fecha del reporte."""
        reporte_ventas_diario.delay()
        fecha_str = timezone.localdate().strftime('%d/%m/%Y')
        self.assertIn(fecha_str, mail.outbox[0].subject)

    def test_reporte_sin_ventas_hoy_envia_correo(self):
        """Aunque no haya ventas, el reporte debe enviarse."""
        # Eliminar ventas y pedidos creados en setUp
        Pedido.objects.all().delete()
        DetalleVenta.objects.all().delete()

        reporte_ventas_diario.delay()

        self.assertEqual(len(mail.outbox), 1)
        # Verificar que menciona 0 pedidos en el texto plano
        cuerpo = mail.outbox[0].body
        self.assertIn('0', cuerpo)

    def test_reporte_devuelve_dict_con_totales(self):
        """La tarea debe devolver un dict con total_pedidos y facturado."""
        resultado = reporte_ventas_diario.delay().get()
        self.assertIn('total_pedidos',   resultado)
        self.assertIn('total_facturado', resultado)
        self.assertIn('top_productos',   resultado)
        self.assertGreaterEqual(resultado['total_pedidos'], 0)


# ── Regresión (2026-11-20): compras en línea y hora configurable ─────────

@override_settings(**EMAIL_SETTINGS)
class ReporteTiendaEnLineaTest(TestCase):
    """El checkout solo crea Pedido (no Venta): el top debe incluirlo."""

    def setUp(self):
        mail.outbox = []
        ConfiguracionERP.get_instance()
        cli = Cliente.objects.create(nombre='Cliente Web', correo='web@test.com')
        Pedido.objects.create(
            numero_pedido  = 'PED-WEB-001',
            cliente        = cli,
            estado         = 'pagado',
            total_pagado   = Decimal('231.42'),
            items_snapshot = [
                {'producto_id': 1, 'nombre': 'Vino Web',
                 'cantidad': 2, 'precio': '99.75'},
            ],
        )

    def test_top_incluye_productos_de_pedidos_en_linea(self):
        resultado = reporte_ventas_diario.delay().get()
        self.assertEqual(resultado['total_pedidos'], 1)
        self.assertEqual(
            resultado['top_productos'],
            [{'nombre': 'Vino Web', 'unidades': 2, 'ingreso': '199.50'}],
        )
        self.assertIn('Vino Web', mail.outbox[0].body)


class HoraReporteConfigurableTest(TestCase):
    """La hora del crontab sale de REPORTE_DIARIO_HORA (hora de México)."""

    def test_crontab_coincide_con_reporte_diario_hora(self):
        h, m = (int(x) for x in settings.REPORTE_DIARIO_HORA.split(':'))
        cron = settings.CELERY_BEAT_SCHEDULE['reporte-ventas-diario-8am']['schedule']
        self.assertEqual(cron.hour, {h})
        self.assertEqual(cron.minute, {m})
        self.assertEqual(settings.CELERY_TIMEZONE, 'America/Mexico_City')
```

### 6.2 Crear `tests/test_w18_dependencias.py`

```python
"""Regresión 2026-11-20 — compatibilidad kombu ↔ redis-py.

En Render el webhook fallaba con:
    kombu.exceptions.VersionMismatch: Redis transport requires
    redis-py versions 6.1.0 or later. You have 5.0.1
porque requirements.txt tenía kombu==5.7.0 con redis==5.0.1.
En el laboratorio no se notaba: sin REDIS_URL todo corre en modo EAGER.

Esta prueba abre el transporte Redis contra un puerto cerrado: debe
fallar por CONEXIÓN (no hay Redis local), nunca por versión.
"""
from django.test import SimpleTestCase
from kombu import Connection
from kombu.exceptions import VersionMismatch


class KombuRedisCompatibilidadTest(SimpleTestCase):

    def test_transporte_redis_acepta_version_de_redis_py(self):
        conexion = Connection('redis://127.0.0.1:6399/0', connect_timeout=1)
        try:
            conexion.ensure_connection(max_retries=1, interval_start=0, interval_step=0)
            conexion.default_channel
        except VersionMismatch as exc:
            self.fail(f'kombu y redis-py incompatibles: {exc}')
        except Exception:
            pass   # esperado: no hay Redis en el laboratorio
        finally:
            conexion.release()


from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings

from clientes.models      import Cliente
from configuracion.models import ConfiguracionERP
from ventas.models        import Pedido


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    CELERY_TASK_ALWAYS_EAGER=True,
)
class AccionReenviarConfirmacionTest(TestCase):
    """Acción del admin: enviar correo a pagados con correo_enviado=False."""

    def setUp(self):
        ConfiguracionERP.get_instance()
        self.admin = get_user_model().objects.create_superuser(
            'root', 'root@test.com', 'x')
        self.client.force_login(self.admin)
        cli = Cliente.objects.create(nombre='C', correo='c@test.com')
        self.pagado = Pedido.objects.create(
            numero_pedido='PED-A-1', cliente=cli, estado='pagado',
            total_pagado=Decimal('30.16'))
        self.pendiente = Pedido.objects.create(
            numero_pedido='PED-A-2', cliente=cli, estado='pendiente')

    def test_envia_solo_pagados_sin_correo(self):
        resp = self.client.post('/admin/ventas/pedido/', {
            'action': 'reenviar_confirmacion',
            '_selected_action': [self.pagado.pk, self.pendiente.pk],
        })
        self.assertEqual(resp.status_code, 302)   # la acción redirige a la lista
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('PED-A-1', mail.outbox[0].subject)
        self.pagado.refresh_from_db()
        self.assertTrue(self.pagado.correo_enviado)
```

### 6.3 Ejecutar los tests

```cmd
python manage.py test tests.test_w18_beat tests.test_w18_dependencias --verbosity=2
```

**Resultado esperado:** `Ran 12 tests … OK` (10 de Beat/reporte + 2 de
dependencias y acción del admin).

### 6.4 Suite acumulada — Hito M6 (en verde)

Antes de W18 la suite arrastraba 11 fallas heredadas. Se corrigen así:

| Prueba | Causa | Corrección |
|---|---|---|
| W01 `/clientes/` → 404 | Desde W07 la lista vive en `/clientes/lista/` (enlace del menú del admin roto) | `clientes/urls.py`: `path('', ClienteListView, name='inicio')` |
| W02 (4) `<app>:inicio` / `index.html` | W07 reemplazó las vistas `index` por CBV | Pruebas → `<app>:lista` / `<app>/lista.html` |
| W03 ficha E1 | Faltaba `fichas/espiral_01_infra.md` | Crear la ficha (plantilla de W03) |
| W08 (2) mensajes en inglés | `LANGUAGE_CODE='es-mx'` y `assertFormError` de Django 4.2 | Validar `form.errors[campo]`, no el texto |
| W12 (3) `libgobject` | WeasyPrint necesita GTK; el `import` iba antes del 404 | Import después de `get_object_or_404`; `skipUnless` en las 2 pruebas que generan PDF |

```cmd
python manage.py test tests --verbosity=0
```

**Resultado esperado:** `Ran 171 tests … OK (skipped=2)`
(los 2 omitidos generan PDF y corren en Docker/Render).

### COMMIT PARCIAL

```cmd
git add .
git commit -m "Sprint 5 W18: Beat embebido + reporte_diario + kombu 5.3.7 + 171 tests OK [pre-M6]"
```

---

## PARTE 7 — Sprint 5 Review ante el asesor (20 min)

### Guión de demo (≤ 10 min en vivo, sobre Render)

```
1. Logs de Render: beat: Starting... · Connected to redis://... · celery@... ready.

2. Correo de confirmación:
   → Compra en https://TU-SERVICIO.onrender.com/catalogo/ con tarjeta 4242
   → Logs: Webhook recibido: payment_intent.succeeded
           Task ventas.enviar_confirmacion_pedido[...] succeeded ... 'estado': 'ok'
   → Bandeja: "Confirmación de pedido PED-AAAA-NNNN — ..."
   → Admin → Pedidos: Correo de confirmación enviado ✔

3. Reporte programado:
   → REPORTE_DIARIO_HORA = hora actual + 10 min (5.3)
   → Logs: Scheduler: Sending due task reporte-ventas-diario-8am
   → Bandeja de ADMIN_EMAIL: "Reporte de ventas del DD/MM/AAAA — ..."

4. Alerta de stock: verificar_stock_bajo corre cada hora (timedelta);
   en local: verificar_stock_bajo.delay(100).get() → correo en la terminal

5. Tests: python manage.py test tests --verbosity=0 → Ran 171 tests … OK

6. Declarar: "Celery activo + correo recibido + alerta de stock +
   Beat programado (8:00 AM diario + cada hora)" → ✅ HITO M6 ALCANZADO
```

### Tabla de verificación M6

| Criterio | Evidencia | Estado |
|---|---|---|
| Worker embebido procesa tareas | Logs: `celery@... ready` + `Task ... succeeded` | ✅ |
| Beat embebido activo | Logs: `beat: Starting...` | ✅ |
| Pago confirmado → correo de confirmación | Correo recibido vía SendGrid | ✅ |
| Stock bajo → alerta al admin | Test + correo local | ✅ |
| Reporte diario por crontab | Correo recibido a la hora programada | ✅ |
| Verificación de stock cada hora (timedelta) | `CELERY_BEAT_SCHEDULE` + test | ✅ |
| Monitoreo de tareas | Logs del worker (Flower no se expone en Render Free) | ✅ |
| 171 tests acumulados OK | `Ran 171 tests … OK (skipped=2)` | ✅ |

---

## PARTE 8 — Sprint 5 Retrospectiva + Ficha Schmelkes E6 (20 min)

### 8.1 Crear `sprint5_retrospective.md`

```markdown
# Sprint 5 Retrospective — ERP Django
## Semanas W16–W18 · Espiral 6: Celery e Integraciones

**Fecha:** 20/11/2026

## ¿Qué funcionó bien? (Keep)
1. El campo `correo_enviado` en `Pedido` resolvió los duplicados (reintentos
   de Stripe y de Celery) sin un sistema externo de idempotencia.
2. `@override_settings(EMAIL_BACKEND=locmem)` hizo triviales los tests de
   correo: `mail.outbox` captura todo sin enviar nada.
3. Modo EAGER sin `REDIS_URL`: el laboratorio sin Docker Desktop puede
   desarrollar y probar todas las tareas sin Redis ni worker.
4. El webhook como ÚNICO disparador del correo, con `try/except`: si Redis
   falla, el pago queda registrado y Stripe recibe 200.
5. Worker y Beat embebidos en el contenedor web: Celery funciona en el
   plan gratuito de Render (sin Background Workers).

## ¿Qué mejorar? (Improve)
1. **Dependencias:** `pip freeze` subió `kombu` a 5.7.0, que exige
   `redis>=6.1`, con `redis==5.0.1` fijo. En producción ninguna tarea
   llegaba a Redis y en el laboratorio no se veía (EAGER no usa Redis).
   Se fijó `kombu==5.3.7` y se agregó `tests/test_w18_dependencias.py`.
2. **Variables de entorno:** valores capturados en el campo equivocado
   (`CELERY_EMBEDDED_BEAT=10:00`, `DEFAULT_FROM_EMAIL` = Reply-To en vez
   del From verificado). Revisar la tabla de variables antes de desplegar.
3. **Render Free se duerme:** Beat no dispara mientras el servicio duerme;
   se necesita un ping externo cada 10 min.
4. **Pruebas antiguas desactualizadas:** 11 fallas heredadas de W01–W12
   (rutas cambiadas en W07, mensajes en español, WeasyPrint sin GTK en
   Windows, ficha E1 faltante). Corregidas en este cierre.

## Acción de mejora (Kaizen) para Sprint 6
> "En el Sprint 6 no regeneraré `requirements.txt` con `pip freeze`:
>  agregaré solo la dependencia nueva y correré `pip check` y la prueba de
>  compatibilidad kombu↔redis antes de cada push. Y pre-calcularé los KPIs
>  del Dashboard con `annotate` desde el principio."

## Velocidad del Sprint 5

| HU | Pts plan. | Pts ent. |
|---|---|---|
| HU-E6-01 Infraestructura Celery+Redis | 3 | 3 |
| HU-E6-02 Tareas sin bloquear HTTP | 2 | 2 |
| HU-E6-03 Correo confirmación post-pago | 5 | 5 |
| HU-E6-04 Alerta stock bajo | 3 | 3 |
| HU-E6-05 Reporte diario 8 AM | 3 | 3 |
| HU-E6-06 Monitorear con Flower | 2 | 2 |
| **Total** | **18** | **18** |

**Velocidad Sprint 5:** 18 puntos
**Velocidad acumulada (S0–S5):** 123 puntos
**Tests al cierre:** 171 (OK, 2 skipped por GTK en Windows)
```

---

### 8.2 Crear `fichas/espiral_06_async.md`

```markdown
# Ficha de Sistematización — Espiral 6
## ERP Django · Espiral E6: Celery e Integraciones
## UTEC Celaya · Técnico en Programación (SEP 3061300006-23)

| Campo | Contenido |
|---|---|
| **Número de espiral** | 6 |
| **Nombre del ciclo** | Celery e Integraciones |
| **Semanas** | W16 – W18 |
| **Fecha de inicio** | ___/___/_____ |
| **Fecha de cierre** | 20/11/2026 |
| **Responsable** | [Nombre del estudiante] |
| **Asesor** | MC. Román Fernando López González |

---

## 1. Objetivo del ciclo

Implementar procesamiento asíncrono con Celery y Redis para:
correos transaccionales de confirmación de pedido, alertas de
stock bajo y reportes diarios automáticos vía Celery Beat, en un
entorno sin Docker Desktop (laboratorio en modo EAGER) y con
producción en el plan gratuito de Render.

---

## 2. Tareas realizadas

| # | Tarea | Estado | Semana |
|---|---|---|---|
| 1 | Celery 5.3.6 + redis 5.0.1 + flower 2.0.1 | ✅ | W16 |
| 2 | `core/celery.py` + `core/__init__.py` | ✅ | W16 |
| 3 | `CELERY_*` en settings: Redis si hay `REDIS_URL`, EAGER si no | ✅ | W16 |
| 4 | Worker embebido en `docker-entrypoint.sh` (`CELERY_EMBEDDED_WORKER=1`) | ✅ | W16 |
| 5 | Webhook `payment_intent.succeeded` como único disparador del correo | ✅ | W16 |
| 6 | `django-anymail[sendgrid]==10.3`; SendGrid en prod si hay API Key | ✅ | W17 |
| 7 | `Pedido.correo_enviado` + migración 0004 (idempotencia) | ✅ | W17 |
| 8 | Templates `confirmacion_pedido` y `alerta_stock` (.html + .txt) con `items_snapshot` | ✅ | W17 |
| 9 | `enviar_confirmacion_pedido`: correo real + idempotencia + retry | ✅ | W17 |
| 10 | `verificar_stock_bajo`: alerta al admin | ✅ | W17 |
| 11 | Templates `reporte_ventas` (.html + .txt) con KPIs y tabla | ✅ | W18 |
| 12 | `reporte_ventas_diario` con `annotate` + `Sum(F('cantidad') * F('precio_unitario'))` | ✅ | W18 |
| 13 | `CELERY_BEAT_SCHEDULE`: crontab(hour=8, minute=0) + timedelta(hours=1) | ✅ | W18 |
| 14 | Beat embebido en el worker de Render (`--beat`) | ✅ | W18 |
| 15 | Fix `kombu==5.3.7` (VersionMismatch con redis-py 5.0.1) | ✅ | W18 |
| 16 | Acción admin para reenviar confirmación de pagados sin correo | ✅ | W18 |

---

## 3. Evidencias

- Pruebas: `python manage.py test tests` → **Ran 171 tests — OK (skipped=2)**
  (los 2 omitidos generan PDF con WeasyPrint y requieren GTK: corren en Docker/Render)
- Pruebas de la espiral: `test_w16_celery` (9), `test_w17_correo` (12),
  `test_w18_beat` (10), `test_w18_dependencias` (2)
- Correo de confirmación: consola local `Resultado 1: ok` / `Resultado 2: skip`
- Logs de Render a verificar tras desplegar:
  - [ ] `Celery Beat embebido ACTIVADO (reporte diario HH:MM hora MX)`
  - [ ] `celery@... ready.` y `beat: Starting...` sin `VersionMismatch`
  - [ ] `Task ventas.enviar_confirmacion_pedido[...] succeeded ... 'estado': 'ok'`
  - [ ] `Scheduler: Sending due task reporte-ventas-diario-8am`
- [ ] Captura del correo recibido: `evidencias/espiral_06/correo_confirmacion.png`
- [ ] Captura del reporte diario: `evidencias/espiral_06/reporte_diario.png`

---

## 4. Criterios de aceptación

| Criterio | Estado |
|---|---|
| Worker procesa `enviar_confirmacion_pedido` | ✅ (EAGER local · Render tras fix kombu) |
| `correo_enviado=True` previene duplicados | ✅ |
| Alerta de stock enviada al admin | ✅ |
| `reporte_ventas_diario` en `CELERY_BEAT_SCHEDULE` | ✅ |
| `verificar_stock_bajo` en `CELERY_BEAT_SCHEDULE` | ✅ |
| 171 tests OK | ✅ |

---

## 5. Problemas encontrados

| Problema | Causa | Solución aplicada |
|---|---|---|
| Sin Docker Desktop en el laboratorio | Política del equipo | Modo EAGER sin `REDIS_URL`; Redis/worker solo en Render |
| Render Free sin Background Workers | Plan gratuito | Worker y Beat embebidos en el contenedor web |
| Webhook: `VersionMismatch: redis-py 6.1.0 or later` | `pip freeze` subió `kombu` a 5.7.0 | `kombu==5.3.7` + prueba de compatibilidad |
| Reporte de las 8:30 nunca llegó | Worker sin `--beat` y servicio dormido | `--beat` en el entrypoint + ping externo |
| Top de productos vacío | El checkout crea `Pedido`, no `Venta` | Top suma también `items_snapshot` |
| SendGrid 403 | `DEFAULT_FROM_EMAIL` ≠ remitente verificado | Usar el From del Single Sender |
| `requirements.txt` en UTF-16 | `pip freeze >` en PowerShell | Editar a mano / usar cmd |

---

## 6. Lecciones aprendidas

1. El modo EAGER es ideal para desarrollar, pero oculta los errores de
   conexión con el broker: hay que probar el transporte real o al menos
   la compatibilidad de versiones.
2. La idempotencia (`correo_enviado`) se diseña desde el modelo, no se
   agrega después.
3.

---

## 7. Tiempo total invertido

| Categoría | Horas |
|---|---|
| Diseño | |
| Implementación | |
| Pruebas | |
| Documentación | |
| **Total Espiral 6** | |
```

---

## CIERRE — Commit Final [M6] y Respaldo (10 min)

### Actualizar `sprint5_planning.md`

```markdown
## Sprint 5 — Estado final W18

| HU | Historia | Estado | Pts |
|---|---|---|---|
| HU-E6-01 | Infraestructura Celery+Redis funcional | ✅ Completada | 3 |
| HU-E6-02 | Tareas sin bloquear HTTP | ✅ Completada | 2 |
| HU-E6-03 | Correo de confirmación post-pago | ✅ Completada | 5 |
| HU-E6-04 | Correo de alerta de stock bajo | ✅ Completada | 3 |
| HU-E6-05 | Reporte diario de ventas a las 8 AM | ✅ Completada | 3 |
| HU-E6-06 | Monitorear tareas con Flower | ✅ Completada | 2 |
| **Total** | | | **18/18** |

## Sprint Backlog — actualización W18

| Tarea | Estado |
|---|---|
| reporte_ventas_diario: annotate + Sum(F('cantidad') * F('precio_unitario')) | ✅ W18 |
| Top 5 incluye compras en línea (Pedido.items_snapshot) | ✅ W18 |
| Templates reporte_ventas.html + .txt (KPIs + tabla) | ✅ W18 |
| CELERY_BEAT_SCHEDULE: reporte crontab(hour=8, minute=0) + stock timedelta(hours=1) | ✅ W18 |
| Hora configurable REPORTE_DIARIO_HORA (Render: 10:00 para pruebas) | ✅ W18 |
| Beat embebido en el worker de Render (--beat, CELERY_EMBEDDED_BEAT=1) | ✅ W18 |
| Fix kombu 5.7.0 → 5.3.7 (VersionMismatch con redis 5.0.1) | ✅ W18 |
| Acción admin "Enviar correo de confirmación" (pagados sin correo) | ✅ W18 |
| Suite completa en verde | ✅ W18 |

## Hito M6 — ALCANZADO ✅
- Worker: embebido en el contenedor web de Render (`--pool=solo`)
- Beat: embebido en el worker (`--beat`), una sola instancia
- Correo: enviar_confirmacion_pedido → solo desde el webhook, idempotente
- Alerta: verificar_stock_bajo → cada hora, correo al admin
- Reporte: crontab(hour=8, minute=0) → 8:00 AM hora de México
  (configurable con REPORTE_DIARIO_HORA)
- Tests: Ran 171 tests → OK (2 skipped: PDF requiere GTK, corre en Docker/Render)
- Fecha: 20/Noviembre/2026

### Observaciones de verificación (2026-11-20)
- Laboratorio sin Docker Desktop: Redis, worker, Beat y Flower solo
  existen en Render; localmente todo corre en modo EAGER.
- En Render el correo no llegaba por `kombu==5.7.0` + `redis==5.0.1`
  (VersionMismatch). Corregido; confirmar en los Logs tras el despliegue.
- Render Free se duerme sin tráfico: Beat solo dispara si el servicio
  está despierto (ping externo cada 10 min).
- Flower (HU-E6-06) está instalado (`flower==2.0.1`), pero no se expone
  en Render Free: en producción se monitorea con los Logs del worker.
```

### Commit final de la Espiral 6

```cmd
git add .
git status

:: Verificar que incluye:
::   ventas/tasks.py (reporte_ventas_diario con dos fuentes)
::   ventas/admin.py (acción "Enviar correo de confirmación")
::   templates/emails/reporte_ventas.html + .txt
::   core/settings.py (CELERY_BEAT_SCHEDULE + REPORTE_DIARIO_HORA)
::   docker-entrypoint.sh (worker --beat)
::   docker-compose.yml (celery_beat opcional, solo Docker Desktop)
::   render.yaml (CELERY_EMBEDDED_BEAT, REPORTE_DIARIO_HORA)
::   requirements.txt (kombu==5.3.7, UTF-8)
::   tests/test_w18_beat.py + tests/test_w18_dependencias.py
::   clientes/urls.py, ventas/views.py y pruebas W02/W08/W12 corregidas
::   fichas/espiral_01_infra.md + fichas/espiral_06_async.md
::   sprint5_retrospective.md + sprint5_planning.md

git commit -m "Sprint 5 CIERRE [M6]: Beat embebido + reporte_diario + 171 tests OK + Fichas E1/E6"
git push origin main
```

### Ejecutar `finalizar_sesion.bat`

```cmd
E:\finalizar_sesion.bat
```

---

## CHECKLIST FINAL W18 — HITO M6

### Técnico

```
TAREA REPORTE DIARIO
[ ] ventas/tasks.py: reporte_ventas_diario(@shared_task)
[ ] annotate + Sum(F('cantidad') * F('precio_unitario')) para ventas internas
[ ] Top 5 suma también Pedido.items_snapshot (compras en línea)
[ ] Pedidos pagados de HOY: fecha_pedido__date=timezone.localdate()
[ ] Envía correo a ADMINS[0]; url_admin con SITE_URL (sin URL fija)
[ ] Devuelve dict con fecha, total_pedidos, total_facturado, top_productos

TEMPLATES
[ ] reporte_ventas.html con KPI grid y tabla top productos
[ ] reporte_ventas.txt (versión texto plano)
[ ] Pie con {{ hora_programada }} (no "8:00 AM" fijo)

CELERY BEAT
[ ] Imports crontab y timedelta al inicio de settings.py
[ ] verificar_stock_bajo: timedelta(hours=1) con args=(5,)
[ ] reporte_ventas_diario: crontab desde REPORTE_DIARIO_HORA (default 08:00)
[ ] CELERY_BEAT_TIMEZONE = TIME_ZONE

RENDER
[ ] docker-entrypoint.sh: worker con --beat --schedule=/tmp/celerybeat-schedule
[ ] CELERY_EMBEDDED_BEAT=1 (no la hora)
[ ] REPORTE_DIARIO_HORA=HH:MM
[ ] requirements.txt: kombu==5.3.7 con redis==5.0.1 (pip check OK)
[ ] Logs: beat: Starting... · Connected to redis · celery@... ready
[ ] Correo de confirmación recibido tras una compra
[ ] Correo de reporte recibido a la hora programada
[ ] Ping externo cada 10 min (Render Free se duerme)

TESTS
[ ] test tests.test_w18_beat → 10/10 OK
[ ] test tests.test_w18_dependencias → 2/2 OK
[ ] test tests → 171 OK (skipped=2)

SCRUM / SCHMELKES
[ ] sprint5_planning.md: 18/18 puntos entregados
[ ] sprint5_retrospective.md: Keep · Improve · Kaizen · velocidad
[ ] fichas/espiral_06_async.md completa
[ ] fichas/espiral_01_infra.md (requerida por test_w03_deploy)
[ ] Commit de cierre con etiqueta [M6] + git push
[ ] finalizar_sesion.bat → archivos en USB
```

---

## DIAGRAMA: Arquitectura de Celery al cerrar Espiral 6 (Render Free)

```
┌─────────────────────── Contenedor web en Render (1 instancia) ───────────────────────┐
│                                                                                      │
│  Gunicorn (Django)                          Celery worker --pool=solo --beat         │
│  ─────────────────                          ─────────────────────────────────        │
│  POST /catalogo/webhook/                    Worker: ejecuta las tareas de la cola    │
│    → pedido.estado = 'pagado'               Beat:   cada hora → verificar_stock_bajo │
│    → descontar stock (W15)                          REPORTE_DIARIO_HORA →            │
│    → try: enviar_confirmacion_pedido                   reporte_ventas_diario         │
│           .delay(pk)  ──────────┐                          │                         │
│                                 │                          │                         │
│  GET /catalogo/pago-exitoso/    │                          │                         │
│    → vacía carrito (NO encola)  │                          │                         │
└─────────────────────────────────┼──────────────────────────┼─────────────────────────┘
                                  ▼                          ▼
                     ┌─────────────────────────────────────────────┐
                     │ Render Key Value (Redis) — cola erp_django   │
                     └─────────────────────────────────────────────┘
                                  │
                                  ▼
                 anymail → SendGrid → ✉️ confirmación · ⚠️ alerta · 📊 reporte

Laboratorio (sin Docker): REDIS_URL vacía → EAGER → .delay() se ejecuta en el mismo
proceso y el correo se imprime en la terminal (backend de consola).
```

---

## HILO CONDUCTOR → W19

**¿Qué cierra W18 / Espiral 6?**
La automatización completa del ERP: correos transaccionales, alertas
y reportes ejecutándose de forma autónoma en Render. 171 tests verifican
cada pieza de la integración. Hito M6 declarado.

**¿Qué abre W19 / Espiral 7 / Sprint 6?**
Con todas las operaciones automatizadas, el siguiente paso es
**visualizar los datos**: un dashboard de KPIs con gráficas
en tiempo real usando Chart.js y consultas optimizadas con `annotate`.

**¿Qué necesita W19 de W18?**

| Artefacto de W18 | Uso en W19 |
|---|---|
| `reporte_ventas_diario` con `annotate` | El dashboard usa las mismas queries SQL pero en tiempo real |
| `Pedido.objects.filter(estado='pagado')` | El KPI de ventas del día usa este mismo filtro |
| Redis (Render Key Value) ya conectado | W19 usará `cache.set/get` con Redis para cachear el dashboard (el plan Free tiene 25 MB) |
| 171 tests pasando | W19 agrega tests de las vistas del dashboard |

**Tarea de investigación para W19:**
> Lee la documentación de Django sobre caché:
> `https://docs.djangoproject.com/en/4.2/topics/cache/`
>
> ¿Cómo se configura Redis como backend de caché en Django?
> ¿Qué diferencia hay entre `cache.set(key, value, timeout=300)`
> y el decorador `@cache_page(300)`?
> ¿Cuándo conviene cachear el resultado de una vista completa vs.
> cachear solo los datos de una consulta?

**Pregunta de reflexión:**
> "El `reporte_ventas_diario` usa `annotate` con `Sum(F(...))`.
> Si el administrador quiere ver este reporte en tiempo real
> desde el dashboard (no solo por correo), ¿debería llamarse
> a la tarea Celery o ejecutarse directamente en la vista?
> ¿Qué trade-off hay entre las dos opciones?"

---

## NOTAS — Observaciones de la verificación (2026-11-20)

Funcionamiento confirmado en Render: `beat: Starting...`, worker conectado
a Redis, correo de confirmación de una compra recibido vía SendGrid y
reporte diario recibido exactamente a la hora de `REPORTE_DIARIO_HORA`.

| # | Sección | Problema en la versión anterior | Corrección |
|---|---|---|---|
| 1 | Parte 4 | Beat como servicio de `docker-compose` con `django_celery_beat` (no instalado) | Beat embebido: `worker --beat` en `docker-entrypoint.sh` |
| 1b | 4.6 | `celery_beat` de `docker-compose.yml` con credenciales y scheduler erróneos | Servicio corregido (opcional, solo Docker Desktop) |
| 2 | Parte 5 | 4 terminales con Redis local y Flower en `:5555` | Laboratorio en EAGER; verificación con los Logs de Render |
| 3 | 2.2 | Top 5 solo de `DetalleVenta`: el checkout no crea `Venta` | Suma también `Pedido.items_snapshot` |
| 4 | 2.2 | URL fija `erp-django-utec.onrender.com` | `_url_absoluta()` con `SITE_URL` |
| 5 | 3.1 | `crontab` importado a mitad de `settings.py` | Imports al inicio |
| 6 | 3.1 / 1.x | Hora fija 8:00 en código y plantillas | `REPORTE_DIARIO_HORA` + `{{ hora_programada }}` |
| 7 | — | `kombu==5.7.0` con `redis==5.0.1` → `VersionMismatch` en Render | `kombu==5.3.7` + `test_w18_dependencias.py` |
| 8 | — | Variables mal capturadas (`CELERY_EMBEDDED_BEAT=10:00`, Reply-To como remitente) | Tabla 4.4 |
| 9 | — | Render Free se duerme y Beat no dispara | Ping externo cada 10 min (4.5) |
| 10 | Diagrama | `pago_exitoso` encolaba el correo | Desde W16 solo el webhook encola |
| 11 | Arranque / 6.x | 163 → 171 con 8 pruebas | 159 → 171 (10 + 2 nuevas); 11 fallas heredadas corregidas (6.4) |
| 12 | Parte 8 / Cierre | Retro y ficha describían procesos separados y Flower | Contenido real del proyecto |

---

## Referencia rápida de comandos W18

```cmd
:: SESIÓN
E:\iniciar_sesion.bat
E:\finalizar_sesion.bat

:: DJANGO
python manage.py check
python manage.py runserver

:: CELERY → NO en el laboratorio (sin Docker/Redis: modo EAGER).
::   En Render: docker-entrypoint.sh arranca "celery -A core worker ... --beat"
::   con CELERY_EMBEDDED_WORKER=1 y CELERY_EMBEDDED_BEAT=1.

:: SHELL — ejecutar tareas inmediatamente (EAGER)
python manage.py shell
>>> from ventas.tasks import reporte_ventas_diario, verificar_stock_bajo
>>> reporte_ventas_diario.delay().get()
>>> verificar_stock_bajo.delay(100).get()

:: DEPENDENCIAS
pip install "kombu==5.3.7"
pip check

:: TESTS
python manage.py test tests.test_w18_beat tests.test_w18_dependencias --verbosity=2
python manage.py test tests --verbosity=0   (171 tests, skipped=2)

:: GIT
git add .
git commit -m "Sprint 5 CIERRE [M6]: descripción"
git push origin main
git log --oneline
```

---

*Guía de Laboratorio W18 · ERP Django*
*Espiral 6 Cierre · Sprint 5 Review + Retrospectiva · Hito M6*
*SEP 3061300006-23 · UTEC Celaya · MC. Román Fernando López González*

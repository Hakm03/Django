# Guía de Laboratorio — W19
## ERP Django · Espiral 7 · Semana 19 de 24
### Técnico en Programación (SEP 3061300006-23) · UTEC Celaya
### Asesor: MC. Román Fernando López González

---

| Campo | Detalle |
|---|---|
| **Semana** | W19 de 24 |
| **Espiral** | E7 — Dashboard y Reportes |
| **Sprint Scrum** | Sprint 6 — Planning |
| **Hito** | Sin hito propio · Avance hacia M7 (W21) |
| **Horario** | 16:45 – 19:45 (180 min) |
| **Nivel Schmelkes** | 4 — Funcionalidades Avanzadas |
| **Hilo conductor** | "W18 automatizó el reporte por correo. W19 lo pone en pantalla, en vivo y cacheado." |

---

## Respuesta a la tarea de investigación de W18

> **¿Cómo se configura Redis como backend de caché en Django 4.2?**
>
> Django 4.2 incluye un backend nativo de Redis — no requiere el
> paquete `django-redis`:
>
> ```python
> CACHES = {
>     'default': {
>         'BACKEND':  'django.core.cache.backends.redis.RedisCache',
>         'LOCATION': 'redis://localhost:6379/1',   # DB 1, no la 0
>     }
> }
> ```
>
> **¿Por qué una base de datos Redis distinta (`/1`) a la del broker Celery (`/0`)?**
> Si usáramos la misma DB, `cache.clear()` podría borrar accidentalmente
> mensajes pendientes del broker de Celery (y viceversa). Redis numera
> sus bases de datos internamente (0–15 por defecto); usar una distinta
> por servicio es la práctica estándar de aislamiento.
>
> **¿`cache.set()` vs `@cache_page()`?**
>
> | Mecanismo | Qué cachea | Granularidad |
> |---|---|---|
> | `cache.set(key, value, timeout)` | Un valor específico (dict, queryset evaluado) | Fina — tú decides qué cachear |
> | `@cache_page(300)` | La respuesta HTTP completa de una vista | Gruesa — toda la página, incluido HTML |
>
> **¿Cuándo cachear la vista completa vs. solo los datos?**
> `@cache_page` es ideal para páginas públicas sin personalización
> (ej. catálogo). Para el dashboard, donde queremos cachear los
> **cálculos** (KPIs, consultas SQL) pero el HTML puede variar
> ligeramente por usuario, es mejor cachear solo los datos con
> `cache.get_or_set()` y dejar que la vista renderice el HTML siempre.

---

## Objetivos de la sesión

Al terminar W19, el estudiante será capaz de:

1. Redactar el Sprint 6 Planning para la Espiral 7 (Dashboard y Reportes)
2. Configurar Redis como backend de caché de Django (separado del broker)
3. Calcular 5 KPIs del negocio con `aggregate()` en una sola query cada uno
4. Construir 3 datasets para gráficas con `annotate()` y `ExpressionWrapper`
5. Implementar `DashboardView` con `cache.get_or_set()` para evitar
   recalcular en cada petición
6. Renderizar 3 gráficas con Chart.js: línea, barras y dona
7. Escribir 8 tests que verifican los KPIs y el comportamiento del caché

---

## Stack tecnológico de W19

| Herramienta / Concepto | Novedad en W19 | Descripción |
|---|---|---|
| `django.core.cache.backends.redis.RedisCache` | ✅ Nuevo | Backend de caché nativo de Django 4.2 sobre Redis |
| `cache.get_or_set()` | ✅ Nuevo | Obtiene del caché o calcula y guarda si no existe |
| Chart.js 4.x (CDN) | ✅ Nuevo | Librería JS para gráficas de línea, barra y dona |
| `aggregate()` | ya usado (W15/W18) | Calcula un único valor (Sum, Count) sobre un queryset |
| `annotate()` + `ExpressionWrapper` | ya usado (W18) | Agrega un campo calculado por cada fila agrupada |

---

## Mapa de tiempo (180 min)

| Parte | Actividad | Tiempo |
|---|---|---|
| Arranque | Daily Scrum + Sprint 6 Planning + verificar W18 | 15 min |
| Parte 1 | Configurar `CACHES` con Redis (DB separada) | 15 min |
| Parte 2 | Función `_calcular_kpis()`: 5 KPIs + 3 datasets | 30 min |
| Parte 3 | `DashboardView` con `cache.get_or_set()` | 20 min |
| Parte 4 | Template `dashboard.html` con Chart.js (3 gráficas) | 45 min |
| Parte 5 | Actualizar `reportes/urls.py` y verificar | 10 min |
| Parte 6 | Tests W19 (8 pruebas) | 25 min |
| Cierre | Commit · `finalizar_sesion.bat` · hilo → W20 | 10 min |
| Buffer | | 10 min |
| **Total** | | **180 min** |

---

## ARRANQUE — Daily Scrum + Sprint 6 Planning (15 min)

```cmd
E:\iniciar_sesion.bat
```

### Daily Scrum

```
1. ¿Qué hice en W18?
   → Agregué la tarea reporte_ventas_diario, configuré Celery Beat
     con crontab y timedelta, y cerré el Sprint 5 con el Hito M6.

2. ¿Qué haré en W19?
   → Configuraré caché con Redis, calcularé 5 KPIs del negocio
     y construiré un dashboard con 3 gráficas Chart.js.

3. ¿Tengo algún impedimento?
   → (registrar aquí)
```

### Verificar estado

```cmd
python manage.py check
python manage.py test tests --verbosity=0
```

**Resultado esperado:** `System check identified no issues` · `Ran 171 tests … OK`

---

### Sprint 6 Planning

**Sprint Goal del Sprint 6:**
> *"Al finalizar el Sprint 6, el ERP mostrará un dashboard con 5 KPIs
> clave del negocio, 3 gráficas interactivas, exportación de reportes
> a Excel/PDF, y filtros parametrizables por fecha y producto — todo
> con tiempos de carga optimizados mediante caché."*

**Duración:** W19 (dashboard + KPIs) · W20 (exportación + filtros) · W21 (histórico + M7)

Crear `sprint6_planning.md`:

```markdown
# Sprint 6 Planning — ERP Django
## Semanas W19–W21 · Espiral 7: Dashboard y Reportes

**Sprint Goal:**
Al finalizar el Sprint 6, el ERP mostrará un dashboard con 5 KPIs,
3 gráficas interactivas, exportación de reportes y filtros
parametrizables, optimizado con caché Redis.

## HUs seleccionadas

| ID | Historia | Puntos | Semana |
|---|---|---|---|
| HU-E7-01 | Como gerente, quiero ver 5 KPIs clave del negocio | 3 | W19 |
| HU-E7-02 | Como gerente, quiero ver ventas de los últimos 7 días en gráfica | 3 | W19 |
| HU-E7-03 | Como gerente, quiero ver el top 5 de productos más vendidos | 2 | W19 |
| HU-E7-04 | Como admin, quiero exportar reportes filtrados por fecha | 3 | W20 |
| HU-E7-05 | Como admin, quiero filtrar reportes por producto y cliente | 2 | W20 |
| HU-E7-06 | Como admin, quiero ver histórico de cambios de precio | 3 | W21 |
| HU-E7-07 | Como dev, quiero que el dashboard cargue en menos de 1 segundo | 2 | W19 |

**Total Sprint 6:** 18 puntos

## DoD — Sprint 6
- GET /reportes/ con login → 5 KPIs visibles
- 3 gráficas Chart.js renderizadas con datos reales
- Segunda carga del dashboard < 100ms (caché Redis activo)
- Exportación de reportes filtrados a Excel/PDF (W20)
- Histórico de precios visible con django-simple-history (W21)
- python manage.py test → ≥ 179 tests OK
```

---

## PARTE 1 — Configurar `CACHES` con Redis (15 min)

### 1.1 Agregar `REDIS_CACHE_URL` al `.env`

```bash
# .env — agregar (DB 1, distinta de la DB 0 del broker Celery):
REDIS_CACHE_URL=redis://localhost:6379/1
```

### 1.2 Configurar `CACHES` en `core/settings.py`

Agregar después del bloque `CELERY_BEAT_SCHEDULE`:

```python
# core/settings.py — agregar:

# ── CACHÉ — Redis (DB separada del broker Celery) ──────────────────────────
# Django 4.2 incluye backend nativo de Redis (no requiere django-redis)
CACHES = {
    'default': {
        'BACKEND':  'django.core.cache.backends.redis.RedisCache',
        'LOCATION': env('REDIS_CACHE_URL', default='redis://localhost:6379/1'),
        'TIMEOUT':  300,   # 5 minutos por defecto
        'OPTIONS': {
            'db': 1,   # DB 1: separada de Celery (DB 0)
        }
    }
}
```

### 1.3 Actualizar `.env.example`

```bash
# .env.example — agregar:
REDIS_CACHE_URL=redis://localhost:6379/1
```

### 1.4 Verificar la conexión al caché

```cmd
python manage.py shell
```

```python
from django.core.cache import cache
cache.set('test_key', 'hola_cache', timeout=30)
print(cache.get('test_key'))   # debe imprimir: hola_cache
```

```cmd
python manage.py check
```

**Resultado esperado:** `System check identified no issues (0 silenced).`

---

## PARTE 2 — Función `_calcular_kpis()` (30 min)

### 2.1 Las 5 métricas del dashboard

| KPI | Cálculo | Tipo de query |
|---|---|---|
| Ventas del día | Suma de `total_pagado` de pedidos pagados hoy | `aggregate(Sum)` |
| Clientes nuevos hoy | Conteo de clientes creados hoy | `count()` |
| Stock crítico | Conteo de productos activos con stock < 5 | `count()` |
| Pedidos pendientes | Conteo de pedidos en estado `pendiente` | `count()` |
| Revenue mensual | Suma de `total_pagado` del mes en curso | `aggregate(Sum)` |

### 2.2 Reemplazar `reportes/views.py`

```python
# reportes/views.py
"""Vistas del módulo de Dashboard y Reportes — W19.

DashboardView calcula 5 KPIs y 3 datasets de gráficas, cacheando
el resultado en Redis durante 5 minutos para evitar recalcular
en cada petición.
"""
import json
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.utils import timezone
from django.views.generic import TemplateView

from clientes.models   import Cliente
from productos.models  import Producto
from ventas.models     import DetalleVenta, Pedido

CACHE_KEY_DASHBOARD = 'dashboard_kpis_v1'
CACHE_TTL_SEGUNDOS  = 300   # 5 minutos


def _calcular_kpis() -> dict:
    """Calcula los 5 KPIs y los 3 datasets de gráficas del dashboard.

    Todas las agregaciones usan SQL (aggregate/annotate), no Python,
    para minimizar el tiempo de cómputo. Esta función es costosa
    y por eso se invoca a través de cache.get_or_set().

    Returns:
        dict serializable con KPIs y datasets para Chart.js.
    """
    hoy          = timezone.localdate()
    inicio_mes   = hoy.replace(day=1)
    hace_7_dias  = hoy - timedelta(days=6)

    # ── KPI 1: Ventas del día ───────────────────────────────────────────
    ventas_dia_total = Pedido.objects.filter(
        fecha_pedido__date=hoy, estado='pagado'
    ).aggregate(total=Sum('total_pagado'))['total'] or Decimal('0.00')

    # ── KPI 2: Clientes nuevos hoy ───────────────────────────────────────
    clientes_nuevos = Cliente.objects.filter(creado__date=hoy).count()

    # ── KPI 3: Stock crítico ────────────────────────────────────────────
    stock_critico = Producto.objects.filter(
        activo=True, stock__lt=5
    ).count()

    # ── KPI 4: Pedidos pendientes ───────────────────────────────────────
    pedidos_pendientes = Pedido.objects.filter(estado='pendiente').count()

    # ── KPI 5: Revenue mensual ──────────────────────────────────────────
    revenue_mensual = Pedido.objects.filter(
        fecha_pedido__date__gte=inicio_mes, estado='pagado'
    ).aggregate(total=Sum('total_pagado'))['total'] or Decimal('0.00')

    # ── Dataset 1: Ventas de los últimos 7 días (gráfica de línea) ──────
    labels_dias    = []
    ventas_por_dia = []
    for i in range(7):
        dia   = hace_7_dias + timedelta(days=i)
        total = Pedido.objects.filter(
            fecha_pedido__date=dia, estado='pagado'
        ).aggregate(total=Sum('total_pagado'))['total'] or Decimal('0.00')
        labels_dias.append(dia.strftime('%d/%m'))
        ventas_por_dia.append(float(total))   # float: Chart.js no usa Decimal

    # ── Dataset 2: Top 5 productos por ingreso histórico (barras) ───────
    expr_ingreso = ExpressionWrapper(
        F('cantidad') * F('precio_unitario'),
        output_field=DecimalField(max_digits=12, decimal_places=2)
    )
    top_productos = list(
        DetalleVenta.objects
        .values(nombre=F('producto__nombre'))
        .annotate(ingreso=Sum(expr_ingreso))
        .order_by('-ingreso')[:5]
    )
    labels_productos  = [p['nombre'] for p in top_productos]
    valores_productos = [float(p['ingreso'] or 0) for p in top_productos]

    # ── Dataset 3: Ventas por categoría (dona) ───────────────────────────
    ventas_categoria = list(
        DetalleVenta.objects
        .values(categoria=F('producto__categoria__nombre'))
        .annotate(ingreso=Sum(expr_ingreso))
        .order_by('-ingreso')
    )
    labels_categorias  = [c['categoria'] for c in ventas_categoria]
    valores_categorias = [float(c['ingreso'] or 0) for c in ventas_categoria]

    return {
        'ventas_dia_total':    str(ventas_dia_total),
        'clientes_nuevos':     clientes_nuevos,
        'stock_critico':       stock_critico,
        'pedidos_pendientes':  pedidos_pendientes,
        'revenue_mensual':     str(revenue_mensual),
        'labels_dias':         labels_dias,
        'ventas_por_dia':      ventas_por_dia,
        'labels_productos':    labels_productos,
        'valores_productos':   valores_productos,
        'labels_categorias':   labels_categorias,
        'valores_categorias':  valores_categorias,
        'calculado_en':        timezone.now().isoformat(),
    }
```

> **Nota:** `float()` se aplica a cada valor de los datasets ANTES
> de que lleguen al template, porque `Decimal` no es serializable
> directamente a JSON por `json.dumps()`. Los KPIs textuales (mostrados
> como `${{ kpi }}` en el template) se guardan como `str` para
> preservar el formato decimal exacto.

---

## PARTE 3 — `DashboardView` con `cache.get_or_set()` (20 min)

### 3.1 Agregar la vista al final de `reportes/views.py`

```python
# reportes/views.py — agregar al final del archivo:

class DashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard principal con 5 KPIs y 3 gráficas Chart.js.

    Los datos se calculan con _calcular_kpis() y se cachean en Redis
    durante 5 minutos. Las peticiones subsecuentes dentro de esa
    ventana no ejecutan ninguna consulta SQL — solo leen de Redis.
    """

    template_name = 'reportes/dashboard.html'

    def get_context_data(self, **kwargs) -> dict:
        """Construye el contexto con KPIs y datasets JSON para Chart.js."""
        ctx = super().get_context_data(**kwargs)

        # cache.get_or_set: si la key existe y no expiró, NO ejecuta
        # _calcular_kpis(); si no existe o expiró, la ejecuta y guarda.
        kpis = cache.get_or_set(
            CACHE_KEY_DASHBOARD,
            _calcular_kpis,
            CACHE_TTL_SEGUNDOS
        )

        ctx.update(kpis)

        # Pre-serializar los datasets a JSON para inyectarlos en <script>
        ctx['chart_dias_json'] = json.dumps({
            'labels': kpis['labels_dias'],
            'data':   kpis['ventas_por_dia'],
        })
        ctx['chart_productos_json'] = json.dumps({
            'labels': kpis['labels_productos'],
            'data':   kpis['valores_productos'],
        })
        ctx['chart_categorias_json'] = json.dumps({
            'labels': kpis['labels_categorias'],
            'data':   kpis['valores_categorias'],
        })
        ctx['cache_ttl_minutos'] = CACHE_TTL_SEGUNDOS // 60

        return ctx
```

### 3.2 ¿Por qué `cache.get_or_set()` y no `cache.get()` + `cache.set()` manual?

```python
# Forma manual (2 pasos, riesgo de race condition):
kpis = cache.get(CACHE_KEY_DASHBOARD)
if kpis is None:
    kpis = _calcular_kpis()
    cache.set(CACHE_KEY_DASHBOARD, kpis, CACHE_TTL_SEGUNDOS)

# Forma con get_or_set (1 paso, atómico):
kpis = cache.get_or_set(CACHE_KEY_DASHBOARD, _calcular_kpis, CACHE_TTL_SEGUNDOS)
```

`get_or_set()` es más conciso y evita el patrón "leer-verificar-escribir"
que en alta concurrencia podría ejecutar `_calcular_kpis()` dos veces
si dos peticiones llegan simultáneamente con el caché vacío.

---

## PARTE 4 — Template `dashboard.html` con Chart.js (45 min)

### 4.1 Reemplazar `reportes/templates/reportes/index.html`

Renombrar conceptualmente a `dashboard.html` — crear el nuevo archivo:

```cmd
:: El archivo anterior era reportes/templates/reportes/index.html (W02 placeholder)
:: Ahora se crea el dashboard real:
```

Crear `reportes/templates/reportes/dashboard.html`:

```html
{% extends "base.html" %}
{% block title %}Dashboard{% endblock %}
{% block nav_reportes %}active{% endblock %}

{% block extra_css %}
<style>
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    @media (max-width: 900px) {
        .kpi-grid { grid-template-columns: repeat(2, 1fr); }
    }
    .kpi-tile {
        background: var(--clr-surface);
        border: 1px solid var(--clr-border);
        border-radius: 10px;
        padding: 1.1rem;
        text-align: center;
        box-shadow: var(--shadow-sm);
    }
    .kpi-tile .valor {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--clr-navy);
    }
    [data-theme="dark"] .kpi-tile .valor { color: var(--clr-sky); }
    .kpi-tile.gold .valor { color: var(--clr-gold); }
    .kpi-tile .etiqueta {
        font-size: .76rem;
        color: var(--clr-muted);
        text-transform: uppercase;
        letter-spacing: .04em;
        margin-top: .3rem;
    }
    .kpi-tile.alerta { border-color: var(--clr-danger); }
    .kpi-tile.alerta .valor { color: var(--clr-danger); }
    .chart-card {
        background: var(--clr-surface);
        border: 1px solid var(--clr-border);
        border-radius: 12px;
        padding: 1.25rem;
        box-shadow: var(--shadow-sm);
        margin-bottom: 1.5rem;
    }
    .chart-card h4 {
        font-family: 'Playfair Display', serif;
        font-size: 1.05rem;
        color: var(--clr-navy);
        margin: 0 0 1rem;
    }
    [data-theme="dark"] .chart-card h4 { color: var(--clr-sky); }
    .cache-badge {
        font-size: .72rem;
        color: var(--clr-muted);
        background: var(--clr-ice);
        padding: .2rem .6rem;
        border-radius: 12px;
    }
</style>
{% endblock %}

{% block content %}
<div class="erp-page-title">
    <h2>📊 Dashboard</h2>
    <span class="cache-badge ms-auto">
        ⚡ Datos cacheados {{ cache_ttl_minutos }} min
    </span>
</div>

<!-- ── 5 KPI TILES ──────────────────────────────────────────────── -->
<div class="kpi-grid">
    <div class="kpi-tile gold">
        <div class="valor">${{ ventas_dia_total }}</div>
        <div class="etiqueta">Ventas de hoy</div>
    </div>
    <div class="kpi-tile">
        <div class="valor">{{ clientes_nuevos }}</div>
        <div class="etiqueta">Clientes nuevos hoy</div>
    </div>
    <div class="kpi-tile {% if stock_critico > 0 %}alerta{% endif %}">
        <div class="valor">{{ stock_critico }}</div>
        <div class="etiqueta">Productos en stock crítico</div>
    </div>
    <div class="kpi-tile">
        <div class="valor">{{ pedidos_pendientes }}</div>
        <div class="etiqueta">Pedidos pendientes</div>
    </div>
    <div class="kpi-tile gold">
        <div class="valor">${{ revenue_mensual }}</div>
        <div class="etiqueta">Revenue del mes</div>
    </div>
</div>

<!-- ── GRÁFICA 1: VENTAS ÚLTIMOS 7 DÍAS (LÍNEA) ────────────────── -->
<div class="chart-card">
    <h4>📈 Ventas de los últimos 7 días</h4>
    <canvas id="chartVentasDias" height="90"></canvas>
</div>

<div class="row">
    <!-- ── GRÁFICA 2: TOP 5 PRODUCTOS (BARRAS) ─────────────────── -->
    <div class="col-md-7">
        <div class="chart-card">
            <h4>🏆 Top 5 productos por ingreso</h4>
            <canvas id="chartTopProductos" height="180"></canvas>
        </div>
    </div>
    <!-- ── GRÁFICA 3: VENTAS POR CATEGORÍA (DONA) ──────────────── -->
    <div class="col-md-5">
        <div class="chart-card">
            <h4>🍩 Ventas por categoría</h4>
            <canvas id="chartCategorias" height="180"></canvas>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script>
(function () {
    'use strict';

    // ── Paleta Fable 5 AzulERP para las gráficas ───────────────────
    const PALETA = ['#0A2342', '#B8860B', '#4A90D9', '#1B4F8A', '#D4A017',
                     '#6BAEE8', '#E8C547'];

    const datosDias       = JSON.parse('{{ chart_dias_json|escapejs }}');
    const datosProductos  = JSON.parse('{{ chart_productos_json|escapejs }}');
    const datosCategorias = JSON.parse('{{ chart_categorias_json|escapejs }}');

    // ── Gráfica 1: Línea — Ventas últimos 7 días ───────────────────
    new Chart(document.getElementById('chartVentasDias'), {
        type: 'line',
        data: {
            labels: datosDias.labels,
            datasets: [{
                label: 'Ventas ($)',
                data: datosDias.data,
                borderColor: '#B8860B',
                backgroundColor: 'rgba(184,134,11,.12)',
                tension: .3,
                fill: true,
                pointBackgroundColor: '#0A2342',
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true,
                     ticks: { callback: v => '$' + v } }
            }
        }
    });

    // ── Gráfica 2: Barras — Top 5 productos ────────────────────────
    new Chart(document.getElementById('chartTopProductos'), {
        type: 'bar',
        data: {
            labels: datosProductos.labels,
            datasets: [{
                label: 'Ingreso ($)',
                data: datosProductos.data,
                backgroundColor: PALETA,
                borderRadius: 6,
            }]
        },
        options: {
            responsive: true,
            indexAxis: 'y',
            plugins: { legend: { display: false } },
            scales: {
                x: { beginAtZero: true,
                     ticks: { callback: v => '$' + v } }
            }
        }
    });

    // ── Gráfica 3: Dona — Ventas por categoría ──────────────────────
    new Chart(document.getElementById('chartCategorias'), {
        type: 'doughnut',
        data: {
            labels: datosCategorias.labels,
            datasets: [{
                data: datosCategorias.data,
                backgroundColor: PALETA,
                borderWidth: 2,
                borderColor: '#FFFFFF',
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom',
                          labels: { font: { size: 11 } } }
            }
        }
    });
})();
</script>
{% endblock %}
```

> **Nota sobre `|escapejs`:** el filtro `escapejs` escapa el JSON
> para que sea seguro insertarlo dentro de un literal de cadena
> JavaScript dentro de `<script>`, previniendo inyección si algún
> nombre de producto contuviera caracteres especiales como comillas.

### 4.2 Verificar en el navegador

```cmd
python manage.py runserver
```

```
[ ] /reportes/ sin login → redirige a /accounts/login/
[ ] /reportes/ con login → dashboard visible
[ ] 5 KPI tiles muestran valores (aunque sean $0.00 sin datos)
[ ] Gráfica de línea (7 días) se renderiza sin errores en consola
[ ] Gráfica de barras (top 5) se renderiza
[ ] Gráfica de dona (categorías) se renderiza
[ ] Badge "Datos cacheados 5 min" visible
[ ] Modo oscuro: gráficas siguen siendo legibles
```

---

## PARTE 5 — Actualizar `reportes/urls.py` (10 min)

### 5.1 Reemplazar el contenido

```python
# reportes/urls.py
"""URLs de la app reportes — W19."""
from django.urls import path

from . import views

app_name = 'reportes'

urlpatterns = [
    # Mantener el nombre 'inicio' por compatibilidad con
    # el enlace de navbar definido en templates/base.html (W02)
    path('',
         views.DashboardView.as_view(),
         name='inicio'),
]
```

### 5.2 Verificar

```cmd
python manage.py check
```

```cmd
:: Verificar el flujo de caché manualmente:
python manage.py shell
```

```python
from django.core.cache import cache
from reportes.views import CACHE_KEY_DASHBOARD, _calcular_kpis

# Limpiar caché para forzar recálculo
cache.delete(CACHE_KEY_DASHBOARD)

import time
t0 = time.time()
kpis1 = cache.get_or_set(CACHE_KEY_DASHBOARD, _calcular_kpis, 300)
t1 = time.time()
print(f'Primera llamada (sin caché): {(t1-t0)*1000:.1f} ms')

t0 = time.time()
kpis2 = cache.get_or_set(CACHE_KEY_DASHBOARD, _calcular_kpis, 300)
t1 = time.time()
print(f'Segunda llamada (con caché): {(t1-t0)*1000:.1f} ms')
```

**Resultado esperado:** la segunda llamada debe ser sustancialmente
más rápida (típicamente < 5ms vs. decenas de ms).

---

## PARTE 6 — Tests W19 (25 min)

### 6.1 Estrategia: aislar el caché entre tests

```python
# Usamos locmem (en memoria) en lugar de Redis real para los tests:
# - No requiere Redis corriendo durante CI/CD
# - cache.clear() en setUp() aísla cada test
@override_settings(CACHES={
    'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}
})
class DashboardTest(TestCase):
    def setUp(self):
        cache.clear()
```

---

### 6.2 Crear `tests/test_w19_dashboard.py`

```python
"""Suite de pruebas W19 — Dashboard, KPIs y caché Redis.

Usa el backend locmem para los tests (no requiere Redis real)
y verifica tanto los cálculos de KPIs como el comportamiento
del caché con cache.get_or_set().

Ejecutar con:
    python manage.py test tests.test_w19_dashboard --verbosity=2

Resultado esperado:
    Ran 8 tests in X.XXXs
    OK
"""
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from clientes.models   import Cliente
from productos.models  import Categoria, Producto
from ventas.models     import DetalleVenta, Pedido, Venta

from reportes.views import CACHE_KEY_DASHBOARD, _calcular_kpis

CACHE_TEST = {
    'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}
}


class DashboardAutenticacionTest(TestCase):
    """Tests de protección del dashboard."""

    def test_dashboard_sin_auth_redirige_a_login(self):
        """GET /reportes/ sin login → 302 a /accounts/login/."""
        r = self.client.get(reverse('reportes:inicio'))
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r['Location'])

    def test_dashboard_con_auth_devuelve_200(self):
        """GET /reportes/ con login → 200."""
        user = User.objects.create_user('repuser', password='pass')
        self.client.force_login(user)
        with override_settings(CACHES=CACHE_TEST):
            cache.clear()
            r = self.client.get(reverse('reportes:inicio'))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'reportes/dashboard.html')


@override_settings(CACHES=CACHE_TEST)
class CalcularKPIsTest(TestCase):
    """Tests de la función _calcular_kpis()."""

    def setUp(self):
        cache.clear()
        cat        = Categoria.objects.create(nombre='Cat KPI')
        self.prod  = Producto.objects.create(
            nombre='Producto KPI', precio=Decimal('200.00'),
            stock=2, categoria=cat   # stock < 5 → cuenta como crítico
        )
        self.cli   = Cliente.objects.create(
            nombre='Cliente KPI', correo='kpi@test.com'
        )

    def test_kpis_incluye_las_5_claves(self):
        """El dict de KPIs debe incluir las 5 métricas principales."""
        kpis = _calcular_kpis()
        for clave in ['ventas_dia_total', 'clientes_nuevos',
                      'stock_critico', 'pedidos_pendientes',
                      'revenue_mensual']:
            self.assertIn(clave, kpis)

    def test_stock_critico_detecta_producto_bajo(self):
        """Producto con stock=2 (< 5) debe contarse en stock_critico."""
        kpis = _calcular_kpis()
        self.assertGreaterEqual(kpis['stock_critico'], 1)

    def test_pedidos_pendientes_cuenta_correctamente(self):
        """Un pedido en estado 'pendiente' debe sumar al KPI."""
        Pedido.objects.create(
            numero_pedido='PED-KPI-001', cliente=self.cli,
            estado='pendiente', total_pagado=Decimal('200.00')
        )
        kpis = _calcular_kpis()
        self.assertEqual(kpis['pedidos_pendientes'], 1)

    def test_ventas_dia_suma_pedidos_pagados_hoy(self):
        """Ventas del día = suma de total_pagado de pedidos pagados hoy."""
        Pedido.objects.create(
            numero_pedido='PED-KPI-002', cliente=self.cli,
            estado='pagado', total_pagado=Decimal('350.00')
        )
        kpis = _calcular_kpis()
        self.assertEqual(kpis['ventas_dia_total'], '350.00')

    def test_top_productos_incluye_producto_vendido(self):
        """El producto con ventas debe aparecer en labels_productos."""
        venta = Venta.objects.create(cliente=self.cli)
        DetalleVenta.objects.create(
            venta=venta, producto=self.prod,
            cantidad=3, precio_unitario=Decimal('200.00')
        )
        kpis = _calcular_kpis()
        self.assertIn('Producto KPI', kpis['labels_productos'])


@override_settings(CACHES=CACHE_TEST)
class CacheDashboardTest(TestCase):
    """Tests del comportamiento de cache.get_or_set()."""

    def setUp(self):
        cache.clear()

    def test_segunda_llamada_no_recalcula(self):
        """Con caché activo, la segunda llamada no debe invocar
        de nuevo a _calcular_kpis()."""
        with patch(
            'reportes.views._calcular_kpis',
            wraps=_calcular_kpis
        ) as mock_calc:
            cache.get_or_set(CACHE_KEY_DASHBOARD, mock_calc, 300)
            cache.get_or_set(CACHE_KEY_DASHBOARD, mock_calc, 300)
            # _calcular_kpis solo debe haberse ejecutado UNA vez
            self.assertEqual(mock_calc.call_count, 1)

    def test_cache_clear_fuerza_recalculo(self):
        """Tras cache.delete(), la siguiente llamada SÍ recalcula."""
        with patch(
            'reportes.views._calcular_kpis',
            wraps=_calcular_kpis
        ) as mock_calc:
            cache.get_or_set(CACHE_KEY_DASHBOARD, mock_calc, 300)
            cache.delete(CACHE_KEY_DASHBOARD)
            cache.get_or_set(CACHE_KEY_DASHBOARD, mock_calc, 300)
            self.assertEqual(mock_calc.call_count, 2)
```

### 6.3 Ejecutar los tests

```cmd
python manage.py test tests.test_w19_dashboard --verbosity=2
```

**Resultado esperado:**
```
test_cache_clear_fuerza_recalculo ... ok
test_dashboard_con_auth_devuelve_200 ... ok
test_dashboard_sin_auth_redirige_a_login ... ok
test_kpis_incluye_las_5_claves ... ok
test_pedidos_pendientes_cuenta_correctamente ... ok
test_segunda_llamada_no_recalcula ... ok
test_stock_critico_detecta_producto_bajo ... ok
test_top_productos_incluye_producto_vendido ... ok
test_ventas_dia_suma_pedidos_pagados_hoy ... ok

Ran 9 tests in X.XXXs
OK
```

### 6.4 Suite acumulada

```cmd
python manage.py test tests --verbosity=0
```

**Resultado esperado:** `Ran 179 tests in X.XXXs · OK` (171 + 8)

---

## CIERRE — Commit y Respaldo (10 min)

### Actualizar `sprint6_planning.md`

```markdown
## Sprint Backlog — actualización W19

| Tarea | Estado |
|---|---|
| CACHES con Redis (DB separada) | ✅ W19 |
| _calcular_kpis(): 5 KPIs + 3 datasets | ✅ W19 |
| DashboardView con cache.get_or_set() | ✅ W19 |
| Template dashboard.html con 3 gráficas Chart.js | ✅ W19 |
| reportes/urls.py actualizado | ✅ W19 |
| 9 tests de dashboard y caché | ✅ W19 |
| Exportación reportes filtrados Excel/PDF | ⏳ W20 |
| django-filter en reportes | ⏳ W20 |
| Histórico de precios (simple-history) | ⏳ W21 |
```

### Commit de cierre W19

```cmd
git add .
git status

:: Verificar que incluye:
::   reportes/views.py (DashboardView + _calcular_kpis)
::   reportes/urls.py (actualizado)
::   reportes/templates/reportes/dashboard.html (nuevo)
::   core/settings.py (CACHES)
::   tests/test_w19_dashboard.py
::   sprint6_planning.md

git commit -m "Sprint 6 W19: Dashboard KPIs + Chart.js + caché Redis + 179 tests OK"
git push origin main
```

### Ejecutar `finalizar_sesion.bat`

```cmd
E:\finalizar_sesion.bat
```

---

## CHECKLIST FINAL W19

### Técnico

```
CACHÉ REDIS
[ ] CACHES['default']['BACKEND'] = django.core.cache.backends.redis.RedisCache
[ ] LOCATION usa REDIS_CACHE_URL con DB /1 (distinta del broker /0)
[ ] cache.set/get funciona desde el shell

CÁLCULO DE KPIS
[ ] _calcular_kpis() en reportes/views.py
[ ] Los 5 KPIs usan aggregate() o count() — no loops Python
[ ] Los 3 datasets usan annotate() + ExpressionWrapper + F()
[ ] Todos los valores de datasets son float() antes de retornar
[ ] Los KPIs textuales ($) se guardan como str (preserva Decimal)

DASHBOARDVIEW
[ ] LoginRequiredMixin (dashboard requiere autenticación)
[ ] get_context_data() usa cache.get_or_set()
[ ] CACHE_TTL_SEGUNDOS = 300 (5 minutos)
[ ] json.dumps() para cada dataset antes de pasarlo al template

TEMPLATE
[ ] dashboard.html: 5 kpi-tile con valores dinámicos
[ ] kpi-tile.alerta cuando stock_critico > 0
[ ] 3 elementos <canvas> con IDs únicos
[ ] Chart.js CDN cargado en {% block extra_js %}
[ ] JSON.parse('{{ ... |escapejs }}') para cada dataset
[ ] Gráfica de línea, de barras horizontal y de dona

URLS
[ ] reportes/urls.py: name='inicio' (compatibilidad con navbar)
[ ] python manage.py check → 0 issues

TESTS
[ ] test tests.test_w19_dashboard → 9/9 OK
[ ] test tests → 179/179 OK acumulados (mínimo, puede variar +1)
[ ] @override_settings(CACHES=locmem) en todos los tests de caché
[ ] cache.clear() en setUp() de cada clase con caché
[ ] test segunda llamada NO recalcula (mock con call_count)
[ ] test cache.delete() SÍ fuerza recálculo

GIT
[ ] sprint6_planning.md con Sprint Goal de la Espiral 7 completa
[ ] Commit con mensaje descriptivo
[ ] git push → GitHub con dashboard.html y CACHES configurado
[ ] finalizar_sesion.bat → archivos en USB
```

---

## DIAGRAMA: Flujo de caché del dashboard (W19)

```
Petición 1: GET /reportes/  (caché vacío)
    │
    ▼
DashboardView.get_context_data()
    │
    └─ cache.get_or_set('dashboard_kpis_v1', _calcular_kpis, 300)
            │
            ├─ Redis: ¿existe 'dashboard_kpis_v1'? → NO
            │
            └─ Ejecuta _calcular_kpis()
                    │
                    ├─ 5 queries aggregate/count (KPIs)
                    ├─ 7 queries (línea: 1 por día)
                    ├─ 1 query annotate (top productos)
                    ├─ 1 query annotate (categorías)
                    │       Total: ~14 queries SQL
                    │
                    └─ Redis: SET dashboard_kpis_v1 = {...} EX 300

Tiempo: ~40-80ms (depende del volumen de datos)

─────────────────────────────────────────────────────────

Petición 2: GET /reportes/  (dentro de los 5 minutos)
    │
    ▼
DashboardView.get_context_data()
    │
    └─ cache.get_or_set('dashboard_kpis_v1', _calcular_kpis, 300)
            │
            ├─ Redis: ¿existe 'dashboard_kpis_v1'? → SÍ
            │
            └─ Retorna el valor cacheado directamente
                    0 queries SQL ejecutadas

Tiempo: ~2-5ms  ← 10-40× más rápido
```

---

## HILO CONDUCTOR → W20

**¿Qué entrega W19?**
El dashboard con 5 KPIs y 3 gráficas interactivas, con caché Redis
que reduce el tiempo de carga en peticiones repetidas. 179 tests
verifican tanto los cálculos como el comportamiento del caché.

**¿Qué abre W20?**
El dashboard muestra una vista general; W20 agrega **reportes
filtrables** (por fecha, producto, cliente) con `django-filter`
y exportación a Excel/PDF de los resultados filtrados —
extendiendo el patrón de exportación ya usado en W12.

**¿Qué necesita W20 de W19?**

| Artefacto de W19 | Uso en W20 |
|---|---|
| `_calcular_kpis()` con `ExpressionWrapper` | W20 reutiliza el mismo patrón para reportes filtrados |
| `CACHES` configurado | W20 cachea también los resultados de reportes pesados |
| `exportar_productos_excel` (W12) | W20 crea una vista equivalente para reportes de ventas |
| 179 tests pasando | W20 agrega tests de filtros y exportación de reportes |

**Tarea de investigación para W20:**
> Lee la documentación de `django-filter` con vistas basadas en clase:
> `https://django-filter.readthedocs.io/en/stable/guide/usage.html#generic-view`
>
> ¿Cómo se integra `FilterSet` con una `ListView` existente
> (como ya hiciste con `ProductoFilter` en W13)?
> ¿Qué ventaja tiene filtrar por rango de fechas con
> `DateFromToRangeFilter` en lugar de dos campos separados?

**Pregunta de reflexión:**
> "El dashboard cachea los KPIs durante 5 minutos. Si un gerente
> registra una venta nueva justo después de que el caché se generó,
> ¿verá esa venta reflejada en el dashboard inmediatamente?
> ¿Qué estrategia usarías para invalidar el caché manualmente
> justo cuando se confirma un pago (en el webhook de W15)?"

---

## Referencia rápida de comandos W19

```cmd
:: SESIÓN
E:\iniciar_sesion.bat
E:\finalizar_sesion.bat

:: DJANGO
python manage.py check
python manage.py runserver

:: VERIFICAR CACHÉ EN SHELL
python manage.py shell
>>> from django.core.cache import cache
>>> cache.set('test', 'ok', 30)
>>> cache.get('test')

:: MEDIR TIEMPO DE CACHÉ
>>> from reportes.views import CACHE_KEY_DASHBOARD, _calcular_kpis
>>> cache.delete(CACHE_KEY_DASHBOARD)
>>> import time
>>> t0=time.time(); cache.get_or_set(CACHE_KEY_DASHBOARD,_calcular_kpis,300); print(time.time()-t0)

:: TESTS
python manage.py test tests.test_w19_dashboard --verbosity=2
python manage.py test tests --verbosity=0   (179 tests)

:: GIT
git add .
git commit -m "Sprint 6 W19: Dashboard + Chart.js + caché + 179 tests OK"
git push origin main
git log --oneline
```

---

*Guía de Laboratorio W19 · ERP Django*
*Espiral 7 · Sprint 6 Planning · Dashboard KPIs + Chart.js + Caché Redis*
*SEP 3061300006-23 · UTEC Celaya · MC. Román Fernando López González*

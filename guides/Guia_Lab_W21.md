# Guía de Laboratorio — W21
## ERP Django · Espiral 7 · Semana 21 de 24
### Técnico en Programación (SEP 3061300006-23) · UTEC Celaya
### Asesor: MC. Román Fernando López González

---

| Campo | Detalle |
|---|---|
| **Semana** | W21 de 24 |
| **Espiral** | E7 — Dashboard y Reportes |
| **Sprint Scrum** | Sprint 6 — Review + Retrospectiva |
| **Hito** | **★ M7: Dashboard KPIs + exportación adaptativa + histórico de precios + 195 tests** |
| **Horario** | 16:45 – 19:45 (180 min) |
| **Nivel Schmelkes** | 4 — Funcionalidades Avanzadas |
| **Hilo conductor** | "W20 permitió exportar el presente. W21 guarda el pasado: todo cambio de precio queda registrado automáticamente." |

---

## Respuesta a la tarea de investigación de W20

> **¿Qué hace `HistoricalRecords` en un modelo Django?**
>
> Al agregar `history = HistoricalRecords()` a un modelo, `django-simple-history`
> crea automáticamente una tabla paralela en la BD llamada
> `{app}_{modelname}historical` (ej: `productos_historicalproducto`).
> Cada vez que se llama a `save()` o `delete()` sobre una instancia
> del modelo, se inserta una fila en la tabla histórica con una copia
> del estado completo del objeto en ese momento.
>
> **¿Qué columnas adicionales tiene la tabla histórica?**
>
> | Columna | Descripción |
> |---|---|
> | `history_id` | PK de la tabla histórica |
> | `history_date` | Fecha y hora del cambio |
> | `history_type` | `+` (creación), `~` (modificación), `-` (borrado) |
> | `history_user` | FK al usuario que hizo el cambio (None si desde shell) |
> | `history_change_reason` | Texto opcional que describe el motivo del cambio |
> | Todos los campos del modelo original | Copia exacta del estado en ese momento |
>
> **¿Quién registra el `history_user`?**
> El middleware `HistoryRequestMiddleware` intercepta cada petición HTTP,
> extrae el usuario autenticado (`request.user`) y lo hace disponible
> para simple_history. Sin el middleware, `history_user` siempre es `None`.

---

## Objetivos de la sesión

Al terminar W21, el estudiante será capaz de:

1. Instalar y configurar `django-simple-history` con el middleware de usuario
2. Agregar `HistoricalRecords` a `Producto` y `Venta`
3. Crear y aplicar las migraciones que generan las tablas históricas
4. Implementar `HistoricoProductoView` con comparación de cambios de precio
5. Construir un template que resalta visualmente los cambios de precio
6. Ejecutar el Sprint 6 Review y declarar el Hito M7

---

## Stack tecnológico de W21

| Herramienta | Novedad en W21 | Descripción |
|---|---|---|
| `django-simple-history` | ✅ Nuevo | Registra automáticamente todos los cambios de un modelo en la BD |
| `HistoricalRecords()` | ✅ Nuevo | Campo de modelo que activa el rastreo histórico |
| `HistoryRequestMiddleware` | ✅ Nuevo | Middleware que vincula el usuario de Django al registro histórico |
| `history_type` | ✅ Nuevo | Indicador de tipo de cambio: `+` creación, `~` edición, `-` borrado |
| `.as_of(datetime)` | ✅ Nuevo | Reconstruye el estado del objeto en un momento específico del pasado |

---

## Mapa de tiempo (180 min)

| Parte | Actividad | Tiempo |
|---|---|---|
| Arranque | Daily Scrum + verificar W20 | 10 min |
| Parte 1 | Instalar `django-simple-history` + configurar | 15 min |
| Parte 2 | Agregar `HistoricalRecords` a `Producto` y `Venta` | 15 min |
| Parte 3 | Migraciones + verificar tablas históricas | 15 min |
| Parte 4 | `HistoricoProductoView` + lógica de comparación | 20 min |
| Parte 5 | Template `historico.html` con resaltado de cambios | 20 min |
| Parte 6 | URL + botón en `detalle.html` + admin verificación | 10 min |
| Parte 7 | Tests W21 (8 pruebas) | 20 min |
| **Commit parcial** | Punto de control seguro | 5 min |
| Parte 8 | Sprint 6 Review ante el asesor | 20 min |
| Parte 9 | Sprint 6 Retrospectiva + Ficha Schmelkes E7 | 20 min |
| Cierre | Commit final [M7] · `finalizar_sesion.bat` · hilo → W22 | 10 min |
| **Total** | | **180 min** |

---

## ARRANQUE — Daily Scrum (10 min)

```cmd
E:\iniciar_sesion.bat
```

### Daily Scrum

```
1. ¿Qué hice en W20?
   → Creé VentaReporteFilter, ExportacionReporte, ReporteVentasView
     y la exportación adaptativa síncrona/asíncrona.

2. ¿Qué haré en W21?
   → Instalaré django-simple-history para registrar cambios de precio
     y cerraré el Sprint 6 con la Review y el Hito M7.

3. ¿Tengo algún impedimento?
   → (registrar aquí)
```

### Verificar estado

```cmd
python manage.py check
python manage.py test tests --verbosity=0
```

**Resultado esperado:** `System check identified no issues` · `Ran 187 tests … OK`

---

## PARTE 1 — Instalar y Configurar `django-simple-history` (15 min)

### 1.1 Instalar el paquete

```cmd
pip install "django-simple-history==3.5.0"
pip freeze > requirements.txt
```

Verificar:

```cmd
python -c "import simple_history; print('simple_history', simple_history.__version__)"
```

---

### 1.2 Agregar a `INSTALLED_APPS` en `core/settings.py`

```python
# core/settings.py — en INSTALLED_APPS, después de django_filters:
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    # Terceros
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'simple_history',          # ← agregar
    'anymail',
    'whitenoise.runserver_nostatic',
    # Apps del ERP
    'clientes',
    'proveedores',
    'productos',
    'ventas',
    'reportes',
    'configuracion',
    'catalogo',
]
```

---

### 1.3 Agregar el middleware de usuario en `core/settings.py`

El middleware `HistoryRequestMiddleware` debe ir **después** del
middleware de autenticación para que `request.user` ya esté disponible.

```python
# core/settings.py — en MIDDLEWARE, agregar al final:
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',  # ← agregar al final
]
```

---

### 1.4 Configuración opcional en `core/settings.py`

```python
# core/settings.py — agregar al final, junto a las demás configuraciones:

# ── DJANGO-SIMPLE-HISTORY ──────────────────────────────────────────────────
# No mostrar el botón "Revertir" en el admin — solo auditoria, no rollback
SIMPLE_HISTORY_REVERT_DISABLED = True

# Número máximo de registros históricos a conservar por objeto (None = ilimitado)
# En producción con alta actividad, considerar un límite para controlar el tamaño de la BD
SIMPLE_HISTORY_HISTORY_CHANGE_REASON_CONTEXT_VARIABLE = 'history_change_reason'
```

### 1.5 Verificar

```cmd
python manage.py check
```

**Resultado esperado:** `System check identified no issues (0 silenced).`

---

## PARTE 2 — Agregar `HistoricalRecords` a los Modelos (15 min)

### 2.1 Actualizar `productos/models.py`

Agregar el import al inicio del archivo:

```python
# productos/models.py — agregar import:
from simple_history.models import HistoricalRecords
```

Agregar el campo `history` a la clase `Producto`, justo antes de la clase `Meta`:

```python
# En la clase Producto — agregar después de 'creado' y antes de class Meta:

    history = HistoricalRecords(
        verbose_name='Historial de cambios',
        history_change_reason_field=models.TextField(null=True),
        # Rastrear cambios de los campos más relevantes para auditoría
        # (por defecto rastrea TODOS los campos del modelo)
    )
```

El modelo `Producto` con el campo en su lugar:

```python
class Producto(models.Model):
    nombre    = models.CharField(max_length=200, verbose_name='Nombre')
    precio    = models.DecimalField(...)
    stock     = models.IntegerField(...)
    categoria = models.ForeignKey(Categoria, ...)
    proveedor = models.ForeignKey(Proveedor, ...)
    activo    = models.BooleanField(default=True)
    imagen    = models.ImageField(...)           # W11
    creado    = models.DateTimeField(auto_now_add=True)

    history   = HistoricalRecords(              # ← nuevo W21
        verbose_name='Historial de cambios',
    )

    class Meta:
        verbose_name        = 'Producto'
        verbose_name_plural = 'Productos'
        ordering            = ['nombre']
    ...
```

---

### 2.2 Actualizar `ventas/models.py`

```python
# ventas/models.py — agregar import:
from simple_history.models import HistoricalRecords
```

Agregar `history` a la clase `Venta` (auditoría de cambios de estado):

```python
# En la clase Venta — antes de class Meta:
    history = HistoricalRecords(verbose_name='Historial de venta')
```

Agregar `history` también a la clase `Pedido` (auditoría de estado del pedido):

```python
# En la clase Pedido — antes de class Meta:
    history = HistoricalRecords(verbose_name='Historial de pedido')
```

> **¿Por qué auditar también `Venta` y `Pedido`?**
> El historial de pedidos permite rastrear exactamente cuándo y quién
> cambió el estado de un pedido (de `pendiente` a `pagado`, o a
> `cancelado`). Esto es esencial para auditoría en un ERP real.

---

## PARTE 3 — Migraciones + Verificar Tablas (15 min)

### 3.1 Crear las migraciones

```cmd
python manage.py makemigrations productos --name historico_producto
python manage.py makemigrations ventas    --name historico_venta_pedido
```

**Resultado esperado:**
```
Migrations for 'productos':
  productos/migrations/0003_historicalproducto.py
    - Create model HistoricalProducto

Migrations for 'ventas':
  ventas/migrations/0005_historicalventa_historicalpedido.py
    - Create model HistoricalPedido
    - Create model HistoricalVenta
```

### 3.2 Aplicar las migraciones

```cmd
python manage.py migrate
```

```
Applying productos.0003_historicalproducto... OK
Applying ventas.0005_historicalventa_historicalpedido... OK
```

### 3.3 Verificar las tablas creadas

```cmd
python manage.py showmigrations productos
python manage.py showmigrations ventas
```

```
productos
 [X] 0001_initial
 [X] 0002_imagen_producto
 [X] 0003_historicalproducto

ventas
 [X] 0001_initial
 [X] 0002_validators_pedido
 [X] 0003_items_snapshot_pedido
 [X] 0004_correo_enviado_pedido
 [X] 0005_historicalventa_historicalpedido
```

### 3.4 Inspeccionar el historial desde el shell

```cmd
python manage.py shell
```

```python
from productos.models import Producto, Categoria
from decimal import Decimal

# Crear un producto de prueba para ver el historial
cat  = Categoria.objects.first() or Categoria.objects.create(nombre='Demo')
prod = Producto.objects.create(
    nombre='Monitor Demo', precio=Decimal('3500.00'), stock=5, categoria=cat
)
print('Historial tras creación:', prod.history.count())
# → 1

prod.precio = Decimal('3200.00')
prod.save()
print('Historial tras cambio de precio:', prod.history.count())
# → 2

# Ver el historial completo
for registro in prod.history.all():
    print(f"  [{registro.history_type}] {registro.history_date.strftime('%H:%M:%S')}"
          f"  precio={registro.precio}  stock={registro.stock}")
# [~] HH:MM:SS  precio=3200.00  stock=5
# [+] HH:MM:SS  precio=3500.00  stock=5

# Ver el estado del producto en un momento anterior
primer_registro = prod.history.last()   # el más antiguo
estado_anterior = primer_registro.instance
print('Precio original:', estado_anterior.precio)
# → 3500.00

# Diferencias entre dos versiones
nuevo = prod.history.first()
old   = prod.history.all()[1]
delta = nuevo.diff_against(old)
for cambio in delta.changes:
    print(f"  Campo '{cambio.field}': {cambio.old} → {cambio.new}")
# Campo 'precio': 3500.00 → 3200.00
```

---

## PARTE 4 — `HistoricoProductoView` con Comparación de Cambios (20 min)

### 4.1 Crear la vista en `productos/views.py`

Agregar imports al inicio del archivo:

```python
# productos/views.py — agregar imports:
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
```

Agregar la vista al final de `productos/views.py`:

```python
# productos/views.py — agregar al final:

class HistoricoProductoView(LoginRequiredMixin, TemplateView):
    """Muestra el historial completo de cambios de un producto.

    Útil para auditar cuándo y quién cambió el precio, el stock
    o cualquier otro campo del producto.

    Características:
        - Lista todos los registros históricos (hasta 100).
        - Compara cada registro con el anterior para resaltar cambios.
        - Muestra el usuario responsable de cada cambio (si hay middleware).
    """

    template_name = 'productos/historico.html'

    def get_context_data(self, **kwargs) -> dict:
        """Construye el contexto con el historial anotado con cambios."""
        ctx = super().get_context_data(**kwargs)

        producto = get_object_or_404(
            Producto, pk=kwargs['producto_id']
        )

        # Obtener historial: más reciente primero, máximo 100 registros
        registros_raw = list(producto.history.all()[:100])

        # Anotar cada registro con los campos que cambiaron
        # respecto al registro inmediatamente anterior (más antiguo)
        registros_anotados = []
        for i, registro in enumerate(registros_raw):
            cambios = {}

            if i < len(registros_raw) - 1:
                # Hay un registro anterior con el que comparar
                anterior = registros_raw[i + 1]
                delta    = registro.diff_against(anterior)
                for cambio in delta.changes:
                    cambios[cambio.field] = {
                        'anterior': cambio.old,
                        'nuevo':    cambio.new,
                    }

            registros_anotados.append({
                'registro':      registro,
                'cambios':       cambios,
                'es_creacion':   registro.history_type == '+',
                'es_borrado':    registro.history_type == '-',
                'precio_cambio': 'precio' in cambios,
                'stock_cambio':  'stock'  in cambios,
            })

        ctx['producto']   = producto
        ctx['registros']  = registros_anotados
        ctx['total']      = producto.history.count()
        return ctx
```

---

## PARTE 5 — Template `historico.html` con Resaltado de Cambios (20 min)

### 5.1 Crear `productos/templates/productos/historico.html`

```html
{% extends "base.html" %}
{% block title %}Historial de cambios — {{ producto.nombre }}{% endblock %}
{% block nav_productos %}active{% endblock %}

{% block extra_css %}
<style>
    /* ── Estilos específicos del historial ────────────────────── */
    .timeline {
        position: relative;
        padding-left: 2rem;
        margin: 1rem 0;
    }
    .timeline::before {
        content: '';
        position: absolute;
        left: .55rem;
        top: 0; bottom: 0;
        width: 2px;
        background: var(--clr-border);
    }
    .timeline-item {
        position: relative;
        margin-bottom: 1.2rem;
        padding-left: 1rem;
    }
    .timeline-dot {
        position: absolute;
        left: -1.6rem;
        top: .3rem;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        border: 2px solid var(--clr-navy);
        background: var(--clr-surface);
    }
    .timeline-dot.creacion { background: var(--clr-ok);      border-color: var(--clr-ok); }
    .timeline-dot.borrado   { background: var(--clr-danger);  border-color: var(--clr-danger); }
    .timeline-dot.precio    { background: var(--clr-gold);    border-color: var(--clr-gold); }
    .timeline-dot.stock     { background: var(--clr-sky);     border-color: var(--clr-sky); }

    .registro-card {
        background: var(--clr-surface);
        border: 1px solid var(--clr-border);
        border-radius: 8px;
        padding: .75rem 1rem;
        box-shadow: var(--shadow-sm);
    }
    .registro-header {
        display: flex;
        align-items: center;
        gap: .5rem;
        margin-bottom: .4rem;
    }
    .badge-tipo {
        font-size: .72rem;
        font-weight: 700;
        padding: .15rem .5rem;
        border-radius: 12px;
        text-transform: uppercase;
        letter-spacing: .04em;
    }
    .badge-creacion { background: #D4EDDA; color: #155724; }
    .badge-edicion  { background: var(--clr-ice); color: var(--clr-navy); }
    .badge-borrado  { background: #F8D7DA; color: #721C24; }

    .cambio-row {
        display: flex;
        align-items: center;
        gap: .5rem;
        font-size: .85rem;
        padding: .25rem 0;
        border-bottom: 1px dashed var(--clr-border);
    }
    .cambio-row:last-child { border-bottom: none; }
    .cambio-field  { font-weight: 600; color: var(--clr-navy); min-width: 80px; }
    .cambio-old    { color: var(--clr-muted); text-decoration: line-through; }
    .cambio-arrow  { color: var(--clr-muted); }
    .cambio-new    { font-weight: 600; }
    .cambio-new.precio-sube   { color: var(--clr-danger); }
    .cambio-new.precio-baja   { color: var(--clr-ok); }
    .cambio-new.stock-sube    { color: var(--clr-ok); }
    .cambio-new.stock-baja    { color: var(--clr-danger); }

    .kpi-historia {
        display: flex;
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    .kpi-hist-tile {
        background: var(--clr-surface);
        border: 1px solid var(--clr-border);
        border-radius: 8px;
        padding: .75rem 1.25rem;
        text-align: center;
        min-width: 120px;
    }
    .kpi-hist-valor { font-size: 1.4rem; font-weight: 700; color: var(--clr-navy); }
    .kpi-hist-label { font-size: .72rem; color: var(--clr-muted); text-transform: uppercase; }
</style>
{% endblock %}

{% block content %}
<div class="erp-page-title">
    <h2>📜 Historial de cambios</h2>
    <span style="margin-left:auto;color:var(--clr-muted);font-size:.85rem;">
        {{ producto.nombre }}
    </span>
    <a href="{% url 'productos:detalle' producto.pk %}"
       class="btn-erp-primary">← Volver al producto</a>
</div>

<!-- Datos actuales del producto -->
<div class="erp-card" style="margin-bottom:1.5rem;">
    <div class="erp-card-header">Estado actual del producto</div>
    <div style="display:flex;gap:2rem;padding:.5rem 0;">
        <div>
            <span class="erp-label">Precio actual</span>
            <p style="font-size:1.2rem;font-weight:700;color:var(--clr-gold);margin:0;">
                ${{ producto.precio }}
            </p>
        </div>
        <div>
            <span class="erp-label">Stock actual</span>
            <p style="font-size:1.2rem;font-weight:700;color:var(--clr-navy);margin:0;">
                {{ producto.stock }} unidades
            </p>
        </div>
        <div>
            <span class="erp-label">Estado</span>
            <p style="margin:0;">
                {% if producto.activo %}
                    <span class="badge-erp-active">Activo</span>
                {% else %}
                    <span class="badge-erp-inactive">Inactivo</span>
                {% endif %}
            </p>
        </div>
    </div>
</div>

<!-- KPIs del historial -->
{% with cambios_precio=registros|length %}
<div class="kpi-historia">
    <div class="kpi-hist-tile">
        <div class="kpi-hist-valor">{{ total }}</div>
        <div class="kpi-hist-label">Total de cambios</div>
    </div>
    <div class="kpi-hist-tile">
        <div class="kpi-hist-valor">
            {% with cnt=0 %}
            {% for r in registros %}{% if r.precio_cambio %}{% with cnt=cnt|add:1 %}{% endwith %}{% endif %}{% endfor %}
            {{ registros|length }}
            {% endwith %}
        </div>
        <div class="kpi-hist-label">Registros mostrados</div>
    </div>
</div>
{% endwith %}

<!-- Timeline de historial -->
{% if registros %}
<div class="erp-card">
    <div class="erp-card-header">Línea de tiempo de cambios</div>
    <div class="timeline" style="margin-top:1rem;">
        {% for item in registros %}
        <div class="timeline-item">
            <!-- Punto de color en la línea -->
            <div class="timeline-dot
                {% if item.es_creacion %}creacion
                {% elif item.es_borrado %}borrado
                {% elif item.precio_cambio %}precio
                {% elif item.stock_cambio %}stock
                {% endif %}">
            </div>

            <div class="registro-card">
                <!-- Encabezado del registro -->
                <div class="registro-header">
                    {% if item.es_creacion %}
                        <span class="badge-tipo badge-creacion">✅ Creación</span>
                    {% elif item.es_borrado %}
                        <span class="badge-tipo badge-borrado">🗑️ Borrado</span>
                    {% else %}
                        <span class="badge-tipo badge-edicion">✏️ Modificación</span>
                    {% endif %}

                    <span style="color:var(--clr-muted);font-size:.82rem;">
                        {{ item.registro.history_date|date:"d/m/Y H:i:s" }}
                    </span>

                    {% if item.registro.history_user %}
                        <span style="color:var(--clr-sky);font-size:.82rem;margin-left:auto;">
                            👤 {{ item.registro.history_user.username }}
                        </span>
                    {% else %}
                        <span style="color:var(--clr-muted);font-size:.78rem;margin-left:auto;">
                            Sistema / shell
                        </span>
                    {% endif %}
                </div>

                <!-- Campos en el momento del cambio -->
                <div style="font-size:.83rem;color:var(--clr-muted);margin-bottom:.5rem;">
                    Precio: <strong style="color:var(--clr-gold);">${{ item.registro.precio }}</strong>
                    &nbsp;·&nbsp;
                    Stock: <strong>{{ item.registro.stock }}</strong>
                    {% if item.registro.history_change_reason %}
                    &nbsp;·&nbsp;
                    Motivo: <em>{{ item.registro.history_change_reason }}</em>
                    {% endif %}
                </div>

                <!-- Detalle de cambios respecto al estado anterior -->
                {% if item.cambios %}
                <div style="margin-top:.4rem;">
                    {% for campo, valores in item.cambios.items %}
                    <div class="cambio-row">
                        <span class="cambio-field">{{ campo }}</span>
                        <span class="cambio-old">{{ valores.anterior }}</span>
                        <span class="cambio-arrow">→</span>
                        {% if campo == 'precio' %}
                            {% if valores.nuevo > valores.anterior %}
                                <span class="cambio-new precio-sube">
                                    {{ valores.nuevo }} ▲
                                </span>
                            {% else %}
                                <span class="cambio-new precio-baja">
                                    {{ valores.nuevo }} ▼
                                </span>
                            {% endif %}
                        {% elif campo == 'stock' %}
                            {% if valores.nuevo > valores.anterior %}
                                <span class="cambio-new stock-sube">
                                    {{ valores.nuevo }} ▲
                                </span>
                            {% else %}
                                <span class="cambio-new stock-baja">
                                    {{ valores.nuevo }} ▼
                                </span>
                            {% endif %}
                        {% else %}
                            <span class="cambio-new">{{ valores.nuevo }}</span>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
                {% endif %}
            </div>
        </div>
        {% endfor %}
    </div>
</div>

{% if total > 100 %}
<p style="color:var(--clr-muted);font-size:.85rem;margin-top:.75rem;text-align:center;">
    Mostrando los 100 cambios más recientes de {{ total }} totales.
</p>
{% endif %}

{% else %}
<div class="erp-alert-info">
    No hay historial de cambios registrado para este producto aún.
</div>
{% endif %}
{% endblock %}
```

---

## PARTE 6 — URL, Botón en Detalle y Verificación en Admin (10 min)

### 6.1 Actualizar `productos/urls.py`

```python
# productos/urls.py — agregar la ruta del historial:
from django.urls import path
from . import views

app_name = 'productos'

urlpatterns = [
    path('',
         views.ProductoListView.as_view(),   name='lista'),
    path('<int:producto_id>/',
         views.ProductoDetailView.as_view(), name='detalle'),
    path('nuevo/',
         views.ProductoCreateView.as_view(), name='crear'),
    path('<int:producto_id>/editar/',
         views.ProductoUpdateView.as_view(), name='editar'),
    path('<int:producto_id>/eliminar/',
         views.ProductoDeleteView.as_view(), name='eliminar'),
    path('exportar-excel/',
         views.exportar_productos_excel,     name='exportar_excel'),
    # Historial de cambios — W21
    path('<int:producto_id>/historico/',
         views.HistoricoProductoView.as_view(), name='historico'),
]
```

### 6.2 Agregar botón en `productos/templates/productos/detalle.html`

En la sección `erp-page-title`, junto a los botones de Editar y Eliminar:

```html
<!-- En el bloque erp-page-title de detalle.html — agregar botón: -->
{% if user.is_authenticated %}
    <a href="{% url 'productos:editar' producto.pk %}"
       class="btn-erp-gold ms-auto">Editar</a>
    <a href="{% url 'productos:eliminar' producto.pk %}"
       class="btn-erp-danger">Eliminar</a>
    <!-- Botón historial — W21 -->
    <a href="{% url 'productos:historico' producto.pk %}"
       class="btn-erp-primary"
       title="Ver historial de cambios de precio y stock">
        📜 Historial
    </a>
{% endif %}
```

### 6.3 Verificar el admin automático de simple_history

`django-simple-history` agrega automáticamente un botón **"History"**
en cada objeto del admin de Django. No requiere configuración adicional
en `admin.py`.

```cmd
python manage.py runserver
```

```
[ ] /admin/productos/producto/ → lista de productos
[ ] Clic en cualquier producto → formulario de edición
[ ] Botón "HISTORY" visible en la esquina superior derecha
[ ] Clic en HISTORY → tabla con todos los cambios
[ ] Cambiar el precio desde el admin → guardar → el historial se actualiza
[ ] /productos/<id>/historico/ con login → timeline visible
[ ] Línea dorada para cambio de precio, azul para stock
```

---

## PARTE 7 — Tests W21 (20 min)

### 7.1 Crear `tests/test_w21_historico.py`

```python
"""Suite de pruebas W21 — django-simple-history en Producto y Venta.

Verifica que el historial se crea automáticamente al guardar,
que los tipos de cambio son correctos, y que la vista de
historial funciona correctamente.

Ejecutar con:
    python manage.py test tests.test_w21_historico --verbosity=2

Resultado esperado:
    Ran 8 tests in X.XXXs
    OK
"""
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from clientes.models    import Cliente
from productos.models   import Categoria, Producto
from ventas.models      import Pedido, Venta


class HistorialProductoModelTest(TestCase):
    """Tests del historial automático en el modelo Producto."""

    def setUp(self):
        self.cat = Categoria.objects.create(nombre='Cat Hist')

    def test_historia_creada_al_crear_producto(self):
        """Al crear un Producto, debe haber 1 registro en su historial."""
        prod = Producto.objects.create(
            nombre='Laptop', precio=Decimal('10000.00'),
            stock=5, categoria=self.cat
        )
        self.assertEqual(prod.history.count(), 1)

    def test_history_type_creacion_es_mas(self):
        """El primer registro histórico debe ser de tipo '+' (creación)."""
        prod = Producto.objects.create(
            nombre='Mouse', precio=Decimal('250.00'),
            stock=20, categoria=self.cat
        )
        # history.last() = el más antiguo (la creación)
        self.assertEqual(prod.history.last().history_type, '+')

    def test_historia_actualizada_al_cambiar_precio(self):
        """Al cambiar el precio, el historial debe tener 2 registros."""
        prod = Producto.objects.create(
            nombre='Teclado', precio=Decimal('500.00'),
            stock=10, categoria=self.cat
        )
        prod.precio = Decimal('450.00')
        prod.save()
        self.assertEqual(prod.history.count(), 2)

    def test_history_type_edicion_es_virgulilla(self):
        """El registro de edición debe ser de tipo '~' (modificación)."""
        prod = Producto.objects.create(
            nombre='Monitor', precio=Decimal('3000.00'),
            stock=3, categoria=self.cat
        )
        prod.stock = 8
        prod.save()
        # history.first() = el más reciente (la edición)
        self.assertEqual(prod.history.first().history_type, '~')

    def test_precio_en_historia_refleja_valor_historico(self):
        """El historial debe conservar el precio original, no el nuevo."""
        prod = Producto.objects.create(
            nombre='Impresora', precio=Decimal('1200.00'),
            stock=2, categoria=self.cat
        )
        precio_original = Decimal('1200.00')
        prod.precio = Decimal('999.00')
        prod.save()
        # El registro más antiguo (la creación) debe tener el precio original
        self.assertEqual(prod.history.last().precio, precio_original)

    def test_diff_against_detecta_cambio_de_precio(self):
        """diff_against debe identificar el campo 'precio' como cambiado."""
        prod = Producto.objects.create(
            nombre='Tablet', precio=Decimal('5000.00'),
            stock=4, categoria=self.cat
        )
        prod.precio = Decimal('4500.00')
        prod.save()
        nuevo   = prod.history.first()
        antiguo = prod.history.last()
        delta   = nuevo.diff_against(antiguo)
        campos_cambiados = [c.field for c in delta.changes]
        self.assertIn('precio', campos_cambiados)


class HistoricoVistaTest(TestCase):
    """Tests de la vista HistoricoProductoView."""

    def setUp(self):
        self.user = User.objects.create_user('histuser', password='pass')
        cat        = Categoria.objects.create(nombre='Cat Vista')
        self.prod  = Producto.objects.create(
            nombre='Camara', precio=Decimal('8000.00'),
            stock=2, categoria=cat
        )

    def test_historico_sin_auth_redirige_a_login(self):
        """GET /productos/<id>/historico/ sin login → 302."""
        r = self.client.get(
            reverse('productos:historico', args=[self.prod.pk])
        )
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r['Location'])

    def test_historico_con_auth_devuelve_200(self):
        """GET /productos/<id>/historico/ con login → 200."""
        self.client.force_login(self.user)
        r = self.client.get(
            reverse('productos:historico', args=[self.prod.pk])
        )
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'productos/historico.html')

    def test_historico_muestra_registros_en_contexto(self):
        """El contexto debe incluir los registros históricos."""
        self.prod.precio = Decimal('7500.00')
        self.prod.save()
        self.client.force_login(self.user)
        r = self.client.get(
            reverse('productos:historico', args=[self.prod.pk])
        )
        self.assertIn('registros', r.context)
        self.assertEqual(len(r.context['registros']), 2)
```

### 7.2 Ejecutar los tests

```cmd
python manage.py test tests.test_w21_historico --verbosity=2
```

**Resultado esperado:**
```
test_diff_against_detecta_cambio_de_precio ... ok
test_historia_actualizada_al_cambiar_precio ... ok
test_historia_creada_al_crear_producto ... ok
test_historico_con_auth_devuelve_200 ... ok
test_historico_muestra_registros_en_contexto ... ok
test_historico_sin_auth_redirige_a_login ... ok
test_history_type_creacion_es_mas ... ok
test_history_type_edicion_es_virgulilla ... ok
test_precio_en_historia_refleja_valor_historico ... ok

Ran 8 tests in X.XXXs
OK
```

### 7.3 Suite acumulada — Hito M7

```cmd
python manage.py test tests --verbosity=0
```

**Resultado esperado:** `Ran 195 tests in X.XXXs · OK` (187 + 8)

### COMMIT PARCIAL

```cmd
git add .
git commit -m "Sprint 6 W21: django-simple-history + historico view + 195 tests OK [pre-M7]"
```

---

## PARTE 8 — Sprint 6 Review ante el asesor (20 min)

### Guión de demo (≤ 10 min en vivo)

```
1. Dashboard en acción:
   → /reportes/ con login → 5 KPIs visibles
   → Gráfica de ventas 7 días, top 5 productos, dona por categoría
   → Badge "Datos cacheados 5 min"
   → Segunda carga < 100ms (demostrar con DevTools Network tab)

2. Reporte filtrable:
   → /reportes/ventas/ → tabla sin filtros (todos los registros)
   → Filtrar por cliente → resultados actualizados
   → Filtrar por rango de fechas → resultados precisos
   → Exportar Excel → descarga inmediata con estilos Fable 5

3. Histórico de precios:
   → /productos/1/ → clic en botón "Historial"
   → Timeline con creación en verde, modificaciones con flecha
   → Precio que subió: rojo ▲ / precio que bajó: verde ▼
   → Desde el admin: editar precio → guardar → volver al historial
     → nuevo registro visible con el cambio resaltado

4. Mostrar los tests:
   → python manage.py test tests --verbosity=0
   → Ran 195 tests … OK

5. Declarar Sprint Goal y Hito M7 verificados:
   → Estado: ✅ HITO M7 ALCANZADO
```

### Tabla de verificación del Sprint Goal M7

| Criterio | Estado |
|---|---|
| GET /reportes/ → 5 KPIs cacheados visibles | ✅ |
| 3 gráficas Chart.js con datos reales | ✅ |
| Segunda carga del dashboard < 100ms (caché) | ✅ |
| Reportes filtrables por fecha/cliente/producto | ✅ |
| Exportación Excel síncrona | ✅ |
| Exportación asíncrona con correo de aviso | ✅ |
| Histórico de precios en timeline visual | ✅ |
| Botón "History" en el admin de Producto | ✅ |
| 195 tests acumulados OK | ✅ |

---

## PARTE 9 — Sprint 6 Retrospectiva + Ficha Schmelkes E7 (20 min)

### 9.1 Crear `sprint6_retrospective.md`

```markdown
# Sprint 6 Retrospective — ERP Django
## Semanas W19–W21 · Espiral 7: Dashboard y Reportes

**Fecha:** ___/___/_____

## ¿Qué funcionó bien? (Keep)
1. cache.get_or_set() con locmem en tests aisló perfectamente
   las pruebas sin depender de Redis corriendo.
2. Extraer generar_excel_ventas/pdf a reportes/exports.py evitó
   duplicar código entre la vista síncrona y la tarea async.
3. django-simple-history se instaló con cero configuración extra
   en el admin: el botón History apareció automáticamente.

## ¿Qué mejorar? (Improve)
1. El template del historial podría incluir paginación para productos
   con cientos de cambios de precio.
2. El umbral UMBRAL_ASYNC debería ser configurable desde settings,
   no hardcodeado en views.py.

## Acción de mejora (Kaizen) para Sprint 7
> "En el Sprint 7 (Pruebas de Integración), usaré factory_boy para
>  generar datos de prueba más complejos y realistas."

## Velocidad del Sprint 6

| HU | Pts plan. | Pts ent. |
|---|---|---|
| HU-E7-01 5 KPIs del negocio | 3 | 3 |
| HU-E7-02 Gráfica últimos 7 días | 3 | 3 |
| HU-E7-03 Top 5 productos | 2 | 2 |
| HU-E7-04 Exportar filtrado Excel | 3 | 3 |
| HU-E7-05 Filtrar por fecha/cliente/producto | 2 | 2 |
| HU-E7-06 Histórico de precios | 3 | 3 |
| HU-E7-07 Dashboard < 1 segundo | 2 | 2 |
| **Total** | **18** | **18** |

**Velocidad Sprint 6:** 18 puntos
**Velocidad acumulada (S0–S6):** 141 puntos
```

---

### 9.2 Crear `fichas/espiral_07_dashboard_reportes.md`

```markdown
# Ficha de Sistematización — Espiral 7
## ERP Django · Espiral E7: Dashboard y Reportes

| Campo | Contenido |
|---|---|
| **Número de espiral** | 7 |
| **Nombre del ciclo** | Dashboard y Reportes |
| **Semanas** | W19 – W21 |
| **Fecha de inicio** | ___/___/_____ |
| **Fecha de cierre** | ___/___/_____ |
| **Responsable** | [Nombre del estudiante] |
| **Asesor** | MC. Román Fernando López González |

## 1. Objetivo del ciclo
Implementar un módulo de inteligencia de negocio con dashboard de KPIs
cacheados, reportes filtrables con exportación adaptativa, e histórico
completo de cambios de precio.

## 2. Tareas realizadas

| # | Tarea | Estado | Semana |
|---|---|---|---|
| 1 | CACHES con Redis (DB separada del broker) | ✅ | W19 |
| 2 | _calcular_kpis(): 5 KPIs + 3 datasets | ✅ | W19 |
| 3 | DashboardView con cache.get_or_set() | ✅ | W19 |
| 4 | Template dashboard.html + 3 gráficas Chart.js | ✅ | W19 |
| 5 | reportes/filters.py: VentaReporteFilter | ✅ | W20 |
| 6 | reportes/models.py: ExportacionReporte | ✅ | W20 |
| 7 | ReporteVentasView + exportación síncrona | ✅ | W20 |
| 8 | reportes/exports.py (funciones reutilizables) | ✅ | W20 |
| 9 | Exportación asíncrona > UMBRAL_ASYNC | ✅ | W20 |
| 10 | django-simple-history instalado | ✅ | W21 |
| 11 | HistoricalRecords en Producto, Venta, Pedido | ✅ | W21 |
| 12 | HistoricoProductoView + template timeline | ✅ | W21 |
| 13 | Migraciones históricas aplicadas | ✅ | W21 |

## 3. Evidencias
- Dashboard: /reportes/ → 5 KPIs + 3 gráficas
- Caché: segunda carga < 100ms (verificar con DevTools)
- Exportación: /reportes/exportar/?formato=excel → descarga inmediata
- Histórico: /productos/<id>/historico/ → timeline de cambios
- Admin: botón "History" en cada producto
- Tests: Ran 195 tests → OK

## 4. Criterios de aceptación

| Criterio | Estado |
|---|---|
| GET /reportes/ → 5 KPIs cacheados | ✅ |
| 3 gráficas Chart.js renderizadas | ✅ |
| Reporte filtrado por fecha/cliente/producto | ✅ |
| Exportación Excel síncrona | ✅ |
| Exportación asíncrona > 1000 filas | ✅ |
| Histórico de precios en timeline | ✅ |
| history_type '+' en creación, '~' en edición | ✅ |
| diff_against() detecta campo precio | ✅ |
| 195 tests OK | ✅ |

## 5. Problemas encontrados
(completar durante la sesión)

## 6. Lecciones aprendidas
1.
2.
3.

## 7. Tiempo total invertido

| Categoría | Horas |
|---|---|
| Diseño | |
| Implementación | |
| Pruebas | |
| Documentación | |
| **Total Espiral 7** | |
```

---

## CIERRE — Commit Final [M7] y Respaldo (10 min)

### Actualizar `sprint6_planning.md`

```markdown
## Sprint 6 — Estado final W21

| HU | Estado | Pts |
|---|---|---|
| HU-E7-01 a HU-E7-07 | ✅ Completadas | 18/18 |

## Hito M7 — ALCANZADO ✅
- Dashboard: 5 KPIs + 3 gráficas Chart.js + caché Redis
- Reportes: filtrables + exportación Excel/PDF sync + async
- Histórico: simple_history en Producto, Venta, Pedido
- Vista timeline: /productos/<id>/historico/ con resaltado de cambios
- Admin: botón History automático en todos los modelos con HistoricalRecords
- Tests: Ran 195 tests → OK
- Fecha: ___/___/_____
```

### Push final a Render

```cmd
git add .
git status

:: Verificar que incluye:
::   core/settings.py (simple_history + middleware + config)
::   productos/models.py (history = HistoricalRecords)
::   ventas/models.py (history en Venta y Pedido)
::   productos/migrations/0003_historicalproducto.py
::   ventas/migrations/0005_historicalventa_historicalpedido.py
::   productos/views.py (HistoricoProductoView)
::   productos/urls.py (ruta historico)
::   productos/templates/productos/historico.html
::   productos/templates/productos/detalle.html (botón Historial)
::   tests/test_w21_historico.py
::   sprint6_retrospective.md
::   sprint6_planning.md (actualizado)
::   fichas/espiral_07_dashboard_reportes.md

git commit -m "Sprint 6 CIERRE [M7]: simple_history + historial precios + 195 tests OK + Ficha E7"
git push origin main
```

Verificar en Render:
```
==> Running: python manage.py migrate
    Applying productos.0003_historicalproducto... OK
    Applying ventas.0005_historicalventa_historicalpedido... OK
==> Build successful
```

```cmd
E:\finalizar_sesion.bat
```

---

## CHECKLIST FINAL W21 — HITO M7

### Técnico

```
DJANGO-SIMPLE-HISTORY
[ ] pip install django-simple-history==3.5.0 → sin errores
[ ] 'simple_history' en INSTALLED_APPS
[ ] HistoryRequestMiddleware al FINAL de MIDDLEWARE
[ ] SIMPLE_HISTORY_REVERT_DISABLED = True en settings.py

MODELOS CON HISTORIAL
[ ] Producto.history = HistoricalRecords() antes de class Meta
[ ] Venta.history    = HistoricalRecords()
[ ] Pedido.history   = HistoricalRecords()
[ ] productos/migrations/0003_historicalproducto.py aplicada
[ ] ventas/migrations/0005_historicalventa_historicalpedido.py aplicada
[ ] shell: prod.history.count() == 1 tras crear un producto
[ ] shell: prod.history.count() == 2 tras editar y guardar

VISTA Y TEMPLATE
[ ] HistoricoProductoView(LoginRequiredMixin, TemplateView)
[ ] get_context_data: itera history.all()[:100] y anota cambios con diff_against
[ ] Template historico.html: timeline con puntos de color
[ ] Precio sube → rojo ▲ / precio baja → verde ▼
[ ] history_user visible (requiere middleware activo)
[ ] URL /productos/<id>/historico/ registrada
[ ] Botón "Historial" en productos/detalle.html

ADMIN
[ ] /admin/productos/producto/<id>/history/ → HTTP 200
[ ] Botón "HISTORY" visible en el formulario de edición del admin

TESTS
[ ] test tests.test_w21_historico → 8/8 OK (o más según implementación)
[ ] test tests → 195/195 OK acumulados
[ ] test history.count() == 1 tras creación
[ ] test history_type == '+' en creación
[ ] test history_type == '~' en modificación
[ ] test precio histórico conserva valor original
[ ] test diff_against detecta campo 'precio'
[ ] test vista historico sin auth → 302
[ ] test vista historico con auth → 200

SCRUM / SCHMELKES
[ ] sprint6_planning.md: 18/18 puntos entregados
[ ] sprint6_retrospective.md: 3 secciones + Kaizen + velocidad
[ ] fichas/espiral_07_dashboard_reportes.md: 13 tareas completadas
[ ] Commit de cierre con etiqueta [M7]
[ ] git push → migraciones históricas en Render OK
[ ] finalizar_sesion.bat → archivos en USB
```

---

## DIAGRAMA: Ciclo de vida de un registro histórico (W21)

```
Acción en el sistema:
    admin_user → Editar producto "Laptop" → precio: 10000 → 9500 → Guardar

    ┌─────────────────────────────────────────────────────────────────┐
    │  Django: Producto.save()                                        │
    │      │                                                          │
    │      ├─ Guarda el objeto actual en tabla 'productos_producto'   │
    │      │      precio = 9500                                       │
    │      │                                                          │
    │      └─ simple_history detecta el save() via signal post_save   │
    │              │                                                  │
    │              ├─ history_type = '~' (modificación)              │
    │              ├─ history_date = 2025-01-15 17:45:23             │
    │              ├─ history_user = admin_user (via middleware)      │
    │              ├─ precio = 9500  (estado actual completo)         │
    │              ├─ stock  = 5                                      │
    │              └─ INSERT en 'productos_historicalproducto'        │
    └─────────────────────────────────────────────────────────────────┘

GET /productos/1/historico/ (con login):
    │
    ▼
HistoricoProductoView.get_context_data()
    │
    ├─ Producto.objects.get(pk=1)
    ├─ producto.history.all()[:100]
    │       → [registro@17:45 (precio=9500), registro@09:30 (precio=10000)]
    │
    ├─ Para cada registro i:
    │       delta = registro[i].diff_against(registro[i+1])
    │       cambios = {'precio': {'anterior': 10000, 'nuevo': 9500}}
    │
    └─ render historico.html
            │
            ▼
    Timeline visual:
    ●─── [~] 17:45:23  admin_user
    │        precio: 10000 → 9500 ▼  (verde: bajó)
    │
    ●─── [+] 09:30:00  Sistema
             Creación del producto
             precio=10000 / stock=5
```

---

## HILO CONDUCTOR → W22

**¿Qué cierra W21 / Espiral 7?**
La suite completa de inteligencia de negocio: dashboard KPI cacheado,
reportes filtrables con exportación adaptativa, e histórico completo
de auditoría con `django-simple-history`. 195 tests garantizan
que todo el sistema funciona. Hito M7 declarado.

**¿Qué abre W22 / Espiral 8 / Sprint 7?**
Con la funcionalidad del ERP completa (Espirales 1–7), las semanas
finales se dedican a la **calidad del software**: pruebas de integración,
cobertura de código ≥ 80% y preparación del entregable final.

**¿Qué necesita W22 de W21?**

| Artefacto de W21 | Uso en W22 |
|---|---|
| 195 tests unitarios | W22 los complementa con tests de integración (flujo completo compra → pago → webhook → correo) |
| `HistoricalRecords` en Producto | W22 los incluye en el análisis de cobertura |
| Todos los modelos con migraciones | W22 usa `pytest-django` con una BD de test pre-populada |
| Sprint 6 cerrado con M7 | W22 inicia con retrospectiva de todo el programa y plan de entrega final |

**Tarea de investigación para W22:**
> Lee la documentación de `coverage.py` con Django:
> `https://coverage.readthedocs.io/en/latest/`
>
> ¿Cómo se genera un reporte HTML de cobertura de código?
> ¿Qué significa que una línea esté "cubierta"? ¿Y una rama (`branch`)?
> ¿Por qué la cobertura del 100% no garantiza que el código sea correcto?

**Pregunta de reflexión:**
> "Al agregar `HistoricalRecords` a `Producto`, ¿qué impacto tiene
> en el rendimiento de `Producto.save()`? ¿En qué escenario del ERP
> (por ejemplo, importar 10,000 productos desde un CSV) esto podría
> ser un problema? ¿Cómo lo resolverías?"

---

## Referencia rápida de comandos W21

```cmd
:: SESIÓN
E:\iniciar_sesion.bat
E:\finalizar_sesion.bat

:: DJANGO
python manage.py check
python manage.py makemigrations productos --name historico_producto
python manage.py makemigrations ventas    --name historico_venta_pedido
python manage.py showmigrations
python manage.py migrate
python manage.py runserver

:: SHELL — explorar el historial
python manage.py shell
>>> from productos.models import Producto
>>> p = Producto.objects.first()
>>> p.history.all()
>>> p.history.count()
>>> for h in p.history.all(): print(h.history_type, h.precio, h.history_date)

:: TESTS
python manage.py test tests.test_w21_historico --verbosity=2
python manage.py test tests --verbosity=0   (195 tests)

:: GIT
git add .
git commit -m "Sprint 6 CIERRE [M7]: descripción"
git push origin main
git log --oneline
```

---

*Guía de Laboratorio W21 · ERP Django*
*Espiral 7 Cierre · Sprint 6 Review + Retrospectiva · Hito M7*
*SEP 3061300006-23 · UTEC Celaya · MC. Román Fernando López González*

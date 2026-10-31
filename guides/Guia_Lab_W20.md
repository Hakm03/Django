# Guía de Laboratorio — W20
## ERP Django · Espiral 7 · Semana 20 de 24
### Técnico en Programación (SEP 3061300006-23) · UTEC Celaya
### Asesor: MC. Román Fernando López González

---

| Campo | Detalle |
|---|---|
| **Semana** | W20 de 24 |
| **Espiral** | E7 — Dashboard y Reportes |
| **Sprint Scrum** | Sprint 6 — Desarrollo |
| **Hito** | Sin hito propio · Avance hacia M7 (W21) |
| **Horario** | 16:45 – 19:45 (180 min) |
| **Nivel Schmelkes** | 4 — Funcionalidades Avanzadas |
| **Hilo conductor** | "W19 mostró el panorama general. W20 permite hacer zoom: filtrar, exportar, y no bloquear al usuario si el reporte es grande." |

---

## Respuesta a la tarea de investigación de W19

> **¿Cómo se integra `FilterSet` con una `ListView` existente?**
>
> El patrón es el mismo que ya usamos en W13 con `ProductoFilter`:
> en `get_queryset()`, se instancia el filtro con `self.request.GET`
> y el queryset base, y se retorna `self.filtro.qs`. El objeto filtro
> completo se agrega al contexto para que el template pueda renderizar
> el formulario de filtros.
>
> ```python
> def get_queryset(self):
>     qs = Modelo.objects.all()
>     self.filtro = MiFilterSet(self.request.GET, queryset=qs)
>     return self.filtro.qs
> ```
>
> **¿Ventaja de `DateFromToRangeFilter` sobre dos campos separados?**
>
> | Enfoque | Código en `filters.py` | Código en el template |
> |---|---|---|
> | Dos campos (`fecha_inicio`, `fecha_fin`) | 2 declaraciones `DateFilter` | 2 campos a renderizar por separado |
> | `DateFromToRangeFilter` | 1 declaración | El widget renderiza ambos inputs juntos automáticamente |
>
> Además, `DateFromToRangeFilter` aplica automáticamente `gte`/`lte`
> sobre el mismo campo del modelo, evitando errores de "inicio mayor
> que fin" mal manejados manualmente.

---

## Objetivos de la sesión

Al terminar W20, el estudiante será capaz de:

1. Crear `VentaReporteFilter` con filtro de rango de fechas, cliente y producto
2. Implementar `ReporteVentasView` filtrable con `django-filter`
3. Extraer la lógica de generación de Excel/PDF a funciones reutilizables
4. Implementar exportación **síncrona** (≤1000 filas) y **asíncrona** vía
   Celery (>1000 filas) con notificación por correo
5. Modelar `ExportacionReporte` para rastrear exportaciones pendientes
6. Escribir 8 tests que verifican filtros y ambas rutas de exportación

---

## Stack tecnológico de W20

| Herramienta / Concepto | Novedad en W20 | Descripción |
|---|---|---|
| `DateFromToRangeFilter` | ✅ Nuevo | Filtro de rango de fechas con un solo campo declarado |
| `RangeWidget` | ✅ Nuevo | Widget que renderiza dos inputs (desde/hasta) para un rango |
| `ContentFile` | ✅ Nuevo | Convierte bytes en memoria a un archivo guardable en `FileField` |
| Exportación diferida | ✅ Nuevo | Patrón: generar en background + avisar por correo cuando termine |
| `JSONField` en `ExportacionReporte` | ya usado (W15) | Guarda los filtros aplicados para reconstruirlos en la tarea async |

---

## Mapa de tiempo (180 min)

| Parte | Actividad | Tiempo |
|---|---|---|
| Arranque | Daily Scrum + verificar W19 | 10 min |
| Parte 1 | `reportes/filters.py`: `VentaReporteFilter` | 20 min |
| Parte 2 | `reportes/models.py`: `ExportacionReporte` + migración | 15 min |
| Parte 3 | `ReporteVentasView` + template filtrable | 25 min |
| Parte 4 | `reportes/exports.py`: funciones reutilizables | 20 min |
| Parte 5 | Vista `exportar_reporte`: síncrona vs. asíncrona | 20 min |
| Parte 6 | `reportes/tasks.py`: `generar_exportacion_async` | 20 min |
| Parte 7 | Templates restantes + botones de exportación | 15 min |
| Parte 8 | Tests W20 (8 pruebas) | 25 min |
| Cierre | Commit · `finalizar_sesion.bat` · hilo → W21 | 10 min |
| **Total** | | **180 min** |

---

## ARRANQUE — Daily Scrum (10 min)

```cmd
E:\iniciar_sesion.bat
```

### Daily Scrum

```
1. ¿Qué hice en W19?
   → Configuré caché Redis, calculé 5 KPIs con aggregate/annotate
     y construí el dashboard con 3 gráficas Chart.js.

2. ¿Qué haré en W20?
   → Implementaré reportes filtrables por fecha, cliente y producto,
     con exportación síncrona o asíncrona según el volumen de datos.

3. ¿Tengo algún impedimento?
   → (registrar aquí)
```

### Verificar estado

```cmd
python manage.py check
python manage.py test tests --verbosity=0
```

**Resultado esperado:** `System check identified no issues` · `Ran 179 tests … OK`

---

## PARTE 1 — `reportes/filters.py`: `VentaReporteFilter` (20 min)

### 1.1 Crear el archivo de filtros

```python
# reportes/filters.py
"""Filtros para el reporte de ventas — W20."""
import django_filters

from clientes.models  import Cliente
from productos.models import Producto
from ventas.models    import Venta


class VentaReporteFilter(django_filters.FilterSet):
    """Filtro de ventas para el reporte administrativo.

    Permite filtrar por:
        fecha:    rango de fechas (desde/hasta) sobre Venta.fecha.
        cliente:  cliente exacto (selector).
        producto: producto incluido en alguna línea de la venta
                  (filtra a través de la relación inversa detalles).
    """

    fecha = django_filters.DateFromToRangeFilter(
        field_name='fecha',
        label='Rango de fechas',
        widget=django_filters.widgets.RangeWidget(
            attrs={'type': 'date', 'class': 'erp-input'}
        ),
    )
    cliente = django_filters.ModelChoiceFilter(
        queryset=Cliente.objects.filter(activo=True).order_by('nombre'),
        label='Cliente',
        empty_label='Todos los clientes',
    )
    producto = django_filters.ModelChoiceFilter(
        field_name='detalles__producto',
        queryset=Producto.objects.filter(activo=True).order_by('nombre'),
        label='Producto',
        empty_label='Todos los productos',
        distinct=True,    # evita duplicar Venta si tiene varias líneas del mismo producto
    )

    class Meta:
        model  = Venta
        fields = ['fecha', 'cliente', 'producto']
```

> **Nota sobre `distinct=True`:** al filtrar por `detalles__producto`,
> Django hace un JOIN con `DetalleVenta`. Si una venta tuviera dos
> líneas con el mismo producto, aparecería duplicada en los resultados
> sin `distinct=True`.

---

## PARTE 2 — `reportes/models.py`: `ExportacionReporte` (15 min)

### 2.1 ¿Por qué necesitamos un modelo para rastrear exportaciones?

```
Exportación SÍNCRONA (≤1000 filas):
  GET /reportes/exportar/?formato=excel
      → genera el archivo en la misma petición
      → el usuario espera unos segundos y descarga directo

Exportación ASÍNCRONA (>1000 filas):
  GET /reportes/exportar/?formato=excel
      → la petición NO puede esperar minutos generando el archivo
      → se crea un registro ExportacionReporte (estado: pendiente)
      → Celery genera el archivo en segundo plano
      → al terminar, marca completado=True y envía correo con el link
      → el usuario revisa su correo más tarde
```

### 2.2 Crear `reportes/models.py`

```python
# reportes/models.py
"""Modelos de la app reportes — W20.

ExportacionReporte rastrea las exportaciones generadas de forma
asíncrona (más de 1000 filas), permitiendo reconstruir el filtro
original en la tarea Celery y notificar al usuario por correo
cuando el archivo esté listo.
"""
from django.conf import settings
from django.db import models


class ExportacionReporte(models.Model):
    """Registro de una exportación de reporte generada en background.

    Atributos:
        usuario:    quién solicitó la exportación.
        formato:    'excel' o 'pdf'.
        filtros:    copia de los parámetros GET aplicados (para
                    reconstruir el mismo queryset en la tarea async).
        archivo:    el archivo generado (None hasta que termine).
        completado: True cuando la tarea terminó exitosamente.
        error:      mensaje de error si la generación falló.
    """

    FORMATO_CHOICES = [
        ('excel', 'Excel (.xlsx)'),
        ('pdf',   'PDF'),
    ]

    usuario    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='exportaciones',
        verbose_name='Usuario solicitante',
    )
    formato    = models.CharField(
        max_length=10, choices=FORMATO_CHOICES, verbose_name='Formato'
    )
    filtros    = models.JSONField(
        default=dict, blank=True, verbose_name='Filtros aplicados'
    )
    archivo    = models.FileField(
        upload_to='exportaciones/', null=True, blank=True,
        verbose_name='Archivo generado'
    )
    completado = models.BooleanField(
        default=False, verbose_name='Completado'
    )
    error      = models.TextField(
        blank=True, verbose_name='Mensaje de error'
    )
    creado     = models.DateTimeField(
        auto_now_add=True, verbose_name='Fecha de solicitud'
    )

    class Meta:
        verbose_name        = 'Exportación de reporte'
        verbose_name_plural  = 'Exportaciones de reportes'
        ordering             = ['-creado']

    def __str__(self) -> str:
        estado = 'completada' if self.completado else 'pendiente'
        return f'Exportación {self.get_formato_display()} #{self.pk} ({estado})'
```

### 2.3 Crear y aplicar la migración

> **Nota:** esta es la **primera migración** de la app `reportes`,
> ya que hasta ahora solo tenía vistas (sin modelos propios).

```cmd
python manage.py makemigrations reportes --name exportacion_reporte_inicial
python manage.py migrate
```

**Resultado esperado:**
```
Migrations for 'reportes':
  reportes/migrations/0001_initial.py
    - Create model ExportacionReporte
Applying reportes.0001_initial... OK
```

### 2.4 Registrar en el admin (opcional pero recomendado)

```python
# reportes/admin.py
"""Configuración del panel admin para reportes — W20."""
from django.contrib import admin

from .models import ExportacionReporte


@admin.register(ExportacionReporte)
class ExportacionReporteAdmin(admin.ModelAdmin):
    """Admin de exportaciones — útil para depurar tareas fallidas."""

    list_display    = ['pk', 'usuario', 'formato', 'completado', 'creado']
    list_filter     = ['formato', 'completado']
    readonly_fields = ['creado', 'filtros']
    search_fields   = ['usuario__username']
```

### 2.5 Verificar

```cmd
python manage.py check
python manage.py showmigrations reportes
```

```
reportes
 [X] 0001_initial
```

---

## PARTE 3 — `ReporteVentasView` con Filtro (25 min)

### 3.1 Reemplazar/ampliar `reportes/views.py`

Agregar imports al inicio del archivo (junto a los existentes de W19):

```python
# reportes/views.py — agregar imports al inicio:
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import ListView

from ventas.models   import Venta
from .filters import VentaReporteFilter
from .models  import ExportacionReporte
```

Agregar la vista al final de `reportes/views.py`:

```python
# reportes/views.py — agregar al final del archivo:

class ReporteVentasView(LoginRequiredMixin, ListView):
    """Reporte de ventas filtrable por fecha, cliente y producto.

    Permite consultar el histórico completo de ventas (a diferencia
    del dashboard de W19, que solo muestra agregados de los últimos
    7 días).
    """

    model               = Venta
    template_name       = 'reportes/reporte_ventas.html'
    context_object_name = 'ventas'
    paginate_by         = 20

    def get_queryset(self):
        """Aplica el filtro VentaReporteFilter sobre el queryset base."""
        qs = (
            Venta.objects
            .select_related('cliente')
            .prefetch_related('detalles__producto')
            .order_by('-fecha')
        )
        self.filtro = VentaReporteFilter(self.request.GET, queryset=qs)
        return self.filtro.qs.distinct()

    def get_context_data(self, **kwargs) -> dict:
        """Agrega el objeto filtro y el conteo total al contexto."""
        ctx = super().get_context_data(**kwargs)
        ctx['filtro']         = self.filtro
        ctx['total_filtrado'] = self.filtro.qs.distinct().count()
        return ctx
```

---

### 3.2 Crear `reportes/templates/reportes/reporte_ventas.html`

```html
{% extends "base.html" %}
{% block title %}Reporte de ventas{% endblock %}
{% block nav_reportes %}active{% endblock %}

{% block content %}
<div class="erp-page-title">
    <h2>📋 Reporte de ventas</h2>
    <span style="margin-left:auto;color:var(--clr-muted);font-size:.85rem;">
        {{ total_filtrado }} venta(s) encontradas
    </span>
</div>

<!-- Filtros -->
<div class="erp-card" style="margin-bottom:1.5rem;">
    <div class="erp-card-header">🔍 Filtrar reporte</div>
    <form method="get" style="margin-top:.5rem;">
        <div class="row g-3 align-items-end">
            <div class="col-md-4">
                <label class="erp-label">Rango de fechas</label>
                {{ filtro.form.fecha }}
            </div>
            <div class="col-md-3">
                <label class="erp-label">Cliente</label>
                {{ filtro.form.cliente }}
            </div>
            <div class="col-md-3">
                <label class="erp-label">Producto</label>
                {{ filtro.form.producto }}
            </div>
            <div class="col-md-2">
                <button type="submit" class="btn-erp-primary w-100">
                    Filtrar
                </button>
            </div>
        </div>
        {% if request.GET %}
        <div style="margin-top:.75rem;">
            <a href="{% url 'reportes:reporte_ventas' %}"
               style="color:var(--clr-muted);font-size:.85rem;">
                ✕ Limpiar filtros
            </a>
        </div>
        {% endif %}
    </form>
</div>

<!-- Botones de exportación — conservan los filtros activos -->
<div class="d-flex gap-2 mb-3">
    <a href="{% url 'reportes:exportar' %}?{{ request.GET.urlencode }}{% if request.GET %}&{% endif %}formato=excel"
       class="btn-erp-gold">
        📊 Exportar Excel
    </a>
    <a href="{% url 'reportes:exportar' %}?{{ request.GET.urlencode }}{% if request.GET %}&{% endif %}formato=pdf"
       class="btn-erp-primary">
        📄 Exportar PDF
    </a>
</div>

<!-- Tabla de resultados -->
{% if ventas %}
<table class="erp-table">
    <thead>
        <tr>
            <th>#</th>
            <th>Cliente</th>
            <th>Fecha</th>
            <th>Productos</th>
            <th>Total</th>
        </tr>
    </thead>
    <tbody>
        {% for v in ventas %}
        <tr>
            <td>
                <a href="{% url 'ventas:detalle' v.pk %}"
                   style="color:var(--clr-royal);font-weight:600;">
                    #{{ v.pk }}
                </a>
            </td>
            <td>{{ v.cliente.nombre }}</td>
            <td>{{ v.fecha|date:"d/m/Y H:i" }}</td>
            <td style="font-size:.85rem;color:var(--clr-muted);">
                {% for d in v.detalles.all %}
                    {{ d.producto.nombre }}{% if not forloop.last %}, {% endif %}
                {% endfor %}
            </td>
            <td style="font-weight:600;color:var(--clr-gold);">
                ${{ v.total }}
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>

<!-- Paginación (preserva filtros) -->
{% if is_paginated %}
<div style="display:flex;gap:.5rem;justify-content:center;margin-top:1.5rem;">
    {% if page_obj.has_previous %}
        <a href="?{% if request.GET.urlencode %}{{ request.GET.urlencode }}&{% endif %}page={{ page_obj.previous_page_number }}"
           class="btn-erp-primary btn-erp-sm">← Anterior</a>
    {% endif %}
    <span style="padding:.35rem .75rem;color:var(--clr-muted);font-size:.88rem;">
        Página {{ page_obj.number }} de {{ page_obj.paginator.num_pages }}
    </span>
    {% if page_obj.has_next %}
        <a href="?{% if request.GET.urlencode %}{{ request.GET.urlencode }}&{% endif %}page={{ page_obj.next_page_number }}"
           class="btn-erp-primary btn-erp-sm">Siguiente →</a>
    {% endif %}
</div>
{% endif %}

{% else %}
<div class="erp-alert-info">
    No se encontraron ventas con los filtros seleccionados.
</div>
{% endif %}
{% endblock %}
```

---

## PARTE 4 — `reportes/exports.py`: Funciones Reutilizables (20 min)

### 4.1 ¿Por qué extraer la lógica a un módulo separado?

```
Sin extraer:               Con extraer (reportes/exports.py):
  views.py (síncrono)        views.py    → llama generar_excel_ventas()
    código Excel completo    tasks.py    → llama generar_excel_ventas()
  tasks.py (asíncrono)              ambos reutilizan EXACTAMENTE
    código Excel duplicado          la misma función — sin duplicación
```

### 4.2 Crear `reportes/exports.py`

```python
# reportes/exports.py
"""Funciones de generación de reportes — W20.

Reutilizadas tanto por la vista síncrona (exportar_reporte)
como por la tarea asíncrona (generar_exportacion_async),
evitando duplicar la lógica de construcción de Excel/PDF.
"""
import io
from decimal import Decimal

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill


def generar_excel_ventas(queryset) -> io.BytesIO:
    """Genera un archivo Excel con el listado de ventas dado.

    Args:
        queryset: QuerySet de Venta (ya filtrado).

    Returns:
        io.BytesIO con el contenido del archivo .xlsx, listo para leer.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Reporte de Ventas'

    # ── Estilos Fable 5 AzulERP ─────────────────────────────────────────
    encabezado_font  = Font(bold=True, color='FFFFFF', size=11)
    encabezado_fill  = PatternFill('solid', fgColor='0A2342')
    encabezado_align = Alignment(horizontal='center', vertical='center')

    columnas = [
        ('#',          8),
        ('Cliente',    32),
        ('Fecha',      20),
        ('Productos',  40),
        ('Total ($)',  14),
    ]
    for idx, (titulo, ancho) in enumerate(columnas, start=1):
        celda = ws.cell(row=1, column=idx, value=titulo)
        celda.font      = encabezado_font
        celda.fill      = encabezado_fill
        celda.alignment = encabezado_align
        ws.column_dimensions[
            openpyxl.utils.get_column_letter(idx)
        ].width = ancho
    ws.row_dimensions[1].height = 22

    # ── Filas de datos ────────────────────────────────────────────────
    fila = 2
    for venta in queryset:
        productos_str = ', '.join(
            d.producto.nombre for d in venta.detalles.all()
        )
        ws.cell(row=fila, column=1, value=venta.pk)
        ws.cell(row=fila, column=2, value=venta.cliente.nombre)
        ws.cell(row=fila, column=3, value=venta.fecha.strftime('%d/%m/%Y %H:%M'))
        ws.cell(row=fila, column=4, value=productos_str)
        celda_total = ws.cell(row=fila, column=5, value=float(venta.total))
        celda_total.alignment = Alignment(horizontal='right')
        fila += 1

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


def generar_pdf_ventas(queryset, contexto_extra: dict | None = None) -> io.BytesIO:
    """Genera un archivo PDF con el listado de ventas dado.

    Args:
        queryset:        QuerySet de Venta (ya filtrado).
        contexto_extra:  variables adicionales para el template.

    Returns:
        io.BytesIO con el contenido del archivo .pdf.
    """
    from xhtml2pdf import pisa
    from django.template.loader import render_to_string

    from configuracion.models import ConfiguracionERP

    ventas = list(queryset)
    total_general = sum(
        (v.total for v in ventas), Decimal('0.00')
    )

    contexto = {
        'ventas':        ventas,
        'config':        ConfiguracionERP.get_instance(),
        'total_general': total_general,
    }
    if contexto_extra:
        contexto.update(contexto_extra)

    html_string = render_to_string(
        'reportes/reporte_ventas_pdf.html', contexto
    )

    buffer    = io.BytesIO()
    resultado = pisa.CreatePDF(src=html_string, dest=buffer)

    if resultado.err:
        raise RuntimeError(f'Error al generar PDF: {resultado.err}')

    buffer.seek(0)
    return buffer
```

---

### 4.3 Crear `reportes/templates/reportes/reporte_ventas_pdf.html`

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Reporte de ventas</title>
    <style>
        @page { size: A4 landscape; margin: 1.5cm; }
        body { font-family: Arial, Helvetica, sans-serif; font-size: 10pt; }
        .header {
            background: #0A2342; color: #FFFFFF;
            padding: 14px 18px; border-bottom: 4px solid #B8860B;
            margin-bottom: 16px;
        }
        .header h1 { color: #D4AF37; font-size: 16pt; margin: 0; }
        table { width: 100%; border-collapse: collapse; }
        th {
            background: #0A2342; color: #FFFFFF;
            padding: 7px 10px; font-size: 9pt; text-align: left;
        }
        th.num { text-align: right; }
        td { padding: 6px 10px; border-bottom: 1px solid #E8F0FB; }
        td.num { text-align: right; }
        tr:nth-child(even) td { background: #F5F7FA; }
        .total-row td {
            background: #FDF8E8; font-weight: bold;
            border-top: 2px solid #B8860B; font-size: 11pt;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Reporte de Ventas — {{ config.nombre_empresa }}</h1>
    </div>

    <table>
        <thead>
            <tr>
                <th>#</th>
                <th>Cliente</th>
                <th>Fecha</th>
                <th>Productos</th>
                <th class="num">Total</th>
            </tr>
        </thead>
        <tbody>
            {% for v in ventas %}
            <tr>
                <td>{{ v.pk }}</td>
                <td>{{ v.cliente.nombre }}</td>
                <td>{{ v.fecha|date:"d/m/Y H:i" }}</td>
                <td>
                    {% for d in v.detalles.all %}
                        {{ d.producto.nombre }}{% if not forloop.last %}, {% endif %}
                    {% endfor %}
                </td>
                <td class="num">${{ v.total }}</td>
            </tr>
            {% endfor %}
        </tbody>
        <tfoot>
            <tr class="total-row">
                <td colspan="4" style="text-align:right;">TOTAL GENERAL:</td>
                <td class="num">${{ total_general }}</td>
            </tr>
        </tfoot>
    </table>
</body>
</html>
```

---

## PARTE 5 — Vista `exportar_reporte`: Síncrona vs. Asíncrona (20 min)

### 5.1 Agregar la vista a `reportes/views.py`

```python
# reportes/views.py — agregar al final del archivo:

UMBRAL_ASYNC = 1000   # filas; por debajo se exporta en la misma petición


@login_required
def exportar_reporte(request):
    """Exporta el reporte de ventas filtrado a Excel o PDF.

    Estrategia adaptativa según el volumen de datos:
        ≤ UMBRAL_ASYNC filas → genera y descarga en esta misma petición.
        > UMBRAL_ASYNC filas → encola una tarea Celery y notifica
                                por correo cuando el archivo esté listo.
    """
    from .exports import generar_excel_ventas, generar_pdf_ventas
    from .tasks   import generar_exportacion_async

    formato = request.GET.get('formato', 'excel')

    qs = (
        Venta.objects
        .select_related('cliente')
        .prefetch_related('detalles__producto')
        .order_by('-fecha')
    )
    filtro    = VentaReporteFilter(request.GET, queryset=qs)
    queryset  = filtro.qs.distinct()
    total     = queryset.count()

    # ── Ruta asíncrona: volumen grande ──────────────────────────────────
    if total > UMBRAL_ASYNC:
        exportacion = ExportacionReporte.objects.create(
            usuario = request.user,
            formato = formato,
            filtros = request.GET.dict(),
        )
        generar_exportacion_async.delay(exportacion.pk)

        messages.info(
            request,
            f'Tu reporte tiene {total} registros. '
            f'Te enviaremos un correo con el enlace de descarga '
            f'cuando esté listo.'
        )
        return redirect(
            'reportes:exportacion_en_proceso',
            exportacion_id=exportacion.pk
        )

    # ── Ruta síncrona: volumen manejable ────────────────────────────────
    if formato == 'excel':
        buffer = generar_excel_ventas(queryset)
        response = HttpResponse(
            buffer.read(),
            content_type=(
                'application/vnd.openxmlformats-officedocument'
                '.spreadsheetml.sheet'
            )
        )
        response['Content-Disposition'] = (
            'attachment; filename="reporte_ventas.xlsx"'
        )
    else:
        buffer = generar_pdf_ventas(queryset)
        response = HttpResponse(buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = (
            'attachment; filename="reporte_ventas.pdf"'
        )

    return response


@login_required
def exportacion_en_proceso(request, exportacion_id: int):
    """Página de espera mientras se genera la exportación asíncrona."""
    exportacion = get_object_or_404(
        ExportacionReporte, pk=exportacion_id, usuario=request.user
    )
    return render(request, 'reportes/exportacion_en_proceso.html', {
        'exportacion': exportacion,
    })
```

> Agregar también el import faltante al inicio del archivo:
> ```python
> from django.contrib import messages
> from django.http import HttpResponse
> ```

---

## PARTE 6 — `reportes/tasks.py`: Tarea Asíncrona (20 min)

### 6.1 Crear `reportes/tasks.py`

```python
# reportes/tasks.py
"""Tareas asíncronas de la app reportes — W20.

generar_exportacion_async: genera el archivo en background y notifica
                            al usuario por correo cuando está listo.
"""
import logging

from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=120,
    name='reportes.generar_exportacion_async',
)
def generar_exportacion_async(self, exportacion_id: int) -> dict:
    """Genera el archivo de exportación y notifica por correo.

    Reconstruye el queryset filtrado a partir de los parámetros
    guardados en ExportacionReporte.filtros, genera el Excel o PDF
    con las funciones reutilizables de reportes/exports.py, y
    guarda el resultado en el FileField del registro.

    Args:
        exportacion_id: ID del registro ExportacionReporte.

    Returns:
        dict con el estado del procesamiento.
    """
    from reportes.exports import generar_excel_ventas, generar_pdf_ventas
    from reportes.filters import VentaReporteFilter
    from reportes.models  import ExportacionReporte
    from ventas.models    import Venta

    try:
        exportacion = ExportacionReporte.objects.get(pk=exportacion_id)
    except ExportacionReporte.DoesNotExist:
        logger.error(
            f'[exportacion_async] Exportación {exportacion_id} no existe.'
        )
        return {'estado': 'error', 'razon': 'no encontrada'}

    # ── Reconstruir el mismo filtro aplicado por el usuario ────────────
    qs = (
        Venta.objects
        .select_related('cliente')
        .prefetch_related('detalles__producto')
        .order_by('-fecha')
    )
    filtro    = VentaReporteFilter(exportacion.filtros, queryset=qs)
    queryset  = filtro.qs.distinct()

    try:
        # ── Generar el archivo según el formato ─────────────────────────
        if exportacion.formato == 'excel':
            buffer = generar_excel_ventas(queryset)
            nombre = f'reporte_ventas_{exportacion.pk}.xlsx'
        else:
            buffer = generar_pdf_ventas(queryset)
            nombre = f'reporte_ventas_{exportacion.pk}.pdf'

        # ── Guardar en el FileField ──────────────────────────────────────
        exportacion.archivo.save(
            nombre, ContentFile(buffer.read()), save=False
        )
        exportacion.completado = True
        exportacion.save(update_fields=['archivo', 'completado'])

        logger.info(
            f'[exportacion_async] Exportación {exportacion.pk} '
            f'completada: {nombre} ({queryset.count()} filas).'
        )

        _enviar_correo_exportacion_lista(exportacion)

        return {'estado': 'ok', 'exportacion_id': exportacion_id}

    except Exception as exc:
        exportacion.error = str(exc)
        exportacion.save(update_fields=['error'])
        logger.error(
            f'[exportacion_async] Error al generar exportación '
            f'{exportacion_id}: {exc}'
        )
        raise self.retry(exc=exc, countdown=120)


def _enviar_correo_exportacion_lista(exportacion: 'ExportacionReporte') -> None:
    """Envía un correo con el enlace de descarga al solicitante.

    Args:
        exportacion: instancia de ExportacionReporte con archivo guardado.
    """
    # Las tareas Celery no tienen 'request', por lo que el dominio
    # debe construirse desde una constante de configuración.
    dominio = getattr(
        settings, 'SITE_DOMAIN', 'https://erp-django-utec.onrender.com'
    )
    url_descarga = f'{dominio}{exportacion.archivo.url}'

    mensaje = EmailMultiAlternatives(
        subject    = f'Tu reporte de ventas está listo (#{exportacion.pk})',
        body       = (
            f'Hola,\n\n'
            f'Tu exportación de ventas en formato '
            f'{exportacion.get_formato_display()} está lista.\n\n'
            f'Descárgala aquí: {url_descarga}\n\n'
            f'Equipo ERP Django'
        ),
        from_email = settings.DEFAULT_FROM_EMAIL,
        to         = [exportacion.usuario.email],
    )

    try:
        mensaje.send()
        logger.info(
            f'[exportacion_async] Correo de descarga enviado a '
            f'{exportacion.usuario.email}.'
        )
    except Exception as exc:
        logger.error(
            f'[exportacion_async] Error al enviar correo de '
            f'exportación: {exc}'
        )
```

### 6.2 Agregar `SITE_DOMAIN` a `settings.py`

```python
# core/settings.py — agregar cerca de ALLOWED_HOSTS:
SITE_DOMAIN = env('SITE_DOMAIN', default='http://127.0.0.1:8000')
```

```bash
# .env.example — agregar:
SITE_DOMAIN=https://erp-django-utec.onrender.com
```

---

## PARTE 7 — Template de Espera y Botones (15 min)

### 7.1 Crear `reportes/templates/reportes/exportacion_en_proceso.html`

```html
{% extends "base.html" %}
{% block title %}Exportación en proceso{% endblock %}

{% block content %}
<div style="display:flex;justify-content:center;align-items:center;
            min-height:50vh;">
    <div class="erp-card" style="max-width:480px;text-align:center;">
        <div style="font-size:3rem;margin-bottom:1rem;">
            {% if exportacion.completado %}✅{% else %}⏳{% endif %}
        </div>

        {% if exportacion.completado %}
            <h3 style="color:var(--clr-navy);">¡Tu reporte está listo!</h3>
            <p style="color:var(--clr-muted);margin:.75rem 0 1.5rem;">
                Formato: {{ exportacion.get_formato_display }}
            </p>
            <a href="{{ exportacion.archivo.url }}"
               class="btn-erp-gold" download>
                ⬇️ Descargar ahora
            </a>
        {% elif exportacion.error %}
            <h3 style="color:var(--clr-danger);">Error al generar el reporte</h3>
            <p style="color:var(--clr-muted);margin:.75rem 0 1.5rem;">
                {{ exportacion.error }}
            </p>
        {% else %}
            <h3 style="color:var(--clr-navy);">Generando tu reporte…</h3>
            <p style="color:var(--clr-muted);margin:.75rem 0 1.5rem;">
                Tu reporte de {{ exportacion.get_formato_display }}
                se está generando en segundo plano.
                Te enviaremos un correo a
                <strong>{{ exportacion.usuario.email }}</strong>
                con el enlace de descarga.
            </p>
        {% endif %}

        <a href="{% url 'reportes:reporte_ventas' %}"
           class="btn-erp-primary">
            ← Volver al reporte
        </a>
    </div>
</div>
{% endblock %}
```

### 7.2 Actualizar `reportes/urls.py`

```python
# reportes/urls.py
"""URLs de la app reportes — W20."""
from django.urls import path

from . import views

app_name = 'reportes'

urlpatterns = [
    # Dashboard (W19) — mantiene name='inicio' por compatibilidad navbar
    path('',
         views.DashboardView.as_view(),
         name='inicio'),

    # Reporte filtrable (W20)
    path('ventas/',
         views.ReporteVentasView.as_view(),
         name='reporte_ventas'),

    # Exportación
    path('exportar/',
         views.exportar_reporte,
         name='exportar'),
    path('exportacion/<int:exportacion_id>/',
         views.exportacion_en_proceso,
         name='exportacion_en_proceso'),
]
```

### 7.3 Agregar enlace al reporte desde el dashboard

En `reportes/templates/reportes/dashboard.html`, agregar después del
`erp-page-title`:

```html
<!-- Agregar dentro del bloque content, antes del kpi-grid -->
<div style="margin-bottom:1rem;">
    <a href="{% url 'reportes:reporte_ventas' %}" class="btn-erp-primary">
        📋 Ver reporte detallado de ventas →
    </a>
</div>
```

### 7.4 Verificar en el navegador

```cmd
python manage.py check
python manage.py runserver
```

```
[ ] /reportes/ventas/ con login → tabla de ventas + filtros
[ ] Filtrar por cliente → solo ventas de ese cliente
[ ] Filtrar por rango de fechas → solo ventas en ese rango
[ ] Exportar Excel con pocos registros → descarga inmediata
[ ] Exportar PDF con pocos registros → descarga inmediata
[ ] Botón "Ver reporte detallado" visible en el dashboard
```

---

## PARTE 8 — Tests W20 (25 min)

### 8.1 Crear `tests/test_w20_reportes.py`

```python
"""Suite de pruebas W20 — Reportes filtrables y exportación adaptativa.

Verifica filtros del reporte de ventas y ambas rutas de exportación
(síncrona y asíncrona), usando mock para forzar el umbral asíncrono
sin necesidad de crear 1000+ registros reales.

Ejecutar con:
    python manage.py test tests.test_w20_reportes --verbosity=2

Resultado esperado:
    Ran 8 tests in X.XXXs
    OK
"""
import tempfile
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from clientes.models   import Cliente
from configuracion.models import ConfiguracionERP
from productos.models  import Categoria, Producto
from reportes.models   import ExportacionReporte
from reportes.tasks    import generar_exportacion_async
from ventas.models     import DetalleVenta, Venta


EMAIL_SETTINGS = {
    'EMAIL_BACKEND':                'django.core.mail.backends.locmem.EmailBackend',
    'CELERY_TASK_ALWAYS_EAGER':     True,
    'CELERY_TASK_EAGER_PROPAGATES': True,
    'DEFAULT_FROM_EMAIL':           'test@erp.com',
}


def _crear_venta(cliente, producto, cantidad=1) -> Venta:
    """Crea una venta de prueba con una línea de detalle."""
    venta = Venta.objects.create(cliente=cliente)
    DetalleVenta.objects.create(
        venta=venta, producto=producto,
        cantidad=cantidad, precio_unitario=producto.precio
    )
    return venta


class ReporteFiltrosTest(TestCase):
    """Tests del filtrado en ReporteVentasView."""

    def setUp(self):
        self.user = User.objects.create_user('repuser', password='pass')
        cat            = Categoria.objects.create(nombre='Cat Rep')
        self.prod      = Producto.objects.create(
            nombre='Producto A', precio=Decimal('100.00'),
            stock=10, categoria=cat
        )
        self.otro_prod = Producto.objects.create(
            nombre='Producto B', precio=Decimal('50.00'),
            stock=10, categoria=cat
        )
        self.cli_a = Cliente.objects.create(nombre='Cliente A', correo='a@t.com')
        self.cli_b = Cliente.objects.create(nombre='Cliente B', correo='b@t.com')

        _crear_venta(self.cli_a, self.prod, cantidad=2)
        _crear_venta(self.cli_b, self.otro_prod, cantidad=1)

        self.client.force_login(self.user)

    def test_reporte_sin_auth_redirige_a_login(self):
        """GET /reportes/ventas/ sin login → 302."""
        self.client.logout()
        r = self.client.get(reverse('reportes:reporte_ventas'))
        self.assertEqual(r.status_code, 302)

    def test_filtro_por_cliente(self):
        """Filtrar por cliente debe devolver solo sus ventas."""
        r = self.client.get(
            reverse('reportes:reporte_ventas'),
            {'cliente': self.cli_a.pk}
        )
        ventas = list(r.context['ventas'])
        self.assertEqual(len(ventas), 1)
        self.assertEqual(ventas[0].cliente, self.cli_a)

    def test_filtro_por_producto(self):
        """Filtrar por producto debe devolver solo ventas con ese producto."""
        r = self.client.get(
            reverse('reportes:reporte_ventas'),
            {'producto': self.prod.pk}
        )
        ventas = list(r.context['ventas'])
        self.assertEqual(len(ventas), 1)
        self.assertEqual(ventas[0].cliente, self.cli_a)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ExportacionSincronaTest(TestCase):
    """Tests de la exportación síncrona (≤ UMBRAL_ASYNC filas)."""

    def setUp(self):
        self.user = User.objects.create_user('expuser', password='pass')
        cat        = Categoria.objects.create(nombre='Cat Exp')
        prod       = Producto.objects.create(
            nombre='Prod Exp', precio=Decimal('200.00'),
            stock=5, categoria=cat
        )
        cli        = Cliente.objects.create(nombre='Cli Exp', correo='exp@t.com')
        _crear_venta(cli, prod)
        self.client.force_login(self.user)

    def test_exportar_excel_descarga_inmediata(self):
        """Con pocas filas, exportar Excel debe descargar de inmediato."""
        r = self.client.get(
            reverse('reportes:exportar'), {'formato': 'excel'}
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn('spreadsheetml', r.get('Content-Type', ''))

    def test_exportar_pdf_descarga_inmediata(self):
        """Con pocas filas, exportar PDF debe descargar de inmediato."""
        r = self.client.get(
            reverse('reportes:exportar'), {'formato': 'pdf'}
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn('application/pdf', r.get('Content-Type', ''))


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(), **EMAIL_SETTINGS)
class ExportacionAsincronaTest(TestCase):
    """Tests de la exportación asíncrona (> UMBRAL_ASYNC filas, simulado)."""

    def setUp(self):
        mail.outbox = []
        ConfiguracionERP.get_instance()
        self.user = User.objects.create_user(
            'asyncuser', password='pass', email='async@test.com'
        )
        cat        = Categoria.objects.create(nombre='Cat Async')
        self.prod  = Producto.objects.create(
            nombre='Prod Async', precio=Decimal('300.00'),
            stock=5, categoria=cat
        )
        cli        = Cliente.objects.create(nombre='Cli Async', correo='ca@t.com')
        _crear_venta(cli, self.prod)
        self.client.force_login(self.user)

    @patch('reportes.views.UMBRAL_ASYNC', 0)   # fuerza la ruta async
    def test_exportar_supera_umbral_crea_registro_pendiente(self):
        """Si el total supera el umbral, se crea ExportacionReporte."""
        r = self.client.get(
            reverse('reportes:exportar'), {'formato': 'excel'}
        )
        self.assertEqual(ExportacionReporte.objects.count(), 1)
        exportacion = ExportacionReporte.objects.first()
        self.assertFalse(exportacion.completado)
        self.assertEqual(r.status_code, 302)   # redirect a página de espera

    def test_tarea_genera_archivo_y_marca_completado(self):
        """generar_exportacion_async debe generar el archivo y marcar listo."""
        exportacion = ExportacionReporte.objects.create(
            usuario=self.user, formato='excel', filtros={}
        )
        generar_exportacion_async.delay(exportacion.pk)

        exportacion.refresh_from_db()
        self.assertTrue(exportacion.completado)
        self.assertTrue(bool(exportacion.archivo))

    def test_tarea_envia_correo_con_link_descarga(self):
        """Al completar, debe enviarse un correo con el link al usuario."""
        exportacion = ExportacionReporte.objects.create(
            usuario=self.user, formato='pdf', filtros={}
        )
        generar_exportacion_async.delay(exportacion.pk)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('async@test.com', mail.outbox[0].to)
        self.assertIn('http', mail.outbox[0].body)
```

### 8.2 Ejecutar los tests

```cmd
python manage.py test tests.test_w20_reportes --verbosity=2
```

**Resultado esperado:**
```
test_exportar_excel_descarga_inmediata ... ok
test_exportar_pdf_descarga_inmediata ... ok
test_exportar_supera_umbral_crea_registro_pendiente ... ok
test_filtro_por_cliente ... ok
test_filtro_por_producto ... ok
test_reporte_sin_auth_redirige_a_login ... ok
test_tarea_envia_correo_con_link_descarga ... ok
test_tarea_genera_archivo_y_marca_completado ... ok

Ran 8 tests in X.XXXs
OK
```

### 8.3 Suite acumulada

```cmd
python manage.py test tests --verbosity=0
```

**Resultado esperado:** `Ran 187 tests in X.XXXs · OK` (179 + 8)

---

## CIERRE — Commit y Respaldo (10 min)

### Actualizar `sprint6_planning.md`

```markdown
## Sprint Backlog — actualización W20

| Tarea | Estado |
|---|---|
| Dashboard + KPIs + Chart.js + caché | ✅ W19 |
| reportes/filters.py: VentaReporteFilter | ✅ W20 |
| reportes/models.py: ExportacionReporte + migración 0001 | ✅ W20 |
| ReporteVentasView filtrable | ✅ W20 |
| reportes/exports.py: funciones reutilizables Excel/PDF | ✅ W20 |
| Exportación adaptativa (síncrona/asíncrona) | ✅ W20 |
| reportes/tasks.py: generar_exportacion_async | ✅ W20 |
| Correo con link de descarga | ✅ W20 |
| 8 tests de reportes y exportación | ✅ W20 |
| Histórico de precios (simple-history) | ⏳ W21 |
| Sprint 6 Review + Retrospectiva + Hito M7 | ⏳ W21 |
```

### Commit de cierre W20

```cmd
git add .
git status

:: Verificar que incluye:
::   reportes/filters.py
::   reportes/models.py + migrations/0001_initial.py
::   reportes/exports.py
::   reportes/tasks.py
::   reportes/views.py (actualizado)
::   reportes/urls.py (actualizado)
::   reportes/admin.py
::   reportes/templates/reportes/reporte_ventas.html
::   reportes/templates/reportes/reporte_ventas_pdf.html
::   reportes/templates/reportes/exportacion_en_proceso.html
::   tests/test_w20_reportes.py
::   sprint6_planning.md

git commit -m "Sprint 6 W20: reportes filtrables + exportacion sync/async + 187 tests OK"
git push origin main
```

### Ejecutar `finalizar_sesion.bat`

```cmd
E:\finalizar_sesion.bat
```

---

## CHECKLIST FINAL W20

### Técnico

```
FILTROS
[ ] reportes/filters.py: VentaReporteFilter con fecha/cliente/producto
[ ] DateFromToRangeFilter + RangeWidget para el campo fecha
[ ] ModelChoiceFilter con field_name='detalles__producto' + distinct=True

MODELO Y MIGRACIÓN
[ ] reportes/models.py: ExportacionReporte con JSONField filtros
[ ] reportes/migrations/0001_initial.py creada y aplicada
[ ] reportes/admin.py registrado

VISTA DE REPORTE
[ ] ReporteVentasView(LoginRequiredMixin, ListView)
[ ] get_queryset() aplica VentaReporteFilter
[ ] get_context_data() agrega filtro y total_filtrado

EXPORTS REUTILIZABLES
[ ] reportes/exports.py: generar_excel_ventas() y generar_pdf_ventas()
[ ] Misma función usada por la vista síncrona y la tarea async
[ ] reportes/templates/reportes/reporte_ventas_pdf.html (A4 landscape)

EXPORTACIÓN ADAPTATIVA
[ ] UMBRAL_ASYNC = 1000 como constante en views.py
[ ] total <= UMBRAL_ASYNC → descarga inmediata (mismo patrón de W12)
[ ] total > UMBRAL_ASYNC → crea ExportacionReporte + .delay() + redirect

TAREA ASÍNCRONA
[ ] reportes/tasks.py: generar_exportacion_async(@shared_task)
[ ] Reconstruye el filtro desde exportacion.filtros (JSONField)
[ ] ContentFile(buffer.read()) para guardar en FileField
[ ] archivo.save(nombre, ContentFile(...), save=False) + save(update_fields=[...])
[ ] _enviar_correo_exportacion_lista() con link de descarga
[ ] SITE_DOMAIN en settings.py (las tareas no tienen request)

TEMPLATES
[ ] reporte_ventas.html: filtros + botones exportar + tabla + paginación
[ ] Botones de exportación preservan request.GET.urlencode
[ ] exportacion_en_proceso.html: 3 estados (pendiente/completado/error)
[ ] Enlace al reporte desde dashboard.html

TESTS
[ ] test tests.test_w20_reportes → 8/8 OK
[ ] test tests → 187/187 OK acumulados
[ ] @override_settings(MEDIA_ROOT=tempfile.mkdtemp()) en tests con archivos
[ ] @patch('reportes.views.UMBRAL_ASYNC', 0) para forzar ruta async
[ ] test filtro por cliente y por producto
[ ] test exportación síncrona: Content-Type correcto
[ ] test exportación asíncrona: ExportacionReporte creado + correo enviado

GIT
[ ] sprint6_planning.md actualizado
[ ] Commit con mensaje descriptivo
[ ] git push → GitHub con reportes/exports.py y tasks.py
[ ] finalizar_sesion.bat → archivos en USB
```

---

## DIAGRAMA: Decisión de ruta de exportación (W20)

```
GET /reportes/exportar/?formato=excel&cliente=5
    │
    ▼
exportar_reporte(request)
    │
    ├─ VentaReporteFilter(request.GET, queryset).qs.distinct()
    ├─ total = queryset.count()
    │
    ├──────────────── ¿total > UMBRAL_ASYNC (1000)? ────────────────┐
    │                                                                │
   NO                                                               SÍ
    │                                                                │
    ▼                                                                ▼
generar_excel_ventas(queryset)               ExportacionReporte.objects.create(
    │                                            usuario=request.user,
    ├─ Workbook en memoria                       formato='excel',
    └─ buffer.read()                             filtros=request.GET.dict()
    │                                        )
    ▼                                            │
HttpResponse(buffer,                             ├─ generar_exportacion_async
    content_type=spreadsheetml)                  │       .delay(exportacion.pk)
    │                                            │
    ▼                                            ▼
Descarga inmediata en el navegador        redirect a
(~1-3 segundos)                           exportacion_en_proceso/<id>/
                                                  │
                                                  ▼
                                        Celery Worker (background):
                                            reconstruye filtro
                                            genera archivo
                                            guarda en FileField
                                            envía correo con link
                                                  │
                                                  ▼
                                        Usuario revisa su correo
                                        minutos después → descarga
```

---

## HILO CONDUCTOR → W21

**¿Qué entrega W20?**
Reportes filtrables por fecha, cliente y producto, con exportación
que se adapta automáticamente al volumen de datos: inmediata para
reportes pequeños, asíncrona con notificación por correo para
reportes grandes. 187 tests verifican ambas rutas.

**¿Qué abre W21 / Hito M7?**
La última pieza de la Espiral 7 es el **histórico de cambios de
precio** con `django-simple-history`, que permite auditar cuándo
y cómo cambió el precio de cada producto. W21 también cierra el
Sprint 6 con el Review, la Retrospectiva y la declaración del Hito M7.

**¿Qué necesita W21 de W20?**

| Artefacto de W20 | Uso en W21 |
|---|---|
| `VentaReporteFilter` como patrón | W21 crea un filtro similar para el histórico de precios |
| `reportes/exports.py` | W21 puede reutilizar `generar_excel_ventas` como referencia para exportar histórico |
| `ExportacionReporte` model | Patrón de referencia si W21 necesita exportar el histórico de forma asíncrona |
| 187 tests pasando | W21 los amplía y cierra con el Sprint 6 Review |

**Tarea de investigación para W21:**
> Lee la documentación de `django-simple-history`:
> `https://django-simple-history.readthedocs.io/en/latest/quick_start.html`
>
> ¿Qué hace el decorador `@register(Producto)` o heredar de
> `HistoricalRecords`? ¿Qué tabla nueva crea en la base de datos
> y qué columnas adicionales tiene respecto a `Producto`?

**Pregunta de reflexión:**
> "Elegimos 1000 filas como umbral para decidir entre exportación
> síncrona y asíncrona. ¿Qué pasaría si el umbral fuera demasiado
> bajo (por ejemplo, 10)? ¿Y si fuera demasiado alto (100,000)?
> ¿Cómo determinarías el umbral correcto para un servidor real
> con recursos limitados como el plan gratuito de Render?"

---

## Referencia rápida de comandos W20

```cmd
:: SESIÓN
E:\iniciar_sesion.bat
E:\finalizar_sesion.bat

:: DJANGO
python manage.py check
python manage.py makemigrations reportes --name exportacion_reporte_inicial
python manage.py migrate
python manage.py runserver

:: CELERY WORKER (terminal 2 — necesario para exportaciones reales async)
celery -A core worker -l info -Q erp_django

:: TESTS
python manage.py test tests.test_w20_reportes --verbosity=2
python manage.py test tests --verbosity=0   (187 tests)

:: GIT
git add .
git commit -m "Sprint 6 W20: reportes filtrables + exportacion adaptativa + 187 tests OK"
git push origin main
git log --oneline
```

---

*Guía de Laboratorio W20 · ERP Django*
*Espiral 7 · Sprint 6 Desarrollo · Reportes Filtrables + Exportación Adaptativa*
*SEP 3061300006-23 · UTEC Celaya · MC. Román Fernando López González*

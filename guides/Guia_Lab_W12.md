# Guía de Laboratorio — W12
## ERP Django · Espiral 4 · Semana 12 de 24
### Técnico en Programación (SEP 3061300006-23) · UTEC Celaya
### Asesor: MC. Román Fernando López González

---

| Campo | Detalle |
|---|---|
| **Semana** | W12 de 24 |
| **Espiral** | E4 — API REST y Media |
| **Sprint Scrum** | Sprint 3 — Review + Retrospectiva |
| **Hito** | **★ M4: DRF completo + PDF descargable + imágenes + Excel funcionales** |
| **Horario** | 16:45 – 19:45 (180 min) |
| **Nivel Schmelkes** | 3 — Infraestructura |
| **Hilo conductor** | "W11 dio ojos al ERP. W12 le da voz: documentos descargables para el mundo real." |

---

## Respuesta a la tarea de investigación de W11

> **¿Cómo genera PDF WeasyPrint desde un template Django?**
>
> ```python
> from django.template.loader import render_to_string
> import weasyprint   # producción Linux / Render.com
>
> html = render_to_string('ventas/factura_pdf.html', context, request=request)
> pdf  = weasyprint.HTML(string=html).write_pdf()
> response = HttpResponse(pdf, content_type='application/pdf')
> ```
>
> **¿Diferencia entre `render_to_string()` y `render()`?**
>
> | Función | Devuelve | Uso típico |
> |---|---|---|
> | `render(request, template, context)` | `HttpResponse` con HTML | Vistas normales que devuelven HTML al navegador |
> | `render_to_string(template, context)` | `str` con el HTML | Cuando necesitas el HTML como texto para procesarlo (PDF, email, etc.) |
>
> Para generar un PDF: primero `render_to_string()` → obtienes el HTML
> como cadena → se lo pasas al motor de PDF (xhtml2pdf o WeasyPrint) →
> el motor lo convierte a bytes → los bytes van en la `HttpResponse`.
>
> **¿Por qué xhtml2pdf en lugar de WeasyPrint en el aula?**
> WeasyPrint requiere `GTK3`, `Cairo` y `Pango` — librerías de sistema
> que no pueden instalarse en un entorno USB sin permisos de administrador.
> `xhtml2pdf` es puro Python (sin dependencias de sistema), ideal para
> el entorno portable del aula. En producción con Render.com (Ubuntu),
> WeasyPrint funciona perfectamente y produce PDFs de mayor calidad.

---

## Objetivos de la sesión

Al terminar W12, el estudiante será capaz de:

1. Instalar `xhtml2pdf` y `openpyxl` en el entorno portable
2. Crear un template HTML optimizado para conversión a PDF
3. Implementar `VentaPDFView` que genera y descarga facturas en PDF
4. Implementar `ExportarProductosExcelView` que descarga inventario en Excel
5. Agregar botones de descarga en los templates existentes
6. Ejecutar el Sprint 3 Review con demo de todos los entregables de M4
7. Completar la ficha Schmelkes E4 y declarar el Hito M4

---

## Stack tecnológico de W12

| Herramienta | Novedad en W12 | Descripción |
|---|---|---|
| `xhtml2pdf` | ✅ Nuevo | Convierte HTML a PDF — puro Python, sin dependencias de sistema |
| `openpyxl` | ✅ Nuevo | Crea y manipula archivos Excel `.xlsx` |
| `render_to_string` | ✅ Nuevo | Renderiza un template Django como cadena de texto |
| `WeasyPrint` | Mención | Alternativa de mayor calidad para Linux/producción |
| `ConfiguracionERP` | ya existe | Datos de la empresa que aparecen en la factura |

---

## Mapa de tiempo (180 min)

| Parte | Actividad | Tiempo |
|---|---|---|
| Arranque | Daily Scrum + verificar W11 | 10 min |
| Parte 1 | Instalar `xhtml2pdf` + `openpyxl` | 10 min |
| Parte 2 | Template `factura_pdf.html` (HTML para PDF) | 25 min |
| Parte 3 | `VentaPDFView` + URL + botón en detalle | 20 min |
| Parte 4 | `ExportarProductosExcelView` + URL + botón en lista | 20 min |
| Parte 5 | Tests W12 (8 pruebas) | 20 min |
| **Commit parcial** | Punto de control seguro | 5 min |
| Parte 6 | Sprint 3 Review ante el asesor | 20 min |
| Parte 7 | Sprint 3 Retrospectiva + Ficha Schmelkes E4 | 20 min |
| Cierre | Commit final [M4] · `finalizar_sesion.bat` · hilo → W13 | 10 min |
| Buffer | | 20 min |
| **Total** | | **180 min** |

---

## ARRANQUE — Daily Scrum (10 min)

```cmd
E:\iniciar_sesion.bat
```

### Daily Scrum

```
1. ¿Qué hice en W11?
   → Agregué ImageField al modelo Producto, creé el validador
     MIME con filetype y configuré django-storages para S3.

2. ¿Qué haré en W12?
   → Implementaré generación de facturas PDF con xhtml2pdf,
     exportación de inventario a Excel, y cerraré el Sprint 3
     con el Review y la declaración de M4.

3. ¿Tengo algún impedimento?
   → (registrar aquí)
```

### Verificar estado

```cmd
python manage.py check
python manage.py test tests --verbosity=0
```

**Resultado esperado:** `System check identified no issues` · `Ran 115 tests … OK`

---

## PARTE 1 — Instalar dependencias (10 min)

### 1.1 Instalar `xhtml2pdf` y `openpyxl`

```cmd
pip install "xhtml2pdf==0.2.15" "openpyxl==3.1.2"
pip freeze > requirements.txt
```

Verificar instalación:

```cmd
python -c "import xhtml2pdf; print('xhtml2pdf OK')"
python -c "import openpyxl; print('openpyxl', openpyxl.__version__)"
```

**Resultado esperado:**
```
xhtml2pdf OK
openpyxl 3.1.2
```

> **Nota sobre WeasyPrint en producción:**
> En `core/settings_prod.py` (Linux/Render.com) puedes cambiar el backend
> de PDF a WeasyPrint sin modificar la lógica de la vista:
>
> ```python
> # requirements-prod.txt (solo para Render.com)
> weasyprint==60.x
> ```
>
> La vista `VentaPDFView` detecta el entorno y usa el motor disponible.
> En el aula usamos xhtml2pdf; en Render.com se puede usar WeasyPrint.

---

## PARTE 2 — Template `factura_pdf.html` (25 min)

### 2.1 ¿Por qué el template PDF es diferente a los otros?

Los templates normales extienden `base.html` y cargan Bootstrap desde CDN.
Un template PDF debe:
- **No extender `base.html`** — la navbar y el toggle JS no tienen sentido en PDF
- **CSS inline o en `<style>`** — los renderizadores PDF no pueden acceder a CDNs
- **Solo fuentes del sistema** — no Google Fonts (sin acceso a internet en el render)
- **Layout en tablas HTML** — más predecible que CSS Grid/Flexbox en renderizadores

---

### 2.2 Crear carpeta y template

```cmd
:: Los templates de PDF van en la misma carpeta de la app
:: (ya existe ventas/templates/ventas/)
```

Crear `ventas/templates/ventas/factura_pdf.html`:

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Factura #{{ venta.pk }} — {{ config.nombre_empresa }}</title>
    <style>
        /* CSS inline — sin CDN — compatible con xhtml2pdf y WeasyPrint */
        @page {
            size: A4 portrait;
            margin: 2cm;
        }
        body {
            font-family: Arial, Helvetica, sans-serif;
            font-size: 11pt;
            color: #1A1A2E;
            margin: 0; padding: 0;
        }

        /* ── ENCABEZADO ─────────────────────────────────────────── */
        .header {
            background: #0A2342;
            color: #FFFFFF;
            padding: 16px 20px;
            border-bottom: 4px solid #B8860B;
            margin-bottom: 20px;
        }
        .header-title {
            font-size: 20pt;
            font-weight: bold;
            color: #D4AF37;
            margin: 0;
        }
        .header-empresa {
            font-size: 10pt;
            color: rgba(255,255,255,.8);
            margin: 2px 0 0;
        }
        .header-folio {
            font-size: 13pt;
            font-weight: bold;
            color: #D4AF37;
            text-align: right;
        }

        /* ── SECCIÓN DE DATOS ───────────────────────────────────── */
        .datos-tabla {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 16px;
        }
        .datos-tabla td {
            padding: 5px 8px;
            font-size: 10pt;
            border: 1px solid #C8D8EC;
        }
        .datos-tabla .label {
            background: #E8F0FB;
            font-weight: bold;
            width: 30%;
            color: #0A2342;
        }

        /* ── TABLA DE PRODUCTOS ─────────────────────────────────── */
        .tabla-productos {
            width: 100%;
            border-collapse: collapse;
            margin-top: 16px;
        }
        .tabla-productos thead th {
            background: #0A2342;
            color: #FFFFFF;
            padding: 8px 10px;
            font-size: 9pt;
            text-align: left;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 3px solid #B8860B;
        }
        .tabla-productos thead th.num {
            text-align: right;
        }
        .tabla-productos tbody td {
            padding: 7px 10px;
            font-size: 10pt;
            border-bottom: 1px solid #E8F0FB;
        }
        .tabla-productos tbody td.num {
            text-align: right;
        }
        .tabla-productos tbody tr:nth-child(even) td {
            background: #F5F7FA;
        }

        /* ── TOTAL ──────────────────────────────────────────────── */
        .total-row {
            background: #FDF8E8;
            border-top: 2px solid #B8860B;
        }
        .total-label {
            padding: 10px;
            font-weight: bold;
            font-size: 11pt;
            text-align: right;
            color: #0A2342;
        }
        .total-valor {
            padding: 10px;
            font-weight: bold;
            font-size: 13pt;
            text-align: right;
            color: #B8860B;
        }

        /* ── PIE ────────────────────────────────────────────────── */
        .footer {
            margin-top: 32px;
            border-top: 1px solid #C8D8EC;
            padding-top: 10px;
            font-size: 8pt;
            color: #5A6A7E;
            text-align: center;
        }
    </style>
</head>
<body>

<!-- ENCABEZADO -->
<div class="header">
    <table width="100%">
        <tr>
            <td>
                <p class="header-title">FACTURA</p>
                <p class="header-empresa">{{ config.nombre_empresa }}</p>
                {% if config.rfc %}
                <p class="header-empresa">RFC: {{ config.rfc }}</p>
                {% endif %}
            </td>
            <td style="text-align:right;vertical-align:top;">
                <p class="header-folio"># {{ venta.pk|stringformat:"05d" }}</p>
                <p style="color:rgba(255,255,255,.7);font-size:9pt;margin:0;">
                    {{ venta.fecha|date:"d/m/Y" }}
                </p>
            </td>
        </tr>
    </table>
</div>

<!-- DATOS DEL CLIENTE -->
<table class="datos-tabla">
    <tr>
        <td class="label">Cliente</td>
        <td>{{ venta.cliente.nombre }}</td>
        <td class="label">Correo</td>
        <td>{{ venta.cliente.correo }}</td>
    </tr>
    <tr>
        <td class="label">Fecha de emisión</td>
        <td>{{ venta.fecha|date:"d/m/Y H:i" }}</td>
        <td class="label">Moneda</td>
        <td>{{ config.moneda }}</td>
    </tr>
</table>

<!-- TABLA DE PRODUCTOS -->
<table class="tabla-productos">
    <thead>
        <tr>
            <th style="width:5%;">#</th>
            <th style="width:40%;">Producto</th>
            <th class="num" style="width:15%;">Precio unit.</th>
            <th class="num" style="width:10%;">Cant.</th>
            <th class="num" style="width:15%;">Subtotal</th>
        </tr>
    </thead>
    <tbody>
        {% for detalle in venta.detalles.all %}
        <tr>
            <td>{{ forloop.counter }}</td>
            <td>{{ detalle.producto.nombre }}</td>
            <td class="num">${{ detalle.precio_unitario }}</td>
            <td class="num">{{ detalle.cantidad }}</td>
            <td class="num">${{ detalle.subtotal }}</td>
        </tr>
        {% empty %}
        <tr>
            <td colspan="5" style="text-align:center;
                color:#5A6A7E;padding:16px;">
                Sin líneas de detalle.
            </td>
        </tr>
        {% endfor %}
    </tbody>
    <tfoot>
        {% with subtotal=venta.total iva_pct=config.iva_porcentaje %}
        {% if iva_pct %}
        <tr class="total-row">
            <td colspan="4" class="total-label">Subtotal (sin IVA):</td>
            <td class="total-valor">
                ${{ subtotal }}
            </td>
        </tr>
        <tr class="total-row">
            <td colspan="4" class="total-label">
                IVA ({{ iva_pct }}%):
            </td>
            <td class="total-valor" style="font-size:11pt;">
                ${% widthratio subtotal 100 iva_pct %}
            </td>
        </tr>
        {% endif %}
        <tr class="total-row">
            <td colspan="4" class="total-label"
                style="font-size:12pt;">TOTAL:</td>
            <td class="total-valor" style="font-size:15pt;">
                ${{ subtotal }}
            </td>
        </tr>
        {% endwith %}
    </tfoot>
</table>

<!-- PIE DE PÁGINA -->
<div class="footer">
    <p>
        {{ config.nombre_empresa }}
        {% if config.rfc %}· RFC: {{ config.rfc }}{% endif %}
        · {{ config.moneda }}
    </p>
    <p>Documento generado el {{ hoy|date:"d/m/Y H:i" }} ·
       ERP Django UTEC Celaya</p>
</div>

</body>
</html>
```

---

## PARTE 3 — `VentaPDFView` + URL + Botón (20 min)

### 3.1 Agregar la vista PDF a `ventas/views.py`

Agregar al inicio del archivo los imports necesarios:

```python
# ventas/views.py — agregar imports:
import io
from datetime import date

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string

from configuracion.models import ConfiguracionERP
```

Agregar la vista al final de `ventas/views.py`:

```python
# ventas/views.py — agregar al final del archivo:

@login_required
def venta_pdf(request, venta_id: int) -> HttpResponse:
    """Genera y descarga la factura de una venta en formato PDF.

    Usa xhtml2pdf (entorno aula / Windows) como motor de conversión.
    En producción Linux puede reemplazarse por WeasyPrint para mejor calidad.

    Args:
        request:  HttpRequest de Django.
        venta_id: ID de la venta a generar.

    Returns:
        HttpResponse con Content-Type application/pdf
        y Content-Disposition attachment (descarga directa).

    Raises:
        Http404: si la venta no existe.
    """
    from xhtml2pdf import pisa   # import local para aislar la dependencia

    venta = get_object_or_404(
        Venta.objects
        .select_related('cliente')
        .prefetch_related('detalles__producto'),
        pk=venta_id
    )

    config = ConfiguracionERP.get_instance()

    contexto = {
        'venta':  venta,
        'config': config,
        'hoy':    date.today(),
    }

    html_string = render_to_string(
        'ventas/factura_pdf.html',
        contexto,
        request=request
    )

    buffer = io.BytesIO()
    resultado = pisa.CreatePDF(src=html_string, dest=buffer)

    if resultado.err:
        return HttpResponse(
            f'Error al generar el PDF: {resultado.err}',
            status=500
        )

    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="factura_{venta.pk:05d}.pdf"'
    )
    return response
```

---

### 3.2 Agregar URL en `ventas/urls.py`

```python
# ventas/urls.py — agregar la ruta del PDF:
from django.urls import path
from . import views

app_name = 'ventas'

urlpatterns = [
    path('',
         views.VentaListView.as_view(),
         name='lista'),
    path('<int:venta_id>/',
         views.VentaDetailView.as_view(),
         name='detalle'),
    path('nueva/',
         views.crear_venta,
         name='crear'),
    path('<int:venta_id>/eliminar/',
         views.VentaDeleteView.as_view(),
         name='eliminar'),
    path('<int:venta_id>/pdf/',       # ← nuevo W12
         views.venta_pdf,
         name='pdf'),
]
```

---

### 3.3 Agregar botón "Descargar PDF" en `ventas/templates/ventas/detalle.html`

Actualizar la sección `erp-page-title` del template:

```html
<!-- ventas/detalle.html — actualizar erp-page-title: -->
<div class="erp-page-title">
    <h2>💰 Venta #{{ venta.pk }}</h2>
    {% if user.is_authenticated %}
        <!-- Botón de descarga PDF — W12 -->
        <a href="{% url 'ventas:pdf' venta.pk %}"
           class="btn-erp-gold ms-auto"
           title="Descargar factura en PDF">
            📄 Descargar PDF
        </a>
        <a href="{% url 'ventas:eliminar' venta.pk %}"
           class="btn-erp-danger">Eliminar venta</a>
    {% endif %}
</div>
```

---

### 3.4 Verificar la generación de PDF

```cmd
python manage.py runserver
```

```
[ ] /ventas/ → listar ventas
[ ] /ventas/1/ → detalle de venta con botón "Descargar PDF"
[ ] Clic en "Descargar PDF" → descarga factura_00001.pdf
[ ] Abrir el PDF → tabla de productos con total visible
[ ] /ventas/1/pdf/ sin login → redirige a /accounts/login/
```

---

## PARTE 4 — `ExportarProductosExcelView` + URL + Botón (20 min)

### 4.1 Agregar la vista Excel a `productos/views.py`

Agregar imports al inicio:

```python
# productos/views.py — agregar imports:
import io
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
```

Agregar la vista al final de `productos/views.py`:

```python
# productos/views.py — agregar al final:

@login_required
def exportar_productos_excel(request) -> HttpResponse:
    """Exporta el inventario completo de productos a un archivo Excel.

    Genera un archivo .xlsx con:
        - Fila de encabezados con estilo Fable 5 (azul/dorado)
        - Una fila por producto activo
        - Columnas: ID, Nombre, Categoría, Proveedor, Precio, Stock, Estado

    Returns:
        HttpResponse con Content-Type xlsx y descarga directa.
    """
    # ── 1. Crear workbook y configurar hoja ───────────────────────
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Inventario de Productos'

    # ── 2. Estilos Fable 5 AzulERP ────────────────────────────────
    color_navy  = '0A2342'
    color_gold  = 'B8860B'
    color_ice   = 'E8F0FB'

    encabezado_font  = Font(bold=True, color='FFFFFF', size=11)
    encabezado_fill  = PatternFill('solid', fgColor=color_navy)
    encabezado_align = Alignment(horizontal='center', vertical='center')

    fila_par_fill    = PatternFill('solid', fgColor=color_ice)
    total_font       = Font(bold=True, color=color_gold, size=11)

    # ── 3. Encabezados ────────────────────────────────────────────
    columnas = [
        ('ID',         8),
        ('Nombre',     35),
        ('Categoría',  20),
        ('Proveedor',  25),
        ('Precio ($)', 14),
        ('Stock',      10),
        ('Estado',     10),
    ]

    for col_idx, (titulo, ancho) in enumerate(columnas, start=1):
        celda = ws.cell(row=1, column=col_idx, value=titulo)
        celda.font      = encabezado_font
        celda.fill      = encabezado_fill
        celda.alignment = encabezado_align
        ws.column_dimensions[
            openpyxl.utils.get_column_letter(col_idx)
        ].width = ancho

    ws.row_dimensions[1].height = 22

    # ── 4. Datos de productos ──────────────────────────────────────
    productos = (
        Producto.objects
        .select_related('categoria', 'proveedor')
        .filter(activo=True)
        .order_by('nombre')
    )

    for fila_idx, prod in enumerate(productos, start=2):
        datos_fila = [
            prod.pk,
            prod.nombre,
            prod.categoria.nombre,
            prod.proveedor.nombre if prod.proveedor else '—',
            float(prod.precio),
            prod.stock,
            'Activo' if prod.activo else 'Inactivo',
        ]
        for col_idx, valor in enumerate(datos_fila, start=1):
            celda = ws.cell(row=fila_idx, column=col_idx, value=valor)
            if fila_idx % 2 == 0:
                celda.fill = fila_par_fill
            # Alinear precios y stock a la derecha
            if col_idx in (5, 6):
                celda.alignment = Alignment(horizontal='right')

    # ── 5. Fila de totales ────────────────────────────────────────
    fila_total = len(list(productos)) + 2
    ws.cell(row=fila_total, column=1,
            value=f'Total: {len(list(productos))} productos'
            ).font = total_font

    # ── 6. Guardar en buffer y devolver respuesta ─────────────────
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.read(),
        content_type=(
            'application/vnd.openxmlformats-officedocument'
            '.spreadsheetml.sheet'
        )
    )
    response['Content-Disposition'] = (
        'attachment; filename="inventario_productos.xlsx"'
    )
    return response
```

---

### 4.2 Agregar URL en `productos/urls.py`

```python
# productos/urls.py — agregar la ruta de exportación Excel:
from django.urls import path
from . import views

app_name = 'productos'

urlpatterns = [
    # Lectura
    path('',
         views.ProductoListView.as_view(),
         name='lista'),
    path('<int:producto_id>/',
         views.ProductoDetailView.as_view(),
         name='detalle'),
    # Escritura
    path('nuevo/',
         views.ProductoCreateView.as_view(),
         name='crear'),
    path('<int:producto_id>/editar/',
         views.ProductoUpdateView.as_view(),
         name='editar'),
    path('<int:producto_id>/eliminar/',
         views.ProductoDeleteView.as_view(),
         name='eliminar'),
    # Exportación — W12
    path('exportar-excel/',
         views.exportar_productos_excel,
         name='exportar_excel'),
]
```

---

### 4.3 Agregar botón "Exportar Excel" en `productos/templates/productos/lista.html`

Actualizar la sección `erp-page-title`:

```html
<!-- productos/lista.html — actualizar erp-page-title: -->
<div class="erp-page-title">
    <h2>📦 Productos</h2>
    <span style="margin-left:auto;color:var(--clr-muted);font-size:.85rem;">
        {{ page_obj.paginator.count }} producto(s)
    </span>
    {% if user.is_authenticated %}
        <!-- Exportar Excel — W12 -->
        <a href="{% url 'productos:exportar_excel' %}"
           class="btn-erp-primary"
           title="Descargar inventario como Excel">
            📊 Exportar Excel
        </a>
        <a href="{% url 'productos:crear' %}" class="btn-erp-gold">
            + Nuevo producto
        </a>
    {% endif %}
</div>
```

### 4.4 Verificar la exportación Excel

```
[ ] /productos/ con login → botón "Exportar Excel" visible
[ ] Clic en "Exportar Excel" → descarga inventario_productos.xlsx
[ ] Abrir en Excel/LibreOffice → fila de encabezados azul marino
[ ] Filas pares en azul claro → estilo Fable 5 AzulERP
[ ] Columna "Precio" alineada a la derecha
[ ] /productos/exportar-excel/ sin login → redirige a /accounts/login/
```

---

## PARTE 5 — Tests W12 (20 min)

### 5.1 Crear `tests/test_w12_documentos.py`

```python
"""Suite de pruebas W12 — Generación de PDF y exportación Excel.

Verifica: autenticación requerida, Content-Type correcto,
          Content-Disposition, 404 para venta inexistente.

Ejecutar con:
    python manage.py test tests.test_w12_documentos --verbosity=2

Resultado esperado:
    Ran 8 tests in X.XXXs
    OK
"""
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from clientes.models    import Cliente
from configuracion.models import ConfiguracionERP
from productos.models   import Categoria, Producto
from ventas.models      import DetalleVenta, Venta


class VentaPDFTest(TestCase):
    """Tests de la vista venta_pdf."""

    def setUp(self):
        # Crear ConfiguracionERP para que el template tenga datos
        ConfiguracionERP.get_instance()

        self.user = User.objects.create_user('pdfuser', password='pass')
        cat       = Categoria.objects.create(nombre='Cat PDF')
        prod      = Producto.objects.create(
            nombre='Producto PDF', precio=Decimal('500.00'),
            stock=5, categoria=cat
        )
        cli       = Cliente.objects.create(
            nombre='Cliente PDF', correo='pdf@test.com'
        )
        self.venta = Venta.objects.create(cliente=cli)
        DetalleVenta.objects.create(
            venta=self.venta, producto=prod,
            cantidad=2, precio_unitario=Decimal('500.00')
        )

    def test_pdf_sin_auth_redirige_a_login(self):
        """GET /ventas/<id>/pdf/ sin login → 302 a /accounts/login/."""
        r = self.client.get(
            reverse('ventas:pdf', args=[self.venta.pk])
        )
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r['Location'])

    def test_pdf_con_auth_devuelve_200(self):
        """GET /ventas/<id>/pdf/ con login → 200 con Content-Type PDF."""
        self.client.force_login(self.user)
        r = self.client.get(
            reverse('ventas:pdf', args=[self.venta.pk])
        )
        self.assertEqual(r.status_code, 200)

    def test_pdf_content_type_es_pdf(self):
        """La respuesta debe tener Content-Type application/pdf."""
        self.client.force_login(self.user)
        r = self.client.get(
            reverse('ventas:pdf', args=[self.venta.pk])
        )
        self.assertIn('application/pdf', r.get('Content-Type', ''))

    def test_pdf_content_disposition_es_attachment(self):
        """La respuesta debe ser una descarga (attachment)."""
        self.client.force_login(self.user)
        r = self.client.get(
            reverse('ventas:pdf', args=[self.venta.pk])
        )
        disposition = r.get('Content-Disposition', '')
        self.assertIn('attachment', disposition)
        self.assertIn('.pdf', disposition)

    def test_pdf_venta_inexistente_devuelve_404(self):
        """GET /ventas/9999/pdf/ → 404 Not Found."""
        self.client.force_login(self.user)
        r = self.client.get(
            reverse('ventas:pdf', args=[9999])
        )
        self.assertEqual(r.status_code, 404)


class ExportarExcelTest(TestCase):
    """Tests de la vista exportar_productos_excel."""

    def setUp(self):
        self.user = User.objects.create_user('xlsuser', password='pass')
        cat       = Categoria.objects.create(nombre='Cat Excel')
        self.prod = Producto.objects.create(
            nombre='Producto Excel', precio=Decimal('250.00'),
            stock=10, categoria=cat
        )

    def test_excel_sin_auth_redirige(self):
        """GET /productos/exportar-excel/ sin login → 302."""
        r = self.client.get(reverse('productos:exportar_excel'))
        self.assertEqual(r.status_code, 302)

    def test_excel_con_auth_devuelve_200(self):
        """GET /productos/exportar-excel/ con login → 200."""
        self.client.force_login(self.user)
        r = self.client.get(reverse('productos:exportar_excel'))
        self.assertEqual(r.status_code, 200)

    def test_excel_content_type_es_xlsx(self):
        """La respuesta debe tener el Content-Type de Excel."""
        self.client.force_login(self.user)
        r = self.client.get(reverse('productos:exportar_excel'))
        ct = r.get('Content-Type', '')
        self.assertIn('spreadsheetml', ct)

    def test_excel_content_disposition_es_attachment(self):
        """La respuesta debe ser una descarga con extensión .xlsx."""
        self.client.force_login(self.user)
        r = self.client.get(reverse('productos:exportar_excel'))
        disposition = r.get('Content-Disposition', '')
        self.assertIn('attachment', disposition)
        self.assertIn('.xlsx', disposition)
```

### 5.2 Ejecutar los tests

```cmd
python manage.py test tests.test_w12_documentos --verbosity=2
```

**Resultado esperado:**
```
test_excel_con_auth_devuelve_200 ... ok
test_excel_content_disposition_es_attachment ... ok
test_excel_content_type_es_xlsx ... ok
test_excel_sin_auth_redirige ... ok
test_pdf_con_auth_devuelve_200 ... ok
test_pdf_content_disposition_es_attachment ... ok
test_pdf_content_type_es_pdf ... ok
test_pdf_sin_auth_redirige_a_login ... ok
test_pdf_venta_inexistente_devuelve_404 ... ok

Ran 8 tests in X.XXXs
OK
```

### 5.3 Suite acumulada — Hito M4

```cmd
python manage.py test tests --verbosity=0
```

**Resultado esperado:** `Ran 123 tests in X.XXXs · OK` (115 + 8)

---

### COMMIT PARCIAL

```cmd
git add .
git commit -m "Sprint 3 W12: PDF xhtml2pdf + Excel openpyxl + 123 tests OK [pre-M4]"
```

---

## PARTE 6 — Sprint 3 Review ante el asesor (20 min)

### Guión de demo (≤ 10 min en vivo)

```
1. Demostrar la API REST:
   → Abrir /api/productos/ → JSON paginado con imagen_url
   → Obtener token: POST /api/auth/token/
   → Crear producto con token → 201 Created

2. Demostrar imagen de producto:
   → /productos/nuevo/ → subir imagen .jpg válida → guardar
   → /productos/<id>/ → imagen visible en el template
   → /api/productos/<id>/ → campo imagen_url con URL absoluta

3. Demostrar descarga de PDF:
   → /ventas/1/ → clic en "Descargar PDF"
   → PDF se descarga con nombre "factura_00001.pdf"
   → Abrir el PDF → tabla con líneas, total y datos de empresa

4. Demostrar exportación a Excel:
   → /productos/ → clic en "Exportar Excel"
   → Archivo .xlsx descargado
   → Abrir en Excel → encabezados azul marino, filas con datos

5. Mostrar los tests:
   → python manage.py test tests --verbosity=0
   → Ran 123 tests … OK

6. Declarar Sprint Goal verificado:
   "Al finalizar el Sprint 3, el ERP expone una API REST completa,
    gestiona imágenes de productos y genera documentos descargables."
   → Estado: ✅ COMPLETADO
```

### Tabla de verificación del Sprint Goal

| Criterio | Estado |
|---|---|
| GET /api/productos/ → JSON sin auth | ✅ |
| POST /api/productos/ con token → 201 | ✅ |
| Imagen de producto visible en detalle y en API | ✅ |
| GET /ventas/<id>/pdf/ → PDF descargable | ✅ |
| GET /productos/exportar-excel/ → .xlsx descargable | ✅ |
| django-storages configurado para prod | ✅ |
| 123 tests acumulados OK | ✅ |

---

## PARTE 7 — Sprint 3 Retrospectiva + Ficha Schmelkes E4 (20 min)

### 7.1 Crear `sprint3_retrospective.md`

```markdown
# Sprint 3 Retrospective — ERP Django
## Semanas W10–W12 · Espiral 4: API REST y Media

**Fecha:** ___/___/_____

## ¿Qué funcionó bien? (Keep)
1. SerializerMethodField para imagen_url devolvió URLs absolutas
   sin necesidad de configuración adicional.
2. xhtml2pdf funcionó sin dependencias de sistema en el entorno USB.
3. openpyxl con estilos Fable 5 produjo un Excel profesional en pocas líneas.

## ¿Qué mejorar? (Improve)
1. El template de PDF necesita más pruebas con ventas de muchos productos
   (paginación de página PDF).
2. Documentar mejor las diferencias xhtml2pdf vs WeasyPrint.

## Acción de mejora (Kaizen) para Sprint 4
> "En el Sprint 4 (E-commerce), diseñaré el flujo del carrito
>  en papel antes de escribir código, igual que el ER en W04."

## Velocidad del Sprint 3

| HU | Pts plan. | Pts ent. |
|---|---|---|
| HU-E4-01 Listar productos via API | 2 | 2 |
| HU-E4-02 Crear via API con token | 3 | 3 |
| HU-E4-03 API clientes, proveedores, ventas | 3 | 3 |
| HU-E4-04 Subir imagen de producto | 3 | 3 |
| HU-E4-05 Imagen en API | 2 | 2 |
| HU-E4-06 Factura en PDF | 5 | 5 |
| HU-E4-07 Exportar inventario a Excel | 3 | 3 |
| **Total** | **21** | **21** |

**Velocidad Sprint 3:** 21 puntos
**Velocidad acumulada (S0+S1+S2+S3):** 79 puntos
```

---

### 7.2 Completar `fichas/espiral_04_api_media.md`

```markdown
# Ficha de Sistematización — Espiral 4
## ERP Django · Espiral E4: API REST y Media

| Campo | Contenido |
|---|---|
| **Número de espiral** | 4 |
| **Nombre del ciclo** | API REST y Media |
| **Semanas** | W10 – W12 |
| **Fecha de inicio** | ___/___/_____ |
| **Fecha de cierre** | ___/___/_____ |
| **Responsable** | [Nombre del estudiante] |
| **Asesor** | MC. Román Fernando López González |

## 1. Objetivo del ciclo
Exponer los datos del ERP como API REST con DRF y autenticación
por token; agregar gestión de imágenes de productos con validación
MIME; generar documentos descargables (PDF, Excel).

## 2. Tareas realizadas

| # | Tarea | Estado | Semana |
|---|---|---|---|
| 1 | Serializers × 5 entidades | ✅ | W10 |
| 2 | ListCreateAPIView + RetrieveUpdateDestroyAPIView × 5 | ✅ | W10 |
| 3 | Token Auth + /api/auth/token/ | ✅ | W10 |
| 4 | ImageField + validador MIME (filetype) | ✅ | W11 |
| 5 | django-storages para prod S3 | ✅ | W11 |
| 6 | imagen_url en ProductoSerializer | ✅ | W11 |
| 7 | Template factura_pdf.html (HTML para PDF) | ✅ | W12 |
| 8 | VentaPDFView con xhtml2pdf | ✅ | W12 |
| 9 | ExportarProductosExcelView con openpyxl | ✅ | W12 |
| 10 | 8 tests de documentos | ✅ | W12 |

## 3. Evidencias
- URL API: https://erp-django-utec.onrender.com/api/productos/
- Token endpoint: /api/auth/token/
- PDF: GET /ventas/1/pdf/ → descarga factura_00001.pdf
- Excel: GET /productos/exportar-excel/ → inventario_productos.xlsx
- Tests: Ran 123 tests → OK

## 4. Criterios de aceptación

| Criterio | Estado |
|---|---|
| GET /api/productos/ sin token → 200 JSON | ✅ |
| POST /api/productos/ sin token → 403 | ✅ |
| Imagen subida → visible en /media/ y en imagen_url | ✅ |
| Archivo no-imagen → ValidationError | ✅ |
| GET /ventas/<id>/pdf/ → Content-Type: application/pdf | ✅ |
| GET /productos/exportar-excel/ → Content-Type: spreadsheetml | ✅ |
| 123 tests OK | ✅ |

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
| **Total Espiral 4** | |
```

---

## CIERRE — Commit Final [M4] y Respaldo (10 min)

### Actualizar `sprint3_planning.md`

```markdown
## Sprint 3 — Estado final W12

| HU | Estado | Pts |
|---|---|---|
| HU-E4-01 a HU-E4-07 | ✅ Completadas | 21/21 |

## Hito M4 — ALCANZADO ✅
- API DRF: /api/productos/, /api/clientes/, /api/ventas/ → 200 JSON
- Token: /api/auth/token/ → devuelve token
- Imagen: /productos/<id>/ → imagen visible + imagen_url en API
- PDF: /ventas/<id>/pdf/ → factura_00001.pdf descargable
- Excel: /productos/exportar-excel/ → inventario_productos.xlsx
- Tests: Ran 123 tests → OK
- Fecha: ___/___/_____
```

### Commit final de la Espiral 4

```cmd
git add .
git status

:: Verificar que incluye:
::   ventas/templates/ventas/factura_pdf.html
::   ventas/views.py (con venta_pdf)
::   ventas/urls.py (con ruta pdf)
::   ventas/templates/ventas/detalle.html (botón PDF)
::   productos/views.py (con exportar_productos_excel)
::   productos/urls.py (con ruta exportar-excel)
::   productos/templates/productos/lista.html (botón Excel)
::   tests/test_w12_documentos.py
::   sprint3_retrospective.md
::   sprint3_planning.md (actualizado)
::   fichas/espiral_04_api_media.md

git commit -m "Sprint 3 CIERRE [M4]: PDF + Excel + 123 tests OK + Ficha E4"
git push origin main
```

### Ejecutar `finalizar_sesion.bat`

```cmd
E:\finalizar_sesion.bat
```

---

## CHECKLIST FINAL W12 — HITO M4

### Técnico

```
INSTALACIÓN
[ ] pip install xhtml2pdf openpyxl → sin errores
[ ] requirements.txt actualizado

GENERACIÓN PDF
[ ] ventas/templates/ventas/factura_pdf.html sin {% extends "base.html" %}
[ ] CSS inline en <style> (sin CDN)
[ ] VentaPDFView usa render_to_string → pisa.CreatePDF → HttpResponse
[ ] @login_required en venta_pdf
[ ] ConfiguracionERP.get_instance() en el contexto del PDF
[ ] Content-Type: application/pdf
[ ] Content-Disposition: attachment; filename="factura_00001.pdf"
[ ] /ventas/<id>/pdf/ → PDF descargable en navegador
[ ] /ventas/9999/pdf/ → 404

EXPORTACIÓN EXCEL
[ ] exportar_productos_excel usa openpyxl.Workbook()
[ ] @login_required en exportar_productos_excel
[ ] Encabezados con fondo azul marino (#0A2342) y texto blanco
[ ] Filas pares con fondo azul claro (#E8F0FB)
[ ] select_related en el queryset
[ ] Content-Type: spreadsheetml
[ ] Content-Disposition: attachment; filename="inventario_productos.xlsx"
[ ] /productos/exportar-excel/ → .xlsx descargable

TEMPLATES ACTUALIZADOS
[ ] ventas/detalle.html: botón "Descargar PDF" visible con login
[ ] productos/lista.html: botón "Exportar Excel" visible con login

TESTS
[ ] test tests.test_w12_documentos → 8/8 OK
[ ] test tests → 123/123 OK acumulados
[ ] test PDF sin auth → 302
[ ] test PDF content-type → application/pdf
[ ] test PDF 9999 → 404
[ ] test Excel sin auth → 302
[ ] test Excel content-type → spreadsheetml

SCRUM / SCHMELKES
[ ] sprint3_planning.md: 21/21 puntos entregados
[ ] sprint3_retrospective.md: 3 secciones + Kaizen + velocidad
[ ] fichas/espiral_04_api_media.md: todos los campos completados
[ ] Commit de cierre con etiqueta [M4]
[ ] git push → GitHub actualizado
[ ] finalizar_sesion.bat → archivos en USB
```

---

## DIAGRAMA: Flujo de generación de documentos (W12)

```
FACTURA PDF:
GET /ventas/1/pdf/
    │ @login_required ──── NO auth → 302 /accounts/login/
    │ SÍ auth → continuar
    ▼
venta_pdf(request, venta_id=1)
    │
    ├─ get_object_or_404(Venta, pk=1) ── no existe → 404
    ├─ ConfiguracionERP.get_instance()  ── obtiene o crea datos empresa
    │
    ├─ render_to_string('ventas/factura_pdf.html', contexto)
    │       → HTML string con tabla de productos y total
    │
    ├─ pisa.CreatePDF(src=html_string, dest=buffer)
    │       → convierte HTML a bytes PDF (xhtml2pdf)
    │
    └─ HttpResponse(buffer.read(), content_type='application/pdf')
       Content-Disposition: attachment; filename="factura_00001.pdf"
           │
           ▼
       Navegador → descarga factura_00001.pdf

EXPORTACIÓN EXCEL:
GET /productos/exportar-excel/
    │ @login_required ──── NO auth → 302
    ▼
exportar_productos_excel(request)
    │
    ├─ openpyxl.Workbook() → ws.append(encabezados) → estilos navy/gold
    ├─ Producto.objects.select_related(...).filter(activo=True)
    │       → ws.append([prod.pk, prod.nombre, ...]) por cada producto
    │
    ├─ wb.save(buffer) → buffer.seek(0)
    │
    └─ HttpResponse(buffer.read(), content_type='...spreadsheetml...')
       Content-Disposition: attachment; filename="inventario_productos.xlsx"
```

---

## HILO CONDUCTOR → W13

**¿Qué cierra W12 / Espiral 4?**
La capa de infraestructura avanzada: API REST con tokens, gestión de
imágenes validadas, generación de facturas PDF y exportación Excel.
Los 123 tests garantizan la estabilidad del sistema para las próximas
espirales de mayor complejidad.

**¿Qué abre W13 / Espiral 5 / Sprint 4?**
Con toda la infraestructura en su lugar, W13 inicia el módulo de
**e-commerce**: catálogo público filtrable y carrito de compras
usando sesiones Django.

**¿Qué necesita W13 de W12?**

| Artefacto de W12 | Uso en W13 |
|---|---|
| `ProductoSerializer` con `imagen_url` | El catálogo público muestra imágenes de productos |
| `ListView` de productos (W07) | W13 crea un `CatalogoView` público que lo extiende |
| `templates/base.html` con modo noche | El carrito y el catálogo heredan el mismo diseño |
| 123 tests pasando | W13 agrega tests del carrito (sesión, agregar, quitar) |

**Tarea de investigación para W13:**
> Lee la documentación de Django sobre sesiones:
> `https://docs.djangoproject.com/en/4.2/topics/http/sessions/`
>
> ¿Cómo se almacena información en la sesión de un usuario?
> ¿Cómo implementarías un carrito de compras usando `request.session`?
> ¿Cuál es la diferencia entre `SESSION_COOKIE_AGE` y la sesión de allauth?

**Pregunta de reflexión:**
> "La factura PDF muestra el total de la venta usando `venta.total`
> que es una `@property` calculada. Si una venta tuviera 500 líneas
> de detalle, ¿cuántas queries SQL ejecutaría esta `@property`?
> ¿Cómo lo optimizarías para el PDF?"

---

## Referencia rápida de comandos W12

```cmd
:: SESIÓN
E:\iniciar_sesion.bat
E:\finalizar_sesion.bat

:: DJANGO
python manage.py check
python manage.py runserver

:: TESTS
python manage.py test tests.test_w12_documentos --verbosity=2
python manage.py test tests --verbosity=0   (123 tests)

:: VERIFICAR PDF (con servidor activo)
:: → Navegar a /ventas/1/ → clic en "Descargar PDF"
:: → Abrir el .pdf descargado

:: VERIFICAR EXCEL
:: → Navegar a /productos/ → clic en "Exportar Excel"
:: → Abrir el .xlsx en LibreOffice o Excel

:: GIT
git add .
git commit -m "Sprint 3 CIERRE [M4]: descripción"
git push origin main
git log --oneline
```

---

*Guía de Laboratorio W12 · ERP Django*
*Espiral 4 Cierre · Sprint 3 Review + Retrospectiva · Hito M4*
*SEP 3061300006-23 · UTEC Celaya · MC. Román Fernando López González*

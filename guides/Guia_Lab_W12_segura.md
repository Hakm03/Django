# Guía de Laboratorio W12 — Versión Segura y Simplificada

*ERP Django · Espiral 4 · Semana 12 de 24 · Hito M4 · Técnico en Programación — UTEC Celaya*

**Tema:** documentos del ERP — exportar a Excel y facturas en PDF.

**Qué cambia respecto a la guía original:** menos palabras técnicas, un paso a la vez, y todo adaptado a **tu** proyecto (tu repositorio, tu Render, tus archivos). Todo el código de esta guía fue probado antes de escribirla: con él, tu proyecto pasa **136 tests**.

---

## 1. ¿Qué vamos a lograr?

| # | Qué haremos | Para qué sirve | Dónde lo verás |
| --- | --- | --- | --- |
| 1 | Exportar el inventario a **Excel** | Descargar todos tus productos en una hoja de cálculo | Botón "Exportar Excel" en `/productos/` |
| 2 | Factura en **PDF** | Descargar la factura de una venta, lista para imprimir | Botón "Descargar PDF" en el detalle de una venta |
| 3 | Preparar **Docker** y **Render** | El PDF necesita programas de Linux; Docker los empaqueta para que funcionen en tu PC y en internet | Tu ERP en `onrender.com` |

> ⚠️ **Lo más importante de leer antes de empezar:** la parte 3 es la más delicada, porque cambia la forma en que se publica tu proyecto. Por eso esta guía la deja para el final, la hace en una **rama separada**, y **no toca el servicio de Render que ya funciona** hasta que el nuevo esté probado.

## 2. Mapa de la guía

| Fase | Qué haces | Riesgo | Tiempo aprox. |
| --- | --- | --- | --- |
| 0 | Respaldo del proyecto | 🟢 Bajo | 5 min |
| 1 | Exportar a Excel | 🟢 Bajo | 25 min |
| 2 | Factura en PDF (código y tests) | 🟡 Medio | 40 min |
| 3 | Instalar Docker en tu PC | 🔴 Cuidado | 40 min |
| 4 | Probar el ERP dentro de Docker | 🟡 Medio | 40 min |
| 5 | Publicar en Render (servicio nuevo) | 🔴 Cuidado | 30 min |
| 6 | Cierre y respaldo | 🟢 Bajo | 15 min |

**Puedes parar al terminar cualquier fase** y seguir otro día. Las fases 0, 1 y 2 funcionan sin Docker.

## 3. Las 6 reglas de oro

1. **Todo el trabajo va en la rama `w12`.** La rama `main` (lo que Render publica hoy) no se toca hasta la Fase 6.
2. **No borres tu servicio actual de Render** hasta que el nuevo funcione.
3. **Al terminar cada fase:** corre los tests y haz commit.
4. **Si un paso falla, no sigas al siguiente.** Copia el error completo y pide ayuda.
5. **Nunca uses `git push --force`.** Puede borrar trabajo de GitHub sin posibilidad de recuperarlo.
6. **Nunca escribas contraseñas reales dentro de archivos que subes a GitHub** (tu repositorio es público). Las contraseñas van en variables de entorno de Render.

## 4. Palabras que vas a ver

| Palabra | En palabras simples |
| --- | --- |
| **Rama (branch)** | Una copia de trabajo del proyecto. Lo que hagas en ella no afecta a `main` hasta que tú lo decidas. |
| **Commit** | Guardar una versión del proyecto con un mensaje. |
| **openpyxl** | Librería de Python que crea archivos de Excel. |
| **WeasyPrint** | Librería de Python que convierte una página HTML en un PDF. |
| **Docker** | Programa que empaqueta tu proyecto con todo lo que necesita, para que funcione igual en cualquier computadora. |
| **Imagen / Contenedor** | La imagen es el "paquete" ya armado; el contenedor es ese paquete funcionando. |
| **WSL2** | Una parte de Windows que corre Linux por dentro. Docker la necesita en Windows. |
| **Variable de entorno** | Un dato (como una contraseña) que se guarda en el servidor y no dentro del código. |

---

## FASE 0 — Respaldo 🟢

**¿Qué hace?** Toma una "foto" del proyecto tal como está hoy (que funciona). Si algo sale mal en cualquier momento, podrás regresar a ella.

Abre PowerShell en `C:\Temp_Workspace_ERP`, con tu entorno `(env_erp)` activo, y ejecuta:

```powershell
git status
python manage.py test tests
```

- `git status` debe decir `nothing to commit, working tree clean`.
- Los tests deben terminar en `OK`.

Si alguno de los dos falla, **detente aquí** y pide ayuda antes de seguir.

Ahora crea la foto y tu rama de trabajo:

```powershell
git tag respaldo-antes-w12
git push origin respaldo-antes-w12
git checkout -b w12
```

> **En palabras simples:** `git tag` pone una etiqueta en el estado actual. `git checkout -b w12` crea tu copia de trabajo llamada `w12`: todo lo que hagas desde ahora queda ahí y **no afecta** a `main`.

**Cómo comprobar que salió bien:** `git branch` debe mostrar `* w12`.

**Cómo regresar si algo se rompe:** `git checkout main` te devuelve al proyecto que funciona.

---

## FASE 1 — Exportar el inventario a Excel 🟢

**¿Qué hace?** Agrega un botón que descarga un archivo `.xlsx` con todos tus productos: nombre, categoría, proveedor, precio, stock y el valor del inventario, con un total al final.

### Paso 1.1 — Instalar openpyxl

```powershell
pip install openpyxl==3.1.5
```

Abre `requirements.txt` en VS Code y agrega esta línea **al final** (cada paquete va en su propia línea):

```txt
openpyxl==3.1.5
```

> ⚠️ **Cuidado:** edita `requirements.txt` a mano. No uses `pip freeze > requirements.txt` en PowerShell: guarda el archivo en un formato que Render y tus tests no pueden leer.

### Paso 1.2 — Crear la vista que genera el Excel

Abre `productos/views.py`.

**(a)** Busca la línea `from django.views.generic import DetailView, ListView` y, justo **antes** de ella, pega:

```python
from datetime import date

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
```

**(b)** Baja hasta el **final del archivo** y pega esto:

```python
# ── W12: exportar inventario a Excel ──────────────────────────────────────
def _celda_texto(hoja, fila, columna, valor):
    """Escribe un texto en la celda y lo marca SIEMPRE como texto.

    Si alguien guarda un producto llamado "=1+1", Excel lo trataría como
    una fórmula. Marcarlo como texto evita que se ejecute.
    """
    celda = hoja.cell(row=fila, column=columna, value=str(valor))
    celda.data_type = 's'
    return celda


@login_required
def exportar_excel(request):
    """Descarga el inventario completo en un archivo .xlsx."""
    productos = (
        Producto.objects
        .select_related('categoria', 'proveedor')
        .order_by('nombre')
    )

    libro = Workbook()
    hoja = libro.active
    hoja.title = 'Inventario'

    # Fila 1: encabezados con color
    encabezados = ['ID', 'Producto', 'Categoría', 'Proveedor',
                   'Precio', 'Stock', 'Valor en inventario', 'Activo']
    for col, texto in enumerate(encabezados, start=1):
        celda = hoja.cell(row=1, column=col, value=texto)
        celda.font = Font(bold=True, color='FFFFFF')
        celda.fill = PatternFill('solid', fgColor='1F3A5F')
        celda.alignment = Alignment(horizontal='center')

    # Filas de datos
    fila = 1
    for fila, p in enumerate(productos, start=2):
        hoja.cell(row=fila, column=1, value=p.pk)
        _celda_texto(hoja, fila, 2, p.nombre)
        _celda_texto(hoja, fila, 3, p.categoria.nombre)
        _celda_texto(hoja, fila, 4, p.proveedor.nombre if p.proveedor else '—')
        hoja.cell(row=fila, column=5, value=p.precio).number_format = '#,##0.00'
        hoja.cell(row=fila, column=6, value=p.stock)
        hoja.cell(row=fila, column=7,
                  value=p.precio * p.stock).number_format = '#,##0.00'
        _celda_texto(hoja, fila, 8, 'Sí' if p.activo else 'No')

    # Fila final: total del inventario (fórmula SUM de Excel)
    if fila >= 2:
        hoja.cell(row=fila + 1, column=6, value='TOTAL').font = Font(bold=True)
        total = hoja.cell(row=fila + 1, column=7, value=f'=SUM(G2:G{fila})')
        total.font = Font(bold=True)
        total.number_format = '#,##0.00'

    # Comodidad: primera fila fija, filtros y anchos de columna
    hoja.freeze_panes = 'A2'
    hoja.auto_filter.ref = f'A1:H{max(fila, 1)}'
    for letra, ancho in zip('ABCDEFGH', (8, 32, 20, 24, 12, 10, 20, 10)):
        hoja.column_dimensions[letra].width = ancho

    respuesta = HttpResponse(
        content_type=(
            'application/vnd.openxmlformats-officedocument.'
            'spreadsheetml.sheet'
        )
    )
    respuesta['Content-Disposition'] = (
        f'attachment; filename="inventario_{date.today():%Y-%m-%d}.xlsx"'
    )
    libro.save(respuesta)
    return respuesta
```

> **En palabras simples:**
>
> - `@login_required` → solo usuarios con sesión iniciada pueden descargar el inventario.
> - `Workbook()` crea un libro de Excel vacío; luego se llenan sus celdas fila por fila.
> - `_celda_texto` es una medida de **seguridad**: obliga a que los nombres se guarden como texto. Sin ella, un producto llamado `=algo` podría ejecutarse como fórmula al abrir el Excel.
> - La última fila usa la fórmula `=SUM(...)`: el total lo calcula Excel.

### Paso 1.3 — Crear la ruta (la dirección web)

Abre `productos/urls.py` y agrega esta ruta dentro de `urlpatterns`, después de la ruta `eliminar`:

```python
    # Exportación a Excel (W12)
    path('exportar-excel/',
         views.exportar_excel,
         name='exportar_excel'),
```

### Paso 1.4 — Agregar el botón

Abre `productos/templates/productos/lista.html`. Busca el bloque que empieza con `{% if user.is_authenticated %}` (el que contiene "+ Nuevo producto") y déjalo así:

```html
    {% if user.is_authenticated %}
        <a href="{% url 'productos:exportar_excel' %}" class="btn-erp-primary">
            ⬇ Exportar Excel
        </a>
        <a href="{% url 'productos:crear' %}" class="btn-erp-gold">
            + Nuevo producto
        </a>
    {% endif %}
```

### Paso 1.5 — Probarlo

```powershell
python manage.py runserver
```

1. Abre `http://127.0.0.1:8000/productos/` e inicia sesión.
2. Pulsa **⬇ Exportar Excel**. Se descarga `inventario_AAAA-MM-DD.xlsx`.
3. Ábrelo: debes ver encabezados azules, tus productos y un total al final.

Detén el servidor con `Ctrl+C`.

### Paso 1.6 — Guardar (commit)

```powershell
git add -A
git commit -m "W12 Fase 1: exportar inventario a Excel"
```

> Aún **no** hagas `git push`. Lo haremos cuando todo esté probado.

---

## FASE 2 — Factura en PDF 🟡

**¿Qué hace?** Agrega un botón "Descargar PDF" en el detalle de cada venta. La factura incluye el cliente, la fecha, la tabla de productos con su total y el número de página en cada hoja.

**Lo importante de esta fase:** el generador de PDF (WeasyPrint) necesita programas de Linux que Windows no tiene. Por eso el código está escrito para que, **si faltan esos programas, tu ERP siga funcionando normal** y solo el botón del PDF avise "no disponible". El PDF real lo probaremos en Docker (Fase 4).

### Paso 2.1 — Agregar las dependencias

Abre `requirements.txt` y agrega estas dos líneas **al final**:

```txt
pydyf==0.10.0
weasyprint==60.2
```

> **En palabras simples:** `weasyprint` hace el PDF. `pydyf` es una pieza que WeasyPrint usa; la dejamos **fija** en esa versión porque si se actualiza sola, rompe todos los PDF.

No hace falta instalarlas en tu Windows: se instalarán dentro de Docker y de Render.

### Paso 2.2 — Crear la vista del PDF

Abre `ventas/views.py`.

**(a)** Busca la línea `from django.shortcuts import redirect, render` y **reemplázala** por este bloque:

```python
import logging
from pathlib import Path
from urllib.parse import unquote, urlparse

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
```

**(b)** Baja al **final del archivo** y pega:

```python
# ── W12: factura en PDF (WeasyPrint) ──────────────────────────────────────
logger = logging.getLogger(__name__)


def _fetcher_seguro(url):
    """Decide qué archivos puede leer WeasyPrint al armar el PDF.

    Solo se permiten archivos locales de /static y /media (y imágenes
    incrustadas "data:"). Cualquier dirección de internet se bloquea.
    """
    import weasyprint   # import "perezoso": ver nota en _generar_pdf

    if url.startswith('data:'):
        return weasyprint.default_url_fetcher(url)
    if url.startswith('file:'):
        ruta = Path(unquote(urlparse(url).path)).resolve()
        for carpeta in (settings.STATIC_ROOT, settings.MEDIA_ROOT):
            if ruta.is_relative_to(Path(carpeta).resolve()):
                return weasyprint.default_url_fetcher(url)
    raise ValueError(f'Recurso no permitido en el PDF: {url}')


def _generar_pdf(html: str) -> bytes:
    """Convierte un texto HTML en los bytes de un PDF."""
    # IMPORTANTE: weasyprint se importa AQUÍ ADENTRO y no al inicio del
    # archivo. Así, si la máquina no tiene sus librerías (por ejemplo
    # Windows sin Docker), el resto del ERP sigue funcionando normal.
    import weasyprint

    return weasyprint.HTML(string=html, url_fetcher=_fetcher_seguro).write_pdf()


@login_required
def venta_pdf(request, venta_id):
    """Descarga la factura de una venta en PDF."""
    venta = get_object_or_404(
        Venta.objects
        .select_related('cliente')
        .prefetch_related('detalles__producto'),
        pk=venta_id,
    )
    html = render_to_string(
        'ventas/factura_pdf.html',
        {'venta': venta, 'emitida': timezone.now()},
    )
    try:
        pdf = _generar_pdf(html)
    except (ImportError, OSError):
        logger.exception('WeasyPrint no está disponible en este servidor')
        return HttpResponse(
            'El generador de PDF no está disponible en este servidor.',
            status=503,
            content_type='text/plain; charset=utf-8',
        )

    respuesta = HttpResponse(pdf, content_type='application/pdf')
    respuesta['Content-Disposition'] = (
        f'attachment; filename="factura_{venta.pk:05d}.pdf"'
    )
    return respuesta
```

> **En palabras simples:**
>
> - `import weasyprint` está **dentro** de las funciones, no arriba del archivo. Es el truco más importante de esta guía: si estuviera arriba y tu PC no tiene las librerías, **todo el ERP se caería** al arrancar, incluidos tus tests.
> - `get_object_or_404` → si pides la factura de una venta que no existe, ves "404 No encontrado" en vez de un error feo.
> - `_fetcher_seguro` → el PDF solo puede leer archivos de tu propio proyecto. Nunca descarga nada de internet (así nadie puede usar tu factura para que el servidor visite páginas ajenas).
> - Si faltan las librerías, la vista responde **503** con un mensaje claro, en lugar de romperse.

### Paso 2.3 — Crear la ruta

Abre `ventas/urls.py` y agrega esta línea dentro de `urlpatterns`, después de la ruta `eliminar`:

```python
    # Factura en PDF (W12)
    path('<int:venta_id>/pdf/',     views.venta_pdf,                name='pdf'),
```

### Paso 2.4 — Crear la plantilla de la factura

> 💡 **Atajo:** este archivo viene listo en el ZIP `archivos_nuevos_w12.zip` (ruta `ventas/templates/ventas/factura_pdf.html`). Si lo usas, salta al paso 2.5.

Crea el archivo `ventas/templates/ventas/factura_pdf.html` y pega:

```html
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Factura {{ venta.pk }}</title>
<style>
    /* Tamaño de hoja, márgenes y número de página en cada hoja */
    @page {
        size: A4;
        margin: 2.2cm 1.8cm;
        @bottom-center {
            content: "Página " counter(page) " de " counter(pages);
            font-size: 9pt; color: #666;
        }
    }
    body { font-family: "Liberation Sans", "DejaVu Sans", sans-serif;
           font-size: 10.5pt; color: #222; }
    .encabezado { border-bottom: 3px solid #1F3A5F; padding-bottom: 10px;
                  margin-bottom: 18px; }
    h1 { margin: 0; color: #1F3A5F; font-size: 22pt; }
    .sub { color: #666; font-size: 10pt; margin-top: 4px; }
    .caja { background: #F2F5FA; padding: 10px 14px; border-radius: 4px;
            margin-bottom: 18px; }
    .caja p { margin: 3px 0; }
    table { width: 100%; border-collapse: collapse; }
    /* Los encabezados de la tabla se repiten en cada hoja */
    thead { display: table-header-group; }
    th { background: #1F3A5F; color: #fff; padding: 7px; text-align: left; }
    td { padding: 7px; border-bottom: 1px solid #ddd; }
    tr { page-break-inside: avoid; }
    .der { text-align: right; }
    .total td { border-top: 2px solid #1F3A5F; border-bottom: none;
                font-weight: bold; font-size: 12pt; }
    .pie { margin-top: 30px; color: #666; font-size: 9pt; }
</style>
</head>
<body>
    <div class="encabezado">
        <h1>FACTURA No. {{ venta.pk|stringformat:"05d" }}</h1>
        <div class="sub">ERP Django · UTEC Celaya</div>
    </div>

    <div class="caja">
        <p><strong>Cliente:</strong> {{ venta.cliente.nombre }}</p>
        <p><strong>Correo:</strong> {{ venta.cliente.correo }}</p>
        <p><strong>Fecha de la venta:</strong> {{ venta.fecha|date:"d/m/Y H:i" }}</p>
    </div>

    <table>
        <thead>
            <tr>
                <th>Producto</th>
                <th class="der">Precio unit.</th>
                <th class="der">Cantidad</th>
                <th class="der">Subtotal</th>
            </tr>
        </thead>
        <tbody>
            {% for d in venta.detalles.all %}
            <tr>
                <td>{{ d.producto.nombre }}</td>
                <td class="der">${{ d.precio_unitario|floatformat:2 }}</td>
                <td class="der">{{ d.cantidad }}</td>
                <td class="der">${{ d.subtotal|floatformat:2 }}</td>
            </tr>
            {% empty %}
            <tr><td colspan="4">Esta venta no tiene productos.</td></tr>
            {% endfor %}
            <tr class="total">
                <td colspan="3" class="der">TOTAL</td>
                <td class="der">${{ venta.total|floatformat:2 }}</td>
            </tr>
        </tbody>
    </table>

    <p class="pie">Documento generado el {{ emitida|date:"d/m/Y H:i" }}.</p>
</body>
</html>
```

> **En palabras simples:** es una página web normal (HTML + CSS) que WeasyPrint convierte en PDF. La parte `@page` define el tamaño de hoja y el texto "Página 1 de 2" al pie. `thead { display: table-header-group; }` hace que los títulos de la tabla se repitan si la factura ocupa varias hojas.

### Paso 2.5 — Agregar el botón en el detalle de la venta

Abre `ventas/templates/ventas/detalle.html` y reemplaza el bloque de arriba (el de `erp-page-title`) por:

```html
<div class="erp-page-title">
    <h2>💰 Venta #{{ venta.pk }}</h2>
    {% if user.is_authenticated %}
        <a href="{% url 'ventas:pdf' venta.pk %}"
           class="btn-erp-gold ms-auto">⬇ Descargar PDF</a>
        <a href="{% url 'ventas:eliminar' venta.pk %}"
           class="btn-erp-danger">Eliminar venta</a>
    {% endif %}
</div>
```

### Paso 2.6 — Crear los tests

> **Atajo:** este archivo también viene en el ZIP (`tests/test_w12_documentos.py`).

Crea el archivo `tests/test_w12_documentos.py` y pega:

```python
"""Pruebas W12 — Exportar inventario a Excel y factura en PDF.

Ejecutar con:
    python manage.py test tests.test_w12_documentos --verbosity=2

Las pruebas del PDF real solo corren donde WeasyPrint funciona (Docker/Linux).
En Windows sin Docker se omiten (skip) y el resto pasa normal.
"""
from decimal import Decimal
from io import BytesIO
from unittest import skipUnless
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from openpyxl import load_workbook

from clientes.models import Cliente
from productos.models import Categoria, Producto
from ventas.models import DetalleVenta, Venta


def _hay_weasyprint() -> bool:
    try:
        import weasyprint  # noqa: F401
        return True
    except (ImportError, OSError):
        return False


HAY_WEASYPRINT = _hay_weasyprint()


class ExportarExcelTest(TestCase):
    """GET /productos/exportar-excel/"""

    def setUp(self):
        self.user = User.objects.create_user('excel_user', password='pass')
        cat = Categoria.objects.create(nombre='Cómputo')
        Producto.objects.create(
            nombre='Teclado', precio=Decimal('450.00'), stock=10, categoria=cat)
        Producto.objects.create(
            nombre='=1+1', precio=Decimal('10.00'), stock=2, categoria=cat)
        self.url = reverse('productos:exportar_excel')

    def _abrir_excel(self):
        self.client.login(username='excel_user', password='pass')
        r = self.client.get(self.url)
        return r, load_workbook(BytesIO(r.content))

    def test_sin_login_redirige_a_login(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r['Location'])

    def test_con_login_devuelve_200_y_xlsx(self):
        self.client.login(username='excel_user', password='pass')
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertIn('spreadsheetml.sheet', r['Content-Type'])

    def test_se_descarga_como_archivo_xlsx(self):
        self.client.login(username='excel_user', password='pass')
        r = self.client.get(self.url)
        self.assertIn('attachment', r['Content-Disposition'])
        self.assertIn('.xlsx', r['Content-Disposition'])

    def test_contiene_encabezados_y_productos(self):
        _, libro = self._abrir_excel()
        hoja = libro['Inventario']
        self.assertEqual(hoja['B1'].value, 'Producto')
        nombres = [hoja.cell(row=f, column=2).value for f in (2, 3)]
        self.assertIn('Teclado', nombres)

    def test_valor_en_inventario_es_precio_por_stock(self):
        _, libro = self._abrir_excel()
        hoja = libro['Inventario']
        for fila in (2, 3):
            if hoja.cell(row=fila, column=2).value == 'Teclado':
                self.assertEqual(hoja.cell(row=fila, column=7).value, 4500)

    def test_fila_total_usa_formula_sum(self):
        _, libro = self._abrir_excel()
        self.assertEqual(libro['Inventario']['G4'].value, '=SUM(G2:G3)')

    def test_nombre_con_formula_se_guarda_como_texto(self):
        """Un producto llamado '=1+1' NO debe convertirse en fórmula."""
        _, libro = self._abrir_excel()
        hoja = libro['Inventario']
        celdas = [hoja.cell(row=f, column=2) for f in (2, 3)]
        peligrosa = next(c for c in celdas if c.value == '=1+1')
        self.assertEqual(peligrosa.data_type, 's')


class VentaPDFTest(TestCase):
    """GET /ventas/<id>/pdf/"""

    def setUp(self):
        self.user = User.objects.create_user('pdf_user', password='pass')
        cat = Categoria.objects.create(nombre='Cat PDF')
        prod = Producto.objects.create(
            nombre='Mouse', precio=Decimal('150.00'), stock=5, categoria=cat)
        cli = Cliente.objects.create(
            nombre='Cliente PDF', correo='pdf@test.com', telefono='4611234567')
        self.venta = Venta.objects.create(cliente=cli)
        DetalleVenta.objects.create(
            venta=self.venta, producto=prod, cantidad=2,
            precio_unitario=Decimal('150.00'))
        self.url = reverse('ventas:pdf', args=[self.venta.pk])

    def test_sin_login_redirige_a_login(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r['Location'])

    def test_venta_inexistente_devuelve_404(self):
        self.client.login(username='pdf_user', password='pass')
        r = self.client.get(reverse('ventas:pdf', args=[99999]))
        self.assertEqual(r.status_code, 404)

    def test_sin_weasyprint_responde_503_y_no_se_cae(self):
        """Si faltan las librerías del PDF, el ERP debe seguir vivo."""
        self.client.login(username='pdf_user', password='pass')
        with patch('ventas.views._generar_pdf', side_effect=OSError('sin pango')):
            with self.assertLogs('ventas.views', level='ERROR'):
                r = self.client.get(self.url)
        self.assertEqual(r.status_code, 503)

    @skipUnless(HAY_WEASYPRINT, 'WeasyPrint no disponible (usar Docker)')
    def test_con_login_devuelve_pdf_valido(self):
        self.client.login(username='pdf_user', password='pass')
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'application/pdf')
        self.assertTrue(r.content.startswith(b'%PDF'))
        self.assertGreater(len(r.content), 1000)

    @skipUnless(HAY_WEASYPRINT, 'WeasyPrint no disponible (usar Docker)')
    def test_pdf_se_descarga_como_archivo(self):
        self.client.login(username='pdf_user', password='pass')
        r = self.client.get(self.url)
        self.assertIn('attachment', r['Content-Disposition'])
        self.assertIn('.pdf', r['Content-Disposition'])

    @skipUnless(HAY_WEASYPRINT, 'WeasyPrint no disponible (usar Docker)')
    def test_pdf_bloquea_direcciones_de_internet(self):
        from ventas.views import _fetcher_seguro
        with self.assertRaises(ValueError):
            _fetcher_seguro('http://example.com/logo.png')
```

> **En palabras simples:** un *test* es un robot que prueba tu código y te avisa si algo se rompió. Estos revisan que: sin iniciar sesión te mande al login, que el Excel y el PDF tengan el formato correcto, que una venta inexistente dé "404", y que el ERP no se caiga si falta WeasyPrint. Las pruebas marcadas con `@skipUnless` se **saltan** si WeasyPrint no está disponible (tu Windows) y corren en Docker.

### Paso 2.7 — Correr los tests

```powershell
python manage.py test tests.test_w12_documentos -v 2
python manage.py test tests
```

**Resultado esperado en tu Windows:** el último mensaje debe ser `OK (skipped=3)`.

- `OK` → todo pasó.
- `skipped=3` → 3 pruebas del PDF real se saltaron porque tu Windows no tiene WeasyPrint. **Es normal.** Correrán en Docker.
- En total son alrededor de **136 tests**.

Si ves `FAILED` o `ERROR`, **detente** y mándame la captura.

### Paso 2.8 — Probar el botón

```powershell
python manage.py runserver
```

Entra a `http://127.0.0.1:8000/ventas/`, abre una venta y pulsa **⬇ Descargar PDF**. En tu Windows verás el mensaje *"El generador de PDF no está disponible en este servidor."* **Eso es lo correcto por ahora:** significa que la protección funciona y el resto del ERP sigue vivo.

### Paso 2.9 — Guardar (commit)

```powershell
git add -A
git commit -m "W12 Fase 2: factura PDF (WeasyPrint) con tests"
```

---

## FASE 3 — Instalar Docker en tu PC 🔴

**¿Qué hace?** Instala dos programas en Windows: **WSL2** (Linux dentro de Windows) y **Docker Desktop**. Con ellos tu PC podrá correr el ERP con las librerías que el PDF necesita, igual que en internet.

> ⚠️ **Esta es la única fase que modifica tu computadora** (no tu proyecto). Pide permisos de administrador y un reinicio. Cierra y guarda todo antes de empezar.

### Paso 3.1 — ¿Tu PC puede usar Docker?

Revisa esta lista:

- Windows 10 (versión 2004 o mayor) o Windows 11.
- **Virtualización activada.** Abre el Administrador de tareas (`Ctrl+Shift+Esc`), pestaña **Rendimiento**, apartado **CPU**. Debe decir *"Virtualización: Habilitada"*.
- Al menos 4 GB de memoria RAM libres y varios GB de disco libres.
- Una cuenta de **Administrador** en Windows.

Si dice *"Deshabilitada"*, hay que activarla en el BIOS de la computadora. **Si no te sientes seguro haciendo eso, usa el Plan B del paso 3.6.**

### Paso 3.2 — Crear un punto de restauración

Es un seguro: si algo sale mal, Windows puede volver a este momento.

1. Abre el menú Inicio y escribe **Crear un punto de restauración**.
2. Pulsa **Crear...**, ponle el nombre `antes-de-docker` y confirma.

### Paso 3.3 — Instalar WSL2

Abre PowerShell **como administrador** (clic derecho, *Ejecutar como administrador*) y ejecuta:

```powershell
wsl --install
```

Reinicia la PC cuando lo pida. Al volver, puede abrirse una ventana de Ubuntu pidiendo un usuario y contraseña de Linux: créalos (anótalos; no son los de Windows) y luego cierra esa ventana.

### Paso 3.4 — Instalar Docker Desktop

1. Descarga **Docker Desktop para Windows** desde el sitio oficial (`docker.com`).
2. Instala dejando marcada la opción de usar **WSL 2**.
3. Reinicia si lo pide, abre Docker Desktop y espera a que indique que el motor está corriendo (*Engine running*).
4. En **Settings**, apartado **General**, verifica que esté activada la opción **Use the WSL 2 based engine**.

### Paso 3.5 — Verificar

Con Docker Desktop abierto, en PowerShell:

```powershell
docker --version
docker compose version
docker run hello-world
```

El último comando debe mostrar el mensaje **"Hello from Docker!"**. Si es así, la Fase 3 terminó bien.

### Paso 3.6 — Plan B: si no puedes instalar Docker

No pasa nada: tu proyecto **no depende** de Docker en tu PC. Haz esto:

1. Crea los archivos de la Fase 4 (pasos 4.1 a 4.5), pero **no** ejecutes `docker compose`.
2. Salta a la **Fase 5**. Render construye la imagen con Docker en sus propios servidores.
3. El PDF lo probarás directamente en Render, no en tu PC.

---

## FASE 4 — Probar el ERP dentro de Docker 🟡

**¿Qué hace?** Levanta tu ERP completo dentro de contenedores: una base de datos PostgreSQL y tu aplicación, igual que funcionará en internet.

> 💡 **Atajo:** los pasos 4.1 a 4.4 (cuatro archivos) vienen listos en el ZIP `archivos_nuevos_w12.zip`. Descomprímelo en la raíz de tu proyecto (`C:\Temp_Workspace_ERP`) aceptando reemplazar los archivos existentes, y salta al paso 4.5.

### Paso 4.1 — `.gitattributes` (cuida los saltos de línea)

Crea el archivo `.gitattributes` en la raíz del proyecto:

```gitattributes
# Evita que Windows convierta estos archivos a CRLF (Linux no los entiende así)
* text=auto
*.sh             text eol=lf
Dockerfile       text eol=lf
*.yml            text eol=lf
*.yaml           text eol=lf
requirements.txt text eol=lf
# Archivos binarios: no tocar
*.png  binary
*.jpg  binary
*.jpeg binary
*.webp binary
*.pdf  binary
*.xlsx binary
*.sqlite3 binary
```

> **En palabras simples:** Windows y Linux marcan el final de cada línea de forma distinta. Si un script llega a Linux con el formato de Windows, falla con errores raros. Este archivo le dice a Git que respete el formato de Linux.

### Paso 4.2 — `Dockerfile` (la receta de la imagen)

Reemplaza el contenido de tu archivo `Dockerfile` por:

```dockerfile
# Dockerfile — imagen del ERP con WeasyPrint (PDF)
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Programas de Linux que WeasyPrint necesita para dibujar el PDF
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libcairo-gobject2 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-liberation \
    fonts-dejavu-core \
    libjpeg62-turbo-dev \
    libpng-dev \
    libwebp-dev \
    zlib1g-dev \
    libpq-dev \
    gcc \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Primero solo requirements.txt: así Docker reutiliza esta capa si no cambió
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Después el código del proyecto
COPY . .

# Seguro extra: quita saltos de línea de Windows (CRLF) del script de arranque
RUN sed -i 's/\r$//' docker-entrypoint.sh && chmod +x docker-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["./docker-entrypoint.sh"]
```

> **En palabras simples:** es una receta paso a paso. Parte de un Linux mínimo con Python 3.11, le instala los programas que necesita el PDF, instala tus librerías de Python, copia tu proyecto y dice "al arrancar, ejecuta `docker-entrypoint.sh`".

### Paso 4.3 — `docker-entrypoint.sh` (lo que corre al arrancar)

Crea el archivo `docker-entrypoint.sh` en la raíz del proyecto:

```sh
#!/bin/sh
# docker-entrypoint.sh — se ejecuta cada vez que arranca el contenedor
# (en tu PC con docker compose y en Render).
set -e

echo "==> [1/5] Aplicando migraciones de la base de datos..."
python manage.py migrate --noinput

echo "==> [2/5] Reuniendo archivos estáticos (CSS, imágenes)..."
python manage.py collectstatic --noinput

echo "==> [3/5] Creando grupos y permisos (Gerente, Vendedor, Almacén)..."
python manage.py crear_grupos

echo "==> [4/5] Verificando superusuario..."
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    python manage.py createsuperuser --noinput \
        || echo "AVISO: no se creó el superusuario (si ya existe, es normal)."
else
    echo "AVISO: faltan las variables DJANGO_SUPERUSER_*; no se crea superusuario."
fi

echo "==> [5/5] Iniciando el servidor en el puerto ${PORT:-8000}..."
exec gunicorn core.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
```

> **En palabras simples:** son 5 tareas automáticas: crear las tablas, juntar los archivos CSS, crear los grupos de usuarios (los de `crear_grupos`), crear tu administrador y encender el servidor. Reemplaza el *build command* que tienes hoy en Render.
>
> **Seguridad:** la guía original creaba un administrador con la contraseña `12345` escrita en el código. Aquí el usuario y la contraseña salen de **variables de entorno**, así que nunca quedan expuestos en GitHub.

### Paso 4.4 — `docker-compose.yml` (tu ERP + base de datos en tu PC)

Reemplaza el contenido de `docker-compose.yml` por:

```yaml
# docker-compose.yml — ERP en tu PC: base de datos + aplicación
# Uso:  docker compose up --build
services:

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
      retries: 10

  web:
    build: .
    entrypoint: ["sh", "/app/docker-entrypoint.sh"]
    restart: unless-stopped
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    environment:
      DJANGO_SETTINGS_MODULE:     core.settings_prod
      MODO_LOCAL:                 "True"
      SECRET_KEY:                 dev-clave-docker-no-usar-en-produccion
      DATABASE_URL:               postgres://erp_user:erp_pass_local@db:5432/erp_db
      ALLOWED_HOSTS:              localhost,127.0.0.1
      DJANGO_SUPERUSER_USERNAME:  admin
      DJANGO_SUPERUSER_EMAIL:     admin@erp.local
      DJANGO_SUPERUSER_PASSWORD:  admin-local-123

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

> **En palabras simples:** define dos "cajas": `db` (la base de datos PostgreSQL) y `web` (tu ERP). `MODO_LOCAL: "True"` le avisa a tu ERP que está en tu PC y no en internet. Las contraseñas de este archivo son **solo de práctica local**; nunca las uses en Render.

### Paso 4.5 — Agregar el interruptor `MODO_LOCAL` en `core/settings_prod.py`

**Por qué es necesario:** tu `settings_prod.py` obliga a usar HTTPS y conexión segura a la base de datos **siempre**. Eso es perfecto en internet, pero en tu PC (que usa `http://` y una base de datos sin SSL) provocaría que el navegador no abra la página aunque los contenedores estén corriendo. El interruptor relaja eso **solo** cuando `MODO_LOCAL` es `True`. En Render esa variable no existe, así que producción queda siempre con todos los candados.

Abre `core/settings_prod.py` y haz estos **3 cambios**:

**(a)** Justo **antes** de la línea `# ── HOSTS PERMITIDOS`, agrega:

```python
# ── MODO LOCAL (solo para probar con Docker en tu PC) ──────────────────────────────────────
# En Render esta variable NO existe, así que producción siempre queda con
# todos los candados puestos (HTTPS obligatorio, cookies seguras, etc.).
MODO_LOCAL = os.environ.get('MODO_LOCAL', 'False').lower() == 'true'
```

**(b)** En el bloque `DATABASES`, cambia la línea de `ssl_require` por:

```python
        ssl_require=not MODO_LOCAL,   # Render exige SSL; el Postgres local no lo tiene
```

**(c)** En "HEADERS HTTP SEGUROS", reemplaza estas 6 líneas (de `SECURE_SSL_REDIRECT` a `CSRF_COOKIE_SECURE`) por:

```python
SECURE_SSL_REDIRECT            = not MODO_LOCAL
SECURE_HSTS_SECONDS            = 0 if MODO_LOCAL else 31536000    # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = not MODO_LOCAL
SECURE_HSTS_PRELOAD            = not MODO_LOCAL
SESSION_COOKIE_SECURE          = not MODO_LOCAL
CSRF_COOKIE_SECURE             = not MODO_LOCAL
```

No borres la línea `SECURE_PROXY_SSL_HEADER` que está justo arriba: es la que evita el bucle de redirecciones en Render.

### Paso 4.6 — Verificar los saltos de línea

```powershell
git add -A
git ls-files --eol docker-entrypoint.sh
```

Debe mostrar `i/lf    w/lf`. Si muestra `w/crlf`:

1. Abre `docker-entrypoint.sh` en VS Code.
2. En la esquina inferior derecha haz clic en **CRLF** y elige **LF**.
3. Guarda con `Ctrl+S` y repite `git add -A`.

### Paso 4.7 — Levantar el ERP en Docker

Con Docker Desktop abierto:

```powershell
docker compose up --build
```

La primera vez tarda varios minutos (descarga e instala todo). Al final debes ver líneas como:

```text
==> [1/5] Aplicando migraciones de la base de datos...
==> [3/5] Creando grupos y permisos (Gerente, Vendedor, Almacén)...
==> [5/5] Iniciando el servidor en el puerto 8000...
[INFO] Listening at: http://0.0.0.0:8000
```

**Deja esa ventana abierta** mientras pruebas.

### Paso 4.8 — Probarlo en el navegador

1. Abre `http://127.0.0.1:8000`.
2. Inicia sesión en `/admin/` con usuario `admin` y contraseña `admin-local-123` (solo para tu PC).
3. Esta base de datos es **nueva y está vacía** (no es tu SQLite de siempre). Crea una categoría, un producto, un cliente y una venta con al menos un producto.
4. Entra al detalle de la venta y pulsa **⬇ Descargar PDF**. Ahora **sí** se descarga la factura.
5. En `/productos/` pulsa **⬇ Exportar Excel** y revisa el archivo.

### Paso 4.9 — Correr los tests dentro del contenedor

Abre **otra** ventana de PowerShell en la carpeta del proyecto y ejecuta:

```powershell
docker compose exec web python manage.py test tests
```

Debe terminar en `OK` y **sin `skipped`**: ahora el PDF real también se prueba.

### Paso 4.10 — Apagar y guardar

En la ventana donde corre Docker pulsa `Ctrl+C`, y luego:

```powershell
docker compose down
git add -A
git commit -m "W12 Fase 4: Docker (Dockerfile, entrypoint, compose, MODO_LOCAL)"
```

---

## FASE 5 — Publicar en Render con un servicio nuevo 🔴

**¿Qué hace?** Crea un servicio **nuevo** en Render que construye tu imagen de Docker. Tu servicio actual (el que ya funciona) **no se toca**: sigue en línea mientras pruebas el nuevo.

> ⚠️ **Por qué un servicio nuevo:** en Render el tipo de servicio no se puede cambiar después de crearlo, y el archivo `render.yaml` de tu repositorio **no se usa** (tu servicio se configuró a mano en el panel). Por eso no cambiamos el actual: creamos otro al lado.

**Antes de empezar, ten a la mano** (cópialas del servicio actual, pestaña *Environment*): `SECRET_KEY`, `DATABASE_URL`, y tus variables `DJANGO_SUPERUSER_*`.

### Paso 5.1 — Subir la rama a GitHub

```powershell
git status
git push -u origin w12
```

`git status` debe decir `nothing to commit, working tree clean`. Esto sube **solo** la rama `w12`; no cambia `main` ni el servicio actual.

### Paso 5.2 — Crear el servicio nuevo

En el panel de Render (los nombres de los botones pueden variar un poco):

1. Pulsa **New +** y elige **Web Service**.
2. Selecciona tu repositorio de GitHub (`Hakm03/Django`).
3. Configura:
   - **Name:** un nombre distinto al actual, por ejemplo `erp-docker`.
   - **Branch:** `w12`.
   - **Language / Runtime:** `Docker`.
   - **Region:** la misma de tu base de datos.
   - **Instance Type:** `Free`.
4. **No escribas** Build Command ni Start Command: con Docker no se usan, todo está en el `Dockerfile` y en `docker-entrypoint.sh`.
5. **Antes** de pulsar *Create Web Service*, agrega las variables del paso 5.3.

### Paso 5.3 — Variables de entorno

| Variable | Valor | Nota |
| --- | --- | --- |
| `DJANGO_SETTINGS_MODULE` | `core.settings_prod` | Sin esta vuelve el error `DisallowedHost` |
| `SECRET_KEY` | la misma de tu servicio actual | Cópiala tal cual |
| `DATABASE_URL` | la misma de tu servicio actual | Usa la *Internal Database URL* |
| `DJANGO_SUPERUSER_USERNAME` | tu usuario administrador |  |
| `DJANGO_SUPERUSER_EMAIL` | un correo válido | Si es inválido, no se crea el usuario |
| `DJANGO_SUPERUSER_PASSWORD` | tu contraseña | Escríbelo con **doble S** (`PASSWORD`) |

**NO agregues** estas variables:

- `MODO_LOCAL`: dejaría producción sin HTTPS obligatorio.
- `PYTHON_VERSION`: Docker usa la versión que dice el `Dockerfile`.
- `DEBUG`: `settings_prod.py` ya lo apaga.

> **Dos servicios, una base de datos:** mientras pruebas, el servicio viejo y el nuevo usarán la misma base de datos. Está bien, porque las migraciones son las mismas. **No borres la base de datos.**

### Paso 5.4 — Vigilar el despliegue

Pulsa **Create Web Service** y abre la pestaña **Logs**. La primera vez puede tardar varios minutos. Debes ver, en orden:

```text
==> [1/5] Aplicando migraciones de la base de datos...
==> [3/5] Creando grupos y permisos (Gerente, Vendedor, Almacén)...
==> [5/5] Iniciando el servidor en el puerto ...
[INFO] Listening at: http://0.0.0.0:...
```

El número de puerto puede ser distinto; lo importante es ver **Listening at** y luego que el servicio aparezca como *Live*.

### Paso 5.5 — Probar la dirección nueva

Abre la URL del servicio nuevo (termina en `onrender.com`):

1. La página de inicio carga.
2. Puedes iniciar sesión con tu usuario administrador.
3. En `/productos/`, **⬇ Exportar Excel** descarga el archivo.
4. Crea o abre una venta y pulsa **⬇ Descargar PDF**: ahora se descarga la factura.

En el plan gratuito, el servicio se "duerme" cuando nadie lo usa; la primera visita puede tardar cerca de un minuto en responder. Es normal.

### Paso 5.6 — Si algo falla

No borres nada. Revisa la tabla de **Problemas comunes** al final de esta guía y, si no aparece tu caso, mándame el log completo del despliegue.

---

## FASE 6 — Cierre y respaldo 🟢

**¿Qué hace?** Une tu rama `w12` con `main` (solo cuando todo ya funcionó) y guarda un respaldo.

### Paso 6.1 — Unir `w12` con `main`

Hazlo **solo** si el servicio nuevo funcionó bien en el paso 5.5:

```powershell
git checkout main
git merge w12
python manage.py test tests
git push origin main
```

> **Qué va a pasar:** tu servicio **anterior** sigue apuntando a `main`, así que se actualiza solo con el código nuevo. Ahí el Excel funcionará, pero el botón de PDF mostrará "no disponible" (ese servicio no usa Docker). Es lo esperado y no causa caídas, gracias al `import weasyprint` dentro de las funciones.

### Paso 6.2 — Hacer que el servicio nuevo siga a `main`

En Render, entra al servicio nuevo, **Settings**, cambia **Branch** de `w12` a `main` y guarda. Se volverá a desplegar con lo mismo.

### Paso 6.3 — Retirar el servicio viejo (sin prisa)

Cuando el servicio nuevo lleve unos días funcionando bien, puedes borrar el viejo desde su pestaña **Settings**. **No borres la base de datos**: el servicio nuevo la está usando. Revisa también en el panel de la base de datos la fecha de vencimiento de su plan gratuito.

### Paso 6.4 — Respaldo en tu USB

Ejecuta tu script `finalizar_sesion.bat`. Si te muestra "Acceso denegado" por archivos de `.git`, agrega la opción `/r` a su comando `xcopy`, igual que hicimos en `iniciar_sesion.bat`.

### Paso 6.5 — Lista final

- [ ] Existe la etiqueta `respaldo-antes-w12` en GitHub.
- [ ] El botón **Exportar Excel** descarga un `.xlsx` correcto.
- [ ] El botón **Descargar PDF** descarga una factura (en Docker y en Render).
- [ ] `python manage.py test tests` termina en `OK`.
- [ ] `docker compose exec web python manage.py test tests` termina en `OK` sin `skipped`.
- [ ] El servicio nuevo de Render está *Live* y puedes iniciar sesión.
- [ ] No hay contraseñas reales escritas en ningún archivo del repositorio.
- [ ] `main` actualizado en GitHub y respaldo hecho en la USB.

---

## Problemas comunes

| Lo que ves | Qué significa | Qué hacer |
| --- | --- | --- |
| `/bin/sh^M: not found` o `exec format error` | El script de arranque tiene saltos de línea de Windows | Paso 4.6: cámbialo a **LF** en VS Code y repite `git add -A` |
| `docker: command not found` o *Cannot connect to the Docker daemon* | Docker Desktop no está abierto | Ábrelo y espera a que diga *Engine running* |
| Los contenedores corren pero el navegador no abre `127.0.0.1:8000` | Falta `MODO_LOCAL` o el paso 4.5 | Revisa que el compose tenga `MODO_LOCAL: "True"` y que hiciste los 3 cambios en `settings_prod.py` |
| *Port is already allocated* (puerto 8000 ocupado) | Tienes `runserver` abierto | Ciérralo con `Ctrl+C` y vuelve a intentar |
| Docker Desktop no inicia | Virtualización desactivada o WSL2 incompleto | Revisa el paso 3.1; si no puedes, usa el Plan B (3.6) |
| En Render: *Build failed* con conflicto de versiones | `requirements.txt` tiene un paquete repetido | Que cada paquete aparezca una sola vez |
| `DisallowedHost` | Falta `DJANGO_SETTINGS_MODULE` en Render | Agrégala con el valor `core.settings_prod` |
| `ERR_TOO_MANY_REDIRECTS` en Render | Falta `SECURE_PROXY_SSL_HEADER` o pusiste `MODO_LOCAL` | Verifica que la línea exista y que `MODO_LOCAL` **no** esté en Render |
| El PDF dice "no disponible" en Render | Ese servicio no es Docker | Confirma que el servicio nuevo tenga *Language: Docker* |
| No puedes entrar al administrador | Variable mal escrita o correo inválido | Revisa `DJANGO_SUPERUSER_PASSWORD` (doble S) y que el correo sea válido |
| `column ... does not exist` o `relation ... does not exist` | La base de datos tiene una versión vieja de las tablas | Mándame el log; se resuelve con una base limpia |
| El PDF tarda mucho o el servicio se reinicia | El plan gratuito tiene poca memoria | Prueba con una venta pequeña; si persiste, mándame el log |

---

## Cómo volver atrás si algo sale mal

| Situación | Qué hacer |
| --- | --- |
| Quiero regresar al proyecto que funcionaba | `git checkout main` |
| Quiero tirar **todo** el trabajo de la rama | `git checkout main` y luego `git branch -D w12` |
| Quiero ver el proyecto exactamente como estaba antes | `git checkout respaldo-antes-w12` (solo para mirar; luego `git checkout main`) |
| El servicio nuevo de Render no funciona | Ignóralo o bórralo: el servicio viejo sigue funcionando |
| Docker dejó mi PC rara | Restaura el punto `antes-de-docker` de Windows |

**Fin de la guía W12.** Si te trabas en cualquier paso, copia el mensaje de error completo (o toma captura) y pídeme ayuda indicando el número de paso.

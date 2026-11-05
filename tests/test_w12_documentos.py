"""Pruebas W12 — Exportar inventario (Excel / CSV).

Ejecutar con:
    python manage.py test tests.test_w12_documentos --verbosity=2

Las pruebas del PDF real solo corren donde WeasyPrint funciona (Docker/Linux).
En Windows sin Docker se omiten (skip) y el resto pasa normal.
"""
import csv
from decimal import Decimal
from io import BytesIO, StringIO
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
    """GET /productos/exportar-excel/ (ruta anterior: siempre xlsx)."""

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


class ExportarInventarioTest(TestCase):
    """GET /productos/exportar/?formato=xlsx|csv"""

    def setUp(self):
        self.user = User.objects.create_user('inv_user', password='pass')
        cat = Categoria.objects.create(nombre='Cómputo')
        Producto.objects.create(
            nombre='Teclado', precio=Decimal('450.00'), stock=10, categoria=cat)
        Producto.objects.create(
            nombre='=1+1', precio=Decimal('10.00'), stock=2, categoria=cat)
        self.url = reverse('productos:exportar')

    def _login(self):
        self.client.login(username='inv_user', password='pass')

    def _filas_csv(self, respuesta):
        texto = respuesta.content.decode('utf-8-sig')
        return list(csv.reader(StringIO(texto)))

    # --- acceso -----------------------------------------------------------
    def test_sin_login_redirige_a_login(self):
        for formato in ('xlsx', 'csv'):
            r = self.client.get(self.url, {'formato': formato})
            self.assertEqual(r.status_code, 302)
            self.assertIn('/accounts/login/', r['Location'])

    # --- xlsx -------------------------------------------------------------
    def test_xlsx_200_tipo_y_attachment(self):
        self._login()
        r = self.client.get(self.url, {'formato': 'xlsx'})
        self.assertEqual(r.status_code, 200)
        self.assertIn('spreadsheetml.sheet', r['Content-Type'])
        self.assertIn('attachment', r['Content-Disposition'])
        self.assertIn('inventario_', r['Content-Disposition'])
        self.assertIn('.xlsx', r['Content-Disposition'])

    def test_sin_formato_devuelve_xlsx(self):
        self._login()
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertIn('spreadsheetml.sheet', r['Content-Type'])
        self.assertIn('.xlsx', r['Content-Disposition'])

    def test_xlsx_formula_no_es_ejecutable(self):
        self._login()
        r = self.client.get(self.url, {'formato': 'xlsx'})
        hoja = load_workbook(BytesIO(r.content))['Inventario']
        celdas = [hoja.cell(row=f, column=2) for f in (2, 3)]
        peligrosa = next(c for c in celdas if c.value == '=1+1')
        self.assertEqual(peligrosa.data_type, 's')

    # --- csv --------------------------------------------------------------
    def test_csv_200_tipo_y_attachment(self):
        self._login()
        r = self.client.get(self.url, {'formato': 'csv'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('attachment', r['Content-Disposition'])
        self.assertIn('inventario_', r['Content-Disposition'])
        self.assertIn('.csv', r['Content-Disposition'])

    def test_csv_empieza_con_bom_y_trae_encabezados(self):
        self._login()
        r = self.client.get(self.url, {'formato': 'csv'})
        self.assertTrue(r.content.startswith(b'\xef\xbb\xbf'))
        filas = self._filas_csv(r)
        self.assertEqual(
            filas[0],
            ['ID', 'Producto', 'Categoría', 'Proveedor',
             'Precio', 'Stock', 'Valor en inventario', 'Activo'])
        nombres = [f[1] for f in filas[1:]]
        self.assertIn('Teclado', nombres)
        self.assertEqual(len(filas), 3)  # encabezado + 2 productos

    def test_csv_formula_no_es_ejecutable(self):
        self._login()
        r = self.client.get(self.url, {'formato': 'csv'})
        nombres = [f[1] for f in self._filas_csv(r)[1:]]
        self.assertIn("'=1+1", nombres)
        self.assertNotIn('=1+1', nombres)

    def test_csv_protege_todos_los_prefijos_peligrosos(self):
        cat = Categoria.objects.first()
        for nombre in ('+cmd', '-cmd', '@cmd'):
            Producto.objects.create(
                nombre=nombre, precio=Decimal('1.00'), stock=1, categoria=cat)
        self._login()
        r = self.client.get(self.url, {'formato': 'csv'})
        nombres = [f[1] for f in self._filas_csv(r)[1:]]
        for nombre in ('+cmd', '-cmd', '@cmd'):
            self.assertIn("'" + nombre, nombres)
            self.assertNotIn(nombre, nombres)

    # --- formato inválido -------------------------------------------------
    def test_formato_invalido_devuelve_400_con_mensaje(self):
        self._login()
        for formato in ('exe', 'docx', '../../etc', ''):
            r = self.client.get(self.url, {'formato': formato})
            self.assertEqual(r.status_code, 400, formato)
            self.assertIn('Formato no válido', r.content.decode('utf-8'))


class InventarioPDFTest(TestCase):
    """GET /productos/exportar/?formato=pdf"""

    def setUp(self):
        self.user = User.objects.create_user('invpdf_user', password='pass')
        cat = Categoria.objects.create(nombre='Cómputo')
        Producto.objects.create(
            nombre='Teclado', precio=Decimal('450.00'), stock=10, categoria=cat)
        self.url = reverse('productos:exportar')

    def test_sin_login_redirige_a_login(self):
        r = self.client.get(self.url, {'formato': 'pdf'})
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r['Location'])

    def test_sin_weasyprint_responde_503(self):
        self.client.login(username='invpdf_user', password='pass')
        with patch('core.pdf_utils.generar_pdf', side_effect=OSError('sin pango')):
            with self.assertLogs('productos.views', level='ERROR'):
                r = self.client.get(self.url, {'formato': 'pdf'})
        self.assertEqual(r.status_code, 503)

    def test_demasiados_productos_devuelve_400(self):
        self.client.login(username='invpdf_user', password='pass')
        with patch('productos.views.MAX_PRODUCTOS_PDF', 1):
            Producto.objects.create(
                nombre='Otro', precio=Decimal('1.00'), stock=1,
                categoria=Categoria.objects.first())
            r = self.client.get(self.url, {'formato': 'pdf'})
        self.assertEqual(r.status_code, 400)
        self.assertIn('demasiados', r.content.decode('utf-8'))

    @skipUnless(HAY_WEASYPRINT, 'WeasyPrint no disponible (usar Docker)')
    def test_pdf_valido_y_attachment(self):
        self.client.login(username='invpdf_user', password='pass')
        r = self.client.get(self.url, {'formato': 'pdf'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'application/pdf')
        self.assertTrue(r.content.startswith(b'%PDF'))
        self.assertIn('attachment', r['Content-Disposition'])
        self.assertIn('.pdf', r['Content-Disposition'])


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
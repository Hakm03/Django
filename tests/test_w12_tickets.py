"""Pruebas W12 (ampliación) — tickets de venta: vista previa e impresión.

Ejecutar con:
    python manage.py test tests.test_w12_tickets --verbosity=2

El PDF real solo se prueba donde WeasyPrint funciona (Docker/Linux).
"""
from decimal import Decimal
from unittest import skipUnless
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

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


def _crear_venta(cliente, producto, cantidad=2, precio='150.00'):
    venta = Venta.objects.create(cliente=cliente)
    DetalleVenta.objects.create(
        venta=venta, producto=producto, cantidad=cantidad,
        precio_unitario=Decimal(precio))
    return venta


class TicketBaseTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('tk_user', password='pass')
        cat = Categoria.objects.create(nombre='Cat Ticket')
        self.prod = Producto.objects.create(
            nombre='Mouse', precio=Decimal('150.00'), stock=50,
            categoria=cat)
        self.cli = Cliente.objects.create(
            nombre='Cliente Ticket', correo='tk@test.com',
            telefono='4611234567')
        self.venta = _crear_venta(self.cli, self.prod)  # total 300.00


class TicketIndividualTest(TicketBaseTest):
    """GET /ventas/<id>/ticket/"""

    def setUp(self):
        super().setUp()
        self.url = reverse('ventas:ticket', args=[self.venta.pk])

    def test_sin_login_redirige_a_login(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r['Location'])

    def test_con_login_200_con_folio_y_total(self):
        self.client.login(username='tk_user', password='pass')
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, f'{self.venta.pk:05d}')
        self.assertContains(r, '300.00')
        self.assertContains(r, 'Mouse')

    def test_venta_inexistente_404(self):
        self.client.login(username='tk_user', password='pass')
        r = self.client.get(reverse('ventas:ticket', args=[99999]))
        self.assertEqual(r.status_code, 404)

    def test_papel_por_defecto_es_80mm(self):
        self.client.login(username='tk_user', password='pass')
        r = self.client.get(self.url)
        self.assertContains(r, 'size: 80mm auto')

    def test_papeles_permitidos(self):
        self.client.login(username='tk_user', password='pass')
        esperado = {'58mm': '58mm auto', 'a4': 'size: A4',
                    'carta': 'size: letter', 'a5': 'size: A5'}
        for papel, texto in esperado.items():
            r = self.client.get(self.url, {'papel': papel})
            self.assertEqual(r.status_code, 200, papel)
            self.assertContains(r, texto)

    def test_papel_no_permitido_400(self):
        self.client.login(username='tk_user', password='pass')
        for malo in ('1000mm', 'a4; } body { display:none', '<script>'):
            r = self.client.get(self.url, {'papel': malo})
            self.assertEqual(r.status_code, 400, malo)

    def test_nombre_de_producto_se_escapa(self):
        self.client.login(username='tk_user', password='pass')
        self.prod.nombre = '<script>alert(1)</script>'
        self.prod.save()
        r = self.client.get(self.url)
        self.assertNotContains(r, '<script>alert(1)</script>')
        self.assertContains(r, '&lt;script&gt;alert(1)&lt;/script&gt;')

    def test_detalle_tiene_boton_vista_previa(self):
        self.client.login(username='tk_user', password='pass')
        r = self.client.get(reverse('ventas:detalle', args=[self.venta.pk]))
        self.assertContains(r, self.url)
        self.assertContains(r, 'Vista previa')
        # El botón anterior de la factura sigue ahí.
        self.assertContains(r, reverse('ventas:pdf', args=[self.venta.pk]))


class TicketsLoteTest(TicketBaseTest):
    """GET /ventas/tickets/?ids=1&ids=2&formato=html|pdf"""

    def setUp(self):
        super().setUp()
        self.venta2 = _crear_venta(self.cli, self.prod, 1, '99.50')
        self.url = reverse('ventas:tickets')
        self.client.login(username='tk_user', password='pass')

    def _get(self, **params):
        return self.client.get(self.url, params)

    def test_sin_login_redirige_a_login(self):
        self.client.logout()
        r = self.client.get(self.url, {'ids': self.venta.pk})
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r['Location'])

    def test_lote_html_muestra_todos_los_tickets(self):
        r = self._get(ids=[self.venta.pk, self.venta2.pk])
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, '300.00')
        self.assertContains(r, '99.50')
        self.assertContains(r, 'class="ticket"', count=2)

    def test_ids_repetidos_no_duplican_tickets(self):
        r = self._get(ids=[self.venta.pk, self.venta.pk])
        self.assertContains(r, 'class="ticket"', count=1)

    def test_ids_inexistentes_se_ignoran_si_hay_alguno_valido(self):
        r = self._get(ids=[self.venta.pk, 99999])
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'class="ticket"', count=1)

    def test_todos_inexistentes_404(self):
        self.assertEqual(self._get(ids=[99998, 99999]).status_code, 404)

    def test_sin_ids_400(self):
        self.assertEqual(self._get().status_code, 400)

    def test_ids_no_numericos_400(self):
        for malo in ('abc', '1;2', '-1', '１２', '²', '1' * 30, ''):
            self.assertEqual(self._get(ids=malo).status_code, 400, malo)

    def test_mas_de_100_ids_400(self):
        r = self._get(ids=list(range(1, 102)))
        self.assertEqual(r.status_code, 400)
        self.assertIn('máximo 100', r.content.decode('utf-8'))

    def test_formato_y_papel_no_permitidos_400(self):
        self.assertEqual(
            self._get(ids=self.venta.pk, formato='exe').status_code, 400)
        self.assertEqual(
            self._get(ids=self.venta.pk, papel='9000mm').status_code, 400)

    def test_pdf_sin_weasyprint_responde_503(self):
        with patch('core.pdf_utils.generar_pdf',
                   side_effect=OSError('sin pango')):
            with self.assertLogs('ventas.views', level='ERROR'):
                r = self._get(ids=self.venta.pk, formato='pdf')
        self.assertEqual(r.status_code, 503)

    @skipUnless(HAY_WEASYPRINT, 'WeasyPrint no disponible (usar Docker)')
    def test_pdf_valido_y_attachment(self):
        r = self._get(ids=[self.venta.pk, self.venta2.pk],
                      formato='pdf', papel='80mm')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'application/pdf')
        self.assertTrue(r.content.startswith(b'%PDF'))
        self.assertIn('attachment', r['Content-Disposition'])

    def test_lista_muestra_casillas_y_un_solo_boton_oculto(self):
        r = self.client.get(reverse('ventas:lista'))
        self.assertContains(r, f'name="ids" value="{self.venta.pk}"')
        # Un solo botón "Vista previa", oculto hasta marcar una casilla.
        self.assertContains(r, 'id="btn-vista-previa"')
        self.assertContains(r, 'hidden>')
        self.assertNotContains(r, 'id="btn-imprimir"')
        self.assertNotContains(r, 'id="btn-exportar"')
        self.assertNotContains(r, 'name="papel"')
        self.assertContains(r, reverse('ventas:crear'))  # Nueva venta sigue

    def test_lista_sin_login_no_muestra_casillas(self):
        self.client.logout()
        r = self.client.get(reverse('ventas:lista'))
        self.assertNotContains(r, 'name="ids"')
        self.assertNotContains(r, 'id="btn-vista-previa"')

    def test_vista_previa_ofrece_hojas_y_formatos(self):
        r = self._get(ids=[self.venta.pk, self.venta2.pk])
        for hoja in ('58mm', '80mm', 'a5', 'a4', 'carta'):
            self.assertContains(r, f'data-vp-hoja="{hoja}"')
        tickets = reverse('ventas:tickets')
        for formato in ('pdf', 'xlsx', 'csv'):
            self.assertContains(r, f'{tickets}?ids={self.venta.pk}&amp;'
                                   f'ids={self.venta2.pk}&amp;formato={formato}')
        self.assertContains(r, 'data-vp-con-hoja="1"')   # solo el PDF usa la hoja

    def test_xlsx_de_ventas(self):
        from io import BytesIO
        from openpyxl import load_workbook
        r = self._get(ids=[self.venta.pk, self.venta2.pk], formato='xlsx')
        self.assertEqual(r.status_code, 200)
        self.assertIn('spreadsheetml', r['Content-Type'])
        self.assertIn('attachment', r['Content-Disposition'])
        self.assertIn('.xlsx', r['Content-Disposition'])
        hoja = load_workbook(BytesIO(r.content)).active
        self.assertEqual(hoja['A1'].value, 'Folio')
        self.assertEqual(hoja.max_row, 3)             # encabezado + 2 líneas
        self.assertEqual(hoja['D2'].value, 'Mouse')
        self.assertEqual(hoja['H2'].value, Decimal('300.00'))

    def test_xlsx_texto_con_formula_queda_como_texto(self):
        from io import BytesIO
        from openpyxl import load_workbook
        self.prod.nombre = '=1+1'
        self.prod.save()
        r = self._get(ids=self.venta.pk, formato='xlsx')
        celda = load_workbook(BytesIO(r.content)).active['D2']
        self.assertEqual(celda.data_type, 's')
        self.assertEqual(celda.value, '=1+1')

    def test_csv_de_ventas(self):
        r = self._get(ids=[self.venta.pk, self.venta2.pk], formato='csv')
        self.assertEqual(r.status_code, 200)
        self.assertIn('text/csv', r['Content-Type'])
        self.assertIn('.csv', r['Content-Disposition'])
        texto = r.content.decode('utf-8')
        self.assertTrue(texto.startswith('﻿'))
        self.assertIn('Folio,Fecha,Cliente,Producto', texto)
        self.assertIn('Mouse', texto)

    def test_csv_protege_formulas(self):
        for prefijo in ('=', '+', '-', '@'):
            self.prod.nombre = f'{prefijo}CMD'
            self.prod.save()
            texto = self._get(ids=self.venta.pk,
                              formato='csv').content.decode('utf-8')
            self.assertIn(f"'{prefijo}CMD", texto, prefijo)

    def test_xlsx_y_csv_sin_login_redirigen(self):
        self.client.logout()
        for formato in ('xlsx', 'csv'):
            r = self.client.get(self.url, {'ids': self.venta.pk,
                                           'formato': formato})
            self.assertEqual(r.status_code, 302, formato)
            self.assertIn('/accounts/login/', r['Location'])

    def test_xlsx_ids_inexistentes_404_e_invalidos_400(self):
        self.assertEqual(self._get(ids=99999, formato='xlsx').status_code, 404)
        self.assertEqual(self._get(ids='x', formato='csv').status_code, 400)


class InventarioImprimirTest(TestCase):
    """GET /productos/imprimir/"""

    def setUp(self):
        self.user = User.objects.create_user('inv_print', password='pass')
        cat = Categoria.objects.create(nombre='Cat Imp')
        Producto.objects.create(
            nombre='Teclado', precio=Decimal('450.00'), stock=10,
            categoria=cat)                                   # valor 4500.00
        Producto.objects.create(
            nombre='<b>Raro</b>', precio=Decimal('10.00'), stock=3,
            categoria=cat)                                   # valor 30.00
        self.url = reverse('productos:imprimir')

    def test_sin_login_redirige_a_login(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r['Location'])

    def test_con_login_200_total_y_texto_escapado(self):
        self.client.login(username='inv_print', password='pass')
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Teclado')
        self.assertContains(r, '4530.00')
        self.assertNotContains(r, '<b>Raro</b>')
        self.assertContains(r, 'size: A4')

    def test_papel_carta_y_papel_invalido(self):
        self.client.login(username='inv_print', password='pass')
        self.assertContains(self.client.get(self.url, {'papel': 'carta'}),
                            'size: letter')
        self.assertEqual(
            self.client.get(self.url, {'papel': 'x; }'}).status_code, 400)

    def test_demasiados_productos_400(self):
        self.client.login(username='inv_print', password='pass')
        with patch('productos.views.MAX_PRODUCTOS_PDF', 1):
            r = self.client.get(self.url)
        self.assertEqual(r.status_code, 400)

    def test_lista_de_productos_solo_tiene_vista_previa(self):
        """Un único botón: ya no hay selector de formato ni botón Exportar."""
        self.client.login(username='inv_print', password='pass')
        r = self.client.get(reverse('productos:lista'))
        self.assertContains(r, self.url)
        self.assertContains(r, 'Vista previa')
        self.assertNotContains(r, 'Formato de exportación')

    def test_vista_previa_ofrece_hojas_y_formatos(self):
        self.client.login(username='inv_print', password='pass')
        r = self.client.get(self.url)
        for hoja in ('data-vp-hoja="a4"', 'data-vp-hoja="carta"',
                     'data-vp-hoja="oficio"'):
            self.assertContains(r, hoja)
        exportar = reverse('productos:exportar')
        for formato in ('pdf', 'xlsx', 'csv'):
            self.assertContains(r, f'{exportar}?formato={formato}')

    def test_oficio_es_papel_permitido(self):
        self.client.login(username='inv_print', password='pass')
        r = self.client.get(self.url, {'papel': 'oficio'})
        self.assertContains(r, 'size: 216mm 356mm')

    def test_detalle_de_producto_tiene_vista_previa_de_ese_producto(self):
        self.client.login(username='inv_print', password='pass')
        p = Producto.objects.get(nombre='Teclado')
        r = self.client.get(reverse('productos:detalle', args=[p.pk]))
        self.assertContains(r, f'{self.url}?ids={p.pk}')
        self.assertContains(r, 'Vista previa')

    def test_vista_previa_con_ids_muestra_solo_ese_producto(self):
        self.client.login(username='inv_print', password='pass')
        p = Producto.objects.get(nombre='Teclado')
        r = self.client.get(self.url, {'ids': p.pk})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Ficha de producto')
        self.assertContains(r, 'Teclado')
        self.assertNotContains(r, 'Raro')
        # Los enlaces de exportar llevan el mismo filtro.
        self.assertContains(r, f'formato=xlsx')
        self.assertContains(r, f'ids={p.pk}')

    def test_ids_invalidos_400_e_inexistentes_404(self):
        self.client.login(username='inv_print', password='pass')
        for malo in ('abc', '1;2', '-1', '²', '9' * 12):
            self.assertEqual(
                self.client.get(self.url, {'ids': malo}).status_code, 400, malo)
        self.assertEqual(
            self.client.get(self.url, {'ids': 99999}).status_code, 404)

    def test_exportar_xlsx_con_ids_solo_trae_ese_producto(self):
        from io import BytesIO
        from openpyxl import load_workbook
        self.client.login(username='inv_print', password='pass')
        p = Producto.objects.get(nombre='Teclado')
        r = self.client.get(reverse('productos:exportar'),
                            {'formato': 'xlsx', 'ids': p.pk})
        self.assertEqual(r.status_code, 200)
        hoja = load_workbook(BytesIO(r.content)).active
        nombres = [c.value for c in hoja['B'][1:] if c.value]
        self.assertEqual(nombres, ['Teclado'])

    def test_exportar_csv_con_ids_invalidos_400_e_inexistentes_404(self):
        self.client.login(username='inv_print', password='pass')
        url = reverse('productos:exportar')
        self.assertEqual(
            self.client.get(url, {'formato': 'csv', 'ids': 'x'}).status_code, 400)
        self.assertEqual(
            self.client.get(url, {'formato': 'csv', 'ids': 99999}).status_code, 404)

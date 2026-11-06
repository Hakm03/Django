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

    def test_detalle_tiene_boton_imprimir_ticket(self):
        self.client.login(username='tk_user', password='pass')
        r = self.client.get(reverse('ventas:detalle', args=[self.venta.pk]))
        self.assertContains(r, self.url)
        self.assertContains(r, 'Imprimir ticket')
        # El botón anterior de la factura sigue ahí.
        self.assertContains(r, reverse('ventas:pdf', args=[self.venta.pk]))

"""Pruebas W13 — Catálogo público y carrito de compras.

Ejecutar con:
    python manage.py test tests.test_w13_ecommerce --verbosity=2
"""
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from productos.models import Categoria, Producto


class CatalogoPublicoTest(TestCase):
    """Catálogo accesible sin autenticación."""

    def setUp(self):
        cat = Categoria.objects.create(nombre='Electrónica')
        Producto.objects.create(
            nombre='Laptop', precio=Decimal('10000.00'), stock=5, categoria=cat)
        Producto.objects.create(
            nombre='Mouse', precio=Decimal('250.00'), stock=20, categoria=cat)
        Producto.objects.create(
            nombre='Producto Inactivo', precio=Decimal('100.00'),
            stock=5, categoria=cat, activo=False)

    def _nombres(self, params=None):
        r = self.client.get(reverse('catalogo:catalogo'), params or {})
        self.assertEqual(r.status_code, 200)
        return [p.nombre for p in r.context['productos']]

    def test_catalogo_accesible_sin_auth(self):
        r = self.client.get(reverse('catalogo:catalogo'))
        self.assertEqual(r.status_code, 200)

    def test_catalogo_solo_muestra_activos(self):
        nombres = self._nombres()
        self.assertIn('Laptop', nombres)
        self.assertNotIn('Producto Inactivo', nombres)

    def test_catalogo_filtro_por_nombre(self):
        nombres = self._nombres({'nombre': 'lapt'})
        self.assertIn('Laptop', nombres)
        self.assertNotIn('Mouse', nombres)

    def test_catalogo_filtro_por_precio_max(self):
        nombres = self._nombres({'precio_max': 500})
        self.assertIn('Mouse', nombres)
        self.assertNotIn('Laptop', nombres)


class CarritoTest(TestCase):
    """Carrito de compras en sesión."""

    def setUp(self):
        cat = Categoria.objects.create(nombre='Cat')
        self.prod = Producto.objects.create(
            nombre='Teclado', precio=Decimal('350.00'), stock=10, categoria=cat)
        self.url_agregar = reverse('catalogo:agregar', args=[self.prod.pk])

    def _items(self):
        return self.client.get(reverse('catalogo:carrito')).context['items']

    def test_carrito_vacio_al_inicio(self):
        self.assertEqual(self._items(), [])

    def test_agregar_producto_incrementa_carrito(self):
        self.client.post(self.url_agregar, {'cantidad': 2})
        items = self._items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['cantidad'], 2)

    def test_agregar_mismo_producto_acumula_cantidad(self):
        self.client.post(self.url_agregar, {'cantidad': 1})
        self.client.post(self.url_agregar, {'cantidad': 3})
        self.assertEqual(self._items()[0]['cantidad'], 4)

    def test_carrito_calcula_total_correcto(self):
        self.client.post(self.url_agregar, {'cantidad': 2})
        r = self.client.get(reverse('catalogo:carrito'))
        self.assertEqual(r.context['total'], Decimal('700.00'))

    def test_remover_producto_lo_elimina(self):
        self.client.post(self.url_agregar, {'cantidad': 1})
        self.client.post(reverse('catalogo:remover', args=[self.prod.pk]))
        self.assertEqual(self._items(), [])

    # ── Extras de seguridad / robustez ──
    def test_agregar_por_get_no_modifica_carrito(self):
        self.client.get(self.url_agregar)
        self.assertEqual(self._items(), [])

    def test_cantidad_no_numerica_no_rompe(self):
        r = self.client.post(self.url_agregar, {'cantidad': 'abc'})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(self._items()[0]['cantidad'], 1)

    def test_cantidad_no_supera_el_stock(self):
        self.client.post(self.url_agregar, {'cantidad': 500})
        self.assertEqual(self._items()[0]['cantidad'], 10)

    def test_next_externo_se_ignora(self):
        r = self.client.post(
            self.url_agregar, {'cantidad': 1, 'next': 'https://malo.example/'})
        self.assertEqual(r.url, reverse('catalogo:catalogo'))

    def test_actualizar_a_cero_elimina_y_vaciar_limpia(self):
        self.client.post(self.url_agregar, {'cantidad': 2})
        self.client.post(
            reverse('catalogo:actualizar', args=[self.prod.pk]), {'cantidad': 0})
        self.assertEqual(self._items(), [])
        self.client.post(self.url_agregar, {'cantidad': 1})
        self.client.post(reverse('catalogo:vaciar'))
        self.assertEqual(self._items(), [])

    def test_contador_navbar_en_contexto(self):
        self.client.post(self.url_agregar, {'cantidad': 3})
        r = self.client.get(reverse('catalogo:catalogo'))
        self.assertEqual(r.context['carrito_total_items'], 3)

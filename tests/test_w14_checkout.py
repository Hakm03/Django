"""Suite de pruebas W14 — Checkout y proceso de pago con Stripe.

Usa unittest.mock.patch para simular stripe.PaymentIntent.create
sin requerir claves reales ni conexión a internet.

Ejecutar con:
    python manage.py test tests.test_w14_checkout --verbosity=2

Resultado esperado:
    Ran 28 tests in X.XXXs
    OK
"""
from decimal import Decimal
from unittest.mock import MagicMock, patch

import stripe
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from catalogo.checkout_utils import (
    a_centavos, crear_pedido_pendiente, obtener_o_crear_cliente,
)
from clientes.models        import Cliente
from configuracion.models   import ConfiguracionERP
from productos.models       import Categoria, Producto
from ventas.models          import Pedido

# Claves falsas SOLO para tests: el checkout exige que empiecen con sk_/pk_.
# (No se usa ninguna clave real ni se llama a Stripe: PaymentIntent.create
# está mockeado.)
CLAVES_FALSAS = dict(STRIPE_SECRET_KEY='sk_test_fake',
                     STRIPE_PUBLISHABLE_KEY='pk_test_fake')


def _setup_carrito(client, producto):
    """Agrega un producto al carrito de la sesión del test client."""
    client.post(
        reverse('catalogo:agregar', args=[producto.pk]),
        {'cantidad': 2}
    )


def _total_esperado(subtotal: Decimal) -> Decimal:
    iva = ConfiguracionERP.get_instance().iva_porcentaje / 100
    return (subtotal + subtotal * iva).quantize(Decimal('0.01'))


class CheckoutAutenticacionTest(TestCase):
    """Tests de autenticación del checkout."""

    def test_checkout_sin_auth_redirige_a_login(self):
        """GET /catalogo/checkout/ sin login → 302 a /accounts/login/."""
        r = self.client.get(reverse('catalogo:checkout'))
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r['Location'])

    def test_checkout_carrito_vacio_redirige_a_catalogo(self):
        """Checkout con carrito vacío → redirect al catálogo."""
        user = User.objects.create_user('empty', password='pass')
        self.client.force_login(user)
        r = self.client.get(reverse('catalogo:checkout'))
        self.assertRedirects(r, reverse('catalogo:catalogo'),
                             fetch_redirect_response=False)

    def test_checkout_get_con_carrito_devuelve_200(self):
        """GET /catalogo/checkout/ con carrito → 200 y NO crea Pedido."""
        ConfiguracionERP.get_instance()
        cat  = Categoria.objects.create(nombre='Cat')
        prod = Producto.objects.create(
            nombre='P', precio=Decimal('100.00'),
            stock=5, categoria=cat
        )
        user = User.objects.create_user('userco', password='pass',
                                        email='userco@test.com')
        self.client.force_login(user)
        _setup_carrito(self.client, prod)
        r = self.client.get(reverse('catalogo:checkout'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Pedido.objects.count(), 0)


@override_settings(**CLAVES_FALSAS)
class CheckoutPagoTest(TestCase):
    """Tests del proceso POST de checkout con Stripe mockeado."""

    def setUp(self):
        cache.clear()
        ConfiguracionERP.get_instance()
        cat       = Categoria.objects.create(nombre='Cat')
        self.prod = Producto.objects.create(
            nombre='Laptop', precio=Decimal('500.00'),
            stock=5, categoria=cat
        )
        self.user = User.objects.create_user(
            'payer', password='pass', email='payer@test.com'
        )
        self.client.force_login(self.user)
        _setup_carrito(self.client, self.prod)   # 2 × 500 = 1000

    @patch('catalogo.views.stripe.PaymentIntent.create')
    def test_post_checkout_crea_pedido(self, mock_pi):
        """POST /catalogo/checkout/ → se crea un Pedido en BD."""
        mock_pi.return_value = MagicMock(id='pi_test_1', client_secret='pi_test_secret')
        self.client.post(reverse('catalogo:checkout'))
        self.assertEqual(Pedido.objects.count(), 1)

    @patch('catalogo.views.stripe.PaymentIntent.create')
    def test_post_checkout_pedido_estado_pendiente(self, mock_pi):
        """El Pedido creado debe tener estado 'pendiente'."""
        mock_pi.return_value = MagicMock(id='pi_test_1', client_secret='pi_test_secret')
        self.client.post(reverse('catalogo:checkout'))
        self.assertEqual(Pedido.objects.first().estado, 'pendiente')

    @patch('catalogo.views.stripe.PaymentIntent.create')
    def test_post_checkout_calcula_iva(self, mock_pi):
        """El total del Pedido debe incluir el IVA configurado."""
        mock_pi.return_value = MagicMock(id='pi_test_1', client_secret='pi_test_secret')
        self.client.post(reverse('catalogo:checkout'))
        self.assertEqual(Pedido.objects.first().total_pagado,
                         _total_esperado(Decimal('1000.00')))

    @patch('catalogo.views.stripe.PaymentIntent.create')
    def test_post_checkout_crea_cliente_erp(self, mock_pi):
        """Se debe crear (o encontrar) un Cliente ERP para el usuario."""
        mock_pi.return_value = MagicMock(id='pi_test_1', client_secret='pi_test_secret')
        self.client.post(reverse('catalogo:checkout'))
        self.assertTrue(
            Cliente.objects.filter(correo=self.user.email).exists()
        )

    @patch('catalogo.views.stripe.PaymentIntent.create')
    def test_post_checkout_llama_stripe_con_monto_correcto(self, mock_pi):
        """Stripe debe recibir el monto en centavos."""
        mock_pi.return_value = MagicMock(id='pi_test_1', client_secret='pi_test_secret')
        self.client.post(reverse('catalogo:checkout'))
        centavos = int(_total_esperado(Decimal('1000.00')) * 100)
        mock_pi.assert_called_once()
        self.assertEqual(mock_pi.call_args.kwargs['amount'], centavos)

    @patch('catalogo.views.stripe.PaymentIntent.create')
    def test_post_repetido_reutiliza_pedido(self, mock_pi):
        """Recargar / doble POST con el mismo carrito → UN solo Pedido."""
        mock_pi.return_value = MagicMock(id='pi_test_1', client_secret='pi_test_secret')
        self.client.post(reverse('catalogo:checkout'))
        self.client.post(reverse('catalogo:checkout'))
        self.assertEqual(Pedido.objects.count(), 1)

    @patch('catalogo.views.stripe.PaymentIntent.create')
    def test_precio_cambiado_no_se_cobra_en_silencio(self, mock_pi):
        """Si el precio cambia tras agregar al carrito: aviso + sin Pedido;
        al confirmar de nuevo se cobra el precio NUEVO."""
        mock_pi.return_value = MagicMock(id='pi_test_1', client_secret='pi_test_secret')
        Producto.objects.filter(pk=self.prod.pk).update(
            precio=Decimal('600.00'))

        r = self.client.post(reverse('catalogo:checkout'))
        self.assertEqual(r.status_code, 302)           # a revisar el resumen
        self.assertEqual(Pedido.objects.count(), 0)
        mock_pi.assert_not_called()

        self.client.post(reverse('catalogo:checkout'))  # ya revisado
        centavos = int(_total_esperado(Decimal('1200.00')) * 100)
        self.assertEqual(mock_pi.call_args.kwargs['amount'], centavos)

    @patch('catalogo.views.stripe.PaymentIntent.create')
    def test_stock_insuficiente_ajusta_carrito_sin_pedido(self, mock_pi):
        """Stock menor a lo pedido → ajusta carrito, no crea Pedido ni cobra."""
        Producto.objects.filter(pk=self.prod.pk).update(stock=1)
        r = self.client.post(reverse('catalogo:checkout'))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Pedido.objects.count(), 0)
        mock_pi.assert_not_called()
        carrito = self.client.session['carrito']
        self.assertEqual(carrito[str(self.prod.pk)]['cantidad'], 1)

    @patch('catalogo.views.stripe.PaymentIntent.create')
    def test_error_de_stripe_cancela_pedido_nuevo(self, mock_pi):
        """Stripe falla → redirect a pago_error y el Pedido queda 'cancelado'."""
        mock_pi.side_effect = stripe.error.StripeError('boom')
        r = self.client.post(reverse('catalogo:checkout'))
        self.assertRedirects(r, reverse('catalogo:pago_error'),
                             fetch_redirect_response=False)
        self.assertEqual(Pedido.objects.get().estado, 'cancelado')

    @patch('catalogo.views.stripe.PaymentIntent.create')
    def test_error_inesperado_no_filtra_detalle_al_usuario(self, mock_pi):
        """El texto de una excepción interna NO debe mostrarse al usuario."""
        mock_pi.side_effect = Exception('DETALLE-INTERNO-123')
        r = self.client.post(reverse('catalogo:checkout'), follow=True)
        self.assertNotContains(r, 'DETALLE-INTERNO-123')


class PagoExitosoTest(TestCase):
    """Tests de pago_exitoso: autorización + verificación real con Stripe."""

    def setUp(self):
        cache.clear()
        ConfiguracionERP.get_instance()
        cli = Cliente.objects.create(nombre='C', correo='c@t.com')
        self.pedido = Pedido.objects.create(
            numero_pedido='PED-2025-0001', cliente=cli,
            estado='pendiente', total_pagado=Decimal('116.00')
        )
        self.user = User.objects.create_user('dueno', password='pass')
        self.url  = reverse('catalogo:pago_exitoso', args=[self.pedido.pk])

    def _autorizar(self, con_intent=True):
        """Simula que ESTE usuario creó el pedido (y su PaymentIntent)."""
        self.client.force_login(self.user)
        sesion = self.client.session
        sesion['pedidos_checkout'] = [self.pedido.pk]
        if con_intent:
            sesion['intents_checkout'] = {str(self.pedido.pk): 'pi_test_1'}
        sesion['carrito'] = {'1': {'nombre': 'P', 'precio': '100',
                                   'cantidad': 1}}
        sesion.save()

    def _intent(self, status='succeeded', pedido_id=None, amount=11600):
        return MagicMock(
            status=status, amount=amount,
            metadata={'pedido_id': str(pedido_id or self.pedido.pk)})

    @patch('catalogo.views.stripe.PaymentIntent.retrieve')
    def test_intent_stripe_object_real_no_da_500(self, mock_get):
        """Regresión (stripe >= 15): retrieve() devuelve un StripeObject, no
        un dict ni un MagicMock. Antes: metadata.get() -> AttributeError -> 500."""
        mock_get.return_value = stripe.PaymentIntent.construct_from({
            'id': 'pi_test_1', 'object': 'payment_intent',
            'status': 'succeeded', 'amount': 11600,
            'metadata': {'pedido_id': str(self.pedido.pk)},
        }, 'sk_test_fake')
        self._autorizar()
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(self.client.session.get('carrito', {}), {})

    def test_sin_login_redirige_a_login(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r['Location'])

    def test_pedido_ajeno_devuelve_404(self):
        """Un usuario NO puede ver un pedido que no creó (cambiando la URL)."""
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.url).status_code, 404)

    @patch('catalogo.views.stripe.PaymentIntent.retrieve')
    def test_pago_verificado_devuelve_200_y_vacia_carrito(self, mock_get):
        mock_get.return_value = self._intent('succeeded')
        self._autorizar()
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(self.client.session.get('carrito', {}), {})

    @patch('catalogo.views.stripe.PaymentIntent.retrieve')
    def test_pago_en_proceso_tambien_se_acepta(self, mock_get):
        mock_get.return_value = self._intent('processing')
        self._autorizar()
        self.assertEqual(self.client.get(self.url).status_code, 200)

    @patch('catalogo.views.stripe.PaymentIntent.retrieve')
    def test_sin_pagar_no_vacia_carrito(self, mock_get):
        """Abrir la URL de éxito SIN haber pagado no sirve de nada."""
        mock_get.return_value = self._intent('requires_payment_method')
        self._autorizar()
        r = self.client.get(self.url)
        self.assertRedirects(r, reverse('catalogo:checkout'),
                             fetch_redirect_response=False)
        self.assertNotEqual(self.client.session.get('carrito', {}), {})

    def test_sin_payment_intent_registrado_no_vacia_carrito(self):
        self._autorizar(con_intent=False)
        r = self.client.get(self.url)
        self.assertRedirects(r, reverse('catalogo:checkout'),
                             fetch_redirect_response=False)
        self.assertNotEqual(self.client.session.get('carrito', {}), {})

    @patch('catalogo.views.stripe.PaymentIntent.retrieve')
    def test_error_de_stripe_al_verificar_no_vacia_carrito(self, mock_get):
        mock_get.side_effect = stripe.error.StripeError('boom')
        self._autorizar()
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 302)
        self.assertNotEqual(self.client.session.get('carrito', {}), {})

    @patch('catalogo.views.stripe.PaymentIntent.retrieve')
    def test_intent_de_otro_pedido_se_rechaza(self, mock_get):
        mock_get.return_value = self._intent('succeeded', pedido_id=999)
        self._autorizar()
        self.assertEqual(self.client.get(self.url).status_code, 302)

    @patch('catalogo.views.stripe.PaymentIntent.retrieve')
    def test_monto_distinto_se_rechaza(self, mock_get):
        mock_get.return_value = self._intent('succeeded', amount=100)
        self._autorizar()
        self.assertEqual(self.client.get(self.url).status_code, 302)

    @patch('catalogo.views.stripe.PaymentIntent.retrieve')
    def test_llegar_a_pago_exitoso_no_marca_pagado(self, mock_get):
        """Solo el webhook (W15) puede pasar el pedido a 'pagado'."""
        mock_get.return_value = self._intent('succeeded')
        self._autorizar()
        self.client.get(self.url)
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'pendiente')


@override_settings(**CLAVES_FALSAS)
class LimiteDeIntentosTest(TestCase):
    """El checkout limita los intentos de pago por usuario."""

    def setUp(self):
        cache.clear()
        ConfiguracionERP.get_instance()
        cat  = Categoria.objects.create(nombre='Cat')
        prod = Producto.objects.create(
            nombre='P', precio=Decimal('500.00'), stock=5, categoria=cat)
        user = User.objects.create_user('spam', password='pass',
                                        email='spam@test.com')
        self.client.force_login(user)
        _setup_carrito(self.client, prod)

    @patch('catalogo.views.stripe.PaymentIntent.create')
    def test_el_intento_11_recibe_429(self, mock_pi):
        mock_pi.return_value = MagicMock(
            id='pi_test_1', client_secret='pi_test_secret')
        url = reverse('catalogo:checkout')
        for _ in range(10):
            self.assertEqual(self.client.post(url).status_code, 200)
        r = self.client.post(url)
        self.assertEqual(r.status_code, 429)
        self.assertEqual(mock_pi.call_count, 10)    # el 11.º no llegó a Stripe

    def test_dentro_del_limite_cuenta_y_corta(self):
        from catalogo.checkout_utils import dentro_del_limite
        resultados = [dentro_del_limite('prueba:1', maximo=3) for _ in range(5)]
        self.assertEqual(resultados, [True, True, True, False, False])


class CheckoutUtilsTest(TestCase):
    """Tests de las funciones auxiliares."""

    def test_numero_pedido_no_se_repite_tras_borrar(self):
        cli = Cliente.objects.create(nombre='C', correo='u@t.com')
        crear_pedido_pendiente(cli, Decimal('10.00'))
        p2 = crear_pedido_pendiente(cli, Decimal('10.00'))
        Pedido.objects.exclude(pk=p2.pk).delete()      # se borra el primero
        p3 = crear_pedido_pendiente(cli, Decimal('10.00'))
        self.assertNotEqual(p3.numero_pedido, p2.numero_pedido)
        self.assertTrue(p3.numero_pedido.endswith('-0003'))

    def test_a_centavos_redondea_hacia_arriba(self):
        self.assertEqual(a_centavos(Decimal('10.005')), 1001)
        self.assertEqual(a_centavos(Decimal('1160.00')), 116000)

    def test_no_modifica_cliente_existente(self):
        """Un usuario con el correo de un Cliente real NO puede renombrarlo."""
        Cliente.objects.create(nombre='Cliente Real', correo='real@t.com')
        intruso = User.objects.create_user(
            'intruso', email='REAL@t.com', first_name='Otro', password='x')
        cliente = obtener_o_crear_cliente(intruso)
        self.assertEqual(cliente.nombre, 'Cliente Real')
        self.assertEqual(Cliente.objects.count(), 1)

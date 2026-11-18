"""Suite de pruebas W15 — Webhook de Stripe y lógica de pedidos.

Usa unittest.mock.patch para simular stripe.Webhook.construct_event
sin requerir claves reales ni conexión a Stripe.

Ejecutar con:
    python manage.py test tests.test_w15_webhooks --verbosity=2
"""
from decimal import Decimal
from unittest.mock import MagicMock, patch

import stripe
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from catalogo.checkout_utils import a_centavos
from clientes.models import Cliente
from configuracion.models import ConfiguracionERP
from productos.models import Categoria, Producto
from ventas.models import Pedido

CONSTRUCT = 'catalogo.webhook_views.stripe.Webhook.construct_event'
TOTAL = Decimal('1000.00')


def _crear_evento(tipo: str, pedido_id: int, monto: int = None) -> dict:
    """Construye un evento Stripe simulado (monto por defecto = TOTAL)."""
    return {
        'type': tipo,
        'data': {
            'object': {
                'id':       f'pi_test_{pedido_id}',
                'amount':   a_centavos(TOTAL) if monto is None else monto,
                'currency': 'mxn',
                'status':   'succeeded' if 'succeeded' in tipo else 'failed',
                'metadata': {'pedido_id': str(pedido_id)},
            }
        }
    }


def _crear_pedido_con_snapshot(cliente, producto, cantidad=2) -> Pedido:
    return Pedido.objects.create(
        numero_pedido='PED-2025-TEST',
        cliente=cliente,
        estado='pendiente',
        total_pagado=TOTAL,
        items_snapshot=[{
            'producto_id': producto.pk,
            'nombre':      producto.nombre,
            'cantidad':    cantidad,
            'precio':      str(producto.precio),
        }],
    )


def _post(client):
    return client.post(
        reverse('catalogo:webhook'),
        data=b'{}',
        content_type='application/json',
        HTTP_STRIPE_SIGNATURE='t=123,v1=ok',
    )


@override_settings(STRIPE_WEBHOOK_SECRET='whsec_test')
class WebhookSeguridadTest(TestCase):
    """Seguridad del endpoint."""

    def test_get_rechazado_con_405(self):
        r = self.client.get(reverse('catalogo:webhook'))
        self.assertEqual(r.status_code, 405)

    @patch(CONSTRUCT)
    def test_firma_invalida_devuelve_400(self, mock_construct):
        mock_construct.side_effect = stripe.SignatureVerificationError(
            'Test error', 'sig_header')
        self.assertEqual(_post(self.client).status_code, 400)

    @patch(CONSTRUCT)
    def test_payload_invalido_devuelve_400(self, mock_construct):
        mock_construct.side_effect = ValueError('JSON inválido')
        self.assertEqual(_post(self.client).status_code, 400)

    @override_settings(STRIPE_WEBHOOK_SECRET='')
    @patch(CONSTRUCT)
    def test_secreto_vacio_devuelve_500(self, mock_construct):
        """Sin STRIPE_WEBHOOK_SECRET → 500 y no se intenta verificar nada."""
        with self.assertLogs('catalogo.webhook_views', level='ERROR'):
            r = _post(self.client)
        self.assertEqual(r.status_code, 500)
        mock_construct.assert_not_called()


@override_settings(STRIPE_WEBHOOK_SECRET='whsec_test')
class WebhookPagoExitosoTest(TestCase):
    """payment_intent.succeeded."""

    def setUp(self):
        ConfiguracionERP.get_instance()
        cat = Categoria.objects.create(nombre='Cat')
        self.prod = Producto.objects.create(
            nombre='P', precio=Decimal('500.00'), stock=10, categoria=cat)
        self.cli = Cliente.objects.create(nombre='C', correo='c@t.com')
        self.pedido = _crear_pedido_con_snapshot(self.cli, self.prod, 2)

    @patch(CONSTRUCT)
    def test_actualiza_estado(self, mock_construct):
        mock_construct.return_value = _crear_evento(
            'payment_intent.succeeded', self.pedido.pk)
        self.assertEqual(_post(self.client).status_code, 200)
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'pagado')

    @patch(CONSTRUCT)
    def test_descuenta_stock(self, mock_construct):
        mock_construct.return_value = _crear_evento(
            'payment_intent.succeeded', self.pedido.pk)
        _post(self.client)
        self.prod.refresh_from_db()
        self.assertEqual(self.prod.stock, 8)

    @patch(CONSTRUCT)
    def test_idempotente_pedido_ya_pagado(self, mock_construct):
        self.pedido.estado = 'pagado'
        self.pedido.save()
        mock_construct.return_value = _crear_evento(
            'payment_intent.succeeded', self.pedido.pk)
        _post(self.client)
        self.prod.refresh_from_db()
        self.assertEqual(self.prod.stock, 10)

    @patch(CONSTRUCT)
    def test_evento_duplicado_descuenta_stock_una_sola_vez(self, mock_construct):
        """El mismo evento entregado dos veces → stock baja solo una vez."""
        mock_construct.return_value = _crear_evento(
            'payment_intent.succeeded', self.pedido.pk)
        self.assertEqual(_post(self.client).status_code, 200)
        self.assertEqual(_post(self.client).status_code, 200)
        self.prod.refresh_from_db()
        self.assertEqual(self.prod.stock, 8)

    @patch(CONSTRUCT)
    def test_monto_distinto_no_marca_pagado(self, mock_construct):
        """Si Stripe cobró un monto distinto al del pedido → no se paga."""
        mock_construct.return_value = _crear_evento(
            'payment_intent.succeeded', self.pedido.pk, monto=100)
        with self.assertLogs('catalogo.webhook_views', level='ERROR'):
            r = _post(self.client)
        self.assertEqual(r.status_code, 200)
        self.pedido.refresh_from_db()
        self.prod.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'pendiente')
        self.assertEqual(self.prod.stock, 10)

    @patch(CONSTRUCT)
    def test_stock_insuficiente_no_queda_negativo(self, mock_construct):
        """Si falta stock, el pedido se paga pero el stock no baja de 0."""
        Producto.objects.filter(pk=self.prod.pk).update(stock=1)
        mock_construct.return_value = _crear_evento(
            'payment_intent.succeeded', self.pedido.pk)
        with self.assertLogs('catalogo.webhook_views', level='WARNING'):
            _post(self.client)
        self.prod.refresh_from_db()
        self.assertEqual(self.prod.stock, 1)


@override_settings(STRIPE_WEBHOOK_SECRET='whsec_test')
class WebhookPagoFallidoTest(TestCase):
    """payment_intent.payment_failed."""

    def setUp(self):
        cat = Categoria.objects.create(nombre='Cat')
        self.prod = Producto.objects.create(
            nombre='P', precio=Decimal('100.00'), stock=5, categoria=cat)
        cli = Cliente.objects.create(nombre='C', correo='c2@t.com')
        self.pedido = _crear_pedido_con_snapshot(cli, self.prod)

    @patch(CONSTRUCT)
    def test_cancela_pedido_pendiente(self, mock_construct):
        mock_construct.return_value = _crear_evento(
            'payment_intent.payment_failed', self.pedido.pk)
        self.assertEqual(_post(self.client).status_code, 200)
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'cancelado')

    @patch(CONSTRUCT)
    def test_no_cancela_pedido_ya_pagado(self, mock_construct):
        """Un fallo tardío no debe cancelar un pedido ya pagado."""
        self.pedido.estado = 'pagado'
        self.pedido.save()
        mock_construct.return_value = _crear_evento(
            'payment_intent.payment_failed', self.pedido.pk)
        _post(self.client)
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'pagado')


@override_settings(STRIPE_WEBHOOK_SECRET='whsec_test')
class WebhookStripeObjectTest(TestCase):
    """Regresión: con stripe >= 15 el evento real es un StripeObject."""

    def setUp(self):
        cat = Categoria.objects.create(nombre='Cat')
        self.prod = Producto.objects.create(
            nombre='P', precio=Decimal('500.00'), stock=10, categoria=cat)
        cli = Cliente.objects.create(nombre='C', correo='c3@t.com')
        self.pedido = _crear_pedido_con_snapshot(cli, self.prod, 2)

    @patch(CONSTRUCT)
    def test_evento_stripe_object_real(self, mock_construct):
        datos = _crear_evento('payment_intent.succeeded', self.pedido.pk)
        datos['data']['object']['object'] = 'payment_intent'
        datos.update({'id': 'evt_test', 'object': 'event'})
        mock_construct.return_value = stripe.Event.construct_from(
            datos, 'sk_test')

        self.assertEqual(_post(self.client).status_code, 200)
        self.pedido.refresh_from_db()
        self.prod.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'pagado')
        self.assertEqual(self.prod.stock, 8)


class CheckoutGuardaSnapshotTest(TestCase):
    """El checkout debe guardar el snapshot que el webhook necesita."""

    @override_settings(STRIPE_SECRET_KEY='sk_test_fake',
                       STRIPE_PUBLISHABLE_KEY='pk_test_fake')
    @patch('catalogo.views.stripe.PaymentIntent.create')
    def test_checkout_guarda_items_snapshot(self, mock_pi):
        ConfiguracionERP.get_instance()
        cat = Categoria.objects.create(nombre='Cat')
        prod = Producto.objects.create(
            nombre='Prod', precio=Decimal('500.00'), stock=5, categoria=cat)
        user = User.objects.create_user('snap', password='pass',
                                        email='snap@test.com')
        self.client.force_login(user)
        self.client.post(reverse('catalogo:agregar', args=[prod.pk]),
                         {'cantidad': 2})
        mock_pi.return_value = MagicMock(id='pi_snap',
                                         client_secret='pi_snap_secret')
        self.client.post(reverse('catalogo:checkout'))

        pedido = Pedido.objects.get()
        self.assertEqual(pedido.items_snapshot, [{
            'producto_id': prod.pk,
            'nombre':      'Prod',
            'cantidad':    2,
            'precio':      '500.00',
        }])

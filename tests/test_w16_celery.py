"""Suite de pruebas W16 — Celery y tareas asíncronas.

No requiere Redis ni Docker: sin REDIS_URL, settings.py activa el modo EAGER.

Ejecutar con:
    python manage.py test tests.test_w16_celery --verbosity=2
"""
from decimal import Decimal
from unittest.mock import patch

import stripe
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from catalogo.checkout_utils import a_centavos
from clientes.models import Cliente
from configuracion.models import ConfiguracionERP
from productos.models import Categoria, Producto
from ventas.models import Pedido
from ventas.tasks import enviar_confirmacion_pedido, verificar_stock_bajo

CONSTRUCT = 'catalogo.webhook_views.stripe.Webhook.construct_event'
DELAY = 'catalogo.webhook_views.enviar_confirmacion_pedido.delay'
TOTAL = Decimal('100.00')


class CeleryConfigTest(TestCase):
    """Celery está configurado y las tareas registradas."""

    def test_celery_app_importable(self):
        from core.celery import app as celery_app
        self.assertEqual(celery_app.main, 'core')

    def test_tareas_registradas_en_celery(self):
        from core.celery import app as celery_app
        self.assertIn('ventas.enviar_confirmacion_pedido', celery_app.tasks)
        self.assertIn('ventas.verificar_stock_bajo', celery_app.tasks)

    def test_sin_redis_url_usa_modo_eager(self):
        from django.conf import settings
        if settings.REDIS_URL:
            self.skipTest('REDIS_URL definida: entorno con Redis.')
        self.assertTrue(settings.CELERY_TASK_ALWAYS_EAGER)
        self.assertEqual(settings.CELERY_BROKER_URL, 'memory://')


class TareasTest(TestCase):
    """Lógica de las tareas (modo EAGER)."""

    def setUp(self):
        ConfiguracionERP.get_instance()
        cat = Categoria.objects.create(nombre='Cat')
        Producto.objects.create(
            nombre='P', precio=Decimal('100.00'), stock=3, categoria=cat)
        cli = Cliente.objects.create(nombre='C', correo='c@t.com')
        self.pedido = Pedido.objects.create(
            numero_pedido='PED-2025-0001', cliente=cli,
            estado='pagado', total_pagado=Decimal('116.00'))

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_confirmacion_retorna_ok(self):
        data = enviar_confirmacion_pedido.delay(self.pedido.pk).get()
        self.assertEqual(data['estado'], 'ok')
        self.assertEqual(data['pedido_id'], self.pedido.pk)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_confirmacion_pedido_inexistente_retorna_error(self):
        data = enviar_confirmacion_pedido.delay(9999).get()
        self.assertEqual(data['estado'], 'error')

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_verificar_stock_bajo_detecta_productos(self):
        data = verificar_stock_bajo.delay(umbral=5).get()
        self.assertGreaterEqual(data['total'], 1)
        self.assertIn('P', [p['nombre'] for p in data['productos_bajos']])

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_verificar_stock_bajo_ignora_inactivos(self):
        """Extra: un producto inactivo no debe disparar alerta."""
        Producto.objects.filter(nombre='P').update(activo=False)
        data = verificar_stock_bajo.delay(umbral=5).get()
        self.assertEqual(data['total'], 0)


@override_settings(STRIPE_WEBHOOK_SECRET='whsec_test')
class TareaDesdeVistasTest(TestCase):
    """Qué puntos encolan la tarea con .delay()."""

    def setUp(self):
        ConfiguracionERP.get_instance()
        Categoria.objects.create(nombre='Cat')
        cli = Cliente.objects.create(nombre='C', correo='test@test.com')
        self.pedido = Pedido.objects.create(
            numero_pedido='PED-2025-VISTA', cliente=cli,
            estado='pendiente', total_pagado=TOTAL, items_snapshot=[])
        self.user = User.objects.create_user('viewer', password='pass')

    def _evento(self):
        return {
            'type': 'payment_intent.succeeded',
            'data': {'object': {
                'id': 'pi_test',
                'amount': a_centavos(TOTAL),
                'metadata': {'pedido_id': str(self.pedido.pk)},
            }},
        }

    def _post(self):
        return self.client.post(
            reverse('catalogo:webhook'), data=b'{}',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=1,v1=ok')

    @patch('catalogo.views._pago_verificado', return_value=True)
    @patch('ventas.tasks.enviar_confirmacion_pedido.delay')
    def test_pago_exitoso_no_encola_tarea(self, mock_delay, _verificado):
        """pago_exitoso() NO encola: el webhook es el único disparo."""
        self.client.force_login(self.user)
        sesion = self.client.session
        sesion['pedidos_checkout'] = [self.pedido.pk]
        sesion.save()
        r = self.client.get(
            reverse('catalogo:pago_exitoso', args=[self.pedido.pk]))
        self.assertEqual(r.status_code, 200)
        mock_delay.assert_not_called()

    @patch(DELAY)
    @patch(CONSTRUCT)
    def test_webhook_succeeded_llama_a_delay(self, mock_event, mock_delay):
        mock_event.return_value = self._evento()
        self.assertEqual(self._post().status_code, 200)
        mock_delay.assert_called_once_with(self.pedido.pk)

    @patch(DELAY)
    @patch(CONSTRUCT)
    def test_webhook_duplicado_encola_una_sola_vez(self, mock_event, mock_delay):
        """Extra: Stripe reenvía el evento → un solo correo."""
        mock_event.return_value = self._evento()
        self._post()
        self._post()
        self.assertEqual(mock_delay.call_count, 1)

    @patch(DELAY, side_effect=ConnectionError('Redis caído'))
    @patch(CONSTRUCT)
    def test_webhook_responde_200_aunque_redis_falle(self, mock_event, _):
        mock_event.return_value = self._evento()
        with self.assertLogs('catalogo.webhook_views', level='ERROR'):
            r = self._post()
        self.assertEqual(r.status_code, 200)
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'pagado')

    @patch(DELAY)
    @patch(CONSTRUCT)
    def test_webhook_monto_distinto_no_encola(self, mock_event, mock_delay):
        """Extra: monto que no coincide → no se marca pagado ni se encola."""
        evento = self._evento()
        evento['data']['object']['amount'] = 1
        mock_event.return_value = evento
        self._post()
        mock_delay.assert_not_called()
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'pendiente')

"""Suite de pruebas W17 — correo real (django-anymail + SendGrid).

No envía nada: el runner de tests usa el backend locmem (mail.outbox) y
no requiere Redis (modo EAGER).

Ejecutar con:
    python manage.py test tests.test_w17_correo --verbosity=2
"""
from decimal import Decimal
from importlib import import_module
from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from catalogo.checkout_utils import a_centavos
from clientes.models import Cliente
from configuracion.models import ConfiguracionERP
from productos.models import Categoria, Producto
from ventas.models import Pedido
from ventas.tasks import enviar_confirmacion_pedido, verificar_stock_bajo

CONSTRUCT = 'catalogo.webhook_views.stripe.Webhook.construct_event'
TOTAL = Decimal('116.00')


def _crear_pedido(correo='cliente@test.com', estado='pagado', snapshot=None):
    cli = Cliente.objects.create(nombre='Ana', correo=correo)
    return Pedido.objects.create(
        numero_pedido='PED-2025-0777', cliente=cli, estado=estado,
        total_pagado=TOTAL,
        items_snapshot=snapshot if snapshot is not None else [
            {'producto_id': 1, 'nombre': 'Taza azul',
             'cantidad': 2, 'precio': '50.00'},
        ],
    )


class ConfigCorreoTest(TestCase):
    """El conector de SendGrid está disponible y hay remitente por defecto."""

    def test_backend_sendgrid_de_anymail_importable(self):
        modulo = import_module('anymail.backends.sendgrid')
        self.assertTrue(hasattr(modulo, 'EmailBackend'))

    def test_remitente_por_defecto_definido(self):
        from django.conf import settings
        self.assertTrue(settings.DEFAULT_FROM_EMAIL)

    def test_campo_correo_enviado_inicia_en_false(self):
        self.assertFalse(_crear_pedido().correo_enviado)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True,
                   DEFAULT_FROM_EMAIL='ERP Django <tienda@test.com>')
class ReciboTest(TestCase):
    """enviar_confirmacion_pedido: contenido, idempotencia y errores."""

    def setUp(self):
        ConfiguracionERP.get_instance()

    def test_envia_recibo_al_cliente(self):
        pedido = _crear_pedido()
        data = enviar_confirmacion_pedido.delay(pedido.pk).get()
        self.assertEqual(data['estado'], 'ok')
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.to, ['cliente@test.com'])
        self.assertEqual(msg.from_email, 'ERP Django <tienda@test.com>')
        self.assertIn('PED-2025-0777', msg.subject)
        self.assertIn('Taza azul', msg.body)
        self.assertIn('116.00', msg.body)

    def test_marca_correo_enviado(self):
        pedido = _crear_pedido()
        enviar_confirmacion_pedido.delay(pedido.pk).get()
        pedido.refresh_from_db()
        self.assertTrue(pedido.correo_enviado)

    def test_idempotente_no_envia_dos_veces(self):
        pedido = _crear_pedido()
        enviar_confirmacion_pedido.delay(pedido.pk).get()
        segunda = enviar_confirmacion_pedido.delay(pedido.pk).get()
        self.assertEqual(segunda['estado'], 'omitido')
        self.assertEqual(len(mail.outbox), 1)

    def test_pedido_inexistente_no_envia(self):
        data = enviar_confirmacion_pedido.delay(9999).get()
        self.assertEqual(data['estado'], 'error')
        self.assertEqual(len(mail.outbox), 0)

    def test_cliente_sin_correo_no_envia(self):
        pedido = _crear_pedido(correo='')
        data = enviar_confirmacion_pedido.delay(pedido.pk).get()
        self.assertEqual(data['estado'], 'sin_correo')
        self.assertEqual(len(mail.outbox), 0)

    def test_pedido_sin_items_igual_envia(self):
        pedido = _crear_pedido(snapshot=[])
        data = enviar_confirmacion_pedido.delay(pedido.pk).get()
        self.assertEqual(data['estado'], 'ok')
        self.assertNotIn('Detalle:', mail.outbox[0].body)

    def test_fallo_del_proveedor_no_marca_como_enviado(self):
        """Si SendGrid falla: se reintenta y NO se marca correo_enviado."""
        pedido = _crear_pedido()
        with patch('ventas.tasks.send_mail',
                   side_effect=ConnectionError('SendGrid caído')), \
             patch.object(enviar_confirmacion_pedido, 'retry',
                          side_effect=RuntimeError('reintento')), \
             self.assertLogs('ventas.tasks', level='ERROR'):
            with self.assertRaises(RuntimeError):
                enviar_confirmacion_pedido.apply(args=[pedido.pk])
        pedido.refresh_from_db()
        self.assertFalse(pedido.correo_enviado)
        self.assertEqual(len(mail.outbox), 0)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True,
                   ADMIN_EMAIL='admin@test.com')
class AlertaStockTest(TestCase):
    """verificar_stock_bajo: avisa al admin solo cuando corresponde."""

    def setUp(self):
        ConfiguracionERP.get_instance()
        self.cat = Categoria.objects.create(nombre='Cat')

    def _producto(self, nombre, stock, activo=True):
        return Producto.objects.create(
            nombre=nombre, precio=Decimal('10.00'), stock=stock,
            categoria=self.cat, activo=activo)

    def test_envia_alerta_con_productos_bajos(self):
        self._producto('Lapiz', 2)
        self._producto('Libreta', 50)
        data = verificar_stock_bajo.delay(umbral=5).get()
        self.assertTrue(data['correo_enviado'])
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['admin@test.com'])
        self.assertIn('Lapiz', mail.outbox[0].body)
        self.assertNotIn('Libreta', mail.outbox[0].body)

    def test_sin_productos_bajos_no_envia(self):
        self._producto('Libreta', 50)
        data = verificar_stock_bajo.delay(umbral=5).get()
        self.assertFalse(data['correo_enviado'])
        self.assertEqual(len(mail.outbox), 0)

    def test_producto_inactivo_no_dispara_alerta(self):
        self._producto('Descontinuado', 0, activo=False)
        verificar_stock_bajo.delay(umbral=5).get()
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(ADMIN_EMAIL='')
    def test_sin_admin_email_no_envia(self):
        self._producto('Lapiz', 1)
        data = verificar_stock_bajo.delay(umbral=5).get()
        self.assertEqual(data['total'], 1)
        self.assertFalse(data['correo_enviado'])
        self.assertEqual(len(mail.outbox), 0)


@override_settings(STRIPE_WEBHOOK_SECRET='whsec_test',
                   CELERY_TASK_ALWAYS_EAGER=True)
class RecibosDesdeWebhookTest(TestCase):
    """Extremo a extremo (modo EAGER): webhook de Stripe → correo."""

    def setUp(self):
        ConfiguracionERP.get_instance()
        self.pedido = _crear_pedido(estado='pendiente', snapshot=[])

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

    @patch(CONSTRUCT)
    def test_webhook_pagado_envia_un_recibo(self, mock_event):
        mock_event.return_value = self._evento()
        self.assertEqual(self._post().status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['cliente@test.com'])
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'pagado')
        self.assertTrue(self.pedido.correo_enviado)

    @patch(CONSTRUCT)
    def test_webhook_duplicado_no_duplica_el_recibo(self, mock_event):
        mock_event.return_value = self._evento()
        self._post()
        self._post()
        self.assertEqual(len(mail.outbox), 1)

    @patch(CONSTRUCT)
    def test_monto_distinto_no_envia_recibo(self, mock_event):
        evento = self._evento()
        evento['data']['object']['amount'] = 1
        mock_event.return_value = evento
        self._post()
        self.assertEqual(len(mail.outbox), 0)

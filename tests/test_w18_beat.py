"""Suite de pruebas W18 — Celery Beat y reporte diario de ventas.

No envía nada: el runner usa locmem (mail.outbox) y modo EAGER.

Ejecutar con:
    python manage.py test tests.test_w18_beat --verbosity=2
"""
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from celery.schedules import crontab
from django.conf import settings
from django.core import mail
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from clientes.models import Cliente
from configuracion.models import ConfiguracionERP
from productos.models import Categoria, Producto
from ventas.models import DetalleVenta, Pedido, Venta
from ventas.tasks import reporte_ventas_diario, verificar_stock_bajo

ADMIN = 'admin@test.com'
AYER = lambda: timezone.now() - timedelta(days=1)   # noqa: E731


def _cliente():
    return Cliente.objects.create(nombre='Cli', correo='cli@test.com')


def _pedido(num, total, items=None, estado='pagado', cuando=None):
    """Crea un pedido; fecha_pedido es auto_now_add, se fija con update()."""
    p = Pedido.objects.create(
        numero_pedido=num, cliente=_cliente_unico(), estado=estado,
        total_pagado=Decimal(total), items_snapshot=items or [])
    Pedido.objects.filter(pk=p.pk).update(fecha_pedido=cuando or AYER())
    return p


def _cliente_unico():
    return Cliente.objects.get_or_create(
        correo='cli@test.com', defaults={'nombre': 'Cli'})[0]


class ConfigBeatTest(SimpleTestCase):

    def test_schedule_tiene_las_dos_tareas(self):
        tareas = {v['task'] for v in settings.CELERY_BEAT_SCHEDULE.values()}
        self.assertEqual(tareas, {'ventas.verificar_stock_bajo',
                                  'ventas.reporte_ventas_diario'})

    def test_ambas_usan_crontab_diario(self):
        for nombre, cfg in settings.CELERY_BEAT_SCHEDULE.items():
            self.assertIsInstance(cfg['schedule'], crontab, nombre)

    def test_hora_del_reporte_sale_de_la_variable(self):
        h, m = (int(x) for x in settings.REPORTE_DIARIO_HORA.split(':'))
        cron = settings.CELERY_BEAT_SCHEDULE['reporte-ventas-diario']['schedule']
        self.assertEqual((cron.hour, cron.minute), ({h}, {m}))

    def test_zona_horaria_es_mexico(self):
        self.assertEqual(settings.CELERY_BEAT_TIMEZONE, 'America/Mexico_City')

    def test_hora_invalida_vuelve_al_defecto(self):
        from core.settings import _hora_hhmm
        self.assertEqual(_hora_hhmm('10:30', (8, 0)), (10, 30))
        for malo in ('abc', '25:00', '8', '10:99', ''):
            self.assertEqual(_hora_hhmm(malo, (8, 0)), (8, 0), malo)

    def test_las_tareas_programadas_existen_en_celery(self):
        from core.celery import app
        app.loader.import_default_modules()
        for cfg in settings.CELERY_BEAT_SCHEDULE.values():
            self.assertIn(cfg['task'], app.tasks)

    def test_entrypoint_arranca_beat_y_tiene_saltos_lf(self):
        ruta = Path(settings.BASE_DIR) / 'docker-entrypoint.sh'
        crudo = ruta.read_bytes()
        self.assertIn(b'--beat', crudo)
        self.assertIn(b'CELERY_EMBEDDED_BEAT', crudo)
        self.assertNotIn(b'\r\n', crudo, 'El script debe usar saltos LF')


@override_settings(ADMIN_EMAIL=ADMIN, SITE_URL='https://erp.example.com',
                   DEFAULT_FROM_EMAIL='ERP <no-reply@test.com>')
class ReporteDiarioTest(TestCase):

    def setUp(self):
        mail.outbox = []
        ConfiguracionERP.get_instance()

    def test_con_ventas_de_ayer_envia_un_correo_al_admin(self):
        _pedido('PED-1', '116.00', [
            {'nombre': 'Vino Tinto', 'cantidad': 2, 'precio': '58.00'}])
        res = reporte_ventas_diario.apply().get()
        self.assertTrue(res['correo_enviado'])
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.to, [ADMIN])
        self.assertIn((timezone.localdate() - timedelta(days=1))
                      .strftime('%d/%m/%Y'), msg.subject)
        self.assertIn('Vino Tinto', msg.body)
        self.assertIn('116.00', msg.body)
        self.assertIn('https://erp.example.com/admin/ventas/pedido/', msg.body)
        self.assertEqual(msg.alternatives[0][1], 'text/html')

    def test_sin_ventas_no_envia_correo(self):
        res = reporte_ventas_diario.apply().get()
        self.assertEqual(res['total_pedidos'], 0)
        self.assertFalse(res['correo_enviado'])
        self.assertEqual(len(mail.outbox), 0)

    def test_pedido_de_hoy_no_cuenta_en_el_reporte_de_ayer(self):
        _pedido('PED-HOY', '50.00', cuando=timezone.now())
        reporte_ventas_diario.apply().get()
        self.assertEqual(len(mail.outbox), 0)

    def test_pedido_pendiente_no_cuenta(self):
        _pedido('PED-PEND', '50.00', estado='pendiente')
        reporte_ventas_diario.apply().get()
        self.assertEqual(len(mail.outbox), 0)

    def test_forzar_envia_aunque_no_haya_ventas(self):
        res = reporte_ventas_diario.apply(kwargs={'forzar': True}).get()
        self.assertTrue(res['correo_enviado'])
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Sin ventas', mail.outbox[0].alternatives[0][0])

    @override_settings(ADMIN_EMAIL='')
    def test_sin_admin_email_no_envia(self):
        _pedido('PED-2', '10.00')
        res = reporte_ventas_diario.apply().get()
        self.assertFalse(res['correo_enviado'])
        self.assertEqual(len(mail.outbox), 0)

    def test_totales_suman_varios_pedidos(self):
        _pedido('PED-A', '100.50')
        _pedido('PED-B', '20.25')
        res = reporte_ventas_diario.apply().get()
        self.assertEqual(res['total_pedidos'], 2)
        self.assertEqual(res['total_facturado'], '120.75')

    def test_top_suma_tienda_en_linea_y_ventas_internas(self):
        cat = Categoria.objects.create(nombre='C')
        prod = Producto.objects.create(
            nombre='Queso', precio=Decimal('30.00'), stock=50, categoria=cat)
        venta = Venta.objects.create(cliente=_cliente_unico())
        Venta.objects.filter(pk=venta.pk).update(fecha=AYER())
        DetalleVenta.objects.create(venta=venta, producto=prod, cantidad=3,
                                    precio_unitario=Decimal('30.00'))
        _pedido('PED-W', '60.00', [
            {'nombre': 'Queso', 'cantidad': 2, 'precio': '30.00'}])
        res = reporte_ventas_diario.apply().get()
        self.assertEqual(res['top_productos'],
                         [{'nombre': 'Queso', 'unidades': 5,
                           'ingreso': '150.00'}])

    def test_top_se_limita_a_cinco_y_ordena_por_ingreso(self):
        items = [{'nombre': f'P{i}', 'cantidad': 1, 'precio': str(i * 10)}
                 for i in range(1, 8)]
        _pedido('PED-X', '280.00', items)
        top = reporte_ventas_diario.apply().get()['top_productos']
        self.assertEqual(len(top), 5)
        self.assertEqual(top[0]['nombre'], 'P7')

    def test_item_con_precio_roto_no_rompe_el_reporte(self):
        _pedido('PED-R', '10.00', [
            {'nombre': 'Raro', 'cantidad': 'x', 'precio': 'abc'}])
        res = reporte_ventas_diario.apply().get()
        self.assertTrue(res['correo_enviado'])

    def test_html_escapa_nombres_de_producto(self):
        _pedido('PED-E', '10.00', [
            {'nombre': '<script>x</script>', 'cantidad': 1, 'precio': '10'}])
        reporte_ventas_diario.apply().get()
        html = mail.outbox[0].alternatives[0][0]
        self.assertNotIn('<script>x', html)
        self.assertIn('&lt;script&gt;', html)

    def test_falla_del_proveedor_reintenta_y_registra_error(self):
        _pedido('PED-F', '10.00')
        with patch('ventas.tasks.send_mail',
                   side_effect=ConnectionError('SendGrid caído')), \
             patch.object(reporte_ventas_diario, 'retry',
                          side_effect=RuntimeError('reintento')), \
             self.assertLogs('ventas.tasks', level='ERROR'):
            with self.assertRaises(RuntimeError):
                reporte_ventas_diario.apply(throw=True)
        self.assertEqual(len(mail.outbox), 0)


@override_settings(ADMIN_EMAIL=ADMIN)
class AlertaStockProgramadaTest(TestCase):
    """La alerta diaria solo manda correo si hay productos bajos."""

    def setUp(self):
        mail.outbox = []
        self.cat = Categoria.objects.create(nombre='C')

    def test_sin_productos_bajos_no_envia(self):
        Producto.objects.create(nombre='Lleno', precio=Decimal('1'),
                                stock=50, categoria=self.cat)
        res = verificar_stock_bajo.apply(args=[5]).get()
        self.assertFalse(res['correo_enviado'])
        self.assertEqual(len(mail.outbox), 0)

    def test_con_producto_bajo_envia_un_solo_correo(self):
        Producto.objects.create(nombre='Casi agotado', precio=Decimal('1'),
                                stock=2, categoria=self.cat)
        res = verificar_stock_bajo.apply(args=[5]).get()
        self.assertTrue(res['correo_enviado'])
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Casi agotado', mail.outbox[0].body)


# ── Extras W18: alerta por proveedor, HTML y acción del admin ─────────────

@override_settings(ADMIN_EMAIL=ADMIN)
class AlertaPorProveedorTest(TestCase):

    def setUp(self):
        from proveedores.models import Proveedor
        mail.outbox = []
        cat = Categoria.objects.create(nombre='C')
        v = Proveedor.objects.create(nombre='Vinos del Valle',
                                     correo='valle@prov.com')
        Producto.objects.create(nombre='Tinto', precio=Decimal('9'), stock=2,
                                categoria=cat, proveedor=v)
        Producto.objects.create(nombre='Rosado', precio=Decimal('9'), stock=1,
                                categoria=cat, proveedor=v)
        Producto.objects.create(nombre='Huerfano', precio=Decimal('9'),
                                stock=0, categoria=cat)

    def test_texto_agrupa_por_proveedor_y_deja_sin_proveedor_al_final(self):
        verificar_stock_bajo.apply(args=[5]).get()
        cuerpo = mail.outbox[0].body
        self.assertIn('Vinos del Valle <valle@prov.com>', cuerpo)
        self.assertLess(cuerpo.index('Vinos del Valle'),
                        cuerpo.index('Sin proveedor asignado'))
        self.assertIn('Tinto: 2', cuerpo)
        self.assertIn('Huerfano: 0', cuerpo)

    def test_correo_va_solo_al_admin_nunca_al_proveedor(self):
        verificar_stock_bajo.apply(args=[5]).get()
        self.assertEqual(mail.outbox[0].to, [ADMIN])
        self.assertNotIn('valle@prov.com', mail.outbox[0].to)

    def test_tiene_version_html(self):
        verificar_stock_bajo.apply(args=[5]).get()
        html, tipo = mail.outbox[0].alternatives[0]
        self.assertEqual(tipo, 'text/html')
        self.assertIn('Vinos del Valle', html)
        self.assertIn('Sin proveedor asignado', html)

    def test_resultado_incluye_proveedor_por_producto(self):
        res = verificar_stock_bajo.apply(args=[5]).get()
        por_nombre = {p['nombre']: p for p in res['productos_bajos']}
        self.assertEqual(por_nombre['Tinto']['proveedor_nombre'], 'Vinos del Valle')
        self.assertIsNone(por_nombre['Huerfano']['proveedor_nombre'])


@override_settings(ADMIN_EMAIL=ADMIN)
class AccionEnviarReporteTest(TestCase):

    def setUp(self):
        from django.contrib.auth import get_user_model
        mail.outbox = []
        ConfiguracionERP.get_instance()
        self.root = get_user_model().objects.create_superuser(
            'root', 'root@test.com', 'x')
        self.client.force_login(self.root)
        self.pedido = _pedido('PED-ACC', '10.00', estado='pendiente')

    def _post(self):
        return self.client.post('/admin/ventas/pedido/', {
            'action': 'enviar_reporte_ahora',
            '_selected_action': [self.pedido.pk]})

    def test_envia_el_reporte_aunque_no_haya_ventas(self):
        self.assertEqual(self._post().status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [ADMIN])

    @override_settings(ADMIN_EMAIL='')
    def test_sin_admin_email_no_envia(self):
        self._post()
        self.assertEqual(len(mail.outbox), 0)

    def test_usuario_sin_permiso_no_envia(self):
        from django.contrib.auth import get_user_model
        u = get_user_model().objects.create_user('emp', 'e@t.com', 'x',
                                                 is_staff=True)
        self.client.force_login(u)
        self._post()
        self.assertEqual(len(mail.outbox), 0)

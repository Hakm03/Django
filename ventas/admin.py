# ventas/admin.py
"""Configuración del panel admin para la app ventas."""
import logging

from django.contrib import admin, messages

from .models import DetalleVenta, Pedido, Venta

logger = logging.getLogger(__name__)


class DetalleVentaInline(admin.TabularInline):
    """Líneas de detalle dentro del admin de Venta."""

    model       = DetalleVenta
    extra       = 1            # mostrar 1 fila vacía para agregar
    fields      = ['producto', 'cantidad', 'precio_unitario']
    readonly_fields = []


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    """Admin de ventas con detalles inline y total calculado."""

    list_display    = ['pk', 'cliente', 'fecha', 'total_admin']
    search_fields   = ['cliente__nombre', 'cliente__correo']
    readonly_fields = ['fecha']
    inlines         = [DetalleVentaInline]
    date_hierarchy  = 'fecha'

    @admin.display(description='Total ($)')
    def total_admin(self, obj: Venta) -> str:
        """Muestra el total calculado de la venta en la lista."""
        return f"${obj.total:.2f}"


@admin.register(DetalleVenta)
class DetalleVentaAdmin(admin.ModelAdmin):
    """Admin de líneas de detalle (vista independiente)."""

    list_display  = ['pk', 'venta', 'producto', 'cantidad',
                     'precio_unitario', 'subtotal_admin']
    search_fields = ['producto__nombre', 'venta__pk']
    readonly_fields = ['precio_unitario']

    @admin.display(description='Subtotal ($)')
    def subtotal_admin(self, obj: DetalleVenta) -> str:
        return f"${obj.subtotal:.2f}"


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    """Admin de pedidos de e-commerce."""

    list_display   = ['numero_pedido', 'cliente', 'estado',
                      'fecha_pedido', 'total_pagado', 'correo_enviado']
    search_fields  = ['numero_pedido', 'cliente__nombre']
    list_filter    = ['estado', 'correo_enviado']
    readonly_fields = ['fecha_pedido']
    actions        = ['reenviar_recibo', 'enviar_reporte_ahora']

    @admin.action(description='Reenviar recibo por correo (solo pedidos pagados)')
    def reenviar_recibo(self, request, queryset):
        """Vuelve a encolar el recibo de los pedidos pagados seleccionados."""
        from .tasks import enviar_confirmacion_pedido   # import local

        pagados = queryset.filter(estado='pagado')
        omitidos = queryset.count() - pagados.count()
        encolados = 0
        for pedido in pagados:
            pedido.correo_enviado = False
            pedido.save(update_fields=['correo_enviado'])
            try:
                enviar_confirmacion_pedido.delay(pedido.pk)
                encolados += 1
            except Exception:
                logger.exception('Admin: no se pudo encolar el recibo de %s.',
                                 pedido.numero_pedido)
                self.message_user(
                    request,
                    f'No se pudo encolar el recibo de {pedido.numero_pedido} '
                    '(¿Redis disponible?).',
                    level=messages.ERROR)
        if encolados:
            self.message_user(
                request, f'Recibo en cola para {encolados} pedido(s).',
                level=messages.SUCCESS)
        if omitidos:
            self.message_user(
                request,
                f'{omitidos} pedido(s) omitido(s): solo se reenvían los '
                'pagados.', level=messages.WARNING)

    @admin.action(description='Enviar reporte de ventas de ayer AHORA '
                              '(selecciona cualquier pedido)')
    def enviar_reporte_ahora(self, request, queryset):
        """Dispara el reporte diario al instante, aunque ayer no haya ventas.

        Útil para demostrar el reporte sin esperar a Celery Beat. Siempre
        se envía a ADMIN_EMAIL, nunca a otra dirección. La selección de
        pedidos solo sirve para activar la acción (Django la exige).
        """
        from django.conf import settings

        from .tasks import reporte_ventas_diario   # import local

        if not request.user.has_perm('ventas.change_pedido'):
            self.message_user(request, 'No tienes permiso para esto.',
                              level=messages.ERROR)
            return
        if not settings.ADMIN_EMAIL:
            self.message_user(request, 'ADMIN_EMAIL no está configurado.',
                              level=messages.ERROR)
            return
        try:
            reporte_ventas_diario.delay(forzar=True)
        except Exception:
            logger.exception('Admin: no se pudo encolar el reporte.')
            self.message_user(request, 'No se pudo encolar el reporte '
                              '(¿Redis disponible?).', level=messages.ERROR)
            return
        self.message_user(
            request, 'Reporte en cola: llegará a ADMIN_EMAIL en unos '
            'segundos (revisa también Spam).', level=messages.SUCCESS)

# productos/admin.py — actualizar ProductoAdmin:
import logging

from django.conf     import settings
from django.contrib  import admin, messages
from django.utils.html import format_html

from .models import Categoria, Producto

logger = logging.getLogger(__name__)

UMBRAL_STOCK_BAJO = 5


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display  = ['pk', 'nombre', 'descripcion']
    search_fields = ['nombre']


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    """Admin de productos con preview de imagen — W11."""

    list_display   = ['pk', 'imagen_preview', 'nombre', 'precio',
                      'stock', 'categoria', 'proveedor', 'activo']
    search_fields  = ['nombre', 'categoria__nombre', 'proveedor__nombre']
    list_filter    = ['activo', 'categoria']
    list_editable  = ['precio', 'stock', 'activo']
    readonly_fields = ['creado', 'imagen_preview_grande']
    date_hierarchy  = 'creado'
    ordering        = ['nombre']
    actions         = ['enviar_alerta_stock']

    @admin.display(description='Imagen')
    def imagen_preview(self, obj: Producto) -> str:
        """Miniatura de la imagen en la lista del admin."""
        if obj.imagen:
            return format_html(
                '<img src="{}" style="height:48px;width:48px;'
                'object-fit:cover;border-radius:6px;">',
                obj.imagen.url
            )
        return '—'

    @admin.display(description='Vista previa')
    def imagen_preview_grande(self, obj: Producto) -> str:
        """Imagen ampliada en el formulario de edición del admin."""
        if obj.imagen:
            return format_html(
                '<img src="{}" style="max-height:200px;'
                'border-radius:8px;margin-top:.5rem;">',
                obj.imagen.url
            )
        return 'Sin imagen'

    @admin.action(description='Enviar alerta de stock bajo AHORA '
                              '(selecciona cualquier producto)')
    def enviar_alerta_stock(self, request, queryset):
        """Dispara la alerta de stock al instante (revisa TODO el inventario).

        La selección solo activa la acción (Django la exige). El correo va
        siempre a ADMIN_EMAIL.
        """
        from ventas.tasks import verificar_stock_bajo   # import local

        if not request.user.has_perm('productos.change_producto'):
            self.message_user(request, 'No tienes permiso para esto.',
                              level=messages.ERROR)
            return
        if not settings.ADMIN_EMAIL:
            self.message_user(request, 'ADMIN_EMAIL no está configurado.',
                              level=messages.ERROR)
            return
        bajos = Producto.objects.filter(
            activo=True, stock__lt=UMBRAL_STOCK_BAJO).count()
        if not bajos:
            self.message_user(
                request, f'Ningún producto activo tiene menos de '
                f'{UMBRAL_STOCK_BAJO} unidades: no se envía correo.',
                level=messages.WARNING)
            return
        try:
            verificar_stock_bajo.delay(UMBRAL_STOCK_BAJO)
        except Exception:
            logger.exception('Admin: no se pudo encolar la alerta de stock.')
            self.message_user(request, 'No se pudo encolar la alerta '
                              '(¿Redis disponible?).', level=messages.ERROR)
            return
        self.message_user(
            request, f'Alerta en cola ({bajos} producto(s) bajos): llegará a '
            'ADMIN_EMAIL en unos segundos (revisa también Spam).',
            level=messages.SUCCESS)

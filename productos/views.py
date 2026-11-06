# productos/views.py
"""Vistas de la app productos — W07.

ListView y DetailView con select_related y paginación.
Escritura (Create/Update/Delete) se implementa en W08.
"""
import csv
import logging
from datetime import date
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.utils import timezone
from django.http import HttpResponse, HttpResponseBadRequest
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from django.views.generic import DetailView, ListView

from .models import Producto

# productos/views.py — agregar los imports al inicio del archivo:
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)

from .forms import ProductoForm

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from django.contrib.auth.views import redirect_to_login

class ProductoListView(ListView):
    """Lista paginada de productos activos.

    Atributos:
        model:               Modelo a listar.
        template_name:       Plantilla HTML (Fable 5 AzulERP).
        context_object_name: Nombre de la variable en el template.
        paginate_by:         20 productos por página.
        queryset:            Solo productos activos, con FK pre-cargadas.
    """

    model               = Producto
    template_name       = 'productos/lista.html'
    context_object_name = 'productos'
    paginate_by         = 20

    def get_queryset(self):
        """Devuelve productos activos con FKs pre-cargadas (evita N+1)."""
        return (
            Producto.objects
            .select_related('categoria', 'proveedor')
            .filter(activo=True)
            .order_by('nombre')
        )


class ProductoDetailView(DetailView):
    """Detalle de un producto por ID de URL.

    Atributos:
        model:               Modelo a mostrar.
        template_name:       Plantilla HTML.
        context_object_name: Nombre en el template ('producto').
        pk_url_kwarg:        Parámetro de URL. Usa 'producto_id'
                             para ser consistente con W02.
    """

    model               = Producto
    template_name       = 'productos/detalle.html'
    context_object_name = 'producto'
    pk_url_kwarg        = 'producto_id'

    def get_queryset(self):
        """Pre-carga FKs para evitar queries adicionales en el template."""
        return Producto.objects.select_related('categoria', 'proveedor')

class ProductoCreateView(LoginRequiredMixin, CreateView):
    """Formulario para crear un nuevo producto.

    LoginRequiredMixin PRIMERO en la herencia (obligatorio).
    Redirige a /accounts/login/ si el usuario no está autenticado.
    """

    model         = Producto
    form_class    = ProductoForm
    template_name = 'productos/crear.html'
    success_url   = reverse_lazy('productos:lista')  # reverse_lazy (no reverse)

    def form_valid(self, form):
        """Agrega mensaje flash de éxito al guardar."""
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Producto "{self.object.nombre}" creado exitosamente.'
        )
        return response


class ProductoUpdateView(LoginRequiredMixin, UpdateView):
    """Formulario para editar un producto existente."""

    model         = Producto
    form_class    = ProductoForm
    template_name = 'productos/editar.html'
    pk_url_kwarg  = 'producto_id'
    success_url   = reverse_lazy('productos:lista')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Producto "{self.object.nombre}" actualizado.'
        )
        return response


class ProductoDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Confirmación y borrado de un producto.

    Requiere permiso 'productos.delete_producto'.
    Sin permiso: HTTP 403 Forbidden (raise_exception=True).
    """

    model               = Producto
    template_name       = 'productos/eliminar.html'
    pk_url_kwarg        = 'producto_id'
    success_url         = reverse_lazy('productos:lista')
    permission_required = 'productos.delete_producto'
    raise_exception     = True

    def handle_no_permission(self):
        # Sin sesión → login; con sesión pero sin permiso → 403
        if not self.request.user.is_authenticated:
            return redirect_to_login(self.request.get_full_path(),
                                     self.get_login_url(),
                                     self.get_redirect_field_name())
        return super().handle_no_permission()

    def form_valid(self, form):
        nombre   = self.object.nombre
        response = super().form_valid(form)
        messages.success(self.request, f'Producto "{nombre}" eliminado.')
        return response


# ── W12: exportar inventario (Excel / CSV) ────────────────────────────────
FORMATOS_INVENTARIO = {'xlsx', 'csv', 'pdf'}  # lista permitida de ?formato=
MAX_PRODUCTOS_PDF = 1000  # límite del PDF para no agotar la memoria
logger = logging.getLogger(__name__)

ENCABEZADOS_INVENTARIO = ['ID', 'Producto', 'Categoría', 'Proveedor',
                          'Precio', 'Stock', 'Valor en inventario', 'Activo']


def _productos_inventario():
    """Todos los productos con sus FK pre-cargadas (evita N+1)."""
    return (
        Producto.objects
        .select_related('categoria', 'proveedor')
        .order_by('nombre')
    )


def _celda_texto(hoja, fila, columna, valor):
    """Escribe un texto en la celda y lo marca SIEMPRE como texto.

    Si alguien guarda un producto llamado "=1+1", Excel lo trataría como
    una fórmula. Marcarlo como texto evita que se ejecute.
    """
    celda = hoja.cell(row=fila, column=columna, value=str(valor))
    celda.data_type = 's'
    return celda


def _texto_csv_seguro(valor):
    """Evita la inyección de fórmulas en CSV.

    Si el texto empieza con = + - @ (o tabulador/retorno), Excel lo
    ejecutaría como fórmula; con un ' al inicio se muestra como texto.
    """
    texto = str(valor)
    if texto and texto[0] in ('=', '+', '-', '@', '\t', '\r'):
        return "'" + texto
    return texto


def _respuesta_xlsx():
    """Construye la descarga del inventario en formato .xlsx."""
    productos = _productos_inventario()

    libro = Workbook()
    hoja = libro.active
    hoja.title = 'Inventario'

    # Fila 1: encabezados con color
    for col, texto in enumerate(ENCABEZADOS_INVENTARIO, start=1):
        celda = hoja.cell(row=1, column=col, value=texto)
        celda.font = Font(bold=True, color='FFFFFF')
        celda.fill = PatternFill('solid', fgColor='1F3A5F')
        celda.alignment = Alignment(horizontal='center')

    # Filas de datos
    fila = 1
    for fila, p in enumerate(productos, start=2):
        hoja.cell(row=fila, column=1, value=p.pk)
        _celda_texto(hoja, fila, 2, p.nombre)
        _celda_texto(hoja, fila, 3, p.categoria.nombre)
        _celda_texto(hoja, fila, 4, p.proveedor.nombre if p.proveedor else '—')
        hoja.cell(row=fila, column=5, value=p.precio).number_format = '#,##0.00'
        hoja.cell(row=fila, column=6, value=p.stock)
        hoja.cell(row=fila, column=7,
                  value=p.precio * p.stock).number_format = '#,##0.00'
        _celda_texto(hoja, fila, 8, 'Sí' if p.activo else 'No')

    # Fila final: total del inventario (fórmula SUM de Excel)
    if fila >= 2:
        hoja.cell(row=fila + 1, column=6, value='TOTAL').font = Font(bold=True)
        total = hoja.cell(row=fila + 1, column=7, value=f'=SUM(G2:G{fila})')
        total.font = Font(bold=True)
        total.number_format = '#,##0.00'

    # Comodidad: primera fila fija, filtros y anchos de columna
    hoja.freeze_panes = 'A2'
    hoja.auto_filter.ref = f'A1:H{max(fila, 1)}'
    for letra, ancho in zip('ABCDEFGH', (8, 32, 20, 24, 12, 10, 20, 10)):
        hoja.column_dimensions[letra].width = ancho

    respuesta = HttpResponse(
        content_type=(
            'application/vnd.openxmlformats-officedocument.'
            'spreadsheetml.sheet'
        )
    )
    respuesta['Content-Disposition'] = (
        f'attachment; filename="inventario_{date.today():%Y-%m-%d}.xlsx"'
    )
    libro.save(respuesta)
    return respuesta


def _respuesta_csv():
    """Construye la descarga del inventario en formato .csv."""
    respuesta = HttpResponse(content_type='text/csv; charset=utf-8')
    respuesta['Content-Disposition'] = (
        f'attachment; filename="inventario_{date.today():%Y-%m-%d}.csv"'
    )
    # BOM utf-8-sig: así Excel muestra bien los acentos.
    respuesta.write('\ufeff')
    escritor = csv.writer(respuesta)
    escritor.writerow(ENCABEZADOS_INVENTARIO)
    for p in _productos_inventario():
        escritor.writerow([
            p.pk,
            _texto_csv_seguro(p.nombre),
            _texto_csv_seguro(p.categoria.nombre),
            _texto_csv_seguro(p.proveedor.nombre if p.proveedor else '—'),
            p.precio,
            p.stock,
            p.precio * p.stock,
            'Sí' if p.activo else 'No',
        ])
    return respuesta


def _respuesta_pdf():
    """Construye la descarga del inventario en PDF (WeasyPrint)."""
    productos_qs = _productos_inventario()
    if productos_qs.count() > MAX_PRODUCTOS_PDF:
        return HttpResponseBadRequest(
            f'Hay demasiados productos para un PDF (máximo '
            f'{MAX_PRODUCTOS_PDF}). Usa Excel o CSV.',
            content_type='text/plain; charset=utf-8',
        )
    productos = list(productos_qs)
    for p in productos:
        p.valor = p.precio * p.stock
    html = render_to_string('productos/inventario_pdf.html', {
        'productos': productos,
        'total': sum((p.valor for p in productos), Decimal('0')),
        'emitida': timezone.now(),
    })
    try:
        from core.pdf_utils import generar_pdf  # import perezoso
        pdf = generar_pdf(html)
    except (ImportError, OSError):
        logger.exception('WeasyPrint no está disponible en este servidor')
        return HttpResponse(
            'El generador de PDF no está disponible en este servidor.',
            status=503,
            content_type='text/plain; charset=utf-8',
        )
    respuesta = HttpResponse(pdf, content_type='application/pdf')
    respuesta['Content-Disposition'] = (
        f'attachment; filename="inventario_{date.today():%Y-%m-%d}.pdf"'
    )
    return respuesta


@login_required
def exportar_inventario(request):
    """Descarga el inventario en el formato elegido (?formato=xlsx|csv|pdf)."""
    formato = request.GET.get('formato', 'xlsx').strip().lower()
    if formato not in FORMATOS_INVENTARIO:
        return HttpResponseBadRequest(
            'Formato no válido. Formatos permitidos: xlsx, csv, pdf.',
            content_type='text/plain; charset=utf-8',
        )
    if formato == 'csv':
        return _respuesta_csv()
    if formato == 'pdf':
        return _respuesta_pdf()
    return _respuesta_xlsx()


@login_required
def exportar_excel(request):
    """Descarga el inventario completo en .xlsx (ruta anterior, siempre Excel)."""
    return _respuesta_xlsx()


# ── W12 (ampliación): vista previa e impresión del inventario ─────────────
PAPELES_INVENTARIO = {
    'a4':    {'etiqueta': 'Hoja A4',    'pagina': 'A4'},
    'carta': {'etiqueta': 'Hoja Carta', 'pagina': 'letter'},
}


@login_required
def inventario_imprimir(request):
    """Vista previa del inventario con botón Imprimir (?papel=a4|carta)."""
    from django.shortcuts import render

    papel = request.GET.get('papel', 'a4').strip().lower()
    if papel not in PAPELES_INVENTARIO:
        return HttpResponseBadRequest(
            'Papel no válido. Permitidos: a4, carta.',
            content_type='text/plain; charset=utf-8',
        )
    productos_qs = _productos_inventario()
    if productos_qs.count() > MAX_PRODUCTOS_PDF:
        return HttpResponseBadRequest(
            f'Hay demasiados productos para imprimir (máximo '
            f'{MAX_PRODUCTOS_PDF}). Usa Excel o CSV.',
            content_type='text/plain; charset=utf-8',
        )
    productos = list(productos_qs)
    for p in productos:
        p.valor = p.precio * p.stock
    from configuracion.models import ConfiguracionERP
    return render(request, 'productos/inventario_imprimir.html', {
        'productos': productos,
        'total': sum((p.valor for p in productos), Decimal('0')),
        'emitida': timezone.now(),
        'empresa': ConfiguracionERP.get_instance(),
        'papel': papel,
        'papel_info': PAPELES_INVENTARIO[papel],
        'papeles': list(PAPELES_INVENTARIO.items()),
    })

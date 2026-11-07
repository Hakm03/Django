# ventas/views.py
"""Vistas de la app ventas — W07.

Lectura: VentaListView y VentaDetailView.
Escritura (crear_venta): W08.
"""
# ventas/views.py — agregar imports al inicio:
import logging

from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import DeleteView, DetailView, ListView
from .forms  import DetalleVentaForm, VentaForm
from .models import DetalleVenta, Venta
from django.views.generic import DetailView, ListView
from .models import Venta
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import (
    login_required,
    permission_required,
)


class VentaListView(ListView):
    """Lista paginada de ventas en orden cronológico inverso."""

    model               = Venta
    template_name       = 'ventas/lista.html'
    context_object_name = 'ventas'
    paginate_by         = 20

    def get_queryset(self):
        """Pre-carga cliente para evitar N+1 en la tabla de ventas."""
        return (
            Venta.objects
            .select_related('cliente')
            .order_by('-fecha')
        )


class VentaDetailView(DetailView):
    """Detalle de una venta con todas sus líneas de producto."""

    model               = Venta
    template_name       = 'ventas/detalle.html'
    context_object_name = 'venta'
    pk_url_kwarg        = 'venta_id'

    def get_queryset(self):
        """Pre-carga cliente y prefetch líneas de detalle."""
        return (
            Venta.objects
            .select_related('cliente')
            .prefetch_related('detalles__producto')
        )

@login_required
@permission_required('ventas.add_venta', raise_exception=True)
def crear_venta(request):
    """Crea un encabezado de venta con una línea de detalle.

    Decoradores (se aplican de abajo hacia arriba):
        @login_required            → verifica autenticación
        @permission_required(...)  → verifica permiso add_venta

    GET  → muestra los dos formularios vacíos.
    POST → valida ambos, guarda si correctos, muestra errores si no.
    """
    venta_form   = VentaForm(request.POST or None)
    detalle_form = DetalleVentaForm(request.POST or None)

    if request.method == 'POST':
        if venta_form.is_valid() and detalle_form.is_valid():
            venta         = venta_form.save()
            detalle       = detalle_form.save(commit=False)
            detalle.venta = venta
            detalle.save()
            messages.success(
                request,
                f'Venta #{venta.pk} registrada. '
                f'Total: ${venta.total:.2f}'
            )
            return redirect('ventas:detalle', venta_id=venta.pk)

    return render(request, 'ventas/crear.html', {
        'venta_form':   venta_form,
        'detalle_form': detalle_form,
    })

class VentaDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model               = Venta
    template_name       = 'ventas/eliminar.html'
    pk_url_kwarg        = 'venta_id'
    success_url         = reverse_lazy('ventas:lista')
    permission_required = 'ventas.delete_venta'
    raise_exception     = True

    def form_valid(self, form):
        pk       = self.object.pk
        response = super().form_valid(form)
        messages.success(self.request, f'Venta #{pk} eliminada.')
        return response


# ── W12: factura en PDF (WeasyPrint) ──────────────────────────────────────
logger = logging.getLogger(__name__)


def _fetcher_seguro(url):
    """Envoltorio delgado: la lógica vive en core.pdf_utils."""
    from core.pdf_utils import fetcher_seguro
    return fetcher_seguro(url)


def _generar_pdf(html: str) -> bytes:
    """Envoltorio delgado: la lógica vive en core.pdf_utils."""
    from core.pdf_utils import generar_pdf
    return generar_pdf(html)


@login_required
def venta_pdf(request, venta_id):
    """Descarga la factura de una venta en PDF."""
    venta = get_object_or_404(
        Venta.objects
        .select_related('cliente')
        .prefetch_related('detalles__producto'),
        pk=venta_id,
    )
    html = render_to_string(
        'ventas/factura_pdf.html',
        {'venta': venta, 'emitida': timezone.now()},
    )
    try:
        pdf = _generar_pdf(html)
    except (ImportError, OSError):
        logger.exception('WeasyPrint no está disponible en este servidor')
        return HttpResponse(
            'El generador de PDF no está disponible en este servidor.',
            status=503,
            content_type='text/plain; charset=utf-8',
        )

    respuesta = HttpResponse(pdf, content_type='application/pdf')
    respuesta['Content-Disposition'] = (
        f'attachment; filename="factura_{venta.pk:05d}.pdf"'
    )
    return respuesta



# ── W12 (ampliación): tickets de venta (vista previa / imprimir / lote) ───
# Papeles permitidos. El valor que llega por ?papel= SOLO se usa como llave
# de este diccionario; nunca se pega directo en el CSS.
PAPELES_TICKET = {
    '58mm': {'etiqueta': 'Térmica 58 mm', 'detalle': 'Rollo de 58 mm',
             'pagina': '58mm auto', 'pagina_pdf': '58mm 297mm',
             'margen': '2mm', 'fuente': '9pt',
             'ancho': '54mm', 'ancho_impresion': '100%'},
    '80mm': {'etiqueta': 'Térmica 80 mm', 'detalle': 'Rollo de 80 mm',
             'pagina': '80mm auto', 'pagina_pdf': '80mm 297mm',
             'margen': '3mm', 'fuente': '10pt',
             'ancho': '76mm', 'ancho_impresion': '100%'},
    'a5':   {'etiqueta': 'Media hoja (A5)', 'detalle': '148 × 210 mm',
             'pagina': 'A5', 'pagina_pdf': 'A5',
             'margen': '10mm', 'fuente': '11pt',
             'ancho': '120mm', 'ancho_impresion': '110mm'},
    'a4':   {'etiqueta': 'Hoja A4', 'detalle': '210 × 297 mm',
             'pagina': 'A4', 'pagina_pdf': 'A4',
             'margen': '15mm', 'fuente': '11pt',
             'ancho': '120mm', 'ancho_impresion': '110mm'},
    'carta': {'etiqueta': 'Hoja Carta', 'detalle': '216 × 279 mm',
              'pagina': 'letter', 'pagina_pdf': 'letter',
              'margen': '15mm', 'fuente': '11pt',
              'ancho': '120mm', 'ancho_impresion': '110mm'},
}
PAPEL_TICKET_DEFECTO = '80mm'
FORMATOS_TICKET = {'html', 'pdf', 'xlsx', 'csv'}   # lista permitida de ?formato=
MAX_TICKETS_LOTE = 100              # tope de tickets por impresión/exportación
ENCABEZADOS_VENTAS = ['Folio', 'Fecha', 'Cliente', 'Producto', 'Cantidad',
                      'Precio unitario', 'Subtotal', 'Total de la venta']


def _papel_de_la_peticion(request):
    """Devuelve la llave del papel pedido, o None si no está permitido."""
    papel = request.GET.get('papel', PAPEL_TICKET_DEFECTO).strip().lower()
    return papel if papel in PAPELES_TICKET else None


def _filas_ventas(ventas):
    """Una fila por línea de detalle (o una fila si la venta no tiene líneas)."""
    for v in ventas:
        fecha = timezone.localtime(v.fecha).strftime('%d/%m/%Y %H:%M')
        lineas = list(v.detalles.all())
        total = v.total
        if not lineas:
            yield [v.pk, fecha, str(v.cliente), 'Sin productos', 0, 0, 0, total]
        for d in lineas:
            yield [v.pk, fecha, str(v.cliente), d.producto.nombre,
                   d.cantidad, d.precio_unitario, d.subtotal, total]


def _respuesta_ventas_xlsx(ventas):
    """Descarga de las ventas elegidas en .xlsx (textos marcados como texto)."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from productos.views import _celda_texto

    libro = Workbook()
    hoja = libro.active
    hoja.title = 'Ventas'
    for col, texto in enumerate(ENCABEZADOS_VENTAS, start=1):
        celda = hoja.cell(row=1, column=col, value=texto)
        celda.font = Font(bold=True, color='FFFFFF')
        celda.fill = PatternFill('solid', fgColor='1F3A5F')
        celda.alignment = Alignment(horizontal='center')
    fila = 1
    for fila, datos in enumerate(_filas_ventas(ventas), start=2):
        folio, fecha, cliente, producto, cant, precio, sub, total = datos
        hoja.cell(row=fila, column=1, value=folio).number_format = '00000'
        _celda_texto(hoja, fila, 2, fecha)
        _celda_texto(hoja, fila, 3, cliente)
        _celda_texto(hoja, fila, 4, producto)
        hoja.cell(row=fila, column=5, value=cant)
        hoja.cell(row=fila, column=6, value=precio).number_format = '#,##0.00'
        hoja.cell(row=fila, column=7, value=sub).number_format = '#,##0.00'
        hoja.cell(row=fila, column=8, value=total).number_format = '#,##0.00'
    hoja.freeze_panes = 'A2'
    hoja.auto_filter.ref = f'A1:H{max(fila, 1)}'
    for letra, ancho in zip('ABCDEFGH', (9, 18, 26, 32, 10, 15, 13, 17)):
        hoja.column_dimensions[letra].width = ancho
    respuesta = HttpResponse(
        content_type=('application/vnd.openxmlformats-officedocument.'
                      'spreadsheetml.sheet'))
    respuesta['Content-Disposition'] = (
        f'attachment; filename="ventas_{timezone.localdate():%Y-%m-%d}.xlsx"')
    libro.save(respuesta)
    return respuesta


def _respuesta_ventas_csv(ventas):
    """Descarga de las ventas elegidas en .csv (sin fórmulas ejecutables)."""
    import csv
    from productos.views import _texto_csv_seguro

    respuesta = HttpResponse(content_type='text/csv; charset=utf-8')
    respuesta['Content-Disposition'] = (
        f'attachment; filename="ventas_{timezone.localdate():%Y-%m-%d}.csv"')
    respuesta.write('﻿')   # BOM: Excel muestra bien los acentos
    escritor = csv.writer(respuesta)
    escritor.writerow(ENCABEZADOS_VENTAS)
    for datos in _filas_ventas(ventas):
        folio, fecha, cliente, producto, cant, precio, sub, total = datos
        escritor.writerow([
            folio, fecha, _texto_csv_seguro(cliente),
            _texto_csv_seguro(producto), cant, precio, sub, total,
        ])
    return respuesta


def _respuesta_tickets(request, ventas, papel, formato='html'):
    """Vista previa de tickets (HTML) o descarga (PDF / Excel / CSV)."""
    from urllib.parse import urlencode
    from configuracion.models import ConfiguracionERP

    if formato == 'xlsx':
        return _respuesta_ventas_xlsx(ventas)
    if formato == 'csv':
        return _respuesta_ventas_csv(ventas)

    es_pdf = formato == 'pdf'
    info = dict(PAPELES_TICKET[papel])
    if es_pdf:
        info['pagina'] = info['pagina_pdf']

    def _url(fmt):
        consulta = [('ids', v.pk) for v in ventas] + [('formato', fmt)]
        return f"{reverse('ventas:tickets')}?{urlencode(consulta)}"

    contexto = {
        'ventas': ventas,
        'papel': papel,
        'papel_info': info,
        'empresa': ConfiguracionERP.get_instance(),
        'es_pdf': es_pdf,
        'vp_titulo': ('Ticket de venta — vista previa' if len(ventas) == 1
                      else f'{len(ventas)} tickets — vista previa'),
        'hojas_js': {
            'actual': papel,
            'clave_guardado': 'erp_papel_ticket',
            'hojas': {
                k: {c: h[c] for c in ('etiqueta', 'detalle', 'pagina', 'margen',
                                      'ancho', 'ancho_impresion', 'fuente')}
                for k, h in PAPELES_TICKET.items()
            },
        },
        'formatos': [
            {'etiqueta': 'PDF', 'detalle': 'Tickets con la hoja elegida (.pdf)',
             'url': _url('pdf'), 'con_hoja': True},
            {'etiqueta': 'Excel', 'detalle': 'Hoja de cálculo (.xlsx)',
             'url': _url('xlsx')},
            {'etiqueta': 'CSV', 'detalle': 'Texto separado por comas (.csv)',
             'url': _url('csv')},
        ],
    }
    if not es_pdf:
        return render(request, 'ventas/ticket.html', contexto)

    html = render_to_string('ventas/ticket.html', contexto)
    try:
        pdf = _generar_pdf(html)
    except (ImportError, OSError):
        logger.exception('WeasyPrint no está disponible en este servidor')
        return HttpResponse(
            'El generador de PDF no está disponible en este servidor.',
            status=503,
            content_type='text/plain; charset=utf-8',
        )
    respuesta = HttpResponse(pdf, content_type='application/pdf')
    nombre = (f'ticket_{ventas[0].pk:05d}.pdf' if len(ventas) == 1
              else f'tickets_{timezone.localdate():%Y-%m-%d}.pdf')
    respuesta['Content-Disposition'] = f'attachment; filename="{nombre}"'
    return respuesta


def _error_400(mensaje):
    return HttpResponseBadRequest(
        mensaje, content_type='text/plain; charset=utf-8')


@login_required
def venta_ticket(request, venta_id):
    """Vista previa del ticket de UNA venta (con Imprimir ▾ y Exportar ▾)."""
    papel = _papel_de_la_peticion(request)
    if papel is None:
        return _error_400(
            'Papel no válido. Permitidos: ' + ', '.join(PAPELES_TICKET) + '.')
    venta = get_object_or_404(
        Venta.objects
        .select_related('cliente')
        .prefetch_related('detalles__producto'),
        pk=venta_id,
    )
    return _respuesta_tickets(request, [venta], papel)


@login_required
def venta_tickets_lote(request):
    """Varias ventas a la vez: ?ids=1&ids=2&formato=html|pdf|xlsx|csv."""
    papel = _papel_de_la_peticion(request)
    if papel is None:
        return _error_400(
            'Papel no válido. Permitidos: ' + ', '.join(PAPELES_TICKET) + '.')
    formato = request.GET.get('formato', 'html').strip().lower()
    if formato not in FORMATOS_TICKET:
        return _error_400('Formato no válido. Permitidos: html, pdf, xlsx, csv.')

    ids = []
    for crudo in request.GET.getlist('ids'):
        crudo = crudo.strip()
        # Solo dígitos ASCII y de largo razonable (evita desbordar la BD).
        if not (crudo.isascii() and crudo.isdigit() and len(crudo) <= 9):
            return _error_400('Lista de ventas no válida.')
        numero = int(crudo)
        if numero not in ids:
            ids.append(numero)
    if not ids:
        return _error_400('Selecciona al menos una venta.')
    if len(ids) > MAX_TICKETS_LOTE:
        return _error_400(
            f'Demasiadas ventas: máximo {MAX_TICKETS_LOTE} tickets a la vez.')

    ventas = list(
        Venta.objects
        .select_related('cliente')
        .prefetch_related('detalles__producto')
        .filter(pk__in=ids)
        .order_by('pk')
    )
    if not ventas:
        raise Http404('Ninguna de las ventas seleccionadas existe.')
    return _respuesta_tickets(request, ventas, papel, formato=formato)

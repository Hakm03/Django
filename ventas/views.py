# ventas/views.py
"""Vistas de la app ventas — W07.

Lectura: VentaListView y VentaDetailView.
Escritura (crear_venta): W08.
"""
# ventas/views.py — agregar imports al inicio:
import logging

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, HttpResponseBadRequest
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



# ── W12 (ampliación): tickets de venta (imprimir / vista previa / lote) ───
# Papeles permitidos. El valor que llega por ?papel= SOLO se usa como llave
# de este diccionario; nunca se pega directo en el CSS.
PAPELES_TICKET = {
    '58mm': {'etiqueta': 'Térmica 58 mm', 'pagina': '58mm auto',
             'pagina_pdf': '58mm 297mm', 'margen': '2mm', 'fuente': '9pt',
             'ancho': '54mm', 'ancho_impresion': '100%'},
    '80mm': {'etiqueta': 'Térmica 80 mm', 'pagina': '80mm auto',
             'pagina_pdf': '80mm 297mm', 'margen': '3mm', 'fuente': '10pt',
             'ancho': '76mm', 'ancho_impresion': '100%'},
    'a5':   {'etiqueta': 'Media hoja (A5)', 'pagina': 'A5',
             'pagina_pdf': 'A5', 'margen': '10mm', 'fuente': '11pt',
             'ancho': '120mm', 'ancho_impresion': '110mm'},
    'a4':   {'etiqueta': 'Hoja A4', 'pagina': 'A4',
             'pagina_pdf': 'A4', 'margen': '15mm', 'fuente': '11pt',
             'ancho': '120mm', 'ancho_impresion': '110mm'},
    'carta': {'etiqueta': 'Hoja Carta', 'pagina': 'letter',
              'pagina_pdf': 'letter', 'margen': '15mm', 'fuente': '11pt',
              'ancho': '120mm', 'ancho_impresion': '110mm'},
}
PAPEL_TICKET_DEFECTO = '80mm'
FORMATOS_TICKET = {'html', 'pdf'}   # lista permitida de ?formato=
MAX_TICKETS_LOTE = 100              # tope de tickets por impresión/PDF


def _papel_de_la_peticion(request):
    """Devuelve la llave del papel pedido, o None si no está permitido."""
    papel = request.GET.get('papel', PAPEL_TICKET_DEFECTO).strip().lower()
    return papel if papel in PAPELES_TICKET else None


def _respuesta_tickets(request, ventas, papel, ids=(), accion='',
                       formato='html'):
    """Arma los tickets (pantalla para imprimir, o PDF descargable)."""
    from configuracion.models import ConfiguracionERP

    es_pdf = formato == 'pdf'
    info = dict(PAPELES_TICKET[papel])
    if es_pdf:
        info['pagina'] = info['pagina_pdf']
    contexto = {
        'ventas': ventas,
        'papel': papel,
        'papel_info': info,
        'papeles': list(PAPELES_TICKET.items()),
        'empresa': ConfiguracionERP.get_instance(),
        'ids': list(ids),
        'accion': accion,
        'es_pdf': es_pdf,
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
    """Vista previa e impresión del ticket de UNA venta."""
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
    return _respuesta_tickets(
        request, [venta], papel,
        accion=reverse('ventas:ticket', args=[venta.pk]),
    )

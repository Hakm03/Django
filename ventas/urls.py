# ventas/urls.py
from django.urls import path
from . import views

app_name = 'ventas'

urlpatterns = [
    path('',                        views.VentaListView.as_view(),  name='lista'),
    path('<int:venta_id>/',         views.VentaDetailView.as_view(),name='detalle'),
    path('nueva/',                  views.crear_venta,              name='crear'),
    # Tickets de varias ventas a la vez (ampliación W12)
    path('tickets/',                views.venta_tickets_lote,       name='tickets'),
    path('<int:venta_id>/eliminar/',views.VentaDeleteView.as_view(),name='eliminar'),
    # Factura en PDF (W12)
    path('<int:venta_id>/pdf/',     views.venta_pdf,                name='pdf'),
    # Ticket: vista previa e impresión (ampliación W12)
    path('<int:venta_id>/ticket/',  views.venta_ticket,             name='ticket'),
]

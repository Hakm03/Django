# catalogo/filters.py
"""Filtros para el catálogo público de productos — W13."""
import django_filters
from django import forms

from productos.models import Categoria, Producto

_INPUT = {'class': 'erp-input'}


class ProductoFilter(django_filters.FilterSet):
    """Filtra por nombre, categoría y rango de precio."""

    nombre = django_filters.CharFilter(
        field_name='nombre', lookup_expr='icontains',
        label='Buscar por nombre',
        widget=forms.TextInput(attrs=_INPUT),
    )
    categoria = django_filters.ModelChoiceFilter(
        queryset=Categoria.objects.all(),
        label='Categoría', empty_label='Todas las categorías',
        widget=forms.Select(attrs=_INPUT),
    )
    precio_min = django_filters.NumberFilter(
        field_name='precio', lookup_expr='gte', label='Precio mínimo ($)',
        widget=forms.NumberInput(attrs=_INPUT),
    )
    precio_max = django_filters.NumberFilter(
        field_name='precio', lookup_expr='lte', label='Precio máximo ($)',
        widget=forms.NumberInput(attrs=_INPUT),
    )

    class Meta:
        model = Producto
        fields = ['nombre', 'categoria', 'precio_min', 'precio_max']

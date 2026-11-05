"""Utilidades compartidas para generar PDF con WeasyPrint (W12).

IMPORTANTE: `import weasyprint` va SIEMPRE dentro de las funciones, nunca al
inicio del archivo. Así, si la máquina no tiene las librerías de WeasyPrint
(Windows sin Docker), el resto del ERP sigue funcionando.
"""
from pathlib import Path
from urllib.parse import unquote, urlparse

from django.conf import settings


def fetcher_seguro(url):
    """Decide qué archivos puede leer WeasyPrint al armar el PDF.

    Solo se permiten archivos locales de /static y /media (y imágenes
    incrustadas "data:"). Cualquier dirección de internet se bloquea.
    """
    import weasyprint

    if url.startswith('data:'):
        return weasyprint.default_url_fetcher(url)
    if url.startswith('file:'):
        ruta = Path(unquote(urlparse(url).path)).resolve()
        for carpeta in (settings.STATIC_ROOT, settings.MEDIA_ROOT):
            if carpeta and ruta.is_relative_to(Path(carpeta).resolve()):
                return weasyprint.default_url_fetcher(url)
    raise ValueError(f'Recurso no permitido en el PDF: {url}')


def generar_pdf(html: str) -> bytes:
    """Convierte un texto HTML en los bytes de un PDF."""
    import weasyprint

    return weasyprint.HTML(string=html, url_fetcher=fetcher_seguro).write_pdf()

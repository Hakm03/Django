# core/celery.py
"""Configuración de la aplicación Celery para el proyecto ERP Django (W16).

Uso desde la línea de comandos (solo con Redis disponible):
    celery -A core worker -l info -Q erp_django
    celery -A core flower --port=5555

Sin REDIS_URL (laboratorio / tests) las tareas corren en modo EAGER:
.delay() ejecuta la tarea en el mismo proceso, sin broker ni worker.
"""
import os

from celery import Celery

# Debe establecerse antes de crear la app Celery.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')

# Lee las variables CELERY_* de Django settings.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Descubre tasks.py en las apps instaladas (ventas/tasks.py, etc.).
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Tarea de diagnóstico: imprime el request de la tarea."""
    print(f'Request: {self.request!r}')

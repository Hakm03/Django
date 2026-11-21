# core/__init__.py
"""Paquete core del ERP Django.

Importa la app Celery al arrancar Django para que @shared_task la encuentre.
"""
from .celery import app as celery_app

__all__ = ('celery_app',)

"""Envía un correo de prueba para validar la configuración de SendGrid.

Uso:
    python manage.py probar_correo                 # envía a ADMIN_EMAIL
    python manage.py probar_correo otro@correo.com # envía a otra dirección
"""
from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone


class Command(BaseCommand):
    help = 'Envía un correo de prueba con la configuración de correo actual.'

    def add_arguments(self, parser):
        parser.add_argument('destinatario', nargs='?', default='',
                            help='Correo destino (por defecto ADMIN_EMAIL).')

    def handle(self, *args, **options):
        destino = options['destinatario'] or settings.ADMIN_EMAIL
        if not destino:
            raise CommandError(
                'Sin destinatario: define ADMIN_EMAIL en .env o pásalo como '
                'argumento.')
        if 'localhost' in settings.DEFAULT_FROM_EMAIL:
            raise CommandError(
                'DEFAULT_FROM_EMAIL no está definido en .env: usa el '
                'remitente verificado en SendGrid.')

        backend = settings.EMAIL_BACKEND.rsplit('.', 2)[-2]
        self.stdout.write(f'Backend: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'Remitente: {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write(f'Destino: {destino}')
        if backend == 'console':
            self.stdout.write(self.style.WARNING(
                'Sin SENDGRID_API_KEY: el correo solo se imprime aquí.'))

        try:
            enviados = send_mail(
                subject='Prueba de correo — ERP Django',
                message=('Si lees esto, el envío por SendGrid funciona.\n'
                         f'Enviado: {timezone.now():%Y-%m-%d %H:%M:%S}\n'),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[destino],
                fail_silently=False,
            )
        except Exception as exc:
            raise CommandError(f'Falló el envío: {exc}')

        self.stdout.write(self.style.SUCCESS(
            f'Listo: {enviados} correo(s) entregado(s) a SendGrid. '
            'Revisa tu bandeja (y la carpeta de Spam).'))

#!/bin/sh
# docker-entrypoint.sh — se ejecuta cada vez que arranca el contenedor
# (en tu PC con docker compose y en Render).
set -e

echo "==> [1/5] Aplicando migraciones de la base de datos..."
python manage.py migrate --noinput

echo "==> [2/5] Reuniendo archivos estáticos (CSS, imágenes)..."
python manage.py collectstatic --noinput

echo "==> [3/5] Creando grupos y permisos (Gerente, Vendedor, Almacén)..."
python manage.py crear_grupos

echo "==> [4/5] Verificando superusuario..."
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    python manage.py createsuperuser --noinput \
        || echo "AVISO: no se creó el superusuario (si ya existe, es normal)."
else
    echo "AVISO: faltan las variables DJANGO_SUPERUSER_*; no se crea superusuario."
fi

echo "==> [5/5] Iniciando el servidor en el puerto ${PORT:-8000}..."
exec gunicorn core.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -

#!/bin/sh
# docker-entrypoint.sh — se ejecuta cada vez que arranca el contenedor
# (en tu PC con docker compose y en Render).
set -e

# W16: si el contenedor recibe un comando (command: de docker-compose o el
# "Docker Command" de un Background Worker), se ejecuta tal cual.
if [ "$#" -gt 0 ]; then
    echo "==> [entrypoint] Ejecutando comando: $*"
    exec "$@"
fi

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

# W16: worker de Celery embebido (Render Free no ofrece Background Workers).
# Se activa con CELERY_EMBEDDED_WORKER=1 y requiere REDIS_URL.
# W18: Beat (tareas programadas) va dentro del mismo proceso con --beat.
# Solo debe existir UN Beat: el servicio web debe tener 1 instancia.
# Se desactiva con CELERY_EMBEDDED_BEAT=0. El archivo del schedule va a /tmp
# porque el disco de Render es efimero.
if [ "${CELERY_EMBEDDED_WORKER:-0}" = "1" ] && [ -n "${REDIS_URL:-}" ]; then
    BEAT_OPTS=""
    if [ "${CELERY_EMBEDDED_BEAT:-1}" = "1" ]; then
        BEAT_OPTS="--beat --schedule=/tmp/celerybeat-schedule"
        echo "==> [W18] Celery Beat embebido ACTIVADO (reporte ${REPORTE_DIARIO_HORA:-23:00}, alerta de stock ${ALERTA_STOCK_HORA:-08:05}, hora de Mexico)."
    fi
    echo "==> [W16] Iniciando worker de Celery embebido (cola erp_django)..."
    # shellcheck disable=SC2086
    celery -A core worker --loglevel=info --queues=erp_django --pool=solo         --without-gossip --without-mingle --without-heartbeat $BEAT_OPTS &
else
    echo "==> [W16] Worker de Celery embebido DESACTIVADO."
fi

echo "==> [5/5] Iniciando el servidor en el puerto ${PORT:-8000}..."
exec gunicorn core.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -

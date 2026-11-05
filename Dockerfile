# Dockerfile — imagen del ERP con WeasyPrint (PDF)
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Programas de Linux que WeasyPrint necesita para dibujar el PDF
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libcairo-gobject2 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-liberation \
    fonts-dejavu-core \
    libjpeg62-turbo-dev \
    libpng-dev \
    libwebp-dev \
    zlib1g-dev \
    libpq-dev \
    gcc \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Primero solo requirements.txt: así Docker reutiliza esta capa si no cambió
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Después el código del proyecto
COPY . .

# Seguro extra: quita saltos de línea de Windows (CRLF) del script de arranque
RUN sed -i 's/\r$//' docker-entrypoint.sh && chmod +x docker-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["./docker-entrypoint.sh"]

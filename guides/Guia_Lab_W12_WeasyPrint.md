# Guía de Laboratorio — W12 (Versión WeasyPrint)
## ERP Django · Espiral 4 · Semana 12 de 24
### Técnico en Programación (SEP 3061300006-23) · UTEC Celaya
### Asesor: MC. Román Fernando López González

---

| Campo | Detalle |
|---|---|
| **Semana** | W12 de 24 |
| **Variante** | **WeasyPrint via Docker** (sustituye a xhtml2pdf en la Guía W12 original) |
| **Espiral** | E4 — API REST y Media |
| **Sprint Scrum** | Sprint 3 — Review + Retrospectiva |
| **Hito** | **★ M4: DRF completo + PDF de alta calidad + imágenes + Excel funcionales** |
| **Horario** | 16:45 – 19:45 (180 min) |
| **Nivel Schmelkes** | 3 — Infraestructura |
| **Hilo conductor** | "xhtml2pdf fue el aperitivo. WeasyPrint es el platillo principal: PDFs con imágenes, encabezados y pie de página en cada hoja." |

---

## 1. ¿Por qué esta guía alternativa?

La **Guía Lab W12 original** usa `xhtml2pdf` como motor de PDF.
Es la elección correcta para el entorno USB del aula porque no requiere
librerías de sistema y funciona directamente con el Python portable.

**WeasyPrint** produce PDFs de calidad significativamente superior:

| Característica | xhtml2pdf | WeasyPrint |
|---|---|---|
| Calidad de tipografía | ★★★☆☆ | ★★★★★ |
| Imágenes (logo, fotos) | Soporte limitado | Soporte completo |
| CSS moderno (`flexbox`, `grid`) | No compatible | Compatible |
| `@page` (encabezados/pies por página) | Parcial | Completo |
| `counter(page)` (número de página) | No | Sí |
| Tablas multipágina | Corta filas | Respeta `thead` en cada página |
| Instalación en Windows sin Docker | Compleja (requiere GTK3 runtime) | **Requiere Docker** |
| Instalación en Linux/macOS | `pip install weasyprint` | `pip install weasyprint` |

**Por qué necesitamos Docker en el aula:**
WeasyPrint depende de `libpango-1.0`, `libcairo2` y `libgdk-pixbuf-2.0`
— librerías nativas del sistema operativo que NO pueden instalarse en
el entorno USB portable de Windows sin permisos de administrador.
Docker empaqueta esas librerías dentro del contenedor, resolviendo el
problema de dependencias para el aula y producción con el mismo artefacto.

> **Alternativa nativa en Windows (NO recomendada para el aula):**
> Se puede instalar GTK3 runtime para Windows desde `https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer`.
> Requiere reiniciar, configurar el PATH manualmente y ejecutar como
> administrador. Demasiado frágil para el entorno de aula; Docker
> es la vía confiable.

---

## 2. Prerrequisitos

### 2.1 Docker Desktop instalado y corriendo

```cmd
docker --version
docker-compose --version
```

**Resultado esperado:**
```
Docker version 25.x.x, build xxxxxxx
Docker Compose version v2.x.x
```

Si Docker no está instalado:
1. Descargar desde `https://www.docker.com/products/docker-desktop/`
2. Instalador `.exe` → siguiente × 3 → reiniciar
3. Al abrir Docker Desktop, aceptar la licencia WSL2

### 2.2 Estado del proyecto

```cmd
:: Verificar que el proyecto tiene los archivos base de Docker
dir Dockerfile
dir docker-compose.yml
dir docker-entrypoint.sh
```

Si `docker-entrypoint.sh` y `Dockerfile` no existen aún, esta guía
los crea completos en las Partes 5 y 6.

---

## 3. Dependencias de Sistema de WeasyPrint

WeasyPrint necesita estas librerías nativas instaladas en el sistema
operativo (en Ubuntu/Debian, que es lo que usa el contenedor Docker):

| Librería | Propósito |
|---|---|
| `libpango-1.0-0` | Motor de composición tipográfica |
| `libpangoft2-1.0-0` | Soporte FreeType para Pango |
| `libpangocairo-1.0-0` | Puente entre Pango y Cairo |
| `libcairo2` | Motor de renderizado 2D (PDF, PNG, SVG) |
| `libcairo-gobject2` | Binding GObject de Cairo |
| `libgdk-pixbuf-2.0-0` | Manejo de imágenes (PNG, JPEG, WebP) |
| `libffi-dev` | Interfaz de funciones externas (requerido por cffi) |
| `shared-mime-info` | Base de datos de tipos MIME |
| `fonts-liberation` | Fuentes Liberation (equivalentes a Times, Arial, Courier) |

**¿Por qué tantas librerías?**
WeasyPrint convierte HTML+CSS a PDF usando la misma pila de renderizado
que usa el navegador GTK (WebKitGTK). Cairo genera el PDF; Pango hace
el layout de texto; GDK-PixBuf maneja las imágenes incrustadas.

---

## 4. `requirements.txt` Actualizado

Agregar `weasyprint` al archivo. Se **mantiene** `xhtml2pdf` como
dependencia opcional (para fallback o reportes secundarios):

```txt
# requirements.txt — agregar:

# Motor de PDF de alta calidad (requiere Docker o Linux)
weasyprint==60.2

# Motor de PDF alternativo sin dependencias nativas (fallback)
# xhtml2pdf==0.2.15   ← mantener comentado, disponible si se necesita

# (El resto de requirements existentes permanecen igual)
```

> **Nota sobre versiones:** WeasyPrint 60.x es estable en Python 3.11.
> Versiones 62+ requieren Python 3.9+ pero pueden cambiar el API de
> `weasyprint.HTML()`. Si se actualiza, revisar el parámetro `string`
> vs `filename` en la llamada.

---

## 5. `docker-entrypoint.sh` — Punto de entrada unificado

Este script se ejecuta **siempre** al arrancar el contenedor, tanto
en local (docker-compose) como en Render. Centraliza las tareas de
inicialización que antes estaban dispersas en el `command` del
docker-compose y en el `buildCommand` de render.yaml.

```bash
#!/bin/sh
# docker-entrypoint.sh
# Punto de entrada unificado para el contenedor ERP Django.
# Se ejecuta en LOCAL (docker-compose) y en PRODUCCIÓN (Render).
# ─────────────────────────────────────────────────────────────────
set -e   # detener si cualquier comando falla

echo "==> [entrypoint] Ejecutando migraciones de base de datos..."
python manage.py migrate --noinput

echo "==> [entrypoint] Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear

echo "==> [entrypoint] Verificando la configuración de Django..."
python manage.py check --deploy 2>/dev/null || python manage.py check

echo "==> [entrypoint] Iniciando Gunicorn..."
exec gunicorn core.wsgi \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 120 \
    --log-file - \
    --access-logfile -
```

Dar permisos de ejecución:

```cmd
:: En Windows (Git Bash o WSL):
chmod +x docker-entrypoint.sh

:: Verificar el atributo en git para que se preserve en Linux:
git add docker-entrypoint.sh
git update-index --chmod=+x docker-entrypoint.sh
```

---

## 6. `Dockerfile` Completo y Actualizado

```dockerfile
# Dockerfile
# ERP Django con WeasyPrint
# Base: Python 3.11 sobre Debian Bookworm slim
# ─────────────────────────────────────────────────────────────────

# ── ETAPA 1: imagen base ─────────────────────────────────────────
FROM python:3.11-slim-bookworm AS base

# Evitar archivos .pyc y que Python bufferice la salida
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ── ETAPA 2: dependencias de sistema ─────────────────────────────
FROM base AS system-deps

RUN apt-get update && apt-get install -y --no-install-recommends \
    # ── Dependencias de WeasyPrint ──────────────────────────────
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libcairo-gobject2 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-liberation \
    # ── Fuentes adicionales para mejor tipografía ───────────────
    fonts-dejavu-core \
    # ── Dependencias para Pillow (imágenes en Django) ───────────
    libjpeg62-turbo-dev \
    libpng-dev \
    libwebp-dev \
    zlib1g-dev \
    # ── Cliente PostgreSQL (psycopg2) ───────────────────────────
    libpq-dev \
    gcc \
    # ── Herramientas de diagnóstico (se pueden eliminar en prod) ─
    curl \
 && rm -rf /var/lib/apt/lists/*    # limpiar caché de apt → imagen más pequeña

# ── ETAPA 3: dependencias Python ─────────────────────────────────
FROM system-deps AS python-deps

WORKDIR /app

# Copiar solo requirements primero para aprovechar la caché de capas Docker.
# Si el código cambia pero requirements.txt no, esta capa NO se reconstruye.
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# ── ETAPA 4: código de la aplicación ─────────────────────────────
FROM python-deps AS app

WORKDIR /app

# Copiar el código fuente
COPY . .

# Dar permisos de ejecución al entrypoint
RUN chmod +x docker-entrypoint.sh

# Puerto que expone el contenedor (Gunicorn escucha en 8000)
EXPOSE 8000

# Punto de entrada: siempre ejecuta el entrypoint al arrancar
ENTRYPOINT ["./docker-entrypoint.sh"]
```

> **Detalle clave: imagen multicapa.**
> El orden de `COPY requirements.txt` → `pip install` → `COPY . .`
> no es accidental. Docker cachea cada capa. Si modificas el código
> Python pero no `requirements.txt`, la capa de `pip install` no se
> repite, acelerando el build de ~3 minutos a ~10 segundos.

---

## 7. `docker-compose.yml` Completo — Stack Acumulado W18

Este archivo incluye **todos los servicios** que el proyecto ha acumulado
hasta W18 (web, base de datos, Redis, worker Celery, Beat y Flower).

```yaml
# docker-compose.yml — Stack completo ERP Django con WeasyPrint
# Incluye todos los servicios acumulados hasta W18
version: '3.9'

services:

  # ── PostgreSQL ─────────────────────────────────────────────────
  db:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB:       ${POSTGRES_DB:-erp_db}
      POSTGRES_USER:     ${POSTGRES_USER:-erp_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-erp_pass_local}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-erp_user}"]
      interval: 5s
      timeout: 5s
      retries: 10

  # ── Redis (broker Celery + caché Django) ───────────────────────
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 10

  # ── Aplicación Django (con WeasyPrint) ─────────────────────────
  web:
    build:
      context: .
      dockerfile: Dockerfile
    restart: unless-stopped
    # ENTRYPOINT ya definido en Dockerfile → aquí no se necesita command
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    env_file:
      - .env
    environment:
      DJANGO_SETTINGS_MODULE: core.settings_prod
      DATABASE_URL:   postgresql://${POSTGRES_USER:-erp_user}:${POSTGRES_PASSWORD:-erp_pass_local}@db:5432/${POSTGRES_DB:-erp_db}
      REDIS_URL:      redis://redis:6379/0
      REDIS_CACHE_URL: redis://redis:6379/1

  # ── Celery Worker ──────────────────────────────────────────────
  celery_worker:
    build:
      context: .
      dockerfile: Dockerfile
    restart: unless-stopped
    # Sobreescribir el entrypoint del Dockerfile para esta imagen
    entrypoint: []
    command: celery -A core worker -l info -Q erp_django
    volumes:
      - .:/app
      - media_volume:/app/media   # necesita acceso a media para exportaciones
    depends_on:
      redis:
        condition: service_healthy
      db:
        condition: service_healthy
    env_file:
      - .env
    environment:
      DJANGO_SETTINGS_MODULE: core.settings_prod
      DATABASE_URL:   postgresql://${POSTGRES_USER:-erp_user}:${POSTGRES_PASSWORD:-erp_pass_local}@db:5432/${POSTGRES_DB:-erp_db}
      REDIS_URL:      redis://redis:6379/0

  # ── Celery Beat (scheduler) ────────────────────────────────────
  celery_beat:
    build:
      context: .
      dockerfile: Dockerfile
    restart: unless-stopped
    entrypoint: []
    command: celery -A core beat -l info
    volumes:
      - .:/app
    depends_on:
      redis:
        condition: service_healthy
      db:
        condition: service_healthy
    env_file:
      - .env
    environment:
      DJANGO_SETTINGS_MODULE: core.settings_prod
      DATABASE_URL:   postgresql://${POSTGRES_USER:-erp_user}:${POSTGRES_PASSWORD:-erp_pass_local}@db:5432/${POSTGRES_DB:-erp_db}
      REDIS_URL:      redis://redis:6379/0

  # ── Flower (monitor Celery) ────────────────────────────────────
  flower:
    build:
      context: .
      dockerfile: Dockerfile
    restart: unless-stopped
    entrypoint: []
    command: celery -A core flower --port=5555
    ports:
      - "5555:5555"
    depends_on:
      - redis
      - celery_worker
    env_file:
      - .env
    environment:
      DJANGO_SETTINGS_MODULE: core.settings_prod
      REDIS_URL:      redis://redis:6379/0

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

---

## 8. Build y Arranque Local — Verificar WeasyPrint en el Contenedor

### 8.1 Construir la imagen

```cmd
:: Desde la raíz del proyecto (donde está el Dockerfile)
docker-compose build --no-cache web
```

**El build tarda ~3-5 minutos la primera vez** (descarga la imagen base,
instala las librerías nativas y los paquetes Python). En builds
subsecuentes, Docker usa el caché y tarda ~10-30 segundos.

Salida esperada al final:
```
 => [app 4/4] COPY . .
 => exporting to image
 => => writing image sha256:abc123...
 => => naming to docker.io/library/erp_web
✓ Built
```

### 8.2 Arrancar todos los servicios

```cmd
docker-compose up -d
```

Verificar que todos los servicios están saludables:

```cmd
docker-compose ps
```

**Resultado esperado:**
```
NAME                  SERVICE         STATUS          PORTS
erp-db-1              db              running         0.0.0.0:5432->5432/tcp
erp-redis-1           redis           running         0.0.0.0:6379->6379/tcp
erp-web-1             web             running         0.0.0.0:8000->8000/tcp
erp-celery_worker-1   celery_worker   running
erp-celery_beat-1     celery_beat     running
erp-flower-1          flower          running         0.0.0.0:5555->5555/tcp
```

### 8.3 Verificar que WeasyPrint tiene acceso a todas sus librerías

```cmd
docker-compose exec web python -c "
import weasyprint
print('WeasyPrint version:', weasyprint.__version__)

# Verificar que puede generar un PDF mínimo
from weasyprint import HTML
pdf = HTML(string='<h1>Prueba WeasyPrint</h1><p>ERP Django UTEC</p>').write_pdf()
print('PDF generado:', len(pdf), 'bytes')
print('Primeros bytes (debe ser %PDF):', pdf[:4])
"
```

**Resultado esperado:**
```
WeasyPrint version: 60.2
PDF generado: 1423 bytes
Primeros bytes (debe ser %PDF): b'%PDF'
```

Si ves este resultado, WeasyPrint está completamente funcional dentro
del contenedor con todas sus dependencias nativas disponibles.

### 8.4 Ver los logs del contenedor web

```cmd
docker-compose logs -f web
```

Buscar estas líneas que confirman la inicialización:
```
==> [entrypoint] Ejecutando migraciones de base de datos...
Operations to perform: Apply all migrations...
...OK
==> [entrypoint] Recolectando archivos estáticos...
...
==> [entrypoint] Iniciando Gunicorn...
[INFO] Listening at: http://0.0.0.0:8000
```

---

## 9. Template `factura_pdf.html` Mejorado con WeasyPrint

### 9.1 Ventajas de CSS que SOLO WeasyPrint soporta

```css
/* @page: controla el tamaño y los márgenes de CADA página del PDF */
@page {
    size: A4 portrait;
    margin: 2.5cm 2cm 3cm;  /* top right bottom — bottom mayor para pie de página */

    /* running element: el encabezado se repite en CADA página */
    @top-center { content: element(encabezado-pdf); }

    /* pie de página con número de página */
    @bottom-right {
        content: "Página " counter(page) " de " counter(pages);
        font-size: 9pt;
        color: #5A6A7E;
    }
    @bottom-left {
        content: string(nombre-empresa);
        font-size: 9pt;
        color: #5A6A7E;
    }
}
```

Nada de esto funciona en xhtml2pdf. En WeasyPrint funciona
de fábrica cuando el HTML está dentro de un contenedor Docker
con las librerías correctas.

---

### 9.2 Reemplazar `ventas/templates/ventas/factura_pdf.html`

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Factura {{ pedido.numero_pedido|default:venta.pk }}</title>
    <style>
        /* ── Variables de color Fable 5 AzulERP ──────────────────── */
        :root {
            --navy:  #0A2342;
            --gold:  #B8860B;
            --sky:   #4A90D9;
            --ice:   #E8F0FB;
            --muted: #5A6A7E;
            --text:  #1A1A2E;
        }

        /* ── Configuración de página ──────────────────────────────── */
        @page {
            size: A4 portrait;
            margin: 2cm 2cm 3cm 2cm;

            /* Encabezado de empresa en cada página (excepto la primera) */
            @top-left {
                content: element(header-running);
                margin-top: .5cm;
            }

            /* Número de página en el pie */
            @bottom-right {
                content: "Página " counter(page) " de " counter(pages);
                font-family: Arial, sans-serif;
                font-size: 8.5pt;
                color: #5A6A7E;
                border-top: 1px solid #C8D8EC;
                padding-top: .3cm;
            }

            /* Nombre de empresa en el pie izquierdo */
            @bottom-left {
                content: string(empresa-nombre);
                font-family: Arial, sans-serif;
                font-size: 8.5pt;
                color: #5A6A7E;
                border-top: 1px solid #C8D8EC;
                padding-top: .3cm;
            }
        }

        /* Primera página: sin encabezado (ya tiene el bloque header completo) */
        @page :first {
            @top-left { content: none; }
        }

        /* ── Reset base ─────────────────────────────────────────── */
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, Helvetica, sans-serif;
            font-size: 10.5pt;
            color: var(--text);
            line-height: 1.5;
        }

        /* ── Elemento de running (encabezado en páginas 2+) ───────── */
        #header-running {
            position: running(header-running);
            display: flex;
            align-items: center;
            gap: 12px;
            border-bottom: 2px solid var(--gold);
            padding-bottom: .3cm;
        }
        #header-running .empresa { font-weight: bold; color: var(--navy); }
        #header-running .folio   { margin-left: auto; color: var(--gold); font-weight: bold; }

        /* String para el pie izquierdo */
        #empresa-string { string-set: empresa-nombre content(); }

        /* ── ENCABEZADO (primera página) ───────────────────────────── */
        .header {
            background: var(--navy);
            color: #FFFFFF;
            padding: 18px 24px;
            border-bottom: 4px solid var(--gold);
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 16px;
        }
        .header-logo {
            width: 64px;
            height: 64px;
            object-fit: contain;
            border-radius: 8px;
            background: rgba(255,255,255,.08);
        }
        .header-logo-placeholder {
            width: 64px;
            height: 64px;
            border-radius: 8px;
            background: rgba(255,255,255,.12);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
        }
        .header-title { font-size: 22pt; font-weight: bold; color: var(--gold); }
        .header-empresa { color: rgba(255,255,255,.78); font-size: 10pt; margin-top: 2px; }
        .header-folio {
            margin-left: auto;
            text-align: right;
        }
        .header-folio .folio-num { font-size: 15pt; font-weight: bold; color: var(--gold); }
        .header-folio .folio-fecha { color: rgba(255,255,255,.68); font-size: 9pt; }

        /* ── SECCIÓN DE DATOS DEL CLIENTE ──────────────────────────── */
        .datos-section { margin-bottom: 18px; }
        .datos-tabla {
            width: 100%;
            border-collapse: collapse;
        }
        .datos-tabla td {
            padding: 5px 9px;
            font-size: 9.5pt;
            border: 1px solid var(--ice);
        }
        .datos-tabla .lbl {
            background: var(--ice);
            font-weight: bold;
            color: var(--navy);
            width: 28%;
        }

        /* ── TABLA DE PRODUCTOS ─────────────────────────────────────── */
        .productos-tabla {
            width: 100%;
            border-collapse: collapse;
            margin: 18px 0;
            /* WeasyPrint: repetir thead en cada nueva página */
            border-spacing: 0;
        }
        /* La propiedad que hace que WeasyPrint repita la cabecera */
        thead { display: table-header-group; }
        tfoot { display: table-footer-group; }

        .productos-tabla thead th {
            background: var(--navy);
            color: #FFFFFF;
            padding: 8px 11px;
            font-size: 9pt;
            text-align: left;
            text-transform: uppercase;
            letter-spacing: .04em;
            border-bottom: 3px solid var(--gold);
        }
        .productos-tabla thead th.num { text-align: right; }
        .productos-tabla tbody td {
            padding: 7px 11px;
            font-size: 9.5pt;
            border-bottom: 1px solid var(--ice);
            /* Evitar cortar una fila entre dos páginas */
            page-break-inside: avoid;
        }
        .productos-tabla tbody td.num { text-align: right; }
        .productos-tabla tbody tr:nth-child(even) td { background: #F8FAFD; }

        /* ── TOTALES ───────────────────────────────────────────────── */
        .total-section { margin-top: 12px; }
        .total-tabla { width: 50%; margin-left: 50%; border-collapse: collapse; }
        .total-tabla td {
            padding: 6px 10px;
            font-size: 9.5pt;
            border: 1px solid var(--ice);
        }
        .total-tabla .lbl {
            background: var(--ice);
            font-weight: bold;
            color: var(--navy);
        }
        .total-tabla .val { text-align: right; }
        .total-tabla tr.final td {
            background: #FDF8E8;
            border-top: 2px solid var(--gold);
            font-weight: bold;
            font-size: 11.5pt;
        }
        .total-tabla .val.gold { color: var(--gold); font-size: 12.5pt; }

        /* ── NOTA LEGAL / PIE ─────────────────────────────────────── */
        .nota {
            margin-top: 24px;
            padding: 12px 16px;
            border-left: 4px solid var(--sky);
            background: #F5F9FF;
            font-size: 8.5pt;
            color: var(--muted);
            /* No cortar la nota entre páginas */
            page-break-inside: avoid;
        }
    </style>
</head>
<body>

<!--
    Elemento de running: aparece en el encabezado de las páginas 2, 3, ...
    WeasyPrint lo extrae del flujo normal y lo repite en @top-left de @page.
-->
<div id="header-running">
    <span class="empresa">{{ config.nombre_empresa }}</span>
    {% if config.rfc %}<span style="color:var(--muted);font-size:8.5pt;">RFC: {{ config.rfc }}</span>{% endif %}
    <span class="folio">Factura #{{ venta.pk|stringformat:"05d" }}</span>
</div>

<!-- String invisible para el pie de página izquierdo -->
<span id="empresa-string">{{ config.nombre_empresa }}</span>

<!-- ── ENCABEZADO PRIMERA PÁGINA ───────────────────────────────── -->
<div class="header">
    {% if config.logo %}
        <!--
            base_url en weasyprint.HTML() resuelve esta URL relativa.
            Sin base_url, WeasyPrint no encontraría el archivo de imagen.
        -->
        <img class="header-logo" src="{{ config.logo.url }}" alt="Logo">
    {% else %}
        <div class="header-logo-placeholder">📦</div>
    {% endif %}

    <div>
        <div class="header-title">FACTURA</div>
        <div class="header-empresa">{{ config.nombre_empresa }}</div>
        {% if config.rfc %}
        <div class="header-empresa" style="font-size:9pt;">RFC: {{ config.rfc }}</div>
        {% endif %}
    </div>

    <div class="header-folio">
        <div class="folio-num"># {{ venta.pk|stringformat:"05d" }}</div>
        <div class="folio-fecha">{{ venta.fecha|date:"d/m/Y" }}</div>
        <div class="folio-fecha">{{ venta.fecha|date:"H:i" }} h</div>
    </div>
</div>

<!-- ── DATOS DEL CLIENTE ────────────────────────────────────────── -->
<div class="datos-section">
    <table class="datos-tabla">
        <tr>
            <td class="lbl">Cliente</td>
            <td>{{ venta.cliente.nombre }}</td>
            <td class="lbl">Correo</td>
            <td>{{ venta.cliente.correo }}</td>
        </tr>
        <tr>
            <td class="lbl">Teléfono</td>
            <td>{{ venta.cliente.telefono|default:"—" }}</td>
            <td class="lbl">Moneda</td>
            <td>{{ config.moneda }}</td>
        </tr>
        <tr>
            <td class="lbl">Fecha de emisión</td>
            <td>{{ venta.fecha|date:"d/m/Y H:i" }}</td>
            <td class="lbl">IVA</td>
            <td>{{ config.iva_porcentaje }}%</td>
        </tr>
    </table>
</div>

<!-- ── TABLA DE PRODUCTOS ────────────────────────────────────────── -->
<table class="productos-tabla">
    <thead>
        <tr>
            <th style="width:4%">#</th>
            <th style="width:40%">Producto</th>
            <th class="num" style="width:16%">Precio unit.</th>
            <th class="num" style="width:10%">Cant.</th>
            <th class="num" style="width:14%">Subtotal</th>
        </tr>
    </thead>
    <tbody>
        {% for detalle in venta.detalles.all %}
        <tr>
            <td>{{ forloop.counter }}</td>
            <td>{{ detalle.producto.nombre }}</td>
            <td class="num">${{ detalle.precio_unitario }}</td>
            <td class="num">{{ detalle.cantidad }}</td>
            <td class="num">${{ detalle.subtotal }}</td>
        </tr>
        {% empty %}
        <tr>
            <td colspan="5" style="text-align:center;padding:16px;color:var(--muted);">
                Sin líneas de detalle registradas.
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>

<!-- ── TOTALES ───────────────────────────────────────────────────── -->
<div class="total-section">
    <table class="total-tabla">
        {% with subtotal=venta.total iva_pct=config.iva_porcentaje %}
        <tr>
            <td class="lbl">Subtotal (sin IVA)</td>
            <td class="val">${{ subtotal }}</td>
        </tr>
        <tr>
            <td class="lbl">IVA ({{ iva_pct }}%)</td>
            <td class="val">
                ${% widthratio subtotal 100 iva_pct %}
            </td>
        </tr>
        <tr class="final">
            <td class="lbl" style="font-size:11.5pt;">TOTAL</td>
            <td class="val gold">${{ subtotal }}</td>
        </tr>
        {% endwith %}
    </table>
</div>

<!-- ── NOTA LEGAL ─────────────────────────────────────────────────── -->
<div class="nota">
    <strong>Nota:</strong> Este documento es una representación de la factura generada por
    el sistema ERP Django de {{ config.nombre_empresa }}.
    {% if config.rfc %}RFC: {{ config.rfc }}.{% endif %}
    Generado el {{ hoy|date:"d/m/Y \a \l\a\s H:i" }} h.
</div>

</body>
</html>
```

---

## 10. Actualizar `venta_pdf()` en `ventas/views.py`

### 10.1 Diferencia crítica: `base_url` en WeasyPrint

```python
# xhtml2pdf — no necesita base_url, busca archivos en el sistema de archivos
pisa.CreatePDF(src=html_string, dest=buffer)

# WeasyPrint — NECESITA base_url para resolver rutas de imágenes
# Sin base_url, los <img src="/media/productos/logo.jpg"> no se encuentran
weasyprint.HTML(
    string=html_string,
    base_url=request.build_absolute_uri('/')   # → 'http://localhost:8000/'
).write_pdf()
```

`request.build_absolute_uri('/')` devuelve la URL raíz del servidor
(ej: `http://localhost:8000/`). WeasyPrint la usa como base para
resolver todas las rutas relativas de imágenes en el HTML.

---

### 10.2 Reemplazar la vista `venta_pdf` en `ventas/views.py`

```python
# ventas/views.py — reemplazar la función venta_pdf completa:

@login_required
def venta_pdf(request, venta_id: int) -> HttpResponse:
    """Genera y descarga la factura de una venta en formato PDF.

    Motor: WeasyPrint (requiere Docker o Linux con libpango/cairo/gdk-pixbuf).
    Alternativa de entorno sin Docker: ver Guía W12 original con xhtml2pdf.

    Args:
        request:  HttpRequest de Django.
        venta_id: ID de la venta a generar.

    Returns:
        HttpResponse con Content-Type application/pdf y descarga directa.

    Raises:
        Http404: si la venta no existe.
    """
    import weasyprint   # import local: solo disponible en Docker/Linux

    from datetime import date
    from django.template.loader import render_to_string
    from configuracion.models  import ConfiguracionERP

    venta = get_object_or_404(
        Venta.objects
        .select_related('cliente')
        .prefetch_related('detalles__producto__categoria'),
        pk=venta_id
    )

    config  = ConfiguracionERP.get_instance()
    context = {
        'venta':  venta,
        'config': config,
        'hoy':    date.today(),
    }

    html_string = render_to_string(
        'ventas/factura_pdf.html',
        context,
        request=request   # necesario para template tags que usen request
    )

    # ── WeasyPrint: conversión HTML → PDF ─────────────────────────────
    # base_url: permite que WeasyPrint encuentre imágenes relativas
    # como /media/productos/logo.jpg o /static/css/factura.css.
    # Sin base_url, las imágenes aparecen en blanco en el PDF.
    pdf_bytes = weasyprint.HTML(
        string   = html_string,
        base_url = request.build_absolute_uri('/'),
    ).write_pdf()

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="factura_{venta.pk:05d}.pdf"'
    )
    return response
```

---

## 11. Probar el PDF en Local vía Docker

### 11.1 Acceder a la aplicación

Con todos los contenedores arriba:

```
http://localhost:8000/admin/   → crear datos de prueba si no existen
http://localhost:8000/ventas/  → lista de ventas
http://localhost:8000/ventas/1/pdf/ → descargar factura en PDF
```

### 11.2 Prueba directa desde el contenedor (sin navegador)

```cmd
docker-compose exec web python manage.py shell -c "
import weasyprint

# Generar un PDF de prueba con logo embebido
html = '''
<html>
<head>
<style>
@page { size: A4; margin: 2cm; }
body { font-family: Arial; }
h1 { color: #0A2342; border-bottom: 3px solid #B8860B; padding-bottom: .5rem; }
p.num::after { content: counter(page) ' de ' counter(pages); }
</style>
</head>
<body>
<h1>ERP Django — UTEC Celaya</h1>
<p>Prueba de generación PDF con WeasyPrint 60.x</p>
<p>Página: <span class=num></span></p>
</body>
</html>
'''
pdf = weasyprint.HTML(string=html).write_pdf()
with open('/tmp/prueba_weasyprint.pdf', 'wb') as f:
    f.write(pdf)
print('PDF guardado en /tmp/prueba_weasyprint.pdf')
print('Tamaño:', len(pdf), 'bytes')
"
```

Para copiar el PDF al host y abrirlo:

```cmd
docker cp erp-web-1:/tmp/prueba_weasyprint.pdf C:\Temp\prueba_weasyprint.pdf
start C:\Temp\prueba_weasyprint.pdf
```

---

## 12. Despliegue a Render con Docker

### 12.1 Migrar `render.yaml` de Buildpack a Docker

El `render.yaml` original usaba `env: python` (Render Buildpack).
Para usar el Dockerfile con las dependencias nativas, se migra a
`env: docker`.

```yaml
# render.yaml — versión con Docker (reemplaza la versión buildpack)
services:

  # ── Aplicación Web Django ──────────────────────────────────────
  - type: web
    name: erp-django-utec
    env: docker                          # ← CAMBIO CLAVE vs buildpack
    dockerfilePath: ./Dockerfile         # ruta al Dockerfile en el repo
    dockerContext: .                     # contexto de build (raíz del repo)
    plan: free
    region: oregon

    # ENTRYPOINT ya definido en Dockerfile → no se necesita buildCommand
    # render.yaml no necesita startCommand; usa el ENTRYPOINT del Dockerfile

    healthCheckPath: /

    envVars:
      - key: DJANGO_SETTINGS_MODULE
        value: core.settings_prod
      - key: SECRET_KEY
        generateValue: true
      - key: DEBUG
        value: "False"
      - key: DATABASE_URL
        fromDatabase:
          name: erp-django-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          type: redis
          name: erp-django-redis
          property: connectionString
      - key: REDIS_CACHE_URL
        fromService:
          type: redis
          name: erp-django-redis
          property: connectionString
        # Nota: en producción ideal usar una segunda instancia Redis
        # para separar broker y caché. En el plan gratuito, se usa la misma.
      - key: ALLOWED_HOSTS
        value: ".onrender.com"
      - key: STRIPE_SECRET_KEY
        sync: false
      - key: STRIPE_PUBLISHABLE_KEY
        sync: false
      - key: STRIPE_WEBHOOK_SECRET
        sync: false
      - key: SENDGRID_API_KEY
        sync: false
      - key: DEFAULT_FROM_EMAIL
        value: "ERP Django <noreply@erp-django.com>"
      - key: ADMIN_EMAIL
        sync: false
      - key: AWS_ACCESS_KEY_ID
        sync: false
      - key: AWS_SECRET_ACCESS_KEY
        sync: false
      - key: AWS_STORAGE_BUCKET_NAME
        sync: false

  # ── Celery Worker ──────────────────────────────────────────────
  - type: worker
    name: erp-django-celery-worker
    env: docker
    dockerfilePath: ./Dockerfile
    dockerContext: .
    plan: free
    startCommand: celery -A core worker -l info -Q erp_django
    envVars:
      - key: DJANGO_SETTINGS_MODULE
        value: core.settings_prod
      - key: DATABASE_URL
        fromDatabase:
          name: erp-django-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          type: redis
          name: erp-django-redis
          property: connectionString
      - key: SENDGRID_API_KEY
        sync: false

  # ── Celery Beat ────────────────────────────────────────────────
  - type: worker
    name: erp-django-celery-beat
    env: docker
    dockerfilePath: ./Dockerfile
    dockerContext: .
    plan: free
    numInstances: 1    # CRÍTICO: el Beat scheduler solo debe tener 1 instancia
    startCommand: celery -A core beat -l info
    envVars:
      - key: DJANGO_SETTINGS_MODULE
        value: core.settings_prod
      - key: DATABASE_URL
        fromDatabase:
          name: erp-django-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          type: redis
          name: erp-django-redis
          property: connectionString

  # ── Base de Datos ──────────────────────────────────────────────
databases:
  - name: erp-django-db
    plan: free
    region: oregon
    databaseName: erp_db
    user: erp_user

  # ── Redis ──────────────────────────────────────────────────────
  - name: erp-django-redis
    type: redis
    plan: free
    region: oregon
```

---

### 12.2 Push y despliegue automático

```cmd
git add .
git commit -m "W12-WeasyPrint: Dockerfile + entrypoint + render.yaml docker + factura_pdf mejorada"
git push origin main
```

Render detecta el push automáticamente y:
1. **Build:** ejecuta `docker build` con el `Dockerfile`
2. **Start:** ejecuta el `ENTRYPOINT` (docker-entrypoint.sh)
3. Dentro del entrypoint: `migrate` → `collectstatic` → `gunicorn`

### 12.3 Monitorear el despliegue en Render

1. Ir a `dashboard.render.com`
2. Seleccionar el servicio `erp-django-utec`
3. Pestaña **Logs** → seguir el despliegue en tiempo real

**Líneas clave que buscar:**
```
==> Building Docker image...
Step X: RUN apt-get install -y ... libpango-1.0-0 libcairo2 ...
Step X: RUN pip install ... weasyprint==60.2
==> Build successful

==> Starting service with Dockerfile entrypoint...
==> [entrypoint] Ejecutando migraciones de base de datos...
...OK
==> [entrypoint] Recolectando archivos estáticos...
...
==> [entrypoint] Iniciando Gunicorn...
[INFO] Listening at: http://0.0.0.0:8000
```

---

## 13. Verificación en Producción + Troubleshooting

### 13.1 Verificar el PDF en producción

```
[ ] https://erp-django-utec.onrender.com/accounts/login/ → login
[ ] https://erp-django-utec.onrender.com/ventas/1/pdf/ → descarga PDF
[ ] Abrir PDF → encabezado con logo (si está configurado)
[ ] Abrir PDF → número de página en el pie ("Página 1 de 1")
[ ] Si hay muchas líneas → verificar que el thead se repite en página 2
```

---

### 13.2 Troubleshooting — Errores Comunes de WeasyPrint en Docker

---

**Error 1: `OSError: no library called "cairo" was found`**

```
OSError: no library called "cairo" was found
```

**Causa:** `libcairo2` no está instalado en el contenedor o el entorno Python
no puede encontrar las librerías compartidas del sistema.

**Solución:** verificar que el `Dockerfile` incluye `libcairo2` y `libcairo-gobject2`:
```dockerfile
RUN apt-get install -y --no-install-recommends libcairo2 libcairo-gobject2 ...
```

Luego reconstruir la imagen:
```cmd
docker-compose build --no-cache web
docker-compose up -d web
```

---

**Error 2: `OSError: no library called "pango-1.0" was found`**

**Causa:** `libpango-1.0-0` no está instalado.

**Solución:** mismo procedimiento, verificar el `apt-get install` en el `Dockerfile`.

---

**Error 3: `libgdk_pixbuf-2.0.so.0: cannot open shared object file`**

**Causa:** En Debian Bookworm (versión más nueva), el nombre del paquete
cambió ligeramente en algunas configuraciones.

**Solución:** instalar las dos variantes del nombre:
```dockerfile
libgdk-pixbuf-2.0-0 \
libgdk-pixbuf2.0-0 \
```
Una de las dos existirá según la versión exacta de Debian.

---

**Error 4: `fontconfig: No writable cache directories`**

```
Fontconfig warning: "/etc/fonts/fonts.conf", line X: ...
Fontconfig error: No writable cache directories
```

**Causa:** el proceso no tiene permisos para escribir el caché de fuentes.

**Solución:** agregar al Dockerfile, después de instalar las fuentes:
```dockerfile
RUN fc-cache -f -v 2>/dev/null && chmod -R 777 /var/cache/fontconfig 2>/dev/null || true
```

---

**Error 5: Imágenes en blanco (logo no aparece) en producción**

**Causa:** en producción con S3, la URL del logo es absoluta
(`https://bucket.s3.amazonaws.com/...`) y WeasyPrint necesita acceso
a Internet para descargarla.

**Solución en producción:** verificar que el worker de Render tiene acceso
a la URL del bucket S3. En desarrollo local con Docker, la URL es
relativa (`/media/...`) y se resuelve via `base_url='http://web:8000/'`.

Para la red interna de Docker:
```python
# En vista venta_pdf, dentro del contenedor Docker:
base_url = 'http://web:8000/'   # nombre del servicio en docker-compose
# En lugar de request.build_absolute_uri('/') que daría http://localhost:8000/
```

Solución definitiva (funciona en todos los entornos):
```python
# Usar BASE_URL de settings para tener consistencia
base_url = getattr(settings, 'SITE_DOMAIN', request.build_absolute_uri('/'))
```

---

**Error 6: `django.core.exceptions.ImproperlyConfigured: WeasyPrint is not available`**

**Causa:** se intenta importar WeasyPrint fuera del contenedor (en el
entorno USB/Windows nativo de aula).

**Solución:** asegurarse de ejecutar la generación de PDF siempre dentro
del contenedor Docker, no desde el entorno virtual nativo de Windows.
Ver la sección 8.3 de esta guía.

---

**Error 7: PDF genera pero está en blanco o con CSS incorrecto**

**Causa:** el template usa clases CSS de Bootstrap que se cargan vía CDN.
WeasyPrint intenta descargar el CSS del CDN durante la generación
del PDF; si no hay Internet o el CDN falla, el CSS se ignora.

**Solución:** el template `factura_pdf.html` de esta guía usa EXCLUSIVAMENTE
CSS inline en la etiqueta `<style>`, sin importar nada del CDN.
Verificar que no se heredó base.html (que sí carga Bootstrap del CDN).

---

## 14. Tests del PDF — Ejecutados dentro del Contenedor Docker

### 14.1 ¿Por qué ejecutar los tests dentro del contenedor?

WeasyPrint NO está disponible fuera del contenedor en el entorno
de aula (USB Windows). Ejecutar los tests en el host fallaría con
`ImportError: No module named 'weasyprint'` o
`OSError: no library called "cairo" was found`.

La solución es ejecutar los tests **dentro** del contenedor:

```cmd
:: Ejecutar tests específicos de PDF dentro del contenedor web
docker-compose exec web python manage.py test tests.test_w12_documentos --verbosity=2
```

### 14.2 Actualizar `tests/test_w12_documentos.py`

```python
"""Suite de pruebas W12 — WeasyPrint PDF y exportación Excel.

IMPORTANTE: Estos tests deben ejecutarse dentro del contenedor Docker
donde WeasyPrint y sus dependencias nativas están disponibles.

Ejecutar con:
    docker-compose exec web python manage.py test tests.test_w12_documentos --verbosity=2

NO ejecutar directamente en el host Windows (faltarán las librerías nativas).

Resultado esperado:
    Ran 8 tests in X.XXXs
    OK
"""
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from clientes.models      import Cliente
from configuracion.models import ConfiguracionERP
from productos.models     import Categoria, Producto
from ventas.models        import DetalleVenta, Venta


class VentaPDFWeasyPrintTest(TestCase):
    """Tests de la vista venta_pdf — motor WeasyPrint."""

    def setUp(self):
        ConfiguracionERP.get_instance()
        self.user = User.objects.create_user('pdfuser', password='pass')
        cat        = Categoria.objects.create(nombre='Cat PDF')
        prod       = Producto.objects.create(
            nombre='Producto PDF', precio=Decimal('500.00'),
            stock=5, categoria=cat
        )
        cli        = Cliente.objects.create(
            nombre='Cliente PDF', correo='pdf@test.com'
        )
        self.venta = Venta.objects.create(cliente=cli)
        DetalleVenta.objects.create(
            venta=self.venta, producto=prod,
            cantidad=2, precio_unitario=Decimal('500.00')
        )

    def test_pdf_sin_auth_redirige_a_login(self):
        """GET /ventas/<id>/pdf/ sin login → 302 al login."""
        r = self.client.get(
            reverse('ventas:pdf', args=[self.venta.pk])
        )
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r['Location'])

    def test_pdf_con_auth_devuelve_200(self):
        """GET /ventas/<id>/pdf/ con login → 200."""
        self.client.force_login(self.user)
        r = self.client.get(
            reverse('ventas:pdf', args=[self.venta.pk])
        )
        self.assertEqual(r.status_code, 200)

    def test_pdf_content_type_application_pdf(self):
        """La respuesta debe tener Content-Type application/pdf."""
        self.client.force_login(self.user)
        r = self.client.get(
            reverse('ventas:pdf', args=[self.venta.pk])
        )
        self.assertIn('application/pdf', r.get('Content-Type', ''))

    def test_pdf_empieza_con_header_pdf(self):
        """El contenido del PDF debe empezar con '%PDF' (PDF válido)."""
        self.client.force_login(self.user)
        r = self.client.get(
            reverse('ventas:pdf', args=[self.venta.pk])
        )
        # Los primeros 4 bytes deben ser '%PDF' para un PDF válido
        self.assertTrue(
            r.content[:4] == b'%PDF',
            "La respuesta no es un PDF válido (no empieza con %PDF)"
        )

    def test_pdf_content_disposition_attachment(self):
        """La respuesta debe ser descarga directa (attachment)."""
        self.client.force_login(self.user)
        r = self.client.get(
            reverse('ventas:pdf', args=[self.venta.pk])
        )
        disposition = r.get('Content-Disposition', '')
        self.assertIn('attachment', disposition)
        self.assertIn('.pdf', disposition)

    def test_pdf_venta_inexistente_devuelve_404(self):
        """GET /ventas/9999/pdf/ → 404 Not Found."""
        self.client.force_login(self.user)
        r = self.client.get(
            reverse('ventas:pdf', args=[9999])
        )
        self.assertEqual(r.status_code, 404)

    def test_pdf_es_mayor_que_1kb(self):
        """Un PDF real de WeasyPrint debe tener al menos 1 KB."""
        self.client.force_login(self.user)
        r = self.client.get(
            reverse('ventas:pdf', args=[self.venta.pk])
        )
        self.assertGreater(
            len(r.content), 1024,
            "El PDF parece demasiado pequeño para ser real"
        )

    def test_pdf_excel_exportacion_tambien_funciona(self):
        """La exportación de Excel (openpyxl) debe seguir funcionando."""
        self.client.force_login(self.user)
        r = self.client.get(reverse('productos:exportar_excel'))
        self.assertEqual(r.status_code, 200)
        self.assertIn('spreadsheetml', r.get('Content-Type', ''))
```

### 14.3 Ejecutar los tests completos dentro del contenedor

```cmd
:: Suite completa
docker-compose exec web python manage.py test tests --verbosity=0

:: Solo los tests de PDF
docker-compose exec web python manage.py test tests.test_w12_documentos --verbosity=2

:: Con cobertura de código (si coverage está instalado)
docker-compose exec web coverage run manage.py test tests
docker-compose exec web coverage report
```

---

## CHECKLIST FINAL — Versión WeasyPrint (M4)

### Infraestructura Docker

```
[ ] docker-entrypoint.sh creado con chmod +x y git update-index --chmod=+x
[ ] Dockerfile multicapa: base → system-deps → python-deps → app
[ ] apt-get instala los 8+ paquetes requeridos por WeasyPrint
[ ] libpango-1.0-0 + libpangoft2 + libpangocairo + libcairo2 + libgdk-pixbuf
[ ] fonts-liberation + fonts-dejavu-core para tipografía PDF
[ ] libjpeg, libpng, libwebp para Pillow (imágenes en Django)
[ ] docker-compose.yml: servicios web + db + redis + worker + beat + flower
[ ] docker-compose build --no-cache web → build exitoso sin errores
[ ] docker-compose up -d → todos los servicios en STATUS: running
[ ] docker-compose exec web python -c "import weasyprint; print(weasyprint.__version__)" → 60.2
```

### WeasyPrint en Local

```
[ ] Verificación: PDF de prueba generado dentro del contenedor
[ ] Primeros bytes del PDF: b'%PDF'
[ ] base_url correctamente configurado en venta_pdf()
[ ] factura_pdf.html: usa solo CSS inline (sin CDN de Bootstrap)
[ ] factura_pdf.html: @page con @bottom-right counter(page)
[ ] factura_pdf.html: thead con display:table-header-group
  (se repite en cada página si la factura tiene muchas líneas)
[ ] factura_pdf.html: encabezado running element para páginas 2+
[ ] factura_pdf.html: logo visible si config.logo existe
[ ] http://localhost:8000/ventas/1/pdf/ → PDF descargable
[ ] PDF descargado: abrir en Adobe Reader o Preview
[ ] PDF: número de página visible en el pie
[ ] PDF: encabezado de empresa visible en páginas 2, 3...
```

### Despliegue a Render

```
[ ] render.yaml migrado de env:python a env:docker
[ ] dockerfilePath: ./Dockerfile
[ ] Celery worker y beat también usan env:docker
[ ] numInstances: 1 en celery_beat
[ ] git push main → build Docker automático en Render
[ ] Logs de Render: "apt-get install ... libpango-1.0-0 ... OK"
[ ] Logs de Render: "pip install ... weasyprint==60.2 ... OK"
[ ] Logs de Render: "entrypoint → migrate → collectstatic → gunicorn"
[ ] https://erp-django-utec.onrender.com/ventas/1/pdf/ → PDF en producción
[ ] PDF en producción: logo visible (si S3 configurado y accesible)
```

### Tests dentro del contenedor

```
[ ] docker-compose exec web python manage.py test tests.test_w12_documentos
  → 8/8 tests OK
[ ] test_pdf_empieza_con_header_pdf → content[:4] == b'%PDF'
[ ] test_pdf_es_mayor_que_1kb → len(content) > 1024
[ ] docker-compose exec web python manage.py test tests --verbosity=0
  → todos los tests OK
```

---

## DIAGRAMA: Arquitectura de generación PDF con WeasyPrint

```
ENTORNO LOCAL (Docker Desktop)
─────────────────────────────────────────────────────────
Browser → GET /ventas/1/pdf/
    │
    ▼
Docker Container: erp-web-1
    │  (Ubuntu/Debian con libpango + libcairo + libgdk-pixbuf)
    │
    ├─ ventas/views.py → venta_pdf(request, venta_id=1)
    │       │
    │       ├─ Venta.objects.get(pk=1) [PostgreSQL en container erp-db-1]
    │       ├─ ConfiguracionERP.get_instance()
    │       │
    │       ├─ render_to_string('ventas/factura_pdf.html', context, request)
    │       │       → HTML string con CSS inline + @page rules
    │       │
    │       └─ weasyprint.HTML(
    │               string=html_string,
    │               base_url='http://localhost:8000/'
    │           ).write_pdf()
    │               │
    │               ├─ Pango: layout del texto (fuentes, párrafos)
    │               ├─ Cairo: renderiza cada elemento a primitivas PDF
    │               ├─ GDK-PixBuf: decodifica imágenes (logo.jpg → RGB)
    │               └─ → bytes PDF (b'%PDF...')
    │
    └─ HttpResponse(pdf_bytes, content_type='application/pdf')
       Content-Disposition: attachment; filename="factura_00001.pdf"
           │
           ▼
Browser → descarga factura_00001.pdf ✅

─────────────────────────────────────────────────────────
PRODUCCIÓN (Render.com — Docker)
─────────────────────────────────────────────────────────
Browser → GET https://erp-django-utec.onrender.com/ventas/1/pdf/
    │
    ▼
Render: servicio erp-django-utec (Docker)
    │  MISMO Dockerfile → MISMAS librerías de sistema
    │
    ├─ render.yaml: env=docker, dockerfilePath=./Dockerfile
    ├─ build: apt-get instala libpango, libcairo, libgdk-pixbuf
    ├─ deploy: ENTRYPOINT ./docker-entrypoint.sh
    │
    └─ [mismo flujo que en local]
            │
            ▼
       factura_00001.pdf ✅ con calidad idéntica al entorno local
```

---

## Comparativa Final: xhtml2pdf vs WeasyPrint

| Aspecto | xhtml2pdf | WeasyPrint |
|---|---|---|
| **Calidad del PDF** | Aceptable para reportes simples | Profesional — idéntica a imprimir desde un navegador |
| **@page (encabezados/pies)** | Soporte mínimo | Completo: running headers, counter(page), @top/@bottom |
| **thead en multipágina** | Se pierde en páginas 2+ | Se repite en cada página con `thead { display: table-header-group }` |
| **Imágenes (logo)** | Limitado, ruta relativa compleja | Completo con `base_url` |
| **CSS Grid / Flexbox** | No compatible | Compatible |
| **Entorno sin Docker (Windows)** | ✅ Funciona con pip install | ❌ Requiere GTK3 runtime (complejo) |
| **Entorno Docker / Linux** | ✅ pip install | ✅ pip install + 8 libs de sistema |
| **Render.com (Docker)** | ✅ Sin cambios en Dockerfile | ✅ Con libs en Dockerfile |
| **Velocidad de generación** | ~0.2s para facturas pequeñas | ~0.8s para facturas pequeñas |
| **Tests en CI/CD** | Desde el host | Debe ejecutarse dentro del contenedor |
| **Caso de uso ideal** | Aula sin Docker, reportes rápidos | Producción, PDFs profesionales |

**Recomendación final:**
- **Aula (USB Windows, sin Docker):** mantener xhtml2pdf (Guía W12 original)
- **Con Docker local o Render.com:** usar WeasyPrint (esta guía)
- **Proyecto final de carrera o portafolio profesional:** WeasyPrint siempre

---

*Guía de Laboratorio W12 — Versión WeasyPrint*
*Espiral 4 Cierre · Sprint 3 Review · Hito M4 (variante Docker)*
*SEP 3061300006-23 · UTEC Celaya · MC. Román Fernando López González*

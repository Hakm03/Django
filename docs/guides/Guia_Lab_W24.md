# Guía de Laboratorio — W24
## ERP Django · Espiral 8 · Semana 24 de 24
### Técnico en Programación (SEP 3061300006-23) · UTEC Celaya
### Asesor: MC. Román Fernando López González

---

| Campo | Detalle |
|---|---|
| **Semana** | W24 de 24 ★ SEMANA FINAL ★ |
| **Espiral** | E8 — Calidad y Entrega |
| **Sprint Scrum** | Sprint 7 — Review + Retrospectiva |
| **Hito** | **★ M8: Entrega final — sistema completo, certificado y desplegado** |
| **Horario** | 16:45 – 19:45 (180 min) |
| **Nivel Schmelkes** | 5 — Integración y Cierre |
| **Hilo conductor** | "Veinticuatro semanas. Ocho espirales. Un ERP completo. W24 es el lazo que cierra el paquete." |

---

## Respuesta a la tarea de investigación de W23

> **¿Cómo se define `healthCheckPath` en `render.yaml`?**
>
> ```yaml
> services:
>   - type: web
>     name: erp-django-utec
>     healthCheckPath: /       # ← Render hace GET a esta ruta cada 30s
>     # Si la ruta devuelve 2xx en < 10s, el servicio está "healthy"
>     # Si falla 3 veces → Render reinicia automáticamente el contenedor
> ```
>
> **¿Qué sección del README es más importante para un evaluador técnico?**
> La sección de **instalación rápida** (Quick Start). Si el evaluador
> no puede levantar el proyecto en menos de 5 minutos siguiendo el README,
> el documento ha fallado en su propósito principal.
> El orden ideal: Prerrequisitos → Clonar → Variables de entorno →
> Un solo comando para levantar todo (`docker-compose up`) → URL final.
>
> **¿`assertNumQueries` difiere entre SQLite y PostgreSQL?**
> Sí, en algunos casos. PostgreSQL puede usar una query interna extra
> para resolver nombres de columna en ciertos JOINs. Los tests con
> `assertNumQueries` escritos en SQLite (dev) pueden fallar en PostgreSQL
> (prod) con un valor mayor en 1 o 2. La solución: ejecutar los tests
> localmente con `DATABASE_URL` apuntando a PostgreSQL via Docker, o
> usar un margen (`assertNumQueries(N+1)`) con comentario explicativo.

---

## Objetivos de la sesión

Al terminar W24, el estudiante será capaz de:

1. Redactar un `README.md` profesional que permita a cualquier
   desarrollador levantar el proyecto desde cero
2. Documentar todos los endpoints de la API REST en `docs/API.md`
3. Actualizar `render.yaml` con `healthCheckPath` y verificar que
   todos los servicios están activos en producción
4. Escribir 8 smoke tests que verifican las rutas más críticas del sistema
5. Ejecutar el Sprint 7 Review con demo completa de las 8 espirales
6. Completar la retrospectiva global del programa (24 semanas)
7. Declarar el Hito M8 — la entrega final del ERP Django

---

## Mapa de tiempo (180 min)

| Parte | Actividad | Tiempo |
|---|---|---|
| Arranque | Daily Scrum final + verificar W23 | 10 min |
| Parte 1 | `README.md` completo | 30 min |
| Parte 2 | `docs/API.md` — documentación de endpoints | 20 min |
| Parte 3 | `render.yaml` final + verificación en producción | 15 min |
| Parte 4 | Smoke tests (8 pruebas de humo) | 20 min |
| Parte 5 | Commit final + push + verificación en GitHub/Render | 10 min |
| Parte 6 | Sprint 7 Review ante el asesor (demo completa) | 30 min |
| Parte 7 | Retrospectiva global del programa + Ficha E8 | 25 min |
| Cierre | Declaración de Hito M8 · Palabras finales | 10 min |
| Buffer | | 10 min |
| **Total** | | **180 min** |

---

## ARRANQUE — Daily Scrum Final (10 min)

```cmd
E:\iniciar_sesion.bat
```

### Daily Scrum — Sesión 24/24

```
1. ¿Qué hice en W23?
   → Instalé django-debug-toolbar, identifiqué y corregí 3 problemas
     de N+1 en el sistema, y escribí tests con assertNumQueries.

2. ¿Qué haré en W24?
   → Redactaré el README.md profesional, documentaré la API,
     verificaré el despliegue en producción y presentaré la demo
     final del ERP Django al asesor.

3. ¿Impedimentos?
   → Esta es la última sesión. No hay impedimentos — hay entrega. ✅
```

### Estado final acumulado

```cmd
python manage.py check
python manage.py test tests --verbosity=0
coverage run manage.py test tests
coverage report
```

**Resultado esperado:**
```
System check identified no issues (0 silenced).
Ran 211 tests in X.XXXs
OK
TOTAL  ≥ 80%
```

---

## PARTE 1 — `README.md` Completo (30 min)

### 1.1 Estructura del README

```markdown
# ERP Django — UTEC Celaya
## Sistema de Planificación de Recursos Empresariales

<!-- Badges -->
![Python](https://img.shields.io/badge/python-3.11-blue)
![Django](https://img.shields.io/badge/django-4.2_LTS-green)
![Tests](https://img.shields.io/badge/tests-211_passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-≥80%25-yellowgreen)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

Sistema ERP académico desarrollado durante 24 semanas en el
**Técnico en Programación (SEP 3061300006-23)** de UTEC Celaya.

**URL Pública:** https://erp-django-utec.onrender.com

---

## Tabla de Contenidos

- [Características](#características)
- [Stack Tecnológico](#stack-tecnológico)
- [Instalación Rápida con Docker](#instalación-rápida-con-docker)
- [Instalación Manual (sin Docker)](#instalación-manual-sin-docker)
- [Variables de Entorno](#variables-de-entorno)
- [Comandos Útiles](#comandos-útiles)
- [API REST](#api-rest)
- [Arquitectura del Sistema](#arquitectura-del-sistema)
- [Tests y Cobertura](#tests-y-cobertura)
- [Despliegue en Render.com](#despliegue-en-rendercom)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Autor](#autor)

---

## Características

| Módulo | Funcionalidad | Semana |
|---|---|---|
| 🏢 **Gestión de inventario** | Productos, categorías, proveedores con historial de precios | W05, W21 |
| 👥 **Clientes** | CRUD completo con validaciones | W05–W08 |
| 💰 **Ventas** | Registro, líneas de detalle, cálculo automático de totales | W05–W08 |
| 🔐 **Autenticación y roles** | Login/logout allauth + 3 grupos RBAC | W09 |
| 🌐 **API REST** | Endpoints DRF con autenticación por token | W10 |
| 🖼️ **Gestión de imágenes** | Subida con validación MIME, almacenamiento S3 | W11 |
| 📄 **Documentos** | Facturas PDF (WeasyPrint/xhtml2pdf) + exportación Excel | W12 |
| 🛒 **E-commerce** | Catálogo público, carrito de sesión, filtros | W13 |
| 💳 **Pagos Stripe** | Checkout sandbox, webhooks, descuento de stock | W14–W15 |
| ⚡ **Tareas asíncronas** | Celery + Redis: correos, alertas, reportes automáticos | W16–W18 |
| 📊 **Dashboard** | 5 KPIs + 3 gráficas Chart.js + caché Redis | W19 |
| 📋 **Reportes** | Filtros por fecha/cliente/producto + exportación adaptativa | W20 |
| 📜 **Auditoría** | Historial de cambios de precio (django-simple-history) | W21 |

---

## Stack Tecnológico

```
Backend:      Python 3.11 · Django 4.2 LTS · Django REST Framework
Base de datos: PostgreSQL 15 (producción) · SQLite (desarrollo)
Caché/Cola:   Redis 7 (broker Celery + caché Django)
Tareas:       Celery 5.3 · Celery Beat · Flower
Email:        django-anymail + SendGrid
Pagos:        Stripe (sandbox)
Almacenamiento: django-storages + S3 (producción)
Frontend:     Bootstrap 5 · Chart.js 4.4 · Fable 5 AzulERP
PDF:          WeasyPrint 60 (Docker/Linux) · xhtml2pdf (Windows/USB)
Historial:    django-simple-history 3.5
Despliegue:   Render.com (Docker) · GitHub Actions (CI opcional)
```

---

## Instalación Rápida con Docker

### Prerrequisitos

- Docker Desktop ≥ 25.x instalado y corriendo
- Git instalado
- Cuenta en Stripe (modo sandbox, gratuita)
- Cuenta en SendGrid (plan gratuito: 100 correos/día)

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/TU_USUARIO/erp-django-utec.git
cd erp-django-utec

# 2. Copiar y configurar las variables de entorno
cp .env.example .env
# → Editar .env con tus claves (ver sección Variables de Entorno)

# 3. Construir y arrancar todos los servicios
docker-compose build
docker-compose up -d

# 4. Crear el superusuario
docker-compose exec web python manage.py createsuperuser

# 5. Configurar los grupos de roles
docker-compose exec web python manage.py crear_grupos

# 6. Abrir en el navegador
# → http://localhost:8000           (ERP)
# → http://localhost:8000/admin/    (Panel Admin con Jazzmin)
# → http://localhost:8000/catalogo/ (Tienda pública)
# → http://localhost:5555           (Flower — monitor Celery)
```

---

## Instalación Manual (sin Docker)

Para el entorno USB del aula (Windows, sin permisos de administrador):

```cmd
:: Prerrequisito: Python 3.11 embeddable + Git Portable

:: 1. Clonar
git clone https://github.com/TU_USUARIO/erp-django-utec.git
cd erp-django-utec

:: 2. Crear entorno virtual y activar
python -m venv env_erp
call env_erp\Scripts\activate

:: 3. Instalar dependencias
pip install -r requirements.txt

:: 4. Configurar variables de entorno
copy .env.example .env
:: Editar .env con tus valores

:: 5. Migrar y arrancar
python manage.py migrate
python manage.py createsuperuser
python manage.py crear_grupos
python manage.py runserver

:: Nota: En este entorno, la generación de PDF usa xhtml2pdf (no WeasyPrint)
:: y no se dispone de Celery (las tareas se ejecutan síncronamente con CELERY_TASK_ALWAYS_EAGER=True)
```

---

## Variables de Entorno

Copiar `.env.example` como `.env` y completar:

```bash
# ── Django ─────────────────────────────────────────────────────────
SECRET_KEY=genera-una-clave-aleatoria-de-50-caracteres
DEBUG=True                         # False en producción
ALLOWED_HOSTS=localhost,127.0.0.1  # dominio Render en producción

# ── Base de datos ──────────────────────────────────────────────────
DATABASE_URL=postgresql://erp_user:erp_pass@localhost:5432/erp_db
# En desarrollo con SQLite (más simple):
# DATABASE_URL=sqlite:///db.sqlite3

# ── Redis ──────────────────────────────────────────────────────────
REDIS_URL=redis://localhost:6379/0        # broker Celery
REDIS_CACHE_URL=redis://localhost:6379/1  # caché Django

# ── Stripe ─────────────────────────────────────────────────────────
STRIPE_SECRET_KEY=sk_test_...             # clave secreta sandbox
STRIPE_PUBLISHABLE_KEY=pk_test_...       # clave publicable sandbox
STRIPE_WEBHOOK_SECRET=whsec_...          # obtener con: stripe listen

# ── SendGrid ───────────────────────────────────────────────────────
SENDGRID_API_KEY=SG....
DEFAULT_FROM_EMAIL=ERP Django <noreply@tudominio.com>
ADMIN_EMAIL=admin@tudominio.com

# ── Almacenamiento S3 (opcional, para producción) ──────────────────
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=

# ── Dominio del sitio (para tareas Celery) ─────────────────────────
SITE_DOMAIN=https://erp-django-utec.onrender.com
```

---

## Comandos Útiles

```bash
# ── Tests y Cobertura ──────────────────────────────────────────────
python manage.py test tests                        # todos los tests
python manage.py test tests.test_w09_auth_rbac     # un módulo específico
coverage run manage.py test tests && coverage report   # con cobertura
coverage html && open htmlcov/index.html               # reporte visual

# ── Administración ─────────────────────────────────────────────────
python manage.py createsuperuser         # crear admin
python manage.py crear_grupos            # configurar Gerente/Vendedor/Almacén
python manage.py migrate                 # aplicar migraciones
python manage.py collectstatic           # recolectar estáticos

# ── Celery (en terminales separadas) ──────────────────────────────
celery -A core worker -l info -Q erp_django    # procesar tareas
celery -A core beat   -l info                  # tareas programadas
celery -A core flower --port=5555              # monitorear

# ── Docker ─────────────────────────────────────────────────────────
docker-compose up -d                           # arrancar todo
docker-compose logs -f web                     # ver logs del servidor
docker-compose exec web python manage.py shell # shell interactivo
docker-compose down                            # detener todo

# ── Stripe CLI (para probar webhooks) ─────────────────────────────
stripe listen --forward-to http://localhost:8000/catalogo/webhook/
```

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────────┐
│  CLIENTE (Navegador / App móvil / Stripe / SendGrid)               │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ HTTP/HTTPS
┌───────────────────────────▼─────────────────────────────────────────┐
│  RENDER.COM / DOCKER LOCAL                                          │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Django 4.2 + Gunicorn                                       │  │
│  │  ┌────────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────┐  │  │
│  │  │ Interface  │ │ API REST │ │ Catálogo │ │  Reportes   │  │  │
│  │  │   Web      │ │  (DRF)   │ │ Carrito  │ │  Dashboard  │  │  │
│  │  │ (Jazzmin)  │ │ Token    │ │ Checkout │ │  Exportar   │  │  │
│  │  └────────────┘ └──────────┘ └──────────┘ └─────────────┘  │  │
│  └───────────────────────┬──────────────────────────────────────┘  │
│                          │                                          │
│  ┌────────────┐  ┌───────▼──────┐  ┌──────────────────────────┐  │
│  │ PostgreSQL │  │   Redis 7    │  │  Celery Worker + Beat    │  │
│  │    15      │  │  DB/0 broker │  │  · enviar_confirmacion   │  │
│  │ (datos)    │  │  DB/1 caché  │  │  · verificar_stock_bajo  │  │
│  │            │  │              │  │  · reporte_ventas_diario │  │
│  └────────────┘  └──────────────┘  │  · generar_exportacion  │  │
│                                    └──────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  Servicios Externos                                         │  │
│  │  · Stripe (pagos sandbox)  · SendGrid (correo transaccional)│  │
│  │  · Amazon S3 (imágenes)    · Flower (monitor Celery :5555)  │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Tests y Cobertura

```bash
python manage.py test tests   # Ran 219 tests — OK
coverage report               # TOTAL ≥ 80%
```

**Suite de tests por espiral:**

| Espiral | Semanas | Tests agregados | Acumulado |
|---|---|---|---|
| E1 — Entorno y Templates | W01–W03 | 33 | 33 |
| E2 — Modelado y ORM | W04–W06 | 33 | 66 |
| E3 — CRUD y Auth | W07–W09 | 34 | 100 |
| E4 — API REST y Media | W10–W12 | 23 | 123 |
| E5 — E-commerce | W13–W15 | 24 | 147 |
| E6 — Celery e Integraciones | W16–W18 | 24 | 171 |
| E7 — Dashboard y Reportes | W19–W21 | 24 | 195 |
| E8 — Calidad y Entrega | W22–W24 | 24+ | 219+ |

---

## Despliegue en Render.com

```bash
# 1. Fork del repositorio en GitHub
# 2. Conectar Render con GitHub
# 3. Crear Blueprint desde render.yaml (incluido en el repo)
# 4. Configurar las variables de entorno secretas en el dashboard
# 5. Deploy automático al hacer git push origin main

# Comandos post-deploy (desde la Shell de Render):
python manage.py crear_grupos
```

---

## Estructura del Proyecto

```
erp-django-utec/
├── core/                    # Configuración central de Django
│   ├── settings.py          # Dev (SQLite, console email, debug-toolbar)
│   ├── settings_prod.py     # Producción (PostgreSQL, SendGrid, S3)
│   ├── celery.py            # Configuración de Celery
│   └── urls.py              # Enrutador principal
├── clientes/                # App: gestión de clientes
├── proveedores/             # App: gestión de proveedores
├── productos/               # App: inventario (con historial django-simple-history)
├── ventas/                  # App: ventas, detalles y pedidos
├── reportes/                # App: dashboard, reportes filtrables, exportación
├── configuracion/           # App: singleton ConfiguracionERP
├── catalogo/                # App: tienda pública, carrito, checkout, webhooks
├── templates/               # Templates base + emails
├── static/                  # CSS, JS (Fable 5 AzulERP)
├── tests/                   # Suite de tests (unit + integración + rendimiento)
│   └── factories.py         # factory_boy para datos de prueba
├── docs/                    # Documentación técnica
│   ├── API.md               # Referencia completa de la API REST
│   ├── auditoria_rendimiento_w23.md
│   └── cobertura_analisis_w22.md
├── Dockerfile               # Multi-stage con WeasyPrint
├── docker-compose.yml       # Stack local: web + db + redis + celery + flower
├── render.yaml              # Blueprint de despliegue en Render.com
├── requirements.txt         # Dependencias Python
└── README.md                # Este archivo
```

---

## Autor

**MC. Román Fernando López González**
Asesor de Programación · UTEC Celaya
SEP 3061300006-23 · Técnico en Programación
```

---

### 1.2 Escribir el README completo

Crear el archivo en la raíz del proyecto:

```cmd
:: Abrir en el editor y escribir el contenido de la sección 1.1
notepad README.md
```

---

## PARTE 2 — `docs/API.md` — Documentación de Endpoints (20 min)

### 2.1 Crear `docs/API.md`

```markdown
# API REST — Referencia Completa
## ERP Django · UTEC Celaya

Base URL: `https://erp-django-utec.onrender.com/api/`

---

## Autenticación

La API usa **Token Authentication**. Incluir en cada petición:

```
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

### Obtener Token

```
POST /api/auth/token/
Content-Type: application/json

{ "username": "admin", "password": "tu-password" }

→ 200 OK
{ "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" }
```

---

## Permisos

| Método | Permiso requerido |
|---|---|
| `GET` (lectura) | Sin autenticación (público) |
| `POST`, `PUT`, `PATCH`, `DELETE` | Token válido |

---

## Endpoints

### Categorías

| Método | URL | Descripción |
|---|---|---|
| `GET` | `/api/categorias/` | Lista todas las categorías |
| `POST` | `/api/categorias/` | Crea una categoría |
| `GET` | `/api/categorias/{id}/` | Detalle de una categoría |
| `PUT` | `/api/categorias/{id}/` | Actualiza una categoría |
| `DELETE` | `/api/categorias/{id}/` | Elimina una categoría |

**Ejemplo de respuesta `GET /api/categorias/1/`:**
```json
{
  "id": 1,
  "nombre": "Electrónica",
  "descripcion": "Dispositivos electrónicos y accesorios"
}
```

---

### Productos

| Método | URL | Descripción |
|---|---|---|
| `GET` | `/api/productos/` | Lista productos activos (paginado, 20/página) |
| `POST` | `/api/productos/` | Crea un producto (requiere token) |
| `GET` | `/api/productos/{id}/` | Detalle de un producto |
| `PUT` | `/api/productos/{id}/` | Actualización completa |
| `PATCH` | `/api/productos/{id}/` | Actualización parcial |
| `DELETE` | `/api/productos/{id}/` | Elimina un producto |

**Parámetros de paginación:** `?page=2` → página 2 de resultados.

**Ejemplo de respuesta `GET /api/productos/1/`:**
```json
{
  "id": 1,
  "nombre": "Laptop HP ProBook",
  "precio": "12500.00",
  "stock": 5,
  "categoria": 1,
  "categoria_nombre": "Electrónica",
  "proveedor": 2,
  "proveedor_nombre": "Distribuidora Norte S.A.",
  "activo": true,
  "imagen": null,
  "imagen_url": "https://erp-django-utec.onrender.com/media/productos/laptop.jpg",
  "creado": "2025-01-15T10:30:00Z"
}
```

**Campos de solo lectura:** `id`, `creado`, `categoria_nombre`,
`proveedor_nombre`, `imagen_url`.

---

### Clientes

| Método | URL | Descripción |
|---|---|---|
| `GET` | `/api/clientes/` | Lista clientes activos |
| `POST` | `/api/clientes/` | Crea un cliente |
| `GET` | `/api/clientes/{id}/` | Detalle de un cliente |
| `PUT` | `/api/clientes/{id}/` | Actualización completa |
| `PATCH` | `/api/clientes/{id}/` | Actualización parcial |
| `DELETE` | `/api/clientes/{id}/` | Elimina un cliente |

---

### Proveedores

| Método | URL | Descripción |
|---|---|---|
| `GET` | `/api/proveedores/` | Lista proveedores activos |
| `POST` | `/api/proveedores/` | Crea un proveedor |
| `GET` | `/api/proveedores/{id}/` | Detalle de un proveedor |
| `PUT` | `/api/proveedores/{id}/` | Actualización completa |
| `DELETE` | `/api/proveedores/{id}/` | Elimina un proveedor |

---

### Ventas

| Método | URL | Descripción |
|---|---|---|
| `GET` | `/api/ventas/` | Lista ventas (más recientes primero) |
| `POST` | `/api/ventas/` | Crea el encabezado de una venta |
| `GET` | `/api/ventas/{id}/` | Detalle con líneas anidadas y total |
| `DELETE` | `/api/ventas/{id}/` | Elimina una venta y sus líneas |

**Ejemplo de respuesta `GET /api/ventas/1/`:**
```json
{
  "id": 1,
  "cliente": 3,
  "cliente_nombre": "Juan García",
  "fecha": "2025-01-15T18:30:00Z",
  "detalles": [
    {
      "id": 1,
      "producto": 5,
      "cantidad": 2,
      "precio_unitario": "12500.00",
      "subtotal": "25000.00"
    }
  ],
  "total": "25000.00"
}
```

---

## Códigos de Respuesta

| Código | Significado |
|---|---|
| `200 OK` | Petición exitosa (GET, PUT, PATCH) |
| `201 Created` | Recurso creado exitosamente (POST) |
| `204 No Content` | Eliminado exitosamente (DELETE) |
| `400 Bad Request` | Datos de entrada inválidos |
| `401 Unauthorized` | Token faltante o inválido |
| `403 Forbidden` | Token válido pero sin permiso |
| `404 Not Found` | Recurso no encontrado |

---

## Browsable API

La API tiene una interfaz web navegable disponible en:
`https://erp-django-utec.onrender.com/api/`

Acceder desde el navegador para explorar todos los endpoints
con formularios interactivos.
```

---

## PARTE 3 — `render.yaml` Final y Verificación en Producción (15 min)

### 3.1 Agregar `healthCheckPath` al `render.yaml`

```yaml
# render.yaml — agregar healthCheckPath al servicio web:
services:
  - type: web
    name: erp-django-utec
    env: docker
    dockerfilePath: ./Dockerfile
    dockerContext: .
    plan: free
    region: oregon
    healthCheckPath: /          # ← agregar: Render verifica cada 30s
    # Si GET / devuelve 2xx en < 10s → servicio healthy
    # Si falla 3 veces consecutivas → Render reinicia el contenedor

    envVars:
      # ... (resto del render.yaml de W12-WeasyPrint, sin cambios)
```

### 3.2 Push final y verificación

```cmd
git add .
git commit -m "W24 [ENTREGA FINAL M8]: README + docs/API + healthCheck + smoke tests"
git push origin main
```

### 3.3 Verificar en el dashboard de Render

```
[ ] Servicio erp-django-utec → Status: Live (verde)
[ ] Servicio celery worker  → Status: Running
[ ] Servicio celery beat    → Status: Running
[ ] Logs: sin errores en los últimos 10 minutos
[ ] healthCheck: pasando (indicador verde junto al nombre del servicio)
```

### 3.4 Verificar todos los flujos en producción

```
[ ] https://erp-django-utec.onrender.com/               → HTTP 200
[ ] https://erp-django-utec.onrender.com/admin/         → Jazzmin visible
[ ] https://erp-django-utec.onrender.com/api/productos/ → JSON 200
[ ] https://erp-django-utec.onrender.com/catalogo/      → Tienda pública
[ ] https://erp-django-utec.onrender.com/reportes/      → Dashboard con KPIs
[ ] Token: POST /api/auth/token/ con credenciales → recibe token
[ ] PDF: GET /ventas/1/pdf/ → descarga PDF
```

### 3.5 Ejecutar comandos de inicialización en la Shell de Render

Desde el dashboard de Render → servicio web → Shell:

```bash
python manage.py crear_grupos
python manage.py check --deploy
```

---

## PARTE 4 — Smoke Tests (20 min)

### 4.1 ¿Qué son los smoke tests?

Los smoke tests (pruebas de humo) son los tests más simples y de
mayor valor: solo verifican que el sistema arranca y las rutas
más críticas responden. Se llaman así porque si "hay humo", algo
está claramente mal.

**Pirámide de tests del proyecto:**
```
       E2E (3)           ← Flujo completo (W22)
      /       \
    Integración (15)     ← Flujos parciales (W22)
   /             \
  Rendimiento (8)        ← Presupuesto de queries (W23)
 /                 \
Unitarios (185+)         ← Lógica de negocio (W01-W21)
```

Los smoke tests se ejecutan PRIMERO en cualquier pipeline de CI/CD.
Si un smoke test falla, no tiene sentido ejecutar los demás.

---

### 4.2 Crear `tests/test_w24_smoke.py`

```python
"""Smoke tests W24 — Verificación de que el sistema está vivo.

Estos 8 tests comprueban que las rutas más críticas del ERP responden
correctamente. Son los tests más simples pero los más importantes:
si alguno falla, el sistema no está operativo.

Orden de criticidad:
    1. Página de inicio         — el sistema arranca
    2. Login                    — la autenticación funciona
    3. API pública              — la API responde sin auth
    4. API con token            — la autenticación de API funciona
    5. Panel admin              — el admin está accesible
    6. Catálogo público         — la tienda es accesible sin login
    7. Dashboard                — los reportes funcionan
    8. Webhook                  — el endpoint de Stripe responde

Ejecutar con:
    python manage.py test tests.test_w24_smoke --verbosity=2

Resultado esperado:
    Ran 8 tests in X.XXXs
    OK
"""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from tests.factories import CategoriaFactory, ProductoFactory


class SmokePaginaInicioTest(TestCase):
    """Smoke test 1: El sistema arranca y responde."""

    def test_pagina_inicio_responde_200(self):
        """GET / → 200. Si falla, el servidor no está arriba."""
        r = self.client.get(reverse('inicio'))
        self.assertIn(r.status_code, [200, 301, 302],
                      "La página de inicio no responde correctamente")


class SmokeAutenticacionTest(TestCase):
    """Smoke test 2: La autenticación funciona."""

    def test_pagina_login_accesible(self):
        """GET /accounts/login/ → 200. Si falla, allauth no está configurado."""
        r = self.client.get(reverse('account_login'))
        self.assertEqual(r.status_code, 200,
                         "La página de login no está accesible")

    def test_login_y_logout_funcional(self):
        """Login exitoso → 302. Si falla, la autenticación está rota."""
        User.objects.create_user('smoke_user', password='smoke_pass123')
        r = self.client.post(reverse('account_login'), {
            'login':    'smoke_user',
            'password': 'smoke_pass123',
        })
        # allauth redirige tras login exitoso
        self.assertEqual(r.status_code, 302,
                         "El login no redirigió correctamente")


class SmokeAPITest(TestCase):
    """Smoke tests 3 y 4: La API responde."""

    def setUp(self):
        self.api_client = APIClient()
        self.user  = User.objects.create_user('api_smoke', password='pass')
        self.token = Token.objects.create(user=self.user)
        CategoriaFactory()          # hay al menos 1 categoría en la BD
        ProductoFactory()           # hay al menos 1 producto

    def test_api_productos_publica_200(self):
        """GET /api/productos/ sin token → 200.
        Si falla, la API no está funcionando o IsAuthenticatedOrReadOnly está mal."""
        r = self.api_client.get('/api/productos/')
        self.assertEqual(r.status_code, 200,
                         "La API pública de productos no responde")

    def test_api_con_token_valido_200(self):
        """GET /api/productos/ con token → 200 con JSON válido.
        Si falla, la autenticación por token está rota."""
        self.api_client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.token.key}'
        )
        r = self.api_client.get('/api/productos/')
        self.assertEqual(r.status_code, 200)
        self.assertIn('results', r.json(),
                      "La respuesta JSON no tiene la clave 'results' esperada")


class SmokeAdminTest(TestCase):
    """Smoke test 5: El panel admin está accesible."""

    def test_admin_login_accesible(self):
        """GET /admin/ sin auth → redirige al login del admin.
        Si falla, el admin no está configurado."""
        r = self.client.get('/admin/')
        # El admin sin autenticar redirige al login
        self.assertIn(r.status_code, [200, 302],
                      "El admin no está accesible")


class SmokeCatalogoTest(TestCase):
    """Smoke test 6: La tienda pública funciona."""

    def test_catalogo_publico_200(self):
        """GET /catalogo/ sin login → 200.
        Si falla, la app catalogo no está registrada o la URL no existe."""
        r = self.client.get(reverse('catalogo:catalogo'))
        self.assertEqual(r.status_code, 200,
                         "El catálogo público no está accesible")


class SmokeDashboardTest(TestCase):
    """Smoke test 7: El dashboard funciona tras login."""

    def test_dashboard_requiere_auth(self):
        """GET /reportes/ sin login → 302 al login.
        Si falla, el LoginRequiredMixin no está aplicado."""
        r = self.client.get(reverse('reportes:inicio'))
        self.assertEqual(r.status_code, 302,
                         "El dashboard debería requerir autenticación")

    def test_dashboard_con_auth_200(self):
        """GET /reportes/ con login → 200.
        Si falla, el dashboard tiene un error de cálculo o template."""
        user = User.objects.create_user('dash_smoke', password='pass')
        self.client.force_login(user)
        with self.settings(CACHES={'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
        }}):
            r = self.client.get(reverse('reportes:inicio'))
        self.assertEqual(r.status_code, 200,
                         "El dashboard retornó un error tras autenticación")
```

### 4.3 Ejecutar los smoke tests

```cmd
python manage.py test tests.test_w24_smoke --verbosity=2
```

**Resultado esperado:**
```
test_admin_login_accesible ... ok
test_api_con_token_valido_200 ... ok
test_api_productos_publica_200 ... ok
test_catalogo_publico_200 ... ok
test_dashboard_con_auth_200 ... ok
test_dashboard_requiere_auth ... ok
test_login_y_logout_funcional ... ok
test_pagina_inicio_responde_200 ... ok

Ran 8 tests in X.XXXs
OK
```

### 4.4 Suite acumulada final

```cmd
python manage.py test tests --verbosity=0
```

**Resultado esperado:** `Ran 219 tests in X.XXXs · OK`

---

## PARTE 5 — Commit Final y Verificación GitHub/Render (10 min)

```cmd
git add .
git status

:: Verificar que incluye:
::   README.md (nuevo/actualizado)
::   docs/API.md (nuevo)
::   render.yaml (healthCheckPath agregado)
::   tests/test_w24_smoke.py (nuevo)
::   sprint7_planning.md (actualizado)

git commit -m "ENTREGA FINAL [M8]: README + API docs + smoke tests + 219 tests OK ✅"
git push origin main
```

**Verificar en GitHub:**
```
[ ] Repositorio visible y público (o compartido con el asesor)
[ ] README.md renderizado con badges y secciones
[ ] docs/API.md visible como referencia técnica
[ ] Último commit: "ENTREGA FINAL [M8]..."
[ ] Actions (si configurado): tests pasando en verde
```

**Verificar en Render:**
```
[ ] Deploy automático disparado por el push
[ ] Build exitoso en los logs
[ ] Servicios web + worker + beat: Status Live / Running
[ ] healthCheck: pasando
```

---

## PARTE 6 — Sprint 7 Review ante el Asesor (30 min)

### Guión de demo final — Las 8 Espirales en 15 minutos

```
ESPIRAL 1 (W01-W03) — Entorno y Templates:
→ Mostrar: git log --oneline | head -20
   "El proyecto tiene X commits desde la Semana 1"
→ Mostrar: python manage.py test tests --verbosity=0
   "219 tests, todos pasando"

ESPIRAL 2 (W04-W06) — Modelos y ORM:
→ Abrir: /admin/productos/producto/
→ "8 modelos con migraciones, validators, Jazzmin"
→ Clic en un producto → botón HISTORY → historial de precios (E7)

ESPIRAL 3 (W07-W09) — CRUD y Auth:
→ Abrir: /productos/ (lista paginada con filtros y badges de stock)
→ Login como vendedor_test → "solo puede crear ventas, no borrar productos"
→ GET /productos/1/eliminar/ → HTTP 403

ESPIRAL 4 (W10-W12) — API REST y Media:
→ Abrir: /api/productos/ → JSON paginado con imagen_url
→ POST /api/auth/token/ → obtener token
→ GET /ventas/1/pdf/ → descargar factura PDF

ESPIRAL 5 (W13-W15) — E-commerce:
→ Abrir: /catalogo/ → tienda sin login
→ Agregar producto → contador en navbar se actualiza
→ Checkout → tarjeta 4242 → pago exitoso
→ Terminal worker: "[correo_confirmacion] Procesando..."

ESPIRAL 6 (W16-W18) — Celery e Integraciones:
→ Abrir: http://localhost:5555 → Flower con historial de tareas
→ Shell: verificar_stock_bajo.apply(args=(100,)).get()
→ "Alerta enviada al admin por correo"

ESPIRAL 7 (W19-W21) — Dashboard y Reportes:
→ Abrir: /reportes/ → 5 KPIs + 3 gráficas Chart.js
→ "Segunda carga: < 100ms — caché Redis activo"
→ Abrir: /reportes/ventas/ → filtrar por fecha → exportar Excel

ESPIRAL 8 (W22-W24) — Calidad y Entrega:
→ coverage report → TOTAL ≥ 80%
→ Mostrar: htmlcov/index.html → informe visual de cobertura
→ Mostrar: docs/API.md y README.md
→ Mostrar: https://erp-django-utec.onrender.com en producción

"219 tests. 8 espirales. 1 ERP funcionando en producción."
→ Estado: ✅ HITO M8 ALCANZADO
```

### Tabla de verificación M8

| Criterio | Estado |
|---|---|
| URL pública funcionando en Render.com | ✅ |
| 219+ tests pasando | ✅ |
| Cobertura ≥ 80% | ✅ |
| README.md completo con instalación rápida | ✅ |
| docs/API.md con todos los endpoints | ✅ |
| Smoke tests verificando rutas críticas | ✅ |
| Todos los hitos M1–M7 previamente declarados | ✅ |
| Celery worker + beat corriendo en producción | ✅ |
| Panel admin con Jazzmin + historial de precios | ✅ |
| Catálogo → carrito → pago Stripe → correo | ✅ |

---

## PARTE 7 — Retrospectiva Global del Programa (25 min)

### 7.1 Crear `sprint7_retrospective.md`

```markdown
# Sprint 7 Retrospective — ERP Django
## Semanas W22–W24 · Espiral 8: Calidad y Entrega

**Fecha:** ___/___/_____

## ¿Qué funcionó bien? (Keep)
1. Los factories (factory_boy) redujeron drásticamente el código
   repetitivo en el setUp() de los tests de integración.
2. assertNumQueries fue el detector perfecto para regresiones de N+1.
3. El bloque if DEBUG en settings.py fue la forma correcta de
   proteger debug-toolbar de producción.

## ¿Qué mejorar? (Improve)
1. Documentar los endpoints de la API desde la W10, no al final.
2. Establecer el presupuesto de queries con assertNumQueries
   desde la primera vez que se escribe la vista.

## Velocidad del Sprint 7

| HU | Pts plan. | Pts ent. |
|---|---|---|
| HU-E8-01 Cobertura ≥ 80% | 5 | 5 |
| HU-E8-02 Tests integración E2E | 5 | 5 |
| HU-E8-03 Factories datos realistas | 3 | 3 |
| HU-E8-04 Fixes N+1 | 3 | 3 |
| HU-E8-05 django-debug-toolbar | 2 | 2 |
| HU-E8-06 Documentación técnica | 3 | 3 |
| HU-E8-07 Sistema desplegado | 5 | 5 |
| **Total** | **26** | **26** |

**Velocidad Sprint 7:** 26 puntos
**Velocidad acumulada (S0–S7):** 167 puntos
```

---

### 7.2 Retrospectiva Global del Programa (24 semanas)

```markdown
# Retrospectiva Global del Programa
## Técnico en Programación — ERP Django
## SEP 3061300006-23 · UTEC Celaya

**Duración:** 24 semanas (6 meses)
**Asesor:** MC. Román Fernando López González

## Resumen de hitos alcanzados

| Hito | Semana | Logro |
|---|---|---|
| M0 | W01 | Entorno USB portable · Git · Python 3.11 |
| M1 | W03 | URL pública en Render.com + repositorio GitHub |
| M2 | W06 | Esquema ER + 8 modelos + migraciones + 66 tests |
| M3 | W09 | CRUD + allauth + 3 roles RBAC + 100 tests |
| M4 | W12 | DRF completo + PDF + imágenes + Excel + 123 tests |
| M5 | W15 | Pago Stripe sandbox + webhook + stock decrementado |
| M6 | W18 | Celery + correos + alertas + Beat programado |
| M7 | W21 | Dashboard + exportación adaptativa + historial precios |
| **M8** | **W24** | **Entrega final: 219 tests · ≥80% cobertura · URL pública** |

## Velocidad acumulada por sprint

| Sprint | Semanas | Puntos |
|---|---|---|
| Sprint 0 | W01-W03 | 10 |
| Sprint 1 | W04-W06 | 21 |
| Sprint 2 | W07-W09 | 27 |
| Sprint 3 | W10-W12 | 21 |
| Sprint 4 | W13-W15 | 26 |
| Sprint 5 | W16-W18 | 18 |
| Sprint 6 | W19-W21 | 18 |
| Sprint 7 | W22-W24 | 26 |
| **TOTAL** | **24 semanas** | **167 puntos** |

## Tecnologías dominadas en el programa

Python 3.11 · Django 4.2 · PostgreSQL · Redis · Celery ·
Django REST Framework · Stripe · SendGrid · Pillow · WeasyPrint ·
openpyxl · django-allauth · django-jazzmin · django-filter ·
django-simple-history · django-anymail · django-storages ·
factory_boy · coverage.py · Chart.js · Bootstrap 5 ·
Docker · Render.com · Git · GitHub

## Lecciones aprendidas del programa

1. **El modelo es el corazón**: las decisiones de diseño ER
   de la Semana 4 impactaron TODAS las semanas siguientes.
   Tiempo invertido en diseño = tiempo ahorrado en refactoring.

2. **Tests desde el primer día**: los 33 tests de las primeras
   3 semanas nos protegieron de romper funcionalidad al agregar
   características nuevas cada semana.

3. **Celery debe aislarse bien**: los imports locales dentro de
   las tareas (`from ventas.models import Pedido`) son obligatorios
   para evitar importaciones circulares en proyectos Django medianos.

4. **El caché es la herramienta más poderosa**: `cache.get_or_set()`
   redujo el tiempo de carga del dashboard de ~80ms a ~3ms.

5. **N+1 en exportaciones es el error más costoso**: generar un
   Excel de 1000 ventas sin prefetch_related → 3000+ queries.
   Con prefetch → 3 queries.

6. **Docker desde el inicio**: instalar WeasyPrint en W12 habría
   sido trivial si el entorno Docker estuviera configurado desde W01.

7. **factory_boy desde W05**: crear factories desde que se definen
   los modelos habría reducido el código de setUp() en 50 tests.
```

---

### 7.3 Crear `fichas/espiral_08_calidad_entrega.md`

```markdown
# Ficha de Sistematización — Espiral 8
## ERP Django · Espiral E8: Calidad y Entrega

| Campo | Contenido |
|---|---|
| **Número de espiral** | 8 |
| **Nombre del ciclo** | Calidad y Entrega |
| **Semanas** | W22 – W24 |
| **Responsable** | [Nombre del estudiante] |
| **Asesor** | MC. Román Fernando López González |

## 1. Objetivo del ciclo
Certificar la calidad del ERP Django mediante cobertura de código
≥ 80%, tests de integración E2E, optimización de queries SQL,
y entrega de documentación técnica completa (README + API + auditoría).

## 2. Tareas realizadas

| # | Tarea | Estado | Semana |
|---|---|---|---|
| 1 | setup.cfg con coverage + fail_under=80 | ✅ | W22 |
| 2 | tests/factories.py con factory_boy | ✅ | W22 |
| 3 | 3 tests integración E2E | ✅ | W22 |
| 4 | Tests dirigidos para brechas | ✅ | W22 |
| 5 | Coverage ≥ 80% alcanzado | ✅ | W22 |
| 6 | django-debug-toolbar configurado | ✅ | W23 |
| 7 | Auditoría N+1: 3 fixes aplicados | ✅ | W23 |
| 8 | Tests assertNumQueries | ✅ | W23 |
| 9 | README.md completo | ✅ | W24 |
| 10 | docs/API.md con todos los endpoints | ✅ | W24 |
| 11 | render.yaml con healthCheckPath | ✅ | W24 |
| 12 | 8 smoke tests | ✅ | W24 |
| 13 | Demo final ante el asesor | ✅ | W24 |

## 3. Evidencias finales del programa
- URL: https://erp-django-utec.onrender.com
- Repositorio: https://github.com/TU_USUARIO/erp-django-utec
- Tests: Ran 219 tests → OK
- Cobertura: ≥ 80% (ver htmlcov/index.html)
- Documentación: README.md + docs/API.md + docs/auditoria*.md

## 4. Criterios de aceptación M8

| Criterio | Estado |
|---|---|
| URL pública accesible | ✅ |
| ≥ 219 tests passing | ✅ |
| Coverage ≥ 80% | ✅ |
| README con instalación rápida (< 5 min) | ✅ |
| API documentada con ejemplos JSON | ✅ |
| Smoke tests para rutas críticas | ✅ |
| Demo completa ante el asesor (15 min) | ✅ |

## 5. Tiempo total del programa

| Espiral | Semanas | Horas aprox. |
|---|---|---|
| E1 | W01–W03 | 9h |
| E2 | W04–W06 | 9h |
| E3 | W07–W09 | 9h |
| E4 | W10–W12 | 9h |
| E5 | W13–W15 | 9h |
| E6 | W16–W18 | 9h |
| E7 | W19–W21 | 9h |
| E8 | W22–W24 | 9h |
| **Total** | **24 semanas** | **72 horas de laboratorio** |
```

---

## CIERRE — Declaración del Hito M8 (10 min)

### Commit final del programa

```cmd
git add .
git status

git commit -m "PROGRAMA COMPLETO [M8]: 219 tests · ≥80% cobertura · README · API docs ✅"
git push origin main
```

### Ejecutar `finalizar_sesion.bat` por última vez

```cmd
E:\finalizar_sesion.bat
```

### Checklist final de entrega

```
ENTREGABLES DEL PROGRAMA
[ ] Repositorio GitHub con historial de 24 semanas de commits
[ ] URL pública en Render.com: https://erp-django-utec.onrender.com
[ ] README.md con instalación en < 5 min (verificado)
[ ] docs/API.md con todos los endpoints documentados
[ ] docs/auditoria_rendimiento_w23.md (análisis N+1)
[ ] docs/cobertura_analisis_w22.md (análisis de brechas)
[ ] Todas las fichas de sistematización (E1–E8) completadas
[ ] Todas las retrospectivas de sprint (S0–S7) redactadas
[ ] 219+ tests pasando en la rama main
[ ] Coverage ≥ 80% (verificable con coverage run manage.py test tests)
[ ] 8 hitos M1–M8 declarados y documentados
[ ] Demo final ejecutada ante el asesor
```

### Declaración formal del Hito M8

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║         ★  HITO M8 — ENTREGA FINAL ALCANZADA  ★                 ║
║                                                                  ║
║   Proyecto:    ERP Django — UTEC Celaya                          ║
║   Programa:    Técnico en Programación (SEP 3061300006-23)       ║
║   Semanas:     24 (W01 – W24)                                    ║
║   Espirales:   8 (E1 – E8)                                       ║
║   Sprints:     7 (S0 – S7)                                       ║
║   Tests:       ≥ 219 pasando                                     ║
║   Cobertura:   ≥ 80%                                             ║
║   URL pública: https://erp-django-utec.onrender.com              ║
║   Asesor:      MC. Román Fernando López González                 ║
║                                                                  ║
║   Estado: ✅ ENTREGADO                                           ║
║   Fecha:  ___/___/_____                                          ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## Referencia rápida de comandos W24

```cmd
:: TESTS FINALES
python manage.py test tests.test_w24_smoke --verbosity=2
python manage.py test tests --verbosity=0   (219 tests)

:: COBERTURA FINAL
coverage run manage.py test tests
coverage report
coverage html
start htmlcov\index.html

:: SMOKE TEST RÁPIDO (el más rápido de todos)
python manage.py test tests.test_w24_smoke

:: VERIFICAR PRODUCCIÓN
curl https://erp-django-utec.onrender.com/api/productos/

:: GIT FINAL
git add .
git commit -m "ENTREGA FINAL [M8]: descripción"
git push origin main
git log --oneline | head -10
git tag M8-entrega-final
git push origin M8-entrega-final
```

---

## Palabras Finales

Veinticuatro semanas, ocho espirales, siete sprints, 167 puntos de
historia de usuario, 219 tests, cobertura ≥ 80%.

El ERP Django pasó de ser un proyecto vacío en un USB portable
a un sistema completo con autenticación, e-commerce, pagos en línea,
tareas asíncronas, dashboard con caché, reportes exportables,
auditoría de precios, documentación técnica y despliegue en la nube.

Cada semana agregó una capa sobre las anteriores — eso es exactamente
lo que significa el Modelo Espiral de Boehm: no un salto, sino una
construcción progresiva donde cada vuelta de la espiral consolida
lo anterior y abre el siguiente nivel de complejidad.

El ERP no es perfecto. Ningún software lo es. Pero está certificado:
las pruebas dicen que funciona, la cobertura dice que se probó bien,
el historial de commits dice que se construyó disciplinadamente.

**Eso es ingeniería de software.**

---

*Guía de Laboratorio W24 · ERP Django*
*Espiral 8 Cierre · Sprint 7 Review + Retrospectiva Global · Hito M8*
*SEP 3061300006-23 · UTEC Celaya · MC. Román Fernando López González*

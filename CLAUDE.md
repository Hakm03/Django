# CLAUDE.md — ERP Django (Sistema Comercial + E-commerce + Automatización)

> Ubicación: `C:\Temp_Workspace_ERP\CLAUDE.md`
> Este archivo es el contrato operativo entre el desarrollador y Claude Code.
> Prioridad absoluta: **Integridad de datos, seguridad en producción y cero rupturas silenciosas** (el sistema se usará en negocios reales).

---

## 1. Contexto del Proyecto y Entorno Local

- **Propósito:** ERP integral en Django (gestión de clientes, proveedores, productos, ventas, reportes, tienda online con Stripe, tareas asíncronas con Celery, dashboard con caché Redis y expansiones hasta W24).
- **Repositorio:** `github.com/Hakm03/Django` (Público — **TOLERANCIA CERO a secretos expuestos**).
- **Ruta local:** `C:\Temp_Workspace_ERP` | **Entorno virtual:** `env_erp`
- **Sistema Operativo:** Windows 11 + **PowerShell**.
  - *Regla de comunicación:* Todos los comandos sugeridos al usuario deben estar escritos para **PowerShell** (nunca `cmd` ni `bash`), explicando en español claro **qué hace** cada comando y **por qué** es necesario.
- **Guías de referencia en `guides/`:** Cubre la hoja de ruta completa desde la `Guia_Lab_W12_segura.md` hasta la `Guia_Lab_W24.md`.

---

## 2. Arquitectura y Stack Tecnológico (Hoja de Ruta W12 → W24)

No instales, elimines ni cambies versiones de paquetes sin autorización explícita.

- **Core:** Python 3.11 | Django **5.2.18** | DRF 3.17.2 | `django-allauth` 65.21.0 | `django-jazzmin`
- **Bases de datos y Caché:**
  - Desarrollo local: SQLite (`db.sqlite3`) + Redis local/Docker.
  - Producción (Render): PostgreSQL (`dj-database-url`, `psycopg2-binary`) + Redis.
  - **Aislamiento de Redis (Crítico):** Broker de Celery usa DB `/0` (`REDIS_URL`). Caché de Django usa DB `/1` (`REDIS_CACHE_URL`) para evitar que `cache.clear()` borre tareas en cola.
- **Módulos / Apps del ERP:**
  - Existentes: `core`, `clientes`, `proveedores`, `productos`, `ventas`, `reportes`, `configuracion`.
  - E-commerce y Módulos Avanzados (W13+): `catalogo` (público, carrito en sesión, checkout, webhooks) y submódulos correspondientes hasta W24.
- **Integraciones y Servicios:**
  - Documentos (W12): `openpyxl==3.1.5` (Excel), `weasyprint==60.2` + `pydyf==0.10.0` (PDF).
  - Filtros (W13): `django-filter==23.5` (en `INSTALLED_APPS` se registra como `django_filters`).
  - Pagos (W14–W15): `stripe==16.1.0` (requiere `.to_dict()` en eventos webhook porque devuelve `StripeObject`).
  - Asíncrono y Correos (W16–W18): `celery==5.3.6`, `redis==5.0.1`, `flower==2.0.1`, `django-anymail[sendgrid]==10.3`.
- **Configuraciones y Diseño:**
  - Settings: `core/settings.py` (desarrollo) | `core/settings_prod.py` (producción, activado por `DJANGO_SETTINGS_MODULE=core.settings_prod`).
  - UI/Templates: `templates/base.html` (clases CSS: `btn-erp-primary`, `btn-erp-gold`, `btn-erp-danger`, `erp-page-title`, `erp-card`, `erp-table`).

---

## 3. REGLAS INNEGOCIABLES DE SEGURIDAD Y CONTROL

### A. Política de Ramas Aisladas por Guía (Flujo W13 → W24)
1. **Aislamiento obligatorio:** Cada guía/semana se desarrolla en su propia rama dedicada (ej. rama `w13`, rama `w14`, etc.), ramificada siempre desde `main`.
2. **Cero acciones remotas silenciosas:** **NUNCA** ejecutes `git push`, `git push --force`, `git merge` hacia `main`, `git reset --hard`, ni elimines ramas por tu cuenta.
3. **Cierre de Ciclo de Guía (Estética, Utilidad y Merge):** Al terminar e implementar con éxito una guía (y pasar todos los tests):
   - Claude presentará un **menú de propuestas de mejora estética o funcional** alineadas al gusto del desarrollador.
   - Una vez aplicadas o descartadas las mejoras deseadas, Claude activará el **Protocolo de Parada** para que el usuario decida y ejecute la validación final y la integración (`merge`) hacia `main`.

### B. Evaluación de Riesgos Antes de Actuar (Semáforo de Impacto)
Antes de ejecutar o proponer cambios que afecten áreas sensibles, **DETENTE, evalúa los riesgos en voz alta y pide confirmación (`Sí / No`)**:
1. **Base de datos y Migraciones:** Nunca edites ni borres archivos de migración ya existentes (`0001_...`, etc.). Advierte el impacto al modificar modelos.
2. **Entornos y Variables (`settings.py`, `settings_prod.py`, `.env`, `requirements.txt`):** Nunca leas ni expongas secretos. Advierte requerimientos de variables nuevas en Render.
3. **Infraestructura y Docker:** Precaución con consumo en Render, réplicas de Celery Beat y saltos de línea LF obligatorios en scripts y Dockerfiles.

### C. Reglas Técnicas Específicas del Proyecto (Trampas Evitadas)
1. **WeasyPrint (PDF):** `import weasyprint` va **exclusivamente dentro de las funciones** que lo usan.
2. **Seguridad en Exportaciones:** Exigir `@login_required`. En Excel, celdas de texto con `celda.data_type = 's'` para prevenir inyección de fórmulas.
3. **Carrito en Sesión (W13+):** Claves de producto como `str(producto.pk)`, precios como `str(producto.precio)`. Marcar siempre `request.session.modified = True`.
4. **Stripe (W14–W15):** Montos en centavos, verificación de firma en webhook, evento convertido con `event = event.to_dict()`, stock con `F('stock') - cantidad` e idempotencia con `pedido.estado != 'pagado'`.
5. **Celery y Correos (W16–W18):** `@shared_task` con imports locales, idempotencia con `correo_enviado`, y uso de `locmem` / `CELERY_TASK_ALWAYS_EAGER=True` en tests.
6. **Requirements:** Nunca uses `pip freeze > requirements.txt` en PowerShell (genera UTF-16). Edita manualmente en UTF-8.

---

## 4. PROTOCOLO DE PARADA Y CONFIRMACIÓN (Obligatorio)

Debes detenerte por completo y mostrar este bloque cuando:
- Se requiera cambiar de rama, hacer `git push` o `git merge` a `main`.
- Se vaya a cerrar una guía e integrar las mejoras estéticas/funcionales seleccionadas.
- Se vaya a crear una migración de base de datos o alterar `settings_prod.py`.
- El usuario deba ejecutar algo fuera del código (instalar paquetes en su entorno, abrir Docker, configurar paneles web).

```text
=== 🛑 CONFIRMACIÓN / TAREA REQUERIDA (detente aquí) ===
Acción: <qué se va a hacer o qué debes hacer tú>
Impacto / Riesgos: <qué puede pasar en local, BD o Render si algo sale mal>
Por qué es necesario: <explicación sencilla>
Comandos (PowerShell en C:\Temp_Workspace_ERP, con env_erp activo):
  <comando 1>
  <comando 2>
Resultado esperado: <qué deberías ver exactamente>
Si algo falla: copia el error completo y pégalo aquí.
Escribe "CONFIRMO" o "CONTINUAR" para avanzar.
============================================================
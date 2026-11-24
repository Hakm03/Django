# Sprint 5 Planning — ERP Django
## Semanas W16–W18 · Espiral 6: Celery e Integraciones

**Sprint Goal:**
Al finalizar el Sprint 5, el ERP ejecutará tareas pesadas de forma
asíncrona con Celery+Redis: correo de confirmación de pedido, alerta
de stock bajo y reporte diario de ventas, sin bloquear las peticiones HTTP.

**Nota (2026-11-23):** se evaluaron Mailjet y Brevo cuando SendGrid no dejaba
verificar un teléfono. Al lograr la verificación se volvió al plan original:
**SendGrid** (plan gratuito, API por HTTPS) vía `django-anymail`.
Render Free bloquea los puertos SMTP, por eso no se usa SMTP (p. ej. Gmail).
Plan B si SendGrid falla: Brevo (vía anymail).

## HUs seleccionadas

| ID | Historia | Puntos | Semana |
|---|---|---|---|
| HU-E6-01 | Como dev, quiero infraestructura Celery+Redis funcional | 3 | W16 |
| HU-E6-02 | Como sistema, quiero ejecutar tareas sin bloquear HTTP | 2 | W16 |
| HU-E6-03 | Como cliente, quiero correo de confirmación post-pago | 5 | W17 |
| HU-E6-04 | Como admin, quiero correo cuando el stock es bajo | 3 | W17 |
| HU-E6-05 | Como admin, quiero reporte diario de ventas a las 8 AM | 3 | W18 |
| HU-E6-06 | Como dev, quiero monitorear tareas con Flower | 2 | W16 |

**Total Sprint 5:** 18 puntos

## DoD — Sprint 5
- Logs de Render: worker de Celery embebido "ready" y procesa tareas
- Webhook payment_intent.succeeded → tarea de correo en la cola (no espera)
- Correo de confirmación recibido en < 30 s (W17)
- Alerta de stock enviada cuando stock < umbral (W17)
- Reporte diario ejecutado a las 8:00 AM (W18)
- python manage.py test → ≥ 155 tests OK

## Sprint Backlog — actualización W16/W17

| Tarea | Estado |
|---|---|
| celery, redis, flower, kombu==5.3.7 en requirements.txt (UTF-8) | ✅ W16 |
| core/celery.py + core/__init__.py | ✅ W16 |
| CELERY_* en settings.py (Redis si hay REDIS_URL · EAGER si no) | ✅ W16 |
| ventas/tasks.py (2 tareas placeholder) | ✅ W16 |
| Webhook: .delay() con try/except, solo en el primer cambio a "pagado" | ✅ W16 |
| docker-entrypoint.sh: exec "$@" + worker embebido | ✅ W16 |
| render.yaml: REDIS_URL + CELERY_EMBEDDED_WORKER | ✅ W16 |
| docker-compose.yml: redis, celery_worker, flower (opcional) | ✅ W16 |
| tests/test_w16_celery.py (12 tests) · suite completa 259 OK | ✅ W16 |
| Key Value (Redis) Free en Render + variables en Environment | ⏳ usuario |
| Worker embebido "ready" en logs de Render | ⏳ usuario |
| SendGrid: correo de confirmación real + correo_enviado (migración 0004) | ✅ W17 |
| Alerta de stock bajo por correo (a ADMIN_EMAIL) | ✅ W17 |
| Recibo HTML con diseño + texto plano | ✅ W17 |
| Admin de pedidos: columna/filtro «Recibo enviado» + acción reenviar | ✅ W17 |
| Aviso «revisa Spam» en la página de pago exitoso | ✅ W17 |
| Comando `manage.py probar_correo` (validar SendGrid) | ✅ W17 |
| Variables SENDGRID_API_KEY, DEFAULT_FROM_EMAIL, ADMIN_EMAIL en Render | ✅ usuario |
| Celery Beat + reporte diario (solo si hubo ventas ayer) + alerta de stock diaria | ✅ W18 (2026-11-24) |

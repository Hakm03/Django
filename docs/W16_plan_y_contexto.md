# W16 — Plan y contexto de sesión (Celery + Redis + Flower)

> Documento de traspaso para continuar en otra sesión de Claude Code (casa).
> Guía fuente: `docs/guides/Guia_Lab_W16.md` · Reglas: `CLAUDE.md`

> **Actualización 2026-11-22:** este plan quedó superado por la guía W16 revisada.
> Sin Docker en el laboratorio: modo EAGER sin `REDIS_URL`; Redis y worker solo en
> Render (worker embebido, `CELERY_EMBEDDED_WORKER=1`). La tarea se encola solo
> desde el webhook. W16 ya está implementada en la rama `w16` (ver `git log`).
> SendGrid se descartó (exige verificar teléfono): el proveedor de correo de W17
> está por definir (alternativas: Brevo / Mailjet vía django-anymail).

## 1. Estado al cerrar la sesión (escuela) — histórico

- Rama `w16` **creada** desde `main` (commit `1edd08a`, que ya incluye W15). Está en el repo local.
- **Sigo en `main`**: el checkout a `w16` está pendiente de confirmación (Protocolo de Parada). Nada instalado, nada de código escrito.
- La rama `w16` es local. Si trabajas desde otra PC, la rama no estará allí (no se hizo `push`). Créala con `git branch w16 main`, o cópiala con la carpeta del proyecto.
- Git portable (USB): en la escuela estaba en `E:\ARASAKA-main_data-\Git_portable\cmd\git.exe`. En casa la ruta puede cambiar; usa el comando de búsqueda de CLAUDE.md §1.
- Working tree con cambios ajenos a W16 que **no se tocan**:
  - Borrados sin commitear en `docs/plaining/` (sprint0 a sprint3).
  - Sin trackear: `guides/` y `modelos base.txt`.

## 2. Qué veremos en W16

**Idea central:** W15 completó la venta. W16 saca las tareas pesadas del ciclo HTTP.

- **Productor, broker, consumidor:** Django deja un mensaje en Redis; el worker de Celery lo lee y ejecuta.
- **Tareas** con `@shared_task`: `enviar_confirmacion_pedido` y `verificar_stock_bajo`. En W16 son placeholders (solo log). Correo real en W17; programación con Celery Beat en W18.
- **Conexión al flujo de pago:** `pago_exitoso()` y el webhook de Stripe llaman a `.delay(pedido.pk)`.
- **Monitoreo** con Flower en `http://localhost:5555`.
- **Tests:** `CELERY_TASK_ALWAYS_EAGER=True` (lógica) y `@patch('...delay')` (invocación desde vistas).

## 3. Estado del repo (verificado)

- No existen `core/celery.py` ni `ventas/tasks.py`; `core/__init__.py` está vacío.
- `requirements.txt` no tiene celery, redis ni flower.
- `core/settings.py` no tiene configuración CELERY, REDIS ni CACHES.
- Tests existentes hasta `test_w15_webhooks.py`. Existen `docker-compose.yml`, `Dockerfile` y `render.yaml`.

## 4. Ajustes sobre la guía (CLAUDE.md manda)

1. **Redis:** broker de Celery en DB `/0` (`REDIS_URL`); caché de Django, si se añade, en DB `/1` (`REDIS_CACHE_URL`).
2. **`requirements.txt`:** edición manual en UTF-8. Nunca `pip freeze >` en PowerShell (genera UTF-16).
3. **Git:** trabajar en `w16`. Sin `push` ni `merge` por mi cuenta. La guía dice `git push origin main`; **no se hace**.
4. **Idempotencia:** la tarea se dispara desde `pago_exitoso()` y desde el webhook, así que el cliente podría recibir 2 correos. Es placeholder en W16; el flag `correo_enviado` (W17) requiere migración y se pedirá confirmación aparte.
5. **Comandos:** todo en PowerShell (la guía usa `cmd`).
6. **Tests:** la guía dice "8" y lista 7. Se escriben las 7 y se evalúa una más útil. Meta: ≥155 en total (147 + nuevos).
7. **`render.yaml` y Render:** si hace falta un worker en Render, avisar y pedir `Sí / No` antes de tocar el archivo.

## 5. Reparto

### Claude (código, rama `w16`)

1. `core/celery.py` y `core/__init__.py`.
2. Variables `CELERY_*` en `core/settings.py` y `REDIS_URL` en `.env.example`.
3. `ventas/tasks.py` con las 2 tareas.
4. `.delay()` en `catalogo/views.py` (`pago_exitoso`) y `catalogo/webhook_views.py` (`_manejar_pago_exitoso`, después del `save()`, con `pedido.estado != 'pagado'`).
5. `tests/test_w16_celery.py`.
6. `requirements.txt` (a mano) y `docs/plaining/sprint5_planning.md`.
7. `docker-compose.yml` con servicios `celery_worker` y `flower` (saltos de línea LF en scripts y Dockerfiles).
8. Suite completa de tests y menú de mejoras para el cierre de la guía.

### Usuario (dashboards y conexiones)

Todos los comandos en PowerShell, en `C:\Temp_Workspace_ERP` con `env_erp` activo:

```powershell
# 1. Instalar paquetes (requiere tu autorización)
pip install "celery==5.3.6" "redis==5.0.1" "flower==2.0.1"

# 2. Verificar instalación
python -c "import celery; print('Celery', celery.__version__)"
python -c "import redis; print('redis', redis.__version__)"
python -c "import flower; print('flower OK')"

# 3. Levantar Redis con Docker y verificar conexión
docker-compose up -d redis
python -c "import redis; r=redis.from_url('redis://localhost:6379/0'); print('PING:', r.ping())"
```

4. Agregar `REDIS_URL=redis://localhost:6379/0` a tu `.env` local (no se commitea).
5. Arrancar el worker (segunda terminal): `celery -A core worker -l info -Q erp_django`.
6. Arrancar Flower (tercera terminal): `celery -A core flower --port=5555`, y revisar `http://localhost:5555` (worker en verde, pestaña Tasks).
7. Prueba extremo a extremo: compra con tarjeta 4242 y Stripe CLI activo; el worker debe mostrar la tarea (dos veces: vista y webhook).
8. Render: decidir si habrá worker allá (se habla aparte).

En Windows, el pool `prefork` de Celery 5 puede dar problemas. Si el worker falla al ejecutar tareas, usa `--pool=solo` (o `--pool=threads`).

## 6. Siguiente paso al retomar

Primero confirmar el cambio de rama:

```text
=== 🛑 CONFIRMACIÓN / TAREA REQUERIDA (detente aquí) ===
Acción: Cambiar de la rama main a la rama w16.
Impacto / Riesgos: Mínimo. Ambas ramas apuntan al mismo commit; los cambios sin commitear se conservan.
Por qué es necesario: Cada guía se desarrolla en su rama aislada.
Comandos (PowerShell en C:\Temp_Workspace_ERP, con env_erp activo):
  $g = (Get-ChildItem E:\ -Recurse -Filter git.exe -Depth 4 | ? FullName -like '*\cmd\git.exe' | select -First 1)
  & $g.FullName branch --list w16        # si no aparece: & $g.FullName branch w16 main
  & $g.FullName checkout w16
  & $g.FullName branch --show-current
Resultado esperado: Se imprime "w16".
Escribe "CONFIRMO" o "CONTINUAR" para avanzar.
============================================================
```

Frase sugerida para la nueva sesión:

> Lee `CLAUDE.md`, `docs/guides/Guia_Lab_W16.md` y `docs/W16_plan_y_contexto.md`. Confirmo el cambio a la rama `w16`; continúa con la parte de código del plan.

## 7. Cierre de guía (recordatorio)

Al pasar todos los tests: menú de mejoras estéticas y funcionales, luego Protocolo de Parada. El usuario decide y ejecuta el `merge` a `main`.

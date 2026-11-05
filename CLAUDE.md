# CLAUDE.md — ERP Django (tienda web + gestor de inventarios)

> Este archivo va en la raíz del proyecto (`C:\Temp_Workspace_ERP\CLAUDE.md`).
> Claude Code lo lee al iniciar cada sesión. Es tu "memoria" del proyecto.

## 1. Qué es este proyecto

ERP web en **Django** para gestionar clientes, proveedores, productos, ventas e
inventario. Empezó como proyecto escolar (UTEC Celaya, guías `guides/Guia_Lab_Wxx.md`)
pero **va a usarse en negocios reales**: prioriza seguridad, claridad y que nada
se rompa por encima de "que funcione rápido".

- Repositorio: `github.com/Hakm03/Django` (público → **nunca** subir secretos).
- Carpeta local: `C:\Temp_Workspace_ERP` · entorno virtual: `env_erp` (Windows).
- Sistema del usuario: Windows 11 + **PowerShell**. Los comandos que le des a la
  persona deben ser de PowerShell, no de bash.
- La persona **está aprendiendo**: explica en español sencillo, una línea por comando,
  sin jerga innecesaria. Cada comando que le pidas ejecutar debe llevar su porqué.

## 2. Stack real (no lo cambies sin pedir permiso)

- Python 3.11 en Render (local: el de `env_erp`). Django **5.2.18**.
- django-allauth **65.21.0** (login/registro), DRF 3.17.2 (API), django-jazzmin (admin).
- WhiteNoise (estáticos), gunicorn, dj-database-url, psycopg2-binary.
- django-storages + boto3 + Pillow + filetype (imágenes de productos, W11).
- Desarrollo: SQLite. Producción: PostgreSQL en Render.
- Apps: `clientes`, `proveedores`, `productos`, `ventas`, `reportes`, `configuracion`, `core`.
- Comando propio: `python manage.py crear_grupos` (roles Gerente, Vendedor, Almacén).
- Settings: `core/settings.py` = desarrollo · `core/settings_prod.py` = producción
  (se activa con la variable `DJANGO_SETTINGS_MODULE=core.settings_prod`).
- Plantillas globales en `templates/` (`base.html`: clases `btn-erp-primary`,
  `btn-erp-gold`, `btn-erp-danger`, `erp-page-title`, `erp-card`, `erp-table`).
- Tests: carpeta `tests/`. Línea base antes de W12: **123 tests OK**.

## 3. Comandos útiles (PowerShell, con `(env_erp)` activo)

```powershell
python manage.py check
python manage.py test tests
python manage.py runserver
git status
git branch --show-current
```

## 4. REGLAS INNEGOCIABLES

1. **Solo trabajas en la rama `w12`.** Antes de editar, ejecuta
   `git branch --show-current`. Si no dice `w12`, detente y avisa.
2. **Nunca** hagas `git push`, `git push --force`, `git reset --hard`, ni toques `main`.
   Puedes hacer `git add` y `git commit` **locales** en `w12`, solo si los tests pasan.
   Mensaje de commit: `W12 Fase N: <qué se hizo>`.
3. **No instales ni ejecutes nada fuera del proyecto.** Prohibido por tu cuenta:
   `pip install`, `winget`, `wsl`, `docker`, `npm`, cambios de configuración de
   Windows, abrir puertos, tocar carpetas fuera de `C:\Temp_Workspace_ERP`.
   Cuando algo así haga falta → aplica el **PROTOCOLO DE PARADA** (sección 5).
   Sí puedes correr lecturas y pruebas: `git status/log/diff`, `python manage.py check`,
   `python manage.py test tests`.
4. **Cero secretos.** No leas ni imprimas `.env`, `db.sqlite3` ni valores de variables
   de entorno. No escribas contraseñas reales en archivos. Las contraseñas de práctica
   solo pueden ir en `docker-compose.yml` y deben decir que son locales.
5. **No edites migraciones ya existentes.** Si cambias modelos: migración nueva y avísalo.
6. **`import weasyprint` SOLO dentro de funciones**, nunca al inicio de un archivo.
   Si falta la librería (Windows sin Docker) el ERP debe seguir funcionando y
   el PDF responder 503 con mensaje claro.
7. **Seguridad en exportaciones:** valida el parámetro `formato` contra una lista
   permitida (nunca lo uses directo); exige `login_required`; en Excel marca los textos
   como texto (`data_type = 's'`) y en CSV prefija con `'` los valores que empiecen con
   `=`, `+`, `-`, `@` (evita inyección de fórmulas).
8. **Saltos de línea:** `docker-entrypoint.sh` y archivos `.yml` deben ser LF, no CRLF.
   El archivo se llama `Dockerfile` (D mayúscula; en Linux importa).
9. **Cambios mínimos:** no refactorices ni "mejores" código que no sea de la tarea.
   No cambies nombres de funciones, rutas ni nombres de URL que ya usan los tests.
10. **Sé honesto.** Nunca digas "probado" si no ejecutaste la prueba. Al final de cada
    fase informa qué verificaste y **qué no pudiste verificar**.

## 5. PROTOCOLO DE PARADA (cuando la persona debe actuar)

Si el siguiente paso requiere que la persona haga algo en su PC o en un panel web,
**detente por completo** (no sigas con otra cosa) y escribe exactamente este bloque:

```text
=== TAREA PARA TI (detente aquí) ===
Qué vas a hacer: <una frase simple>
Por qué: <una frase simple>
Comandos (PowerShell, en C:\Temp_Workspace_ERP):
  <comando 1>
  <comando 2>
Resultado esperado: <qué debería ver>
Si algo sale distinto: copia el mensaje completo y pégalo aquí.
Cuando termines escribe: CONTINUAR
====================================
```

Paradas obligatorias: instalar paquetes, instalar/abrir Docker o WSL, `docker compose`,
crear o configurar servicios en Render, `git push`, `git merge`, correr scripts `.bat`,
abrir el navegador a probar algo.

## 6. Informe al terminar cada fase (formato fijo)

1. **Archivos creados/modificados** (lista).
2. **Tests:** comando ejecutado, número total y resultado (`OK`, `skipped=N`, fallos).
3. **Verificado:** lo que de verdad ejecutaste.
4. **NO verificado:** lo que no pudiste comprobar y por qué.
5. **Siguiente paso** y si requiere una PARADA.

## 7. Trampas conocidas de este proyecto (ya nos pasaron)

- `requirements.txt` con un paquete **duplicado** (dos versiones de Django) rompe el
  build de Render. Cada paquete una sola vez. No usar `pip freeze >` en PowerShell
  (guarda en UTF-16 y rompe lectura).
- Si falta `DJANGO_SETTINGS_MODULE=core.settings_prod` en Render → `DisallowedHost`.
- `SECURE_PROXY_SSL_HEADER` es obligatorio en producción (sin él, bucle de redirecciones).
- `settings_prod.py` fuerza HTTPS y SSL de base de datos: en Docker local se relaja con
  `MODO_LOCAL=True` (esa variable **jamás** va en Render).
- `createsuperuser --noinput` necesita `DJANGO_SUPERUSER_USERNAME/EMAIL/PASSWORD`
  (con **doble S** en PASSWORD) y un correo válido.
- El servicio actual de Render se configuró a mano: `render.yaml` **no se usa**.
- El `Dockerfile` es sensible a mayúsculas en Linux; `templates/registration` no debe
  ser un archivo vacío.
- Al unir archivos con conflicto, nunca aceptar "ambos": duplica bloques de Django.

## 8. Definición de "terminado" (por fase)

- `python manage.py check` sin problemas.
- `python manage.py test tests` termina en `OK` (en Windows sin WeasyPrint se esperan
  pruebas `skipped`, nunca `FAILED` ni `ERROR`).
- Diff pequeño y revisable; commit local en `w12`.
- Informe de la sección 6 entregado.

## 9. Guía de referencia

La guía paso a paso (código ya probado) está en `guides/Guia_Lab_W12_segura.md`.
Úsala como fuente de verdad: copia su código tal cual, salvo cuando el prompt pida
una ampliación.

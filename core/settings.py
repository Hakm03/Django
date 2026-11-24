# core/settings.py
import environ
from pathlib import Path
import sys


BASE_DIR = Path(__file__).resolve().parent.parent

# ── Variables de entorno ──────────────────────────────────────────────────
env = environ.Env(DEBUG=(bool, True))
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY  = env('SECRET_KEY', default='dev-key-insegura-solo-para-desarrollo')
DEBUG       = env('DEBUG', default=True)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

# ── Apps instaladas ───────────────────────────────────────────────────────
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',        # requerido por allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'rest_framework',
    'rest_framework.authtoken',    # ← agrega
    'django_filters',              # W13: filtros del catálogo
    'whitenoise.runserver_nostatic',
    'clientes',
    'proveedores',
    'productos',
    'ventas',
    'reportes',
    'configuracion',
    'catalogo',                    # W13: tienda pública y carrito
    'core',                        # necesario para el comando crear_grupos
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',   # requerido por allauth
]

ROOT_URLCONF = 'core.urls'

# ── Templates ─────────────────────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],       # carpeta global de templates
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'catalogo.context_processors.carrito_info',   # W13
            ],
        },
    },
]

# ── Base de datos ─────────────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ── Internacionalización ──────────────────────────────────────────────────
LANGUAGE_CODE = 'es-mx'
TIME_ZONE     = 'America/Mexico_City'
USE_I18N      = True
USE_TZ        = True

# ── Archivos estáticos ────────────────────────────────────────────────────
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
if 'test' in sys.argv:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# ── Archivos media ────────────────────────────────────────────────────────
MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ── Autenticación ─────────────────────────────────────────────────────────
LOGIN_URL           = '/accounts/login/'
LOGIN_REDIRECT_URL  = '/productos/'
LOGOUT_REDIRECT_URL = '/'

# ── DRF ──────────────────────────────────────────────────────────────────
# core/settings.py — reemplazar la configuración REST_FRAMEWORK de W01:
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',   # para el navegador
        'rest_framework.authentication.TokenAuthentication',     # para clientes externos
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}



DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# core/settings.py — agregar al final del archivo

# ── STRIPE (Pasarela de pago) — W14 ───────────────────────────────────────
# Default vacío a propósito: si falta la variable, el checkout lo detecta y
# muestra un error controlado en lugar de intentar cobrar con una clave falsa.
STRIPE_SECRET_KEY      = env('STRIPE_SECRET_KEY',      default='')
STRIPE_PUBLISHABLE_KEY = env('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_WEBHOOK_SECRET  = env('STRIPE_WEBHOOK_SECRET',  default='')   # se usa en W15

# ── JAZZMIN — Personalización del admin con Fable 5 AzulERP ───────────────
JAZZMIN_SETTINGS = {
    # Identidad
    'site_title':       'ERP Django',
    'site_header':      'ERP UTEC Celaya',
    'site_brand':       '📦 ERP Django',
    'welcome_sign':     'Bienvenido al Sistema ERP · UTEC Celaya',
    'copyright':        'MC. Román Fernando López González · UTEC Celaya',

    # Icono del sitio (usar emoji como fallback)
    'site_icon':        None,
    'site_logo':        None,    # ruta a logo en static/ (agregar en W11+)

    # Búsqueda global en el admin
    'search_model':     ['clientes.Cliente', 'productos.Producto'],

    # Menú superior (top navigation)
    'topmenu_links': [
        {'name': 'Inicio ERP',   'url': '/', 'new_window': False},
        {'name': 'Productos',    'url': '/productos/'},
        {'name': 'Clientes',     'url': '/clientes/'},
        {'name': 'Ventas',       'url': '/ventas/'},
    ],

    # Menú de usuario (avatar)
    'usermenu_links': [
        {'name': 'Ver ERP', 'url': '/', 'new_window': False},
    ],

    # Menú lateral: orden de apps y modelos
    'order_with_respect_to': [
        'clientes', 'proveedores', 'productos',
        'ventas', 'configuracion', 'auth',
    ],

    # Iconos de Font Awesome para cada modelo
    'icons': {
        'auth':                       'fas fa-users-cog',
        'auth.user':                  'fas fa-user',
        'auth.Group':                 'fas fa-users',
        'clientes.Cliente':           'fas fa-user-tie',
        'proveedores.Proveedor':      'fas fa-truck',
        'productos.Categoria':        'fas fa-tags',
        'productos.Producto':         'fas fa-box',
        'ventas.Venta':               'fas fa-file-invoice-dollar',
        'ventas.DetalleVenta':        'fas fa-list',
        'ventas.Pedido':              'fas fa-shopping-cart',
        'configuracion.ConfiguracionERP': 'fas fa-cogs',
    },
    'default_icon_parents': 'fas fa-folder',
    'default_icon_children': 'fas fa-circle',

    # Apariencia
    'related_modal_active':     True,
    'custom_css':               'erp_custom.css',   # archivo en static/
    'show_sidebar':             True,
    'navigation_expanded':      True,
    'hide_apps':                [],
    'hide_models':              [],

    # UI tweaks
    'changeform_format':        'horizontal_tabs',
    'language_chooser':         False,
}

JAZZMIN_UI_TWEAKS = {
    'navbar_small_text':        False,
    'footer_small_text':        False,
    'body_small_text':          False,
    'brand_small_text':         False,
    'brand_colour':             'navbar-dark',
    'accent':                   'accent-navy',
    'navbar':                   'navbar-dark',
    'no_navbar_border':         False,
    'navbar_fixed':             True,
    'layout_boxed':             False,
    'footer_fixed':             False,
    'sidebar_fixed':            True,
    'sidebar':                  'sidebar-dark-navy',
    'sidebar_nav_small_text':   False,
    'sidebar_disable_expand':   False,
    'sidebar_nav_child_indent': True,
    'sidebar_nav_compact_style': False,
    'sidebar_nav_legacy_style': False,
    'sidebar_nav_flat_style':   False,
    'theme':                    'default',
    'dark_mode_theme':          None,
    'button_classes': {
        'primary':   'btn-primary',
        'secondary': 'btn-secondary',
        'info':      'btn-info',
        'warning':   'btn-warning',
        'danger':    'btn-danger',
        'success':   'btn-success',
    },
}

SITE_ID = 1

# ── AUTHENTICATION BACKENDS ───────────────────────────────────────────────
AUTHENTICATION_BACKENDS = [
    # Backend estándar de Django (username + password en admin)
    'django.contrib.auth.backends.ModelBackend',
    # Backend de allauth (permite login por email también)
    'allauth.account.auth_backends.AuthenticationBackend',
]

ACCOUNT_LOGIN_METHODS          = {'username'}   # login por username
ACCOUNT_SIGNUP_FIELDS          = ['username*', 'password1*', 'password2*']   # correo no obligatorio
ACCOUNT_EMAIL_VERIFICATION     = 'none'         # no enviar email de verificación
ACCOUNT_LOGOUT_ON_GET          = True           # logout sin confirmar (dev)
ACCOUNT_SESSION_REMEMBER       = True           # recordar sesión

# LOGIN_URL y LOGIN_REDIRECT_URL ya definidos en W01:
# LOGIN_URL           = '/accounts/login/'
# LOGIN_REDIRECT_URL  = '/productos/'
LOGOUT_REDIRECT_URL = '/'

# ── CELERY — Cola de tareas asíncronas (W16) ──────────────────────────────
# REDIS_URL definida (Render → Key Value): las tareas se encolan en Redis y
#     las procesa el worker.
# REDIS_URL vacía (laboratorio sin Docker / tests): modo EAGER → .delay()
#     ejecuta la tarea en el mismo proceso, sin broker ni worker.
REDIS_URL = env('REDIS_URL', default='')

if REDIS_URL:
    CELERY_BROKER_URL        = REDIS_URL
    CELERY_RESULT_BACKEND    = REDIS_URL
    CELERY_TASK_ALWAYS_EAGER = False
else:
    CELERY_BROKER_URL        = 'memory://'
    CELERY_RESULT_BACKEND    = 'cache+memory://'
    CELERY_TASK_ALWAYS_EAGER = True

CELERY_RESULT_EXPIRES    = 3600          # resultados caducan en 1 hora
CELERY_ACCEPT_CONTENT    = ['json']
CELERY_TASK_SERIALIZER   = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE          = TIME_ZONE
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_TASK_SOFT_TIME_LIMIT = 300        # 5 min
CELERY_TASK_TIME_LIMIT      = 360        # 6 min (límite duro)
CELERY_TASK_DEFAULT_QUEUE   = 'erp_django'
CELERY_TASK_EAGER_PROPAGATES = True      # en EAGER, las excepciones se propagan
# ─── W17: Correo (django-anymail + SendGrid) ──────────────────────────────
# Con SENDGRID_API_KEY → envío real por la API HTTPS de SendGrid (Render Free
# bloquea SMTP). Sin la clave → los correos se imprimen en la consola.
# En los tests Django usa siempre el backend locmem (no envía nada).
SENDGRID_API_KEY    = env('SENDGRID_API_KEY', default='')
DEFAULT_FROM_EMAIL  = env('DEFAULT_FROM_EMAIL', default='ERP Django <noreply@localhost>')
SERVER_EMAIL        = DEFAULT_FROM_EMAIL
ADMIN_EMAIL         = env('ADMIN_EMAIL', default='')   # destino de alertas de stock
if SENDGRID_API_KEY:
    EMAIL_BACKEND = 'anymail.backends.sendgrid.EmailBackend'
    ANYMAIL = {'SENDGRID_API_KEY': SENDGRID_API_KEY}
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ─── W18: Celery Beat — tareas programadas ────────────────────────────────
# Beat es el "reloj": a la hora indicada mete la tarea en la cola y el worker
# la ejecuta. En Render corre embebido en el worker (docker-entrypoint.sh).
# Las horas son HH:MM en hora de México y se cambian desde Render → Environment
# sin tocar código. Un valor con formato inválido vuelve al valor por defecto.
from celery.schedules import crontab


def _hora_hhmm(valor: str, defecto: tuple) -> tuple:
    """Convierte 'HH:MM' en (hora, minuto); si es inválida usa el defecto."""
    try:
        h, m = (int(x) for x in str(valor).strip().split(':'))
        if 0 <= h <= 23 and 0 <= m <= 59:
            return h, m
    except ValueError:
        pass
    return defecto


REPORTE_DIARIO_HORA = env('REPORTE_DIARIO_HORA', default='08:00')
ALERTA_STOCK_HORA   = env('ALERTA_STOCK_HORA',   default='08:05')
_rep_h, _rep_m = _hora_hhmm(REPORTE_DIARIO_HORA, (8, 0))
_stk_h, _stk_m = _hora_hhmm(ALERTA_STOCK_HORA,   (8, 5))

# URL pública para los enlaces de los correos (Render la inyecta sola).
SITE_URL = env('SITE_URL', default=env('RENDER_EXTERNAL_URL', default=''))

CELERY_BEAT_SCHEDULE = {
    # Una vez al día revisa el stock; el correo sale SOLO si hay productos bajos.
    'alerta-stock-bajo-diaria': {
        'task':     'ventas.verificar_stock_bajo',
        'schedule': crontab(hour=_stk_h, minute=_stk_m),
        'args':     (5,),   # umbral: menos de 5 unidades
    },
    # Una vez al día revisa las ventas de AYER; el correo sale SOLO si hubo.
    'reporte-ventas-diario': {
        'task':     'ventas.reporte_ventas_diario',
        'schedule': crontab(hour=_rep_h, minute=_rep_m),
    },
}
CELERY_BEAT_TIMEZONE = TIME_ZONE   # horas en México, no en UTC

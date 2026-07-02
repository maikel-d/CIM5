"""
Django settings for core project.
"""

from pathlib import Path
import sys
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent


# ---- Cargar variables de entorno ----
# python-dotenv carga .env sin sobrescribir variables del sistema.
# En Docker: las variables vienen de docker-compose (toman prioridad).
# En local: .env se carga correctamente sin interferencia de vars del sistema.
_env_file = BASE_DIR / ".env"
if _env_file.exists():
    load_dotenv(_env_file, override=False)


def _env(key, default=None, cast=None):
    """Lee variable de entorno con soporte de casteo.
    En Docker: usa variables del sistema (docker-compose define).
    En local: usa variables cargadas desde .env.
    Variables del sistema tienen prioridad sobre .env."""
    val = os.environ.get(key)
    if val is None:
        return default
    if cast is bool:
        return val.lower() in ("true", "1", "yes", "on")
    elif callable(cast):
        return cast(val)
    return val


def _csv(val):
    """Parsea string separado por comas a lista (reemplaza Csv())."""
    if isinstance(val, str):
        return [v.strip() for v in val.split(",") if v.strip()]
    return val
SECRET_KEY = _env('SECRET_KEY', default='cambiar-esta-clave-en-produccion')

# Saltar validacion durante tests (no necesita clave segura en desarrollo/CI)
if 'test' in sys.argv or 'pytest' in sys.modules:
    SECRET_KEY = 'test-secret-key-not-for-production'
elif SECRET_KEY == 'cambiar-esta-clave-en-produccion':
    import sys as _sys
    print("=" * 60, file=_sys.stderr)
    print("  ERROR DE SEGURIDAD: SECRET_KEY no configurada", file=_sys.stderr)
    print("=" * 60, file=_sys.stderr)
    print("  La variable SECRET_KEY tiene el valor por defecto.", file=_sys.stderr)
    print("  El servidor NO puede iniciar con una clave insegura.", file=_sys.stderr)
    print(file=_sys.stderr)
    print("  Para generar una clave unica, ejecuta:", file=_sys.stderr)
    print("    python3 -c 'import secrets; print(secrets.token_urlsafe(50))'", file=_sys.stderr)
    print(file=_sys.stderr)
    print("  Luego agregala a tu archivo .env:", file=_sys.stderr)
    print("    SECRET_KEY=<clave_generada>", file=_sys.stderr)
    print("=" * 60, file=_sys.stderr)
    _sys.exit(1)


DEBUG = _env('DEBUG', default=False, cast=bool)

# En desarrollo, agrega tu IP local a la variable ALLOWED_HOSTS en .env
ALLOWED_HOSTS = _env('ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=_csv)

# Detectar y agregar automáticamente la IP local de red para acceso desde otros dispositivos
local_ip = ''
import socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0.1)
    s.connect(("8.8.8.8", 80))
    local_ip = s.getsockname()[0]
    s.close()
    if local_ip and local_ip not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(local_ip)
except Exception:
    pass

# Si DEBUG está activo, permitir cualquier host (útil en desarrollo local)
if DEBUG and 'localhost' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.extend(['localhost', '127.0.0.1'])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'sorl.thumbnail',
    'direccion',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'direccion.middleware.CSRFTrustedOriginMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'direccion.middleware.UserOnlineMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'direccion.context_processors.notificaciones',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

DATA_DIR = BASE_DIR / 'data'
DATA_DIR.mkdir(exist_ok=True)

DATABASES = {
    'default': {
        'ENGINE': _env('DB_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': _env('DB_NAME', default=str(DATA_DIR / 'db.sqlite3')),
        'USER': _env('DB_USER', default=''),
        'PASSWORD': _env('DB_PASSWORD', default=''),
        'HOST': _env('DB_HOST', default=''),
        'PORT': _env('DB_PORT', default=''),
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': _env('REDIS_URL', default='redis://127.0.0.1:6379/1'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Caracas'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
# En producción (DEBUG=False), usar WhiteNoise con compresión y manifiesto.
# En desarrollo/testing, Django sirve los archivos estáticos directamente.
if not DEBUG:
    STORAGES = {
        'default': {
            'BACKEND': 'django.core.files.storage.FileSystemStorage',
        },
        'staticfiles': {
            'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
        },
    }

# Media files (fotos, documentos)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Auth settings
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

# Límite de tamaño para archivos subidos (coincide con la validación en forms.py: 10MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB

# Archivos >2.5MB se escriben a disco en vez de mantenerse en memoria
FILE_UPLOAD_MAX_MEMORY_SIZE = 2.5 * 1024 * 1024  # 2.5 MB (default de Django)

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Seguridad para producción detrás de nginx
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = _env('SECURE_SSL_REDIRECT', default=False, cast=bool)

# HTTPS Security Headers (solo cuando DEBUG=False y DOMAIN está configurado)
_domain = _env('DOMAIN', default='')

# When running tests, override environment settings to avoid SSL redirects
# and ensure DEBUG is enabled. This must be placed AFTER all config() calls
# to ensure the overrides take effect.
if 'test' in sys.argv:
    DEBUG = True
    SECURE_SSL_REDIRECT = False

# Seguridad: prevenir DEBUG=True accidental en produccion
if DEBUG and 'test' not in sys.argv:
    import warnings
    warnings.warn('DEBUG=True fuera de pruebas - posible riesgo de seguridad', RuntimeWarning)

if not DEBUG:
    # Content Security Policy básica
    SECURE_CONTENT_TYPE_NOSNIFF = True

if not DEBUG and _domain:
    # HSTS: forzar HTTPS por 2 años (63072000s) solo si es un dominio real
    # (no aplicar HSTS a IPs locales porque produce errores)
    if not _domain.replace('.', '').isdigit():
        SECURE_HSTS_SECONDS = 63072000
        SECURE_HSTS_INCLUDE_SUBDOMAINS = True
        SECURE_HSTS_PRELOAD = True

    # Cookies seguras solo por HTTPS (activar con SECURE_COOKIES=true en .env)
    # Nota: Si accedes por HTTP (IP local), mantener SECURE_COOKIES=false
    SESSION_COOKIE_SECURE = _env('SECURE_COOKIES', default=False, cast=bool)
    CSRF_COOKIE_SECURE = _env('SECURE_COOKIES', default=False, cast=bool)
    CSRF_COOKIE_HTTPONLY = _env('SECURE_COOKIES', default=False, cast=bool)

    # Trusted origins para CSRF: incluir HTTP y HTTPS para la IP/dominio
    # Esto permite que la redirección HTTP→HTTPS funcione sin errores CSRF
    CSRF_TRUSTED_ORIGINS = [
        f'https://{_domain}',
        f'http://{_domain}',
    ]
    # Si el dominio es una IP, agregar también los puertos personalizados
    if _domain.replace('.', '').isdigit():
        _webui_port = _env('WEBUI_PORT', default='80')
        if _webui_port != '80':
            CSRF_TRUSTED_ORIGINS.append(f'https://{_domain}:{_webui_port}')
            CSRF_TRUSTED_ORIGINS.append(f'http://{_domain}:{_webui_port}')
        # Puerto HTTPS personalizado (WEBUI_PORT_SSL)
        _webui_port_ssl = _env('WEBUI_PORT_SSL', default='443')
        if _webui_port_ssl != '443':
            CSRF_TRUSTED_ORIGINS.append(f'https://{_domain}:{_webui_port_ssl}')

# Sin DOMAIN (modo HTTP/IP local como CasaOS): construir CSRF_TRUSTED_ORIGINS
# dinamicamente con la IP local y el puerto WEBUI_PORT.
# Django 4.0+ NO acepta '*' en ALLOWED_HOSTS para validar el Referer de CSRF,
# por lo que debemos listar explicitamente los origenes confiables.
# Ademas, usar CSRF_USE_SESSIONS para evitar problemas con cookies CSRF
# en entornos con proxies como CasaOS.
if not DEBUG and not _domain:
    CSRF_USE_SESSIONS = True

    # Construir trusted origins desde la IP local detectada + ALLOWED_HOSTS
    _webui_port = _env('WEBUI_PORT', default='80')
    _trusted_origins = []

    # Agregar la IP local con puerto (ej: http://192.168.0.101:8080)
    try:
        if local_ip:
            _trusted_origins.append(f'http://{local_ip}:{_webui_port}')
            _trusted_origins.append(f'http://{local_ip}')
    except Exception:
        pass

    # Agregar ALLOWED_HOSTS (excepto '*' que Django rechaza)
    for _host in ALLOWED_HOSTS:
        if _host and _host != '*':
            _trusted_origins.append(f'http://{_host}')
            if ':' not in _host and _webui_port != '80':
                _trusted_origins.append(f'http://{_host}:{_webui_port}')

    # Agregar localhost siempre
    _trusted_origins.append('http://localhost')
    if _webui_port != '80':
        _trusted_origins.append(f'http://localhost:{_webui_port}')
        _trusted_origins.append(f'http://127.0.0.1:{_webui_port}')
    _trusted_origins.append('http://127.0.0.1')

    CSRF_TRUSTED_ORIGINS = _trusted_origins



LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file_django': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/DATA/CIM5NV/logs/django.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'file_errors': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/DATA/CIM5NV/logs/errors.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file_django'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console', 'file_errors'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['file_django'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}



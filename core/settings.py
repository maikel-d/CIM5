"""
Django settings for core project.
"""

from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='cambiar-esta-clave-en-produccion')

DEBUG = config('DEBUG', default=False, cast=bool)

# En desarrollo, agrega tu IP local a la variable ALLOWED_HOSTS en .env
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())

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
if DEBUG and '*' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('*')

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
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
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
        'ENGINE': config('DB_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': config('DB_NAME', default=str(DATA_DIR / 'db.sqlite3')),
        'USER': config('DB_USER', default=''),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default=''),
        'PORT': config('DB_PORT', default=''),
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

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Seguridad para producción detrás de nginx
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)

# HTTPS Security Headers (solo cuando DEBUG=False y DOMAIN está configurado)
_domain = config('DOMAIN', default='')

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

    # Cookies seguras solo por HTTPS
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True

    # Trusted origins para CSRF: incluir HTTP y HTTPS para la IP/dominio
    # Esto permite que la redirección HTTP→HTTPS funcione sin errores CSRF
    CSRF_TRUSTED_ORIGINS = [
        f'https://{_domain}',
        f'http://{_domain}',
    ]
    # Si el dominio es una IP, agregar también los puertos personalizados
    if _domain.replace('.', '').isdigit():
        _webui_port = config('WEBUI_PORT', default='80')
        if _webui_port != '80':
            CSRF_TRUSTED_ORIGINS.append(f'https://{_domain}:{_webui_port}')
            CSRF_TRUSTED_ORIGINS.append(f'http://{_domain}:{_webui_port}')
        # Puerto HTTPS personalizado (WEBUI_PORT_SSL)
        _webui_port_ssl = config('WEBUI_PORT_SSL', default='443')
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
    _webui_port = config('WEBUI_PORT', default='80')
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


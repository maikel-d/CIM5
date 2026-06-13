"""Middleware personalizado para el Sistema de Gestión - Dirección General"""

import time

from django.conf import settings
from django.contrib.auth import logout
from django.core.cache import cache
from django.shortcuts import redirect


ONLINE_TIMEOUT = 300  # 5 minutos sin actividad para considerarse "desconectado"


def usuarios_online():
    """Retorna el número de usuarios activos en los últimos 5 minutos."""
    online_ids = cache.get('online_users', set())
    if not online_ids:
        return 0
    ahora = time.time()
    activos = 0
    for uid in list(online_ids):
        last_seen = cache.get(f'online_{uid}', 0)
        if ahora - last_seen < ONLINE_TIMEOUT:
            activos += 1
    return activos


class UserOnlineMiddleware:
    """
    Actualiza la marca de "última actividad" del usuario en cache
    y lo agrega al conjunto de usuarios online.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            uid = request.user.pk

            # Verificar sesión única (una sola sesión por usuario)
            if 'session_token' in request.session:
                stored_token = cache.get(f'auth_token_{uid}')
                if stored_token and request.session['session_token'] != stored_token:
                    # Esta sesión fue invalidada por un nuevo inicio de sesión
                    logout(request)
                    return redirect('login')

            ahora = time.time()
            cache.set(f'online_{uid}', ahora, ONLINE_TIMEOUT * 2)
            online_ids = cache.get('online_users', set())
            online_ids.add(uid)
            cache.set('online_users', online_ids, ONLINE_TIMEOUT * 2)
        return self.get_response(request)


class CSRFTrustedOriginMiddleware:
    """
    Agrega dinámicamente el host de la solicitud actual a
    CSRF_TRUSTED_ORIGINS para que el Referer check de CSRF no falle
    en entornos con IP dinámica (CasaOS, redes locales).

    Django 4.0+ excluye '*' de ALLOWED_HOSTS cuando construye la lista de
    orígenes confiables para CSRF, lo que causa 403 en navegadores que
    envían cabecera Referer. Este middleware resuelve ese problema
    agregando el host real (IP:puerto) antes de la validación CSRF.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Solo actuar si no hay CSRF_TRUSTED_ORIGINS definido (modo HTTP/IP local)
        if not settings.CSRF_TRUSTED_ORIGINS:
            host = request.get_host()
            if host:
                origin = f"http://{host}"
                # Verificar si ya existe
                origins = list(settings.CSRF_TRUSTED_ORIGINS)
                if origin not in origins:
                    origins.append(origin)
                    # Usar setattr para asegurar atomicidad de la asignacion
                    # (settings puede ser un objeto LazyObject o similar)
                    setattr(settings, 'CSRF_TRUSTED_ORIGINS', origins)
        return self.get_response(request)

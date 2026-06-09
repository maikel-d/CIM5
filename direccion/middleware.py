"""Middleware personalizado para el Sistema de Gestión - Dirección General"""

from django.conf import settings


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
                    settings.CSRF_TRUSTED_ORIGINS = origins
        return self.get_response(request)

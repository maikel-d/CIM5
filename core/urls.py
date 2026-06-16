from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.db import connection, OperationalError
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt


@require_GET
@csrf_exempt
def health_check(request):
    """Health check endpoint para Docker healthcheck.
    Verifica conexión a BD y retorna JSON rápido sin templates ni sesiones.
    """
    try:
        connection.ensure_connection()
        db_status = "connected"
        status = "ok"
    except Exception:
        db_status = "error"
        status = "degraded"

    return JsonResponse({
        "status": status,
        "database": db_status,
    })


urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('admin/', admin.site.urls),
    path('', include('direccion.urls')),
]

from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.static import serve

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Serve PDF files without X-Frame-Options for the inline PDF viewer
    urlpatterns += [re_path(r'^media/(?P<path>.*\.pdf)$', xframe_options_exempt(serve), {'document_root': settings.MEDIA_ROOT})]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

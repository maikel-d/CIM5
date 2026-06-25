from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.db import connection, OperationalError
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
import time


@require_GET
@csrf_exempt
def health_check(request):
    """Health check endpoint para Docker healthcheck.
    Verifica conexión a BD, Redis cache y retorna JSON.
    HTTP 200 = saludable, HTTP 503 = degradado.
    """
    start = time.time()
    
    checks = {
        "database": {"status": "ok", "latency_ms": 0},
        "cache": {"status": "ok", "latency_ms": 0},
    }
    overall = "ok"
    http_code = 200
    
    # Check database
    try:
        t0 = time.time()
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"]["latency_ms"] = round((time.time() - t0) * 1000, 1)
    except Exception as e:
        checks["database"] = {"status": "error", "error": str(e)[:100]}
        overall = "degraded"
        http_code = 503
    
    # Check Redis cache
    try:
        t0 = time.time()
        cache.set("_health_ping", "ok", 5)
        val = cache.get("_health_ping")
        checks["cache"]["latency_ms"] = round((time.time() - t0) * 1000, 1)
        if val != "ok":
            raise ValueError("Cache mismatch")
    except Exception as e:
        checks["cache"] = {"status": "error", "error": str(e)[:100]}
        overall = "degraded"
        http_code = 503
    
    response = JsonResponse({
        "status": overall,
        "checks": checks,
        "response_time_ms": round((time.time() - start) * 1000, 1),
        "timestamp": int(time.time()),
    })
    response.status_code = http_code
    return response


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

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
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

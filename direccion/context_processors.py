from django.core.cache import cache
from .models import Notificacion, Caso
from .middleware import usuarios_online

def notificaciones(request):
    """Devuelve el conteo de notificaciones no leídas del usuario y
    la lista de casos activos para los sub-menús del sidebar.
    """
    context = {}
    if request.user.is_authenticated:
        cache_key = f'notis_unread_{request.user.pk}'
        no_leidas = cache.get(cache_key)
        if no_leidas is None:
            no_leidas = Notificacion.objects.filter(
                usuario=request.user, leida=False
            ).count()
            cache.set(cache_key, no_leidas, 60)
        context['notificaciones_no_leidas'] = no_leidas
        # Casos activos para sub-menús del sidebar
        # Cache sidebar_casos for 180 seconds to avoid query on every request
        sidebar_cache_key = 'sidebar_casos_cache'
        sidebar_casos = cache.get(sidebar_cache_key)
        if sidebar_casos is None:
            sidebar_casos = list(Caso.objects.filter(activo=True).order_by('nombre'))
            cache.set(sidebar_cache_key, sidebar_casos, 180)
        context['sidebar_casos'] = sidebar_casos
        # Usuarios conectados
        context['usuarios_online'] = usuarios_online()
    else:
        context['notificaciones_no_leidas'] = 0
        context['sidebar_casos'] = []
        context['usuarios_online'] = 0
    return context

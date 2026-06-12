from django.core.cache import cache
from .models import Notificacion, Caso

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
        context['sidebar_casos'] = Caso.objects.filter(activo=True).order_by('nombre')
    else:
        context['notificaciones_no_leidas'] = 0
        context['sidebar_casos'] = []
    return context

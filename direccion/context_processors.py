from django.core.cache import cache
from .models import Notificacion

def notificaciones(request):
    """Devuelve el conteo de notificaciones no leídas del usuario.
    Usa Django cache (60s TTL) para evitar una query en cada petición HTTP.
    """
    if request.user.is_authenticated:
        cache_key = f'notis_unread_{request.user.pk}'
        no_leidas = cache.get(cache_key)
        if no_leidas is None:
            no_leidas = Notificacion.objects.filter(
                usuario=request.user, leida=False
            ).count()
            cache.set(cache_key, no_leidas, 60)
        return {
            'notificaciones_no_leidas': no_leidas,
        }
    return {'notificaciones_no_leidas': 0}

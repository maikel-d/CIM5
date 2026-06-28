# ============================================================
# Notificaciones
# ============================================================

from django.shortcuts import render
from ..decorators import permiso_required
from .. import permissions as perms
from django.core.cache import cache

from ..models import Notificacion


@permiso_required(perms.NOTIFICACIONES_VER)
def notificaciones_list(request):
    """Lista todas las notificaciones y marca las no leídas como leídas."""
    notis = Notificacion.objects.filter(usuario=request.user)
    notis.filter(leida=False).update(leida=True)
    # Invalidar cache del badge de notificaciones
    cache.delete(f'notis_unread_{request.user.pk}')
    return render(request, "direccion/notificaciones_list.html", {
        "notificaciones": notis,
    })




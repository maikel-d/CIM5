from .models import Notificacion

def notificaciones(request):
    if request.user.is_authenticated:
        no_leidas = Notificacion.objects.filter(
            usuario=request.user, leida=False
        ).count()
        return {
            'notificaciones_no_leidas': no_leidas,
        }
    return {'notificaciones_no_leidas': 0}

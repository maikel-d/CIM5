from .models import AuditLog

def auditar(request, accion, modelo, objeto_id=None, objeto_repr="", detalle=""):
    ip = request.META.get("REMOTE_ADDR", "")
    username = request.user.username if request.user.is_authenticated else "ANONIMO"
    AuditLog.objects.create(
        usuario=request.user if request.user.is_authenticated else None,
        username=username,
        accion=accion,
        modelo=modelo,
        objeto_id=objeto_id,
        objeto_repr=str(objeto_repr)[:255],
        detalle=str(detalle),
        direccion_ip=ip,
    )

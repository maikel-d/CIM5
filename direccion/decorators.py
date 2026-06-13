from django.shortcuts import redirect, render
from functools import wraps

from .permissions import verificar_permiso_acceso


def _pagina_403(request, mensaje):
    """Renderiza la pagina 403 con estilo glassmorphism usando el template."""
    usuario = str(request.user)
    response = render(request, '403.html', {
        'mensaje': mensaje,
        'usuario': usuario,
    })
    response.status_code = 403
    return response


def permiso_required(*permisos):
    """Decorador para restringir acceso basado en permisos granulares."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("login")
            if verificar_permiso_acceso(request.user, permisos):
                return view_func(request, *args, **kwargs)
            return _pagina_403(request, "No tienes permisos para acceder a esta seccion.")
        return _wrapped_view
    return decorator


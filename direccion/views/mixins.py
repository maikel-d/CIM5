# ============================================================
# Mixins de vistas
# ============================================================

from django.contrib.auth.mixins import LoginRequiredMixin
from django.middleware.csrf import get_token
from ..decorators import _pagina_403


class PermissionRequiredMixin(LoginRequiredMixin):
    """Mixin que verifica permisos granulares en dispatch()."""
    permisos_requeridos = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        try:
            profile = request.user.profile
            for permiso in self.permisos_requeridos:
                if profile.tiene_permiso(permiso):
                    return super().dispatch(request, *args, **kwargs)
            return _pagina_403(request.user, "No tienes permisos.", get_token(request))
        except Exception:
            return _pagina_403(request.user, "No tienes permisos.", get_token(request))

# ============================================================
# Mixins de vistas
# ============================================================

from django.contrib.auth.mixins import LoginRequiredMixin
from django.middleware.csrf import get_token

from ..decorators import _pagina_403
from ..permissions import verificar_permiso_acceso


class PermissionRequiredMixin(LoginRequiredMixin):
    """Mixin que verifica permisos granulares en dispatch()."""
    permisos_requeridos = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if verificar_permiso_acceso(request.user, self.permisos_requeridos):
            return super().dispatch(request, *args, **kwargs)
        return _pagina_403(request.user, "No tienes permisos.", get_token(request))

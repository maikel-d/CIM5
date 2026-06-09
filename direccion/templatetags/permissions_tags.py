from django import template
from direccion.permissions import tiene_permiso as _check_permiso

register = template.Library()


@register.filter
def can(profile, permiso):
    """Template filter para verificar si un perfil tiene un permiso.
    Uso: {{ user.profile|can:'personal_ver' }}
    """
    return _check_permiso(profile.rol, permiso)




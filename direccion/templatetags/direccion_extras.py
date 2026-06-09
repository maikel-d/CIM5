import os
from django import template

register = template.Library()


@register.filter
def filename(value):
    """Extrae solo el nombre del archivo de una ruta completa."""
    if not value:
        return value
    return os.path.basename(value)

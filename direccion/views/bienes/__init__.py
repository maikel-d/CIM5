# ============================================================
# Vista: Re-exporta todas las vistas del modulo bienes
# ============================================================

from .bien_views import (
    bien_crear_rapido,
    BienListView, BienCreateView, BienDetailView,
    BienUpdateView, BienDeleteView,
    agregar_documento_bien, eliminar_documento_bien,
)
from .carpeta_views import (
    carpeta_bien_crear, carpeta_bien_renombrar, carpeta_bien_eliminar,
    CarpetaBienUpdateView, CarpetaBienDetailView,
    agregar_documento_carpeta, eliminar_documento_carpeta,
)

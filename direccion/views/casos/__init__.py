# ============================================================
# Vista: Re-exporta todas las vistas del modulo casos
# ============================================================

from .caso_views import (
    CasoListView, CasoCreateView, CasoDetailView,
    CasoUpdateView, CasoDeleteView,
    agregar_documento_caso, eliminar_documento_caso,
    caso_crear_rapido,
)
from .investigado_views import (
    InvestigadoListView, InvestigadoCreateView, InvestigadoDetailView,
    InvestigadoUpdateView, InvestigadoDeleteView,
    agregar_documento_investigado, eliminar_documento_investigado,
)

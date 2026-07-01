# ============================================================
# Vista: Re-exporta todas las vistas del modulo documentos
# ============================================================

from .views import (
    documentos_direccion_list, documentos_direccion_categoria,
    editar_documento_direccion, eliminar_documento_direccion,
)
from .api import batch_upload_documentos
from .carpetas import (
    carpeta_direccion_crear, carpeta_direccion_renombrar,
    carpeta_direccion_eliminar,
)

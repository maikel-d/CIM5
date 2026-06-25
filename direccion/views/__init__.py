# ============================================================
# Vista: Importaciones globales del paquete views/
# Re-exporta todas las vistas para compatibilidad con urls.py
# ============================================================

from .mixins import PermissionRequiredMixin
from .auth import CustomLoginView
from .dashboard import dashboard, usuarios_online_json
from .personal import (
    PersonalListView, PersonalCreateView, PersonalDetailView,
    PersonalUpdateView, PersonalDeleteView,
    agregar_documento_personal, eliminar_documento_personal,
)
from .casos import (
    CasoListView, CasoCreateView, CasoDetailView,
    CasoUpdateView, CasoDeleteView,
    agregar_documento_caso, eliminar_documento_caso,
    InvestigadoListView, InvestigadoCreateView, InvestigadoDetailView,
    InvestigadoUpdateView, InvestigadoDeleteView,
    agregar_documento_investigado, eliminar_documento_investigado,
)
from .documentos import documentos_direccion_list, editar_documento_direccion, eliminar_documento_direccion, batch_upload_documentos, documentos_direccion_categoria, carpeta_direccion_crear, carpeta_direccion_renombrar, carpeta_direccion_eliminar
from .usuarios import (
    UserListView, UserCreateView, UserUpdateView,
    user_toggle_active, user_delete,
)
from .notificaciones import notificaciones_list
from .tareas import tareas_list, tarea_completar, tarea_eliminar
from .tickets import (
    ticket_detail, ticket_list, ticket_create,
    ticket_resolver, ticket_asignar, ticket_cambiar_estado, ticket_eliminar,
)
from .informes import (
    informes_diarios_list, previsualizar_informe_pdf,
    exportar_informes_descargar, eliminar_informe_diario,
)
from .busqueda import busqueda_global
from .bienes import (
    BienListView, BienCreateView, BienDetailView,
    BienUpdateView, BienDeleteView,
    agregar_documento_bien, eliminar_documento_bien,
    agregar_documento_carpeta, eliminar_documento_carpeta,
    carpeta_bien_crear, carpeta_bien_renombrar, carpeta_bien_eliminar,
    CarpetaBienDetailView, CarpetaBienUpdateView,
)
from .reportes import panel_reportes
from .backup import backup_view, descargar_backup, restaurar_backup
from .auditoria import (
    audit_log_list, exportar_auditoria_excel, exportar_auditoria_pdf,
)
from .export import (
    exportar_personal_excel, exportar_personal_pdf,
    exportar_investigados_excel, exportar_investigados_pdf,
)

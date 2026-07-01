from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # Dashboard
    path("", views.DashboardView.as_view(), name="dashboard"),

    # User management (Admin only)
    path("usuarios/", views.UserListView.as_view(), name="usuario_list"),
    path("usuarios/crear/", views.UserCreateView.as_view(), name="usuario_create"),
    path("usuarios/<int:pk>/editar/", views.UserUpdateView.as_view(), name="usuario_edit"),
    path("usuarios/<int:pk>/toggle/", views.user_toggle_active, name="usuario_toggle"),
    path("usuarios/<int:pk>/eliminar/", views.user_delete, name="usuario_delete"),

    # Documentacion de la Direccion
    path("documentos-direccion/", views.documentos_direccion_list, name="documentos_direccion"),
    path("documentos-direccion/batch-upload/", views.batch_upload_documentos, name="batch_upload_documentos"),
    path("documentos-direccion/carpeta/crear/", views.carpeta_direccion_crear, name="carpeta_direccion_crear"),
    path("documentos-direccion/carpeta/<int:pk>/renombrar/", views.carpeta_direccion_renombrar, name="carpeta_direccion_renombrar"),
    path("documentos-direccion/carpeta/<int:pk>/eliminar/", views.carpeta_direccion_eliminar, name="carpeta_direccion_eliminar"),
    path("documentos-direccion/<int:doc_pk>/editar/", views.editar_documento_direccion, name="documento_direccion_edit"),
    path("documentos-direccion/<int:doc_pk>/eliminar/", views.eliminar_documento_direccion, name="documento_direccion_delete"),
    path("documentos-direccion/<str:categoria>/", views.documentos_direccion_categoria, name="documentos_direccion_categoria"),

    # Personal CRUD
    path("personal/", views.PersonalListView.as_view(), name="personal_list"),
    path("personal/crear/", views.PersonalCreateView.as_view(), name="personal_create"),
    path("personal/<int:pk>/", views.PersonalDetailView.as_view(), name="personal_detail"),
    path("personal/<int:pk>/editar/", views.PersonalUpdateView.as_view(), name="personal_edit"),
    path("personal/<int:pk>/eliminar/", views.PersonalDeleteView.as_view(), name="personal_delete"),
    path("personal/<int:pk>/documento/agregar/", views.agregar_documento_personal, name="personal_documento_add"),
    path("personal/<int:pk>/documento/<int:doc_pk>/eliminar/", views.eliminar_documento_personal, name="personal_documento_delete"),

    # Casos CRUD
    path("casos/", views.CasoListView.as_view(), name="caso_list"),
    path("casos/crear/", views.CasoCreateView.as_view(), name="caso_create"),
    path("casos/<int:pk>/", views.CasoDetailView.as_view(), name="caso_detail"),
    path("casos/<int:pk>/editar/", views.CasoUpdateView.as_view(), name="caso_edit"),
    path("casos/<int:pk>/eliminar/", views.CasoDeleteView.as_view(), name="caso_delete"),
    path("casos/crear-rapido/", views.caso_crear_rapido, name="caso_crear_rapido"),
    path("casos/<int:pk>/documento/agregar/", views.agregar_documento_caso, name="caso_documento_add"),
    path("casos/<int:pk>/documento/<int:doc_pk>/eliminar/", views.eliminar_documento_caso, name="caso_documento_delete"),

    # Investigados CRUD
    path("investigados/", views.InvestigadoListView.as_view(), name="investigado_list"),
    path("investigados/crear/", views.InvestigadoCreateView.as_view(), name="investigado_create"),
    path("investigados/<int:pk>/", views.InvestigadoDetailView.as_view(), name="investigado_detail"),
    path("investigados/<int:pk>/editar/", views.InvestigadoUpdateView.as_view(), name="investigado_edit"),
    path("investigados/<int:pk>/eliminar/", views.InvestigadoDeleteView.as_view(), name="investigado_delete"),
    path("investigados/<int:pk>/documento/agregar/", views.agregar_documento_investigado, name="investigado_documento_add"),
    path("investigados/<int:pk>/documento/<int:doc_pk>/eliminar/", views.eliminar_documento_investigado, name="investigado_documento_delete"),
    # Export to Excel
    path("personal/exportar/", views.exportar_personal_excel, name="personal_export"),
    path("investigados/exportar/", views.exportar_investigados_excel, name="investigado_export"),

    # Export to PDF
    path("personal/exportar-pdf/", views.exportar_personal_pdf, name="personal_pdf"),
    path("investigados/exportar-pdf/", views.exportar_investigados_pdf, name="investigado_pdf"),

    # Notificaciones
    path("notificaciones/", views.notificaciones_list, name="notificaciones_list"),

    # Tareas Pendientes
    path("tareas/", views.tareas_list, name="tareas_list"),
    path("tareas/<int:pk>/completar/", views.tarea_completar, name="tarea_completar"),
    path("tareas/<int:pk>/eliminar/", views.tarea_eliminar, name="tarea_eliminar"),

    # Tickets de Soporte
    path("tickets/", views.ticket_list, name="ticket_list"),
    path("tickets/<int:pk>/", views.ticket_detail, name="ticket_detail"),
    path("tickets/crear/", views.ticket_create, name="ticket_create"),
    path("tickets/<int:pk>/resolver/", views.ticket_resolver, name="ticket_resolver"),
    path("tickets/<int:pk>/asignar/", views.ticket_asignar, name="ticket_asignar"),

    path("tickets/<int:pk>/estado/", views.ticket_cambiar_estado, name="ticket_estado"),
    path("tickets/<int:pk>/eliminar/", views.ticket_eliminar, name="ticket_eliminar"),

    # Informes Diarios
    path("informes-diarios/", views.informes_diarios_list, name="informes_diarios"),
    path("informes-diarios/descargar/", views.exportar_informes_descargar, name="informes_descargar"),
    path("informes-diarios/<int:pk>/eliminar/", views.eliminar_informe_diario, name="informe_diario_eliminar"),
    path("informes-diarios/<int:pk>/previsualizar/", views.previsualizar_informe_pdf, name="informe_diario_preview"),

    # Búsqueda Global (JSON)
    path("buscar/", views.busqueda_global, name="busqueda_global"),

    # Bienes CRUD
    path("bienes/", views.BienListView.as_view(), name="bien_list"),
    path("bienes/crear/", views.BienCreateView.as_view(), name="bien_create"),
    path("bienes/<int:pk>/", views.BienDetailView.as_view(), name="bien_detail"),
    path("bienes/<int:pk>/editar/", views.BienUpdateView.as_view(), name="bien_edit"),
    path("bienes/<int:pk>/eliminar/", views.BienDeleteView.as_view(), name="bien_delete"),
    path("bienes/<int:pk>/documento/agregar/", views.agregar_documento_bien, name="bien_documento_add"),
    path("bienes/<int:pk>/documento/<int:doc_pk>/eliminar/", views.eliminar_documento_bien, name="bien_documento_delete"),
    path("bienes/crear-rapido/", views.bien_crear_rapido, name="bien_crear_rapido"),
    path("bienes/carpeta/crear/", views.carpeta_bien_crear, name="bien_carpeta_crear"),
    path("bienes/carpeta/<int:pk>/renombrar/", views.carpeta_bien_renombrar, name="bien_carpeta_renombrar"),
    path("bienes/carpeta/<int:pk>/editar/", views.CarpetaBienUpdateView.as_view(), name="bien_carpeta_edit"),
    path("bienes/carpeta/<int:pk>/eliminar/", views.carpeta_bien_eliminar, name="bien_carpeta_eliminar"),
    path("bienes/carpeta/<int:pk>/documento/subir/", views.agregar_documento_carpeta, name="bien_carpeta_doc_upload"),
    path("bienes/carpeta/<int:pk>/documento/<int:doc_pk>/eliminar/", views.eliminar_documento_carpeta, name="bien_carpeta_doc_delete"),
    path("bienes/carpeta/<int:pk>/", views.CarpetaBienDetailView.as_view(), name="bien_carpeta_detail"),

    # Reports Center
    path("reportes/", views.panel_reportes, name="reportes"),

    # Audit Logs (Admin only)
    path("auditoria/", views.audit_log_list, name="audit_log_list"),
    path("auditoria/exportar-excel/", views.exportar_auditoria_excel, name="audit_log_export_excel"),
    path("auditoria/exportar-pdf/", views.exportar_auditoria_pdf, name="audit_log_export_pdf"),

    # Backup & Restore (Admin only)
    path("backup/", views.backup_view, name="backup"),
    path("backup/descargar/", views.descargar_backup, name="backup_descargar"),
    path("backup/restaurar/", views.restaurar_backup, name="backup_restaurar"),

    # API JSON
    path("usuarios-online/json/", views.usuarios_online_json, name="usuarios_online_json"),
]

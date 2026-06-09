from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile, Personal, DocumentoPersonal, Caso, Investigado, DocumentoInvestigado, DocumentoDireccion, DocumentoCaso, AuditLog, TicketSoporte, TicketHistorial, Tarea, Notificacion, InformeDiario


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Perfil"


class CustomUserAdmin(UserAdmin):
    inlines = [UserProfileInline]
    list_display = ["username", "email", "first_name", "last_name", "is_active", "get_rol"]
    list_filter = ["is_active", "profile__rol"]

    def get_rol(self, obj):
        try:
            return obj.profile.get_rol_display()
        except Exception:
            return "-"
    get_rol.short_description = "Rol"

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


class DocumentoPersonalInline(admin.TabularInline):
    model = DocumentoPersonal
    extra = 1
    fields = ["archivo", "descripcion", "tipo", "fecha_subida"]
    readonly_fields = ["tipo", "fecha_subida"]


@admin.register(Personal)
class PersonalAdmin(admin.ModelAdmin):
    list_display = ["apellidos", "nombres", "cedula", "activo"]
    search_fields = ["apellidos", "nombres", "cedula"]
    list_filter = ["activo"]
    inlines = [DocumentoPersonalInline]


@admin.register(DocumentoCaso)
class DocumentoCasoAdmin(admin.ModelAdmin):
    list_display = ["caso", "archivo", "tipo", "descripcion", "fecha_subida"]
    list_filter = ["tipo"]
    search_fields = ["descripcion", "caso__nombre"]


@admin.register(DocumentoPersonal)
class DocumentoPersonalAdmin(admin.ModelAdmin):
    list_display = ["personal", "tipo", "descripcion", "fecha_subida"]
    list_filter = ["tipo"]


class DocumentoInvestigadoInline(admin.TabularInline):
    model = DocumentoInvestigado
    extra = 1
    fields = ["archivo", "descripcion", "tipo", "fecha_subida"]
    readonly_fields = ["tipo", "fecha_subida"]


@admin.register(Caso)
class CasoAdmin(admin.ModelAdmin):
    list_display = ["nombre", "fecha_apertura", "count_investigados", "activo"]
    search_fields = ["nombre"]
    list_filter = ["activo"]


@admin.register(Investigado)
class InvestigadoAdmin(admin.ModelAdmin):
    list_display = ["apellidos", "nombres", "cedula", "caso", "activo"]
    search_fields = ["apellidos", "nombres", "cedula"]
    list_filter = ["activo", "caso"]
    inlines = [DocumentoInvestigadoInline]


@admin.register(DocumentoInvestigado)
class DocumentoInvestigadoAdmin(admin.ModelAdmin):
    list_display = ["investigado", "tipo", "descripcion", "fecha_subida"]
    list_filter = ["tipo"]


@admin.register(DocumentoDireccion)
class DocumentoDireccionAdmin(admin.ModelAdmin):
    list_display = ["descripcion", "tipo", "fecha_subida"]
    list_filter = ["tipo"]
    search_fields = ["descripcion"]


class TicketHistorialInline(admin.TabularInline):
    model = TicketHistorial
    extra = 0
    readonly_fields = ['usuario', 'campo', 'valor_anterior', 'valor_nuevo', 'fecha']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(TicketSoporte)
class TicketSoporteAdmin(admin.ModelAdmin):
    list_display = ["pk", "asunto", "estado", "prioridad", "creado_por", "asignado_a", "fecha_creacion"]
    list_filter = ["estado", "prioridad"]
    search_fields = ["asunto", "descripcion"]
    inlines = [TicketHistorialInline]


@admin.register(TicketHistorial)
class TicketHistorialAdmin(admin.ModelAdmin):
    list_display = ["ticket", "usuario", "campo", "valor_anterior", "valor_nuevo", "fecha"]
    list_filter = ["campo", "fecha"]
    search_fields = ["ticket__asunto"]
    readonly_fields = ['ticket', 'usuario', 'campo', 'valor_anterior', 'valor_nuevo', 'fecha']

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    list_display = ["descripcion", "completada", "prioridad", "creado_por", "fecha_creacion"]
    list_filter = ["completada", "prioridad"]


@admin.register(InformeDiario)
class InformeDiarioAdmin(admin.ModelAdmin):
    list_display = ["titulo", "fecha", "creado_por", "fecha_creacion"]
    list_filter = ["fecha"]
    search_fields = ["titulo", "contenido"]
    date_hierarchy = "fecha"
    readonly_fields = ["fecha_creacion", "fecha_actualizacion"]


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ["usuario", "mensaje", "leida", "fecha_creacion"]
    list_filter = ["leida"]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["fecha", "username", "accion", "modelo", "objeto_repr"]
    list_filter = ["accion", "modelo"]
    search_fields = ["username", "objeto_repr", "detalle"]
    readonly_fields = ["fecha", "usuario", "username", "accion", "modelo", "objeto_id", "objeto_repr", "detalle", "direccion_ip"]
    date_hierarchy = "fecha"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

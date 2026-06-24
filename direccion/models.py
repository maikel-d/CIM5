from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from datetime import date
import os


from .permissions import tiene_permiso as _tiene_permiso


class UserProfile(models.Model):
    ROL_CHOICES = [
        ('ADMINISTRADOR', 'Administrador'),
        ('SUPERVISOR', 'Supervisor'),
        ('ANALISTA', 'Analista'),
        ('ADMINISTRATIVO', 'Administrativo'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    rol = models.CharField('Rol', max_length=20, choices=ROL_CHOICES, default='ADMINISTRATIVO')
    telefono = models.CharField('Teléfono', max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuarios'

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_rol_display()}"

    def tiene_permiso(self, permiso):
        """Verifica si este perfil tiene un permiso específico.
        Uso: request.user.profile.tiene_permiso('personal_ver')
        """
        return _tiene_permiso(self.rol, permiso)


def personal_photo_path(instance, filename):
    ext = filename.split('.')[-1]
    return f'personal/fotos/{instance.cedula}_{instance.apellidos}_{instance.nombres}.{ext}'


def personal_document_path(instance, filename):
    return f'personal/documentos/{instance.personal.cedula}/{filename}'


class Personal(models.Model):
    foto = models.ImageField(
        'Foto', upload_to=personal_photo_path, blank=True, null=True,
        help_text='Formatos: .jpg, .jpeg, .png'
    )
    apellidos = models.CharField('Apellidos', max_length=150, db_index=True)
    nombres = models.CharField('Nombres', max_length=150, db_index=True)
    cedula = models.CharField(
        'Cédula', max_length=15, unique=True,
        validators=[RegexValidator(r'^[VEJPGvejpg]-?\d{5,10}$', 'Formato: V-12345678')]
    )
    telefonos = models.TextField('Teléfonos', blank=True, null=True, help_text='Ingrese uno o varios números')
    fecha_nacimiento = models.DateField('Fecha de Nacimiento', blank=True, null=True)
    grado = models.CharField('Grado', max_length=100, blank=True, default='', help_text='Grado profesional / jerárquico')
    direccion = models.TextField('Dirección', blank=True, null=True, help_text='Dirección de domicilio')
    fecha_ingreso = models.DateField('Fecha de Ingreso', blank=True, null=True)
    contacto_emergencia = models.TextField('Contacto de Emergencia', blank=True, null=True, help_text='Nombre, parentesco y teléfono')
    correo = models.CharField('Correo Electrónico', max_length=254, blank=True, null=True, help_text='Correo electrónico institucional o personal')
    fecha_creacion = models.DateTimeField('Fecha de creación', auto_now_add=True, db_index=True)
    fecha_actualizacion = models.DateTimeField('Fecha de actualización', auto_now=True)
    activo = models.BooleanField('Activo', default=True, db_index=True)

    class Meta:
        verbose_name = 'Personal'
        verbose_name_plural = 'Personal de la Dirección'
        ordering = ['apellidos', 'nombres']

    def __str__(self):
        return f"{self.apellidos}, {self.nombres} - {self.cedula}"

    @property
    def edad(self):
        if not self.fecha_nacimiento:
            return None
        today = date.today()
        return today.year - self.fecha_nacimiento.year - (
            (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
        )

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old = Personal.objects.get(pk=self.pk)
                if old.foto and old.foto != self.foto:
                    old.foto.delete(save=False)
            except Personal.DoesNotExist:
                pass
        super().save(*args, **kwargs)


class TipoDocumentoMixin:
    """Mixin que detecta automáticamente el tipo de archivo por extensión."""
    def save(self, *args, **kwargs):
        archivo = getattr(self, 'archivo', None)
        if archivo and hasattr(archivo, 'name') and archivo.name:
            ext = os.path.splitext(archivo.name)[1].lower()
            if ext in ['.pdf']:
                self.tipo = 'PDF'
            elif ext in ['.doc', '.docx']:
                self.tipo = 'WORD'
            elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                self.tipo = 'IMAGEN'
            else:
                self.tipo = 'OTRO'
        else:
            self.tipo = 'OTRO'
        super().save(*args, **kwargs)


class DocumentoPersonal(TipoDocumentoMixin, models.Model):
    TIPO_CHOICES = [
        ('PDF', 'PDF'),
        ('WORD', 'Word'),
        ('IMAGEN', 'Imagen'),
        ('OTRO', 'Otro'),
    ]

    personal = models.ForeignKey(
        Personal, on_delete=models.CASCADE, related_name='documentos',
        verbose_name='Personal'
    )
    archivo = models.FileField(
        'Archivo', upload_to=personal_document_path,
        help_text='Formatos: PDF, Word (.doc, .docx), imágenes'
    )
    tipo = models.CharField('Tipo', max_length=10, choices=TIPO_CHOICES, editable=False, db_index=True)
    descripcion = models.CharField('Descripción', max_length=255, blank=True, null=True)
    fecha_subida = models.DateTimeField('Fecha de subida', auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Documento del Personal'
        verbose_name_plural = 'Documentos del Personal'
        ordering = ['-fecha_subida']

    def __str__(self):
        nombre = os.path.basename(self.archivo.name) if self.archivo.name else '(sin archivo)'
        return f"{self.personal} - {nombre}"




def caso_document_path(instance, filename):
    return f'casos/documentos/{instance.caso.pk}/{filename}'


class DocumentoCaso(TipoDocumentoMixin, models.Model):
    TIPO_CHOICES = [
        ('PDF', 'PDF'),
        ('WORD', 'Word'),
        ('IMAGEN', 'Imagen'),
        ('OTRO', 'Otro'),
    ]

    caso = models.ForeignKey(
        'Caso', on_delete=models.CASCADE, related_name='documentos',
        verbose_name='Caso'
    )
    archivo = models.FileField(
        'Archivo', upload_to=caso_document_path,
        help_text='Formatos: PDF, Word (.doc, .docx), imágenes'
    )
    tipo = models.CharField('Tipo', max_length=10, choices=TIPO_CHOICES, editable=False, db_index=True)
    descripcion = models.CharField('Descripción', max_length=255, blank=True, null=True)
    fecha_subida = models.DateTimeField('Fecha de subida', auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Documento del Caso'
        verbose_name_plural = 'Documentos del Caso'
        ordering = ['-fecha_subida']

    def __str__(self):
        nombre = os.path.basename(self.archivo.name) if self.archivo.name else '(sin archivo)'
        return f"{self.caso} - {nombre}"


class Caso(models.Model):
    """Agrupa varias personas investigadas bajo un mismo caso."""
    nombre = models.CharField('Nombre del caso', max_length=200, db_index=True)
    descripcion = models.TextField('Descripción', blank=True, null=True)
    fecha_apertura = models.DateField('Fecha de apertura', blank=True, null=True)
    fecha_creacion = models.DateTimeField('Fecha de creación', auto_now_add=True, db_index=True)
    fecha_actualizacion = models.DateTimeField('Fecha de actualización', auto_now=True)
    activo = models.BooleanField('Activo', default=True, db_index=True)

    class Meta:
        verbose_name = 'Caso'
        verbose_name_plural = 'Casos'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return self.nombre

    def count_investigados(self):
        return self.investigados.filter(activo=True).count()

    def count_documentos(self):
        return self.documentos.count()


def investigado_photo_path(instance, filename):
    ext = filename.split('.')[-1]
    return f'investigados/fotos/{instance.cedula}_{instance.apellidos}_{instance.nombres}.{ext}'


def investigado_document_path(instance, filename):
    return f'investigados/documentos/{instance.investigado.cedula}/{filename}'


class Investigado(models.Model):
    caso = models.ForeignKey(
        Caso, on_delete=models.CASCADE, related_name='investigados',
        verbose_name='Caso', blank=True, null=True
    )
    foto = models.ImageField(
        'Foto', upload_to=investigado_photo_path, blank=True, null=True,
        help_text='Formatos: .jpg, .jpeg, .png'
    )
    apellidos = models.CharField('Apellidos', max_length=150, db_index=True)
    nombres = models.CharField('Nombres', max_length=150, db_index=True)
    entrada_investigacion = models.TextField(
        'Entrada a investigación', blank=True, null=True,
        help_text='Breve resumen del caso'
    )
    cedula = models.CharField(
        'Cédula', max_length=15, blank=True, null=True,
        validators=[RegexValidator(r'^[VEJPGvejpg]-?\d{5,10}$', 'Formato: V-12345678')]
    )
    rif = models.CharField(
        'RIF', max_length=15, blank=True, null=True,
        validators=[RegexValidator(r'^[VEJPGvejpg]-?\d{5,10}-\d$', 'Formato: V-12345678-0')]
    )
    partida_nacimiento = models.CharField(
        'Partida de nacimiento', max_length=255, blank=True, null=True,
        help_text='Tomo, folio o datos de acta'
    )
    fecha_creacion = models.DateTimeField('Fecha de creación', auto_now_add=True, db_index=True)
    fecha_actualizacion = models.DateTimeField('Fecha de actualización', auto_now=True)
    activo = models.BooleanField('Activo', default=True, db_index=True)

    class Meta:
        verbose_name = 'Persona Investigada'
        verbose_name_plural = 'Personas Investigadas'
        ordering = ['apellidos', 'nombres']

    def __str__(self):
        return f"{self.apellidos}, {self.nombres} - {self.cedula or 'Sin cédula'}"

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old = Investigado.objects.get(pk=self.pk)
                if old.foto and old.foto != self.foto:
                    old.foto.delete(save=False)
            except Investigado.DoesNotExist:
                pass
        super().save(*args, **kwargs)


def direccion_document_path(instance, filename):
    return f'direccion/documentos/{filename}'


class DocumentoDireccion(TipoDocumentoMixin, models.Model):
    TIPO_CHOICES = [
        ('PDF', 'PDF'),
        ('WORD', 'Word'),
        ('IMAGEN', 'Imagen'),
        ('OTRO', 'Otro'),
    ]

    CATEGORIA_CHOICES = [
        ('LEYES', 'Leyes'),
        ('DOCUMENTOS', 'Documentos'),
        ('MEMO', 'Formato de Memos'),
        ('RECURSOS', 'Recursos CIM5'),
        
    ]

    archivo = models.FileField(
        'Archivo', upload_to=direccion_document_path,
        help_text='Formatos: PDF, Word (.doc, .docx), imágenes'
    )
    tipo = models.CharField('Tipo', max_length=10, choices=TIPO_CHOICES, editable=False, db_index=True)
    categoria = models.CharField('Categoría', max_length=20, choices=CATEGORIA_CHOICES, default='DOCUMENTOS', db_index=True)
    descripcion = models.CharField('Descripción', max_length=255, blank=True, null=True)
    fecha_subida = models.DateTimeField('Fecha de subida', auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Documento de la Dirección'
        verbose_name_plural = 'Documentos de la Dirección'
        ordering = ['-fecha_subida']

    def __str__(self):
        nombre = os.path.basename(self.archivo.name) if self.archivo.name else '(sin archivo)'
        return f"{self.descripcion or 'Sin descripción'} - {nombre}"


class CarpetaDireccion(models.Model):
    """Carpeta dinámica para organizar documentos de la dirección."""
    nombre = models.CharField('Nombre', max_length=100)
    categoria = models.CharField('Categoría', max_length=20, blank=True, null=True)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='subcarpetas', verbose_name='Carpeta padre'
    )
    orden = models.IntegerField('Orden', default=0)
    fecha_creacion = models.DateTimeField('Fecha de creación', auto_now_add=True)

    class Meta:
        verbose_name = 'Carpeta de Documento'
        verbose_name_plural = 'Carpetas de Documentos'
        ordering = ['orden', 'nombre']

    def __str__(self):
        return self.nombre


class AuditLog(models.Model):
    ACCIONES = [
        ('CREAR', 'Creaci\u00f3n'),
        ('ACTUALIZAR', 'Actualizaci\u00f3n'),
        ('ELIMINAR', 'Eliminaci\u00f3n'),
        ('RESTAURAR', 'Restauraci\u00f3n'),
        ('TOGGLE', 'Activar/Desactivar'),
        ('LOGIN', 'Inicio de sesi\u00f3n'),
        ('EXPORTAR', 'Exportaci\u00f3n'),
        ('BACKUP', 'Respaldo'),
    ]

    usuario = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Usuario', related_name='audit_logs'
    )
    username = models.CharField('Nombre de usuario', max_length=150, blank=True)
    accion = models.CharField('Acci\u00f3n', max_length=20, choices=ACCIONES, db_index=True)
    modelo = models.CharField('Modelo', max_length=100, blank=True, db_index=True)
    objeto_id = models.PositiveIntegerField('ID del objeto', null=True, blank=True)
    objeto_repr = models.CharField('Representaci\u00f3n', max_length=255, blank=True)
    detalle = models.TextField('Detalle', blank=True)
    direccion_ip = models.GenericIPAddressField('Direcci\u00f3n IP', blank=True, null=True)
    fecha = models.DateTimeField('Fecha', auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Registro de Auditor\u00eda'
        verbose_name_plural = 'Registros de Auditor\u00eda'
        ordering = ['-fecha']

    def __str__(self):
        return f"[{self.fecha:%d/%m/%Y %H:%M}] {self.username} - {self.get_accion_display()} - {self.modelo}"


class Tarea(models.Model):
    """Tarea pendiente con categorización y seguimiento."""
    PRIORIDAD_CHOICES = [
        ('BAJO', 'Bajo'),
        ('MEDIO', 'Medio'),
        ('ALTO', 'Alto'),
    ]
    CATEGORIA_CHOICES = [
        ('GENERAL', 'General'),
        ('INVESTIGACION', 'Investigación'),
        ('DOCUMENTACION', 'Documentación'),
        ('SOPORTE', 'Soporte Técnico'),
        ('ADMINISTRACION', 'Administración'),
        ('REUNION', 'Reuniones'),
        ('OTRO', 'Otro'),
    ]

    descripcion = models.TextField('Descripción')
    completada = models.BooleanField('Completada', default=False, db_index=True)
    prioridad = models.CharField('Prioridad', max_length=10, choices=PRIORIDAD_CHOICES, default='MEDIO')
    categoria = models.CharField('Categoría', max_length=20, choices=CATEGORIA_CHOICES, default='GENERAL', db_index=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Creado por')
    fecha_creacion = models.DateTimeField('Fecha de creación', auto_now_add=True, db_index=True)
    fecha_actualizacion = models.DateTimeField('Fecha de actualización', auto_now=True)

    class Meta:
        verbose_name = 'Tarea'
        verbose_name_plural = 'Tareas Pendientes'
        ordering = ['completada', '-fecha_creacion']

    def __str__(self):
        return self.descripcion[:50]


class TicketSoporte(models.Model):
    """Ticket de soporte interno - ayuda tipo helpdesk."""
    ESTADO_CHOICES = [
        ('ABIERTO', 'Abierto'),
        ('EN_PROCESO', 'En proceso'),
        ('RESUELTO', 'Resuelto'),
        ('CERRADO', 'Cerrado'),
    ]
    PRIORIDAD_CHOICES = [
        ('BAJO', 'Bajo'),
        ('MEDIO', 'Medio'),
        ('ALTO', 'Alto'),
    ]

    asunto = models.CharField('Asunto', max_length=200)
    descripcion = models.TextField('Descripción')
    estado = models.CharField('Estado', max_length=20, choices=ESTADO_CHOICES, default='ABIERTO', db_index=True)
    prioridad = models.CharField('Prioridad', max_length=10, choices=PRIORIDAD_CHOICES, default='MEDIO', db_index=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_creados', verbose_name='Creado por')
    asignado_a = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_asignados', verbose_name='Asignado a')
    fecha_creacion = models.DateTimeField('Fecha de creación', auto_now_add=True, db_index=True)
    fecha_actualizacion = models.DateTimeField('Fecha de actualización', auto_now=True)

    class Meta:
        verbose_name = 'Ticket de Soporte'
        verbose_name_plural = 'Tickets de Soporte'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"#{self.pk} - {self.asunto}"

    def registrar_cambio(self, usuario, campo, valor_anterior, valor_nuevo):
        """Registra un cambio en el historial del ticket."""
        if valor_anterior != valor_nuevo:
            TicketHistorial.objects.create(
                ticket=self,
                usuario=usuario,
                campo=campo,
                valor_anterior=self._formatear_valor(campo, valor_anterior),
                valor_nuevo=self._formatear_valor(campo, valor_nuevo),
            )

    def _formatear_valor(self, campo, valor):
        """Convierte valores de opciones a su etiqueta legible."""
        if valor is None:
            return '---'
        if campo == 'estado':
            for v, label in self.ESTADO_CHOICES:
                if v == valor:
                    return label
        elif campo == 'prioridad':
            for v, label in self.PRIORIDAD_CHOICES:
                if v == valor:
                    return label
        elif campo == 'asignado_a':
            if isinstance(valor, User):
                return valor.get_full_name() or valor.username
            if isinstance(valor, str):
                return valor
        return str(valor)


class TicketHistorial(models.Model):
    """Registro de cambios en un ticket de soporte (historial de estado/prioridad/asignacion)."""
    CAMPO_CHOICES = [
        ('estado', 'Estado'),
        ('prioridad', 'Prioridad'),
        ('asignado_a', 'Asignado a'),
    ]

    ticket = models.ForeignKey(
        TicketSoporte, on_delete=models.CASCADE, related_name='historial',
        verbose_name='Ticket'
    )
    usuario = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Usuario', related_name='ticket_cambios'
    )
    campo = models.CharField('Campo', max_length=20, choices=CAMPO_CHOICES)
    valor_anterior = models.CharField('Valor anterior', max_length=100, blank=True, null=True)
    valor_nuevo = models.CharField('Valor nuevo', max_length=100, blank=True, null=True)
    fecha = models.DateTimeField('Fecha', auto_now_add=True)

    class Meta:
        verbose_name = 'Cambio en Ticket'
        verbose_name_plural = 'Historial de Tickets'
        ordering = ['-fecha']

    def __str__(self):
        return f"#{self.ticket_id} - {self.get_campo_display()}: {self.valor_anterior} -> {self.valor_nuevo}"


class Notificacion(models.Model):
    """Notificación persistente para usuarios."""
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificaciones', verbose_name='Usuario')
    mensaje = models.CharField('Mensaje', max_length=255)
    link = models.CharField('Enlace', max_length=255, blank=True, null=True)
    leida = models.BooleanField('Leída', default=False, db_index=True)
    fecha_creacion = models.DateTimeField('Fecha de creación', auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return self.mensaje[:50]


def notificar_administradores(mensaje, link=None):
    """Crea una notificación para todos los usuarios con rol ADMINISTRADOR."""
    admins = User.objects.filter(
        profile__rol='ADMINISTRADOR',
        is_active=True
    )
    notis = []
    for admin in admins:
        notis.append(Notificacion(usuario=admin, mensaje=mensaje, link=link))
    if notis:
        Notificacion.objects.bulk_create(notis)


class InformeDiario(models.Model):
    """Informe diario con segmentación por semana, mes y año."""
    titulo = models.CharField('Título', max_length=200)
    contenido = models.TextField('Contenido del informe')
    archivo = models.FileField(
        'Archivo adjunto', upload_to='informes/archivos/',
        blank=True, null=True,
        help_text='Opcional: PDF, Word, imagen...'
    )
    fecha = models.DateField('Fecha del informe', db_index=True)
    creado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Creado por'
    )
    fecha_creacion = models.DateTimeField('Fecha de creación', auto_now_add=True, db_index=True)
    fecha_actualizacion = models.DateTimeField('Fecha de actualización', auto_now=True)

    class Meta:
        verbose_name = 'Informe Diario'
        verbose_name_plural = 'Informes Diarios'
        ordering = ['-fecha', '-fecha_creacion']

    def __str__(self):
        return f"{self.fecha} - {self.titulo}"

    def semana_del_anio(self):
        """Retorna el número de semana ISO del año."""
        return self.fecha.isocalendar()[1]

    def mes_del_anio(self):
        """Retorna el número de mes."""
        return self.fecha.month


class DocumentoInvestigado(TipoDocumentoMixin, models.Model):
    TIPO_CHOICES = [
        ('PDF', 'PDF'),
        ('WORD', 'Word'),
        ('IMAGEN', 'Imagen'),
        ('OTRO', 'Otro'),
    ]

    investigado = models.ForeignKey(
        Investigado, on_delete=models.CASCADE, related_name='documentos',
        verbose_name='Persona Investigada'
    )
    archivo = models.FileField(
        'Archivo', upload_to=investigado_document_path,
        help_text='Formatos: PDF, Word (.doc, .docx), imágenes'
    )
    tipo = models.CharField('Tipo', max_length=10, choices=TIPO_CHOICES, editable=False, db_index=True)
    descripcion = models.CharField('Descripción', max_length=255, blank=True, null=True)
    fecha_subida = models.DateTimeField('Fecha de subida', auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Documento de Evidencia'
        verbose_name_plural = 'Documentos de Evidencias'
        ordering = ['-fecha_subida']

    def __str__(self):
        nombre = os.path.basename(self.archivo.name) if self.archivo.name else '(sin archivo)'
        return f"{self.investigado} - {nombre}"


# ============================================================
# BIENES (Assets / Inventory)
# ============================================================

def bien_photo_path(instance, filename):
    ext = filename.split('.')[-1]
    return f'bienes/fotos/{instance.pk}_{instance.nombre}.{ext}'


def bien_document_path(instance, filename):
    return f'bienes/documentos/{instance.bien.pk}/{filename}'


class Bien(models.Model):
    CATEGORIA_CHOICES = [
        ('VEHICULO', 'Vehículo'),
        ('INMUEBLE', 'Inmueble'),
        ('EQUIPO', 'Equipo'),
        ('MUEBLE', 'Mueble'),
        ('ARMAMENTO', 'Armamento'),
        ('COMUNICACIONES', 'Comunicaciones'),
        ('INFORMATICA', 'Informática'),
        ('OTRO', 'Otro'),
    ]

    ESTADO_CHOICES = [
        ('BUENO', 'Bueno'),
        ('REGULAR', 'Regular'),
        ('MALO', 'Malo'),
        ('OBSOLETO', 'Obsoleto'),
    ]

    caso = models.ForeignKey(
        'Caso', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Caso', related_name='bienes'
    )
    nombre = models.CharField('Nombre del bien', max_length=200)
    descripcion = models.TextField('Descripción', blank=True, null=True)
    foto = models.ImageField(
        'Foto', upload_to=bien_photo_path, blank=True, null=True,
        help_text='Formatos: .jpg, .jpeg, .png'
    )
    categoria = models.CharField('Categoría', max_length=20, choices=CATEGORIA_CHOICES, default='OTRO', db_index=True)
    codigo_inventario = models.CharField('Código de inventario', max_length=50, unique=True, blank=True, null=True)
    serial = models.CharField('Serial', max_length=100, blank=True, null=True)
    marca = models.CharField('Marca', max_length=100, blank=True, null=True)
    modelo_bien = models.CharField('Modelo', max_length=100, blank=True, null=True)
    ubicacion = models.CharField('Ubicación', max_length=200, blank=True, null=True)
    estado = models.CharField('Estado', max_length=20, choices=ESTADO_CHOICES, default='BUENO', db_index=True)
    fecha_adquisicion = models.DateField('Fecha de adquisición', blank=True, null=True)
    valor = models.DecimalField('Valor (Bs.)', max_digits=14, decimal_places=2, blank=True, null=True)
    carpeta = models.ForeignKey(
        'CarpetaBien', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Carpeta', related_name='bienes'
    )
    activo = models.BooleanField('Activo', default=True, db_index=True)
    fecha_creacion = models.DateTimeField('Fecha de creación', auto_now_add=True, db_index=True)
    fecha_actualizacion = models.DateTimeField('Fecha de actualización', auto_now=True)

    class Meta:
        verbose_name = 'Bien'
        verbose_name_plural = 'Bienes'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.nombre} - {self.get_categoria_display()}"

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old = Bien.objects.get(pk=self.pk)
                if old.foto and old.foto != self.foto:
                    old.foto.delete(save=False)
            except Bien.DoesNotExist:
                pass
        super().save(*args, **kwargs)


class DocumentoBien(TipoDocumentoMixin, models.Model):
    TIPO_CHOICES = [
        ('PDF', 'PDF'),
        ('WORD', 'Word'),
        ('IMAGEN', 'Imagen'),
        ('OTRO', 'Otro'),
    ]

    bien = models.ForeignKey(
        Bien, on_delete=models.CASCADE, related_name='documentos',
        verbose_name='Bien'
    )
    archivo = models.FileField(
        'Archivo', upload_to=bien_document_path,
        help_text='Formatos: PDF, Word (.doc, .docx), imágenes'
    )
    tipo = models.CharField('Tipo', max_length=10, choices=TIPO_CHOICES, editable=False, db_index=True)
    descripcion = models.CharField('Descripción', max_length=255, blank=True, null=True)
    fecha_subida = models.DateTimeField('Fecha de subida', auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Documento del Bien'
        verbose_name_plural = 'Documentos de Bienes'
        ordering = ['-fecha_subida']

    def __str__(self):
        nombre = os.path.basename(self.archivo.name) if self.archivo.name else '(sin archivo)'
        return f"{self.bien} - {nombre}"


def carpeta_bien_document_path(instance, filename):
    return f'bienes/carpetas/{instance.carpeta.pk}/{filename}'


class CarpetaBien(models.Model):
    """Carpeta dinámica para organizar bienes."""
    nombre = models.CharField('Nombre', max_length=100)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='subcarpetas', verbose_name='Carpeta padre'
    )
    orden = models.IntegerField('Orden', default=0)
    fecha_creacion = models.DateTimeField('Fecha de creación', auto_now_add=True)

    class Meta:
        verbose_name = 'Carpeta de Bien'
        verbose_name_plural = 'Carpetas de Bienes'
        ordering = ['orden', 'nombre']

    def __str__(self):
        return self.nombre


class DocumentoCarpetaBien(TipoDocumentoMixin, models.Model):
    """Documento dentro de una carpeta de bienes."""
    TIPO_CHOICES = [
        ('PDF', 'PDF'),
        ('WORD', 'Word'),
        ('IMAGEN', 'Imagen'),
        ('OTRO', 'Otro'),
    ]

    carpeta = models.ForeignKey(
        CarpetaBien, on_delete=models.CASCADE, related_name='documentos',
        verbose_name='Carpeta'
    )
    archivo = models.FileField(
        'Archivo', upload_to=carpeta_bien_document_path,
        help_text='Formatos: PDF, Word (.doc, .docx), imágenes'
    )
    tipo = models.CharField('Tipo', max_length=10, choices=TIPO_CHOICES, editable=False, db_index=True)
    descripcion = models.CharField('Descripción', max_length=255, blank=True, null=True)
    fecha_subida = models.DateTimeField('Fecha de subida', auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Documento de Carpeta'
        verbose_name_plural = 'Documentos de Carpetas'
        ordering = ['-fecha_subida']

    def __str__(self):
        nombre = os.path.basename(self.archivo.name) if self.archivo.name else '(sin archivo)'
        return f"{self.carpeta} - {nombre}"

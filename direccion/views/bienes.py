# ============================================================
# Bienes CRUD
# ============================================================

from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

from ..models import Bien, CarpetaBien, DocumentoBien
from ..forms import BienForm, DocumentoBienForm
from .mixins import PermissionRequiredMixin
from ..decorators import permiso_required
from ..audit import auditar
from .. import permissions as perms


class BienListView(PermissionRequiredMixin, ListView):
    model = Bien
    template_name = "direccion/bien_list.html"
    context_object_name = "bienes"
    login_url = reverse_lazy("login")
    permisos_requeridos = [perms.BIENES_VER]

    def get_queryset(self):
        """Retorna todos los bienes activos (usado para el listado completo)."""
        queryset = Bien.objects.filter(activo=True).select_related('caso')
        search = self.request.GET.get("search", "")
        caso_id = self.request.GET.get("caso", "")
        categoria = self.request.GET.get("categoria", "")
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) |
                Q(codigo_inventario__icontains=search) |
                Q(serial__icontains=search) |
                Q(marca__icontains=search) |
                Q(ubicacion__icontains=search)
            )
        if caso_id:
            queryset = queryset.filter(caso_id=caso_id)
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        estado = self.request.GET.get("estado", "")
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset.order_by("-fecha_creacion")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from ..models import Caso
        context["search"] = self.request.GET.get("search", "")
        context["categoria_filtro"] = self.request.GET.get("categoria", "")
        context["estado_filtro"] = self.request.GET.get("estado", "")
        context["categorias"] = Bien.CATEGORIA_CHOICES
        context["estados"] = Bien.ESTADO_CHOICES
        # Agrupar bienes por caso para la vista de carpetas
        todos_bienes = self.get_queryset()
        bienes_sin_caso = todos_bienes.filter(caso__isnull=True)
        casos_con_bienes = []
        for c in Caso.objects.filter(activo=True, bienes__in=todos_bienes).distinct().order_by('nombre'):
            casos_con_bienes.append({
                'caso': c,
                'bienes': todos_bienes.filter(caso=c),
            })
        context['bienes_sin_caso'] = bienes_sin_caso
        # Carpetas de Bienes con soporte para subcarpetas
        from ..models import CarpetaBien
        carpeta_pk = self.request.GET.get('carpeta', '')
        carpeta_actual = None
        breadcrumbs = []
        if carpeta_pk and carpeta_pk.isdigit():
            try:
                carpeta_actual = CarpetaBien.objects.get(pk=carpeta_pk)
                temp = carpeta_actual
                while temp:
                    breadcrumbs.insert(0, temp)
                    temp = temp.parent
            except CarpetaBien.DoesNotExist:
                pass
        if carpeta_actual:
            carpetas_bien = CarpetaBien.objects.filter(parent=carpeta_actual).order_by('nombre')
        else:
            carpetas_bien = CarpetaBien.objects.filter(parent__isnull=True).order_by('nombre')
        context['carpetas_bien'] = carpetas_bien
        context['carpeta_actual'] = carpeta_actual
        context['breadcrumbs'] = breadcrumbs
        context['casos_con_bienes'] = casos_con_bienes
        return context


class BienCreateView(PermissionRequiredMixin, CreateView):
    model = Bien
    form_class = BienForm
    template_name = "direccion/bien_form.html"
    login_url = reverse_lazy("login")
    permisos_requeridos = [perms.BIENES_CREAR]

    def get_success_url(self):
        return reverse_lazy("bien_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "Bien registrado exitosamente.")
        resp = super().form_valid(form)
        auditar(self.request, "CREAR", "Bien", self.object.pk, str(self.object), f"Nombre: {self.object.nombre}")
        return resp


class BienDetailView(PermissionRequiredMixin, DetailView):
    model = Bien
    template_name = "direccion/bien_detail.html"
    context_object_name = "bien"
    login_url = reverse_lazy("login")
    permisos_requeridos = [perms.BIENES_VER]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["documentos"] = DocumentoBien.objects.filter(bien=self.object)
        return context


class BienUpdateView(PermissionRequiredMixin, UpdateView):
    model = Bien
    form_class = BienForm
    template_name = "direccion/bien_form.html"
    login_url = reverse_lazy("login")
    permisos_requeridos = [perms.BIENES_EDITAR]

    def get_success_url(self):
        return reverse_lazy("bien_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "Bien actualizado exitosamente.")
        resp = super().form_valid(form)
        auditar(self.request, "ACTUALIZAR", "Bien", self.object.pk, str(self.object), f"Nombre: {self.object.nombre}")
        return resp


class BienDeleteView(PermissionRequiredMixin, DeleteView):
    model = Bien
    template_name = "direccion/bien_confirm_delete.html"
    success_url = reverse_lazy("bien_list")
    login_url = reverse_lazy("login")
    permisos_requeridos = [perms.BIENES_ELIMINAR]

    def form_valid(self, form):
        obj = self.object
        repr_ = str(obj)
        pk_val = obj.pk
        nombre = obj.nombre
        for doc in DocumentoBien.objects.filter(bien=obj):
            if doc.archivo:
                doc.archivo.delete(False)
        if obj.foto:
            obj.foto.delete(False)
        obj.delete()
        messages.success(self.request, f"Bien eliminado permanentemente: {repr_}")
        auditar(self.request, "ELIMINAR", "Bien", pk_val, repr_, f"Nombre: {nombre}")
        return redirect(self.success_url)


@permiso_required(perms.BIENES_DOCUMENTOS_AGREGAR)
def agregar_documento_bien(request, pk):
    bien = get_object_or_404(Bien, pk=pk)
    if request.method == "POST":
        form = DocumentoBienForm(request.POST, request.FILES)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.bien = bien
            documento.save()
            messages.success(request, "Documento agregado exitosamente.")
            auditar(request, "CREAR", "DocumentoBien", documento.pk, str(documento), f"Bien: {bien}")
        else:
            messages.error(request, "Error al subir el documento. Verifique el formato.")
    return redirect("bien_detail", pk=pk)


@permiso_required(perms.BIENES_DOCUMENTOS_ELIMINAR)
def eliminar_documento_bien(request, pk, doc_pk):
    documento = get_object_or_404(DocumentoBien, pk=doc_pk, bien_id=pk)
    doc_repr = str(documento)
    pk_val = documento.pk
    bien_repr = str(documento.bien)
    if documento.archivo:
        documento.archivo.delete()
    documento.delete()
    messages.success(request, "Documento eliminado exitosamente.")
    auditar(request, "ELIMINAR", "DocumentoBien", pk_val, doc_repr, f"Bien: {bien_repr}")
    return redirect("bien_detail", pk=pk)



# ============================================================
# Carpetas de Bienes
# ============================================================


@permiso_required(perms.BIENES_CARPETAS_CREAR)
def carpeta_bien_crear(request):
    """Crear una carpeta de bienes."""
    from ..models import CarpetaBien
    from ..audit import auditar
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        parent_id = request.POST.get("parent_id")
        if not nombre:
            messages.error(request, "El nombre es obligatorio.")
        else:
            parent = None
            if parent_id:
                parent = CarpetaBien.objects.filter(pk=parent_id).first()
            carpeta = CarpetaBien(nombre=nombre, parent=parent)
            carpeta.save()
            messages.success(request, f'Carpeta "{nombre}" creada.')
            auditar(request, "CREAR", "CarpetaBien", carpeta.pk, str(carpeta), "Carpeta de Bien: " + nombre)
    return redirect("bien_list")


@permiso_required(perms.BIENES_CARPETAS_RENOMBRAR)
def carpeta_bien_renombrar(request, pk):
    """Renombrar una carpeta de bienes."""
    from ..models import CarpetaBien
    from ..audit import auditar
    carpeta = get_object_or_404(CarpetaBien, pk=pk)
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        if nombre:
            viejo = carpeta.nombre
            carpeta.nombre = nombre
            carpeta.save()
            messages.success(request, f'Carpeta renombrada a "{nombre}".')
            auditar(request, "EDITAR", "CarpetaBien", carpeta.pk, f"{viejo} -> {nombre}", "Carpeta de Bien")
    return redirect("bien_list")


class CarpetaBienDetailView(PermissionRequiredMixin, DetailView):
    """
    Vista de detalle de una carpeta de bienes.
    Muestra la informacion de la carpeta y los bienes que contiene,
    similar a como caso_detail muestra los investigados.
    """
    model = CarpetaBien
    template_name = 'direccion/bien_carpeta_detail.html'
    context_object_name = 'carpeta'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Bienes dentro de esta carpeta
        context['bienes'] = Bien.objects.filter(
            carpeta=self.object, activo=True
        ).order_by('nombre')
        # Subcarpetas
        context['subcarpetas'] = CarpetaBien.objects.filter(
            parent=self.object
        ).order_by('orden', 'nombre')
        # Breadcrumbs
        breadcrumbs = []
        p = self.object.parent
        while p:
            breadcrumbs.insert(0, p)
            p = p.parent
        context['breadcrumbs'] = breadcrumbs
        # Documentos de bienes en esta carpeta
        context['documentos'] = DocumentoBien.objects.filter(
            bien__carpeta=self.object
        ).order_by('-fecha_subida')[:20]
        return context



@permiso_required(perms.BIENES_CARPETAS_ELIMINAR)
def carpeta_bien_eliminar(request, pk):
    """Eliminar una carpeta de bienes."""
    from ..models import CarpetaBien
    from ..audit import auditar
    carpeta = get_object_or_404(CarpetaBien, pk=pk)
    nombre = str(carpeta)
    pk_val = carpeta.pk
    carpeta.delete()
    messages.success(request, f'Carpeta "{nombre}" eliminada.')
    auditar(request, "ELIMINAR", "CarpetaBien", pk_val, nombre, "Carpeta de Bien: " + nombre)
    return redirect("bien_list")




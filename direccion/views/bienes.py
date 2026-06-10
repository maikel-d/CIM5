# ============================================================
# Bienes CRUD
# ============================================================

from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

from ..models import Bien, DocumentoBien
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
    paginate_by = 25
    permisos_requeridos = [perms.BIENES_VER]

    def get_queryset(self):
        queryset = Bien.objects.filter(activo=True)
        search = self.request.GET.get("search", "")
        categoria = self.request.GET.get("categoria", "")
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) |
                Q(codigo_inventario__icontains=search) |
                Q(serial__icontains=search) |
                Q(marca__icontains=search) |
                Q(ubicacion__icontains=search)
            )
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        return queryset.order_by("-fecha_creacion")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search"] = self.request.GET.get("search", "")
        context["categoria_filtro"] = self.request.GET.get("categoria", "")
        context["categorias"] = Bien.CATEGORIA_CHOICES
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



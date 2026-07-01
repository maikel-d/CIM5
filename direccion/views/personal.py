# ============================================================
# Personal CRUD
# ============================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

from ..models import Personal, DocumentoPersonal
from ..forms import PersonalForm, DocumentoPersonalForm
from .mixins import PermissionRequiredMixin
from ..decorators import permiso_required
from ..audit import auditar
from .. import permissions as perms


class PersonalListView(LoginRequiredMixin, ListView):
    model = Personal
    template_name = "direccion/personal_list.html"
    context_object_name = "personal_list"
    login_url = reverse_lazy("login")
    paginate_by = 25

    def get_queryset(self):
        queryset = Personal.objects.filter(activo=True)
        search = self.request.GET.get("search", "")
        if search:
            queryset = queryset.filter(
                Q(apellidos__icontains=search) |
                Q(nombres__icontains=search) |
                Q(cedula__icontains=search)
            )
        return queryset.order_by("apellidos", "nombres")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search"] = self.request.GET.get("search", "")
        return context


class PersonalCreateView(PermissionRequiredMixin, CreateView):
    model = Personal
    form_class = PersonalForm
    template_name = "direccion/personal_form.html"
    login_url = reverse_lazy("login")
    permisos_requeridos = [perms.PERSONAL_CREAR]

    def get_success_url(self):
        return reverse_lazy("personal_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "Personal registrado exitosamente.")
        resp = super().form_valid(form)
        auditar(self.request, "CREAR", "Personal", self.object.pk, str(self.object), f"Cédula: {self.object.cedula}")
        return resp


class PersonalDetailView(LoginRequiredMixin, DetailView):
    model = Personal
    template_name = "direccion/personal_detail.html"
    context_object_name = "personal"
    login_url = reverse_lazy("login")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["documentos"] = DocumentoPersonal.objects.filter(personal=self.object)
        return context


class PersonalUpdateView(PermissionRequiredMixin, UpdateView):
    model = Personal
    form_class = PersonalForm
    template_name = "direccion/personal_form.html"
    login_url = reverse_lazy("login")
    permisos_requeridos = [perms.PERSONAL_EDITAR]

    def get_success_url(self):
        return reverse_lazy("personal_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "Personal actualizado exitosamente.")
        resp = super().form_valid(form)
        auditar(self.request, "ACTUALIZAR", "Personal", self.object.pk, str(self.object), f"Cédula: {self.object.cedula}")
        return resp


class PersonalDeleteView(PermissionRequiredMixin, DeleteView):
    model = Personal
    template_name = "direccion/personal_confirm_delete.html"
    success_url = reverse_lazy("personal_list")
    login_url = reverse_lazy("login")
    permisos_requeridos = [perms.PERSONAL_ELIMINAR]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["documentos_count"] = DocumentoPersonal.objects.filter(personal=self.object).count()
        return context

    def form_valid(self, form):
        obj = self.object
        repr_ = str(obj)
        pk_val = obj.pk
        cedula = obj.cedula
        for doc in DocumentoPersonal.objects.filter(personal=obj):
            if doc.archivo:
                doc.archivo.delete(False)
        if obj.foto:
            obj.foto.delete(False)
        obj.delete()
        messages.success(self.request, f"Personal eliminado permanentemente: {repr_}")
        auditar(self.request, "ELIMINAR", "Personal", pk_val, repr_, f"Cédula: {cedula}")
        return redirect(self.success_url)


@permiso_required(perms.PERSONAL_DOCUMENTOS_AGREGAR)
def agregar_documento_personal(request, pk):
    personal = get_object_or_404(Personal, pk=pk)
    if request.method == "POST":
        form = DocumentoPersonalForm(request.POST, request.FILES)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.personal = personal
            documento.save()
            messages.success(request, "Documento agregado exitosamente.")
            auditar(request, "CREAR", "DocumentoPersonal", documento.pk, str(documento), f"Personal: {personal}")
        else:
            messages.error(request, "Error al subir el documento. Verifique el formato.")
    return redirect("personal_detail", pk=pk)


@permiso_required(perms.PERSONAL_DOCUMENTOS_ELIMINAR)
def eliminar_documento_personal(request, pk, doc_pk):
    documento = get_object_or_404(DocumentoPersonal, pk=doc_pk, personal_id=pk)
    doc_repr = str(documento)
    pk_val = documento.pk
    personal_repr = str(documento.personal)
    if documento.archivo:
        documento.archivo.delete()
    documento.delete()
    messages.success(request, "Documento eliminado exitosamente.")
    auditar(request, "ELIMINAR", "DocumentoPersonal", pk_val, doc_repr, f"Personal: {personal_repr}")
    return redirect("personal_detail", pk=pk)



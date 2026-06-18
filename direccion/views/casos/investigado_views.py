# ============================================================
# INVESTIGADOS CRUD
# ============================================================

from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Count
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

from ...models import Investigado, DocumentoInvestigado, Caso
from ...forms import InvestigadoForm, DocumentoInvestigadoForm
from ..mixins import PermissionRequiredMixin
from ...decorators import permiso_required
from ...audit import auditar
from ... import permissions as perms


class InvestigadoListView(PermissionRequiredMixin, ListView):
    model = Caso
    template_name = "direccion/investigado_list.html"
    context_object_name = "casos"
    login_url = reverse_lazy("login")
    paginate_by = 25
    permisos_requeridos = [perms.INVESTIGADOS_VER]

    def get_queryset(self):
        queryset = Caso.objects.filter(activo=True).annotate(
            count_investigados=Count("investigados", filter=Q(investigados__activo=True)),
            count_documentos=Count("documentos")
        )
        search = self.request.GET.get("search", "")
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) |
                Q(descripcion__icontains=search)
            )
        return queryset.order_by("-fecha_creacion")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search"] = self.request.GET.get("search", "")
        return context


class InvestigadoCreateView(PermissionRequiredMixin, CreateView):
    model = Investigado
    form_class = InvestigadoForm
    template_name = "direccion/investigado_form.html"
    login_url = reverse_lazy("login")
    permisos_requeridos = [perms.INVESTIGADOS_CREAR]

    def get_initial(self):
        initial = super().get_initial()
        caso_id = self.request.GET.get("caso")
        if caso_id:
            try:
                initial["caso"] = int(caso_id)
            except (ValueError, TypeError):
                pass
        return initial

    def get_success_url(self):
        return reverse_lazy("investigado_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "Investigado registrado exitosamente.")
        resp = super().form_valid(form)
        auditar(self.request, "CREAR", "Investigado", self.object.pk, str(self.object), f"Cedula: {self.object.cedula or 'N/A'}")
        return resp


class InvestigadoDetailView(PermissionRequiredMixin, DetailView):
    model = Investigado
    template_name = "direccion/investigado_detail.html"
    context_object_name = "investigado"
    login_url = reverse_lazy("login")
    permisos_requeridos = [perms.INVESTIGADOS_VER]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["documentos"] = DocumentoInvestigado.objects.filter(investigado=self.object)
        return context


class InvestigadoUpdateView(PermissionRequiredMixin, UpdateView):
    model = Investigado
    form_class = InvestigadoForm
    template_name = "direccion/investigado_form.html"
    login_url = reverse_lazy("login")
    permisos_requeridos = [perms.INVESTIGADOS_EDITAR]

    def get_success_url(self):
        return reverse_lazy("investigado_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "Investigado actualizado exitosamente.")
        resp = super().form_valid(form)
        auditar(self.request, "ACTUALIZAR", "Investigado", self.object.pk, str(self.object), f"Cedula: {self.object.cedula or 'N/A'}")
        return resp


class InvestigadoDeleteView(PermissionRequiredMixin, DeleteView):
    model = Investigado
    template_name = "direccion/investigado_confirm_delete.html"
    success_url = reverse_lazy("investigado_list")
    login_url = reverse_lazy("login")
    permisos_requeridos = [perms.INVESTIGADOS_ELIMINAR]

    def form_valid(self, form):
        obj = self.object
        repr_ = str(obj)
        pk_val = obj.pk
        cedula = obj.cedula or "N/A"
        for doc in DocumentoInvestigado.objects.filter(investigado=obj):
            if doc.archivo:
                doc.archivo.delete(False)
        if obj.foto:
            obj.foto.delete(False)
        obj.delete()
        messages.success(self.request, f"Caso eliminado permanentemente: {repr_}")
        auditar(self.request, "ELIMINAR", "Investigado", pk_val, repr_, f"Cedula: {cedula}")
        return redirect(self.success_url)


@permiso_required(perms.INVESTIGADOS_DOCUMENTOS_AGREGAR)
def agregar_documento_investigado(request, pk):
    investigado = get_object_or_404(Investigado, pk=pk)
    if request.method == "POST":
        form = DocumentoInvestigadoForm(request.POST, request.FILES)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.investigado = investigado
            documento.save()
            messages.success(request, "Documento agregado exitosamente.")
            auditar(request, "CREAR", "DocumentoInvestigado", documento.pk, str(documento), f"Investigado: {investigado}")
        else:
            messages.error(request, "Error al subir el documento. Verifique el formato.")
    return redirect("investigado_detail", pk=pk)


@permiso_required(perms.INVESTIGADOS_DOCUMENTOS_ELIMINAR)
def eliminar_documento_investigado(request, pk, doc_pk):
    documento = get_object_or_404(DocumentoInvestigado, pk=doc_pk, investigado_id=pk)
    doc_repr = str(documento)
    pk_val = documento.pk
    inv_repr = str(documento.investigado)
    if documento.archivo:
        documento.archivo.delete()
    documento.delete()
    messages.success(request, "Documento eliminado exitosamente.")
    auditar(request, "ELIMINAR", "DocumentoInvestigado", pk_val, doc_repr, f"Investigado: {inv_repr}")
    return redirect("investigado_detail", pk=pk)

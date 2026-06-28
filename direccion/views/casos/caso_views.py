# ======================================================================================
# Casos CRUD
# ======================================================================================

from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Count
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

from ...models import Caso, Investigado, DocumentoInvestigado, DocumentoCaso, Bien, DocumentoBien
from ...forms import CasoForm, DocumentoCasoForm
from ..mixins import PermissionRequiredMixin
from ...decorators import permiso_required
from ...audit import auditar
from ... import permissions as perms


class CasoListView(PermissionRequiredMixin, ListView):
    model = Caso
    template_name = "direccion/caso_list.html"
    context_object_name = "casos"
    login_url = reverse_lazy("login")
    permisos_requeridos = [perms.CASOS_VER]

    def get_queryset(self):
        return Caso.objects.filter(activo=True).annotate(
            count_investigados=Count("investigados", filter=Q(investigados__activo=True)),
            count_documentos=Count("documentos")
        ).order_by("-fecha_creacion")


class CasoCreateView(PermissionRequiredMixin, CreateView):
    model = Caso
    form_class = CasoForm
    template_name = "direccion/caso_form.html"
    login_url = reverse_lazy("login")
    success_url = reverse_lazy("caso_list")
    permisos_requeridos = [perms.CASOS_CREAR]

    def form_valid(self, form):
        messages.success(self.request, "Caso creado exitosamente.")
        resp = super().form_valid(form)
        auditar(self.request, "CREAR", "Caso", self.object.pk, str(self.object), f"Caso: {self.object.nombre}")
        return resp


class CasoDetailView(PermissionRequiredMixin, DetailView):
    model = Caso
    template_name = "direccion/caso_detail.html"
    context_object_name = "caso"
    login_url = reverse_lazy("login")
    permisos_requeridos = [perms.CASOS_VER]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["investigados"] = Investigado.objects.filter(caso=self.object, activo=True).select_related('caso').annotate(doc_count=Count('documentos')).order_by("apellidos", "nombres")
        context["documentos"] = DocumentoCaso.objects.filter(caso=self.object)
        return context


class CasoUpdateView(PermissionRequiredMixin, UpdateView):
    model = Caso
    form_class = CasoForm
    template_name = "direccion/caso_form.html"
    login_url = reverse_lazy("login")
    success_url = reverse_lazy("caso_list")
    permisos_requeridos = [perms.CASOS_EDITAR]

    def form_valid(self, form):
        messages.success(self.request, "Caso actualizado exitosamente.")
        resp = super().form_valid(form)
        auditar(self.request, "ACTUALIZAR", "Caso", self.object.pk, str(self.object), f"Caso: {self.object.nombre}")
        return resp


class CasoDeleteView(PermissionRequiredMixin, DeleteView):
    model = Caso
    template_name = "direccion/caso_confirm_delete.html"
    success_url = reverse_lazy("caso_list")
    login_url = reverse_lazy("login")
    permisos_requeridos = [perms.CASOS_ELIMINAR]

    def form_valid(self, form):
        obj = self.object
        repr_ = str(obj)
        pk_val = obj.pk
        nombre = obj.nombre
        # Clean up associated documents from disk
        for doc in DocumentoCaso.objects.filter(caso=obj):
            if doc.archivo:
                doc.archivo.delete(False)
        for inv in Investigado.objects.filter(caso=obj):
            for doc in DocumentoInvestigado.objects.filter(investigado=inv):
                if doc.archivo:
                    doc.archivo.delete(False)
            inv.delete()
        for b in Bien.objects.filter(caso=obj):
            for doc in DocumentoBien.objects.filter(bien=b):
                if doc.archivo:
                    doc.archivo.delete(False)
            if b.foto:
                b.foto.delete(False)
            b.delete()
        obj.delete()
        messages.success(self.request, f"Expediente eliminado permanentemente: {repr_}")
        auditar(self.request, "ELIMINAR", "Caso", pk_val, repr_, f"Nombre: {nombre}")
        return redirect(self.success_url)



# ======================================================================================
# CASO RAPIDO (Modal create from investigado_list)
# ======================================================================================

@permiso_required(perms.CASOS_CREAR)
def caso_crear_rapido(request):
    """Crear un caso desde el modal rapido (POST-only)."""
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        descripcion = request.POST.get("descripcion", "").strip()
        if not nombre:
            messages.error(request, "El nombre es obligatorio.")
        else:
            caso = Caso(nombre=nombre, descripcion=descripcion or None)
            caso.save()
            messages.success(request, f'Caso "{nombre}" creado.')
            auditar(request, "CREAR", "Caso", caso.pk, str(caso), "Caso: " + nombre)
    return redirect("investigado_list")

# ======================================================================================
# CASO DOCUMENTS
# ======================================================================================

@permiso_required(perms.CASOS_DOCUMENTOS_AGREGAR)
def agregar_documento_caso(request, pk):
    caso = get_object_or_404(Caso, pk=pk)
    if request.method == "POST":
        form = DocumentoCasoForm(request.POST, request.FILES)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.caso = caso
            documento.save()
            messages.success(request, "Documento agregado al caso exitosamente.")
            auditar(request, "CREAR", "DocumentoCaso", documento.pk, str(documento), f"Caso: {caso}")
        else:
            messages.error(request, "Error al subir el documento. Verifique el formato.")
    return redirect("caso_detail", pk=pk)


@permiso_required(perms.CASOS_DOCUMENTOS_ELIMINAR)
def eliminar_documento_caso(request, pk, doc_pk):
    documento = get_object_or_404(DocumentoCaso, pk=doc_pk, caso_id=pk)
    doc_repr = str(documento)
    pk_val = documento.pk
    caso_repr = str(documento.caso)
    if documento.archivo:
        documento.archivo.delete()
    documento.delete()
    messages.success(request, "Documento eliminado del caso exitosamente.")
    auditar(request, "ELIMINAR", "DocumentoCaso", pk_val, doc_repr, f"Caso: {caso_repr}")
    return redirect("caso_detail", pk=pk)

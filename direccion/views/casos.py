# ============================================================
# Casos e Investigados CRUD
# ============================================================

from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Count
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

from ..models import Caso, Investigado, DocumentoInvestigado, DocumentoCaso
from ..forms import CasoForm, InvestigadoForm, DocumentoInvestigadoForm, DocumentoCasoForm
from .mixins import PermissionRequiredMixin
from ..decorators import permiso_required
from ..audit import auditar
from .. import permissions as perms


class CasoListView(PermissionRequiredMixin, ListView):
    model = Caso
    template_name = "direccion/caso_list.html"
    context_object_name = "casos"
    login_url = reverse_lazy("login")
    permisos_requeridos = [perms.CASOS_VER]

    def get_queryset(self):
        return Caso.objects.filter(activo=True).order_by("-fecha_creacion")


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
        Investigado.objects.filter(caso=obj).update(caso=None)
        obj.delete()
        messages.success(self.request, f"Expediente eliminado permanentemente: {repr_}")
        auditar(self.request, "ELIMINAR", "Caso", pk_val, repr_, f"Nombre: {nombre}")
        return redirect(self.success_url)


# ============================================================
# INVESTIGADOS CRUD
# ============================================================

class InvestigadoListView(PermissionRequiredMixin, ListView):
    model = Investigado
    template_name = "direccion/investigado_list.html"
    context_object_name = "investigado_list"
    login_url = reverse_lazy("login")
    paginate_by = 25
    permisos_requeridos = [perms.INVESTIGADOS_VER]

    def get_queryset(self):
        queryset = Investigado.objects.filter(activo=True).select_related("caso")
        caso_id = self.request.GET.get("caso", "")
        search = self.request.GET.get("search", "")
        if caso_id:
            queryset = queryset.filter(caso_id=caso_id)
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
        context["caso_filtro"] = self.request.GET.get("caso", "")
        context["casos"] = Caso.objects.filter(activo=True).order_by("nombre")
        return context


class InvestigadoCreateView(PermissionRequiredMixin, CreateView):
    model = Investigado
    form_class = InvestigadoForm
    template_name = "direccion/investigado_form.html"
    login_url = reverse_lazy("login")
    permisos_requeridos = [perms.INVESTIGADOS_CREAR]

    def get_success_url(self):
        return reverse_lazy("investigado_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "Investigado registrado exitosamente.")
        resp = super().form_valid(form)
        auditar(self.request, "CREAR", "Investigado", self.object.pk, str(self.object), f"Cédula: {self.object.cedula or 'N/A'}")
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
        auditar(self.request, "ACTUALIZAR", "Investigado", self.object.pk, str(self.object), f"Cédula: {self.object.cedula or 'N/A'}")
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
        auditar(self.request, "ELIMINAR", "Investigado", pk_val, repr_, f"Cédula: {cedula}")
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


# ============================================================
# DOCUMENTACION DE LA DIRECCION
# ============================================================

@permiso_required(perms.DOCUMENTOS_DIRECCION_VER)
def documentos_direccion_list(request):
    categoria_filtro = request.GET.get('categoria', '')
    documentos = DocumentoDireccion.objects.all().order_by('-fecha_subida')
    if categoria_filtro:
        documentos = documentos.filter(categoria=categoria_filtro)
    if request.method == "POST":
        form = DocumentoDireccionForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Documento subido exitosamente.")
            auditar(request, "CREAR", "DocumentoDireccion", form.instance.pk, str(form.instance), "Documento Direccion")
        else:
            messages.error(request, "Error al subir el documento. Verifique el formato.")
        return redirect("documentos_direccion" + (f'?categoria={categoria_filtro}' if categoria_filtro else ''))
    else:
        form = DocumentoDireccionForm()
    return render(request, "direccion/documentos_direccion.html", {
        "documentos": documentos,
        "form": form,
        "categoria_filtro": categoria_filtro,
        "categorias": DocumentoDireccion.CATEGORIA_CHOICES,
    })


@permiso_required(perms.DOCUMENTOS_DIRECCION_ELIMINAR)
def eliminar_documento_direccion(request, doc_pk):
    documento = get_object_or_404(DocumentoDireccion, pk=doc_pk)
    doc_repr = str(documento)
    pk_val = documento.pk
    if documento.archivo:
        documento.archivo.delete()
    documento.delete()
    messages.success(request, "Documento eliminado exitosamente.")
    auditar(request, "ELIMINAR", "DocumentoDireccion", pk_val, doc_repr, "Documento Direccion")
    return redirect("documentos_direccion")


# ============================================================
# CASO DOCUMENTS
# ============================================================

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



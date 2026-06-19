from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import UpdateView, DetailView
from django.contrib.auth.decorators import login_required

from ...models import CarpetaBien, Bien, DocumentoBien, DocumentoCarpetaBien
from ...forms import CarpetaForm, CarpetaBienDocumentForm
from ..mixins import PermissionRequiredMixin
from ...decorators import permiso_required
from ...audit import auditar
from ... import permissions as perms


# ============================================================
# Carpetas de Bienes
# ============================================================


@permiso_required(perms.BIENES_CARPETAS_CREAR)
def carpeta_bien_crear(request):
    """Crear una carpeta de bienes."""
    from ...models import CarpetaBien
    from ...audit import auditar
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
    from ...models import CarpetaBien
    from ...audit import auditar
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




class CarpetaBienUpdateView(PermissionRequiredMixin, UpdateView):
    """Vista para editar/renombrar una carpeta de bienes."""
    model = CarpetaBien
    form_class = CarpetaForm
    template_name = 'direccion/bien_carpeta_form.html'
    permission_required = perms.BIENES_CARPETAS_RENOMBRAR

    def get_success_url(self):
        return reverse_lazy('bien_carpeta_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, f'Carpeta renombrada a "{form.instance.nombre}".')
        auditar(
            self.request, "EDITAR", "CarpetaBien", form.instance.pk,
            f'Renombrada de "{CarpetaBien.objects.get(pk=form.instance.pk).nombre}" a "{form.instance.nombre}"',
            "Carpeta de Bien"
        )
        return super().form_valid(form)

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
    from ...models import CarpetaBien
    from ...audit import auditar
    carpeta = get_object_or_404(CarpetaBien, pk=pk)
    nombre = str(carpeta)
    pk_val = carpeta.pk
    carpeta.delete()
    messages.success(request, f'Carpeta "{nombre}" eliminada.')
    auditar(request, "ELIMINAR", "CarpetaBien", pk_val, nombre, "Carpeta de Bien: " + nombre)
    return redirect("bien_list")

@login_required
@permiso_required(perms.BIENES_DOCUMENTOS_AGREGAR)
def agregar_documento_carpeta(request, pk):
    carpeta = get_object_or_404(CarpetaBien, pk=pk)
    if request.method == "POST":
        form = CarpetaBienDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.carpeta = carpeta
            documento.save()
            messages.success(request, "Documento agregado exitosamente.")
            auditar(request, "CREAR", "DocumentoCarpetaBien", documento.pk, str(documento), f"Carpeta: {carpeta}")
        else:
            messages.error(request, "Error al subir el documento. Verifique el formato.")
    return redirect("bien_carpeta_detail", pk=pk)


@login_required
@permiso_required(perms.BIENES_DOCUMENTOS_ELIMINAR)
def eliminar_documento_carpeta(request, pk, doc_pk):
    documento = get_object_or_404(DocumentoCarpetaBien, pk=doc_pk, carpeta_id=pk)
    doc_repr = str(documento)
    pk_val = documento.pk
    carpeta_repr = str(documento.carpeta)
    if documento.archivo:
        documento.archivo.delete()
    documento.delete()
    messages.success(request, "Documento eliminado exitosamente.")
    auditar(request, "ELIMINAR", "DocumentoCarpetaBien", pk_val, doc_repr, f"Carpeta: {carpeta_repr}")
    return redirect("bien_carpeta_detail", pk=pk)


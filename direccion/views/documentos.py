# ============================================================
# Documentos de la Dirección
# ============================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from ..models import DocumentoDireccion
from ..forms import DocumentoDireccionForm
from ..decorators import permiso_required
from ..audit import auditar
from .. import permissions as perms


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



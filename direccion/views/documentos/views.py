# ============================================================
# Documentos de la Direccion - Vistas principales
# ============================================================

import os

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages

from direccion.models import DocumentoDireccion
from direccion.forms import DocumentoDireccionForm
from direccion.decorators import permiso_required
from direccion.audit import auditar
from direccion import permissions as perms

CAT_COLORS = {
    'LEYES': ('bg-amber-50', 'text-amber-600', 'hover:bg-amber-100', 'bg-amber-100', 'text-amber-700', 'border-amber-200', '#FDE68A', '#D97706'),
    'DOCUMENTOS': ('bg-blue-50', 'text-blue-600', 'hover:bg-blue-100', 'bg-blue-100', 'text-blue-700', 'border-blue-200', '#DBEAFE', '#2563EB'),
    'MEMO': ('bg-purple-50', 'text-purple-600', 'hover:bg-purple-100', 'bg-purple-100', 'text-purple-700', 'border-purple-200', '#E9D5FF', '#7C3AED'),
    'RECURSOS': ('bg-emerald-50', 'text-emerald-600', 'hover:bg-emerald-100', 'bg-emerald-100', 'text-emerald-700', 'border-emerald-200', '#D1FAE5', '#059669'),
}

CAT_ICONS = {
    'LEYES': 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253',
    'DOCUMENTOS': 'M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z',
    'MEMO': 'M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z',
    'RECURSOS': 'M13 10V3L4 14h7v7l9-11h-7z',
}


@permiso_required(perms.DOCUMENTOS_DIRECCION_VER)
def documentos_direccion_list(request):
    """Lista los documentos de la direccion con filtros por categoria."""
    categoria_filtro = request.GET.get('categoria', '')
    documentos = DocumentoDireccion.objects.all().order_by('-fecha_subida')
    # Agrupar documentos por categoria
    carpetas = []
    for key, label in DocumentoDireccion.CATEGORIA_CHOICES:
        if categoria_filtro and categoria_filtro != key:
            docs_cat = []
        else:
            docs_cat = [d for d in documentos if d.categoria == key]
        colors = CAT_COLORS.get(key, ('bg-gray-50', 'text-gray-600', 'hover:bg-gray-100', 'bg-gray-100', 'text-gray-700', 'border-gray-200', '#E5E7EB', '#6B7280'))
        icon_path = CAT_ICONS.get(key, 'M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z')
        carpetas.append({
            'key': key,
            'label': label,
            'documentos': docs_cat,
            'count': len(docs_cat),
            'bg_color': colors[0],
            'icon_color': colors[1],
            'hover_bg': colors[2],
            'badge_bg': colors[3],
            'badge_text': colors[4],
            'border_color': colors[5],
        })

    if request.method == "POST":
        form = DocumentoDireccionForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Documento subido exitosamente.")
            auditar(request, "CREAR", "DocumentoDireccion", form.instance.pk, str(form.instance), "Documento Direccion")
        else:
            messages.error(request, "Error al subir el documento. Verifique el formato.")
        url = reverse("documentos_direccion")
        if categoria_filtro:
            url += f"?categoria={categoria_filtro}"
        return redirect(url)
    else:
        form = DocumentoDireccionForm()

    return render(request, "direccion/documentos_direccion.html", {
        "carpetas": carpetas,
        "form": form,
        "categoria_filtro": categoria_filtro,
        "categorias": DocumentoDireccion.CATEGORIA_CHOICES,
        "documentos": documentos,
    })


@permiso_required(perms.DOCUMENTOS_DIRECCION_EDITAR)
def editar_documento_direccion(request, doc_pk):
    """Edita la descripcion y categoria de un documento de la direccion."""
    doc = get_object_or_404(DocumentoDireccion, pk=doc_pk)
    if request.method == "POST":
        form = DocumentoDireccionForm(request.POST, instance=doc)
        if form.is_valid():
            form.save()
            messages.success(request, "Documento actualizado.")
            return redirect("documentos_direccion_categoria", categoria=doc.categoria)
    else:
        form = DocumentoDireccionForm(instance=doc)
    form.fields.pop('archivo', None)
    return render(request, "direccion/documento_direccion_edit.html", {
        "form": form,
        "doc": doc,
    })


@permiso_required(perms.DOCUMENTOS_DIRECCION_ELIMINAR)
def eliminar_documento_direccion(request, doc_pk):
    """Elimina un documento de la direccion."""
    documento = get_object_or_404(DocumentoDireccion, pk=doc_pk)
    doc_repr = str(documento)
    pk_val = documento.pk
    if documento.archivo:
        documento.archivo.delete()
    documento.delete()
    messages.success(request, "Documento eliminado exitosamente.")
    auditar(request, "ELIMINAR", "DocumentoDireccion", pk_val, doc_repr, "Documento Direccion")
    return redirect("documentos_direccion")


@permiso_required(perms.DOCUMENTOS_DIRECCION_VER)
def documentos_direccion_categoria(request, categoria):
    """Muestra documentos filtrados por una categoria especifica."""
    valid_cats = [k for k,_ in DocumentoDireccion.CATEGORIA_CHOICES]
    if categoria not in valid_cats:
        messages.error(request, "Categoria no valida.")
        return redirect("documentos_direccion")

    documentos_cat = DocumentoDireccion.objects.filter(categoria=categoria).order_by("-fecha_subida")

    cat_label = dict(DocumentoDireccion.CATEGORIA_CHOICES).get(categoria, categoria)
    colors = CAT_COLORS.get(categoria, ("bg-gray-50", "text-gray-600", "hover:bg-gray-100", "bg-gray-100", "text-gray-700", "border-gray-200", "#E5E7EB", "#6B7280"))
    icon_path = CAT_ICONS.get(categoria, "M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z")

    if request.method == "POST":
        form = DocumentoDireccionForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.categoria = categoria
            doc.save()
            messages.success(request, "Documento subido exitosamente.")
            auditar(request, "CREAR", "DocumentoDireccion", doc.pk, str(doc), "Documentos Direccion")
            return redirect("documentos_direccion_categoria", categoria=categoria)
        else:
            messages.error(request, "Error al subir el documento. Verifique el formato.")
    else:
        form = DocumentoDireccionForm(initial={"categoria": categoria})

    context = {
        "documentos_cat": documentos_cat,
        "categoria_key": categoria,
        "cat_label": cat_label,
        "bg_color": colors[0],
        "icon_color": colors[1],
        "icon_path": icon_path,
        "badge_bg": colors[3],
        "badge_text": colors[4],
        "count": len(documentos_cat),
        "form": form,
    }
    return render(request, "direccion/documentos_direccion_categoria.html", context)

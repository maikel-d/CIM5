# ============================================================
# Documentos de la Dirección
# ============================================================

import os

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from ..models import DocumentoDireccion, CarpetaDireccion
from ..forms import DocumentoDireccionForm, CarpetaDireccionForm
from ..decorators import permiso_required
from ..audit import auditar
from .. import permissions as perms

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
    # Remove archivo from form so users can only edit descripcion/categoria
    form.fields.pop('archivo', None)
    return render(request, "direccion/documento_direccion_edit.html", {
        "form": form,
        "doc": doc,
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

@permiso_required(perms.DOCUMENTOS_DIRECCION_VER)
def documentos_direccion_categoria(request, categoria):
    valid_cats = [k for k,_ in DocumentoDireccion.CATEGORIA_CHOICES]
    if categoria not in valid_cats:
        messages.error(request, "Categoría no válida.")
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
            auditar(request, "CREAR", "DocumentoDireccion", doc.pk, str(doc), "Documentos Dirección")
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
@permiso_required(perms.DOCUMENTOS_DIRECCION_SUBIR)

@require_POST
def batch_upload_documentos(request):
    """Subida masiva de documentos vía drag & drop (AJAX/multi-file).
    Acepta múltiples archivos en request.FILES y crea un DocumentoDireccion
    por cada uno. Retorna JSON con resultados.
    """
    categoria = request.POST.get("categoria", "DOCUMENTOS")
    files = request.FILES.getlist("archivos")
    
    if not files:
        return JsonResponse({"success": False, "error": "No se recibieron archivos."}, status=400)
    
    results = []
    created_count = 0
    error_count = 0
    
    for f in files:
        # Validar tamaño (10 MB)
        if f.size > 10 * 1024 * 1024:
            results.append({
                "name": f.name,
                "status": "error",
                "error": f"El archivo supera el límite de 10MB ({f.size / 1024 / 1024:.1f}MB)",
            })
            error_count += 1
            continue
        
        # Validar extensión
        ext = os.path.splitext(f.name)[1].lower()
        allowed = ['.pdf', '.doc', '.docx', '.png', '.jpg', '.jpeg', '.gif', '.webp']
        if ext not in allowed:
            results.append({
                "name": f.name,
                "status": "error",
                "error": f"Formato no soportado: {ext}",
            })
            error_count += 1
            continue
        
        # Crear el documento
        try:
            doc = DocumentoDireccion.objects.create(
                archivo=f,
                categoria=categoria,
                descripcion=os.path.splitext(f.name)[0],
            )
            created_count += 1
            results.append({
                "name": f.name,
                "status": "ok",
                "id": doc.pk,
                "url": doc.archivo.url,
                "tipo": doc.tipo,
            })
        except Exception as e:
            results.append({
                "name": f.name,
                "status": "error",
                "error": str(e),
            })
            error_count += 1
    
    if created_count:
        auditar(request, "CREAR", "DocumentoDireccion", 0,
                f"Subida masiva: {created_count} documento(s), {error_count} error(es)",
                "Documentos Direccion")
    
    return JsonResponse({
        "success": True,
        "created": created_count,
        "errors": error_count,
        "results": results,
    })

@permiso_required(perms.DOCUMENTOS_DIRECCION_ELIMINAR)
def carpeta_direccion_crear(request):
    """Crea una nueva carpeta de documentos."""
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        categoria = request.POST.get("categoria", "")
        if nombre:
            carpeta = CarpetaDireccion.objects.create(
                nombre=nombre,
                categoria=categoria or None,
            )
            messages.success(request, f"Carpeta '{nombre}' creada exitosamente.")
            auditar(request, "CREAR", "CarpetaDireccion", carpeta.pk, nombre, "Documentos Direccion")
        else:
            messages.error(request, "Debe ingresar un nombre para la carpeta.")
    return redirect("documentos_direccion")

@permiso_required(perms.DOCUMENTOS_DIRECCION_ELIMINAR)
def carpeta_direccion_renombrar(request, pk):
    """Renombra una carpeta de documentos."""
    carpeta = get_object_or_404(CarpetaDireccion, pk=pk)
    if request.method == "POST":
        nuevo_nombre = request.POST.get("nombre", "").strip()
        if nuevo_nombre:
            old_name = carpeta.nombre
            carpeta.nombre = nuevo_nombre
            carpeta.save()
            messages.success(request, f"Carpeta renombrada a '{nuevo_nombre}'.")
            auditar(request, "ACTUALIZAR", "CarpetaDireccion", carpeta.pk, f"{old_name} -> {nuevo_nombre}", "Documentos Direccion")
        else:
            messages.error(request, "Debe ingresar un nombre para la carpeta.")
    return redirect("documentos_direccion")

@permiso_required(perms.DOCUMENTOS_DIRECCION_ELIMINAR)
def carpeta_direccion_eliminar(request, pk):
    """Elimina una carpeta de documentos."""
    carpeta = get_object_or_404(CarpetaDireccion, pk=pk)
    nombre = carpeta.nombre
    pk_val = carpeta.pk
    carpeta.delete()
    messages.success(request, f"Carpeta '{nombre}' eliminada.")
    auditar(request, "ELIMINAR", "CarpetaDireccion", pk_val, nombre, "Documentos Direccion")
    return redirect("documentos_direccion")




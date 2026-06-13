from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..models import DocumentoUsuario, CarpetaUsuario
from ..forms import DocumentoUsuarioForm
from ..audit import auditar


@login_required
def mis_documentos_list(request, carpeta_pk=None):
    usuario = request.user
    carpeta_actual = None
    breadcrumb = []
    if carpeta_pk:
        carpeta_actual = get_object_or_404(CarpetaUsuario, pk=carpeta_pk, usuario=usuario)
        parent = carpeta_actual
        crumbs = []
        while parent:
            crumbs.insert(0, parent)
            parent = parent.parent
        breadcrumb = crumbs
    carpetas = CarpetaUsuario.objects.filter(usuario=usuario, parent=carpeta_actual).order_by('orden', 'nombre')
    docs = DocumentoUsuario.objects.filter(usuario=usuario, carpeta=carpeta_actual).order_by('-fecha_subida')
    if request.method == "POST" and not request.POST.get('crear_carpeta'):
        form = DocumentoUsuarioForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.usuario = usuario
            doc.carpeta = carpeta_actual
            doc.save()
            messages.success(request, "Documento subido exitosamente.")
            auditar(request, "CREAR", "DocumentoUsuario", doc.pk, str(doc), "Mis Documentos")
        else:
            messages.error(request, "Error al subir el documento.")
        if carpeta_actual:
            return redirect("mis_documentos_carpeta", carpeta_pk=carpeta_actual.pk)
        return redirect("mis_documentos")
    else:
        form = DocumentoUsuarioForm()
    return render(request, "direccion/mis_documentos.html", {
        "documentos": docs,
        "carpetas": carpetas,
        "carpeta_actual": carpeta_actual,
        "breadcrumb": breadcrumb,
        "form": form,
        "total": docs.count(),
        "docs_pdf": docs.filter(tipo="PDF").count(),
        "docs_word": docs.filter(tipo="WORD").count(),
        "docs_img": docs.filter(tipo="IMAGEN").count(),
    })


@login_required
def eliminar_documento_usuario(request, doc_pk):
    doc = get_object_or_404(DocumentoUsuario, pk=doc_pk, usuario=request.user)
    carpeta_pk = doc.carpeta.pk if doc.carpeta else None
    if request.method == "POST":
        dr, pv = str(doc), doc.pk
        if doc.archivo:
            doc.archivo.delete()
        doc.delete()
        messages.success(request, "Documento eliminado.")
        auditar(request, "ELIMINAR", "DocumentoUsuario", pv, dr, "Mis Documentos")
        if carpeta_pk:
            return redirect("mis_documentos_carpeta", carpeta_pk=carpeta_pk)
        return redirect("mis_documentos")
    if carpeta_pk:
        return redirect("mis_documentos_carpeta", carpeta_pk=carpeta_pk)
    return redirect("mis_documentos")


@login_required
def crear_carpeta(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        parent_pk = request.POST.get("parent", None)
        if not nombre:
            messages.error(request, "El nombre de la carpeta es obligatorio.")
        else:
            parent = None
            if parent_pk:
                parent = get_object_or_404(CarpetaUsuario, pk=parent_pk, usuario=request.user)
            exists = CarpetaUsuario.objects.filter(
                usuario=request.user, nombre=nombre, parent=parent
            ).exists()
            if exists:
                messages.error(request, 'Ya existe una carpeta llamada "' + nombre + '" en esta ubicacion.')
            else:
                CarpetaUsuario.objects.create(
                    usuario=request.user, nombre=nombre, parent=parent
                )
                messages.success(request, 'Carpeta "' + nombre + '" creada.')
                auditar(request, "CREAR", "CarpetaUsuario", None, nombre, "Mis Documentos - Carpetas")
        if parent_pk:
            return redirect("mis_documentos_carpeta", carpeta_pk=parent_pk)
        return redirect("mis_documentos")
    return redirect("mis_documentos")


@login_required
def renombrar_carpeta(request, carpeta_pk):
    carpeta = get_object_or_404(CarpetaUsuario, pk=carpeta_pk, usuario=request.user)
    if request.method == "POST":
        nuevo_nombre = request.POST.get("nombre", "").strip()
        if not nuevo_nombre:
            messages.error(request, "El nombre es obligatorio.")
        else:
            exists = CarpetaUsuario.objects.filter(
                usuario=request.user, nombre=nuevo_nombre,
                parent=carpeta.parent
            ).exclude(pk=carpeta.pk).exists()
            if exists:
                messages.error(request, 'Ya existe otra carpeta llamada "' + nuevo_nombre + '" aqui.')
            else:
                viejo = carpeta.nombre
                carpeta.nombre = nuevo_nombre
                carpeta.save()
                messages.success(request, 'Carpeta renombrada a "' + nuevo_nombre + '".')
                auditar(request, "ACTUALIZAR", "CarpetaUsuario", carpeta.pk, viejo + ' -> ' + nuevo_nombre, "Mis Documentos")
        if carpeta.parent:
            return redirect("mis_documentos_carpeta", carpeta_pk=carpeta.parent.pk)
        return redirect("mis_documentos")
    if carpeta.parent:
        return redirect("mis_documentos_carpeta", carpeta_pk=carpeta.parent.pk)
    return redirect("mis_documentos")


@login_required
def eliminar_carpeta(request, carpeta_pk):
    carpeta = get_object_or_404(CarpetaUsuario, pk=carpeta_pk, usuario=request.user)
    parent_pk = carpeta.parent.pk if carpeta.parent else None
    if request.method == "POST":
        nombre = str(carpeta)
        pk_val = carpeta.pk
        def get_descendant_ids(folder):
            ids = [folder.pk]
            for sub in folder.subcarpetas.all():
                ids.extend(get_descendant_ids(sub))
            return ids
        all_ids = get_descendant_ids(carpeta)
        DocumentoUsuario.objects.filter(carpeta__pk__in=all_ids).update(carpeta=None)
        CarpetaUsuario.objects.filter(pk__in=all_ids).delete()
        messages.success(request, 'Carpeta "' + carpeta.nombre + '" eliminada.')
        auditar(request, "ELIMINAR", "CarpetaUsuario", pk_val, nombre, "Mis Documentos")
        if parent_pk:
            return redirect("mis_documentos_carpeta", carpeta_pk=parent_pk)
        return redirect("mis_documentos")
    if parent_pk:
        return redirect("mis_documentos_carpeta", carpeta_pk=parent_pk)
    return redirect("mis_documentos")

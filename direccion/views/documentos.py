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



# ============================================================
# MIS DOCUMENTOS (Documentos por usuario)
# ============================================================



def mis_documentos_subir(request):
    """Subir archivo(s) a Mis Documentos."""
    if not request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect("login")
    
    from ..models import DocumentoUsuario, CarpetaUsuario
    from ..audit import auditar
    from django.contrib import messages
    from django.shortcuts import redirect
    
    if request.method == "POST":
        archivos = request.FILES.getlist("archivos")
        carpeta_id = request.POST.get("carpeta_id")
        carpeta = None
        if carpeta_id:
            carpeta = CarpetaUsuario.objects.filter(pk=carpeta_id, usuario=request.user).first()
        
        for archivo in archivos:
            doc = DocumentoUsuario(
                usuario=request.user,
                archivo=archivo,
                carpeta=carpeta,
            )
            doc.save()
            auditar(request, "CREAR", "DocumentoUsuario", doc.pk, str(doc), "Archivo: " + archivo.name)
        
        if len(archivos) == 1:
            msg = "1 archivo subido exitosamente."
        else:
            msg = str(len(archivos)) + " archivos subidos exitosamente."
        messages.success(request, msg)
    return redirect("mis_documentos")


def mis_documentos_eliminar(request, doc_pk):
    """Eliminar un documento."""
    if not request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect("login")
    
    from ..models import DocumentoUsuario
    from ..audit import auditar
    from django.contrib import messages
    from django.shortcuts import redirect, get_object_or_404
    
    documento = get_object_or_404(DocumentoUsuario, pk=doc_pk, usuario=request.user)
    if request.method == "POST":
        doc_repr = str(documento)
        pk_val = documento.pk
        if documento.archivo:
            documento.archivo.delete()
        documento.delete()
        messages.success(request, "Documento eliminado exitosamente.")
        auditar(request, "ELIMINAR", "DocumentoUsuario", pk_val, doc_repr, "Documento de usuario")
    return redirect("mis_documentos")



def mis_documentos(request, carpeta_pk=None):
    """Vista principal con soporte para subcarpetas."""
    if not request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect("login")
    from ..models import CarpetaUsuario, DocumentoUsuario
    carpeta_actual = None
    breadcrumbs = []
    if carpeta_pk:
        from django.shortcuts import get_object_or_404
        carpeta_actual = get_object_or_404(CarpetaUsuario, pk=carpeta_pk, usuario=request.user)
        temp = carpeta_actual
        while temp:
            breadcrumbs.insert(0, temp)
            temp = temp.parent
    carpetas = CarpetaUsuario.objects.filter(usuario=request.user, parent=carpeta_actual).order_by("orden", "nombre")
    documentos = DocumentoUsuario.objects.filter(usuario=request.user, carpeta=carpeta_actual).order_by("-fecha_subida")
    carpetas_data = [{"carpeta": c, "subcarpetas": CarpetaUsuario.objects.filter(parent=c).order_by("orden", "nombre"), "documentos": DocumentoUsuario.objects.filter(carpeta=c).order_by("-fecha_subida")} for c in carpetas]
    return render(request, "direccion/mis_documentos.html", {"carpetas": carpetas_data, "documentos": documentos, "carpeta_actual": carpeta_actual, "breadcrumbs": breadcrumbs})

def mis_documentos_crear_carpeta(request):
    """Crear una carpeta o subcarpeta."""
    if not request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect("login")
    from ..models import CarpetaUsuario
    from ..audit import auditar
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        parent_id = request.POST.get("parent_id")
        if not nombre:
            messages.error(request, "El nombre es obligatorio.")
        else:
            parent = None
            if parent_id:
                parent = CarpetaUsuario.objects.filter(pk=parent_id, usuario=request.user).first()
            carpeta = CarpetaUsuario(usuario=request.user, nombre=nombre, parent=parent)
            carpeta.save()
            messages.success(request, "Carpeta creada exitosamente.")
            auditar(request, "CREAR", "CarpetaUsuario", carpeta.pk, str(carpeta), "Carpeta: " + nombre)
    if parent_id:
        from django.shortcuts import redirect
        return redirect("mis_documentos_carpeta", carpeta_pk=parent_id)
    return redirect("mis_documentos")

def mis_documentos_renombrar_carpeta(request, carpeta_pk):
    """Renombrar una carpeta."""
    if not request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect("login")
    from ..models import CarpetaUsuario
    from ..audit import auditar
    from django.shortcuts import get_object_or_404
    carpeta = get_object_or_404(CarpetaUsuario, pk=carpeta_pk, usuario=request.user)
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        if nombre:
            old = str(carpeta.nombre)
            carpeta.nombre = nombre
            carpeta.save()
            messages.success(request, "Carpeta renombrada exitosamente.")
            auditar(request, "ACTUALIZAR", "CarpetaUsuario", carpeta.pk, str(carpeta), "Renombrar: " + old + " -> " + nombre)
        else:
            messages.error(request, "El nombre es obligatorio.")
    if carpeta.parent:
        return redirect("mis_documentos_carpeta", carpeta_pk=carpeta.parent.pk)
    return redirect("mis_documentos")

def mis_documentos_eliminar_carpeta(request, carpeta_pk):
    """Eliminar carpeta y todo su contenido."""
    if not request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect("login")
    from ..models import CarpetaUsuario, DocumentoUsuario
    from ..audit import auditar
    from django.shortcuts import get_object_or_404
    carpeta = get_object_or_404(CarpetaUsuario, pk=carpeta_pk, usuario=request.user)
    parent = carpeta.parent
    if request.method == "POST":
        def eliminar_recursivo(obj):
            for d in DocumentoUsuario.objects.filter(carpeta=obj):
                if d.archivo:
                    d.archivo.delete()
                d.delete()
            for s in CarpetaUsuario.objects.filter(parent=obj):
                eliminar_recursivo(s)
                s.delete()
        eliminar_recursivo(carpeta)
        auditar(request, "ELIMINAR", "CarpetaUsuario", carpeta.pk, str(carpeta), "Eliminar carpeta")
        carpeta.delete()
        messages.success(request, "Carpeta eliminada exitosamente.")
    if parent:
        return redirect("mis_documentos_carpeta", carpeta_pk=parent.pk)
    return redirect("mis_documentos")

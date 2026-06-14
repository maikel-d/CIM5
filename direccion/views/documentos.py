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
    carpeta_filtro = request.GET.get('carpeta', '')
    documentos = DocumentoDireccion.objects.all().order_by('-fecha_subida')
    if categoria_filtro:
        documentos = documentos.filter(categoria=categoria_filtro)
    if carpeta_filtro and carpeta_filtro.isdigit():
        documentos = documentos.filter(carpeta_id=carpeta_filtro)
    
    # Subcarpetas de documentos
    from ..models import CarpetaDireccion
    carpeta_actual = None
    breadcrumbs = []
    if carpeta_filtro and carpeta_filtro.isdigit():
        try:
            carpeta_actual = CarpetaDireccion.objects.get(pk=carpeta_filtro)
            temp = carpeta_actual
            while temp:
                breadcrumbs.insert(0, temp)
                temp = temp.parent
            # Show subfolders of the current folder
            carpetas_direccion = CarpetaDireccion.objects.filter(parent=carpeta_actual).order_by('nombre')
        except CarpetaDireccion.DoesNotExist:
            carpetas_direccion = CarpetaDireccion.objects.filter(parent__isnull=True).order_by('nombre')
    else:
        carpetas_direccion = CarpetaDireccion.objects.filter(parent__isnull=True).order_by('nombre')
    if request.method == "POST":
        form = DocumentoDireccionForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Documento subido exitosamente.")
            auditar(request, "CREAR", "DocumentoDireccion", form.instance.pk, str(form.instance), "Documento Direccion")
        else:
            messages.error(request, "Error al subir el documento. Verifique el formato.")
        params = []
        if categoria_filtro:
            params.append(f'categoria={categoria_filtro}')
        if carpeta_filtro:
            params.append(f'carpeta={carpeta_filtro}')
        qs = '?' + '&'.join(params) if params else ''
        return redirect(f"documentos_direccion{qs}")
    else:
        form = DocumentoDireccionForm()
    return render(request, "direccion/documentos_direccion.html", {
        "documentos": documentos,
        "carpetas_direccion": carpetas_direccion,
        "form": form,
        "categoria_filtro": categoria_filtro,
        "carpeta_filtro": carpeta_filtro,
        "categorias": DocumentoDireccion.CATEGORIA_CHOICES,
        "carpeta_actual": carpeta_actual,
        "breadcrumbs": breadcrumbs,
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



@permiso_required(perms.DOCUMENTOS_DIRECCION_CARPETAS_CREAR)
def carpeta_direccion_crear(request):
    from ..models import CarpetaDireccion
    from ..audit import auditar
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        parent_id = request.POST.get("parent_id")
        if not nombre:
            messages.error(request, "El nombre es obligatorio.")
        else:
            parent = None
            if parent_id:
                parent = CarpetaDireccion.objects.filter(pk=parent_id).first()
            carpeta = CarpetaDireccion(nombre=nombre, parent=parent)
            carpeta.save()
            messages.success(request, f'Carpeta "{nombre}" creada.')
            auditar(request, "CREAR", "CarpetaDireccion", carpeta.pk, str(carpeta), "Carpeta de Documento: " + nombre)
    return redirect("documentos_direccion")


@permiso_required(perms.DOCUMENTOS_DIRECCION_CARPETAS_RENOMBRAR)
def carpeta_direccion_renombrar(request, pk):
    from ..models import CarpetaDireccion
    from ..audit import auditar
    carpeta = get_object_or_404(CarpetaDireccion, pk=pk)
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        if nombre:
            viejo = carpeta.nombre
            carpeta.nombre = nombre
            carpeta.save()
            messages.success(request, f'Carpeta renombrada a "{nombre}".')
            auditar(request, "EDITAR", "CarpetaDireccion", carpeta.pk, f"{viejo} -> {nombre}", "Carpeta de Documento")
    return redirect("documentos_direccion")


@permiso_required(perms.DOCUMENTOS_DIRECCION_CARPETAS_ELIMINAR)
def carpeta_direccion_eliminar(request, pk):
    from ..models import CarpetaDireccion
    from ..audit import auditar
    carpeta = get_object_or_404(CarpetaDireccion, pk=pk)
    nombre = str(carpeta)
    pk_val = carpeta.pk
    carpeta.delete()
    messages.success(request, f'Carpeta "{nombre}" eliminada.')
    auditar(request, "ELIMINAR", "CarpetaDireccion", pk_val, nombre, "Carpeta de Documento: " + nombre)
    return redirect("documentos_direccion")


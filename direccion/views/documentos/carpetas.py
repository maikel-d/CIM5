# ============================================================
# Documentos de la Direccion - Gestion de Carpetas
# ============================================================

from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages

from direccion.models import CarpetaDireccion
from direccion.decorators import permiso_required
from direccion.audit import auditar
from direccion import permissions as perms


@permiso_required(perms.DOCUMENTOS_DIRECCION_ELIMINAR)
def carpeta_direccion_crear(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        categoria = request.POST.get("categoria", "")
        if nombre:
            carpeta = CarpetaDireccion.objects.create(nombre=nombre, categoria=categoria or None)
            messages.success(request, f"Carpeta '{nombre}' creada exitosamente.")
            auditar(request, "CREAR", "CarpetaDireccion", carpeta.pk, nombre, "Documentos Direccion")
        else:
            messages.error(request, "Debe ingresar un nombre para la carpeta.")
    return redirect("documentos_direccion")


@permiso_required(perms.DOCUMENTOS_DIRECCION_ELIMINAR)
def carpeta_direccion_renombrar(request, pk):
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
    carpeta = get_object_or_404(CarpetaDireccion, pk=pk)
    nombre = carpeta.nombre
    pk_val = carpeta.pk
    carpeta.delete()
    messages.success(request, f"Carpeta '{nombre}' eliminada.")
    auditar(request, "ELIMINAR", "CarpetaDireccion", pk_val, nombre, "Documentos Direccion")
    return redirect("documentos_direccion")

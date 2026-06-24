# ============================================================
# Tareas Pendientes
# ============================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from ..models import Tarea
from ..forms import TareaForm
from ..decorators import permiso_required
from .. import permissions as perms


@permiso_required(perms.TAREAS_VER)
@login_required
def tareas_list(request):
    """Lista todas las tareas con filtros, busqueda y categorias."""
    if request.method == "POST":
        form = TareaForm(request.POST)
        if form.is_valid():
            tarea = form.save(commit=False)
            tarea.creado_por = request.user
            tarea.save()
            messages.success(request, "Tarea agregada.")
        return redirect("tareas_list")

    # Filtros
    filtro_prioridad = request.GET.get("prioridad", "")
    filtro_categoria = request.GET.get("categoria", "")
    filtro_estado = request.GET.get("estado", "")
    busqueda = request.GET.get("q", "")

    tareas = Tarea.objects.all()

    if filtro_prioridad:
        tareas = tareas.filter(prioridad=filtro_prioridad)
    if filtro_categoria:
        tareas = tareas.filter(categoria=filtro_categoria)
    if filtro_estado == "pendientes":
        tareas = tareas.filter(completada=False)
    elif filtro_estado == "completadas":
        tareas = tareas.filter(completada=True)
    if busqueda:
        tareas = tareas.filter(
            Q(descripcion__icontains=busqueda) |
            Q(creado_por__username__icontains=busqueda) |
            Q(creado_por__first_name__icontains=busqueda)
        )

    tareas = tareas.order_by('completada', '-fecha_creacion')

    form = TareaForm()
    return render(request, "direccion/tareas_list.html", {
        "tareas": tareas,
        "form": form,
        "CATEGORIA_CHOICES": Tarea.CATEGORIA_CHOICES,
        "filtro_prioridad": filtro_prioridad,
        "filtro_categoria": filtro_categoria,
        "filtro_estado": filtro_estado,
        "busqueda": busqueda,
    })


@permiso_required(perms.TAREAS_COMPLETAR)
def tarea_completar(request, pk):
    """Marca/desmarca una tarea como completada."""
    tarea = get_object_or_404(Tarea, pk=pk)
    tarea.completada = not tarea.completada
    tarea.save()
    estado = "completada" if tarea.completada else "pendiente"
    messages.success(request, f"Tarea marcada como {estado}.")
    # Redirect back to the page the user came from (preserves filters)
    next_url = request.GET.get("next", "tareas_list")
    return redirect(next_url)


@permiso_required(perms.TAREAS_ELIMINAR)
def tarea_eliminar(request, pk):
    """Elimina una tarea."""
    tarea = get_object_or_404(Tarea, pk=pk)
    tarea.delete()
    messages.success(request, "Tarea eliminada.")
    next_url = request.GET.get("next") or request.POST.get("next") or "tareas_list"
    return redirect(next_url)

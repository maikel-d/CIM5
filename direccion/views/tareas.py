# ============================================================
# Tareas Pendientes
# ============================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from ..models import Tarea
from ..forms import TareaForm
from ..decorators import permiso_required
from .. import permissions as perms


@permiso_required(perms.TAREAS_VER)
def tareas_list(request):
    """Lista todas las tareas pendientes. Cualquier usuario puede añadir."""
    if request.method == "POST":
        form = TareaForm(request.POST)
        if form.is_valid():
            tarea = form.save(commit=False)
            tarea.creado_por = request.user
            tarea.save()
            messages.success(request, "Tarea agregada.")
        return redirect("tareas_list")
    tareas = Tarea.objects.all()
    form = TareaForm()
    return render(request, "direccion/tareas_list.html", {
        "tareas": tareas,
        "form": form,
    })


@permiso_required(perms.TAREAS_COMPLETAR)
def tarea_completar(request, pk):
    """Marca/desmarca una tarea como completada."""
    tarea = get_object_or_404(Tarea, pk=pk)
    tarea.completada = not tarea.completada
    tarea.save()
    estado = "completada" if tarea.completada else "pendiente"
    messages.success(request, f"Tarea marcada como {estado}.")
    return redirect("tareas_list")


@permiso_required(perms.TAREAS_ELIMINAR)
def tarea_eliminar(request, pk):
    """Elimina una tarea."""
    tarea = get_object_or_404(Tarea, pk=pk)
    tarea.delete()
    messages.success(request, "Tarea eliminada.")
    return redirect("tareas_list")



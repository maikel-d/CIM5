# ============================================================
# Tareas Pendientes
# ============================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Q

from ..models import Tarea
from ..forms import TareaForm
from ..audit import auditar
from ..decorators import permiso_required
from .. import permissions as perms


@permiso_required(perms.TAREAS_VER)
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


@require_POST
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
    """Elimina una tarea con confirmacion previa."""
    tarea = get_object_or_404(Tarea, pk=pk)
    if request.method == "POST":
        pk_val = tarea.pk
        desc = tarea.descripcion[:50]
        tarea.delete()
        messages.success(request, "Tarea eliminada.")
        auditar(request, "ELIMINAR", "Tarea", pk_val, desc, "Tarea")
        next_url = request.POST.get("next") or "tareas_list"
        if next_url.startswith("http://") or next_url.startswith("https://") or next_url.startswith("//"):
            next_url = "tareas_list"
        return redirect(next_url)
    return render(request, "direccion/tarea_confirm_delete.html", {"tarea": tarea})


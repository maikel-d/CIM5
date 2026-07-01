# ============================================================
# Tickets de Soporte
# ============================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Case, When, IntegerField

from ..models import TicketSoporte, notificar_administradores
from ..forms import TicketSoporteForm, TicketAsignarForm
from ..decorators import permiso_required
from ..audit import auditar
from django.views.decorators.http import require_POST
from .. import permissions as perms


@permiso_required(perms.TICKETS_VER)
def ticket_detail(request, pk):
    """Detalle de un ticket con su historial de cambios."""
    ticket = get_object_or_404(TicketSoporte.objects.select_related('creado_por', 'asignado_a'), pk=pk)
    return render(request, "direccion/ticket_detail.html", {
        "ticket": ticket,
        "historial": ticket.historial.all(),
    })


@permiso_required(perms.TICKETS_VER)
def ticket_list(request):
    """Lista de tickets con filtros por estado y usuario."""
    filtro_estado = request.GET.get("estado", "")
    filtro_usuario = request.GET.get("usuario", "")
    filtro_prioridad = request.GET.get("prioridad", "")

    # Admin/Supervisor ven todos los tickets; el resto solo los propios
    if request.user.profile.tiene_permiso(perms.TICKETS_RESOLVER):
        tickets = TicketSoporte.objects.select_related('creado_por', 'asignado_a').all()
        if filtro_usuario:
            tickets = tickets.filter(creado_por_id=filtro_usuario)
    else:
        tickets = TicketSoporte.objects.select_related('creado_por', 'asignado_a').filter(creado_por=request.user)

    if filtro_estado:
        tickets = tickets.filter(estado=filtro_estado)

    if filtro_prioridad:
        tickets = tickets.filter(prioridad=filtro_prioridad)

    # Orden: abiertos/en_proceso primero, luego por fecha descendente
    tickets = tickets.annotate(
        estado_prioridad=Case(
            When(estado='ABIERTO', then=0),
            When(estado='EN_PROCESO', then=1),
            When(estado='RESUELTO', then=2),
            When(estado='CERRADO', then=3),
            output_field=IntegerField(),
        )
    ).order_by('estado_prioridad', '-fecha_creacion')

    usuarios = User.objects.filter(is_active=True).order_by("username") if request.user.profile.tiene_permiso(perms.TICKETS_RESOLVER) else []

    return render(request, "direccion/ticket_list.html", {
        "tickets": tickets,
        "filtro_estado": filtro_estado,
        "filtro_usuario": filtro_usuario,
        "filtro_prioridad": filtro_prioridad,
        "usuarios": usuarios,
        "estados": TicketSoporte.ESTADO_CHOICES,
    })


@permiso_required(perms.TICKETS_CREAR)
def ticket_create(request):
    """Crea un nuevo ticket de soporte."""
    if request.method == "POST":
        form = TicketSoporteForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.creado_por = request.user
            ticket.save()
            # Registrar creación en el historial
            ticket.registrar_cambio(request.user, 'estado', '---', 'ABIERTO')
            ticket.registrar_cambio(request.user, 'prioridad', '---', ticket.prioridad)
            messages.success(request, f"Ticket #{ticket.pk} creado exitosamente.")
            auditar(request, "CREAR", "TicketSoporte", ticket.pk, str(ticket), f"Asunto: {ticket.asunto}")
            notificar_administradores(
                f"Nuevo ticket #{ticket.pk}: {ticket.asunto} (por {request.user.get_full_name() or request.user.username})",
                link="/tickets/"
            )
            return redirect("ticket_detail", pk=ticket.pk)
    else:
        form = TicketSoporteForm()
    return render(request, "direccion/ticket_form.html", {
        "form": form,
        "accion": "Crear"
    })


@permiso_required(perms.TICKETS_RESOLVER)
def ticket_resolver(request, pk):
    """Marca un ticket como resuelto (un solo clic desde la lista)."""
    ticket = get_object_or_404(TicketSoporte, pk=pk)
    estado_anterior = ticket.estado
    if ticket.estado == 'RESUELTO':
        ticket.estado = 'ABIERTO'
        mensaje = "reabierto"
    else:
        ticket.estado = 'RESUELTO'
        mensaje = "resuelto"
    ticket.save()
    ticket.registrar_cambio(request.user, 'estado', estado_anterior, ticket.estado)
    messages.success(request, f"Ticket #{ticket.pk} marcado como {mensaje}.")
    auditar(request, "ACTUALIZAR", "TicketSoporte", ticket.pk, str(ticket),
            f"Estado: {ticket.get_estado_display()}")
    return redirect("ticket_list")


@permiso_required(perms.TICKETS_ASIGNAR)
def ticket_asignar(request, pk):
    """Asigna un ticket a un usuario y/o cambia su estado (solo admin)."""
    ticket = get_object_or_404(TicketSoporte, pk=pk)
    estado_anterior = ticket.estado
    prioridad_anterior = ticket.prioridad
    asignado_anterior = ticket.asignado_a

    if request.method == "POST":
        form = TicketAsignarForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            ticket.registrar_cambio(request.user, 'estado', estado_anterior, ticket.estado)
            ticket.registrar_cambio(request.user, 'prioridad', prioridad_anterior, ticket.prioridad)
            anterior_nombre = asignado_anterior.get_full_name() or asignado_anterior.username if asignado_anterior else '---'
            nuevo_nombre = ticket.asignado_a.get_full_name() or ticket.asignado_a.username if ticket.asignado_a else '---'
            ticket.registrar_cambio(request.user, 'asignado_a', anterior_nombre, nuevo_nombre)
            messages.success(request, f"Ticket #{ticket.pk} actualizado.")
            auditar(request, "ACTUALIZAR", "TicketSoporte", ticket.pk, str(ticket),
                    f"Estado: {ticket.get_estado_display()}, Asignado: {ticket.asignado_a or 'Nadie'}")
            return redirect("ticket_detail", pk=ticket.pk)
    else:
        form = TicketAsignarForm(instance=ticket)
    return render(request, "direccion/ticket_form.html", {
        "form": form,
        "ticket": ticket,
        "accion": "Asignar"
    })

@permiso_required(perms.TICKETS_VER)
@require_POST
def ticket_cambiar_estado(request, pk):
    ticket = get_object_or_404(TicketSoporte, pk=pk)
    estado_anterior = ticket.estado
    nuevo_estado = request.POST.get("estado", "")
    estados_validos = [e[0] for e in TicketSoporte.ESTADO_CHOICES]
    if nuevo_estado not in estados_validos:
        messages.error(request, "Estado invalido.")
        return redirect("dashboard")
    if nuevo_estado != ticket.estado:
        ticket.estado = nuevo_estado
        ticket.save()
        ticket.registrar_cambio(request.user, 'estado', estado_anterior, ticket.estado)
        messages.success(request, f"Ticket #{ticket.pk} cambiado a {ticket.get_estado_display()}.")
        auditar(request, "ACTUALIZAR", "TicketSoporte", ticket.pk, str(ticket),
                f"Estado: {estado_anterior} -> {ticket.get_estado_display()}")
    else:
        messages.info(request, f"Ticket #{ticket.pk} ya esta {ticket.get_estado_display()}.")
    return redirect("dashboard")


@permiso_required(perms.TICKETS_RESOLVER)
def ticket_eliminar(request, pk):
    """Elimina un ticket con confirmacion previa."""
    ticket = get_object_or_404(TicketSoporte, pk=pk)
    if request.method == "POST":
        pk_val = ticket.pk
        asunto = ticket.asunto
        ticket.delete()
        messages.success(request, f"Ticket #{pk} eliminado.")
        auditar(request, "ELIMINAR", "TicketSoporte", pk_val, asunto, f"Asunto: {asunto}")
        return redirect("ticket_list")
    return render(request, "direccion/ticket_confirm_delete.html", {"ticket": ticket})


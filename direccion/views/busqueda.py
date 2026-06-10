# ============================================================
# Búsqueda Global
# ============================================================

from django.http import JsonResponse
from django.urls import reverse_lazy
from django.db.models import Q

from ..models import (
    Personal, Caso, Investigado, DocumentoDireccion,
    TicketSoporte, Tarea, Bien, InformeDiario
)
from ..decorators import permiso_required
from .. import permissions as perms


@permiso_required(perms.DASHBOARD_VER)
def busqueda_global(request):
    """Endpoint JSON para búsqueda global en todos los módulos del sistema.
    Retorna resultados agrupados por modelo, ordenados por relevancia.
    Filtra según los permisos del usuario autenticado.
    """
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'results': {}})

    try:
        profile = request.user.profile
    except Exception:
        return JsonResponse({'results': {}})

    results = {}

    # Personal
    if profile.tiene_permiso(perms.PERSONAL_VER):
        personal_qs = Personal.objects.filter(activo=True).filter(
            Q(apellidos__icontains=q) |
            Q(nombres__icontains=q) |
            Q(cedula__icontains=q)
        )[:8]
        if personal_qs:
            results['personal'] = {
                'label': 'Personal',
                'icon': 'users',
                'items': [{
                    'id': p.pk,
                    'title': f"{p.apellidos}, {p.nombres}",
                    'subtitle': p.cedula,
                    'url': reverse_lazy('personal_detail', args=[p.pk]),
                } for p in personal_qs]
            }

    # Casos
    if profile.tiene_permiso(perms.CASOS_VER):
        casos_qs = Caso.objects.filter(activo=True).filter(
            Q(nombre__icontains=q) |
            Q(descripcion__icontains=q)
        )[:5]
        if casos_qs:
            results['casos'] = {
                'label': 'Expedientes',
                'icon': 'folder',
                'items': [{
                    'id': c.pk,
                    'title': c.nombre,
                    'subtitle': c.descripcion or '',
                    'url': reverse_lazy('caso_detail', args=[c.pk]),
                } for c in casos_qs]
            }

    # Investigados
    if profile.tiene_permiso(perms.INVESTIGADOS_VER):
        inv_qs = Investigado.objects.filter(activo=True).filter(
            Q(apellidos__icontains=q) |
            Q(nombres__icontains=q) |
            Q(cedula__icontains=q)
        )[:8]
        if inv_qs:
            results['investigados'] = {
                'label': 'Investigados',
                'icon': 'search',
                'items': [{
                    'id': i.pk,
                    'title': f"{i.apellidos}, {i.nombres}",
                    'subtitle': i.cedula or 'Sin cédula',
                    'url': reverse_lazy('investigado_detail', args=[i.pk]),
                } for i in inv_qs]
            }

    # Documentos de la Dirección
    if profile.tiene_permiso(perms.DOCUMENTOS_DIRECCION_VER):
        docs_qs = DocumentoDireccion.objects.filter(
            Q(descripcion__icontains=q)
        )[:5]
        if docs_qs:
            results['documentos'] = {
                'label': 'Documentación',
                'icon': 'file',
                'items': [{
                    'id': d.pk,
                    'title': d.descripcion or d.archivo.name.split('/')[-1],
                    'subtitle': f"{d.get_categoria_display()} · {d.get_tipo_display()}",
                    'url': d.archivo.url if d.archivo else '#',
                } for d in docs_qs]
            }

    # Tickets de Soporte
    if profile.tiene_permiso(perms.TICKETS_VER):
        tickets_qs = TicketSoporte.objects.filter(
            Q(asunto__icontains=q) |
            Q(descripcion__icontains=q)
        ).select_related('creado_por')[:5]
        if tickets_qs:
            results['tickets'] = {
                'label': 'Tickets de Soporte',
                'icon': 'ticket',
                'items': [{
                    'id': t.pk,
                    'title': f"#{t.pk} - {t.asunto}",
                    'subtitle': f"{t.get_estado_display()} · {t.creado_por.get_full_name() or t.creado_por.username if t.creado_por else 'Sistema'}",
                    'url': reverse_lazy('ticket_detail', args=[t.pk]),
                } for t in tickets_qs]
            }

    # Tareas
    if profile.tiene_permiso(perms.TAREAS_VER):
        tareas_qs = Tarea.objects.filter(
            Q(descripcion__icontains=q)
        )[:5]
        if tareas_qs:
            results['tareas'] = {
                'label': 'Tareas',
                'icon': 'checklist',
                'items': [{
                    'id': t.pk,
                    'title': t.descripcion[:80],
                    'subtitle': f"{'✓ Completada' if t.completada else '○ Pendiente'} · {t.get_prioridad_display()}",
                    'url': reverse_lazy('tareas_list'),
                } for t in tareas_qs]
            }

    # Bienes
    if profile.tiene_permiso(perms.BIENES_VER):
        bienes_qs = Bien.objects.filter(activo=True).filter(
            Q(nombre__icontains=q) |
            Q(codigo_inventario__icontains=q) |
            Q(serial__icontains=q) |
            Q(marca__icontains=q) |
            Q(ubicacion__icontains=q)
        )[:5]
        if bienes_qs:
            results['bienes'] = {
                'label': 'Bienes',
                'icon': 'folder',
                'items': [{
                    'id': b.pk,
                    'title': f"{b.nombre}",
                    'subtitle': f"{b.get_categoria_display()} · {b.get_estado_display()}",
                    'url': reverse_lazy('bien_detail', args=[b.pk]),
                } for b in bienes_qs]
            }

    # Informes Diarios
    if profile.tiene_permiso(perms.INFORMES_VER):
        informes_qs = InformeDiario.objects.filter(
            Q(titulo__icontains=q) |
            Q(contenido__icontains=q)
        )[:5]
        if informes_qs:
            results['informes'] = {
                'label': 'Informes Diarios',
                'icon': 'chart',
                'items': [{
                    'id': i.pk,
                    'title': i.titulo,
                    'subtitle': i.fecha.strftime('%d/%m/%Y'),
                    'url': reverse_lazy('informe_diario_preview', args=[i.pk]),
                } for i in informes_qs]
            }

    return JsonResponse({'results': results, 'total': sum(len(v['items']) for v in results.values())})



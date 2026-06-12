# ============================================================
# Registros de Auditoría
# ============================================================

import calendar
from datetime import date, timedelta

from django.shortcuts import render
from django.core.paginator import Paginator

from ..models import AuditLog
from ..decorators import permiso_required
from .. import permissions as perms
from ..audit import auditar
from .export import _build_excel_response, _build_pdf_response


def _filtrar_audit_logs(periodo, anio, mes, semana, modelo, accion):
    """Aplica filtros de periodo, modelo y acción a AuditLog y retorna el QuerySet ordenado."""
    qs = AuditLog.objects.all()
    hoy = date.today()

    if modelo:
        qs = qs.filter(modelo__icontains=modelo)
    if accion:
        qs = qs.filter(accion=accion)

    if not anio:
        anio = str(hoy.year)
    if not mes:
        mes = str(hoy.month)

    if periodo == 'dia':
        qs = qs.filter(fecha__date=hoy)
    elif periodo == 'semana' and semana:
        try:
            semana_int = int(semana)
            primer_dia = date(int(anio), 1, 1)
            dias_restar = primer_dia.weekday()
            if dias_restar <= 3:
                lunes_sem1 = primer_dia - timedelta(days=dias_restar)
            else:
                lunes_sem1 = primer_dia + timedelta(days=(7 - dias_restar))
            lunes = lunes_sem1 + timedelta(weeks=semana_int - 1)
            domingo = lunes + timedelta(days=6)
            qs = qs.filter(fecha__date__gte=lunes, fecha__date__lte=domingo)
        except (ValueError, TypeError):
            pass
    elif periodo == 'mes' and mes:
        qs = qs.filter(fecha__year=int(anio), fecha__month=int(mes))
    elif periodo == 'anio' and anio:
        qs = qs.filter(fecha__year=int(anio))

    return qs.order_by("-fecha"), hoy, anio, mes


@permiso_required(perms.AUDITORIA_VER)
def audit_log_list(request):
    """Lista de registros de auditoría con filtros por periodo (día/semana/mes/año), modelo y acción."""
    from django.core.paginator import Paginator

    periodo = request.GET.get('periodo', 'dia')
    anio = request.GET.get('anio', '')
    mes = request.GET.get('mes', '')
    semana = request.GET.get('semana', '')
    modelo = request.GET.get("modelo", "")
    accion = request.GET.get("accion", "")

    qs, hoy, anio, mes = _filtrar_audit_logs(periodo, anio, mes, semana, modelo, accion)

    paginator = Paginator(qs, 25)
    page = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page)
    except Exception:
        page_obj = paginator.page(1)

    # Años disponibles
    anios_disponibles = AuditLog.objects.dates('fecha', 'year', order='DESC')
    if not anios_disponibles:
        anios_disponibles = [hoy]

    # Meses
    meses_opciones = []
    for i in range(1, 13):
        meses_opciones.append((i, calendar.month_name[i].capitalize()))

    context = {
        "logs": page_obj,
        "page_obj": page_obj,
        "paginator": paginator,
        "is_paginated": paginator.num_pages > 1,
        "total_logs": AuditLog.objects.count(),
        "modelo_filtro": modelo,
        "accion_filtro": accion,
        "acciones": AuditLog.ACCIONES,
        "periodo": periodo,
        "anio_actual": anio,
        "mes_actual": mes,
        "semana_actual": semana,
        "anios_disponibles": anios_disponibles,
        "meses_opciones": meses_opciones,
        "hoy": hoy,
    }
    return render(request, "direccion/audit_log_list.html", context)


@permiso_required(perms.AUDITORIA_EXPORTAR_EXCEL)
def exportar_auditoria_excel(request):
    """Exporta los registros de auditoría filtrados a Excel."""
    periodo = request.GET.get('periodo', 'dia')
    anio = request.GET.get('anio', '')
    mes = request.GET.get('mes', '')
    semana = request.GET.get('semana', '')
    modelo = request.GET.get("modelo", "")
    accion = request.GET.get("accion", "")

    qs, _, _, _ = _filtrar_audit_logs(periodo, anio, mes, semana, modelo, accion)

    headers = ["Fecha", "Usuario", "Acción", "Modelo", "Objeto", "Detalle", "IP"]
    rows = []
    for log in qs:
        rows.append([
            log.fecha.strftime("%d/%m/%Y %H:%M"),
            log.username,
            log.get_accion_display(),
            log.modelo,
            log.objeto_repr or "",
            log.detalle or "",
            log.direccion_ip or "",
        ])

    auditar(request, "EXPORTAR", "AuditLog", None, "Exportación Excel",
            f"{qs.count()} registros")
    return _build_excel_response(
        "Auditoría", headers, rows,
        [20, 25, 18, 25, 40, 40, 18], "auditoria.xlsx"
    )


@permiso_required(perms.AUDITORIA_EXPORTAR_PDF)
def exportar_auditoria_pdf(request):
    """Exporta los registros de auditoría filtrados a PDF."""
    periodo = request.GET.get('periodo', 'dia')
    anio = request.GET.get('anio', '')
    mes = request.GET.get('mes', '')
    semana = request.GET.get('semana', '')
    modelo = request.GET.get("modelo", "")
    accion = request.GET.get("accion", "")

    qs, _, _, _ = _filtrar_audit_logs(periodo, anio, mes, semana, modelo, accion)

    headers = ["Fecha", "Usuario", "Acción", "Modelo", "Objeto", "Detalle", "IP"]
    rows = []
    for log in qs:
        rows.append([
            log.fecha.strftime("%d/%m/%Y %H:%M"),
            log.username,
            log.get_accion_display(),
            log.modelo,
            log.objeto_repr or "",
            log.detalle or "",
            log.direccion_ip or "",
        ])

    auditar(request, "EXPORTAR", "AuditLog", None, "Exportación PDF",
            f"{qs.count()} registros")
    return _build_pdf_response(
        "Registros de Auditoría - Reporte",
        headers, rows, "auditoria.pdf"
    )

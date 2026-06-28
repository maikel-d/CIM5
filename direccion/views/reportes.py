# ============================================================
# Reportes - Panel Centralizado
# ============================================================

from datetime import datetime

from django.shortcuts import render
from ..models import Personal, Investigado, DocumentoPersonal, DocumentoInvestigado, DocumentoCaso
from ..decorators import permiso_required
from .. import permissions as perms


@permiso_required(perms.REPORTES_VER)
def panel_reportes(request):
    """Panel central de reportes con filtros y descarga."""
    fec_desde = request.GET.get("fecha_desde", "")
    fec_hasta = request.GET.get("fecha_hasta", "")

    q_personal = Personal.objects.filter(activo=True)
    q_investigados = Investigado.objects.filter(activo=True)
    q_docs_p = DocumentoPersonal.objects.all()
    q_docs_i = DocumentoInvestigado.objects.all()
    q_docs_c = DocumentoCaso.objects.all()

    if fec_desde:
        try:
            desde_dt = datetime.strptime(fec_desde, "%Y-%m-%d")
            q_personal = q_personal.filter(fecha_creacion__gte=desde_dt)
            q_investigados = q_investigados.filter(fecha_creacion__gte=desde_dt)
        except (ValueError, TypeError):
            pass
    if fec_hasta:
        try:
            hasta_dt = datetime.strptime(fec_hasta, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            q_personal = q_personal.filter(fecha_creacion__lte=hasta_dt)
            q_investigados = q_investigados.filter(fecha_creacion__lte=hasta_dt)
        except (ValueError, TypeError):
            pass

    context = {
        "total_personal": q_personal.count(),
        "total_investigados": q_investigados.count(),
        "total_documentos": q_docs_p.count() + q_docs_i.count() + q_docs_c.count(),
        "fecha_desde": fec_desde,
        "fecha_hasta": fec_hasta,
    }
    return render(request, "reportes.html", context)




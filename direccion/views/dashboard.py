# ============================================================
# Dashboard
# ============================================================

import json
import calendar
from datetime import date, timedelta

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.db.models import Q, Case, When, IntegerField, Count
from django.db.models.functions import TruncMonth
from django.utils import timezone

from django.contrib import messages
from ..models import (
    Personal, DocumentoPersonal, Caso, Investigado, DocumentoInvestigado,
    DocumentoCaso, DocumentoDireccion, AuditLog, Tarea,
    InformeDiario, Bien
)
from ..decorators import permiso_required
from .. import permissions as perms
from ..middleware import usuarios_online, usuarios_online_list


@permiso_required(perms.DASHBOARD_VER)
def dashboard(request):
    # Handle quick-add tarea from dashboard
    if request.method == "POST":
        descripcion = request.POST.get("descripcion", "").strip()
        prioridad = request.POST.get("prioridad", "MEDIO")
        if descripcion:
            Tarea.objects.create(
                descripcion=descripcion,
                prioridad=prioridad,
                categoria="GENERAL",
                creado_por=request.user,
            )
            messages.success(request, "Tarea agregada.")
        else:
            messages.error(request, "La descripción de la tarea es requerida.")
        return redirect("dashboard")

    total_personal = Personal.objects.filter(activo=True).count()
    total_casos = Caso.objects.filter(activo=True).count()
    total_investigados = Investigado.objects.filter(activo=True).count()
    total_bienes = Bien.objects.filter(activo=True).count()
    tareas_pendientes = Tarea.objects.filter(completada=False).annotate(
        prioridad_order=Case(
            When(prioridad='ALTO', then=0),
            When(prioridad='MEDIO', then=1),
            When(prioridad='BAJO', then=2),
            output_field=IntegerField(),
        )
    ).order_by('prioridad_order', '-fecha_creacion')
    tareas_count = Tarea.objects.count()
    tareas_completadas = Tarea.objects.filter(completada=True).count()

    # Document type counts — 4 queries using conditional aggregation (instead of 12+)
    _doc_q_pdf = Count('id', filter=Q(tipo='PDF'))
    _doc_q_word = Count('id', filter=Q(tipo='WORD'))
    _doc_q_img = Count('id', filter=Q(tipo='IMAGEN'))
    _doc_q_otro = Count('id', filter=Q(tipo='OTRO'))
    dp = DocumentoPersonal.objects.aggregate(p=_doc_q_pdf, w=_doc_q_word, i=_doc_q_img, o=_doc_q_otro)
    di = DocumentoInvestigado.objects.aggregate(p=_doc_q_pdf, w=_doc_q_word, i=_doc_q_img, o=_doc_q_otro)
    dc = DocumentoCaso.objects.aggregate(p=_doc_q_pdf, w=_doc_q_word, i=_doc_q_img, o=_doc_q_otro)
    dd = DocumentoDireccion.objects.aggregate(p=_doc_q_pdf, w=_doc_q_word, i=_doc_q_img, o=_doc_q_otro)
    docs_pdf = dp['p'] + di['p'] + dc['p'] + dd['p']
    docs_word = dp['w'] + di['w'] + dc['w'] + dd['w']
    docs_img = dp['i'] + di['i'] + dc['i'] + dd['i']
    total_documentos_personal = dp['p'] + dp['w'] + dp['i'] + dp['o']
    total_documentos_investigados = di['p'] + di['w'] + di['i'] + di['o']
    total_documentos_casos = dc['p'] + dc['w'] + dc['i'] + dc['o']
    total_documentos_direccion = dd['p'] + dd['w'] + dd['i'] + dd['o']


    # Recent documents — single set of queries, used for both the chart list and the "by type" section
    docs_personal = DocumentoPersonal.objects.all().order_by("-fecha_subida")[:10]
    docs_investigados = DocumentoInvestigado.objects.all().order_by("-fecha_subida")[:10]
    docs_casos = DocumentoCaso.objects.all().order_by("-fecha_subida")[:10]
    docs_direccion = DocumentoDireccion.objects.all().order_by("-fecha_subida")[:10]

    all_docs_merged = sorted(
        list(docs_personal) + list(docs_investigados) + list(docs_casos) + list(docs_direccion),
        key=lambda d: d.fecha_subida,
        reverse=True
    )

    docs_pdf_list = [d for d in all_docs_merged if d.tipo == 'PDF'][:5]
    docs_word_list = [d for d in all_docs_merged if d.tipo == 'WORD'][:5]
    docs_img_list = [d for d in all_docs_merged if d.tipo == 'IMAGEN'][:5]
    docs_otro_list = [d for d in all_docs_merged if d.tipo == 'OTRO'][:5]

    # Build monthly chart data (last 6 months) — 3 queries instead of 18
    now = timezone.now()
    six_months_ago = (now - timedelta(days=180)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_names_es = {1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun',
                      7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'}

    expected_months = []
    d = six_months_ago
    for _ in range(6):
        expected_months.append((d.year, d.month))
        if d.month == 12:
            d = d.replace(year=d.year + 1, month=1)
        else:
            d = d.replace(month=d.month + 1)
    months = [month_names_es[m] for _, m in expected_months]

    def _monthly_counts(queryset):
        counts = {}
        for row in (queryset.filter(fecha_creacion__gte=six_months_ago)
                           .annotate(month=TruncMonth('fecha_creacion'))
                           .values('month')
                           .annotate(cnt=Count('id'))):
            key = (row['month'].year, row['month'].month)
            counts[key] = row['cnt']
        return [counts.get(ym, 0) for ym in expected_months]

    pm = _monthly_counts(Personal.objects)
    im = _monthly_counts(Investigado.objects)
    cm = _monthly_counts(Caso.objects)

    chart_data = json.dumps({
        "docTypes": {"pdf": docs_pdf, "word": docs_word, "img": docs_img},
        "months": months,
        "personalMonthly": pm,
        "investigadoMonthly": im,
        "casoMonthly": cm,
        "totalPersonal": total_personal,
        "totalCasos": total_casos,
        "totalInvestigados": total_investigados,
    })


    # Informes del mes actual — single query reuse for count and list
    hoy = date.today()
    informes_qs = InformeDiario.objects.filter(
        fecha__year=hoy.year, fecha__month=hoy.month
    )
    total_informes_mes = informes_qs.count()
    informes_mes = informes_qs.order_by('-fecha', '-fecha_creacion')[:10]

    # Auditoria reciente (ultimos 10 registros, si el usuario tiene permiso)
    auditoria_reciente = []
    try:
        if request.user.profile.tiene_permiso(perms.AUDITORIA_VER):
            auditoria_reciente = AuditLog.objects.all().order_by('-fecha')[:10]
    except Exception:
        pass

    context = {
        "total_personal": total_personal,
        "total_casos": total_casos,
        "total_investigados": total_investigados,
        "total_documentos_personal": total_documentos_personal,
        "total_documentos_investigados": total_documentos_investigados,
        "total_documentos_casos": total_documentos_casos,
        "total_documentos_direccion": total_documentos_direccion,
        "docs_pdf": docs_pdf_list,
        "docs_word": docs_word_list,
        "docs_img": docs_img_list,
        "docs_otro": docs_otro_list,
        "tareas_pendientes": tareas_pendientes,
        "tareas_count": tareas_count,
        "tareas_completadas": tareas_completadas,
        "chart_data_json": chart_data,
        "informes_mes": informes_mes,
        "total_informes_mes": total_informes_mes,
        "auditoria_reciente": auditoria_reciente,
        "total_bienes": total_bienes,
        "usuarios_online": usuarios_online(),
        "usuarios_online_list": usuarios_online_list(),
        "mes_actual_nombre": calendar.month_name[hoy.month].capitalize(),
    }
    return render(request, "dashboard.html", context)

from django.contrib.auth.decorators import login_required

@login_required
def usuarios_online_json(request):
    """API JSON: retorna lista de usuarios conectados."""
    from django.http import JsonResponse
    from ..middleware import usuarios_online_list
    usuarios = usuarios_online_list()
    data = []
    for item in usuarios:
        data.append({
            'nombre': item['user'].get_full_name() or item['user'].username,
            'username': item['user'].username,
            'inicial': (item['user'].get_full_name() or item['user'].username)[0].upper(),
            'time_ago': item['time_ago'],
            'rol': item['rol'],
            'rol_class': item.get('rol_class', 'bg-gray-100 text-gray-500'),
        })
    return JsonResponse({'usuarios': data, 'total': len(data)})

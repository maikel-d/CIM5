# ============================================================
# Informes Diarios
# ============================================================

import calendar
import zipfile
import re
from io import BytesIO
from datetime import date, datetime, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.conf import settings

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable
)

from ..models import InformeDiario
from ..forms import InformeDiarioForm
from ..decorators import permiso_required
from ..audit import auditar
from .. import permissions as perms

MESES_ESPANOL = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']


def _generar_pdf_informe(informe):
    """Genera un PDF en memoria para un InformeDiario y devuelve los bytes."""
    pdf_buf = BytesIO()
    styles = getSampleStyleSheet()

    doc = SimpleDocTemplate(
        pdf_buf, pagesize=letter,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.6 * inch, bottomMargin=0.6 * inch
    )

    elements = []

    # Título
    elements.append(Paragraph(
        f"<b>{informe.titulo}</b>",
        ParagraphStyle("TitlePDF", parent=styles["Normal"],
                       fontSize=16, textColor=HexColor("#003363"),
                       spaceAfter=6, leading=20)
    ))

    # Fecha y autor
    autor = informe.creado_por.get_full_name() or informe.creado_por.username if informe.creado_por else 'Sistema'
    elements.append(Paragraph(
        f"<font size='9' color='#6B7280'>Fecha: {informe.fecha.strftime('%d/%m/%Y')} &nbsp;|&nbsp; Autor: {autor}</font>",
        ParagraphStyle("MetaPDF", parent=styles["Normal"],
                       fontSize=9, textColor=HexColor("#6B7280"),
                       spaceAfter=8, leading=12)
    ))

    # Línea separadora
    elements.append(HRFlowable(width="100%", thickness=1, color=HexColor("#E5E7EB"), spaceAfter=14, spaceBefore=2))

    # Contenido
    contenido_html = informe.contenido.replace('\n', '<br/>')
    elements.append(Paragraph(
        contenido_html,
        ParagraphStyle("BodyPDF", parent=styles["Normal"],
                       fontSize=10, leading=15, spaceAfter=10)
    ))

    # Archivo adjunto
    if informe.archivo:
        elements.append(Spacer(1, 12))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#D1D5DB"), spaceAfter=8, spaceBefore=2))
        elements.append(Paragraph(
            f"<font size='9' color='#003363'>Archivo adjunto: {informe.archivo.name.split('/')[-1]}</font>",
            ParagraphStyle("AttachPDF", parent=styles["Normal"],
                           fontSize=9, textColor=HexColor("#003363"),
                           spaceAfter=6, leading=12)
        ))

    # Footer
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(
        f"<font size='7.5' color='#9CA3AF'>Generado: {datetime.now():%d/%m/%Y %H:%M}</font>",
        ParagraphStyle("FooterPDF", parent=styles["Normal"],
                       fontSize=7.5, textColor=HexColor("#9CA3AF"),
                       alignment=1)
    ))

    doc.build(elements)
    pdf_data = pdf_buf.getvalue()
    pdf_buf.close()
    return pdf_data


@permiso_required(perms.INFORMES_PREVIEW)
def previsualizar_informe_pdf(request, pk):
    """Muestra un PDF inline de un informe diario individual para previsualización."""
    informe = get_object_or_404(InformeDiario, pk=pk)
    pdf_data = _generar_pdf_informe(informe)

    safe_titulo = informe.titulo.replace(' ', '_')[:60]
    filename = f"{informe.fecha}_{safe_titulo}.pdf"

    response = HttpResponse(pdf_data, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response


@permiso_required(perms.INFORMES_DESCARGAR)
def exportar_informes_descargar(request):
    """Genera un ZIP con uno o varios informes diarios."""
    tipo = request.GET.get('tipo', 'mes')
    pk = request.GET.get('pk', '')
    semana = request.GET.get('semana', '')
    mes = request.GET.get('mes', '')
    anio = request.GET.get('anio', '')
    hoy = date.today()

    if not anio:
        anio = str(hoy.year)

    informes = InformeDiario.objects.none()
    nombre_zip = "informes.zip"

    if tipo == 'semana' and semana:
        try:
            semana_int = int(semana)
            from datetime import timedelta
            primer_dia = date(int(anio), 1, 1)
            dias_restar = primer_dia.weekday()
            if dias_restar <= 3:
                lunes_sem1 = primer_dia - timedelta(days=dias_restar)
            else:
                lunes_sem1 = primer_dia + timedelta(days=(7 - dias_restar))
            lunes = lunes_sem1 + timedelta(weeks=semana_int - 1)
            domingo = lunes + timedelta(days=6)
            informes = InformeDiario.objects.filter(fecha__gte=lunes, fecha__lte=domingo).order_by('fecha')
        except (ValueError, TypeError):
            pass
        nombre_zip = f"informes_semana_{semana}_{anio}.zip"
    elif tipo == 'anio':
        informes = InformeDiario.objects.filter(
            fecha__year=int(anio)
        ).order_by('fecha')
        nombre_zip = f"informes_{anio}.zip"
    else:  # mes
        if not mes:
            mes = str(hoy.month)
        informes = InformeDiario.objects.filter(
            fecha__year=int(anio), fecha__month=int(mes)
        ).order_by('fecha')
        nombre_mes = MESES_ESPANOL[int(mes) - 1]
        nombre_zip = f"informes_{nombre_mes.lower()}_{anio}.zip"

    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for informe in informes:
            safe_titulo = re.sub(r'[^\w\s-]', '', informe.titulo)
            safe_titulo = re.sub(r'[-\s]+', '_', safe_titulo).strip('_')[:60]
            pdf_filename = f"{informe.fecha}_{safe_titulo}.pdf"

            pdf_data = _generar_pdf_informe(informe)
            zf.writestr(pdf_filename, pdf_data)

    zip_data = buf.getvalue()
    buf.close()

    auditar(request, "EXPORTAR", "InformeDiario", None,
            f"ZIP {nombre_zip}", f"{informes.count()} informe(s)")

    response = HttpResponse(zip_data, content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{nombre_zip}"'
    return response


@permiso_required(perms.INFORMES_ELIMINAR)
def eliminar_informe_diario(request, pk):
    """Elimina un informe diario."""
    informe = get_object_or_404(InformeDiario, pk=pk)
    if request.method == "POST":
        repr_ = str(informe)
        pk_val = informe.pk
        if informe.archivo:
            informe.archivo.delete()
        informe.delete()
        messages.success(request, f"Informe '{repr_}' eliminado exitosamente.")
        auditar(request, "ELIMINAR", "InformeDiario", pk_val, repr_,
                f"Título: {repr_}")
        return redirect("informes_diarios")
    return redirect("informes_diarios")


@permiso_required(perms.INFORMES_VER)
def informes_diarios_list(request):
    """Lista de informes diarios organizados en carpetas por mes."""
    anio = request.GET.get('anio', '')
    mes = request.GET.get('mes', '')

    informes = InformeDiario.objects.all()
    hoy = date.today()

    # Valores por defecto
    if not anio:
        anio = str(hoy.year)

    # Filtrar por año — una sola query para todo el año
    informes_anio = list(informes.filter(fecha__year=int(anio)).order_by('fecha'))

    # Agrupar por mes en Python (evita 12 queries extra)
    informes_por_mes = {i: [] for i in range(1, 13)}
    for inf in informes_anio:
        informes_por_mes[inf.fecha.month].append(inf)

    # Filtrar informes por el mes seleccionado (usa la lista ya cargada)
    if mes:
        mes_int = int(mes)
        informes = [inf for inf in informes_anio if inf.fecha.month == mes_int]
    else:
        mes = ''
        informes = informes_anio

    # Generar opciones de años disponibles (incluye años sin informes)
    anios_bd = list(InformeDiario.objects.dates('fecha', 'year', order='DESC'))
    anios_disponibles = set(anios_bd)
    for extra in range(3):
        anios_disponibles.add(date(hoy.year + extra, 1, 1))
    anios_disponibles.add(date(hoy.year - 1, 1, 1))
    anios_disponibles = sorted(anios_disponibles, reverse=True)

    # Paleta de colores para cada mes
    colores_meses = [
        ('bg-blue-50', 'text-blue-600', 'hover:bg-blue-100', 'border-blue-200', 'bg-blue-100', 'text-blue-700'),
        ('bg-indigo-50', 'text-indigo-600', 'hover:bg-indigo-100', 'border-indigo-200', 'bg-indigo-100', 'text-indigo-700'),
        ('bg-violet-50', 'text-violet-600', 'hover:bg-violet-100', 'border-violet-200', 'bg-violet-100', 'text-violet-700'),
        ('bg-teal-50', 'text-teal-600', 'hover:bg-teal-100', 'border-teal-200', 'bg-teal-100', 'text-teal-700'),
        ('bg-emerald-50', 'text-emerald-600', 'hover:bg-emerald-100', 'border-emerald-200', 'bg-emerald-100', 'text-emerald-700'),
        ('bg-green-50', 'text-green-600', 'hover:bg-green-100', 'border-green-200', 'bg-green-100', 'text-green-700'),
        ('bg-amber-50', 'text-amber-600', 'hover:bg-amber-100', 'border-amber-200', 'bg-amber-100', 'text-amber-700'),
        ('bg-orange-50', 'text-orange-600', 'hover:bg-orange-100', 'border-orange-200', 'bg-orange-100', 'text-orange-700'),
        ('bg-rose-50', 'text-rose-600', 'hover:bg-rose-100', 'border-rose-200', 'bg-rose-100', 'text-rose-700'),
        ('bg-pink-50', 'text-pink-600', 'hover:bg-pink-100', 'border-pink-200', 'bg-pink-100', 'text-pink-700'),
        ('bg-fuchsia-50', 'text-fuchsia-600', 'hover:bg-fuchsia-100', 'border-fuchsia-200', 'bg-fuchsia-100', 'text-fuchsia-700'),
        ('bg-cyan-50', 'text-cyan-600', 'hover:bg-cyan-100', 'border-cyan-200', 'bg-cyan-100', 'text-cyan-700'),
    ]

    # Construir las 12 carpetas de meses con su resumen e informes completos
    meses_con_informes = []
    for mes_num in range(1, 13):
        mes_informes = informes_por_mes[mes_num]
        # Ordenar informes del dia 1 al ultimo del mes
        mes_informes.sort(key=lambda x: x.fecha)
        primer_informe = mes_informes[0] if mes_informes else None
        ultimo_informe = mes_informes[-1] if mes_informes else None
        bg, icon_color, hover_bg, border_accent, badge_bg, badge_text = colores_meses[mes_num - 1]
        meses_con_informes.append({
            'numero': mes_num,
            'nombre': MESES_ESPANOL[mes_num - 1],
            'count': len(mes_informes),
            'informes': mes_informes,  # lista completa ordenada dia 1 -> ultimo
            'primer_informe': primer_informe,
            'ultima_fecha': ultimo_informe.fecha if ultimo_informe else None,  # CORREGIDO: antes era primer_informe.fecha
            'bg_color': bg,
            'icon_color': icon_color,
            'hover_bg': hover_bg,
            'border_accent': border_accent,
            'badge_bg': badge_bg,
            'badge_text': badge_text,
        })

    meses_opciones = []
    for i in range(1, 13):
        meses_opciones.append((i, MESES_ESPANOL[i - 1]))

    # Gestión de creación/edición
    if request.method == "POST":
        form = InformeDiarioForm(request.POST, request.FILES)
        if form.is_valid():
            informe = form.save(commit=False)
            informe.creado_por = request.user
            informe.save()
            messages.success(request, f"Informe '{informe.titulo}' creado exitosamente.")
            auditar(request, "CREAR", "InformeDiario", informe.pk, str(informe), f"Título: {informe.titulo}")
        else:
            messages.error(request, "Error al crear el informe. Verifica los datos.")
        return redirect(request.path + f'?anio={anio}&mes={mes}')
    else:
        form = InformeDiarioForm()

    return render(request, "direccion/informes_diarios.html", {
        "informes": informes,
        "form": form,
        "anio_actual": anio,
        "mes_actual": mes,
        "semana_actual": str(hoy.isocalendar()[1]),
        "anios_disponibles": anios_disponibles,
        "meses_opciones": meses_opciones,
        "meses_con_informes": meses_con_informes,
        "hoy": hoy,
    })



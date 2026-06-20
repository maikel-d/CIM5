# ============================================================
# Informes Diarios
# ============================================================

import calendar
import zipfile
import re
from io import BytesIO
from datetime import date, datetime, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, FileResponse
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
    """Muestra el PDF original subido o genera uno si no hay archivo adjunto."""
    informe = get_object_or_404(InformeDiario, pk=pk)

    # Si el informe tiene un archivo subido, servirlo directamente
    if informe.archivo and informe.archivo.name:
        try:
            import mimetypes
            import os
            content_type, _ = mimetypes.guess_type(informe.archivo.name)
            if not content_type:
                content_type = "application/octet-stream"
            response = FileResponse(informe.archivo.open('rb'), content_type=content_type)
            original_filename = os.path.basename(informe.archivo.name)
            response["Content-Disposition"] = f'inline; filename="{original_filename}"'
            return response
        except (FileNotFoundError, PermissionError, IOError, OSError):
            # Si falla al abrir el archivo, generar uno
            pass

    # Fallback: generar PDF con los datos del informe
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
    total_informes_anio = len(informes_anio)
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

    # Color unificado para todos los meses (tema sidebar #003363)
    color_mes = {"bg": "#E8F0F8", "icon": "#003363", "border": "#C8D8E8", "badge_bg": "#D6E4F0", "badge_text": "#003363"}

    # Construir las 12 carpetas de meses con su resumen e informes completos
    meses_con_informes = []
    for mes_num in range(1, 13):
        mes_informes = informes_por_mes[mes_num]
        # Ordenar informes del dia 1 al ultimo del mes
        mes_informes.sort(key=lambda x: x.fecha)
        color = color_mes

        # Build days of month with indicators
        days_in_month = calendar.monthrange(int(anio), mes_num)[1]
        informe_dates = {inf.fecha.day for inf in mes_informes}
        dias_del_mes = []
        for dia_num in range(1, days_in_month + 1):
            dias_del_mes.append({
                'numero': dia_num,
                'tiene_informe': dia_num in informe_dates,
            })

        meses_con_informes.append({
            'numero': mes_num,
            'nombre': MESES_ESPANOL[mes_num - 1],
            'count': len(mes_informes),
            'informes': mes_informes,  # lista completa ordenada dia 1 -> ultimo
            'dias_del_mes': dias_del_mes,
            'bg_color': color['bg'],
            'icon_color': color['icon'],
            'hover_bg': color['bg'],
            'border_accent': color['border'],
            'badge_bg': color['badge_bg'],
            'badge_text': color['badge_text'],
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
        "total_informes_anio": total_informes_anio,
        "hoy": hoy,
    })



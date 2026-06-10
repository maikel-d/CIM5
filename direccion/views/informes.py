# ============================================================
# Informes Diarios
# ============================================================

import calendar
import zipfile
import re
from io import BytesIO
from datetime import date, datetime, timedelta

from django.shortcuts import render, redirect, get_object_or_404
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
    else:  # mes
        if not mes:
            mes = str(hoy.month)
        informes = InformeDiario.objects.filter(
            fecha__year=int(anio), fecha__month=int(mes)
        ).order_by('fecha')
        nombre_mes = calendar.month_name[int(mes)].capitalize()
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
    """Lista de informes diarios con filtros por semana, mes y año."""
    periodo = request.GET.get('periodo', 'mes')
    anio = request.GET.get('anio', '')
    mes = request.GET.get('mes', '')
    semana = request.GET.get('semana', '')

    informes = InformeDiario.objects.all()
    hoy = date.today()

    # Valores por defecto
    if not anio:
        anio = str(hoy.year)
    if not mes:
        mes = str(hoy.month)

    # Aplicar filtros
    informes = informes.filter(fecha__year=int(anio))

    if periodo == 'semana' and semana:
        try:
            semana_int = int(semana)
            # Calcular rango de fechas para la semana ISO
            from datetime import timedelta
            # Primero obtenemos el primer día del año
            primer_dia = date(int(anio), 1, 1)
            # Ajustar al lunes de la semana 1 ISO
            dias_restar = primer_dia.weekday()  # 0 = lunes
            if dias_restar <= 3:
                lunes_sem1 = primer_dia - timedelta(days=dias_restar)
            else:
                lunes_sem1 = primer_dia + timedelta(days=(7 - dias_restar))
            lunes = lunes_sem1 + timedelta(weeks=semana_int - 1)
            domingo = lunes + timedelta(days=6)
            informes = informes.filter(fecha__gte=lunes, fecha__lte=domingo)
        except (ValueError, TypeError):
            pass

    if periodo == 'mes' and mes:
        informes = informes.filter(fecha__month=int(mes))

    # Generar opciones para los filtros
    anios_disponibles = InformeDiario.objects.dates('fecha', 'year', order='DESC')
    if not anios_disponibles:
        anios_disponibles = [hoy]

    # Meses en español
    meses_opciones = []
    for i in range(1, 13):
        meses_opciones.append((i, calendar.month_name[i].capitalize()))

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
        return redirect(request.path + (f'?periodo={periodo}&anio={anio}&mes={mes}&semana={semana}' if periodo else ''))
    else:
        form = InformeDiarioForm()

    return render(request, "direccion/informes_diarios.html", {
        "informes": informes,
        "form": form,
        "periodo": periodo,
        "anio_actual": anio,
        "mes_actual": mes,
        "semana_actual": semana,
        "anios_disponibles": anios_disponibles,
        "meses_opciones": meses_opciones,
        "hoy": hoy,

    })



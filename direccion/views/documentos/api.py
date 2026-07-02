# ============================================================
# Documentos de la Direccion - API / Batch Upload
# ============================================================

import os
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from direccion.models import DocumentoDireccion
from direccion.decorators import permiso_required
from direccion.audit import auditar
from direccion import permissions as perms
from direccion.validators import validar_tipo_real


@permiso_required(perms.DOCUMENTOS_DIRECCION_SUBIR)
@require_POST
def batch_upload_documentos(request):
    categoria = request.POST.get("categoria", "DOCUMENTOS")
    files = request.FILES.getlist("archivos")
    if not files:
        return JsonResponse({"success": False, "error": "No se recibieron archivos."}, status=400)
    results = []
    created_count = 0
    error_count = 0
    for f in files:
        if f.size > 10 * 1024 * 1024:
            results.append({"name": f.name, "status": "error", "error": f"Archivo supera limite de 10MB ({f.size / 1024 / 1024:.1f}MB)"})
            error_count += 1
            continue

        # Validar tipo real (extensión + firma de bytes)
        es_valido, error_msg = validar_tipo_real(f)
        if not es_valido:
            results.append({"name": f.name, "status": "error", "error": error_msg})
            error_count += 1
            continue

        try:
            doc = DocumentoDireccion.objects.create(archivo=f, categoria=categoria, descripcion=os.path.splitext(f.name)[0])
            created_count += 1
            results.append({"name": f.name, "status": "ok", "id": doc.pk, "url": doc.archivo.url, "tipo": doc.tipo})
        except Exception as e:
            results.append({"name": f.name, "status": "error", "error": str(e)})
            error_count += 1
    if created_count:
        auditar(request, "CREAR", "DocumentoDireccion", 0, f"Subida masiva: {created_count} doc(s), {error_count} error(es)", "Documentos Direccion")
    return JsonResponse({"success": True, "created": created_count, "errors": error_count, "results": results})

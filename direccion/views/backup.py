# ============================================================
# Backup & Restore
# ============================================================

import zipfile
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.conf import settings
from django.core.management import call_command

from ..decorators import permiso_required
from ..audit import auditar
from .. import permissions as perms
from .export import _human_size


@permiso_required(perms.BACKUP_DESCARGAR)
def backup_view(request):
    """Panel de copias de seguridad: descargar backup o restaurar.
    Compatible con SQLite y PostgreSQL (usa dumpdata/loaddata).
    """
    db_engine = settings.DATABASES['default']['ENGINE']
    db_name = settings.DATABASES['default']['NAME']

    # Obtener info del tamaño de BD según el motor
    db_size = 0
    if 'sqlite' in db_engine:
        db_path = Path(settings.DATABASES['default']['NAME'])
        db_size = db_path.stat().st_size if db_path.exists() else 0

    media_root = settings.MEDIA_ROOT
    media_count = sum(1 for _ in media_root.rglob('*') if _.is_file()) if media_root.exists() else 0
    media_size = sum(f.stat().st_size for f in media_root.rglob('*') if f.is_file()) if media_root.exists() else 0

    context = {
        'db_size': db_size,
        'db_size_human': _human_size(db_size) if 'sqlite' in db_engine else 'Gestionado por PostgreSQL',
        'media_count': media_count,
        'media_size_human': _human_size(media_size),
        'total_size_human': _human_size(db_size + media_size) if 'sqlite' in db_engine else _human_size(media_size),
        'fecha_actual': datetime.now().strftime('%d/%m/%Y %H:%M'),
        'db_engine': 'PostgreSQL' if 'postgresql' in db_engine else 'SQLite',
    }
    return render(request, 'direccion/backup.html', context)


@permiso_required(perms.BACKUP_DESCARGAR)
def descargar_backup(request):
    """Genera y descarga un archivo ZIP con dump de la BD y los archivos media.
    Compatible con SQLite y PostgreSQL (usa dumpdata de Django).
    """
    from django.core.management import call_command

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        # 1. Backup de la base de datos usando dumpdata (funciona con cualquier motor)
        backup_json = tmp / 'backup.json'
        with open(str(backup_json), 'w', encoding='utf-8') as f:
            call_command('dumpdata', '--natural-foreign', '--natural-primary',
                         '--exclude', 'contenttypes', '--exclude', 'auth.permission',
                         stdout=f)

        # 2. Copiar archivos media
        media_copy = tmp / 'media'
        if settings.MEDIA_ROOT.exists():
            shutil.copytree(str(settings.MEDIA_ROOT), str(media_copy), dirs_exist_ok=True)

        # 3. Crear ZIP
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_name = f'respaldo_{timestamp}.zip'
        zip_path = tmp / zip_name

        with zipfile.ZipFile(str(zip_path), 'w', zipfile.ZIP_DEFLATED) as zf:
            if backup_json.exists():
                zf.write(str(backup_json), 'backup.json')
            if media_copy.exists():
                for f in sorted(media_copy.rglob('*')):
                    if f.is_file():
                        rel = f.relative_to(media_copy)
                        zf.write(str(f), f'media/{rel}')

        # 4. Información del backup
        with zipfile.ZipFile(str(zip_path), 'r') as zf:
            info = zf.infolist()

        auditar(request, "BACKUP", "Sistema", None, "Descarga de respaldo",
                f"{zip_name} - {len(info)} archivos")

        # 5. Servir el archivo
        response = HttpResponse(content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{zip_name}"'
        with open(str(zip_path), 'rb') as f:
            response.write(f.read())
        return response


@permiso_required(perms.BACKUP_RESTAURAR)
def restaurar_backup(request):
    """Recibe un archivo ZIP de respaldo y restaura la BD y media.
    Compatible con SQLite y PostgreSQL (usa dumpdata/loaddata de Django).
    Soporta tanto el formato nuevo (backup.json) como el antiguo (db.sqlite3).
    """
    from django.core.management import call_command

    if request.method != 'POST':
        return redirect('backup')

    archivo = request.FILES.get('archivo_respaldo')
    if not archivo:
        messages.error(request, 'Debe seleccionar un archivo de respaldo.')
        return redirect('backup')

    if not archivo.name.endswith('.zip'):
        messages.error(request, 'El archivo debe ser un ZIP.')
        return redirect('backup')

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        zip_path = tmp / 'uploaded.zip'

        with open(str(zip_path), 'wb') as f:
            for chunk in archivo.chunks():
                f.write(chunk)

        try:
            with zipfile.ZipFile(str(zip_path), 'r') as zf:
                zf.extractall(str(tmp))
        except zipfile.BadZipFile:
            messages.error(request, 'El archivo ZIP está corrupto o no es válido.')
            return redirect('backup')

        # Determinar formato del respaldo: nuevo (backup.json) o antiguo (db.sqlite3)
        es_formato_antiguo = (tmp / 'db.sqlite3').exists()
        es_formato_nuevo = (tmp / 'backup.json').exists()

        if not es_formato_antiguo and not es_formato_nuevo:
            messages.error(request, 'El respaldo no contiene una base de datos válida. Debe incluir backup.json o db.sqlite3.')
            return redirect('backup')

        # Si es formato antiguo (SQLite), verificar que el motor actual también sea SQLite
        if es_formato_antiguo and 'postgresql' in settings.DATABASES['default']['ENGINE']:
            messages.error(request, 'El respaldo es de SQLite pero la base de datos actual es PostgreSQL. No se puede restaurar.')
            return redirect('backup')

        # 1. Restaurar la base de datos
        try:
            if es_formato_nuevo:
                # Formato nuevo: limpiar BD y cargar fixture JSON (funciona con PostgreSQL y SQLite)
                call_command('flush', '--noinput', verbosity=0)
                call_command('loaddata', str(tmp / 'backup.json'), verbosity=0)
            elif es_formato_antiguo:
                # Formato antiguo: copiar archivo SQLite directamente (solo SQLite)
                db_destino = Path(settings.DATABASES['default']['NAME'])
                shutil.copy2(str(tmp / 'db.sqlite3'), str(db_destino))
        except Exception as e:
            messages.error(request, f'Error al restaurar la base de datos: {e}')
            return redirect('backup')

        # 3. Restaurar archivos media
        if (tmp / 'media').exists():
            try:
                if settings.MEDIA_ROOT.exists():
                    shutil.rmtree(str(settings.MEDIA_ROOT))
                shutil.copytree(str(tmp / 'media'), str(settings.MEDIA_ROOT))
            except Exception as e:
                messages.error(request, f'Error al restaurar archivos: {e}')
                return redirect('backup')

        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
        auditar(request, "RESTAURAR", "Sistema", None,
                f"Restauración desde {archivo.name}", f"Realizada el {timestamp}")

        messages.success(request, 'Respaldo restaurado exitosamente. La base de datos y los archivos han sido recuperados.')
        return redirect('backup')



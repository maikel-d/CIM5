import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import FileField, ImageField
from django.apps import apps


class Command(BaseCommand):
    help = "Detecta y opcionalmente elimina archivos huerfanos en MEDIA_ROOT"

    def add_arguments(self, parser):
        parser.add_argument(
            '--eliminar',
            action='store_true',
            dest='eliminar',
            help='Elimina los archivos huerfanos del disco',
        )
        parser.add_argument(
            '--solo-bd',
            action='store_true',
            dest='solo_bd',
            help='Muestra solo registros en BD cuyo archivo no existe en disco',
        )

    def handle(self, *args, **options):
        media_root = settings.MEDIA_ROOT
        dry_run = not options['eliminar']
        solo_bd = options['solo_bd']

        if not media_root.exists():
            self.stdout.write(self.style.WARNING(
                "El directorio {} no existe.".format(media_root)))
            return

        # ---- 1. Collect all paths referenced in the database ----
        referenced = set()
        model_fields = []

        for model in apps.get_models():
            for field in model._meta.get_fields():
                if isinstance(field, (FileField, ImageField)):
                    model_fields.append((model, field))

        for model, field in model_fields:
            try:
                for instance in model.objects.all():
                    f = getattr(instance, field.name)
                    if f and f.name:
                        ref = f.name.replace('\\', '/')
                        referenced.add(ref)
            except Exception as e:
                self.stdout.write(self.style.WARNING(
                    "  [!] Error leyendo {}.{}: {}".format(
                        model.__name__, field.name, e)))

        self.stdout.write(self.style.SUCCESS(
            "\n[OK] Archivos referenciados en BD: {}".format(len(referenced))))

        # ---- 2. Scan disk for orphan files ----
        orphan_files = []
        total_size = 0
        file_count = 0

        for root, dirs, files in os.walk(str(media_root)):
            for fname in files:
                full_path = Path(root) / fname
                rel_path = str(full_path.relative_to(media_root)).replace('\\', '/')
                file_count += 1

                if rel_path not in referenced:
                    size = full_path.stat().st_size
                    orphan_files.append((rel_path, size))
                    total_size += size

        # ---- 3. Report orphan files on disk ----
        if not solo_bd:
            self._report_orphan_files(orphan_files, total_size,
                                      file_count, dry_run)

        # ---- 4. Report DB records pointing to missing files ----
        self._report_missing_in_db(model_fields, media_root)

        # ---- 5. Delete if requested ----
        if orphan_files and not dry_run and not solo_bd:
            deleted_count = 0
            for rel_path, size in orphan_files:
                full = media_root / rel_path
                try:
                    full.unlink()
                    deleted_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        "  [X] Error al eliminar {}: {}".format(rel_path, e)))
            self.stdout.write(self.style.SUCCESS(
                "\n[OK] {} archivos eliminados del disco.".format(deleted_count)))

            # Clean up empty directories
            for root, dirs, files in os.walk(str(media_root), topdown=False):
                if root == str(media_root):
                    continue
                try:
                    if not os.listdir(root):
                        os.rmdir(root)
                        rel = Path(root).relative_to(media_root)
                        self.stdout.write(
                            "  [-] Directorio vacio eliminado: {}".format(rel))
                except OSError:
                    pass

            self.stdout.write(self.style.SUCCESS("[OK] Limpieza completada."))
        elif dry_run and orphan_files and not solo_bd:
            self.stdout.write(self.style.WARNING(
                "\n[Sugerencia] Ejecuta 'python manage.py"
                " limpiar_archivos_huerfanos --eliminar'"
                " para borrar estos archivos."))

    def _report_orphan_files(self, orphan_files, total_size,
                              file_count, dry_run):
        self.stdout.write("\nArchivos en disco: {}".format(file_count))

        if not orphan_files:
            self.stdout.write(self.style.SUCCESS(
                "\n[OK] No hay archivos huerfanos. Todo en orden."))
            return

        self.stdout.write(self.style.WARNING(
            "\n[!] Archivos HUERFANOS encontrados: {}".format(
                len(orphan_files))))
        self._print_size(total_size)
        self.stdout.write("")

        by_dir = {}
        for rel_path, size in orphan_files:
            dirname = os.path.dirname(rel_path) or '(raiz)'
            by_dir.setdefault(dirname, []).append((rel_path, size))

        for dirname in sorted(by_dir.keys()):
            dir_size = sum(s for _, s in by_dir[dirname])
            self.stdout.write("  {}/".format(dirname))
            for rel_path, size in sorted(by_dir[dirname]):
                fname = os.path.basename(rel_path)
                self.stdout.write(
                    "    {:<50s} {:>8s}".format(fname, self._format_size(size)))
            self.stdout.write("    {} {}".format('-' * 50, '-' * 8))
            self.stdout.write(
                "    {:<50s} {:>8s}".format('Total',
                                            self._format_size(dir_size)))
            self.stdout.write("")

        accion = " (SIMULACION - no se borraron)" if dry_run else ""
        self.stdout.write(self.style.WARNING(
            "Total: {} archivos huerfanos{}".format(len(orphan_files), accion)))

    def _report_missing_in_db(self, model_fields, media_root):
        missing = []
        for model, field in model_fields:
            try:
                for instance in model.objects.all():
                    f = getattr(instance, field.name)
                    if f and f.name:
                        full_path = media_root / f.name
                        if not full_path.exists():
                            missing.append((
                                model.__name__, instance.pk,
                                field.name, f.name))
            except Exception:
                pass

        if missing:
            self.stdout.write(self.style.WARNING(
                "\n[!] Registros en BD con archivo faltante en disco: {}"
                .format(len(missing))))
            for model_name, pk, field_name, path in sorted(missing):
                self.stdout.write(
                    "  {:<25s} ID:{:<5} {:<15s} {}".format(
                        model_name, pk, field_name, path))
        else:
            self.stdout.write(self.style.SUCCESS(
                "[OK] Todos los registros en BD tienen su archivo en disco."))

    def _print_size(self, bytes_val):
        self.stdout.write(
            "  Espacio ocupado: {}".format(self._format_size(bytes_val)))

    def _format_size(self, bytes_val):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_val < 1024:
                return '{:.1f} {}'.format(bytes_val, unit)
            bytes_val /= 1024
        return '{:.1f} TB'.format(bytes_val)

"""Healthcheck command para Docker."""
import sys
from django.core.management.base import BaseCommand
from django.db import connections, DEFAULT_DB_ALIAS
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = "Verifica que la app este saludable (imports, BD, migraciones)"

    def handle(self, *args, **options):
        errores = []

        # 1. Verificar imports de modelos criticos
        modelos = [
            'CarpetaBien', 'Bien', 'Personal', 'Caso',
            'Investigado', 'TicketSoporte', 'Tarea',
            'Notificacion', 'InformeDiario', 'AuditLog',
        ]
        for m in modelos:
            try:
                __import__('direccion.models', fromlist=[m])
                getattr(sys.modules['direccion.models'], m)
            except (ImportError, AttributeError) as e:
                errores.append(f"Modelo {m}: {e}")

        # 2. Verificar conexion a BD
        try:
            conn = connections[DEFAULT_DB_ALIAS]
            conn.ensure_connection()
            conn.close()
        except OperationalError as e:
            errores.append(f"BD: {e}")
        except Exception as e:
            errores.append(f"BD (otro): {e}")

        # 3. Verificar migraciones pendientes
        try:
            from io import StringIO
            from django.core.management import call_command
            out = StringIO()
            call_command('showmigrations', '--plan', stdout=out)
            res = out.getvalue()
            if '[ ]' in res:
                count = res.count('[ ]')
                errores.append(f"{count} migracion(es) pendiente(s)")
        except Exception as e:
            errores.append(f"Migrations: {e}")

        if errores:
            for e in errores:
                self.stdout.write(self.style.ERROR(f"  - {e}"))
            raise SystemExit(1)
        else:
            self.stdout.write(self.style.SUCCESS("HEALTHCHECK OK"))

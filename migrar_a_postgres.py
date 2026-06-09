#!/usr/bin/env python
"""
  migrar_a_postgres.py
  Migra datos de SQLite a PostgreSQL para Docker
"""
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
json_path = sys.argv[1] if len(sys.argv) > 1 else 'respaldo_migracion.json'
import django
django.setup()
from django.conf import settings
from django.core.management import call_command
engine = settings.DATABASES['default']['ENGINE']
if 'postgresql' not in engine:
    print(f"ERROR: Motor {engine} no es PostgreSQL")
    sys.exit(1)
if not os.path.exists(json_path):
    print(f"ERROR: No existe {json_path}")
    sys.exit(1)
print("Migrando datos a PostgreSQL...")
call_command('flush', '--noinput', verbosity=0)
call_command('loaddata', json_path, verbosity=0)
from django.contrib.auth.models import User
admin = User.objects.filter(username='admin').first()
if admin:
    print(f"Admin activo: {admin.is_active}")
else:
    print("Admin no encontrado")
print(f"Usuarios: {User.objects.count()}")
print("Migracion completada. Usuario: admin / Contrasena: admin321")

#!/bin/bash
# ============================================
#   Entrypoint - Docker
#   Sistema de Gestión - Dirección General
# ============================================

set -e

echo "============================================"
echo "  Sistema de Gestión - Dirección General"
echo "============================================"
echo ""

# Esperar a que PostgreSQL esté disponible (si se usa)
if [ "$DB_ENGINE" = "django.db.backends.postgresql" ]; then
    echo "[*] Esperando a PostgreSQL..."
    until python -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(
        dbname=os.environ.get('DB_NAME', 'direccion'),
        user=os.environ.get('DB_USER', 'direccion'),
        password=os.environ.get('DB_PASSWORD', 'direccion'),
        host=os.environ.get('DB_HOST', 'db'),
        port=os.environ.get('DB_PORT', '5432'),
    )
    conn.close()
    print('[OK] PostgreSQL listo')
    exit(0)
except Exception as e:
    print(f'  Esperando... {e}')
    exit(1)
" 2>&1; do
        sleep 2
    done
    echo "[OK] PostgreSQL disponible"
fi

# Migraciones
echo "[*] Ejecutando migraciones..."
python manage.py migrate --noinput
echo "[OK] Migraciones aplicadas"

# Static files
echo ""
echo "[*] Recopilando archivos estáticos..."
python manage.py collectstatic --noinput
echo "[OK] Archivos estáticos recopilados"

# Superusuario por defecto (solo si no existe)
echo ""
echo "[*] Verificando superusuario..."
python setup_admin.py

# Mostrar información
echo ""
echo "============================================"
echo "  Servidor listo en http://0.0.0.0:8000"
echo "============================================"
echo ""

# Iniciar Gunicorn
exec gunicorn core.wsgi:application     --bind 0.0.0.0:8000     --workers ${GUNICORN_WORKERS:-4}     --timeout ${GUNICORN_TIMEOUT:-120}     --access-logfile -     --error-logfile -     --log-level ${GUNICORN_LOG_LEVEL:-info}

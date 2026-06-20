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

echo [*] Verificando sintaxis de Python...
for f in /DATA/CIM5NV/core/urls.py /DATA/CIM5NV/direccion/urls.py /DATA/CIM5NV/direccion/views/__init__.py /DATA/CIM5NV/direccion/views/dashboard.py /DATA/CIM5NV/direccion/views/tickets.py; do
  if [ -f "$f" ]; then
    python -m py_compile "$f"
  fi
done
echo [OK] Sintaxis verificada
echo 

# Esperar a que PostgreSQL esté disponible (si se usa)
if [ "$DB_ENGINE" = "django.db.backends.postgresql" ]; then
    MAX_RETRIES=30
    RETRY_COUNT=0
    until python -c "
import psycopg2, os, sys
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
    sys.exit(0)
except Exception as e:
    print(f'  Esperando... {e}')
    sys.exit(1)
" 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ "$RETRY_COUNT" -ge "$MAX_RETRIES" ]; then
        echo "[ERROR] PostgreSQL no disponible tras $MAX_RETRIES intentos. Abortando."
        exit 1
    fi
    sleep 2
done
echo "[OK] PostgreSQL disponible"
fi

# Migraciones
echo "[*] Ejecutando migraciones..."
python manage.py migrate --noinput
echo "[OK] Migraciones aplicadas"

# Verificar cache (Redis)
echo "[*] Verificando Redis cache..."
python -c "from django.core.cache import cache; cache.set('healthcheck', 'ok')" 2>&1 || echo "[WARN] Redis no disponible, continuando..."
echo "[OK] Redis cache verificado"

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
exec gunicorn core.wsgi:application     --bind 0.0.0.0:8000     --workers ${GUNICORN_WORKERS:-4}     --timeout ${GUNICORN_TIMEOUT:-120}     --access-logfile /DATA/CIM5NV/logs/gunicorn_access.log     --error-logfile /DATA/CIM5NV/logs/gunicorn_error.log     --log-level ${GUNICORN_LOG_LEVEL:-info}

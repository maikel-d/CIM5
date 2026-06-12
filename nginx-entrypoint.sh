#!/bin/sh
# ============================================
#   Entrypoint - Nginx
#   Sistema de Gestión - Dirección General
#   Con Cloudflare Tunnel, nginx siempre sirve
#   en HTTP (puerto 80) para el túnel, y HTTPS
#   local (puerto 443) para acceso interno.
# ============================================

set -e

TEMPLATE=/etc/nginx/templates/default.conf.template
OUTPUT=/etc/nginx/conf.d/default.conf

mkdir -p /etc/nginx/templates 2>/dev/null || true

if [ ! -f "$TEMPLATE" ]; then
    echo "[nginx-entrypoint] ERROR: No se encuentra $TEMPLATE"
    exit 1
fi

# Copiar plantilla directamente (sin toggle de modos)
cp "$TEMPLATE" "$OUTPUT"

echo "[nginx-entrypoint] Configuracion escrita en $OUTPUT"
echo "[nginx-entrypoint] Iniciando nginx..."
exec nginx -g 'daemon off;'

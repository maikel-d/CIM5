#!/bin/sh
# ============================================
#   Entrypoint - Nginx
#   Sistema de Gestión - Dirección General
#   Activa/desactiva el redirect HTTP->HTTPS
#   según la variable DOMAIN.
#
#   NOTA: La plantilla se monta en /etc/nginx/templates/
#   (NO en conf.d/), así que podemos escribir el archivo
#   final en conf.d/ sin problemas de bind mounts.
# ============================================

set -e

# Leer plantilla desde /etc/nginx/templates (bind mount, solo lectura)
TEMPLATE=/etc/nginx/templates/default.conf.template
OUTPUT=/etc/nginx/conf.d/default.conf

if [ ! -f "$TEMPLATE" ]; then
    echo "[nginx-entrypoint] ERROR: No se encuentra $TEMPLATE"
    exit 1
fi

if [ -z "$DOMAIN" ]; then
    echo "[nginx-entrypoint] DOMAIN vacio -> modo HTTP directo"
    # Mantener bloque HTTP_ONLY, eliminar SSL_MODE + marcadores
    sed '/@SSL_MODE@/,/@END_SSL_MODE@/d' "$TEMPLATE" \
      | sed '/@HTTP_ONLY@/d; /@END_HTTP_ONLY@/d' \
      > "$OUTPUT"
else
    echo "[nginx-entrypoint] DOMAIN=$DOMAIN -> modo SSL (redirect HTTP->HTTPS)"
    # Mantener bloque SSL_MODE, eliminar HTTP_ONLY + marcadores
    sed '/@HTTP_ONLY@/,/@END_HTTP_ONLY@/d' "$TEMPLATE" \
      | sed '/@SSL_MODE@/d; /@END_SSL_MODE@/d' \
      > "$OUTPUT"
fi

echo "[nginx-entrypoint] Configuracion escrita en $OUTPUT"
echo "[nginx-entrypoint] Iniciando nginx..."
exec nginx -g 'daemon off;'

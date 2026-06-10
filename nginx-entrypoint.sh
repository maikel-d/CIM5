#!/bin/sh
# ============================================
#   Entrypoint - Nginx
#   Sistema de Gestión - Dirección General
#   Activa/desactiva el redirect HTTP->HTTPS
#   según la variable DOMAIN.
#
#   NOTA: No usar sed -i porque falla con bind
#   mounts en overlay2 (rename() no soportado).
#   En su lugar: copiar a /tmp, sed sin -i, cp.
# ============================================

set -e

# Copiar la plantilla a /tmp (evita problemas con bind mounts)
cp /etc/nginx/conf.d/default.conf /tmp/default.conf

if [ -z "$DOMAIN" ]; then
    echo "[nginx-entrypoint] DOMAIN vacio -> modo HTTP directo"
    # Mantener bloque HTTP_ONLY, eliminar SSL_MODE + marcadores
    sed '/@SSL_MODE@/,/@END_SSL_MODE@/d' /tmp/default.conf \
      | sed '/@HTTP_ONLY@/d; /@END_HTTP_ONLY@/d' \
      > /tmp/clean.conf
else
    echo "[nginx-entrypoint] DOMAIN=$DOMAIN -> modo SSL (redirect HTTP->HTTPS)"
    # Mantener bloque SSL_MODE, eliminar HTTP_ONLY + marcadores
    sed '/@HTTP_ONLY@/,/@END_HTTP_ONLY@/d' /tmp/default.conf \
      | sed '/@SSL_MODE@/d; /@END_SSL_MODE@/d' \
      > /tmp/clean.conf
fi

# Copiar resultado al bind mount (cp usa open/write, no rename)
cp /tmp/clean.conf /etc/nginx/conf.d/default.conf

echo "[nginx-entrypoint] Iniciando nginx..."
exec nginx -g 'daemon off;'

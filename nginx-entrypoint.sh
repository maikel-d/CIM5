#!/bin/sh
# ============================================
#   Entrypoint - Nginx
#   Sistema de Gesti\u00f3n - Direcci\u00f3n General
#   Activa/desactiva el redirect HTTP->HTTPS
#   seg\u00fan la variable DOMAIN.
# ============================================

set -e

# Si DOMAIN est\u00e1 vac\u00edo -> modo HTTP directo (sin SSL)
# Si DOMAIN tiene valor -> modo SSL (con redirect HTTP->HTTPS)
if [ -z "$DOMAIN" ]; then
    # Modo HTTP: eliminar el bloque SSL_MODE
    echo "[nginx-entrypoint] DOMAIN vac\u00edo -> modo HTTP directo"
    sed -i '/@SSL_MODE@/,/@END_SSL_MODE@/d' /etc/nginx/conf.d/default.conf
    sed -i '/@HTTP_ONLY@/d; /@END_HTTP_ONLY@/d' /etc/nginx/conf.d/default.conf
else
    # Modo SSL: eliminar el bloque HTTP_ONLY
    echo "[nginx-entrypoint] DOMAIN=$DOMAIN -> modo SSL (redirect HTTP->HTTPS)"
    sed -i '/@HTTP_ONLY@/,/@END_HTTP_ONLY@/d' /etc/nginx/conf.d/default.conf
    sed -i '/@SSL_MODE@/d; /@END_SSL_MODE@/d' /etc/nginx/conf.d/default.conf
fi

echo "[nginx-entrypoint] Iniciando nginx..."
exec nginx -g 'daemon off;'

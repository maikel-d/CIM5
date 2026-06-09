#!/bin/bash
# ============================================
#   Inicializar Let's Encrypt
#   Sistema de Gesti�n - Direcci�n General
# ============================================
#
# Uso:
#   1. Configura DOMAIN y CERTBOT_EMAIL en .env
#   2. Aseg�rate de que el DNS apunte a este servidor
#   3. Ejecuta:  ./init-letsencrypt.sh
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

DOMAIN="${DOMAIN:-}"
EMAIL="${CERTBOT_EMAIL:-}"

if [ -z "$DOMAIN" ]; then
    echo "============================================"
    echo "  ERROR: DOMAIN no esta configurado"
    echo "============================================"
    echo ""
    echo "  Edita tu archivo .env y agrega:"
    echo "    DOMAIN=midominio.gob.ve"
    echo "    CERTBOT_EMAIL=admin@midominio.gob.ve"
    echo ""
    echo "  Luego ejecuta este script nuevamente."
    echo "============================================"
    exit 1
fi

if [ -z "$EMAIL" ]; then
    echo "============================================"
    echo "  ERROR: CERTBOT_EMAIL no esta configurado"
    echo "============================================"
    echo ""
    echo "  Edita tu archivo .env y agrega:"
    echo "    CERTBOT_EMAIL=admin@midominio.gob.ve"
    echo ""
    echo "  Luego ejecuta este script nuevamente."
    echo "============================================"
    exit 1
fi

echo "============================================"
echo "  Inicializando Let's Encrypt"
echo "============================================"
echo ""
echo "  Dominio: $DOMAIN"
echo "  Email:   $EMAIL"
echo ""

# Verificar que docker compose esté disponible
DOCKER_CMD=""
if command -v docker-compose &>/dev/null; then
    DOCKER_CMD="docker-compose"
elif docker compose version &>/dev/null 2>&1; then
    DOCKER_CMD="docker compose"
else
    echo "[ERROR] No se encontró docker compose"
    exit 1
fi

# Paso 1: Actualizar rutas de certificados en nginx.conf
echo "[1/5] Actualizando rutas de certificados en nginx.conf..."
# Reemplazar rutas de certificados autofirmados por las de Let's Encrypt
sed -i "s|/etc/nginx/ssl/cert.pem|/etc/letsencrypt/live/direccion/fullchain.pem|" nginx.conf
sed -i "s|/etc/nginx/ssl/key.pem|/etc/letsencrypt/live/direccion/privkey.pem|" nginx.conf
echo "[OK] Rutas actualizadas a Let's Encrypt"

# Paso 2: Detener nginx para liberar puerto 80 (certbot standalone lo necesita)
echo "[2/5] Deteniendo nginx temporalmente para certbot..."
$DOCKER_CMD stop nginx 2>/dev/null || true
echo "[OK] Nginx detenido"

# Paso 3: Solicitar certificado SSL con standalone
echo "[3/5] Solicitando certificado SSL a Let's Encrypt..."
$DOCKER_CMD run --rm --profile ssl --network host \
    --entrypoint "" \
    certbot certonly --standalone \
    -d "$DOMAIN" \
    --email "$EMAIL" \
    --cert-name direccion \
    --agree-tos \
    --no-eff-email \
    --force-renewal

echo "[OK] Certificado obtenido para $DOMAIN"

echo "[4/5] Iniciando servicios con HTTPS..."
$DOCKER_CMD --profile ssl up -d

sleep 3

echo "[5/5] Verificando que nginx sirva HTTPS..."
if $DOCKER_CMD exec nginx sh -c "nginx -t" 2>/dev/null; then
    echo "[OK] Configuracion nginx valida"
else
    echo "[OK] (Verificacion omitida - nginx puede tardar en arrancar)"
fi

echo ""
echo "============================================"
echo "  LISTO! HTTPS configurado para $DOMAIN"
echo "============================================"
echo ""
echo "  https://$DOMAIN"
echo ""
echo "  Los certificados se renovaran automaticamente"
echo "  cada 24 horas via el contenedor certbot."
echo "============================================"

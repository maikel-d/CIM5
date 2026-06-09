#!/bin/bash
# ============================================
#   configurar_ssl_local.sh
#   HTTPS con certificado autofirmado
#   Sistema de Gestión - Dirección General
# ============================================
#
# Configura HTTPS en la red local usando un
# certificado SSL autofirmado para la IP del
# servidor.
#
# Uso:
#   ./configurar_ssl_local.sh
#   docker compose up -d
#
# ============================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Cargar .env si existe
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Detectar IP local del servidor
DETECTED_IP=""
if command -v ip &>/dev/null; then
    DETECTED_IP=$(ip -4 addr show 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v 127.0.0.1 | head -1)
fi
if [ -z "$DETECTED_IP" ] && command -v hostname &>/dev/null; then
    DETECTED_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
fi
if [ -z "$DETECTED_IP" ]; then
    DETECTED_IP="192.168.0.101"
fi

SSL_IP="${SERVER_IP:-$DETECTED_IP}"
SSL_DIR="$SCRIPT_DIR/ssl"

mkdir -p "$SSL_DIR"

echo "============================================"
echo "  Configurar HTTPS Local (Autofirmado)"
echo "============================================"
echo ""
echo "  IP del servidor: $SSL_IP"
echo ""

# ============================================
#   Paso 1: Generar certificado autofirmado
# ============================================
echo "[1/4] Generando certificado SSL autofirmado..."

# Crear archivo de configuración de OpenSSL para SAN (IP válida)
cat > "$SSL_DIR/openssl.cnf" << EOF
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no

[req_distinguished_name]
CN = $SSL_IP

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
IP.1 = $SSL_IP
IP.2 = 127.0.0.1
EOF

# Generar clave privada y certificado autofirmado (válido por 10 años)
openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
    -keyout "$SSL_DIR/key.pem" \
    -out "$SSL_DIR/cert.pem" \
    -config "$SSL_DIR/openssl.cnf" \
    2>>"$SCRIPT_DIR/logs/ssl_setup.log"

# Verificar que se generaron
if [ ! -f "$SSL_DIR/cert.pem" ] || [ ! -f "$SSL_DIR/key.pem" ]; then
    echo "[ERROR] Falló la generación del certificado"
    exit 1
fi

# Permisos seguros
chmod 644 "$SSL_DIR/cert.pem"
chmod 600 "$SSL_DIR/key.pem"

echo "[OK] Certificado generado: ssl/cert.pem, ssl/key.pem"

# ============================================
#   Paso 2: Activar HTTPS en nginx.conf
# ============================================
echo "[2/4] Activando HTTPS en nginx.conf..."

# Verificar si el bloque HTTPS ya está activo (no comentado)
if grep -q 'listen 443 ssl;' nginx.conf; then
    echo "[OK] Bloque HTTPS ya está activo en nginx.conf"
else
    # Activar el bloque HTTPS (descomentar)
    sed -i '/^#server {$/,/HTTPS_SERVER/s/^#//' nginx.conf
    echo "[OK] Bloque HTTPS activado en nginx.conf"
fi

# ============================================
#   Paso 3: Configurar .env
# ============================================
echo "[3/4] Configurando variables de entorno..."

# DOMAIN (usar IP)
if grep -q '^DOMAIN=' .env; then
    sed -i "s|^DOMAIN=.*|DOMAIN=$SSL_IP|" .env
else
    echo "DOMAIN=$SSL_IP" >> .env
fi

# SECURE_SSL_REDIRECT
if grep -q '^SECURE_SSL_REDIRECT=' .env; then
    sed -i 's|^SECURE_SSL_REDIRECT=.*|SECURE_SSL_REDIRECT=True|' .env
else
    echo 'SECURE_SSL_REDIRECT=True' >> .env
fi

echo "[OK] Variables DOMAIN=$SSL_IP y SECURE_SSL_REDIRECT=True configuradas"

# ============================================
#   Paso 4: Información al usuario
# ============================================
echo ""
echo "============================================"
echo "  HTTPS LOCAL CONFIGURADO"
echo "============================================"
echo ""
echo "  Certificado autofirmado para: $SSL_IP"
echo "  Validez: 10 años"
echo ""
echo "  Para aplicar los cambios:"
echo "    docker compose up -d"
echo ""
echo "  Luego accede a:"
echo "    https://$SSL_IP"
echo ""
echo "  NOTA: El navegador mostrará una advertencia"
echo "  de seguridad por ser un certificado"
echo "  autofirmado. Es normal en redes locales."
echo "  Puedes aceptar la excepción de seguridad"
echo "  para continuar."
echo ""
echo "============================================"

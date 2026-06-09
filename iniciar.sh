#!/bin/bash
# ============================================
#   Sistema de Gestión - Dirección General
# ============================================

echo "============================================"
echo "  Sistema de Gestión - Dirección General"
echo "============================================"
echo ""

# Activar entorno virtual
if [ -d "venv" ]; then
    source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
    echo "[OK] Entorno virtual activado"
else
    echo "[*] Usando Python del sistema"
fi

echo ""
echo "[*] Ejecutando migraciones..."
python manage.py migrate 2>/dev/null
echo "[OK] Migraciones aplicadas"

echo ""
echo "[*] Verificando superusuario..."
python setup_admin.py

# Detectar IP local
IP=$(ip -4 addr show 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v 127.0.0.1 | head -1)
if [ -z "$IP" ]; then
    IP=$(hostname -I 2>/dev/null | awk '{print $1}')
fi
if [ -z "$IP" ]; then
    IP=$(ifconfig 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v 127.0.0.1 | head -1)
fi

echo ""
echo "============================================"
echo "  http://127.0.0.1:8000   -  Esta computadora"
if [ -n "$IP" ]; then
    echo "  http://$IP:8000       -  Red local"
fi
echo ""
echo "  Las credenciales del superusuario se"
echo "  mostraron al ejecutar la configuración."
echo ""
echo "  Si olvidaste la contraseña, ejecuta:"
echo "  python manage.py changepassword admin"
echo "============================================"

echo ""
python manage.py runserver 0.0.0.0:8000

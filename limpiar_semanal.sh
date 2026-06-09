#!/usr/bin/env bash
# ========================================
# Limpieza Semanal de Archivos Huerfanos
# Direccion General - Sistema de Gestion
# ========================================

cd "$(dirname "$0")"
LOG_DIR="logs"
LOG_FILE="$LOG_DIR/limpieza_$(date +%Y%m%d).log"

mkdir -p "$LOG_DIR"

echo "$(date) Iniciando limpieza de archivos huerfanos..." >> "$LOG_FILE"

./venv/bin/python manage.py limpiar_archivos_huerfanos --eliminar >> "$LOG_FILE" 2>&1

echo "$(date) Limpieza completada." >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

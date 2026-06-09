#!/bin/bash
# ============================================
#   backup_db.sh
#   Backup Automático - Sistema de Gestión
#   Realiza dump de PostgreSQL + respaldo de
#   archivos multimedia.
# ============================================
#
# Instalación como cron diario:
#   sudo ln -s "$(pwd)/backup_db.sh" /etc/cron.daily/backup-direccion
#   sudo chmod +x "$(pwd)/backup_db.sh"
#
# O manualmente:
#   crontab -e
#   # Agregar: 0 3 * * * /ruta/del/proyecto/backup_db.sh
#
# ============================================

set -euo pipefail

# ============================================
#   CONFIGURACIÓN
# ============================================

# Ruta base del proyecto
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Cargar variables de entorno del .env
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

# Directorio de backups (sobrescribir con BACKUP_DIR en .env)
BACKUP_DIR="${BACKUP_DIR:-$SCRIPT_DIR/backups}"

# Días de retención (sobrescribir con BACKUP_RETENTION_DAYS en .env)
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"

# Nombre de la base de datos
DB_NAME="${DB_NAME:-direccion}"
DB_USER="${DB_USER:-direccion}"

PROJECT_NAME="direccion"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

LOG_DIR="$SCRIPT_DIR/logs"
LOG_FILE="$LOG_DIR/backup_$(date +%Y%m%d).log"

# Detectar comando docker compose (compatible con docker-compose y docker compose)
DOCKER_CMD=""
if command -v docker-compose &>/dev/null; then
    DOCKER_CMD="docker-compose"
elif docker compose version &>/dev/null 2>&1; then
    DOCKER_CMD="docker compose"
else
    echo "[ERROR] No se encontró docker-compose ni docker compose"
    exit 1
fi

# ============================================
#   FUNCIONES
# ============================================

log() {
    local level="$1"
    local message="$2"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $message" | tee -a "$LOG_FILE"
}

cleanup_old_backups() {
    log "INFO" "Limpiando backups anteriores a $RETENTION_DAYS días..."
    local deleted=0

    if [ -d "$BACKUP_DIR/db" ]; then
        local count=$(find "$BACKUP_DIR/db" -name "${PROJECT_NAME}_db_*.sql.gz" -type f -mtime "+$RETENTION_DAYS" -delete -print 2>/dev/null | wc -l)
        deleted=$((deleted + count))
    fi

    if [ -d "$BACKUP_DIR/media" ]; then
        local count=$(find "$BACKUP_DIR/media" -name "${PROJECT_NAME}_media_*.tar.gz" -type f -mtime "+$RETENTION_DAYS" -delete -print 2>/dev/null | wc -l)
        deleted=$((deleted + count))
    fi

    log "INFO" "Backups eliminados: $deleted"
}

backup_database() {
    log "INFO" "Iniciando backup de base de datos..."

    local backup_path="$BACKUP_DIR/db"
    mkdir -p "$backup_path"

    local filename="${PROJECT_NAME}_db_${TIMESTAMP}.sql.gz"
    local filepath="$backup_path/$filename"

    if ! $DOCKER_CMD ps db 2>/dev/null | grep -q "Up"; then
        log "ERROR" "El contenedor de base de datos no está corriendo"
        return 1
    fi

    log "INFO" "Ejecutando pg_dump de la base '$DB_NAME'..."
    if $DOCKER_CMD exec -T db pg_dump -U "$DB_USER" "$DB_NAME" 2>>"$LOG_FILE" | gzip > "$filepath"; then
        local size=$(du -h "$filepath" | cut -f1)
        log "OK" "Backup de BD completado: $filepath ($size)"
    else
        log "ERROR" "Falló el backup de base de datos"
        rm -f "$filepath"
        return 1
    fi
}

backup_media() {
    log "INFO" "Iniciando backup de archivos multimedia..."

    local backup_path="$BACKUP_DIR/media"
    mkdir -p "$backup_path"

    local filename="${PROJECT_NAME}_media_${TIMESTAMP}.tar.gz"
    local filepath="$backup_path/$filename"

    if ! $DOCKER_CMD ps app 2>/dev/null | grep -q "Up"; then
        log "WARN" "El contenedor app no está corriendo, se omite backup de media"
        return 0
    fi

    log "INFO" "Comprimiendo archivos multimedia del contenedor..."
    if $DOCKER_CMD exec -T app tar czf - -C /DATA/CIM5NV/media . 2>>"$LOG_FILE" > "$filepath"; then
        local size=$(du -h "$filepath" | cut -f1)
        log "OK" "Backup de media completado: $filepath ($size)"
    else
        log "WARN" "Falló el backup de media (puede no haber archivos)"
        rm -f "$filepath"
        return 0
    fi
}

# ============================================
#   EJECUCIÓN PRINCIPAL
# ============================================

mkdir -p "$BACKUP_DIR/db" "$BACKUP_DIR/media" "$LOG_DIR"

log "INFO" "=== INICIO BACKUP: $PROJECT_NAME ==="
log "INFO" "Directorio de backups: $BACKUP_DIR"
log "INFO" "Retención: $RETENTION_DAYS días"

backup_database
DB_STATUS=$?

backup_media
MEDIA_STATUS=$?

cleanup_old_backups

log "INFO" "=== BACKUP FINALIZADO ==="

[ $DB_STATUS -eq 0 ] && log "OK" "Base de datos: OK" || log "ERROR" "Base de datos: FALLÓ"
[ $MEDIA_STATUS -eq 0 ] && log "OK" "Multimedia: OK" || log "WARN" "Multimedia: Con errores (ver logs)"

log "INFO" "Espacio usado en backups:"
du -sh "$BACKUP_DIR" 2>/dev/null | tee -a "$LOG_FILE"

log "INFO" "Últimos backups:"
ls -lh "$BACKUP_DIR/db" "$BACKUP_DIR/media" 2>/dev/null | tee -a "$LOG_FILE"

log "INFO" "=== FIN BACKUP ==="
echo "" >> "$LOG_FILE"

exit $((DB_STATUS != 0))

#!/bin/bash
# ============================================
#   direccion-automation.sh
#   Automatizacion diaria - Direccion General
#   Backup COMPLETO: PostgreSQL + codigo + volumenes Docker
# ============================================
set -e

LOG_FILE="/DATA/CIM5NV/scripts/automation.log"
DATE=$(date "+%Y-%m-%d %H:%M:%S")
DATE_STAMP=$(date +%Y-%m-%d)
RCLONE_DIR="drive:/CIM5-Backups"
TARBALL="/tmp/backup_completo_$DATE_STAMP.tar.gz"
BACKUP_DIR="/tmp/backup_temp_$DATE_STAMP"
MAX_BACKUPS=3
VOLUMES=("media_data" "static_data")

echo "" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"
echo "[$DATE] INICIO" >> "$LOG_FILE"

cd /DATA/CIM5NV

# ---- Tarea 1: Backup completo ----
if [[ "$1" == "git-push" || -z "$1" ]]; then
    echo "[$DATE] [1/5] Backup completo (PostgreSQL + codigo + volumenes)..." >> "$LOG_FILE"

    mkdir -p "$BACKUP_DIR"

    # 1a. Dump completo de PostgreSQL
    echo "[$DATE] 1a. Dump PostgreSQL..." >> "$LOG_FILE"
    docker exec direccion-db pg_dump -U direccion direccion --no-owner --no-acl > "$BACKUP_DIR/base_de_datos.sql" 2>>"$LOG_FILE"
    PG_SIZE=$(wc -c < "$BACKUP_DIR/base_de_datos.sql" 2>/dev/null || echo 0)
    echo "[$DATE] PostgreSQL dump: $(numfmt --to=iec $PG_SIZE 2>/dev/null || echo ${PG_SIZE}B)" >> "$LOG_FILE"

    # 1b. Copiar el codigo del proyecto
    echo "[$DATE] 1b. Copiando codigo del proyecto..." >> "$LOG_FILE"
    mkdir -p "$BACKUP_DIR/proyecto"
    rsync -a --exclude=".git" --exclude="__pycache__" --exclude="*.pyc" --exclude="*.pyo"         --exclude=".gitignore" --exclude="respaldos" --exclude="scripts/automation.log"         /DATA/CIM5NV/ "$BACKUP_DIR/proyecto/" 2>>"$LOG_FILE"

    # 1c. Backup de volumenes Docker
    echo "[$DATE] 1c. Backupeando volumenes Docker..." >> "$LOG_FILE"
    mkdir -p "$BACKUP_DIR/volumenes"
    for vol in "${VOLUMES[@]}"; do
        FULL_VOL="cim5nv_$vol"
        VOL_FILE="$BACKUP_DIR/volumenes/$vol.tar.gz"
        echo "[$DATE]     Volumen: $FULL_VOL" >> "$LOG_FILE"
        docker run --rm -v "$FULL_VOL:/source" alpine tar czf - -C /source . 2>>"$LOG_FILE" > "$VOL_FILE" ||             echo "[$DATE]     AVISO: Volumen $FULL_VOL vacio o no disponible" >> "$LOG_FILE"
        if [ -f "$VOL_FILE" ] && [ -s "$VOL_FILE" ]; then
            VOL_SIZE=$(wc -c < "$VOL_FILE" 2>/dev/null || echo 0)
            echo "[$DATE]     Backup OK: $(numfmt --to=iec $VOL_SIZE 2>/dev/null || echo ${VOL_SIZE}B)" >> "$LOG_FILE"
        fi
    done

    # 1d. Crear tarball comprimido
    echo "[$DATE] 1d. Comprimiendo backup..." >> "$LOG_FILE"
    cd /tmp
    tar czf "$TARBALL" -C /tmp "backup_temp_$DATE_STAMP" 2>>"$LOG_FILE"
    rm -rf "$BACKUP_DIR"
    cd /DATA/CIM5NV

    TAR_SIZE=$(stat -c%s "$TARBALL" 2>/dev/null || stat -f%z "$TARBALL" 2>/dev/null || echo 0)
    echo "[$DATE] Backup completo creado: $(numfmt --to=iec $TAR_SIZE 2>/dev/null || echo ${TAR_SIZE}B)" >> "$LOG_FILE"

    # ---- Tarea 2: Subir a Google Drive ----
    echo "[$DATE] [2/5] Subiendo backup a Google Drive..." >> "$LOG_FILE"

    if [ -f "$TARBALL" ] && [ -s "$TARBALL" ]; then
        rclone copyto "$TARBALL" "$RCLONE_DIR/backup_completo_$DATE_STAMP.tar.gz" >> "$LOG_FILE" 2>&1
        echo "[$DATE] Backup subido a Drive: backup_completo_$DATE_STAMP.tar.gz" >> "$LOG_FILE"
    else
        echo "[$DATE] ERROR: Archivo de backup vacio o no existe" >> "$LOG_FILE"
    fi

    # ---- Tarea 3: Rotar backups en Drive ----
    echo "[$DATE] [3/5] Rotando backups antiguos en Google Drive..." >> "$LOG_FILE"

    rclone ls "$RCLONE_DIR" 2>>"$LOG_FILE" | grep -oP "backup_completo_\d{4}-\d{2}-\d{2}\.tar\.gz" | sort > /tmp/backups_list.txt

    TOTAL=$(wc -l < /tmp/backups_list.txt 2>/dev/null || echo 0)
    TO_DELETE=$((TOTAL - MAX_BACKUPS))

    echo "[$DATE] Backups en Drive: $TOTAL, se eliminaran: $TO_DELETE" >> "$LOG_FILE"

    if [ "$TO_DELETE" -gt 0 ]; then
        head -n "$TO_DELETE" /tmp/backups_list.txt | while IFS= read -r file; do
            echo "[$DATE] Eliminando: $file" >> "$LOG_FILE"
            rclone deletefile "$RCLONE_DIR/$file" >> "$LOG_FILE" 2>&1
        done
    fi

    rm -f /tmp/backups_list.txt

    # ---- Tarea 4: Git commit + push ----
    echo "[$DATE] [4/5] Git commit + push..." >> "$LOG_FILE"

    git add -A 2>>"$LOG_FILE"

    if ! git diff --cached --quiet 2>>"$LOG_FILE"; then
        git commit -m "auto: cambios $DATE_STAMP" >> "$LOG_FILE" 2>&1
        git push origin main >> "$LOG_FILE" 2>&1
        echo "[$DATE] Git push completado" >> "$LOG_FILE"
    else
        echo "[$DATE] Sin cambios nuevos, no se creo commit" >> "$LOG_FILE"
    fi

    # Limpiar tarball temporal
    rm -f "$TARBALL"
fi

# ---- Tarea 5: Reiniciar contenedores ----
if [[ "$1" == "restart" || -z "$1" ]]; then
    echo "[$DATE] [5/5] Reiniciando contenedores Docker..." >> "$LOG_FILE"
    docker compose -f /DATA/CIM5NV/docker-compose.yml restart >> "$LOG_FILE" 2>&1
    echo "[$DATE] Contenedores reiniciados" >> "$LOG_FILE"
fi

echo "[$DATE] FIN" >> "$LOG_FILE"

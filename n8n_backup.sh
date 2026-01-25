#!/usr/bin/env bash
set -euo pipefail

# ========================
# CONFIG — adjust as needed
# ========================

PROJECT_NAME="n8n"
PROJECT_ROOT_DIR="/containers/n8n_deployer"
BACKUP_ROOT="/containers/n8n_deployer/backups"
RETENTION_DAYS=14

# Docker service/container names
POSTGRES_CONTAINER="n8n_db"
N8N_VOLUME="n8n_storage"
POSTGRES_VOLUME="db_storage"

# Postgres creds (should match .env)
POSTGRES_DB="n8n_db"
POSTGRES_USER="postgres"

# ========================
# RUNTIME VARS
# ========================

DATE="$(date +%F_%H-%M-%S)"
DB_BACKUP_DIR="$BACKUP_ROOT/db"
VOL_BACKUP_DIR="$BACKUP_ROOT/volumes"
LOG_DIR="$BACKUP_ROOT/logs"

mkdir -p "$DB_BACKUP_DIR" "$VOL_BACKUP_DIR" "$LOG_DIR"

LOG_FILE="$LOG_DIR/backup-$DATE.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "=== n8n backup started at $(date) ==="

# ========================
# 1️⃣ DATABASE BACKUP
# ========================

echo "--- Backing up Postgres database ---"

docker exec "$POSTGRES_CONTAINER" \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" \
  | gzip > "$DB_BACKUP_DIR/n8n-db-$DATE.sql.gz"

echo "Database backup complete"

# ========================
# 2️⃣ VOLUME BACKUPS
# ========================

backup_volume () {
  local VOLUME_NAME="$1"
  local OUT_FILE="$VOL_BACKUP_DIR/${VOLUME_NAME}-${DATE}.tar.gz"

  echo "--- Backing up volume: $VOLUME_NAME ---"

  docker run --rm \
    -v "${VOLUME_NAME}:/volume:ro" \
    -v "${VOL_BACKUP_DIR}:/backup" \
    alpine \
    tar czf "/backup/$(basename "$OUT_FILE")" -C /volume .

  echo "Volume $VOLUME_NAME backup complete"
}

backup_volume "$N8N_VOLUME"
backup_volume "$POSTGRES_VOLUME"

# ========================
# 3️⃣ ENV FILE BACKUP
# ========================

if [[ -f "$PROJECT_ROOT_DIR/.env" ]]; then
  echo "--- Backing up .env file ---"
  cp "$PROJECT_ROOT_DIR/.env" "$BACKUP_ROOT/.env-$DATE"
fi

# ========================
# 4️⃣ ROTATION / CLEANUP
# ========================

echo "--- Cleaning up old backups (>${RETENTION_DAYS} days) ---

find "$BACKUP_ROOT" -type f -mtime +"$RETENTION_DAYS" -delete

echo "Cleanup complete"

echo "=== n8n backup finished at $(date) ==="

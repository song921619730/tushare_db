#!/bin/bash
# Backup ClickHouse tushare database using native BACKUP command.
# Requires ClickHouse 22.8+.
#
# Usage:
#   ./backup_clickhouse.sh                    # defaults to /backups dir
#   BACKUP_DIR=/tmp/backups ./backup_clickhouse.sh
#   RETENTION_DAYS=7 ./backup_clickhouse.sh   # override retention

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
BACKUP_NAME="tushare_$(date +%Y%m%d_%H%M%S).zip"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"

echo "=== ClickHouse Backup ==="
echo "Backup name: $BACKUP_NAME"
echo "Backup dir: $BACKUP_DIR"

# Create backup directory on host
mkdir -p "$BACKUP_DIR"

# Trigger ClickHouse native backup
docker compose -f "$COMPOSE_FILE" exec -T clickhouse clickhouse-client --query "
BACKUP DATABASE tushare TO Disk('backups', '$BACKUP_NAME')
"

# Copy backup from container to host
docker compose -f "$COMPOSE_FILE" cp \
  clickhouse:/var/lib/clickhouse/backups/"$BACKUP_NAME" \
  "$BACKUP_DIR/$BACKUP_NAME"

BACKUP_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_NAME" | cut -f1)
echo "Backup saved: $BACKUP_DIR/$BACKUP_NAME ($BACKUP_SIZE)"

# Cleanup old backups
echo "Removing backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "tushare_*.zip" -mtime +"$RETENTION_DAYS" -delete

# List remaining backups
echo "Remaining backups:"
ls -lh "$BACKUP_DIR"/tushare_*.zip 2>/dev/null || echo "  (none)"

echo "=== Backup complete ==="

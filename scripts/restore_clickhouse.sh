#!/bin/bash
# Restore ClickHouse tushare database from a native backup.
#
# Usage:
#   ./restore_clickhouse.sh tushare_20260420_040000.zip
#   BACKUP_DIR=/tmp/backups ./restore_clickhouse.sh tushare_20260420_040000.zip
#
# WARNING: This will OVERWRITE the existing tushare database.

set -euo pipefail

BACKUP_NAME="${1:?Usage: $0 <backup_name.zip>}"
BACKUP_DIR="${BACKUP_DIR:-/backups}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"

echo "=== ClickHouse Restore ==="
echo "Backup: $BACKUP_NAME"
echo "Backup dir: $BACKUP_DIR"

# Verify backup exists on host
if [ ! -f "$BACKUP_DIR/$BACKUP_NAME" ]; then
  echo "ERROR: Backup not found: $BACKUP_DIR/$BACKUP_NAME"
  exit 1
fi

# Copy backup to container
echo "Copying backup to container..."
docker compose -f "$COMPOSE_FILE" cp \
  "$BACKUP_DIR/$BACKUP_NAME" \
  clickhouse:/var/lib/clickhouse/backups/"$BACKUP_NAME"

# Confirm before restore
echo ""
echo "WARNING: This will OVERWRITE the existing tushare database."
read -p "Type 'RESTORE' to continue: " CONFIRM
if [ "$CONFIRM" != "RESTORE" ]; then
  echo "Restore cancelled."
  exit 1
fi

# Restore
echo "Restoring..."
docker compose -f "$COMPOSE_FILE" exec -T clickhouse clickhouse-client --query "
RESTORE DATABASE tushare FROM Disk('backups', '$BACKUP_NAME')
"

echo "=== Restore complete ==="

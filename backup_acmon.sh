#!/bin/sh
# Daily Acmon backup — runs as NAS cron job.
# Keeps last 30 SQLite snapshots in /volume1/backups/acmon/.

BACKUP_DIR="/volume1/backups/acmon"
DB_SRC="/volume1/docker/acmon/data/acmon.db"
DATE=$(date +%Y-%m-%d)

mkdir -p "$BACKUP_DIR"

# Flush WAL into main DB before copying
sqlite3 "$DB_SRC" "PRAGMA wal_checkpoint(TRUNCATE);" 2>/dev/null || true
cp "$DB_SRC" "$BACKUP_DIR/acmon-$DATE.db"

# Keep only the 30 most recent backups
ls -t "$BACKUP_DIR"/acmon-*.db | tail -n +31 | xargs rm -f 2>/dev/null || true

echo "Backup done: $BACKUP_DIR/acmon-$DATE.db"

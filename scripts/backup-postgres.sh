#!/usr/bin/env sh
set -eu

: "${POSTGRES_DB:?Set POSTGRES_DB}"
: "${POSTGRES_USER:?Set POSTGRES_USER}"
: "${BACKUP_DIR:?Set BACKUP_DIR}"

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$BACKUP_DIR"
pg_dump \
  --format=custom \
  --file="$BACKUP_DIR/${POSTGRES_DB}-${timestamp}.dump" \
  --dbname="$POSTGRES_DB" \
  --username="$POSTGRES_USER"

find "$BACKUP_DIR" -type f -name "${POSTGRES_DB}-*.dump" -mtime +"${BACKUP_RETENTION_DAYS:-30}" -delete

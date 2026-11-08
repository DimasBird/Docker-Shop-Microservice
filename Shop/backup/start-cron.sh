#!/bin/sh
set -eu

: "${BACKUP_CRON:=0 3 * * *}"
: "${TZ:=Europe/Berlin}"
export TZ

mkdir -p /var/spool/cron/crontabs

printf '%s\n' "$BACKUP_CRON /usr/local/bin/backup.sh >> /proc/1/fd/1 2>> /proc/1/fd/2" \
  > /var/spool/cron/crontabs/root

echo "Cron started: $BACKUP_CRON ($TZ)"
exec busybox crond -f -d 8 -c /var/spool/cron/crontabs
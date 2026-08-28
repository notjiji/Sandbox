#!/bin/sh
set -e

case "${1:-cron}" in
  cron)
    echo "[entrypoint] Starting backup scheduler (crond)"
    exec crond -f -l 2
    ;;
  backup)
    shift
    exec /opt/backup/scripts/backup.sh "$@"
    ;;
  restore)
    shift
    exec /opt/backup/scripts/restore.sh "$@"
    ;;
  restore-test)
    shift
    exec /opt/backup/scripts/restore-test.sh "$@"
    ;;
  retention)
    # shellcheck source=/dev/null
    . /opt/backup/scripts/lib.sh
    apply_retention "$(backup_root)/postgres"
    apply_retention "$(backup_root)/reports"
    ;;
  *)
    exec "$@"
    ;;
esac

FROM postgres:16-alpine

RUN apk add --no-cache bash openssl gzip tar findutils dcron

COPY scripts/ /opt/backup/scripts/
RUN chmod +x /opt/backup/scripts/*.sh

COPY crontab /etc/crontabs/root
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV BACKUP_ROOT=/backups \
    BACKUP_RETENTION_DAYS=7 \
    BACKUP_REPORT_FILES=true \
    REPORT_STORAGE_MOUNT=/report_storage

VOLUME ["/backups"]

ENTRYPOINT ["/entrypoint.sh"]
CMD ["cron"]

FROM postgres:16-alpine

RUN apk add --no-cache aws-cli dcron tzdata

COPY backup.sh /usr/local/bin/backup.sh
COPY start-cron.sh /usr/local/bin/start-cron.sh

RUN chmod +x /usr/local/bin/backup.sh /usr/local/bin/start-cron.sh

ENTRYPOINT ["/usr/local/bin/backup.sh"]
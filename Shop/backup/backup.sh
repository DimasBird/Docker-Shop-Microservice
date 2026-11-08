#!/bin/sh
set -eu

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
S3_PREFIX="${S3_PREFIX:-postgres}"

mkdir -p "$BACKUP_DIR"

# Проверяем обязательные переменные
: "${SHOP_DB_HOST:?Не задан SHOP_DB_HOST}"
: "${SHOP_DB_USER:?Не задан SHOP_DB_USER}"
: "${SHOP_DB_PASSWORD:?Не задан SHOP_DB_PASSWORD}"
: "${SHOP_DB_NAME:?Не задан SHOP_DB_NAME}"

: "${AUTH_DB_HOST:?Не задан AUTH_DB_HOST}"
: "${AUTH_DB_USER:?Не задан AUTH_DB_USER}"
: "${AUTH_DB_PASSWORD:?Не задан AUTH_DB_PASSWORD}"
: "${AUTH_DB_NAME:?Не задан AUTH_DB_NAME}"

: "${S3_ENDPOINT_URL:?Не задан S3_ENDPOINT_URL}"
: "${S3_BUCKET:?Не задан S3_BUCKET}"
: "${S3_ACCESS_KEY:?Не задан S3_ACCESS_KEY}"
: "${S3_SECRET_KEY:?Не задан S3_SECRET_KEY}"

export AWS_ACCESS_KEY_ID="$S3_ACCESS_KEY"
export AWS_SECRET_ACCESS_KEY="$S3_SECRET_KEY"
export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"
export AWS_EC2_METADATA_DISABLED=true

echo "[$(date)] Начало резервного копирования"

SHOP_FILE="$BACKUP_DIR/shop_$TIMESTAMP.dump"
AUTH_FILE="$BACKUP_DIR/auth_$TIMESTAMP.dump"

cleanup() {
    rm -f "$SHOP_FILE.tmp" "$AUTH_FILE.tmp"
}
trap cleanup EXIT HUP INT TERM

# Создаём дамп магазина
PGPASSWORD="$SHOP_DB_PASSWORD" pg_dump \
    -h "$SHOP_DB_HOST" \
    -U "$SHOP_DB_USER" \
    -d "$SHOP_DB_NAME" \
    -Fc \
    -f "$SHOP_FILE.tmp"

mv "$SHOP_FILE.tmp" "$SHOP_FILE"
echo "[$(date)] Дамп магазина создан"

# Создаём дамп авторизации
PGPASSWORD="$AUTH_DB_PASSWORD" pg_dump \
    -h "$AUTH_DB_HOST" \
    -U "$AUTH_DB_USER" \
    -d "$AUTH_DB_NAME" \
    -Fc \
    -f "$AUTH_FILE.tmp"

mv "$AUTH_FILE.tmp" "$AUTH_FILE"
echo "[$(date)] Дамп авторизации создан"

# Загружаем оба дампа в Garage через S3 API
aws --endpoint-url "$S3_ENDPOINT_URL" s3 cp \
    "$SHOP_FILE" "s3://$S3_BUCKET/$S3_PREFIX/$TIMESTAMP/shop.dump"

aws --endpoint-url "$S3_ENDPOINT_URL" s3 cp \
    "$AUTH_FILE" "s3://$S3_BUCKET/$S3_PREFIX/$TIMESTAMP/auth.dump"

echo "[$(date)] Оба дампа загружены в S3"

# Удаляем локальные копии после успешной загрузки обоих файлов
rm -f "$SHOP_FILE" "$AUTH_FILE"

echo "[$(date)] Резервное копирование завершено успешно"

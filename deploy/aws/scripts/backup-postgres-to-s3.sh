#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "${ROOT_DIR}"

: "${S3_BUCKET:?Set S3_BUCKET environment variable}"
AWS_REGION="${AWS_REGION:-ap-south-1}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="${ROOT_DIR}/.backups"
BACKUP_FILE="${BACKUP_DIR}/postgres-${TIMESTAMP}.sql.gz"

mkdir -p "${BACKUP_DIR}"

POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-trading_postgres}"
POSTGRES_USER="${POSTGRES_USER:-trading_user}"
POSTGRES_DB="${POSTGRES_DB:-trading_db}"

docker exec "${POSTGRES_CONTAINER}" pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" | gzip > "${BACKUP_FILE}"

aws s3 cp "${BACKUP_FILE}" "s3://${S3_BUCKET}/postgres/${TIMESTAMP}.sql.gz" --region "${AWS_REGION}"

echo "Uploaded backup to s3://${S3_BUCKET}/postgres/${TIMESTAMP}.sql.gz"

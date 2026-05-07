#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "${ROOT_DIR}"

if [[ ! -f .env ]]; then
  echo "Missing .env. Copy from .env.example and set production values."
  exit 1
fi

echo "Building Docker images..."
docker compose build

echo "Starting services..."
docker compose up -d

echo "Service status:"
docker compose ps

echo "Waiting for API health..."
API_HEALTH_URL="${API_HEALTH_URL:-http://localhost:8000/health}"
for i in {1..30}; do
  if curl -fsS "${API_HEALTH_URL}" >/dev/null; then
    echo "API is healthy"
    exit 0
  fi
  sleep 2
done

echo "API health check failed"
exit 1

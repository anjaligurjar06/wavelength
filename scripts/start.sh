#!/bin/sh
set -eu

echo "Running database migrations..."
alembic -c /app/migrations/alembic.ini upgrade head

echo "Starting API on port ${PORT:-8000}..."
exec uvicorn api.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --no-access-log \
  --proxy-headers \
  --forwarded-allow-ips="*"

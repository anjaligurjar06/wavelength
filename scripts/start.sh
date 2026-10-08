#!/bin/sh
set -eu

# Fail fast with a readable message instead of a 100-line traceback
missing=""
for var in DATABASE_URL JWT_SECRET SPOTIFY_CLIENT_ID SPOTIFY_CLIENT_SECRET SPOTIFY_REDIRECT_URI; do
  eval "val=\${$var:-}"
  [ -n "$val" ] || missing="$missing $var"
done
if [ -n "$missing" ]; then
  echo "ERROR: required environment variables are missing or empty:$missing" >&2
  echo "Set them on this Railway service (Variables tab) and redeploy." >&2
  exit 1
fi

# Only enforced on Railway (it sets RAILWAY_ENVIRONMENT); local docker runs may use localhost
if [ -n "${RAILWAY_ENVIRONMENT:-}" ]; then
  case "${DATABASE_URL}" in
    *localhost*|*127.0.0.1*)
      echo "ERROR: DATABASE_URL points at localhost; it must point at the Railway Postgres service." >&2
      exit 1 ;;
  esac
fi

[ -n "${REDIS_URL:-}" ] || echo "WARNING: REDIS_URL is not set; feed cache and chat rate limiting will use localhost and fail." >&2

echo "Running database migrations..."
alembic -c /app/migrations/alembic.ini upgrade head

echo "Starting API on port ${PORT:-8000}..."
exec uvicorn api.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --no-access-log \
  --proxy-headers \
  --forwarded-allow-ips="*"
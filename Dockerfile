# ---------- build stage: resolve + install the uv workspace ----------
FROM python:3.12-slim AS build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app
# uv needs every workspace member's pyproject present to resolve the lockfile
COPY pyproject.toml uv.lock ./
COPY packages ./packages

# Install only the api package and its workspace deps, no dev tools, non-editable
RUN uv sync --frozen --no-dev --no-editable --package api

# ---------- runtime stage ----------
FROM python:3.12-slim

RUN useradd --create-home --uid 1000 app
WORKDIR /app

COPY --from=build /app/.venv /app/.venv
# Alembic files are not part of the shared wheel, so copy them explicitly
COPY --from=build /app/packages/shared/alembic /app/migrations/alembic
COPY --from=build /app/packages/shared/alembic.ini /app/migrations/alembic.ini
COPY scripts/start.sh /app/start.sh
RUN chmod 755 /app/start.sh

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PORT=8000

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import os,urllib.request;urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8000\")}/health')" || exit 1

CMD ["/app/start.sh"]

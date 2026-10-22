# Core Task API Dockerfile (uv-managed)
FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# Dependency metadata and application code are needed together because the
# project itself is installed as a package.
COPY pyproject.toml README.md ./
COPY app/ ./app/

RUN uv pip install --system --no-cache .

# Migrations
COPY alembic.ini ./
COPY alembic/ ./alembic/

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=5)" || exit 1

# Apply migrations before serving so a fresh volume gets a working schema.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
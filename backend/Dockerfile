# --- RUNTIME (imagen final mínima)
FROM python:3.12-slim-bookworm AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# --- BUILDER (solo para instalar dependencias)
FROM runtime AS builder
WORKDIR /app

COPY utils-project /app/utils-project
COPY backend /app/backend

RUN uv venv .venv && \
    uv pip install -e utils-project -e backend

# --- PRODUCTION
FROM runtime AS production
WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/utils-project /app/utils-project
COPY --from=builder /app/backend /app/backend

ENV PATH="/app/.venv/bin:$PATH"
CMD ["uvicorn", "app.application:app", "--host", "0.0.0.0", "--port", "8000"]

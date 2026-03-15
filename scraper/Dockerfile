# --- RUNTIME (imagen final con Chromium mínimo)
FROM python:3.12-slim-bookworm AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    chromium \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Chromium en PATH para webdriver-manager
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMIUM_FLAGS="--no-sandbox --headless --disable-gpu --disable-dev-shm-usage"

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# --- BUILDER
FROM runtime AS builder
WORKDIR /app

COPY utils-project /app/utils-project
COPY scraper /app/scraper

RUN uv venv .venv && \
    uv pip install -e utils-project -e scraper

# --- PRODUCTION
FROM runtime AS production
WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/utils-project /app/utils-project
COPY --from=builder /app/scraper /app/scraper

ENV PATH="/app/.venv/bin:$PATH"
CMD ["uv", "run", "scraper/src/pipeline/main.py"]

# --- BASE---------------------
FROM python:3.12-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    chromium \
    libnss3 \
    libgconf-2-4 \
    libxss1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
    
# --- UV INSTALLER
FROM base AS uv-installer
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/


# --- BUILDER------------
FROM uv-installer AS builder
WORKDIR /app

COPY utils-project /app/utils-project
COPY scraper /app/scraper

RUN uv venv .venv && \
    uv pip install -e utils-project && \
    uv pip install -e scraper

FROM builder AS production
WORKDIR /app
CMD [ "uv", "run", "scraper/src/pipeline/main.py" ]
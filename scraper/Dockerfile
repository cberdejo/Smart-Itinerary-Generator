# --- BASE---------------------
FROM python:3.12-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    && apt-get purge -y build-essential \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# --- UV INSTALLER
FROM base AS uv-installer
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN uv --version

# --- BUILDER------------
FROM uv-installer AS builder
WORKDIR /app

COPY utils-project /app/utils-project
COPY scraper /app/scraper

RUN uv venv .venv && \
    uv pip install -e utils-project && \
    uv pip install -e scraper

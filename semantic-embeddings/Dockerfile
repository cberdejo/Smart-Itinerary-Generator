FROM python:3.12-slim-bookworm AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

FROM runtime AS builder
WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY semantic-embeddings /app/semantic-embeddings

RUN uv venv .venv && \
    uv pip install -e semantic-embeddings

FROM runtime AS production
WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/semantic-embeddings /app/semantic-embeddings

ENV PATH="/app/.venv/bin:$PATH"
ENV EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"
ENV RERANKER_MODEL="cross-encoder/ms-marco-MiniLM-L-6-v2"

CMD ["uvicorn", "service.application:app", "--host", "0.0.0.0", "--port", "8080"]

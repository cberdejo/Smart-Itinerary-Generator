# Semantic Embeddings Service

Microservicio para:
- Generar embeddings (`/api/v1/embed`)
- Rerank de documentos (`/api/v1/rerank`)
- Construir texto canonico para busqueda hibrida de municipios (`/api/v1/search-text/town*`)

## Variables de entorno

- `EMBEDDING_MODEL` (default: `sentence-transformers/all-MiniLM-L6-v2`)
- `RERANKER_MODEL` (default: `cross-encoder/ms-marco-MiniLM-L-6-v2`)

## Ejecutar

```bash
uv pip install -e .
uv run uvicorn service.application:app --host 0.0.0.0 --port 8080
```

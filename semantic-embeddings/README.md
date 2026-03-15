# Semantic Embeddings Service

Microservicio para:
- Generar embeddings (`/embed`)
- Rerank de documentos (`/rerank`)
- Construir texto canónico para búsqueda híbrida (`/search-text/*`)

## Variables de entorno

- `EMBEDDING_MODEL` (default: `sentence-transformers/all-MiniLM-L6-v2`)
- `RERANKER_MODEL` (default: `cross-encoder/ms-marco-MiniLM-L-6-v2`)

## Ejecutar

```bash
uv pip install -e .
uv run uvicorn service.application:app --host 0.0.0.0 --port 8080
```

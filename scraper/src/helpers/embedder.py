from collections.abc import Sequence

import httpx

from config.settings import settings


def _is_batch_input(value: str | Sequence[str]) -> bool:
    return isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    )


def _normalize_embed_response(payload: object) -> list[list[float]]:
    if isinstance(payload, list):
        return [[float(x) for x in row] for row in payload]

    if not isinstance(payload, dict):
        raise RuntimeError("Unexpected embed response format")

    if isinstance(payload.get("embeddings"), list):
        return [[float(x) for x in row] for row in payload["embeddings"]]

    if isinstance(payload.get("data"), list):
        vectors = []
        for item in payload["data"]:
            if not isinstance(item, dict) or "embedding" not in item:
                raise RuntimeError("Invalid embedding entry in response data")
            vectors.append([float(x) for x in item["embedding"]])
        return vectors

    raise RuntimeError("Embeddings key not found in response")


def get_embedding(text: str | Sequence[str]):
    is_batch = _is_batch_input(text)
    texts = list(text) if is_batch else [str(text)]

    base_url = str(settings.semantic_embeddings_url).rstrip("/")
    payload = {"input": texts, "model": settings.embedding_model}

    with httpx.Client(timeout=settings.semantic_embeddings_timeout_seconds) as client:
        response = client.post(f"{base_url}/api/v1/embed", json=payload)
        response.raise_for_status()
        vectors = _normalize_embed_response(response.json())

    if len(vectors) != len(texts):
        raise RuntimeError("Embedding API returned a mismatched number of vectors")

    return vectors if is_batch else vectors[0]

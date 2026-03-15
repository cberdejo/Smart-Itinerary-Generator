from functools import lru_cache

from sentence_transformers import CrossEncoder, SentenceTransformer

from service.settings import settings


@lru_cache(maxsize=8)
def get_embedder(model_name: str | None = None) -> SentenceTransformer:
    selected = model_name or settings.embedding_model
    return SentenceTransformer(selected)


@lru_cache(maxsize=8)
def get_reranker(model_name: str | None = None) -> CrossEncoder:
    selected = model_name or settings.reranker_model
    return CrossEncoder(selected)

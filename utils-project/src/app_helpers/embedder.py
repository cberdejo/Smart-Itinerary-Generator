from sentence_transformers import SentenceTransformer
from functools import lru_cache


@lru_cache()
def get_model() -> SentenceTransformer:
    try:
        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception as e:
        raise RuntimeError(f"Error loading SentenceTransformer model: {e}")


def get_embedding(text: str):
    model = get_model()
    return model.encode(text)

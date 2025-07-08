from sentence_transformers import SentenceTransformer

try:
    _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
except Exception as e:
    raise RuntimeError(f"Error loading SentenceTransformer model: {e}")

def get_embedding(text: str):
    return _MODEL.encode(text)

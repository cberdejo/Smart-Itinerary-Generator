from fastapi import FastAPI

from service.embedding_models import get_embedder, get_reranker
from service.hybrid_search import build_search_text_from_town
from service.schemas import (
    EmbedRequest,
    EmbedResponse,
    RerankRequest,
    RerankResponse,
    SearchTextResponse,
    SearchTextsResponse,
    SearchTownTextRequest,
    SearchTownTextsRequest,
)

app = FastAPI(
    title="semantic-embeddings-service",
    version="0.1.0",
    description="Microservicio para embeddings, reranking y texto canonico de busqueda.",
)


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/embed", response_model=EmbedResponse)
def embed(request: EmbedRequest) -> EmbedResponse:
    texts = request.input if isinstance(request.input, list) else [request.input]
    model = get_embedder(request.model)
    vectors = model.encode(texts, convert_to_numpy=True)
    return EmbedResponse(embeddings=[[float(x) for x in row] for row in vectors])


@app.post("/api/v1/rerank", response_model=RerankResponse)
def rerank(request: RerankRequest) -> RerankResponse:
    if not request.documents:
        return RerankResponse(scores=[])

    model = get_reranker(request.model)
    pairs = [[request.query, doc] for doc in request.documents]
    scores = model.predict(pairs)
    return RerankResponse(scores=[float(value) for value in scores])



@app.post("/api/v1/search-text/town", response_model=SearchTextResponse)
def search_text_town(request: SearchTownTextRequest) -> SearchTextResponse:
    return SearchTextResponse(text=build_search_text_from_town(request.town))



@app.post("/api/v1/search-text/towns", response_model=SearchTextsResponse)
def search_text_towns(request: SearchTownTextsRequest) -> SearchTextsResponse:
    return SearchTextsResponse(
        texts=[build_search_text_from_town(town) for town in request.towns]
    )

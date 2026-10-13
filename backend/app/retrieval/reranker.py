
from functools import lru_cache

from FlagEmbedding import FlagReranker

from app.db.models.chunk import Chunk


MODEL_NAME = "BAAI/bge-reranker-v2-m3"


@lru_cache(maxsize=1)
def get_reranker() -> FlagReranker:
    """Load the model once and reuse it across requests."""
    return FlagReranker(MODEL_NAME, use_fp16=False)


def rerank_chunks(
    query: str,
    candidates: list[tuple[Chunk, float]],
    top_k: int = 5,
) -> list[tuple[Chunk, float]]:
    """
    Rerank retrieved chunks using cross-encoder relevance scores.

    Args:
        query: The user's search query.
        candidates: (Chunk, previous_score) pairs from hybrid retrieval.
        top_k: Maximum number of chunks to return.

    Returns:
        (Chunk, reranker_score) pairs, sorted by descending score.
    """
    if not query.strip():
        raise ValueError("query must not be empty")

    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    if not candidates:
        return []

    reranker = get_reranker()

    pairs = [
        [query, chunk.text]
        for chunk, _ in candidates
    ]

    scores = reranker.compute_score(pairs)

    # Some library/model configurations may return a scalar for one pair.
    if isinstance(scores, (int, float)):
        scores = [scores]

    if len(scores) != len(candidates):
        raise RuntimeError("Reranker returned an unexpected number of scores")

    reranked = [
        (chunk, float(score))
        for (chunk, _), score in zip(candidates, scores)
    ]

    reranked.sort(key=lambda item: item[1], reverse=True)

    return reranked[:top_k]

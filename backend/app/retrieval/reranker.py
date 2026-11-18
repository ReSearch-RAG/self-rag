import logging
import math
from functools import lru_cache

from FlagEmbedding import FlagReranker

from app.db.models.chunk import Chunk

logger = logging.getLogger(__name__)

MODEL_NAME = "BAAI/bge-reranker-v2-m3"


@lru_cache(maxsize=1)
def get_reranker() -> FlagReranker:
    """Load the reranker model once and reuse it."""
    logger.info("Loading reranker model %s", MODEL_NAME)
    return FlagReranker(MODEL_NAME, use_fp16=False)


def _sigmoid(x: float) -> float:
    """Map an unbounded logit to [0, 1]."""
    return 1.0 / (1.0 + math.exp(-x))


def rerank_chunks(
    query: str,
    candidates: list[tuple[Chunk, float]],
    top_k: int = 5,
) -> list[tuple[Chunk, float]]:
    """
    Rerank candidate chunks against a query using a cross-encoder.

    Args:
        query: The user's search query.
        candidates: (Chunk, initial retrieval score) pairs.
        top_k: Maximum number of reranked chunks to return.

    Returns:
        (Chunk, normalized_reranker_score) pairs sorted by descending score.
        Scores are in [0, 1] after sigmoid normalization.
    """
    if not query.strip():
        raise ValueError("query must not be empty")

    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    if not candidates:
        return []

    reranker = get_reranker()

    pairs = [[query, chunk.text] for chunk, _ in candidates]
    scores = reranker.compute_score(pairs)

    # Handle a single candidate if the library returns a scalar.
    if isinstance(scores, (int, float)):
        scores = [scores]

    if len(scores) != len(candidates):
        raise RuntimeError(
            "Reranker returned an unexpected number of scores"
        )

    reranked = [
        (chunk, _sigmoid(float(score)))
        for (chunk, _), score in zip(candidates, scores)
    ]

    reranked.sort(key=lambda item: item[1], reverse=True)

    return reranked[:top_k]
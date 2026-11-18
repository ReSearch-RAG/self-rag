import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from sqlalchemy.orm import Session

from app.db.models.chunk import Chunk
from app.retrieval.lexical import lexical_search
from app.retrieval.vector import vector_search

logger = logging.getLogger(__name__)


def hybrid_search(
    db: Session,
    query: str,
    query_embedding: list[float],
    document_id: int,
    top_k: int = 5,
    candidate_k: int = 20,
    rrf_k: int = 60,
) -> list[tuple[Chunk, float]]:
    """
    Combine vector and lexical retrieval using Reciprocal Rank Fusion (RRF).

    Both searches run in parallel via a thread pool to reduce latency.

    Returns:
        A list of (Chunk, fused_score) tuples, sorted by fused score descending.
    """
    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    if candidate_k < 1:
        raise ValueError("candidate_k must be at least 1")

    if rrf_k < 1:
        raise ValueError("rrf_k must be at least 1")

    # Run both searches in parallel
    vector_results: list[tuple[Chunk, float]] = []
    lexical_results: list[tuple[Chunk, float]] = []

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_vector = executor.submit(
            vector_search,
            db,
            query_embedding,
            document_id,
            candidate_k,
        )
        future_lexical = executor.submit(
            lexical_search,
            db,
            query,
            document_id,
            candidate_k,
        )

        for future in as_completed([future_vector, future_lexical]):
            if future is future_vector:
                vector_results = future.result()
            else:
                lexical_results = future.result()

    scores: dict[int, float] = defaultdict(float)
    chunks: dict[int, Chunk] = {}

    for results in (vector_results, lexical_results):
        for rank, (chunk, _) in enumerate(results, start=1):
            chunks[chunk.id] = chunk
            scores[chunk.id] += 1.0 / (rrf_k + rank)

    ranked_chunks = sorted(
        scores,
        key=lambda chunk_id: scores[chunk_id],
        reverse=True,
    )

    logger.debug(
        "Hybrid search: %d vector + %d lexical → %d fused candidates",
        len(vector_results),
        len(lexical_results),
        len(ranked_chunks),
    )

    return [
        (chunks[chunk_id], scores[chunk_id])
        for chunk_id in ranked_chunks[:top_k]
    ]

from collections import defaultdict

from sqlalchemy.orm import Session

from app.db.models.chunk import Chunk
from app.retrieval.lexical import lexical_search
from app.retrieval.vector import vector_search


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
    Combine vector and lexical retrieval using Reciprocal Rank Fusion.

    Returns:
        A list of (Chunk, fused_score) tuples, sorted by fused score.
    """
    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    if candidate_k < 1:
        raise ValueError("candidate_k must be at least 1")

    if rrf_k < 1:
        raise ValueError("rrf_k must be at least 1")

    vector_results = vector_search(
        db=db,
        query_embedding=query_embedding,
        document_id=document_id,
        top_k=candidate_k,
    )

    lexical_results = lexical_search(
        db=db,
        query=query,
        document_id=document_id,
        top_k=candidate_k,
    )

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

    return [
        (chunks[chunk_id], scores[chunk_id])
        for chunk_id in ranked_chunks[:top_k]
    ]

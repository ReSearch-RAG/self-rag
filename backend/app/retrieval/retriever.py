from sqlalchemy.orm import Session

from app.db.models.chunk import Chunk
from app.retrieval.hybrid import hybrid_search
from app.retrieval.reranker import rerank_chunks


def retrieve(
    db: Session,
    query: str,
    query_embedding: list[float],
    document_id: int,
    top_k: int = 5,
    candidate_k: int = 20,
) -> list[tuple[Chunk, float]]:
    """
    Retrieve relevant chunks using hybrid search followed by reranking.

    Returns:
        (Chunk, reranker_score) pairs sorted by descending score.
    """
    if not query.strip():
        raise ValueError("query must not be empty")

    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    if candidate_k < 1:
        raise ValueError("candidate_k must be at least 1")

    candidates = hybrid_search(
        db=db,
        query=query,
        query_embedding=query_embedding,
        document_id=document_id,
        top_k=candidate_k,
        candidate_k=candidate_k,
    )

    if not candidates:
        return []

    return rerank_chunks(
        query=query,
        candidates=candidates,
        top_k=top_k,
    )

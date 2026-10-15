import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from sqlalchemy.orm import Session

from app.correction.query_decomposer import decompose_query
from app.db.models.chunk import Chunk
from app.ingestion.embedder import Embedder
from app.retrieval.retriever import retrieve

logger = logging.getLogger(__name__)


@dataclass
class QueryRetrievalResult:
    original_query: str
    subqueries: list[str]
    chunks: list[tuple[Chunk, float]]


@lru_cache(maxsize=1)
def get_embedder() -> Embedder:
    """Load BGE-M3 once and reuse it."""
    return Embedder()


def run_query_retrieval(
    db: Session,
    query: str,
    document_id: int,
    top_k: int = 5,
    candidate_k: int = 20,
    max_subqueries: int = 4,
) -> QueryRetrievalResult:
    """Decompose a query, retrieve evidence, and merge duplicate chunks."""
    if not query or not query.strip():
        raise ValueError("query must not be empty")

    if document_id < 1:
        raise ValueError("document_id must be positive")

    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    if candidate_k < top_k:
        raise ValueError("candidate_k must be at least top_k")

    if max_subqueries < 1:
        raise ValueError("max_subqueries must be at least 1")

    original_query = query.strip()

    # If Gemini is unavailable, continue retrieval with the original query.
    try:
        generated_queries = decompose_query(
            original_query,
            max_subqueries=max_subqueries,
        )
    except Exception:
        logger.exception(
            "Query decomposition failed; using the original query"
        )
        generated_queries = [original_query]

    # Ensure queries are valid and unique.
    subqueries = []
    for item in generated_queries:
        if isinstance(item, str) and item.strip():
            cleaned = item.strip()
            if cleaned not in subqueries:
                subqueries.append(cleaned)

    if not subqueries:
        subqueries = [original_query]

    embedder = get_embedder()
    best_chunks: dict[int, tuple[Chunk, float]] = {}

    for subquery in subqueries:
        query_embedding = embedder.embed([subquery])[0]

        results = retrieve(
            db=db,
            query=subquery,
            query_embedding=query_embedding,
            document_id=document_id,
            top_k=top_k,
            candidate_k=candidate_k,
        )

        # Keep each chunk once, retaining its highest observed score.
        for chunk, score in results:
            existing = best_chunks.get(chunk.id)

            if existing is None or score > existing[1]:
                best_chunks[chunk.id] = (chunk, score)

    merged_chunks = sorted(
        best_chunks.values(),
        key=lambda item: item[1],
        reverse=True,
    )[:top_k]

    return QueryRetrievalResult(
        original_query=original_query,
        subqueries=subqueries,
        chunks=merged_chunks,
    )
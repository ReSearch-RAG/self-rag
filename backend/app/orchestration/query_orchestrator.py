import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import List, Tuple

from sqlalchemy.orm import Session

from app.correction.query_decomposer import decompose_query
from app.correction.query_rewriter import rewrite_query
from app.db.models.chunk import Chunk
from app.generation.llm import generate_text
from app.generation.llm import generate_text
from app.evaluation.retrieval_evaluator import (
    RetrievalEvaluation,
    evaluate_retrieval,
)
from app.ingestion.embedder import Embedder
from app.retrieval.retriever import retrieve

logger = logging.getLogger(__name__)


@dataclass
class QueryRetrievalResult:
    original_query: str
    subqueries: List[str]
    chunks: List[Tuple[Chunk, float]]
    evaluation: RetrievalEvaluation
    attempts: int


@lru_cache(maxsize=1)
def get_embedder() -> Embedder:
    """Load BGE-M3 once and reuse it."""
    return Embedder()


def _retrieve_queries(
    db: Session,
    queries: List[str],
    document_id: int,
    top_k: int,
    candidate_k: int,
) -> List[Tuple[Chunk, float]]:
    """Retrieve evidence for multiple queries and deduplicate chunks."""
    embedder = get_embedder()
    best_chunks = {}

    for query in queries:
        embedding = embedder.embed([query])[0]

        results = retrieve(
            db=db,
            query=query,
            query_embedding=embedding,
            document_id=document_id,
            top_k=top_k,
            candidate_k=candidate_k,
        )

        for chunk, score in results:
            existing = best_chunks.get(chunk.id)
            if existing is None or score > existing[1]:
                best_chunks[chunk.id] = (chunk, score)

    return sorted(
        best_chunks.values(),
        key=lambda item: item[1],
        reverse=True,
    )[:top_k]


def run_query_retrieval(
    db: Session,
    query: str,
    document_id: int,
    top_k: int = 5,
    candidate_k: int = 20,
    max_subqueries: int = 4,
    max_retries: int = 2,
) -> QueryRetrievalResult:
    """Retrieve, evaluate, and attempt bounded query correction."""
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
    if max_retries < 0:
        raise ValueError("max_retries cannot be negative")

    original_query = query.strip()

    try:
        subqueries = decompose_query(
            original_query,
            generate=generate_text,
            max_subqueries=max_subqueries,
        )
    except Exception:
        logger.exception("Decomposition failed; using original query")
        subqueries = [original_query]

    subqueries = list(dict.fromkeys(
        item.strip()
        for item in subqueries
        if isinstance(item, str) and item.strip()
    ))

    if not subqueries:
        subqueries = [original_query]

    chunks = []
    evaluation = None
    attempts = 0
    current_queries = subqueries

    while True:
        chunks = _retrieve_queries(
            db=db,
            queries=current_queries,
            document_id=document_id,
            top_k=top_k,
            candidate_k=candidate_k,
        )

        attempts += 1

        try:
            evaluation = evaluate_retrieval(
                original_query=original_query,
                subqueries=subqueries,
                chunks=chunks,
            )
        except Exception:
            logger.exception("Retrieval evaluation failed")
            evaluation = RetrievalEvaluation(
                is_sufficient=False,
                relevance_score=0.0,
                coverage_score=0.0,
                missing_information=[original_query],
                reason="Evaluation failed; evidence is unverified.",
            )

        if evaluation.is_sufficient or attempts > max_retries:
            break

        try:
            rewritten = rewrite_query(
                original_query=original_query,
                missing_information=evaluation.missing_information,
            )
        except Exception:
            logger.exception("Query rewriting failed")
            break

        # Avoid repeating the same retrieval indefinitely.
        if not rewritten or rewritten.strip() in current_queries:
            break

        current_queries = [rewritten.strip()]

    return QueryRetrievalResult(
        original_query=original_query,
        subqueries=subqueries,
        chunks=chunks,
        evaluation=evaluation,
        attempts=attempts,
    )
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.correction.query_decomposer import decompose_query
from app.correction.query_rewriter import rewrite_query
from app.db.models.chunk import Chunk
from app.evaluation.conflict import ConflictDetection, detect_conflicts
from app.evaluation.retrieval_evaluator import (
    RetrievalEvaluation,
    evaluate_retrieval,
)
from app.generation.llm import generate_text
from app.ingestion.embedder import get_embedder
from app.orchestration.query_trace import QueryTrace
from app.retrieval.retriever import retrieve

logger = logging.getLogger(__name__)


@dataclass
class QueryRetrievalResult:
    original_query: str
    subqueries: List[str]
    chunks: List[Tuple[Chunk, float]]
    evaluation: RetrievalEvaluation
    attempts: int
    conflict: Optional[ConflictDetection] = None
    trace: dict = field(default_factory=dict)


def _retrieve_queries(
    db: Session,
    queries: List[str],
    document_id: int,
    top_k: int,
    candidate_k: int,
) -> List[Tuple[Chunk, float]]:
    """Retrieve evidence for multiple queries and deduplicate chunks by best score."""
    embedder = get_embedder()
    best_chunks: dict[int, Tuple[Chunk, float]] = {}

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
    min_relevance: float = 0.6,
    min_coverage: float = 0.7,
) -> QueryRetrievalResult:
    """Retrieve, evaluate, and attempt bounded query correction.

    Args:
        db: Database session.
        query: User's original query.
        document_id: ID of the document to search within.
        top_k: Number of final chunks to return.
        candidate_k: Number of candidates passed to the reranker.
        max_subqueries: Maximum decomposed sub-queries per attempt.
        max_retries: Maximum correction-and-retry loops.
        min_relevance: Minimum relevance score for sufficiency.
        min_coverage: Minimum coverage score for sufficiency.

    Returns:
        QueryRetrievalResult with chunks, evaluation, conflict info, and timing trace.
    """
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
    trace = QueryTrace()

    # ── Step 1: Query decomposition ──────────────────────────────────────────
    with trace.step("decompose"):
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

    chunks: List[Tuple[Chunk, float]] = []
    evaluation: Optional[RetrievalEvaluation] = None
    attempts = 0
    current_queries = subqueries
    current_candidate_k = candidate_k

    while True:
        # ── Step 2: Retrieval ────────────────────────────────────────────────
        with trace.step(f"retrieve_attempt_{attempts + 1}"):
            chunks = _retrieve_queries(
                db=db,
                queries=current_queries,
                document_id=document_id,
                top_k=top_k,
                candidate_k=current_candidate_k,
            )

        attempts += 1

        # ── Step 3: Evaluation ───────────────────────────────────────────────
        with trace.step(f"evaluate_attempt_{attempts}"):
            try:
                evaluation = evaluate_retrieval(
                    original_query=original_query,
                    subqueries=subqueries,
                    chunks=chunks,
                    min_relevance=min_relevance,
                    min_coverage=min_coverage,
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

        logger.info(
            "Attempt %d: relevance=%.2f coverage=%.2f sufficient=%s",
            attempts,
            evaluation.relevance_score,
            evaluation.coverage_score,
            evaluation.is_sufficient,
        )

        if evaluation.is_sufficient or attempts > max_retries:
            break

        # ── Step 4: Query rewriting ──────────────────────────────────────────
        with trace.step(f"rewrite_attempt_{attempts}"):
            try:
                rewritten = rewrite_query(
                    original_query=original_query,
                    missing_information=evaluation.missing_information,
                )
            except Exception:
                logger.exception("Query rewriting failed")
                break

        if not rewritten or rewritten.strip() in current_queries:
            break

        current_queries = [rewritten.strip()]
        # Widen the candidate pool on retries to cast a broader net
        current_candidate_k = int(current_candidate_k * 1.5)

    # ── Step 5: Conflict detection ───────────────────────────────────────────
    conflict: Optional[ConflictDetection] = None
    if len(chunks) >= 2:
        with trace.step("conflict_detection"):
            try:
                conflict = detect_conflicts(chunks)
                if conflict.has_conflict:
                    logger.warning(
                        "Conflicting chunks detected: %s",
                        conflict.conflicting_chunk_pairs,
                    )
            except Exception:
                logger.exception("Conflict detection failed")

    return QueryRetrievalResult(
        original_query=original_query,
        subqueries=subqueries,
        chunks=chunks,
        evaluation=evaluation,
        attempts=attempts,
        conflict=conflict,
        trace=trace.summary(),
    )
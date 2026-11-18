from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.models.user import User
from app.generation.answer_generator import generate_answer
from app.schemas.query import (
    AnswerResponse,
    ConflictDetectionResult,
    RetrievalRequest,
    RetrievalResponse,
    RetrievedChunk,
    SelfCorrectingRetrievalResponse,
)
from app.db.database import get_db
from app.db.models.document import Document
from app.ingestion.embedder import get_embedder
from app.orchestration.query_orchestrator import run_query_retrieval
from app.retrieval.retriever import retrieve

router = APIRouter(prefix="/queries", tags=["queries"])


def _verify_document_ownership(
    document_id: int,
    user: User,
    db: Session,
) -> Document:
    """Return the document if it exists and belongs to the user, else raise 404."""
    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == user.id,
        )
        .first()
    )
    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )
    return document


def _to_conflict_result(conflict) -> ConflictDetectionResult | None:
    if conflict is None:
        return None
    return ConflictDetectionResult(
        has_conflict=conflict.has_conflict,
        conflicting_chunk_pairs=conflict.conflicting_chunk_pairs,
        explanation=conflict.explanation,
    )


@router.post("/retrieve", response_model=RetrievalResponse)
def retrieve_document(
    request: RetrievalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RetrievalResponse:
    _verify_document_ownership(request.document_id, current_user, db)

    query = request.query.strip()

    if not query:
        raise HTTPException(
            status_code=422,
            detail="Query must not be empty",
        )

    embedder = get_embedder()
    query_embedding = embedder.embed([query])[0]

    try:
        results = retrieve(
            db=db,
            query=query,
            query_embedding=query_embedding,
            document_id=request.document_id,
            top_k=request.top_k,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return RetrievalResponse(
        document_id=request.document_id,
        query=query,
        results=[
            RetrievedChunk(
                chunk_id=chunk.id,
                text=chunk.text,
                page_number=chunk.page_number,
                section=chunk.section,
                score=score,
            )
            for chunk, score in results
        ],
    )


@router.post(
    "/search",
    response_model=SelfCorrectingRetrievalResponse,
)
def self_correcting_search(
    request: RetrievalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SelfCorrectingRetrievalResponse:
    _verify_document_ownership(request.document_id, current_user, db)

    query = request.query.strip()

    if not query:
        raise HTTPException(
            status_code=422,
            detail="Query must not be empty",
        )

    try:
        result = run_query_retrieval(
            db=db,
            query=query,
            document_id=request.document_id,
            top_k=request.top_k,
            min_relevance=request.min_relevance,
            min_coverage=request.min_coverage,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return SelfCorrectingRetrievalResponse(
        document_id=request.document_id,
        query=result.original_query,
        subqueries=result.subqueries,
        results=[
            RetrievedChunk(
                chunk_id=chunk.id,
                text=chunk.text,
                page_number=chunk.page_number,
                section=chunk.section,
                score=score,
            )
            for chunk, score in result.chunks
        ],
        is_sufficient=result.evaluation.is_sufficient,
        relevance_score=result.evaluation.relevance_score,
        coverage_score=result.evaluation.coverage_score,
        missing_information=result.evaluation.missing_information,
        evaluation_reason=result.evaluation.reason,
        attempts=result.attempts,
        trace=result.trace,
        conflict_detection=_to_conflict_result(result.conflict),
    )


@router.post("/answer", response_model=AnswerResponse)
def answer_document_question(
    request: RetrievalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnswerResponse:
    _verify_document_ownership(request.document_id, current_user, db)

    query = request.query.strip()

    if not query:
        raise HTTPException(
            status_code=422,
            detail="Query must not be empty",
        )

    try:
        result = run_query_retrieval(
            db=db,
            query=query,
            document_id=request.document_id,
            top_k=request.top_k,
            min_relevance=request.min_relevance,
            min_coverage=request.min_coverage,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    citations = [
        RetrievedChunk(
            chunk_id=chunk.id,
            text=chunk.text,
            page_number=chunk.page_number,
            section=chunk.section,
            score=score,
        )
        for chunk, score in result.chunks
    ]

    if not result.chunks:
        answer = "I couldn't find relevant evidence in this document to answer your question."
    elif not result.evaluation.is_sufficient and "Evaluation failed" not in result.evaluation.reason:
        # Genuinely insufficient evidence (not an evaluator crash)
        answer = "Insufficient evidence to answer reliably. " + result.evaluation.reason
    else:
        # Either sufficient, or evaluator failed (generate with caveat)
        try:
            answer = generate_answer(
                query=query,
                chunks=result.chunks,
            )
            if "Evaluation failed" in result.evaluation.reason:
                answer += (
                    "\n\n⚠️ Note: Retrieval quality could not be automatically verified. "
                    "Please review the cited chunks."
                )
        except (RuntimeError, ValueError) as exc:
            raise HTTPException(
                status_code=502,
                detail="Answer generation failed. Check the Gemini configuration.",
            ) from exc

    return AnswerResponse(
        document_id=request.document_id,
        query=query,
        answer=answer,
        citations=citations,
        is_sufficient=result.evaluation.is_sufficient,
        relevance_score=result.evaluation.relevance_score,
        coverage_score=result.evaluation.coverage_score,
        missing_information=result.evaluation.missing_information,
        evaluation_reason=result.evaluation.reason,
        attempts=result.attempts,
        conflict_detection=_to_conflict_result(result.conflict),
        trace=result.trace,
    )

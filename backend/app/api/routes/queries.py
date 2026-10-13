from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models.document import Document
from app.ingestion.embedder import Embedder
from app.retrieval.retriever import retrieve
from app.schemas.query import (
    RetrievalRequest,
    RetrievalResponse,
    RetrievedChunk,
)

router = APIRouter(prefix="/queries", tags=["queries"])


@lru_cache(maxsize=1)
def get_embedder() -> Embedder:
    """Load the embedding model once and reuse it."""
    return Embedder()


@router.post("/retrieve", response_model=RetrievalResponse)
def retrieve_document(
    request: RetrievalRequest,
    db: Session = Depends(get_db),
) -> RetrievalResponse:
    document = (
        db.query(Document)
        .filter(Document.id == request.document_id)
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

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
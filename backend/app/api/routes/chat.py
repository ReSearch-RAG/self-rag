from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models.document import Document
from app.generation.answer_generator import generate_answer
from app.orchestration.query_orchestrator import run_query_retrieval
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
def chat_with_document(
    request: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
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

    message = request.message.strip()

    if not message:
        raise HTTPException(
            status_code=422,
            detail="Message must not be empty",
        )

    try:
        result = run_query_retrieval(
            db=db,
            query=message,
            document_id=request.document_id,
            top_k=request.top_k,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    if not result.chunks or not result.evaluation.is_sufficient:
        answer = (
            "I cannot provide a reliable answer from the retrieved "
            "evidence. " + result.evaluation.reason
        )
    else:
        try:
            answer = generate_answer(
                query=message,
                chunks=result.chunks,
            )
        except (RuntimeError, ValueError) as exc:
            raise HTTPException(
                status_code=502,
                detail="Answer generation failed. Check the Gemini configuration.",
            ) from exc

    return ChatResponse(
        document_id=request.document_id,
        message=message,
        answer=answer,
        is_sufficient=result.evaluation.is_sufficient,
        attempts=result.attempts,
    )
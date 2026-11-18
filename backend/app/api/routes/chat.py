from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import re
from typing import Optional

from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.db.models.conversation import Conversation, Message
from app.db.models.document import Document
from app.db.models.user import User
from app.generation.answer_generator import generate_answer
from app.orchestration.query_orchestrator import run_query_retrieval
from app.schemas.chat import (
    ChatHistoryResponse,
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
    ConversationListResponse,
    ConversationSummary,
)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
def chat_with_document(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
    document = (
        db.query(Document)
        .filter(
            Document.id == request.document_id,
            Document.user_id == current_user.id,
        )
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

    conversation = _get_or_create_conversation(db, current_user, request.document_id)

    # Detect common greetings
    greeting = _greeting_response(message)
    if greeting is not None:
        _save_chat_pair(
            db=db,
            conversation=conversation,
            user_message=message,
            assistant_message=greeting,
            is_sufficient=True,
            attempts=0,
        )
        return ChatResponse(
            document_id=request.document_id,
            message=message,
            answer=greeting,
            is_sufficient=True,
            attempts=0,
            is_conversational=True,
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

    if not result.chunks:
        answer = (
            "I could not find relevant evidence in this document to answer "
            "your question."
        )
        effective_sufficient = False
    else:
        try:
            answer = generate_answer(
                query=message,
                chunks=result.chunks,
            )
            effective_sufficient = True
        except (RuntimeError, ValueError) as exc:
            raise HTTPException(
                status_code=502,
                detail="Answer generation failed. Check the Gemini configuration.",
            ) from exc

    # Log the assistant's answer in the conversation
    _save_chat_pair(
        db=db,
        conversation=conversation,
        user_message=message,
        assistant_message=answer,
        is_sufficient=effective_sufficient,
        attempts=result.attempts,
    )

    return ChatResponse(
        document_id=request.document_id,
        message=message,
        answer=answer,
        is_sufficient=effective_sufficient,
        attempts=result.attempts,
    )


@router.get("/{document_id}/history", response_model=ChatHistoryResponse)
def get_chat_history(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatHistoryResponse:
    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
        .first()
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.user_id == current_user.id,
            Conversation.document_id == document_id,
        )
        .first()
    )
    if conversation is None:
        return ChatHistoryResponse(document_id=document_id, messages=[])

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc(), Message.id.asc())
        .all()
    )
    return ChatHistoryResponse(
        document_id=document_id,
        messages=[
            ChatMessageResponse(
                id=item.id,
                role=item.role,
                content=item.content,
                is_sufficient=(
                    None
                    if item.is_sufficient is None
                    else bool(item.is_sufficient)
                ),
                attempts=item.attempts,
            )
            for item in messages
        ],
    )


@router.get("/conversations", response_model=ConversationListResponse)
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationListResponse:
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )

    summaries: list[ConversationSummary] = []
    for conversation in conversations:
        document = db.query(Document).filter(Document.id == conversation.document_id).first()
        if document is None:
            continue

        messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .all()
        )
        if not messages:
            continue

        preview_message = next(
            (message for message in messages if message.role == "assistant"),
            messages[0],
        )
        preview = preview_message.content.strip().replace("\n", " ")
        if len(preview) > 140:
            preview = preview[:137] + "..."

        summaries.append(ConversationSummary(
            conversation_id=conversation.id,
            document_id=document.id,
            document_name=document.filename,
            title=conversation.title or document.filename,
            preview=preview,
            updated_at=conversation.updated_at.isoformat(),
            message_count=len(messages),
        ))

    return ConversationListResponse(conversations=summaries)


def _greeting_response(message: str) -> Optional[str]:
    normalized = re.sub(r"[^a-z0-9 ]", "", message.lower()).strip()
    greetings = {
        "hi",
        "hello",
        "hey",
        "hiya",
        "good morning",
        "good afternoon",
        "good evening",
        "how are you",
    }

    if normalized in greetings:
        return "Hello! How can I help you today?"
    if normalized in {"thanks", "thank you", "thx"}:
        return "You're welcome!"
    if normalized in {"bye", "goodbye", "see you"}:
        return "Goodbye! Feel free to ask whenever you need help."
    return None


def _get_or_create_conversation(
    db: Session,
    user: User,
    document_id: int,
) -> Conversation:
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.user_id == user.id,
            Conversation.document_id == document_id,
        )
        .first()
    )
    if conversation is None:
        conversation = Conversation(
            user_id=user.id,
            document_id=document_id,
            title="Document conversation",
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    return conversation


def _save_chat_pair(
    db: Session,
    conversation: Conversation,
    user_message: str,
    assistant_message: str,
    is_sufficient: bool,
    attempts: int,
) -> None:
    db.add(Message(
        conversation_id=conversation.id,
        role="user",
        content=user_message,
    ))
    db.add(Message(
        conversation_id=conversation.id,
        role="assistant",
        content=assistant_message,
        is_sufficient=1 if is_sufficient else 0,
        attempts=attempts,
    ))
    db.commit()
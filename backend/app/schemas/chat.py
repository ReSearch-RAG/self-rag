from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    document_id: int = Field(gt=0)
    message: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=20)


class ChatResponse(BaseModel):
    document_id: int
    message: str
    answer: str
    is_sufficient: bool
    attempts: int
    is_conversational: bool = False


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    is_sufficient: Optional[bool] = None
    attempts: Optional[int] = None


class ChatHistoryResponse(BaseModel):
    document_id: int
    messages: list[ChatMessageResponse]


class ConversationSummary(BaseModel):
    conversation_id: int
    document_id: int
    document_name: str
    title: str
    preview: str
    updated_at: str
    message_count: int


class ConversationListResponse(BaseModel):
    conversations: list[ConversationSummary]

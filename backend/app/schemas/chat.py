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

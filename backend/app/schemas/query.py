from __future__ import annotations

from pydantic import BaseModel, Field


class RetrievalRequest(BaseModel):
    document_id: int = Field(gt=0)
    query: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=20)


class RetrievedChunk(BaseModel):
    chunk_id: int
    text: str
    page_number: int | None
    section: str | None
    score: float


class RetrievalResponse(BaseModel):
    document_id: int
    query: str
    results: list[RetrievedChunk]
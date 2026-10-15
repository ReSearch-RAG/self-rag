from typing import List, Optional

from pydantic import BaseModel, Field


class RetrievalRequest(BaseModel):
    document_id: int = Field(gt=0)
    query: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=20)


class RetrievedChunk(BaseModel):
    chunk_id: int
    text: str
    page_number: Optional[int]
    section: Optional[str]
    score: float


class RetrievalResponse(BaseModel):
    document_id: int
    query: str
    results: List[RetrievedChunk]


class SelfCorrectingRetrievalResponse(BaseModel):
    document_id: int
    query: str
    subqueries: List[str]
    results: List[RetrievedChunk]
    is_sufficient: bool
    relevance_score: float
    coverage_score: float
    missing_information: List[str]
    evaluation_reason: str
    attempts: int

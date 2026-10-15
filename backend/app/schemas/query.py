from typing import List, Optional, Tuple

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


class ClaimVerificationResult(BaseModel):
    claim: str
    verdict: str
    supporting_chunk_ids: List[int]
    contradicting_chunk_ids: List[int]
    explanation: str


class ConflictDetectionResult(BaseModel):
    has_conflict: bool
    conflicting_chunk_pairs: List[Tuple[int, int]]
    explanation: str


class AnswerResponse(BaseModel):
    document_id: int
    query: str
    answer: str
    citations: List[RetrievedChunk]
    is_sufficient: bool
    relevance_score: float
    coverage_score: float
    missing_information: List[str]
    evaluation_reason: str
    attempts: int
    claim_verifications: List[ClaimVerificationResult] = Field(
        default_factory=list
    )
    conflict_detection: Optional[ConflictDetectionResult] = None

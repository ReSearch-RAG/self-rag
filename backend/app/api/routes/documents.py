from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from app.db.models.chunk import Chunk
from app.db.database import get_db
from app.db.models.document import Document
router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    filename: str
    file_type: str
    status: str
    created_at: datetime


@router.get("/", response_model=List[DocumentResponse])
def list_documents(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
) -> List[DocumentResponse]:
    query = db.query(Document)

    if status:
        query = query.filter(Document.status == status)

    documents = query.order_by(Document.created_at.desc()).all()
    return documents
@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
) -> DocumentResponse:
    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if document is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return document
class ChunkResponse(BaseModel):
    id: int
    document_id: int
    text: str
    page_number: Optional[int]
    section: Optional[str]

    model_config = ConfigDict(from_attributes=True)


@router.get(
    "/{document_id}/chunks",
    response_model=List[ChunkResponse],
)
def list_document_chunks(
    document_id: int,
    db: Session = Depends(get_db),
) -> List[ChunkResponse]:
    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    chunks = (
        db.query(Chunk)
        .filter(Chunk.document_id == document_id)
        .order_by(Chunk.page_number.asc(), Chunk.id.asc())
        .all()
    )

    return chunks
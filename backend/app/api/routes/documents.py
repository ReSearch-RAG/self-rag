from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models.document import Document

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    status: str
    created_at: datetime

    class Config:
        orm_mode = True


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
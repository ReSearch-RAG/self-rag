import os
import tempfile
import uuid
from pathlib import Path

from fastapi import File, Form, UploadFile
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.ingestion.pipeline import ingest_document
from app.storage.r2_storage import R2Storage
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

@router.post("/upload", response_model=DocumentResponse, status_code=201)
def upload_document(
    file: UploadFile = File(...),
    user_id: int = Form(...),
    db: Session = Depends(get_db),
) -> DocumentResponse:
    if not file.filename or Path(file.filename).suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    temp_path = None
    object_key = f"documents/{uuid.uuid4()}.pdf"
    storage = R2Storage()

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".pdf", delete=False
        ) as temp_file:
            temp_path = temp_file.name
            while True:
                data = file.file.read(1024 * 1024)
                if not data:
                    break
                temp_file.write(data)

        with open(temp_path, "rb") as pdf_file:
            if pdf_file.read(5) != b"%PDF-":
                raise HTTPException(
                    status_code=400,
                    detail="The uploaded file is not a valid PDF.",
                )
            pdf_file.seek(0)
            storage.upload_file(
                pdf_file,
                object_key,
                "application/pdf",
            )

        document = Document(
            user_id=user_id,
            filename=Path(file.filename).name,
            storage_path=object_key,
            file_type="pdf",
            status="pending",
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        try:
            chunks = ingest_document(
                db=db,
                document_id=document.id,
                file_path=temp_path,
            )

            if not chunks:
                raise ValueError("No extractable text was found in the PDF.")

            document.status = "processed"
            db.commit()
            db.refresh(document)

        except Exception:
            db.rollback()
            document = (
                db.query(Document)
                .filter(Document.id == document.id)
                .first()
            )
            if document is not None:
                document.status = "failed"
                db.commit()
            # Preserve the uploaded file in R2 for investigation/retry.

        return document

    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Document upload failed. Check the backend logs.",
        )
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        file.file.close()
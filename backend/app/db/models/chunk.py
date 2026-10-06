from sqlalchemy import Column, ForeignKey, Integer, String, Text
from app.db.database import Base
from pgvector.sqlalchemy  import Vector
class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    text = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    section = Column(String, nullable=True)
    embedding = Column(Vector(1024), nullable=True)

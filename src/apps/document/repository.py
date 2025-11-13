from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Document


class DocumentRepository:
    @staticmethod
    def create(db: Session, **data) -> Document:
        d = Document(**data)
        db.add(d)
        db.flush()
        db.refresh(d)
        return d

    @staticmethod
    def get_by_id(db: Session, document_id: str) -> Optional[Document]:
        return db.get(Document, document_id)

    @staticmethod
    def update_content(db: Session, doc: Document, content: str, is_finalized: bool) -> Document:
        doc.content = content
        doc.is_finalized = is_finalized
        db.flush()
        db.refresh(doc)
        return doc

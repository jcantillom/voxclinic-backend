from typing import Optional, Sequence
from sqlalchemy import select, func
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
    def list_by_tenant(
            db: Session, tenant_id, *, q: Optional[str] = None, document_type: Optional[str] = None,
            page: int = 1, page_size: int = 50
    ) -> Sequence[Document]:
        """Lista documentos por tenant con filtros básicos."""
        stmt = select(Document).where(Document.tenant_id == tenant_id)

        if document_type:
            stmt = stmt.where(Document.document_type == document_type)
        if q:
            # Buscar en título o contenido
            stmt = stmt.where(
                (Document.title.ilike(f"%{q}%")) | (Document.content.ilike(f"%{q}%"))
            )

        offset = (page - 1) * page_size
        rows = db.execute(
            stmt.order_by(Document.created_at.desc()).offset(offset).limit(page_size)
        ).scalars().all()
        return rows

    @staticmethod
    def update_content(db: Session, doc: Document, content: str, is_finalized: bool,
                       is_synced: bool = False) -> Document:
        doc.content = content
        doc.is_finalized = is_finalized
        doc.is_synced = is_synced
        db.flush()
        db.refresh(doc)
        return doc

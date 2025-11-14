from typing import Optional, Sequence, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from .models import Document


class DocumentRepository:
    @staticmethod
    def create(db: Session, **data) -> Document:
        p = Document(**data)
        db.add(p)
        db.flush()
        db.refresh(p)
        return p

    @staticmethod
    def get_by_id(db: Session, document_id: str) -> Optional[Document]:
        return db.get(Document, document_id)

    @staticmethod
    def update_content(
            db: Session, doc: Document, content: str, is_finalized: bool, is_synced: bool
    ) -> Document:
        doc.content = content
        doc.is_finalized = is_finalized
        doc.is_synced = is_synced  # Aseguramos que se pueda resetear si se edita
        db.flush()
        db.refresh(doc)
        return doc

    @staticmethod
    def list_by_tenant(
            db: Session, tenant_id, *, q: Optional[str] = None, document_type: Optional[str] = None,
            page: int = 1, page_size: int = 5
    ) -> Tuple[Sequence[Document], int]:
        """Lista documentos por tenant con filtros básicos y paginación."""

        # 1. Crear la base de la sentencia de selección
        stmt = select(Document).where(Document.tenant_id == tenant_id)

        # 2. Aplicar filtros (si existen)
        if document_type:
            stmt = stmt.where(Document.document_type == document_type)

        if q:
            # Búsqueda por título o contenido (ilike es sensible a Postgres)
            # Aseguramos que la búsqueda por 'q' siempre use minúsculas
            search_term = f"%{q.lower()}%"
            stmt = stmt.where(
                (Document.title.ilike(search_term)) | (Document.content.ilike(search_term))
            )

        # 3. Obtener el total (COUNT)
        # CORRECCIÓN: Usar .subquery() para el conteo y evitar el producto cartesiano (SAWarning)
        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.execute(total_stmt).scalar_one()

        # 4. Aplicar ordenamiento y paginación
        offset = (page - 1) * page_size
        rows = db.execute(
            stmt.order_by(Document.created_at.desc()).offset(offset).limit(page_size)
        ).scalars().all()

        return rows, total
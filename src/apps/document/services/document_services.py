import logging
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.apps.tenant.models import Tenant
from src.apps.users.models import User
from src.apps.recordings.models import Recording
from src.core.errors.errors import EntityNotFoundError, ConflictError
from src.apps.document.repository import DocumentRepository  # Importamos para tipado
from src.apps.document.models import Document
from src.apps.document.services.llm_service import AbstractLLMEngine
from datetime import datetime
from typing import Optional, Sequence, Tuple
from fastapi import BackgroundTasks

logger = logging.getLogger(__name__)


class DocumentService:
    # Constructor ahora recibe el repositorio y el LLM
    def __init__(self, repo: DocumentRepository, llm_engine: AbstractLLMEngine):
        self.repo = repo
        self.llm_engine = llm_engine

    def list_documents(self, db: Session, tenant_id: str, **kwargs) -> Tuple[Sequence[Document], int]:

        return self.repo.list_by_tenant(db, tenant_id, **kwargs)

    def update_document_content(
            self,
            db: Session,
            document_id: str,
            tenant_id: str,
            content: str,
            is_finalized: bool,
            is_synced: bool
    ) -> Document:
        doc = self.repo.get_by_id(db, document_id)
        if not doc or str(doc.tenant_id) != tenant_id:
            raise EntityNotFoundError("Document", "id", document_id)

        return self.repo.update_content(db, doc, content, is_finalized, is_synced)

    def export_to_his(self, db: Session, document_id: str, tenant: Tenant,
                      background_tasks: BackgroundTasks) -> Document:
        doc = self.repo.get_by_id(db, document_id)
        if not doc or str(doc.tenant_id) != str(tenant.id):
            raise EntityNotFoundError("Document", "id", document_id)

        if doc.is_synced:
            raise ConflictError("Document already synced with HIS.")

        doc = self.repo.update_content(db, doc, doc.content, True, False)

        doc = self.repo.update_content(db, doc, doc.content, True, True)

        return doc

    def get_by_id(self, db: Session, document_id: str) -> Document:
        doc = self.repo.get_by_id(db, document_id)
        if not doc:
            raise EntityNotFoundError("Document", "id", document_id)
        return doc
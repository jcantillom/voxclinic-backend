import logging
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.apps.tenant.models import Tenant
from src.apps.users.models import User
from src.apps.recordings.models import Recording
from src.core.errors.errors import EntityNotFoundError, ConflictError
from src.apps.document.repository import DocumentRepository
from src.apps.document.models import Document
from src.apps.document.services.llm_service import AbstractLLMEngine
from datetime import datetime
from typing import Optional, Sequence, Tuple
from fastapi import BackgroundTasks

logger = logging.getLogger(__name__)


class DocumentService:
    # Constructor (intacto)
    def __init__(self, repo: DocumentRepository, llm_engine: AbstractLLMEngine):
        self.repo = repo
        self.llm_engine = llm_engine

    # generate_and_save_document (intacto)
    def generate_and_save_document(
            self,
            db: Session,
            *,
            tenant: Tenant,
            user: User,
            recording: Recording,
            document_type: str,
            transcript: str,
            clinical_meta: dict
    ) -> Document:
        """
        Genera un documento clínico estructurado usando el LLM y lo guarda en la base de datos.
        """
        if str(recording.tenant_id) != str(tenant.id):
            raise ConflictError("Recording does not belong to the current tenant.")

        existing_doc = db.execute(
            select(Document).where(Document.recording_id == recording.id)
        ).scalar_one_or_none()

        if existing_doc:
            raise ConflictError(f"A Document (ID: {existing_doc.id}) already exists for this Recording.")

        # --- 1. LLAMADA AL LLM ---
        title = f"{document_type.replace('_', ' ').title()} generado"

        document_body = self.llm_engine.structure_document(
            document_type,
            transcript,
            clinical_meta
        )

        # --- 2. CONSTRUIR DOCUMENTO FINAL ---
        structured_content = self._build_final_document(
            document_type,
            tenant,
            user,
            clinical_meta,
            document_body
        )

        # --- 3. CREACIÓN EN DB ---
        doc = self.repo.create(
            db,
            tenant_id=tenant.id,
            user_id=user.id,
            recording_id=recording.id,
            document_type=document_type,
            title=title,
            content=structured_content,
            clinical_meta=clinical_meta,
            is_finalized=False,
            is_synced=False
        )
        return doc

    # list_documents (intacto)
    def list_documents(self, db: Session, tenant_id: str, **kwargs) -> Tuple[Sequence[Document], int]:
        return self.repo.list_by_tenant(db, tenant_id, **kwargs)

    # update_document_content (intacto)
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

    # export_to_his (intacto)
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

    # -----------------------------------------------------------
    # LÓGICA INTERNA Y FORMATO
    # -----------------------------------------------------------

    def _build_final_document(
            self, doc_type: str, tenant: Tenant, user: User, meta: dict, document_body: str
    ) -> str:
        """
        Construye el contenido final. Quitamos toda la estructura Markdown/HTML de aquí
        para que el LLM lo maneje. Solo insertamos marcadores y el cuerpo.
        """
        doctor_name = user.full_name
        current_time = datetime.now().strftime('%H:%M:%S')

        # Marcador de Encabezado (para que el frontend sepa que es el documento oficial)
        official_header = "--- INFORME MÉDICO OFICIAL ---\n"

        # Marcador de pie de página para la validación (va al final del documento)
        footer = f"\n\n--- FIN DEL INFORME ---\n[Documento Validado por DataVox Medical a las {current_time} por {doctor_name}]\n"

        # Devolvemos: Marcador + Cuerpo LLM + Pie de página
        return official_header + document_body + footer

    def get_by_id(self, db: Session, document_id: str) -> Document:
        doc = self.repo.get_by_id(db, document_id)
        if not doc:
            raise EntityNotFoundError("Document", "id", document_id)
        return doc

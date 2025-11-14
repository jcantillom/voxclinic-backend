import logging
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.apps.tenant.models import Tenant
from src.apps.users.models import User
from src.apps.recordings.models import Recording
from src.core.errors.errors import EntityNotFoundError, ConflictError
from .repository import DocumentRepository
from .models import Document
from datetime import datetime
from typing import Optional, Sequence, Tuple
from fastapi import BackgroundTasks

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self, repo: DocumentRepository):
        self.repo = repo
        # SUPOSICIÓN: Se instancia el servicio de integración
        # self.integration_service = IntegrationService()

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
        Genera el contenido del documento basado en la transcripción y el tipo, y lo guarda.
        """
        if str(recording.tenant_id) != str(tenant.id):
            raise ConflictError("Recording does not belong to the current tenant.")

        # Verificar si ya existe un Documento asociado a este Recording ID
        existing_doc = db.execute(
            select(Document).where(Document.recording_id == recording.id)
        ).scalar_one_or_none()

        if existing_doc:
            raise ConflictError(f"A Document (ID: {existing_doc.id}) already exists for this Recording.")

        # --- Lógica de Generación Estructurada (Simulada) ---
        title = f"{document_type.replace('_', ' ').title()} generado"

        structured_content = self._structure_document(
            document_type,
            tenant.name,
            user.full_name,
            transcript,
            clinical_meta
        )

        # --- Creación en DB ---
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
            is_synced=False  # Por defecto no sincronizado
        )

        return doc

    def list_documents(self, db: Session, tenant_id: str, **kwargs) -> Tuple[Sequence[Document], int]:
        """Lista documentos con filtros y paginación y devuelve (rows, total)."""
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
        """
        Marca el documento como finalizado (si no lo estaba) y dispara la tarea de integración.
        """
        doc = self.repo.get_by_id(db, document_id)
        if not doc or str(doc.tenant_id) != str(tenant.id):
            raise EntityNotFoundError("Document", "id", document_id)

        if doc.is_synced:
            raise ConflictError("Document already synced with HIS.")

        # 1. Marcar como finalizado (si no lo está) y pendiente de sincronización
        doc = self.repo.update_content(db, doc, doc.content, True, False)

        # 2. Disparar la integración asíncrona
        # background_tasks.add_task(
        #     self.integration_service.send_document,
        #     tenant_code=tenant.code,
        #     document=doc,
        # )

        # SUPOSICIÓN MVP: Marcamos inmediatamente como sincronizado en el entorno de demo
        doc = self.repo.update_content(db, doc, doc.content, True, True)

        return doc

    def _structure_document(
            self, doc_type: str, tenant_name: str, doctor_name: str, transcript: str, meta: dict
    ) -> str:
        """Simula la generación de contenido estructurado (MVP)."""
        patient_info = meta.get('patient_id', 'N/A')
        clinical_subject = meta.get('clinical_subject', 'Sin foco')

        header = f"""
{tenant_name} | 
DOCUMENTO MÉDICO: {doc_type.upper().replace('_', ' ')}
PACIENTE ID: {patient_info}
MÉDICO: {doctor_name}
ASUNTO: {clinical_subject}
FECHA: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        """
        footer = f"\n\n--- FIN DEL INFORME ---\n[ESTADO: FINALIZADO Y PENDIENTE DE SINCRONIZACIÓN HIS]\n"

        if doc_type == "radiology_report":
            return f"{header}\nINFORME RADIOLÓGICO\n\nHALLAZGOS:\n{transcript}\n\nIMPRESIÓN DIAGNÓSTICA:\n[Generada por IA - Revisar]\n{footer}"

        if doc_type == "clinical_history":
            return f"{header}\nHISTORIA CLÍNICA\n\nMOTIVO DE CONSULTA:\n{clinical_subject}\n\nANAMNESIS DETALLADA:\n{transcript}\n\nPLAN:\n[Generado por IA - Revisar]{footer}"

        return f"{header}\nTRANSCRIPCIÓN:\n{transcript}{footer}"

    def get_by_id(self, db: Session, document_id: str) -> Document:
        doc = self.repo.get_by_id(db, document_id)
        if not doc:
            raise EntityNotFoundError("Document", "id", document_id)
        return doc

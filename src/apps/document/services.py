import logging
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.apps.tenant.models import Tenant
from src.apps.users.models import User
from src.apps.recordings.models import Recording
from src.core.errors.errors import EntityNotFoundError, ConflictError
from .repository import DocumentRepository
from .models import Document
from datetime import datetime  # Asegurar importación de datetime

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self, repo: DocumentRepository):
        self.repo = repo

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

        # CORRECCIÓN: Verificar si ya existe un Documento asociado a este Recording ID
        existing_doc = db.execute(
            select(Document).where(Document.recording_id == recording.id)
        ).scalar_one_or_none()

        if existing_doc:
            raise ConflictError(f"A Document (ID: {existing_doc.id}) already exists for this Recording.")

        # --- Lógica de Generación Estructurada (Simulada) ---
        title = f"{document_type.replace('_', ' ').title()} generado"

        # Simulación: Estructura el texto con membrete (esto sería lógica compleja de Jinja/NLP)
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
            recording_id=recording.id,  # Usamos recording.id (UUID)
            document_type=document_type,
            title=title,
            content=structured_content,
            clinical_meta=clinical_meta,
            is_finalized=False  # Listo para revisión
        )

        return doc

    def update_document_content(
            self,
            db: Session,
            document_id: str,
            tenant_id: str,
            content: str,
            is_finalized: bool
    ) -> Document:
        doc = self.repo.get_by_id(db, document_id)
        if not doc or str(doc.tenant_id) != tenant_id:
            raise EntityNotFoundError("Document", "id", document_id)

        return self.repo.update_content(db, doc, content, is_finalized)

    def _structure_document(
            self, doc_type: str, tenant_name: str, doctor_name: str, transcript: str, meta: dict
    ) -> str:
        """Simula la generación de contenido estructurado (MVP)."""
        header = f"--- {tenant_name} ---\nDOCUMENTO MÉDICO: {doc_type.upper().replace('_', ' ')}\nMÉDICO: {doctor_name}\nFECHA: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n---"
        footer = f"\n\n--- FIN DEL INFORME ---\n[ESTADO: PENDIENTE DE FIRMA]\n"

        # La lógica real aquí usaría un modelo de lenguaje para clasificar el texto.
        if doc_type == "radiology_report":
            return f"{header}\n\nINFORME RADIOLÓGICO\n\nHALLAZGOS:\n{transcript}\n\nIMPRESIÓN DIAGNÓSTICA:\n[Generada por IA - Revisar]\n{footer}"

        if doc_type == "clinical_history":
            return f"{header}\n\nHISTORIA CLÍNICA\n\nMOTIVO DE CONSULTA:\n{transcript[:100]}...\n\nANAMNESIS:\n{transcript}\n\nPLAN:\n[Generado por IA - Revisar]{footer}"

        return f"{header}\n\nTRANSCRIPCIÓN COMPLETA:\n{transcript}{footer}"

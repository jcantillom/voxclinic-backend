from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from src.core.connections.deps import get_db, get_current_tenant, get_current_user
from src.core.middlewares.permissions import require_roles
from src.apps.recordings.services.recording_service import RecordingService
from src.apps.recordings.dependencies import get_recording_service
from src.core.errors.errors import EntityNotFoundError
from .services import DocumentService
from .repository import DocumentRepository
from .schemas import DocumentGenerateIn, DocumentOut, DocumentContentUpdate

router = APIRouter(prefix="/documents", tags=["Documents"])


def get_document_service() -> DocumentService:
    return DocumentService(DocumentRepository())


@router.post(
    "/generate",
    response_model=DocumentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Generar y guardar documento clínico desde una transcripción",
    dependencies=[Depends(require_roles("owner", "admin", "staff"))],
)
def generate_document(
        payload: DocumentGenerateIn,
        db: Session = Depends(get_db),
        tenant=Depends(get_current_tenant),
        user=Depends(get_current_user),
        recording_service: RecordingService = Depends(get_recording_service),
        doc_service: DocumentService = Depends(get_document_service),
):
    recording = recording_service.get(db, payload.recording_id)
    if not recording or str(recording.tenant_id) != str(tenant.id):
        raise EntityNotFoundError("Recording", "id", payload.recording_id)

    if recording.status != "completed":
        raise HTTPException(
            status_code=409,
            detail=f"Recording status is '{recording.status}', must be 'completed' to generate document."
        )

    doc = doc_service.generate_and_save_document(
        db,
        tenant=tenant,
        user=user,
        recording=recording,
        document_type=payload.document_type,
        transcript=payload.transcript,
        clinical_meta=payload.clinical_meta
    )
    return DocumentOut.model_validate(doc)


@router.put(
    "/{document_id}/content",
    response_model=DocumentOut,
    summary="Actualizar contenido y estado de finalización del documento",
    dependencies=[Depends(require_roles("owner", "admin", "staff"))],
)
def update_document_content(
        document_id: UUID,
        payload: DocumentContentUpdate,
        db: Session = Depends(get_db),
        tenant=Depends(get_current_tenant),
        _=Depends(get_current_user),
        doc_service: DocumentService = Depends(get_document_service),
):
    doc = doc_service.update_document_content(
        db,
        document_id=str(document_id),
        tenant_id=str(tenant.id),
        content=payload.content,
        is_finalized=payload.is_finalized
    )
    return DocumentOut.model_validate(doc)



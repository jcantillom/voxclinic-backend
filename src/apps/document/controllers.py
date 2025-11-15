from typing import List
from fastapi import APIRouter, Depends, status, HTTPException, Query, Response, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID
from src.core.connections.deps import get_db, get_current_tenant, get_current_user
from src.core.middlewares.permissions import require_roles
from src.apps.recordings.services.recording_service import RecordingService
from src.apps.recordings.dependencies import get_recording_service
from src.core.errors.errors import EntityNotFoundError, ConflictError
from src.apps.document.services.document_services import DocumentService
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


# NUEVO ENDPOINT: Obtener documento por ID
@router.get(
    "/{document_id}",
    response_model=DocumentOut,
    summary="Obtener documento clínico por ID",
    dependencies=[Depends(require_roles("owner", "admin", "staff", "viewer"))],
)
def get_document(
        document_id: UUID,
        db: Session = Depends(get_db),
        tenant=Depends(get_current_tenant),
        doc_service: DocumentService = Depends(get_document_service),
):
    doc = doc_service.get_by_id(db, str(document_id))
    if not doc or str(doc.tenant_id) != str(tenant.id):
        raise EntityNotFoundError("Document", "id", document_id)
    return DocumentOut.model_validate(doc)


@router.get(
    "",
    response_model=List[DocumentOut],
    summary="Listar documentos clínicos del tenant (para Reportes)",
    dependencies=[Depends(require_roles("owner", "admin", "staff", "viewer"))],
)
def list_documents(
        response: Response,  # Necesitamos el objeto Response para modificar los headers
        db: Session = Depends(get_db),
        tenant=Depends(get_current_tenant),
        q: str | None = Query(None, description="Buscar en título o contenido"),
        document_type: str | None = Query(None, description="Filtrar por tipo de documento"),
        page: int = Query(1, ge=1),
        page_size: int = Query(5, ge=1, le=50),  # CAMBIO: Establecemos 5 por defecto
        doc_service: DocumentService = Depends(get_document_service),
):
    rows, total = doc_service.list_documents(
        db,
        str(tenant.id),
        q=q,
        document_type=document_type,
        page=page,
        page_size=page_size
    )
    # CORRECCIÓN CLAVE: Agregar el header para que el frontend pueda calcular las páginas
    response.headers["X-Total-Count"] = str(total)

    return [DocumentOut.model_validate(x) for x in rows]


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
        is_finalized=payload.is_finalized,
        is_synced=payload.is_synced
    )
    return DocumentOut.model_validate(doc)


@router.post(
    "/{document_id}/export",
    response_model=DocumentOut,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Disparar exportación del documento finalizado al HIS/EMR",
    dependencies=[Depends(require_roles("owner", "admin", "staff"))],
)
def export_document_to_his(
        document_id: str,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db),
        tenant=Depends(get_current_tenant),
        _=Depends(get_current_user),
        doc_service: DocumentService = Depends(get_document_service),
):
    # El servicio se encarga de la lógica de sincronización asíncrona
    updated_doc = doc_service.export_to_his(db, document_id, tenant, background_tasks)
    return DocumentOut.model_validate(updated_doc)

from typing import List
from fastapi import APIRouter, Depends, Query, Response, status, HTTPException
from sqlalchemy.orm import Session
from src.core.connections.deps import get_db, get_current_tenant, get_current_user
from src.core.middlewares.permissions import require_roles
from .schemas import RecordingCreate, RecordingOut, RecordingUpdateStatus, RecordingAttachTranscript
from .services import RecordingService
from .repository import RecordingRepository
from .transcription_service import TranscriptionService

router = APIRouter(prefix="/recordings", tags=["recordings"])

ALLOWED_CT = {
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/webm",
    "audio/ogg",
}


def get_service() -> RecordingService:
    return RecordingService(RecordingRepository())


@router.post(
    "",
    response_model=RecordingOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un audio recién subido a S3",
    dependencies=[Depends(require_roles("owner", "admin", "staff"))],
)
def register_recording(
        payload: RecordingCreate,
        db: Session = Depends(get_db),
        tenant=Depends(get_current_tenant),
        me=Depends(get_current_user),
):
    if payload.content_type not in ALLOWED_CT:
        raise HTTPException(
            status_code=400,
            detail=f"content_type '{payload.content_type}' no es soportado. "
                   f"Los tipos permitidos son: {', '.join(ALLOWED_CT)}"
        )
    svc = get_service()
    r = svc.register_upload(
        db,
        tenant=tenant,
        user=me,
        bucket=payload.bucket,
        key=payload.key,
        content_type="audio/wav" if payload.content_type == "audio/x-wav" else payload.content_type,
        size_bytes=payload.size_bytes,
        duration_sec=payload.duration_sec,
    )
    return RecordingOut.model_validate(r)


@router.get(
    "",
    response_model=List[RecordingOut],
    summary="Listar recordings",
    dependencies=[Depends(require_roles("owner", "admin", "staff", "viewer"))],
)
def list_recordings(
        response: Response,
        db: Session = Depends(get_db),
        tenant=Depends(get_current_tenant),
        _=Depends(get_current_user),
        q: str | None = Query(None, description="Buscar por key"),
        status_q: str | None = Query(None, pattern="^(uploaded|processing|completed|failed)$"),
        page: int = Query(1, ge=1),
        page_size: int = Query(50, ge=1, le=200),
):
    svc = get_service()
    rows, total = svc.list(db, tenant=tenant, q=q, status=status_q, page=page, page_size=page_size)
    response.headers["X-Total-Count"] = str(total)
    return [RecordingOut.model_validate(x) for x in rows]


@router.get(
    "/{recording_id}",
    response_model=RecordingOut,
    summary="Obtener recording por id",
    dependencies=[Depends(require_roles("owner", "admin", "staff", "viewer"))],
)
def get_recording(
        recording_id: str,
        db: Session = Depends(get_db),
        tenant=Depends(get_current_tenant),
        _=Depends(get_current_user),
        svc: RecordingService = Depends(get_service)
):
    r = svc.get(db, recording_id)
    if not r or str(r.tenant_id) != str(tenant.id):
        raise HTTPException(status_code=404, detail="Recording not found")
    return RecordingOut.model_validate(r)


@router.put(
    "/{recording_id}/status",
    response_model=RecordingOut,
    summary="Actualizar estado del recording",
    dependencies=[Depends(require_roles("owner", "admin", "staff"))],
)
def update_recording_status(
        recording_id: str,
        payload: RecordingUpdateStatus,
        db: Session = Depends(get_db),
        tenant=Depends(get_current_tenant),
        _=Depends(get_current_user),
        svc: RecordingService = Depends(get_service)
):
    r = svc.get(db, recording_id)
    if not r or str(r.tenant_id) != str(tenant.id):
        raise HTTPException(status_code=404, detail="Recording not found")
    r = svc.update_status(db, r, payload.status, payload.error_message)
    return RecordingOut.model_validate(r)


@router.put(
    "/{recording_id}/transcript",
    response_model=RecordingOut,
    summary="Adjuntar transcripción (marca completed)",
    dependencies=[Depends(require_roles("owner", "admin", "staff"))],
)
def attach_transcript(
        recording_id: str,
        payload: RecordingAttachTranscript,
        db: Session = Depends(get_db),
        tenant=Depends(get_current_tenant),
        _=Depends(get_current_user),
        svc: RecordingService = Depends(get_service)
):
    r = svc.get(db, recording_id)
    if not r or str(r.tenant_id) != str(tenant.id):
        raise HTTPException(status_code=404, detail="Recording not found")
    r = svc.set_transcript(db, r, payload.transcript_text, payload.duration_sec)
    return RecordingOut.model_validate(r)


@router.post(
    "/{recording_id}/transcribe",
    response_model=RecordingOut,
    summary="Iniciar transcripción de audio",
    dependencies=[Depends(require_roles("owner", "admin", "staff"))],
)
def start_transcription(
        recording_id: str,
        db: Session = Depends(get_db),
        tenant=Depends(get_current_tenant),
        _=Depends(get_current_user),
        svc: RecordingService = Depends(get_service)
):
    """Iniciar proceso de transcripción para un audio"""
    recording = svc.get(db, recording_id)
    if not recording or str(recording.tenant_id) != str(tenant.id):
        raise HTTPException(status_code=404, detail="Recording not found")

    # Iniciar transcripción
    transcription_svc = TranscriptionService()
    success = transcription_svc.start_transcription_job(recording)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to start transcription")

    # Actualizar estado
    recording = svc.update_status(db, recording, "processing")
    return RecordingOut.model_validate(recording)


@router.get(
    "/{recording_id}/transcription-status",
    summary="Obtener estado de la transcripción",
    dependencies=[Depends(require_roles("owner", "admin", "staff", "viewer"))],
)
def get_transcription_status(
        recording_id: str,
        db: Session = Depends(get_db),
        tenant=Depends(get_current_tenant),
        _=Depends(get_current_user),
        svc: RecordingService = Depends(get_service)
):
    """Consultar estado del trabajo de transcripción"""
    recording = svc.get(db, recording_id)
    if not recording or str(recording.tenant_id) != str(tenant.id):
        raise HTTPException(status_code=404, detail="Recording not found")

    transcription_svc = TranscriptionService()
    job_name = f"transcribe-{recording.id}-{int(recording.created_at.timestamp())}"
    result = transcription_svc.get_transcription_result(job_name[:200])  # Limitar longitud

    if result and result['job_status'] == 'COMPLETED' and result['text']:
        # Actualizar recording con el texto transcrito
        recording = svc.set_transcript(db, recording, result['text'])

    return {
        "recording_id": recording_id,
        "transcription_status": result['job_status'] if result else 'UNKNOWN',
        "transcript_text": result['text'] if result and 'text' in result else None,
        "error": result.get('error') if result else None
    }

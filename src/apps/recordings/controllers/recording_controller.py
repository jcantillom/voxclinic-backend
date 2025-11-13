# src/apps/recordings/controllers/recording_controller.py
from typing import List
from fastapi import APIRouter, Depends, Query, Response, status, HTTPException
from sqlalchemy.orm import Session
from src.core.connections.deps import get_db, get_current_tenant, get_current_user
from src.core.middlewares.permissions import require_roles
from ..schemas import RecordingCreate, RecordingOut, RecordingUpdateStatus, RecordingAttachTranscript
from ..dependencies import get_recording_service, get_transcription_service
from ..services.recording_service import RecordingService
from ..services.transcription_service import TranscriptionService

router = APIRouter(prefix="/recordings", tags=["recordings"])

ALLOWED_CT = {
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/webm",
    "audio/ogg",
}


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
        recording_service: RecordingService = Depends(get_recording_service),
):
    if payload.content_type not in ALLOWED_CT:
        raise HTTPException(
            status_code=400,
            detail=f"content_type '{payload.content_type}' no es soportado. "
                   f"Los tipos permitidos son: {', '.join(ALLOWED_CT)}"
        )
    r = recording_service.register_upload(
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
        recording_service: RecordingService = Depends(get_recording_service),
):
    rows, total = recording_service.list(db, tenant=tenant, q=q, status=status_q, page=page, page_size=page_size)
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
        recording_service: RecordingService = Depends(get_recording_service),
):
    r = recording_service.get(db, recording_id)
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
        recording_service: RecordingService = Depends(get_recording_service),
):
    r = recording_service.get(db, recording_id)
    if not r or str(r.tenant_id) != str(tenant.id):
        raise HTTPException(status_code=404, detail="Recording not found")
    r = recording_service.update_status(db, r, payload.status, payload.error_message)
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
        recording_service: RecordingService = Depends(get_recording_service),
):
    r = recording_service.get(db, recording_id)
    if not r or str(r.tenant_id) != str(tenant.id):
        raise HTTPException(status_code=404, detail="Recording not found")
    r = recording_service.set_transcript(db, r, payload.transcript_text, payload.duration_sec)
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
        recording_service: RecordingService = Depends(get_recording_service),
        transcription_service: TranscriptionService = Depends(get_transcription_service),
):
    """Iniciar proceso de transcripción para un audio"""
    recording = recording_service.get(db, recording_id)
    if not recording or str(recording.tenant_id) != str(tenant.id):
        raise HTTPException(status_code=404, detail="Recording not found")

    # Iniciar transcripción
    success = transcription_service.start_transcription_job(recording)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to start transcription")

    # Actualizar estado
    recording = recording_service.update_status(db, recording, "processing")
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
        recording_service: RecordingService = Depends(get_recording_service),
        transcription_service: TranscriptionService = Depends(get_transcription_service),
):
    """Consultar estado del trabajo de transcripción"""
    recording = recording_service.get(db, recording_id)
    if not recording or str(recording.tenant_id) != str(tenant.id):
        raise HTTPException(status_code=404, detail="Recording not found")

    # Obtener estado de la transcripción
    result = transcription_service.get_transcription_status(recording)

    # Si la transcripción está completada, actualizar el recording
    if result["transcription_status"] == "COMPLETED" and result["transcript_text"]:
        recording = recording_service.set_transcript(db, recording, result["transcript_text"])

    return {
        "recording_id": recording_id,
        "transcription_status": result["transcription_status"],
        "transcript_text": result["transcript_text"],
        "error": result["error"]
    }

from typing import List
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session
from src.core.connections.deps import get_db, get_current_tenant, get_current_user
from src.core.middlewares.permissions import require_roles
from .schemas import RecordingCreate, RecordingOut
from .services import RecordingService
from .repository import RecordingRepository

router = APIRouter(prefix="/recordings", tags=["recordings"])


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
    svc = get_service()
    r = svc.register_upload(
        db,
        tenant=tenant,
        user=me,
        bucket=payload.bucket,
        key=payload.key,
        content_type=payload.content_type,
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

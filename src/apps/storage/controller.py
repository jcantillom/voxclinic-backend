from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.core.connections.deps import get_db, get_current_tenant, get_current_user
from src.core.middlewares.permissions import require_roles
from .schemas import PresignPutIn, PresignPutOut
from .services import StorageService

router = APIRouter(prefix="/storage", tags=["storage"])


def get_service() -> StorageService:
    return StorageService()


@router.post(
    "/presign/put",
    response_model=PresignPutOut,
    status_code=status.HTTP_200_OK,
    summary="Genera URL prefirmada para subir audio (PUT) a S3",
    dependencies=[Depends(require_roles("owner", "admin", "staff"))],
)
def presign_put(
        payload: PresignPutIn,
        db: Session = Depends(get_db),  # por consistencia de deps (auditoría futura)
        tenant=Depends(get_current_tenant),
        me=Depends(get_current_user),
        svc: StorageService = Depends(get_service),
):
    """
    Devuelve URL prefirmada y headers requeridos.
    El backend NO recibe el archivo; el frontend lo sube directo a S3.
    """
    key = svc.build_key(
        folder=payload.folder or "recordings",
        tenant_code=tenant.code,
        user_id=str(me.id),
        content_type=payload.content_type,
        filename=payload.filename,
    )

    out = svc.presign_put(key=key, content_type=payload.content_type, expires_sec=900)
    return PresignPutOut(**out)

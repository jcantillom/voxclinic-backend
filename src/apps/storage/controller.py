from uuid import uuid4
from fastapi import APIRouter, Depends, status
from src.core.connections.deps import get_current_user, get_current_tenant
from .schemas import PresignPutIn, PresignPutOut
from .services import StorageService

router = APIRouter(prefix="/storage", tags=["storage"])


def get_service() -> StorageService:
    return StorageService()


@router.post(
    "/presign/put",
    response_model=PresignPutOut,
    status_code=status.HTTP_200_OK,
    summary="Generar URL prefirmada para subir un archivo a S3 (PUT)",
)
def presign_put(
        payload: PresignPutIn,
        _user=Depends(get_current_user),  # exige auth
        _tenant=Depends(get_current_tenant)
):
    svc = get_service()

    # Generamos una key limpia y única por carpeta
    # Ejemplo: recordings/2025-11-12/<uuid>__nombre.ext   (simple por ahora)
    key = f"{payload.folder}/{uuid4()}__{payload.filename}"

    out = svc.presign_put(
        key=key,
        content_type=payload.content_type,
        expires_sec=900,  # 15 min
    )
    return PresignPutOut(**out)

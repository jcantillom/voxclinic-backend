from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.core.connections.deps import get_db
from .services import TenantService
from .repository import TenantRepository
from .schemas import TenantSchema, TenantCreate

router = APIRouter(prefix="/tenants", tags=["tenants"])


def get_service(db: Session = Depends(get_db)) -> TenantService:
    return TenantService(TenantRepository())


@router.get("", response_model=List[TenantSchema], summary="Listar tenants")
def list_tenants(svc: TenantService = Depends(get_service), db: Session = Depends(get_db)):
    rows = svc.get_all(db)
    return [TenantSchema.model_validate(x) for x in rows]


# Opcional: crear tenant (útil para probar end-to-end)
@router.post("", response_model=TenantSchema, status_code=status.HTTP_201_CREATED, summary="Crear tenant")
def create_tenant(payload: TenantCreate, svc: TenantService = Depends(get_service), db: Session = Depends(get_db)):
    t = svc.create(db, code=payload.code, name=payload.name, meta=payload.meta)
    return TenantSchema.model_validate(t)


# Opcional: obtener por code
@router.get("/by-code", response_model=TenantSchema, summary="Obtener tenant por code")
def get_tenant_by_code(
        code: str = Query(..., max_length=120),
        svc: TenantService = Depends(get_service),
        db: Session = Depends(get_db),
):
    t = svc.get_by_code(db, code)
    return TenantSchema.model_validate(t)

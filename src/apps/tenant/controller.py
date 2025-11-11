# src/apps/tenant/controller.py
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.core.connections.deps import get_db
from .services import TenantService
from .repository import TenantRepository
from .schemas import (
    TenantSchema, TenantCreate, TenantUpdateName,
    TenantUpdateCode, TenantUpdateStatus, TenantUpdateMeta,
    TenantPatch,
)

router = APIRouter(prefix="/tenants", tags=["Tenants"])


def get_service() -> TenantService:
    return TenantService(TenantRepository())


# ============================================================
#                         READ
# ============================================================
@router.get("", response_model=List[TenantSchema], summary="Listar tenants")
def list_tenants(
    svc: TenantService = Depends(get_service),
    db: Session = Depends(get_db),
):
    rows = svc.get_all(db)
    return [TenantSchema.model_validate(x) for x in rows]


@router.get("/by-code", response_model=TenantSchema, summary="Obtener tenant por code")
def get_tenant_by_code(
    code: str = Query(..., max_length=120),
    svc: TenantService = Depends(get_service),
    db: Session = Depends(get_db),
):
    t = svc.get_by_code(db, code)
    return TenantSchema.model_validate(t)


# ============================================================
#                        CREATE
# ============================================================
@router.post(
    "",
    response_model=TenantSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Crear tenant",
)
def create_tenant(
    payload: TenantCreate,
    svc: TenantService = Depends(get_service),
    db: Session = Depends(get_db),
):
    t = svc.create(db, code=payload.code, name=payload.name, meta=payload.meta)
    return TenantSchema.model_validate(t)


# ============================================================
#                        UPDATE (PUT parciales)
# ============================================================
@router.put(
    "/{tenant_id}/name",
    response_model=TenantSchema,
    summary="Actualizar nombre del tenant",
)
def update_tenant_name(
    tenant_id: str,
    payload: TenantUpdateName,
    svc: TenantService = Depends(get_service),
    db: Session = Depends(get_db),
):
    t = svc.update_name(db, tenant_id, payload.name)
    return TenantSchema.model_validate(t)


@router.put(
    "/{tenant_id}/code",
    response_model=TenantSchema,
    summary="Actualizar code del tenant",
)
def update_tenant_code(
    tenant_id: str,
    payload: TenantUpdateCode,
    svc: TenantService = Depends(get_service),
    db: Session = Depends(get_db),
):
    t = svc.update_code(db, tenant_id, payload.code)
    return TenantSchema.model_validate(t)


@router.put(
    "/{tenant_id}/status",
    response_model=TenantSchema,
    summary="Activar/Desactivar tenant",
)
def update_tenant_status(
    tenant_id: str,
    payload: TenantUpdateStatus,
    svc: TenantService = Depends(get_service),
    db: Session = Depends(get_db),
):
    t = svc.update_status(db, tenant_id, payload.is_active)
    return TenantSchema.model_validate(t)


@router.put(
    "/{tenant_id}/meta",
    response_model=TenantSchema,
    summary="Reemplazar meta (PUT)",
)
def replace_tenant_meta(
    tenant_id: str,
    payload: TenantUpdateMeta,
    svc: TenantService = Depends(get_service),
    db: Session = Depends(get_db),
):
    t = svc.replace_meta(db, tenant_id, payload.meta)
    return TenantSchema.model_validate(t)


# ============================================================
#                         PATCH (merge)
# ============================================================
@router.patch(
    "/{tenant_id}",
    response_model=TenantSchema,
    summary="Actualizar parcialmente (merge)",
)
def patch_tenant(
    tenant_id: str,
    payload: TenantPatch,
    svc: TenantService = Depends(get_service),
    db: Session = Depends(get_db),
):
    t = svc.patch(
        db,
        tenant_id,
        name=payload.name,
        code=payload.code,
        is_active=payload.is_active,
        meta=payload.meta,
    )
    return TenantSchema.model_validate(t)

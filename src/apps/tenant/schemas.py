# src/apps/tenant/schemas.py
from typing import Dict, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class TenantSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str = Field(..., max_length=255)
    code: str = Field(..., max_length=120)
    is_active: bool
    meta: Dict
    created_at: datetime
    updated_at: datetime


class TenantCreate(BaseModel):
    code: str = Field(..., max_length=120)
    name: str = Field(..., max_length=255)
    meta: Dict = {}


class TenantUpdateName(BaseModel):
    name: str = Field(..., max_length=255)


class TenantUpdateCode(BaseModel):
    code: str = Field(..., max_length=120)


class TenantUpdateStatus(BaseModel):
    is_active: bool


class TenantUpdateMeta(BaseModel):
    """
    Reemplazo completo de meta (PUT).
    Si prefieres merge fino, usa el PATCH de abajo.
    """
    meta: Dict


class TenantPatch(BaseModel):
    """
    PATCH parcial tipo merge-patch:
    - Todos los campos son opcionales
    - Si no envías un campo, no se toca
    - `meta` si se envía, hace merge superficial (dict.update)
    """
    name: Optional[str] = Field(None, max_length=255)
    code: Optional[str] = Field(None, max_length=120)
    is_active: Optional[bool] = None
    meta: Optional[Dict] = None

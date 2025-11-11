from typing import Dict
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

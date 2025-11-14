from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class PatientCreate(BaseModel):
    identifier: str = Field(..., max_length=120, description="Cédula, DNI o ID de Historia Clínica.")
    full_name: str = Field(..., max_length=255)
    date_of_birth: Optional[datetime] = Field(None, description="Fecha de nacimiento para cálculo de edad.")
    is_active: bool = Field(True)
    meta: Optional[dict] = Field({}, description="Metadatos o información adicional (JSON).")


class PatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    identifier: str
    full_name: str
    date_of_birth: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PatientUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    date_of_birth: Optional[datetime] = None
    is_active: Optional[bool] = None
    meta: Optional[dict] = None

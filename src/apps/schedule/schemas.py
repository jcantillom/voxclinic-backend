from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class AppointmentCreate(BaseModel):
    patient_id: UUID
    start_time: datetime
    end_time: datetime
    reason: str = Field(..., max_length=255)


class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    user_id: Optional[UUID]  # Médico asignado
    patient_id: UUID
    start_time: datetime
    end_time: Optional[datetime]
    reason: str
    status: str
    created_at: datetime
from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class RecordingCreate(BaseModel):
    bucket: str = Field(..., max_length=255)
    key: str = Field(..., max_length=1024)
    content_type: str = "audio/wav"
    size_bytes: Optional[int] = None
    duration_sec: Optional[int] = None


class RecordingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    user_id: Optional[UUID]
    bucket: str
    key: str
    content_type: str
    size_bytes: Optional[int]
    duration_sec: Optional[int]
    status: str
    transcript_text: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

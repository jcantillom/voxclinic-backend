from typing import Optional, Dict
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from src.apps.document.models import DOCUMENT_TYPES


class DocumentGenerateIn(BaseModel):
    recording_id: UUID
    document_type: str = Field(..., pattern=f"^({'|'.join(DOCUMENT_TYPES)})$")
    transcript: str = Field(..., min_length=1)
    clinical_meta: Dict = {}


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    user_id: Optional[UUID]
    recording_id: Optional[UUID]
    document_type: str
    title: str
    content: str
    clinical_meta: Dict
    is_finalized: bool
    created_at: datetime
    updated_at: datetime


class DocumentContentUpdate(BaseModel):
    content: str = Field(..., min_length=1)
    is_finalized: bool = Field(False)
from typing import Optional, Dict
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., max_length=255)
    role: str = Field(..., pattern="^(owner|admin|staff|viewer)$")
    is_active: bool = True
    meta: Dict = {}  # opcional si luego quieres metadata de usuario


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8)
    role: str = Field(..., pattern="^(owner|admin|staff|viewer)$")


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime

class UserUpdateName(BaseModel):
    full_name: str = Field(..., max_length=255)


class UserUpdateActive(BaseModel):
    is_active: bool

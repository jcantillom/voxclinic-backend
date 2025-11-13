# src/apps/onboarding/schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class InstitutionOnboardingRequest(BaseModel):
    institution_type: str = Field(..., description="clinic|hospital|radiology_center|lab")
    institution_name: str = Field(..., max_length=255)
    contact_name: str = Field(..., max_length=255)
    contact_email: EmailStr
    contact_phone: str
    message: Optional[str] = None
    estimated_doctors: int = Field(gt=0)
    estimated_recordings_month: int = Field(gt=0)


class OnboardingResponse(BaseModel):
    request_id: str
    status: str
    message: str

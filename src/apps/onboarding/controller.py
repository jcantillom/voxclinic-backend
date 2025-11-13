# src/apps/onboarding/controller.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.core.connections.deps import get_db
from .schemas import InstitutionOnboardingRequest, OnboardingResponse
from .services import OnboardingService

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


def get_onboarding_service() -> OnboardingService:
    return OnboardingService()


@router.post(
    "/request-demo",
    response_model=OnboardingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Solicitar demostración para institución médica"
)
async def request_institution_demo(
        payload: InstitutionOnboardingRequest,
        db: Session = Depends(get_db),
        onboarding_service: OnboardingService = Depends(get_onboarding_service)
):
    """
    Endpoint para solicitudes de demostración institucional.
    Crea un tenant en estado pendiente y notifica al equipo comercial.
    """
    return await onboarding_service.process_onboarding_request(db, payload.dict())

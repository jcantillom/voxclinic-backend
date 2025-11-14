from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from src.core.connections.deps import get_db, get_current_tenant, get_current_user
from src.core.middlewares.permissions import require_roles
from .schemas import AppointmentCreate, AppointmentOut
from .services import AppointmentService
from .dependencies import get_appointment_service
from datetime import date

router = APIRouter(prefix="/schedule", tags=["Schedule"])


@router.post(
    "/appointments",
    response_model=AppointmentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva cita en la agenda",
    dependencies=[Depends(require_roles("owner", "admin", "staff"))],
)
def create_appointment(
        payload: AppointmentCreate,
        db: Session = Depends(get_db),
        tenant=Depends(get_current_tenant),
        user=Depends(get_current_user),
        svc: AppointmentService = Depends(get_appointment_service),
):
    appointment = svc.create_appointment(db, tenant=tenant, user=user, payload=payload.model_dump())
    return AppointmentOut.model_validate(appointment)


@router.get(
    "/daily",
    response_model=List[AppointmentOut],
    summary="Obtener agenda diaria del usuario logueado",
    dependencies=[Depends(require_roles("owner", "admin", "staff", "viewer"))],
)
def get_daily_schedule(
        date_str: str = Query(None, description="Fecha a consultar (YYYY-MM-DD). Por defecto: hoy."),
        db: Session = Depends(get_db),
        tenant=Depends(get_current_tenant),
        user=Depends(get_current_user),
        svc: AppointmentService = Depends(get_appointment_service),
):
    try:
        target_date = date.fromisoformat(date_str) if date_str else date.today()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    appointments = svc.get_daily_schedule(db, tenant=tenant, user=user, target_date=target_date)
    return [AppointmentOut.model_validate(a) for a in appointments]
from sqlalchemy.orm import Session
from src.core.errors.errors import EntityNotFoundError
from src.apps.tenant.models import Tenant
from src.apps.users.models import User
from src.apps.patients.repository import PatientRepository # Para validar paciente
from .repository import AppointmentRepository
from .models import Appointment
from datetime import date, datetime
from typing import Sequence


class AppointmentService:
    def __init__(self, repo: AppointmentRepository, patient_repo: PatientRepository):
        self.repo = repo
        self.patient_repo = patient_repo

    def create_appointment(
        self, db: Session, *, tenant: Tenant, user: User, payload: dict
    ) -> Appointment:
        # Validación de existencia del paciente
        patient_id = str(payload['patient_id'])
        if not self.patient_repo.get_by_id(db, patient_id):
            raise EntityNotFoundError("Patient", "id", patient_id)

        return self.repo.create(
            db,
            tenant_id=tenant.id,
            user_id=user.id,
            **payload
        )

    def get_daily_schedule(
        self, db: Session, *, tenant: Tenant, user: User, target_date: date
    ) -> Sequence[Appointment]:
        return self.repo.list_by_user_and_day(
            db,
            user_id=str(user.id),
            target_date=target_date,
            tenant_id=str(tenant.id)
        )
from datetime import datetime

from sqlalchemy.orm import Session
from src.core.errors.errors import EntityAlreadyExistsError, EntityNotFoundError
from src.apps.tenant.models import Tenant
from .repository import PatientRepository
from .models import Patient
from typing import Optional, Tuple, Sequence


class PatientService:
    def __init__(self, repo: PatientRepository):
        self.repo = repo

    def create_patient(
            self, db: Session, *, tenant: Tenant, identifier: str, full_name: str,
            date_of_birth: Optional[datetime] = None, is_active: bool = True, meta: Optional[dict] = None
    ) -> Patient:
        if self.repo.get_by_identifier(db, tenant.id, identifier):
            raise EntityAlreadyExistsError("Patient", "identifier", identifier)

        return self.repo.create(
            db,
            tenant_id=tenant.id,
            identifier=identifier,
            full_name=full_name,
            date_of_birth=date_of_birth,
            is_active=is_active,
            meta=meta
        )

    def search_patients(
            self,
            db: Session,
            *,
            tenant: Tenant,
            q: Optional[str] = None,
            page: int = 1,
            page_size: int = 50
    ) -> Tuple[Sequence[Patient], int]:
        return self.repo.list_by_tenant(db, tenant.id, q=q, page=page, page_size=page_size)

    def get_patient(self, db: Session, patient_id: str, tenant_id: str) -> Patient:
        p = self.repo.get_by_id(db, patient_id)
        if not p or str(p.tenant_id) != tenant_id:
            raise EntityNotFoundError("Patient", "id", patient_id)
        return p

    def update_patient(self, db: Session, patient_id: str, tenant_id: str, payload: dict) -> Patient:
        p = self.get_patient(db, patient_id, tenant_id)
        return self.repo.update(db, p, **payload)
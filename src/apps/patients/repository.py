from typing import Optional, Sequence, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from .models import Patient


class PatientRepository:
    @staticmethod
    def create(db: Session, **data) -> Patient:
        p = Patient(**data)
        db.add(p)
        db.flush()
        db.refresh(p)
        return p

    @staticmethod
    def get_by_id(db: Session, patient_id: str) -> Optional[Patient]:
        return db.get(Patient, patient_id)

    @staticmethod
    def get_by_identifier(db: Session, tenant_id: str, identifier: str) -> Optional[Patient]:
        return db.execute(
            select(Patient).where(
                Patient.tenant_id == tenant_id,
                Patient.identifier == identifier
            )
        ).scalar_one_or_none()

    @staticmethod
    def list_by_tenant(
            db: Session, tenant_id, *, q: Optional[str] = None, page: int = 1, page_size: int = 50
    ) -> Tuple[Sequence[Patient], int]:
        stmt = select(Patient).where(Patient.tenant_id == tenant_id)

        if q:
            # Búsqueda por nombre o identificador
            stmt = stmt.where(
                (Patient.full_name.ilike(f"%{q}%")) | (Patient.identifier.ilike(f"%{q}%"))
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.execute(count_stmt).scalar_one()

        offset = (page - 1) * page_size
        rows = db.execute(
            stmt.order_by(Patient.full_name.asc()).offset(offset).limit(page_size)
        ).scalars().all()
        return rows, total

    @staticmethod
    def update(db: Session, patient: Patient, **data) -> Patient:
        for key, value in data.items():
            if value is not None:
                setattr(patient, key, value)
        db.flush()
        db.refresh(patient)
        return patient
from typing import List, Optional, Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Tenant


class TenantRepository:
    """Acceso a datos para Tenant."""

    @staticmethod
    def get_all(db: Session) -> Sequence[Tenant]:
        return db.execute(select(Tenant)).scalars().all()

    @staticmethod
    def get_by_id(db: Session, tenant_id: str) -> Optional[Tenant]:
        return db.get(Tenant, tenant_id)

    @staticmethod
    def get_by_code(db: Session, code: str) -> Optional[Tenant]:
        return db.execute(
            select(Tenant).where(Tenant.code == code)
        ).scalar_one_or_none()

    @staticmethod
    def create(db: Session, *, code: str, name: str, meta: dict | None = None) -> Tenant:
        t = Tenant(
            code=code,
            name=name,
            meta=meta or {}
        )
        db.add(t)
        db.flush()
        db.refresh(t)
        return t

    @staticmethod
    def deactivate_tenant(db: Session, tenant_id: str) -> bool:
        t = db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        ).scalar_one_or_none()

        if not t:
            return False

        t.is_active = False
        return True

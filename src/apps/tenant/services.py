from typing import List, Sequence
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.apps.tenant.models import Tenant
from .repository import TenantRepository
from .models import Tenant

class TenantService:
    """Reglas de negocio para Tenant."""

    def __init__(self, repo: TenantRepository):
        self.repo = repo

    def get_all(self, db: Session) -> Sequence[Tenant]:
        return self.repo.get_all(db)

    def get_by_code(self, db: Session, code: str) -> Tenant:
        t = self.repo.get_by_code(db, code)
        if not t:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        return t

    def create(self, db: Session, *, code: str, name: str, meta: dict | None = None) -> Tenant:
        if self.repo.get_by_code(db, code):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tenant with this code already exists",
            )
        return self.repo.create(db, code=code, name=name, meta=meta)

    def deactivate_tenant(self, db: Session, tenant_id: str) -> bool:
        ok = self.repo.deactivate_tenant(db, tenant_id)
        if not ok:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        return ok

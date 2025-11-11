# src/apps/tenant/services.py
from typing import Sequence, Optional
from sqlalchemy.orm import Session
from .repository import TenantRepository
from .models import Tenant
from src.core.errors.errors import (
    EntityNotFoundError,
    EntityAlreadyExistsError,
    ConflictError,
)


class TenantService:
    """Reglas de negocio para Tenant."""

    def __init__(self, repo: TenantRepository):
        self.repo = repo

    #=========================================================
    #                      LIST / GET
    #=========================================================
    def get_all(self, db: Session) -> Sequence[Tenant]:
        return self.repo.get_all(db)

    def get_by_code(self, db: Session, code: str) -> Tenant:
        t = self.repo.get_by_code(db, code)
        if not t:
            raise EntityNotFoundError("Tenant", "code", code)
        return t

    def get_by_id(self, db: Session, tenant_id: str) -> Tenant:
        t = self.repo.get_by_id(db, tenant_id)
        if not t:
            raise EntityNotFoundError("Tenant", "id", tenant_id)
        return t

    #=========================================================
    #                      CREATE
    #=========================================================
    def create(self, db: Session, *, code: str, name: str, meta: dict | None = None) -> Tenant:
        if self.repo.get_by_code(db, code):
            raise EntityAlreadyExistsError("Tenant", "code", code)
        return self.repo.create(db, code=code, name=name, meta=meta)

    #=========================================================
    #                      UPDATE (PUT parciales)
    #=========================================================
    def update_name(self, db: Session, tenant_id: str, new_name: str) -> Tenant:
        t = self.get_by_id(db, tenant_id)
        return self.repo.update_name(db, t, new_name)

    def update_code(self, db: Session, tenant_id: str, new_code: str) -> Tenant:
        t = self.get_by_id(db, tenant_id)
        # validar unicidad
        if self.repo.get_by_code(db, new_code) and t.code != new_code:
            raise EntityAlreadyExistsError("Tenant", "code", new_code)
        return self.repo.update_code(db, t, new_code)

    def update_status(self, db: Session, tenant_id: str, is_active: bool) -> Tenant:
        t = self.get_by_id(db, tenant_id)
        return self.repo.update_status(db, t, is_active)

    def replace_meta(self, db: Session, tenant_id: str, new_meta: dict) -> Tenant:
        t = self.get_by_id(db, tenant_id)
        return self.repo.replace_meta(db, t, new_meta)

    #=========================================================
    #                      PATCH (merge)
    #=========================================================
    def patch(self, db: Session, tenant_id: str,
              name: Optional[str] = None,
              code: Optional[str] = None,
              is_active: Optional[bool] = None,
              meta: Optional[dict] = None) -> Tenant:
        t = self.get_by_id(db, tenant_id)

        if code is not None:
            if self.repo.get_by_code(db, code) and t.code != code:
                raise EntityAlreadyExistsError("Tenant", "code", code)
            t = self.repo.update_code(db, t, code)

        if name is not None:
            t = self.repo.update_name(db, t, name)

        if is_active is not None:
            t = self.repo.update_status(db, t, is_active)

        if meta is not None:
            # Merge superficial por defecto
            t = self.repo.merge_meta(db, t, meta)

        return t

    #=========================================================
    #                      SOFT-DELETE
    #=========================================================
    def deactivate_tenant(self, db: Session, tenant_id: str) -> bool:
        ok = self.repo.deactivate_tenant(db, tenant_id)
        if not ok:
            raise EntityNotFoundError("Tenant", "id", tenant_id)
        return ok

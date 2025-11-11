# src/apps/tenant/repository.py
from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Tenant


class TenantRepository:
    """Acceso a datos para Tenant."""

    # =========================================================
    #                       READ
    # =========================================================
    @staticmethod
    def get_all(db: Session) -> Sequence[Tenant]:
        return db.execute(select(Tenant)).scalars().all()

    @staticmethod
    def get_by_id(db: Session, tenant_id: str) -> Optional[Tenant]:
        return db.get(Tenant, tenant_id)

    @staticmethod
    def get_by_code(db: Session, code: str) -> Optional[Tenant]:
        return db.execute(select(Tenant).where(Tenant.code == code)).scalar_one_or_none()

    # =========================================================
    #                      CREATE
    # =========================================================
    @staticmethod
    def create(db: Session, *, code: str, name: str, meta: dict | None = None) -> Tenant:
        t = Tenant(code=code, name=name, meta=meta or {})
        db.add(t)
        db.flush()
        db.refresh(t)
        return t

    # =========================================================
    #                      UPDATE (helpers)
    # =========================================================
    @staticmethod
    def update_name(db: Session, tenant: Tenant, new_name: str) -> Tenant:
        tenant.name = new_name
        db.flush()
        db.refresh(tenant)
        return tenant

    @staticmethod
    def update_code(db: Session, tenant: Tenant, new_code: str) -> Tenant:
        tenant.code = new_code
        db.flush()
        db.refresh(tenant)
        return tenant

    @staticmethod
    def update_status(db: Session, tenant: Tenant, is_active: bool) -> Tenant:
        tenant.is_active = is_active
        db.flush()
        db.refresh(tenant)
        return tenant

    @staticmethod
    def replace_meta(db: Session, tenant: Tenant, new_meta: dict) -> Tenant:
        tenant.meta = new_meta or {}
        db.flush()
        db.refresh(tenant)
        return tenant

    @staticmethod
    def merge_meta(db: Session, tenant: Tenant, patch_meta: dict) -> Tenant:
        # merge superficial (key-level)
        merged = dict(tenant.meta or {})
        merged.update(patch_meta or {})
        tenant.meta = merged
        db.flush()
        db.refresh(tenant)
        return tenant

    # =========================================================
    #                      SOFT-DELETE
    # =========================================================
    @staticmethod
    def deactivate_tenant(db: Session, tenant_id: str) -> bool:
        t = db.execute(select(Tenant).where(Tenant.id == tenant_id)).scalar_one_or_none()
        if not t:
            return False
        t.is_active = False
        return True

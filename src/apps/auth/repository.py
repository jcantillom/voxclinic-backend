from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.apps.users.models import User


class AuthRepository:
    @staticmethod
    def list_by_tenant(db: Session, tenant_id) -> Sequence[User]:
        return db.execute(
            select(User).where(User.tenant_id == tenant_id)
        ).scalars().all()

    @staticmethod
    def set_last_login(db: Session, user: User):
        from sqlalchemy.sql import func
        user.last_login = func.now()
        db.flush()
        db.refresh(user)
        return user


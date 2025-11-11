from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import User


class UserRepository:

    @staticmethod
    def list_by_tenant(
            db: Session,
            tenant_id,
            *,
            page: int = 1,
            page_size: int = 20,
            role: str | None = None,
            q: str | None = None,
    ) -> tuple[list[User], int]:
        stmt = select(User).where(User.tenant_id == tenant_id)

        if role:
            stmt = stmt.where(User.role == role)

        if q:
            like = f"%{q}%"
            stmt = stmt.where(or_(User.email.ilike(like), User.full_name.ilike(like)))

        # total
        total = db.execute(stmt.with_only_columns(User.id)).scalars().all()
        total_count = len(total)

        # page
        offset = (page - 1) * page_size
        rows = db.execute(stmt.order_by(User.created_at.desc()).offset(offset).limit(page_size)).scalars().all()
        return rows, total_count

    @staticmethod
    def get_by_id(db: Session, user_id: str) -> Optional[User]:
        return db.get(User, user_id)

    @staticmethod
    def get_by_email(db: Session, tenant_id, email: str) -> Optional[User]:
        return db.execute(
            select(User).where(User.tenant_id == tenant_id, User.email == email)
        ).scalar_one_or_none()

    @staticmethod
    def create(db: Session, *, tenant_id, email: str, full_name: str, role: str, password_hash: str) -> User:
        u = User(
            tenant_id=tenant_id,
            email=email,
            full_name=full_name,
            role=role,
            password_hash=password_hash
        )
        db.add(u)
        db.flush()
        db.refresh(u)
        return u

    @staticmethod
    def update_name(db: Session, user: User, full_name: str) -> User:
        user.full_name = full_name
        db.flush()
        db.refresh(user)
        return user

    @staticmethod
    def set_active(db: Session, user: User, active: bool) -> User:
        user.is_active = active
        db.flush()
        db.refresh(user)
        return user

from sqlalchemy.orm import Session
from src.core.middlewares.security import get_password_hash, verify_password, create_access_token
from src.core.errors.errors import EntityAlreadyExistsError, EntityNotFoundError
from .repository import UserRepository
from .models import User
from src.apps.tenant.models import Tenant
from src.core.middlewares.security import get_password_hash, verify_password


class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    # =================================================
    # Create
    # =================================================
    def create_user(
            self,
            db: Session,
            *,
            tenant: Tenant,
            email: str,
            full_name: str,
            role: str,
            password: str) -> User:
        if self.repo.get_by_email(db, tenant.id, email):
            raise EntityAlreadyExistsError("User", "email", email)
        pwd_hash = get_password_hash(password)
        return self.repo.create(db, tenant_id=tenant.id, email=email, full_name=full_name, role=role,
                                password_hash=pwd_hash)

    # =================================================
    # Read
    # =================================================
    def list_users(
            self,
            db: Session,
            *, tenant: Tenant,
            page: int = 1, page_size:
            int = 20,
            role: str | None = None, q: str | None = None
    ):
        return self.repo.list_by_tenant(db, tenant.id, page=page, page_size=page_size, role=role, q=q)

    # =================================================
    # Update
    # =================================================
    def update_full_name(self, db: Session, *, user: User, full_name: str) -> User:
        return self.repo.update_name(db, user, full_name)

    def set_active(self, db: Session, *, user: User, active: bool) -> User:
        """Activa/Desactiva y devuelve siempre el usuario actualizado."""
        return self.repo.set_active(db, user, active)

    def change_password(self, db: Session, *, user: User, current_password: str, new_password: str) -> None:
        # FIX: usar password_hash correcto
        if not verify_password(current_password, user.password_hash):
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid current password")

        user.password_hash = get_password_hash(new_password)
        db.flush()  # commit vendrá por el session_scope del dependency

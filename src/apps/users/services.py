from sqlalchemy.orm import Session
from src.core.middlewares.security import get_password_hash, verify_password, create_access_token
from src.core.errors.errors import EntityAlreadyExistsError, EntityNotFoundError
from .repository import UserRepository
from .models import User
from src.apps.tenant.models import Tenant


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
    def list_users(self, db: Session, *, tenant: Tenant):
        return self.repo.list_by_tenant(db, tenant.id)

    # =================================================
    # Update
    # =================================================
    def update_full_name(self, db: Session, *, user: User, full_name: str) -> User:
        return self.repo.update_name(db, user, full_name)

    def set_active(self, db: Session, *, user: User, active: bool) -> User:
        """Activa/Desactiva y devuelve siempre el usuario actualizado."""
        return self.repo.set_active(db, user, active)

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.core.middlewares.security import verify_password, create_access_token
from src.core.errors.errors import EntityNotFoundError
from src.apps.auth.repository import AuthRepository
from src.apps.users.repository import UserRepository
from src.apps.tenant.models import Tenant


class AuthService:
    def __init__(self, repo: AuthRepository):
        self.repo = repo

    # =================================================
    # Login
    # =================================================
    def login(self, db: Session, *, tenant: Tenant, email: str, password: str) -> dict:
        u = UserRepository.get_by_email(db, tenant.id, email)
        if not u:
            raise EntityNotFoundError("User", "email", email)
        if not verify_password(password, u.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        self.repo.set_last_login(db, u)
        token = create_access_token({"sub": str(u.id), "tenant_id": str(tenant.id)})
        return {"access_token": token}

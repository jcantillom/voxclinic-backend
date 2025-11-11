from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.core.connections.deps import get_db, get_current_tenant
from src.apps.auth.schemas import LoginInput, TokenOut
from src.apps.auth.services import AuthService
from src.apps.users.repository import UserRepository
from .repository import AuthRepository

router = APIRouter(prefix="/auth", tags=["auth"])


def get_service() -> AuthService:
    return AuthService(
        repo=AuthRepository(),
    )


@router.post(
    "/login",
    response_model=TokenOut,
    status_code=status.HTTP_200_OK,
    summary="Login (JWT)",
)
def login(payload: LoginInput, db: Session = Depends(get_db), tenant=Depends(get_current_tenant)):
    svc = get_service()
    out = svc.login(db, tenant=tenant, email=payload.email, password=payload.password)
    return {"access_token": out["access_token"], "expires_in": 60 * int(1)}

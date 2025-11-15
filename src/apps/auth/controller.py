import os
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.core.connections.deps import get_db, get_current_tenant, get_current_user
from .schemas import LoginInput, TokenOut
from src.apps.auth.services import AuthService
from .repository import AuthRepository

router = APIRouter(prefix="/auth", tags=["auth"])


def get_service() -> AuthService:
    return AuthService(repo=AuthRepository())


@router.post("/login", response_model=TokenOut, status_code=status.HTTP_200_OK)
def login(payload: LoginInput, db: Session = Depends(get_db), tenant=Depends(get_current_tenant)):
    svc = get_service()
    out = svc.login(db, tenant=tenant, email=payload.email, password=payload.password)
    # Asegura int:
    expires = int(os.getenv("JWT_EXPIRES_MIN", "60"))
    return {"access_token": out["access_token"], "expires_in": expires}


@router.get("/me", summary="Usuario actual (token)", status_code=200)
# CORRECCIÓN CLAVE: Inyectar 'tenant' como dependencia
def me(user=Depends(get_current_user), tenant=Depends(get_current_tenant)):
    # Devuelve algo compacto y útil
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "tenant_id": str(user.tenant_id),
        "is_active": user.is_active,
        "last_login": user.last_login,
        "tenant_info": { # Incluir la metadata del Tenant
            "name": tenant.name,
            "code": tenant.code,
            "meta": tenant.meta
        }
    }


@router.post("/refresh", response_model=TokenOut, status_code=200, summary="Renovar token")
def refresh(user=Depends(get_current_user), tenant=Depends(get_current_tenant)):
    from src.core.middlewares.security import create_access_token
    expires = int(os.getenv("JWT_EXPIRES_MIN", "60"))
    token = create_access_token({"sub": str(user.id), "tenant_id": str(tenant.id)})
    return {"access_token": token, "expires_in": expires}
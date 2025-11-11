from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.core.connections.deps import get_db, get_current_tenant, get_current_user
from .schemas import UserCreate, UserOut
from .services import UserService
from .repository import UserRepository

router = APIRouter(prefix="/users", tags=["users"])


def get_service() -> UserService:
    return UserService(UserRepository())


# Crear usuario (solo owner/admin idealmente; aquí lo dejamos abierto para empezar)
@router.post(
    "",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario",
)
def create_user(
        payload: UserCreate,
        db: Session = Depends(get_db),
        tenant=Depends(get_current_tenant),
        _=Depends(get_current_user),  # exige auth
):
    svc = get_service()
    u = svc.create_user(db,
                        tenant=tenant,
                        email=payload.email,
                        full_name=payload.full_name,
                        role=payload.role,
                        password=payload.password,
                        )
    return UserOut.model_validate(u)


# Listar usuarios del tenant
@router.get("", response_model=List[UserOut], summary="Listar usuarios del tenant")
def list_users(
        db: Session = Depends(get_db),
        tenant=Depends(get_current_tenant),
        _=Depends(get_current_user),  # exige auth
):
    svc = get_service()
    rows = svc.list_users(db, tenant=tenant)
    return [UserOut.model_validate(x) for x in rows]

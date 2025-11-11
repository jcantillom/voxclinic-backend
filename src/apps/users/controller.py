from typing import List
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from src.core.connections.deps import get_db, get_current_tenant, get_current_user
from .schemas import UserCreate, UserOut, UserUpdateName, UserUpdateActive, UserChangePassword
from .services import UserService
from .repository import UserRepository
from src.core.middlewares.authorization import require_roles

owner_admin = require_roles("owner", "admin")

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
        _=Depends(get_current_user),
        _role=Depends(owner_admin),
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


@router.get("", summary="Listar usuarios del tenant")
def list_users(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=200),
        role: str | None = Query(None, pattern="^(owner|admin|staff|viewer)$"),
        q: str | None = Query(None, description="Buscar por email o nombre"),
        db: Session = Depends(get_db),
        tenant=Depends(get_current_tenant),
        _=Depends(get_current_user),
        _role=Depends(owner_admin),
):
    svc = get_service()
    rows, total = svc.list_users(db, tenant=tenant, page=page, page_size=page_size, role=role, q=q)
    return {
        "items": [UserOut.model_validate(x) for x in rows],
        "page": page,
        "page_size": page_size,
        "total": total
    }


@router.put(
    "/{user_id}/name",
    response_model=UserOut,
    summary="Actualizar nombre completo del usuario"
)
def update_full_name(
        user_id: str,
        payload: UserUpdateName,
        db: Session = Depends(get_db),
        tenant=Depends(get_current_tenant),
        svc: UserService = Depends(get_service),
        _role=Depends(owner_admin),
):
    # obtenemos usuario
    user = svc.repo.get_by_id(db, user_id)
    if not user or str(user.tenant_id) != str(tenant.id):
        from src.core.errors.errors import EntityNotFoundError
        raise EntityNotFoundError("User", "id", user_id)

    updated = svc.update_full_name(db, user=user, full_name=payload.full_name)
    return UserOut.model_validate(updated)


# ============================================================
# Activate / Deactivate User
# ============================================================
@router.put(
    "/{user_id}/active",
    response_model=UserOut,
    summary="Activar o desactivar usuario"
)
def update_user_active(
        user_id: str,
        payload: UserUpdateActive,
        db: Session = Depends(get_db),
        tenant=Depends(get_current_tenant),
        svc: UserService = Depends(get_service),
        _role=Depends(owner_admin),
):
    user = svc.repo.get_by_id(db, user_id)
    if not user or str(user.tenant_id) != str(tenant.id):
        from src.core.errors.errors import EntityNotFoundError
        raise EntityNotFoundError("User", "id", user_id)

    updated_user = svc.set_active(db, user=user, active=payload.is_active)
    return UserOut.model_validate(updated_user)


@router.put("/me/password", status_code=200, summary="Cambiar mi contraseña")
def change_my_password(
        payload: UserChangePassword,
        db: Session = Depends(get_db),
        me=Depends(get_current_user)  # cualquier usuario autenticado
):
    svc = get_service()
    svc.change_password(
        db,
        user=me,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
    return {
        "message": "Password updated successfully",
    }

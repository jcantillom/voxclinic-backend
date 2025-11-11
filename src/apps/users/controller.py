from typing import List
from fastapi import APIRouter, Depends, status, Query, Response
from sqlalchemy.orm import Session
from src.core.connections.deps import get_db, get_current_tenant, get_current_user
from .schemas import UserCreate, UserOut, UserUpdateName, UserUpdateActive, UserChangePassword
from .services import UserService
from .repository import UserRepository
from src.core.middlewares.permissions import require_roles

router = APIRouter(prefix="/users", tags=["users"])


def get_service() -> UserService:
    return UserService(UserRepository())


# Crear usuario (solo owner/admin idealmente; aquí lo dejamos abierto para empezar)
@router.post(
    "",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario",
    dependencies=[Depends(require_roles("owner", "admin"))],
)
def create_user(
        payload: UserCreate,
        db: Session = Depends(get_db),
        tenant=Depends(get_current_tenant),
        _=Depends(get_current_user),
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


@router.get(
    "",
    response_model=List[UserOut],
    summary="Listar usuarios del tenant",
    dependencies=[Depends(require_roles("owner", "admin"))],
)
def list_users(
        response: Response,
        db: Session = Depends(get_db),
        tenant=Depends(get_current_tenant),
        _=Depends(get_current_user),
        q: str | None = Query(None, description="Buscar por email/full_name"),
        role: str | None = Query(None, pattern="^(owner|admin|staff|viewer)$"),
        is_active: bool | None = Query(None),
        page: int = Query(1, ge=1),
        page_size: int = Query(50, ge=1, le=200),
):
    svc = get_service()
    rows, total = svc.search_users(
        db, tenant=tenant, q=q, role=role, is_active=is_active, page=page, page_size=page_size
    )
    response.headers["X-Total-Count"] = str(total)
    return [UserOut.model_validate(x) for x in rows]


# Update nombre: permitir al propio usuario o a admin/owner (regla en línea)
@router.put(
    "/{user_id}/name",
    response_model=UserOut,
    summary="Actualizar nombre completo del usuario",
)
def update_full_name(
        user_id: str,
        payload: UserUpdateName,
        db: Session = Depends(get_db),
        tenant=Depends(get_current_tenant),
        me=Depends(get_current_user),
        svc: UserService = Depends(get_service)
):
    user = svc.repo.get_by_id(db, user_id)
    if not user or str(user.tenant_id) != str(tenant.id):
        from src.core.errors.errors import EntityNotFoundError
        raise EntityNotFoundError("User", "id", user_id)

    # regla: puede si (me.id == user.id) o me.role in owner/admin
    if str(me.id) != str(user.id) and me.role not in ("owner", "admin"):
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    updated = svc.update_full_name(db, user=user, full_name=payload.full_name)
    return UserOut.model_validate(updated)


# ============================================================
# Activate / Deactivate User
# ============================================================
# Activar/Desactivar usuario: solo owner/admin
@router.put(
    "/{user_id}/active",
    response_model=UserOut,
    summary="Activar o desactivar usuario",
    dependencies=[Depends(require_roles("owner", "admin"))],
)
def update_user_active(
        user_id: str,
        payload: UserUpdateActive,
        db: Session = Depends(get_db),
        tenant=Depends(get_current_tenant),
        svc: UserService = Depends(get_service)
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

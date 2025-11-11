from typing import Generator
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from src.core.connections.database import DataAccessLayer
from src.apps.tenant.repository import TenantRepository
from src.apps.users.repository import UserRepository
from src.core.middlewares.security import decode_token
from fastapi.security import OAuth2PasswordBearer

_dal = DataAccessLayer()
_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")  # url del login


def get_db() -> Generator[Session, None, None]:
    with _dal.session_scope() as db:
        yield db


def get_tenant_code(x_tenant_code: str = Header(alias="X-Tenant-Code")) -> str:
    if not x_tenant_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Tenant-Code header is required")
    return x_tenant_code


def get_current_tenant(db: Session = Depends(get_db), tenant_code: str = Depends(get_tenant_code)):
    t = TenantRepository().get_by_code(db, tenant_code)
    if not t or not t.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found or inactive")
    return t


def get_current_user(
        db: Session = Depends(get_db),
        token: str = Depends(_oauth2),
        tenant=Depends(get_current_tenant),
):
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        token_tenant_id = payload.get("tenant_id")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if not user_id or not token_tenant_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed token")

    # El usuario debe existir y pertenecer al mismo tenant del header
    u = UserRepository.get_by_id(db, user_id)
    if not u or str(u.tenant_id) != str(token_tenant_id) or str(tenant.id) != str(token_tenant_id):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid tenant context")

    if not u.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User inactive")
    return u

# src/core/middlewares/permissions.py
from fastapi import Depends, HTTPException, status
from src.core.connections.deps import get_current_user

ALLOWED_ROLES = ("owner", "admin", "staff", "viewer")


def require_roles(*roles: str):
    """
    Ejemplo de uso:
      @router.post(..., dependencies=[Depends(require_roles("owner","admin"))])
    """
    invalid = [r for r in roles if r not in ALLOWED_ROLES]
    if invalid:
        raise ValueError(f"Invalid roles in require_roles: {invalid}")

    def _dep(user=Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not allowed for role '{user.role}'. Required: {roles}"
            )
        return user

    return _dep

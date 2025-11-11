from fastapi import Depends, HTTPException, status
from src.core.connections.deps import get_current_user


def require_roles(*allowed: str):
    """
    Uso: dep = require_roles("owner", "admin")
    Luego en el endpoint: _=Depends(dep)
    """

    def _dep(user=Depends(get_current_user)):
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden for role '{user.role}'. Requires one of: {allowed}"
            )
        return user

    return _dep

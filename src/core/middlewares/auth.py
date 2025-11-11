from datetime import datetime
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from src.core.connections.database import DataAccessLayer
from sqlalchemy.orm import Session
from jwt import ExpiredSignatureError, InvalidSignatureError
import jwt

http_bearer = HTTPBearer()


def get_current_user(
        credentials: HTTPBearer = Depends(http_bearer),
        db: Session = Depends(DataAccessLayer().session_scope)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token expired or invalid",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials

        token_bytes = token.encode('utf-8')

        payload = jwt.decode(token_bytes, options={"verify_signature": False})
        email = payload.get("emails")[0]
        expiration = payload.get("exp")

        time_remaining = int(
            (datetime.fromtimestamp(expiration) - datetime.now()).total_seconds() / 60)
        print(f" Tiempo Restate De Expiration del Token ⏱ -----> : {time_remaining} minutes")



        with db as session:
            user = session.query(User).filter(User.email == email).first()
            if user is None:
                raise credentials_exception

        return user

    except InvalidSignatureError:
        raise credentials_exception

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )


def is_administrator(user: User = Depends(get_current_user)):
    if not user.is_administrator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not administrator"
        )
    return user


def create_new_token(user: User):
    payload = {
        "emails": [user.email],
        "exp": datetime.now().timestamp() + 60 * 60
    }

    token = jwt.encode(payload, os.getenv("SECRET_KEY"), algorithm="HS256")
    return token


@router.get("/renew-token")
def renew_token(user: User = Depends(get_current_user)):
    """
    Refresh token.
    :param user:
    :return:
    """
    new_token = create_new_token(user)
    return {"refreshToken": new_token}

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Dict
from jose import jwt, JWTError
from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuración de JWT mejorada
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET or JWT_SECRET == "change-me":
    raise ValueError("JWT_SECRET no está configurado correctamente")

JWT_EXPIRES_MIN = int(os.getenv("JWT_EXPIRES_MIN", "60"))
JWT_ALG = "HS256"


def get_password_hash(password: str) -> str:
    """Genera hash seguro de contraseña"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica contraseña contra hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: Dict[str, Any], expires_minutes: int | None = None) -> str:
    """Crea JWT token con expiración"""
    expire = datetime.now(tz=timezone.utc) + timedelta(
        minutes=expires_minutes or JWT_EXPIRES_MIN
    )
    to_encode = {"exp": expire, **subject}

    try:
        return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALG)
    except JWTError as e:
        logger.error(f"Error creating JWT token: {e}")
        raise


def decode_token(token: str) -> dict:
    """Decodifica y valida JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        raise ValueError("Token expirado")
    except jwt.JWTError as e:
        logger.warning(f"Invalid JWT token: {e}")
        raise ValueError("Token inválido")

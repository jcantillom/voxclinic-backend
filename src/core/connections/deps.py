from typing import Generator
from sqlalchemy.orm import Session
from src.core.connections.database import DataAccessLayer

_dal = DataAccessLayer()

def get_db() -> Generator[Session, None, None]:
    """
    Entrega una Session ligada al engine por request.
    Maneja commit/rollback/close automáticamente.
    """
    with _dal.session_scope() as db:
        yield db

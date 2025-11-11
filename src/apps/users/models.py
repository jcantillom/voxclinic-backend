from sqlalchemy import Column, String, Boolean, CheckConstraint, Index, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func
import uuid

from src.core.connections.database import Base

# Roles: owner (dueño del tenant), admin (admin del tenant), staff (operativo), viewer (solo lectura)
ROLE_VALUES = (
    "owner",
    "admin",
    "staff",
    "viewer",
)


class User(Base):
    __tablename__ = "app_user"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, server_default="true")
    last_login = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        # Email único por tenant
        UniqueConstraint("tenant_id", "email", name="uq_user_tenant_email"),
        # Validación de rol
        CheckConstraint(f"role IN {ROLE_VALUES}", name="ck_user_role_valid"),
        # Índices útiles
        Index("ix_user_tenant_email", "tenant_id", "email"),
        Index("ix_user_tenant_role", "tenant_id", "role"),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} tenant_id={self.tenant_id} email={self.email} role={self.role}>"

from sqlalchemy import Column, String, Boolean, ForeignKey, Index, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func
import uuid
from src.core.connections.database import Base


class Patient(Base):
    __tablename__ = "patient"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)

    # Identificación básica
    identifier = Column(String(120), nullable=False, index=True)  # Cedula, DNI, ID de Historia Clínica
    full_name = Column(String(255), nullable=False)
    date_of_birth = Column(TIMESTAMP(timezone=True))  # Para calcular edad

    # Estado (ej. Activo para citas)
    is_active = Column(Boolean, nullable=False, server_default="true")

    # Metadatos clínicos/administrativos (puede incluir CIE-10 reciente, o datos del HIS)
    meta = Column(Text, nullable=False, server_default='{}')

    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        # Identificador único por Tenant
        UniqueConstraint("tenant_id", "identifier", name="uq_patient_tenant_id"),
        Index("ix_patient_tenant_name", "tenant_id", "full_name"),
    )
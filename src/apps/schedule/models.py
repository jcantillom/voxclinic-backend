from sqlalchemy import Column, String, Boolean, ForeignKey, Index, Text, Enum
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func
import uuid
from src.core.connections.database import Base

APPOINTMENT_STATUS = ("scheduled", "completed", "cancelled", "missed")


class Appointment(Base):
    __tablename__ = "appointment"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey(
        "tenant.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey(
        "app_user.id", ondelete="SET NULL"))  # Medico asignado
    patient_id = Column(UUID(as_uuid=True), ForeignKey(
        "patient.id", ondelete="CASCADE"), nullable=False)

    # Datos de la cita
    start_time = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    end_time = Column(TIMESTAMP(timezone=True))
    reason = Column(String(255), nullable=False)

    status = Column(Enum(
        *APPOINTMENT_STATUS, name="appointment_status_enum"), nullable=False, default="scheduled")

    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_appointment_tenant_time", "tenant_id", "start_time"),
    )

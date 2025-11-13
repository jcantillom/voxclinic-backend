from sqlalchemy import Column, String, Boolean, ForeignKey, Index, Text, Enum
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP, JSONB
from sqlalchemy.sql import func
import uuid
from src.core.connections.database import Base

DOCUMENT_TYPES = (
    "clinical_history",
    "radiology_report",
    "medical_prescription",
    "medical_certificate",
    "incapacity",
)

class Document(Base):
    __tablename__ = "document"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="SET NULL"))

    # Referencia al audio original
    recording_id = Column(UUID(as_uuid=True), ForeignKey("recording.id", ondelete="SET NULL"), unique=True,
                          nullable=True)

    document_type = Column(Enum(*DOCUMENT_TYPES, name="document_type_enum"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)  # Contenido final (ej. HTML o Markdown o texto plano)

    # Metadatos clínicos (ej: ID de paciente, CIE-10, médico remitente)
    clinical_meta = Column(JSONB, nullable=False, server_default='{}')

    is_finalized = Column(Boolean, nullable=False, server_default="false")
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_document_tenant_user_type", "tenant_id", "user_id", "document_type"),
        Index("ix_document_tenant_recording", "tenant_id", "recording_id"),
    )
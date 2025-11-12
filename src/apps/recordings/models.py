from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func
import uuid
from src.core.connections.database import Base

# Estados simples de la ingesta/transcripción
RECORDING_STATUS = ("uploaded", "processing", "completed", "failed")


class Recording(Base):
    __tablename__ = "recording"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="SET NULL"))

    bucket = Column(String(255), nullable=False)
    key = Column(String(1024), nullable=False)  # p. ej. recordings/dev/juan/2025-11-11/audio-test.wav
    content_type = Column(String(120), nullable=False, default="audio/wav")
    size_bytes = Column(Integer)
    duration_sec = Column(Integer)

    status = Column(String(30), nullable=False, default="uploaded")
    transcript_text = Column(String)  # null hasta que exista
    error_message = Column(String)

    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

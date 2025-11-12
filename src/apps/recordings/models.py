from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy import Text  # NEW
import uuid
from src.core.connections.database import Base

RECORDING_STATUS = ("uploaded", "processing", "completed", "failed")


class Recording(Base):
    __tablename__ = "recording"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="SET NULL"))

    bucket = Column(String(255), nullable=False)
    key = Column(String(1024), nullable=False)
    content_type = Column(String(120), nullable=False, default="audio/wav")
    size_bytes = Column(Integer)
    duration_sec = Column(Integer)

    status = Column(String(30), nullable=False, default="uploaded")
    transcript_text = Column(Text)
    error_message = Column(Text)

    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        # Unicidad por tenant+objeto S3
        UniqueConstraint("tenant_id", "bucket", "key", name="uq_recording_tenant_bucket_key"),
        # Índices útiles para listados y filtros
        Index("ix_recording_tenant_created", "tenant_id", "created_at"),
        Index("ix_recording_tenant_status", "tenant_id", "status"),
        Index("ix_recording_tenant_key", "tenant_id", "key"),
    )

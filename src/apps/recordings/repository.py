from typing import Sequence, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from .models import Recording


class RecordingRepository:
    @staticmethod
    def create(db: Session, **data) -> Recording:
        r = Recording(**data)
        db.add(r)
        db.flush()
        db.refresh(r)
        return r

    @staticmethod
    def get_by_unique(
            db: Session,
            *,
            tenant_id,
            bucket: str,
            key: str,
    ) -> Optional[Recording]:
        """
        Recupera un Recording por su clave única (tenant_id, bucket, key).
        """
        return db.execute(
            select(Recording).where(
                Recording.tenant_id == tenant_id,
                Recording.bucket == bucket,
                Recording.key == key,
            )
        ).scalar_one_or_none()

    @staticmethod
    def list_by_tenant(
            db: Session, tenant_id, *, q: Optional[str] = None, status: Optional[str] = None,
            page: int = 1, page_size: int = 50
    ) -> Tuple[Sequence[Recording], int]:
        stmt = select(Recording).where(Recording.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(Recording.status == status)
        if q:
            # búsqueda simple por key
            stmt = stmt.where(Recording.key.ilike(f"%{q}%"))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.execute(count_stmt).scalar_one()

        offset = (page - 1) * page_size
        rows = db.execute(
            stmt.order_by(Recording.created_at.desc()).offset(offset).limit(page_size)
        ).scalars().all()
        return rows, total

    @staticmethod
    def get_by_id(db: Session, recording_id: str) -> Recording | None:
        r = db.get(Recording, recording_id)
        return r

    @staticmethod
    def set_status(db: Session, recording: Recording, status: str, error_message: str | None = None) -> Recording:
        recording.status = status
        recording.error_message = error_message
        db.flush()
        db.refresh(recording)
        return recording

    @staticmethod
    def attach_transcript(db: Session, recording: Recording, transcript_text: str,
                          duration_sec: int | None = None) -> Recording:
        recording.transcript_text = transcript_text
        if duration_sec is not None:
            recording.duration_sec = duration_sec
        recording.status = "completed"
        db.flush()
        db.refresh(recording)
        return recording

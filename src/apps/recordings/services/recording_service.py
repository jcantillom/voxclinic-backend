# src/apps/recordings/services/recording_service.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.apps.tenant.models import Tenant
from src.apps.users.models import User
from ..repository import RecordingRepository
from ..models import Recording

class RecordingService:
    def __init__(self, repo: RecordingRepository):
        self.repo = repo

    def register_upload(
            self, db: Session, *, tenant: Tenant, user: User,
            bucket: str, key: str, content_type: str, size_bytes: int | None, duration_sec: int | None
    ) -> Recording:
        try:
            return self.repo.create(
                db,
                tenant_id=tenant.id,
                user_id=user.id if user else None,
                bucket=bucket,
                key=key,
                content_type=content_type,
                size_bytes=size_bytes,
                duration_sec=duration_sec,
                status="uploaded",
            )
        except IntegrityError:
            db.rollback()
            existing = self.repo.get_by_unique(
                db,
                tenant_id=tenant.id,
                bucket=bucket,
                key=key,
            )
            if existing:
                return existing
            raise

    def list(
            self,
            db: Session,
            *,
            tenant: Tenant,
            q=None,
            status=None,
            page=1,
            page_size=50
    ):
        return self.repo.list_by_tenant(
            db,
            tenant.id,
            q=q,
            status=status,
            page=page,
            page_size=page_size,
        )

    def get(self, db: Session, recording_id: str) -> Recording | None:
        return self.repo.get_by_id(db, recording_id)

    def update_status(self, db: Session, recording: Recording, status: str,
                      error_message: str | None = None) -> Recording:
        return self.repo.set_status(db, recording, status, error_message)

    def set_transcript(self, db: Session, recording: Recording, transcript_text: str,
                       duration_sec: int | None = None) -> Recording:
        return self.repo.attach_transcript(db, recording, transcript_text, duration_sec)
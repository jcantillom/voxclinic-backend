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

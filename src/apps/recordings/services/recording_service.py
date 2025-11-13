# src/apps/recordings/services/recording_service.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, func
from datetime import datetime, timedelta
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
        """Crea el registro del audio recién subido"""
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

    def get_dashboard_metrics(self, db: Session, tenant_id: str, user_id: str = None) -> dict:
        """Obtiene métricas reales para el dashboard"""
        # Consulta base para el tenant
        base_query = select(Recording).where(Recording.tenant_id == tenant_id)

        if user_id:
            base_query = base_query.where(Recording.user_id == user_id)

        # Documentos generados (completados)
        documents_count = db.execute(
            base_query.where(Recording.status == 'completed')
        ).scalar() or 0

        # Tiempo ahorrado (suma de duración)
        time_saved_sec = db.execute(
            select(func.coalesce(func.sum(Recording.duration_sec), 0))
            .where(Recording.tenant_id == tenant_id, Recording.status == 'completed')
        ).scalar() or 0

        # Dictados procesados (todos los estados)
        processed_count = db.execute(base_query).scalar() or 0

        # Para pacientes, por ahora usamos documentos como proxy
        patients_count = documents_count

        # Calcular tendencias (vs últimos 30 días)
        thirty_days_ago = datetime.now() - timedelta(days=30)

        previous_documents = db.execute(
            base_query.where(
                Recording.status == 'completed',
                Recording.created_at >= thirty_days_ago
            )
        ).scalar() or 0

        return {
            "documents_generated": {
                "count": documents_count,
                "trend": self._calculate_trend(documents_count, previous_documents),
                "description": "Informes médicos generados"
            },
            "patients_served": {
                "count": patients_count,
                "trend": self._calculate_trend(patients_count, previous_documents),
                "description": "Pacientes atendidos"
            },
            "time_saved": {
                "count": self._format_time_saved(time_saved_sec),
                "trend": "+12%",  # Placeholder por ahora
                "description": "Tiempo ahorrado en documentación"
            },
            "recordings_processed": {
                "count": processed_count,
                "trend": self._calculate_trend(processed_count, previous_documents),
                "description": "Dictados procesados"
            }
        }

    def _calculate_trend(self, current: int, previous: int) -> str:
        """Calcula tendencia porcentual"""
        if previous == 0:
            return "+100%" if current > 0 else "0%"

        change = ((current - previous) / previous) * 100
        trend = "+" if change > 0 else ""
        return f"{trend}{change:.0f}%"

    def _format_time_saved(self, seconds: int) -> str:
        """Formatea tiempo ahorrado en horas"""
        hours = seconds / 3600
        return f"{hours:.0f}h"

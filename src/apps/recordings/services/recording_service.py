# src/apps/recordings/services/recording_service.py
from datetime import datetime, timedelta
from sqlalchemy import select, func
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

    def get_dashboard_metrics(self, db: Session, tenant_id: str, user_id: str = None) -> dict:
        """Obtiene métricas reales para el dashboard"""

        # Documentos generados (recordings completados)
        documents_query = select(func.count(Recording.id)).where(
            Recording.tenant_id == tenant_id,
            Recording.status == 'completed'
        )

        # Pacientes atendidos (únicos por algún criterio)
        # Por ahora usaremos documentos como proxy
        patients_query = select(func.count(Recording.id)).where(
            Recording.tenant_id == tenant_id,
            Recording.status == 'completed'
        )

        # Tiempo ahorrado (suma de duración de recordings)
        time_saved_query = select(func.coalesce(func.sum(Recording.duration_sec), 0)).where(
            Recording.tenant_id == tenant_id,
            Recording.status == 'completed'
        )

        # Dictados procesados (todos los recordings)
        processed_query = select(func.count(Recording.id)).where(
            Recording.tenant_id == tenant_id
        )

        # Ejecutar queries
        documents = db.execute(documents_query).scalar() or 0
        patients = db.execute(patients_query).scalar() or 0
        time_saved_sec = db.execute(time_saved_query).scalar() or 0
        processed = db.execute(processed_query).scalar() or 0

        # Calcular porcentajes (vs mes anterior)
        previous_month = self._get_previous_month_metrics(db, tenant_id)

        return {
            "documents_generated": {
                "count": documents,
                "trend": self._calculate_trend(documents, previous_month.get('documents', 0)),
                "description": "Informes médicos generados"
            },
            "patients_served": {
                "count": patients,
                "trend": self._calculate_trend(patients, previous_month.get('patients', 0)),
                "description": "Pacientes atendidos"
            },
            "time_saved": {
                "count": self._format_time_saved(time_saved_sec),
                "trend": self._calculate_trend(time_saved_sec, previous_month.get('time_saved', 0)),
                "description": "Tiempo ahorrado en documentación"
            },
            "recordings_processed": {
                "count": processed,
                "trend": self._calculate_trend(processed, previous_month.get('processed', 0)),
                "description": "Dictados procesados"
            }
        }

    def _get_previous_month_metrics(self, db: Session, tenant_id: str) -> dict:
        """Obtiene métricas del mes anterior para comparación"""
        one_month_ago = datetime.now() - timedelta(days=30)

        documents = db.execute(
            select(func.count(Recording.id)).where(
                Recording.tenant_id == tenant_id,
                Recording.status == 'completed',
                Recording.created_at >= one_month_ago
            )
        ).scalar() or 0

        return {
            'documents': documents,
            'patients': documents,  # mismo proxy por ahora
            'time_saved': db.execute(
                select(func.coalesce(func.sum(Recording.duration_sec), 0)).where(
                    Recording.tenant_id == tenant_id,
                    Recording.status == 'completed',
                    Recording.created_at >= one_month_ago
                )
            ).scalar() or 0,
            'processed': db.execute(
                select(func.count(Recording.id)).where(
                    Recording.tenant_id == tenant_id,
                    Recording.created_at >= one_month_ago
                )
            ).scalar() or 0
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

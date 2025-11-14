# src/apps/recordings/services/recording_service.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, func
from datetime import datetime, timedelta
from src.apps.tenant.models import Tenant
from src.apps.users.models import User
from ..repository import RecordingRepository
from ..models import Recording
from sqlalchemy import cast, Integer


class RecordingService:
    def __init__(self, repo: RecordingRepository):
        self.repo = repo

    # CORRECCIÓN: El método debe existir aquí
    def register_upload(
            self, db: Session, *, tenant: Tenant, user: User,
            bucket: str, key: str, content_type: str, size_bytes: int | None, duration_sec: int | None
    ) -> Recording:
        """Crea el registro del audio recién subido"""
        try:
            return self.repo.create(  # Llama al repo
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

        # CONSULTAS DE CONTEO

        base_query_completed_count = select(func.count(Recording.id)).where(
            Recording.tenant_id == tenant_id,
            Recording.status == 'completed'
        )
        base_query_total_count = select(func.count(Recording.id)).where(Recording.tenant_id == tenant_id)

        # Filtro por usuario (si aplica)
        if user_id:
            base_query_completed_count = base_query_completed_count.where(Recording.user_id == user_id)
            base_query_total_count = base_query_total_count.where(Recording.user_id == user_id)

        # Métrica: Documentos generados (completados) - Hoy
        today = datetime.now().date()
        today_documents = db.execute(
            base_query_completed_count.where(func.date(Recording.created_at) == today)
        ).scalar_one_or_none() or 0

        # Métrica: Dictados procesados (todos los estados) - Total
        processed_total = db.execute(base_query_total_count).scalar_one_or_none() or 0

        # Métrica: Dictados pendientes de revisión (Ej: status = 'uploaded' o 'processing')
        pending_count = db.execute(
            base_query_total_count.where(Recording.status.in_(['uploaded', 'processing']))
        ).scalar_one_or_none() or 0

        # Tiempo ahorrado (suma de duración) - Total
        time_saved_sec = db.execute(
            select(func.coalesce(func.sum(Recording.duration_sec), 0))
            .where(Recording.tenant_id == tenant_id, Recording.status == 'completed')
        ).scalar_one_or_none() or 0

        # Calcular tendencias (vs últimos 30 días)
        thirty_days_ago = datetime.now() - timedelta(days=30)

        # Documentos completados en los últimos 30 días (CURRENT)
        last_30_days_completed = db.execute(
            select(func.count(Recording.id))
            .where(
                Recording.tenant_id == tenant_id,
                Recording.status == 'completed',
                Recording.created_at >= thirty_days_ago
            )
        ).scalar_one_or_none() or 0

        # Documentos completados en los 30 días anteriores a ese período (PREVIOUS)
        sixty_days_ago = datetime.now() - timedelta(days=60)
        previous_30_days_completed = db.execute(
            select(func.count(Recording.id))
            .where(
                Recording.tenant_id == tenant_id,
                Recording.status == 'completed',
                Recording.created_at >= sixty_days_ago,
                Recording.created_at < thirty_days_ago
            )
        ).scalar_one_or_none() or 0

        # Para pacientes, por ahora usamos documentos generados hoy como proxy
        patients_count = today_documents

        return {
            "documents_generated": {
                "count": today_documents,
                "trend": self._calculate_trend(last_30_days_completed, previous_30_days_completed),
                "description": "Informes generados hoy"
            },
            "patients_served": {
                "count": patients_count,
                "trend": self._calculate_trend(last_30_days_completed, previous_30_days_completed),
                "description": "Pacientes atendidos hoy"
            },
            "time_saved": {
                "count": self._format_time_saved(time_saved_sec),
                "trend": "+0%",
                "description": "Tiempo total ahorrado"
            },
            "recordings_processed": {
                "count": processed_total,
                "trend": self._calculate_trend(processed_total, previous_30_days_completed),
                "description": f"{pending_count} pendiente(s) de revisión"
            }
        }

    def _calculate_trend(self, current: int, previous: int) -> str:
        """Calcula tendencia porcentual, devolviendo '0%' o N/A de forma segura."""
        if current is None or previous is None:
            return "N/A"

        if previous == 0:
            return "+100%" if current > 0 else "0%"

        change = ((current - previous) / previous) * 100
        trend = "+" if change > 0 else ""
        return f"{trend}{change:.0f}%"

    def _format_time_saved(self, seconds: int | float) -> str:
        """Formatea tiempo ahorrado en horas, devolviendo '0h' si es nulo o cero."""
        if seconds is None or seconds == 0:
            return "0h"
        hours = seconds / 3600
        return f"{hours:.0f}h"
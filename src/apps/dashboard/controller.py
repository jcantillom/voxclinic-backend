# src/apps/dashboard/controller.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.core.connections.deps import get_db, get_current_tenant, get_current_user
from src.apps.recordings.dependencies import get_recording_service
from src.apps.recordings.services.recording_service import RecordingService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/metrics")
async def get_dashboard_metrics(
        db: Session = Depends(get_db),
        tenant=Depends(get_current_tenant),
        user=Depends(get_current_user),
        recording_service: RecordingService = Depends(get_recording_service)
):
    """Obtiene métricas reales para el dashboard"""
    metrics = recording_service.get_dashboard_metrics(db, str(tenant.id), str(user.id))
    return metrics

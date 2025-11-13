# src/apps/recordings/controllers/webhook_controller.py
from fastapi import APIRouter, Request, HTTPException, Depends
import json
import logging
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from src.core.connections.deps import get_db
from ..dependencies import get_recording_service, get_transcription_service
from ..services.recording_service import RecordingService
from ..services.transcription_service import TranscriptionService

router = APIRouter(prefix="/webhook", tags=["Webhooks"])
logger = logging.getLogger(__name__)


@router.post("/transcription")
async def handle_transcription_webhook(
        request: Request,
        db: Session = Depends(get_db),
        recording_service: RecordingService = Depends(get_recording_service),
        transcription_service: TranscriptionService = Depends(get_transcription_service),
):
    try:
        # Verificar que el body no esté vacío
        body = await request.body()
        if not body:
            logger.warning("Empty webhook body received")
            return JSONResponse(status_code=400, content={"error": "Empty body"})

        # Intentar parsear como JSON
        try:
            data = await request.json()
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in webhook: {e}")
            return JSONResponse(status_code=400, content={"error": "Invalid JSON"})

        # Procesar el webhook de Transcribe
        # (Aquí puedes agregar lógica para procesar notificaciones de Transcribe)
        logger.info(f"Received webhook: {data}")

        return JSONResponse(status_code=200, content={"status": "processed"})

    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return JSONResponse(status_code=500, content={"error": "Webhook processing failed"})

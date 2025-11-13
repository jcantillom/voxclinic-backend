# src/apps/recordings/webhook_controller.py
from fastapi import APIRouter, Request, HTTPException
import json

from fastapi.logger import logger
from starlette.responses import JSONResponse

router = APIRouter()


@router.post("/webhook/transcription")
async def handle_transcription_webhook(request: Request):
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

        # Procesar el webhook...

    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return JSONResponse(status_code=500, content={"error": "Webhook processing failed"})

# src/apps/recordings/dependencies.py
from .services.recording_service import RecordingService
from .services.transcription_service import TranscriptionService
from .repository import RecordingRepository


def get_recording_service() -> RecordingService:
    return RecordingService(RecordingRepository())


def get_transcription_service() -> TranscriptionService:
    return TranscriptionService()

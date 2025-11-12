from pydantic import BaseModel, Field
from typing import Optional, Dict


class PresignPutIn(BaseModel):
    filename: str = Field(
        ...,
        max_length=255, description="Nombre original del archivo (ej: audio.wav)")
    content_type: str = Field(
        ...,
        max_length=120, description="MIME Type ej: audio/wav, audio/mpeg, audio/webm")
    size_bytes: Optional[int] = Field(
        None,
        ge=0,
        description="Tamaño estimado para validaciones (opcional)")
    folder: Optional[str] = Field(
        "recordings",
        max_length=120, description="Carpeta raíz lógica (default: recordings)")


class PresignPutOut(BaseModel):
    bucket: str
    key: str
    upload_url: str
    required_headers: Dict[str, str]
    expires_in: int

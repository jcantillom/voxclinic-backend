# src/apps/storage/services.py
import os
import re
import uuid
from datetime import datetime

import boto3
from botocore.config import Config
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

ALLOWED_CONTENT_TYPES = {
    "audio/wav": "wav",
    "audio/x-wav": "wav",
    "audio/mpeg": "mp3",
    "audio/webm": "webm",
    "audio/ogg": "ogg",
    "audio/mp4": "m4a",
}


class StorageService:
    def __init__(self):
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.bucket = os.getenv("S3_BUCKET_AUDIO")
        self.app_env = os.getenv("APP_ENV", "development")
        self.profile = os.getenv("AWS_PROFILE")  # solo dev; en prod normalmente vacío

        if not self.bucket:
            raise RuntimeError("S3_BUCKET_AUDIO no configurado en .env")

        try:
            session = boto3.session.Session(
                profile_name=self.profile or None,
                region_name=self.region,
            )
            self.client = session.client("s3", config=Config(signature_version="s3v4"))
        except (NoCredentialsError, PartialCredentialsError) as e:
            raise RuntimeError(
                "No encuentro credenciales AWS. "
                "En desarrollo: ejecuta `aws sso login --profile <perfil>` "
                "y exporta AWS_PROFILE en el entorno donde corres uvicorn. "
                "En producción: usa un IAM Role adjunto al servicio (ECS/EKS/EC2)."
            ) from e

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        base = name.split("/")[-1].split("\\")[-1]
        base = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("._-")
        return base or "file"

    def _ext_from_content_type(self, content_type: str) -> str:
        return ALLOWED_CONTENT_TYPES.get(content_type, "bin")

    def build_key(self, *, folder: str, tenant_code: str, user_id: str, content_type: str, filename: str) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        safe_name = self._sanitize_filename(filename)
        ext = self._ext_from_content_type(content_type)
        if "." not in safe_name or safe_name.split(".")[-1].lower() != ext:
            safe_name = f"{uuid.uuid4()}.{ext}"
        return f"{folder}/{self.app_env}/{tenant_code}/{user_id}/{today}/{safe_name}"

    def presign_put(self, *, key: str, content_type: str, expires_sec: int = 900) -> dict:
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise ValueError(
                f"content_type '{content_type}' no permitido. "
                f"Permitidos: {', '.join(ALLOWED_CONTENT_TYPES)}"
            )

        url = self.client.generate_presigned_url(
            ClientMethod="put_object",
            Params={"Bucket": self.bucket, "Key": key, "ContentType": content_type},
            ExpiresIn=expires_sec,
        )
        return {
            "bucket": self.bucket,
            "key": key,
            "upload_url": url,
            "required_headers": {"Content-Type": content_type},
            "expires_in": expires_sec,
        }

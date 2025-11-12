import os
from typing import Dict
import boto3
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    NoCredentialsError,
    TokenRetrievalError,
)
from fastapi import HTTPException, status


class StorageService:
    """
    Servicio S3 para prefirmar uploads.

    Fuentes de credenciales (en orden):
      1) AWS_PROFILE (SSO o perfil en ~/.aws/config + ~/.aws/credentials)
      2) Variables de entorno estáticas: AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY
      3) Credenciales por defecto del entorno (p.ej. role en EC2/ECS)

    Env usados:
      - S3_BUCKET_AUDIO  (bucket destino)
      - AWS_REGION       (región, ej: us-east-1)
      - AWS_PROFILE      (perfil SSO/local)
      - AWS_SDK_LOAD_CONFIG=1  (recomendado para SSO)
    """

    def __init__(self, *, bucket: str | None = None, region: str | None = None, profile: str | None = None):
        self.bucket = bucket or os.getenv("S3_BUCKET_AUDIO")
        if not self.bucket:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="S3_BUCKET_AUDIO no está definido en el entorno."
            )

        self.region = region or os.getenv("AWS_REGION") or "us-east-1"

        # Construimos la sesión de boto3 respetando AWS_PROFILE si existe
        profile = profile or os.getenv("AWS_PROFILE")
        try:
            if profile:
                # Para SSO, asegúrate de exportar AWS_SDK_LOAD_CONFIG=1
                session = boto3.session.Session(profile_name=profile, region_name=self.region)
            else:
                session = boto3.session.Session(region_name=self.region)

            self.client = session.client("s3", region_name=self.region)
        except (BotoCoreError, Exception) as e:
            # Cualquier error al iniciar cliente
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"No se pudo inicializar el cliente S3: {e}"
            )

    def presign_put(self, *, key: str, content_type: str, expires_sec: int = 900) -> Dict[str, str]:
        """
        Genera URL prefirmada tipo PUT para subir un objeto.
        Devuelve: { bucket, key, upload_url, required_headers, expires_in }
        """
        # Headers requeridos por S3 para que valide ContentType
        params = {
            "Bucket": self.bucket,
            "Key": key,
            "ContentType": content_type,
        }

        try:
            url = self.client.generate_presigned_url(
                ClientMethod="put_object",
                Params=params,
                ExpiresIn=expires_sec,
                HttpMethod="PUT",
            )
            return {
                "bucket": self.bucket,
                "key": key,
                "upload_url": url,
                "required_headers": {
                    "Content-Type": content_type
                },
                "expires_in": expires_sec,
            }

        except TokenRetrievalError:
            # Caso típico de tu log: token SSO vencido
            profile = os.getenv("AWS_PROFILE", "<tu-perfil>")
            hint = (
                f"AWS SSO expirado. Ejecuta: 'aws sso login --profile {profile}' "
                "y asegúrate de tener AWS_SDK_LOAD_CONFIG=1"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=hint
            )

        except NoCredentialsError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No hay credenciales AWS válidas. Usa AWS_PROFILE o variables de acceso de IAM."
            )

        except ClientError as e:
            # Errores firmando/validando contra S3
            code = e.response.get("Error", {}).get("Code", "ClientError")
            msg = e.response.get("Error", {}).get("Message", str(e))
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error de AWS S3 ({code}): {msg}"
            )

        except BotoCoreError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error de AWS SDK: {e}"
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Fallo al generar URL prefirmada: {e}"
            )

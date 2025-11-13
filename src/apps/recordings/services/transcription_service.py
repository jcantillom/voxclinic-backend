# src/apps/recordings/services/transcription_service.py
import boto3
import json
import os
import logging
from typing import Optional, Dict
from botocore.exceptions import BotoCoreError, ClientError
from sqlalchemy.orm import Session
from ..models import Recording

logger = logging.getLogger(__name__)


class TranscriptionService:
    def __init__(self):
        self.transcribe_client = boto3.client(
            'transcribe',
            region_name=os.getenv('AWS_REGION'),
        )
        self.s3_client = boto3.client('s3', region_name=os.getenv('AWS_REGION'))
        self.bucket_name = os.getenv('S3_BUCKET_AUDIO')

    def start_transcription_job(
            self,
            recording: Recording,
            language_code: str = 'es-ES'
    ) -> bool:
        """Inicia un trabajo de transcripción en AWS Transcribe"""
        try:
            job_name = f"transcribe-{recording.id}-{int(recording.created_at.timestamp())}"
            job_name = job_name[:200]  # Limitar longitud

            media_uri = f"s3://{recording.bucket}/{recording.key}"

            response = self.transcribe_client.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={'MediaFileUri': media_uri},
                MediaFormat=self._get_media_format(recording.content_type),
                LanguageCode=language_code,
                Settings={
                    'ShowSpeakerLabels': True,
                    'MaxSpeakerLabels': 2,
                    'ChannelIdentification': False
                },
                OutputBucketName=self.bucket_name,
                OutputKey=f"transcripts/{job_name}.json"
            )

            logger.info(f"Transcription job started: {job_name}")
            return True

        except (BotoCoreError, ClientError) as e:
            logger.error(f"Error starting transcription job: {e}")
            return False

    def get_transcription_status(self, recording: Recording) -> Dict:
        """Obtiene el estado y resultado de la transcripción"""
        try:
            job_name = f"transcribe-{recording.id}-{int(recording.created_at.timestamp())}"
            job_name = job_name[:200]

            # Obtener estado del job desde Transcribe
            response = self.transcribe_client.get_transcription_job(
                TranscriptionJobName=job_name
            )

            job_status = response['TranscriptionJob']['TranscriptionJobStatus']

            if job_status == 'COMPLETED':
                # Leer el archivo JSON de resultados desde S3
                transcript_key = f"transcripts/{job_name}.json"

                try:
                    transcript_obj = self.s3_client.get_object(
                        Bucket=self.bucket_name,
                        Key=transcript_key
                    )
                    transcript_data = json.loads(transcript_obj['Body'].read().decode('utf-8'))

                    transcript_text = transcript_data['results']['transcripts'][0]['transcript']

                    return {
                        "transcription_status": "COMPLETED",
                        "transcript_text": transcript_text,
                        "error": None
                    }

                except Exception as e:
                    logger.error(f"Error reading transcript file: {e}")
                    return {
                        "transcription_status": "ERROR",
                        "transcript_text": None,
                        "error": f"Could not read transcript: {str(e)}"
                    }

            elif job_status == 'FAILED':
                failure_reason = response['TranscriptionJob'].get('FailureReason', 'Unknown error')
                logger.error(f"Transcription failed: {failure_reason}")
                return {
                    "transcription_status": "FAILED",
                    "transcript_text": None,
                    "error": failure_reason
                }
            else:
                return {
                    "transcription_status": job_status,
                    "transcript_text": None,
                    "error": None
                }

        except ClientError as e:
            if e.response['Error']['Code'] == 'BadRequestException':
                # Job no encontrado, probablemente no iniciado
                return {
                    "transcription_status": "NOT_STARTED",
                    "transcript_text": None,
                    "error": None
                }
            logger.error(f"Error getting transcription status: {e}")
            return {
                "transcription_status": "ERROR",
                "transcript_text": None,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error getting transcription status: {e}")
            return {
                "transcription_status": "ERROR",
                "transcript_text": None,
                "error": str(e)
            }

    def _get_media_format(self, content_type: str) -> str:
        """Mapea content_type a formato de Transcribe"""
        format_map = {
            'audio/wav': 'wav',
            'audio/x-wav': 'wav',
            'audio/mpeg': 'mp3',
            'audio/mp3': 'mp3',
            'audio/webm': 'webm',
            'audio/ogg': 'ogg',
        }
        return format_map.get(content_type, 'webm')  # default a webm

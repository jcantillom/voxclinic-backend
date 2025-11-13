import boto3
import json
import os
from typing import Optional, Dict
from botocore.exceptions import BotoCoreError, ClientError
from sqlalchemy.orm import Session
from .models import Recording
from .repository import RecordingRepository


class TranscriptionService:
    def __init__(self):
        self.transcribe_client = boto3.client(
            'transcribe',
            region_name=os.getenv('AWS_REGION'),
        )
        self.s3_client = boto3.client('s3', region_name=os.getenv('AWS_REGION'))

    def start_transcription_job(
            self,
            recording: Recording,
            language_code: str = 'es-ES'
    ) -> bool:
        """Inicia un trabajo de transcripción en AWS Transcribe"""
        try:
            job_name = f"transcribe-{recording.id}-{int(recording.created_at.timestamp())}"

            # Limitar longitud del nombre del job (máx 200 caracteres)
            job_name = job_name[:200]

            media_uri = f"s3://{recording.bucket}/{recording.key}"

            response = self.transcribe_client.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={'MediaFileUri': media_uri},
                MediaFormat='webm',  # o 'mp3', 'wav' según tu formato
                LanguageCode=language_code,
                Settings={
                    'ShowSpeakerLabels': True,
                    'MaxSpeakerLabels': 2,  # Médico y paciente
                    'ChannelIdentification': False
                },
                OutputBucketName=os.getenv('S3_BUCKET_AUDIO'),  # Mismo bucket o uno diferente
                OutputKey=f"transcripts/{recording.id}.json"
            )

            print(f"Transcription job started: {job_name}")
            return True

        except (BotoCoreError, ClientError) as e:
            print(f"Error starting transcription job: {e}")
            return False

    def get_transcription_result(self, job_name: str) -> Optional[Dict]:
        """Obtiene el resultado de la transcripción"""
        try:
            response = self.transcribe_client.get_transcription_job(
                TranscriptionJobName=job_name
            )

            job_status = response['TranscriptionJob']['TranscriptionJobStatus']

            if job_status == 'COMPLETED':
                # Obtener la URL del resultado
                transcript_file_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']

                # Extraer la clave S3 del URI
                # El formato es: https://s3.region.amazonaws.com/bucket/key
                bucket_key = transcript_file_uri.split('/')[-2:]
                bucket_name = bucket_key[0]
                file_key = bucket_key[1]

                # Descargar el archivo de transcripción
                transcript_obj = self.s3_client.get_object(
                    Bucket=bucket_name,
                    Key=file_key
                )

                transcript_data = json.loads(transcript_obj['Body'].read().decode('utf-8'))

                # Extraer el texto transcrito
                transcript_text = transcript_data['results']['transcripts'][0]['transcript']

                return {
                    'text': transcript_text,
                    'raw_data': transcript_data,
                    'job_status': job_status
                }

            elif job_status in ['FAILED', 'CANCELLED']:
                failure_reason = response['TranscriptionJob'].get('FailureReason', 'Unknown error')
                return {
                    'text': None,
                    'error': failure_reason,
                    'job_status': job_status
                }
            else:
                return {
                    'text': None,
                    'job_status': job_status  # 'IN_PROGRESS', 'QUEUED'
                }

        except (BotoCoreError, ClientError) as e:
            print(f"Error getting transcription result: {e}")
            return None

    def transcribe_audio_sync(self, recording: Recording) -> Optional[str]:
        """
        Transcripción síncrona (para audios cortos < 2 minutos)
        Usar solo para pruebas o audios muy cortos
        """
        try:
            # Descargar audio de S3
            audio_obj = self.s3_client.get_object(
                Bucket=recording.bucket,
                Key=recording.key
            )
            audio_content = audio_obj['Body'].read()

            # Usar transcribe con audio directamente (límite 2MB)
            response = self.transcribe_client.start_transcription_job(
                TranscriptionJobName=f"sync-{recording.id}",
                Media={'MediaFileUri': f"s3://{recording.bucket}/{recording.key}"},
                MediaFormat='webm',
                LanguageCode='es-ES'
            )

            # Esperar resultado (no recomendado para producción)
            import time
            max_wait = 300  # 5 minutos máximo
            wait_time = 0

            while wait_time < max_wait:
                result = self.get_transcription_result(f"sync-{recording.id}")
                if result and result['job_status'] == 'COMPLETED':
                    return result['text']
                elif result and result['job_status'] in ['FAILED', 'CANCELLED']:
                    return None

                time.sleep(10)  # Esperar 10 segundos
                wait_time += 10

            return None

        except Exception as e:
            print(f"Error in sync transcription: {e}")
            return None

# src/apps/onboarding/services.py
import logging
import os
from sqlalchemy.orm import Session
from sqlalchemy import select
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from ..tenant.services import TenantService
from ..tenant.repository import TenantRepository
from ..users.services import UserService
from ..users.repository import UserRepository
import uuid
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class OnboardingService:
    def __init__(self):
        self.tenant_service = TenantService(TenantRepository())
        self.user_service = UserService(UserRepository())

    async def process_onboarding_request(
            self,
            db: Session,
            request_data: dict
    ) -> dict:
        """Procesa solicitud de onboarding y notifica al admin"""

        try:
            # 1. Generar código único para la institución
            institution_code = self._generate_institution_code(request_data['institution_name'])

            # 2. Crear tenant en estado "pending_approval"
            tenant = self.tenant_service.create(
                db,
                code=institution_code,
                name=request_data['institution_name'],
                meta={
                    "onboarding_status": "pending",
                    "institution_type": request_data['institution_type'],
                    "contact_name": request_data['contact_name'],
                    "contact_email": request_data['contact_email'],
                    "contact_phone": request_data['contact_phone'],
                    "estimated_doctors": request_data.get('estimated_doctors', 1),
                    "estimated_recordings": request_data.get('estimated_recordings_month', 10),
                    "message": request_data.get('message', ''),
                    "created_at": datetime.now().isoformat()
                }
            )

            # 3. Notificar al equipo de DataVox (opcional - comentar si no hay API key)
            # await self._notify_admin_team(tenant, request_data)

            # 4. Enviar confirmación al solicitante (opcional)
            # await self._send_confirmation_email(request_data)

            logger.info(f"Onboarding request created for {request_data['institution_name']}")

            return {
                "request_id": str(tenant.id),
                "institution_code": institution_code,
                "status": "under_review",
                "message": "Solicitud recibida. Nos contactaremos dentro de 24 horas."
            }

        except Exception as e:
            logger.error(f"Error processing onboarding request: {e}")
            raise

    def _generate_institution_code(self, institution_name: str) -> str:
        """Genera código único para institución"""
        import re
        # Limpiar nombre para crear código
        base_code = re.sub(r'[^a-zA-Z0-9]', '-', institution_name.lower())
        base_code = re.sub(r'-+', '-', base_code).strip('-')

        return f"{base_code}-{uuid.uuid4().hex[:6]}"

    async def _notify_admin_team(self, tenant, request_data: dict):
        """Notifica al equipo admin de DataVox sobre nueva solicitud"""
        try:
            # Solo enviar email si hay API key configurada
            api_key = os.getenv('SENDGRID_API_KEY')
            if not api_key:
                logger.warning("SENDGRID_API_KEY not configured - skipping email notification")
                return

            message = Mail(
                from_email=os.getenv('FROM_EMAIL', 'notifications@datavoxmedical.com'),
                to_emails=os.getenv('ADMIN_EMAIL', 'admin@datavoxmedical.com'),
                subject=f'📋 Nueva Solicitud - {request_data["institution_name"]}',
                html_content=self._get_admin_email_content(tenant, request_data)
            )

            sg = SendGridAPIClient(api_key)
            response = sg.send(message)
            logger.info(f"Admin notification sent - Status: {response.status_code}")

        except Exception as e:
            logger.error(f"Error sending admin notification: {e}")

    async def _send_confirmation_email(self, request_data: dict):
        """Envía confirmación al solicitante"""
        try:
            api_key = os.getenv('SENDGRID_API_KEY')
            if not api_key:
                logger.warning("SENDGRID_API_KEY not configured - skipping confirmation email")
                return

            message = Mail(
                from_email=os.getenv('FROM_EMAIL', 'onboarding@datavoxmedical.com'),
                to_emails=request_data['contact_email'],
                subject='Solicitud Recibida - DataVox Medical',
                html_content=self._get_confirmation_email_content(request_data)
            )

            sg = SendGridAPIClient(api_key)
            response = sg.send(message)
            logger.info(f"Confirmation email sent to {request_data['contact_email']} - Status: {response.status_code}")

        except Exception as e:
            logger.error(f"Error sending confirmation email: {e}")

    def _get_admin_email_content(self, tenant, request_data: dict) -> str:
        return f"""
        <h2>Nueva Solicitud de Onboarding</h2>
        <p><strong>Institución:</strong> {request_data['institution_name']}</p>
        <p><strong>Tipo:</strong> {request_data['institution_type']}</p>
        <p><strong>Contacto:</strong> {request_data['contact_name']}</p>
        <p><strong>Email:</strong> {request_data['contact_email']}</p>
        <p><strong>Teléfono:</strong> {request_data['contact_phone']}</p>
        <p><strong>Médicos estimados:</strong> {request_data.get('estimated_doctors', 'N/A')}</p>
        <p><strong>Dictados/mes:</strong> {request_data.get('estimated_recordings_month', 'N/A')}</p>
        <p><strong>Mensaje:</strong> {request_data.get('message', 'N/A')}</p>
        <br>
        <p><strong>ID Tenant:</strong> {tenant.id}</p>
        <p><strong>Código:</strong> {tenant.code}</p>
        """

    def _get_confirmation_email_content(self, request_data: dict) -> str:
        return f"""
        <h2>¡Gracias por su interés en DataVox Medical!</h2>
        <p>Estimado/a {request_data['contact_name']},</p>
        <p>Hemos recibido su solicitud para <strong>{request_data['institution_name']}</strong>.</p>
        <p>Nuestro equipo se contactará con usted dentro de las próximas 24 horas hábiles para programar una demostración personalizada.</p>
        <br>
        <p><strong>Próximos pasos:</strong></p>
        <ol>
            <li>Evaluaremos sus necesidades específicas</li>
            <li>Programaremos una demo personalizada</li>
            <li>Configuraremos su entorno institucional</li>
        </ol>
        <br>
        <p>Saludos cordiales,<br>Equipo DataVox Medical</p>
        """

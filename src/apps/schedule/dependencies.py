from fastapi import Depends

from .services import AppointmentService
from .repository import AppointmentRepository
from src.apps.patients.repository import PatientRepository


def get_patient_repo() -> PatientRepository:
    return PatientRepository()

def get_appointment_service(patient_repo: PatientRepository = Depends(get_patient_repo)) -> AppointmentService:
    return AppointmentService(AppointmentRepository(), patient_repo)
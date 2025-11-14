from typing import List
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session
from src.core.connections.deps import get_db, get_current_tenant, get_current_user
from src.core.middlewares.permissions import require_roles
from .schemas import PatientCreate, PatientOut, PatientUpdate
from .services import PatientService
from .repository import PatientRepository

router = APIRouter(prefix="/patients", tags=["Patients"])


def get_service() -> PatientService:
    return PatientService(PatientRepository())


@router.post(
    "",
    response_model=PatientOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo paciente",
    dependencies=[Depends(require_roles("owner", "admin", "staff"))],
)
def create_patient(
        payload: PatientCreate,
        db: Session = Depends(get_db),
        tenant=Depends(get_current_tenant),
        svc: PatientService = Depends(get_service),
):
    p = svc.create_patient(
        db,
        tenant=tenant,
        identifier=payload.identifier,
        full_name=payload.full_name,
        date_of_birth=payload.date_of_birth,
        is_active=payload.is_active,
        meta=payload.meta
    )
    return PatientOut.model_validate(p)


@router.get(
    "",
    response_model=List[PatientOut],
    summary="Listar y buscar pacientes del tenant",
    dependencies=[Depends(require_roles("owner", "admin", "staff", "viewer"))],
)
def list_patients(
        response: Response,
        db: Session = Depends(get_db),
        tenant=Depends(get_current_tenant),
        _=Depends(get_current_user),
        q: str | None = Query(None, description="Buscar por email/full_name"),
        page: int = Query(1, ge=1),
        page_size: int = Query(5, ge=1, le=50),  # Establecemos 5 por defecto
        svc: PatientService = Depends(get_service),
):
    rows, total = svc.search_patients(
        db, tenant=tenant, q=q, page=page, page_size=page_size
    )
    # CORRECCIÓN CLAVE: Agregar el header para que el frontend pueda calcular las páginas
    response.headers["X-Total-Count"] = str(total)

    return [PatientOut.model_validate(x) for x in rows]


@router.get(
    "/{patient_id}",
    response_model=PatientOut,
    summary="Obtener paciente por ID",
    dependencies=[Depends(require_roles("owner", "admin", "staff", "viewer"))],
)
def get_patient(
        patient_id: str,
        db: Session = Depends(get_db),
        tenant=Depends(get_current_tenant),
        svc: PatientService = Depends(get_service),
):
    p = svc.get_patient(db, patient_id, str(tenant.id))
    return PatientOut.model_validate(p)


@router.patch(
    "/{patient_id}",
    response_model=PatientOut,
    summary="Actualizar parcialmente datos del paciente",
    dependencies=[Depends(require_roles("owner", "admin", "staff"))],
)
def update_patient_data(
        patient_id: str,
        payload: PatientUpdate,
        db: Session = Depends(get_db),
        tenant=Depends(get_current_tenant),
        svc: PatientService = Depends(get_service),
):
    updated = svc.update_patient(db, patient_id, str(tenant.id), payload.model_dump(exclude_unset=True))
    return PatientOut.model_validate(updated)

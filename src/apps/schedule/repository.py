from typing import Optional, Sequence
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session
from .models import Appointment
from datetime import date, datetime, timedelta


class AppointmentRepository:
    @staticmethod
    def create(db: Session, **data) -> Appointment:
        a = Appointment(**data)
        db.add(a)
        db.flush()
        db.refresh(a)
        return a

    @staticmethod
    def list_by_user_and_day(
        db: Session, user_id: str, target_date: date, tenant_id: str
    ) -> Sequence[Appointment]:
        # Filtra por el día (ignorando la hora en la BD si es TIMESTAMP(timezone=True))
        # SQLA no tiene date() directo sobre TIMESTAMP con tz, por lo que usamos comparación de rango
        start_of_day = datetime(target_date.year, target_date.month, target_date.day)
        end_of_day = start_of_day + timedelta(days=1)

        return db.execute(
            select(Appointment)
            .where(
                Appointment.tenant_id == tenant_id,
                Appointment.user_id == user_id,
                and_(
                    Appointment.start_time >= start_of_day,
                    Appointment.start_time < end_of_day,
                )
            )
            .order_by(Appointment.start_time.asc())
        ).scalars().all()
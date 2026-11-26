from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Reservation
from ..schemas import ReservationIn, ReservationOut
from ..services import reservations as svc

router = APIRouter(prefix="/api/reservations", tags=["reservations"])


@router.post("", response_model=ReservationOut)
def create(data: ReservationIn, db: Session = Depends(get_db)) -> Reservation:
    return svc.create_reservation(db, data, source="web")


@router.get("/{code}", response_model=ReservationOut)
def get(code: str, db: Session = Depends(get_db)) -> Reservation:
    return svc.get_by_code(db, code)

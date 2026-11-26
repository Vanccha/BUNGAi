import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Reservation
from ..schemas import ReservationIn
from .availability import ServiceError, get_bungalow, is_available, validate_range

_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_code(db: Session) -> str:
    while True:
        code = "BNG-" + "".join(secrets.choice(_ALPHABET) for _ in range(6))
        if db.scalars(select(Reservation.id).where(Reservation.code == code)).first() is None:
            return code


def create_reservation(db: Session, data: ReservationIn, source: str = "web") -> Reservation:
    b = get_bungalow(db, data.bungalow_id)
    _, _, nights = validate_range(data.check_in, data.check_out)
    if data.guests > b.capacity:
        raise ServiceError(422, f"Bu bungalov en fazla {b.capacity} kişiliktir.")
    if not is_available(db, b.id, data.check_in, data.check_out):
        raise ServiceError(409, "Seçtiğiniz tarihler bu bungalov için müsait değil.")
    r = Reservation(
        code=generate_code(db),
        bungalow_id=b.id,
        guest_name=data.guest_name.strip(),
        guest_email=str(data.guest_email),
        guest_phone=data.guest_phone.strip(),
        check_in=data.check_in,
        check_out=data.check_out,
        guests=data.guests,
        nights=nights,
        total_price=round(nights * b.price_per_night, 2),
        note=data.note,
        status="pending_payment",
        source=source,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def get_by_code(db: Session, code: str) -> Reservation:
    r = db.scalars(select(Reservation).where(Reservation.code == code.strip().upper())).first()
    if r is None:
        raise ServiceError(404, "Rezervasyon bulunamadı.")
    return r

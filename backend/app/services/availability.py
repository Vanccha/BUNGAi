from datetime import date, datetime, timedelta

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from ..models import Bungalow, Reservation, utcnow

PENDING_HOLD_MINUTES = 30


class ServiceError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def parse_date(value: str, label: str = "Tarih") -> date:
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        raise ServiceError(422, f"{label} geçersiz. Beklenen biçim: YYYY-AA-GG.") from None


def validate_range(check_in: str, check_out: str) -> tuple[date, date, int]:
    ci = parse_date(check_in, "Giriş tarihi")
    co = parse_date(check_out, "Çıkış tarihi")
    if co <= ci:
        raise ServiceError(422, "Çıkış tarihi giriş tarihinden sonra olmalıdır.")
    if ci < date.today():
        raise ServiceError(422, "Giriş tarihi geçmişte olamaz.")
    return ci, co, (co - ci).days


def get_bungalow(db: Session, bungalow_id: int, active_only: bool = True) -> Bungalow:
    b = db.get(Bungalow, bungalow_id)
    if b is None or (active_only and not b.is_active):
        raise ServiceError(404, "Bungalov bulunamadı.")
    return b


def _blocking_filter(cutoff: datetime):
    return or_(
        Reservation.status == "confirmed",
        and_(Reservation.status == "pending_payment", Reservation.created_at > cutoff),
    )


def is_available(
    db: Session, bungalow_id: int, check_in: str, check_out: str, exclude_reservation_id: int | None = None
) -> bool:
    cutoff = utcnow() - timedelta(minutes=PENDING_HOLD_MINUTES)
    stmt = select(Reservation.id).where(
        Reservation.bungalow_id == bungalow_id,
        _blocking_filter(cutoff),
        Reservation.check_in < check_out,
        Reservation.check_out > check_in,
    )
    if exclude_reservation_id is not None:
        stmt = stmt.where(Reservation.id != exclude_reservation_id)
    return db.scalars(stmt.limit(1)).first() is None


def quote(db: Session, bungalow_id: int, check_in: str, check_out: str) -> dict:
    b = get_bungalow(db, bungalow_id)
    _, _, nights = validate_range(check_in, check_out)
    return {
        "available": is_available(db, bungalow_id, check_in, check_out),
        "nights": nights,
        "total_price": round(nights * b.price_per_night, 2),
    }


def booked_dates(db: Session, bungalow_id: int, month: str) -> list[str]:
    try:
        first = datetime.strptime(month, "%Y-%m").date()
    except ValueError:
        raise ServiceError(422, "Ay biçimi geçersiz. Beklenen biçim: YYYY-AA.") from None
    get_bungalow(db, bungalow_id)
    nxt = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
    cutoff = utcnow() - timedelta(minutes=PENDING_HOLD_MINUTES)
    rows = db.scalars(
        select(Reservation).where(
            Reservation.bungalow_id == bungalow_id,
            _blocking_filter(cutoff),
            Reservation.check_in < nxt.isoformat(),
            Reservation.check_out > first.isoformat(),
        )
    ).all()
    days: set[str] = set()
    for r in rows:
        d = date.fromisoformat(r.check_in)
        end = date.fromisoformat(r.check_out)
        while d < end:  # check_out günü bloklanmaz
            if first <= d < nxt:
                days.add(d.isoformat())
            d += timedelta(days=1)
    return sorted(days)


def find_available(db: Session, check_in: str, check_out: str, guests: int) -> list[Bungalow]:
    validate_range(check_in, check_out)
    bungalows = db.scalars(
        select(Bungalow).where(Bungalow.is_active.is_(True), Bungalow.capacity >= guests).order_by(Bungalow.price_per_night)
    ).all()
    return [b for b in bungalows if is_available(db, b.id, check_in, check_out)]

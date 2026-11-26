import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Payment, Reservation
from ..schemas import CardIn
from .availability import ServiceError, is_available
from .reservations import get_by_code

SUCCESS_CARDS = {"5528790000000008", "4766620000000001"}
FAILURE_CARDS = {
    "4111111111111129": "Yetersiz bakiye.",
    "4129111111111111": "Kart limiti aşıldı / işlem reddedildi.",
}


def luhn_valid(number: str) -> bool:
    if not number.isdigit() or not 12 <= len(number) <= 19:
        return False
    total = 0
    for i, ch in enumerate(reversed(number)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def payment_url(token: str) -> str:
    return f"/odeme/{token}"


def init_payment(db: Session, reservation_code: str) -> Payment:
    r = get_by_code(db, reservation_code)
    if r.status == "confirmed":
        raise ServiceError(409, "Bu rezervasyonun ödemesi zaten tamamlanmış.")
    if r.status == "cancelled":
        raise ServiceError(409, "Bu rezervasyon iptal edilmiş.")
    p = Payment(token=secrets.token_urlsafe(24), reservation_id=r.id, amount=r.total_price, status="initialized")
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def get_payment(db: Session, token: str) -> Payment:
    p = db.scalars(select(Payment).where(Payment.token == token)).first()
    if p is None:
        raise ServiceError(404, "Ödeme bulunamadı.")
    return p


def complete_payment(db: Session, token: str, card: CardIn) -> tuple[Payment, str]:
    p = get_payment(db, token)
    r: Reservation = p.reservation
    if p.status == "success" or r.status == "confirmed":
        raise ServiceError(409, "Bu ödeme zaten tamamlanmış.")
    if r.status == "cancelled":
        raise ServiceError(409, "Bu rezervasyon iptal edilmiş.")

    number = "".join(ch for ch in card.card_number if ch.isdigit())
    if number in SUCCESS_CARDS:
        ok, message = True, ""
    elif number in FAILURE_CARDS:
        ok, message = False, FAILURE_CARDS[number]
    elif luhn_valid(number):
        ok, message = True, ""
    else:
        ok, message = False, "Geçersiz kart numarası."

    if ok and not is_available(db, r.bungalow_id, r.check_in, r.check_out, exclude_reservation_id=r.id):
        raise ServiceError(409, "Süre dolduğu için bu tarihler başka bir misafire ayrıldı. Lütfen yeni bir rezervasyon oluşturun.")

    if ok:
        p.status = "success"
        r.status = "confirmed"
        message = "Ödemeniz başarıyla alındı. Rezervasyonunuz onaylandı."
    else:
        p.status = "failure"
        r.status = "payment_failed"
    db.commit()
    db.refresh(p)
    return p, message

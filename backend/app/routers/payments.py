from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Payment
from ..schemas import CardIn, PaymentInitIn, PaymentInitOut, PaymentOut, PaymentResult
from ..services import payments as svc

router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.post("/init", response_model=PaymentInitOut)
def init(data: PaymentInitIn, db: Session = Depends(get_db)) -> dict:
    p = svc.init_payment(db, data.reservation_code)
    return {"token": p.token, "amount": p.amount, "payment_page_url": svc.payment_url(p.token)}


@router.get("/{token}", response_model=PaymentOut)
def get(token: str, db: Session = Depends(get_db)) -> Payment:
    return svc.get_payment(db, token)


@router.post("/{token}/complete", response_model=PaymentResult)
def complete(token: str, card: CardIn, db: Session = Depends(get_db)) -> dict:
    p, message = svc.complete_payment(db, token, card)
    return {"status": p.status, "message": message, "reservation": p.reservation}

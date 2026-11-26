from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Bungalow, Settings
from ..schemas import AvailabilityOut, BungalowOut, CalendarOut, SettingsPublic
from ..services import availability

router = APIRouter(prefix="/api", tags=["public"])


@router.get("/settings/public", response_model=SettingsPublic)
def public_settings(db: Session = Depends(get_db)) -> Settings:
    s = db.scalars(select(Settings)).first()
    if s is None:
        raise HTTPException(404, "Ayarlar bulunamadı.")
    return s


@router.get("/bungalows", response_model=list[BungalowOut])
def list_bungalows(db: Session = Depends(get_db)) -> list[Bungalow]:
    return list(db.scalars(select(Bungalow).where(Bungalow.is_active.is_(True)).order_by(Bungalow.price_per_night)))


@router.get("/bungalows/{slug}", response_model=BungalowOut)
def get_bungalow(slug: str, db: Session = Depends(get_db)) -> Bungalow:
    b = db.scalars(select(Bungalow).where(Bungalow.slug == slug, Bungalow.is_active.is_(True))).first()
    if b is None:
        raise HTTPException(404, "Bungalov bulunamadı.")
    return b


@router.get("/availability", response_model=AvailabilityOut)
def check_availability(bungalow_id: int, check_in: str, check_out: str, db: Session = Depends(get_db)) -> dict:
    return availability.quote(db, bungalow_id, check_in, check_out)


@router.get("/availability/calendar", response_model=CalendarOut)
def calendar(bungalow_id: int, month: str, db: Session = Depends(get_db)) -> dict:
    return {"booked_dates": availability.booked_dates(db, bungalow_id, month)}

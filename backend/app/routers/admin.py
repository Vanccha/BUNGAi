import hmac
import re
from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import rag
from ..agent.bot import build_always_section, run_chat_with_debug
from ..config import config
from ..database import get_db
from ..models import Bungalow, KnowledgeEntry, Reservation, Settings, VoiceSession
from ..schemas import (
    BungalowIn,
    BungalowOut,
    ChatIn,
    ChatTestOut,
    KnowledgeIn,
    KnowledgeOut,
    LoginIn,
    RagSearchIn,
    RagStats,
    ReindexIn,
    SearchTraceOut,
    ReservationOut,
    SettingsFull,
    VoiceSessionDetail,
    VoiceSessionListItem,
    StatsOut,
    StatusPatch,
    TokenOut,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])
bearer = HTTPBearer(auto_error=False)
ALGO = "HS256"


def require_admin(creds: HTTPAuthorizationCredentials | None = Depends(bearer)) -> str:
    if creds is None:
        raise HTTPException(401, "Giriş yapmanız gerekiyor.", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(creds.credentials, config.jwt_secret, algorithms=[ALGO])
    except jwt.PyJWTError:
        raise HTTPException(401, "Oturum geçersiz veya süresi dolmuş.", headers={"WWW-Authenticate": "Bearer"}) from None
    return str(payload.get("sub", ""))


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn) -> TokenOut:
    ok_user = hmac.compare_digest(data.username.encode(), config.admin_username.encode())
    ok_pass = hmac.compare_digest(data.password.encode(), config.admin_password.encode())
    if not (ok_user and ok_pass):
        raise HTTPException(401, "Kullanıcı adı veya şifre hatalı.")
    exp = datetime.now(timezone.utc) + timedelta(hours=12)
    token = jwt.encode({"sub": data.username, "exp": exp}, config.jwt_secret, algorithm=ALGO)
    return TokenOut(access_token=token)


@router.get("/me")
def me(user: str = Depends(require_admin)) -> dict:
    return {"username": user}


# ---- Settings ----
@router.get("/settings", response_model=SettingsFull)
def get_settings(_: str = Depends(require_admin), db: Session = Depends(get_db)) -> Settings:
    return db.scalars(select(Settings)).one()


@router.put("/settings", response_model=SettingsFull)
def put_settings(data: SettingsFull, _: str = Depends(require_admin), db: Session = Depends(get_db)) -> Settings:
    s = db.scalars(select(Settings)).one()
    for k, v in data.model_dump().items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return s


# ---- Knowledge ----
@router.get("/knowledge", response_model=list[KnowledgeOut])
def list_knowledge(_: str = Depends(require_admin), db: Session = Depends(get_db)) -> list[KnowledgeEntry]:
    return list(db.scalars(select(KnowledgeEntry).order_by(KnowledgeEntry.category, KnowledgeEntry.sort_order, KnowledgeEntry.id)))


@router.post("/knowledge", response_model=KnowledgeOut)
def create_knowledge(data: KnowledgeIn, background: BackgroundTasks, _: str = Depends(require_admin), db: Session = Depends(get_db)) -> KnowledgeEntry:
    e = KnowledgeEntry(**data.model_dump())
    db.add(e)
    db.flush()                                            # e.id oluşsun
    needs_index = rag.mark_pending_if_changed(db, e)      # always ise parça yok; search ise durum 'pending'
    db.commit()
    db.refresh(e)
    if needs_index:
        background.add_task(rag.index_entry, e.id)        # yanıt döndükten sonra arka planda indekslenir
    return e


def _get_knowledge(db: Session, entry_id: int) -> KnowledgeEntry:
    e = db.get(KnowledgeEntry, entry_id)
    if e is None:
        raise HTTPException(404, "Bilgi kaydı bulunamadı.")
    return e


@router.put("/knowledge/{entry_id}", response_model=KnowledgeOut)
def update_knowledge(entry_id: int, data: KnowledgeIn, background: BackgroundTasks, _: str = Depends(require_admin), db: Session = Depends(get_db)) -> KnowledgeEntry:
    e = _get_knowledge(db, entry_id)
    for k, v in data.model_dump().items():
        setattr(e, k, v)
    needs_index = rag.mark_pending_if_changed(db, e)      # hash değişmediyse (örn. sadece sıra/aktiflik) pending olmaz
    db.commit()
    db.refresh(e)
    rag.invalidate_cache()                                # is_active / mode değişmiş olabilir: vektör önbelleğini yenile
    if needs_index:
        background.add_task(rag.index_entry, e.id)
    return e


@router.delete("/knowledge/{entry_id}")
def delete_knowledge(entry_id: int, _: str = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    e = _get_knowledge(db, entry_id)
    rag.remove_entry(db, e.id)                            # parçaları + FTS satırlarını sil
    db.delete(e)
    db.commit()
    return {"ok": True}


# ---- RAG ----
ALWAYS_TOKEN_LIMIT = 20000


@router.get("/rag/stats", response_model=RagStats)
def rag_stats(_: str = Depends(require_admin), db: Session = Depends(get_db)) -> RagStats:
    from ..rag.chunking import count_tokens

    def count(*conds) -> int:
        return db.scalar(select(func.count()).select_from(KnowledgeEntry).where(*conds)) or 0

    search_mode = KnowledgeEntry.mode == "search"
    last = db.scalar(select(func.max(KnowledgeEntry.indexed_at)))
    return RagStats(
        always_entries=count(KnowledgeEntry.mode == "always", KnowledgeEntry.is_active.is_(True)),
        always_tokens=count_tokens(build_always_section(db)),
        always_token_limit=ALWAYS_TOKEN_LIMIT,
        search_entries=count(search_mode),
        chunks=rag.count_chunks(db),
        indexed_entries=count(search_mode, KnowledgeEntry.index_status == "indexed"),
        pending_entries=count(search_mode, KnowledgeEntry.index_status == "pending"),
        error_entries=count(search_mode, KnowledgeEntry.index_status == "error"),
        embedding_model=rag.EMBEDDING_MODEL,
        embeddings_enabled=rag.embeddings_enabled(),
        last_indexed_at=last.isoformat() if last else None,
    )


@router.post("/rag/reindex")
def rag_reindex(data: ReindexIn | None = None, _: str = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    force = bool(data and data.force)
    # Yeniden indekslenecek kayıtlar 'pending' görünsün (arayüz ilerlemeyi gösterebilsin)
    for e in db.scalars(select(KnowledgeEntry).where(KnowledgeEntry.mode == "search")):
        if force or e.index_status != "indexed":
            e.index_status = "pending"
    db.commit()
    rag.start_background_reindex(force=force)
    return {"started": True}


@router.post("/rag/search", response_model=SearchTraceOut)
def rag_search(data: RagSearchIn, _: str = Depends(require_admin), db: Session = Depends(get_db)) -> SearchTraceOut:
    return SearchTraceOut.model_validate(asdict(rag.search(db, data.query, top_k=data.top_k)))


# ---- Bungalows ----
_TR = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.translate(_TR).lower()).strip("-")
    return s or "bungalov"


def _unique_slug(db: Session, base: str, exclude_id: int | None = None) -> str:
    slug, i = base, 2
    while True:
        q = select(Bungalow.id).where(Bungalow.slug == slug)
        found = db.scalars(q).first()
        if found is None or found == exclude_id:
            return slug
        slug = f"{base}-{i}"
        i += 1


def _apply_bungalow(b: Bungalow, data: BungalowIn, slug: str) -> None:
    b.slug = slug
    b.name = data.name
    b.short_description = data.short_description
    b.description = data.description
    b.capacity = data.capacity
    b.bedrooms = data.bedrooms
    b.size_m2 = data.size_m2
    b.price_per_night = data.price_per_night
    b.amenities = data.amenities
    b.images = data.images
    b.is_active = data.is_active


@router.get("/bungalows", response_model=list[BungalowOut])
def admin_list_bungalows(_: str = Depends(require_admin), db: Session = Depends(get_db)) -> list[Bungalow]:
    return list(db.scalars(select(Bungalow).order_by(Bungalow.id)))


@router.post("/bungalows", response_model=BungalowOut)
def create_bungalow(data: BungalowIn, _: str = Depends(require_admin), db: Session = Depends(get_db)) -> Bungalow:
    b = Bungalow()
    _apply_bungalow(b, data, _unique_slug(db, slugify(data.slug or data.name)))
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


def _get_bungalow(db: Session, bungalow_id: int) -> Bungalow:
    b = db.get(Bungalow, bungalow_id)
    if b is None:
        raise HTTPException(404, "Bungalov bulunamadı.")
    return b


@router.put("/bungalows/{bungalow_id}", response_model=BungalowOut)
def update_bungalow(bungalow_id: int, data: BungalowIn, _: str = Depends(require_admin), db: Session = Depends(get_db)) -> Bungalow:
    b = _get_bungalow(db, bungalow_id)
    slug = _unique_slug(db, slugify(data.slug), b.id) if data.slug else b.slug
    _apply_bungalow(b, data, slug)
    db.commit()
    db.refresh(b)
    return b


@router.delete("/bungalows/{bungalow_id}")
def delete_bungalow(bungalow_id: int, _: str = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    b = _get_bungalow(db, bungalow_id)
    has_res = db.scalars(select(Reservation.id).where(Reservation.bungalow_id == b.id).limit(1)).first()
    if has_res is not None:
        raise HTTPException(409, "Bu bungalovun rezervasyonları var; silmek yerine pasif yapabilirsiniz.")
    db.delete(b)
    db.commit()
    return {"ok": True}


# ---- Reservations ----
@router.get("/reservations", response_model=list[ReservationOut])
def list_reservations(status: str | None = None, _: str = Depends(require_admin), db: Session = Depends(get_db)) -> list[Reservation]:
    q = select(Reservation).order_by(Reservation.created_at.desc(), Reservation.id.desc())
    if status:
        q = q.where(Reservation.status == status)
    return list(db.scalars(q))


@router.patch("/reservations/{reservation_id}", response_model=ReservationOut)
def patch_reservation(reservation_id: int, data: StatusPatch, _: str = Depends(require_admin), db: Session = Depends(get_db)) -> Reservation:
    r = db.get(Reservation, reservation_id)
    if r is None:
        raise HTTPException(404, "Rezervasyon bulunamadı.")
    r.status = data.status
    db.commit()
    db.refresh(r)
    return r


@router.get("/stats", response_model=StatsOut)
def stats(_: str = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    def count(*conds) -> int:
        return db.scalar(select(func.count()).select_from(Reservation).where(*conds)) or 0

    revenue = db.scalar(select(func.coalesce(func.sum(Reservation.total_price), 0)).where(Reservation.status == "confirmed")) or 0
    upcoming = db.scalars(
        select(Reservation)
        .where(Reservation.status == "confirmed", Reservation.check_in >= date.today().isoformat())
        .order_by(Reservation.check_in)
        .limit(10)
    ).all()
    return {
        "total_reservations": count(),
        "confirmed": count(Reservation.status == "confirmed"),
        "pending": count(Reservation.status == "pending_payment"),
        "revenue_confirmed": float(revenue),
        "upcoming_checkins": list(upcoming),
    }


# ---- Chat test ----
@router.post("/chat/test", response_model=ChatTestOut)
async def chat_test(data: ChatIn, _: str = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    out, searches = await run_chat_with_debug(db, data.session_id, data.message)
    return {**out.model_dump(), "debug": {"searches": [asdict(t) for t in searches]}}


# ---- Sesli görüşmeler ----
def _voice_item(v: VoiceSession) -> dict:
    tr = v.transcript
    first = next((t["text"] for t in tr if t.get("role") == "user" and t.get("text")), "")
    return {
        "id": v.id, "session_id": v.session_id, "model": v.model, "voice": v.voice, "status": v.status,
        "started_at": v.started_at, "ended_at": v.ended_at, "duration_seconds": v.duration_seconds,
        "turn_count": sum(1 for t in tr if t.get("role") in ("user", "assistant")),
        "first_user_text": first[:140], "reservation_codes": v.reservation_codes,
    }


@router.get("/voice/sessions", response_model=list[VoiceSessionListItem])
def list_voice_sessions(_: str = Depends(require_admin), db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(select(VoiceSession).order_by(VoiceSession.id.desc()).limit(200))
    return [_voice_item(v) for v in rows]


@router.get("/voice/sessions/{vid}", response_model=VoiceSessionDetail)
def get_voice_session(vid: int, _: str = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    v = db.get(VoiceSession, vid)
    if v is None:
        raise HTTPException(404, "Görüşme bulunamadı.")
    return {**_voice_item(v), "call_id": v.call_id, "transcript": v.transcript}

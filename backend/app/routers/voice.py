"""Sesli asistan uçları (bkz. app/voice/service.py ve CONTRACT.md)."""
import asyncio
import time
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Settings
from ..schemas import VoiceActionsOut, VoiceAttachIn, VoiceSessionOut
from ..voice import service
from ..voice.service import VoiceError

router = APIRouter(prefix="/api/voice", tags=["voice"])

# Basit IP başına hız sınırı (dakikada 6 oturum): kötüye kullanım / maliyet koruması
_HITS: dict[str, deque[float]] = defaultdict(deque)


def _rate_limit(request: Request) -> None:
    ip = request.client.host if request.client else "?"
    q = _HITS[ip]
    now = time.time()
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= 6:
        raise HTTPException(429, "Çok sık deneme yaptınız. Lütfen biraz bekleyin.")
    q.append(now)


def _wrap(e: VoiceError) -> HTTPException:
    return HTTPException(e.status, e.detail)


@router.post("/session", response_model=VoiceSessionOut)
async def create_session(request: Request, db: Session = Depends(get_db)) -> dict:
    """Geçici (ephemeral) anahtar üretir. Talimatlar, araçlar, VAD, ses sunucuda sabitlenir."""
    _rate_limit(request)
    s = db.scalars(select(Settings)).first()
    try:
        data = await asyncio.to_thread(service.create_session_sync)
    except VoiceError as e:
        raise _wrap(e) from e
    data["greeting"] = s.voice_greeting if s else ""
    return data


@router.post("/session/{session_id}/attach")
async def attach(session_id: str, body: VoiceAttachIn) -> dict:
    """Tarayıcı WebRTC bağlantısını kurunca call_id'yi bildirir; backend aynı çağrıya yan kanal WebSocket'i açar."""
    try:
        service.attach(session_id, body.call_id)
    except VoiceError as e:
        raise _wrap(e) from e
    return {"ok": True}


@router.get("/session/{session_id}/actions", response_model=VoiceActionsOut)
def actions(session_id: str, after: int = 0) -> dict:
    """Araç çağrılarından doğan arayüz kartları (rezervasyon özeti, ödeme bağlantısı). `after` = görülen sayı."""
    try:
        rt = service.get_runtime(session_id)
    except VoiceError as e:
        raise _wrap(e) from e
    return {"actions": rt.actions[after:], "next": len(rt.actions), "ended": rt.ended}


@router.post("/session/{session_id}/end")
async def end(session_id: str) -> dict:
    await service.end_session(session_id)
    return {"ok": True}

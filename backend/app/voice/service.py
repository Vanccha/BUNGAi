"""Sesli asistan oturum yönetimi: geçici anahtar üretme + YAN KANAL (sideband) olay işleme.

MİMARİ (özet; ayrıntı için SESLI_ASISTAN.md):

    Tarayıcı ──WebRTC (ses + oai-events veri kanalı)──► OpenAI Realtime
        │                                                    ▲
        │  POST /api/voice/session  (geçici anahtar)         │ WebSocket  wss://.../v1/realtime?call_id=...
        │  POST /api/voice/session/{id}/attach {call_id}     │ (yan kanal: araç çağrıları + döküm)
        ▼                                                    │
    FastAPI backend ─────────────────────────────────────────┘

* Ses tarayıcı ile OpenAI arasında DOĞRUDAN akar (en düşük gecikme).
* Aynı çağrıya backend de bir WebSocket ile bağlanır. Model bir araç çağırınca olayı backend görür,
  aracı sunucuda çalıştırır ve sonucu aynı WebSocket'ten modele yollar. Araç çağrıları tarayıcıdan geçmez;
  tarayıcı yalnızca kart (rezervasyon/ödeme) göstermek için `GET .../actions` ile sonuçları çeker.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

import requests
import websockets

from ..config import config
from ..database import SessionLocal
from ..models import VoiceSession
from .instructions import build_session_config, lexicon_of
from .tools import VOICE_TOOL_NAMES, run_voice_tool

log = logging.getLogger("bungai.voice")

OPENAI_BASE = "https://api.openai.com/v1"
SECRET_TTL_SECONDS = 120          # geçici anahtarın kullanılabileceği süre (bağlantı kurmak için)
GRACE_SECONDS = 10                # sunucu tarafı zorla kapatma payı (istemci kendi sayacıyla zaten kapatır)
MAX_CONCURRENT = 8                # aynı anda en fazla aktif görüşme (maliyet koruması)
_CALL_ID_RE = re.compile(r"^rtc_[A-Za-z0-9_\-]{4,100}$")


class VoiceError(Exception):
    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status, self.detail = status, detail


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


@dataclass
class VoiceRuntime:
    """Bellekte tutulan canlı oturum durumu (tek süreçli kurulum için yeterli)."""

    session_id: str
    model: str
    voice: str
    max_seconds: int
    lex: dict[str, str]
    instructions: str
    tool_names: set[str]
    created: float = field(default_factory=time.time)
    call_id: str | None = None
    attached: bool = False
    ended: bool = False
    started: float | None = None
    actions: list[dict[str, Any]] = field(default_factory=list)
    transcript: list[dict[str, Any]] = field(default_factory=list)
    reservation_codes: list[str] = field(default_factory=list)
    task: asyncio.Task | None = None
    expected: dict[str, Any] = field(default_factory=dict)  # bütünlük kontrolü için beklenen oturum ayarı


_SESSIONS: dict[str, VoiceRuntime] = {}


def get_runtime(session_id: str) -> VoiceRuntime:
    rt = _SESSIONS.get(session_id)
    if rt is None:
        raise VoiceError(404, "Sesli görüşme oturumu bulunamadı veya süresi doldu.")
    return rt


def _gc() -> None:
    now = time.time()
    for sid, rt in list(_SESSIONS.items()):
        if now - rt.created > rt.max_seconds + 3600:
            _SESSIONS.pop(sid, None)


def active_count() -> int:
    return sum(1 for r in _SESSIONS.values() if not r.ended and time.time() - r.created < r.max_seconds + 120)


# ------------------------------------------------------------------ kalıcılık
def persist(rt: VoiceRuntime, status: str | None = None) -> None:
    with SessionLocal() as db:
        row = db.query(VoiceSession).filter_by(session_id=rt.session_id).first()
        if row is None:
            return
        row.call_id = rt.call_id
        row.transcript_json = json.dumps(rt.transcript, ensure_ascii=False)
        row.reservation_codes_json = json.dumps(rt.reservation_codes)
        if status:
            row.status = status
        if rt.started:
            row.duration_seconds = int(time.time() - rt.started)
        if status in ("ended", "error"):
            row.ended_at = _now()
        db.commit()


def add_turn(rt: VoiceRuntime, role: str, text: str = "", **extra: Any) -> dict[str, Any]:
    entry = {"role": role, "text": text, "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), **extra}
    rt.transcript.append(entry)
    return entry


# ------------------------------------------------------------------ geçici anahtar
def _post_client_secret(body: dict) -> dict:
    r = requests.post(
        f"{OPENAI_BASE}/realtime/client_secrets",
        headers={"Authorization": f"Bearer {config.openai_api_key.strip()}"},
        json=body,
        timeout=20,
    )
    if r.status_code >= 400:
        log.error("client_secrets hata %s: %s", r.status_code, r.text[:500])
        raise VoiceError(502, "Sesli asistan şu anda başlatılamadı. Lütfen biraz sonra tekrar deneyin.")
    return r.json()


def create_session_sync() -> dict:
    """POST /api/voice/session gövdesi. (Bloklayıcı: router thread'de çağırır.)"""
    if not config.openai_api_key.strip():
        raise VoiceError(503, "Sesli asistan yapılandırılmamış.")
    _gc()
    if active_count() >= MAX_CONCURRENT:
        raise VoiceError(429, "Şu anda çok fazla sesli görüşme var. Lütfen birazdan tekrar deneyin.")

    with SessionLocal() as db:
        from ..agent.bot import load_prompt_parts

        s = load_prompt_parts(db).s
        if not s.voice_enabled:
            raise VoiceError(403, "Sesli asistan şu anda kapalı.")
        session_cfg = build_session_config(db)
        max_seconds = int(s.voice_max_session_seconds or 300)
        lex = lexicon_of(s)

    data = _post_client_secret(
        {"expires_after": {"anchor": "created_at", "seconds": SECRET_TTL_SECONDS}, "session": session_cfg}
    )
    sid = "vs_" + secrets.token_urlsafe(18)
    rt = VoiceRuntime(
        session_id=sid,
        model=session_cfg["model"],
        voice=session_cfg["audio"]["output"]["voice"],
        max_seconds=max_seconds,
        lex=lex,
        instructions=session_cfg["instructions"],
        tool_names={t["name"] for t in session_cfg["tools"]},
        expected={"type": "realtime", "instructions": session_cfg["instructions"], "tools": session_cfg["tools"], "tool_choice": "auto"},
    )
    _SESSIONS[sid] = rt
    with SessionLocal() as db:
        db.add(VoiceSession(session_id=sid, model=rt.model, voice=rt.voice, status="created"))
        db.commit()
    return {
        "client_secret": data["value"],
        "expires_at": data["expires_at"],
        "model": rt.model,
        "session_id": sid,
        "max_seconds": max_seconds,
    }


def hangup_sync(call_id: str) -> None:
    try:
        requests.post(
            f"{OPENAI_BASE}/realtime/calls/{call_id}/hangup",
            headers={"Authorization": f"Bearer {config.openai_api_key.strip()}"},
            timeout=10,
        )
    except requests.RequestException:
        log.warning("hangup başarısız (çağrı zaten kapanmış olabilir)")


# ------------------------------------------------------------------ olay işleme (yan kanal beyni)
Send = Callable[[dict], Awaitable[None]]


class VoiceBrain:
    """Realtime olaylarını işler: döküm toplar, araçları çalıştırır, oturum bütünlüğünü korur.
    Bağlantıdan bağımsızdır: WebSocket'e (sideband) de, smoke test'in doğrudan WebSocket'ine de takılır."""

    def __init__(self, rt: VoiceRuntime, send: Send, *, verbose: bool = False):
        self.rt = rt
        self.send = send
        self.verbose = verbose
        self._placeholders: dict[str, dict] = {}   # item_id -> döküm kaydı (sıralama korunsun)
        self._fixes = 0
        self.tool_log: list[dict] = []            # smoke test için
        self.assistant_lines: list[str] = []      # smoke test için

    async def on_event(self, ev: dict) -> None:
        t = ev.get("type", "")
        if t in ("conversation.item.added", "conversation.item.created"):
            self._on_item(ev.get("item") or {}, final=False)
        elif t == "conversation.item.done":
            self._on_item(ev.get("item") or {}, final=True)
        elif t == "conversation.item.input_audio_transcription.completed":
            self._on_user_transcript(ev.get("item_id", ""), ev.get("transcript", ""))
        elif t == "response.output_audio_transcript.done":
            text = (ev.get("transcript") or "").strip()
            if text:
                add_turn(self.rt, "assistant", text)
                self.assistant_lines.append(text)
                persist(self.rt)
        elif t == "response.done":
            await self._on_response_done(ev.get("response") or {})
        elif t in ("session.updated", "session.created"):
            await self._check_integrity(ev.get("session") or {})
        elif t == "error":
            log.warning("Realtime hata olayı: %s", json.dumps(ev.get("error"), ensure_ascii=False)[:400])

    # -- döküm
    def _on_item(self, item: dict, final: bool) -> None:
        if item.get("type") != "message" or item.get("role") != "user":
            return
        iid = item.get("id", "")
        texts = [c.get("text") for c in item.get("content", []) if c.get("type") == "input_text" and c.get("text")]
        if texts:  # klavyeden yazılan metin
            if iid in self._placeholders:
                self._placeholders[iid]["text"] = " ".join(texts)
            elif not any(e.get("item_id") == iid for e in self.rt.transcript):
                e = add_turn(self.rt, "user", " ".join(texts), item_id=iid, typed=True)
                self._placeholders[iid] = e
            persist(self.rt)
        elif iid and iid not in self._placeholders:
            # Sesli giriş: transkript sonra gelir; sırayı korumak için şimdiden yer ayır.
            self._placeholders[iid] = add_turn(self.rt, "user", "", item_id=iid)

    def _on_user_transcript(self, item_id: str, text: str) -> None:
        text = (text or "").strip()
        e = self._placeholders.get(item_id)
        if e is None:
            e = add_turn(self.rt, "user", text, item_id=item_id)
            self._placeholders[item_id] = e
        e["text"] = text
        persist(self.rt)

    # -- araçlar
    async def _on_response_done(self, resp: dict) -> None:
        calls = [o for o in resp.get("output", []) if o.get("type") == "function_call"]
        if not calls:
            return
        for c in calls:
            name, args, call_id = c.get("name", ""), c.get("arguments", "{}"), c.get("call_id", "")
            t0 = time.time()
            if name not in self.rt.tool_names or name not in VOICE_TOOL_NAMES:
                output, actions = json.dumps({"error": "Bilinmeyen araç."}, ensure_ascii=False), []
            else:
                output, actions = await asyncio.to_thread(self._run_tool, name, args)
            ms = int((time.time() - t0) * 1000)
            for a in actions:
                self.rt.actions.append(a)
                code = a.get("reservation", {}).get("code") if a.get("type") == "reservation_summary" else None
                if code and code not in self.rt.reservation_codes:
                    self.rt.reservation_codes.append(code)
            add_turn(self.rt, "tool", name=name, arguments=args, output=output[:1500], ms=ms)
            self.tool_log.append({"name": name, "arguments": args, "output": output, "ms": ms})
            persist(self.rt)
            await self.send({
                "type": "conversation.item.create",
                "item": {"type": "function_call_output", "call_id": call_id, "output": output},
            })
        await self.send({"type": "response.create"})

    def _run_tool(self, name: str, args: str) -> tuple[str, list[dict]]:
        with SessionLocal() as db:   # her araç çağrısı kendi DB oturumuyla (thread güvenliği)
            try:
                return run_voice_tool(db, name, args, lex=self.rt.lex)
            except Exception:  # noqa: BLE001 - araç hatası görüşmeyi düşürmesin
                log.exception("Sesli araç hatası: %s", name)
                return json.dumps({"error": "Araç şu anda çalışmıyor."}, ensure_ascii=False), []

    # -- bütünlük: tarayıcı veri kanalından talimat/araç değiştirmeye kalkarsa geri al
    async def _check_integrity(self, sess: dict) -> None:
        if not sess:
            return
        ins, tools = sess.get("instructions"), sess.get("tools")
        bad = (ins is not None and ins.strip() != self.rt.instructions.strip()) or (
            tools is not None and {t.get("name") for t in tools} != self.rt.tool_names
        )
        if bad and self._fixes < 3:
            self._fixes += 1
            log.warning("Oturum talimat/araç değişikliği algılandı; geri alınıyor (%s)", self.rt.session_id)
            await self.send({"type": "session.update", "session": self.rt.expected})


# ------------------------------------------------------------------ yan kanal bağlantısı
async def run_sideband(rt: VoiceRuntime) -> None:
    url = f"wss://api.openai.com/v1/realtime?call_id={rt.call_id}"
    headers = {"Authorization": f"Bearer {config.openai_api_key.strip()}"}
    deadline = (rt.started or time.time()) + rt.max_seconds + GRACE_SECONDS
    status = "ended"
    try:
        async with websockets.connect(url, additional_headers=headers, max_size=None, ping_interval=20) as ws:

            async def send(ev: dict) -> None:
                await ws.send(json.dumps(ev))

            brain = VoiceBrain(rt, send)

            async def reader() -> None:
                async for raw in ws:
                    try:
                        ev = json.loads(raw)
                    except ValueError:
                        continue
                    if ev.get("type", "").startswith("response.output_audio.delta"):
                        continue
                    await brain.on_event(ev)

            reader_task = asyncio.create_task(reader())
            try:
                await asyncio.wait_for(asyncio.shield(reader_task), timeout=max(1, deadline - time.time()))
            except asyncio.TimeoutError:
                # Süre doldu: çağrıyı sunucu tarafında kapat (istemci kapatmayı atlasa bile maliyet durur).
                log.info("Görüşme süresi doldu, kapatılıyor: %s", rt.session_id)
                await asyncio.to_thread(hangup_sync, rt.call_id)
                reader_task.cancel()
    except websockets.exceptions.ConnectionClosed:
        pass  # çağrı kapandı (kullanıcı bitirdi / süre doldu): normal sonlanma
    except Exception:  # noqa: BLE001
        log.exception("Yan kanal hatası (%s)", rt.session_id)
        status = "error"
    finally:
        rt.ended = True
        persist(rt, status)


def attach(session_id: str, call_id: str) -> VoiceRuntime:
    rt = get_runtime(session_id)
    if not _CALL_ID_RE.match(call_id or ""):
        raise VoiceError(422, "Geçersiz çağrı kimliği.")
    if rt.attached:
        raise VoiceError(409, "Bu oturum zaten bağlandı.")
    if time.time() - rt.created > SECRET_TTL_SECONDS + 60:
        raise VoiceError(410, "Oturumun süresi doldu; lütfen yeniden başlatın.")
    rt.attached, rt.call_id, rt.started = True, call_id, time.time()
    persist(rt, "active")
    rt.task = asyncio.create_task(run_sideband(rt))
    return rt


async def end_session(session_id: str) -> None:
    rt = _SESSIONS.get(session_id)
    if rt is None or rt.ended:
        return
    if rt.call_id:
        await asyncio.to_thread(hangup_sync, rt.call_id)
    persist(rt, "ended")

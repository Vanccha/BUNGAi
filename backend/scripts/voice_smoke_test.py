"""Mikrofonsuz uçtan uca sesli asistan testi.

Sunucu tarafında, GERÇEK anahtarla bir Realtime WebSocket oturumu açar; oturum ayarı
/api/voice/session'ın kullandığı fonksiyonla (build_session_config) AYNIDIR; araç çağrıları
canlı sistemle AYNI dispatcher'dan (VoiceBrain -> run_voice_tool) geçer. Kullanıcı turları METİN olarak gönderilir,
asistanın SES çıktısının transkripti yazdırılır.

Çalıştırma (backend/ klasöründen):
    .venv/Scripts/python.exe scripts/voice_smoke_test.py            # varsayılan senaryo
    .venv/Scripts/python.exe scripts/voice_smoke_test.py --model gpt-realtime-2.1
    .venv/Scripts/python.exe scripts/voice_smoke_test.py --audio    # ek: TTS ile üretilmiş Türkçe ses -> girdi transkripsiyonu
Test rezervasyonları sonunda otomatik iptal edilir (status=cancelled).
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")  # Windows konsolunda Türkçe karakterler

import requests  # noqa: E402
import websockets  # noqa: E402

from app.config import config  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models import Reservation  # noqa: E402
from app.voice.instructions import build_session_config, lexicon_of  # noqa: E402
from app.voice.service import VoiceBrain, VoiceRuntime  # noqa: E402

DEFAULT_TURNS = [
    "Merhaba, köpeğimi getirebilir miyim?",
    "Mavi Ufuk villası on ile on üç Temmuz iki bin yirmi yedi arası iki kişi için müsait mi, fiyatı ne olur?",
    "Güzel, onu ayırtmak istiyorum. Adım Ayşe Yılmaz, telefonum sıfır beş yüz otuz bir yüz on bir yirmi iki otuz üç, e-postam ayse nokta yilmaz et gmail nokta com.",
    "Evet, doğru.",
    "Evet, doğru.",
    "Hayır, özel bir notum yok.",
    "Evet, onaylıyorum.",
    "Ödemeyi nasıl yapacağım?",
]


async def run(turns: list[str], model: str | None, audio_test: bool, dump_types: bool) -> None:
    with SessionLocal() as db:
        cfg = build_session_config(db, for_websocket=True)
        s_lex = lexicon_of(__import__("app.agent.bot", fromlist=["x"]).load_prompt_parts(db).s)
        greeting = __import__("app.agent.bot", fromlist=["x"]).load_prompt_parts(db).s.voice_greeting
    if model:
        cfg["model"] = model
    print(f"== Oturum: model={cfg['model']} voice={cfg['audio']['output']['voice']} "
          f"vad={cfg['audio']['input']['turn_detection']['eagerness']} talimat={len(cfg['instructions'])} karakter")

    rt = VoiceRuntime(
        session_id="smoke", model=cfg["model"], voice=cfg["audio"]["output"]["voice"], max_seconds=300, lex=s_lex,
        instructions=cfg["instructions"], tool_names={t["name"] for t in cfg["tools"]},
        expected={"type": "realtime", "instructions": cfg["instructions"], "tools": cfg["tools"], "tool_choice": "auto"},
    )
    url = f"wss://api.openai.com/v1/realtime?model={cfg['model']}"
    headers = {"Authorization": f"Bearer {config.openai_api_key.strip()}"}
    types_seen: dict[str, int] = {}
    turn_done = asyncio.Event()
    transcripts_in: list[str] = []
    errors: list[dict] = []

    async with websockets.connect(url, additional_headers=headers, max_size=None) as ws:
        async def send(ev: dict) -> None:
            await ws.send(json.dumps(ev))

        brain = VoiceBrain(rt, send)

        async def reader() -> None:
            async for raw in ws:
                ev = json.loads(raw)
                t = ev.get("type", "")
                types_seen[t] = types_seen.get(t, 0) + 1
                if t == "error":
                    errors.append(ev.get("error"))
                    print("!! HATA:", json.dumps(ev.get("error"), ensure_ascii=False))
                if t == "conversation.item.input_audio_transcription.completed":
                    transcripts_in.append(ev.get("transcript", ""))
                if t == "response.output_audio_transcript.done":
                    print(f"   ASİSTAN: {ev.get('transcript')}")
                if t == "response.done":
                    outs = ev.get("response", {}).get("output", [])
                    if not any(o.get("type") == "function_call" for o in outs):
                        turn_done.set()
                if t != "response.output_audio.delta":
                    await brain.on_event(ev)

        rtask = asyncio.create_task(reader())
        # Oturum ayarını gönder (WebRTC yolunda bu, client_secrets isteğiyle yapılır)
        sess = {k: v for k, v in cfg.items() if k != "model"}
        await send({"type": "session.update", "session": sess})
        await asyncio.sleep(1.0)

        async def say(text: str, label: str = "KULLANICI") -> None:
            turn_done.clear()
            print(f"\n{label}: {text}")
            await send({"type": "conversation.item.create",
                        "item": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": text}]}})
            await send({"type": "response.create"})
            await asyncio.wait_for(turn_done.wait(), timeout=90)
            # araç çağrılarını göster
            while brain.tool_log:
                t = brain.tool_log.pop(0)
                print(f"   [araç] {t['name']}({t['arguments'][:200]}) -> {t['output'][:260]}... ({t['ms']} ms)")

        # Karşılama (tarayıcıda da böyle yapılır)
        turn_done.clear()
        print(f"\n[karşılama] {greeting}")
        await send({"type": "response.create", "response": {
            "instructions": f"Misafiri şu cümlelerle karşıla, başka bir şey ekleme: {greeting}"}})
        await asyncio.wait_for(turn_done.wait(), timeout=60)

        for t in turns:
            await say(t)

        if audio_test:
            await audio_turn(ws, send, turn_done, brain, transcripts_in)

        await asyncio.sleep(0.5)
        rtask.cancel()

    print("\n== Eylemler (arayüze gidecek):", json.dumps([{k: (v if k != 'reservation' else v['code']) for k, v in a.items()} for a in rt.actions], ensure_ascii=False))
    if dump_types:
        print("== Olay türleri:", json.dumps(types_seen, indent=0, ensure_ascii=False))
    # Kontroller
    all_text = " ".join(brain.assistant_lines)
    print("\n== KONTROLLER")
    print("  rakam içeren asistan cümleleri:", [l for l in brain.assistant_lines if re.search(r"\d", l)] or "yok")
    print("  markdown/liste işareti:", [l for l in brain.assistant_lines if re.search(r"[*#]|^\s*-\s|\bhttps?://", l)] or "yok")
    print("  cümle sayısı/tur:", [len(re.findall(r"[.!?]+", l)) for l in brain.assistant_lines])
    print("  rezervasyon kodları:", rt.reservation_codes)
    print("  hata olayları:", errors or "yok")
    if transcripts_in:
        print("  girdi transkriptleri:", transcripts_in)
    cancel_test_reservations(rt.reservation_codes)


async def audio_turn(ws, send, turn_done, brain, transcripts_in) -> None:
    """OpenAI TTS ile Türkçe konuşma üret -> 24 kHz PCM16 -> input_audio_buffer.append. Girdi transkripsiyonunu sınar."""
    text = "Merhaba, Kalkan'daki Zeytin Plunge Bungalov için on beş Ağustos'ta müsaitlik var mı?"
    r = requests.post(
        "https://api.openai.com/v1/audio/speech",
        headers={"Authorization": f"Bearer {config.openai_api_key.strip()}"},
        json={"model": "gpt-4o-mini-tts", "voice": "coral", "input": text, "response_format": "pcm"},  # pcm = 24 kHz 16-bit mono
        timeout=60,
    )
    r.raise_for_status()
    pcm = r.content
    print(f"\nSES GİRDİSİ ({len(pcm) / 48000:.1f} sn): {text}")
    turn_done.clear()
    chunk = 4800 * 2  # 100 ms
    for i in range(0, len(pcm), chunk):
        await send({"type": "input_audio_buffer.append", "audio": base64.b64encode(pcm[i:i + chunk]).decode()})
        await asyncio.sleep(0.05)
    silence = b"\x00" * chunk  # VAD konuşmanın bittiğini anlasın diye sessizlik
    for _ in range(25):
        await send({"type": "input_audio_buffer.append", "audio": base64.b64encode(silence).decode()})
        await asyncio.sleep(0.05)
    await asyncio.wait_for(turn_done.wait(), timeout=90)
    while brain.tool_log:
        t = brain.tool_log.pop(0)
        print(f"   [araç] {t['name']}({t['arguments'][:200]})")


def cancel_test_reservations(codes: list[str]) -> None:
    if not codes:
        return
    with SessionLocal() as db:
        for r in db.query(Reservation).filter(Reservation.code.in_(codes)).all():
            r.status = "cancelled"
        db.commit()
    print(f"  test rezervasyonları iptal edildi: {codes}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model")
    ap.add_argument("--audio", action="store_true")
    ap.add_argument("--dump-types", action="store_true")
    ap.add_argument("--turn", action="append", help="Varsayılan senaryo yerine kendi turların (tekrarlanabilir)")
    a = ap.parse_args()
    t0 = time.time()
    asyncio.run(run(a.turn or DEFAULT_TURNS, a.model, a.audio, a.dump_types))
    print(f"\n(süre: {time.time() - t0:.0f} sn)")

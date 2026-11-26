"""Sesli asistanın araçları: şemalar + dispatcher + "konusma" alanı ekleyen sarmalayıcı.

Araç GÖVDELERİ yazılı botla ortaktır (app/agent/tools.py -> TOOL_IMPLS). Burada yalnızca:
  1. Şemalar: Agents SDK'nın ürettiği JSON şemasından Realtime biçimine çevrilir (tek kaynak).
  2. run_voice_tool: bilinen araç adı + doğrulanmış argümanlarla gövdeyi çalıştırır.
  3. add_konusma: çıktıya sesli okunmaya hazır Türkçe "konusma" alanları ekler (turkish_speech.py).
"""
from __future__ import annotations

import json
from typing import Any

from ..agent.tools import ALL_TOOLS, TOOL_IMPLS, ChatContext
from . import turkish_speech as ts

# --- Yalnızca sesli asistana özel yardımcı araç ---------------------------------------------------
SPEAK_TOOL_NAME = "konusma_hazirla"
_SPEAK_KINDS = ["eposta", "telefon", "tarih", "tarih_araligi", "para", "sayi", "saat", "kod"]


def _strip_titles(o: Any) -> Any:
    """Pydantic'in eklediği gürültülü 'title' alanlarını temizler (jeton tasarrufu)."""
    if isinstance(o, dict):
        return {k: _strip_titles(v) for k, v in o.items() if k != "title"}
    if isinstance(o, list):
        return [_strip_titles(x) for x in o]
    return o


def voice_tool_schemas() -> list[dict]:
    tools = [
        {
            "type": "function",
            "name": t.name,
            "description": t.description,
            "parameters": _strip_titles(t.params_json_schema),
        }
        for t in ALL_TOOLS
    ]
    tools.append(
        {
            "type": "function",
            "name": SPEAK_TOOL_NAME,
            "description": (
                "Sayı, tarih, para, saat, telefon, e-posta veya kodu sesli okunacak Türkçe metne çevirir. "
                "Misafirin söylediği e-posta/telefonu geri okumadan, tarihleri/tutarı özetlemeden ve konusma alanı "
                "olmayan her rakamı okumadan önce çağır. Birden çok değeri tek çağrıda gönderebilirsin."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ogeler": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "tur": {"type": "string", "enum": _SPEAK_KINDS},
                                "deger": {
                                    "type": "string",
                                    "description": "tarih: YYYY-MM-DD; tarih_araligi: 'YYYY-MM-DD/YYYY-MM-DD'; saat: HH:MM; para/sayi: rakamlar; diğerleri: olduğu gibi.",
                                },
                            },
                            "required": ["tur", "deger"],
                        },
                    }
                },
                "required": ["ogeler"],
            },
        }
    )
    return tools


VOICE_TOOL_NAMES = {t["name"] for t in voice_tool_schemas()}

_STATUS_TR = {
    "pending_payment": "ödeme bekliyor",
    "confirmed": "onaylandı",
    "cancelled": "iptal edildi",
    "payment_failed": "ödeme başarısız oldu",
}


def _speak_item(tur: str, deger: str) -> str:
    if tur == "eposta":
        return ts.eposta_oku(deger)
    if tur == "telefon":
        return ts.telefon_oku(deger)
    if tur == "tarih":
        return ts.tarih_oku(deger)
    if tur == "tarih_araligi":
        a, b = deger.split("/", 1)
        return ts.tarih_araligi_oku(a, b)
    if tur == "para":
        return ts.para_oku(deger)
    if tur == "sayi":
        return ts.sayi_oku(deger)
    if tur == "saat":
        return ts.saat_oku(deger, dogal=True)
    if tur == "kod":
        return ts.kod_oku(deger)
    raise ValueError(f"Bilinmeyen tür: {tur}")


def _run_speak_tool(args: dict) -> dict:
    out = []
    for it in args.get("ogeler", [])[:12]:
        try:
            out.append({"tur": it.get("tur"), "deger": it.get("deger"), "konusma": _speak_item(it["tur"], str(it["deger"]))})
        except Exception as e:  # noqa: BLE001
            out.append({"tur": it.get("tur"), "deger": it.get("deger"), "hata": f"Okunamadı: {e}"})
    return {"sonuclar": out}


# --- konusma alanı ekleme ------------------------------------------------------------------------
def _gece(n: int) -> str:
    return f"{ts.sayi_oku(n)} gece"


def _kisi(n: int) -> str:
    return f"{ts.sayi_oku(n)} kişi"


def _resv_speech(r: dict, lex: dict[str, str]) -> dict:
    return {
        "kod": ts.kod_oku(r["code"]),
        "kod_ayirt_edici": ts.kod_oku(r["code"], ayirt_et=True),
        "bungalov": ts.telaffuz_duzelt(r["bungalow"], lex),
        "giris": ts.tarih_oku(r["check_in"]),
        "cikis": ts.tarih_oku(r["check_out"]),
        "gece": _gece(r["nights"]),
        "kisi": _kisi(r["guests"]),
        "toplam": ts.para_oku(r["total_price_try"]),
        "durum": _STATUS_TR.get(r["status"], r["status"]),
    }


def add_konusma(name: str, data: Any, lex: dict[str, str] | None = None, args: dict | None = None) -> Any:
    """Araç çıktısına (dict/list) sesli okunacak alanlar ekler. Ham alanlar korunur (model mantık yürütsün diye)."""
    lex = lex or {}
    args = args or {}
    # Giriş/çıkış tarihleri modelin kendi hesabına bırakılmasın (gün adı hatası olur): sunucu söyler.
    tarihler: dict[str, str] = {}
    if args.get("check_in") and args.get("check_out"):
        try:
            tarihler = {"giris": ts.tarih_oku(args["check_in"]), "cikis": ts.tarih_oku(args["check_out"])}
        except ValueError:
            pass
    if isinstance(data, dict) and "error" in data:
        data["konusma_hata"] = ts.metin_hazirla(str(data["error"]), lex)
        return data

    if name == "list_bungalows" and isinstance(data, list):
        for b in data:
            b["ad_konusma"] = ts.telaffuz_duzelt(b["name"], lex)
            b["gecelik_konusma"] = ts.para_oku(b["price_per_night_try"])
            b["kapasite_konusma"] = _kisi(b["capacity"])
        return {"bungalovlar": data}

    if name == "find_available_bungalows":
        data["gece_konusma"] = _gece(data["nights"])
        data["tarih_konusma"] = tarihler
        for b in data["available"]:
            b["ad_konusma"] = ts.telaffuz_duzelt(b["name"], lex)
            b["gecelik_konusma"] = ts.para_oku(b["price_per_night_try"])
            b["toplam_konusma"] = ts.para_oku(b["total_price_try"])
            b["kapasite_konusma"] = _kisi(b["capacity"])
        return data

    if name == "check_availability":
        n = max(1, int(data.get("nights", 1)))
        data["konusma"] = {
            "bungalov": ts.telaffuz_duzelt(data.get("bungalow_name", ""), lex),
            "gece": _gece(n),
            "toplam": ts.para_oku(data["total_price"]),
            "gecelik": ts.para_oku(round(data["total_price"] / n, 2)),
            "durum": "müsait" if data.get("available") else "müsait değil",
            **tarihler,
        }
        return data

    if name == "create_reservation" and "reservation" in data:
        data["konusma"] = _resv_speech(data["reservation"], lex)
        return data

    if name == "get_reservation_status" and "code" in data:
        data["konusma"] = _resv_speech(data, lex)
        return data

    if name == "create_payment_link" and "amount_try" in data:
        data["konusma"] = {"tutar": ts.para_oku(data["amount_try"])}
        return data

    if name == "search_knowledge" and "results" in data:
        for h in data["results"]:
            h["konusma"] = ts.metin_hazirla(h.pop("text", ""), lex)  # ham 'text' kaldırılır: model rakam okumasın
        return data

    return data


# --- Dispatcher ----------------------------------------------------------------------------------
def run_voice_tool(db, name: str, arguments: str | dict, *, lex: dict[str, str] | None = None) -> tuple[str, list[dict]]:
    """Aracı çalıştırır. Dönen: (modele gidecek JSON metni, arayüze gidecek 'actions' listesi).

    GÜVENLİK: yalnızca bilinen araç adları; argümanlar gövdenin imzasına göre süzülür (fazla alanlar atılır),
    ve gövdeler zaten REST uçlarıyla aynı servis katmanını/doğrulamayı kullanır.
    """
    lex = lex or {}
    if name not in VOICE_TOOL_NAMES:
        return json.dumps({"error": "Bilinmeyen araç."}, ensure_ascii=False), []
    try:
        args = json.loads(arguments) if isinstance(arguments, str) else dict(arguments)
        if not isinstance(args, dict):
            raise ValueError
    except ValueError:
        return json.dumps({"error": "Araç argümanları geçersiz."}, ensure_ascii=False), []

    if name == SPEAK_TOOL_NAME:
        return json.dumps(_run_speak_tool(args), ensure_ascii=False), []

    import inspect

    impl = TOOL_IMPLS[name]
    allowed = set(inspect.signature(impl).parameters) - {"c"}
    clean = {k: v for k, v in args.items() if k in allowed}
    ctx = ChatContext(db=db, source="voice")
    try:
        raw = impl(ctx, **clean)
    except TypeError:
        return json.dumps({"error": "Eksik veya geçersiz araç argümanı."}, ensure_ascii=False), []
    data = json.loads(raw)
    data = add_konusma(name, data, lex, clean)
    return json.dumps(data, ensure_ascii=False, default=str), ctx.actions

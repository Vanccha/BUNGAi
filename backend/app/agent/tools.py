"""Chatbot function tools. They reuse the same service layer as the REST endpoints."""
import asyncio
import json
from dataclasses import dataclass, field
from typing import Any

from agents import RunContextWrapper, function_tool
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import rag
from ..models import Bungalow
from ..schemas import ReservationIn, ReservationOut
from ..services import availability, payments, reservations
from ..services.availability import ServiceError


@dataclass
class ChatContext:
    """Per-request context: DB session + actions collected from tool calls."""

    db: Session
    actions: list[dict[str, Any]] = field(default_factory=list)
    searches: list[rag.SearchTrace] = field(default_factory=list)  # bu turda yapılan RAG aramaları (admin debug için)
    source: str = "chatbot"  # rezervasyon kaynağı: "chatbot" (yazılı sohbet) | "voice" (sesli asistan)


Ctx = RunContextWrapper[ChatContext]


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


def _bungalow_dict(b: Bungalow) -> dict[str, Any]:
    return {
        "id": b.id,
        "name": b.name,
        "short_description": b.short_description,
        "capacity": b.capacity,
        "bedrooms": b.bedrooms,
        "size_m2": b.size_m2,
        "price_per_night_try": b.price_per_night,
        "amenities": b.amenities,
    }


def _reservation_dict(r: Any) -> dict[str, Any]:
    return {
        "code": r.code,
        "bungalow": r.bungalow_name,
        "guest_name": r.guest_name,
        "check_in": r.check_in,
        "check_out": r.check_out,
        "guests": r.guests,
        "nights": r.nights,
        "total_price_try": r.total_price,
        "status": r.status,
    }




# ---------------------------------------------------------------------------
# Araç GÖVDELERİ: düz fonksiyonlar (do_*). Hem yazılı sohbet botunun @function_tool sarmalayıcıları
# hem de sesli asistanın dispatcher'ı (app/voice/tools.py) AYNI gövdeleri çağırır -> kod tekrarı yok.
# Hepsi JSON metni döndürür.
# ---------------------------------------------------------------------------
def do_list_bungalows(c: ChatContext) -> str:
    rows = c.db.scalars(
        select(Bungalow).where(Bungalow.is_active.is_(True)).order_by(Bungalow.price_per_night)
    ).all()
    return _json([_bungalow_dict(b) for b in rows])


def do_check_availability(c: ChatContext, bungalow_id: int, check_in: str, check_out: str) -> str:
    try:
        q = availability.quote(c.db, bungalow_id, check_in, check_out)
        b = availability.get_bungalow(c.db, bungalow_id)
        return _json({"bungalow_id": b.id, "bungalow_name": b.name, **q})
    except ServiceError as e:
        return _json({"error": e.detail})


def do_find_available_bungalows(c: ChatContext, check_in: str, check_out: str, guests: int) -> str:
    try:
        found = availability.find_available(c.db, check_in, check_out, guests)
        _, _, nights = availability.validate_range(check_in, check_out)
    except ServiceError as e:
        return _json({"error": e.detail})
    return _json(
        {
            "nights": nights,
            "available": [{**_bungalow_dict(b), "total_price_try": round(nights * b.price_per_night, 2)} for b in found],
        }
    )


def do_create_reservation(
    c: ChatContext,
    bungalow_id: int,
    guest_name: str,
    guest_email: str,
    guest_phone: str,
    check_in: str,
    check_out: str,
    guests: int,
    note: str | None = None,
) -> str:
    try:
        data = ReservationIn(
            bungalow_id=bungalow_id,
            guest_name=guest_name,
            guest_email=guest_email,  # type: ignore[arg-type]
            guest_phone=guest_phone,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            note=note,
        )
    except ValidationError as e:
        fields = ", ".join(str(err["loc"][0]) for err in e.errors())
        return _json({"error": f"Geçersiz veya eksik bilgi: {fields}"})
    try:
        r = reservations.create_reservation(c.db, data, source=c.source)
    except ServiceError as e:
        return _json({"error": e.detail})
    c.actions.append(
        {"type": "reservation_summary", "reservation": ReservationOut.model_validate(r).model_dump(mode="json")}
    )
    try:
        p = payments.init_payment(c.db, r.code)
    except ServiceError as e:
        return _json({"ok": True, "reservation": _reservation_dict(r), "payment_error": e.detail})
    url = payments.payment_url(p.token)
    c.actions.append(
        {"type": "payment_link", "reservation_code": p.reservation_code, "url": url, "amount": p.amount}
    )
    return _json({"ok": True, "reservation": _reservation_dict(r), "amount_try": p.amount, "payment_button": "Misafirin sohbet ekranında Ödemeye Geç butonu gösterildi."})


def do_create_payment_link(c: ChatContext, reservation_code: str) -> str:
    try:
        p = payments.init_payment(c.db, reservation_code)
    except ServiceError as e:
        return _json({"error": e.detail})
    url = payments.payment_url(p.token)
    c.actions.append(
        {"type": "payment_link", "reservation_code": p.reservation_code, "url": url, "amount": p.amount}
    )
    return _json({"ok": True, "amount_try": p.amount, "payment_button": "Misafirin sohbet ekranında Ödemeye Geç butonu gösterildi."})


def do_get_reservation_status(c: ChatContext, reservation_code: str) -> str:
    try:
        r = reservations.get_by_code(c.db, reservation_code)
    except ServiceError as e:
        return _json({"error": e.detail})
    return _json(_reservation_dict(r))


SEARCH_TOP_K = 4  # bota giden en fazla sonuç sayısı


def do_search_knowledge(c: ChatContext, query: str, category: str | None = None) -> str:
    """Senkron gövde. RAG araması ağ çağrısı (embedding) içerir; async çağıranlar thread'de çalıştırmalıdır."""
    trace = rag.search(c.db, query, SEARCH_TOP_K, category or None)
    if category and trace.below_threshold:
        # Model yanlış kategori seçmiş olabilir: filtre olmadan bir kez daha dene.
        c.searches.append(trace)
        trace = rag.search(c.db, query, SEARCH_TOP_K, None)
    c.searches.append(trace)
    if trace.below_threshold:
        return _json({"results": [], "below_threshold": True,
                      "note": "İlgili bilgi bulunamadı. Farklı kelimelerle bir kez daha deneyebilir ya da bilmediğini söyleyip telefon/e-posta verebilirsin."})
    return _json({
        "results": [{"title": h.entry_title, "category": h.category, "text": h.text} for h in trace.results],
        "below_threshold": False,
    })


# ---------------------------------------------------------------------------
# Agents SDK sarmalayıcıları (yazılı sohbet botu). Davranış değişmez; sadece gövdelere yönlendirir.
# ---------------------------------------------------------------------------
@function_tool
def list_bungalows(ctx: Ctx) -> str:
    """Tüm aktif bungalovları (id, ad, kapasite, gecelik fiyat, olanaklar) listeler."""
    return do_list_bungalows(ctx.context)


@function_tool
def check_availability(ctx: Ctx, bungalow_id: int, check_in: str, check_out: str) -> str:
    """Belirli bir bungalovun tarih aralığında müsait olup olmadığını ve toplam fiyatı döndürür.

    Args:
        bungalow_id: Bungalov id'si.
        check_in: Giriş tarihi, YYYY-MM-DD.
        check_out: Çıkış tarihi, YYYY-MM-DD.
    """
    return do_check_availability(ctx.context, bungalow_id, check_in, check_out)


@function_tool
def find_available_bungalows(ctx: Ctx, check_in: str, check_out: str, guests: int) -> str:
    """Verilen tarihlerde ve kişi sayısı için müsait bungalovları toplam fiyatlarıyla listeler.

    Args:
        check_in: Giriş tarihi, YYYY-MM-DD.
        check_out: Çıkış tarihi, YYYY-MM-DD.
        guests: Kişi sayısı.
    """
    return do_find_available_bungalows(ctx.context, check_in, check_out, guests)


@function_tool
def create_reservation(
    ctx: Ctx,
    bungalow_id: int,
    guest_name: str,
    guest_email: str,
    guest_phone: str,
    check_in: str,
    check_out: str,
    guests: int,
    note: str | None = None,
) -> str:
    """Rezervasyon oluşturur VE ödeme bağlantısını da otomatik hazırlar (ayrıca create_payment_link çağırma).
    SADECE misafir özeti açıkça onayladıktan sonra çağır. Sonuçtaki bungalov adını misafire aynen bildir.

    Args:
        bungalow_id: Bungalov id'si.
        guest_name: Misafirin adı soyadı.
        guest_email: Misafirin e-posta adresi.
        guest_phone: Misafirin telefon numarası.
        check_in: Giriş tarihi, YYYY-MM-DD.
        check_out: Çıkış tarihi, YYYY-MM-DD.
        guests: Kişi sayısı.
        note: Misafirin özel notu (opsiyonel).
    """
    return do_create_reservation(
        ctx.context, bungalow_id, guest_name, guest_email, guest_phone, check_in, check_out, guests, note
    )


@function_tool
def create_payment_link(ctx: Ctx, reservation_code: str) -> str:
    """Mevcut bir rezervasyon için YENİ ödeme bağlantısı oluşturur (örn. ödeme başarısız olduktan sonra tekrar denemek için).
    Yeni rezervasyon oluştururken çağırma; create_reservation bağlantıyı zaten verir.

    Args:
        reservation_code: Rezervasyon kodu, örn. BNG-7K2Q9X.
    """
    return do_create_payment_link(ctx.context, reservation_code)


@function_tool
def get_reservation_status(ctx: Ctx, reservation_code: str) -> str:
    """Rezervasyon kodu ile rezervasyonun durumunu sorgular.

    Args:
        reservation_code: Rezervasyon kodu, örn. BNG-7K2Q9X.
    """
    return do_get_reservation_status(ctx.context, reservation_code)


@function_tool
async def search_knowledge(ctx: Ctx, query: str, category: str | None = None) -> str:
    """İşletme bilgi bankasında arama yapar (menü, fiyatlar, kurallar, spa, aktiviteler, transfer, çocuk kulübü,
    düğün paketleri vb.). Sistem istemindeki 'her zaman bilinen' bölümde olmayan her bilgi için ÖNCE bunu çağır.
    Sonuç yetersizse farklı kelimelerle tekrar arayabilirsin.

    Args:
        query: Aranacak konu, doğal Türkçe ifade. Misafirin sorusunu anahtar kelimelerle zenginleştir (örn. "evcil hayvan köpek ücreti").
        category: Opsiyonel kategori filtresi. Geçerli değerler: Genel, Konaklama, Havuz & Plaj, Yeme-İçme, Spa & Wellness, Aktiviteler, Çocuk Kulübü, Etkinlik & Organizasyon, Ulaşım & Transfer, Politikalar, Güvenlik, Ödeme & Fatura, SSS. Çoğu zaman BOŞ bırak; yalnızca konudan tamamen eminsen kullan.
    """
    # Arama ağ çağrısı (embedding) içerir; olay döngüsünü bloklamamak için thread'de çalıştır.
    return await asyncio.to_thread(do_search_knowledge, ctx.context, query, category)


ALL_TOOLS = [
    search_knowledge,
    list_bungalows,
    check_availability,
    find_available_bungalows,
    create_reservation,
    create_payment_link,
    get_reservation_status,
]

# Sesli asistan dispatcher'ı için: araç adı -> düz gövde (ChatContext, **argümanlar)
TOOL_IMPLS = {
    "search_knowledge": do_search_knowledge,
    "list_bungalows": do_list_bungalows,
    "check_availability": do_check_availability,
    "find_available_bungalows": do_find_available_bungalows,
    "create_reservation": do_create_reservation,
    "create_payment_link": do_create_payment_link,
    "get_reservation_status": do_get_reservation_status,
}

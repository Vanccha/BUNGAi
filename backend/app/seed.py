"""Demo içerik (kurgusal tesis). Yalnızca veritabanı boşken, uygulama açılışında çalışır.
İçerik app/seed_data/ altındadır; bilgi bankası kayıtları sonra RAG indeksleyicisi tarafından parçalanıp indekslenir."""
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Bungalow, KnowledgeEntry, Reservation, Settings
from .seed_data.bungalows import BUNGALOWS, U
from .seed_data.knowledge_long import LONG_DOCS
from .seed_data.knowledge_short import SHORT

SAMPLE_GUESTS = [
    ("Ayşe Yılmaz", "ayse.yilmaz@example.com", "0532 111 22 33"),
    ("Mehmet Demir", "mehmet.demir@example.com", "0533 222 33 44"),
    ("Elif Kaya", "elif.kaya@example.com", "0535 333 44 55"),
    ("Can Öztürk", "can.ozturk@example.com", "0536 444 55 66"),
    ("Zeynep Arslan", "zeynep.arslan@example.com", "0537 555 66 77"),
]


def seed_if_empty(db: Session) -> None:
    if (db.scalar(select(func.count()).select_from(Settings)) or 0) > 0:
        return

    db.add(
        Settings(
            resort_name="BUNGAi Villa & Bungalov Resort",
            tagline="Akdeniz'in kıyısında, özel havuzlu villalarda yaz tatili",
            phone="+90 242 555 01 23",
            email="info@bungai.example",
            address="Kalamar Yolu Sk. No:8, Kalkan, Kaş / Antalya",
            check_in_time="15:00",
            check_out_time="11:00",
            map_embed_url="https://www.google.com/maps?q=Kalkan,Antalya&output=embed",
            bot_name="Bunga",
            bot_welcome_message="Merhaba! Ben Bunga, BUNGAi Villa & Bungalov Resort'un sanal asistanıyım. Özel havuzlu villalarımız, müsaitlik, restoran, spa, plaj ve rezervasyon konusunda size yardımcı olabilirim. Nasıl yardımcı olayım?",
            bot_extra_instructions="Misafirlere her zaman sıcak ve saygılı hitap et. İndirim veya kampanya sözü verme. Rakip tesisler hakkında yorum yapma.",
        )
    )

    bungalows: list[Bungalow] = []
    for data in BUNGALOWS:
        b = Bungalow(**{k: v for k, v in data.items() if k not in ("images", "amenities")})
        b.amenities = data["amenities"]
        b.images = [U.format(p) for p in data["images"]]
        db.add(b)
        bungalows.append(b)

    # Kısa kayıtlar (ilk 12'si "always") + uzun dokümanlar. Search modundaki kayıtlar "pending" başlar;
    # uygulama açılışında arka planda indekslenir (bkz. app/rag/indexer.py).
    rows = [(c, t, x, m) for c, t, x, m in SHORT] + [(c, t, x.strip(), "search") for c, t, x in LONG_DOCS]
    for i, (cat, title, content, mode) in enumerate(rows):
        db.add(KnowledgeEntry(
            category=cat, title=title, content=content, sort_order=i, mode=mode,
            index_status="not_applicable" if mode == "always" else "pending",
        ))

    db.flush()

    today = date.today()
    samples = [
        # (bungalov idx, misafir idx, başlangıç ofseti, gece, kişi, durum, kaynak)
        (2, 0, 14, 3, 4, "confirmed", "web"),
        (5, 1, 30, 2, 2, "confirmed", "chatbot"),
        (0, 2, 7, 3, 2, "confirmed", "web"),
        (4, 3, 21, 4, 5, "pending_payment", "chatbot"),
        (1, 4, -20, 3, 2, "confirmed", "web"),
        (6, 0, 45, 5, 8, "cancelled", "web"),
    ]
    for n, (bi, gi, off, nights, guests, status, source) in enumerate(samples):
        b = bungalows[bi]
        ci = today + timedelta(days=off)
        name, email, phone = SAMPLE_GUESTS[gi]
        r = Reservation(
            code=f"BNG-{'ABCDEF'[n]}{n + 1}K2Q9",
            bungalow_id=b.id,
            guest_name=name,
            guest_email=email,
            guest_phone=phone,
            check_in=ci.isoformat(),
            check_out=(ci + timedelta(days=nights)).isoformat(),
            guests=guests,
            nights=nights,
            total_price=nights * b.price_per_night,
            status=status,
            source=source,
        )
        # Sample pending reservation must not block dates forever: it is old enough to be ignored.
        if status == "pending_payment":
            from datetime import datetime

            r.created_at = datetime.utcnow() - timedelta(hours=3)
        db.add(r)
    db.commit()

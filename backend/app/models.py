import json
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Bungalow(Base):
    __tablename__ = "bungalows"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    short_description: Mapped[str] = mapped_column(String(500), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    capacity: Mapped[int] = mapped_column(Integer)
    bedrooms: Mapped[int] = mapped_column(Integer, default=1)
    size_m2: Mapped[int] = mapped_column(Integer, default=30)
    price_per_night: Mapped[float] = mapped_column(Float)
    amenities_json: Mapped[str] = mapped_column(Text, default="[]")
    images_json: Mapped[str] = mapped_column(Text, default="[]")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    @property
    def amenities(self) -> list[str]:
        return json.loads(self.amenities_json or "[]")

    @amenities.setter
    def amenities(self, v: list[str]) -> None:
        self.amenities_json = json.dumps(v, ensure_ascii=False)

    @property
    def images(self) -> list[str]:
        return json.loads(self.images_json or "[]")

    @images.setter
    def images(self, v: list[str]) -> None:
        self.images_json = json.dumps(v, ensure_ascii=False)


class KnowledgeEntry(Base):
    __tablename__ = "knowledge_entries"
    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(300))
    content: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    # --- RAG alanları (bkz. app/rag/) ---
    # always = her mesajda system prompt'ta; search = parçalanıp indekslenir, bot gerektiğinde arar.
    mode: Mapped[str] = mapped_column(String(10), default="search")
    # En son başarıyla indekslenen içeriğin özeti; değişmediyse yeniden indekslemeyiz.
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # indexed | pending | error | not_applicable
    index_status: Mapped[str] = mapped_column(String(20), default="pending")
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    index_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)


class Settings(Base):
    __tablename__ = "settings"
    id: Mapped[int] = mapped_column(primary_key=True)
    resort_name: Mapped[str] = mapped_column(String(200), default="")
    tagline: Mapped[str] = mapped_column(String(300), default="")
    phone: Mapped[str] = mapped_column(String(50), default="")
    email: Mapped[str] = mapped_column(String(200), default="")
    address: Mapped[str] = mapped_column(String(500), default="")
    check_in_time: Mapped[str] = mapped_column(String(20), default="14:00")
    check_out_time: Mapped[str] = mapped_column(String(20), default="11:00")
    map_embed_url: Mapped[str] = mapped_column(Text, default="")
    bot_name: Mapped[str] = mapped_column(String(100), default="Bunga")
    bot_welcome_message: Mapped[str] = mapped_column(Text, default="")
    bot_extra_instructions: Mapped[str] = mapped_column(Text, default="")

    # --- Sesli asistan (bkz. app/voice/, SESLI_ASISTAN.md) ---
    voice_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    voice_model: Mapped[str] = mapped_column(String(60), default="gpt-realtime")
    voice_name: Mapped[str] = mapped_column(String(40), default="marin")
    voice_vad_eagerness: Mapped[str] = mapped_column(String(10), default="medium")  # low | medium | high
    voice_speed: Mapped[float] = mapped_column(Float, default=1.0)
    voice_max_session_seconds: Mapped[int] = mapped_column(Integer, default=300)
    voice_greeting: Mapped[str] = mapped_column(Text, default="")
    voice_lexicon_json: Mapped[str] = mapped_column(Text, default="{}")  # {"Infinity": "infiniti", ...}


class Reservation(Base):
    __tablename__ = "reservations"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    bungalow_id: Mapped[int] = mapped_column(ForeignKey("bungalows.id"))
    guest_name: Mapped[str] = mapped_column(String(200))
    guest_email: Mapped[str] = mapped_column(String(200))
    guest_phone: Mapped[str] = mapped_column(String(50))
    check_in: Mapped[str] = mapped_column(String(10))
    check_out: Mapped[str] = mapped_column(String(10))
    guests: Mapped[int] = mapped_column(Integer)
    nights: Mapped[int] = mapped_column(Integer)
    total_price: Mapped[float] = mapped_column(Float)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending_payment")
    source: Mapped[str] = mapped_column(String(20), default="web")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    bungalow: Mapped[Bungalow] = relationship(lazy="joined")

    @property
    def bungalow_name(self) -> str:
        return self.bungalow.name


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    reservation_id: Mapped[int] = mapped_column(ForeignKey("reservations.id"))
    amount: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="initialized")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    reservation: Mapped[Reservation] = relationship(lazy="joined")

    @property
    def reservation_code(self) -> str:
        return self.reservation.code


class VoiceSession(Base):
    """Sesli görüşme kaydı: konuşma dökümü + araç çağrıları (yönetici panelinde incelenir)."""

    __tablename__ = "voice_sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)  # /api/voice/session'ın verdiği
    call_id: Mapped[str | None] = mapped_column(String(100), nullable=True)       # OpenAI WebRTC çağrı kimliği
    model: Mapped[str] = mapped_column(String(60), default="")
    voice: Mapped[str] = mapped_column(String(40), default="")
    status: Mapped[str] = mapped_column(String(20), default="created")  # created | active | ended | error
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    transcript_json: Mapped[str] = mapped_column(Text, default="[]")  # [{role, text, ts, ...}]
    reservation_codes_json: Mapped[str] = mapped_column(Text, default="[]")

    @property
    def transcript(self) -> list[dict]:
        return json.loads(self.transcript_json or "[]")

    @property
    def reservation_codes(self) -> list[str]:
        return json.loads(self.reservation_codes_json or "[]")

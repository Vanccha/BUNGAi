from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

ReservationStatus = Literal["pending_payment", "confirmed", "cancelled", "payment_failed"]


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BungalowOut(ORM):
    id: int
    slug: str
    name: str
    short_description: str
    description: str
    capacity: int
    bedrooms: int
    size_m2: int
    price_per_night: float
    amenities: list[str]
    images: list[str]
    is_active: bool


class BungalowIn(BaseModel):
    slug: str | None = None
    name: str
    short_description: str = ""
    description: str = ""
    capacity: int = Field(ge=1)
    bedrooms: int = 1
    size_m2: int = 30
    price_per_night: float = Field(ge=0)
    amenities: list[str] = []
    images: list[str] = []
    is_active: bool = True


class KnowledgeOut(ORM):
    id: int
    category: str
    title: str
    content: str
    is_active: bool
    sort_order: int
    updated_at: datetime
    mode: Literal["always", "search"]
    index_status: Literal["indexed", "pending", "error", "not_applicable"]
    chunk_count: int


class KnowledgeIn(BaseModel):
    category: str
    title: str
    content: str
    is_active: bool = True
    sort_order: int = 0
    mode: Literal["always", "search"] = "search"


class SettingsPublic(ORM):
    resort_name: str
    tagline: str
    phone: str
    email: str
    address: str
    check_in_time: str
    check_out_time: str
    map_embed_url: str
    bot_name: str
    bot_welcome_message: str
    voice_enabled: bool = True
    voice_greeting: str = ""
    voice_max_session_seconds: int = 300


class SettingsFull(SettingsPublic):
    bot_extra_instructions: str
    voice_model: str = "gpt-realtime"
    voice_name: str = "marin"
    voice_vad_eagerness: Literal["low", "medium", "high"] = "medium"
    voice_speed: float = Field(default=1.0, ge=0.25, le=1.5)
    voice_lexicon_json: str = "{}"

    @field_validator("voice_max_session_seconds")
    @classmethod
    def _max_seconds(cls, v: int) -> int:
        return max(30, min(v, 1800))

    @field_validator("voice_lexicon_json")
    @classmethod
    def _lexicon(cls, v: str) -> str:
        import json
        try:
            d = json.loads(v or "{}")
        except ValueError as e:
            raise ValueError("Telaffuz sözlüğü geçerli bir JSON olmalı") from e
        if not isinstance(d, dict) or not all(isinstance(k, str) and isinstance(x, str) for k, x in d.items()):
            raise ValueError("Telaffuz sözlüğü {\"kelime\": \"okunuş\"} biçiminde olmalı")
        return v or "{}"


class AvailabilityOut(BaseModel):
    available: bool
    nights: int
    total_price: float


class CalendarOut(BaseModel):
    booked_dates: list[str]


class ReservationIn(BaseModel):
    bungalow_id: int
    guest_name: str = Field(min_length=2)
    guest_email: EmailStr
    guest_phone: str = Field(min_length=7)
    check_in: str
    check_out: str
    guests: int = Field(ge=1)
    note: str | None = None


class ReservationOut(ORM):
    id: int
    code: str
    bungalow_id: int
    bungalow_name: str
    guest_name: str
    guest_email: str
    guest_phone: str
    check_in: str
    check_out: str
    guests: int
    nights: int
    total_price: float
    note: str | None
    status: ReservationStatus
    source: Literal["web", "chatbot", "voice"]
    created_at: datetime


class StatusPatch(BaseModel):
    status: ReservationStatus


class PaymentInitIn(BaseModel):
    reservation_code: str


class PaymentInitOut(BaseModel):
    token: str
    amount: float
    payment_page_url: str


class PaymentOut(BaseModel):
    token: str
    amount: float
    status: Literal["initialized", "success", "failure"]
    reservation: ReservationOut


class CardIn(BaseModel):
    card_holder: str
    card_number: str
    expire_month: str
    expire_year: str
    cvc: str


class PaymentResult(BaseModel):
    status: Literal["success", "failure"]
    message: str
    reservation: ReservationOut


class ChatIn(BaseModel):
    session_id: str | None = None
    message: str = Field(min_length=1, max_length=4000)


class ChatOut(BaseModel):
    session_id: str
    reply: str
    actions: list[dict[str, Any]]


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class StatsOut(BaseModel):
    total_reservations: int
    confirmed: int
    pending: int
    revenue_confirmed: float
    upcoming_checkins: list[ReservationOut]


# ---- RAG (bkz. CONTRACT.md) ----
class RagStats(BaseModel):
    always_entries: int
    always_tokens: int
    always_token_limit: int
    search_entries: int
    chunks: int
    indexed_entries: int
    pending_entries: int
    error_entries: int
    embedding_model: str
    embeddings_enabled: bool
    last_indexed_at: str | None


class ReindexIn(BaseModel):
    force: bool = False


class RagSearchIn(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)


class SearchHitOut(BaseModel):
    entry_id: int
    entry_title: str
    category: str
    chunk_index: int
    text: str
    vector_score: float | None
    keyword_score: float | None
    vector_rank: int | None
    keyword_rank: int | None
    fused_score: float


class SearchTraceOut(BaseModel):
    query: str
    normalized_query: str
    results: list[SearchHitOut]
    below_threshold: bool


class ChatDebug(BaseModel):
    searches: list[SearchTraceOut]


class ChatTestOut(ChatOut):
    debug: ChatDebug


# ---- Sesli asistan (bkz. CONTRACT.md) ----
class VoiceSessionOut(BaseModel):
    client_secret: str
    expires_at: int
    model: str
    session_id: str
    max_seconds: int
    greeting: str


class VoiceAttachIn(BaseModel):
    call_id: str


class VoiceActionsOut(BaseModel):
    actions: list[dict[str, Any]]
    next: int
    ended: bool


class VoiceSessionListItem(ORM):
    id: int
    session_id: str
    model: str
    voice: str
    status: str
    started_at: datetime
    ended_at: datetime | None
    duration_seconds: int
    turn_count: int
    first_user_text: str
    reservation_codes: list[str]


class VoiceSessionDetail(VoiceSessionListItem):
    call_id: str | None
    transcript: list[dict[str, Any]]

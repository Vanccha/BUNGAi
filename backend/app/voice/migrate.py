"""Hafif şema geçişi: mevcut SQLite veritabanındaki `settings` tablosuna sesli asistan sütunlarını ekler.
(Projede Alembic yok; Base.metadata.create_all yalnızca YENİ tabloları oluşturur, var olan tabloya sütun eklemez.)"""
from sqlalchemy import Engine, text

DEFAULT_GREETING = (
    "Merhaba, BUNGAi'ye hoş geldiniz. Ben Bunga, sanal asistanınızım. "
    "Rezervasyon, müsaitlik ya da tesisimizle ilgili size nasıl yardımcı olabilirim?"
)

_COLUMNS = {
    "voice_enabled": "BOOLEAN NOT NULL DEFAULT 1",
    "voice_model": "VARCHAR(60) NOT NULL DEFAULT 'gpt-realtime'",
    "voice_name": "VARCHAR(40) NOT NULL DEFAULT 'marin'",
    "voice_vad_eagerness": "VARCHAR(10) NOT NULL DEFAULT 'medium'",
    "voice_speed": "FLOAT NOT NULL DEFAULT 1.0",
    "voice_max_session_seconds": "INTEGER NOT NULL DEFAULT 300",
    "voice_greeting": "TEXT NOT NULL DEFAULT ''",
    "voice_lexicon_json": "TEXT NOT NULL DEFAULT '{}'",
}


def ensure_voice_columns(engine: Engine) -> None:
    with engine.begin() as conn:
        have = {r[1] for r in conn.execute(text("PRAGMA table_info(settings)"))}
        for name, ddl in _COLUMNS.items():
            if name not in have:
                conn.execute(text(f"ALTER TABLE settings ADD COLUMN {name} {ddl}"))
        conn.execute(
            text("UPDATE settings SET voice_greeting = :g WHERE voice_greeting = ''"), {"g": DEFAULT_GREETING}
        )

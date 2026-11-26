"""ADIM 5 - Depolama: SQLite + numpy yeterli mi?  EVET (bu ölçekte).

NE SAKLIYORUZ?
    knowledge_chunks   : her parça için görünen metin, embedding'e giren metin, embedding BLOB'u,
                         embedding modeli, token sayısı, içerik özeti (hash), tarih.
    knowledge_fts      : FTS5 sanal tablosu. Normalize edilmiş metin üzerinde BM25 kelime araması yapar.
                         (rowid = knowledge_chunks.id; iki tablo aynı id ile eşleşir.)

NEDEN AYRI BİR VEKTÖR VERİTABANI YOK?
    Bu tesiste birkaç yüz parça var (< 10.000). 1536 boyutlu float32 vektörler: 1.000 parça ~ 6 MB.
    Tüm vektörleri RAM'e alıp numpy ile tek matris çarpımı yapmak milisaniyeler sürer.
    Yani "brute-force" (kaba kuvvet) arama bu ölçekte hem basit hem hızlı.
    NE ZAMAN DEĞİŞTİRİLİR?
      * ~50-100 bin parçayı geçince ya da birden çok işlemde paylaşılan indeks gerekince:
        önce `sqlite-vec` eklentisi (aynı SQLite dosyasında vektör indeksi), sonra pgvector / Qdrant /
        Weaviate gibi gerçek bir vektör veritabanı.
      * Metadata filtresi + hibrit + ölçek birlikte gerekince yönetilen servisler (Pinecone vb.).

NOT: FTS5 SQLite'a gömülüdür (ek kurulum yok). bm25() fonksiyonu "ne kadar küçükse o kadar iyi"
(negatif) değer döndürür; biz işareti çevirip "büyük = iyi" yapıyoruz.
"""
from dataclasses import dataclass

import numpy as np
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from .embeddings import from_blob

_SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS knowledge_chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entry_id INTEGER NOT NULL REFERENCES knowledge_entries(id) ON DELETE CASCADE,
        chunk_index INTEGER NOT NULL,
        text TEXT NOT NULL,              -- bota gösterilen metin (başlık + gövde)
        embed_text TEXT NOT NULL,        -- embedding'e giren metin (bağlam cümlesi + text)
        embedding BLOB,                  -- float32 vektör; API anahtarı yoksa NULL
        embedding_model TEXT,
        token_count INTEGER NOT NULL,
        content_hash TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_chunks_entry ON knowledge_chunks(entry_id)",
    # İki sütun: header (Kategori > Başlık) ve body. bm25 ağırlığı ile başlık eşleşmeleri öne çıkar.
    "CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(header, body, tokenize='unicode61')",
]


def init_schema(engine: Engine) -> None:
    """Uygulama açılışında bir kez çağrılır (CREATE ... IF NOT EXISTS: tekrar çağırmak zararsız)."""
    with engine.begin() as conn:
        for stmt in _SCHEMA:
            conn.execute(text(stmt))


# ---------------------------------------------------------------------------------------------
# Yazma
# ---------------------------------------------------------------------------------------------
@dataclass
class ChunkRecord:
    chunk_index: int
    text: str
    embed_text: str
    token_count: int
    content_hash: str
    fts_header: str          # normalize edilmiş başlık
    fts_body: str            # normalize edilmiş gövde (bağlam cümlesi dahil)
    embedding: bytes | None = None
    embedding_model: str | None = None


def delete_entry_chunks(db: Session, entry_id: int) -> None:
    db.execute(text("DELETE FROM knowledge_fts WHERE rowid IN (SELECT id FROM knowledge_chunks WHERE entry_id = :e)"), {"e": entry_id})
    db.execute(text("DELETE FROM knowledge_chunks WHERE entry_id = :e"), {"e": entry_id})


def insert_chunks(db: Session, entry_id: int, records: list[ChunkRecord]) -> None:
    for r in records:
        result = db.execute(
            text(
                "INSERT INTO knowledge_chunks (entry_id, chunk_index, text, embed_text, embedding, embedding_model, token_count, content_hash) "
                "VALUES (:entry_id, :idx, :text, :embed_text, :emb, :model, :tokens, :hash)"
            ),
            {"entry_id": entry_id, "idx": r.chunk_index, "text": r.text, "embed_text": r.embed_text, "emb": r.embedding,
             "model": r.embedding_model, "tokens": r.token_count, "hash": r.content_hash},
        )
        chunk_id = result.lastrowid
        db.execute(text("INSERT INTO knowledge_fts(rowid, header, body) VALUES (:id, :h, :b)"), {"id": chunk_id, "h": r.fts_header, "b": r.fts_body})


# ---------------------------------------------------------------------------------------------
# Okuma
# ---------------------------------------------------------------------------------------------
def count_chunks(db: Session) -> int:
    return db.execute(text("SELECT COUNT(*) FROM knowledge_chunks")).scalar() or 0


def count_entry_chunks(db: Session, entry_id: int) -> int:
    return db.execute(text("SELECT COUNT(*) FROM knowledge_chunks WHERE entry_id = :e"), {"e": entry_id}).scalar() or 0


def entry_chunks_fully_embedded(db: Session, entry_id: int, model: str) -> bool:
    """Kaydın tüm parçalarında bu modelle üretilmiş embedding var mı?"""
    row = db.execute(
        text("SELECT COUNT(*), SUM(CASE WHEN embedding IS NOT NULL AND embedding_model = :m THEN 1 ELSE 0 END) FROM knowledge_chunks WHERE entry_id = :e"),
        {"e": entry_id, "m": model},
    ).one()
    return row[0] > 0 and row[0] == (row[1] or 0)


@dataclass
class VectorIndex:
    """RAM'deki vektör matrisi + her satırın meta verisi."""
    chunk_ids: np.ndarray      # (n,)   int64
    entry_ids: np.ndarray      # (n,)   int64
    categories: np.ndarray     # (n,)   str
    matrix: np.ndarray         # (n, d) float32, satırlar normalize


def load_vector_index(db: Session) -> VectorIndex:
    """Aktif 'search' kayıtlarının embedding'li parçalarını tek bir matrise yükler."""
    rows = db.execute(
        text(
            "SELECT c.id, c.entry_id, e.category, c.embedding FROM knowledge_chunks c "
            "JOIN knowledge_entries e ON e.id = c.entry_id "
            "WHERE e.is_active = 1 AND e.mode = 'search' AND c.embedding IS NOT NULL ORDER BY c.id"
        )
    ).all()
    if not rows:
        return VectorIndex(np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64), np.zeros(0, dtype=object), np.zeros((0, 1), dtype=np.float32))
    return VectorIndex(
        chunk_ids=np.array([r[0] for r in rows], dtype=np.int64),
        entry_ids=np.array([r[1] for r in rows], dtype=np.int64),
        categories=np.array([r[2] for r in rows], dtype=object),
        matrix=np.vstack([from_blob(r[3]) for r in rows]),
    )


def keyword_search(db: Session, match_query: str, limit: int, category: str | None = None) -> list[tuple[int, float]]:
    """FTS5 BM25 araması. [(chunk_id, skor)] döner; skor büyük = daha iyi.

    bm25(knowledge_fts, 3.0, 1.0): header sütunundaki eşleşmeler body'dekinden 3 kat önemli sayılır
    (başlıkta geçen kelime, parçanın konusunu belirler).
    """
    if not match_query:
        return []
    sql = (
        "SELECT c.id, bm25(knowledge_fts, 3.0, 1.0) AS score FROM knowledge_fts "
        "JOIN knowledge_chunks c ON c.id = knowledge_fts.rowid "
        "JOIN knowledge_entries e ON e.id = c.entry_id "
        "WHERE knowledge_fts MATCH :q AND e.is_active = 1 AND e.mode = 'search' "
        + ("AND e.category = :cat " if category else "")
        + "ORDER BY score LIMIT :n"
    )
    params: dict = {"q": match_query, "n": limit}
    if category:
        params["cat"] = category
    rows = db.execute(text(sql), params).all()
    return [(int(r[0]), -float(r[1])) for r in rows]  # bm25 negatif döner; işareti çevir


def get_chunks(db: Session, chunk_ids: list[int]) -> dict[int, dict]:
    """chunk_id -> {entry_id, entry_title, category, chunk_index, text}"""
    if not chunk_ids:
        return {}
    placeholders = ",".join(str(int(i)) for i in chunk_ids)  # int() ile zorlandı: enjeksiyon riski yok
    rows = db.execute(
        text(
            "SELECT c.id, c.entry_id, e.title, e.category, c.chunk_index, c.text FROM knowledge_chunks c "
            f"JOIN knowledge_entries e ON e.id = c.entry_id WHERE c.id IN ({placeholders})"
        )
    ).all()
    return {r[0]: {"entry_id": r[1], "entry_title": r[2], "category": r[3], "chunk_index": r[4], "text": r[5]} for r in rows}


def list_categories(db: Session) -> list[str]:
    """Aktif 'search' kayıtlarındaki kategori adları (kategori filtresini doğrulamak için)."""
    rows = db.execute(text("SELECT DISTINCT category FROM knowledge_entries WHERE is_active = 1 AND mode = 'search' ORDER BY category")).all()
    return [r[0] for r in rows]

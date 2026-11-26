"""ADIM 6 - İndeksleme boru hattı (kayıt kaydedilince çalışan taraf) + ARTIMLI (incremental) indeksleme.

BORU HATTI (bir kayıt için)
    KnowledgeEntry
        └─ chunk_entry()          chunking.py     parçalara böl + bağlam başlığı ekle
        └─ generate_contexts()    contextual.py   (yalnızca uzun kayıt) parça başına bağlam cümlesi
        └─ embed_texts()          embeddings.py   embed_text -> vektör
        └─ normalize_for_search() normalize.py    kelime indeksi için normalize metin
        └─ insert_chunks()        store.py        knowledge_chunks + knowledge_fts

NEDEN "ARTIMLI"? (hash ile değişiklik tespiti)
    Embedding ve bağlam üretimi PARA ve ZAMAN harcar. Admin 130 kaydın birini düzenlediğinde 129'unu yeniden
    indekslemek israftır. Bu yüzden her kayıt için bir İÇERİK ÖZETİ (sha256) hesaplarız:
        hash = sha256(sürüm | kategori | başlık | içerik | mod)
    Son başarılı indekslemedeki hash, KnowledgeEntry.content_hash'te saklanır. Yeni hash aynıysa hiçbir şey
    yapmayız. Farklıysa eski parçaları silip yeniden kurarız. Sıralama/aktiflik gibi arama içeriğini
    etkilemeyen alanlar hash'e girmez. 'sürüm' alanı, parçalama ayarını değiştirdiğinizde herkesi yeniden
    indekslemek içindir.

DURUM MAKİNESİ (KnowledgeEntry.index_status)
    pending  ──indeksleme başarılı──►  indexed
       │
       └──hata (örn. embedding API)────►  error   (kelime araması yine çalışır; tekrar denenebilir)
    not_applicable : mode="always" kayıtlar (prompt'ta durur, indekslenmez)

KURALLAR
    * Admin create/update -> mark_pending_if_changed() (hızlı, senkron) + arka planda index_entry().
    * Admin delete        -> remove_entry().
    * Pasif yapma         -> parçalar SİLİNMEZ; arama sorgusu is_active ile süzer (tekrar aktif edince bedava).
    * mode "always"a geçiş-> parçalar silinir (artık prompt'ta).
    * Açılışta            -> start_background_reindex(): eksik/değişmiş kayıtlar, sunucuyu bloklamadan.
    * API anahtarı yok    -> parçalar + FTS yine kurulur (embedding NULL); yalnızca kelime araması çalışır.
"""
import hashlib
import logging
import threading
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import KnowledgeEntry
from . import chunking, store
from .contextual import generate_contexts
from .embeddings import EMBEDDING_MODEL, embed_texts, embeddings_enabled, to_blob
from .normalize import normalize_for_search
from .search import invalidate_cache

log = logging.getLogger("bungai.rag.indexer")

# Parçalama/bağlam mantığını değiştirdiğinizde bu sürümü artırın: tüm kayıtlar bir sonraki
# reindex_all'da yeniden indekslenir.
PIPELINE_VERSION = f"v1|{chunking.CHUNK_MAX_TOKENS}|{chunking.MIN_CHUNK_TOKENS}|{chunking.OVERLAP_RATIO}"

# Aynı anda tek indeksleme (SQLite yazımı + API çağrıları sırayla yapılsın).
_index_lock = threading.RLock()


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def compute_hash(entry: KnowledgeEntry) -> str:
    """Arama içeriğini etkileyen alanların özeti."""
    payload = "\x1f".join([PIPELINE_VERSION, entry.category, entry.title, entry.content, entry.mode])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------------------------
# Admin tarafından çağrılan hızlı (senkron) yardımcılar
# ---------------------------------------------------------------------------------------------
def mark_pending_if_changed(db: Session, entry: KnowledgeEntry) -> bool:
    """create/update sonrası çağrılır. Arka plan indekslemesi gerekiyorsa True döner.

    * mode=always : parçaları hemen sil, durum not_applicable.
    * mode=search : hash değiştiyse (ya da hiç indekslenmediyse) durum pending.
    Çağıran db.commit() yapar.
    """
    if entry.mode == "always":
        store.delete_entry_chunks(db, entry.id)
        entry.content_hash = None
        entry.index_status, entry.chunk_count, entry.index_error, entry.indexed_at = "not_applicable", 0, None, None
        invalidate_cache()
        return False
    if entry.content_hash != compute_hash(entry) or entry.index_status != "indexed":
        entry.index_status = "pending"
        return True
    return False


def remove_entry(db: Session, entry_id: int) -> None:
    """Kayıt silinirken parçalarını da sil (SQLite'ta FK cascade varsayılan kapalı olduğu için elle)."""
    store.delete_entry_chunks(db, entry_id)
    invalidate_cache()


# ---------------------------------------------------------------------------------------------
# Çekirdek: tek kaydı indeksle
# ---------------------------------------------------------------------------------------------
def build_records(entry: KnowledgeEntry, content_hash: str) -> tuple[list[store.ChunkRecord], str | None]:
    """Kaydı parçalara bölüp ChunkRecord listesi üretir. (kayıtlar, embedding_hatası | None)."""
    chunks = chunking.chunk_entry(entry.category, entry.title, entry.content)
    contexts = generate_contexts(entry.category, entry.title, entry.content, chunks)

    records: list[store.ChunkRecord] = []
    for chunk, ctx in zip(chunks, contexts):
        # embed_text = bağlam cümlesi + görünen metin. Bota yalnızca chunk.text gider.
        embed_text = f"{ctx}\n{chunk.text}" if ctx else chunk.text
        records.append(
            store.ChunkRecord(
                chunk_index=chunk.index, text=chunk.text, embed_text=embed_text,
                token_count=chunk.token_count, content_hash=content_hash,
                fts_header=normalize_for_search(chunk.header),
                fts_body=normalize_for_search(f"{ctx} {chunk.body}"),
            )
        )

    embed_error: str | None = None
    if embeddings_enabled():
        try:
            vectors = embed_texts([r.embed_text for r in records])
            for record, vec in zip(records, vectors):
                record.embedding, record.embedding_model = to_blob(vec), EMBEDDING_MODEL
        except Exception as exc:  # noqa: BLE001
            embed_error = f"Embedding hatası: {exc}"[:500]
            log.error("Embedding başarısız (kayıt %s): %s", entry.id, exc)
    return records, embed_error


def index_entry(entry_id: int, force: bool = False) -> str:
    """Tek kaydı indeksler (kendi DB oturumunu açar; arka plan görevinden çağrılabilir).

    Dönüş: 'skipped' (değişmemiş) | 'indexed' | 'error' | 'removed' | 'not_applicable'
    """
    with _index_lock, SessionLocal() as db:
        entry = db.get(KnowledgeEntry, entry_id)
        if entry is None:                                   # kayıt silinmiş
            store.delete_entry_chunks(db, entry_id)
            db.commit(); invalidate_cache()
            return "removed"

        if entry.mode == "always":                          # prompt'ta durur; indekslenmez
            store.delete_entry_chunks(db, entry_id)
            entry.content_hash, entry.chunk_count = None, 0
            entry.index_status, entry.index_error, entry.indexed_at = "not_applicable", None, None
            db.commit(); invalidate_cache()
            return "not_applicable"

        new_hash = compute_hash(entry)
        unchanged = entry.content_hash == new_hash and entry.index_status == "indexed" and store.count_entry_chunks(db, entry_id) > 0
        # API anahtarı sonradan eklendiyse (parçalarda embedding yok) yine de yeniden kur.
        if unchanged and embeddings_enabled() and not store.entry_chunks_fully_embedded(db, entry_id, EMBEDDING_MODEL):
            unchanged = False
        if unchanged and not force:
            return "skipped"

        try:
            records, embed_error = build_records(entry, new_hash)
        except Exception as exc:  # noqa: BLE001 - parçalama hatası: eski parçalar korunur
            log.exception("İndeksleme başarısız (kayıt %s)", entry_id)
            entry.index_status, entry.index_error = "error", f"İndeksleme hatası: {exc}"[:500]
            db.commit()
            return "error"

        # Eski parçaları sil + yenileri yaz: TEK işlemde (arada arama yarım indeks görmez)
        store.delete_entry_chunks(db, entry_id)
        store.insert_chunks(db, entry_id, records)
        entry.chunk_count = len(records)
        entry.indexed_at = _now()
        if embed_error:
            # Parçalar + FTS yazıldı (kelime araması çalışır) ama vektör yok: hash'i KAYDETME ki tekrar denensin.
            entry.index_status, entry.index_error, entry.content_hash = "error", embed_error, None
        else:
            entry.index_status, entry.index_error, entry.content_hash = "indexed", None, new_hash
        db.commit()
        invalidate_cache()
        return entry.index_status


def reindex_all(force: bool = False) -> dict[str, int]:
    """Tüm 'search' kayıtlarını indeksler (force=False: yalnızca değişen/eksik olanlar)."""
    result: dict[str, int] = {}
    with SessionLocal() as db:
        ids = list(db.scalars(select(KnowledgeEntry.id).order_by(KnowledgeEntry.id)))
    for entry_id in ids:
        outcome = index_entry(entry_id, force=force)
        result[outcome] = result.get(outcome, 0) + 1
    log.info("reindex_all(force=%s) tamamlandı: %s", force, result)
    return result


def start_background_reindex(force: bool = False) -> threading.Thread:
    """Sunucuyu bloklamadan arka plan thread'inde reindex_all çalıştırır (açılışta ve admin 'reindex' ile)."""
    thread = threading.Thread(target=reindex_all, kwargs={"force": force}, name="rag-reindex", daemon=True)
    thread.start()
    return thread

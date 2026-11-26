"""BUNGAi RAG (Retrieval-Augmented Generation) paketi - öğretici sürüm.

OKUMA SIRASI (RAG_REHBERI.md ile aynı):
    1. normalize.py   Türkçe metin normalizasyonu (kelime araması için)
    2. chunking.py    uzun kaydı anlamlı parçalara bölme + bağlam başlığı
    3. contextual.py  (uzun kayıtlar) parçaya "dokümandaki yeri" cümlesi ekleme
    4. embeddings.py  metin -> vektör
    5. store.py       SQLite (parçalar + FTS5) ve RAM'de vektör matrisi
    6. indexer.py     kayıt kaydedilince tüm bunları çalıştıran artımlı indeksleyici
    7. search.py      soru gelince: vektör + BM25 + RRF + eşik

Dışarıya açılan sade API:
"""
from .embeddings import EMBEDDING_MODEL, embeddings_enabled
from .indexer import (
    index_entry,
    mark_pending_if_changed,
    reindex_all,
    remove_entry,
    start_background_reindex,
)
from .normalize import normalize_for_search
from .search import SearchHit, SearchTrace, invalidate_cache, search
from .store import count_chunks, init_schema

__all__ = [
    "EMBEDDING_MODEL", "SearchHit", "SearchTrace", "count_chunks", "embeddings_enabled", "index_entry",
    "init_schema", "invalidate_cache", "mark_pending_if_changed", "normalize_for_search", "reindex_all",
    "remove_entry", "search", "start_background_reindex",
]

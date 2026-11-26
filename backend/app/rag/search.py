"""ADIM 7 - Hibrit arama (soru geldiğinde çalışan boru hattı).

AKIŞ
    sorgu ──┬─► (a) VEKTÖR ARAMASI : sorguyu embed et, RAM'deki matrisle kosinüs benzerliği -> sıralı liste
            │
            └─► (b) KELİME ARAMASI : sorguyu normalize et (normalize.py), FTS5 BM25 -> sıralı liste
                         │
                  (c) RRF ile BİRLEŞTİR  ->  (d) komşu parçaları birleştir  ->  (e) GÜVEN EŞİĞİ  ->  SearchTrace

NEDEN İKİSİ BİRDEN (HİBRİT)?
    * Vektör araması ANLAMI yakalar: "köpüşümü getirebilir miyim" -> "Evcil hayvan politikası". Ama tam
      kelime/sayı/ad eşleşmelerinde bazen yetersizdir ("Troy kart", "Mavi Ufuk").
    * Kelime araması (BM25) tam kelimeyi çok iyi yakalar ama eş anlamlıyı/yazım hatasını bilmez.
    İkisi birbirinin açığını kapatır.

(c) RECIPROCAL RANK FUSION (RRF) - İKİ SIRALAMAYI NASIL BİRLEŞTİRİRİZ?
    Vektör skoru (0.45 gibi kosinüs) ile BM25 skoru (12.3 gibi) FARKLI ölçeklerdedir; toplanamaz.
    RRF skorları değil SIRALARI kullanır:   fused(d) = Σ  1 / (k + sıra_i(d))     (k = 60)
    Bir doküman bir listede yoksa o listeden katkı almaz.

    SAYISAL ÖRNEK (k = 60):
        Parça A: vektörde 1., kelimede 3.   ->  1/61 + 1/63 = 0.01639 + 0.01587 = 0.03226
        Parça C: vektörde yok, kelimede 1.  ->  1/61                              = 0.01639
        Parça B: vektörde 2., kelimede yok  ->  1/62                              = 0.01613
        Sonuç sırası: A > C > B.  İki listede de görünen A açık farkla öne geçti: "iki bağımsız yöntem
        de bunu ilgili buldu" demek güçlü bir işarettir. k=60, bir listedeki 1. ile 5. sıra arasındaki
        farkı yumuşatır (büyük k = daha yumuşak, küçük k = en üsttekilere daha çok ağırlık).

(d) KOMŞU PARÇALARI BİRLEŞTİR
    Aynı kaydın ardışık iki parçası (örn. 2 ve 3) sonuçlarda varsa tek bir parça olarak birleştirilir
    (örtüşen satırlar tekrar edilmez). Bota aynı bilgi iki kez gitmez, bağlam bütün kalır.

(e) GÜVEN EŞİĞİ - "bilmiyorum" diyebilmek
    Arama HER ZAMAN bir şey döndürür (en yakın çöp bile). Bot bunu "doğru bilgi" sanıp uydurmasın diye
    her sonucu iki eşikle süzeriz:
        vektör kosinüsü >= VECTOR_MIN_COSINE   VEYA   BM25 skoru >= KEYWORD_MIN_SCORE
    Hiçbir sonuç geçemezse below_threshold=True: bot "bilmiyorum, telefonla arayın" demelidir.
    Eşikler eval/rag_eval.py ile ölçülerek ayarlandı (bkz. RAG_REHBERI.md).
"""
import logging
import threading
from dataclasses import dataclass, field

import numpy as np
from sqlalchemy.orm import Session

from . import store
from .embeddings import embed_query, embeddings_enabled
from .normalize import normalize_tokens

log = logging.getLogger("bungai.rag.search")

# --- Ayarlar ---
RRF_K = 60                   # RRF sabiti
CANDIDATES_PER_RETRIEVER = 20  # her yöntemden RRF'e girecek en iyi N parça
VECTOR_MIN_COSINE = 0.38     # eval ile ayarlandı (cevaplı sorularda yanlış red = 0; bkz. eval/rag_eval.py)
KEYWORD_MIN_SCORE = 10.0     # eval ile ayarlandı (bm25, başlık ağırlığı dahil)
PREFIX_MIN_LEN = 4           # bu uzunluktaki kökler FTS'te önek (kök*) olarak da aranır


@dataclass
class SearchHit:
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


@dataclass
class SearchTrace:
    query: str
    normalized_query: str
    results: list[SearchHit] = field(default_factory=list)
    below_threshold: bool = False


# ---------------------------------------------------------------------------------------------
# Vektör matrisi önbelleği
# ---------------------------------------------------------------------------------------------
# Matrisi her aramada diskten okumak yerine RAM'de tutarız. İndeks her değiştiğinde (indexer.py)
# invalidate_cache() çağrılır; bir sonraki arama matrisi yeniden yükler.
_cache_lock = threading.Lock()
_cache: store.VectorIndex | None = None


def invalidate_cache() -> None:
    global _cache
    with _cache_lock:
        _cache = None


def _get_vector_index(db: Session) -> store.VectorIndex:
    global _cache
    with _cache_lock:
        if _cache is None:
            _cache = store.load_vector_index(db)
        return _cache


# ---------------------------------------------------------------------------------------------
# (a) Vektör araması
# ---------------------------------------------------------------------------------------------
def _vector_candidates(db: Session, query: str, category: str | None) -> tuple[list[tuple[int, float]], dict[int, float]]:
    """([(chunk_id, cosine)] en iyiler sıralı, {chunk_id: cosine} tüm parçalar)."""
    if not embeddings_enabled():
        return [], {}
    index = _get_vector_index(db)
    if len(index.chunk_ids) == 0:
        return [], {}
    query_vec = embed_query(query)
    scores = index.matrix @ query_vec              # (n,) kosinüs benzerliği: normalize vektörlerde nokta çarpımı
    if category:
        scores = np.where(index.categories == category, scores, -1.0)   # kategori dışını ele
    order = np.argsort(-scores)[:CANDIDATES_PER_RETRIEVER]
    ranked = [(int(index.chunk_ids[i]), float(scores[i])) for i in order if scores[i] > -1.0]
    all_scores = {int(cid): float(s) for cid, s in zip(index.chunk_ids, scores) if s > -1.0}
    return ranked, all_scores


# ---------------------------------------------------------------------------------------------
# (b) Kelime araması
# ---------------------------------------------------------------------------------------------
def build_fts_query(tokens: list[str]) -> str:
    """Kök listesinden FTS5 sorgusu: "havuz" OR "havuz"* OR "kural" ...  (VEYA: herhangi biri eşleşsin).

    Her token tırnak içine alınır (özel karakter/FTS operatörü sızmasın). Uzun kökler ayrıca önek olarak
    aranır: stemmer'ın kaçırdığı ekleri ("kahvalt" -> "kahvaltilar") yakalamak için.
    """
    parts: list[str] = []
    for tok in dict.fromkeys(tokens):  # tekrarları at, sırayı koru
        parts.append(f'"{tok}"')
        if len(tok) >= PREFIX_MIN_LEN:
            parts.append(f'"{tok}"*')
    return " OR ".join(parts)


def _keyword_candidates(db: Session, tokens: list[str], category: str | None) -> list[tuple[int, float]]:
    return store.keyword_search(db, build_fts_query(tokens), CANDIDATES_PER_RETRIEVER, category)


# ---------------------------------------------------------------------------------------------
# (c) RRF
# ---------------------------------------------------------------------------------------------
def reciprocal_rank_fusion(*rankings: list[int]) -> dict[int, float]:
    """Her biri sıralı chunk_id listesi olan N sıralamayı tek skor sözlüğünde birleştirir."""
    fused: dict[int, float] = {}
    for ranking in rankings:
        for rank, chunk_id in enumerate(ranking, start=1):   # rank 1'den başlar
            fused[chunk_id] = fused.get(chunk_id, 0.0) + 1.0 / (RRF_K + rank)
    return fused


# ---------------------------------------------------------------------------------------------
# (d) Komşu parçaları birleştir
# ---------------------------------------------------------------------------------------------
def _split_header(text: str) -> tuple[str, list[str]]:
    header, _, body = text.partition("\n")
    return header, body.split("\n")


def _merge_texts(texts: list[str]) -> str:
    """Ardışık parçaların metinlerini birleştirir; örtüşen (tekrar eden) satırları bir kez yazar."""
    header, merged = _split_header(texts[0])
    for nxt in texts[1:]:
        _, lines = _split_header(nxt)
        overlap = 0
        for k in range(min(len(merged), len(lines)), 0, -1):   # en uzun örtüşen son/ön ek
            if merged[-k:] == lines[:k]:
                overlap = k
                break
        merged.extend(lines[overlap:])
    return header + "\n" + "\n".join(merged)


def _merge_adjacent(hits: list[SearchHit]) -> list[SearchHit]:
    """Aynı kaydın ardışık chunk_index'li hit'lerini tek hit yapar (skorlar: en iyisi)."""
    by_entry: dict[int, list[SearchHit]] = {}
    for h in hits:
        by_entry.setdefault(h.entry_id, []).append(h)
    merged: list[SearchHit] = []
    for group in by_entry.values():
        group.sort(key=lambda h: h.chunk_index)
        run = [group[0]]
        for h in group[1:]:
            if h.chunk_index == run[-1].chunk_index + 1:
                run.append(h)
            else:
                merged.append(_combine(run))
                run = [h]
        merged.append(_combine(run))
    merged.sort(key=lambda h: h.fused_score, reverse=True)
    return merged


def _combine(run: list[SearchHit]) -> SearchHit:
    if len(run) == 1:
        return run[0]
    def best(values, pick):
        vals = [v for v in values if v is not None]
        return pick(vals) if vals else None
    return SearchHit(
        entry_id=run[0].entry_id, entry_title=run[0].entry_title, category=run[0].category,
        chunk_index=run[0].chunk_index, text=_merge_texts([h.text for h in run]),
        vector_score=best([h.vector_score for h in run], max), keyword_score=best([h.keyword_score for h in run], max),
        vector_rank=best([h.vector_rank for h in run], min), keyword_rank=best([h.keyword_rank for h in run], min),
        fused_score=sum(h.fused_score for h in run),   # birleşen parçaların kanıtı toplanır
    )


# ---------------------------------------------------------------------------------------------
# Ana fonksiyon
# ---------------------------------------------------------------------------------------------
def passes_threshold(hit: SearchHit) -> bool:
    """(e) Güven eşiği: yeterince benzer VEYA yeterince güçlü kelime eşleşmesi."""
    vector_ok = hit.vector_score is not None and hit.vector_score >= VECTOR_MIN_COSINE
    keyword_ok = hit.keyword_score is not None and hit.keyword_score >= KEYWORD_MIN_SCORE
    return vector_ok or keyword_ok


def resolve_category(db: Session, category: str | None) -> str | None:
    """Botun verdiği kategori adını gerçek bir kategoriye eşler; eşleşmezse None (filtre uygulanmaz).

    Neden? Dil modeli "Ulaşım" ya da "Düğün" gibi yaklaşık bir ad verebilir. Katı filtre uygulasaydık
    sonuç boş dönerdi ve bot yanlışlıkla "bilmiyorum" derdi. Kategori filtresi yardımcıdır, engel değil.
    """
    if not category:
        return None
    wanted = set(normalize_tokens(category))
    for real in store.list_categories(db):
        real_tokens = set(normalize_tokens(real))
        if real == category or (wanted and (wanted <= real_tokens or real_tokens <= wanted)):
            return real
    return None


def search(db: Session, query: str, top_k: int = 5, category: str | None = None, method: str = "hybrid") -> SearchTrace:
    """Hibrit arama. method: 'hybrid' | 'vector' | 'keyword' (son ikisi yalnızca eval karşılaştırması içindir)."""
    category = resolve_category(db, category)
    tokens = normalize_tokens(query)
    trace = SearchTrace(query=query, normalized_query=" ".join(tokens))

    vec_ranked, vec_all = _vector_candidates(db, query, category) if method in ("hybrid", "vector") else ([], {})
    kw_ranked = _keyword_candidates(db, tokens, category) if method in ("hybrid", "keyword") else []

    vec_rank = {cid: r for r, (cid, _) in enumerate(vec_ranked, start=1)}
    kw_rank = {cid: r for r, (cid, _) in enumerate(kw_ranked, start=1)}
    kw_score = dict(kw_ranked)

    fused = reciprocal_rank_fusion([c for c, _ in vec_ranked], [c for c, _ in kw_ranked])
    top_ids = sorted(fused, key=fused.get, reverse=True)[: top_k * 2]    # birleştirme sonrası top_k kalsın diye pay bırak
    chunks = store.get_chunks(db, top_ids)

    hits = [
        SearchHit(
            entry_id=chunks[cid]["entry_id"], entry_title=chunks[cid]["entry_title"], category=chunks[cid]["category"],
            chunk_index=chunks[cid]["chunk_index"], text=chunks[cid]["text"],
            # Vektör skoru: parça kelime aramasından geldiyse bile kosinüsünü matristen biliyoruz.
            vector_score=vec_all.get(cid), keyword_score=kw_score.get(cid),
            vector_rank=vec_rank.get(cid), keyword_rank=kw_rank.get(cid), fused_score=fused[cid],
        )
        for cid in top_ids if cid in chunks
    ]
    hits = [h for h in hits if passes_threshold(h)]          # (e) eşik
    trace.results = _merge_adjacent(hits)[:top_k]            # (d) birleştir, top_k'ya kırp
    trace.below_threshold = len(trace.results) == 0
    return trace

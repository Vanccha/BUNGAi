"""ADIM 4 - Embedding (metni anlamsal vektöre çevirme).

EMBEDDING NEDİR?
    Bir embedding modeli metni sabit uzunlukta bir sayı listesine (vektör) çevirir; burada 1536 sayı.
    Anlamca benzer metinlerin vektörleri uzayda birbirine yakındır:
        "köpeğimi getirebilir miyim"  ~  "Evcil hayvan politikası"      (kelime ortak değil, anlam ortak!)
    Bu, kelime aramasının (BM25) yapamadığı şeydir. Karşılığında vektör araması nadir kelimelerde
    ("Troy kart", "BNG-123") zayıf kalabilir; ikisini birleştirmemizin nedeni budur (bkz. search.py).

NORMALİZE ETME
    Vektörleri birim uzunluğa (L2 norm = 1) getiriyoruz. O zaman iki vektörün KOSİNÜS benzerliği,
    basit bir nokta çarpımına (dot product) eşit olur: cos(a, b) = a · b. Hızlıdır: tüm parçalarla
    karşılaştırma tek bir matris-vektör çarpımıdır.

DEPOLAMA
    float32 numpy dizisini ham byte'a (BLOB) çevirip SQLite'a yazarız (store.py). Hangi modelle üretildiğini
    de saklarız: model değişirse eski vektörlerle yeni sorgu vektörü KARŞILAŞTIRILAMAZ (farklı uzaylar).
"""
import logging
import time

import numpy as np

from ..config import config

log = logging.getLogger("bungai.rag.embeddings")

EMBEDDING_MODEL = "text-embedding-3-small"
BATCH_SIZE = 96  # tek istekte gönderilecek metin sayısı (API sınırı 2048; küçük tutmak güvenli)

_client = None


def embeddings_enabled() -> bool:
    """API anahtarı varsa True. Yoksa sistem yalnızca kelime araması ile çalışır."""
    return bool(config.openai_api_key.strip())


def _get_client():
    global _client
    if _client is None:
        from openai import OpenAI

        _client = OpenAI(api_key=config.openai_api_key.strip())
    return _client


def _l2_normalize(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0  # sıfıra bölmeyi önle
    return matrix / norms


def embed_texts(texts: list[str]) -> np.ndarray:
    """Metin listesini (n, 1536) boyutunda, satırları normalize float32 matrise çevirir."""
    if not texts:
        return np.zeros((0, 1536), dtype=np.float32)
    client = _get_client()
    vectors: list[list[float]] = []
    for start in range(0, len(texts), BATCH_SIZE):
        batch = texts[start : start + BATCH_SIZE]
        for attempt in range(3):  # geçici ağ/hız sınırı hatalarında 3 deneme
            try:
                response = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
                vectors.extend(item.embedding for item in response.data)
                break
            except Exception as exc:  # noqa: BLE001
                if attempt == 2:
                    raise
                log.warning("Embedding isteği başarısız (%s); tekrar denenecek", exc)
                time.sleep(1.5 * (attempt + 1))
    return _l2_normalize(np.asarray(vectors, dtype=np.float32))


def embed_query(text: str) -> np.ndarray:
    """Tek bir sorgu için normalize edilmiş vektör (1536,)."""
    return embed_texts([text])[0]


def to_blob(vector: np.ndarray) -> bytes:
    return np.asarray(vector, dtype=np.float32).tobytes()


def from_blob(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)

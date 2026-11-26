"""ADIM 3 - Bağlamsal getirme (Contextual Retrieval) - yalnızca UZUN kayıtlar için.

SORUN
    Bir parçayı dokümandan kopardığınızda bağlamını kaybeder. Örnek parça:
        "- Fırın sütlaç - 190 TL (S)\\n- Kabak tatlısı - 210 TL (K,S)"
    Bu parça "restoran menüsünün tatlılar bölümü"ne ait olduğunu söylemiyor; "akşam yemeğinde tatlı
    fiyatları nedir?" sorusuyla eşleşmesi zorlaşır. Daha kötüsü: "Pazar günü 17:00" gibi bir parça
    hangi etkinliğin saati olduğunu belirtmeyebilir.

ÇÖZÜM (Anthropic'in "Contextual Retrieval" yöntemi)
    Her parça için, TÜM DOKÜMANI okuyan bir dil modelinden parçayı dokümanın içine yerleştiren TEK
    cümlelik kısa bir bağlam yazmasını isteriz:
        "Bu parça, Restoran ve Bar Menüsü dokümanının tatlı ve dondurma bölümüdür; fiyatlar TL'dir."
    Bu cümleyi parçanın BAŞINA ekleyip öyle embedding'e ve kelime indeksine veririz. Böylece parça
    kendi başına bile "ne olduğunu" bilir. Anthropic'in ölçümlerinde bu yöntem, kaçırılan getirmeleri
    belirgin oranda (yaklaşık üçte bir) azaltır.

NOTLAR
    * Bağlam cümlesi yalnızca "embed_text"e (indekslenen metne) eklenir; bota GÖSTERİLEN metne eklenmez.
      Bot zaten parçanın başlığını görür, bağlam cümlesi arama kalitesi içindir.
    * Kısa kayıtlarda gereksizdir (zaten bütün doküman tek parça) ve maliyet ekler; bu yüzden sadece
      > CONTEXTUAL_MIN_DOC_TOKENS token'lık dokümanlarda çalışır.
    * API anahtarı yoksa ya da çağrı hata verirse sessizce atlanır: bağlam "" olur, indeksleme devam eder.
    * Maliyet: parça başına 1 küçük model çağrısı (doküman ön eki OpenAI tarafından otomatik önbelleğe alınır).
"""
import logging
from concurrent.futures import ThreadPoolExecutor

from ..config import config
from .chunking import Chunk, count_tokens

log = logging.getLogger("bungai.rag.contextual")

CONTEXTUAL_MIN_DOC_TOKENS = 800     # bundan kısa dokümanlarda bağlam üretme
MAX_DOC_TOKENS_IN_PROMPT = 12000    # çok uzun dokümanı kırp (güvenlik sınırı)
PARALLEL_CALLS = 6                  # aynı anda kaç parça için model çağrılsın

_PROMPT = """<doküman>
{document}
</doküman>

Aşağıdaki parça yukarıdaki dokümandan alınmıştır:
<parça>
{chunk}
</parça>

Bu parçayı, arama sonuçlarında daha iyi bulunabilmesi için dokümanın bütünü içinde konumlandıran
TEK ve KISA bir Türkçe cümle yaz (en fazla 35 kelime). Dokümanın adını ve parçanın hangi bölümle
ilgili olduğunu belirt. Yalnızca o cümleyi yaz, başka hiçbir şey ekleme."""


def should_add_context(document: str) -> bool:
    """Doküman bağlamsal getirme için yeterince uzun mu ve API anahtarı var mı?"""
    return bool(config.openai_api_key.strip()) and count_tokens(document) > CONTEXTUAL_MIN_DOC_TOKENS


def _truncate(document: str) -> str:
    if count_tokens(document) <= MAX_DOC_TOKENS_IN_PROMPT:
        return document
    return document[: MAX_DOC_TOKENS_IN_PROMPT * 3]  # kaba kırpma (~3 karakter/token)


def _one_context(client, document: str, chunk: Chunk) -> str:
    try:
        response = client.chat.completions.create(
            model=config.openai_model,
            temperature=0,
            max_tokens=120,
            messages=[{"role": "user", "content": _PROMPT.format(document=document, chunk=chunk.body)}],
        )
        return (response.choices[0].message.content or "").strip().replace("\n", " ")
    except Exception as exc:  # noqa: BLE001 - bağlam isteğe bağlıdır; hata indekslemeyi durdurmasın
        log.warning("Bağlam cümlesi üretilemedi (parça %s): %s", chunk.index, exc)
        return ""


def generate_contexts(category: str, title: str, document: str, chunks: list[Chunk]) -> list[str]:
    """Her parça için bir bağlam cümlesi döndürür (aynı sırada). Üretilemezse ilgili öğe ''."""
    if not should_add_context(document) or len(chunks) <= 1:
        return [""] * len(chunks)
    from openai import OpenAI

    client = OpenAI(api_key=config.openai_api_key.strip())
    full_doc = _truncate(f"{category} > {title}\n\n{document}")
    with ThreadPoolExecutor(max_workers=PARALLEL_CALLS) as pool:
        return list(pool.map(lambda c: _one_context(client, full_doc, c), chunks))

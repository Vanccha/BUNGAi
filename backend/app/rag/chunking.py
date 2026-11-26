"""ADIM 2 - Yapıya duyarlı parçalama (chunking).

NEDEN VAR?
    Embedding modeli bir metni TEK bir vektöre sıkıştırır. 2000 kelimelik "Restoran Menüsü" tek vektöre
    sığdırılırsa her şeyin ortalaması olur: "midye fiyatı" sorusuna yakın çıkmaz. Üstelik bota 2000
    kelimenin hepsini göndermek de israftır. Çözüm: dokümanı ~300-500 token'lık anlamlı PARÇALARA
    (chunk) bölüp her parçayı ayrı indekslemek. Arama sonunda bota yalnızca ilgili parçalar gider.

KURALLARIMIZ
    1. Kısa kayıtlar (<= SINGLE_CHUNK_MAX_TOKENS) bölünmez; tek parça olur.
    2. Uzun kayıtlar önce BLOKLARA ayrılır: başlıklar ("## ..."), boş satırla ayrılmış paragraflar,
       liste blokları ("- ..." satırları). Bloklar mümkünse bölünmez (bir menü kategorisi tek parçada kalır).
    3. Bloklar ~CHUNK_MAX_TOKENS'a kadar paketlenir. Blok tek başına çok büyükse CÜMLE (liste ise SATIR)
       sınırlarından bölünür; hiçbir zaman cümlenin ortasından kesilmez.
    4. Ardışık parçalar arasında ~%15 ÖRTÜŞME (overlap) vardır: önceki parçanın son cümleleri sonrakinin
       başına kopyalanır. Böylece iki parçanın sınırına denk gelen bilgi (örn. cümle başı bir parçada,
       devamı diğerinde) kaybolmaz.
    5. Her parçaya BAĞLAM BAŞLIĞI eklenir:  "Kategori > Başlık > Alt başlık". Parça tek başına okunsa bile
       neyin parçası olduğu belli olur ("Fırın sütlaç - 190 TL" satırı artık "Restoran Menüsü > Tatlılar"
       başlığıyla indekslenir; bu hem vektör hem kelime aramasına yardım eder).

NASIL BAĞLANIYOR?
    indexer.py -> chunk_entry() -> (contextual.py) -> embeddings.py -> store.py
"""
import re
from dataclasses import dataclass

# --- Ayarlar (eval ile ayarlanır; bkz. RAG_REHBERI.md "Nasıl ayar yapılır") ---
CHUNK_MAX_TOKENS = 450          # bir parçanın hedef üst sınırı
OVERLAP_RATIO = 0.15            # parçalar arası örtüşme oranı (~60 token)
SINGLE_CHUNK_MAX_TOKENS = 500   # bundan kısa kayıtlar hiç bölünmez
MIN_CHUNK_TOKENS = 250          # başlık değişiminde parça bundan küçükse sonraki bölümle birleşir

# ---------------------------------------------------------------------------------------------
# Token sayımı
# ---------------------------------------------------------------------------------------------
try:
    import tiktoken

    _ENCODING = tiktoken.get_encoding("o200k_base")  # gpt-4o / gpt-4.1 ailesinin tokenizer'ı
except Exception:  # noqa: BLE001 - tiktoken yoksa / vocab indirilemezse kaba tahmine düş
    _ENCODING = None


def count_tokens(text: str) -> int:
    """Metindeki token sayısı. tiktoken yoksa 'karakter / 4' tahmini (Türkçe için biraz düşük kalır)."""
    if _ENCODING is None:
        return max(1, len(text) // 4)
    return len(_ENCODING.encode(text, disallowed_special=()))


# ---------------------------------------------------------------------------------------------
# Veri yapıları
# ---------------------------------------------------------------------------------------------
@dataclass
class Chunk:
    index: int          # kayıt içindeki sıra (0, 1, 2 ...)
    header: str         # "Kategori > Başlık > Alt başlık"
    body: str           # parçanın ham metni
    token_count: int

    @property
    def text(self) -> str:
        """Bota GÖSTERİLEN metin: başlık + gövde."""
        return f"{self.header}\n{self.body}"


@dataclass
class _Unit:
    """Bölünemeyen en küçük metin parçası: bir cümle ya da bir liste satırı."""
    text: str
    tokens: int


@dataclass
class _Block:
    """Anlamsal blok: paragraf ya da liste. Altındaki birimler (_Unit) cümle/satırdır."""
    heading: str | None
    units: list[_Unit]

    @property
    def tokens(self) -> int:
        return sum(u.tokens for u in self.units)


# ---------------------------------------------------------------------------------------------
# 1) Metni bloklara ayır
# ---------------------------------------------------------------------------------------------
_HEADING_RE = re.compile(r"^\s{0,3}#{1,4}\s+(.+?)\s*$")
_LIST_RE = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+")
# Cümle sonu: . ! ? işaretinden sonra boşluk ve büyük harf/rakam. Kısaltmalara ("Dr. Ali") takılabilir; kabul.
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-ZÇĞİÖŞÜ0-9(\"'])")


def _split_sentences(paragraph: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(paragraph) if s.strip()]


def parse_blocks(content: str) -> list[_Block]:
    """İçeriği başlık / paragraf / liste bloklarına çevirir. Başlıklar blok olmaz; sonraki blokların
    'heading' alanına yazılır."""
    blocks: list[_Block] = []
    heading: str | None = None
    para_lines: list[str] = []
    list_lines: list[str] = []

    def flush_paragraph() -> None:
        if para_lines:
            text = " ".join(para_lines)
            units = [_Unit(s, count_tokens(s)) for s in _split_sentences(text)]
            blocks.append(_Block(heading, units))
            para_lines.clear()

    def flush_list() -> None:
        if list_lines:
            blocks.append(_Block(heading, [_Unit(line, count_tokens(line)) for line in list_lines]))
            list_lines.clear()

    for raw in content.splitlines():
        line = raw.rstrip()
        m = _HEADING_RE.match(line)
        if m:
            flush_paragraph(); flush_list()
            heading = m.group(1)
        elif not line.strip():
            flush_paragraph(); flush_list()
        elif _LIST_RE.match(line):
            flush_paragraph()           # liste başlayınca önceki paragraf biter
            list_lines.append(line.strip())
        else:
            flush_list()                # liste satırı olmayan satır listeyi bitirir
            para_lines.append(line.strip())
    flush_paragraph(); flush_list()
    return blocks


# ---------------------------------------------------------------------------------------------
# 2) Blokları parçalara paketle
# ---------------------------------------------------------------------------------------------
def _make_header(category: str, title: str, headings: list[str]) -> str:
    parts = [category, title]
    if headings:
        parts.append(" / ".join(headings[:3]))  # parça birden çok bölüm kapsıyorsa en çok 3 alt başlık
    return " > ".join(parts)


def _overlap_tail(units: list[_Unit], budget: int) -> list[_Unit]:
    """Önceki parçanın sonundan, toplamı 'budget' token'ı aşmayan TAM birimleri (cümle/satır) alır."""
    tail: list[_Unit] = []
    total = 0
    for unit in reversed(units):
        if total + unit.tokens > budget:
            break
        tail.insert(0, unit)
        total += unit.tokens
    return tail


def chunk_entry(
    category: str,
    title: str,
    content: str,
    max_tokens: int = CHUNK_MAX_TOKENS,
    overlap_ratio: float = OVERLAP_RATIO,
) -> list[Chunk]:
    """Bir bilgi bankası kaydını parçalara böler. Ana giriş noktası."""
    content = content.strip()
    total_tokens = count_tokens(content)

    # Kural 1: kısa kayıt = tek parça
    if total_tokens <= SINGLE_CHUNK_MAX_TOKENS:
        return [Chunk(0, _make_header(category, title, []), content, total_tokens)]

    blocks = parse_blocks(content)
    overlap_budget = int(max_tokens * overlap_ratio)

    chunks: list[Chunk] = []
    cur_units: list[_Unit] = []      # şu an doldurulan parçadaki birimler
    cur_headings: list[str] = []     # bu parçanın kapsadığı alt başlıklar
    cur_tokens = 0
    fresh_overlap = 0                # parçanın başındaki "örtüşme" token'ı (gerçek içerik sayılmaz)

    def flush(carry_overlap: bool) -> None:
        """Mevcut parçayı kaydet; carry_overlap ise sonuna yakın birimleri yeni parçaya taşı."""
        nonlocal cur_units, cur_headings, cur_tokens, fresh_overlap
        if not cur_units:
            return
        body = "\n".join(u.text for u in cur_units)
        chunks.append(Chunk(len(chunks), _make_header(category, title, cur_headings), body, count_tokens(body)))
        tail = _overlap_tail(cur_units, overlap_budget) if carry_overlap else []
        cur_units = list(tail)
        cur_tokens = sum(u.tokens for u in tail)
        fresh_overlap = cur_tokens
        cur_headings = cur_headings[-1:] if tail else []

    def add_units(units: list[_Unit], heading: str | None) -> None:
        nonlocal cur_tokens
        if heading and heading not in cur_headings:
            cur_headings.append(heading)
        cur_units.extend(units)
        cur_tokens += sum(u.tokens for u in units)

    last_heading: str | None = None
    for block in blocks:
        # Başlık değişti ve mevcut parça yeterince doluysa: temiz bir bölüm sınırı aç (örtüşme yok)
        if block.heading != last_heading and cur_tokens - fresh_overlap >= MIN_CHUNK_TOKENS:
            flush(carry_overlap=False)
        last_heading = block.heading

        if cur_tokens + block.tokens <= max_tokens:
            add_units(block.units, block.heading)                       # blok sığıyor
        elif block.tokens <= max_tokens:
            flush(carry_overlap=True)                                   # blok bütün kalsın diye yeni parça aç
            add_units(block.units, block.heading)
        else:
            # Blok tek başına büyük: cümle/satır sınırından böl (asla cümle ortasından değil)
            for unit in block.units:
                if cur_tokens + unit.tokens > max_tokens and cur_tokens - fresh_overlap > 0:
                    flush(carry_overlap=True)
                add_units([unit], block.heading)
    flush(carry_overlap=False)

    # Son parça çok küçükse (sadece örtüşme + birkaç kelime) öncekiyle birleştir
    if len(chunks) > 1 and chunks[-1].token_count < MIN_CHUNK_TOKENS // 2:
        last = chunks.pop()
        prev = chunks[-1]
        merged_body = prev.body + "\n" + last.body
        chunks[-1] = Chunk(prev.index, prev.header, merged_body, count_tokens(merged_body))
    return chunks

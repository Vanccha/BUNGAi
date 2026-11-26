"""ADIM 1 - Türkçe metin normalizasyonu (kelime/BM25 araması için).

NEDEN VAR?
    Kelime araması (keyword search) metinleri "harfi harfine" karşılaştırır. Ama insanlar aynı şeyi
    farklı biçimlerde yazar:
        "Havuzda"  /  "havuz"  /  "HAVUZ"  /  "havuzlar"  /  "Havuz,"
    Bilgisayar için bunlar farklı dizelerdir. Normalizasyon, hepsini aynı "kök forma" indirger ki
    bir sorguda "havuzda" yazan kişi, dokümanda "havuz" geçen kaydı bulabilsin.

NASIL BAĞLANIYOR?
    * indexer.py  -> chunk metnini buradan geçirip FTS5 (kelime indeksi) tablosuna yazar.
    * search.py   -> kullanıcının sorgusunu AYNI fonksiyondan geçirip FTS5'te arar.
    ÖNEMLİ KURAL: doküman ve sorgu AYNI normalizasyondan geçmelidir; aksi halde eşleşme olmaz.

    (Vektör/embedding araması normalizasyona ihtiyaç duymaz; model "havuzda" ile "havuz"un
    anlamca yakın olduğunu zaten bilir. Normalizasyon yalnızca kelime tarafının işidir.)

YAPILAN İŞLEMLER (sırayla)
    1. Türkçe'ye uygun küçük harf:  İ->i, I->ı   (Python'un .lower()'ı bunu yanlış yapar!)
    2. Binlik ayracı temizliği:     "6.500" -> "6500"  (aksi halde "6" ve "500" diye ikiye bölünür)
    3. Noktalama silme ve kelimelere ayırma
    4. Aksan katlama (diacritic folding):  ç->c, ğ->g, ı->i, ö->o, ş->s, ü->u
    5. Stopword (anlamsız sık kelimeler: "ve", "bir", "mi" ...) atma
    6. Hafif kök bulma (stemming): ekleri kırp  "havuzlarda" -> "havuz"
"""
import re

# ---------------------------------------------------------------------------------------------
# 1) Türkçe küçük harf
# ---------------------------------------------------------------------------------------------
def turkish_lower(text: str) -> str:
    """Türkçe kurallarına göre küçük harfe çevirir.

    Neden özel fonksiyon? Python'un str.lower() 'I' harfini 'i' yapar, oysa Türkçe'de 'I' -> 'ı'dır
    ("ISPARTA" -> "ısparta"). 'İ' harfini ise 'i' + birleşik nokta (iki karakter) yapar; bu da
    eşleşmeyi bozar. Bu yüzden .lower()'dan ÖNCE bu iki harfi elle değiştiriyoruz.
    """
    return text.replace("İ", "i").replace("I", "ı").lower()


# ---------------------------------------------------------------------------------------------
# 4) Aksan katlama
# ---------------------------------------------------------------------------------------------
_FOLD_TABLE = str.maketrans({"ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u", "â": "a", "î": "i", "û": "u"})


def fold_diacritics(text: str) -> str:
    """Türkçe'ye özgü harfleri ASCII karşılığına indirger (küçük harfli metin beklenir).

    Neden? İnsanlar mobilde çoğu zaman Türkçe karakter kullanmaz: "havuz kurallari", "kahvalti".
    Hem dokümanı hem sorguyu katlayınca "kahvaltı" ile "kahvalti" aynı olur.
    Bedeli: bazı farklı kelimeler çakışır (örn. "sık" ile "sik"). Küçük bir tesis bilgi bankasında
    bu risk ihmal edilebilir; yararı çok daha büyüktür.
    """
    return text.translate(_FOLD_TABLE)


# ---------------------------------------------------------------------------------------------
# 5) Stopword listesi (aksan katlanmış biçimde)
# ---------------------------------------------------------------------------------------------
# Stopword = hemen her cümlede geçen, arama için ayırt edici olmayan kelimeler. BM25 zaten sık geçen
# kelimeleri düşük puanlar, ama listeyi küçük tutmak sorguyu temizler ve FTS sorgusunu kısaltır.
# Dikkat: "var", "yok", "kac" gibi sorularda anlam taşıyan ama çok sık kelimeleri de attık;
# çünkü ayırt edici olan kelime genelde başkasıdır ("kac gece" -> "gece").
STOPWORDS = frozenset(
    """
    ve veya ile ya ama fakat ancak da de ki mi mu bir bu o ben sen biz siz onlar
    icin gibi kadar daha en cok pek hic her hem ne nasil neden nerede nerde hangi kim
    var yok olan olarak olur olabilir midir mi misiniz musunuz miyim musun mi
    acaba lutfen merhaba selam iyi gunler tesekkurler tesekkur sizin benim bizim bana bize size
    mumkun mu mi nedir midir yapar yapilir ediyor edilir
    """.split()
)

# ---------------------------------------------------------------------------------------------
# 6) Hafif Türkçe kök bulucu (stemmer)
# ---------------------------------------------------------------------------------------------
# Türkçe sondan eklemeli bir dildir: "havuz" -> "havuzlar" -> "havuzlarda" -> "havuzlardaki".
# Gerçek bir morfolojik analiz (Zemberek gibi) çok daha doğrudur ama büyük bir bağımlılıktır.
# Burada "kelimenin sonundan bilinen ekleri sök" şeklinde çok basit bir kural kullanıyoruz.
#
# TAKAS (trade-off):
#   + Basit, hızlı, bağımlılık yok, şeffaf; "kahvaltıda/kahvaltı/kahvaltılar" aynı köke iner.
#   - Hatalı kırpma olur (over-stemming): "kolay" gibi bir kelimenin sonundaki "ay" ek sanılabilir.
#     Bunu azaltmak için MIN_STEM_LEN kuralı var: kırpma sonrası kök en az 3 harf kalmalı.
#   - Ünlü/ünsüz uyumu ve yumuşamayı (köpek -> köpeği) çözmez: "kopek" != "kopeg".
#     Bunu ZATEN vektör araması telafi eder; hibrit aramanın nedenlerinden biri budur.
#
# Ekler, aksan katlanmış biçimde (ı->i, ü->u, ö->o, ş->s, ç->c) yazıldı. Uzun ekler önce denenir.
_SUFFIXES = sorted(
    """
    lar ler
    larin lerin lari leri lara lere larda lerde lardan lerden larla lerle
    nin nun
    dan den tan ten
    da de ta te
    ya ye na ne
    yi yu
    imiz iniz
    im in
    si su
    lik luk
    li lu
    siz suz
    ki
    ndan nden ndaki ndeki
    daki deki taki teki
    i u a e
    """.split(),
    key=len,
    reverse=True,
)
MIN_STEM_LEN = 3  # kök bunun altına inecekse eki kırpma
_MAX_STRIP_PASSES = 3  # "havuz-lar-da-ki" gibi üst üste ekler için en çok 3 tur


def stem(word: str) -> str:
    """Bir kelimenin (katlanmış, küçük harfli) sonundaki yaygın Türkçe ekleri kırpar."""
    if word.isdigit() or len(word) <= MIN_STEM_LEN:
        return word
    for _ in range(_MAX_STRIP_PASSES):
        for suffix in _SUFFIXES:
            if not word.endswith(suffix):
                continue
            remaining = len(word) - len(suffix)
            # Tek harfli ekler (i, u, a, e) çok sık yanlış tetiklenir: kök en az 4 harf kalmalı.
            min_len = MIN_STEM_LEN + 1 if len(suffix) == 1 else MIN_STEM_LEN
            if remaining >= min_len:
                word = word[:remaining]
                break  # bir ek kırpıldı; yeni sona göre tekrar dene
        else:
            break  # hiçbir ek uymadı; bitti
    return word


# ---------------------------------------------------------------------------------------------
# Birleştirilmiş API
# ---------------------------------------------------------------------------------------------
_THOUSANDS_RE = re.compile(r"(?<=\d)\.(?=\d{3}(?!\d))")  # 6.500 -> 6500 (ama 3.5 değişmez)
_WORD_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Metni küçük harfli, aksansız, noktalamasız ham kelimelere ayırır (stem/stopword YOK)."""
    text = turkish_lower(text)
    text = _THOUSANDS_RE.sub("", text)
    text = fold_diacritics(text)
    return _WORD_RE.findall(text)  # harf/rakam dışındaki her şey ayraç sayılır


def normalize_tokens(text: str) -> list[str]:
    """Arama için son kelime listesi: tokenize -> stopword at -> kök bul."""
    out: list[str] = []
    for word in tokenize(text):
        if word in STOPWORDS:
            continue
        root = stem(word)
        if root in STOPWORDS or not root:
            continue
        out.append(root)
    return out


def normalize_for_search(text: str) -> str:
    """normalize_tokens'ın boşlukla birleştirilmiş hali. FTS5'e yazılan ve aranan metin budur.

    Örnek:  "Havuzlarda cam şişe kullanılabilir mi?"  ->  "havuz cam sise kullanilabil"
    """
    return " ".join(normalize_tokens(text))

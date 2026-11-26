"""Türkçe konuşma biçimlendirme katmanı ("Türkçe doğallık eklentisi").

NEDEN VAR?
Ses modeli (OpenAI Realtime) metni okurken rakamları, ISO tarihlerini ("2027-06-10"),
rezervasyon kodlarını ("BNG-6AL3QT") ve yabancı kelimeleri ("Infinity", "Plunge")
kimi zaman yanlış, kimi zaman İngilizce telaffuzla okur. Çözüm: modele "okunacak hâlini"
biz hazırlayıp veririz; model de bu hazır metni AYNEN okur.

Bu dosya SAF Python'dur (ağ yok, veritabanı yok) — bu yüzden kolay test edilir
(bkz. backend/tests/test_turkish_speech.py).

İçindekiler
  1. Sayılar        : sayi_oku, para_oku
  2. Tarih / saat   : tarih_oku, tarih_araligi_oku, saat_oku
  3. Harf harf okuma: kod_oku, eposta_oku, telefon_oku
  4. Telaffuz sözlüğü: LEKSIKON, telaffuz_duzelt
  5. Serbest metin  : metin_hazirla (bilgi bankası metinlerini konuşmaya uygun hâle getirir)
"""
from __future__ import annotations

import re
from datetime import date, datetime

# ---------------------------------------------------------------------------
# 1. SAYILAR
# ---------------------------------------------------------------------------
_BIRLER = ["sıfır", "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz"]
_ONLAR = ["", "on", "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen", "doksan"]
# Türkçede basamak grupları: bin, milyon, milyar, trilyon ...
_BASAMAKLAR = ["", "bin", "milyon", "milyar", "trilyon"]


def _uc_hane(n: int) -> str:
    """0 < n < 1000 arasındaki sayıyı yazıya çevirir. (örn. 543 -> 'beş yüz kırk üç')"""
    yuz, kalan = divmod(n, 100)
    on, bir = divmod(kalan, 10)
    parcalar: list[str] = []
    if yuz:
        # Türkçede "bir yüz" denmez, sadece "yüz"; ama 200 = "iki yüz".
        parcalar.append("yüz" if yuz == 1 else f"{_BIRLER[yuz]} yüz")
    if on:
        parcalar.append(_ONLAR[on])
    if bir:
        parcalar.append(_BIRLER[bir])
    return " ".join(parcalar)


def _tam_sayi_oku(n: int) -> str:
    if n == 0:
        return _BIRLER[0]
    if n < 0:
        return "eksi " + _tam_sayi_oku(-n)
    gruplar: list[int] = []          # en küçük basamaktan başlayarak 3'lü gruplar
    while n:
        n, g = divmod(n, 1000)
        gruplar.append(g)
    if len(gruplar) > len(_BASAMAKLAR):
        raise ValueError("Sayı çok büyük")
    out: list[str] = []
    for i in range(len(gruplar) - 1, -1, -1):
        g = gruplar[i]
        if g == 0:
            continue
        if i == 1 and g == 1:
            out.append("bin")        # "bir bin" denmez -> "bin" (ama "bir milyon" denir)
        else:
            metin = _uc_hane(g)
            out.append(f"{metin} {_BASAMAKLAR[i]}".strip())
    return " ".join(out)


def _ondalik_ayir(s: str) -> tuple[str, str]:
    """Metin sayıyı (tam, ondalık) parçalarına ayırır. Türkçe ve İngilizce yazımı anlar:
       '43.500' -> binlik (43500) | '43,50' -> ondalık | '1.234,56' -> 1234 ve 56 | '3.5' -> 3 ve 5"""
    s = s.strip().replace(" ", "")
    if "." in s and "," in s:
        # İkisi de varsa SON ayraç ondalıktır.
        if s.rfind(",") > s.rfind("."):
            tam, ond = s.rsplit(",", 1)
            return tam.replace(".", ""), ond
        tam, ond = s.rsplit(".", 1)
        return tam.replace(",", ""), ond
    for ayrac in (".", ","):
        if ayrac in s:
            parcalar = s.split(ayrac)
            # 43.500 / 1.234.567 gibi: her parça 3 haneli -> binlik ayracı
            if len(parcalar) > 1 and all(len(p) == 3 for p in parcalar[1:]) and 1 <= len(parcalar[0]) <= 3:
                return "".join(parcalar), ""
            if len(parcalar) == 2:
                return parcalar[0], parcalar[1]
            return "".join(parcalar), ""
    return s, ""


def sayi_oku(n: int | float | str) -> str:
    """Sayıyı Türkçe okunuşuyla yazıya çevirir.

    >>> sayi_oku(43500)
    'kırk üç bin beş yüz'
    >>> sayi_oku("1.250,5")
    'bin iki yüz elli virgül beş'
    """
    if isinstance(n, float):
        n = f"{n:.10f}".rstrip("0").rstrip(".")      # 3.5 -> '3.5' (2.50 -> '2.5')
    s = str(n).strip()
    isaret = ""
    if s.startswith("-") or s.startswith("−"):
        isaret, s = "eksi ", s[1:]
    elif s.startswith("+"):
        s = s[1:]
    tam, ond = _ondalik_ayir(s)
    if not tam.isdigit():
        if tam == "" and ond.isdigit():
            tam = "0"
        else:
            raise ValueError(f"Sayı okunamadı: {n!r}")
    sonuc = _tam_sayi_oku(int(tam))
    if ond:
        if not ond.isdigit():
            raise ValueError(f"Sayı okunamadı: {n!r}")
        # "0,05" -> "sıfır virgül sıfır beş" (baştaki sıfırlar tek tek okunur)
        bas_sifir = len(ond) - len(ond.lstrip("0"))
        kalan = ond.lstrip("0")
        parca = " ".join(["sıfır"] * bas_sifir)
        if kalan:
            parca = (parca + " " if parca else "") + _tam_sayi_oku(int(kalan))
        sonuc += " virgül " + parca
    return isaret + sonuc


def rakam_rakam_oku(s: str) -> str:
    """'4521' -> 'dört beş iki bir' (kodlar, numaralar için)."""
    return " ".join(_BIRLER[int(c)] for c in s if c.isdigit())


def para_oku(tutar: int | float | str, birim: str = "lira") -> str:
    """Tutarı okunur hâle getirir.

    >>> para_oku(43500)
    'kırk üç bin beş yüz lira'
    >>> para_oku(1250.5)
    'bin iki yüz elli lira elli kuruş'
    """
    tam, ond = _ondalik_ayir(str(tutar)) if not isinstance(tutar, float) else _ondalik_ayir(f"{tutar:.2f}")
    lira = int(tam or 0)
    kurus = int((ond + "0")[:2]) if ond else 0
    parcalar = [f"{_tam_sayi_oku(lira)} {birim}"]
    if kurus:
        parcalar.append(f"{_tam_sayi_oku(kurus)} kuruş")
    return " ".join(parcalar)


# ---------------------------------------------------------------------------
# 2. TARİH VE SAAT
# ---------------------------------------------------------------------------
AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]  # date.weekday() sırası


def _tarih_coz(d: str | date | datetime) -> date:
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    return date.fromisoformat(str(d)[:10])


def tarih_oku(d: str | date | datetime, bugun: date | None = None, goreli: bool = True) -> str:
    """ISO tarihi konuşma diline çevirir.

    - Yakın tarihler göreli söylenir: bugün / yarın / öbür gün / "bu Cumartesi" (6 gün içinde).
    - Bu yıl içindeki tarihlerde yıl söylenmez; başka yıl ise yıl da okunur.

    >>> tarih_oku("2027-06-10", bugun=date(2026, 11, 26))
    'on Haziran iki bin yirmi yedi Perşembe'
    """
    t = _tarih_coz(d)
    bugun = bugun or date.today()
    gun_adi = GUNLER[t.weekday()]
    tam = f"{_tam_sayi_oku(t.day)} {AYLAR[t.month - 1]}"
    if t.year != bugun.year:
        tam += f" {_tam_sayi_oku(t.year)}"
    tam += f" {gun_adi}"
    if goreli:
        fark = (t - bugun).days
        if fark == 0:
            return f"bugün, {tam}"
        if fark == 1:
            return f"yarın, {tam}"
        if fark == 2:
            return f"öbür gün, {tam}"
        if 3 <= fark <= 6:
            return f"bu {gun_adi}, {tam}"
    return tam


def tarih_araligi_oku(giris: str | date, cikis: str | date, bugun: date | None = None) -> str:
    """'Giriş on Temmuz Cumartesi, çıkış on üç Temmuz Salı' biçiminde (ek uyumu hatası riskine girmeden)."""
    return f"giriş {tarih_oku(giris, bugun)}, çıkış {tarih_oku(cikis, bugun)}"


def saat_oku(s: str, dogal: bool = False) -> str:
    """'14:00' -> 'saat on dört'. dogal=True ise günlük konuşma: 'öğleden sonra iki'.

    >>> saat_oku("14:30")
    'saat on dört otuz'
    >>> saat_oku("14:30", dogal=True)
    'öğleden sonra iki buçuk'
    """
    m = re.match(r"^\s*(\d{1,2})[:.](\d{2})", s)
    if not m:
        raise ValueError(f"Saat okunamadı: {s!r}")
    sa, dk = int(m.group(1)), int(m.group(2))
    if not dogal:
        return f"saat {_tam_sayi_oku(sa)}" + (f" {_tam_sayi_oku(dk)}" if dk else "")
    # Doğal söyleyiş: gün bölümü + 12'lik saat
    if sa == 12:
        vakit, sa12 = "öğlen", 12
    elif sa == 0:
        vakit, sa12 = "gece", 12
    elif sa < 5:
        vakit, sa12 = "gece", sa
    elif sa < 12:
        vakit, sa12 = "sabah", sa
    elif sa < 18:
        vakit, sa12 = "öğleden sonra", sa - 12
    elif sa < 22:
        vakit, sa12 = "akşam", sa - 12
    else:
        vakit, sa12 = "gece", sa - 12
    dk_metin = ""
    if dk == 30:
        dk_metin = " buçuk"
    elif dk:
        dk_metin = " " + _tam_sayi_oku(dk)
    return f"{vakit} {_tam_sayi_oku(sa12)}{dk_metin}"


# ---------------------------------------------------------------------------
# 3. HARF HARF OKUMA (kod, e-posta, telefon)
# ---------------------------------------------------------------------------
# Türkçe harf adları. TTS "BNG" yerine "Be, Ne, Ge" desin diye yazıyla veriyoruz.
HARF_ADLARI = {
    "a": "A", "b": "Be", "c": "Ce", "ç": "Çe", "d": "De", "e": "E", "f": "Fe", "g": "Ge", "ğ": "yumuşak ge",
    "h": "He", "ı": "Iı", "i": "İ", "j": "Je", "k": "Ke", "l": "Le", "m": "Me", "n": "Ne", "o": "O", "ö": "Ö",
    "p": "Pe", "q": "Ku", "r": "Re", "s": "Se", "ş": "Şe", "t": "Te", "u": "U", "ü": "Ü", "v": "Ve",
    "w": "Çift ve", "x": "İks", "y": "Ye", "z": "Ze",
}
# Karışabilen harfler (B/D/P/T, M/N, S/Ş ...) için telefonda kullanılan şehir adları.
AYIRT_EDICI = {
    "a": "Ankara", "b": "Bursa", "c": "Ceyhan", "ç": "Çanakkale", "d": "Denizli", "e": "Edirne", "f": "Fatsa",
    "g": "Giresun", "h": "Hatay", "ı": "Isparta", "i": "İzmir", "j": "Jale", "k": "Kars", "l": "Lüleburgaz",
    "m": "Muğla", "n": "Niğde", "o": "Ordu", "ö": "Ödemiş", "p": "Pazar", "r": "Rize", "s": "Sinop",
    "ş": "Şanlıurfa", "t": "Trabzon", "u": "Uşak", "ü": "Ünye", "v": "Van", "y": "Yozgat", "z": "Zonguldak",
}
_SEMBOLLER = {"-": "tire", "_": "alt çizgi", ".": "nokta", "@": "et işareti", "+": "artı", "/": "bölü", " ": ""}


def _tr_kucuk(ch: str) -> str:
    """Türkçe küçük harf: 'I' -> 'ı', 'İ' -> 'i' (Python'un varsayılanı 'I' -> 'i' yapar!)."""
    return {"I": "ı", "İ": "i"}.get(ch, ch.lower())


def _harf_oku(ch: str, ayirt_et: bool) -> str:
    if ch.isdigit():
        return _BIRLER[int(ch)]
    if ch in _SEMBOLLER:
        return _SEMBOLLER[ch]
    k = _tr_kucuk(ch)
    ad = HARF_ADLARI.get(k)
    if ad is None:
        return ch
    if ayirt_et and k in AYIRT_EDICI:
        return f"{ad} {AYIRT_EDICI[k]}'dan"      # "Be Bursa'dan"
    return ad


def kod_oku(kod: str, ayirt_et: bool = False) -> str:
    """Rezervasyon kodunu harf harf, virgüllerle (TTS duraksasın diye) okutur.

    >>> kod_oku("BNG-6AL3QT")
    'Be, Ne, Ge, tire, altı, A, Le, üç, Ku, Te'

    ayirt_et=True: karışabilen harflere şehir adı eklenir ('Be Bursa'dan').
    """
    parcalar = [_harf_oku(c, ayirt_et) for c in kod.strip() if c.strip()]
    return ", ".join(p for p in parcalar if p)


# Çok kullanılan e-posta sağlayıcıları bütün olarak okunur.
_ALAN_ADLARI = {
    "gmail": "cimeyl", "hotmail": "hotmeyl", "outlook": "avtluk", "yahoo": "yahu", "icloud": "ayklavd",
    "yandex": "yandeks", "example": "egzampıl",
}
_UZANTILAR = {"com": "kom", "net": "net", "org": "org", "tr": "te re", "edu": "edu", "co": "ko"}


def eposta_oku(adres: str) -> str:
    """E-posta adresini geri okumak için hazırlar: yerel kısım harf harf, alan adı bütün.

    >>> eposta_oku("ali.k@gmail.com")
    'A, Le, İ, nokta, Ke, et işareti, cimeyl, nokta, kom'
    """
    adres = adres.strip().replace(" ", "")
    if "@" not in adres:
        return kod_oku(adres)
    yerel, alan = adres.rsplit("@", 1)
    parcalar = [kod_oku(yerel), "et işareti"]
    etiketler = alan.split(".")
    for i, e in enumerate(etiketler):
        if i:
            parcalar.append("nokta")
        k = e.lower()
        if i == 0 and k in _ALAN_ADLARI:
            parcalar.append(_ALAN_ADLARI[k])
        elif i > 0 and k in _UZANTILAR:
            parcalar.append(_UZANTILAR[k])
        else:
            parcalar.append(kod_oku(e))
    return ", ".join(parcalar)


def _grup_oku(g: str) -> str:
    # '05' gibi sıfırla başlayan grup rakam rakam; diğerleri sayı olarak okunur.
    if g.startswith("0"):
        return rakam_rakam_oku(g)
    return _tam_sayi_oku(int(g))


def telefon_oku(tel: str) -> str:
    """Telefon numarasını gruplayarak okur.

    >>> telefon_oku("0530 111 22 33")
    'sıfır beş yüz otuz, yüz on bir, yirmi iki, otuz üç'
    >>> telefon_oku("+90 530 111 22 33")   # ülke kodu da aynı şekilde
    'sıfır beş yüz otuz, yüz on bir, yirmi iki, otuz üç'
    """
    rakamlar = re.sub(r"\D", "", tel)
    if rakamlar.startswith("90") and len(rakamlar) == 12:
        rakamlar = "0" + rakamlar[2:]
    elif len(rakamlar) == 10 and rakamlar[0] != "0":
        rakamlar = "0" + rakamlar
    if len(rakamlar) == 11:
        gruplar = [rakamlar[0], rakamlar[1:4], rakamlar[4:7], rakamlar[7:9], rakamlar[9:11]]
        # "0" + "530" birlikte: "sıfır beş yüz otuz"
        ilk = "sıfır " + _grup_oku(gruplar[1])
        return ", ".join([ilk] + [_grup_oku(g) for g in gruplar[2:]])
    # Beklenmeyen uzunluk: 3'erli rakam grupları
    return ", ".join(rakam_rakam_oku(rakamlar[i:i + 3]) for i in range(0, len(rakamlar), 3))


# ---------------------------------------------------------------------------
# 4. TELAFFUZ SÖZLÜĞÜ
# ---------------------------------------------------------------------------
# Anahtar: metinde geçen yazım (büyük/küçük harf fark etmez). Değer: Türkçe okunuşu.
# Yalnızca "konusma" alanlarına uygulanır; ekrandaki yazıya DOKUNMAZ.
# Yönetici panelinden (Ayarlar > voice_lexicon_json) eklemeler yapılabilir.
LEKSIKON: dict[str, str] = {
    "BUNGAi": "bunga ay",
    "Infinity": "infiniti",
    "Plunge": "planc",
    "Spa": "spa",
    "Wi-Fi": "vay fay",
    "WiFi": "vay fay",
    "check-in": "çekin",
    "check-out": "çekaut",
    "brunch": "brançı",
    "lounge": "launç",
    "jakuzi": "jakuzi",
    "VIP": "vi ay pi",
    "SPA": "spa",
    "WC": "ve se",
    "TV": "te ve",
    "KDV": "ka de ve",
    "m²": "metrekare",
    "m2": "metrekare",
    "km": "kilometre",
    "kg": "kilo",
    "Dalaman": "Dalaman",
    "Kalkan": "Kalkan",
    "Antalya": "Antalya",
}


def telaffuz_duzelt(metin: str, sozluk: dict[str, str] | None = None) -> str:
    """Metindeki yabancı/marka kelimeleri okunuşlarıyla değiştirir (büyük-küçük harfe duyarsız, tam kelime).

    >>> telaffuz_duzelt("Mavi Ufuk Infinity Villa")
    'Mavi Ufuk infiniti Villa'
    """
    tum = {**LEKSIKON, **(sozluk or {})}
    # Uzun anahtarlar önce eşleşsin ("check-in" "check"ten önce)
    for anahtar in sorted(tum, key=len, reverse=True):
        desen = r"(?<![\wçğıöşüÇĞİÖŞÜ])" + re.escape(anahtar) + r"(?![\wçğıöşüÇĞİÖŞÜ])"
        metin = re.sub(desen, lambda _m, v=tum[anahtar]: v, metin, flags=re.IGNORECASE)
    return metin


# ---------------------------------------------------------------------------
# 5. SERBEST METİN (bilgi bankası kayıtları için)
# ---------------------------------------------------------------------------
_RE_ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_RE_SAAT_ARALIK = re.compile(r"\b(\d{1,2})[:.](\d{2})\s*[-–]\s*(\d{1,2})[:.](\d{2})\b")
_RE_SAAT = re.compile(r"\b([01]?\d|2[0-3]):([0-5]\d)\b")
_RE_PARA = re.compile(r"(?:₺\s*(\d[\d.,]*))|(?:\b(\d[\d.,]*)\s*(?:TL|₺|TRY|lira)\b)", re.IGNORECASE)
_RE_YUZDE = re.compile(r"%\s*(\d+(?:[.,]\d+)?)")
_RE_SAYI = re.compile(r"\d[\d.,]*\d|\d")


def metin_hazirla(metin: str, sozluk: dict[str, str] | None = None) -> str:
    """Serbest metindeki (bilgi bankası cevabı gibi) rakam, saat, para, yüzde ve yabancı kelimeleri
    konuşmaya hazır hâle getirir. Sıra önemlidir: önce özel kalıplar (tarih, saat, para), en son düz sayılar."""
    def _guvenli(f, m, *a):
        try:
            return f(m, *a)
        except Exception:  # noqa: BLE001 - okunamayan kalıbı olduğu gibi bırak
            return m.group(0)

    metin = _RE_ISO.sub(lambda m: _guvenli(lambda mm: tarih_oku(mm.group(0), goreli=False), m), metin)
    metin = _RE_SAAT_ARALIK.sub(
        lambda m: _guvenli(lambda mm: f"{saat_oku(f'{mm.group(1)}:{mm.group(2)}')} ile {saat_oku(f'{mm.group(3)}:{mm.group(4)}')[5:]} arası", m),
        metin,
    )
    metin = _RE_SAAT.sub(lambda m: _guvenli(lambda mm: saat_oku(mm.group(0)), m), metin)
    metin = _RE_PARA.sub(lambda m: _guvenli(lambda mm: para_oku((mm.group(1) or mm.group(2)).rstrip(".,")), m), metin)
    metin = _RE_YUZDE.sub(lambda m: _guvenli(lambda mm: "yüzde " + sayi_oku(mm.group(1)), m), metin)
    metin = _RE_SAYI.sub(lambda m: _guvenli(lambda mm: sayi_oku(mm.group(0)), m), metin)
    metin = telaffuz_duzelt(metin, sozluk)
    # Markdown / URL artıkları sesli okunmasın
    metin = re.sub(r"[*_`#>]+", "", metin)
    metin = re.sub(r"https?://\S+", "", metin)
    return re.sub(r"\s{2,}", " ", metin).strip()

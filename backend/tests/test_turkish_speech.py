"""Türkçe konuşma katmanı testleri: python -m pytest tests/test_turkish_speech.py"""
from datetime import date

import pytest

from app.voice.turkish_speech import (
    eposta_oku, kod_oku, metin_hazirla, para_oku, saat_oku, sayi_oku, tarih_araligi_oku, tarih_oku,
    telaffuz_duzelt, telefon_oku,
)

BUGUN = date(2026, 11, 26)  # Perşembe


@pytest.mark.parametrize("n,beklenen", [
    (0, "sıfır"), (1, "bir"), (10, "on"), (21, "yirmi bir"), (100, "yüz"), (101, "yüz bir"), (200, "iki yüz"),
    (1000, "bin"), (1500, "bin beş yüz"), (2000, "iki bin"), (11000, "on bir bin"), (43500, "kırk üç bin beş yüz"),
    (100000, "yüz bin"), (1000000, "bir milyon"), (2500000, "iki milyon beş yüz bin"), (-5, "eksi beş"),
    ("43.500", "kırk üç bin beş yüz"), ("1.234.567", "bir milyon iki yüz otuz dört bin beş yüz altmış yedi"),
    ("1.250,5", "bin iki yüz elli virgül beş"), (3.5, "üç virgül beş"), ("0,05", "sıfır virgül sıfır beş"),
    ("12,75", "on iki virgül yetmiş beş"),
])
def test_sayi_oku(n, beklenen):
    assert sayi_oku(n) == beklenen


def test_sayi_oku_gecersiz():
    with pytest.raises(ValueError):
        sayi_oku("abc")


def test_para_oku():
    assert para_oku(43500) == "kırk üç bin beş yüz lira"
    assert para_oku(43500.0) == "kırk üç bin beş yüz lira"
    assert para_oku(1250.5) == "bin iki yüz elli lira elli kuruş"
    assert para_oku("6.500 ") == "altı bin beş yüz lira"


def test_tarih_oku_uzak_ve_yil():
    assert tarih_oku("2027-06-10", bugun=BUGUN) == "on Haziran iki bin yirmi yedi Perşembe"
    # Aynı yılda yıl söylenmez
    assert tarih_oku("2026-12-31", bugun=BUGUN) == "otuz bir Aralık Perşembe"


def test_tarih_oku_goreli():
    assert tarih_oku("2026-11-26", bugun=BUGUN).startswith("bugün")
    assert tarih_oku("2026-11-27", bugun=BUGUN) == "yarın, yirmi yedi Kasım Cuma"
    assert tarih_oku("2026-11-28", bugun=BUGUN).startswith("öbür gün")
    assert tarih_oku("2026-11-29", bugun=BUGUN).startswith("bu Pazar")
    assert tarih_oku("2026-11-27", bugun=BUGUN, goreli=False) == "yirmi yedi Kasım Cuma"


def test_tarih_araligi():
    s = tarih_araligi_oku("2027-07-10", "2027-07-13", bugun=BUGUN)
    assert s == "giriş on Temmuz iki bin yirmi yedi Cumartesi, çıkış on üç Temmuz iki bin yirmi yedi Salı"


def test_saat_oku():
    assert saat_oku("14:00") == "saat on dört"
    assert saat_oku("11:00") == "saat on bir"
    assert saat_oku("14:30") == "saat on dört otuz"
    assert saat_oku("14:00", dogal=True) == "öğleden sonra iki"
    assert saat_oku("14:30", dogal=True) == "öğleden sonra iki buçuk"
    assert saat_oku("09:00", dogal=True) == "sabah dokuz"
    assert saat_oku("12:00", dogal=True) == "öğlen on iki"
    assert saat_oku("20:15", dogal=True) == "akşam sekiz on beş"
    with pytest.raises(ValueError):
        saat_oku("abc")


def test_kod_oku():
    assert kod_oku("BNG-6AL3QT") == "Be, Ne, Ge, tire, altı, A, Le, üç, Ku, Te"
    assert "Bursa'dan" in kod_oku("B7", ayirt_et=True)
    assert kod_oku("İI") == "İ, Iı"            # Türkçe i/ı ayrımı


def test_eposta_oku():
    s = eposta_oku("ali.k@gmail.com")
    assert s == "A, Le, İ, nokta, Ke, et işareti, cimeyl, nokta, kom"
    assert "alt çizgi" in eposta_oku("a_b@firma.com.tr")
    assert eposta_oku("zeynep99@x.com").startswith("Ze, E, Ye, Ne, E, Pe, dokuz, dokuz")


def test_telefon_oku():
    beklenen = "sıfır beş yüz otuz, yüz on bir, yirmi iki, otuz üç"
    assert telefon_oku("0530 111 22 33") == beklenen
    assert telefon_oku("+90 530 111 22 33") == beklenen
    assert telefon_oku("5301112233") == beklenen
    assert telefon_oku("0532 505 05 05") == "sıfır beş yüz otuz iki, beş yüz beş, sıfır beş, sıfır beş"


def test_leksikon():
    assert telaffuz_duzelt("Mavi Ufuk Infinity Villa") == "Mavi Ufuk infiniti Villa"
    assert telaffuz_duzelt("Zeytin Plunge Bungalov") == "Zeytin planc Bungalov"
    assert telaffuz_duzelt("BUNGAi Resort") == "bunga ay Resort"
    assert telaffuz_duzelt("Wi-Fi ücretsiz") == "vay fay ücretsiz"
    assert telaffuz_duzelt("Infinitylik") == "Infinitylik"            # tam kelime eşleşmesi
    assert telaffuz_duzelt("Foo bar", {"foo": "fu"}) == "fu bar"      # özel sözlük


def test_metin_hazirla():
    s = metin_hazirla("Kahvaltı 07:30-10:30 arası, gecelik 6.500 TL, depozito %20. Villa 90 m².")
    assert "yedi otuz" in s and "on otuz" in s
    assert "altı bin beş yüz lira" in s
    assert "yüzde yirmi" in s
    assert "doksan metrekare" in s
    assert not any(c.isdigit() for c in s)
    assert metin_hazirla("**Spa** https://x.com/a") == "spa"

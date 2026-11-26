# Sesli Asistan (Türkçe, OpenAI Realtime)

Sitedeki sohbet penceresinin üstündeki **Sesli** düğmesi (ya da sağ alttaki küçük mikrofon düğmesi) ile misafir asistanla konuşarak bilgi alır, müsaitlik sorar ve rezervasyon yapar. Ses→ses çalışan `gpt-realtime` modeli kullanılır.

## Mimari

```
                 ses (WebRTC, doğrudan)
  Tarayıcı  <═══════════════════════════════>  OpenAI Realtime
     │  │  oai-events veri kanalı (döküm, durum)       ▲
     │  │                                              │ WebSocket (yan kanal / sideband)
     │  └── 1) POST /api/voice/session  ─┐              │ wss://api.openai.com/v1/realtime?call_id=...
     │      2) SDP -> /v1/realtime/calls │              │  • araç çağrılarını görür
     │      3) POST .../attach {call_id} ▼              │  • aracı SUNUCUDA çalıştırır, sonucu geri yollar
     └─────────────────────────────►  FastAPI backend ───┘  • dökümü voice_sessions tablosuna yazar
        GET .../actions (kartlar)        │
                                         └─► aynı servis katmanı (availability / reservations / payments / RAG)
```

* **Ses** tarayıcı ile OpenAI arasında doğrudan akar: en düşük gecikme, backend ses taşımaz.
* **Gerçek API anahtarı** yalnızca backend'dedir. Tarayıcı 2 dakika geçerli *geçici anahtar* alır. Talimatlar, araç listesi, ses, VAD ve transkripsiyon ayarı **anahtar üretilirken sunucuda** sabitlenir.
* **Araçlar sunucuda çalışır (sideband).** Tarayıcı çağrı kimliğini (`call_id`) backend'e bildirir; backend aynı çağrıya WebSocket ile bağlanır. Model araç çağırınca olayı backend alır, `app/voice/tools.py` ile çalıştırır ve sonucu modele verir. Araç argümanları/sonuçları tarayıcıdan geçmez. Tarayıcı yalnızca rezervasyon/ödeme **kartlarını** `GET /api/voice/session/{id}/actions` ile çeker.
* **Bütünlük:** tarayıcı veri kanalından `session.update` ile talimat/araç değiştirmeye kalkarsa yan kanal bunu görür ve asıl ayarı geri yükler.
* **Süre sınırı:** istemci sayaç dolunca kapatır; sunucu da `voice_max_session_seconds + 10 sn` sonra `POST /v1/realtime/calls/{call_id}/hangup` ile çağrıyı keser.

## Dosyalar

| Dosya | Görevi |
|---|---|
| `backend/app/voice/turkish_speech.py` | **Türkçe konuşma katmanı**: sayı/para/tarih/saat/kod/e-posta/telefon okuma + telaffuz sözlüğü |
| `backend/app/voice/instructions.py` | Sesli sistem istemi + oturum yapılandırması (VAD, transkripsiyon, ses) |
| `backend/app/voice/tools.py` | Araç şemaları, dispatcher, `konusma` alanı ekleme |
| `backend/app/voice/service.py` | Geçici anahtar, oturum kaydı, yan kanal olay işleme, döküm kaydı |
| `backend/app/routers/voice.py` | `/api/voice/*` uçları |
| `backend/app/agent/tools.py` | Araç gövdeleri (`do_*`): yazılı bot ve sesli asistan **aynı** kodu kullanır |
| `backend/scripts/voice_smoke_test.py` | Mikrofonsuz uçtan uca test |
| `frontend/src/lib/useVoiceAssistant.ts` | WebRTC istemcisi (hook) |
| `frontend/src/components/VoicePanel.tsx` | Küre, döküm, kontroller, kartlar |
| `frontend/src/pages/admin/VoiceSessions.tsx` | Yönetici: görüşme listesi ve döküm |

## Türkçe doğallık katmanı

Model "43500" ya da "2027-06-10" gibi ham değerleri bazen yanlış okur (gün adlarını da yanlış hesaplayabilir). Bu yüzden araç çıktılarına **hazır okunuşlu** alanlar ekleriz ve modele "bu alanları aynen oku" deriz:

```
check_availability  ->  "konusma": {"toplam": "kırk üç bin beş yüz lira", "gece": "üç gece",
                                    "giris": "on Temmuz iki bin yirmi yedi Cumartesi", ...}
create_reservation  ->  "konusma": {"kod": "Be, Ne, Ge, tire, ...", "toplam": "...", ...}
```

`turkish_speech.py` (saf Python, test edilebilir): `sayi_oku`, `para_oku`, `tarih_oku` (bugün/yarın/"bu Cumartesi"), `saat_oku`, `kod_oku` (Türkçe harf adları; `ayirt_et=True` ile "Be Bursa'dan"), `eposta_oku`, `telefon_oku` (gruplu), `telaffuz_duzelt` ve `metin_hazirla` (bilgi bankası metnindeki rakam/saat/para/yüzdeyi yazıya çevirir). `konusma_hazirla` aracı modelin e-posta/telefon geri okumasında kullanılır. Sistem istemindeki "her zaman bilinen" bilgiler de aynı katmandan geçirilerek verilir.

**Telaffuz sözlüğü:** `LEKSIKON` (kodda) + panelden `voice_lexicon_json`. Örn. `"Infinity": "infiniti"`, `"Plunge": "planc"`. Yalnızca konuşma alanlarına uygulanır, ekrandaki yazı değişmez.

## Ayarlar (Yönetim > Bot Ayarları > Sesli Asistan)

`voice_enabled`, `voice_model`, `voice_name`, `voice_vad_eagerness`, `voice_speed`, `voice_max_session_seconds`, `voice_greeting`, `voice_lexicon_json`. Değişiklikler bir sonraki görüşmede geçerli olur. Görüşme dökümleri: **Yönetim > Sesli Görüşmeler**.

* `semantic_vad`: Türkçede fiil sonda gelir, kullanıcı cümle ortasında duraklar; sessizliğe değil cümlenin bitip bitmediğine bakan VAD sözü daha az keser. Varsayılan `medium`; e-posta/telefon dikte edenler için `low` denenebilir (yanıt biraz gecikir).
* Girdi transkripsiyonu: `gpt-4o-transcribe`, `language: tr`, villa adlarını ve alan sözcüklerini içeren `prompt`.

## Maliyet kontrolü

1. `voice_max_session_seconds` (varsayılan 300 sn): istemci + sunucu otomatik kapatma.
2. `voice_model = gpt-realtime-mini`: yaklaşık üçte bir fiyat, daha düşük kalite.
3. Eşzamanlı en fazla 8 görüşme, IP başına dakikada 6 oturum (`routers/voice.py`, `service.py`).
4. Panelden `voice_enabled` kapatılabilir.
5. Kısa cevap kuralı (1-3 cümle) çıktı sesini azaltır.

## Test

```bash
cd backend
.venv/Scripts/python.exe -m pytest                              # Türkçe konuşma katmanı birim testleri
.venv/Scripts/python.exe scripts/voice_smoke_test.py            # metin turlarıyla uçtan uca (gerçek anahtar kullanır)
.venv/Scripts/python.exe scripts/voice_smoke_test.py --audio    # + TTS ile üretilmiş Türkçe ses -> transkripsiyon
```
Betik test rezervasyonlarını otomatik iptal eder. Tarayıcıda mikrofonsuz deneme: konsolda `localStorage.bungai_fake_mic='1'` (sessiz yapay mikrofon) yazıp sayfayı yenileyin; "Yazarak gönder" kutusuyla konuşabilirsiniz.

## Bilinen sınırlar
* Mikrofon izni HTTPS (ya da localhost) gerektirir.
* Oturum durumu bellektedir (tek süreç). Birden çok sunucu için paylaşımlı depo (Redis) gerekir.
* Ödeme kartı bilgisi asla sesle alınmaz; ödeme ekrandaki "Ödemeye Geç" butonuyla yapılır.

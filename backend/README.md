# BUNGAi Backend

BUNGAi Villa & Bungalov Resort için FastAPI + SQLAlchemy (SQLite) arka ucu. Yazılı sohbet asistanı (Bunga) OpenAI Agents SDK ile,
sesli asistan OpenAI Realtime API (WebRTC + yan kanal) ile çalışır; bilgi arama kendi yazdığımız hibrit RAG katmanıdır.
Sistemin bütünü için: [../README.md](../README.md).

## Kurulum

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate          # Git Bash: source .venv/Scripts/activate
pip install -r requirements.txt
copy .env.example .env          # sonra .env içindeki değerleri düzenleyin
```

`.env` değişkenleri (`app/config.py`):

| Değişken | Açıklama |
|---|---|
| `OPENAI_API_KEY` | Sohbet, embeddings ve sesli asistan için OpenAI anahtarı. Boşsa `/api/chat` nazik bir "yapılandırılmadı" yanıtı döner, `/api/voice/session` 503 verir, RAG yalnızca kelime araması yapar; uygulamanın geri kalanı çalışır. |
| `OPENAI_MODEL` | Sohbet botu ve RAG "bağlam cümlesi" modeli. Varsayılan `gpt-4.1-mini` |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | Varsayılan `admin` / `admin123` (üretimde değiştirin) |
| `JWT_SECRET` | Admin JWT imza anahtarı (üretimde değiştirin) |
| `FRONTEND_URL` | CORS için izin verilen adres (varsayılan `http://localhost:5173`) |

## Çalıştırma

```powershell
uvicorn app.main:app --port 8000 --reload
```

- API: http://localhost:8000 — Swagger: http://localhost:8000/docs — sağlık: `/api/health`
- İlk açılışta (`app/main.py:lifespan`) `bungai.db` oluşur, RAG tabloları kurulur ve demo veri yüklenir (`app/seed.py`):
  7 villa/bungalov, 132 bilgi bankası kaydı (12 `always` + 120 `search`), ayarlar, 6 örnek rezervasyon.
  Sonra `search` kayıtları **arka planda** indekslenir (OpenAI embeddings çağrılır; anahtar yoksa atlanır).
- Sıfırlamak için sunucuyu durdurup `bungai.db` dosyasını silin (admin'in tüm değişiklikleri gider). Yalnızca arama indeksini yenilemek için admin panelinde "RAG & Arama → Tümünü yeniden indeksle".
- Yazılı botun konuşma hafızası `chat_sessions.db` içinde (Agents SDK `SQLiteSession`).

## Mock ödeme test kartları (iyzico sandbox benzeri)

| Kart | Sonuç |
|---|---|
| `5528 7900 0000 0008` | Başarılı |
| `4766 6200 0000 0001` | Başarılı |
| `4111 1111 1111 1129` | Başarısız (Yetersiz bakiye) |
| `4129 1111 1111 1111` | Başarısız (Kart limiti aşıldı / reddedildi) |
| Diğer Luhn-geçerli kartlar | Başarılı |
| Luhn-geçersiz numara | Başarısız (Geçersiz kart numarası) |

Rezervasyon durumları: başarılı ödeme -> `confirmed`, başarısız -> `payment_failed` (yeniden denenebilir). `pending_payment` rezervasyonlar 30 dakika sonra tarih bloklamaz (`services/availability.py`).

## Sohbet asistanı (yazılı)

- Her çalıştırmada `Agent`'ın talimatı veritabanından kurulur (`agent/bot.py:build_instructions`): bugünün tarihi, Ayarlar, aktif bungalov listesi, **"her zaman bilinen" (`mode="always"`) bilgi bankası kayıtları** ve işletme sahibinin ek talimatları. Admin panelindeki değişiklikler yeniden başlatma gerekmeden bir sonraki mesajda geçerlidir.
- `mode="search"` kayıtlar talimatta yoktur; bot onları `search_knowledge` aracıyla arar (hibrit RAG, `app/rag/`).
- Araçlar (`agent/tools.py`): `search_knowledge`, `list_bungalows`, `check_availability`, `find_available_bungalows`, `create_reservation` (ödeme bağlantısını da hazırlar), `create_payment_link` (yalnızca mevcut rezervasyonun ödemesini yeniden denemek için), `get_reservation_status`. `parallel_tool_calls=False`.
- Konuşma hafızası: `SQLiteSession(session_id, chat_sessions.db)`; en çok 12 tur (`max_turns`).
- Bot kart bilgisi istemez; ödeme yalnızca `/odeme/{token}` sayfasında yapılır.
- `/api/admin/chat/test` aynı mantığı kullanır (admin JWT gerekir) ve botun o turda yaptığı RAG aramalarını `debug.searches` olarak ekler.

## Bilgi bankası ve RAG

`app/rag/` (okuma sırası ve ayrıntı: [../RAG_REHBERI.md](../RAG_REHBERI.md)): `normalize` -> `chunking` -> `contextual` -> `embeddings` -> `store` (SQLite + FTS5 + RAM'de numpy matrisi) -> `indexer` (hash ile artımlı indeksleme) -> `search` (vektör + BM25 + RRF + güven eşiği).
Admin bir kaydı kaydedince indeksleme arka planda çalışır; sunucu açılışında eksik/değişmiş kayıtlar tamamlanır.

Ölçüm (`eval/`, 57 soru): hibrit Recall@1 0.904, Recall@5 0.962, MRR 0.933; cevaplı sorularda yanlış red 0/52, cevapsızlarda doğru "bilmiyorum" 2/5.

```powershell
$env:PYTHONIOENCODING="utf-8"; .venv\Scripts\python.exe -m eval.rag_eval       # özet (-v: ayrıntı)
```

## Sesli asistan

`app/voice/` + `app/routers/voice.py` (ayrıntı: [../SESLI_ASISTAN.md](../SESLI_ASISTAN.md)):

- `POST /api/voice/session` OpenAI'den 120 sn'lik geçici anahtar alır (talimat/araç/ses/VAD sunucuda sabitlenir).
- Tarayıcı WebRTC'yi OpenAI ile kurar, `call_id`'yi `POST /api/voice/session/{id}/attach` ile bildirir; backend aynı çağrıya WebSocket (sideband) açar ve araçları **sunucuda** çalıştırır (`voice/service.py`, `voice/tools.py`; gövdeler `agent/tools.py:do_*` ile ortak).
- `voice/turkish_speech.py`: sayı/para/tarih/saat/kod/e-posta/telefon için Türkçe okunuş; araç sonuçlarına `konusma` alanları eklenir.
- Görüşme dökümü `voice_sessions` tablosuna yazılır; yönetici panelinde okunur.
- Korumalar: IP başına dakikada 6 oturum, en çok 8 eşzamanlı görüşme, `voice_max_session_seconds` (varsayılan 300) sonunda otomatik kapanış.
- Canlı oturum durumu bellektedir (tek süreç).

## Test

```powershell
.venv\Scripts\python.exe -m pytest                         # 33 birim test (Türkçe konuşma katmanı)
.venv\Scripts\python.exe scripts\voice_smoke_test.py       # mikrofonsuz sesli uçtan uca (gerçek anahtar, ücretli)
```

## Dosya yapısı

```
app/main.py, config.py, database.py, models.py, schemas.py, seed.py
app/seed_data/ bungalows.py, knowledge_short.py, knowledge_long.py   demo içerik
app/routers/   public, reservations, payments, chat, voice, admin
app/services/  availability (30 dk kuralı), reservations, payments (mock iyzico)
app/agent/     bot.py (Agent + dinamik talimat), tools.py (do_* gövdeleri + function tools)
app/rag/       normalize, chunking, contextual, embeddings, store, indexer, search
app/voice/     instructions, tools, service (sideband), turkish_speech, migrate
eval/          rag_eval.py, questions.json
scripts/       voice_smoke_test.py
tests/         test_turkish_speech.py
```

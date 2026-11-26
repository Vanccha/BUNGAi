# BUNGAi — Genel Bakış (Ana Doküman)

Bu doküman projenin **tek giriş kapısı**dır: sistemin uçtan uca nasıl çalıştığını anlatır, ayrıntı için
diğer dokümanlara ve koda bağlantı verir. Buradaki her iddia koddan doğrulanmıştır; kod referansları
`dosya:fonksiyon` biçimindedir (satır numaraları zamanla kayabilir, fonksiyon adı ile arayın).

İçindekiler: [1. BUNGAi nedir](#1-bungai-nedir) · [2. Mimari](#2-genel-mimari) · [3. Klasörler](#3-klasör-yapısı) ·
[4. Çalıştırma](#4-çalıştırma-windows) · [5. İstek yolculukları](#5-bir-isteğin-yolculuğu) ·
[6. Chatbot](#6-chatbot-nasıl-çalışır) · [7. RAG](#7-bilgi-bankası--rag-özet) · [8. Sesli asistan](#8-sesli-asistan-özet) ·
[9. Admin](#9-admin-paneli) · [10. Veri modeli](#10-veri-modeli) · [11. Güvenlik](#11-güvenlik-notları) ·
[12. Maliyet](#12-maliyetler) · [13. Test](#13-test-ve-doğrulama) · [14. Sınırlamalar](#14-bilinen-sınırlamalar--yapılacaklar) ·
[15. Doküman haritası](#15-doküman-haritası)

---

## 1. BUNGAi nedir

BUNGAi, kurgusal bir **havuzlu villa/bungalov tatil köyünün** (Kalkan, Kaş / Antalya) tam bir demo sitesidir.
Misafir sitede villaları gezer, takvimden müsaitliğe bakar, rezervasyon yapar ve **demo iyzico** ödeme sayfasında
(gerçek para yok) ödemeyi tamamlar. Aynı işi iki yapay zekâ asistanıyla da yapabilir: **yazılı chatbot (Bunga)** ve
**sesli asistan** (mikrofonla Türkçe konuşma). İşletme sahibi **admin panelinden** villaları, rezervasyonları,
botun bilgi bankasını ve ayarlarını yönetir, botu test eder, sesli görüşme dökümlerini okur.

Teknolojiler (kısaca, ilk geçtikleri yerde açıklanır):

| Katman | Teknoloji |
|---|---|
| Backend | Python 3.13, **FastAPI** (web API çerçevesi), SQLAlchemy 2 + **SQLite** (tek dosyalık veritabanı) |
| Frontend | **React 19** + Vite + TypeScript + Tailwind CSS v4 (`frontend/package.json`) |
| Yazılı bot | **OpenAI Agents SDK** (`openai-agents`; modelin "araç" çağırarak iş yapmasını sağlayan kütüphane), varsayılan model `gpt-4.1-mini` |
| Bilgi arama | **RAG** (soruya göre bilgi bankasında arayıp cevabı o bilgiyle verme): embedding + BM25 + RRF, çerçevesiz kendi kodumuz |
| Sesli asistan | **OpenAI Realtime API** (ses→ses model), tarayıcıda **WebRTC** (tarayıcı-sunucu arası canlı ses bağlantısı) |

---

## 2. Genel mimari

```
 ┌──────────────────────────┐   /api/*    ┌──────────────┐        ┌──────────────────────────┐
 │ Tarayıcı (React)         │────────────►│ Vite dev     │───────►│ FastAPI backend :8000     │
 │ :5173                    │◄────────────│ proxy        │◄───────│ (app/main.py)             │
 │ site + chat + ses + admin│             │ (vite.config)│        │                           │
 └───────┬──────────────────┘             └──────────────┘        │  routers/  → HTTP uçları  │
         │                                                        │  services/ → iş kuralları │
         │ WebRTC (ses + oai-events)                              │  agent/    → yazılı bot   │
         │ doğrudan, geçici anahtarla                             │  rag/      → bilgi arama  │
         ▼                                                        │  voice/    → sesli asistan│
 ┌──────────────────────────┐   WebSocket (sideband, call_id)     └───┬──────────┬────────────┘
 │ OpenAI Realtime          │◄────────────────────────────────────────┘          │
 │ (gpt-realtime)           │                                                    │ SQLAlchemy
 └──────────────────────────┘                                                    ▼
 ┌──────────────────────────┐  HTTPS (anahtar sadece backend'de)          ┌──────────────────┐
 │ OpenAI API               │◄────── sohbet (Agents SDK), embeddings,     │ SQLite           │
 │ chat / embeddings /      │        bağlam cümleleri, client_secrets     │ bungai.db        │
 │ client_secrets           │                                             │ chat_sessions.db │
 └──────────────────────────┘                                             └──────────────────┘
```

Her kutunun görevi:

* **Tarayıcı (React)** — site sayfaları, sohbet balonu, sesli panel ve admin paneli. Backend'i yalnızca `fetch('/api/...')` ile çağırır (`frontend/src/api/client.ts`).
* **Vite proxy** — geliştirmede `/api` isteklerini `http://localhost:8000`'e yönlendirir (`frontend/vite.config.ts`); CORS derdi olmaz. (Üretimde bunun yerine ters proxy/aynı alan adı gerekir.)
* **FastAPI** — tüm iş mantığı. Rezervasyon/ödeme kuralları `services/` içindedir; REST uçları, yazılı bot ve sesli asistan **aynı servis kodunu** kullanır.
* **SQLite** — `backend/bungai.db` (uygulama verisi + bilgi parçaları + FTS5 kelime indeksi) ve `backend/chat_sessions.db` (yazılı botun konuşma hafızası).
* **OpenAI API (sohbet)** — Agents SDK, `Runner.run` ile modeli ve araçları döngüde çalıştırır (`agent/bot.py:run_chat_with_debug`).
* **OpenAI API (embeddings)** — bilgi parçalarını/soruları sayı vektörüne çevirir (`text-embedding-3-small`, `rag/embeddings.py`).
* **OpenAI Realtime** — sesli asistanın beyni. Ses tarayıcıdan **doğrudan** OpenAI'ye akar; backend sese dokunmaz, yalnızca bir **yan kanal (sideband)** WebSocket ile araçları çalıştırır (`voice/service.py:run_sideband`).

---

## 3. Klasör yapısı

```
BUNGAi/
├─ README.md                  ← bu doküman
├─ CONTRACT.md                ← API sözleşmesi: tüm uçlar, JSON şemaları, mock ödeme kuralları
├─ RAG_REHBERI.md             ← RAG'i kodu okuyarak öğrenme rehberi (+ eval sayıları)
├─ SESLI_ASISTAN.md           ← sesli asistan mimarisi, ayarlar, test
├─ backend/
│  ├─ README.md               ← backend kurulum/özet
│  ├─ .env / .env.example     ← gizli ayarlar (.env git'e girmez)
│  ├─ requirements.txt, pytest.ini
│  ├─ bungai.db               ← ana veritabanı (ilk açılışta oluşur, git'e girmez)
│  ├─ chat_sessions.db        ← yazılı bot konuşma hafızası
│  ├─ app/
│  │  ├─ main.py              ← FastAPI uygulaması, açılış (lifespan), hata işleyiciler, router kayıtları
│  │  ├─ config.py            ← .env okuma (OPENAI_API_KEY, ADMIN_*, JWT_SECRET...)
│  │  ├─ database.py          ← SQLAlchemy engine/oturum
│  │  ├─ models.py            ← tablolar (bkz. §10)
│  │  ├─ schemas.py           ← Pydantic istek/yanıt şemaları
│  │  ├─ seed.py              ← boş DB'ye demo veri yükler
│  │  ├─ seed_data/           ← bungalovlar, 12 kısa + 120 "search" bilgi kaydı (11 uzun doküman dahil)
│  │  ├─ routers/             ← HTTP uçları: public, reservations, payments, chat, voice, admin
│  │  ├─ services/            ← availability.py (müsaitlik/30 dk kuralı), reservations.py, payments.py (mock iyzico)
│  │  ├─ agent/               ← bot.py (Agent + dinamik talimat), tools.py (araç gövdeleri do_*)
│  │  ├─ rag/                 ← normalize, chunking, contextual, embeddings, store, indexer, search
│  │  └─ voice/               ← instructions, tools, service (sideband), turkish_speech, migrate
│  ├─ eval/                   ← rag_eval.py + questions.json (57 soru)
│  ├─ scripts/voice_smoke_test.py   ← mikrofonsuz sesli uçtan uca test
│  └─ tests/test_turkish_speech.py  ← birim testler
└─ frontend/
   ├─ README.md
   ├─ vite.config.ts          ← port 5173 + /api proxy
   └─ src/
      ├─ App.tsx              ← tüm rotalar
      ├─ api/                 ← client.ts (tipli fetch sarmalayıcı), types.ts (CONTRACT ile birebir)
      ├─ components/          ← ChatWidget/ChatPanel (yazılı bot), VoicePanel, Calendar, Layout...
      ├─ pages/               ← Home, Bungalows, BungalowDetail, Payment, ReservationStatus
      ├─ pages/admin/         ← Dashboard, Knowledge, Rag, BotSettings, VoiceSessions, BotTest, AdminBungalows, AdminReservations
      ├─ lib/useVoiceAssistant.ts  ← WebRTC sesli istemci (hook)
      └─ content/images.ts    ← sitedeki statik görsel URL'leri (Unsplash)
```

---

## 4. Çalıştırma (Windows)

### Backend (PowerShell)

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env        # sonra .env'yi düzenleyin
uvicorn app.main:app --port 8000 --reload
```

`backend/.env` (şablon: `backend/.env.example`, okuyan kod: `app/config.py`):

| Değişken | Anlamı |
|---|---|
| `OPENAI_API_KEY` | Sohbet, embeddings ve sesli asistan için **tek** OpenAI anahtarı. Boşsa site çalışır; `/api/chat` "yapılandırılmadı" der, sesli asistan 503 verir, aramada yalnızca kelime araması çalışır. |
| `OPENAI_MODEL` | Sohbet botu ve RAG "bağlam cümlesi" modeli. Varsayılan `gpt-4.1-mini`. |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | Varsayılan **`admin` / `admin123`** — üretimde mutlaka değiştirin. |
| `JWT_SECRET` | Admin oturum jetonlarını imzalama anahtarı. Varsayılan `change-me-in-production`. |
| `FRONTEND_URL` | CORS'ta izinli adres (varsayılan `http://localhost:5173`). |

İlk açılışta (`app/main.py:lifespan`): tablolar oluşur → RAG tabloları (`knowledge_chunks`, FTS5) kurulur → DB boşsa demo veri yüklenir
(`seed.py:seed_if_empty`: **7 villa/bungalov, 132 bilgi kaydı** [12 `always` + 120 `search`], ayarlar, 6 örnek rezervasyon) →
sesli asistan sütunları eski DB'lere eklenir (`voice/migrate.py`) → arka planda eksik bilgi kayıtları indekslenir
(`rag.start_background_reindex`). İlk açılışta bu indeksleme **OpenAI'yi çağırır** (anahtar yoksa atlanır, kelime araması yine çalışır).

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Adresler

| Ne | Adres |
|---|---|
| Site | http://localhost:5173 |
| API + Swagger | http://localhost:8000 · http://localhost:8000/docs |
| Sağlık kontrolü | http://localhost:8000/api/health |
| Admin girişi | http://localhost:5173/admin/giris — `admin` / `admin123` |

Mikrofon tarayıcıda yalnızca **HTTPS veya localhost**'ta çalışır.

### Veritabanını sıfırlama / yeniden yükleme

1. Sunucuyu durdurun.
2. `backend/bungai.db` dosyasını silin (isterseniz `chat_sessions.db*` dosyalarını da: botun konuşma hafızası).
3. Sunucuyu yeniden başlatın: demo veri tekrar yüklenir, bilgi kayıtları arka planda yeniden indekslenir (OpenAI çağrıları, küçük bir maliyet).

Dikkat: bu işlem admin'in yaptığı **tüm** değişiklikleri (bilgi bankası, ayarlar, rezervasyonlar, sesli görüşme kayıtları) siler.
Yalnızca indeksi baştan kurmak için admin panelinde **RAG & Arama → Tümünü yeniden indeksle** yeterlidir.

---

## 5. Bir isteğin yolculuğu

### 5a. Web sitesinden rezervasyon → ödeme

1. Misafir villa sayfasında (`pages/BungalowDetail.tsx`) tarih seçer. Takvim `GET /api/availability/calendar` (`services/availability.py:booked_dates`), fiyat `GET /api/availability` (`availability.quote`) ile gelir.
2. Form gönderilince `api.createReservation` → `POST /api/reservations` → `routers/reservations.py:create` → `services/reservations.py:create_reservation`:
   villa aktif mi, kişi sayısı kapasiteyi aşıyor mu, tarih geçerli mi (`validate_range`: çıkış > giriş, geçmişte değil), müsait mi (`is_available`) kontrol edilir.
   Hepsi geçerse `BNG-XXXXXX` kodlu, **`pending_payment`** durumlu kayıt oluşur (`source="web"`). Müsait değilse **409**.
3. Sayfa hemen `api.initPayment(code)` → `POST /api/payments/init` → `payments.init_payment`: rastgele `token` ile bir `Payment(status="initialized")` oluşturur; yanıtta `payment_page_url = /odeme/{token}`.
4. Misafir `/odeme/{token}` sayfasına (`pages/Payment.tsx`) gider, kart bilgilerini girer → `POST /api/payments/{token}/complete` → `payments.complete_payment`:
   * Kart sahte-iyzico kurallarına bakılır (aşağıdaki tablo). Kart numarası **hiçbir yere kaydedilmez** (`Payment` tablosunda kart alanı yok).
   * Başarılıysa tarih hâlâ boş mu diye bir kez daha bakılır (`is_available(..., exclude_reservation_id=...)`); doluysa 409 "tarihler başkasına ayrıldı".
   * Başarılı → `payment.status="success"`, `reservation.status="confirmed"`. Başarısız → `payment.status="failure"`, `reservation.status="payment_failed"`.
5. Başarısız ödemede aynı sayfadan **tekrar denenebilir** (aynı token; `payment_failed` engel değildir) ya da `/rezervasyon/{code}` sayfasından yeni ödeme başlatılır (`pages/ReservationStatus.tsx` → `initPayment`).

**Durum makinesi** (`Reservation.status`):

```
                     başarılı kart                        admin panelinden elle
 pending_payment ───────────────────► confirmed          (herhangi bir durum → herhangi bir durum:
        │  └──── başarısız kart ───► payment_failed ─┐    PATCH /api/admin/reservations/{id})
        │                                ▲           │
        │                                └─ yeniden dene (başarılıysa → confirmed)
        └────────── admin iptali ──────► cancelled     (cancelled ödenemez: 409)
```

**30 dakika tutma kuralı** (`services/availability.py:PENDING_HOLD_MINUTES`, `_blocking_filter`):
tarihleri yalnızca `confirmed` rezervasyonlar **ve 30 dakikadan yeni `pending_payment`** rezervasyonlar bloklar. `payment_failed`
ve `cancelled` bloklamaz. 30 dakika dolan bekleyen rezervasyon silinmez; sadece tarihi bloklamayı bırakır. Misafir o sırada hâlâ
ödeyebilir — ama tarihler başkasına verildiyse ödeme adımındaki kontrol 409 verir. Çıkış günü bloklanmaz (aynı gün başka giriş olabilir).

**Mock iyzico test kartları** (`services/payments.py`, `CONTRACT.md`):

| Kart | Sonuç |
|---|---|
| `5528 7900 0000 0008`, `4766 6200 0000 0001` | Başarılı |
| `4111 1111 1111 1129` | Başarısız: Yetersiz bakiye |
| `4129 1111 1111 1111` | Başarısız: Kart limiti aşıldı / reddedildi |
| Diğer Luhn-geçerli numara | Başarılı |
| Luhn-geçersiz numara | Başarısız: Geçersiz kart numarası |

(Luhn: kart numaralarının kendi içinde taşıdığı basit sağlama algoritması, `payments.luhn_valid`.)

### 5b. Yazılı chatbot mesajı

1. Sohbet balonu (`components/ChatWidget.tsx` → `ChatPanel.tsx`) `api.chat(message, session_id)` → `POST /api/chat` (`routers/chat.py:chat`; mesaj en çok 4000 karakter, `schemas.ChatIn`).
   `session_id` tarayıcıda `localStorage` içinde (`bungai_chat_session`) saklanır; ilk mesajda boştur, backend üretir.
2. `agent/bot.py:run_chat_with_debug`: anahtar yoksa hazır "yapılandırılmadı" cevabı döner. Varsa `SQLiteSession(session_id, chat_sessions.db)` açılır —
   bu, **konuşma hafızasıdır**: önceki mesajlar ve araç sonuçları SDK tarafından bu dosyadan okunup yazılır, böylece bot bağlamı hatırlar.
3. `Runner.run(build_agent(), message, context=ChatContext(db), session=session, max_turns=12)`. Talimat **her çalıştırmada** veritabanından yeniden kurulur
   (`bot.py:_dynamic_instructions` → `build_instructions`), yani admin'in değişikliği **bir sonraki mesajda** geçerlidir. Talimat şunlardan oluşur:
   * bugünün tarihi + gün adı (göreli tarihler için), tesis bilgileri (`Settings`),
   * genel kurallar, rezervasyon akışı, güvenlik kuralları (bkz. §6),
   * aktif bungalov listesi (id, ad, kapasite, fiyat) — **tek doğru kaynak**,
   * **"her zaman bilinen"** bilgiler: `mode="always"` kayıtlar (`build_always_section`),
   * işletme sahibinin ek talimatları (`Settings.bot_extra_instructions`).
4. Model gerekirse araç çağırır (`agent/tools.py`): bilgi sorusu → `search_knowledge` (RAG, §7); müsaitlik → `find_available_bungalows`/`check_availability`;
   misafir özeti **onayladıktan sonra** → `create_reservation`. Bu araç rezervasyonu oluşturur (`source="chatbot"`) **ve ödeme bağlantısını da** hazırlar (`payments.init_payment`).
   Araçlar, REST uçlarıyla aynı `services/` kodunu çağırır.
5. Araçlar arayüz kartı gerektiğinde `ChatContext.actions` listesine ekler: `reservation_summary` ve `payment_link`. Yanıt: `{session_id, reply, actions}`.
   Frontend `payment_link` için **"Ödemeye Geç"** butonunu (`ChatPanel.tsx:PaymentCard`), `reservation_summary` için özet kartını çizer. Bot ödeme URL'sini metne yazmaz; düğme otomatiktir.
6. Hata olursa (model/ağ) kullanıcıya nazik bir hata metni döner, endpoint çökmez (`ERROR_REPLY`).

### 5c. Sesli asistan görüşmesi

(Ayrıntı: `SESLI_ASISTAN.md`.) Sıra `frontend/src/lib/useVoiceAssistant.ts:start` ve `backend/app/voice/service.py` üzerinden:

1. Misafir sohbet penceresindeki **Sesli** düğmesine basar → tarayıcı mikrofon izni ister (`getUserMedia`).
2. **Oturum açma:** `POST /api/voice/session` (`routers/voice.py:create_session`). IP başına dakikada 6 oturum sınırı; `voice/service.py:create_session_sync`:
   anahtar var mı, `voice_enabled` açık mı, eşzamanlı görüşme < 8 mi kontrol edilir. Sonra `voice/instructions.py:build_session_config` talimat + araç listesi + ses + VAD + transkripsiyon ayarını
   **sunucuda** kurar ve OpenAI'den `POST /v1/realtime/client_secrets` ile **geçici anahtar** (120 sn ömürlü) alır. Bellekte `VoiceRuntime`, DB'de `voice_sessions` satırı (`status="created"`) oluşur.
   Tarayıcıya yalnızca `{client_secret, session_id, max_seconds, greeting...}` gider.
3. **WebRTC:** tarayıcı `RTCPeerConnection` + `oai-events` veri kanalı kurar, SDP teklifini `https://api.openai.com/v1/realtime/calls` adresine **geçici anahtarla** yollar.
   Yanıtın `Location` başlığındaki `rtc_...` değeri **call_id**'dir. Ses artık tarayıcı ↔ OpenAI arasında doğrudan akar.
4. **Attach:** tarayıcı `POST /api/voice/session/{id}/attach {call_id}` der (`service.attach`; `rtc_` biçimi doğrulanır, oturum yalnızca bir kez bağlanır, süre dolmadan). Durum `active` olur ve
   `run_sideband` aynı çağrıya `wss://api.openai.com/v1/realtime?call_id=...` WebSocket'i açar (sunucu anahtarıyla).
5. **Araçlar sunucuda:** model bir fonksiyon çağırınca olay yan kanala düşer (`VoiceBrain._on_response_done`). Araç `asyncio.to_thread` ile `voice/tools.py:run_voice_tool` üzerinden, REST ile **aynı** `do_*` gövdeleriyle çalışır
   (`ChatContext(source="voice")`, yani rezervasyon kaynağı `voice`). Sonuç `function_call_output` olarak modele geri yollanır, ardından `response.create`. Argüman/sonuçlar tarayıcıdan geçmez.
6. **Türkçe konuşma katmanı:** `run_voice_tool` sonuca `konusma` alanları ekler (`add_konusma`): sayı, para, tarih (gün adıyla), saat, kod, e-posta, telefon **sesli okunacak Türkçe metne** çevrilir
   (`voice/turkish_speech.py`); modele "bu alanları aynen oku" denir. Ayrıca `konusma_hazirla` aracı modelin e-posta/telefon geri okumasında kullanılır.
7. **Kartlar:** tarayıcı her saniye `GET /api/voice/session/{id}/actions?after=N` ile yoklar (polling); araçlardan doğan `reservation_summary`/`payment_link` kartları ekranda çıkar. Ödeme yine "Ödemeye Geç" ile sayfada yapılır; kart bilgisi sesle **asla** alınmaz.
8. **Bütünlük ve süre:** tarayıcı veri kanalından talimat/araç değiştirmeye kalkarsa yan kanal bunu fark edip asıl ayarı geri yükler (`_check_integrity`). `voice_max_session_seconds` (varsayılan 300) dolunca istemci kapatır;
   sunucu da +10 sn sonra `hangup` ile çağrıyı keser.
9. **Bitiş:** `POST /api/voice/session/{id}/end` (veya bağlantı kopması) → `service.persist` ile döküm (kullanıcı, asistan, araç satırları), süre, rezervasyon kodları `voice_sessions` tablosuna yazılır; durum `ended` (hata: `error`).
   Admin → **Sesli Görüşmeler** sayfasında okunur.

### 5d. Admin bilgi bankasına kayıt ekler

1. Admin → **Chatbot Bilgi Bankası** (`pages/admin/Knowledge.tsx`) → kayıt ekler → `POST /api/admin/knowledge` (`routers/admin.py:create_knowledge`, JWT gerekir).
2. Kayıt kaydedilir; `rag.mark_pending_if_changed` çalışır:
   * **"Her zaman bilinsin" (`mode="always"`)** → parçalar silinir, durum `not_applicable`, indekslenecek bir şey yoktur.
   * **"Gerektiğinde aransın" (`mode="search"`)** → içerik özeti (SHA-256 hash: kategori+başlık+içerik+mod) eskisinden farklıysa durum `pending`. Hash aynıysa (ör. yalnızca sıra/aktiflik değişti) **hiçbir şey yapılmaz**.
3. HTTP yanıtı hemen döner; indeksleme **arka planda** (`BackgroundTasks` → `rag/indexer.py:index_entry`) şu adımlarla yürür:
   parçala (`chunking.py`, ~450 token, %15 örtüşme, "Kategori > Başlık > Alt başlık" bağlam başlığı) →
   uzun dokümanlarda (>800 token) her parçaya "dokümandaki yeri" cümlesi ekle (`contextual.py`, `OPENAI_MODEL` ile) →
   embedding üret (`embeddings.py`) → kelime indeksi için normalize et (`normalize.py`) → `knowledge_chunks` + `knowledge_fts` tablolarına yaz (`store.py`) → durum `indexed`.
   Hata olursa `error` (kelime araması yine çalışır; hash kaydedilmez, sonra yeniden denenir). Panel `pending` varken durumu yoklar.
4. Bir sonraki misafir sorusunda bot `search_knowledge` ile bu kaydı bulabilir; `always` kayıt ise bir sonraki mesajın talimatında zaten görünür.

**Hangi kayıt hangi modda olmalı?** Basit kural: *önce "gerektiğinde aransın" ile başla; "bot bunu **her konuşmada** bilmeli, yanlış olması pahalı" dediğin kısa şeyi "her zaman bilinsin" yap.*

| | Her zaman bilinir (always) | Gerektiğinde aranır (search) |
|---|---|---|
| Ne anlama gelir | Metin **her mesajda** botun talimatına girer | Parçalanıp indekslenir; bot soruya göre arar |
| Ne koyulur | Kısa, kritik: giriş/çıkış saati, iptal politikası, iletişim, adres, ödeme yöntemleri, fiyat özeti | Uzun/ayrıntılı: menü ve fiyatlar, spa, kurallar, aktivite programı, transfer tablosu |
| Artısı | Arama hatası riski yok | Sınırsız büyür, token maliyeti düşük |
| Eksisi | Her mesajda token öder; toplam 20.000 token uyarı eşiği (`admin.py:ALWAYS_TOKEN_LIMIT`) | Arama kaçırabilir |

(Panelde rozetler "Her zaman bilinir" / "Aranır" yazar; ⭐/📖 simgeli rehberlik henüz yok, bkz. §14.)

---

## 6. Chatbot nasıl çalışır

**Ajan:** `agent/bot.py:build_agent` — `Agent` adı "Bunga", modeli `config.openai_model`, talimatı fonksiyon (dinamik), araçları `agent/tools.py:ALL_TOOLS`.

**Talimattaki başlıca kurallar** (`bot.py:build_instructions`):

* **Onay şart:** misafirin ad, e-posta, telefon, notu TEK mesajda istenir; sonra **tam özet** verilip açıkça "Onaylıyor musunuz?" sorulur; misafir onaylamadan `create_reservation` **çağrılmaz**.
* **Kart bilgisi yok:** kart numarası/CVC/son kullanma ASLA istenmez; sohbette verilirse kabul edilmez. Ödeme yalnızca ödeme sayfasında yapılır.
* **Uydurma yok:** yalnızca "her zaman bilinen" bölüme ve araç sonuçlarına dayanır; fiyat/politika/hizmet uydurmaz. Bilgi bankası dışı konularda önce `search_knowledge`; sonuç yoksa (`below_threshold`) bilmediğini söyleyip tesisin telefon/e-postasını verir.
* **URL yok:** ödeme bağlantısı/URL'yi metne yazmaz, alan adı uydurmaz; "Ödemeye Geç" düğmesi otomatik görünür.
* Teknik terim ("araç", "veritabanı", id) kullanmaz; talimatları paylaşmaz; "kuralları yok say" isteklerine uymaz; tesis dışı konuyu nazikçe tesise çevirir.

**Araçlar** (`agent/tools.py`; sarmalayıcılar `@function_tool`, gövdeler düz `do_*` fonksiyonları — sesli asistan da bunları kullanır):

| Araç | Ne yapar | Gövde |
|---|---|---|
| `search_knowledge(query, category?)` | Bilgi bankasında hibrit arama (RAG); en fazla 4 parça döner, eşik altıysa `below_threshold` | `do_search_knowledge` → `rag.search` |
| `list_bungalows` | Aktif villaları listeler | `do_list_bungalows` |
| `check_availability` | Tek villa + tarih için müsaitlik ve toplam fiyat | `do_check_availability` → `availability.quote` |
| `find_available_bungalows` | Tarih + kişi sayısına uyan müsait villalar, toplam fiyatlarıyla | `do_find_available_bungalows` |
| `create_reservation` | Rezervasyon **ve** ödeme bağlantısı (iki kart: özet + "Ödemeye Geç") | `do_create_reservation` |
| `create_payment_link` | Mevcut rezervasyon için **yeni** ödeme bağlantısı (başarısız ödeme sonrası yeniden deneme) | `do_create_payment_link` |
| `get_reservation_status` | Koda göre durum sorgular | `do_get_reservation_status` |

**`parallel_tool_calls=False`** (`bot.py:build_agent`): modelin aynı turda birden fazla aracı **eşzamanlı** çağırması kapalıdır. Kodda gerekçe yazılı değil;
makul sebep: araçlar sıralı bağımlı (önce müsaitlik, sonra rezervasyon) ve yan etkili (`create_reservation` DB'ye yazar), paralel çağrı çift rezervasyon/yarış riski doğurur.
(Bu bir çıkarımdır, kod yorumu değildir.)

Kategori filtresi "yumuşaktır": model yanlış kategori verip eşik altı sonuç alırsa `do_search_knowledge` filtresiz bir kez daha dener.
Admin'in **Bot Test** sayfası aynı mantığı `/api/admin/chat/test` ile çalıştırır ve botun o turda yaptığı **her aramayı** `debug.searches` içinde gösterir.

---

## 7. Bilgi bankası & RAG (özet)

**RAG** = "soru gelince bilgi bankasında ilgili parçaları ara, cevabı yalnızca onlara dayandır". Tüm menü/spa/kural metnini her mesaja koymak (≈50 bin token) pahalı ve yavaş olurdu; bu yüzden uzun kayıtlar aranır, kısa kritik kayıtlar prompt'ta durur.

**Arama (okuma yolu)**, `rag/search.py:search`:

1. Soru normalize edilir (Türkçe küçük harf, aksan katlama, basit ek kırpma: `rag/normalize.py`).
2. **Vektör araması:** soru embedding'e çevrilir, tüm parça vektörleriyle kosinüs benzerliği (RAM'de numpy matrisi; en iyi 20).
3. **Kelime araması (BM25):** SQLite FTS5 (en iyi 20).
4. **RRF** (Reciprocal Rank Fusion): iki sıralama skor değil **sıra** üzerinden birleştirilir (`reciprocal_rank_fusion`, k=60).
5. Komşu parçalar birleştirilir, sonra **güven eşiği**: kosinüs ≥ 0.38 **veya** BM25 ≥ 10 (`search.py:VECTOR_MIN_COSINE`, `KEYWORD_MIN_SCORE`). Hiçbiri geçemezse `below_threshold=true`.
6. En iyi 4 parça bota gider.

Anahtar yoksa `embeddings_enabled=false` ve yalnızca kelime araması çalışır.

**Güncel ölçüm** (`eval/rag_eval.py`, bu depodaki 132 kayıt / 154 parça, 57 soru: 52 cevaplı + 5 cevapsız; bu belge yazılırken çalıştırıldı):

| Yöntem | Recall@1 | Recall@5 | MRR |
|---|---|---|---|
| Sadece vektör | 0.788 | 0.962 | 0.857 |
| Sadece kelime (BM25) | 0.769 | 0.923 | 0.843 |
| **Hibrit (RRF)** | **0.904** | **0.962** | **0.933** |

Eşik sonrası: cevaplı sorularda yanlış red **0/52**; cevapsız sorularda doğru "bilmiyorum" yalnızca **2/5** (bkz. §14). Hibritin kaçırdıkları: "köpüşümü getirebilir miyim" (argo/yazım) ve "arkadaşım günü birlik gelebilir mi".
(Recall@k: doğru kayıt ilk k sonuçta mı; MRR: doğru sonucun sırasının tersinin ortalaması.)

Derin anlatım, kodu okuma sırası, chunk/eşik denemeleri: **[RAG_REHBERI.md](RAG_REHBERI.md)**.

---

## 8. Sesli asistan (özet)

* Ses **tarayıcı ↔ OpenAI** arasında WebRTC ile doğrudan akar; backend yalnızca (1) geçici anahtar üretir, (2) sideband WebSocket ile **araçları çalıştırır**, (3) dökümü kaydeder. Akış adım adım §5c'dedir.
* Model: Admin → Bot Ayarları → Sesli Asistan'dan seçilir; **varsayılan `gpt-realtime`** (`models.py:Settings.voice_model`, `voice/migrate.py`; sahibi bu varsayılanı korumayı seçti). İzinli değerler `gpt-realtime`, `gpt-realtime-2.1`, `gpt-realtime-mini` (`voice/instructions.py:ALLOWED_MODELS`); geçersiz değer `gpt-realtime`'a düşer.
* Panelden ayarlanabilenler: açık/kapalı, karşılama cümlesi, model, ses (varsayılan `marin`), **söz kesme hassasiyeti** (`semantic_vad` eagerness: low/medium/high), konuşma hızı (0.25–1.5), en uzun görüşme süresi (30–1800 sn, varsayılan 300), telaffuz sözlüğü (JSON). Değişiklik **bir sonraki görüşmede** geçerlidir.
* Türkçe doğallık: girdi transkripsiyonu `gpt-4o-transcribe` (`language: tr` + villa adlarını içeren ipucu metni); `semantic_vad` Türkçede cümle ortasında duraklayan konuşmacıyı daha az keser; araç sonuçlarında hazır okunuşlu `konusma` alanları (sayı/para/tarih/kod).
* Sesli sistem istemi yazılı botla **aynı DB kaynaklarını** (`bot.py:load_prompt_parts`) kullanır, üstüne konuşma üslubu ve geri-okuma kuralları ekler (`voice/instructions.py:build_voice_instructions`).
* Korumalar: IP başına dakikada 6 oturum (`routers/voice.py:_rate_limit`), aynı anda en fazla 8 görüşme (`service.MAX_CONCURRENT`), süre sınırı (istemci + sunucu `hangup`).

Ayrıntı, dosya tablosu, Türkçe konuşma katmanı fonksiyonları: **[SESLI_ASISTAN.md](SESLI_ASISTAN.md)**.

---

## 9. Admin paneli

`/admin/giris` → `admin`/`admin123` ile giriş (12 saatlik JWT, tarayıcıda `localStorage`'da; `routers/admin.py:login`). Menü: `pages/admin/AdminLayout.tsx`.

| Sayfa | Yol | İşletme sahibi burada ne yapar |
|---|---|---|
| **Panel** | `/admin` | Toplam/onaylı/bekleyen rezervasyon, onaylı ciro, yaklaşan girişler (`GET /api/admin/stats`). |
| **Chatbot Bilgi Bankası** | `/admin/bilgi-bankasi` | Bot için bilgi kayıtlarını ekler/düzenler/siler/pasif yapar; her kaydın modunu ("Her zaman bilinsin" / "Gerektiğinde aransın") ve indeks durumunu görür. |
| **RAG & Arama** | `/admin/rag` | Parça/indeks istatistikleri, "her zaman bilinen" token kullanımı (20.000 uyarı eşiği), **Tümünü yeniden indeksle**, **Arama Testi** (her sonucun vektör/kelime sırası ve skoru). |
| **Bot Ayarları** | `/admin/bot-ayarlari` | Tesis bilgileri (ad, telefon, saatler, harita), bot adı, karşılama mesajı, **ek talimatlar** (ton, yasaklar), sesli asistan ayarları. |
| **Sesli Görüşmeler** | `/admin/sesli-gorusmeler` | Son 200 görüşmenin listesi; tıklayınca döküm (kullanıcı/asistan/araç çağrıları, süre, oluşan rezervasyon kodları). |
| **Bot Test** | `/admin/bot-test` | Botu müşteri gibi dener; her turda yapılan RAG aramalarını `debug` olarak görür. Gerçek rezervasyon oluşturabilir. |
| **Villalar & Bungalovlar** | `/admin/bungalovlar` | Villa ekler/düzenler (fiyat, kapasite, olanaklar, görseller), pasif yapar; rezervasyonu olan villa silinemez (409), pasif yapılır. |
| **Rezervasyonlar** | `/admin/rezervasyonlar` | Rezervasyonları durumuna göre süzer, durumu elle değiştirir (örn. iptal). |

---

## 10. Veri modeli

Tablolar `backend/app/models.py` içindedir (SQLite; Alembic yok, sütun eklemek için `voice/migrate.py` gibi elle geçiş yazıldı).

| Tablo | Önemli alanlar |
|---|---|
| `bungalows` | `slug` (benzersiz), `name`, `capacity`, `bedrooms`, `size_m2`, `price_per_night`, `amenities_json`, `images_json`, `is_active` |
| `knowledge_entries` | `category`, `title`, `content`, `is_active`, `sort_order`, **`mode`** (`always`\|`search`), **`content_hash`** (son başarıyla indekslenenin özeti), **`index_status`** (`indexed`\|`pending`\|`error`\|`not_applicable`), `indexed_at`, `index_error`, `chunk_count` |
| `knowledge_chunks` (+ FTS5 `knowledge_fts`) | Parçalar: kayıt id'si, parça metni (bağlam başlığıyla), vektör (BLOB), embedding modeli, kelime indeksi için normalize metin. `rag/store.py:init_schema` ile **ham SQL** olarak oluşur (`models.py`'de yok). |
| `settings` | Tek satır: tesis bilgileri, `bot_name`, `bot_welcome_message`, `bot_extra_instructions`, **sesli asistan**: `voice_enabled/model/name/vad_eagerness/speed/max_session_seconds/greeting/lexicon_json` |
| `reservations` | `code` (BNG-XXXXXX), `bungalow_id`, misafir adı/e-posta/telefon, `check_in/check_out` (YYYY-MM-DD metin), `guests`, `nights`, `total_price`, `note`, `status`, **`source`** (`web`\|`chatbot`\|`voice`), `created_at` (30 dk kuralı bunu kullanır) |
| `payments` | `token` (benzersiz, `secrets.token_urlsafe`), `reservation_id`, `amount`, `status` (`initialized`\|`success`\|`failure`). Kart bilgisi **yok**. |
| `voice_sessions` | `session_id` (`vs_...`), `call_id`, `model`, `voice`, `status` (`created`\|`active`\|`ended`\|`error`), `started_at/ended_at`, `duration_seconds`, `transcript_json` (rol/metin/zaman/araç), `reservation_codes_json` |

Ayrı dosya: `chat_sessions.db` — Agents SDK'nın `SQLiteSession` tablosu (yazılı bot konuşma hafızası; bizim modelimiz değil).
Sesli oturumun **canlı** durumu (`VoiceRuntime`: kartlar, döküm, call_id) ayrıca bellekte tutulur (§14).

---

## 11. Güvenlik notları

**Bugün doğru olanlar:**

* `OPENAI_API_KEY` yalnızca `backend/.env` içindedir; `.env` ve `*.db` `backend/.gitignore`'dadır. Tarayıcı anahtarı hiç görmez.
* Sesli asistanda tarayıcıya **120 sn geçerli geçici anahtar** verilir (`SECRET_TTL_SECONDS`); talimat, araçlar, ses, VAD sunucuda sabitlenir ve sideband bunları bozulursa geri yükler.
* Admin uçları `Authorization: Bearer <JWT>` ister (`admin.py:require_admin`, HS256, 12 saat); giriş karşılaştırması `hmac.compare_digest` ile.
* Kart numarası saklanmaz, bot/sesli asistan kart bilgisi almaz.
* Sesli araç dispatcher'ı yalnızca bilinen araç adlarını çalıştırır ve argümanları fonksiyon imzasına göre süzer (`voice/tools.py:run_voice_tool`).

**Üretime çıkmadan önce mutlaka:**

| Konu | Şimdi | Yapılacak |
|---|---|---|
| Admin şifresi | `admin123` (varsayılan) | `.env`'de güçlü şifre; tercihen hash'li kullanıcı tablosu |
| `JWT_SECRET` | `change-me-in-production` | Uzun rastgele değer |
| CORS | `FRONTEND_URL` + localhost adresleri (`main.py`) | Yalnızca gerçek alan adı |
| Ödeme | **Sahte** iyzico (backend kartı görüyor) | Gerçek iyzico: kart bilgisi bizim sunucudan hiç geçmeyecek (iyzico'nun barındırdığı ödeme formu) + webhook ile onay |
| HTTPS | Yok (yerel) | Zorunlu; mikrofon da HTTPS ister |
| `/api/chat` | Kimliksiz, **hız sınırı yok** (her mesaj OpenAI maliyeti) | IP/oturum başına hız sınırı, bot koruması |
| Genel uçlar | `GET /api/reservations/{code}` kodu bilen herkese misafir adı/e-postası/telefonunu gösterir | Daha az bilgi döndürmek veya doğrulama |
| Sesli oturum durumu | Bellekte, tek süreç | Paylaşımlı depo (Redis) |
| Admin durum değişikliği | `PATCH .../reservations/{id}` her durumu müsaitlik denetimsiz kabul eder | Geçerli geçişler + çakışma kontrolü |

---

## 12. Maliyetler

Aşağıdakiler **tahmindir**; güncel fiyatlar OpenAI fiyat sayfasında değişebilir. Kesin hesap için orada kontrol edin. (`SESLI_ASISTAN.md` dakika başına fiyat vermez, yalnızca "mini ≈ üçte bir fiyat" der.)

| Kalem | Nasıl oluşur | Büyüklük |
|---|---|---|
| **Yazılı bot** | Her mesajda talimat (tesis bilgisi + 12 "always" kayıt + villa listesi, birkaç bin token) + konuşma geçmişi + araç turları, `gpt-4.1-mini` ile | Mesaj başına **küçük** (genelde bir kuruşun çok altı); en büyük kalem tekrarlanan talimat ve uzayan geçmiş |
| **Embeddings** | `text-embedding-3-small`; 154 parça bir kez, sonra her arama için yalnızca kısa soru. Hash sayesinde değişmeyen kayıt yeniden gömülmez | **İhmal edilebilir** |
| **Bağlam cümleleri** | Yalnızca >800 token'lık uzun dokümanlarda, parça başına 1 küçük model çağrısı (kayıt değişince) | Birkaç kuruş mertebesi, nadir |
| **Sesli asistan** | **Dakika başına** (giriş + çıkış sesi); en pahalı kalem. Üst sınır: görüşme süresi × dakika fiyatı | Kaba tahmin (ölçülmedi): `gpt-realtime` için 5 dakikalık tipik görüşme ≈ **0,20–0,40 $**, kötü durumda ≈ 0,75 $. `gpt-realtime-mini` ≈ üçte biri. Ayrıntı aşağıda. |

**Sesli maliyet nasıl hesaplanır** (fiyat sayfası, 1M token başına: ses girişi 32 $, önbellekten giriş 0,40 $, ses çıkışı 64 $; ses ≈ kullanıcı 10, asistan 20 token/saniye):
müşteri 2 dk konuşursa ≈ 1.200 token ≈ 0,04 $; asistan 2 dk konuşursa ≈ 2.400 token ≈ 0,15 $.
Asıl belirleyici **bağlam**: model her cevaptan önce talimatı (~3-4 bin token) ve o ana kadarki konuşmanın tamamını yeniden okur. Bu tekrar okumalar önbellekten gelirse ucuzdur (toplam ≈ 0,20-0,30 $); gelmezse 5 dakikalık görüşme 0,75 $'ı geçebilir.
Kesin rakam için: OpenAI her `response.done` olayında token kullanımını (önbellekli kısım dahil) bildirir; bu kaydedilip görüşme başına gerçek maliyet hesaplanabilir (henüz yapılmadı). Şimdilik OpenAI panelindeki kullanım sayfasına bakın.

Sesli maliyeti sınırlayanlar: `voice_max_session_seconds` (300 sn varsayılan), `gpt-realtime-mini`, 8 eşzamanlı görüşme sınırı, IP hız sınırı, panelden kapatma, kısa cevap kuralı (1-3 cümle).

---

## 13. Test ve doğrulama

| Ne | Komut (hepsi `backend/` içinden; Git Bash veya PowerShell) | Not |
|---|---|---|
| Birim testler | `.venv/Scripts/python.exe -m pytest` | `tests/test_turkish_speech.py`: Türkçe okunuş katmanı, **33 test** (son çalıştırmada hepsi geçti). OpenAI gerekmez. |
| RAG değerlendirmesi | `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m eval.rag_eval` (`-v`: ayrıntı) | 57 soru; indeks dolu olmalı, embedding için anahtar gerekir. PowerShell'de: `$env:PYTHONIOENCODING="utf-8"` |
| Sesli uçtan uca | `.venv/Scripts/python.exe scripts/voice_smoke_test.py` (`--audio`, `--model gpt-realtime-2.1`) | Mikrofonsuz: metin turlarıyla gerçek Realtime oturumu + gerçek araçlar. **Gerçek anahtar kullanır, ücretlidir**; test rezervasyonlarını sonunda iptal eder. |
| Frontend derleme | `cd frontend` → `npm run build` | `tsc --noEmit` (tip kontrolü) + `vite build`. |
| API'yi elle deneme | http://localhost:8000/docs | Swagger arayüzü. |

Otomatik testlerin kapsamadığı: sahici mikrofon yolu, WebRTC bağlantısı, ödeme/rezervasyon REST uçları (birim test yok), yazılı bot davranışı (bunun için **Bot Test** sayfası kullanılır).

---

## 14. Bilinen sınırlamalar & yapılacaklar

| Konu | Ayrıntı |
|---|---|
| **Zayıf "cevapsız" eşiği** | Cevapsız soruların yalnızca 2/5'i eşik altı kalıyor (yanlış red'i 0 tutmak için bilerek gevşek; `RAG_REHBERI.md` §4). Asıl "bilmiyorum" kararını model veriyor. *Fikir:* reranker (cross-encoder) + daha çok cevapsız eval sorusu. |
| **Mikrofon yolu otomatik test edilmedi** | `voice_smoke_test.py` metin/TTS ile sunucu yolunu doğrular; tarayıcı WebRTC + gerçek mikrofon yalnızca elle denenebilir. |
| **`bungai_fake_mic` geliştirme anahtarı** | `localStorage.bungai_fake_mic='1'` sessiz yapay mikrofon kullanır (`useVoiceAssistant.ts:start`). Üretimden önce **kaldırılmalı**. |
| **Hiç bağlanmayan sesli oturumlar** | `POST /voice/session` sonrası `attach` gelmezse DB'deki satır sonsuza dek `created` kalır (bellek kaydı bir saat sonra temizlenir ama DB satırı güncellenmez); admin listesinde görünür. |
| **Sesli oturum durumu bellekte** | `voice/service.py:_SESSIONS` tek süreç; çok sunuculu kurulumda Redis gibi paylaşımlı depo gerekir. SQLite de tek sunucu içindir. |
| **Mock ödeme** | Sahte iyzico kuralları (`services/payments.py`); gerçek iyzico entegrasyonu (barındırılan ödeme formu + webhook) yapılmadı. |
| **Sahibi için ⭐/📖 rehberlik (planlı)** | Bilgi bankası ekranında hangi bilginin "her zaman" hangisinin "aranır" olacağını sade dille anlatan arayüz henüz yok (şimdi yalnızca açıklama metni ve uzun "always" için uyarı var: `Knowledge.tsx`). |
| **Otomatik ön-getirme (opsiyonel RAG)** | Her mesajda aramayı modele bırakmak yerine sistemin kendisinin önceden araması tartışıldı, ertelendi; şimdi arama modelin inisiyatifinde. |
| **Arka plan indeksleme süreç içi** | Sunucu kapanırsa yarım kalan kayıt `pending` kalır; açılışta tamamlanır. |
| **Hız sınırı yalnızca sesli uçta** | `/api/chat` ve diğer genel uçlarda yok (bkz. §11). |
| **Eval seti küçük** | 57 soru; gerçek misafir sorularıyla büyütülmeli. |
| **Basit Türkçe stemmer** | Aşırı/yetersiz kırpma olabilir (vektör telafi eder); Zemberek/Snowball-tr adayı. |
| **Test kapsamı dar** | Yalnızca Türkçe konuşma katmanı için birim test var; servis/ödeme kuralları için yok. |

---

## 15. Doküman haritası

| Şunu öğrenmek istiyorsanız | Okuyun |
|---|---|
| Sistemin bütünü, hangi dosya ne iş yapar | **bu README** |
| Bir API ucunun tam şeması, mock ödeme kuralları, JSON modelleri | [CONTRACT.md](CONTRACT.md) |
| RAG'i satır satır, ölçerek öğrenmek (chunking, RRF, eşik, eval) | [RAG_REHBERI.md](RAG_REHBERI.md) |
| Sesli asistanın mimarisi, Türkçe konuşma katmanı, ayarlar, test | [SESLI_ASISTAN.md](SESLI_ASISTAN.md) |
| Backend kurulumu, `.env`, dosya yapısı | [backend/README.md](backend/README.md) |
| Frontend sayfaları/rotaları, `npm` komutları | [frontend/README.md](frontend/README.md) |
| Kodu hangi sırayla okumalı | Önce `backend/app/main.py` → `services/` → `agent/` → `rag/` (RAG_REHBERI sırası) → `voice/` (SESLI_ASISTAN); frontend'de `App.tsx` → `api/client.ts` → `components/ChatPanel.tsx` → `lib/useVoiceAssistant.ts` |

**Doküman çelişkisi olursa kod doğrudur**; dokümanı düzeltin.

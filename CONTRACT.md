# BUNGAi — Ortak API Sözleşmesi

Bungalov tatil köyü web sitesi. Backend: FastAPI (`backend/`, port 8000). Frontend: React + Vite + TypeScript + Tailwind (`frontend/`, port 5173, Vite proxy `/api` → `http://localhost:8000`).
Tüm kullanıcıya görünen metinler **Türkçe**. Tarihler `YYYY-MM-DD`. Para birimi TRY, tutarlar `number` (kuruş değil, TL, 2 ondalık).

## Veri modelleri (JSON)

```
Bungalow {
  id: int, slug: str, name: str, short_description: str, description: str,
  capacity: int, bedrooms: int, size_m2: int, price_per_night: number,
  amenities: str[], images: str[]   // URL listesi (placeholder: unsplash URL'leri)
  is_active: bool
}

KnowledgeEntry {            // chatbot bilgi bankası, admin düzenler
  id: int, category: str,   // örn: "Genel", "Konaklama", "Yeme-İçme", "Aktiviteler", "Politikalar", "Ulaşım", "SSS"
  title: str, content: str, is_active: bool, sort_order: int, updated_at: str(ISO),
  mode: "always" | "search",   // always = her mesajda system prompt'ta; search = RAG ile gerektiğinde aranır
  index_status: "indexed" | "pending" | "error" | "not_applicable",  // salt okunur; always kayıtlar "not_applicable"
  chunk_count: int             // salt okunur
}

Settings {                  // tek satır
  resort_name: str, tagline: str, phone: str, email: str, address: str,
  check_in_time: str, check_out_time: str, map_embed_url: str,
  bot_name: str, bot_welcome_message: str,
  bot_extra_instructions: str,  // işletme sahibinin bota ek talimatları (ton, yasaklar vb.)
  // --- Sesli asistan (public'e yalnızca voice_enabled, voice_greeting, voice_max_session_seconds çıkar) ---
  voice_enabled: bool,                       // varsayılan true
  voice_greeting: str,                       // asistanın ilk söylediği söz
  voice_max_session_seconds: int,            // varsayılan 300 (30-1800); istemci + sunucu bu sürede kapatır
  voice_model: "gpt-realtime" | "gpt-realtime-2.1" | "gpt-realtime-mini",   // varsayılan gpt-realtime
  voice_name: str,                           // marin (varsayılan), cedar, coral, sage, shimmer, verse, ballad, ash, alloy, echo
  voice_vad_eagerness: "low" | "medium" | "high",   // varsayılan medium
  voice_speed: number,                       // 0.25-1.5, varsayılan 1.0
  voice_lexicon_json: str                    // JSON {"kelime": "okunuş"}: telaffuz sözlüğü (yerleşik sözlüğe ek)
}

Reservation {
  id: int, code: str,       // örn "BNG-7K2Q9X"
  bungalow_id: int, bungalow_name: str,
  guest_name: str, guest_email: str, guest_phone: str,
  check_in: str, check_out: str, guests: int, nights: int,
  total_price: number, note: str | null,
  status: "pending_payment" | "confirmed" | "cancelled" | "payment_failed",
  source: "web" | "chatbot" | "voice", created_at: str(ISO)
}

Payment {
  token: str, reservation_code: str, amount: number,
  status: "initialized" | "success" | "failure", created_at: str
}
```

## Public endpoint'ler

| Method | Path | Body / Query | Yanıt |
|---|---|---|---|
| GET | `/api/settings/public` | – | Settings (bot_extra_instructions HARİÇ) |
| GET | `/api/bungalows` | – | Bungalow[] (sadece aktifler) |
| GET | `/api/bungalows/{slug}` | – | Bungalow |
| GET | `/api/availability` | `?bungalow_id=&check_in=&check_out=` | `{available: bool, nights: int, total_price: number}` |
| GET | `/api/availability/calendar` | `?bungalow_id=&month=YYYY-MM` | `{booked_dates: str[]}` |
| POST | `/api/reservations` | `{bungalow_id, guest_name, guest_email, guest_phone, check_in, check_out, guests, note?}` | `Reservation` (status=pending_payment, source=web). Müsait değilse 409 `{detail}` |
| GET | `/api/reservations/{code}` | – | Reservation |
| POST | `/api/payments/init` | `{reservation_code}` | `{token, amount, payment_page_url}` — `payment_page_url` = `/odeme/{token}` (frontend route) |
| GET | `/api/payments/{token}` | – | `{token, amount, status, reservation: Reservation}` |
| POST | `/api/payments/{token}/complete` | `{card_holder, card_number, expire_month, expire_year, cvc}` | `{status: "success"\|"failure", message, reservation: Reservation}` |
| POST | `/api/chat` | `{session_id?: str, message: str}` | `{session_id: str, reply: str, actions: ChatAction[]}` |

`ChatAction = {type: "payment_link", reservation_code: str, url: str, amount: number} | {type: "reservation_summary", reservation: Reservation}`

### Sesli asistan (OpenAI Realtime, WebRTC + yan kanal) — ayrıntı: SESLI_ASISTAN.md

| Method | Path | Body / Query | Yanıt |
|---|---|---|---|
| POST | `/api/voice/session` | – | `{client_secret, expires_at, model, session_id, max_seconds, greeting}`. `client_secret` = OpenAI geçici anahtarı (120 sn içinde kullanılmalı). Talimat/araç/VAD/ses sunucuda sabitlenir. 403 `voice_enabled=false`, 429 hız/eşzamanlılık sınırı |
| POST | `/api/voice/session/{session_id}/attach` | `{call_id}` | `{ok: true}` — tarayıcı `POST https://api.openai.com/v1/realtime/calls` yanıtının `Location` başlığındaki `rtc_...` kimliğini bildirir; backend aynı çağrıya WebSocket (sideband) açıp araçları çalıştırır |
| GET | `/api/voice/session/{session_id}/actions` | `?after=N` | `{actions: ChatAction[], next: int, ended: bool}` — sesli araçlardan doğan kartlar (`reservation_summary`, `payment_link`); yoklama ile çekilir |
| POST | `/api/voice/session/{session_id}/end` | – | `{ok: true}` — çağrıyı kapatır, dökümü kaydeder |
| GET | `/api/admin/voice/sessions` | – | `VoiceSessionListItem[]` (Bearer) |
| GET | `/api/admin/voice/sessions/{id}` | – | `VoiceSessionDetail` (Bearer) |

```
VoiceSessionListItem { id, session_id, model, voice, status: "created"|"active"|"ended"|"error", started_at, ended_at|null,
                       duration_seconds, turn_count, first_user_text, reservation_codes: str[] }
VoiceSessionDetail   = VoiceSessionListItem + { call_id|null, transcript: VoiceTurn[] }
VoiceTurn { role: "user"|"assistant"|"tool", text, ts, typed?: bool, name?, arguments?, output?, ms? }   // tool: araç çağrısı
```
Sesli araç çıktılarına yalnızca modele giden `konusma` / `*_konusma` alanları eklenir (Türkçe okunuşlu sayı, tarih, para, kod); REST yanıtlarında görünmez.

### Mock iyzico kuralları (iyzico sandbox benzeri test kartları)
- `5528790000000008` → başarılı
- `4766620000000001` → başarılı
- `4111111111111129` → başarısız ("Yetersiz bakiye")
- `4129111111111111` → başarısız ("Kart limiti aşıldı / işlem reddedildi")
- Diğer Luhn-geçerli kartlar → başarılı; Luhn-geçersiz → başarısız ("Geçersiz kart numarası")
- Başarılı ödeme → reservation.status = confirmed. Başarısız → payment_failed (yeniden ödeme denenebilir; yeni init yapılabilir).
- `pending_payment` rezervasyonlar 30 dk içinde ödenmezse müsaitlik hesabında yok sayılır (tarihleri bloklamaz).
- Müsaitlik: `confirmed` + 30 dk'dan yeni `pending_payment` rezervasyonlar tarih bloklar. check_out günü bloklanmaz.

## Admin endpoint'leri (Bearer JWT)

| Method | Path | Not |
|---|---|---|
| POST | `/api/admin/login` | `{username, password}` → `{access_token, token_type:"bearer"}`. Varsayılan: `admin` / `admin123` (.env ile değiştirilebilir) |
| GET | `/api/admin/me` | `{username}` |
| GET/PUT | `/api/admin/settings` | Settings tamamı |
| GET/POST | `/api/admin/knowledge` | liste (tümü, pasifler dahil) / oluştur |
| PUT/DELETE | `/api/admin/knowledge/{id}` | |
| GET/POST | `/api/admin/bungalows` | tümü (pasifler dahil) / oluştur |
| PUT/DELETE | `/api/admin/bungalows/{id}` | |
| GET | `/api/admin/reservations` | `?status=` opsiyonel, yeniden eskiye |
| PATCH | `/api/admin/reservations/{id}` | `{status}` |
| GET | `/api/admin/stats` | `{total_reservations, confirmed, pending, revenue_confirmed, upcoming_checkins: Reservation[]}` |
| POST | `/api/admin/chat/test` | `/api/chat` ile aynı + yanıtta ek alan `debug: {searches: SearchTrace[]}` — botun o turda yaptığı her RAG araması |
| GET | `/api/admin/rag/stats` | `RagStats` |
| POST | `/api/admin/rag/reindex` | `{force?: bool}` → `{started: true}`; tüm search kayıtlarını (force=false ise sadece değişenleri) arka planda indeksler |
| POST | `/api/admin/rag/search` | `{query: str, top_k?: int}` → `SearchTrace` (arama testi / hata ayıklama) |

```
RagStats {
  always_entries: int, always_tokens: int, always_token_limit: int,   // limit: 20000 (uyarı eşiği)
  search_entries: int, chunks: int, indexed_entries: int, pending_entries: int, error_entries: int,
  embedding_model: str, embeddings_enabled: bool,   // API anahtarı yoksa false → sadece kelime araması
  last_indexed_at: str | null
}
SearchTrace {
  query: str, normalized_query: str,
  results: SearchHit[],          // final, birleştirilmiş sıralama (RRF), eşik sonrası
  below_threshold: bool          // hiçbir sonuç güven eşiğini geçmediyse true
}
SearchHit {
  entry_id: int, entry_title: str, category: str, chunk_index: int, text: str,
  vector_score: number | null, keyword_score: number | null, vector_rank: int | null, keyword_rank: int | null,
  fused_score: number
}
```

Hatalar: `{detail: str}` (FastAPI standardı), Türkçe mesaj.

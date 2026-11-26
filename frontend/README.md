# BUNGAi Frontend

Villa/bungalov tatil köyü için React 19 + Vite + TypeScript + Tailwind CSS (v4) arayüzü. Sistemin bütünü için: [../README.md](../README.md).

## Çalıştırma

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

Backend (FastAPI) `http://localhost:8000` adresinde çalışmalıdır; Vite `/api` isteklerini otomatik olarak oraya yönlendirir (`vite.config.ts`).

```bash
npm run build      # tip kontrolü (tsc --noEmit) + üretim derlemesi (dist/)
npm run preview
```

## Sayfalar (`src/App.tsx`)

| Yol | Açıklama |
|---|---|
| `/` | Ana sayfa (hero + müsaitlik arama, bungalovlar, deneyimler, yorumlar, harita) |
| `/bungalovlar`, `/bungalovlar/:slug` | Liste, detay, müsaitlik takvimi, rezervasyon formu |
| `/odeme/:token` | Demo iyzico ödeme sayfası (test kartları sayfada listelenir) |
| `/rezervasyon/:code` | Rezervasyon durumu / ödeme tekrar deneme |
| `/admin/giris` | Yönetici girişi (varsayılan `admin` / `admin123`) |
| `/admin` | Panel (istatistikler) |
| `/admin/bilgi-bankasi` | Chatbot Bilgi Bankası (kayıtlar, "Her zaman bilinsin" / "Gerektiğinde aransın" modu, indeks durumu) |
| `/admin/rag` | RAG & Arama (indeks istatistikleri, yeniden indeksleme, arama testi) |
| `/admin/bot-ayarlari` | Bot Ayarları (tesis bilgileri, bot talimatları, sesli asistan ayarları) |
| `/admin/sesli-gorusmeler` | Sesli görüşme listesi ve dökümü |
| `/admin/bot-test` | Bot Test (botu dene, RAG arama izini gör) |
| `/admin/bungalovlar`, `/admin/rezervasyonlar` | Villa ve rezervasyon yönetimi |

Ödeme sayfası dışındaki herkese açık sayfalarda sağ altta sohbet balonu bulunur (`components/ChatWidget.tsx`): yazılı sohbet ve **Sesli** düğmesi (`VoicePanel`).
Sohbet oturum kimliği `localStorage`'da (`bungai_chat_session`), admin jetonu `bungai_admin_token` anahtarında saklanır.

## Yapı

- `src/api/` — tiplenmiş API istemcisi (`client.ts`) ve tipler (`types.ts`, `CONTRACT.md` ile birebir)
- `src/components/` — `ChatWidget`/`ChatPanel` (yazılı bot; `payment_link` için "Ödemeye Geç" ve rezervasyon özet kartları), `VoicePanel` (sesli panel), `Calendar`, `Layout`, ortak UI
- `src/lib/useVoiceAssistant.ts` — sesli asistan WebRTC istemcisi: geçici anahtar al, SDP'yi OpenAI'ye yolla, `call_id`'yi backend'e bildir, kartları 1 sn'de bir yokla, süre sayacı
- `src/pages/` — herkese açık sayfalar; `src/pages/admin/` — yönetim paneli
- `src/content/images.ts` — statik görsel URL'leri (Unsplash)

Geliştirme notu: tarayıcı konsolunda `localStorage.bungai_fake_mic='1'` sessiz yapay mikrofonla sesli asistanı denemeye yarar; üretimden önce kaldırılmalıdır.

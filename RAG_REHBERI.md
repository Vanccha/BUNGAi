# BUNGAi RAG Rehberi - Kodu Okuyarak RAG Öğrenin

Bu rehber, `backend/app/rag/` altındaki "hibrit RAG" kodunu **okuyarak** öğrenmeniz için yazıldı.
Hiçbir çerçeve (LangChain, LlamaIndex vb.) kullanılmadı; mekanik her satırda görünür. Rehberdeki
sayılar, bu depodaki gerçek bilgi bankası (132 kayıt, 154 parça) ve `backend/eval/` çalıştırmasından alınmıştır.

---

## 1. RAG nedir, neden?

Chatbotun tesis hakkında doğru konuşması için bilgiye ihtiyacı var (menü fiyatları, spa, kurallar...).
Üç yol var:

| Yol | Nasıl | Sorun |
|---|---|---|
| **Prompt'a doldurmak** | Tüm bilgiyi system prompt'a koymak | 132 kayıt ≈ 50 bin+ token. Her mesajda para öder, yavaşlar; model uzun metinde ortadaki bilgiyi kaçırır. Yine de **kısa, kritik bilgiler için en iyisi** (bizde `mode="always"`). |
| **Fine-tuning** | Modeli bilgiyle eğitmek | Fiyat değişince yeniden eğitim; bilginin nereden geldiği görünmez; yanlış bilgiyi "sökmek" zor. Bilgi için değil, *üslup/format* için uygundur. |
| **RAG** (Retrieval-Augmented Generation) | Soru gelince bilgi bankasında **ilgili parçaları ara**, yalnızca onları modele ver | Arama kalitesi her şeydir: yanlış parça gelirse model doğru cevap veremez. |

Bizde ikisi birlikte: **12 kritik kayıt** (giriş-çıkış, iptal, iletişim...) her mesajda prompt'ta durur (`always`),
**120 kayıt** (menü, spa, kurallar...) indekslenir ve gerektiğinde aranır (`search`).

---

## 2. İki boru hattı

RAG'in iki ayrı yolculuğu vardır. Karıştırmayın:

### A) İndeksleme (admin bir kaydı kaydedince - "yazma yolu")

```
 Admin kaydı kaydeder (POST/PUT /api/admin/knowledge)
          │
          ▼
  mode = always? ──evet──► parçaları sil, durum "not_applicable" (prompt'ta duracak)
          │hayır
          ▼
  hash(kategori|başlık|içerik|mod) eskisiyle aynı mı? ──evet──► HİÇBİR ŞEY YAPMA (artımlı indeksleme)
          │hayır   (durum = "pending"; arka plan görevi başlar)
          ▼
  ┌─ chunking.py     parçala: ~450 token, %15 örtüşme, "Kategori > Başlık > Alt başlık" başlığı
  ├─ contextual.py   (yalnızca uzun kayıtlar) her parça için "dokümandaki yeri" cümlesi (LLM)
  ├─ embeddings.py   embed_text ──► 1536 sayılık vektör (text-embedding-3-small)
  ├─ normalize.py    metni kök/aksansız hale getir (kelime indeksi için)
  └─ store.py        knowledge_chunks (metin + vektör BLOB) + knowledge_fts (FTS5 / BM25)
          │
          ▼
  durum "indexed" (hata olursa "error", kelime araması yine çalışır)
```

### B) Getirme (misafir soru sorunca - "okuma yolu")

```
 Misafir: "fırın sütlaç fiyatı"
          │
          ▼
  Bot, always bölümünde cevap yok → search_knowledge("fırın sütlaç fiyat") aracını çağırır
          │
          ▼  search.py:search()
  ┌────────────────────────────┐    ┌──────────────────────────────┐
  │ (a) VEKTÖR                 │    │ (b) KELİME (BM25)            │
  │ sorguyu embed et           │    │ sorguyu normalize et         │
  │ matris @ vektör → kosinüs  │    │ FTS5: "fir" OR "sutlac" ...  │
  │ en iyi 20 parça (sıralı)   │    │ en iyi 20 parça (sıralı)     │
  └─────────────┬──────────────┘    └───────────────┬──────────────┘
                └───────────► (c) RRF ◄─────────────┘   skor değil SIRA birleştirilir
                                  │
                      (d) komşu parçaları birleştir
                                  │
                 (e) güven eşiği: cos >= 0.38 VEYA bm25 >= 10 ?
                       │hayır (hiçbiri geçemedi)        │evet
                       ▼                                ▼
              below_threshold = true        en iyi 4 parça bota gider
              bot: "bilmiyorum, arayın"      bot: yalnızca bu parçalara dayanarak cevaplar
```

---

## 3. "Kodu bu sırayla oku"

Her dosyanın en üstündeki Türkçe docstring, o adımın **ne**, **neden** ve **diğerleriyle nasıl bağlandığını**
anlatır. Sırayla okuyun:

| # | Dosya : fonksiyon | Ne öğretir |
|---|---|---|
| 0 | `app/seed_data/knowledge_*.py` | Veri: 12 `always` + 120 `search` kayıt, 11 uzun doküman (başlıklar `## `) |
| 1 | `app/rag/normalize.py : turkish_lower, fold_diacritics, stem, normalize_tokens` | Türkçe'ye özgü sorunlar: `İ/I`, aksan katlama, ek kırpma. Takaslar yorumlarda. |
| 2 | `app/rag/chunking.py : chunk_entry, parse_blocks` | Neden parçalıyoruz; başlık/paragraf/liste blokları; örtüşme; bağlam başlığı |
| 3 | `app/rag/contextual.py : generate_contexts` | Anthropic'in "contextual retrieval" fikri |
| 4 | `app/rag/embeddings.py : embed_texts` | Vektör nedir, neden normalize ediyoruz (kosinüs = nokta çarpımı) |
| 5 | `app/rag/store.py : insert_chunks, load_vector_index, keyword_search` | SQLite + FTS5 + numpy yeterli mi? Ne zaman değişmeli? |
| 6 | `app/rag/indexer.py : compute_hash, index_entry, mark_pending_if_changed, reindex_all` | Artımlı indeksleme, durum makinesi |
| 7 | `app/rag/search.py : search, reciprocal_rank_fusion, passes_threshold` | Hibrit arama, RRF, birleştirme, eşik |
| 8 | `app/agent/tools.py : search_knowledge` | Aramayı bota "araç" olarak verme; `ctx.searches` ile iz kaydı |
| 9 | `app/agent/bot.py : build_always_section, build_instructions` | `always` kayıtlarının prompt'a girişi, "önce ara" kuralları |
| 10 | `app/routers/admin.py : create/update_knowledge, rag_stats, rag_reindex, rag_search, chat_test` | Admin tarafı + `debug.searches` |
| 11 | `eval/rag_eval.py`, `eval/questions.json` | Ölçmeden ayarlanmaz |

### 3.1 Bir kayıt boru hattında (gerçek örnek)

Kayıt: **Yeme-İçme > "Restoran ve Bar Menüsü (fiyatlar ve alerjenler)"** (~2.350 token'lık uzun doküman).

1. **Parçalama** (`chunk_entry`): doküman `## Tatlılar`, `## Kokteyller...` gibi başlıklara ve `- ` liste bloklarına
   ayrılır; 7 parça çıkar (417, 397, 309, 341, 332, 283, 160 token). 5. parçanın (index 4) görünen metni:
   ```
   Yeme-İçme > Restoran ve Bar Menüsü (fiyatlar ve alerjenler) > Tatlılar / Kokteyller ve alkollü içecekler
   - Fırın sütlaç - 190 TL (S)
   - Kabak tatlısı (cevizli, kaymaklı) - 210 TL (K,S)
   ...
   ```
   İlk satır **bağlam başlığı**dır. Parça tek başına okunsa bile neyin parçası olduğu belli.
2. **Bağlamsal getirme** (`generate_contexts`): doküman > 800 token olduğu için model her parça için bir cümle yazar:
   > "Bungai Villa & Bungalov Resort Restoran ve Bar Menüsü dokümanında, tatlılar ile kokteyller ve alkollü
   > içecekler bölümüne ait fiyatlar ve alerjen bilgileri yer almaktadır."

   Bu cümle yalnızca `embed_text`e (indekslenen metne) eklenir; bota gösterilen `text`e eklenmez.
3. **Embedding**: `embed_text` → 1536 float32 sayı, uzunluğu 1.0'a normalize (`[-0.0117, -0.0085, -0.0055, ...]`).
   `knowledge_chunks.embedding` sütununa BLOB olarak, `embedding_model="text-embedding-3-small"` ile yazılır.
4. **Normalize** (kelime indeksi için): başlık → `yeme icme restoran bar menu fiyat alerjen tat kokteyl alkol icecek`;
   gövde → `bung vill bungalov resort restoran bar menu dokum tat ... fir sutlac 190 tl s kabak tat ceviz kayma...`
   (kökler kırpılmış: `tatlılar → tat`, `fırın → fir`; aksanlar katlanmış). Bu metin `knowledge_fts` tablosuna gider.
5. **Hash**: `sha256(sürüm|kategori|başlık|içerik|mod)` `KnowledgeEntry.content_hash`'e yazılır → bir sonraki kayıtta
   değişmediyse bu 7 parça için embedding/LLM çağrısı **hiç yapılmaz**.

### 3.2 Bir soru boru hattında (gerçek sayılarla)

Soru: **"fırın sütlaç fiyatı"**

1. **Normalize**: `fir sutlac fiyat` (`fırın→fir`, `sütlaç→sutlac`, `fiyatı→fiyat`).
2. **Vektör**: sorgu embed edilir, tüm parça matrisiyle kosinüs hesaplanır. Menü parçası #4 **1. sırada, cos = 0.34**.
   (Dikkat: kısa sorgu ile uzun menü parçası arasındaki benzerlik düşüktür; bu yüzden tek başına vektöre güvenmiyoruz.)
3. **BM25**: FTS5 sorgusu `"fir" OR "fir"* OR "sutlac" OR "sutlac"* OR "fiyat" OR "fiyat"*`... Aynı parça **1. sırada, bm25 = 12.8**.
4. **RRF** (k=60): `1/(60+1) + 1/(60+1) = 0.01639 + 0.01639 = 0.0328`. İki yöntem de 1. dediği için en yüksek skor.
5. **Eşik**: cos 0.34 < 0.38 ama bm25 12.8 ≥ 10 → **geçer**. (Vektör tek başına kalsaydı bu cevaplı soru "bilmiyorum"a düşerdi;
   hibrit bunu kurtarır. Eval'deki yanlış-red sayımızın 0 olmasının nedeni budur.)
6. **Bot**: `search_knowledge` sonucu bota gider, bot "Fırın sütlaç 190 TL'dir" der. Misafir arama yapıldığını görmez.

RRF'nin iki yöntemin **anlaşmazlığını** nasıl çözdüğüne bir örnek (soru: "bitcoin ile ödeme kabul ediyor musunuz"):

| Parça | Vektör sırası | BM25 sırası | RRF |
|---|---|---|---|
| Döviz ve nakit ödeme | 2 | 1 | 1/62 + 1/61 = **0.0325** |
| Havale ve EFT ile ödeme | 1 | 4 | 1/61 + 1/64 = **0.0320** |

Vektörde 1. olan, kelimede 4. olduğu için 2. sıraya düştü. Skorların ölçeği farklı (0.5 ile 15) ama sıralar karşılaştırılabilir.

Sınır örneği: **"köpüşümü getirebilir miyim"** → normalize `kopusum getirebilir`; kelime araması hiçbir şey bulamaz,
vektör "Spa hediye çeki"ni öne çıkarır (cos 0.43). Yazım yanlışı + argo. Çözüm bot tarafındadır: model sorguyu
`search_knowledge("evcil hayvan köpek")` diye yeniden yazar (canlı testlerde böyle yapıyor). Bu, RAG'de "sorgu yeniden yazma"nın
(query rewriting) neden değerli olduğunu gösterir.

### 3.3 `always` mı `search` mı?

- **always**: kısa, **her konuşmada** gerekebilecek, yanlış olması pahalı bilgiler: giriş/çıkış saati, iptal politikası,
  iletişim, adres, ödeme yöntemleri, evcil hayvan özeti, minimum konaklama, çocuk özeti, depozito, fiyat özeti.
  `bot.py:build_always_section` bunları prompt'a koyar (şu an 12 kayıt ≈ 1.200 token; uyarı eşiği 20.000).
  Avantaj: arama hatası riski yok. Dezavantaj: her mesajda token maliyeti.
- **search**: uzun/detay bilgi (menü, spa, kurallar, program). `indexer.py` parçalar ve indeksler; bot
  `search_knowledge` ile arar. Avantaj: sınırsız büyüyebilir. Dezavantaj: arama kaçırabilir.
- Admin bir kaydın modunu değiştirince: `always→search` hash değişir (mod hash'e dahil) → indekslenir;
  `search→always` parçalar silinir ve kayıt prompt'ta görünür (`/api/admin/rag/stats` `always_entries/always_tokens` artar).
- Genel kural: **önce `search` ile başla; "bot bunu hep bilmeli" dediğin kısa şeyi `always` yap.**

### 3.4 Artımlı indeksleme (hash)

`indexer.py:compute_hash` → `sha256(sürüm|kategori|başlık|içerik|mod)`.

- Admin bir kaydı kaydeder → `mark_pending_if_changed`: hash farklıysa `index_status="pending"`, arka planda `index_entry`.
- Sadece `sort_order` ya da `is_active` değiştiyse hash aynıdır → **yeniden indekslenmez** (`PUT` sonrası durum `indexed` kalır).
- Pasif yapılan kaydın parçaları silinmez; arama sorgusu `is_active=1` ile süzer (geri açınca bedava).
- Sürüm alanı (`PIPELINE_VERSION`) parça boyutu ayarlarını içerir: chunk ayarını değiştirirseniz bir sonraki açılışta/`reindex` ile hepsi yeniden kurulur.
- Sunucu yeniden başlayınca `reindex_all(force=False)` çalışır; değişmeyen kayıtlar `skipped` olur (gerçekten test edildi: yeniden başlatmada 0 API çağrısı).
- Embedding API'si hata verirse: parçalar+FTS yine yazılır (kelime araması çalışır), durum `error`, hash kaydedilmez → sonraki denemede yeniden kurulur.
- API anahtarı yoksa: `embeddings_enabled=false`, sadece kelime araması.

---

## 4. Değerlendirme (eval)

```bash
cd backend
.venv/Scripts/python.exe -m eval.rag_eval        # özet
.venv/Scripts/python.exe -m eval.rag_eval -v     # her soru için ilk 3 sonuç
```

`eval/questions.json`: 52 cevaplı + 5 cevapsız gerçekçi soru ("köpüşümü getirebilir miyim", "akşam yemeği kaçta", "havaalanından nasıl gelirim"...),
her biri için kabul edilen kayıt başlıkları.

**Metrikler**

- **Recall@k**: doğru kayıt ilk k sonuçta mı? (Recall@1: ilk sonuç doğru; Recall@5: ilk 5'te.)
- **MRR**: ilk doğru sonucun sırasının tersinin ortalaması (1., 2., 3. → 1, 0.5, 0.33).
- **Cevapsız doğruluğu**: cevabı olmayan soruda `below_threshold=true` oranı. **Yanlış red**: cevaplı soruda yanlışlıkla `below_threshold` oranı.

**Son sonuçlar** (eşik uygulanmadan sıralama kalitesi, 52 cevaplı soru):

| Yöntem | Recall@1 | Recall@5 | MRR |
|---|---|---|---|
| Sadece vektör | 0.788 | 0.962 | 0.857 |
| Sadece kelime (BM25) | 0.769 | 0.923 | 0.843 |
| **Hibrit (RRF)** | **0.904** | **0.962** | **0.933** |

Hibrit, 1. sıra doğruluğunu ~12 puan artırır: iki yöntemin hataları farklı olduğu için birleşince birbirini düzeltir.
Kaçırılanlar (ikisi de 5'te yok): "köpüşümü getirebilir miyim" (argo/yazım), "arkadaşım günü birlik gelebilir mi" ("günübirlik" ayrı yazılmış).

**Chunk boyutu denemesi** (hepsi hibrit): 300 token → R@1 0.827 / MRR 0.894; **450 → 0.904 / 0.933**; 600 → 0.808 / 0.885.
Küçük parçalar bağlamı koparır, büyük parçalar vektörü "bulandırır". (52 soruluk sette ±0.02 fark gürültüdür; bağlamsal cümleler LLM çıktısı olduğundan
tekrar indekslemede küçük oynama olur.)

**Eşik ayarı** (`search.py`: `VECTOR_MIN_COSINE=0.38`, `KEYWORD_MIN_SCORE=10`). Cevaplı soruların en iyi kosinüsü 0.34-0.72 (medyan 0.56),
cevapsızlarınki 0.21-0.51. **İki dağılım örtüşüyor**: text-embedding-3-small'da alakasız metinler bile ~0.3-0.5 benzerlik verir.
Süpürme (satır: kosinüs eşiği, hücre: doğru-"bilmiyorum" / yanlış-red, BM25 eşiği 10):

| cos eşiği | 0.30 | 0.35 | **0.38** | 0.40 | 0.45 |
|---|---|---|---|---|---|
| cevapsız doğru (/5) / yanlış red (/52) | 1/0 | 1/0 | **2/0** | 2/1 | 2/3 |

Yanlış red'i 0'da tutan en yüksek eşiği seçtik: sonuç **cevapsızların 2/5'i** eşik altı; "bitcoin", "uzay bileti", "hava durumu" sorularında
ilgili-gibi görünen parçalar geçer. Bu kasıtlıdır: eşik **kaba bir filtredir**; asıl "bilmiyorum" kararını, "sonuçlarda olmayan şeyi uydurma" talimatı alan
model verir (canlı testte bitcoin sorusuna "kabul edilmiyor, ödeme yöntemleri şunlar" dedi; helikopter pisti sorusu eşik altı kaldı ve bot telefon verdi).
Daha iyi ayrım için: cevapsız soru sayısını artırın, bir reranker ekleyin (bkz. §6).

### Nasıl ayar yapılır?
1. `eval/rag_eval.py`'yi çalıştırın, ana sayıları not edin.
2. Tek bir şeyi değiştirin: `chunking.py` (`CHUNK_MAX_TOKENS`, `MIN_CHUNK_TOKENS`, `OVERLAP_RATIO`), `search.py` (`RRF_K`, `CANDIDATES_PER_RETRIEVER`, eşikler),
   `normalize.py` (stopword/ek listesi).
3. Parça ayarını değiştirdiyseniz yeniden indeksleyin: `POST /api/admin/rag/reindex {"force": true}` (ya da açılışta otomatik; sürüm hash'i değişti).
4. Eval'i tekrar çalıştırın; kötüleştiyse geri alın. **Sezgiyle değil sayıyla karar verin.**
- **k (RRF)**: 60 standarttır; küçültürseniz en üstteki sıralar daha baskın olur. Bu veride fark ihmal edilebilir.
- **Eşik**: yanlış red ↔ yanlış kabul dengesi. Hedefiniz "asla yanlışlıkla bilmiyorum demesin" mi, "asla uydurmasın" mı?

---

## 5. Sistemi gözlemleme (debug)

- `/api/admin/rag/search` `{"query": "...", "top_k": 5}` → `SearchTrace`: normalize sorgu, her sonucun `vector_score/rank`, `keyword_score/rank`, `fused_score`.
- `/api/admin/chat/test` yanıtındaki `debug.searches` → botun o turda yaptığı **her** arama (modelin yeniden yazdığı sorgu dahil).
  Bot yanlış cevap verdiyse önce buraya bakın: doğru parça geldi mi (arama sorunu) yoksa geldi de model mi yanlış kullandı (prompt sorunu)?
- `/api/admin/rag/stats`: parça sayısı, bekleyen/hatalı kayıt, `always_tokens`.
- Kategori filtresi (`search_knowledge(query, category)`) "yumuşak"tır: bilinmeyen kategori yok sayılır, filtreli sonuç eşik altıysa filtre olmadan yeniden denenir
  (model ilk testlerde "Ulaşım" gibi yaklaşık adlar verip boş sonuç almıştı; böyle bir hatayı canlı testte yakaladık).

---

## 6. Bilinen sınırlamalar ve sonraki adımlar

- **Eşik kaba**: yukarıda anlatıldı. *Sonraki adım:* **reranker** (cross-encoder, örn. bir `bge-reranker` ya da Cohere Rerank): ilk 20 adayı soru ile birlikte
  okuyup 0-1 alaka skoru verir; eşiği o skora koyarsanız cevapsız ayrımı belirgin düzelir.
- **Stemmer basit**: yumuşama (`köpek/köpeği`), fazla kırpma (`bitcoin → bitco`) olur. Vektör tarafı telafi eder. *Sonraki adım:* Zemberek/Snowball-tr.
- **Sorgu yeniden yazma** botun inisiyatifinde. *Sonraki adım:* sorgu genişletme (eşanlam listesi, HyDE).
- **Çok-turlu bağlam**: "ya çocuklar?" gibi takip soruları yeni arama sorgusuna çevrilmeli; şimdilik model bunu yapıyor.
- **Ölçek**: SQLite+numpy ~10 bin parçaya kadar rahat (matris RAM'de, tek matris çarpımı). Ötesinde: **sqlite-vec** (aynı dosyada vektör indeksi),
  sonra pgvector/Qdrant/Weaviate. `store.py` başındaki yorum ne zaman geçileceğini anlatır.
- **Eval seti küçük** (57 soru). Gerçek misafir sorularıyla (sohbet kayıtları) büyütün; her başarısız konuşmayı soruya çevirin.
- **Bağlamsal cümleler LLM üretimi**: aynı kayıtta tekrar indeksleme küçük farklar üretir; hash aynıysa yeniden üretilmez.
- **Arka plan indeksleme süreç içi** (thread): sunucu kapanırsa yarım kalan kayıt `pending` kalır, açılışta tamamlanır.

---

## 7. Hızlı komutlar

```bash
cd backend
.venv/Scripts/python.exe -m uvicorn app.main:app --port 8000   # açılışta eksik indeksleri kurar (arka plan)
.venv/Scripts/python.exe -m eval.rag_eval                      # değerlendirme
# tüm kayıtları zorla yeniden indeksle (admin token ile):
#   POST /api/admin/rag/reindex   {"force": true}
```

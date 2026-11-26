"""Kısa bilgi bankası kayıtları. İlk 12 kayıt kritik bilgilerdir ve mode="always" (her mesajda prompt'ta);
diğerleri mode="search" (RAG ile gerektiğinde aranır). (kategori, başlık, içerik, mod)"""

A, S = "always", "search"

SHORT: list[tuple[str, str, str, str]] = [
    # ======================= ALWAYS (12) =======================
    ("Konaklama", "Giriş ve çıkış saatleri", "Check-in saat 15:00'ten itibaren, check-out en geç 11:00'dir. Erken giriş (12:00'den itibaren) ve geç çıkış müsaitliğe bağlıdır ve ücretlidir; ücret ayrıntıları için ilgili kayda bakınız.", A),
    ("Politikalar", "İptal politikası özeti", "Giriş tarihinden 14 gün veya daha önce iptalde tam iade; 14 günden az ve 7 gün veya daha fazla kala %50 iade; 7 günden az kala iptal ve gelinmeyen rezervasyonlarda iade yok. Yüksek sezonda (1 Temmuz-31 Ağustos) süreler 21 ve 10 gündür. İptal talepleri info@bungai.example adresine veya telefonla iletilir; sohbet asistanı iptal işlemi yapamaz.", A),
    ("Genel", "İletişim bilgileri", "Telefon (resepsiyon, 7/24): +90 242 555 01 23. WhatsApp: +90 532 555 01 23. E-posta: info@bungai.example. Web sitesi: bungai.example. Rezervasyon, grup ve organizasyon talepleri için aynı kanallar kullanılır.", A),
    ("Genel", "Adres ve konum", "BUNGAi Villa & Bungalov Resort, Kalamar Yolu Sk. No:8, Kalkan, Kaş / Antalya adresindedir. Kalkan merkeze 3 km, Kaş'a 28 km, Dalaman Havalimanı'na yaklaşık 105 km, Antalya Havalimanı'na yaklaşık 190 km uzaklıktadır.", A),
    ("Ödeme & Fatura", "Ödeme yöntemleri", "Online rezervasyon güvenli ödeme sayfasında kredi/banka kartıyla (Visa, Mastercard, Troy) ödenir; ödeme tamamlanınca rezervasyon onaylanır. Tesiste nakit (TL, EUR, USD, GBP), kart ve EFT/havale kabul edilir. Rezervasyon sonrası 30 dakika içinde ödeme yapılmazsa tarihler serbest kalır.", A),
    ("Politikalar", "Evcil hayvan politikası özeti", "Evcil hayvanlar yalnızca Zeytin Plunge Bungalov, Lavanta Plunge Bungalov ve Akdeniz Saray Villa'da kabul edilir; önceden bildirim gerekir. Konaklama başına en fazla 2 hayvan (her biri 25 kg'a kadar), hayvan başı gecelik 750 TL. Diğer villalarda ve ortak alanlarda (restoran, havuz, plaj, spa) hayvan kabul edilmez. Rehber köpekler istisnadır.", A),
    ("Konaklama", "Minimum konaklama süresi", "Yüksek sezonda (1 Temmuz-31 Ağustos) tüm ünitelerde minimum 3 gece, Akdeniz Saray Villa için minimum 5 gece konaklama gerekir. Diğer dönemlerde minimum 2 gecedir (resmi tatil ve bayram dönemlerinde 3 gece olabilir).", A),
    ("Politikalar", "Çocuk politikası özeti", "0-3 yaş bebekler ücretsizdir ve kapasiteye dahil değildir (bebek yatağı ücretsiz). 4-12 yaş çocuklar kapasiteye dahildir; kapasite aşılamaz. Mercan Balayı Süiti ve Spa yalnızca 16 yaş üstü misafirlere açıktır. Zeytin ve Lavanta Plunge bungalovlarda en fazla 2 yetişkin ve 1 bebek kalabilir. Çocuk havuzu ve Mini Bunga Çocuk Kulübü (4-12 yaş) vardır.", A),
    ("Genel", "Tesis hakkında", "BUNGAi Villa & Bungalov Resort, Akdeniz kıyısında Kalkan'da, tamamı özel havuzlu 7 villa ve bungalovdan oluşan butik bir yaz tatil köyüdür. Plaj kulübü, Mavi Sofra Restoran, Havuz Başı Bar & Kafe, Deniz Yıldızı Spa, Mini Bunga Çocuk Kulübü ve aktivite programı vardır. Havuz ve plaj sezonu 1 Mayıs-31 Ekim'dir; tesis yıl boyu açıktır. Kahvaltı tüm konaklamalara dahildir.", A),
    ("Ödeme & Fatura", "Hasar depozitosu ve ön ödeme", "Rezervasyon bedeli online ödemede tam olarak alınır. Girişte hasar depozitosu olarak kredi kartından blokaj yapılır: bungalovlar için 5.000 TL, villalar için 10.000 TL; hasar yoksa çıkıştan sonra 7 iş günü içinde kaldırılır.", A),
    ("Genel", "Resepsiyon ve sessiz saatler", "Resepsiyon 7/24 hizmet verir. Sessiz saatler 23:00-08:00 arasıdır. Havuz alanında hoparlör kullanımı yasaktır; sigara iç mekanlarda yasaktır.", A),
    ("Konaklama", "Fiyatlar ve konaklama tipleri özeti", "Gecelik fiyatlar: Zeytin Plunge Bungalov 6.500 TL (2 kişi), Lavanta Plunge Bungalov 7.800 TL (2), Mercan Balayı Süiti 12.000 TL (2, yalnızca yetişkin), Mavi Ufuk Infinity Villa 14.500 TL (4), Martı Aile Villası 16.500 TL (6), Gün Batımı Infinity Villa 18.000 TL (5), Akdeniz Saray Villa 35.000 TL (10). Fiyatlar yıl boyu aynıdır, kahvaltı ve KDV dahildir. Güncel müsaitlik ve toplam tutar için bungalov listesi araçları kullanılır.", A),

    # ======================= SEARCH =======================
    # --- Genel
    ("Genel", "Wi-Fi ve internet", "Tüm villalarda, bungalovlarda ve ortak alanlarda ücretsiz fiber Wi-Fi vardır (ortalama 100 Mbps). Ağ adı ve şifresi villa kartında yazılıdır. Plajda Wi-Fi sınırlıdır.", S),
    ("Genel", "Sezon ve çalışma dönemleri", "Tesis yıl boyu açıktır. Tam hizmet sezonu 1 Mayıs-31 Ekim'dir: plaj kulübü, ortak ana havuz, Kumsal Bar, çocuk kulübü (1 Haziran-15 Eylül) ve tam aktivite programı. 1 Kasım-30 Nisan arasında restoran sınırlı çalışır (akşam yemeği ön rezervasyonla), plaj kulübü ve ana havuz kapalıdır; özel havuz ısıtma talep üzerine ücretlidir (gecelik 1.500 TL). Spa, fitness ve yoga yıl boyu açıktır.", S),
    ("Genel", "Hava ve iklim", "Kalkan'da yazlar sıcak ve kuraktır; Temmuz-Ağustos ortalama 33-36°C, deniz suyu 26-28°C'dir. Kış aylarında ortalama 12-17°C'dir ve yağışlıdır. Havuzu en uygun dönem Mayıs-Ekim'dir.", S),
    ("Genel", "Resepsiyon hizmetleri", "Resepsiyon: bagaj muhafazası, kasa, taksi ve transfer, tur rezervasyonu, çamaşır, havlu, ütü, kayıp eşya, doktor çağırma, araç kiralama, hediye çeki satışı ve ilaç/market siparişi gibi hizmetleri sağlar. Dahili numara 0'dır.", S),
    ("Genel", "Bagaj muhafazası", "Erken varışta veya geç çıkış sonrası bagajlarınız resepsiyonda ücretsiz saklanır (en fazla 12 saat; sorumluluk değerli eşyalar hariç).", S),
    ("Genel", "Dil ve yabancı misafirler", "Personelimiz Türkçe, İngilizce ve Almanca konuşur; Rusça ve Arapça için tercümanlık yapılır. Menüler Türkçe, İngilizce ve Almancadır.", S),
    ("Genel", "Çevre ve sürdürülebilirlik", "Resort güneş enerjisiyle su ısıtır, plastik pipet kullanmaz, bahçelerde damla sulama yapar ve yemek atıklarından kompost üretir. Havlu değişimini azaltmak isterseniz havlunuzu yerde değil askıda bırakmanız yeterlidir.", S),
    ("Genel", "Ödüller ve sertifikalar", "Resort, yeşil otel (sürdürülebilir turizm) sertifikasına ve Türkiye Turizm Bakanlığı belgeli tesis statüsüne sahiptir. Çocuklu aileler kategorisinde 2025 yılında misafir memnuniyeti ödülü almıştır.", S),

    # --- Konaklama
    ("Konaklama", "Erken giriş ve geç çıkış ücretleri", "Erken giriş: 12:00-15:00 arası müsaitlik varsa ücretsizdir; 12:00'den önce giriş gecelik fiyatın %25'idir. Geç çıkış: 11:00-14:00 arası gecelik fiyatın %25'i; 14:00-18:00 arası %50; 18:00'den sonra tam gecelik ücret alınır. Yüksek sezonda geç çıkış her zaman müsait olmayabilir; resepsiyondan en az bir gün önce talep ediniz.", S),
    ("Konaklama", "Ek yatak ve bebek yatağı", "Bebek yatağı (0-3 yaş) tüm ünitelerde ücretsizdir; Mercan Balayı Süiti'nde bebek kabul edilmez. Ek yatak yalnızca Martı Aile Villası ve Akdeniz Saray Villa'da mümkündür (gecelik 1.000 TL); kapasite aşımı yapılamaz. Bebek yatağı ve mama sandalyesi için rezervasyon notuna yazınız.", S),
    ("Konaklama", "Kahvaltı dahil mi?", "Evet, tüm konaklamalarda kahvaltı fiyata dahildir. Mavi Sofra Restoran'da 08:00-10:30 arası servis edilir; villalarda ve Mercan Balayı Süiti'nde isteğe bağlı odaya servis yapılır.", S),
    ("Konaklama", "Klima, ısıtma ve elektrik", "Tüm ünitelerde inverter klima (soğutma ve ısıtma) vardır. Villaların jeneratör desteği vardır; elektrik kesintisinde 30 saniye içinde devreye girer. Elektrik ve su kullanımı fiyata dahildir.", S),
    ("Konaklama", "Mutfak olanakları", "Mutfaklı üniteler: Mavi Ufuk Infinity, Gün Batımı Infinity, Martı Aile ve Akdeniz Saray Villa. Zeytin ve Lavanta Plunge bungalovlarda ve Mercan Balayı Süiti'nde mutfak yoktur; mini bar, su ısıtıcı ve Nespresso makinesi bulunur.", S),
    ("Konaklama", "Çamaşır ve ütü", "Çamaşır servisi kilo başı 300 TL'dir ve 24 saatte teslim edilir. Ütü ve ütü masası talep üzerine ücretsiz odaya getirilir. Villalarda çamaşır makinesi yoktur.", S),
    ("Konaklama", "Temizlik ve havlu değişimi", "Günlük temizlik 09:30-14:00 arası yapılır. Havlu ve çarşaf 3 günde bir değişir; daha sık değişim ücretsiz talep edilebilir. 'Rahatsız Etmeyin' kartıyla temizlik atlanabilir.", S),
    ("Konaklama", "Mercan Balayı Süiti - balayı hizmetleri", "Mercan Balayı Süiti'nde karşılama hediyesi (şarap, meyve tabağı), akşam turn-down, çiçekli yatak süslemesi (talep üzerine ücretsiz), odaya kahvaltı ve bir çiftler masajı (60 dk) dahildir. Yalnızca 16 yaş üstü misafir kabul edilir. Evlilik cüzdanı gösterene ek sürpriz yapılır.", S),
    ("Konaklama", "Engelli ve yaşlı misafirler için erişim", "Zeytin ve Lavanta Plunge bungalovları ile Mavi Ufuk Infinity Villa zemin kattadır ve basamaksızdır; tekerlekli sandalye ile girilebilir. Duş alanı basamaksız, tutunma barları talep üzerine takılır. Resort içinde golf arabası ile ücretsiz transfer yapılır. Plaj kulübünde tekerlekli sandalye rampası vardır.", S),
    ("Konaklama", "Villa seçimi - çocuklu aileler", "Küçük çocuklu aileler için en uygun seçenek Martı Aile Villası'dır: ayrı 40 cm'lik çocuk havuzu, çitli ve kilitli havuz alanı, bebek yatağı ve mama sandalyesi, çocuk kulübüne 2 dakika yürüme mesafesi. 6 kişiye kadardır ve gecelik 16.500 TL'dir.", S),
    ("Konaklama", "Villa seçimi - çiftler", "Çiftler için Zeytin Plunge Bungalov (6.500 TL), Lavanta Plunge Bungalov (7.800 TL, kısmi deniz manzarası) ve jakuzili Mercan Balayı Süiti (12.000 TL) uygundur. Hepsinde özel havuz vardır; Mercan Balayı Süiti yalnızca yetişkinlere özeldir.", S),
    ("Konaklama", "Villa seçimi - büyük gruplar", "10 kişiye kadar gruplar için Akdeniz Saray Villa (4 yatak odası, 60 m² sonsuzluk havuzu, jakuzi, 35.000 TL/gece) uygundur. 10 kişiden fazla gruplar için iki villa (örn. Gün Batımı ve Mavi Ufuk Infinity) komşu olarak ayarlanabilir; grup indirimi için info@bungai.example'a yazınız.", S),
    ("Konaklama", "Kasa, değerli eşyalar ve güvenlik", "Her villada elektronik kasa bulunur. Kasaya konmayan eşyalar için tesis sorumluluk almaz. Resepsiyonda ayrıca değerli eşya emanetçisi vardır. 7/24 güvenlik ve kamera gözetimi vardır; villa içlerine kamera konmaz.", S),
    ("Konaklama", "Villada özel şef ve hizmetli", "Akdeniz Saray Villa'da talep üzerine özel şef günlük 12.000 TL ve villa görevlisi günlük 4.500 TL'dir; yiyecek malzemesi ayrıca faturalanır. Diğer villalarda mini şef hizmeti (akşam yemeği için) 3.500 TL'dir ve 48 saat öncesinden ayrılmalıdır.", S),
    ("Konaklama", "Çiçek, pasta ve süsleme siparişi", "Doğum günü, yıl dönümü veya evlilik teklifi için çiçek buketi (1.200 TL'den), özel pasta (900 TL'den) ve oda süsleme (1.500 TL) talep edilebilir. En az 24 saat önce resepsiyona bildirilmelidir.", S),

    # --- Havuz & Plaj
    ("Havuz & Plaj", "Havuz ısıtma", "1 Mayıs-31 Ekim arasında havuzlar güneş enerjisiyle 26-28°C'de tutulur ve ücretsizdir. 1 Kasım-30 Nisan arasında özel havuz ısıtma talebe bağlıdır, gecelik 1.500 TL'dir ve 24 saat önceden bildirilmelidir. Jakuzi 36-38°C'dedir.", S),
    ("Havuz & Plaj", "Plaj kulübü saatleri ve ulaşım", "Plaj kulübü 1 Mayıs-31 Ekim arası 09:00-19:00 açıktır; resorta 250 metre uzaklıkta, her saat başı kalkan ücretsiz servisle (09:00-18:00) ulaşılır. Şezlong, şemsiye ve havlu ücretsizdir. Cankurtaran 09:30-18:30 arası görevdedir.", S),
    ("Havuz & Plaj", "Havlu politikası", "Havuz/plaj havluları kişi başı 2 adet, resepsiyondan veya havuz başı bardan verilir. Kaybı 600 TL'dir. Villaların kendi havuz havluları villada bulunur.", S),
    ("Havuz & Plaj", "Özel havuz derinlikleri", "Zeytin Plunge 1,2 m; Lavanta Plunge 1,3 m; Mavi Ufuk Infinity 1,4 m; Gün Batımı Infinity 1,5 m; Martı Aile ana havuz 1,4 m ve çocuk havuzu 0,4 m; Mercan Balayı 1,2 m; Akdeniz Saray en fazla 1,6 m. Özel havuzlarda cankurtaran yoktur.", S),
    ("Havuz & Plaj", "Havuzda cam ve yiyecek kuralı", "Havuz çevresinde cam bardak/şişe yasaktır; resepsiyondan plastik bardak istenebilir. Havuz başında yemek ve içecek servisi ücretsiz taşınır, ancak dışarıdan alkol getirilemez.", S),
    ("Havuz & Plaj", "Deniz araçları kiralama", "Plaj kulübünde kano saatlik 400 TL, SUP 450 TL, deniz bisikleti 500 TL, şnorkel seti günlük 250 TL'dir. Can yeleği zorunludur. Jet ski ve parasailing anlaşmalı operatörle yapılır (20 dk jet ski 2.500 TL).", S),
    ("Havuz & Plaj", "Jakuzi kullanım kuralları", "Jakuzide 12 yaş altı çocuklar bulunamaz, en fazla 20 dakika kalınmalıdır. Hamileler, kalp ve tansiyon hastaları doktorlarına danışmalıdır. Alkol aldıktan sonra jakuziye girilmez.", S),
    ("Havuz & Plaj", "Güneş koruması ve bayrak sistemi", "Plajda yeşil bayrak yüzmeye uygun, sarı bayrak dikkat, kırmızı bayrak yüzmek yasaktır. 12:00-16:00 arası güneşten korunmanız önerilir. Güneş kremi ve şapka resepsiyon mağazasında satılır.", S),

    # --- Yeme-İçme
    ("Yeme-İçme", "Akşam yemeği saatleri", "Mavi Sofra Restoran'da akşam yemeği 19:00-22:30 arası servis edilir (son sipariş 22:00). Yüksek sezonda rezervasyon önerilir; kış aylarında yalnızca ön rezervasyonla 19:00-21:30 arası hizmet verilir.", S),
    ("Yeme-İçme", "Kahvaltı saatleri", "Kahvaltı 08:00-10:30 arasında Mavi Sofra'da serpme olarak servis edilir. Villalara odaya servis için önceki akşam bildirim yeterlidir. Erken yola çıkanlara 06:30'dan itibaren ücretsiz kahvaltı kutusu hazırlanır.", S),
    ("Yeme-İçme", "Öğle yemeği ve atıştırmalıklar", "Öğle yemeği Mavi Sofra'da 12:30-15:00, Havuz Başı Bar & Kafe'de 10:00-19:00 arası hafif yemekler (tost, hamburger, salata) sunulur. Servis şezlonga getirilir ve ek ücret alınmaz.", S),
    ("Yeme-İçme", "Balık Gecesi", "Her Cuma 20:00'de Mavi Sofra'da Balık Gecesi düzenlenir: sınırsız meze ve günün balığı dahil kişi başı 1.450 TL; rezervasyon gerekir.", S),
    ("Yeme-İçme", "Türk Gecesi", "Her Çarşamba 20:30'da Türk Gecesi: Anadolu mezeleri, rakı-balık menüsü ve halk oyunları. Menü kişi başı 1.250 TL'dir, rezervasyon önerilir.", S),
    ("Yeme-İçme", "Odaya servis", "Odaya servis 08:00-22:00 arasındadır; menü fiyatlarına ek 100 TL servis kabı ücreti uygulanır. Sipariş için dahili 0'ı arayınız.", S),
    ("Yeme-İçme", "Vegan, vejetaryen ve glutensiz seçenekler", "Menüde vegan (V) ve glutensiz (GF) seçenekler işaretlidir. Özel diyet taleplerinde 12 saat önceden bildirim önerilir. Ciddi alerjilerde garsona bildirim zorunludur.", S),
    ("Yeme-İçme", "Gece Lounge ve canlı müzik", "Gece Lounge 20:00-01:00 arasında kokteyl ve müzik sunar. Perşembe akustik canlı müzik, Cumartesi DJ gecesi vardır (01:00'e kadar). Giriş ücretsizdir.", S),
    ("Yeme-İçme", "Dışarıdan yiyecek ve içecek", "Restoran, bar, havuz ve plaj alanlarına dışarıdan alkollü içecek ve hazır yemek getirilemez. Villanın özel alanında kendi yiyeceğinizi tüketebilirsiniz. Doğum günü pastası (24 saat önceden sipariş edilmesi koşuluyla) resortumuz tarafından hazırlanır.", S),
    ("Yeme-İçme", "Alkol politikası", "18 yaşından küçüklere alkol servis edilmez. Her villada mini barda alkolsüz içecekler bulunur; alkollü içkiler ücrete tabidir. Aşırı alkollü misafirlere servis durdurulabilir.", S),
    ("Yeme-İçme", "Market ve su siparişi", "Resepsiyondan Kalkan'daki marketten alışveriş siparişi verilebilir (komisyon yok, 150 TL teslimat). Ücretsiz su (her villa için günde 6 adet 0,5 L) villaya bırakılır.", S),
    ("Yeme-İçme", "Barbekü kullanımı", "Gün Batımı Infinity Villa, Martı Aile Villası ve Akdeniz Saray Villa'nın barbekü köşesi vardır. Mangal kömürü ve ızgara resepsiyondan 350 TL'ye alınır. Barbekü en geç 22:00'ye kadar yakılabilir; kuru çalı bölgelerinde açık ateş yasaktır.", S),

    # --- Spa
    ("Spa & Wellness", "Spa çalışma saatleri", "Deniz Yıldızı Spa yıl boyu her gün 10:00-20:00 açıktır. Randevu için resepsiyonu veya spa resepsiyonunu (dahili 7) arayınız. Sauna ve buhar odası konaklayan misafirler için ücretsizdir.", S),
    ("Spa & Wellness", "Spa yaş sınırı", "Spa alanı (kapalı havuz, sauna, buhar) 16 yaşından küçüklere kapalıdır. 8-15 yaş çocuklar 10:00-12:00 arasında yetişkin eşliğinde kapalı havuzu kullanabilir. Çocuk masajı 7-15 yaş için 900 TL'dir.", S),
    ("Spa & Wellness", "Spa randevu iptali", "Spa randevusu 24 saat öncesine kadar ücretsiz iptal edilir. 24 saatten az kala iptalde %50, 2 saatten az kala iptalde ve gelmemede tamamı alınır.", S),
    ("Spa & Wellness", "Yoga ve fitness", "Sabah yogası her gün 07:30'da yoga terasında ücretsizdir. Fitness salonu 07:00-21:00 arası ücretsiz açıktır. Özel yoga dersi 1.500 TL, personal trainer saatlik 1.800 TL'dir.", S),
    ("Spa & Wellness", "Spa hediye çeki", "Spa hediye çekleri resepsiyondan satın alınabilir ve 1 yıl geçerlidir. Tutar serbesttir (en az 1.000 TL).", S),
    ("Spa & Wellness", "Hamamda kese köpük", "Geleneksel hamam (kese ve köpük masajı) 45 dakikadır ve 1.250 TL'dir; çiftler için hamam seremonisi 75 dk, kişi başı 1.900 TL'dir.", S),

    # --- Aktiviteler
    ("Aktiviteler", "Tekne turu", "Resort tekne turu Cumartesi günleri 6 saattir (Kaputaş ve koylar), kişi başı 3.500 TL, öğle yemeği dahildir. Özel tekne kiralama (günlük 18.000 TL'den) için resepsiyonla görüşünüz. Yüksek sezonda en az 2 gün önceden rezervasyon gerekir.", S),
    ("Aktiviteler", "Dalış", "Dalış tanıtım dersi (havuzda) kişi başı 800 TL, deniz tek dalış 2.800 TL'dir. Dalış için 10 yaş ve üzeri olmak ve sağlık beyanı vermek gerekir. Sertifika kursu için Kaş'taki dalış merkezine yönlendirme yapılır.", S),
    ("Aktiviteler", "Tenis kortu", "Tenis kortu saatlik 400 TL'dir; misafirlere ilk saat ücretsizdir. Raket ve top resepsiyondan verilir. Işıklı kort 22:00'ye kadar kullanılabilir.", S),
    ("Aktiviteler", "Bisiklet ve scooter kiralama", "Bisiklet günlük 500 TL (kask dahil), scooter günlük 1.200 TL'dir (ehliyet gerekli). Kalkan'a bisikletle yaklaşık 15 dakikadır.", S),
    ("Aktiviteler", "Yoga ve meditasyon", "Sabah yogası 07:30, gün batımı meditasyonu 17:30'da ücretsizdir. Pazar akşamı 17:00'de yoga ve ses banyosu 600 TL'dir.", S),
    ("Aktiviteler", "Mutfak atölyesi", "Salı günleri 16:30'da Ege otları ve zeytinyağlılar mutfak atölyesi düzenlenir, kişi başı 900 TL'dir; en az 4 kişi gerekir.", S),
    ("Aktiviteler", "Animasyon ve akşam programı", "Her akşam 21:00'de farklı bir etkinlik vardır: sinema, karaoke, canlı müzik, DJ. Program resepsiyonda ve villa kartındadır.", S),
    ("Aktiviteler", "Doğa yürüyüşü", "Çarşamba 08:30'da rehberli ücretsiz doğa yürüyüşü yapılır (2 saat). Likya Yolu için rehber kiralama günlük 3.500 TL'dir.", S),

    # --- Çocuk Kulübü
    ("Çocuk Kulübü", "Çocuk kulübü saatleri ve yaş sınırı", "Mini Bunga Çocuk Kulübü 4-12 yaş arası çocuklar içindir; 1 Haziran-15 Eylül arası her gün 10:00-17:00 ücretsiz açıktır. Akşam kulübü (1 Temmuz-31 Ağustos) 18:30-21:30, kişi başı 600 TL'dir. 0-3 yaş bebekler kabul edilmez.", S),
    ("Çocuk Kulübü", "Çocuk bakıcısı", "Çocuk bakıcısı saatlik 600 TL'dir, en az 2 saat ve 24 saat önceden rezerve edilir. Bebekler dahil tüm yaşlar için hizmet verilir.", S),
    ("Çocuk Kulübü", "Çocuk menüsü ve mama sandalyesi", "Çocuk menüsü (köfte veya nugget, patates, meyve suyu) 340 TL'dir. Mama sandalyesi, biberon ısıtma ve bebek maması hazırlama ücretsizdir.", S),
    ("Çocuk Kulübü", "Çocuklar için havuz güvenliği", "Çocuk havuzu 40 cm derinliğindedir ve yetişkin gözetimi gerekir. Cankurtaran ana havuzda 09:00-19:00 görevdedir. Özel havuzlarda cankurtaran yoktur; Martı Aile Villası'nda havuz alanı kilitli çitle çevrilidir. Şişme kolluk ve can yeleği resepsiyondan ücretsiz alınabilir.", S),
    ("Çocuk Kulübü", "Çocuk doğum günü", "Mini Bunga Kulübü'nde çocuk doğum günü (15 çocuğa kadar, 2 saat) 12.000 TL'dir; animatör, pasta ve atıştırmalıklar dahildir. En az 3 gün önceden rezervasyon gerekir.", S),
    ("Çocuk Kulübü", "Bebek ve çocuk ekipmanı", "Bebek yatağı, mama sandalyesi, küvet, kapı güvenlik bariyeri ücretsizdir. Bebek arabası günlük 250 TL'dir. Bebek koltuğu (araç) transferde ücretsizdir.", S),

    # --- Etkinlik & Organizasyon
    ("Etkinlik & Organizasyon", "Düğün yapılabilir mi?", "Evet, 30-100 kişilik düğün ve nişan organizasyonları için Beyaz Dalga (30 kişi, 145.000 TL), Akdeniz Rüyası (60 kişi, 310.000 TL) ve Saray Gecesi (100 kişi, 695.000 TL) paketleri vardır. Ayrıntı ve teklif için info@bungai.example.", S),
    ("Etkinlik & Organizasyon", "Evlilik teklifi organizasyonu", "Gün batımında plajda veya Ufuk Terası'nda evlilik teklifi paketi 18.500 TL'dir (çiçek, mum, şampanya, fotoğrafçı, akşam yemeği). En az 7 gün önceden rezervasyon gerekir.", S),
    ("Etkinlik & Organizasyon", "Toplantı salonu", "Salon Mavi 40 kişilik, klimalı ve projeksiyonlu toplantı salonudur: tam gün 18.000 TL, yarım gün 11.000 TL.", S),
    ("Etkinlik & Organizasyon", "Düğün kaporası ve iptali", "Düğün/organizasyon için paket bedelinin %30'u kapora alınır. 60 günden önce iptalde kapora iade edilir, 60-30 gün arasında %50, 30 günden az kala iade edilmez.", S),
    ("Etkinlik & Organizasyon", "Düğün misafirleri için konaklama", "Düğün misafirleri için villalar ve bungalovlar %10 indirimle ayrılabilir. Gelin-damat paketlere göre 1-3 gece hediye konaklama alır.", S),

    # --- Ulaşım & Transfer
    ("Ulaşım & Transfer", "Dalaman havalimanı transferi", "Dalaman Havalimanı (DLM) transferi yaklaşık 1 saat 40 dakikadır: 1-3 kişilik araç 4.200 TL, Vito VIP (4-7 kişi) 5.500 TL, minibüs (8-14) 7.800 TL; tek yön, araç başı. Uçuş saatini 48 saat önceden bildiriniz.", S),
    ("Ulaşım & Transfer", "Antalya havalimanı transferi", "Antalya Havalimanı (AYT) yaklaşık 190 km, 3 saattir: 1-3 kişilik araç 6.800 TL, Vito VIP 8.900 TL, minibüs 12.500 TL (tek yön, araç başı).", S),
    ("Ulaşım & Transfer", "Kalkan merkeze servis", "Resortumuzdan Kalkan merkeze 10:00-23:00 arası her saat başı ücretsiz servis aracı vardır. Taksi yaklaşık 250 TL'dir.", S),
    ("Ulaşım & Transfer", "Otopark ve araçla gelenler", "Her villanın yanında ücretsiz park yeri vardır (Akdeniz Saray için 3 araç). Bungalovlar ortak otoparkı kullanır. Elektrikli araç şarjı (22 kW) ücretsizdir.", S),
    ("Ulaşım & Transfer", "Taksi ve araç kiralama", "Taksi çağrısı resepsiyondan yapılır. Anlaşmalı araç kiralama günlük 1.800 TL'den başlar ve araç resort girişine getirilir.", S),
    ("Ulaşım & Transfer", "Gece transfer ek ücreti", "23:00-06:00 arasındaki transferlerde %20 gece tarifesi uygulanır. Uçuş gecikmelerinde sürücü 60 dakika ücretsiz bekler.", S),
    ("Ulaşım & Transfer", "Marmaris, Bodrum ve Fethiye transferi", "Fethiye 3.600 TL, Ölüdeniz 4.000 TL, Bodrum Havalimanı 9.500 TL (ön rezervasyonla). Marmaris için özel teklif alınız.", S),

    # --- Politikalar
    ("Politikalar", "Sigara politikası", "İç mekanlarda ve restoranda sigara ve vape yasaktır. Teras ve bahçelerde içilebilir. İç mekanda sigara içilmesi halinde 3.000 TL temizlik bedeli alınır.", S),
    ("Politikalar", "Ziyaretçi politikası", "Konaklamayan ziyaretçiler önceden bildirimle 10:00-20:00 arası kabul edilir; villa başına en fazla 4 kişi; günlük kişi başı 750 TL katılım ücreti. Ziyaretçiler geceleyemez.", S),
    ("Politikalar", "Drone yasağı", "Tesis içinde drone kullanımı yasaktır. Profesyonel çekimler için yönetimden izin alınmalıdır.", S),
    ("Politikalar", "Gürültü ve komşu şikayetleri", "Sessiz saatler 23:00-08:00'dir. Hoparlör kullanımı 22:00'den sonra yasaktır. Şikayet halinde güvenlik görevlisi uyarı yapar; tekrarında konaklama sonlandırılabilir.", S),
    ("Politikalar", "Evcil hayvan ücreti ve kuralları (ayrıntı)", "Evcil hayvan ücreti hayvan başı gecelik 750 TL'dir. Tesis içinde tasma zorunludur, hayvanlar restoran, havuz, plaj ve spa'ya alınamaz. Hayvanın tek başına villada bırakılmaması rica edilir. Aşı karnesi istenebilir. Kedi ve köpek dışındaki egzotik hayvanlar kabul edilmez.", S),
    ("Politikalar", "Rezervasyonda kimlik ve yaş şartı", "Rezervasyonu yapan kişi 18 yaşından büyük olmalıdır. Girişte tüm yetişkinlerin kimlik veya pasaport ibraz etmesi gerekir. 18 yaş altı misafirler reşit yakınlarıyla kalmalıdır.", S),
    ("Politikalar", "Grup ve toplu rezervasyonlar", "5 ve üzeri villa için grup sözleşmesi yapılır. Grup indirimi (%10'a kadar) müsaitliğe bağlıdır. Taleplerinizi info@bungai.example adresine iletiniz.", S),
    ("Politikalar", "Kayıp eşya", "Kayıp eşyalar resepsiyonda 3 ay saklanır. Gönderim kargo ücreti alıcıya aittir. Değerli eşyalar kasada saklanmalıdır.", S),

    # --- Güvenlik
    ("Güvenlik", "Sağlık ve doktor", "Resortun 7/24 çağrı üzerine doktoru vardır; muayene ücreti 2.500 TL'dir. Acil durumlarda resepsiyonu veya 112'yi arayın. En yakın eczane Kalkan'da (3 km), hastane Kaş'ta (28 km).", S),
    ("Güvenlik", "Yangın ve deprem güvenliği", "Her villada yangın söndürücü ve duman dedektörü vardır. Acil çıkış planı kapının arkasındadır. Toplanma alanı resort giriş meydanıdır. Resort yapıları deprem yönetmeliğine uygundur.", S),
    ("Güvenlik", "Güvenlik ve kamera", "Resort 7/24 güvenlik görevlisi ve ortak alan kamera gözetimiyle korunur; villa içlerinde kamera yoktur. Girişte kimlik kontrolü yapılır.", S),
    ("Güvenlik", "Bakım ve acil durum telefon", "Teknik arıza, su, elektrik gibi acil durumlar için resepsiyon (dahili 0) 7/24 teknik ekibi yönlendirir. Havuz ekipmanları arızası 2 saat içinde giderilir.", S),
    ("Güvenlik", "Deniz güvenliği ve denize giriş", "Plajda cankurtaran 09:30-18:30 arasındadır. Gece denize girmek yasaktır. Bayrak sistemi: yeşil serbest, sarı dikkat, kırmızı yasak.", S),
    ("Güvenlik", "Gıda güvenliği ve alerji", "Mutfağımız HACCP belgelidir. Alerjen bilgisi menüde belirtilmiştir; ciddi alerjilerde garsonu bilgilendirin. Eser miktarda çapraz bulaşma riski her zaman vardır.", S),

    # --- Ödeme & Fatura
    ("Ödeme & Fatura", "Fatura ve vergi", "Fiyatlara KDV ve konaklama vergisi dahildir. Fatura kişi veya şirket adına kesilir; şirket faturası için vergi numarasını ve ünvanı rezervasyon notunda veya e-posta ile bildirin. e-Fatura/e-Arşiv e-posta ile gönderilir.", S),
    ("Ödeme & Fatura", "Döviz ve nakit ödeme", "Tesiste TL, EUR, USD ve GBP nakit kabul edilir; döviz günlük resort kuruyla çevrilir. Rezervasyon online ödemelerde TL geçerlidir.", S),
    ("Ödeme & Fatura", "Taksit imkanı", "Online ödemede bankanız destekliyorsa 2-6 taksit seçeneği sunulabilir. Taksit oranları bankaya aittir. İade durumunda banka komisyon farkı iade edilmez.", S),
    ("Ödeme & Fatura", "Havale ve EFT ile ödeme", "Girişe 14 günden fazla süre varsa havale/EFT ile ödeme yapılabilir; bilgi için info@bungai.example'a yazınız. Dekont gönderilene kadar rezervasyon bloke edilmez.", S),
    ("Ödeme & Fatura", "Ödeme başarısız oldu", "Ödeme başarısız olursa aynı rezervasyon için yeni ödeme bağlantısı oluşturulabilir. Kartınızdan çekilen tutar varsa 3 iş günü içinde bankanız iade eder. Rezervasyon 30 dakika içinde ödenmezse iptal olur.", S),
    ("Ödeme & Fatura", "Villa hesabı ve harcamalar", "Restoran, bar, spa harcamaları villa hesabınıza yazdırılabilir ve çıkışta toplu ödenir. Harcama limiti yoktur; kart bilgisi girişte alınır.", S),
    ("Ödeme & Fatura", "Hediye çeki", "Konaklama ve spa hediye çekleri satın alınabilir; konaklama hediye çeki 12 ay geçerlidir. Çek iade veya nakde çevrilemez.", S),

    # --- SSS
    ("SSS", "Havuzu özel mi ortak mı?", "Tüm villaların ve bungalovların kendi özel havuzu vardır; ayrıca ortak ana havuz ve plaj kulübü tüm misafirlere açıktır. Özel havuzlar yalnızca o villa misafirleri içindir.", S),
    ("SSS", "Denize uzak mı?", "Resort denize yürüyerek yaklaşık 5 dakika (250 m) mesafededir; plaj kulübüne her saat başı ücretsiz servis vardır. Mavi Ufuk, Gün Batımı, Lavanta ve Mercan'dan deniz manzarası vardır.", S),
    ("SSS", "Evcil hayvanla gelebilir miyim?", "Kedi veya köpekle yalnızca Zeytin Plunge, Lavanta Plunge ve Akdeniz Saray Villa'ya gelebilirsiniz; hayvan başı gecelik 750 TL, en fazla 2 hayvan.", S),
    ("SSS", "Tesis sadece yetişkinlere mi?", "Hayır, resort aile dostudur. Yalnızca Mercan Balayı Süiti ve spa alanları 16 yaş üstüdür.", S),
    ("SSS", "Yemekler dahil mi?", "Kahvaltı dahildir. Öğle ve akşam yemekleri, içecekler ayrıca ücretlidir (À la carte). Yarım pansiyon veya her şey dahil paket yoktur.", S),
    ("SSS", "Havuz kış aylarında kullanılabilir mi?", "Özel havuzlar kış aylarında ısıtma talebiyle (gecelik 1.500 TL) kullanılabilir. Ortak ana havuz 1 Kasım-30 Nisan arasında kapalıdır. Spa'nın kapalı havuzu yıl boyu açıktır.", S),
    ("SSS", "Rezervasyon nasıl yapılır?", "Web sitesinden veya sohbet asistanından tarih, kişi sayısı ve villa seçerek rezervasyon yapılır; ardından güvenli ödeme sayfasında ödeme tamamlanır. Telefon veya e-posta ile de yapılabilir.", S),
    ("SSS", "Wi-Fi şifresi nedir?", "Wi-Fi şifresi villa kartında yazılıdır. Bulamazsanız resepsiyon dahili 0'dan öğrenebilirsiniz.", S),
    ("SSS", "Balayı için ne öneriyorsunuz?", "Mercan Balayı Süiti: jakuzi, özel havuz, karşılama hediyesi, odaya kahvaltı ve çiftler masajı dahil, 12.000 TL/gece. Yalnızca yetişkinlere özeldir.", S),
    ("SSS", "Sinek, böcek ve sivrisinek var mı?", "Villalarda sineklik ve gece sivrisinek önleyici cihaz vardır. Yaz akşamları bahçede sivrisinek olabilir; sprey resepsiyondan ücretsizdir.", S),
    ("SSS", "Su ve elektrik kesintisi olur mu?", "Resortta yedek depo ve jeneratör vardır; kesintiler genellikle fark edilmez. Kısa kesintilerde klima otomatik yeniden başlar.", S),
    ("SSS", "Sigara içilen alan var mı?", "Teras ve bahçelerde içilebilir. İç mekan, restoran, spa ve çocuk kulübü sigara yasaktır.", S),
    ("SSS", "Yaş sınırı olan bir villa var mı?", "Mercan Balayı Süiti 16 yaş ve üzeri içindir. Diğer ünitelerde yaş sınırı yoktur ancak Zeytin ve Lavanta Plunge'larda en fazla 2 yetişkin ve 1 bebek kalabilir.", S),
]

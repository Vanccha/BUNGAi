"""Uzun bilgi bankası dokümanları (RAG'in 'yapıya duyarlı parçalama' ve 'bağlamsal getirme' özelliklerini
sınamak için bilerek uzun tutuldu). Başlıklar '## ' ile işaretlidir; chunking.py bu başlıkları kullanır."""

LONG_DOCS: list[tuple[str, str, str]] = []  # (kategori, başlık, içerik)

# ---------------------------------------------------------------------------------------------
LONG_DOCS.append(("Yeme-İçme", "Restoran ve Bar Menüsü (fiyatlar ve alerjenler)", """
BUNGAi Villa & Bungalov Resort'ta dört yeme-içme noktası vardır: Mavi Sofra Restoran (ana restoran), Havuz Başı Bar & Kafe, Kumsal Bar (plaj kulübünde) ve Gece Lounge. Tüm fiyatlar TL cinsindendir ve KDV dahildir; ayrıca servis ücreti alınmaz. Alerjen kodları: G = gluten, S = süt/laktoz, Y = yumurta, K = kuruyemiş/fıstık, D = deniz ürünü/kabuklu, B = balık, N = hardal/susam. Vegan ve vejetaryen seçenekler (V) ile glutensiz seçenekler (GF) işaretlidir. Ciddi alerjileriniz varsa siparişte garsonumuza mutlaka bildirin; mutfağımız eser miktarda çapraz bulaşma riskini ortadan kaldıramaz.

## Çalışma saatleri
- Mavi Sofra Restoran: kahvaltı 08:00-10:30 (konaklama fiyatına dahil), öğle 12:30-15:00, akşam yemeği 19:00-22:30 (son sipariş 22:00). Akşam yemeği için yüksek sezonda (1 Temmuz-31 Ağustos) rezervasyon önerilir.
- Havuz Başı Bar & Kafe: her gün 10:00-19:00 (hafif öğle yemekleri, atıştırmalıklar, içecekler).
- Kumsal Bar (plaj kulübü): 1 Mayıs-31 Ekim arası 10:00-19:00.
- Gece Lounge: her gün 20:00-01:00, kokteyl ve canlı müzik geceleri.
- Odaya servis: 08:00-22:00 arası, menü fiyatlarına ek 100 TL servis kabı ücreti ile.

## Kahvaltı
Kahvaltı tüm konaklamalara dahildir. Mavi Sofra'da serpme köy kahvaltısı sunulur: Ege otları, zeytinyağlı sebzeler, 12 çeşit peynir, bal-kaymak, sahanda yumurta (Y,S), menemen (Y), taze meyve ve ev yapımı reçeller. Villalara ve Mercan Balayı Süiti'ne istenirse kahvaltı odaya/teras masasına servis edilir; bunun için önceki akşam resepsiyona bildirim yeterlidir. Erken yola çıkacak misafirler için 06:30'dan itibaren kahvaltı kutusu hazırlanır (ücretsiz). Ek kişi (kapasite dışı günübirlikçi misafir) kahvaltısı kişi başı 450 TL'dir.

## Mezeler ve başlangıçlar
- Atom (süzme yoğurt, acı biber, ceviz) - 220 TL (S,K)
- Haydari - 190 TL (S,K)
- Girit ezmesi (V,GF) - 200 TL (S içermez; peynirsiz versiyon)
- Közlenmiş patlıcan salatası - 210 TL (S)
- Zeytinyağlı enginar (V,GF) - 240 TL
- Deniz börülcesi (V,GF) - 230 TL
- Ahtapot salatası - 340 TL (D)
- Kalamar tava - 360 TL (G,D,Y)
- Sigara böreği (4 adet) - 240 TL (G,S,Y)
- Çıtır kabak çiçeği dolması - 280 TL (G,S)
- Karides güveç - 420 TL (D,S)
- Meze tabağı (6 çeşit, 2 kişilik) - 590 TL (S,K)

## Çorbalar ve salatalar
- Günün çorbası - 160 TL (içeriği günlük değişir; alerjen için garsona sorunuz)
- Balık çorbası - 240 TL (B,G)
- Çoban salata (V,GF) - 190 TL
- Akdeniz yeşillik salatası (nar ekşisi, ceviz, tulum peyniri) - 260 TL (S,K)
- Sezar salata (tavuklu) - 320 TL (G,S,Y,B)
- Avokado ve roka salatası (V,GF) - 280 TL

## Ana yemekler - et
- Dana bonfile (250 g, patates püresi, mevsim sebzesi) - 980 TL (S)
- Kuzu pirzola (4 adet, közlenmiş sebze) - 890 TL (GF)
- Kuzu tandır (pilav üzeri) - 820 TL (S)
- Izgara köfte (Ege usulü) - 540 TL (G,Y)
- Tavuk şiş (pilav, közlenmiş domates ve biber) - 460 TL (GF)
- Mantarlı tavuk sote - 480 TL (S)
- Hünkar beğendi - 720 TL (S,G)
- Çocuk menüsü: köfte veya tavuk nugget, patates kızartması, meyve suyu - 340 TL (G,Y)

## Ana yemekler - deniz ürünleri
- Günün balığı (levrek, çipura veya granyöz; ızgara veya fırında, tartılarak) - 100 gram başına 190 TL (B)
- Levrek buğulama - 640 TL (B,S)
- Çipura ızgara - 620 TL (B,GF)
- Karides tava (8 adet) - 760 TL (D,S)
- Deniz mahsulleri güveç - 840 TL (D,B,S)
- Ahtapot ızgara - 780 TL (D,GF)
- Balık tabağı (2 kişilik; levrek, kalamar, karides, salata) - 1.650 TL (B,D,G)
- Her Cuma 20:00'de Balık Gecesi: sınırsız meze ve günün balığı dahil kişi başı 1.450 TL (rezervasyon gerekli).

## Makarna, pizza ve vejetaryen ana yemekler
- Karidesli linguine - 580 TL (G,D,S)
- Penne arrabbiata (V) - 360 TL (G)
- Mantarlı risotto (V seçeneği: peynirsiz) - 420 TL (S)
- Mevsim sebzeli güveç (V,GF) - 380 TL
- Zeytinyağlı sebze tabağı (V,GF) - 340 TL
- Margarita pizza - 380 TL (G,S)
- Ege pizza (ıspanak, tulum, domates) - 420 TL (G,S)
- Falafel tabağı (V) - 360 TL (N,G)

## Tatlılar
- Fırın sütlaç - 190 TL (S)
- Kabak tatlısı (cevizli, kaymaklı) - 210 TL (K,S)
- İncirli cheesecake - 260 TL (G,S,Y)
- Baklava (4 dilim) - 280 TL (G,K,S)
- Dondurma (3 top; vanilya, çikolata, limon, mastika) - 200 TL (S)
- Mevsim meyve tabağı (V,GF) - 240 TL
- Sorbe (limon, nar; V,GF) - 170 TL

## Kokteyller ve alkollü içecekler
- Mojito - 420 TL
- Aperol Spritz - 450 TL
- Margarita - 440 TL
- Pina Colada - 430 TL
- Cosmopolitan - 450 TL
- Bungai Sunset (özel kokteyl: votka, portakal, nar şurubu, nane) - 460 TL
- Yerli bira (33 cl) - 180 TL; ithal bira - 240 TL
- Kadeh şarap (Ege kırmızı, beyaz veya roze) - 260 TL; şişe şarap 1.100 TL'den başlar
- Rakı (tek) - 190 TL, (35 cl) - 780 TL, (70 cl) - 1.450 TL
- Gin tonik / viski kola - 380 TL
- Alkol satışı 18 yaşından küçüklere yapılmaz; kimlik istenebilir.

## Alkolsüz içecekler ve kahveler
- Su (75 cl) - 70 TL, soda - 70 TL, maden suyu - 90 TL
- Kola ve meşrubatlar - 100 TL
- Taze sıkılmış portakal suyu - 170 TL
- Ev yapımı limonata (nane, zencefil) - 150 TL
- Smoothie (çilek-muz, mango, yeşil) - 220 TL
- Türk kahvesi - 110 TL, filtre kahve - 130 TL, espresso - 120 TL, cappuccino ve latte - 160 TL, buzlu latte - 180 TL
- Çay (bardak) - 40 TL, bitki çayları - 90 TL
- Ayran - 70 TL, şalgam - 80 TL

## Plajda ve havuz başında hafif yiyecekler
- Tost (kaşarlı veya karışık) - 260 TL (G,S)
- Hamburger (180 g, patates ile) - 520 TL (G,S,Y,N)
- Club sandviç - 440 TL (G,S,Y)
- Patates kızartması - 180 TL
- Meyve tabağı - 240 TL
- Dondurma (tek top) - 80 TL (S)
- Havuz başı servisi şezlonga getirilir; ek ücret yoktur.

## Özel diyet ve talepler
Vegan, vejetaryen, glutensiz ve laktozsuz menüler için en az 12 saat önceden bildirmeniz tavsiye edilir; anlık taleplerde mutfağımız elinden geleni yapar. Doğum günü pastası (10 kişiye kadar) 1.800 TL'dir ve 24 saat önceden sipariş edilmelidir. Dışarıdan hazır yiyecek ve alkollü içecek restoran ve bar alanlarına getirilemez; villaların özel alanında kendi yiyeceğinizi tüketebilirsiniz. Mangal (barbekü) olanağı olan villalarda mangal malzemesi (kömür, ızgara) resepsiyondan 350 TL karşılığında verilir.
"""))

# ---------------------------------------------------------------------------------------------
LONG_DOCS.append(("Spa & Wellness", "Deniz Yıldızı Spa Hizmet Menüsü", """
Deniz Yıldızı Spa, resortun merkezinde yer alır ve yıl boyu 10:00-20:00 saatleri arasında açıktır. Spa girişinde misafirlerimize havlu, terlik ve bornoz verilir. Tüm masaj ve bakım fiyatları TL cinsindendir, KDV dahildir ve bir kişi içindir. Randevu için resepsiyonu veya spa resepsiyonunu (dahili 7) arayabilirsiniz; yüksek sezonda en az 1 gün önceden rezervasyon önerilir.

## Spa alanı ve ücretsiz olanaklar
Konaklayan tüm misafirlerimiz şu olanaklardan ücretsiz yararlanır: kapalı ısıtmalı havuz (28°C), Fin saunası, buhar odası (hamam buharı), dinlenme alanı ve bitki çayı bar. Fitness salonu 07:00-21:00 arası ücretsizdir. Sabah yogası her gün 07:30'da yoga terasında ücretsiz yapılır. Spa'nın kapalı havuzu ve sauna alanına 16 yaşından küçük çocuklar giremez; 8-15 yaş arası çocuklar yetişkin eşliğinde 10:00-12:00 saatlerinde kapalı havuzu kullanabilir.

## Masajlar
- İsveç masajı (klasik, rahatlatıcı) - 50 dk, 2.200 TL
- Derin doku masajı - 50 dk, 2.600 TL
- Aromaterapi masajı (lavanta, bergamot veya portakal çiçeği yağı) - 50 dk, 2.400 TL
- Sıcak taş masajı - 75 dk, 3.200 TL
- Bali masajı - 60 dk, 2.800 TL
- Spor masajı - 40 dk, 2.000 TL
- Sırt, boyun ve omuz masajı - 30 dk, 1.500 TL
- Ayak refleksoloji masajı - 30 dk, 1.400 TL
- Çiftler masajı (iki kişi, yan yana, aromaterapi) - 60 dk, kişi başı 3.100 TL
- Hamilelik masajı (ikinci ve üçüncü trimester) - 50 dk, 2.500 TL; doktor onayı sorulabilir.
- Çocuk masajı (7-15 yaş, ebeveyn izniyle) - 25 dk, 900 TL

## Hamam ve vücut bakımları
- Geleneksel Türk hamamı (kese ve köpük masajı) - 45 dk, 1.250 TL
- Çiftler için hamam seremonisi (kese, köpük, bal maskesi, çay servisi) - 75 dk, kişi başı 1.900 TL
- Deniz tuzu peelingi - 30 dk, 1.300 TL
- Zeytinyağı ve bal vücut paketi - 45 dk, 1.700 TL
- Çamur maskesi (vücut) - 40 dk, 1.600 TL
- Detoks paketi (peeling + sarma + masaj) - 90 dk, 3.900 TL

## Cilt bakımları
- Klasik yüz bakımı - 50 dk, 1.800 TL
- Hyaluronik nem bakımı - 60 dk, 2.300 TL
- Altın ışıltı yüz bakımı - 75 dk, 3.000 TL
- Erkek cilt bakımı - 45 dk, 1.600 TL
- Güneş sonrası aloe vera bakımı (yüz ve vücut) - 40 dk, 1.200 TL

## El, ayak ve saç bakımı
- Manikür - 45 dk, 700 TL
- Pedikür - 60 dk, 850 TL
- Kalıcı oje (el veya ayak) - 60 dk, 950 TL
- Saç yıkama ve fön - 30 dk, 600 TL
- Argan yağlı saç bakımı - 45 dk, 900 TL
- Gelin saç ve makyaj paketi (deneme dahil) - 3 saat, 7.500 TL; düğün paketlerinde indirimli sunulur.

## Paketler
- Romantik Kaçamak Paketi: çiftler masajı (60 dk) + çiftler için hamam seremonisi + özel şarap ve meyve servisi - çift için 7.900 TL (normal fiyatı toplamı 9.700 TL).
- Rahatlama Günü Paketi: İsveç masajı + klasik yüz bakımı + zeytinyağı vücut paketi - kişi başı 5.300 TL.
- Detoks Hafta Sonu Paketi (3 gün, her gün bir uygulama) - kişi başı 8.900 TL.
- Mercan Balayı Süiti misafirlerine konaklamada bir adet çiftler masajı (60 dk) hediye edilir.

## Randevu, iptal ve kurallar
Randevunuzdan 24 saat öncesine kadar ücretsiz iptal veya değişiklik yapabilirsiniz. 24 saatten az kala iptal veya gelinmeyen randevularda hizmet bedelinin %50'si, randevu saatine 2 saatten az kala iptalde tamamı villa hesabınıza yansıtılır. Randevu saatinden 15 dakikadan fazla geç gelmeniz halinde uygulama süresi kısalabilir. Spa ücretleri odanıza/villanıza yazdırılabilir ve çıkışta toplu ödenebilir. Spa'da hizmet veren terapistlerimiz sertifikalıdır; kalp rahatsızlığı, gebelik, tansiyon, cilt hastalığı gibi durumları randevu sırasında bildirmeniz gerekir. Spa içerisinde cep telefonu sessize alınmalı, sessizliğe önem verilmelidir. Hediye çeki (spa) resepsiyondan satın alınabilir, bir yıl geçerlidir.
"""))

# ---------------------------------------------------------------------------------------------
LONG_DOCS.append(("Politikalar", "Tesis Kuralları (genel kurallar ve misafir sorumlulukları)", """
Bu kurallar, tüm misafirlerimizin huzurlu ve güvenli bir tatil geçirmesi için hazırlanmıştır. Rezervasyon yaptıran ve tesise giriş yapan her misafir bu kuralları kabul etmiş sayılır. Kurallara uymayan misafirlere uyarı yapılır; tekrarında veya ciddi ihlallerde konaklama iade yapılmaksızın sonlandırılabilir.

## Giriş ve kimlik
Girişte tüm yetişkin misafirlerin geçerli bir kimlik belgesi (T.C. kimlik kartı, pasaport veya ehliyet) ibraz etmesi zorunludur. Yabancı uyruklu misafirler için pasaport gereklidir. 18 yaşından küçükler yalnız başına konaklayamaz; reşit bir yakınları ile birlikte kalmalıdır. Rezervasyonda belirtilenden fazla kişi villaya alınamaz; kapasite aşımı yapılamaz. Check-in saat 15:00'ten itibaren, check-out en geç 11:00'dir. Girişte hasar depozitosu olarak kredi kartınızdan blokaj yapılır (bungalovlar için 5.000 TL, villalar için 10.000 TL); hasar yoksa blokaj çıkıştan sonra 7 iş günü içinde kaldırılır.

## Sessiz saatler ve gürültü
Sessiz saatler her gün 23:00-08:00 arasıdır. Bu saatlerde havuz başında yüksek sesli müzik, bağırarak konuşma, havuza atlama ve parti yapılamaz. Villaların teraslarında müzik yalnızca düşük ses seviyesinde dinlenebilir; komşu villalardan şikayet gelmesi halinde güvenlik uyarı yapar. Hoparlör kullanımı 22:00'den sonra yasaktır. Özel kutlamalar için gece lounge ve organizasyon alanı kullanılmalıdır.

## Sigara ve vape
Villaların ve bungalovların iç mekanlarında, kapalı alanlarda, restoranda, spa'da ve çocuk kulübünde sigara ve elektronik sigara içmek yasaktır. Teras, bahçe ve işaretli açık alanlarda içilebilir; izmaritler kül tablalarına atılmalıdır. İç mekanda sigara içilmesi halinde 3.000 TL özel temizlik bedeli hesaba yansıtılır.

## Ziyaretçi politikası
Konaklamayan günübirlik ziyaretçiler önceden resepsiyona bildirilmek koşuluyla 10:00-20:00 arası ağırlanabilir. Villa başına en fazla 4 ziyaretçi kabul edilir; ziyaretçiler geceleyemez. Ziyaretçi başına günlük tesis katılım ücreti 750 TL'dir (plaj ve havuz kullanımı dahil, yemek hariç). Ziyaretçilerin eylemlerinden ev sahibi misafir sorumludur. Düğün ve organizasyon misafirleri için ayrı kurallar geçerlidir.

## Evcil hayvanlar
Evcil hayvanlar yalnızca Zeytin Plunge Bungalov, Lavanta Plunge Bungalov ve Akdeniz Saray Villa'da kabul edilir (çit çevrili özel bahçe). Rezervasyonda önceden bildirilmesi şarttır. Konaklama başına en fazla 2 evcil hayvan, her biri en fazla 25 kg olabilir. Gecelik hayvan başı 750 TL ücret alınır. Hayvanlar restoran, havuz, plaj, spa, çocuk kulübü ve ortak alanlarda bulunamaz; tesis içinde gezdirilirken tasma takılmalı, dışkıları toplanmalıdır. Hayvanın yatak ve koltuklara çıkarılmaması, villada yalnız bırakılmaması rica edilir; hasar durumunda depozitodan kesinti yapılır. Rehber köpekler tüm alanlara kabul edilir ve ücret alınmaz.

## Havuz, jakuzi ve özel alan güvenliği
Özel havuzlarda ve jakuzilerde gözetimsiz çocuk bırakılamaz; çocukların güvenliğinden ebeveynler sorumludur. Havuz çevresinde cam şişe ve bardak kullanımı yasaktır; plastik veya akrilik bardak resepsiyondan temin edilebilir. Jakuzide 12 yaşından küçük çocuklar bulunamaz ve en fazla 20 dakika kalınması önerilir. Alkollü iken havuza girmek tavsiye edilmez. Villa havuzlarının kapak ve çitleri açık bırakılmamalıdır. Havuz ve plaj kurallarının ayrıntısı için "Havuz ve Plaj Kuralları" dokümanına bakınız.

## Temizlik ve ev düzeni
Günlük oda temizliği 09:30-14:00 arasında yapılır; temizlik istemiyorsanız kapıya "Rahatsız Etmeyin" kartını asabilirsiniz. Havlu ve çarşaf değişimi 3 günde bir yapılır; daha sık değişim için resepsiyondan talep edebilirsiniz. Villada 7 gece ve üzeri konaklamalarda ara temizlik ücretsizdir. Çöpler villa dışındaki konteynerlere değil, kapı önündeki özel kutuya bırakılır. Mutfak ve barbekü kullanımından sonra ekipmanlar temiz teslim edilmelidir; aksi halde 500 TL temizlik ücreti uygulanır.

## Ateş, barbekü ve yangın güvenliği
Barbekü yalnızca barbekü köşesi olan villalarda (Gün Batımı Infinity Villa, Martı Aile Villası, Akdeniz Saray Villa) ve belirlenen alanlarda yakılabilir. Kuru çalı ve çam bölgelerinde açık ateş, mum, fener ve havai fişek kesinlikle yasaktır. Bungalovlarda mum yakılabilir ancak balkon ve terasta açık alev bırakılmamalıdır. Yangın söndürücüler her villada ve ortak alanlarda bulunur; acil çıkış planı kapı arkasındadır. Mangal külleri kapalı metal kovaya boşaltılmalıdır.

## Drone, ses ve görüntü kaydı
Drone kullanımı yasaktır; bu hem diğer misafirlerin mahremiyeti hem de havacılık kuralları gereğidir. Diğer misafirlerin izni olmadan fotoğraf ve video çekilemez. Profesyonel çekimler (evlilik teklifi çekimleri, sosyal medya içerik üretimi) için yönetimden önceden izin alınmalıdır.

## Alkol, uyuşturucu ve yasaklı maddeler
18 yaşından küçüklere alkol servis edilmez. Uyuşturucu madde kullanımı ve bulundurulması yasaktır ve yasal makamlara bildirilir. Silah, patlayıcı ve yanıcı madde getirilemez. Aşırı sarhoşluk nedeniyle diğer misafirleri rahatsız eden kişilerin konaklaması sonlandırılabilir.

## Eşyalar, kayıp eşya ve hasar
Her villada kasa bulunur; değerli eşyalar kasaya konmalıdır. Tesis, kasaya konmayan eşyaların kaybından sorumlu değildir. Bulunan kayıp eşyalar resepsiyonda 3 ay saklanır; sahibi talep ederse kargo ücreti alıcıya ait olmak üzere gönderilir. Villa içi eşyalara verilen hasarlar, hasar tespit formuna göre depozitodan veya kayıtlı karttan tahsil edilir; çarşaf, havlu ve bornoz kaybında 1.500 TL'ye kadar bedel yansıtılır. Resort ürünleri (bornoz, terlik, havlu) villa dışına götürülemez.

## Otopark ve araçlar
Her villanın yanında ücretsiz otopark yeri vardır; bungalovlar ortak otoparkı kullanır. Tesis içinde hız sınırı 15 km/s'dir. Elektrikli araç şarj istasyonu (2 adet, 22 kW) otoparktadır; şarj ücretsizdir. Araçlardaki eşyalardan tesis sorumlu değildir. Tesis içinde motosiklet ve quad kullanımı yasaktır.

## Çocuklar için kurallar
Çocukların havuz ve plajda 12 yaş altı iseler her zaman yetişkin gözetiminde olması zorunludur. Çocukların güvenliği ebeveynlerin sorumluluğundadır. Mini Bunga Çocuk Kulübü kuralları ayrıca duyurulur. Mercan Balayı Süiti ve Spa alanları 16 yaşından küçük misafirlere kapalıdır.

## Şikayet ve geri bildirim
Her türlü talep ve şikayetinizi resepsiyona (dahili 0) veya info@bungai.example adresine iletebilirsiniz. Sorunlar mümkün olan en kısa sürede çözülür. Konaklama sonunda misafir memnuniyet formunu doldurmanızdan memnuniyet duyarız.
"""))

# ---------------------------------------------------------------------------------------------
LONG_DOCS.append(("Havuz & Plaj", "Havuz ve Plaj Kuralları", """
Resortumuzda üç tür havuz alanı vardır: villa ve bungalovların özel havuzları, ortak ana havuz ve çocuk havuzu ile plaj kulübü. Aşağıdaki kurallar tüm misafirler içindir.

## Özel havuzlar
Özel havuzlar yalnızca o villanın misafirlerine aittir ve 7/24 kullanılabilir; ancak 23:00-08:00 sessiz saatlerinde bağırarak konuşma, müzik ve havuza atlama yapılamaz. Havuz derinlikleri: Zeytin Plunge 1,2 m; Lavanta Plunge 1,3 m; Mavi Ufuk Infinity 1,4 m; Gün Batımı Infinity 1,5 m; Martı Aile Villası ana havuz 1,4 m ve çocuk havuzu 0,4 m; Mercan Balayı Süiti 1,2 m; Akdeniz Saray Villa en fazla 1,6 m. Özel havuzlarda cankurtaran bulunmaz; misafir sorumluluğu esastır. Havuzlar her sabah 08:00-10:00 arasında temizlenir ve kimyasal değerleri kontrol edilir; bu sürede havuzun kullanımı kısa süreli kısıtlanabilir.

## Havuz suyu ve ısıtma
1 Mayıs-31 Ekim arasında havuzlar güneş enerjisiyle ısıtılır ve su sıcaklığı genellikle 26-28°C'dir; bu hizmet ücretsizdir. 1 Kasım-30 Nisan arasında özel havuz ısıtması talebe bağlıdır ve gecelik 1.500 TL ücretlidir (en az 24 saat önceden bildirilmelidir). Jakuzi sıcaklığı 36-38°C'ye ayarlıdır. Ortak ana havuz kış aylarında kapalıdır.

## Ortak ana havuz
Ana havuz 08:00-20:00 arası açıktır. Cankurtaran 09:00-19:00 arası görevdedir; bu saatlerin dışında yüzülmesi tavsiye edilmez. Havuza girmeden önce duş alınmalıdır. Mayo, şort veya bikini dışında kıyafetle (şort, tişört, kot vb.) havuza girilemez. Bebekler ve bez kullanan çocuklar için yüzme bezi (mayo bezi) zorunludur. Koşmak, itip kakmak, tehlikeli atlayışlar ve havuzda cam kullanmak yasaktır. Havuzda top oyunu yalnızca işaretli bölümde ve diğer misafirleri rahatsız etmemek koşuluyla oynanabilir. Hastalık, açık yara veya bulaşıcı cilt hastalığı olan kişiler havuza giremez.

## Çocuk havuzu
Çocuk havuzu derinliği 40 cm'dir; 0-8 yaş çocuklar için tasarlanmıştır ve yetişkin gözetiminde kullanılır. Yetişkinlerin çocuk havuzuna girmesi sadece çocuğuna refakat içindir. Çocuk havuzu 09:00-19:00 arası açıktır. Martı Aile Villası'nın kendi çocuk havuzu özeldir ve bu kurallara tabi değildir ancak çit kapısı daima kilitli tutulmalıdır.

## Havlu ve şezlong
Plaj ve havuz havluları (kişi başı 2 adet) resepsiyondan veya havuz başı bardan oda anahtarı/kart karşılığı verilir. Havlu kaybında 600 TL bedel alınır. Şezlonglar ücretsizdir ve ilk gelen alır esasına dayanır; şezlong "rezerve" etmek için havlu bırakıp 45 dakikadan fazla ayrılmak yasaktır; bu durumda görevliler şezlongu boşaltabilir. Şemsiyeler ücretsizdir. Villa misafirleri isterlerse kendi havuz başı şezlonglarını kullanır.

## Plaj kulübü
Plaj kulübü Kalkan Koyu'nda resortun 250 metre yakınında, ücretsiz servis aracıyla (her saat başı 09:00-18:00) ulaşılan özel bir plaj alanıdır. 1 Mayıs-31 Ekim arasında 09:00-19:00 saatlerinde hizmet verir. Plaj kulübünde şezlong ve şemsiye ücretsizdir; Kumsal Bar yiyecek ve içecek servisi yapar; kano, SUP ve deniz bisikleti kiralama noktası bulunur. Plaj tüm misafirler için tehlike bayrağı sistemi kullanır: yeşil bayrak yüzmek serbesttir, sarı bayrak dikkat, kırmızı bayrak yüzmek yasaktır. Cankurtaran 09:30-18:30 arası plajdadır. Denize gece girmek yasaktır.

## Deniz araçları ve güvenlik
Deniz araçlarını (kano, SUP, deniz bisikleti) kullanırken can yeleği giymek zorunludur. Yüzme bilmeyenler yüzme alanı dışına çıkamaz. Dalış ve şnorkel için işaretli alanlar kullanılmalıdır. Jet ski ve motorlu araçlar yalnızca anlaşmalı operatör tarafından belirlenen alanlarda kullanılır; misafirlerin kendi deniz araçlarıyla plaja gelmesine izin verilmez. 12 yaş altı çocuklar deniz araçlarına yetişkin eşliğinde binebilir.

## Yasaklar
- Havuz ve plaj alanında cam şişe, cam bardak yasaktır.
- Sigara plajda yalnızca belirlenen alanlarda içilebilir; izmaritler plaja atılamaz.
- Evcil hayvanlar havuz ve plaj alanına alınamaz.
- Drone kullanımı yasaktır.
- Dışarıdan yiyecek-içecek (özellikle alkol) plaja getirilemez.
- Havuz kenarında müzik yalnızca kulaklıkla dinlenir; hoparlör yasaktır.
- Plajda topless güneşlenme serbest değildir.
"""))

# ---------------------------------------------------------------------------------------------
LONG_DOCS.append(("Etkinlik & Organizasyon", "Düğün ve Organizasyon Paketleri", """
BUNGAi Villa & Bungalov Resort, deniz manzaralı terasında ve bahçesinde küçük ve orta ölçekli düğün, nişan, evlilik teklifi, doğum günü ve kurumsal etkinlikler için hizmet verir. Organizasyonlar için en uygun dönem Mayıs-Ekim arasıdır. Tüm fiyatlar TL, KDV dahildir ve kişi sayısı yetişkin misafir içindir (7-12 yaş çocuklar %50, 0-6 yaş ücretsiz).

## Mekanlar
- Ufuk Terası: deniz manzaralı açık hava düğün ve tören alanı, 60 kişiye kadar oturmalı, 100 kişiye kadar kokteyl düzeni.
- Zeytin Bahçesi: gölgeli açık hava, ağaç altında uzun masalar, 80 kişiye kadar.
- Kumsal Kulüp Alanı: plajda gün batımı töreni, 40 kişiye kadar.
- Toplantı Salonu (Salon Mavi): kapalı, klimalı, 40 kişi tiyatro düzeni, projeksiyon ve ses sistemi dahil.

## Paket 1: Beyaz Dalga (Nişan ve Küçük Düğün)
30 kişiye kadar, 4 saatlik organizasyon. Ufuk Terası kullanımı, çiçekli tören takı, 3 çeşit meze + ana yemek (seçmeli) + tatlı, sınırsız alkolsüz içecek, 2 saat alkollü içecek (şarap, bira, rakı), düğün pastası, DJ ve ses sistemi. Paket fiyatı 145.000 TL (30 kişi dahil); ek yetişkin başı 3.900 TL. Konaklama dahil değildir; gelin-damat için Mercan Balayı Süiti 1 gece hediye.

## Paket 2: Akdeniz Rüyası (Düğün)
60 kişiye kadar, 6 saatlik organizasyon. Ufuk Terası veya Zeytin Bahçesi, tören düzeni ve çiçek süslemeleri, 5 çeşit meze, ana yemek, tatlı, gece yarısı çorbası, sınırsız alkolsüz içecek ve 4 saat alkollü içecek, 3 katlı düğün pastası, canlı müzik (3 kişilik grup) + DJ, profesyonel foto çekimi (3 saat), gelin saç ve makyaj (spa'da). Paket fiyatı 310.000 TL (60 kişi dahil); ek yetişkin başı 4.700 TL. Gelin-damata Mercan Balayı Süiti 2 gece ve çiftlere özel Romantik Kaçamak Spa Paketi hediye edilir.

## Paket 3: Saray Gecesi (Büyük Düğün)
100 kişiye kadar, 8 saatlik organizasyon. Akdeniz Saray Villa'nın bahçesi ve sonsuzluk havuzu çevresinde özel organizasyon; tam menü (5 meze, 2 ana yemek seçeneği, tatlı, meyve), sınırsız içecek paketi (premium markalar), canlı orkestra ve DJ, havai fişek yerine ışık şovu (havai fişek yasaktır), foto ve video çekimi (drone dahil değildir; drone yasaktır), 20 kişilik süs ve ışıklandırma, gelin-damat için Akdeniz Saray Villa 3 gece. Paket fiyatı 695.000 TL (100 kişi dahil). Ek yetişkin başı 5.900 TL.

## Evlilik teklifi paketi
Plaj kulübünde veya Ufuk Terası'nda gün batımı evlilik teklifi: çiçek ve mum süslemesi, şampanya ve meyve tabağı, profesyonel fotoğrafçı (30 dakika), 2 kişilik akşam yemeği. Fiyat 18.500 TL. En az 7 gün öncesinden rezervasyon gerekir.

## Doğum günü ve özel kutlamalar
- Villa doğum günü paketi: süslü villa, pasta (10 kişi), balonlar, fotoğraflı albüm; 9.500 TL.
- Çocuk doğum günü (Mini Bunga Kulübü içinde, 15 çocuğa kadar, 2 saat): animatör, pasta, atıştırmalıklar, oyunlar; 12.000 TL.
- Yıldönümü akşam yemeği (havuz başında özel masa, 3 servis): çift için 4.800 TL.

## Kurumsal etkinlik ve toplantı
Salon Mavi günlük (09:00-18:00) 18.000 TL; yarım gün (4 saat) 11.000 TL. Fiyata projeksiyon, ses sistemi, Wi-Fi, çay-kahve servisi dahildir. İki kahve molası ve öğle yemeği dahil kişi başı 1.450 TL. Takım oluşturma aktivitesi (tekne turu, SUP yarışı, yoga) kişi başı 1.800 TL'den başlar. 10 villa ve üzeri toplu konaklamalarda %10 grup indirimi uygulanabilir (konaklama fiyatı üzerinden, müsaitliğe göre).

## Rezervasyon ve ödeme koşulları
Organizasyon rezervasyonu için en az 90 gün önceden başvuru önerilir; yüksek sezonda (Haziran-Eylül) cumartesi günleri hızlı dolar. Tarih ayırma için paket bedelinin %30'u kapora olarak ödenir; kalan bedelin %40'ı etkinlikten 30 gün, kalanı 7 gün önce ödenir. Etkinliğe 60 günden önce yapılan iptallerde kaporanın tamamı iade edilir; 60-30 gün arasında %50 iade; 30 günden az kala iptalde kapora iade edilmez. Tarih değişikliği bir kez, 45 gün öncesine kadar ücretsizdir. Kesin kişi sayısı etkinlikten 7 gün önce bildirilir; azaltma yapılamaz, artış yapılabilir.

## Kurallar ve sınırlamalar
Müzik 00:00'da sona erer, ses sistemi 23:00'ten sonra kısılır. Havai fişek ve drone yasaktır. Dışarıdan yemek-içecek, pasta ve alkol getirilemez (tapa/mantar bedeli ayrıca alınmaz ancak dışarıdan içki getirilemez). Dekorasyon için dışarıdan firma çalışılacaksa 14 gün önce yönetime bildirilmeli, kurulum için sadece 1 gün önce erişim verilir. Düğün misafirlerinin konaklaması için resort villaları ve bungalovları %10 indirimle ayrılabilir; konaklayacak misafirler giriş-çıkış kurallarına uyar. Detaylı teklif ve tarih için info@bungai.example adresine veya +90 242 555 01 23 numarasına ulaşabilirsiniz.
"""))

# ---------------------------------------------------------------------------------------------
LONG_DOCS.append(("Aktiviteler", "Haftalık Aktivite Programı", """
Resort animasyon ekibi yaz sezonunda (1 Mayıs-31 Ekim) her gün farklı aktiviteler sunar. Aşağıdaki program standart haftalık programdır; hava koşulları ve katılımcı sayısına göre değişebilir, güncel program resepsiyonda ve villaların tanıtım kartında bulunur. Programdaki aktivitelerin çoğu ücretsizdir; ücretli olanların fiyatı yanında belirtilmiştir. Kasım-Nisan döneminde program sınırlıdır (sabah yogası, doğa yürüyüşü, spa etkinlikleri).

## Her gün
- 07:30 Sabah yogası (yoga terası, ücretsiz, 45 dk)
- 09:30 Su jimnastiği (ana havuz, ücretsiz, 30 dk)
- 10:00-17:00 Mini Bunga Çocuk Kulübü (4-12 yaş; ayrı dokümana bakınız)
- 11:00 Kano ve SUP tanıtım dersi (plaj kulübü, ücretsiz; ekipman kirası ayrıdır)
- 15:30 Havuz başı oyunları (voleybol, su topu)
- 17:30 Gün batımı meditasyonu (Ufuk Terası, ücretsiz)
- 21:00 Akşam eğlencesi (aşağıya bakınız)

## Pazartesi
- 10:30 Pilates (yoga terası, ücretsiz)
- 16:00 Zeytinyağı tadımı ve atölyesi (kişi başı 450 TL)
- 21:00 Sinema gecesi (açık hava, patlamış mısır ücretsiz)

## Salı
- 09:00 Kalkan çarşı gezisi (ücretsiz servis, 3 saat)
- 16:30 Mutfak atölyesi: Ege otları ve zeytinyağlılar (kişi başı 900 TL)
- 21:00 Karaoke gecesi (Gece Lounge)

## Çarşamba
- 08:30 Doğa yürüyüşü: Kalkan patika yolu (ücretsiz, 2 saat, rehber eşliğinde)
- 16:00 Dalış tanıtım dersi (havuzda; kişi başı 800 TL)
- 20:30 Türk Gecesi (Mavi Sofra: Anadolu mezeleri, halk oyunları, rakı-balık menüsü)

## Perşembe
- 09:30 Tenis turnuvası (tenis kortu, ücretsiz katılım)
- 16:00 Boyama ve seramik atölyesi (çocuklar ve yetişkinler, malzeme 300 TL)
- 21:00 Akustik canlı müzik (Gece Lounge)

## Cuma
- 10:00 Plaj voleybolu turnuvası
- 17:00 Kokteyl atölyesi (Gece Lounge, 600 TL)
- 20:00 Balık Gecesi (Mavi Sofra, kişi başı 1.450 TL, rezervasyonlu)

## Cumartesi
- 10:00 Tekne turu (Kaputaş ve koylar, 6 saat; kişi başı 3.500 TL, öğle yemeği dahil)
- 16:00 Tavla ve satranç turnuvası (havuz başı kafe)
- 21:30 Canlı müzik ve DJ gecesi (Gece Lounge, 01:00'e kadar)

## Pazar
- 09:00 Patara Plajı gezisi (günlük servis, kişi başı 600 TL; plajda öğle yemeği ayrı)
- 17:00 Yoga ve ses banyosu (yoga terası, 600 TL)
- 20:00 Barbekü gecesi (plaj kulübü, kişi başı 1.100 TL; yüksek sezonda)

## Su sporları ve kiralamalar (plaj kulübü)
- Kano: saatlik 400 TL (2 kişilik)
- SUP (ayakta kürek): saatlik 450 TL
- Deniz bisikleti: saatlik 500 TL
- Şnorkel seti: günlük 250 TL
- Jet ski (anlaşmalı operatör): 20 dakika 2.500 TL, ehliyet gerekmez, 16 yaş üstü
- Parasailing (anlaşmalı operatör): 15 dakika 2.800 TL
- Rehberli şnorkel turu: kişi başı 1.200 TL, 2 saat

## Diğer olanaklar
- Tenis kortu: saatlik 400 TL (misafirlere ilk saat ücretsiz); raket ve top resepsiyondan.
- Fitness salonu: 07:00-21:00, ücretsiz.
- Bisiklet kiralama: günlük 500 TL (kask dahil).
- Masa tenisi, bilardo, langırt: Gece Lounge yanında ücretsiz.
- Kitap ve masa oyunu kütüphanesi: resepsiyondan ödünç alınabilir.
"""))

# ---------------------------------------------------------------------------------------------
LONG_DOCS.append(("Çocuk Kulübü", "Mini Bunga Çocuk Kulübü Programı ve Kuralları", """
Mini Bunga Çocuk Kulübü, 4-12 yaş arası çocuklar için gözetimli oyun, spor ve yaratıcılık alanıdır. Kulüp havuz alanının hemen yanında, gölgelik ve klimalı iç mekanıyla birlikte yer alır. Eğitimli animatörler (pedagoji ve ilk yardım sertifikalı) çocuklara eşlik eder.

## Çalışma günleri ve saatleri
Kulüp 1 Haziran-15 Eylül arasında her gün 10:00-17:00 saatleri arasında ücretsiz hizmet verir (öğle arası 12:30-14:00 yemek saati). Akşam kulübü 18:30-21:30 saatleri arasında yalnızca 1 Temmuz-31 Ağustos'ta çalışır ve kişi başı 600 TL'dir (akşam yemeği dahil). Mayıs ve Eylül'ün ikinci yarısında kulüp hafta sonları açıktır. Kasım-Nisan arasında kulüp kapalıdır.

## Yaş grupları
- Minikler (4-6 yaş): sakin oyunlar, boyama, hikaye saati, müzik ve ritim.
- Kaşifler (7-9 yaş): takım oyunları, hazine avı, sanat atölyesi, mini olimpiyatlar.
- Maceracılar (10-12 yaş): kano tanıtımı, plaj voleybolu, bilim deneyleri, tiyatro.
0-3 yaş bebekler kulübe kabul edilmez; bebek bakımı için çocuk bakıcısı hizmeti vardır.

## Günlük program (örnek)
- 10:00 Karşılama ve tanışma oyunu
- 10:30 Sanat ve el işi atölyesi (boyama, takı yapımı, çamur)
- 11:30 Havuz oyunları (çocuk havuzunda, ebeveyn izni ile; yüzme bilmeyen 8 yaş altı çocuklar için yetişkin yardımı)
- 12:30 Öğle yemeği (çocuk menüsü, ücretsiz)
- 14:00 Dinlenme ve film saati
- 14:30 Spor ve açık hava oyunları
- 15:30 Hikaye ve tiyatro
- 16:30 Dondurma saati ve gün sonu şarkısı
- 17:00 Çocukların ebeveyne teslimi

## Haftalık temalar
Pazartesi: Denizkızları ve korsanlar; Salı: Mini şefler (kek ve pizza yapımı); Çarşamba: Doğa kaşifleri (yürüyüş ve böcek keşfi); Perşembe: Sanat günü; Cuma: Su günü (su balonları, köpük partisi); Cumartesi: Olimpiyatlar; Pazar: Sinema günü ve hediye çekilişi.

## Kayıt ve teslim
Kulüp kaydı çocuk başına resepsiyonda veya kulüp girişinde yapılır; kayıt formunda ebeveyn telefonu, alerji ve sağlık bilgisi alınır. Çocuk teslim ve alımı yalnızca kayıtlı ebeveyn veya yetkili kişi tarafından yapılır; kimlik gösterilir. Kulüpte çocuklara yiyecek verilirken alerji bilgisi dikkate alınır. Hasta (ateşli, bulaşıcı hastalığı olan) çocuklar kulübe kabul edilmez. Tuvalet eğitimi tamamlanmamış çocuklar kabul edilmez. Ebeveynlerin tesis dışına çıkması halinde telefonlarının açık olması gerekir.

## Çocuk bakıcısı ve bebek hizmetleri
Çocuk bakıcısı (4 yaş altı bebekler dahil) saatlik 600 TL'dir ve 24 saat öncesinden rezerve edilir; en az 2 saat çalışır. Bebek yatağı, mama sandalyesi ve küvet talep üzerine ücretsizdir. Bebek maması ısıtma, biberon sterilizasyonu ve mikrodalga resepsiyondan veya Mavi Sofra mutfağından yapılır. Bebek arabası resepsiyondan günlük 250 TL karşılığında kiralanabilir.

## Çocuk güvenliği
Çocuklar kulüp dışında havuz ve deniz alanlarında yetişkin eşliğinde olmalıdır. Kulübün çocuk havuzu animatör gözetiminde kullanılır. Kulüp alanından çıkış tek kapıdan yapılır ve kapı daima kontrol edilir. Fotoğraf ve video çekimi için ebeveyn izin verir; sosyal medyada paylaşım yapılmaz. Animatörler çocuklara ilaç veremez; ilaç kullanımı olan çocuklar için ebeveynin yönergesi ve bilgilendirilmiş onayı gerekir.
"""))

# ---------------------------------------------------------------------------------------------
LONG_DOCS.append(("Ulaşım & Transfer", "Transfer ve Ulaşım Fiyat Tablosu", """
BUNGAi Villa & Bungalov Resort, Antalya'nın Kaş ilçesine bağlı Kalkan'dadır. Havalimanı transferleri önceden rezervasyonla özel araçla yapılır; fiyatlar araç başınadır (kişi başı değil), tek yön içindir ve KDV dahildir. Transfer rezervasyonu için uçuş numaranızı ve iniş saatinizi en az 48 saat önceden e-posta ile veya rezervasyon notunda bildirin. Uçuş gecikmelerinde sürücü sizi 60 dakika boyunca bekler (ek ücretsiz).

## Havalimanı transferleri (araç başı, tek yön)
- Dalaman Havalimanı (DLM) - yaklaşık 105 km, 1 saat 40 dakika: Sedan/Minivan (1-3 kişi) 4.200 TL; Vito VIP (4-7 kişi) 5.500 TL; Minibüs (8-14 kişi) 7.800 TL.
- Antalya Havalimanı (AYT) - yaklaşık 190 km, 3 saat: Sedan/Minivan (1-3 kişi) 6.800 TL; Vito VIP (4-7 kişi) 8.900 TL; Minibüs (8-14 kişi) 12.500 TL.
- Bodrum Milas Havalimanı (BJV) - yaklaşık 260 km, 3 saat 45 dakika: Sedan/Minivan 9.500 TL; Vito VIP 12.500 TL (yalnızca ön rezervasyon).
- Gazipaşa-Alanya (GZP) - yaklaşık 330 km: transfer yapılmaz; Antalya Havalimanı önerilir.

## Yakın çevre transferleri
- Kalkan merkez (3 km): ücretsiz servis aracı (her saat başı 10:00-23:00) veya taksi ile yaklaşık 250 TL.
- Kaş merkez (28 km, 35 dk): 1.400 TL (araç başı).
- Patara Plajı (18 km): 1.100 TL.
- Fethiye (85 km, 1 saat 15 dk): 3.600 TL.
- Ölüdeniz (95 km): 4.000 TL.
- Saklıkent Kanyonu (45 km): 2.200 TL (gidiş-dönüş bekleme dahil 3.000 TL).
- Kaş otogarı / Kalkan otobüs durağı: 250 TL.

## Gece transferleri ve ek ücretler
23:00-06:00 arası transferlerde %20 gece tarifesi uygulanır. Bebek koltuğu (talep üzerine) ücretsizdir ve rezervasyon sırasında istenmelidir. Fazla bagaj (golf seti, bisiklet, sörf) için araç büyütme gerekebilir. Karşılama tabelası, içecek ikramı ve ıslak mendil ücretsizdir. Dönüş transferi için aynı tabloyu kullanırız; en geç 24 saat önceden resepsiyona bildirim yapılmalıdır.

## Ödeme ve iptal
Transfer ücreti rezervasyon sırasında online ödenebilir veya varışta nakit (TL, EUR, USD, GBP) veya kartla sürücüye ödenebilir. 24 saat öncesine kadar yapılan iptallerde ücret alınmaz; 24 saatten az kala iptalde ve gelinmeyen transferlerde ücretin tamamı alınır.

## Kendi aracınızla gelmek
- İstanbul'dan Kalkan'a: yaklaşık 750 km, 9-10 saat (Dalaman üzerinden); Ankara'dan 580 km, 7,5 saat; İzmir'den 410 km, 5,5 saat.
- Kalkan'a ulaşım D400 karayolu ile; Kalkan girişinde "Kalamar Yolu" tabelasını takip ederek resort girişine ulaşılır. Tesisin otoparkı ücretsizdir. Villa başına 1 araç (Akdeniz Saray Villa için 3 araç) park yeri ayrılmıştır; ek araçlar ortak otoparka park edilir.
- Elektrikli araç şarj istasyonu (22 kW, 2 adet) ücretsizdir.

## Toplu taşıma
Dalaman Havalimanı'ndan Havaş/özel shuttle ile Fethiye'ye, oradan dolmuş/otobüsle Kalkan'a ulaşılabilir (toplam yaklaşık 3 saat 30 dakika). Kalkan otobüs durağından resorta taksi 250 TL'dir. Bu seçenek yüksek sezonda yoğun olabileceğinden özel transferi öneririz.

## Araç kiralama ve taksi
Resepsiyonumuz anlaşmalı araç kiralama firması ile iş birliği yapar; günlük kiralama (ekonomik sınıf) 1.800 TL'den başlar, teslim resort girişinde yapılır. Yerel taksi çağrıları resepsiyondan yapılır. Bisiklet kiralama günlük 500 TL, scooter 1.200 TL (ehliyet gerekli).
"""))

# ---------------------------------------------------------------------------------------------
LONG_DOCS.append(("Konaklama", "Villa ve Bungalov Tipleri Detaylı Rehber", """
BUNGAi Villa & Bungalov Resort'ta yedi farklı konaklama seçeneği vardır ve hepsinin özel havuzu bulunur. Gecelik fiyatlar yıl boyu geçerlidir, kahvaltı dahildir ve KDV fiyata dahildir. Tüm üniteler klimalı, Wi-Fi'lı, kasalı ve çay-kahve donanımlıdır.

## Zeytin Plunge Bungalov (2 kişi, 6.500 TL/gece)
38 m², 1 yatak odası, 12 m² özel plunge havuzu (derinlik 1,2 m). Zeytin ağaçları arasında çit çevrili özel bahçe, pergola ve iki şezlong. Mutfak yoktur; çay-kahve, mini bar ve su ısıtıcısı bulunur. Maksimum 2 yetişkin (+1 bebek bebek yatağıyla). Evcil hayvan kabul edilir (hayvan başı gecelik 750 TL). Engelli erişimi için zemin kat, basamaksız giriş.

## Lavanta Plunge Bungalov (2 kişi, 7.800 TL/gece)
45 m², 1 yatak odası, 18 m² özel havuz (1,3 m), kısmi deniz manzarası, açık hava duşu, lavanta bahçesi. Çit çevrili bahçe nedeniyle evcil hayvan kabul eder. 2 yetişkin (+1 bebek). Zemin kat, giriş basamaksızdır.

## Mavi Ufuk Infinity Villa (4 kişi, 14.500 TL/gece)
90 m², 2 yatak odası (biri çift kişilik, biri iki ayrı yatak), 28 m² sonsuzluk havuzu (1,4 m), tam deniz manzarası, tam donanımlı mutfak, dış mekan yemek masası. Evcil hayvan kabul edilmez. 4 kişiye kadar (çocuklar dahil, 0-3 yaş bebekler hariç).

## Gün Batımı Infinity Villa (5 kişi, 18.000 TL/gece)
110 m², 2 yatak odası + salonda çekyat (5. kişi için), 35 m² sonsuzluk havuzu (1,5 m), batıya bakan gün batımı terası, barbekü köşesi, tam donanımlı mutfak. Evcil hayvan kabul edilmez.

## Martı Aile Villası (6 kişi, 16.500 TL/gece)
140 m², 3 yatak odası, 24 m² ana havuz (1,4 m) ve 40 cm derinliğinde çocuk havuzu; havuz alanı çitli ve kapısı kilitlidir. Bebek yatağı, mama sandalyesi, küvet ve çocuk güvenlik kapıları (talep üzerine ücretsiz). Barbekü ve tam donanımlı mutfak vardır. Mini Bunga Çocuk Kulübü'ne yürüyerek 2 dakika. Evcil hayvan kabul edilmez.

## Mercan Balayı Süiti (2 kişi, 12.000 TL/gece)
65 m², 1 yatak odası (king size yuvarlak yatak), 15 m² özel havuz (1,2 m) ve deniz manzaralı jakuzi. Yalnızca 16 yaş üstü misafirler. Karşılama hediyesi (şarap, meyve tabağı), akşam turn-down servisi, odaya kahvaltı ve konaklama başına bir çiftler masajı (60 dk) fiyata dahildir. Evcil hayvan kabul edilmez. Çocuk ve bebek kabul edilmez.

## Akdeniz Saray Villa (10 kişi, 35.000 TL/gece)
320 m², 4 yatak odası (her biri en-suite banyolu), salonda 2 çekyat (10 kişi), 60 m² sonsuzluk havuzu (en derin 1,6 m), jakuzi, açık hava mutfağı, sinema köşesi, barbekü, 3 araçlık park. Talep üzerine özel şef (günlük 12.000 TL) ve villa görevlisi (günlük 4.500 TL). Evcil hayvan kabul edilir (hayvan başı gecelik 750 TL; en fazla 2). Konaklama için minimum süre yüksek sezonda 5 gecedir.

## Hangi villayı seçmeliyim?
- Çiftler ve romantik kaçamak için: Zeytin Plunge (en uygun fiyat), Lavanta Plunge (deniz manzaralı) veya Mercan Balayı Süiti (jakuzi, balayı).
- İki çift veya küçük aile (4-5 kişi) için: Mavi Ufuk Infinity (4) veya Gün Batımı Infinity (5).
- Küçük çocuklu aileler (4-6 kişi) için: Martı Aile Villası (çocuk havuzu ve çitli alan).
- Büyük gruplar, aile buluşmaları ve kutlamalar için: Akdeniz Saray Villa (10 kişi).
- Evcil hayvanla gelenler için: Zeytin Plunge, Lavanta Plunge veya Akdeniz Saray Villa.
- Engelli erişimi: bungalovlar ve Mavi Ufuk Infinity zemin kattadır; basamak yoktur.

## Ortak donanımlar ve olanaklar
Tüm üniteler: klima, Wi-Fi, 50" akıllı TV, kasa, saç kurutma makinesi, ütü ve masası (talep üzerine), bornoz ve terlik, havuz havluları, Nespresso makinesi. Mutfaklı üniteler (Mavi Ufuk, Gün Batımı, Martı Aile, Akdeniz Saray): ocak, fırın, buzdolabı, bulaşık makinesi ve temel mutfak gereçleri. Her ünitede çamaşır makinesi yoktur; çamaşır servisi resepsiyondan yaptırılabilir (kilo başı 300 TL, 24 saatte teslim).
"""))

# ---------------------------------------------------------------------------------------------
LONG_DOCS.append(("Politikalar", "İptal, Değişiklik ve İade Koşulları (ayrıntılı)", """
Bu doküman rezervasyon iptali, tarih değişikliği, iade süreci ve istisnai durumları ayrıntılı açıklar. Özet kural, "İptal politikası" kaydında yer alır; çelişki halinde bu ayrıntılı koşullar geçerlidir.

## Standart iptal kademeleri
- Giriş tarihinden 14 gün veya daha önce yapılan iptalde ödemenin tamamı iade edilir.
- Giriş tarihine 14 günden az, 7 gün veya daha fazla kala iptalde ödemenin %50'si iade edilir.
- Giriş tarihine 7 günden az kala iptalde, gelinmemesi (no-show) ve erken ayrılmalarda iade yapılmaz.
İptal süresi, yazılı iptal talebinin (e-posta veya telefon sonrası e-posta onayı) bize ulaştığı andan hesaplanır. İadeler, ödemenin yapıldığı karta 7-10 iş günü içinde yatar. Ödeme sırasında bankanın kestiği taksit ve komisyon farkları iade edilemez.

## Yüksek sezon istisnası (1 Temmuz-31 Ağustos)
Yüksek sezon rezervasyonlarında ücretsiz iptal süresi 21 gün, %50 iade süresi 21-10 gün arasıdır; 10 günden az kala iptalde iade yapılmaz. Akdeniz Saray Villa için yüksek sezonda ödemenin %30'u (kapora) hiçbir koşulda iade edilmez.

## Tarih değişikliği
Giriş tarihinden en az 10 gün önce, müsaitliğe bağlı olarak, bir kez ücretsiz tarih değişikliği yapılabilir. Fiyat farkı varsa farkı ödersiniz; yeni konaklama toplamı daha düşükse fark iade edilmez, hesabınızda hediye çeki olarak 12 ay saklanır. Yüksek sezona kaydırılan tarihler yüksek sezon koşullarına tabidir. Birden fazla değişiklik, iptal ve yeni rezervasyon sayılır.

## Erken ayrılma
Konaklama sırasında planlanandan önce ayrılırsanız kullanılmayan geceler için iade yapılmaz. Hastalık gibi belgeli mücbir sebeplerde (doktor raporu ile) kullanılmayan geceler için kredi (voucher) verilir.

## Mücbir sebepler
Doğal afet, savaş, salgın, resmi seyahat yasakları veya tesisin kapanmasını gerektiren olağanüstü durumlarda rezervasyon ücretsiz iptal veya tarih değişikliğine hakkı doğurur. Misafirin kişisel mücbir sebepleri (hastalık, uçuş iptali, vize reddi) için seyahat sigortası yaptırmanızı öneririz; tesis bu durumlarda iade yapmak zorunda değildir, ancak belgeli durumlarda iyi niyet kredisi sunabilir.

## Tesis kaynaklı iptaller
Tesisin rezervasyonu teknik veya güvenlik nedeniyle gerçekleştirememesi halinde (örneğin villa hasarı), aynı veya üst kategoride alternatif sunulur; kabul etmezseniz ödemenin tamamı 3 iş günü içinde iade edilir ve ayrıca 1 gecelik konaklama değerinde hediye çek verilir.

## Ödeme başarısız ve bekleyen rezervasyonlar
Rezervasyon sonrası 30 dakika içinde ödeme tamamlanmazsa tarihler serbest bırakılır; rezervasyon geçersiz sayılır. Ödeme başarısız olduysa aynı rezervasyon için yeni ödeme bağlantısı oluşturulabilir. Başarısız ödemelerde karttan çekilen tutar varsa 3 iş günü içinde bankanız tarafından iade edilir.

## Depozito ve hasar
Giriş sırasında alınan hasar depozitosu (bungalov 5.000 TL, villa 10.000 TL) kartta blokaj olarak tutulur ve hasar yoksa çıkıştan sonra 7 iş günü içinde serbest bırakılır. Çıkış sırasında yapılan kontrolde hasar, kayıp veya aşırı kirlilik tespit edilirse bedeli bloke tutardan tahsil edilir ve fark varsa kayıtlı karttan çekilir.

## Üçüncü taraf ve toplu rezervasyonlar
Acentalar veya aracılar üzerinden yapılan rezervasyonlarda ilgili acentanın iptal koşulları geçerlidir. 5 ve üzeri villa içeren grup rezervasyonlarında sözleşme ayrıca düzenlenir; standart iptal kademeleri uygulanmaz.

## İptal talebi nasıl yapılır?
İptal veya değişiklik için rezervasyon kodunuzla birlikte info@bungai.example adresine yazın veya resepsiyonu +90 242 555 01 23 numarasından arayın. Sohbet asistanı iptal işlemi yapamaz; yalnızca bilgi verir. İptal talebiniz alındığında e-posta ile onaylanır.
"""))

# ---------------------------------------------------------------------------------------------
LONG_DOCS.append(("Genel", "Kalkan ve Çevresi Gezi Rehberi", """
Resortumuz Kalkan'ın Kalamar Yolu üzerindedir; bölge, Likya yolu, antik kentler, koylar ve lezzetli restoranları ile bilinir. Aşağıdaki öneriler resepsiyondan organize edilebilir; mesafeler resortumuzdan itibarendir.

## Kalkan Merkez ve Eski Liman (3 km)
Beyaz badanalı taş evler, bugenvil dolu sokaklar ve deniz manzaralı terasları olan butik restoranlar. Ücretsiz servis aracımız saat başı kalkar. Akşam yemeği için rezervasyon yapılması önerilir. Çarşamba ve Cuma günleri açık hava pazarı kurulur (yöresel ürünler, zeytinyağı, baharat).

## Kaputaş Plajı (8 km, 12 dk)
Uçurumlar arasında turkuaz renkli küçük plaj; yüksek sezonda çok kalabalık olduğundan sabah 09:00'dan önce gitmenizi öneririz. Plaja 187 basamak iner; bebek arabası uygun değildir. Ücretsiz park yok, otopark 200 TL.

## Patara Plajı ve Antik Kenti (18 km, 25 dk)
Türkiye'nin en uzun plajlarından biri (18 km kumsal), caretta caretta yuvalama alanı. Plajda gece yürüyüşü ve ışık yasaktır. Antik kent Likya Birliği'nin başkentidir. Giriş ücreti müze kart ile ücretsiz veya yaklaşık 250 TL. Resort günlük servisi pazar günleri kişi başı 600 TL.

## Saklıkent Kanyonu (45 km, 55 dk)
Soğuk dağ suyuyla dolu 18 km'lik kanyon; ıslanmak için uygun ayakkabı gerekir. Alabalık restoranlarında yemek yenir. Bebek ve çok küçük çocuklar için uygun değildir. Transfer 2.200 TL (araç başı).

## Xanthos ve Letoon Antik Kentleri (40 km)
UNESCO Dünya Mirası listesindeki Likya kalıntıları. Tam gün gezi önerilir; kılavuzlu tur 2.800 TL kişi başıdır.

## Kaş (28 km, 35 dk)
Renkli sokaklar, dalış merkezleri, antik tiyatro ve gün batımı. Kaş'tan Meis (Yunanistan) adasına günübirlik feribot seferleri vardır (pasaport gerekli, yaz sezonunda her sabah).

## Tekne turları
12 Adalar tekne turu, Kekova batık şehir turu ve Kaputaş-Kalkan koyları turu resepsiyon aracılığıyla ayarlanır. Kekova turu kişi başı 2.900 TL (öğle yemeği dahil), resort Cumartesi tekne turu 3.500 TL'dir. Yüksek sezonda en az 2 gün önceden rezervasyon gerekir.

## Yamaç paraşütü
Fethiye Ölüdeniz'de tandem yamaç paraşütü (yaklaşık 95 km) kişi başı 4.500 TL; uçuş ağırlık ve hava durumuna bağlıdır. Transfer ayrıdır.

## Likya Yolu ve doğa yürüyüşleri
Likya Yolu'nun Kalkan-Kaş etabı (günlük 10-14 km) rehberli veya rehbersiz yapılabilir. Çarşamba günleri resortumuz ücretsiz kısa patika yürüyüşü düzenler. Yaz aylarında yürüyüşlerde sabah 07:00-10:00 arası önerilir; bol su, şapka ve güneş kremi şarttır.

## Alışveriş
Kalkan'da zeytinyağı, baharat, deri sandalet, seramik ve el işi ürünler bulunur. Banka ve ATM'ler Kalkan merkezde, resort içinde resepsiyonda ise döviz bozdurma (kısıtlı) yapılır.

## Sağlık ve acil
En yakın eczane Kalkan merkezde (3 km), en yakın devlet hastanesi Kaş (28 km) ve özel hastane Fethiye (85 km)'tedir. Resortun 7/24 çağrı üzerine doktoru vardır. Acil durumda 112'yi arayın veya resepsiyonu bilgilendirin.
"""))

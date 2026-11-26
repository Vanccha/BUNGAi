"""Bungalov / villa seed verisi. Görsel URL'lerinin hepsi curl ile doğrulandı (HTTP 200, image/jpeg)."""

U = "https://images.unsplash.com/photo-{}?w=1600&q=80"

BUNGALOWS = [
    dict(
        slug="zeytin-plunge-bungalov", name="Zeytin Plunge Bungalov", capacity=2, bedrooms=1, size_m2=38, price_per_night=6500,
        short_description="Zeytin ağaçları arasında, özel plunge havuzlu ve bahçeli çift kişilik bungalov.",
        description="Zeytin Plunge Bungalov, çiftler için tasarlanmış sakin bir kaçış noktasıdır. 12 m² özel plunge havuzu (derinlik 1,2 m), taş zeminli güneşlenme terası, iki şezlong ve gölgelik pergolası ile gün boyu serinleyebilirsiniz. Çit çevrili özel bahçesi sayesinde evcil hayvan kabul eden iki bungalovdan biridir. Kahvaltı fiyata dahildir.",
        amenities=["Özel Plunge Havuz (12 m²)", "Klima", "Ücretsiz Wi-Fi", "Özel Bahçe", "Pergola ve Şezlong", "Nespresso Kahve Makinesi", "Mini Bar", "Evcil Hayvan Kabul Edilir"],
        images=["1576013551627-0cc20b96c2a7", "1566073771259-6a8506099945", "1582719478250-c89cae4dc85b", "1445019980597-93fa8acb246c"],
    ),
    dict(
        slug="lavanta-plunge-bungalov", name="Lavanta Plunge Bungalov", capacity=2, bedrooms=1, size_m2=45, price_per_night=7800,
        short_description="Kısmi deniz manzaralı, 18 m² özel havuzlu romantik bungalov.",
        description="Lavanta Plunge Bungalov, tepeden Akdeniz'e açılan kısmi deniz manzarası ve 18 m² özel havuzuyla (derinlik 1,3 m) çiftlerin favorisidir. Ahşap pergolalı teras, açık hava duşu ve lavanta bahçesiyle donatılmıştır. Çit çevrili bahçesi nedeniyle evcil hayvan kabul eder. Kahvaltı fiyata dahildir.",
        amenities=["Özel Havuz (18 m²)", "Kısmi Deniz Manzarası", "Açık Hava Duşu", "Klima", "Ücretsiz Wi-Fi", "Pergolalı Teras", "Nespresso Kahve Makinesi", "Evcil Hayvan Kabul Edilir"],
        images=["1564013799919-ab600027ffc6", "1600585154340-be6161a56a0c", "1551882547-ff40c63fe5fa", "1610641818989-c2051b5e2cfd"],
    ),
    dict(
        slug="mavi-ufuk-infinity-villa", name="Mavi Ufuk Infinity Villa", capacity=4, bedrooms=2, size_m2=90, price_per_night=14500,
        short_description="Tam deniz manzaralı, 28 m² sonsuzluk havuzlu iki yatak odalı villa.",
        description="Mavi Ufuk Infinity Villa, ufuk çizgisine kavuşan 28 m² sonsuzluk havuzu (derinlik 1,4 m) ve geniş deniz manzaralı terasıyla en çok tercih edilen villalarımızdandır. İki yatak odası, açık plan salon ve mutfak, dış mekan yemek masası ve güneşlenme alanı bulunur. Kahvaltı fiyata dahildir; evcil hayvan kabul edilmez.",
        amenities=["Sonsuzluk Havuzu (28 m²)", "Tam Deniz Manzarası", "2 Yatak Odası", "Tam Donanımlı Mutfak", "Dış Mekan Yemek Masası", "Klima", "Ücretsiz Wi-Fi", "Güneşlenme Terası"],
        images=["1540541338287-41700207dee6", "1613490493576-7fde63acd811", "1600596542815-ffad4c1539a9", "1584132967334-10e028bd69f7"],
    ),
    dict(
        slug="gun-batimi-infinity-villa", name="Gün Batımı Infinity Villa", capacity=5, bedrooms=2, size_m2=110, price_per_night=18000,
        short_description="Batıya bakan 35 m² sonsuzluk havuzlu, gün batımı terasıyla 5 kişilik villa.",
        description="Gün Batımı Infinity Villa, Akdeniz'e bakan geniş teras ve 35 m² sonsuzluk havuzuyla (derinlik 1,5 m) gün batımı izlemek için en iyi konumdadır. İki yatak odası ve salonda çekyat ile beş kişiyi ağırlar. Açık hava barbekü köşesi, şezlonglu havuz kenarı ve kahvaltı dahildir. Evcil hayvan kabul edilmez.",
        amenities=["Sonsuzluk Havuzu (35 m²)", "Gün Batımı Terası", "Deniz Manzarası", "2 Yatak Odası + Çekyat", "Barbekü Köşesi", "Tam Donanımlı Mutfak", "Klima", "Ücretsiz Wi-Fi"],
        images=["1561501900-3701fa6a0864", "1602343168117-bb8ffe3e2e9f", "1512917774080-9991f1c4c750", "1580587771525-78b9dba3b914"],
    ),
    dict(
        slug="marti-aile-villasi", name="Martı Aile Villası", capacity=6, bedrooms=3, size_m2=140, price_per_night=16500,
        short_description="24 m² havuz ve ayrı çocuk havuzlu, çitli güvenli bahçeli 6 kişilik aile villası.",
        description="Martı Aile Villası çocuklu aileler için tasarlandı: 24 m² ana havuz (1,4 m) yanında 40 cm derinliğinde ayrı bir çocuk havuzu bulunur ve havuz alanı kilitli çitle çevrilidir. Üç yatak odası, çocuk dostu salon, bebek yatağı ve mama sandalyesi (talep üzerine) ile Mini Bunga Çocuk Kulübü'ne yürüme mesafesindedir. Kahvaltı dahildir; evcil hayvan kabul edilmez.",
        amenities=["Ana Havuz (24 m²)", "Çocuk Havuzu (40 cm)", "Çitli Havuz Alanı", "3 Yatak Odası", "Bebek Yatağı ve Mama Sandalyesi", "Tam Donanımlı Mutfak", "Barbekü", "Klima", "Ücretsiz Wi-Fi"],
        images=["1582268611958-ebfd161ef9cf", "1520250497591-112f2f40a3f4", "1564501049412-61c2a3083791", "1571896349842-33c89424de2d"],
    ),
    dict(
        slug="mercan-balayi-suiti", name="Mercan Balayı Süiti", capacity=2, bedrooms=1, size_m2=65, price_per_night=12000,
        short_description="Jakuzili, 15 m² özel havuzlu, yalnızca yetişkinlere özel balayı süiti.",
        description="Mercan Balayı Süiti; yuvarlak yatak, deniz manzaralı jakuzi ve 15 m² özel havuzu (derinlik 1,2 m) ile balayı ve yıl dönümleri için hazırlanmıştır. Yalnızca 16 yaş üstü misafirler kalabilir. Karşılama hediyesi (şarap ve meyve tabağı), akşam turn-down servisi ve odaya kahvaltı servisi fiyata dahildir. Evcil hayvan kabul edilmez.",
        amenities=["Özel Jakuzi", "Özel Havuz (15 m²)", "Deniz Manzarası", "King Size Yatak", "Karşılama Hediyesi", "Odaya Kahvaltı Servisi", "Klima", "Ücretsiz Wi-Fi", "Sadece Yetişkin (16+)"],
        images=["1602002418082-a4443e081dd1", "1537726235470-8504e3beef77", "1578683010236-d716f9a3f461", "1439130490301-25e322d88054"],
    ),
    dict(
        slug="akdeniz-saray-villa", name="Akdeniz Saray Villa", capacity=10, bedrooms=4, size_m2=320, price_per_night=35000,
        short_description="4 yatak odalı, 60 m² sonsuzluk havuzlu ve jakuzili 10 kişilik lüks villa.",
        description="Akdeniz Saray Villa, resortun amiral gemisidir: dört yatak odası, 60 m² sonsuzluk havuzu (derinlik en fazla 1,6 m), jakuzi, açık hava mutfağı, sinema köşesi ve 320 m² yaşam alanı. 10 kişiye kadar konaklama, talep üzerine özel şef ve villa görevlisi hizmeti sunar. Çit çevrili bahçesi nedeniyle evcil hayvan kabul edilir. Kahvaltı dahildir.",
        amenities=["Sonsuzluk Havuzu (60 m²)", "Jakuzi", "4 Yatak Odası", "Deniz Manzarası", "Açık Hava Mutfağı", "Sinema Köşesi", "Özel Şef (talep üzerine)", "Klima", "Ücretsiz Wi-Fi", "Evcil Hayvan Kabul Edilir"],
        images=["1523217582562-09d0def993a6", "1600607687939-ce8a6c25118c", "1455587734955-081b22074882", "1519046904884-53103b34b206"],
    ),
]

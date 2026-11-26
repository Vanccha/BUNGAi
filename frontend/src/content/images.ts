/** Tüm statik görseller (Unsplash). Her ID curl ile doğrulanmıştır (200 image/jpeg). */
const u = (id: string, w = 1600) => `https://images.unsplash.com/photo-${id}?w=${w}&q=80`

const ID = {
  infinityBay: '1543489822-c49534f3271f',       // koya bakan sonsuzluk havuzu
  womanLounge: '1556314231-2f7d9c122691',       // şezlongda dinlenen kadın
  womanPool: '1488345979593-09db0f85545f',      // havuzda kadın
  womanSwimInfinity: '1533070129449-d0ee17425ac4', // sonsuzluk havuzunda yüzen kadın
  sunHatPool: '1598041072698-794501a5fedf',     // bikini ve hasır şapka, turkuaz su
  bikiniOcean: '1500815845799-7748ca339f27',    // denize bakan havuzda bikinili kadın
  villaWhite: '1613977257365-aaae5a9817ff',     // havuzlu beyaz villa
  villaSky: '1600596542815-ffad4c1539a9',       // mavi gökyüzü altında beyaz villa
  villaLoungers: '1512917774080-9991f1c4c750',  // havuz kenarı şezlonglar
  villaModern: '1582268611958-ebfd161ef9cf',    // cam duvarlı modern havuzlu ev
  villaWood: '1596178067639-5c6e68aea6dc',      // havuz kenarında ahşap/beyaz ev
  villaGreen: '1613152184920-bc1c4ab7fd1d',     // yeşillikler içinde havuz
  villaHouse: '1582610116397-edb318620f90',     // havuzlu beyaz-kahve ev
  coupleHug: '1541089361501-9a9698b9baed',      // sarılan çift
  coupleTurquoise: '1776761420449-48c332b4a555',// turkuaz havuzda dinlenen çift
  friendsPool: '1534366381226-672074533fd3',    // havuzda kollarını açmış gülümseyen model
  couplePool: '1558920273-d45d40887ddb',        // havuz kenarında çift
  poolBeachGroup: '1662879587704-96705bdfb8a2', // plaj kenarı havuzda insanlar
  girlSwim: '1536331568701-0b15cbb1a918',       // havuzda yüzen kız
  familyPool: '1758530273449-71ee84763100',     // havuz başında aile
  womanFloating: '1470376619031-a6791e534bf0',  // suda süzülen kadın
  womanArms: '1534366381226-672074533fd3',      // kollarını açan kadın
  whiteBikiniPool: '1772305436752-4f5f7eaf279d',// beyaz bikinili havuzda kadın
  beachSand: '1603085429201-64dadaec4061',      // plaj kumu ve deniz
  womanBackWater: '1634045634161-b842d46ed840', // suda oturan kadın
  oceanViewPool: '1713843841925-6af6ed0df472',  // deniz manzaralı büyük havuz
  poolPeople: '1579069260841-d04ee739cc10',     // havuzda keyif yapan insanlar
  poolRings: '1598041072698-794501a5fedf',      // hasır şapkalı model, havuz kenarı
}

export const IMG = Object.fromEntries(
  Object.entries(ID).map(([k, id]) => [k, u(id)]),
) as Record<keyof typeof ID, string>
export const THUMB = Object.fromEntries(
  Object.entries(ID).map(([k, id]) => [k, u(id, 800)]),
) as Record<keyof typeof ID, string>

export const HERO = IMG.infinityBay
export const GALLERY: { src: string; alt: string; span?: string }[] = [
  { src: THUMB.whiteBikiniPool, alt: 'Villa havuzunda dinlenen misafir', span: 'row-span-2' },
  { src: THUMB.coupleTurquoise, alt: 'Turkuaz havuz başında çift' },
  { src: THUMB.villaLoungers, alt: 'Havuz kenarı şezlonglar' },
  { src: THUMB.familyPool, alt: 'Havuz başında aile keyfi', span: 'row-span-2' },
  { src: THUMB.womanSwimInfinity, alt: 'Sonsuzluk havuzunda yüzüş' },
  { src: THUMB.poolRings, alt: 'Havuz kenarında güneşlenen misafir' },
  { src: THUMB.womanLounge, alt: 'Şezlongda dinlenme' },
  { src: THUMB.friendsPool, alt: 'Havuzda yaz keyfi', span: 'md:row-span-2' },
  { src: THUMB.poolBeachGroup, alt: 'Plaj kenarında havuz' },
]
export const EXPERIENCE_IMG = {
  pool: IMG.womanSwimInfinity,
  beach: IMG.beachSand,
  spa: IMG.womanBackWater,
  dinner: IMG.oceanViewPool,
  kids: IMG.girlSwim,
}
export const LOCATION_IMG = IMG.villaSky

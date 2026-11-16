/**
 * Authoritative Store Logo Registry & Mapping for Ambience Mall Gurugram.
 * 
 * Maps real mall store directory names, OCR abbreviations, and aliases to
 * 100% verified, authentic brand logos stored locally in /store-logos/.
 *
 * Stores with ambiguous OCR text, unverified local counters, or generic services
 * return hasLogo: false, allowing components to cleanly render the neutral fallback icon.
 */

export interface BrandLogoEntry {
  brandName: string
  logoUrl: string
  category: string
}

export interface StoreLogoResult {
  hasLogo: boolean
  logoUrl: string | null
  brandName: string
  category?: string
}

/**
 * Master catalog of 126 authentic brand logos deployed locally.
 */
export const BRAND_CATALOG: Record<string, BrandLogoEntry> = {
  accessorize: {
    brandName: 'Accessorize London',
    logoUrl: '/store-logos/accessorize.svg',
    category: 'Fashion Accessories',
  },
  adidas: {
    brandName: 'Adidas',
    logoUrl: '/store-logos/adidas.svg',
    category: 'Sports & Athleisure',
  },
  aldo: {
    brandName: 'Aldo',
    logoUrl: '/store-logos/aldo.svg',
    category: 'Footwear & Accessories',
  },
  american_eagle: {
    brandName: 'American Eagle Outfitters',
    logoUrl: '/store-logos/american-eagle.svg',
    category: 'Fashion & Apparel',
  },
  anita_dongre: {
    brandName: 'Anita Dongre',
    logoUrl: '/store-logos/anita-dongre.svg',
    category: 'Luxury Designer',
  },
  anokhi: {
    brandName: 'Anokhi',
    logoUrl: '/store-logos/anokhi.png',
    category: 'Ethnic & Handcrafted',
  },
  apple: {
    brandName: 'Apple',
    logoUrl: '/store-logos/apple.svg',
    category: 'Electronics',
  },
  armani_exchange: {
    brandName: 'Armani Exchange',
    logoUrl: '/store-logos/armani-exchange.svg',
    category: 'Luxury Fashion',
  },
  arrow: {
    brandName: 'Arrow',
    logoUrl: '/store-logos/arrow.svg',
    category: 'Menswear & Formal',
  },
  asics: {
    brandName: 'Asics',
    logoUrl: '/store-logos/asics.svg',
    category: 'Sports & Footwear',
  },
  aurelia: {
    brandName: 'Aurelia',
    logoUrl: '/store-logos/aurelia.png',
    category: 'Ethnic Wear',
  },
  barista: {
    brandName: 'Barista Coffee',
    logoUrl: '/store-logos/barista.svg',
    category: 'Cafes & Dining',
  },
  bath_and_body_works: {
    brandName: 'Bath & Body Works',
    logoUrl: '/store-logos/bath-and-body-works.svg',
    category: 'Beauty & Fragrance',
  },
  benetton: {
    brandName: 'United Colors of Benetton',
    logoUrl: '/store-logos/benetton.svg',
    category: 'Fashion & Apparel',
  },
  bens_cookies: {
    brandName: "Ben's Cookies",
    logoUrl: '/store-logos/bens-cookies.svg',
    category: 'Bakeries & Desserts',
  },
  biba: {
    brandName: 'Biba',
    logoUrl: '/store-logos/biba.svg',
    category: 'Ethnic Wear',
  },
  birkenstock: {
    brandName: 'Birkenstock',
    logoUrl: '/store-logos/birkenstock.svg',
    category: 'Footwear',
  },
  bluestone: {
    brandName: 'BlueStone',
    logoUrl: '/store-logos/bluestone.png',
    category: 'Fine Jewellery',
  },
  bluorng: {
    brandName: 'Bluorng',
    logoUrl: '/store-logos/bluorng.png',
    category: 'Streetwear & Fashion',
  },
  bose: {
    brandName: 'Bose',
    logoUrl: '/store-logos/bose.svg',
    category: 'Audio & Electronics',
  },
  brooks_brothers: {
    brandName: 'Brooks Brothers',
    logoUrl: '/store-logos/brooks-brothers.svg',
    category: 'Luxury Menswear',
  },
  celio: {
    brandName: 'Celio',
    logoUrl: '/store-logos/celio.svg',
    category: 'Menswear & Casual',
  },
  chaayos: {
    brandName: 'Chaayos',
    logoUrl: '/store-logos/chaayos.jpg',
    category: 'Tea & Cafes',
  },
  chicco: {
    brandName: 'Chicco',
    logoUrl: '/store-logos/chicco.svg',
    category: 'Kids & Baby Care',
  },
  chique: {
    brandName: 'Chique',
    logoUrl: '/store-logos/chique.jpg',
    category: 'Womenswear',
  },
  clinique: {
    brandName: 'Clinique',
    logoUrl: '/store-logos/clinique.svg',
    category: 'Skincare & Cosmetics',
  },
  cover_story: {
    brandName: 'Cover Story',
    logoUrl: '/store-logos/cover-story.png',
    category: 'Fast Fashion',
  },
  crocs: {
    brandName: 'Crocs',
    logoUrl: '/store-logos/crocs.svg',
    category: 'Footwear',
  },
  croma: {
    brandName: 'Croma',
    logoUrl: '/store-logos/croma.png',
    category: 'Electronics & Appliances',
  },
  delsey: {
    brandName: 'Delsey Paris',
    logoUrl: '/store-logos/delsey.svg',
    category: 'Luggage & Travel',
  },
  diesel: {
    brandName: 'Diesel',
    logoUrl: '/store-logos/diesel.svg',
    category: 'Denim & Fashion',
  },
  dior: {
    brandName: 'Dior',
    logoUrl: '/store-logos/dior.svg',
    category: 'Luxury & Haute Couture',
  },
  dyson: {
    brandName: 'Dyson',
    logoUrl: '/store-logos/dyson.svg',
    category: 'Home & Hair Care',
  },
  ecco: {
    brandName: 'ECCO',
    logoUrl: '/store-logos/ecco.svg',
    category: 'Footwear & Leather',
  },
  estee_lauder: {
    brandName: 'Estée Lauder',
    logoUrl: '/store-logos/estee-lauder.svg',
    category: 'Luxury Cosmetics',
  },
  fabindia: {
    brandName: 'Fabindia',
    logoUrl: '/store-logos/fabindia.svg',
    category: 'Ethnic & Lifestyle',
  },
  forest_essentials: {
    brandName: 'Forest Essentials',
    logoUrl: '/store-logos/forest-essentials.png',
    category: 'Luxury Ayurveda',
  },
  forever_new: {
    brandName: 'Forever New',
    logoUrl: '/store-logos/forever-new.png',
    category: 'Womenswear',
  },
  frozen_bottle: {
    brandName: 'Frozen Bottle',
    logoUrl: '/store-logos/frozen-bottle.png',
    category: 'Desserts & Shakes',
  },
  gas: {
    brandName: 'GAS Jeans',
    logoUrl: '/store-logos/gas-jeans.svg',
    category: 'Denim & Casual',
  },
  geetanjali_salon: {
    brandName: 'Geetanjali Salon',
    logoUrl: '/store-logos/geetanjali-salon.png',
    category: 'Salon & Spa',
  },
  gkb_opticals: {
    brandName: 'GKB Opticals',
    logoUrl: '/store-logos/gkb-opticals.png',
    category: 'Eyewear & Opticals',
  },
  global_desi: {
    brandName: 'Global Desi',
    logoUrl: '/store-logos/global-desi.svg',
    category: 'Boho Ethnic',
  },
  go_colors: {
    brandName: 'Go Colors',
    logoUrl: '/store-logos/go-colors.png',
    category: 'Bottomwear',
  },
  hackett_london: {
    brandName: 'Hackett London',
    logoUrl: '/store-logos/hackett-london.svg',
    category: 'British Luxury Menswear',
  },
  hamleys: {
    brandName: "Hamleys",
    logoUrl: '/store-logos/hamleys.png',
    category: 'Toys & Games',
  },
  hidesign: {
    brandName: 'Hidesign',
    logoUrl: '/store-logos/hidesign.jpg',
    category: 'Leather Bags & Accessories',
  },
  home_centre: {
    brandName: 'Home Centre',
    logoUrl: '/store-logos/home-centre.png',
    category: 'Home & Furniture',
  },
  hugo_boss: {
    brandName: 'Hugo Boss',
    logoUrl: '/store-logos/hugo-boss.svg',
    category: 'Luxury Fashion',
  },
  hush_puppies: {
    brandName: 'Hush Puppies',
    logoUrl: '/store-logos/hush-puppies.png',
    category: 'Comfort Footwear',
  },
  isharya: {
    brandName: 'Isharya',
    logoUrl: '/store-logos/isharya.jpg',
    category: 'Designer Jewellery',
  },
  jaypore: {
    brandName: 'Jaypore',
    logoUrl: '/store-logos/jaypore.png',
    category: 'Artisanal & Ethnic',
  },
  jj_valaya: {
    brandName: 'JJ Valaya',
    logoUrl: '/store-logos/jj-valaya.png',
    category: 'Couture & Luxury',
  },
  kalyan_jewellers: {
    brandName: 'Kalyan Jewellers',
    logoUrl: '/store-logos/kalyan-jewellers.svg',
    category: 'Jewellery',
  },
  kama_ayurveda: {
    brandName: 'Kama Ayurveda',
    logoUrl: '/store-logos/kama-ayurveda.png',
    category: 'Ayurvedic Wellness',
  },
  kate_spade: {
    brandName: 'Kate Spade New York',
    logoUrl: '/store-logos/kate-spade.svg',
    category: 'Luxury Handbags & Fashion',
  },
  kazo: {
    brandName: 'Kazo',
    logoUrl: '/store-logos/kazo.webp',
    category: 'Womenswear',
  },
  kompanero: {
    brandName: 'Kompanero',
    logoUrl: '/store-logos/kompanero.png',
    category: 'Vintage Leather',
  },
  lacoste: {
    brandName: 'Lacoste',
    logoUrl: '/store-logos/lacoste.svg',
    category: 'Sport-Chic Apparel',
  },
  laduree: {
    brandName: 'Ladurée Paris',
    logoUrl: '/store-logos/laduree.png',
    category: 'Luxury Patisserie',
  },
  lego: {
    brandName: 'LEGO',
    logoUrl: '/store-logos/lego.svg',
    category: 'Toys & Collectibles',
  },
  lenovo: {
    brandName: 'Lenovo',
    logoUrl: '/store-logos/lenovo.svg',
    category: 'Laptops & Tech',
  },
  lenscrafters: {
    brandName: 'LensCrafters',
    logoUrl: '/store-logos/lenscrafters.png',
    category: 'Eyewear & Vision',
  },
  lenskart: {
    brandName: 'Lenskart',
    logoUrl: '/store-logos/lenskart.svg',
    category: 'Eyewear',
  },
  levis: {
    brandName: "Levi's",
    logoUrl: '/store-logos/levis.svg',
    category: 'Denim & Casual',
  },
  lladro: {
    brandName: 'Lladró',
    logoUrl: '/store-logos/lladro.svg',
    category: 'Porcelain Art & Luxury',
  },
  loccitane: {
    brandName: "L'Occitane en Provence",
    logoUrl: '/store-logos/loccitane.svg',
    category: 'Luxury Beauty & Skincare',
  },
  looks_salon: {
    brandName: 'Looks Salon',
    logoUrl: '/store-logos/looks-salon.svg',
    category: 'Unisex Salon',
  },
  louis_philippe: {
    brandName: 'Louis Philippe',
    logoUrl: '/store-logos/louis-philippe.svg',
    category: 'Premium Menswear',
  },
  mango: {
    brandName: 'Mango',
    logoUrl: '/store-logos/mango.svg',
    category: 'Fashion & Apparel',
  },
  marks_and_spencer: {
    brandName: 'Marks & Spencer',
    logoUrl: '/store-logos/marks-and-spencer.svg',
    category: 'Department Store & Apparel',
  },
  masaba: {
    brandName: 'House of Masaba',
    logoUrl: '/store-logos/masaba.png',
    category: 'Designer Fashion',
  },
  meena_bazaar: {
    brandName: 'Meena Bazaar',
    logoUrl: '/store-logos/meena-bazaar.png',
    category: 'Ethnic & Bridal',
  },
  mohanlal_sons: {
    brandName: 'Mohanlal Sons',
    logoUrl: '/store-logos/mohanlal-sons.png',
    category: 'Mens Ethnic & Formal',
  },
  mothercare: {
    brandName: 'Mothercare',
    logoUrl: '/store-logos/mothercare.svg',
    category: 'Maternity & Kids',
  },
  mulmul: {
    brandName: 'Mulmul',
    logoUrl: '/store-logos/mulmul.webp',
    category: 'Luxury Cotton Ethnic',
  },
  nars: {
    brandName: 'NARS Cosmetics',
    logoUrl: '/store-logos/nars.png',
    category: 'Luxury Beauty',
  },
  nespresso: {
    brandName: 'Nespresso',
    logoUrl: '/store-logos/nespresso.svg',
    category: 'Coffee & Machines',
  },
  new_balance: {
    brandName: 'New Balance',
    logoUrl: '/store-logos/new-balance.svg',
    category: 'Sneakers & Athleisure',
  },
  nicobar: {
    brandName: 'Nicobar',
    logoUrl: '/store-logos/nicobar.png',
    category: 'Contemporary Lifestyle',
  },
  nike: {
    brandName: 'Nike',
    logoUrl: '/store-logos/nike.svg',
    category: 'Sportswear & Footwear',
  },
  nykaa: {
    brandName: 'Nykaa',
    logoUrl: '/store-logos/nykaa.svg',
    category: 'Beauty & Cosmetics',
  },
  om_book_shop: {
    brandName: 'Om Book Shop',
    logoUrl: '/store-logos/om-book-shop.png',
    category: 'Books & Stationery',
  },
  oma_living: {
    brandName: 'Oma Living',
    logoUrl: '/store-logos/oma-living.png',
    category: 'Luxury Home Decor',
  },
  onitsuka_tiger: {
    brandName: 'Onitsuka Tiger',
    logoUrl: '/store-logos/onitsuka-tiger.svg',
    category: 'Heritage Sneakers',
  },
  pantaloons: {
    brandName: 'Pantaloons',
    logoUrl: '/store-logos/pantaloons.png',
    category: 'Family Fashion',
  },
  paul_bakery: {
    brandName: "Paul's Bakery",
    logoUrl: '/store-logos/paul-bakery.png',
    category: 'French Bakery & Cafe',
  },
  puma: {
    brandName: 'Puma',
    logoUrl: '/store-logos/puma.svg',
    category: 'Sportswear & Footwear',
  },
  ralph_lauren: {
    brandName: 'Polo Ralph Lauren',
    logoUrl: '/store-logos/ralph-lauren.svg',
    category: 'American Luxury',
  },
  ranna_gill: {
    brandName: 'Ranna Gill',
    logoUrl: '/store-logos/ranna-gill.webp',
    category: 'Designer Contemporary',
  },
  rare_rabbit: {
    brandName: 'Rare Rabbit',
    logoUrl: '/store-logos/rare-rabbit.png',
    category: 'Contemporary Menswear',
  },
  raymond: {
    brandName: 'The Raymond Shop',
    logoUrl: '/store-logos/raymond.svg',
    category: 'Fine Tailoring & Suiting',
  },
  reliance_digital: {
    brandName: 'Reliance Digital',
    logoUrl: '/store-logos/reliance-digital.svg',
    category: 'Consumer Electronics',
  },
  ritu_kumar: {
    brandName: 'Ritu Kumar',
    logoUrl: '/store-logos/ritu-kumar.png',
    category: 'Designer Couture',
  },
  rosso_brunello: {
    brandName: 'Rosso Brunello',
    logoUrl: '/store-logos/rosso-brunello.svg',
    category: 'Handcrafted Footwear',
  },
  sabhyata: {
    brandName: 'Sabhyata',
    logoUrl: '/store-logos/sabhyata.png',
    category: 'Ethnic Wear',
  },
  samsonite: {
    brandName: 'Samsonite',
    logoUrl: '/store-logos/samsonite.svg',
    category: 'Luggage & Travel',
  },
  samsung: {
    brandName: 'Samsung',
    logoUrl: '/store-logos/samsung.svg',
    category: 'Smartphones & Electronics',
  },
  saundh: {
    brandName: 'Saundh',
    logoUrl: '/store-logos/saundh.png',
    category: 'Everyday Luxury Ethnic',
  },
  skechers: {
    brandName: 'Skechers',
    logoUrl: '/store-logos/skechers.svg',
    category: 'Comfort Footwear',
  },
  soch: {
    brandName: 'Soch',
    logoUrl: '/store-logos/soch.png',
    category: 'Ethnic Wear',
  },
  sony: {
    brandName: 'Sony Center',
    logoUrl: '/store-logos/sony.svg',
    category: 'Electronics & Gaming',
  },
  starbucks: {
    brandName: 'Starbucks',
    logoUrl: '/store-logos/starbucks.svg',
    category: 'Coffee & Refreshments',
  },
  sunglass_hut: {
    brandName: 'Sunglass Hut',
    logoUrl: '/store-logos/sunglass-hut.svg',
    category: 'Designer Sunglasses',
  },
  superdry: {
    brandName: 'Superdry',
    logoUrl: '/store-logos/superdry.svg',
    category: 'Casual & Outerwear',
  },
  suvasa: {
    brandName: 'Suvasa',
    logoUrl: '/store-logos/suvasa.svg',
    category: 'Block Print & Cotton',
  },
  swarovski: {
    brandName: 'Swarovski',
    logoUrl: '/store-logos/swarovski.svg',
    category: 'Crystal Jewellery',
  },
  sweet_dreams: {
    brandName: 'Sweet Dreams',
    logoUrl: '/store-logos/sweet-dreams.png',
    category: 'Sleepwear & Loungewear',
  },
  taneira: {
    brandName: 'Taneira',
    logoUrl: '/store-logos/taneira.svg',
    category: 'Handcrafted Sarees',
  },
  tanishq: {
    brandName: 'Tanishq',
    logoUrl: '/store-logos/tanishq.svg',
    category: 'Precious Jewellery',
  },
  the_collective: {
    brandName: 'The Collective',
    logoUrl: '/store-logos/the-collective.png',
    category: 'Luxury Multi-Brand',
  },
  the_sleep_company: {
    brandName: 'The Sleep Company',
    logoUrl: '/store-logos/the-sleep-company.webp',
    category: 'SmartGrid Mattresses & Chairs',
  },
  the_souled_store: {
    brandName: 'The Souled Store',
    logoUrl: '/store-logos/the-souled-store.svg',
    category: 'Pop Culture Apparel',
  },
  tira: {
    brandName: 'Tira Beauty',
    logoUrl: '/store-logos/tira.webp',
    category: 'Luxury Beauty',
  },
  tissot: {
    brandName: 'Tissot',
    logoUrl: '/store-logos/tissot.svg',
    category: 'Swiss Watches',
  },
  titan: {
    brandName: 'Titan Company',
    logoUrl: '/store-logos/titan.svg',
    category: 'Watches & Eyewear',
  },
  tommy_hilfiger: {
    brandName: 'Tommy Hilfiger',
    logoUrl: '/store-logos/tommy-hilfiger.png',
    category: 'Classic American Cool',
  },
  trends: {
    brandName: 'Reliance Trends',
    logoUrl: '/store-logos/trends.jpg',
    category: 'Family Fashion',
  },
  tumi: {
    brandName: 'TUMI',
    logoUrl: '/store-logos/tumi.png',
    category: 'Luxury Travel Bags',
  },
  under_armour: {
    brandName: 'Under Armour',
    logoUrl: '/store-logos/under-armour.svg',
    category: 'Athletic Performance',
  },
  uniqlo: {
    brandName: 'UNIQLO',
    logoUrl: '/store-logos/uniqlo.svg',
    category: 'LifeWear & Apparel',
  },
  us_polo: {
    brandName: 'U.S. Polo Assn.',
    logoUrl: '/store-logos/us-polo-assn.png',
    category: 'Sporting Lifestyle',
  },
  van_heusen: {
    brandName: 'Van Heusen',
    logoUrl: '/store-logos/van-heusen.svg',
    category: 'Formal & Power Dressing',
  },
  victorias_secret: {
    brandName: "Victoria's Secret",
    logoUrl: '/store-logos/victorias-secret.svg',
    category: 'Lingerie & Beauty',
  },
  wow_momo: {
    brandName: 'Wow! Momo',
    logoUrl: '/store-logos/wow-momo.jpg',
    category: 'Quick Service Dining',
  },
  zara: {
    brandName: 'ZARA',
    logoUrl: '/store-logos/zara.svg',
    category: 'Fast Fashion & Trendwear',
  },
}

/**
 * Normalized lookup table mapping store directory names, OCR abbreviations,
 * and aliases directly to catalog keys.
 */
export const STORE_ALIASES: Record<string, string> = {
  // Accessories & Jewelry
  'access': 'accessorize',
  'accessorize': 'accessorize',
  'accessorize london': 'accessorize',
  'bluestone': 'bluestone',
  'bluestone mens': 'bluestone',
  'isharya': 'isharya',
  'kalyan jewellers': 'kalyan_jewellers',
  'kalyan': 'kalyan_jewellers',
  'swarovski': 'swarovski',
  'tanishq': 'tanishq',

  // Eyewear & Watches
  'gkb opticals': 'gkb_opticals',
  'lenscrafters': 'lenscrafters',
  'lenskart': 'lenskart',
  'sunglass hut': 'sunglass_hut',
  'tissot': 'tissot',
  'titan eye plus': 'titan',
  'world of titan': 'titan',
  '& helios': 'titan',
  'helios': 'titan',
  'world of watches': 'titan',
  'titan': 'titan',

  // Footwear & Bags
  'birker': 'birkenstock',
  'birkenstock': 'birkenstock',
  'crocs': 'crocs',
  'delse': 'delsey',
  'delsey': 'delsey',
  'delsey paris': 'delsey',
  'ecco shoes': 'ecco',
  'shoes': 'ecco',
  'ecco': 'ecco',
  'hidesign': 'hidesign',
  'hush puppies': 'hush_puppies',
  'pies': 'hush_puppies',
  'kompanero': 'kompanero',
  'rosso brunello': 'rosso_brunello',
  'samsonite': 'samsonite',
  'sonite': 'samsonite',
  'tumi': 'tumi',
  'aldo': 'aldo',

  // Electronics & Tech
  'apple': 'apple',
  'apple store': 'apple',
  'bose': 'bose',
  'croma': 'croma',
  'dyson': 'dyson',
  'lenovo': 'lenovo',
  'reliance': 'reliance_digital',
  'reliance digit': 'reliance_digital',
  'reliance digital': 'reliance_digital',
  'reliance digite': 'reliance_digital',
  'reliar': 'reliance_digital',
  'samsung': 'samsung',
  'sung': 'samsung',
  'sony': 'sony',
  'sony center': 'sony',

  // International Fashion & High Street
  'american eagle': 'american_eagle',
  'american eagle outfitters': 'american_eagle',
  'armani exchange': 'armani_exchange',
  'ax': 'armani_exchange',
  'arrow': 'arrow',
  'benetton (mens)': 'benetton',
  'united colors of': 'benetton',
  'united colors of benetton': 'benetton',
  'brooks brothers': 'brooks_brothers',
  'celio': 'celio',
  'cover story': 'cover_story',
  'diesel': 'diesel',
  'dior': 'dior',
  'christian dior': 'dior',
  'forever new': 'forever_new',
  'gas': 'gas',
  'gas jeans': 'gas',
  'hackett london': 'hackett_london',
  'hackett': 'hackett_london',
  'hugo boss': 'hugo_boss',
  'boss': 'hugo_boss',
  'kate': 'kate_spade',
  'kate oscar': 'kate_spade',
  'oscar': 'kate_spade',
  'kate spade': 'kate_spade',
  'kate spade new york': 'kate_spade',
  'kazo': 'kazo',
  'lacoste': 'lacoste',
  "levi's": 'levis',
  'levis': 'levis',
  'louis philippe': 'louis_philippe',
  'mango man': 'mango',
  'mango': 'mango',
  'mark': 'marks_and_spencer',
  'marks & spencer': 'marks_and_spencer',
  'marks and spencer': 'marks_and_spencer',
  'm&s': 'marks_and_spencer',
  'pantaloons': 'pantaloons',
  'polo ralph lauren': 'ralph_lauren',
  'ralph': 'ralph_lauren',
  'ralph lauren': 'ralph_lauren',
  'rare rabbit': 'rare_rabbit',
  'superdry': 'superdry',
  'the collective': 'the_collective',
  'the raymond shop': 'raymond',
  'raymond': 'raymond',
  'the souled store': 'the_souled_store',
  'tommy hilfiger': 'tommy_hilfiger',
  'tommy': 'tommy_hilfiger',
  'trends': 'trends',
  'reliance trends': 'trends',
  'trends woman': 'trends',
  'uniqlo': 'uniqlo',
  'us polo association': 'us_polo',
  'us polo': 'us_polo',
  'uspa': 'us_polo',
  'van heusen': 'van_heusen',
  'van heusen women': 'van_heusen',
  'heusen women': 'van_heusen',
  'victorias secret': 'victorias_secret',
  "victoria's secret": 'victorias_secret',
  'zara': 'zara',

  // Indian Ethnic & Designer
  'anita dongre': 'anita_dongre',
  'anokhi': 'anokhi',
  'aurelia': 'aurelia',
  'biba': 'biba',
  'bluorng': 'bluorng',
  'chique': 'chique',
  'fab india': 'fabindia',
  'fabindia': 'fabindia',
  'global desi': 'global_desi',
  'go colors': 'go_colors',
  'jaypore': 'jaypore',
  'jj valaya': 'jj_valaya',
  'masaba': 'masaba',
  'house of masaba': 'masaba',
  'meena': 'meena_bazaar',
  'meena bazaar': 'meena_bazaar',
  'meena bz': 'meena_bazaar',
  'mohanlal': 'mohanlal_sons',
  'mohanlal sons': 'mohanlal_sons',
  'mulmul': 'mulmul',
  'nicobar': 'nicobar',
  'ranna gill': 'ranna_gill',
  'ritu kumar': 'ritu_kumar',
  'kumar': 'ritu_kumar',
  'sabhyata': 'sabhyata',
  'saundh': 'saundh',
  'soch': 'soch',
  'suvasa': 'suvasa',
  'sweet dreams': 'sweet_dreams',
  'taneira': 'taneira',

  // Sports & Athleisure
  'adidas': 'adidas',
  'adidas kids': 'adidas',
  'lidas kids': 'adidas',
  'asics': 'asics',
  'new balance': 'new_balance',
  'nike': 'nike',
  'onitsuka tiger': 'onitsuka_tiger',
  'puma': 'puma',
  'skechers': 'skechers',
  'under armour': 'under_armour',

  // Beauty, Wellness & Salon
  'bath & body works': 'bath_and_body_works',
  'body': 'bath_and_body_works',
  'clinique': 'clinique',
  'estee': 'estee_lauder',
  'estee lauder': 'estee_lauder',
  'forest essentials': 'forest_essentials',
  'geetanjali salon': 'geetanjali_salon',
  'jali salon': 'geetanjali_salon',
  'kama ayurveda': 'kama_ayurveda',
  "l'occitane en provence": 'loccitane',
  "l'occitane": 'loccitane',
  'loccitane': 'loccitane',
  'looks unisex salo': 'looks_salon',
  'looks unisex salon': 'looks_salon',
  'looks salon': 'looks_salon',
  'nars': 'nars',
  'nykaa': 'nykaa',
  'tira': 'tira',

  // Kids & Toys
  'chicco': 'chicco',
  'chice': 'chicco',
  "hamley's": 'hamleys',
  'hamleys': 'hamleys',
  'lego': 'lego',
  'mothercar': 'mothercare',
  'mothercare': 'mothercare',

  // Home, Decor & Books
  'home centre': 'home_centre',
  'lladro': 'lladro',
  'om book shop': 'om_book_shop',
  '(oma': 'oma_living',
  'oma': 'oma_living',
  'oma living': 'oma_living',
  'the sleep company': 'the_sleep_company',

  // Dining, Cafes & Bakeries
  'barista': 'barista',
  "ben's cookies": 'bens_cookies',
  'bens cookies': 'bens_cookies',
  'chaayos': 'chaayos',
  'frozen bottle': 'frozen_bottle',
  'froze': 'frozen_bottle',
  'laduree': 'laduree',
  'nespresso': 'nespresso',
  "paul's bakery": 'paul_bakery',
  'paul bakery': 'paul_bakery',
  'starbucks': 'starbucks',
  'wow! momo': 'wow_momo',
  'wow momo': 'wow_momo',
}

/**
 * Normalizes input string for robust dictionary matching.
 */
export function normalizeStoreKey(rawName: string): string {
  return rawName
    .trim()
    .toLowerCase()
    .replace(/[^\w\s&'-]/g, '')
    .replace(/\s+/g, ' ')
}

/**
 * Main resolver to retrieve official store logo information.
 */
export function getStoreLogo(store?: {
  name?: string
  id?: string
  image?: string
  store_name?: string
}): StoreLogoResult {
  const storeName = store?.name || store?.store_name || store?.id || ''
  
  // If store.image is explicitly set to an existing valid URL or logo
  if (store?.image && typeof store.image === 'string' && store.image.length > 0) {
    return {
      hasLogo: true,
      logoUrl: store.image,
      brandName: storeName,
    }
  }

  if (!storeName) {
    return {
      hasLogo: false,
      logoUrl: null,
      brandName: '',
    }
  }

  const normalized = normalizeStoreKey(storeName)

  // 1. Direct alias lookup
  const aliasKey = STORE_ALIASES[normalized]
  if (aliasKey && BRAND_CATALOG[aliasKey]) {
    const entry = BRAND_CATALOG[aliasKey]
    return {
      hasLogo: true,
      logoUrl: entry.logoUrl,
      brandName: entry.brandName,
      category: entry.category,
    }
  }

  // 2. Direct catalog key lookup
  const directKey = normalized.replace(/[\s-]/g, '_')
  if (BRAND_CATALOG[directKey]) {
    const entry = BRAND_CATALOG[directKey]
    return {
      hasLogo: true,
      logoUrl: entry.logoUrl,
      brandName: entry.brandName,
      category: entry.category,
    }
  }

  // 3. Fallback: Clean unverified / OCR fragment
  return {
    hasLogo: false,
    logoUrl: null,
    brandName: storeName,
  }
}

from decimal import Decimal
from django.utils.text import slugify

from core.models import (
    Country, City, Airport, Hotel, AirportTransfer,
    Activity, Day, DayHotel, DayTransfer, DayActivity,
    Tour, TourDay, TourType, Bullet, TourBullet
)


def unique_slug(base):
    base = slugify(base) or "nomaya-tur"
    slug = base
    i = 2
    while Tour.objects.filter(slug=slug).exists():
        slug = f"{base}-{i}"
        i += 1
    return slug


def get_or_create_transfer(city, airport, hotel, price):
    transfer = AirportTransfer.objects.filter(
        city=city,
        airport=airport,
        hotel=hotel,
        direction="A2H"
    ).first()

    if transfer:
        return transfer

    return AirportTransfer.objects.create(
        city=city,
        airport=airport,
        hotel=hotel,
        direction="A2H",
        vehicle_type="Özel Araç",
        price=Decimal(price),
        price_currency="USD"
    )


def create_nomaya_tour(v):
    tour_type, _ = TourType.objects.get_or_create(name="Şehir Deneyimi")

    country, _ = Country.objects.get_or_create(
        name=v["ulke"],
        defaults={"iso2": v["iso2"]}
    )

    city, _ = City.objects.get_or_create(
        name=v["sehir"],
        country=country
    )

    airport, _ = Airport.objects.get_or_create(
        iata=v["iata"],
        defaults={
            "name": v["havalimani"],
            "city": city
        }
    )

    hotel, _ = Hotel.objects.get_or_create(
        name=v["otel"],
        city=city,
        defaults={
            "star": 4,
            "price_per_night": Decimal(v["otel_fiyat"]),
            "price_currency": "USD",
            "hotel_type": "hotel"
        }
    )

    transfer = get_or_create_transfer(
        city=city,
        airport=airport,
        hotel=hotel,
        price=v["transfer_fiyat"]
    )

    last_day = Day.objects.filter(city=city).order_by("-day_number").first()
    day_number = last_day.day_number + 1 if last_day else 1

    day = Day.objects.create(
        city=city,
        day_number=day_number,
        title=v["gun_baslik"],
        description=v["gun_aciklama"],
        bullets=v["bullets"],
        price_currency="USD"
    )

    for idx, item in enumerate(v["aktiviteler"], start=1):
        act = Activity.objects.create(
            title=item["title"],
            city=city,
            location_text=item["location"],
            duration_hours=Decimal(item["duration"]),
            price=Decimal(item["price"]),
            price_currency="USD",
            points=item["points"]
        )
        act.tour_types.add(tour_type)
        DayActivity.objects.create(day=day, activity=act, order=idx)

    DayHotel.objects.create(day=day, hotel=hotel, order=1)
    DayTransfer.objects.create(day=day, transfer=transfer, order=1)

    tour = Tour.objects.create(
        title=v["tur_baslik"],
        slug=unique_slug(v["slug"]),
        overview=v["overview"],
        info=v["info"],
        commission=Decimal("1.30"),
        price_currency="USD",
        badge_text=v["rozet"],
        is_published=True
    )

    tour.places_covered.add(city)
    tour.tour_types.add(tour_type)

    TourDay.objects.create(
        tour=tour,
        day=day,
        order=1,
        title=v["tur_gun_baslik"]
    )

    for idx, text in enumerate(v["highlights"], start=1):
        bullet, _ = Bullet.objects.get_or_create(
            text=text,
            defaults={
                "icon": "check",
                "tags": v["tags"]
            }
        )

        TourBullet.objects.create(
            tour=tour,
            bullet=bullet,
            section="highlights",
            order=idx
        )

    day.recompute_price()
    tour.recompute_item_counts()
    tour.recompute_price()

    print(f"OK: {tour.title} | Gün: {day.day_number} | Fiyat: {tour.price} USD")
    return tour


TOURS = [
    {
        "ulke": "Japonya",
        "iso2": "JP",
        "sehir": "Kyoto",
        "iata": "KIX",
        "havalimani": "Kansai Uluslararası Havalimanı",
        "otel": "Kyoto Gion Butik Otel",
        "otel_fiyat": "130.00",
        "transfer_fiyat": "55.00",
        "gun_baslik": "Kyoto’da Yaşayan Bir Gün 🇯🇵",
        "gun_aciklama": "Kırmızı tapınak kapıları, çay evleri, bambu ormanı, eski sokaklar ve fener ışıklarıyla tasarlanmış zamansız bir Kyoto günü.",
        "bullets": [
            "⛩️ Fushimi Inari’de sabah yürüyüşü",
            "🍵 Geleneksel çay evi molası",
            "🎋 Arashiyama Bambu Ormanı",
            "🍱 Kyoto mutfağı",
            "👘 Gion sokakları",
            "🛕 Yasaka Tapınağı",
            "🌊 Kamo Nehri kıyısı",
            "🌙 Fener ışıkları altında kapanış"
        ],
        "aktiviteler": [
            {
                "title": "08:00 Fushimi Inari Sabahı ⛩️",
                "location": "Fushimi Inari Taisha",
                "duration": "1.50",
                "price": "0",
                "points": [
                    "Gün kırmızı torii kapıları arasında yavaş bir yürüyüşle başlar.",
                    "Fushimi Inari’nin bereket, ticaret ve koruyucu ruhlarla ilişkisi anlatılır.",
                    "Sabah erken saatte tapınağın sessiz atmosferi hissedilir.",
                    "Kyoto’nun Tokyo’dan farklı olarak neden daha geleneksel kaldığı açıklanır."
                ]
            },
            {
                "title": "10:00 Geleneksel Çay Evi Molası 🍵",
                "location": "Higashiyama",
                "duration": "1.00",
                "price": "18",
                "points": [
                    "Ahşap evlerin arasında küçük bir çay evinde mola verilir.",
                    "Matcha kültürünün Japon günlük yaşamındaki yeri anlatılır.",
                    "Çay seremonisinin acele etmeme, dikkat ve sadelik duygusuyla ilişkisi açıklanır.",
                    "Küçük bahçeler, dar geçitler ve sessiz servis anlayışı deneyimlenir."
                ]
            },
            {
                "title": "11:30 Arashiyama Bambu Ormanı 🎋",
                "location": "Arashiyama",
                "duration": "1.50",
                "price": "0",
                "points": [
                    "Bambu koridorları arasında kısa ama etkileyici bir yürüyüş yapılır.",
                    "Japon estetiğinde doğanın neden bu kadar merkezi olduğu anlatılır.",
                    "Bölgedeki nehir, köprü ve küçük dükkânlar keşfedilir.",
                    "Kyoto’nun sadece tapınaklardan değil, doğayla kurduğu bağdan oluştuğu hissedilir."
                ]
            },
            {
                "title": "13:30 Kyoto Mutfağı Öğle Molası 🍱",
                "location": "Arashiyama Çevresi",
                "duration": "1.25",
                "price": "28",
                "points": [
                    "Kyoto mutfağının zarif, mevsimsel ve dengeli yapısı anlatılır.",
                    "Küçük porsiyonlar, sade sunumlar ve yerel malzemeler üzerinden şehir kültürü okunur.",
                    "Aile işletmesi hissi veren bir restoranda öğle molası yapılır.",
                    "Yemek, bu rotada sadece ihtiyaç değil, şehirle bağ kurma anı olur."
                ]
            },
            {
                "title": "15:00 Gion Sokaklarında Eski Kyoto 👘",
                "location": "Gion",
                "duration": "1.25",
                "price": "0",
                "points": [
                    "Dar taş sokaklar, ahşap evler ve eski eğlence kültürü keşfedilir.",
                    "Geyşa kültürü yüzeysel bir gösteri gibi değil, disiplinli bir sanat geleneği olarak anlatılır.",
                    "Bölgede sessiz yürüyüşün ve saygılı gözlemin önemi vurgulanır.",
                    "Eski Kyoto’nun gündelik hayattan çok bir atmosfer gibi yaşandığı hissedilir."
                ]
            },
            {
                "title": "17:00 Yasaka Tapınağı ve Akşam Işığı 🛕",
                "location": "Yasaka Tapınağı",
                "duration": "1.00",
                "price": "0",
                "points": [
                    "Gün batımına yaklaşırken Yasaka Tapınağı ziyaret edilir.",
                    "Kyoto’daki festivaller, tapınak gelenekleri ve mahalle kültürü anlatılır.",
                    "Fenerler yanmaya başladıkça şehrin ruhani yüzü belirginleşir.",
                    "Bu durak gündüzden geceye geçişin yumuşak kapısı olur."
                ]
            },
            {
                "title": "18:30 Kamo Nehri Kıyısında Yavaşlama 🌊",
                "location": "Kamo Nehri",
                "duration": "1.00",
                "price": "0",
                "points": [
                    "Nehir kıyısında yürüyenler, bisikletliler ve oturan gençler gözlemlenir.",
                    "Kyoto’nun sadece geçmişte yaşayan bir şehir değil, bugünün sakin ritmine sahip olduğu anlatılır.",
                    "Nehir kenarı, günün yoğun kültürel duraklarından sonra nefes alma alanı olur.",
                    "Şehir burada daha kişisel, daha gündelik ve daha yakın hissedilir."
                ]
            },
            {
                "title": "20:00 Fener Işıkları Altında Kapanış 🌙",
                "location": "Pontocho ve Gion Çevresi",
                "duration": "1.25",
                "price": "12",
                "points": [
                    "Dar sokaklar fener ışıklarıyla bambaşka bir atmosfere dönüşür.",
                    "Ahşap cepheler, küçük restoranlar ve sessiz geçitler arasında yürünür.",
                    "Sabahın tapınak sessizliği ile gecenin zarif ışıkları birbirine bağlanır.",
                    "Kyoto hafızada huzurlu, ölçülü ve zamansız bir şehir olarak kalır."
                ]
            }
        ],
        "tur_baslik": "Kyoto’da Bir Gün 🇯🇵",
        "slug": "kyoto-bir-gun",
        "overview": "Kyoto’yu tapınak kapıları, çay evleri, bambu ormanı, Gion sokakları ve fener ışıklarıyla tek günde hissettiren zarif şehir deneyimi.",
        "info": "Bu rota Fushimi Inari’den Arashiyama’ya, Gion’dan Kamo Nehri’ne uzanır ve Kyoto’nun hem ruhani hem gündelik yüzünü bir araya getirir.",
        "rozet": "Japonya Deneyimi 🇯🇵",
        "tur_gun_baslik": "1. Gün: Kyoto’nun İçinden Geçmek",
        "highlights": [
            "⛩️ Fushimi Inari sabahı",
            "🍵 Geleneksel çay evi deneyimi",
            "🎋 Arashiyama Bambu Ormanı",
            "👘 Gion sokakları",
            "🌊 Kamo Nehri kıyısı",
            "🌙 Fener ışıkları altında kapanış"
        ],
        "tags": "japonya,kyoto,sehir,deneyim"
    },
    {
        "ulke": "Fas",
        "iso2": "MA",
        "sehir": "Marakeş",
        "iata": "RAK",
        "havalimani": "Marakeş Menara Uluslararası Havalimanı",
        "otel": "Marakeş Medina Riad Otel",
        "otel_fiyat": "90.00",
        "transfer_fiyat": "22.00",
        "gun_baslik": "Marakeş’te Yaşayan Bir Gün 🇲🇦",
        "gun_aciklama": "Medina sokakları, saray avluları, çarşılar, nane çayı ve akşam meydanıyla tasarlanmış renkli bir Marakeş günü.",
        "bullets": [
            "☀️ Medina sokaklarında sabah",
            "☕ Çatı katında nane çayı",
            "🌴 Bahia Sarayı",
            "🛍️ Çarşı kültürü",
            "🍲 Fas mutfağı",
            "🌇 Jemaa el-Fna Meydanı",
            "🔥 Akşam gösterileri",
            "🏨 Riad’a dönüş"
        ],
        "aktiviteler": [
            {
                "title": "08:30 Riad’dan Medina’ya Çıkış ☀️",
                "location": "Medina",
                "duration": "0.75",
                "price": "0",
                "points": [
                    "Gün geleneksel bir riad avlusundan dışarı adım atarak başlar.",
                    "Dar sokaklar, kırmızı duvarlar ve sabah hazırlığındaki dükkânlar gözlemlenir.",
                    "Marakeş’in labirent gibi yapısının tesadüf değil, şehir hafızasının parçası olduğu anlatılır.",
                    "İlk bölümde amaç yolu bitirmek değil, şehrin ritmine alışmaktır."
                ]
            },
            {
                "title": "09:30 Çatı Katında Nane Çayı ☕",
                "location": "Medina Çatı Kafesi",
                "duration": "1.00",
                "price": "8",
                "points": [
                    "Bir çatı kafesinde nane çayı molası verilir.",
                    "Fas’ta çayın misafirperverlik, sohbet ve yavaşlama ile ilişkisi anlatılır.",
                    "Yukarıdan Medina’nın terasları, minareleri ve dar sokak düzeni izlenir.",
                    "Şehir kalabalık olsa da yukarıdan bakınca daha anlaşılır hale gelir."
                ]
            },
            {
                "title": "11:00 Bahia Sarayı ve Avlu Kültürü 🌴",
                "location": "Bahia Sarayı",
                "duration": "1.25",
                "price": "12",
                "points": [
                    "Sarayın avluları, süslemeleri ve gölge oyunları keşfedilir.",
                    "Fas mimarisinde içe dönük yaşam anlayışı anlatılır.",
                    "Mozaikler, ahşap işçiliği ve bahçe düzeni üzerinden zanaatkârlık okunur.",
                    "Bu durak Marakeş’in dışarıdaki kaos ile içerideki huzur arasındaki karşıtlığını gösterir."
                ]
            },
            {
                "title": "13:00 Fas Sofrası ve Baharatlar 🍲",
                "location": "Medina Restoranı",
                "duration": "1.50",
                "price": "24",
                "points": [
                    "Tajin, kuskus ve baharat kültürü üzerinden Fas mutfağı anlatılır.",
                    "Yemeklerin sadece lezzet değil, aile ve paylaşım kültürüyle ilişkisi açıklanır.",
                    "Tarçın, kimyon, safran ve kuru meyve tatları öne çıkar.",
                    "Öğle molası, şehrin kokularını sofrada toplar."
                ]
            },
            {
                "title": "15:00 Çarşı Sokaklarında Zanaat Keşfi 🛍️",
                "location": "Marakeş Çarşıları",
                "duration": "1.50",
                "price": "0",
                "points": [
                    "Dericiler, halıcılar, bakırcılar ve baharat dükkânları arasında yürünür.",
                    "Pazarlık kültürünün sadece fiyat değil, sosyal bir oyun olduğu anlatılır.",
                    "Her sokakta farklı bir zanaatın izleri görülür.",
                    "Bu bölüm Marakeş’i yaşayan bir atölye gibi hissettirir."
                ]
            },
            {
                "title": "17:00 Sessiz Avlu Molası 🌿",
                "location": "Medina İç Avlu",
                "duration": "0.75",
                "price": "6",
                "points": [
                    "Kalabalığın ardından küçük bir iç avluda mola verilir.",
                    "Fas şehirlerinde gölge, su ve avlunun neden önemli olduğu anlatılır.",
                    "Gün ortasının yoğunluğu burada yumuşar.",
                    "Bu durak, Marakeş’i sadece hareketli değil aynı zamanda derin ve sakin gösterir."
                ]
            },
            {
                "title": "18:30 Jemaa el-Fna’da Akşam Dönüşümü 🌇",
                "location": "Jemaa el-Fna Meydanı",
                "duration": "1.50",
                "price": "0",
                "points": [
                    "Meydanın gündüzden geceye nasıl değiştiği izlenir.",
                    "Yemek tezgâhları, hikâye anlatıcıları, müzisyenler ve kalabalıklar gözlemlenir.",
                    "Jemaa el-Fna’nın Marakeş’in sahnesi gibi çalıştığı anlatılır.",
                    "Gün burada şehir tiyatrosuna dönüşür."
                ]
            },
            {
                "title": "20:30 Riad’a Dönüş ve Kapanış 🏨",
                "location": "Medina Riad",
                "duration": "0.50",
                "price": "0",
                "points": [
                    "Gün sonunda dar sokaklardan riad’a geri dönülür.",
                    "Saray, çarşı, baharat, çay ve meydan tek bir deneyim olarak tamamlanır.",
                    "Marakeş hafızada renkli, yoğun, kokulu ve masalsı bir şehir olarak kalır.",
                    "Kapanışta şehirden çok, bir atmosfer yaşanmış gibi hissedilir."
                ]
            }
        ],
        "tur_baslik": "Marakeş’te Bir Gün 🇲🇦",
        "slug": "marakes-bir-gun",
        "overview": "Marakeş’i Medina sokakları, saray avluları, çarşı kültürü, Fas mutfağı ve akşam meydanıyla tek günde hissettiren yoğun şehir deneyimi.",
        "info": "Bu rota riad’dan Medina’ya, Bahia Sarayı’ndan çarşılara ve Jemaa el-Fna Meydanı’na uzanır.",
        "rozet": "Fas Deneyimi 🇲🇦",
        "tur_gun_baslik": "1. Gün: Marakeş’in İçinden Geçmek",
        "highlights": [
            "☀️ Medina sokakları",
            "☕ Nane çayı molası",
            "🌴 Bahia Sarayı",
            "🛍️ Çarşı kültürü",
            "🍲 Fas mutfağı",
            "🌇 Jemaa el-Fna akşamı"
        ],
        "tags": "fas,marakes,sehir,deneyim"
    },
    {
        "ulke": "Peru",
        "iso2": "PE",
        "sehir": "Cusco",
        "iata": "CUZ",
        "havalimani": "Alejandro Velasco Astete Uluslararası Havalimanı",
        "otel": "Cusco San Blas Butik Otel",
        "otel_fiyat": "70.00",
        "transfer_fiyat": "18.00",
        "gun_baslik": "Cusco’da Yaşayan Bir Gün 🇵🇪",
        "gun_aciklama": "İnka taş sokakları, And Dağları havası, pazarlar, San Blas ve altın saat manzaralarıyla tasarlanmış yüksek rakımlı bir Cusco günü.",
        "bullets": [
            "☀️ Plaza de Armas sabahı",
            "🧱 İnka taş sokakları",
            "☕ San Blas kahve molası",
            "🏛️ Sacsayhuaman",
            "🍲 Peru mutfağı",
            "🎨 San Blas atölyeleri",
            "🌄 And Dağları manzarası",
            "🌙 Şehir ışıkları"
        ],
        "aktiviteler": [
            {
                "title": "08:30 Plaza de Armas Sabahı ☀️",
                "location": "Plaza de Armas",
                "duration": "1.00",
                "price": "0",
                "points": [
                    "Gün Cusco’nun tarihi kalbi olan meydanda başlar.",
                    "İspanyol koloni mimarisi ile İnka temellerinin nasıl iç içe geçtiği anlatılır.",
                    "Yüksek rakım nedeniyle güne yavaş ve dikkatli başlanır.",
                    "Meydan, Cusco’nun hem geçmiş hem bugünkü sosyal merkezi olarak okunur."
                ]
            },
            {
                "title": "10:00 İnka Taş Sokakları 🧱",
                "location": "Hatun Rumiyoc",
                "duration": "1.00",
                "price": "0",
                "points": [
                    "İnka taş işçiliği ve kusursuz duvar yapısı keşfedilir.",
                    "Taşların harçsız şekilde nasıl bir arada kaldığı anlatılır.",
                    "Cusco’nun fetih sonrası bile İnka hafızasını taşıdığı gösterilir.",
                    "Sokaklar burada açık hava tarih kitabı gibi deneyimlenir."
                ]
            },
            {
                "title": "11:30 San Blas Kahve Molası ☕",
                "location": "San Blas",
                "duration": "1.00",
                "price": "8",
                "points": [
                    "Yokuşlu sokaklardan San Blas mahallesine çıkılır.",
                    "Küçük kafeler, sanat atölyeleri ve taş evler arasında mola verilir.",
                    "Peru kahvesi ve And şehirlerindeki yavaş yaşam anlatılır.",
                    "Bu durak Cusco’nun bohem ve yaratıcı yüzünü açar."
                ]
            },
            {
                "title": "13:00 Peru Mutfağı Öğle Molası 🍲",
                "location": "San Blas veya Merkez",
                "duration": "1.25",
                "price": "20",
                "points": [
                    "Kinoa, patates çeşitleri, mısır ve yerel tatlar üzerinden Peru mutfağı anlatılır.",
                    "And coğrafyasının yemek kültürünü nasıl şekillendirdiği açıklanır.",
                    "Öğle molası yüksek rakımda yavaşlama ve enerji toplama anı olur.",
                    "Yemek, Cusco’nun doğayla bağını gösterir."
                ]
            },
            {
                "title": "15:00 Sacsayhuaman ve Taş Hafızası 🏛️",
                "location": "Sacsayhuaman",
                "duration": "1.75",
                "price": "18",
                "points": [
                    "Dev taş bloklardan oluşan arkeolojik alan keşfedilir.",
                    "İnka mühendisliği ve törensel alanların önemi anlatılır.",
                    "Yukarıdan Cusco’nun vadi içindeki yerleşimi görülür.",
                    "Bu durak şehir ile dağların birbirinden ayrılamadığını hissettirir."
                ]
            },
            {
                "title": "17:15 San Blas Atölyeleri 🎨",
                "location": "San Blas",
                "duration": "1.00",
                "price": "0",
                "points": [
                    "Mahalledeki küçük sanat atölyeleri ve el işi dükkânları gezilir.",
                    "Cusco’nun sadece geçmişten değil, bugünün üretim kültüründen de beslendiği anlatılır.",
                    "Taş sokaklar akşam ışığında daha sıcak bir renge bürünür.",
                    "Bu bölüm şehrin insan ölçeğindeki ruhunu güçlendirir."
                ]
            },
            {
                "title": "18:30 And Dağları Altında Altın Saat 🌄",
                "location": "San Blas Seyir Noktası",
                "duration": "1.00",
                "price": "0",
                "points": [
                    "Şehir altın saat ışığında yukarıdan izlenir.",
                    "Çatılar, kiliseler ve dağ silüeti birlikte görülür.",
                    "Cusco’nun neden sadece bir şehir değil, eski bir başkent hissi verdiği anlatılır.",
                    "Günün tüm katmanları bu manzarada birleşir."
                ]
            },
            {
                "title": "20:00 Plaza Işıkları ve Otele Dönüş 🌙",
                "location": "Plaza de Armas",
                "duration": "0.75",
                "price": "0",
                "points": [
                    "Akşam ışıkları altında meydana geri dönülür.",
                    "Sabah görülen meydanın gece daha törensel bir hale geldiği fark edilir.",
                    "İnka taşları, kahve, yemek ve dağ manzarası tek deneyime dönüşür.",
                    "Cusco hafızada yüksek, eski, güçlü ve mistik bir şehir olarak kalır."
                ]
            }
        ],
        "tur_baslik": "Cusco’da Bir Gün 🇵🇪",
        "slug": "cusco-bir-gun",
        "overview": "Cusco’yu İnka taş sokakları, San Blas kahveleri, Peru mutfağı ve And Dağları manzarasıyla tek günde hissettiren yüksek rakımlı şehir deneyimi.",
        "info": "Bu rota Plaza de Armas’tan San Blas’a, İnka sokaklarından Sacsayhuaman’a uzanır.",
        "rozet": "Peru Deneyimi 🇵🇪",
        "tur_gun_baslik": "1. Gün: Cusco’nun İçinden Geçmek",
        "highlights": [
            "☀️ Plaza de Armas sabahı",
            "🧱 İnka taş sokakları",
            "☕ San Blas kahve molası",
            "🏛️ Sacsayhuaman",
            "🌄 And Dağları manzarası"
        ],
        "tags": "peru,cusco,sehir,deneyim"
    }
]

TOURS += [
    {
        "ulke": "Gürcistan",
        "iso2": "GE",
        "sehir": "Tiflis",
        "iata": "TBS",
        "havalimani": "Tiflis Uluslararası Havalimanı",
        "otel": "Tiflis Eski Şehir Butik Otel",
        "otel_fiyat": "65.00",
        "transfer_fiyat": "20.00",
        "gun_baslik": "Tiflis’te Yaşayan Bir Gün 🇬🇪",
        "gun_aciklama": "Eski şehir sokakları, kükürt hamamları, teleferik, kale manzarası, Gürcü sofrası ve akşam ışıklarıyla tasarlanmış sıcak bir Tiflis günü.",
        "bullets": [
            "☕ Eski Tiflis sokakları",
            "♨️ Kükürt hamamları",
            "🚠 Teleferik yolculuğu",
            "🏰 Narikala Kalesi",
            "🍷 Gürcü şarap kültürü",
            "🍽️ Khinkali ve haçapuri",
            "🌉 Barış Köprüsü",
            "🌙 Eski şehirde kapanış"
        ],
        "aktiviteler": [
            {
                "title": "08:30 Eski Tiflis Sabahı ☕",
                "location": "Eski Tiflis",
                "duration": "1.00",
                "price": "6",
                "points": [
                    "Gün ahşap balkonlu eski Tiflis sokaklarında başlar.",
                    "Şehrin Pers, Rus, Osmanlı ve Avrupa etkilerini nasıl taşıdığı anlatılır.",
                    "Küçük kafeler, dar sokaklar ve renkli evler arasında yavaş yürünür.",
                    "Tiflis ilk andan itibaren katmanlı, sıcak ve biraz da dağınık hissedilir."
                ]
            },
            {
                "title": "10:00 Kükürt Hamamları Bölgesi ♨️",
                "location": "Abanotubani",
                "duration": "1.00",
                "price": "0",
                "points": [
                    "Kubbe çatılı kükürt hamamları çevresinde yürünür.",
                    "Tiflis’in kuruluş hikâyesi ve sıcak su kaynaklarıyla ilişkisi anlatılır.",
                    "Hamam kültürünün şehir kimliğinde neden önemli olduğu açıklanır.",
                    "Bu durak Tiflis’in hem bedensel hem tarihsel hafızasını gösterir."
                ]
            },
            {
                "title": "11:30 Teleferik ve Narikala Kalesi 🚠",
                "location": "Narikala Kalesi",
                "duration": "1.50",
                "price": "5",
                "points": [
                    "Teleferikle eski şehrin üzerinden kaleye çıkılır.",
                    "Narikala Kalesi’nin savunma ve şehir manzarası açısından önemi anlatılır.",
                    "Kura Nehri, eski mahalleler ve modern yapılar birlikte görülür.",
                    "Tiflis’in neden vadinin içine yerleşmiş dramatik bir şehir olduğu hissedilir."
                ]
            },
            {
                "title": "13:30 Gürcü Sofrası 🍽️",
                "location": "Eski Şehir Restoranı",
                "duration": "1.50",
                "price": "22",
                "points": [
                    "Khinkali, haçapuri ve cevizli mezeler üzerinden Gürcü mutfağı anlatılır.",
                    "Gürcü sofrasının sadece yemek değil, paylaşım ve misafirperverlik kültürü olduğu açıklanır.",
                    "Yerel tatlar şehirle duygusal bir bağ kurar.",
                    "Bu durak Tiflis’i en sıcak haliyle hissettirir."
                ]
            },
            {
                "title": "15:30 Şarap Kültürü ve Küçük Mahzenler 🍷",
                "location": "Eski Tiflis",
                "duration": "1.00",
                "price": "14",
                "points": [
                    "Gürcistan’ın dünyanın en eski şarap kültürlerinden birine sahip olduğu anlatılır.",
                    "Toprak küplerde şarap yapım geleneği açıklanır.",
                    "Küçük mahzenler ve yerel üreticiler üzerinden şehir daha samimi okunur.",
                    "Şarap burada lüks değil, günlük hayatın ve tarihin parçasıdır."
                ]
            },
            {
                "title": "17:00 Barış Köprüsü ve Modern Tiflis 🌉",
                "location": "Barış Köprüsü",
                "duration": "1.00",
                "price": "0",
                "points": [
                    "Eski şehirden modern cam köprüye doğru yürünür.",
                    "Tiflis’in eski ile yeniyi cesur şekilde yan yana koyan yapısı anlatılır.",
                    "Köprü, nehir ve modern yapılar günün tarihsel ağırlığını dengeler.",
                    "Şehir burada değişen yüzünü gösterir."
                ]
            },
            {
                "title": "18:30 Sololaki Sokaklarında Altın Saat 🌇",
                "location": "Sololaki",
                "duration": "1.00",
                "price": "0",
                "points": [
                    "Eski apartmanlar, merdivenler ve balkonlar arasında yürünür.",
                    "Sololaki’nin kozmopolit geçmişi ve mimari çeşitliliği anlatılır.",
                    "Akşam ışığı cepheleri daha sinematik hale getirir.",
                    "Bu bölüm Tiflis’in nostaljik ve kişisel tarafını açar."
                ]
            },
            {
                "title": "20:00 Eski Şehirde Kapanış 🌙",
                "location": "Eski Tiflis",
                "duration": "0.75",
                "price": "0",
                "points": [
                    "Gün tekrar eski şehir sokaklarında tamamlanır.",
                    "Hamamlar, kale, yemek, şarap ve nehir manzarası tek bir hafızaya dönüşür.",
                    "Tiflis akılda sıcak, eski, katmanlı ve misafirperver bir şehir olarak kalır.",
                    "Kapanışta şehir gezilmiş değil, bir sofraya davet edilmiş gibi hissedilir."
                ]
            }
        ],
        "tur_baslik": "Tiflis’te Bir Gün 🇬🇪",
        "slug": "tiflis-bir-gun",
        "overview": "Tiflis’i eski şehir sokakları, kükürt hamamları, kale manzarası, Gürcü sofrası ve şarap kültürüyle tek günde hissettiren sıcak şehir deneyimi.",
        "info": "Bu rota Eski Tiflis’ten Abanotubani’ye, Narikala Kalesi’nden Sololaki sokaklarına uzanır.",
        "rozet": "Gürcistan Deneyimi 🇬🇪",
        "tur_gun_baslik": "1. Gün: Tiflis’in İçinden Geçmek",
        "highlights": [
            "☕ Eski Tiflis sokakları",
            "♨️ Kükürt hamamları",
            "🚠 Narikala manzarası",
            "🍽️ Gürcü sofrası",
            "🍷 Şarap kültürü",
            "🌉 Barış Köprüsü"
        ],
        "tags": "gurcistan,tiflis,sehir,deneyim"
    },
    {
        "ulke": "Özbekistan",
        "iso2": "UZ",
        "sehir": "Buhara",
        "iata": "BHK",
        "havalimani": "Buhara Uluslararası Havalimanı",
        "otel": "Buhara Eski Şehir Butik Otel",
        "otel_fiyat": "55.00",
        "transfer_fiyat": "15.00",
        "gun_baslik": "Buhara’da Yaşayan Bir Gün 🇺🇿",
        "gun_aciklama": "İpek Yolu medreseleri, avlular, çarşı kubbeleri, çay kültürü ve akşam ışıklarıyla tasarlanmış tarihi bir Buhara günü.",
        "bullets": [
            "🕌 Eski şehir sabahı",
            "📚 Medrese avluları",
            "☕ Çay ve gölge molası",
            "🛍️ Kubbeli çarşılar",
            "🍲 Özbek sofrası",
            "🏰 Ark Kalesi",
            "🌇 Poi Kalyan ışıkları",
            "🌙 Eski şehir kapanışı"
        ],
        "aktiviteler": [
            {
                "title": "08:30 Eski Şehir Sabahı 🕌",
                "location": "Buhara Eski Şehir",
                "duration": "1.00",
                "price": "0",
                "points": [
                    "Gün toprak tonlu eski şehir sokaklarında başlar.",
                    "Buhara’nın İpek Yolu üzerindeki öneminden bahsedilir.",
                    "Dar sokaklar, avlular ve küçük dükkânlar arasında yavaş bir yürüyüş yapılır.",
                    "Şehir daha ilk anda bir açık hava müzesi değil, yaşayan bir tarih gibi hissedilir."
                ]
            },
            {
                "title": "10:00 Medrese Avluları ve Bilgelik Hafızası 📚",
                "location": "Eski Medreseler Bölgesi",
                "duration": "1.25",
                "price": "6",
                "points": [
                    "Medrese avluları ve süslemeleri keşfedilir.",
                    "Buhara’nın bilim, eğitim ve ticaretle kurduğu ilişki anlatılır.",
                    "Çini detaylar ve geometrik desenler üzerinden Orta Asya estetiği okunur.",
                    "Bu durak şehrin sadece ticaret değil, bilgi merkezi olduğunu gösterir."
                ]
            },
            {
                "title": "11:30 Çay ve Gölge Molası ☕",
                "location": "Lyabi Havuz",
                "duration": "1.00",
                "price": "5",
                "points": [
                    "Havuz çevresinde çay molası verilir.",
                    "Sıcak iklimde su, gölge ve avlu kültürünün önemi anlatılır.",
                    "Yerel halkın oturma, sohbet etme ve izleme alışkanlıkları gözlemlenir.",
                    "Buhara burada daha sakin ve insani bir ölçeğe iner."
                ]
            },
            {
                "title": "13:00 Özbek Sofrası 🍲",
                "location": "Eski Şehir Restoranı",
                "duration": "1.25",
                "price": "16",
                "points": [
                    "Pilav, tandır ekmeği ve yerel mezeler üzerinden Özbek mutfağı anlatılır.",
                    "İpek Yolu’nun yemek kültürünü nasıl zenginleştirdiği açıklanır.",
                    "Öğle molası, şehrin baharatlı ve doyurucu tarafını ortaya çıkarır.",
                    "Yemek burada yolculuğun doğal devamı gibi yaşanır."
                ]
            },
            {
                "title": "15:00 Kubbeli Çarşılar 🛍️",
                "location": "Buhara Çarşıları",
                "duration": "1.50",
                "price": "0",
                "points": [
                    "Kubbeli eski çarşılar ve zanaat dükkânları gezilir.",
                    "Halı, ipek, metal işçiliği ve minyatür sanatları gözlemlenir.",
                    "Çarşıların eski kervan yollarındaki işlevi anlatılır.",
                    "Bu bölüm Buhara’yı ticaretin ritmiyle hissettirir."
                ]
            },
            {
                "title": "17:00 Ark Kalesi ve Güç Merkezi 🏰",
                "location": "Ark Kalesi",
                "duration": "1.25",
                "price": "8",
                "points": [
                    "Buhara emirlerinin eski yönetim merkezi keşfedilir.",
                    "Kalenin şehir üzerindeki siyasi ve sembolik rolü anlatılır.",
                    "Duvarlar, kapılar ve geniş alanlar geçmiş iktidar yapısını hissettirir.",
                    "Bu durak şehrin sadece ticari değil, politik hafızasını da açar."
                ]
            },
            {
                "title": "18:45 Poi Kalyan’da Altın Saat 🌇",
                "location": "Poi Kalyan",
                "duration": "1.00",
                "price": "0",
                "points": [
                    "Minare ve çevresindeki yapılar akşam ışığında izlenir.",
                    "Buhara’nın en güçlü siluetlerinden biri burada deneyimlenir.",
                    "Günün tüm tarihi katmanları bu meydanda birleşir.",
                    "Altın saat, şehri daha derin ve şiirsel hale getirir."
                ]
            },
            {
                "title": "20:00 Eski Şehirde Kapanış 🌙",
                "location": "Lyabi Havuz",
                "duration": "0.75",
                "price": "0",
                "points": [
                    "Gün tekrar eski şehirde sakin bir yürüyüşle tamamlanır.",
                    "Medreseler, çarşılar, kale ve çay molası tek bir deneyime dönüşür.",
                    "Buhara hafızada eski, bilge, sıcak ve zamansız bir şehir olarak kalır.",
                    "Kapanışta İpek Yolu’nun hâlâ sokaklarda fısıldadığı hissedilir."
                ]
            }
        ],
        "tur_baslik": "Buhara’da Bir Gün 🇺🇿",
        "slug": "buhara-bir-gun",
        "overview": "Buhara’yı İpek Yolu medreseleri, çarşı kubbeleri, çay kültürü ve akşam ışıklarıyla tek günde hissettiren tarihi şehir deneyimi.",
        "info": "Bu rota Lyabi Havuz’dan medreselere, çarşılardan Ark Kalesi’ne ve Poi Kalyan’a uzanır.",
        "rozet": "Özbekistan Deneyimi 🇺🇿",
        "tur_gun_baslik": "1. Gün: Buhara’nın İçinden Geçmek",
        "highlights": [
            "🕌 Eski şehir sabahı",
            "📚 Medrese avluları",
            "☕ Lyabi Havuz molası",
            "🛍️ Kubbeli çarşılar",
            "🏰 Ark Kalesi",
            "🌇 Poi Kalyan ışıkları"
        ],
        "tags": "ozbekistan,buhara,sehir,deneyim"
    }
]

TOURS += [
    {
        "ulke": "Meksika",
        "iso2": "MX",
        "sehir": "Oaxaca",
        "iata": "OAX",
        "havalimani": "Oaxaca Uluslararası Havalimanı",
        "otel": "Oaxaca Tarihi Merkez Butik Otel",
        "otel_fiyat": "80.00",
        "transfer_fiyat": "18.00",
        "gun_baslik": "Oaxaca’da Yaşayan Bir Gün 🇲🇽",
        "gun_aciklama": "Renkli sokaklar, yerel pazarlar, mısır kültürü, zanaat atölyeleri ve akşam meydanıyla tasarlanmış duyusal bir Oaxaca günü.",
        "bullets": [
            "🌈 Renkli sokaklar",
            "☕ Yerel kahve molası",
            "🛍️ Pazar kültürü",
            "🌽 Mısır ve mole hikâyesi",
            "🎨 Zanaat atölyeleri",
            "⛪ Santo Domingo çevresi",
            "🎶 Akşam meydanı",
            "🌙 Tarihi merkez kapanışı"
        ],
        "aktiviteler": [
            {
                "title": "08:30 Tarihi Merkez Sabahı 🌈",
                "location": "Oaxaca Tarihi Merkezi",
                "duration": "1.00",
                "price": "0",
                "points": [
                    "Gün renkli cepheli sokaklarda yavaş bir yürüyüşle başlar.",
                    "Oaxaca’nın yerli kültürler, koloni dönemi ve çağdaş yaşamı nasıl birleştirdiği anlatılır.",
                    "Taş sokaklar, küçük balkonlar ve sabah hazırlığındaki dükkânlar gözlemlenir.",
                    "Şehir ilk anda sıcak, yaratıcı ve güçlü kimlikli hissedilir."
                ]
            },
            {
                "title": "10:00 Yerel Kahve Molası ☕",
                "location": "Tarihi Merkez Kafesi",
                "duration": "1.00",
                "price": "7",
                "points": [
                    "Oaxaca çevresindeki kahve üretim kültürü anlatılır.",
                    "Küçük bir kafede yerel kahve deneyimlenir.",
                    "Sokaklardan gelen müzik, konuşma ve yemek kokuları atmosferi tamamlar.",
                    "Bu mola şehrin acele etmeyen karakterini açar."
                ]
            },
            {
                "title": "11:30 Pazar Kültürü ve Yerel Hayat 🛍️",
                "location": "Mercado Benito Juarez",
                "duration": "1.25",
                "price": "8",
                "points": [
                    "Yerel pazar tezgâhları, baharatlar, kakao ve el işleri keşfedilir.",
                    "Oaxaca’da pazarların sadece alışveriş değil, sosyal hayat merkezi olduğu anlatılır.",
                    "Renkler, kokular ve sesler birlikte yoğun bir şehir hafızası oluşturur.",
                    "Bu durak Oaxaca’yı en canlı haliyle gösterir."
                ]
            },
            {
                "title": "13:00 Mole ve Mısır Kültürü 🌽",
                "location": "Yerel Restoran",
                "duration": "1.50",
                "price": "22",
                "points": [
                    "Mole sosunun Oaxaca mutfağındaki merkezi yeri anlatılır.",
                    "Mısırın Meksika kültüründeki tarihi ve sembolik önemi açıklanır.",
                    "Yerel yemekler üzerinden şehrin yerli kökleri okunur.",
                    "Öğle molası bu rotanın en güçlü duyusal anlarından biri olur."
                ]
            },
            {
                "title": "15:00 Zanaat ve Tekstil Atölyeleri 🎨",
                "location": "Tarihi Merkez Çevresi",
                "duration": "1.25",
                "price": "5",
                "points": [
                    "El dokuması ürünler, seramikler ve küçük atölyeler keşfedilir.",
                    "Oaxaca’da zanaatın turistik eşya değil, yaşayan kültür olduğu anlatılır.",
                    "Renklerin ve desenlerin yerel kimlikle ilişkisi açıklanır.",
                    "Bu bölüm şehrin üretken ve yaratıcı tarafını öne çıkarır."
                ]
            },
            {
                "title": "17:00 Santo Domingo Çevresi ⛪",
                "location": "Santo Domingo Kilisesi",
                "duration": "1.00",
                "price": "0",
                "points": [
                    "Santo Domingo çevresindeki taş meydan ve sokaklar keşfedilir.",
                    "Koloni mimarisi ile yerli kültürün yan yana varlığı anlatılır.",
                    "Akşamüstü ışığı cepheleri daha sıcak hale getirir.",
                    "Bu durak Oaxaca’nın zarif ve törensel yüzünü gösterir."
                ]
            },
            {
                "title": "18:30 Zocalo’da Akşam Ritmi 🎶",
                "location": "Zocalo",
                "duration": "1.25",
                "price": "0",
                "points": [
                    "Meydandaki müzik, aileler ve akşam kalabalığı gözlemlenir.",
                    "Latin Amerika meydan kültürünün günlük yaşamdaki önemi anlatılır.",
                    "Gün burada daha sosyal ve canlı bir tona geçer.",
                    "Oaxaca akşamla birlikte daha sıcak ve samimi hale gelir."
                ]
            },
            {
                "title": "20:00 Tarihi Merkezde Kapanış 🌙",
                "location": "Oaxaca Tarihi Merkezi",
                "duration": "0.75",
                "price": "0",
                "points": [
                    "Gün renkli sokaklarda kısa bir yürüyüşle tamamlanır.",
                    "Kahve, pazar, mısır, zanaat ve meydan kültürü tek deneyime dönüşür.",
                    "Oaxaca hafızada lezzetli, renkli, derin ve yaratıcı bir şehir olarak kalır.",
                    "Kapanışta şehir bir rota değil, güçlü bir kültür hissi bırakır."
                ]
            }
        ],
        "tur_baslik": "Oaxaca’da Bir Gün 🇲🇽",
        "slug": "oaxaca-bir-gun",
        "overview": "Oaxaca’yı renkli sokakları, pazarları, mısır kültürü, mole lezzeti ve zanaat atölyeleriyle tek günde hissettiren duyusal şehir deneyimi.",
        "info": "Bu rota tarihi merkezden pazarlara, Santo Domingo çevresinden Zocalo’ya uzanır.",
        "rozet": "Meksika Deneyimi 🇲🇽",
        "tur_gun_baslik": "1. Gün: Oaxaca’nın İçinden Geçmek",
        "highlights": [
            "🌈 Renkli sokaklar",
            "🛍️ Yerel pazarlar",
            "🌽 Mısır ve mole kültürü",
            "🎨 Zanaat atölyeleri",
            "⛪ Santo Domingo",
            "🎶 Zocalo akşamı"
        ],
        "tags": "meksika,oaxaca,sehir,deneyim"
    },
    {
        "ulke": "Portekiz",
        "iso2": "PT",
        "sehir": "Porto",
        "iata": "OPO",
        "havalimani": "Francisco Sa Carneiro Havalimanı",
        "otel": "Porto Ribeira Butik Otel",
        "otel_fiyat": "95.00",
        "transfer_fiyat": "28.00",
        "gun_baslik": "Porto’da Yaşayan Bir Gün 🇵🇹",
        "gun_aciklama": "Nehir kıyısı, mavi çiniler, eski sokaklar, kahve, köprü manzarası ve fado hissiyle tasarlanmış melankolik bir Porto günü.",
        "bullets": [
            "🌊 Ribeira sabahı",
            "☕ Portekiz kahvesi",
            "🟦 Mavi çiniler",
            "🌉 Dom Luis Köprüsü",
            "🍽️ Porto lezzetleri",
            "🍷 Şarap mahzenleri",
            "🌇 Douro gün batımı",
            "🌙 Eski şehir kapanışı"
        ],
        "aktiviteler": [
            {
                "title": "08:30 Ribeira Sabahı 🌊",
                "location": "Ribeira",
                "duration": "1.00",
                "price": "0",
                "points": [
                    "Gün Douro Nehri kıyısında yavaş bir yürüyüşle başlar.",
                    "Renkli cepheler, dar evler ve nehir hayatı gözlemlenir.",
                    "Porto’nun neden melankolik ama sıcak bir şehir hissi verdiği anlatılır.",
                    "Nehir, bu rotanın ana karakterlerinden biri olur."
                ]
            },
            {
                "title": "10:00 Portekiz Kahvesi Molası ☕",
                "location": "Eski Şehir Kafesi",
                "duration": "0.75",
                "price": "6",
                "points": [
                    "Küçük bir kafede kısa ve yoğun Portekiz kahvesi deneyimlenir.",
                    "Porto’da kafe kültürünün gündelik hayattaki yeri anlatılır.",
                    "Sabah telaşı, konuşmalar ve taş sokaklar atmosferi tamamlar.",
                    "Bu mola şehri izlemek için küçük ama güçlü bir durak olur."
                ]
            },
            {
                "title": "11:00 Mavi Çiniler ve Sao Bento 🟦",
                "location": "Sao Bento İstasyonu",
                "duration": "1.00",
                "price": "0",
                "points": [
                    "Mavi beyaz çinilerle kaplı istasyon içi keşfedilir.",
                    "Portekiz çini sanatının tarih anlatma biçimi açıklanır.",
                    "Günlük ulaşım noktası ile sanatın aynı mekânda birleşmesi gözlemlenir.",
                    "Porto’nun sıradan alanları bile hikâyeye dönüştürme gücü hissedilir."
                ]
            },
            {
                "title": "12:30 Eski Sokaklarda Yavaş Keşif 🚶",
                "location": "Porto Eski Şehir",
                "duration": "1.00",
                "price": "0",
                "points": [
                    "Dar ve inişli çıkışlı sokaklarda yürünür.",
                    "Şehrin yıpranmış cepheleri ile zarif detayları birlikte okunur.",
                    "Porto’nun güzelliğinin kusursuzluktan değil, yaşanmışlıktan geldiği anlatılır.",
                    "Bu bölüm rotaya samimi bir insan ölçeği verir."
                ]
            },
            {
                "title": "13:45 Porto Lezzetleri 🍽️",
                "location": "Yerel Restoran",
                "duration": "1.25",
                "price": "22",
                "points": [
                    "Francesinha veya yerel deniz ürünleri üzerinden Porto mutfağı anlatılır.",
                    "Portekiz yemek kültürünün doyurucu ve sade tarafı açıklanır.",
                    "Öğle molası şehrin işçi sınıfı geçmişiyle bağ kurar.",
                    "Yemek burada manzara kadar güçlü bir karakter taşır."
                ]
            },
            {
                "title": "15:30 Dom Luis Köprüsü 🌉",
                "location": "Dom Luis I Köprüsü",
                "duration": "1.00",
                "price": "0",
                "points": [
                    "Köprü üzerinden Douro Nehri ve Ribeira manzarası izlenir.",
                    "Porto ile Vila Nova de Gaia arasındaki bağ anlatılır.",
                    "Yükseklikten bakınca şehrin kırmızı çatıları ve nehir eğrisi birlikte görülür.",
                    "Bu durak günün en güçlü görsel hafızalarından biri olur."
                ]
            },
            {
                "title": "17:00 Şarap Mahzenleri 🍷",
                "location": "Vila Nova de Gaia",
                "duration": "1.25",
                "price": "18",
                "points": [
                    "Porto şarabının şehir ekonomisi ve kimliğiyle ilişkisi anlatılır.",
                    "Mahzen kültürü ve nehir üzerinden taşımacılık hikâyesi açıklanır.",
                    "Kısa tadım veya mahzen ziyaretiyle şehrin lezzet hafızası tamamlanır.",
                    "Porto burada daha derin, daha yetişkin ve daha yavaş hissedilir."
                ]
            },
            {
                "title": "19:00 Douro Gün Batımı 🌇",
                "location": "Gaia Nehir Kıyısı",
                "duration": "1.00",
                "price": "0",
                "points": [
                    "Gün batımında Ribeira karşı kıyıdan izlenir.",
                    "Işıklar yanarken Porto’nun melankolik güzelliği belirginleşir.",
                    "Nehir, köprü, şarap ve eski sokaklar tek bir görüntüde birleşir.",
                    "Porto hafızada hüzünlü ama çok sıcak bir şehir olarak kalır."
                ]
            }
        ],
        "tur_baslik": "Porto’da Bir Gün 🇵🇹",
        "slug": "porto-bir-gun",
        "overview": "Porto’yu Douro Nehri, mavi çiniler, eski sokaklar, köprü manzarası ve şarap kültürüyle tek günde hissettiren melankolik şehir deneyimi.",
        "info": "Bu rota Ribeira’dan Sao Bento’ya, Dom Luis Köprüsü’nden Gaia kıyısına uzanır.",
        "rozet": "Portekiz Deneyimi 🇵🇹",
        "tur_gun_baslik": "1. Gün: Porto’nun İçinden Geçmek",
        "highlights": [
            "🌊 Ribeira sabahı",
            "🟦 Sao Bento çinileri",
            "🌉 Dom Luis Köprüsü",
            "🍷 Porto şarabı",
            "🌇 Douro gün batımı"
        ],
        "tags": "portekiz,porto,sehir,deneyim"
    }
]

TOURS += [
    {
        "ulke": "İtalya",
        "iso2": "IT",
        "sehir": "Matera",
        "iata": "BRI",
        "havalimani": "Bari Karol Wojtyla Havalimanı",
        "otel": "Matera Sassi Mağara Otel",
        "otel_fiyat": "115.00",
        "transfer_fiyat": "60.00",
        "gun_baslik": "Matera’da Yaşayan Bir Gün 🇮🇹",
        "gun_aciklama": "Taş evler, mağara sokakları, eski kiliseler, güney İtalya lezzetleri ve gün batımı manzarasıyla tasarlanmış benzersiz bir Matera günü.",
        "bullets": [
            "🪨 Sassi sokakları",
            "☕ Taş şehirde kahve",
            "⛪ Mağara kiliseleri",
            "🍝 Güney İtalya lezzetleri",
            "🚶 Eski merdivenler",
            "🌄 Gravina manzarası",
            "🌇 Altın saat",
            "🌙 Taş şehirde kapanış"
        ],
        "aktiviteler": [
            {
                "title": "08:30 Sassi Sokaklarında Sabah 🪨",
                "location": "Sassi di Matera",
                "duration": "1.25",
                "price": "0",
                "points": [
                    "Gün taş evler ve mağara sokakları arasında başlar.",
                    "Matera’nın binlerce yıllık yerleşim geçmişi anlatılır.",
                    "Şehrin neden dünyadaki en sıra dışı insan yerleşimlerinden biri olduğu açıklanır.",
                    "İlk adımda modern bir şehirden çok, zamansız bir taş hafızaya girilmiş gibi hissedilir."
                ]
            },
            {
                "title": "10:00 Taş Şehirde Kahve Molası ☕",
                "location": "Sassi Kafesi",
                "duration": "0.75",
                "price": "6",
                "points": [
                    "Mağara dokusuna sahip küçük bir kafede kahve molası verilir.",
                    "Güney İtalya’da kahvenin kısa ama sosyal bir ritüel olduğu anlatılır.",
                    "Taş duvarlar ve dar sokaklar arasında şehir daha kişisel hale gelir.",
                    "Bu mola Matera’nın sert görünümünün içinde sıcak bir gündelik hayat olduğunu gösterir."
                ]
            },
            {
                "title": "11:00 Mağara Kiliseleri ⛪",
                "location": "Matera Kaya Kiliseleri",
                "duration": "1.25",
                "price": "10",
                "points": [
                    "Kayaya oyulmuş eski ibadet alanları keşfedilir.",
                    "Matera’da inanç, yoksulluk, barınma ve dayanıklılık ilişkisi anlatılır.",
                    "Duvar izleri, freskler ve mağara mekânları üzerinden geçmiş okunur.",
                    "Bu durak şehrin sadece estetik değil, ruhani derinliğini açar."
                ]
            },
            {
                "title": "13:00 Güney İtalya Sofrası 🍝",
                "location": "Matera Eski Şehir",
                "duration": "1.25",
                "price": "24",
                "points": [
                    "Yerel makarna, ekmek ve zeytinyağı kültürü üzerinden Basilicata mutfağı anlatılır.",
                    "Matera ekmeğinin bölgedeki öneminden bahsedilir.",
                    "Öğle molası şehrin yoksul ama güçlü mutfak hafızasını gösterir.",
                    "Yemek burada sade, köklü ve doyurucu bir deneyime dönüşür."
                ]
            },
            {
                "title": "15:00 Eski Merdivenler ve Saklı Geçitler 🚶",
                "location": "Sassi Merdivenleri",
                "duration": "1.25",
                "price": "0",
                "points": [
                    "Taş merdivenlerden, dar geçitlerden ve küçük avlulardan geçilir.",
                    "Matera’nın düz bir rota değil, katman katman açılan bir şehir olduğu anlatılır.",
                    "Her dönüşte farklı bir manzara ve farklı bir yaşam izi görülür.",
                    "Bu bölüm şehirle fiziksel temas kurdurur."
                ]
            },
            {
                "title": "17:00 Gravina Manzarası 🌄",
                "location": "Gravina Kanyonu Manzarası",
                "duration": "1.00",
                "price": "0",
                "points": [
                    "Matera’nın karşı yamaçları ve kanyon manzarası izlenir.",
                    "Şehrin doğa ile kurduğu dramatik ilişki anlatılır.",
                    "Taş yapıların araziye nasıl tutunduğu gözlemlenir.",
                    "Bu durak Matera’yı sadece sokaklardan değil, coğrafyadan da anlamayı sağlar."
                ]
            },
            {
                "title": "18:30 Altın Saatte Taş Cepheler 🌇",
                "location": "Sassi Seyir Noktası",
                "duration": "1.00",
                "price": "0",
                "points": [
                    "Gün batımına yaklaşırken taş cepheler sıcak renklere bürünür.",
                    "Matera’nın sinematik görüntüsünün neden bu kadar güçlü olduğu anlatılır.",
                    "Işık, gölge ve taş dokusu birlikte izlenir.",
                    "Günün en duygusal görsel anı burada yaşanır."
                ]
            },
            {
                "title": "20:00 Taş Şehirde Gece Kapanışı 🌙",
                "location": "Sassi di Matera",
                "duration": "0.75",
                "price": "0",
                "points": [
                    "Akşam ışıklarıyla Sassi sokaklarında kısa bir yürüyüş yapılır.",
                    "Sabah görülen taş şehir, gece daha masalsı ve sessiz hale gelir.",
                    "Kahve, mağara kiliseleri, yemek ve manzara tek bir deneyime dönüşür.",
                    "Matera hafızada eski, sert, şiirsel ve unutulmaz bir şehir olarak kalır."
                ]
            }
        ],
        "tur_baslik": "Matera’da Bir Gün 🇮🇹",
        "slug": "matera-bir-gun",
        "overview": "Matera’yı taş evleri, mağara sokakları, kaya kiliseleri, güney İtalya mutfağı ve gün batımı manzarasıyla tek günde hissettiren benzersiz şehir deneyimi.",
        "info": "Bu rota Sassi sokaklarından mağara kiliselerine, Gravina manzarasından taş şehir gece yürüyüşüne uzanır.",
        "rozet": "İtalya Deneyimi 🇮🇹",
        "tur_gun_baslik": "1. Gün: Matera’nın İçinden Geçmek",
        "highlights": [
            "🪨 Sassi sokakları",
            "⛪ Mağara kiliseleri",
            "🍝 Güney İtalya lezzetleri",
            "🌄 Gravina manzarası",
            "🌙 Taş şehirde kapanış"
        ],
        "tags": "italya,matera,sehir,deneyim"
    },
    {
        "ulke": "Kolombiya",
        "iso2": "CO",
        "sehir": "Cartagena",
        "iata": "CTG",
        "havalimani": "Rafael Nunez Uluslararası Havalimanı",
        "otel": "Cartagena Surlu Şehir Butik Otel",
        "otel_fiyat": "105.00",
        "transfer_fiyat": "20.00",
        "gun_baslik": "Cartagena’da Yaşayan Bir Gün 🇨🇴",
        "gun_aciklama": "Renkli balkonlar, Karayip havası, surlar, meydanlar, müzik ve gün batımıyla tasarlanmış canlı bir Cartagena günü.",
        "bullets": [
            "🌈 Surlu şehir sokakları",
            "☕ Karayip kahvesi",
            "🏰 Şehir surları",
            "🍤 Kolombiya lezzetleri",
            "🎨 Getsemani sokakları",
            "🎶 Akşam müziği",
            "🌅 Gün batımı",
            "🌙 Renkli kapanış"
        ],
        "aktiviteler": [
            {
                "title": "08:30 Surlu Şehir Sabahı 🌈",
                "location": "Cartagena Surlu Şehir",
                "duration": "1.00",
                "price": "0",
                "points": [
                    "Gün renkli balkonlar ve çiçekli cepheler arasında başlar.",
                    "Cartagena’nın Karayip limanı olarak tarihsel önemi anlatılır.",
                    "Dar sokaklar, eski kapılar ve sabah hazırlığındaki meydanlar gözlemlenir.",
                    "Şehir ilk anda sıcak, ritimli ve fotoğraf gibi hissedilir."
                ]
            },
            {
                "title": "10:00 Karayip Kahvesi Molası ☕",
                "location": "Eski Şehir Kafesi",
                "duration": "0.75",
                "price": "7",
                "points": [
                    "Kolombiya kahve kültürü Karayip atmosferiyle birlikte deneyimlenir.",
                    "Kahvenin ülkedeki sosyal ve ekonomik önemi anlatılır.",
                    "Küçük bir kafede şehir akışını izleme zamanı yaratılır.",
                    "Bu mola günün renkli temposuna sakin bir ara verir."
                ]
            },
            {
                "title": "11:00 Surlar ve Liman Hafızası 🏰",
                "location": "Cartagena Surları",
                "duration": "1.25",
                "price": "0",
                "points": [
                    "Şehir surları boyunca yürünür.",
                    "Cartagena’nın korsan saldırıları, ticaret ve savunma tarihindeki yeri anlatılır.",
                    "Deniz, taş duvarlar ve eski şehir birlikte izlenir.",
                    "Bu durak şehrin güzelliğinin arkasındaki sert tarihi gösterir."
                ]
            },
            {
                "title": "13:00 Karayip Sofrası 🍤",
                "location": "Surlu Şehir Restoranı",
                "duration": "1.25",
                "price": "24",
                "points": [
                    "Deniz ürünleri, hindistan cevizi pirinci ve tropikal tatlar keşfedilir.",
                    "Kolombiya Karayip mutfağının Afrika, yerli ve İspanyol etkileri anlatılır.",
                    "Öğle molası şehrin denizle ve ritimle bağını güçlendirir.",
                    "Yemek, Cartagena’yı renk kadar lezzetle de hatırlatır."
                ]
            },
            {
                "title": "15:00 Getsemani Sokak Sanatı 🎨",
                "location": "Getsemani",
                "duration": "1.25",
                "price": "0",
                "points": [
                    "Renkli duvar resimleri, küçük meydanlar ve yerel sokak hayatı keşfedilir.",
                    "Getsemani’nin dönüşen ama hâlâ mahalle ruhunu koruyan yapısı anlatılır.",
                    "Sokak sanatı üzerinden genç ve yaratıcı Cartagena okunur.",
                    "Bu bölüm şehrin daha özgür ve yerel tarafını açar."
                ]
            },
            {
                "title": "17:00 Meydanlarda Akşam Hazırlığı 🎶",
                "location": "Plaza Trinidad",
                "duration": "1.00",
                "price": "0",
                "points": [
                    "Akşama doğru meydanların yavaşça canlandığı gözlemlenir.",
                    "Müzik, sokak satıcıları ve mahalle buluşmaları şehir ritmini değiştirir.",
                    "Cartagena’da kamusal alanın sosyal hayat için önemi anlatılır.",
                    "Gün burada daha sıcak ve topluluk hissi veren bir tona geçer."
                ]
            },
            {
                "title": "18:30 Surlar Üzerinde Gün Batımı 🌅",
                "location": "Surlar",
                "duration": "1.00",
                "price": "0",
                "points": [
                    "Gün batımı deniz ve surlar üzerinden izlenir.",
                    "Taş duvarlar, turuncu gökyüzü ve Karayip rüzgârı birlikte hissedilir.",
                    "Günün tarih, renk ve müzik katmanları bu manzarada birleşir.",
                    "Bu durak Cartagena’nın en güçlü duygusal anlarından biridir."
                ]
            },
            {
                "title": "20:00 Renkli Sokaklarda Kapanış 🌙",
                "location": "Surlu Şehir",
                "duration": "0.75",
                "price": "0",
                "points": [
                    "Akşam ışıkları altında eski şehir sokaklarında kısa bir yürüyüş yapılır.",
                    "Balkonlar, meydanlar, müzik ve deniz hafızası tek deneyime dönüşür.",
                    "Cartagena hafızada canlı, sıcak, renkli ve ritimli bir şehir olarak kalır.",
                    "Kapanışta şehir bir sahil kartpostalı değil, yaşayan Karayip hikâyesi gibi hissedilir."
                ]
            }
        ],
        "tur_baslik": "Cartagena’da Bir Gün 🇨🇴",
        "slug": "cartagena-bir-gun",
        "overview": "Cartagena’yı renkli balkonları, şehir surları, Karayip lezzetleri, Getsemani sokakları ve gün batımıyla tek günde hissettiren canlı şehir deneyimi.",
        "info": "Bu rota surlu şehirden Getsemani’ye, Karayip sofrasından gün batımı surlarına uzanır.",
        "rozet": "Kolombiya Deneyimi 🇨🇴",
        "tur_gun_baslik": "1. Gün: Cartagena’nın İçinden Geçmek",
        "highlights": [
            "🌈 Surlu şehir sokakları",
            "🏰 Cartagena surları",
            "🍤 Karayip lezzetleri",
            "🎨 Getsemani sokak sanatı",
            "🌅 Gün batımı"
        ],
        "tags": "kolombiya,cartagena,sehir,deneyim"
    },
    {
        "ulke": "Hindistan",
        "iso2": "IN",
        "sehir": "Jaipur",
        "iata": "JAI",
        "havalimani": "Jaipur Uluslararası Havalimanı",
        "otel": "Jaipur Pembe Şehir Butik Otel",
        "otel_fiyat": "70.00",
        "transfer_fiyat": "18.00",
        "gun_baslik": "Jaipur’da Yaşayan Bir Gün 🇮🇳",
        "gun_aciklama": "Pembe şehir sokakları, saray cepheleri, kale manzarası, baharatlar, tekstiller ve akşam ışıklarıyla tasarlanmış görkemli bir Jaipur günü.",
        "bullets": [
            "🌸 Pembe şehir sabahı",
            "🏛️ Hawa Mahal",
            "☕ Masala çayı molası",
            "🏰 Amber Kalesi",
            "🍛 Rajasthani lezzetleri",
            "🧵 Tekstil ve zanaat",
            "🌇 Şehir Sarayı çevresi",
            "🌙 Işıklı kapanış"
        ],
        "aktiviteler": [
            {
                "title": "08:30 Pembe Şehir Sabahı 🌸",
                "location": "Jaipur Eski Şehir",
                "duration": "1.00",
                "price": "0",
                "points": [
                    "Gün pembe tonlu eski şehir sokaklarında başlar.",
                    "Jaipur’un planlı şehir yapısı ve renk kimliği anlatılır.",
                    "Sabah pazar hazırlıkları, dükkânlar ve sokak hareketi gözlemlenir.",
                    "Şehir ilk anda kalabalık, görkemli ve çok duyusal hissedilir."
                ]
            },
            {
                "title": "10:00 Hawa Mahal ve Saray Cephesi 🏛️",
                "location": "Hawa Mahal",
                "duration": "1.00",
                "price": "8",
                "points": [
                    "Rüzgâr Sarayı’nın ünlü cephesi keşfedilir.",
                    "Yapının kadınların şehir hayatını görünmeden izleyebilmesi için nasıl tasarlandığı anlatılır.",
                    "Cephedeki küçük pencereler, gölge ve hava akışı üzerinden mimari zekâ okunur.",
                    "Bu durak Jaipur’un estetik kadar sosyal tarihini de açar."
                ]
            },
            {
                "title": "11:30 Masala Çayı Molası ☕",
                "location": "Eski Şehir Çay Noktası",
                "duration": "0.75",
                "price": "4",
                "points": [
                    "Sokak kenarında veya küçük bir kafede masala çayı içilir.",
                    "Baharatlı çayın Hindistan gündelik hayatındaki yeri anlatılır.",
                    "Kakule, zencefil ve süt kokusu şehir deneyimine karışır.",
                    "Bu mola kalabalığın içinde küçük bir durma anı yaratır."
                ]
            },
            {
                "title": "12:45 Amber Kalesi 🏰",
                "location": "Amber Kalesi",
                "duration": "1.75",
                "price": "14",
                "points": [
                    "Tepedeki görkemli kale ve avlular keşfedilir.",
                    "Rajput mimarisi, savunma anlayışı ve saray hayatı anlatılır.",
                    "Yukarıdan Jaipur’un çevresindeki kuru tepeler ve eski yollar görülür.",
                    "Bu durak şehrin kraliyet hafızasını güçlü biçimde hissettirir."
                ]
            },
            {
                "title": "15:00 Rajasthani Sofrası 🍛",
                "location": "Yerel Restoran",
                "duration": "1.25",
                "price": "18",
                "points": [
                    "Rajasthani yemek kültürü, baharatlar ve thali düzeni üzerinden anlatılır.",
                    "Kurak coğrafyanın mutfağı nasıl şekillendirdiği açıklanır.",
                    "Yemekler renk, aroma ve yoğunluk açısından şehrin görselliğiyle birleşir.",
                    "Öğle molası Jaipur’u damakta da kalıcı hale getirir."
                ]
            },
            {
                "title": "16:30 Tekstil ve Zanaat Sokakları 🧵",
                "location": "Jaipur Çarşıları",
                "duration": "1.25",
                "price": "0",
                "points": [
                    "Kumaşlar, blok baskılar, takılar ve renkli dükkânlar keşfedilir.",
                    "Jaipur’un zanaat ve ticaret geleneği anlatılır.",
                    "Renklerin şehir kimliğinde neden bu kadar güçlü olduğu açıklanır.",
                    "Bu bölüm Jaipur’u yaşayan bir üretim merkezi gibi gösterir."
                ]
            },
            {
                "title": "18:00 Şehir Sarayı Çevresi 🌇",
                "location": "Şehir Sarayı Çevresi",
                "duration": "1.00",
                "price": "10",
                "points": [
                    "Saray çevresindeki meydanlar ve geçitler akşam ışığında keşfedilir.",
                    "Jaipur’un kraliyet geçmişi ile bugünkü şehir hayatı yan yana okunur.",
                    "Gün batımı tonları pembe cepheleri daha sıcak hale getirir.",
                    "Bu durak görkemli ama yorgun bir günün sakin bölümüdür."
                ]
            },
            {
                "title": "20:00 Işıklı Eski Şehir Kapanışı 🌙",
                "location": "Jaipur Eski Şehir",
                "duration": "0.75",
                "price": "0",
                "points": [
                    "Akşam ışıkları altında eski şehir sokaklarında kısa bir yürüyüş yapılır.",
                    "Saray, kale, baharat, çay ve tekstil hafızası tek deneyime dönüşür.",
                    "Jaipur hafızada renkli, yoğun, kraliyetli ve canlı bir şehir olarak kalır.",
                    "Kapanışta şehir görkemli bir masal ile gerçek sokak hayatı arasında hissedilir."
                ]
            }
        ],
        "tur_baslik": "Jaipur’da Bir Gün 🇮🇳",
        "slug": "jaipur-bir-gun",
        "overview": "Jaipur’u pembe şehir sokakları, Hawa Mahal, Amber Kalesi, baharatlı çay, Rajasthani mutfağı ve zanaat çarşılarıyla tek günde hissettiren görkemli şehir deneyimi.",
        "info": "Bu rota Eski Şehir’den Hawa Mahal’e, Amber Kalesi’nden çarşı sokaklarına uzanır.",
        "rozet": "Hindistan Deneyimi 🇮🇳",
        "tur_gun_baslik": "1. Gün: Jaipur’un İçinden Geçmek",
        "highlights": [
            "🌸 Pembe şehir sabahı",
            "🏛️ Hawa Mahal",
            "🏰 Amber Kalesi",
            "🍛 Rajasthani mutfağı",
            "🧵 Tekstil ve zanaat"
        ],
        "tags": "hindistan,jaipur,sehir,deneyim"
    }
]


def run():
    print("Nomaya uzun şehir turları oluşturuluyor...")
    for tour_data in TOURS:
        create_nomaya_tour(tour_data)
    print("Bitti.")


run()

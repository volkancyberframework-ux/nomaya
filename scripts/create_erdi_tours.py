from decimal import Decimal
from django.db import transaction
from core.models import Country, City, Tour, TourDay, Day, Activity, DayActivity

country, _ = Country.objects.get_or_create(name="Vietnam", defaults={"iso2": "VN"})

def city(name):
    return City.objects.get_or_create(name=name, country=country)[0]

def create_tour(slug, overview, plan, base_day):
    old = Tour.objects.filter(slug=slug).first()
    if old:
        old.delete()
    tour = Tour.objects.create(
        title="Erdi Bey Aile Turu Vietnam",
        slug=slug,
        overview=overview,
        info="👨‍👩‍👶 10 aylık bebekle seyahate uygun, aile temposunda hazırlanmıştır. Otel, uçak ve transfer dahil değildir; yalnızca aktiviteler sunulur.",
        allow_flights=False,
        allow_hotels=False,
        allow_transfers=False,
        commission=Decimal("1.00"),
        price_currency="USD",
        is_published=True,
        badge_text="Aileye Özel"
    )
    used_cities = []
    for index, item in enumerate(plan, 1):
        city_obj = city(item["city"])
        used_cities.append(city_obj)
        day = Day.objects.create(
            city=city_obj,
            day_number=base_day + index,
            title=item["title"],
            description=item["description"],
            bullets=item["bullets"],
            price_currency="USD"
        )
        TourDay.objects.create(tour=tour, day=day, order=index, title=f"{index}. Gün: {item['title']}")
        for order, activity_data in enumerate(item["activities"], 1):
            title, location, price, points = activity_data
            activity = Activity.objects.create(
                title=title, location_text=location, city=city_obj,
                price=Decimal(str(price)), price_currency="USD",
                duration_hours=Decimal("2.00"), miles_reward=50, points=points
            )
            DayActivity.objects.create(day=day, activity=activity, order=order)
        day.recompute_price()
    tour.places_covered.set(used_cities)
    tour.recompute_item_counts()
    tour.recompute_price()
    return tour

tour1_plan = [
{"city":"Ho Chi Minh City","title":"Ho Chi Minh'e Varış ve Şehirle Tanışma","description":"İlk gün ailece şehre alışma ve merkez bölgesini yormayan bir tempoda keşfetme günü.","bullets":["👶 Bebek arabasıyla uygulanabilir rota","☕ Sık dinlenme molaları","📍 Şehir merkezindeki önemli yapılar","🌙 Erken biten aile programı"],"activities":[
("🏛️ Bağımsızlık Sarayı","District 1",35,["Vietnam Savaşı'nın sona erdiği sembolik yapı.","Sarayın odaları ve tarihî karar merkezleri görülebilir.","Geniş bahçesi ailece rahat bir gezi sunar."]),
("⛪ Notre Dame Katedrali ve Merkez Postanesi","District 1",30,["Fransız sömürge döneminin mimarisi keşfedilir.","Tarihî postane Gustave Eiffel döneminin izlerini taşır.","İki yapı birbirine yürüme mesafesindedir."]),
("🌳 Nguyen Hue Yürüyüş Caddesi","Nguyen Hue",30,["Şehrin modern ve hareketli merkezidir.","Bebek arabasıyla rahatça gezilebilir.","Yerel yaşamı gözlemlemek için ideal bir noktadır."]),
("🍜 Aile Dostu Vietnam Akşam Yemeği","District 1",35,["Pho ve taze spring roll gibi hafif yemekler denenir.","Acı oranı aileye göre ayarlanabilir.","İlk gün için sakin bir restoran seçilir."])]},
{"city":"Ho Chi Minh City","title":"Mekong Deltası Aile Deneyimi","description":"Vietnam'ın pirinç ambarı olarak bilinen Mekong Deltası'nda nehir yaşamının keşfedileceği tam günlük gezi.","bullets":["🚤 Nehir üzerinde tekne deneyimi","🌴 Tropikal köy yaşamı","🍍 Yerel meyve tadımı","👶 Aile temposuna uygun molalar"],"activities":[
("🚤 Mekong Nehri Tekne Gezisi","My Tho",40,["Mekong, Güneydoğu Asya'nın en büyük nehir sistemlerinden biridir.","Nehir kıyısındaki köyler ve günlük yaşam görülür.","Kapalı veya gölgelikli tekne tercih edilir."]),
("🥥 Hindistan Cevizi ve Bal Atölyesi","Ben Tre",30,["Yerel üreticilerin geleneksel yöntemleri öğrenilir.","Hindistan cevizi şekeri ve tropikal ürünler tanıtılır.","Kısa ve aile dostu bir ziyaret yapılır."]),
("🛶 Palmiye Kanallarında Sampan Turu","Mekong Delta",30,["Dar su kanallarında küçük geleneksel teknelerle ilerlenir.","Su palmiyeleri arasında bölgenin doğal yapısı görülür.","Bebekle güvenlik için can yeleği kontrol edilir."]),
("🍍 Mekong Köy Öğle Yemeği","My Tho",30,["Güney Vietnam mutfağından yerel yemekler sunulur.","Tropikal meyveler tadılır.","Dinlenme için uzun bir öğle arası bırakılır."])]},
{"city":"Ho Chi Minh City","title":"Yerel Kültür, Pazarlar ve Saigon Akşamı","description":"Ho Chi Minh'in yerel mahallelerini, pazar kültürünü ve nehir kıyısını keşfetme günü.","bullets":["🛍️ Yerel pazar deneyimi","🏮 Çin-Vietnam kültürü","🌇 Saigon Nehri manzarası","🍲 Aile dostu gastronomi"],"activities":[
("🛍️ Ben Thanh Pazarı","District 1",30,["Şehrin en bilinen kapalı pazarlarından biridir.","Baharatlar, tekstil ürünleri ve hediyelikler görülebilir.","Kalabalık saatlerden kaçınılır."]),
("🏮 Cholon ve Thien Hau Tapınağı","District 5",35,["Ho Chi Minh'in tarihî Çin Mahallesi keşfedilir.","Thien Hau Tapınağı deniz tanrıçasına adanmıştır.","Vietnam'daki Çin kültürünün izleri anlatılır."]),
("🌇 Saigon Nehri Gün Batımı","Bach Dang Wharf",30,["Şehrin modern silüeti nehir kıyısından izlenir.","Geniş yürüyüş alanı bebek arabasına uygundur.","Gün batımında sakin bir aile yürüyüşü yapılır."]),
("🍲 Vietnam Sokak Lezzetleri Tadımı","District 3",35,["Banh xeo ve banh mi gibi lezzetler tanıtılır.","Hijyenik ve aile dostu işletmeler seçilir.","Acısız ve hafif seçeneklere öncelik verilir."])]}
]


tour1_plan += [
{"city":"Da Nang","title":"Da Nang Sahilleri ve Şehir Merkezi","description":"Da Nang'a geçiş sonrasında plaj, tapınak ve nehir çevresinde rahat bir keşif günü.","bullets":["🏖️ Sahil molası","🛕 Budist kültürü","🐉 Dragon Bridge","👶 Bebekle hafif tempo"],"activities":[
("🏖️ My Khe Plajı","My Khe",30,["Vietnam'ın en tanınmış şehir plajlarından biridir.","Geniş kumsalı ailece dinlenmeye uygundur.","Öğle sıcağı dışında ziyaret edilir."]),
("🛕 Linh Ung Pagodası","Son Tra Peninsula",35,["Dev Lady Buddha heykeli şehre ve denize bakar.","Da Nang'ın Budist kültürü anlatılır.","Manzara noktalarında aile fotoğrafları çekilebilir."]),
("🐉 Dragon Bridge ve Han Nehri","Da Nang Centre",30,["Ejderha biçimindeki köprü şehrin simgesidir.","Nehir kıyısında rahat yürüyüş alanları bulunur.","Akşam ışıklandırması izlenebilir."]),
("🍜 Da Nang Yerel Mutfağı","Hai Chau",35,["Mi Quang eriştesi bölgenin simgesel yemeğidir.","Aileye uygun, acısız seçenekler hazırlanabilir.","Yerel tatlarla sakin bir akşam geçirilir."])]},
{"city":"Da Nang","title":"Ba Na Hills ve Golden Bridge","description":"Da Nang'ın dağlık bölgesindeki Ba Na Hills, teleferik ve ünlü Golden Bridge deneyimi.","bullets":["🚠 Teleferik yolculuğu","🌉 Golden Bridge","🏰 French Village","🌦️ Serin dağ havası"],"activities":[
("🚠 Ba Na Hills Teleferiği","Ba Na Hills",35,["Dünyanın uzun teleferik hatlarından biriyle dağa çıkılır.","Orman ve vadi manzaraları izlenir.","Bebek için hava değişimine uygun kıyafet alınır."]),
("🌉 Golden Bridge","Ba Na Hills",35,["Dev taş eller tarafından tutuluyormuş gibi görünen köprü gezilir.","Da Nang'ın en ünlü fotoğraf noktalarındandır.","Sabah erken saatler daha sakindir."]),
("🏰 French Village","Ba Na Hills",30,["Avrupa kasabası tarzında tasarlanmış bölge keşfedilir.","Kapalı alanlar ve kafeler dinlenme imkânı sunar.","Bebekle uzun yürüyüşler arasında mola verilir."]),
("🌸 Le Jardin D'Amour Bahçeleri","Ba Na Hills",30,["Tematik çiçek bahçeleri ve manzara alanları görülür.","Aile fotoğrafları için renkli bir ortamdır.","Program hava durumuna göre esnetilir."])]},
{"city":"Hanoi","title":"Hanoi Eski Şehir ve Göl Çevresi","description":"Hanoi'nin tarihî merkezi, göl çevresi ve geleneksel sokak kültürü keşfedilir.","bullets":["🏮 Old Quarter sokakları","🌊 Hoan Kiem Gölü","☕ Vietnam kahvesi","🎭 Geleneksel sanat"],"activities":[
("🌊 Hoan Kiem Gölü","Hoan Kiem",30,["Hanoi'nin tarihî ve sosyal merkezidir.","Göl çevresi sabah yürüyüşleriyle ünlüdür.","Bebek arabasıyla rahat bir rota uygulanabilir."]),
("🏮 Hanoi Old Quarter","Old Quarter",35,["Eski ticaret sokakları ve kolonyal yapılar keşfedilir.","Her sokağın geçmişte farklı bir zanaata ayrıldığı anlatılır.","Kalabalık bölümlerde kısa rotalar tercih edilir."]),
("☕ Yumurta Kahvesi Deneyimi","Old Quarter",30,["Hanoi'ye özgü yumurta kahvesinin hikâyesi anlatılır.","Kahve içmeyenler için alternatif içecek seçilebilir.","Tarihî bir kafede dinlenme molası verilir."]),
("🎭 Su Kuklası Gösterisi","Thang Long Theatre",35,["Kuzey Vietnam köylerinden doğmuş geleneksel bir sanattır.","Kuklalar su üzerinde müzik eşliğinde hareket eder.","Kapalı salon bebekle dinlenmek için uygundur."])]},
{"city":"Hanoi","title":"Hanoi Tarihi ve Vietnam Kültürü","description":"Vietnam'ın siyasi tarihi, geleneksel mimarisi ve yerel gastronomisini tanıma günü.","bullets":["🏛️ Vietnam tarihi","📚 Edebiyat Tapınağı","🚂 Tren Sokağı","🍜 Hanoi lezzetleri"],"activities":[
("🏛️ Ho Chi Minh Kompleksi","Ba Dinh",35,["Modern Vietnam'ın kurucusu Ho Chi Minh'in yaşamı anlatılır.","Ba Dinh Meydanı ve Başkanlık Sarayı çevresi görülür.","Ziyaret kurallarına uygun kıyafet tercih edilir."]),
("📚 Edebiyat Tapınağı","Dong Da",30,["Vietnam'ın ilk ulusal üniversitesi kabul edilir.","Konfüçyüs geleneği ve eğitim tarihi anlatılır.","Avluları sakin ve aile dostudur."]),
("🚂 Hanoi Tren Sokağı Çevresi","Hoan Kiem",30,["Rayların evlerin arasından geçtiği sıra dışı mahalle görülür.","Güvenli ve izin verilen gözlem alanları kullanılır.","Tren saatlerinde raylara yaklaşılmaz."]),
("🍜 Hanoi Yemek Deneyimi","Old Quarter",35,["Bun cha ve kuzey usulü pho denenir.","Yerel yemeklerin bölgesel farkları anlatılır.","Aile ve bebek için temiz restoran seçilir."])]}
]
tour1 = create_tour(
    "erdi-bey-aile-turu-vietnam-1",
    "🇻🇳 Ho Chi Minh'den başlayıp Da Nang ve Hanoi'ye uzanan 7 günlük aile turu. 3 gün Ho Chi Minh, 2 gün Da Nang ve 2 gün Hanoi.",
    tour1_plan, 7100
)
print("✅ TUR 1:", tour1.id, tour1.slug, tour1.price, tour1.price_currency)


tour2_plan = [
{"city":"Da Nang","title":"Da Nang'a Varış ve Sahil Günü","description":"İlk gün ailece dinlenme, sahile alışma ve Da Nang şehir merkezini keşfetme programı.","bullets":["🏖️ Rahat sahil programı","🌊 Deniz manzarası","🐉 Şehir simgeleri","👶 Bebek dostu tempo"],"activities":[
("🏖️ My Khe Plajı","My Khe",30,["Geniş ve temiz kumsalıyla ailelerin tercih ettiği bir plajdır.","Uzun yolculuk sonrası sakin bir dinlenme sağlar.","Güneşin güçlü olduğu saatlerden kaçınılır."]),
("🌳 East Sea Park","Son Tra",30,["Sahil kenarında geniş ve yeşil bir dinlenme alanıdır.","Bebek arabasıyla yürüyüş için uygundur.","Yerel ailelerin günlük yaşamı gözlemlenir."]),
("🐉 Dragon Bridge","Han River",35,["Ejderha tasarımlı köprü Da Nang'ın modern simgesidir.","Nehir kıyısındaki yürüyüş yolu gezilir.","Akşam ışıklandırması ailece izlenebilir."]),
("🍜 Mi Quang Akşam Yemeği","Hai Chau",35,["Da Nang'ın meşhur erişte yemeği denenir.","Et suyu, otlar ve yer fıstığıyla hazırlanır.","Bebekli aileye uygun sakin restoran seçilir."])]},
{"city":"Da Nang","title":"Ba Na Hills, Golden Bridge ve French Village","description":"Da Nang'ın en ünlü dağ deneyiminde teleferik, Golden Bridge ve French Village gezisi.","bullets":["🚠 Dağ teleferiği","🌉 Golden Bridge","🏰 Fransız köyü","🌸 Tematik bahçeler"],"activities":[
("🚠 Ba Na Hills Teleferiği","Ba Na Hills",35,["Dağlara çıkan panoramik teleferik yolculuğudur.","Tropikal orman ve vadi manzaraları görülür.","Bebek için ince ceket ve taşıyıcı önerilir."]),
("🌉 Golden Bridge","Ba Na Hills",35,["Dev ellerin tuttuğu altın renkli yaya köprüsüdür.","Vietnam'ın en çok fotoğraflanan noktalarındandır.","Kalabalıktan kaçınmak için erken gidilir."]),
("🏰 French Village","Ba Na Hills",30,["Fransız kasabalarını andıran mimari bölgedir.","Restoran ve kapalı alanlarda dinlenilebilir.","Aileye uygun kısa yürüyüş rotası uygulanır."]),
("🌸 Le Jardin D'Amour","Ba Na Hills",30,["Dokuz farklı temaya sahip çiçek bahçeleri gezilir.","Dağ manzaralı aile fotoğrafları çekilebilir.","Hava şartlarına göre süre esnetilir."])]},
{"city":"Da Nang","title":"Hoi An Antik Şehir ve Fenerler","description":"UNESCO listesindeki Hoi An'ın tarihî evleri, nehir kıyısı ve renkli fenerleri keşfedilir.","bullets":["🏮 UNESCO tarihî merkezi","🌉 Japon Köprüsü","🛶 Thu Bon Nehri","✨ Akşam fenerleri"],"activities":[
("🏮 Hoi An Antik Şehir","Hoi An",35,["Tarihî ticaret limanı dokusu korunmuş bir UNESCO alanıdır.","Sarı evler ve geleneksel dükkânlar görülür.","Araç trafiğinin sınırlı olduğu sokaklar aileye uygundur."]),
("🌉 Japon Kapalı Köprüsü","Hoi An",30,["Japon tüccarlar tarafından inşa edilen tarihî bir köprüdür.","Şehrin çok kültürlü geçmişini temsil eder.","Çevresindeki eski sokaklar keşfedilir."]),
("🛶 Thu Bon Nehri Tekne Gezisi","Hoi An Riverside",30,["Hoi An'ın nehir ticareti geçmişi anlatılır.","Kısa ve güvenli bir tekne turu yapılır.","Can yelekleri kullanılmadan tekneye binilmez."]),
("✨ Hoi An Fener Akşamı","Old Town",35,["Şehir akşamları yüzlerce renkli fenerle aydınlanır.","Nehir kıyısında sakin bir aile yürüyüşü yapılır.","Bebek uyku saatine göre erken tamamlanabilir."])]}
]


tour2_plan += [
{"city":"Hanoi","title":"Hanoi Old Quarter ve Hoan Kiem Gölü","description":"Hanoi'ye geçiş sonrasında eski şehir ve göl çevresinde hafif tempolu keşif günü.","bullets":["🌊 Göl çevresi","🏮 Tarihî sokaklar","☕ Yerel kahve kültürü","🎭 Su kuklası"],"activities":[
("🌊 Hoan Kiem Gölü","Hoan Kiem",30,["Hanoi'nin kalbinde yer alan tarihî göldür.","Ngoc Son Tapınağı dışarıdan ve çevresiyle görülür.","Bebek arabasıyla rahatça gezilebilir."]),
("🏮 Hanoi Old Quarter","Old Quarter",35,["Dar sokaklar ve eski ticaret mahalleleri keşfedilir.","Kolonyal mimari ile yerel yaşam bir arada görülür.","Kalabalık saatlerde kısa rota uygulanır."]),
("☕ Yumurta Kahvesi Molası","Old Quarter",30,["Savaş dönemindeki süt kıtlığından doğduğu anlatılır.","Kremamsı yapısıyla Hanoi'nin simgesidir.","Sessiz ve klimalı bir kafede mola verilir."]),
("🎭 Su Kuklası Gösterisi","Thang Long Theatre",35,["Kuzey Vietnam'ın pirinç tarlalarında gelişen sanattır.","Canlı müzik eşliğinde köy hikâyeleri anlatılır.","Kapalı salon aile için rahat bir etkinliktir."])]},
{"city":"Hanoi","title":"Hanoi Tarihi ve Geleneksel Yaşam","description":"Vietnam'ın siyasi geçmişi, eğitim tarihi ve geleneksel mahalle kültürü keşfedilir.","bullets":["🏛️ Tarihî meydanlar","📚 Eğitim mirası","🏯 Geleneksel mimari","🍜 Kuzey mutfağı"],"activities":[
("🏛️ Ho Chi Minh Kompleksi","Ba Dinh",35,["Ho Chi Minh'in Vietnam tarihindeki rolü anlatılır.","Ba Dinh Meydanı ve saray bahçeleri görülür.","Sessiz ve saygılı ziyaret kurallarına uyulur."]),
("📚 Edebiyat Tapınağı","Dong Da",30,["1070 yılında kurulan Konfüçyüs tapınağıdır.","Vietnam'ın ilk üniversitesi olarak kabul edilir.","Geniş avluları ailece gezmeye uygundur."]),
("🏯 One Pillar Pagoda","Ba Dinh",30,["Tek taş sütun üzerinde yükselen küçük Budist tapınağıdır.","Lotus çiçeğini temsil eden mimarisi anlatılır.","Ho Chi Minh Kompleksi'ne yakındır."]),
("🍜 Bun Cha Öğle Yemeği","Hanoi Centre",35,["Izgara et, erişte ve taze otlarla servis edilir.","Hanoi mutfağının en sevilen yemeklerindendir.","Acı sos ayrı sunulur."])]},
{"city":"Sa Pa","title":"Sa Pa Dağları ve Cat Cat Köyü","description":"Kuzey Vietnam'ın dağlık Sa Pa bölgesinde etnik köy yaşamı ve pirinç terasları keşfedilir.","bullets":["⛰️ Dağ manzaraları","🌾 Pirinç terasları","🧵 Hmong kültürü","👶 Kısa yürüyüşler"],"activities":[
("⛰️ Sa Pa Şehir Merkezi","Sa Pa",30,["Fransız döneminden kalan dağ kasabası dokusu görülür.","Serin iklime alışmak için sakin başlangıç yapılır.","Sisli dağ manzaraları izlenir."]),
("🌾 Cat Cat Köyü","Muong Hoa Valley",35,["Black Hmong topluluğunun geleneksel köyüdür.","Pirinç terasları ve ahşap evler görülür.","Bebekle dik merdivenler yerine kısa rota seçilir."]),
("🧵 Hmong El Sanatları","Cat Cat",30,["İndigo boyama ve geleneksel dokuma teknikleri tanıtılır.","Yerel kadınların el emeği ürünleri incelenir.","Kültürel fotoğraflar izin alınarak çekilir."]),
("🌄 Sa Pa Gün Batımı","Sa Pa Viewpoint",35,["Hoang Lien Son dağları panoramik olarak görülür.","Hava açıksa vadinin renk değişimi izlenir.","Soğuyan hava için bebeğe kalın kıyafet hazırlanır."])]},
{"city":"Sa Pa","title":"Fansipan ve Hanoi'ye Dönüş","description":"Hindiçin'in çatısı Fansipan çevresinin keşfi ve ardından Hanoi'ye dönüş günü.","bullets":["🚞 Dağ treni","🚠 Fansipan teleferiği","🛕 Dağ tapınakları","🌄 Panoramik manzara"],"activities":[
("🚞 Muong Hoa Dağ Treni","Sa Pa Station",30,["Sa Pa merkezinden teleferik bölgesine panoramik yolculuk yapılır.","Vadi ve dağ manzaraları izlenir.","Bebekle uzun yürüyüş ihtiyacını azaltır."]),
("🚠 Fansipan Teleferiği","Fansipan",40,["Fansipan 3.143 metreyle Hindiçin'in en yüksek dağıdır.","Teleferik sayesinde zirve bölgesine kolayca ulaşılır.","Bebekte irtifa etkileri gözlemlenir ve süre kısa tutulur."]),
("🛕 Fansipan Tapınakları","Fansipan Summit Area",30,["Dağ yamacındaki Budist yapıları ve heykeller görülür.","Sisli atmosfer bölgeye özel bir görünüm kazandırır.","Zirve merdivenleri yerine erişilebilir alanlar tercih edilir."]),
("🍲 Sa Pa Sıcak Öğle Yemeği","Sa Pa",30,["Dağ iklimine uygun sıcak Vietnam yemekleri yenir.","Hanoi dönüşü öncesinde dinlenme sağlanır.","Bebek ve aile için hafif seçenekler seçilir."])]}
]
tour2 = create_tour(
    "erdi-bey-aile-turu-vietnam-2",
    "🇻🇳 Da Nang'dan başlayıp Hanoi ve Sa Pa'ya uzanan 7 günlük aile turu. 3 gün Da Nang, 2 gün Hanoi ve 2 gün Sa Pa.",
    tour2_plan, 7200
)
print("✅ TUR 2:", tour2.id, tour2.slug, tour2.price, tour2.price_currency)

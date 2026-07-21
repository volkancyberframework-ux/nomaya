from decimal import Decimal; from datetime import date,time; from django.db.models import Max; import re
from core.models import Country,City,Airport,Airline,Flight,Tour,TourDay,TourType,Bullet,TourBullet,Day,Activity,DayActivity,Hotel,DayHotel,DayFlight,Order,Traveler

TR={'sokaklari':'sokakları','rotasi':'rotası','bakis':'bakış','cevresi':'çevresi','cevresinde':'çevresinde','bahce':'bahçe','dis':'dış','kiyidan':'kıyıdan','isi':'işi','pazari':'pazarı','aksami':'akşamı','koprusu':'köprüsü','kacis':'kaçış','sanati':'sanatı','genis':'geniş','mirasi':'mirası','kizlari':'kızları','esi':'eşi','yasindaki':'yaşındaki','aracli':'araçlı','mutfagi':'mutfağı','seceneklerini':'seçeneklerini','paylasilan':'paylaşılan','yaklasik':'yaklaşık','guclu':'güçlü','alinmadigi':'alınmadığı','butce':'bütçe','plani':'planı','cikisli':'çıkışlı','konumundadir':'konumundadır','icerik':'içerik','baskisi':'baskısı','icinde':'içinde','icin':'için','Icin':'İçin','ozel':'özel','Ozel':'Özel','gun':'gün','Gun':'Gün','gunluk':'günlük','Gunluk':'Günlük','dort':'dört','Dort':'Dört','ucus':'uçuş','Ucus':'Uçuş','ucret':'ücret','ucretleri':'ücretleri','kisi':'kişi','Kisi':'Kişi','basi':'başı','Muze':'Müze','muze':'müze','kayitlari':'kayıtları','sonra':'sonra','varis':'varış','Varis':'Varış','cikis':'çıkış','Cikis':'Çıkış','yerlesme':'yerleşme','ayni':'aynı','dagitilir':'dağıtılır','ulasim':'ulaşım','Ulasim':'Ulaşım','ulasimdan':'ulaşımdan','cevre':'çevre','Cevre':'Çevre','cevreye':'çevreye','alisma':'alışma','baslanir':'başlanır','kesif':'keşif','Kesif':'Keşif','kesiflerden':'keşiflerden','ayrilis':'ayrılış','Kultur':'Kültür','kultur':'kültür','yasam':'yaşam','yasami':'yaşamı','birlestirilir':'birleştirilir','saattir':'saattir','yuruyus':'yürüyüş','Yuruyus':'Yürüyüş','tasima':'taşıma','odaklidir':'odaklıdır','ucretsiz':'ücretsiz','Ucretsiz':'Ücretsiz','istege':'isteğe','bagli':'bağlı','kisisel':'kişisel','degildir':'değildir','ayri':'ayrı','olusan':'oluşan','ayrilmistir':'ayrılmıştır','baglantili':'bağlantılı','koordinatli':'koordinatlı','bulusma':'buluşma','noktasi':'noktası','noktalari':'noktaları','odagi':'odağı','fotograf':'fotoğraf','Fotograf':'Fotoğraf','molalari':'molaları','siparisleri':'siparişleri','butcesine':'bütçesine','birakilir':'bırakılır','Simgesel':'Simgesel','yapilari':'yapıları','meydanlari':'meydanları','mekanlari':'mekânları','disaridan':'dışarıdan','incelenir':'incelenir','Mahalle':'Mahalle','sokaklarda':'sokaklarda','gundelik':'gündelik','bolgeye':'bölgeye','ozgu':'özgü','yesil':'yeşil','seyir':'seyir','firin':'fırın','mekanlar':'mekânlar','zorunlu':'zorunlu','noktasindan':'noktasından','gecilir':'geçilir','birakma':'bırakma','tanitimi':'tanıtımı','yorgunluk':'yorgunluk','guvenli':'güvenli','ertesi':'ertesi','gozden':'gözden','donulerek':'dönülerek','tamamlanir':'tamamlanır','emaneti':'emaneti','bilgileri':'bilgileri','simgesel':'simgesel','eksik':'eksik','yakin':'yakın','Hatira':'Hatıra','Fotograflari':'Fotoğrafları','Arastirmasi':'Araştırması','arastirmasi':'araştırması','Baslangic':'Başlangıç','gosterilir':'gösterilir','suresi':'süresi','saat':'saat','dakika':'dakika','cevresindeki':'çevresindeki','secili':'seçili','mantikli':'mantıklı','sirasiyla':'sırasıyla','cocuk':'çocuk','Cocuk':'Çocuk','ihtiyaci':'ihtiyacı','kosullarina':'koşullarına','gore':'göre','ayarlanabilir':'ayarlanabilir','kisa':'kısa','gozlemlemek':'gözlemlemek','verilir':'verilir','onerilir':'önerilir','tarafindan':'tarafından','alindi':'alındı','ayarlandi':'ayarlandı','Tarz':'Tarz','Alacati':'Alaçatı','Cesme':'Çeşme','Izmir':'İzmir','Istanbul':'İstanbul','Turkiye':'Türkiye','Omer':'Ömer','Ozkan':'Özkan','Ozdogan':'Özdoğan','Ozturk':'Öztürk','Ustuner':'Üstüner','Kiz':'Kız','Es':'Eş','Akraba':'Akraba','arkadasini':'arkadaşını','Arkadas':'Arkadaş','yalnizca':'yalnızca','tamamen':'tamamen','sinirlari':'sınırları','yavas':'yavaş','dahil':'dahil','cikarmalar':'çıkarımlar','donusu':'dönüşü','donus':'dönüş','karsilama':'karşılama','giris':'giriş','eski':'eski','sehir':'şehir','Sehir':'Şehir','kiyisi':'kıyısı','sahil':'sahil','degirmenler':'değirmenler','tatlari':'tatları','tas':'taş','Baslangic/bulusma':'Başlangıç/buluşma'}
def T(v): return re.sub(r'\b('+'|'.join(sorted(map(re.escape,TR),key=len,reverse=True))+r')\b',lambda m:TR[m.group(0)],str(v))

def make(cfg, rows):
    typ,_=TourType.objects.get_or_create(name=T(cfg['style'])[:80])
    old=Tour.objects.filter(slug=cfg.get('legacy_slug','')).first(); exists=Tour.objects.filter(slug=cfg['slug']).exists()
    if old and not exists: old.slug=cfg['slug']; old.save(update_fields=['slug'])
    tour,_=Tour.objects.update_or_create(slug=cfg['slug'],defaults={'title':T(cfg['title']),'start_date':cfg['start'],'end_date':cfg['end'],'overview':T(cfg['overview']),'info':'Kişiye özel, günlük dört aktiviteli plan. Her aktivite 1,5 saat ve kişi başı 5 USD’dir. Müze biletleri, restoran hesapları ve kişisel harcamalar dahil değildir. Ses kayıtları daha sonra eklenebilir.','commission':Decimal('1.00'),'price_currency':'USD','badge_text':f"{len(rows)} Günlük Özel Plan",'allow_flights':True,'allow_hotels':True,'allow_transfers':False,'is_published':True})
    tour.tour_types.set([typ]); tour.places_covered.clear(); TourDay.objects.filter(tour=tour,order__gt=len(rows)).delete()
    TourBullet.objects.filter(tour=tour).delete(); hs=[f"🧭 {len(rows)} gün, her gün 4 aktivite",f"🎯 Tarz: {T(cfg['style'])}","⏱️ Her aktivite 1,5 saat; günlük toplam 6 saat",f"✈️ Uçuş: {'gezgin tarafından alındı' if cfg['flight'] else 'programa eklenmedi'}",f"🏨 Konaklama: {'gezgin tarafından ayarlandı' if cfg['hotel'] else 'programa eklenmedi'}"]
    for q,x in enumerate(hs,1): b,_=Bullet.objects.get_or_create(text=f"{T(cfg['title'])} — {x}",defaults={'icon':'check','tags':'custom,nomaya'}); TourBullet.objects.create(tour=tour,bullet=b,section='highlights',order=q)
    made_days=[]
    for i,(city_name,country_name,iso,title,lat,lng) in enumerate(rows,1):
        country,_=Country.objects.get_or_create(name=T(country_name),defaults={'iso2':iso})
        city,_=City.objects.get_or_create(name=T(city_name),country=country); title=T(title)
        td=TourDay.objects.filter(tour=tour,order=i).select_related('day').first()
        if td: d=td.day; d.day_number=(Day.objects.filter(city=city).aggregate(m=Max('day_number'))['m'] or 0)+1 if d.city_id!=city.id else d.day_number
        else: d=Day.objects.create(city=city,day_number=(Day.objects.filter(city=city).aggregate(m=Max('day_number'))['m'] or 0)+1); td=TourDay.objects.create(tour=tour,day=d,order=i)
        flow='Varis, otele yerlesme ve otelden cikis ayni gune dengeli dagitilir.' if len(rows)==1 else ('Otele ulasim, check-in ve cevreye alisma ile baslanir.' if i==1 else ('Son kesiflerden sonra check-out, bagaj ve ayrilis plani tamamlanir.' if i==len(rows) else 'Kultur, mahalle yasami, manzara ve gastronomi dengeli tempoda birlestirilir.'))
        d.city=city; d.title=title; d.description=f'{title}. {T(flow)} Her aktivite 1,5 saattir; rota yürüyüş ve toplu taşıma odaklıdır. Ana mekânlar ücretsizdir, isteğe bağlı kişisel yeme-içme harcamaları programa dahil değildir.'
        d.bullets=['Dört ayrı aktiviteden oluşan 6 saatlik günlük plan','Her aktivite için 1 saat 30 dakika ayrılmıştır','Ücretsiz veya kişi başı en fazla 5 USD olan duraklar','Apple Maps bağlantılı koordinatlı buluşma noktaları','Yerel kültür, mimari ve mahalle yaşamı odağı','Dinlenme, fotoğraf ve serbest keşif molaları','Yeme-içme siparişleri gezginin tercihine ve bütçesine bırakılır']; d.price_currency='USD'; d.save()
        td.title=f'Gün {i}: {title}'; td.save(update_fields=['title'])
        made=[]; normal=[('Simgesel Noktalar ve Mimari','Rotanin ana yapilari, meydanlari ve kamusal mekanlari disaridan incelenir.'),('Mahalle ve Lokal Yasam','Ara sokaklarda gundelik yasam, yerel isletmeler ve bolgeye ozgu sokak dokusu kesfedilir.'),('Park, Sahil ve Manzara','Yesil alan, sahil veya seyir noktasinda dinlenme ve fotograf molalari verilir.'),('Pazar ve Lokal Lezzet Arastirmasi','Yerel pazar, firin ve uygun fiyatli mekanlar incelenir; siparis vermek zorunlu degildir.')]
        first=[('Otele Varis, Check-in ve Cevreye Alisma','Varis noktasindan konaklama bolgesine gecilir; check-in, bagaj birakma ve temel cevre tanitimi yapilir.'),normal[0],normal[1],('Sakin Aksam Yuruyusu ve Gun Sonu Plani','Yorgunluk seviyesine gore guvenli ve kolay bir aksam rotasi izlenir; ertesi gunun ulasim plani gozden gecirilir.')]
        last=[normal[1],normal[3],('Son Simgesel Duraklar ve Hatira Fotograflari','Rotada eksik kalan yakin noktalar tamamlanir ve son fotograf molalari verilir.'),('Otelden Cikis, Bagaj Plani ve Ugurlama','Otele donulerek check-out tamamlanir; bagaj teslimi veya emaneti planlanir ve ayrilis noktasina gecis bilgileri kontrol edilir.')]
        single=[first[0],normal[0],normal[3],last[3]]
        parts=single if len(rows)==1 else (first if i==1 else (last if i==len(rows) else normal))
        for j,(part,detail) in enumerate(parts,1):
            at=f'{title} — {T(part)}'; a=Activity.objects.filter(city=city,title=at).first() or Activity(city=city,title=at)
            a.location_text=f'{title} rotası, {T(city_name)}. Başlangıç/buluşma noktası harita koordinatında gösterilir.'; a.duration_hours=Decimal('1.50'); a.price=Decimal('5.00'); a.price_currency='USD'; a.points=[f'🧭 {T(detail)}',f'⏱️ Aktivite süresi: 1 saat 30 dakika.',f'📍 {title} çevresindeki seçili noktalar mantıklı yürüyüş sırasıyla gezilir.',f'💵 Nomaya aktivite bedeli 5 USD; müze bileti, yemek ve kişisel harcamalar dahil değildir.',f'🚶 Tempo; çocuk, aile yapısı, dinlenme ihtiyacı ve hava koşullarına göre ayarlanabilir.',f'📸 Fotoğraf, kısa video ve çevreyi gözlemlemek için serbest molalar verilir.',f'🎒 Telefon, su, rahat ayakkabı ve mevsime uygun kıyafet önerilir.']; a.miles_reward=25; a.latitude=Decimal(str(lat)); a.longitude=Decimal(str(lng)); a.apple_maps_url=f'https://maps.apple.com/?ll={lat},{lng}&q={at.replace(" ","+")}'; a.save(); a.tour_types.add(typ); made.append(a)
            DayActivity.objects.update_or_create(day=d,activity=a,defaults={'order':j})
        DayActivity.objects.filter(day=d).exclude(activity__in=made).delete(); d.recompute_price(); tour.places_covered.add(city); made_days.append(d)
    if cfg.get('stay'):
        sc,cn,iso,name=cfg['stay']; co,_=Country.objects.get_or_create(name=T(cn),defaults={'iso2':iso}); ci,_=City.objects.get_or_create(name=T(sc),country=co); h,_=Hotel.objects.get_or_create(name=T(name),city=ci,defaults={'star':3,'price_per_night':Decimal('0.00'),'price_currency':'USD','hotel_type':'hotel'})
        for d in made_days[:-1] or made_days: DayHotel.objects.update_or_create(day=d,hotel=h,defaults={'order':1}); d.recompute_price()
    if cfg.get('flights'):
        airline,_=Airline.objects.get_or_create(name='Gezgin Tarafindan Ayarlanmis Ucus')
        for k,f in enumerate(cfg['flights']):
            oc,ocn,oi,oa,dc,dcn,di,da,num,dep,arr,dur=f
            oco,_=Country.objects.get_or_create(name=T(ocn),defaults={'iso2':oi}); oci,_=City.objects.get_or_create(name=T(oc),country=oco); op,_=Airport.objects.get_or_create(iata=oa,defaults={'name':f'{T(oc)} Airport','city':oci})
            dco,_=Country.objects.get_or_create(name=T(dcn),defaults={'iso2':di}); dci,_=City.objects.get_or_create(name=T(dc),country=dco); dp,_=Airport.objects.get_or_create(iata=da,defaults={'name':f'{T(dc)} Airport','city':dci})
            fl,_=Flight.objects.get_or_create(airline=airline,flight_number=num,origin=op,destination=dp,defaults={'departure_time':dep,'arrival_time':arr,'duration_minutes':dur,'price':Decimal('0.00'),'price_currency':'USD'})
            target=made_days[0] if k==0 else made_days[-1]; DayFlight.objects.update_or_create(day=target,flight=fl,defaults={'order':k+1}); target.recompute_price()
    tour.recompute_item_counts(); tour.recompute_price()
    order,_=Order.objects.update_or_create(tour=tour,email=cfg['email'],defaults={'pax':cfg.get('pax',1),'start_date':cfg['start'],'end_date':cfg['end'],'same_room':True,'hide_flights':cfg['flight'],'hide_hotels':cfg['hotel'],'hide_transfers':True,'total_price':Decimal(cfg['try_total']),'is_paid':True,'payment_method':'payment_link'})
    Traveler.objects.filter(order=order).delete(); [Traveler.objects.create(order=order,first_name=T(f),last_name=T(l),phone=p) for f,l,p in cfg.get('travelers',[(cfg['first'],cfg['last'],cfg['phone'])])]
    print(f'https://nomaya.co/tours/booking/p/{order.public_id}/')

make({'slug':'ozkan-nice-marsilya-8-gun','legacy_slug':'ozkan-nice-marsilya-1-gun','title':'Ozkan icin Nice’ten Marsilya’ya Riviera ve Lezzet Rotasi','start':date(2026,11,14),'end':date(2026,11,21),'overview':'14 Kasim Nice varisi ve 21 Kasim Marsilya donusu arasinda bol yuruyus, sahil kasabalari, tarihi mahalleler ve yerel Provence lezzetleri.','style':'Riviera Kesfi ve Gastronomi','email':'ozkansports@gmail.com','phone':'5423871028','first':'Ozkan','last':'Sports','flight':True,'hotel':False,'try_total':'100.00','flights':[('Istanbul','Turkiye','TR','IST','Nice','France','FR','NCE','OWN-NCE',None,None,180),('Marseille','France','FR','MRS','Istanbul','Turkiye','TR','IST','OWN-MRS',None,None,190)]},[('Nice','France','FR','Nice varisi, Vieux Nice ve Cours Saleya’ya ilk bakis','43.697166','7.276581'),('Nice','France','FR','Promenade des Anglais, Colline du Chateau ve liman','43.695440','7.279680'),('Eze','France','FR','Eze tas sokaklari, egzotik bahce cevresi ve panorama','43.727930','7.361950'),('Monaco','Monaco','MC','Monaco-Ville, liman ve Monte Carlo dis mekan rotasi','43.738418','7.424616'),('Antibes','France','FR','Antibes eski sehir, Provencal pazar ve surlar','43.580615','7.123865'),('Cannes','France','FR','Le Suquet, eski liman ve Croisette yuruyusu','43.551300','7.012750'),('Marseille','France','FR','Vieux-Port, Le Panier ve Notre-Dame manzaralari','43.296482','5.369780'),('Marseille','France','FR','Noailles pazari, Corniche ve Marsilya’dan ayrilis','43.292900','5.374350')])

make({'slug':'bahri-aarhus-kuzey-avrupa-random-8-gun','legacy_slug':'bahri-danimarka-youtuber-8-gun','title':'Bahri icin Aarhus Merkezli Random Kuzey Avrupa Rotasi','start':date(2026,8,2),'end':date(2026,8,9),'overview':'Aarhus’taki akraba evini ana us yapan; Hamburg ve Odense gunubirlik, Kopenhag’da iki gece ve Malmo gecisli, icerik baskisi olmayan spontane rota.','style':'Random Gezi ve Sehir Kesfi','email':'bahri.ustuner@gmail.com','phone':'05059314519','first':'Bahri','last':'Ustuner','flight':False,'hotel':False,'try_total':'800.00'},[
('Aarhus','Denmark','DK','Aarhus’a varis, Latin Quarter ve nehir kiyisi','56.157200','10.210700'),
('Aarhus','Denmark','DK','Dokk1, liman mimarisi ve Marselisborg sahili','56.153500','10.214900'),
('Hamburg','Germany','DE','Hamburg gunubirlik: Speicherstadt, Elbphilharmonie ve liman','53.543700','9.984200'),
('Odense','Denmark','DK','Odense gunubirlik: H.C. Andersen izleri ve eski merkez','55.395940','10.388310'),
('Copenhagen','Denmark','DK','Kopenhag ilk gun: Nyhavn, Kraliyet Mahallesi ve Stroget','55.679822','12.591048'),
('Copenhagen','Denmark','DK','Kopenhag ikinci gun: Norrebro, Superkilen ve kanallar','55.699496','12.542969'),
('Malmo','Sweden','SE','Malmo gunubirlik: Gamla Staden, Lilla Torg ve sahil','55.605870','13.000730'),
('Aarhus','Denmark','DK','Aarhus’a donus, yerel pazarlar ve sakin final','56.156740','10.203870')])

make({'slug':'ezgi-sadece-recife-lokal-35-gun','legacy_slug':'ezgi-recife-istanbul-lokal-35-gun','title':'Ezgi icin 35 Gunluk Lokal Recife Yasami','start':date(2027,1,2),'end':date(2027,2,5),'overview':'Recife’de yasayan arkadasini ziyaret eden Ezgi icin tamamen Recife sinirlari icinde; mahalleler, pazarlar, sahiller, parklar ve gundelik yasama yayilan yavas tempolu lokal plan. Istanbul ve Olinda programa dahil degildir.','style':'Recife Lokal Yasam ve Kultur','email':'ezgiserdar16@gmail.com','phone':'+905428295658','first':'Ezgi','last':'Serdar','flight':False,'hotel':True,'try_total':'3500.00','stay':('Recife','Brazil','BR','Arkadas Yaninda Konaklama – Recife')},[
('Recife','Brazil','BR','Marco Zero ve Recife Antigo yuruyusu','-8.063122','-34.871130'),
('Recife','Brazil','BR','Rua do Bom Jesus ve tarihi cepheler','-8.061619','-34.871063'),
('Recife','Brazil','BR','Parque das Esculturas kiyidan seyir','-8.062648','-34.867364'),
('Recife','Brazil','BR','Cais do Sertao cevresi ve liman hikayesi','-8.061271','-34.870029'),
('Recife','Brazil','BR','Casa da Cultura avlulari ve yerel el isi','-8.067526','-34.884752'),
('Recife','Brazil','BR','Mercado de Sao Jose lokal pazar rotasi','-8.071275','-34.880615'),
('Recife','Brazil','BR','Boa Viagem sahil promenadi','-8.125491','-34.898845'),
('Recife','Brazil','BR','Parque Dona Lindu mimari ve sahil','-8.141502','-34.903041'),
('Recife','Brazil','BR','Praca do Arsenal ve Bom Jesus aksami','-8.060272','-34.871983'),
('Recife','Brazil','BR','Capibaribe kiyisi ve Rua da Aurora','-8.058657','-34.881290'),
('Recife','Brazil','BR','Parque da Jaqueira yerel sabah rutini','-8.037673','-34.904988'),
('Recife','Brazil','BR','Pina sahili ve gun batimi yuruyusu','-8.086758','-34.886264'),
('Recife','Brazil','BR','Mercado da Madalena ve mahalle kahvalti kulturu','-8.052570','-34.908270'),
('Recife','Brazil','BR','Mercado da Encruzilhada ve kuzey mahalleleri','-8.036210','-34.891030'),
('Recife','Brazil','BR','Mercado de Casa Amarela ve lokal alisveris','-8.026490','-34.917080'),
('Recife','Brazil','BR','Sitio Trindade, Poco da Panela ve tarih izleri','-8.028930','-34.912650'),
('Recife','Brazil','BR','Parque Santana ve Capibaribe kiyisi','-8.041500','-34.914780'),
('Recife','Brazil','BR','Parque da Macaxeira ve mahalle yasami','-8.014900','-34.933900'),
('Recife','Brazil','BR','Jardim Botanico’da Atlantik Ormani ve ekoloji','-8.075760','-34.962150'),
('Recife','Brazil','BR','Varzea meydani, tarihi evler ve Capibaribe','-8.050900','-34.958210'),
('Recife','Brazil','BR','UFPE kampusu, sanat ve genis yesil alanlar','-8.052240','-34.951620'),
('Recife','Brazil','BR','Derby Meydani ve Benfica mahalle rotasi','-8.057480','-34.900410'),
('Recife','Brazil','BR','Parque 13 de Maio ve Boa Vista kulturu','-8.058860','-34.881060'),
('Recife','Brazil','BR','Praca da Republica ve Santo Antonio mimarisi','-8.061970','-34.878070'),
('Recife','Brazil','BR','Forte das Cinco Pontas cevresi ve Sao Jose','-8.075510','-34.880580'),
('Recife','Brazil','BR','Mercado de Afogados ve gercek mahalle pazari','-8.080210','-34.906610'),
('Recife','Brazil','BR','Mercado do Cordeiro ve lokal ogle rotasi','-8.047300','-34.929300'),
('Recife','Brazil','BR','Brasilia Teimosa ve Pina balikci kulturu','-8.081850','-34.883420'),
('Recife','Brazil','BR','Boa Viagem kuzey kesimi ve sahil sanati','-8.112830','-34.892620'),
('Recife','Brazil','BR','Boa Viagem meydani, kilise ve aksam pazari','-8.131210','-34.900020'),
('Recife','Brazil','BR','Dona Lindu’da Niemeyer mimarisi ve gun batimi','-8.141502','-34.903041'),
('Recife','Brazil','BR','Imbiribeira lagunu ve mahalle kesfi','-8.110630','-34.914970'),
('Recife','Brazil','BR','Cais Jose Estelita ve sehir donusumu rotasi','-8.076010','-34.885150'),
('Recife','Brazil','BR','Capibaribe kopruleri ve Recife’nin suyla hikayesi','-8.064530','-34.876950'),
('Recife','Brazil','BR','Recife Antigo finali, hediyelikler ve ayrilis hazirligi','-8.061619','-34.871063')])

make({'slug':'omer-faruk-mainz-aile-kultur-11-gun','legacy_slug':'omer-faruk-mainz-kultur-doga-11-gun','title':'Kendirci Ailesi icin Mainz, Ren Vadisi ve Kultur Rotasi','start':date(2026,8,11),'end':date(2026,8,21),'overview':'Omer Faruk (36), esi (40) ve 7 yasindaki kizlari icin ozel aracli; muze, eski sehir, doga, outlet ve alkolsuz Alman mutfagi seceneklerini birlestiren aile plani. Konaklama yakinin evinde ve paylasilan Google Maps konumundadir.','style':'Cocuk Dostu Kultur Tarih Gastronomi Doga','email':'omerfarukkendirci@gmail.com','phone':'+905076992249','first':'Omer Faruk','last':'Kendirci','pax':3,'travelers':[('Omer Faruk','Kendirci','+905076992249'),('Es','Kendirci',''),('Kiz Cocuk','Kendirci','')],'flight':True,'hotel':True,'try_total':'1100.00','stay':('Mainz','Germany','DE','Yakin Akraba Evi – Paylasilan Google Maps Konumu'),'flights':[('Istanbul','Turkiye','TR','IST','Frankfurt am Main','Germany','DE','FRA','OWN-FRA',None,None,190),('Frankfurt am Main','Germany','DE','FRA','Istanbul','Turkiye','TR','IST','OWN-IST',None,None,180)]},[
('Mainz','Germany','DE','Akraba evine varis, yerlesme ve yakin cevre aile kesfi','49.998960','8.274292'),
('Mainz','Germany','DE','Mainzer Dom, Marktplatz, Gutenberg mirasi ve eski sehir','49.998960','8.274292'),
('Mainz','Germany','DE','Roma tiyatrosu, Isis Tapinagi ve aile dostu tarih rotasi','49.992610','8.277760'),
('Mainz','Germany','DE','Ren promenadi, Stadtpark ve cocuk oyun molalari','49.990175','8.287067'),
('Wiesbaden','Germany','DE','Kurhaus, Nerotal ve alkolsuz Alman mutfagi deneyimi','50.084358','8.245723'),
('Rudesheim am Rhein','Germany','DE','Ozel aracla Ren Vadisi, Rudesheim ve Bingen manzaralari','49.979722','7.923889'),
('Heidelberg','Germany','DE','Heidelberg gunubirlik: kale manzarasi, eski sehir ve Neckar','49.410610','8.715690'),
('Speyer','Germany','DE','Speyer eski sehir, katedral ve cocuk dostu teknik miras','49.317276','8.442157'),
('Frankfurt am Main','Germany','DE','Romerberg, Main kiyisi ve cocuk dostu muze bolgesi','50.110620','8.682100'),
('Montabaur','Germany','DE','Montabaur Fashion Outlet ve ailece dinlenme molalari','50.437040','7.830780'),
('Mainz','Germany','DE','Neustadt pazari, alkolsuz lokal restoran ve ayrilis','50.006739','8.259897')])

make({'slug':'melis-new-york-ilk-kez-9-gun','legacy_slug':'fmel-new-york-ilk-kez-9-gun','title':'Melis icin Ilk New York Deneyimi','start':date(2026,10,10),'end':date(2026,10,18),'overview':'10 Ekim 10:55 JFK varisi ve 18 Ekim 00:25 JFK donusu dikkate alinarak hazirlanan ilk New York rotasi. Central Park cevresinde gecelik yaklasik 90–100 USD hedefli konaklama arastirmasi; Manhattan ve Brooklyn’de simgesel yerler ve lokal tatlar.','style':'Ilk Kez New York ve Lokal Lezzetler','email':'fmelozturk@gmail.com','phone':'5354727287','first':'Melis','last':'Ozturk','pax':2,'travelers':[('Melis','Ozturk','5354727287'),('Misafir','Ozturk','')],'flight':True,'hotel':False,'try_total':'900.00','flights':[('Istanbul','Turkiye','TR','IST','New York','United States','US','JFK','OWN-JFK',None,time(10,55),660),('New York','United States','US','JFK','Istanbul','Turkiye','TR','IST','OWN-IST',time(0,25),None,600)]},[
('New York','United States','US','JFK 10:55 varis, otele gecis ve sakin Midtown tanisma','40.758000','-73.985500'),
('New York','United States','US','Central Park guneyden kuzeye yuruyus','40.781219','-73.966514'),
('New York','United States','US','High Line, Chelsea Market cevresi ve Hudson','40.748000','-74.004800'),
('New York','United States','US','Brooklyn Bridge ve DUMBO fotograf rotasi','40.703316','-73.988145'),
('New York','United States','US','Statue of Liberty manzarali Staten Island Ferry','40.701730','-74.013369'),
('New York','United States','US','Wall Street, 9/11 cevresi ve Oculus','40.711566','-74.013443'),
('New York','United States','US','SoHo, Nolita, Chinatown ve Little Italy','40.720756','-74.000761'),
('New York','United States','US','Williamsburg ve Domino Park gun batimi','40.715020','-73.967870'),
('New York','United States','US','Roosevelt Island Tram ve Midtown finali','40.761433','-73.964058')])

make({'slug':'edanur-londra-solo-6-gun','title':'Edanur icin Solo Londra Rotasi','start':date(2026,9,28),'end':date(2026,10,3),'overview':'Izmir cikisli, tek basina seyahate uygun ve metro baglantilari guclu Londra plani. Ucak ile otel henuz alinmadigi icin tur kalemi eklenmemistir; ikisi icin toplam yaklasik 60.000 TL hedef butce ve merkezi, guvenli otel bolgeleri dikkate alinmistir.','style':'Solo Seyahat ve Dengeli Butce','email':'edanurkurt52@hotmail.com','phone':'05316509669','first':'Edanur','last':'Kurt','flight':False,'hotel':False,'try_total':'600.00'},[
('London','United Kingdom','GB','Westminster, St James Park ve Buckingham cevresi','51.500729','-0.124625'),
('London','United Kingdom','GB','South Bank, Borough Market cevresi ve Tate disi','51.505504','-0.090649'),
('London','United Kingdom','GB','British Museum, Bloomsbury ve Covent Garden','51.519413','-0.126957'),
('London','United Kingdom','GB','Notting Hill, Portobello ve Kensington Gardens','51.509438','-0.196580'),
('London','United Kingdom','GB','Greenwich Park ve Thames manzarasi','51.476909','0.000517'),
('London','United Kingdom','GB','Camden, Regent Canal ve Primrose Hill finali','51.539190','-0.142500')])

make({'slug':'talha-alacati-cesme-doga-lezzet-2-gun','legacy_slug':'talha-izmir-doga-lezzet-2-gun','title':'Talha icin Alacati ve Cesme Doga–Lezzet Rotasi','start':date(2026,7,23),'end':date(2026,7,24),'overview':'Denize girme plani olmadan Alacati tas sokaklari, Cesme tarihi, seyir noktalari ve kaliteli Ege lezzetlerine odaklanan iki gunluk program.','style':'Alacati Cesme Doga ve Lokal Gastronomi','email':'Talhaozdogan@hotmail.com','phone':'+905454416499','first':'Talha','last':'Ozdogan','flight':True,'hotel':True,'try_total':'200.00','stay':('Cesme','Turkiye','TR','Gezgin Tarafindan Ayarlanmis Cesme Konaklamasi'),'flights':[('Istanbul','Turkiye','TR','IST','Izmir','Turkiye','TR','ADB','OWN-ADB',None,None,70),('Izmir','Turkiye','TR','ADB','Istanbul','Turkiye','TR','IST','OWN-IST',None,None,70)]},[
('Alacati','Turkiye','TR','Otele varis, Alacati tas sokaklari, degirmenler ve Ege tatlari','38.282220','26.374810'),
('Cesme','Turkiye','TR','Cesme Kalesi cevresi, marina, Dalyan ve ayrilis','38.323600','26.302800')])


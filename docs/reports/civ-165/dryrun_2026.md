# CIV-165 — 2026 PP ilk yükleme provası

Kaynak: `2026-performans-programi_ONAYLI.idml`; SHA256: `1aaa0bb81c3cf4e245edaab42452a972b8a59ffc252814216c7628f6dbaf33d6`.

Yalnız yerel, geçici PostgreSQL: önce onaylı 2027 kitabı, sonra 2026 kitabı aynı veritabanına yüklendi. Canlı veritabanına bağlanılmadı. Doğrulama uyarıları kaynak bilgisi olarak korundu; yükleme reddi değildir.

| Ölçüm | Sonuç |
| --- | ---: |
| departments | 33 |
| cards | 105 |
| indicators | 226 |
| activities | 182 |
| cost_rows | 2884 |
| source_cost_cells | 3276 |
| economic_values | 1270 |
| catalogue_entries | 106 |
| catalogue_responsibilities | 106 |
| catalogue_links | 8 |
| unlinked_catalogue_activities | 174 |
| dropped_guidance_rows | 210 |
| refusals | 0 |
| amount_differences | 0 |
| persistent_indicator_links | 0 |

2027 satır hash önce: `e917e7e3f4f911a8cc56c01de872c2a321a1fb96e771b63d7718254b5d4758f0`.

2027 satır hash sonra: `e917e7e3f4f911a8cc56c01de872c2a321a1fb96e771b63d7718254b5d4758f0`.

Tutar kontrolü mevcut BookAudit kitap→Word ve storage_issues ayrıştırma→saklama karşılaştırmalarını kullanır. Bütün kart, faaliyet, personel ve ekonomik kaynak hücreleri karşılaştırıldı. Boş hücreler mevcut importer kuralıyla satır oluşturmayabilir; çizgi ve sıfır ayrı tutulur. Ekonomik tablolarda mevcut 2027 akışı gibi önceki yıl sonu sütunu saklama modelinin kapsamı dışındadır.

## Dönem adları

| Sistem müdürlüğü | 2026 Sorumlu İdare adı |
| --- | --- |
| Afet İşleri ve Risk Yönetimi Müdürlüğü | Afet İşleri ve Risk Değerlendirme Müdürlüğü |
| Halkla İlişkiler Müdürlüğü | Basın Yayın ve Halkla İlişkiler Müdürlüğü |
| Plan Proje Müdürlüğü | Harita ve Planlama Müdürlüğü |
| Sosyal Destek Müdürlüğü | Sosyal Hizmetler Müdürlüğü |

## Kataloğa bağlanmayan maliyet faaliyetleri

Ad yalnız aynı müdürlükte tekil ve normalleştirilmiş olarak eşitse bağlandı. Benzer adlar seçilmedi.

| Müdürlük | Faaliyet | Kitap sayfası |
| --- | --- | --- |
| Park ve Bahçeler Müdürlüğü | Ağaçlandırma ve Yeşil Alanların Artırılması: Kent genelinde ağaçlandırma çalışmaları yaparak yeşil alan miktarını artırmak ve biyolojik çeşitliliği korumak. | 122 |
| Etüd Proje Müdürlüğü | Yeni kamu yapıları projeleri için fizibilite etütleri hazırlamak | 124 |
| Etüd Proje Müdürlüğü | Denetim ve Uygulama Süreçlerinin İyileştirilmesi | 124 |
| Etüd Proje Müdürlüğü | Personelin teknik bilgi ve becerilerini artırmak için eğitim programları düzenlemek | 124 |
| Halkla İlişkiler Müdürlüğü | Basın Mensuplarıyla İlişkileri Geliştirme toplantıları düzenlemek | 180 |
| Etüd Proje Müdürlüğü | Yeni kamu yapıları projeleri için fizibilite etütleri hazırlamak | 124 |
| Halkla İlişkiler Müdürlüğü | Mahalle Meclislerinin Kurulması | 180 |
| Etüd Proje Müdürlüğü | İşbirliği ve Koordinasyon (Kamu, Kurum, Kuruluş, STK’lar ve Üniversiteler | 124 |
| Fen İşleri Müdürlüğü | Sorumluluğumuzda bulunan binaların bakım onarım tadilat tamirat çalışmalarının yapılması | 118 |
| İmar ve Şehircilik Müdürlüğü | Meri Mevzuat Kapsamında Yapı Ruhsatı Düzenlemek | 119 |
| Park ve Bahçeler Müdürlüğü | Bitkisel Peyzaj Düzenlemeleri: Bitkilendirme, budama, gübreleme gibi rutin peyzaj bakımlarının yapılması | 122 |
| Etüd Proje Müdürlüğü | Sigara İçme Alanı Standartlarının Belirlenmesi | 124 |
| Park ve Bahçeler Müdürlüğü | Kentsel Donatıların Yönetimi: Çocuk oyun grupları, spor aletleri, oturma grupları gibi kentsel donatıların temini, montajı, bakımı ve onarımı | 122 |
| Park ve Bahçeler Müdürlüğü | Bitkisel Peyzaj Düzenlemeleri: Bitkilendirme, budama, gübreleme gibi rutin peyzaj bakımlarının yapılması. | 122 |
| Park ve Bahçeler Müdürlüğü | Peyzaj Projelerinin İncelenmesi: Ruhsat ve iskân aşamasındaki yapıların peyzaj projelerinin incelenmesi, onaylanması ve denetimi | 122 |
| Sağlık İşleri Müdürlüğü | Koruyucu sağlık hizmetleri, evde bakım, hasta nakil hizmetlerinin verilmesi | 98 |
| Sağlık İşleri Müdürlüğü | Psikolojik ve Beslenme danışmanlığı hizmetinin verilmesi | 98 |
| Sağlık İşleri Müdürlüğü | İlçe genelinde vektörel ilaçlama ve dezenfekte İşlemlerini gerçekleştirmek | 98 |
| Sağlık İşleri Müdürlüğü | Özel gereksinimli bireylerin sosyal aktivite ve gelişim becerilerini desteklemek | 98 |
| Ruhsat ve Denetim Müdürlüğü | Denetim faaliyetleri | 100 |
| Ruhsat ve Denetim Müdürlüğü | Ruhsatlandırma faaliyetleri | 100 |
| Ruhsat ve Denetim Müdürlüğü | Yıl içerisinde vatandaşlardan gelen şikâyetlerin takibi | 100 |
| Zabıta Müdürlüğü | Mühürleme işlemleri ve denetimi | 105 |
| Zabıta Müdürlüğü | Seyyar satıcılık ve dilencilikle mücadele | 105 |
| Zabıta Müdürlüğü | Fiyat ve etiket denetimleri | 105 |
| Zabıta Müdürlüğü | Kabahatler kanunu uygulamaları | 105 |
| Zabıta Müdürlüğü | Ruhsatsız ve kaçak yapılarla mücadele | 105 |
| Zabıta Müdürlüğü | Belediye sınırları içindeki düzenin sağlanması | 105 |
| Zabıta Müdürlüğü | Kanun ve yönetmeliklere uyumun sağlanması | 105 |
| Veteriner İşleri Müdürlüğü | Uluslararası standartlarda, hayvan barınağı yapmak | 109 |
| Veteriner İşleri Müdürlüğü | Sahipsiz hayvanların tüm bakım, tedavi ve rehabilite hizmetlerini gerçekleştirmek | 109 |
| Veteriner İşleri Müdürlüğü | Periyodik aralıklarla sokak hayvanlarının besleme hizmetlerini gerçekleştirmek | 109 |
| Veteriner İşleri Müdürlüğü | Hayvanların kısırlaştırma işlemlerini yapmak. | 109 |
| Veteriner İşleri Müdürlüğü | Okullarda hayvan sevgisi ve sorumluluğu konularında seminerler vermek | 109 |
| Veteriner İşleri Müdürlüğü | 4 Ekim dünya hayvanlar gününde çeşitli etkinlikler düzenlemek | 109 |
| Emlak İstimlak Müdürlüğü | 2942 sayılı Kamulaştırma Kanunu doğrultusunda kamulaştırma işlemlerinin yapılması | 115 |
| Emlak İstimlak Müdürlüğü | 2942 sayılı Kamulaştırma Kanunu doğrultusunda, fiili ve hukuki el atmadan kaynaklı başlatılan davaların takibi, ödeme süreçleri ve dava süreçlerinin tamamlanması | 115 |
| Emlak İstimlak Müdürlüğü | 2886 sayılı yasa kapsamında tüm ecrimisil işlemlerinin yapılması, | 115 |
| Emlak İstimlak Müdürlüğü | 2886 sayılı yasa kapsamında kiralama işlemleri ile tahakkuk-borç takiplerinin yapılması, | 115 |
| Emlak İstimlak Müdürlüğü | Diğer kamu kurum ve kuruluşları ile Belediyemiz arasında irtifak ve intifa hakkı tesisi, tahsis, kiralama ve devir işlemlerinin yapılması | 115 |
| Fen İşleri Müdürlüğü | Belediyemizin çeşitli organizasyonları için açık/kapalı mekânlar için tasarlanan projeleri faaliyete geçirme çalışmalarının yapılması. | 118 |
| Fen İşleri Müdürlüğü | Yeni bina projelerinin uygulanması | 118 |
| Fen İşleri Müdürlüğü | Yeni sokak yapılması ve mevcut sokakların sağlamlaştırma çalışmalarının yürütülmesi (Bisiklet yolu, yaya yolu, bakım onarım, yapım vb..) | 118 |
| Fen İşleri Müdürlüğü | Yeni altyapı yapılması ve mevcut altyapı sağlamlaştırma çalışmalarının yürütülmesi (yağmursuyu kanalı bakım , onarım, yapım vb..) | 118 |
| Etüd Proje Müdürlüğü | Geri Bildirim ve Değerlendirme Mekanizmalarının Oluşturulması | 124 |
| Etüd Proje Müdürlüğü | Engelliler Eğitim Merkezi-1 | 124 |
| Plan Proje Müdürlüğü | Gerekli durumlarda, 1/5000 ölçekli nazım imar planı değişikliği ve 1/1.000 ölçekli uygulama imar planı değişikliklerinin yapılması, | 127 |
| Plan Proje Müdürlüğü | Talebe bağlı (15. ve 16. madde) imar uygulaması | 127 |
| Yapı Kontrol Müdürlüğü | Kaçak Yapılarla Mücadele | 129 |
| Yapı Kontrol Müdürlüğü | Ruhsatlı İnşaatların Denetlenmesi | 129 |
| Kentsel Dönüşüm Müdürlüğü | Enerji verimliliği ve yenilenebilir enerji kaynakları entegrasyonu | 133 |
| Kentsel Dönüşüm Müdürlüğü | Roman Mahallelerinde Kültürel Dokuyu Koruyan Kentsel Dönüşüm Projesi | 133 |
| Kentsel Dönüşüm Müdürlüğü | Vatandaş bilgilendirme toplantıları | 133 |
| Kentsel Dönüşüm Müdürlüğü | Kentsel Dönüşüm Strateji Eylem Planlarının Güncellenmesi ve İzlenmesi Projesi | 133 |
| Kentsel Dönüşüm Müdürlüğü | Sürdürülebilir Kentsel Dönüşüm İlkeleri Eğitimi Projesi | 133 |
| Afet İşleri ve Risk Yönetimi Müdürlüğü | Toplanma alanlarının modernizasyonu | 136 |
| Afet İşleri ve Risk Yönetimi Müdürlüğü | Kent sakinlerini afetler hakkında bilgilendirmek, afet öncesi, sırası ve sonrasında yapılması gerekenler konusunda bilinçlendirme | 136 |
| Afet İşleri ve Risk Yönetimi Müdürlüğü | Mahalle Afet Gönüllüsü Eğitimleri | 136 |
| Afet İşleri ve Risk Yönetimi Müdürlüğü | Afet Tatbikatları Düzenleme ve tatbikatlara katılma | 136 |
| Afet İşleri ve Risk Yönetimi Müdürlüğü | Afet yönetimiyle ilgili çalışanların bilgi ve becerilerini geliştirmek | 136 |
| Afet İşleri ve Risk Yönetimi Müdürlüğü | Mahalle Bazlı Afet Tehlike/ Risk haritalarının oluşturulması | 136 |
| Afet İşleri ve Risk Yönetimi Müdürlüğü | Kapsamlı afet risk azaltma ve yönetim platformu projesi | 136 |
| Afet İşleri ve Risk Yönetimi Müdürlüğü | İlçe genelinde haberleşme sisteminin kurulması | 136 |
| Afet İşleri ve Risk Yönetimi Müdürlüğü | Kurumlar arası iş birliği ve koordinasyonun güçlendirilmesi | 136 |
| Temizlik İşleri Müdürlüğü | Evsel atıkların düzenli olarak toplanması ve nakli | 141 |
| Temizlik İşleri Müdürlüğü | Şehir merkezinde modern ve estetik çöp konteynerlerinin yerleştirilmesi | 141 |
| Temizlik İşleri Müdürlüğü | Kirleten öder projesi | 141 |
| Temizlik İşleri Müdürlüğü | Kamuya ait alanların (cadde, sokak, meydan, okul bahçesi, durak, semt pazarı vb.) süpürülmesi, yıkanması ve temizlenmesi | 141 |
| Çevre Koruma ve Kontrol Müdürlüğü | Sürdürülebilir Enerji ve İklim Eylem Planının takibi ve ihtiyaç halinde güncellenmesi | 144 |
| Çevre Koruma ve Kontrol Müdürlüğü | Sıfır Atık uygulamaları ve atık yönetim, denetimler ve eğitim faaliyetleri | 144 |
| Çevre Koruma ve Kontrol Müdürlüğü | Gürültü ve çevre denetimlerinin yapılması | 144 |
| Çevre Koruma ve Kontrol Müdürlüğü | 8 Haziran Marmara Denizi gününde etkinlikler düzenlenmesi | 144 |
| Çevre Koruma ve Kontrol Müdürlüğü | Dış paydaşları iklim değişikliği ve etkileri konusunda bilgilendirme | 144 |
| Tarımsal Hizmetler Müdürlüğü | Kentsel tarım ağının genişletilmesi projesi | 150 |
| Tarımsal Hizmetler Müdürlüğü | Tarımsal alanların artırılması | 150 |
| Tarımsal Hizmetler Müdürlüğü | Toplum bazlı tarım projesi | 150 |
| Tarımsal Hizmetler Müdürlüğü | Değer zinciri analizi ve pazarlama desteği | 150 |
| Tarımsal Hizmetler Müdürlüğü | Yerel ürünlerin coğrafi işaret alması konusunda girişimler yapılması | 150 |
| Tarımsal Hizmetler Müdürlüğü | Kadınlara yönelik eğitim ve iş olanaklarının desteklenmesi | 150 |
| Tarımsal Hizmetler Müdürlüğü | Kadın Kooperatiflerini Destekleme Projesi | 150 |
| Tarımsal Hizmetler Müdürlüğü | Dikey ve topraksız tarım gibi yenilikçi yöntemlerin yaygınlaştırılması | 150 |
| Özel Kalem Müdürlüğü | Aylık Koordinasyon Toplantılarını koordine edilmesi | 185 |
| İklim Değişikliği ve Sıfır Atık Müdürlüğü | Sürdürülebilir Enerji ve İklim Eylem Planının takibi ve ihtiyaç halinde güncellenmesi | 154 |
| İklim Değişikliği ve Sıfır Atık Müdürlüğü | Sıfır Atık uygulamaları ve atık yönetim, denetimler ve eğitim faaliyetleri | 154 |
| İklim Değişikliği ve Sıfır Atık Müdürlüğü | Gürültü ve çevre denetimlerinin yapılması | 154 |
| İklim Değişikliği ve Sıfır Atık Müdürlüğü | 8 Haziran Marmara Denizi gününde etkinlikler düzenlenmesi | 154 |
| İklim Değişikliği ve Sıfır Atık Müdürlüğü | Dış paydaşları iklim değişikliği ve etkileri konusunda bilgilendirme | 154 |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | Ulusal ve Uluslararası Etkinlikler | 160 |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | Sanatsal Eğitimler | 160 |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | Müzecilik Hizmetleri | 160 |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | Sanatsal Etkinlikler | 160 |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | Eğitim Kursları | 160 |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | Teknoloji Eğitimleri | 160 |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | İşbirliği ve Ortaklıklar | 160 |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | Okuma Etkinlikleri | 160 |
| Gençlik ve Spor İşleri Müdürlüğü | Amatör spor kulüplerine maddi ve manevi destek sağlamak | 165 |
| Gençlik ve Spor İşleri Müdürlüğü | Spor etkinliklerine sanat etkinlikleri ekleyerek, gençlerin farklı alanlara olan ilgilerini birleştirmek | 165 |
| Gençlik ve Spor İşleri Müdürlüğü | Mevcut spor tesislerini gençlerin ihtiyaçlarına uygun hale getirmek için modernize etmek | 165 |
| Gençlik ve Spor İşleri Müdürlüğü | Spor etkinliklerine sanat etkinlikleri ekleyerek, gençlerin farklı alanlara olan ilgilerini birleştirmek | 165 |
| Gençlik ve Spor İşleri Müdürlüğü | Yenilikçi ve çeşitli spor branşları açmak | 165 |
| Gençlik ve Spor İşleri Müdürlüğü | Toplumun her kesimine yönelik spor programları yapmak | 165 |
| Gençlik ve Spor İşleri Müdürlüğü | Sporla Engelleri Aşalım Projesi | 165 |
| Sosyal Destek Müdürlüğü | Kırılgan gruplara ( kadın, çocuk, genç, yaşlı, hasta, engelli bireyler) ait bireyleri güçlendirici her türlü bilgilendirici, ayni ve nakdi destek vb. destekleyici faaliyetlerde bulunulması | 168 |
| Sosyal Destek Müdürlüğü | Dar gelirli ve ihtiyaç sahibi hemşehrilerimiz destekleyici ve/veya güçlendirici çalışmaların yapılması | 168 |
| Sosyal Destek Müdürlüğü | Kent genelinde 24 mahallede sosyal doku çalışması yapılması | 168 |
| Sosyal Destek Müdürlüğü | Kapsamlı bir veri toplama ve analiz sistemi kurulması projesi | 168 |
| Sosyal Destek Müdürlüğü | Veri seti hazırlıkları için veri toplama ve analiz faaliyetleri | 168 |
| Sosyal Destek Müdürlüğü | Düzenli olarak raporlama yapılacak bir sistemin kurulması | 168 |
| Sosyal Destek Müdürlüğü | Göçmenlere ait veri seti hazırlama | 168 |
| Sosyal Destek Müdürlüğü | Geri bildirimlerin değerlendirilmesi ve iyileştirme çalışmalarının yapılması | 168 |
| Sosyal Destek Müdürlüğü | Beslenme Projesinin Devam Etmesi | 168 |
| Dış İlişkiler Müdürlüğü | Uluslararası iş birlikleriyle ülkemizin ve belediyemizin tanıtımını ve temsilini güçlendirmek | 174 |
| Dış İlişkiler Müdürlüğü | Ulusal ve uluslararası proje, hibe ve ödül programlarına başvurmak ve yönetmek | 174 |
| Dış İlişkiler Müdürlüğü | Kardeş şehir ilişkilerini geliştirmek ve bu kapsamda etkinlikler düzenlemek | 174 |
| Halkla İlişkiler Müdürlüğü | Vatandaşlardan gelen talep, şikâyet ve önerileri ilgili birimlere iletmek ve sonuçları hakkında bilgilendirme yapmak | 180 |
| Halkla İlişkiler Müdürlüğü | Vatandaş memnuniyeti ölçmek amaçlı anketler yapmak | 180 |
| Halkla İlişkiler Müdürlüğü | İletişim ve katılım faaliyetlerinin etkinliğini düzenli olarak izlemek ve değerlendirmek | 180 |
| Halkla İlişkiler Müdürlüğü | Vatandaş memnuniyeti ölçmek amaçlı anketler yapmak | 180 |
| Halkla İlişkiler Müdürlüğü | Etkinliklerin tanıtımını yapmak ve katılımı teşvik etmek için çok kanallı iletişim stratejileri kullanmak (sosyal medya, web sitesi, basın bültenleri vb.). | 180 |
| Halkla İlişkiler Müdürlüğü | Önemli gün ve haftalarda (ulusal bayramlar, özel günler, farkındalık haftaları vb.) kültürel, sosyal ve sportif etkinlikler düzenlemek | 180 |
| Halkla İlişkiler Müdürlüğü | Belediye hizmetleri, projeleri ve etkinlikleri hakkında güncel ve doğru bilgileri hızlı bir şekilde vatandaşlara ulaştırmak | 180 |
| Halkla İlişkiler Müdürlüğü | Medya takip ve analiz çalışmaları yapmak. | 180 |
| Halkla İlişkiler Müdürlüğü | Sosyal medya performansını ölçmek ve raporlamak | 180 |
| Halkla İlişkiler Müdürlüğü | Basın bültenleri ve diğer iletişim materyallerini düzenli olarak arşivlemek ve erişilebilir kılmak | 180 |
| Halkla İlişkiler Müdürlüğü | Hedef kitleye uygun, anlaşılır ve ilgi çekici yazılı içerikler (haberler, makaleler, blog yazıları, röportajlar) hazırlamak. | 180 |
| Özel Kalem Müdürlüğü | Vatandaşlardan gelen randevuların planlanması | 185 |
| Özel Kalem Müdürlüğü | Başkanlık adına diğer kurum, kuruluş, yabancı misyon temsilcilikleri vs… ile ilişkilerin koordine edilmesi | 185 |
| Özel Kalem Müdürlüğü | Muhtarlar ve STK’lar ile yapılacak olan toplantıların koordine edilmesi | 185 |
| İnsan Kaynakları ve Eğitim Müdürlüğü | Eğitim ihtiyacı analizi yapılarak hizmet içi eğitim seminerleri düzenlemek | 188 |
| İnsan Kaynakları ve Eğitim Müdürlüğü | Eğitimci eğitimi programları düzenlemek | 188 |
| İnsan Kaynakları ve Eğitim Müdürlüğü | Moral, motivasyon, kurum aidiyet duygusu, personel kaynaşmasını artırıcı faaliyetler düzenlemek | 188 |
| İnsan Kaynakları ve Eğitim Müdürlüğü | Farklı konularda sertifika programları düzenlemek | 188 |
| Bilgi İşlem Müdürlüğü | Bilişim Teknolojileri Hizmetlerinin Yönetimi ve Bakımı | 191 |
| Bilgi İşlem Müdürlüğü | Bilişim Teknolojileri Donanım ve Çevre Birimlerinin Yönetimi | 191 |
| Bilgi İşlem Müdürlüğü | Bilişim Teknolojileri Altyapısının Modernizasyonu | 191 |
| Bilgi İşlem Müdürlüğü | Büyükçekmece ilçesinin zengin kültürel mirasını, tarihi ve turistik yerlerini, etkinliklerini ve festivallerini tanıtacak mobil uygulama yapılması, | 191 |
| Bilgi İşlem Müdürlüğü | Dijital Dönüşüm Süreçleri devam ettirilmesi (e-İmar, e-Ruhsat, e-İskân, e-Ekspertiz, e-Asansör,e-Bilirkişi vb.) | 191 |
| Bilgi İşlem Müdürlüğü | İHA ile ilçe görüntüsünün alınması ve Dijital Harita Altlıklarının Oluşturulması (2D-3D) | 191 |
| Bilgi İşlem Müdürlüğü | Büyükçekmece Açık Veri Portalı yapılması | 191 |
| Bilgi İşlem Müdürlüğü | Sosyal Hizmetlerin Dijitalleşmesi | 191 |
| Bilgi İşlem Müdürlüğü | Şehir veri Platformu | 191 |
| Bilgi İşlem Müdürlüğü | Kamu Hizmetlerinin Dijitalleşmesi | 191 |
| Rehberlik ve Teftiş Kurulu Müdürlüğü | Devlet Memurlarına yönelik ön inceleme, araştırma raporu, disiplin soruşturması işlemleri yapmak | 194 |
| Rehberlik ve Teftiş Kurulu Müdürlüğü | Belediyenin tüm birimlerinde belirli aralıklarla denetimler yapmak | 194 |
| Rehberlik ve Teftiş Kurulu Müdürlüğü | Devlet Memurlarına yönelik ön inceleme, araştırma raporu, disiplin soruşturması işlemleri yapmak | 194 |
| Rehberlik ve Teftiş Kurulu Müdürlüğü | Belirli bir konu veya şikâyet üzerine özel denetimler yapmak. | 194 |
| Hukuk İşleri Müdürlüğü | Hukuki dosyaların takibi | 196 |
| Hukuk İşleri Müdürlüğü | Müdürlüklere hukuki danışmanlık desteği verilmesi | 196 |
| Strateji Geliştirme Müdürlüğü | Stratejik planlama ve bütçeleme faaliyetleri | 199 |
| Strateji Geliştirme Müdürlüğü | Vatandaş memnuniyeti anketleri | 199 |
| Strateji Geliştirme Müdürlüğü | Performans göstergelerinin takibi ve raporlanması | 199 |
| Strateji Geliştirme Müdürlüğü | İç kontrol sisteminin güçlendirilmesi | 199 |
| Strateji Geliştirme Müdürlüğü | Vatandaş memnuniyeti anketleri | 199 |
| Destek Hizmetleri Müdürlüğü | İhtiyaç duyulan destek hizmetleri yönetiminin sağlanması | 202 |
| Destek Hizmetleri Müdürlüğü | Kurumun tanıtımı için yapılacak olan faaliyetlerde kullanılacak tüm görsel tasarımlar için malzeme temin etmek | 202 |
| Destek Hizmetleri Müdürlüğü | İhtiyaç duyulan destek hizmetleri yönetiminin sağlanması | 202 |
| Destek Hizmetleri Müdürlüğü | Hizmetlerinin aksamadan sürdürülebilmesi için, araç, iş makinesi ve akaryakıt ihtiyaçları yasal çerçeveye uygun olarak ve maliyet etkinliği gözetilerek karşılamak. | 202 |
| Destek Hizmetleri Müdürlüğü | Belediye birimlerinin gereksinim duyduğu malzeme, ekipman ve hizmet alımları, mevzuata uygun, şeffaf ve rekabetçi yöntemlerle temin etmek. | 202 |
| Mali Hizmetler Müdürlüğü | Mali denetim raporlarının değerlendirilmesi ve aksiyon planı hazırlanması | 203 |
| Mali Hizmetler Müdürlüğü | Belediyenin mali verilerinin analiz edilerek karar verme süreçlerine destek sağlanması | 203 |
| Yazı İşleri Müdürlüğü | Encümen ve Belediye Meclisi İşlemleri | 207 |
| Yazı İşleri Müdürlüğü | Gelen-Giden evrakların kayıt altına alınması ve takip edilmesi | 207 |
| Yazı İşleri Müdürlüğü | Müracaat eden çiftlerin nikâh işlemlerinin yapılması, kayıtlarının ve istatistiklerin tutulması | 207 |
| Yazı İşleri Müdürlüğü | 4109 sayılı Kanun kapsamında asker ailelerine yapılacak yardım ile ilgili işlemlerin yapılması | 207 |
| Gelirler Müdürlüğü | Sahada tespiti yapılan emlak, ÇTV, ilan reklam, pay, ceza, işgaliye harcı için tutulan yoklama fişlerinin iş yeri ve konut bazında tasnif edilmesi | 210 |
| Gelirler Müdürlüğü | Tebliğinden itibaren süresi dolan ihbarnamelerin tahakkuka bağlanması | 210 |
| Gelirler Müdürlüğü | Vadesinde ödenmeyen alacaklar hakkında 6183 sayılı kanun kapsamında ödeme emri düzenlenmesi ve tebliğ edilerek takip sürecinin başlatılması, Ödeme emri tebliğ edilmesine rağmen ödenmeyen alacaklar hakkında haciz varakası düzenleyerek haciz işlemleri yapılması | 210 |
| Gelirler Müdürlüğü | Çeşitli ödeme kanalları üzerinde tahsilat yapılması | 210 |
| Gelirler Müdürlüğü | Kadın kooperatifleri, kadın üreticiler ve yerel üreticilerin ürettiği sağlıklı, ekonomik ve güvenilir ürünlerin satışa sunulduğu *Büyükçekmece’den Tarım Marketi işletmek | 210 |
| Gelirler Müdürlüğü | Yuvamız Büyükçekmece projesi kapsamında, Çocuk eğitim Merkezi ile Çocuk Eğitim ve Oyun Merkezlerinde çocuklara eğitim ve bakım hizmeti sunmak | 210 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | Çevre Dostu Araç Entegrasyonu | 214 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | Birimlerden Gelen Araç Taleplerinin Karşılanması | 214 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | Resmi Araç ve İş Makinelerinin Bakım ve Onarımlarının Yapılması | 214 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | Dış Paydaşlardan Gelen Araç Taleplerinin Karşılanması | 214 |

## Düşürülen Bakanlık yönergeleri

- 105 satır: *Alt program hedefine ilişkin kısa ve öz bilgilere yer verilecektir.
- 105 satır: *Alt program kapsamında ilgili mevzuata göre idareye verilen hangi görevlerin yürütüldüğü ve Kalkınma Planı, Stratejik Plan gibi üst politika belgelerinde yer alan hedeflerden hangilerine ulaşılmasına katkı sağlandığına ilişkin açıklamalara yer verilecektir.

## Sınırlar ve varsayımlar

- PDF ayrıca açılmadı; kitap-PDF eşitliği görev paketindeki D-371 teyididir.
- InDesign dizgi motoru kullanılmadı; sayfalar hikâyenin ilk basılı sayfasıdır.
- Açıklama tablolarının program, alt program, ad, açıklama dörtlüsü katalog kimliğidir. Açıklama mevcut katalog denetim kaydında korunur; `name:` SHA256 teknik anahtarı resmî faaliyet kodu değildir.
- 2026 yazımı müdürlük başına savepoint ile yapılır; 2027 değişiklik reddinin tüm çalışmayı geri alabilmesi için tek dış işlem sonunda commit edilir.
- Kalıcı gösterge kimliği atanmadı. Aday raporu yalnız Strateji incelemesi içindir.
- `--resume` aynı kitap SHA256 ve yıl makbuzu bulunan tamamlanmış müdürlükleri atlar; mevcut düzeltmeleri korur.

Paket doğrulama hata sayısı (kaynaktaki eksikler/dağılımlar dahil): 2338.

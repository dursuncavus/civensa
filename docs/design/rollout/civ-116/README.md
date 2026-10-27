# CIV-116 · Rapor hazırlığı prototipi

037 müdürlük rapor hazırlığı ve 036 strateji görünümü için statik tasarım önerisi. Uzun sayfanın başında altı işin bağlantısı ve metinli durumu; 1280 px ve üzerinde sağda yapışkan “Bu sayfada” listesi bulunur. Kart ve finansman formları kapalı başlar; hatalar açık uyarı özetinden ilgili bölüme bağlanır. GOV.UK task list / contents list yapıları, CIV-108 ve D-224 esas alınmıştır. Sekme kullanılmaz.

Başlangıç: `feature/authorization-workflow-phase5`, `b41edac`; PR öncesinde `272ea0e` üzerine güncellendi (hedef dalın gerisinde 0 commit). Uygulama, şablon, test, rota, veri ve şema değişikliği yoktur. Tüm içerik sentetiktir. İşlemler ortak prototip penceresinde temsil edilir; API, depolama, kayıt veya yeni çalışma zamanı bağımlılığı yoktur.

## Beş durum ve ekran görüntüleri

Chromium 151.0.7922.173; 1440×900 ve 390×900, DPR 1, tr-TR, Europe/Istanbul, açık tema, azaltılmış hareket ve yerel Fira Sans. Tam sayfa PNG’ler, mevcut `capture_screenshots.py` içindeki `snap()` ile üretildi. Her dosya ≤ 1.500.000 bayt.

| Durum | Örnek | 1440 px | 390 px |
| --- | --- | --- | --- |
| a | Yeni dönem; tüm işler başlanmadı, kayıt yok. | [1440 PNG · 333,776 bayt](../../prototype/screenshots/037-report-preparation-a-1440.png) | [390 PNG · 282,087 bayt](../../prototype/screenshots/037-report-preparation-a-390.png) |
| b | Devam ediyor; iki faaliyet kartsız, üç kaynak kaydı ve bir ekonomik hücre doğrulanacak. | [1440 PNG · 622,276 bayt](../../prototype/screenshots/037-report-preparation-b-1440.png) | [390 PNG · 512,492 bayt](../../prototype/screenshots/037-report-preparation-b-390.png) |
| c | Tüm işler tamamlandı; düzenleme açık. | [1440 PNG · 497,783 bayt](../../prototype/screenshots/037-report-preparation-c-1440.png) | [390 PNG · 414,764 bayt](../../prototype/screenshots/037-report-preparation-c-390.png) |
| d | Onaylandı; alanlar metin görünümünde, kayıt düğmeleri yok. | [1440 PNG · 456,875 bayt](../../prototype/screenshots/037-report-preparation-d-1440.png) | [390 PNG · 377,034 bayt](../../prototype/screenshots/037-report-preparation-d-390.png) |
| e | Strateji görünümü; program grubu dağılımı uyarısı açık. | [1440 PNG · 629,479 bayt](../../prototype/screenshots/037-report-preparation-e-1440.png) | [390 PNG · 518,921 bayt](../../prototype/screenshots/037-report-preparation-e-390.png) |

## Kapsam ve varsayımlar

- Özetin altındaki maliyet mutabakatı, program → alt program → müdürlük satırlarını ve hesaplanan / kaynak / fark / yapılacak işlem sütunlarını korur. Eksik ara toplam yerine kısmi sayı gösterilmez. Yeni dönemde “Henüz kontrol edilecek kayıt yok.” yazılır.
- Bölüm 1: iki kart, sıra, program / alt program ve mevcut 12 kart alanı; ikincil “Yeni kart” açılır formu. Bölüm 2: dört gösterge, üç faaliyet, kart / kaynak kodu / sıra ataması ve yeni gösterge formu. Bölüm 3: üç faaliyetin çoklu resmî faaliyet seçimi.
- Bölüm 4: bir gösterge değeri ile faaliyet ve Personel ve SGK kaynak tutarları. Bölüm 5: üç faaliyet; 2025/2026 bütçe, 2026 haziran sonu harcama / yıl sonu harcama tahmini, 2027/2028 tahmin ve her sütunda bütçe içi / dışı. Boş ile sıfır ayrımı açıklaması korunur.
- Bölüm 6: doğrulanmamış ekonomik hücre, program grubu dağılımı uyarısı, grup / kaynak araç çubuğu, düzenlenebilir ekonomik ızgara, kayıt tablosu ve ekonomik tutar ekle / güncelle formu. Tutarlar sağa hizalı, Türkçe gösterimdedir. Mobil kaydırma ipucu ve klavyeyle odaklanabilen tablo bölgeleri vardır.
- Durumlar uygulama bağlamındaki `cards`, kartsız gösterge/faaliyet, `official_ids`, doğrulanmamış değer/tutar/hücre ve `errors`/`warnings` türündeki verileri temsil eden sabit örneklerdir. Yeni bir sunucu tamamlanma alanı varsayılmaz. “3 eksik / tutarsız kayıt”: iki kartsız faaliyet ve doğrulanmamış Personel ve SGK kaydıdır; uyarı özeti bu iki faaliyeti birlikte açıklar.
- d durumunda onay örneklenir; gönderilmiş veya dönemi kapalı rapor için aynı salt okunur görünüm önerilir. CIV-114 yönüne uygun olarak kenarlık/gölge kaldırılır, `--surface-muted` zemin ve normal metin kullanılır; klavye odağı korunur. Filtre düğmesi kalır; tüm kayıt düğmeleri ve yeni kayıt formları gizlenir.
- “Tamamlandı” ve kalan iş sayıları sentetik durumu anlatır; prototipte değiştirilen bir alan gerçek kontrol hesabını güncellemez. Filtreleme, sunucu doğrulaması, taslak kaldırma ve reddedilen POST’un geri yüklenmesi bu statik örnekte çalıştırılmaz.

## Kontrast

Yeni renk eklenmedi. `check_contrast.py` içindeki `collect_states`, token eşlemesi ve `ratio` kullanılarak beş durum × dört genişlikte normal/açık ayrıntı, gerçek hover, odak ve tüm diyaloglar ölçüldü. Tarayıcının seçili çoklu seçenek ve pasif seçenek renkleri de tokenlarla tanımlandı. Metin çiftlerinin tamamı ≥ 4,5:1; kontrol sınırı/odak/simgeler ≥ 3:1.

| Ön plan | Arka plan | Kullanım | Oran | Sonuç |
| --- | --- | --- | ---: | --- |
| `--accent` | `--accent-soft` | Normal metin | 5.37:1 | Geçti |
| `--accent` | `--bg` | Kontrol sınırı | 5.76:1 | Geçti |
| `--accent` | `--bg` | Normal metin | 5.76:1 | Geçti |
| `--accent` | `--bg` | Odak çizgisi | 5.76:1 | Geçti |
| `--accent` | `--surface` | Normal metin | 6.28:1 | Geçti |
| `--accent` | `--surface` | Odak çizgisi | 6.28:1 | Geçti |
| `--accent` | `--surface` | Simge | 6.28:1 | Geçti |
| `--accent-hover` | `--bg` | Kontrol sınırı | 7.87:1 | Geçti |
| `--accent-hover` | `--bg` | Normal metin | 7.87:1 | Geçti |
| `--accent-hover` | `--surface` | Büyük metin | 8.58:1 | Geçti |
| `--success` | `--success-bg` | Normal metin | 4.71:1 | Geçti |
| `--surface` | `--accent` | Normal metin | 6.28:1 | Geçti |
| `--surface` | `--accent-hover` | Normal metin | 8.58:1 | Geçti |
| `--text` | `--bg` | Büyük metin | 14.49:1 | Geçti |
| `--text` | `--bg` | Normal metin | 14.49:1 | Geçti |
| `--text` | `--surface` | Büyük metin | 15.80:1 | Geçti |
| `--text` | `--surface` | Normal metin | 15.80:1 | Geçti |
| `--text` | `--surface` | Simge | 15.80:1 | Geçti |
| `--text` | `--surface-muted` | Normal metin | 13.50:1 | Geçti |
| `--text-secondary` | `--bg` | Kontrol sınırı | 6.30:1 | Geçti |
| `--text-secondary` | `--bg` | Normal metin | 6.30:1 | Geçti |
| `--text-secondary` | `--surface` | Kontrol sınırı | 6.87:1 | Geçti |
| `--text-secondary` | `--surface` | Normal metin | 6.87:1 | Geçti |
| `--text-secondary` | `--surface-muted` | Normal metin | 5.87:1 | Geçti |
| `--warning` | `--warning-bg` | Normal metin | 5.41:1 | Geçti |
| `--warning` | `--warning-bg` | Simge | 5.41:1 | Geçti |

## Doğrulama

- Beş durum × 1440/390/1279/1280: tek h1, altı bölüm bağlantısı, tüm alanların etiketi, kontrol/simge kuralları, sayfa ve gövde genişliği, renk çiftleri, duruma bağlı görünürlük geçti. Açık uzun formlarda da sayfa taşmıyor. 390 px’te tablolar içeride yatay kayıyor.
- 1279/1280 sınırında yan gezinmenin gizlenmesi/görünmesi, bölüm bağlantıları, Enter ile ayrıntı açma, kayıt simülasyonu, Escape ile kapanış ve odağın düğmeye dönüşü geçti. d durumunda görünür alanlar salt okunur/pasif, kenarlıksız ve metin renginde; görünür tek form düğmesi “Tabloyu aç”.
- Ağ koruması: yalnız loopback GET; dış istek, POST veya JavaScript hatası yok. Veritabanı ve uygulama başlatılmadı.
- `python docs/design/prototype/capture_screenshots.py`: mevcut dört sayfa × iki genişlik, 104/104 eşleme, pencereler, sekmeler, odak ve ağ kontrolleri geçti; mevcut takip edilen PNG’lerde değişiklik yok.
- `python docs/design/prototype/check_contrast.py`: mevcut ekranlarda 44 kullanım çifti, 0 başarısız. `node --check docs/design/prototype/prototype.js` ve `git diff --check` geçti.
- PostgreSQL / pytest çalıştırılmadı: yalnız belge/statik prototip değişikliği. Gerçek yetkilendirme, kayıt, filtre sonuçları ve sunucu doğrulaması bu çalışmanın doğrulama kapsamı dışında.

## Değişen dosyalar

- `docs/design/prototype/screens/037-report-preparation.html`
- `docs/design/prototype/prototype.css` ve `prototype.js`: yalnız `.report-preparation-prototype` / `#report-state` kapsamında küçük ekler.
- `docs/design/prototype/screenshots/037-report-preparation-{a,b,c,d,e}-{1440,390}.png`: on yeni PNG.
- `docs/design/rollout/civ-116/README.md`: bu kanıt, envanter ve tekrar çalıştırma tarifi.

## Sahibe açık sorular

1. Altı işin bağlantısı ve metinli durumları, dönem başında nereden başlanacağını yeterince açıklıyor mu?
2. Maliyet mutabakatının iş özetinden hemen sonra kalması uygun mu?
3. Kart ve finansman formlarının kapalı başlaması ile masaüstündeki sağ bölüm listesi onaylanıyor mu?
4. Strateji kullanıcısının “Program grubu dağılımı” uyarısı ekonomik bölümde mi kalmalı, yoksa özet panelinde de bir bağlantı istenir mi?

## Görünür metinler: eski → yeni

Başlıklar ve düğmeler cümle düzenindedir; SGK ve özel adlar korunur. Aşağıdaki tabloda ortak kabuk/diyalogdan aynen alınan metinler de eski = yeni olarak listelenir. Numaralı altı başlıkta sıra numarası yeni gezinme düzenine aittir. Kaynakta değişken olan müdürlük adı sentetik örnekle gösterilir. Tekrarlanan metinler bir kez listelenir.

| Eski | Yeni |
| --- | --- |
| Performans Kartları | 1. Performans kartları |
| Gösterge ve Faaliyetlerin Kartlara Atanması | 2. Gösterge ve faaliyetlerin kartlara atanması |
| 2025 Bütçe · Bütçe Dışı | 2025 bütçe · Bütçe dışı |
| 2025 Bütçe · Bütçe İçi | 2025 bütçe · Bütçe içi |
| 2026 Bütçe · Bütçe Dışı | 2026 bütçe · Bütçe dışı |
| 2026 Bütçe · Bütçe İçi | 2026 bütçe · Bütçe içi |
| 2026 Haziran Sonu Harcama · Bütçe Dışı | 2026 haziran sonu harcama · Bütçe dışı |
| 2026 Haziran Sonu Harcama · Bütçe İçi | 2026 haziran sonu harcama · Bütçe içi |
| 2026 Yıl Sonu Harcama Tahmini · Bütçe Dışı | 2026 yıl sonu harcama tahmini · Bütçe dışı |
| 2026 Yıl Sonu Harcama Tahmini · Bütçe İçi | 2026 yıl sonu harcama tahmini · Bütçe içi |
| 2027 Tahmin · Bütçe Dışı | 2027 tahmin · Bütçe dışı |
| 2027 Tahmin · Bütçe İçi | 2027 tahmin · Bütçe içi |
| 2028 Tahmin · Bütçe Dışı | 2028 tahmin · Bütçe dışı |
| 2028 Tahmin · Bütçe İçi | 2028 tahmin · Bütçe içi |
| Sorumlu Harcama Birimleri Kataloğu Bağlantısı | 3. Sorumlu harcama birimleri kataloğu bağlantısı |
| Kaynak Değerlerini Doğrulama | 4. Kaynak değerlerini doğrulama |
| Faaliyet Finansmanı | 5. Faaliyet finansmanı |
| Ekonomik Tablo | 6. Ekonomik tablo |
| Alt Programın Hedefi | Alt programın hedefi |
| Atamayı Kaydet | Atamayı kaydet |
| Bağlantıyı Kaydet | Bağlantıyı kaydet |
| Bütçe Dışı | Bütçe dışı |
| Bütçe İçi | Bütçe içi |
| Durum / Yapılacak İşlem | Durum / yapılacak işlem |
| Ekonomik Ad | Ekonomik ad |
| Ekonomik Tablo | Ekonomik tablo |
| Ekonomik Tutar Ekle / Güncelle | Ekonomik tutar ekle / güncelle |
| Faaliyet Finansmanı | Faaliyet finansmanı |
| Finansmanı Kaydet | Finansmanı kaydet |
| Gerekçe ve Açıklamalar | Gerekçe ve açıklamalar |
| Gösterge Ekle | Gösterge ekle |
| Gösterge ve Faaliyet Girişi | Gösterge ve faaliyet girişi |
| Gösterge ve Faaliyetlerin Kartlara Atanması | Gösterge ve faaliyetlerin kartlara atanması |
| Göstergeye İlişkin Ortak Açıklama | Göstergeye ilişkin ortak açıklama |
| Haziran Sonu Harcama | Haziran sonu harcama |
| Hizmet Alanı | Hizmet alanı |
| Kartı Kaydet | Kartı kaydet |
| Kaynak Değerlerini Doğrulama | Kaynak değerlerini doğrulama |
| Kaynak Sayfa | Kaynak sayfa |
| kaynak toplamı yok | Kaynak toplamı yok |
| Kaynağa Göre Doğrula | Kaynağa göre doğrula |
| Maliyet Ara Toplamları ve Kaynak Mutabakatı | Maliyet ara toplamları ve kaynak mutabakatı |
| Ortak Hesaplama Yöntemi | Ortak hesaplama yöntemi |
| Performans Kartları | Performans kartları |
| Program / Alt Program | Program / alt program |
| Program / Alt Program / Müdürlük | Program / alt program / müdürlük |
| Program Grubu | Program grubu |
| Program Grubu Dağılımı | Program grubu dağılımı |
| Rapor Hazırlığı | Rapor hazırlığı |
| Sorumlu Harcama Birimleri Kataloğu Bağlantısı | Sorumlu harcama birimleri kataloğu bağlantısı |
| Sorumlu İdare | Sorumlu idare |
| Stratejik Plan / PH Bağlantısı | Stratejik plan / PH bağlantısı |
| Tabloyu Aç | Tabloyu aç |
| Tabloyu Kaydet | Tabloyu kaydet |
| Tutarı Doğrula | Tutarı doğrula |
| Tutarı Kaydet | Tutarı kaydet |
| Verinin Kaynağı | Verinin kaynağı |
| Yeni Gösterge | Yeni gösterge |
| Yeni Kart | Yeni kart |
| Yıl / Değer Türü | Yıl / değer türü |
| Yıl / Tür | Yıl / tür |
| Yıl Sonu Gerçekleşme Tahmini | Yıl sonu gerçekleşme tahmini |
| {Müdürlük} — Rapor Hazırlığı | Örnek Hizmet Müdürlüğü — Rapor hazırlığı |
| İdare / Birim Adı | İdare / birim adı |
| / | / |
| Aynı alt programda birden fazla kart olabilir. Kaydın ait olduğu kartı seçin. | Aynı alt programda birden fazla kart olabilir. Kaydın ait olduğu kartı seçin. |
| Aynı yıl, tür, gider, program grubu ve kaynak seçildiğinde mevcut hücre güncellenir. Tutarı boş bırakmak o hücreyi kaldırır. | Aynı yıl, tür, gider, program grubu ve kaynak seçildiğinde mevcut hücre güncellenir. Tutarı boş bırakmak o hücreyi kaldırır. |
| Bağlantı hedefi | Bağlantı hedefi |
| Başlanmadı | Başlanmadı |
| Bildirimler | Bildirimler |
| Birim Müdürü (sentetik) | Birim Müdürü (sentetik) |
| Bu ekran prototip kapsamı dışındadır. | Bu ekran prototip kapsamı dışındadır. |
| Bu işlem görsel inceleme için temsil edilir. Veri kaydedilmez, gönderilmez veya silinmez. | Bu işlem görsel inceleme için temsil edilir. Veri kaydedilmez, gönderilmez veya silinmez. |
| Bütçe | Bütçe |
| Bütçe yılı / kart başlığı | Bütçe yılı / kart başlığı |
| Civensa | Civensa |
| Değer türü | Değer türü |
| Dipnot | Dipnot |
| Doğrulanmış değer | Doğrulanmış değer |
| Ekran haritasında belirtilen bağlantı | Ekran haritasında belirtilen bağlantı |
| Eksik ara toplam | Eksik ara toplam |
| Faaliyet raporu | Faaliyet raporu |
| Faaliyet raporu · EK-1 | Faaliyet raporu · EK-1 |
| Fark (TL) | Fark (TL) |
| Genel bakış | Genel bakış |
| Gerçekleşme | Gerçekleşme |
| Gider yoksa açıkça 0 girin. Boş hücre belirlenmemiştir. | Gider yoksa açıkça 0 girin. Boş hücre belirlenmemiştir. |
| Gönderim yetkileri | Gönderim yetkileri |
| Gösterge adı | Gösterge adı |
| Güncel faaliyet maliyetleri program → alt program → müdürlük sırasıyla toplanır. Bağlantısı veya tutarı eksik kayıt varsa kısmi toplam gösterilmez ve yayın durur. Kaynak toplamı, bütün alt kayıtların saklanan kaynak tutarlarından oluşur; bulunmaması uyarıdır. Personel ve SGK giderleri kitabın ortak maliyet tablosunda ayrıca gösterilir. | Güncel faaliyet maliyetleri program → alt program → müdürlük sırasıyla toplanır. Bağlantısı veya tutarı eksik kayıt varsa kısmi toplam gösterilmez ve yayın durur. Kaynak toplamı, bütün alt kayıtların saklanan kaynak tutarlarından oluşur; bulunmaması uyarıdır. Personel ve SGK giderleri kitabın ortak maliyet tablosunda ayrıca gösterilir. |
| Hedef | Hedef |
| Her dönemde bütçe içi ve bütçe dışını ayrı girin. Kaynak yoksa 0 yazın; henüz belirlenmediyse ikisini de boş bırakın. Toplam otomatik hesaplanır. | Her dönemde bütçe içi ve bütçe dışını ayrı girin. Kaynak yoksa 0 yazın; henüz belirlenmediyse ikisini de boş bırakın. Toplam otomatik hesaplanır. |
| Hesaplanan (TL) | Hesaplanan (TL) |
| Kapat | Kapat |
| Kart | Kart |
| Kart seçin | Kart seçin |
| Kart ve mali tablo kontrolleri tamamlandı. | Kart ve mali tablo kontrolleri tamamlandı. |
| Kaynak | Kaynak |
| Kaynak (TL) | Kaynak (TL) |
| Kaynak kodu | Kaynak kodu |
| Kaynakla doğrulanmış tutar (TL) | Kaynakla doğrulanmış tutar (TL) |
| Kitaptaki sıra | Kitaptaki sıra |
| Kurumsal raporlama | Kurumsal raporlama |
| Menüye git | Menüye git |
| Mevcut parola | Mevcut parola |
| Mevcut uygulamadaki hedef: | Mevcut uygulamadaki hedef: |
| Modüller | Modüller |
| Müdürlük | Müdürlük |
| Parolamı değiştir | Parolamı değiştir |
| Parolayı değiştir | Parolayı değiştir |
| Performans programı | Performans programı |
| Planlanan | Planlanan |
| Program grubu belirlenmemiş kaynak hücreler var. | Program grubu belirlenmemiş kaynak hücreler var. |
| Prototip durumu | Prototip durumu |
| Resmî faaliyetler | Resmî faaliyetler |
| Sentetik bildirim paneli örneği. | Sentetik bildirim paneli örneği. |
| Sentetik çalışma alanı | Sentetik çalışma alanı |
| Statik form örneği; gerçek parola girmeyin. | Statik form örneği; gerçek parola girmeyin. |
| Statik prototip | Statik prototip |
| Sıra | Sıra |
| Tahmin | Tahmin |
| Tasarım sistemi | Tasarım sistemi |
| Tutar (TL) | Tutar (TL) |
| Tür | Tür |
| Vazgeç | Vazgeç |
| Veri girişi | Veri girişi |
| Yeni bildirim yok. | Yeni bildirim yok. |
| Yeni parola | Yeni parola |
| Yeni parola (tekrar) | Yeni parola (tekrar) |
| Yönetim | Yönetim |
| Yıl | Yıl |
| Çıkış | Çıkış |
| Ölçü birimi | Ölçü birimi |
| Örnek Hizmet Müdürlüğü | Örnek Hizmet Müdürlüğü |
| İncelenecek birim uyarıları | İncelenecek birim uyarıları |
| İç kontrol | İç kontrol |
| İç kontrol eylemlerimiz | İç kontrol eylemlerimiz |
| İçeriğe geç | İçeriğe geç |

## Yeni metinler ve sentetik içerik

Durum seçicinin beş seçeneği, yeni yardım/uyarı metinleri, örnek kayıt adları, kaynak kodları, yıllar ve tutarlar aşağıdadır. Açılır formlar, seçenekler ve diyaloglar dahil bütün durumların metin envanteridir; rakamlar/boş değer işareti de listelenmiştir.

| Yeni metin / örnek içerik |
| --- |
| 0 kart · 0 gösterge · 0 faaliyet |
| 0,00 |
| 01 · Park ve yeşil alan hizmetleri |
| 02 · Temizlik hizmetleri |
| 03 · Çevre eğitimi |
| 1 |
| 1 hücre doğrulanacak |
| 1 tutar doğrulanacak |
| 1.000.000,00 |
| 1.250.000,00 |
| 2 |
| 2 faaliyet kartsız |
| 2 kart |
| 2 kart · 4 gösterge · 3 faaliyet |
| 2.500.000,00 |
| 2025 |
| 2025 Bütçe |
| 2026 |
| 2026 / Bütçe |
| 2026 Bütçe |
| 2026 Haziran sonu harcama |
| 2026 bütçe |
| 2026 · Performans kartları, kaynak kontrolü ve ekonomik tablolar |
| 2026 · Temiz çevre hizmetleri |
| 2026 · Yeşil alan hizmetleri |
| 2027 |
| 2027 Tahmin |
| 2028 |
| 2028 Tahmin |
| 24 |
| 250.000,00 |
| 3 |
| 3 eksik / tutarsız kayıt |
| 3 kayıt doğrulanacak |
| 4 |
| 4.000.000,00 |
| 42 |
| 5 |
| 6 |
| 7 |
| Amaç 2 / PH 2.1 |
| Atanacak gösterge veya faaliyet yok. |
| Atık toplama |
| Bakımı yapılan park sayısı |
| Bakımı yapılan park sayısı · 2026 |
| Bağlanacak faaliyet yok. |
| Bu sayfada |
| Bu sayfadaki işler |
| CIV-116 · Görsel inceleme |
| Dağıtılmamış |
| Değerler sentetiktir. |
| Doğrulanacak kaynak değeri yok. |
| Ekonomik tablo · Kaynak toplamı yok. Kaynak belgesindeki toplamı kontrol edin. |
| Ekonomik tutarlar (TL) |
| Eksik bağlantı / tutar · Atamaları ve kaynakları kontrol edin. |
| Erişilebilir ve sürdürülebilir çevre |
| F05 |
| F06 |
| F07 |
| Finansman girilecek faaliyet yok. |
| G01 |
| G02 |
| G03 |
| G04 |
| Genel yönetim |
| Geri dönüşüm eğitimi |
| Geri kazanım oranı |
| Ham kaynak: 1.250.000,00 TL |
| Henüz kayıt yok |
| Henüz kontrol edilecek kayıt yok. |
| Henüz performans kartı yok. Yeni kart ekleyerek başlayın. |
| Hizmet kalitesinin artırılması |
| Kaydedilen ekonomik tutarlar |
| Kaynak değerleri doğrulandı. |
| Kaynak doğrulaması bekliyor |
| Kaynak gösterimi: 24 · Önceki tür: Değer |
| Kaynak tablo 7: 2.500.000,00 · Program grubu belirlenmedi. |
| Mal ve hizmet alım giderleri |
| Mal ve hizmet alım giderleri · 2025 bütçe (TL) |
| Mal ve hizmet alım giderleri · 2026 bütçe (TL) |
| Mal ve hizmet alım giderleri · 2026 bütçe · Bütçe içi |
| Mal ve hizmet alım giderleri · 2026 haziran sonu harcama (TL) |
| Mal ve hizmet alım giderleri · 2027 tahmin (TL) |
| Mal ve hizmet alım giderleri · 2028 tahmin (TL) |
| Mutabık |
| Müdürlük kayıtları |
| Onaylandı · Bu rapor salt okunur. Gönderilen veya dönemi kapalı raporlar da aynı görünümü kullanır. |
| Park bakımı |
| Park bakımı ve atık toplama faaliyetleri kartsız. İlgili kartları seçin. |
| Park bakımı · 2026 bütçe içi |
| Personel giderleri |
| Personel giderleri · 2025 bütçe (TL) |
| Personel giderleri · 2026 bütçe (TL) |
| Personel giderleri · 2026 haziran sonu harcama (TL) |
| Personel giderleri · 2027 tahmin (TL) |
| Personel giderleri · 2028 tahmin (TL) |
| Personel ve SGK giderleri · 2026 |
| Personel ve SGK giderleri · 2026 tutarı kaynakla doğrulanmadı. Kaynak belgesini kontrol edin. |
| SGK giderleri |
| SGK giderleri · 2025 bütçe (TL) |
| SGK giderleri · 2026 bütçe (TL) |
| SGK giderleri · 2026 haziran sonu harcama (TL) |
| SGK giderleri · 2027 tahmin (TL) |
| SGK giderleri · 2028 tahmin (TL) |
| Statik prototip · 037 |
| Strateji |
| Strateji uzmanı (sentetik) |
| Tablonun devamını görmek için yatay kaydırın. |
| Tamamlandı |
| Temiz çevre hizmetleri |
| Toplam · 2026 bütçe: 1.000.000,00 TL |
| Toplam · 2026 bütçe: 1.250.000,00 TL |
| Toplam · 2026 bütçe: 250.000,00 TL |
| Toplanan atık miktarı |
| Yeni yeşil alan miktarı |
| Yeşil alan hizmetleri |
| Yıl içinde tamamlanan işlerin toplamı |
| Yıllık faaliyet kayıtları esas alınır. |
| a · Yeni dönem, başlanmadı |
| b · Devam ediyor, sorunlar var |
| c · Tamamlandı, düzenlenebilir |
| d · Onaylandı, salt okunur |
| e · Strateji görünümü |
| Çevre / Çevre hizmetleri |
| Çevre hizmetleri |
| Çevre hizmetleri · Bütçe içi |
| Çevre programı |
| Önce eksik kayıtları tamamlayın, ardından kaynak değerlerini doğrulayın. |
| Örnek Belediyesi |
| Örnek Belediyesi / Örnek Hizmet Müdürlüğü |
| İsteğe bağlı |
| — |

## Tekrar üretme

Depo kökünde, mevcut Playwright/Pillow ve Chromium ile çalıştırın. Aşağıdaki kod mevcut yakalama betiğindeki `snap()` fonksiyonunu değiştirmeden alır; mevcut `assert_layout`, tarayıcı bağlamı ve kontrast kolektörünü kullanır. Yalnız yeni on PNG’yi üretir; ölçüm çıktısı `/tmp/civ116-results.json` dosyasına yazılır.

```bash
python - <<'PY_CAPTURE'
import sys, inspect, json, re
from pathlib import Path
sys.path.insert(0,'docs/design/prototype')
import capture_screenshots as capture
import check_contrast as contrast
from browser_helpers import *
from playwright.sync_api import sync_playwright, expect
# Mevcut capture_screenshots.py run() içindeki snap() aynen kullanılır.
source=inspect.getsource(capture.run)
snap_source=source[source.index('            def snap('):source.index('            for path in PAGES:')]
snap_source='\n'.join(line[12:] for line in snap_source.splitlines())
output=ROOT/'screenshots'
manifest={'screenshots':[]}
tokens={tuple(bytes.fromhex(v)):'--'+k for k,v in re.findall(r'--([\w-]+):\s*#([\da-fA-F]{6})',(ROOT/'tokens.css').read_text())}
pairs={}; texts=set(); results=[]
with static_server() as base,sync_playwright() as pw:
    browser=launch(pw); version=browser.version
    for width in (1440,390,1279,1280):
        ctx=context(browser,width);page=ctx.new_page();blocked=[];errors=[]
        ctx.route('**/*',lambda route: route.continue_() if route.request.url.startswith(base+'/') and route.request.method=='GET' else (blocked.append(route.request.url),route.abort()))
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(base+'/screens/037-report-preparation.html'); page.evaluate('document.fonts.ready')
        # snap()'ın çalıştığı bağlam.
        namespace=dict(capture.__dict__,page=page,width=width,output=output,manifest=manifest,blocked=blocked,errors=errors)
        exec(snap_source,namespace)
        for state in 'abcde':
            page.select_option('#report-state',state)
            capture.assert_layout(page,width)
            assert page.locator('.rp-tasks li').count()==6
            assert page.locator('.rp-contents').is_visible()==(width>=1280)
            assert page.locator('#rp-strategy').is_visible()==(state=='e')
            assert page.locator('#rp-issues').is_visible()==(state in 'be')
            if state=='d': assert page.locator('.rp-save').filter(visible=True).count()==0
            assert page.evaluate("() => [...document.querySelectorAll('h1,h2,h3,button')].every(e=>getComputedStyle(e).textTransform!=='uppercase')")
            if state!='a': assert all(el.input_value() for el in page.locator('#section-3 select').all())
            if state=='a':
                assert page.locator('.rp-existing').filter(visible=True).count()==0
                assert page.locator('.rp-tasks').inner_text().count('Başlanmadı')==6
            if state in 'cd': assert page.locator('.rp-tasks').inner_text().count('Tamamlandı')==6
            if state in 'be':
                selectors=page.locator('#section-2 form select').all()[:7]
                assert sum(el.input_value()=='Kart seçin' for el in selectors)==2
            if width in (1440,390): namespace['snap']('037-report-preparation-'+state)
            # Açık formlar da taşmamalı; bütün renkler/hover/odak/diyaloglar ölçülür.
            for row in contrast.collect_states(page):
                fg,bg=tuple(row['color']),tuple(row['bg'])
                assert fg in tokens and bg in tokens,row
                value=contrast.ratio(fg,bg)
                assert value>=row['minimum'],(state,width,row,value)
                if 'metin' in row['kind'].lower(): assert value>=4.5,(row,value)
                pairs[(tokens[fg],tokens[bg],row['kind'])]=round(value,4)
            capture.assert_layout(page,width)
            if state=='d':
                for control in page.locator('.rp-content input,.rp-content textarea,.rp-content select').filter(visible=True).all():
                    assert control.evaluate("e=>{const s=getComputedStyle(e);return s.borderTopWidth==='0px' && s.backgroundColor==='rgb(239, 237, 232)' && s.color==='rgb(31, 35, 40)'}")
                    assert control.is_disabled() or control.get_attribute('readonly') is not None
                assert page.locator('.rp-content button').filter(visible=True).all_text_contents()==['Tabloyu aç']
            # Görünür metin ve alan değerleri: tüm açık ayrıntılar ve beş durum.
            texts.update(page.evaluate('''() => { const out=[]; const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT); while(w.nextNode()){const e=w.currentNode.parentElement;if(!e.closest('script,style') && w.currentNode.textContent.trim())out.push(w.currentNode.textContent.trim());} document.querySelectorAll('input,textarea').forEach(e=>{if(e.value?.trim())out.push(e.value.trim())});return out;}'''))
            if width==390:
                grid=page.locator('#section-6 .rp-table').first
                assert grid.evaluate('e=>e.scrollWidth>e.clientWidth')
                grid.evaluate('e=>e.scrollLeft=1000')
                assert grid.evaluate('e=>e.scrollLeft>0')
                assert page.locator('.rp-scroll-hint').is_visible()
            # Bölüm bağlantıları bölümü gizlemeden kaydırır.
            page.locator('.rp-tasks a').last.click()
            assert page.locator('#section-6').is_visible()
            page.evaluate("location.hash='';window.scrollTo(0,0)")
            results.append([state,width,'passed'])
        # Klavye: ayrıntı, durum seçici, simülasyon ve odağın dönüşü.
        page.select_option('#report-state','b')
        summary=page.locator('#section-1 details summary').first
        summary.focus();page.keyboard.press('Enter'); assert summary.evaluate('e=>e.parentElement.open')
        page.locator('#section-1 .rp-save').first.click();expect(page.locator('#simulation-dialog')).to_be_visible()
        page.keyboard.press('Escape');expect(page.locator('#section-1 .rp-save').first).to_be_focused()
        assert not blocked and not errors,(blocked,errors)
        ctx.close()
    browser.close()
result={'browser':version,'screenshots':manifest['screenshots'],'contrast':[{'fg':fg,'bg':bg,'kind':kind,'ratio':r} for (fg,bg,kind),r in sorted(pairs.items())],'checks':results,'texts':sorted(texts)}
Path('/tmp/civ116-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print('20 durum/genişlik kontrolü, açık formlar, klavye, salt okunur, kaydırma ve tüm kontrast çiftleri geçti.')
PY_CAPTURE
```

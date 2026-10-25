# Civensa tasarım prototipi · CIV-095

Bu klasör uygulamadan bağımsız, yalnız HTML/CSS ile hazırlanmış bir görsel onay paketidir. Uygulama, şablon, rota veya veri tabanı değişikliği içermez. Veriler CIV-093 ekran haritasındaki sentetik Örnek kayıtlarıdır. Boş değerler sıfıra çevrilmez.

## Dosyalar ve inceleme

| Dosya | İçerik |
| --- | --- |
| [components.html](components.html) | Renk, tipografi ve tüm bileşenlerin durumları. Düğmelerin normal, üzerine gelme, odak, pasif ve yükleniyor örnekleri; alanların boş/dolu/odak/pasif/salt okunur/hata durumları; onay kutuları, radyo, rozetler, sekmeler, adımlar, tablolar, boş durum, bildirim ve ayrı onay penceresi. Yerel select için salt okunur özelliği yoktur; pasif örnek kullanılır. |
| [screens/034-modules.html](screens/034-modules.html) | Müdürlük rolünde üç raporlama modülü ve bütün eski bağlantılar. |
| [screens/024-department.html](screens/024-department.html) | Gösterge, yıllık değerler ve açıklamalar; üstte kalan işler ve kayıt eylemi; alan yanında hata ve özet; ikincil menüde kaldırma, ayrı onay penceresi. Faaliyet sekmesi aynı sentetik fixture ile özet görünüm sunar; 068/075/076 ekranlarının tüm form tasarımı bu görevin kapsamı değildir. |
| [screens/012-section-editor.html](screens/012-section-editor.html) | EK-1 editörü, metin ve durum alanları, 36 bölüm bağlantısı, belirgin durum rozetleri, görsel tablo taslağı, kaydedilmiş içerik önizlemesi ve Türkçe denetim özetleri; ham önce/sonra verileri varsayılan kapalı “Teknik ayrıntı” içinde. |
| [tokens.css](tokens.css) | İstenen renkler, yazı, boşluk, köşe, kontrol/satır/yan menü boyutları ve odak tokenları. |
| [fonts.css](fonts.css), [fonts/](fonts/) | Fira Sans 400/500/600; Türkçe için latin ve latin-ext woff2 alt kümeleri. SIL OFL lisansı [fonts/OFL.txt](fonts/OFL.txt). Kaynak: Fontsource `@fontsource/fira-sans` 5.2.7 (npm). Harici font isteği yoktur. Yedek system-ui. |
| [prototype.css](prototype.css) | Ortak bileşenler ve duyarlı yerleşim. 248 px açık yan menü masaüstünde sayfanın sonuna kadar uzanır. 390 px görünümde içerikten sonra gelir; üstteki “Menüye git” bağlantısı menüye gider. Etiketler 14 px, girişler 16 px, kontroller 40 px. |
| [prototype.js](prototype.js) | Yalnız menü/pencere açma, kapatma ve odak iadesi. Kaydetme/gönderme/silme/oturum işlemleri temsilî pencere açar; API, depolama veya uygulama isteği yapmaz. |
| [element-map.json](element-map.json) | 104 eski öğenin kaynak kimliği, eski hedefi ve yeni yeri; HTML `data-source-id`/`data-original-target` ile birebir eşleşir. |
| [browser_helpers.py](browser_helpers.py) | Yalnız loopback statik sunucu ve tarayıcı ayarları. CIV-093 yakalama ayarları korunur; uygulama/DB başlatan guide modülü içe alınmaz. |
| [capture_screenshots.py](capture_screenshots.py) | Playwright ile iki genişlikte PNG üretimi; yatay taşma, 40 px kontrol, font, etiket, 104 öğe/hedef/değer, pencere/sekme, klavye odağı ve ağ sınırı doğrulaması. |
| [check_contrast.py](check_contrast.py) | Çizilen metin/zemin çiftlerini, kontrol sınırlarını, odak çizgilerini ve seçim işaretlerini gerçek Chromium stillerinden toplar. AA metin 4,5:1; büyük metin ve kontrol sınırı 3:1. |
| [screenshots/](screenshots/) | Dört sayfa × 1440/390 tam sayfa; ayrıca onay pencereleri, faaliyet sekmesi ve dışa aktarma menüsü. [manifest.json](screenshots/manifest.json) boyutları ve tarayıcı sürümünü kaydeder. Her PNG ≤ 1.500.000 bayt. |

Depo kökünden yerel inceleme:

```sh
python -m http.server 8000 --bind 127.0.0.1 --directory docs/design/prototype
# http://127.0.0.1:8000/components.html
```

Doğrulama ve ekran görüntülerini yenileme (Python, Playwright, Pillow ve Chromium gerekir; uygulama veya PostgreSQL gerekmez):

```sh
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
python docs/design/prototype/check_contrast.py
python docs/design/prototype/capture_screenshots.py
node --check docs/design/prototype/prototype.js
```

Sistem Chromium kurulumu varsa `CIVENSA_CHROMIUM_PATH` seçilebilir; varsayılan olarak sistem `chromium`, yoksa Playwright Chromium kullanılır. Ekranlar 900 px viewport yüksekliği, DPR 1, tr-TR ve Europe/Istanbul ile çekilir. Tam sayfa boyutu korunur; önce kayıpsız PNG optimizasyonu, yalnız 1,5 MB aşılırsa 256 renk kodlama yapılır.

## Etkileşim ve kontrast kararları

Prototip içindeki karşılığı bulunan `/modules` ve `/department/1` bağlantıları ilgili HTML dosyasına gider. Diğer eski bağlantılar “Bağlantı hedefi” penceresinde özgün URL/eylemi gösterir. EK-1 bölüm seçimleri de hedef kodunu gösterir; yeni bölüm içeriği uydurulmaz. Tamamlanma görünümü, dışa aktarımlar, parola, bildirimler ve çıkış erişilebilir kalır. Eski hedefler her öğede ayrıca saklanır. Veri yazma işlemlerinde başarı olmuş gibi davranılmaz. Yerel HTML sekmeleri CSS `:target` ile değişir; JavaScript sadece menü/pencereler içindir.

İki raporda tek birincil düğme üstteki kayıt eylemidir. Strateji gönderimi aynı özetin ikincil eylemidir. EK-1 kalan işler sayıları 36 bölümün 33 boş, 2 taslak, 1 hazır durumundan türetilmiştir. Bölüm listesi varsayılan açık tutulur, istenirse daraltılır. Kaldırma formunun uyarı metni ve Vazgeç/Kaldırmayı Onayla eylemleri ayrı modalda korunur. Başlangıç odağı Vazgeç üzerindedir; Escape kapatır ve odağı çağıran öğeye döndürür.

`--border` (#E3E1DC) dekoratif kart/ayırıcı çizgisidir; beyaz üzerinde etkileşimli sınır için yeterli değildir. Alanlar, ikincil düğmeler ve menüler `--text-secondary`, etkin eylemler `--accent` ile sınırlandırılır. Ölçüm normal ve pasif metinlerde 4,5:1 şartını korur. Gerçek hover/odak, açık menü, her modal, iki sekme ve 1440/390 görünümü taranır. Galerideki sabit hover/odak örnekleri de ölçülür. Betik bilinmeyen renk veya başarısız çiftte hata koduyla çıkar; çıktısı PR açıklamasındadır. Bu kontrol tüm WCAG uygunluğunun beyanı değildir.

Görsel tablo düzenleyici boş 2 sütun/1 satır taslağıdır. Satır/sütun ekle düğmeleri temsilî pencere açar. Kaydedilmiş metin ve denetim JSON’u değiştirilmez; JSON yalnız varsayılan kapalı “Teknik ayrıntı” içinde gösterilir. Saklama biçimi ve canlı önizleme daha sonraki uygulama görevlerinde kararlaştırılacaktır.

## Lead incelemesi sonrası üç düzeltme

- 012 denetim kaydı aynı tarih/kullanıcıyla “Durum: Boş → Taslak” ve “İçerik: 1 paragraf eklendi” olarak özetlenir. “Önceki kayıt” ve “Yeni kayıt” JSON verileri aynen korunur; yeni “Teknik ayrıntı” bölümü varsayılan kapalıdır. E058 konum açıklaması güncellendi.
- Rozet, hata, bildirim ve açılır bölüm simgeleri tek SVG çizgi ailesini kullanır: 16 px, `stroke="currentColor"`, dekoratif `aria-hidden="true"`. Yerel disclosure işaretleri gizlenir; ortak SVG oku açık durumda 90 derece döner, animasyon uygulanmaz. Onay kutusunun işareti, geri/menü okları ve ekleme işaretleri de aynı aileye taşındı; görünür sözcükler korunur.
- “Açıklama · Klavye odağı” örneği açıkça `aria-invalid="false"` olarak işaretlenir. Nötr alan kenarlığı ve yalnız 2 px vurgu odağı/2 px uzaklık kullanır. Kırmızı, `aria-invalid="true"` hata durumuna ayrılır.

## Metin değişiklikleri

Veri, gösterge adı, tarihler, açıklamalar, onay uyarısı ve tüm eylem ifadeleri korunmuştur. Yapılan yazım değişiklikleri ve yeni yardımcı metinler:

- Ortak marka altındaki “RAPORLAMA” → “Kurumsal raporlama”; tamamı büyük tanıtım etiketi kaldırıldı.
- 024 alan etiketleri cümle düzeninde: GÖSTERGE ADI → Gösterge adı; ÖLÇÜ BİRİMİ → Ölçü birimi; 2025 GERÇEKLEŞME → 2025 gerçekleşme; 2026 PLANLANAN → 2026 planlanan; 2026 YIL SONU GERÇEKLEŞME TAHMİNİ → 2026 yıl sonu gerçekleşme tahmini; 2027 HEDEF → 2027 hedef; 2028 TAHMİN → 2028 tahmin; 2029 TAHMİN → 2029 tahmin; GÖSTERGEYE İLİŞKİN AÇIKLAMA → Göstergeye ilişkin açıklama; HESAPLAMA YÖNTEMİ → Hesaplama yöntemi; VERİNİN KAYNAĞI → Verinin kaynağı.
- 012 alan etiketleri: BÖLÜM İÇERİĞİ → Bölüm içeriği; DURUM → Durum; UYGULANAMAZ GEREKÇESİ → Uygulanamaz gerekçesi.
- 012 bölüm başlıkları: YÖNETİCİ ÖZETİ → Yönetici özeti; I- GENEL BİLGİLER → I- Genel bilgiler; II- AMAÇLAR ve HEDEFLER → II- Amaçlar ve hedefler; III- FAALİYETLERE İLİŞKİN BİLGİ VE DEĞERLENDİRMELER → III- Faaliyetlere ilişkin bilgi ve değerlendirmeler; IV- KURUMSAL KABİLİYET VE KAPASİTENİN DEĞERLENDİRİLMESİ → IV- Kurumsal kabiliyet ve kapasitenin değerlendirilmesi; V- ÖNERİ VE TEDBİRLER → V- Öneri ve tedbirler; EKLER → Ekler.
- “Birim raporu · Taslak” ifadesi başlık ve ayrı Taslak rozeti olarak; metin ve durum aynı.
- Boru işaretli tablo açıklaması kaldırıldı. “Paragrafları boş satırla ayırın. Madde için ‘- ’ kullanın.” korundu. Yeni: “Tabloyu hücrelere yazarak düzenleyin. Satır veya sütun eklemek için aşağıdaki düğmeleri kullanın.”; “+ Satır ekle”, “+ Sütun ekle”, “Görsel taslak” ve boş taslağın kaydedilmiş içeriğin parçası olmadığını açıklayan metin.
- “Önizleme kaydetmeden güncellenir.” → “Kaydedilmiş içerik” / “Statik önizleme örneği.”; prototipte canlı güncelleme yapılmadığı açıklandı.
- Mevcut “Göstergeye ilişkin açıklama boş.” hatasına alan yanında “Açıklamayı girin.” eklendi.
- Yeni yönlendirme metinleri: “Kalan işler”, “33 boş bölümü doldurun.”, “Misyon ve Vizyon ile Fiziksel Yapı taslaklarını tamamlayın.”; “Boş değerler sıfır olarak değerlendirilmez.”; “Yıllık değerler · Adet”; “Rapor bölümleri”, “Bölüm listesi” ve durum adetleri.
- Yeni kapsayıcı menü etiketleri “Diğer işlemler” ve “Dışa aktar”; eski eylem adları aynen altlarında korunur.
- İçerik yolu, mobil “Menüye git”, “İçeriğe geç”, dosyalar arası prototip gezintisi ve statik işlem/hedef/parola/bildirim pencerelerinin açıklamaları eklendi. Bunlar yeni prototip yardımcı metinleridir; uygulamaya uygulanmış sayılmaz.
- Faaliyet sekmesindeki ve bileşen galerisindeki örnek sayılar/adlar CIV-093’teki aynı sentetik kayıtlardan alınır. Galeriye eklenen durum/boş liste/yardım örnekleri görsel tasarım metinleridir.

## Eski öğeler → yeni konumlar

Kaynak: [CIV-093 INDEX.md](../../screenshots/ui-map-v1/INDEX.md). Numaralar her ekran için bağımsızdır. Form ve düğmesi ayrı satır olarak korunur. 034: 14/14, 024: 32/32, 012: 58/58; toplam **104/104**.

### 034 · 034-modules-department.png

| Öğe | Eski etiket / işlev | Yeni konum | Eski hedef |
| --- | --- | --- | --- |
| E001 | Faaliyet Raporu · EK-1 | [Sol menü / Faaliyet Raporu · EK-1](screens/034-modules.html#e001) | `/activity-sections` |
| E002 | Modüller | [Sol menü / Modüller](screens/034-modules.html#e002) | `/modules` |
| E003 | Genel Bakış | [Sol menü / Genel Bakış](screens/034-modules.html#e003) | `/dashboard` |
| E004 | İç Kontrol Eylemlerimiz | [Sol menü / İç Kontrol Eylemlerimiz](screens/034-modules.html#e004) | `/internal-control/our-actions` |
| E005 | Veri Girişi | [Sol menü / Veri Girişi](screens/034-modules.html#e005) | `/department/1` |
| E006 | Gönderim Yetkileri | [Sol menü / Gönderim Yetkileri](screens/034-modules.html#e006) | `/submit-authorizations` |
| E007 | Parolamı Değiştir | [Sol menü / hesap işlemleri](screens/034-modules.html#e007) | `#passwordModal` |
| E008 | Çıkış | [Sol menü / çıkış formu](screens/034-modules.html#e008) | `POST /logout` |
| E009 | Çıkış | [Sol menü / hesap işlemleri](screens/034-modules.html#e009) | `POST /logout` |
| E010 | Bildirimler | [Üst çubuk / bildirimler](screens/034-modules.html#e010) | `GET /api/notifications → #notificationPanel` |
| E011 | Performans Programı’na gir | [Performans Programı kartı](screens/034-modules.html#e011) | `/dashboard` |
| E012 | Gösterge gerçekleşmelerine gir | [Faaliyet Raporu kartı](screens/034-modules.html#e012) | `/activity-reports` |
| E013 | Kaynak kayıt inceleme pilotu | [Faaliyet Raporu kartı](screens/034-modules.html#e013) | `/activity-report` |
| E014 | İç Kontrol Eylemlerimiz | [İç Kontrol kartı](screens/034-modules.html#e014) | `/internal-control` |

### 024 · 024-department-department.png

| Öğe | Eski etiket / işlev | Yeni konum | Eski hedef |
| --- | --- | --- | --- |
| E001 | Faaliyet Raporu · EK-1 | [Sol menü / Faaliyet Raporu · EK-1](screens/024-department.html#e001) | `/activity-sections` |
| E002 | Modüller | [Sol menü / Modüller](screens/024-department.html#e002) | `/modules` |
| E003 | Genel Bakış | [Sol menü / Genel Bakış](screens/024-department.html#e003) | `/dashboard?period_id=1` |
| E004 | PP Kaynak Karşılaştırması | [Sol menü / PP Kaynak Karşılaştırması](screens/024-department.html#e004) | `/source-comparison?period_id=1` |
| E005 | İç Kontrol Eylemlerimiz | [Sol menü / İç Kontrol Eylemlerimiz](screens/024-department.html#e005) | `/internal-control/our-actions` |
| E006 | Veri Girişi | [Sol menü / Veri Girişi](screens/024-department.html#e006) | `/department/1?period_id=1` |
| E007 | Gönderim Yetkileri | [Sol menü / Gönderim Yetkileri](screens/024-department.html#e007) | `/submit-authorizations?period_id=1` |
| E008 | Parolamı Değiştir | [Sol menü / hesap işlemleri](screens/024-department.html#e008) | `#passwordModal` |
| E009 | Çıkış | [Sol menü / çıkış formu](screens/024-department.html#e009) | `POST /logout` |
| E010 | Çıkış | [Sol menü / hesap işlemleri](screens/024-department.html#e010) | `POST /logout` |
| E011 | Bildirimler | [Üst çubuk / bildirimler](screens/024-department.html#e011) | `GET /api/notifications → #notificationPanel` |
| E012 | Performans Kartları ve Ekonomik Tablolar | [Rapor üst araçları](screens/024-department.html#e012) | `/program/1?period_id=1` |
| E013 | Performans Göstergeleri | [Veri girişi görünüm sekmeleri](screens/024-department.html#e013) | `#indicators` |
| E014 | Faaliyet Maliyetleri | [Veri girişi görünüm sekmeleri](screens/024-department.html#e014) | `#activities` |
| E015 | Göstergeye ilişkin açıklama boş. | [Gösterge kartı / hata özeti: ilgili alana bağlantı](screens/024-department.html#e015) | `Aynı gösterge kartındaki sorunlu alan` |
| E016 | GÖSTERGE ADI | [Gösterge kartı / kimlik alanları](screens/024-department.html#e016) | `POST /api/indicators/1/save` |
| E017 | ÖLÇÜ BİRİMİ | [Gösterge kartı / kimlik alanları](screens/024-department.html#e017) | `POST /api/indicators/1/save` |
| E018 | 2025 GERÇEKLEŞME | [Gösterge kartı / yıllık değerler](screens/024-department.html#e018) | `POST /api/indicators/1/save` |
| E019 | 2026 PLANLANAN | [Gösterge kartı / yıllık değerler](screens/024-department.html#e019) | `POST /api/indicators/1/save` |
| E020 | 2026 YIL SONU GERÇEKLEŞME TAHMİNİ | [Gösterge kartı / yıllık değerler](screens/024-department.html#e020) | `POST /api/indicators/1/save` |
| E021 | 2027 HEDEF | [Gösterge kartı / yıllık değerler](screens/024-department.html#e021) | `POST /api/indicators/1/save` |
| E022 | 2028 TAHMİN | [Gösterge kartı / yıllık değerler](screens/024-department.html#e022) | `POST /api/indicators/1/save` |
| E023 | 2029 TAHMİN | [Gösterge kartı / yıllık değerler](screens/024-department.html#e023) | `POST /api/indicators/1/save` |
| E024 | GÖSTERGEYE İLİŞKİN AÇIKLAMA | [Gösterge kartı / açıklama ve alan hatası](screens/024-department.html#e024) | `POST /api/indicators/1/save` |
| E025 | HESAPLAMA YÖNTEMİ | [Gösterge kartı / açıklamalar](screens/024-department.html#e025) | `POST /api/indicators/1/save` |
| E026 | VERİNİN KAYNAĞI | [Gösterge kartı / açıklamalar](screens/024-department.html#e026) | `POST /api/indicators/1/save` |
| E027 | Göstergeyi Kaldır | [Gösterge kartı / Diğer işlemler menüsü](screens/024-department.html#e027) | `Aynı sayfadaki ayrıntı bölümü` |
| E028 | Kaldırmayı Onayla / Vazgeç | [Ayrı kaldırma onay penceresi / form](screens/024-department.html#e028) | `POST /program/1/indicator/1/remove` |
| E029 | Kaldırmayı Onayla | [Ayrı kaldırma onay penceresi / onay](screens/024-department.html#e029) | `POST /program/1/indicator/1/remove` |
| E030 | Vazgeç | [Ayrı kaldırma onay penceresi / iptal](screens/024-department.html#e030) | `Aynı taslak kaldırma kutusu` |
| E031 | Kaydet ve Kontrol Et | [Üst rapor özeti / birincil eylem](screens/024-department.html#e031) | `POST /api/indicators/1/save` |
| E032 | Stratejiye Gönder | [Üst rapor özeti / gönderim](screens/024-department.html#e032) | `POST /api/departments/1/submit` |

### 012 · 012-activity-sections-department.png

| Öğe | Eski etiket / işlev | Yeni konum | Eski hedef |
| --- | --- | --- | --- |
| E001 | Faaliyet Raporu · EK-1 | [Sol menü / Faaliyet Raporu · EK-1](screens/012-section-editor.html#e001) | `/activity-sections` |
| E002 | Modüller | [Sol menü / Modüller](screens/012-section-editor.html#e002) | `/modules` |
| E003 | Genel Bakış | [Sol menü / Genel Bakış](screens/012-section-editor.html#e003) | `/dashboard` |
| E004 | İç Kontrol Eylemlerimiz | [Sol menü / İç Kontrol Eylemlerimiz](screens/012-section-editor.html#e004) | `/internal-control/our-actions` |
| E005 | Veri Girişi | [Sol menü / Veri Girişi](screens/012-section-editor.html#e005) | `/department/1` |
| E006 | Gönderim Yetkileri | [Sol menü / Gönderim Yetkileri](screens/012-section-editor.html#e006) | `/submit-authorizations` |
| E007 | Parolamı Değiştir | [Sol menü / hesap işlemleri](screens/012-section-editor.html#e007) | `#passwordModal` |
| E008 | Çıkış | [Sol menü / çıkış formu](screens/012-section-editor.html#e008) | `POST /logout` |
| E009 | Çıkış | [Sol menü / hesap işlemleri](screens/012-section-editor.html#e009) | `POST /logout` |
| E010 | Bildirimler | [Üst çubuk / bildirimler](screens/012-section-editor.html#e010) | `GET /api/notifications → #notificationPanel` |
| E011 | ← Tamamlanma görünümü | [Rapor araçları / geri dönüş](screens/012-section-editor.html#e011) | `/activity-sections` |
| E012 | Word olarak indir | [Dışa aktar menüsü](screens/012-section-editor.html#e012) | `/activity-sections/reports/2/export.docx` |
| E013 | PDF olarak indir | [Dışa aktar menüsü](screens/012-section-editor.html#e013) | `/activity-sections/reports/2/export.pdf` |
| E014 | Dizgi verisi (JSON) | [Dışa aktar menüsü](screens/012-section-editor.html#e014) | `/activity-sections/reports/2/typeset.json` |
| E015 | Strateji’ye gönder | [Üst rapor özeti / gönderim formu](screens/012-section-editor.html#e015) | `POST /activity-sections/reports/2/workflow/submit` |
| E016 | Strateji’ye gönder | [Üst rapor özeti / gönderim](screens/012-section-editor.html#e016) | `POST /activity-sections/reports/2/workflow/submit` |
| E017 | YÖNETİCİ ÖZETİ Boş | [Rapor bölümleri / Yönetici özeti](screens/012-section-editor.html#e017) | `?code=OZET` |
| E018 | I- GENEL BİLGİLER Boş | [Rapor bölümleri / I- Genel bilgiler](screens/012-section-editor.html#e018) | `?code=I` |
| E019 | A- Misyon ve Vizyon Taslak | [Rapor bölümleri / A- Misyon ve Vizyon](screens/012-section-editor.html#e019) | `?code=I.A` |
| E020 | B- Yetki, Görev ve Sorumluluklar Boş | [Rapor bölümleri / B- Yetki, Görev ve Sorumluluklar](screens/012-section-editor.html#e020) | `?code=I.B` |
| E021 | C- İdareye İlişkin Bilgiler Boş | [Rapor bölümleri / C- İdareye İlişkin Bilgiler](screens/012-section-editor.html#e021) | `?code=I.C` |
| E022 | 1- Fiziksel Yapı Taslak | [Rapor bölümleri / 1- Fiziksel Yapı](screens/012-section-editor.html#e022) | `?code=I.C.1` |
| E023 | 2- Teşkilat Yapısı Boş | [Rapor bölümleri / 2- Teşkilat Yapısı](screens/012-section-editor.html#e023) | `?code=I.C.2` |
| E024 | 3- Teknoloji ve Bilişim Altyapısı Boş | [Rapor bölümleri / 3- Teknoloji ve Bilişim Altyapısı](screens/012-section-editor.html#e024) | `?code=I.C.3` |
| E025 | 4- İnsan Kaynakları Boş | [Rapor bölümleri / 4- İnsan Kaynakları](screens/012-section-editor.html#e025) | `?code=I.C.4` |
| E026 | 5- Sunulan Hizmetler Boş | [Rapor bölümleri / 5- Sunulan Hizmetler](screens/012-section-editor.html#e026) | `?code=I.C.5` |
| E027 | 6- Yönetim ve İç Kontrol Sistemi Boş | [Rapor bölümleri / 6- Yönetim ve İç Kontrol Sistemi](screens/012-section-editor.html#e027) | `?code=I.C.6` |
| E028 | D- Diğer Hususlar Boş | [Rapor bölümleri / D- Diğer Hususlar](screens/012-section-editor.html#e028) | `?code=I.D` |
| E029 | II- AMAÇLAR ve HEDEFLER Boş | [Rapor bölümleri / II- Amaçlar ve hedefler](screens/012-section-editor.html#e029) | `?code=II` |
| E030 | A- Temel Politika ve Öncelikler Boş | [Rapor bölümleri / A- Temel Politika ve Öncelikler](screens/012-section-editor.html#e030) | `?code=II.A` |
| E031 | B- İdarenin Stratejik Planında Yer Alan Amaç ve Hedefler Boş | [Rapor bölümleri / B- İdarenin Stratejik Planında Yer Alan Amaç ve Hedefler](screens/012-section-editor.html#e031) | `?code=II.B` |
| E032 | C- Diğer Hususlar Boş | [Rapor bölümleri / C- Diğer Hususlar](screens/012-section-editor.html#e032) | `?code=II.C` |
| E033 | III- FAALİYETLERE İLİŞKİN BİLGİ VE DEĞERLENDİRMELER Boş | [Rapor bölümleri / III- Faaliyetlere ilişkin bilgi ve değerlendirmeler](screens/012-section-editor.html#e033) | `?code=III` |
| E034 | A- Malî Bilgiler Boş | [Rapor bölümleri / A- Malî Bilgiler](screens/012-section-editor.html#e034) | `?code=III.A` |
| E035 | 1- Bütçe Uygulama Sonuçları Boş | [Rapor bölümleri / 1- Bütçe Uygulama Sonuçları](screens/012-section-editor.html#e035) | `?code=III.A.1` |
| E036 | 2- Temel Malî Tablolara İlişkin Açıklamalar Boş | [Rapor bölümleri / 2- Temel Malî Tablolara İlişkin Açıklamalar](screens/012-section-editor.html#e036) | `?code=III.A.2` |
| E037 | 3- Malî Denetim Sonuçları Boş | [Rapor bölümleri / 3- Malî Denetim Sonuçları](screens/012-section-editor.html#e037) | `?code=III.A.3` |
| E038 | 4- Diğer Hususlar Boş | [Rapor bölümleri / 4- Diğer Hususlar](screens/012-section-editor.html#e038) | `?code=III.A.4` |
| E039 | B- Performans Bilgileri Boş | [Rapor bölümleri / B- Performans Bilgileri](screens/012-section-editor.html#e039) | `?code=III.B` |
| E040 | 1- Program, Alt Program, Faaliyet Bilgileri Boş | [Rapor bölümleri / 1- Program, Alt Program, Faaliyet Bilgileri](screens/012-section-editor.html#e040) | `?code=III.B.1` |
| E041 | 2- Performans Sonuçlarının Değerlendirilmesi Boş | [Rapor bölümleri / 2- Performans Sonuçlarının Değerlendirilmesi](screens/012-section-editor.html#e041) | `?code=III.B.2` |
| E042 | i. Alt program hedef ve göstergeleriyle ilgili gerçekleşme sonuçları ve değerlendirmeler Hazır | [Rapor bölümleri / i. Alt program hedef ve göstergeleriyle ilgili gerçekleşme sonuçları ve değerlendirmeler](screens/012-section-editor.html#e042) | `?code=III.B.2.i` |
| E043 | ii. Performans denetim sonuçları Boş | [Rapor bölümleri / ii. Performans denetim sonuçları](screens/012-section-editor.html#e043) | `?code=III.B.2.ii` |
| E044 | 3- Stratejik Plan Değerlendirme Tabloları Boş | [Rapor bölümleri / 3- Stratejik Plan Değerlendirme Tabloları](screens/012-section-editor.html#e044) | `?code=III.B.3` |
| E045 | 4- Performans Bilgi Sisteminin Değerlendirilmesi Boş | [Rapor bölümleri / 4- Performans Bilgi Sisteminin Değerlendirilmesi](screens/012-section-editor.html#e045) | `?code=III.B.4` |
| E046 | 5- Diğer Hususlar Boş | [Rapor bölümleri / 5- Diğer Hususlar](screens/012-section-editor.html#e046) | `?code=III.B.5` |
| E047 | IV- KURUMSAL KABİLİYET VE KAPASİTENİN DEĞERLENDİRİLMESİ Boş | [Rapor bölümleri / IV- Kurumsal kabiliyet ve kapasitenin değerlendirilmesi](screens/012-section-editor.html#e047) | `?code=IV` |
| E048 | A- Üstünlükler Boş | [Rapor bölümleri / A- Üstünlükler](screens/012-section-editor.html#e048) | `?code=IV.A` |
| E049 | B- Zayıflıklar Boş | [Rapor bölümleri / B- Zayıflıklar](screens/012-section-editor.html#e049) | `?code=IV.B` |
| E050 | C- Değerlendirme Boş | [Rapor bölümleri / C- Değerlendirme](screens/012-section-editor.html#e050) | `?code=IV.C` |
| E051 | V- ÖNERİ VE TEDBİRLER Boş | [Rapor bölümleri / V- Öneri ve tedbirler](screens/012-section-editor.html#e051) | `?code=V` |
| E052 | EKLER Boş | [Rapor bölümleri / Ekler](screens/012-section-editor.html#e052) | `?code=EKLER` |
| E053 | Bölümü kaydet | [Bölüm editörü / kayıt formu](screens/012-section-editor.html#e053) | `POST /activity-sections/reports/2/sections/I.A` |
| E054 | BÖLÜM İÇERİĞİ | [Bölüm editörü / metin](screens/012-section-editor.html#e054) | `POST /activity-sections/reports/2/sections/I.A` |
| E055 | DURUM Boş Taslak Hazır Uygulanamaz | [Bölüm editörü / durum](screens/012-section-editor.html#e055) | `POST /activity-sections/reports/2/sections/I.A` |
| E056 | UYGULANAMAZ GEREKÇESİ | [Bölüm editörü / durum gerekçesi](screens/012-section-editor.html#e056) | `POST /activity-sections/reports/2/sections/I.A` |
| E057 | Bölümü kaydet | [Üst rapor özeti / birincil eylem](screens/012-section-editor.html#e057) | `POST /activity-sections/reports/2/sections/I.A` |
| E058 | 25.10.2026 00:35 TSİ · Kullanıcı 2 · Bölüm kaydedildi | [Bölüm denetim geçmişi / Türkçe değişiklik özeti ve kapalı Teknik ayrıntı](screens/012-section-editor.html#e058) | `Aynı sayfadaki ayrıntı bölümü` |

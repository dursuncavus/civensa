# Performans Programı → Faaliyet Raporu veri sözleşmesi

Tarih: 8 Ekim 2026. Durum: kullanıcı tarafından onaylandı; ilk gösterge sözleşmesi uygulandı. Aşağıdaki kayıt tasarımının uygulamadaki karşılıkları ve sınırları son bölümde açıklanır.

## Doğrulanan başlangıç

- HEAD `e2deb12`; C1 üç dosyada commit edilmemiş durumda: PostgreSQL test fixture'ı, concurrency testleri ve CI workflow'u.
- `Publication` dönem, yayın numarası, JSON snapshot ve SHA-256 saklıyor. Yayın kapısı birim onaylarını kontrol ediyor.
- Faaliyet Raporu pilotu bugün canlı `Indicator` / `IndicatorValue` kayıtlarını okuyor; bir yayına bağlı değil.
- `Indicator.id` dönem içindeki kayıt kimliği. `code` ve ad kalıcı kimlik garantisi sağlamıyor.
- Kanıt, sapma ve Faaliyet Raporu revizyonu için ayrı kalıcı kayıtlar bulunmuyor.
- GitHub CI doğrulanmadı. Checkout'ta Git remote tanımlı değil. Dolu PostgreSQL test DB'sinde migration testi tekrar çalıştırılabilir değil; bu issue ayrı kalacak.
- Bu oturumda yeni, boş ve geçici PostgreSQL ortamında `pytest -q --require-postgres`: **149 passed, 0 skipped** (13.87 s). Bir Starlette/httpx deprecation uyarısı var. PostgreSQL olmadan kontrol: 141 passed, 8 skipped. Testler mevcut kurum DB'sine karşı çalıştırılmadı.

## Karar 1 — raporun okuyacağı sürüm

Faaliyet Raporu oluşturulurken strateji kullanıcısı aynı yılın belirli bir `Publication.id` kaydını seçer. Seçim ekranı yıl, yayın numarası, yayın zamanı ve bütünlük durumunu gösterir. Tek uygun yayın varsa önseçim yapılabilir; kayıt sırasında açıkça sabitlenir. Daha sonra `latest` sorgusu kullanılmaz.

Taslak veya yalnız birim onayı alınmış canlı veri resmî baz değildir. Mevcut Publication yayın kapısından geçmiş sabit baz kabul edilir; ayrıca hukuki/meclis onayı iş akışı bulunduğu varsayılmaz. Kurum böyle bir onay isterse ayrı durum ve onay kanıtı tasarlanmalıdır.

Hedef, gösterge adı, birim, yöntem, kaynak, sorumlu birim ve kart bağlantısı seçilen snapshot'tan okunur. Sonraki canlı düzenlemeler raporu değiştirmez. Yayın hash'i her baz okumasında doğrulanır. Geçmiş yıllarda yayın yoksa otomatik olarak canlı veri veya gelecek yıl tahmini kullanılmaz; ayrı, kaynaklı ve onaylı tarihsel baz gerekir.

Yeni Performans Programı yayını mevcut raporu kendiliğinden taşımaz. Kullanıcı yeni rapor revizyonu açar; eski/yeni hedef ve tanım farklarını görür. Aynı kimlikteki gerçekleşmeler bile yeni tanım ve kapsam bakımından kontrol edilmeden taşınmaz. Eski revizyon korunur.

## Karar 2 — kimlik ve sürümler

Birbirinden ayrı dört kimlik:

1. `indicator_identity_id`: kurum kapsamında UUID; yıllar boyunca aynı ölçülen kavramı temsil eder.
2. `indicator_revision_id`: değişmez tanım sürümü; ad, birim, hesaplama yöntemi, kapsam ve veri kaynağı içerir.
3. Dönem kaydı: mevcut `Indicator.id`; kalıcı kimliğe ve tanım sürümüne bağlanır. Yıllık hedef bu kayda aittir.
4. Yayın içi gösterge referansı: `(publication_id, snapshot_indicator_id)`; mevcut snapshot'taki `id` kullanılır. Eski JSON yeniden yazılmaz.

Gösterge kodu, sıra numarası ve ad görüntüleme/arama alanlarıdır; eşleme anahtarı değildir. Birim veya yöntem değişikliği yeni tanım sürümü üretir. Ölçülen kavram veya kapsamın karşılaştırılabilirliği bozulursa yeni kimlik açılır; önceki kimlikle `replaces`, `split_from`, `merged_from` gibi gerekçeli ilişki kurulur. Geçmiş değerler otomatik dönüştürülmez/toplanmaz.

Dönem aktarımı aynı kimliği açıkça taşır. Tarihsel kayıtlar ad benzerliğiyle birleştirilmez; strateji kullanıcısının gerekçeli eşlemesi gerekir. Yeni kimlikler mevcut kayıtlara önce ayrı atanabilir; dönemler arası birleştirme sonradan denetlenebilir biçimde yapılır.

Eski yayınlar için ayrı, denetlenen `PublicationIndicatorBinding` önerilir: yayın, snapshot gösterge id'si, kalıcı kimlik, tanım sürümü, eşleyen kullanıcı, gerekçe ve zaman. Eşleme rapor revizyonunda sabitlenir; sonraki eşleme düzeltmesi yeni rapor revizyonu gerektirir. Yeni yayınların snapshot'ı kimlik ve tanım sürümünü doğrudan taşır.

## Önerilen kayıtlar ve bağlar

| Kayıt | Ana alanlar / kural |
|---|---|
| ActivityReportRevision | report_id, revision, year, organization_id, publication_id, publication_sha256, contract_version, status, created_by; baz sonradan değiştirilmez |
| ReportIndicator | report_revision_id, publication_id, snapshot_indicator_id, identity_id, definition_revision_id, department_id; seçilen snapshot'taki üyelik doğrulanır |
| ActualRevision | report_indicator_id, revision, interval_start/end, value, raw_text, state, entered_by/time, supersedes_id; eski sürüm korunur |
| Evidence | actual_revision_id, source_title, source_date, source_locator, immutable_file_ref/hash veya kaynağın sabit sürüm referansı, added_by/time; bağlantı tek başına doğrulama sayılmaz |
| Deviation | actual_revision_id, target_reference, calculation_rule_version, delta, explanation, corrective_action, responsible_department_id; hesap/yorum aynı gerçekleşme revizyonuna bağlanır |
| ReviewEvent | report/actual revision, actor, action, note, timestamp; gönderme/onay/iade geçmişi eklemeli |

Gerçekleşme referansı kanıt ve sapmanın köküdür. Aynı kanıt birden çok kaydı destekliyorsa açık bağlantı tablosu kullanılır. Gösterge ve faaliyet gerçekleşmeleri farklı kayıt türleri olarak tutulur; faaliyet gideri bir gösterge gerçekleşmesi yerine yazılmaz. Faaliyet gerçekleşmesi için aynı yayın içi faaliyet referansı ve dönem/kapsam kontrolleri uygulanır.

Bir rapor revizyonu ve gösterge için aynı yıllık aralıkta yalnız bir güncel gerçekleşme revizyonu bulunur. Çeyrek/ay değerleri yıllık değerle kendiliğinden toplanmaz; toplama kuralı tanımda açık değilse yıllık değer ayrı doğrulanır. Sürüm çakışmasında 409 döner, ilk kayıt korunur. Onaylı rapor değişmez; düzeltme yeni revizyon açar.

## Sayılar ve hesap

- API'de sayılar ondalık metin; veritabanında Decimal/Numeric. Float kullanılmaz.
- Boş değer sıfır değildir. `missing`, `needs_review`, `verified` ayrımı korunur; mevcut verilerdeki durumlar açıkça eşlenir.
- `verified` sayısal veri durumudur; yönetim onayı ayrı iş akışı durumudur.
- Hedef yalnız snapshot'taki aynı yılın `target` kaydıdır; forecast/planned/year_end_estimate yerine geçmez.
- Sapma yönü için tanımda `increase`, `decrease`, `range`, `non_numeric` gerekir. Sadece `actual - target` olumlu/olumsuz başarı yorumu üretmez.
- Yüzde başarı ancak doğrulanmış karşılaştırılabilir sayılar ve uygun kural varsa hesaplanır. Sıfır hedefte bölme yapılmaz. Aralık ve nitel hedef için ayrı kural gerekir.

## Kullanıcı akışı ve mesajlar

1. Yıl → uygun yayın seçimi → baz özeti → taslak rapor revizyonu.
2. Müdürlük kendi göstergelerinde gerçekleşme ve kaynak ekler; hedefi değiştiremez.
3. Eksik kanıt/inceleme/sapma açıklaması gönderme öncesinde satır bazında gösterilir.
4. Strateji inceleme/onay/iade yapar; kurum raporu yalnız tamamlanmış kapsam üzerinden yayımlanır.

| Durum | Kullanıcı mesajı / sonraki adım |
|---|---|
| Yayın yok | Bu yıl için yayımlanmış Performans Programı bulunamadı. Strateji birimi baz yayını hazırlamalı. |
| Yeni yayın var | Yeni bir program sürümü yayımlandı. Bu rapor vN sürümüne bağlı kalıyor. Yeni revizyon oluşturabilirsiniz. |
| Hash uyuşmuyor | Program yayınının bütünlüğü doğrulanamadı. Rapor işlemi durduruldu; strateji birimine başvurun. |
| Başka yıl/birim göstergesi | Bu gösterge seçilen raporun yılına veya yetkili olduğunuz müdürlüğe ait değil. |
| Kaynak eksik | Gerçekleşmeyi incelemeye göndermek için dayanak kaynağını ekleyin. |
| Kayıt çakışması | Bu kayıt başka bir kullanıcı tarafından güncellendi. Son sürümü açıp değişikliğinizi yeniden kontrol edin. |
| Sıfır hedef | Hedef sıfır olduğu için yüzde başarı hesaplanmadı. Gerçekleşme ve sapma açıklaması gösterilir. |

Mevcut pilotun UX bulguları: 2027 yılı sabit üst sınır nedeniyle açılamıyor; atanmış müdürlüğü olmayan kullanıcı açıklamasız 403 alıyor; veri bulunmaması mesajı kaynağın aktarılmadığını kesin neden gibi söylüyor. Yeni akışta yıl listesi erişilebilir dönemlerden üretilmeli, yetki hatası açıklamalı olmalı, kayıt/yayın/kaynak eksikliği ayrılmalı. Pilot henüz resmî rapor olarak sunulmamalı.

## Uygulama sırası ve kabul testleri

Mimari onaydan sonra küçük adımlar:

1. Kimlik tabloları ve nullable dönem bağlantıları; geriye uyumlu migration. Eski snapshot'lar korunur; eşleme ayrı kayıt olur.
2. Sabit bazlı rapor revizyonu ve salt okunur snapshot okuyucu. Canlı hedef değişikliği, yeni yayın, bozuk hash, yıl/birim izolasyonu ve eski yayın uyumluluğu test edilir.
3. Revizyonlu gerçekleşme/kanıt/sapma girişi. Decimal, boş/sıfır, yetki, yinelenen aralık, concurrency ve kaynak revizyonu test edilir.
4. Onay/yayın kapıları ve kullanıcı akışları; onaylı raporun değişmezliği ve kontrollü yeniden bazlama test edilir.

Mimari kapsam kullanıcı tarafından onaylandı: kalıcı gösterge kimliği + değişmez dönemsel tanım sürümü + belirli yayına sabitlenen rapor revizyonu.

## Uygulanan ilk sözleşme

- `IndicatorIdentity.indicator_id`: UUID. Eski `Indicator.id` dönem satır kimliği olarak korunur; nullable `persistent_indicator_id` açık kimlik bağıdır. Eski kayıtlar migration sırasında isim/kod üzerinden birleştirilmez. Yayın sırasında her bağsız dönem kaydına bağımsız kimlik atanır; dönem kopyalama mevcut kimliği taşır. Aynı dönem/kimlik için tek satır kısıtı vardır.
- `IndicatorDefinitionRevision`: yıl, hedefler, ad/kod, birim, açıklama, yöntem, kaynak, kart/alt program ve müdürlük bilgilerinin değişmez JSON'u. Sürüm numarası kalıcı kimlik kapsamında artar. Tanım sürümü yayın hazırlanırken üretilir; mevcut taslak ekranları geriye uyumluluk için düzenlenebilir çalışma verisi olarak kalır.
- Yeni yayın snapshot'ları kalıcı `indicator_id`, `definition_revision_id` ve `activity_contract_version=1.0` taşır. Eski yayın JSON/hash içerikleri yeniden yazılmaz. Eski yayın göstergesi için strateji kullanıcısı gerekçeli `PublicationIndicatorBinding` oluşturmalıdır.
- `ActivityReport` kurum/yıl raporunun köküdür. `ActivityReportRevision` seçilen yayın id/hash'ini, önceki rapor revizyonunu ve göstergelerin açık kimlik üzerinden hesaplanmış baz farklarını sabitler. Yeni yayın seçmek yeni revizyon oluşturur; gerçekleşmeler otomatik taşınmaz. Onaylı raporu aynı bazla düzeltmek de yeni rapor revizyonu açar.
- `ReportIndicator` belirli rapor revizyonundaki belirli yayın-gösterge-tanım bağını temsil eder. `ActualRevision` yalnız bu kayda bağlanır; genel göstergeye yazılmaz. Kayıt rapor yılının yıllık gerçekleşmesidir; aylık/çeyreklik aralık girişi bu ilk sürümde açılmadı.
- Kanıt listesi, açıklama ve sapma aynı `ActualRevision` içinde atomik saklanır. Kanıt için kaynak adı, konumu ve sabit kaynak sürüm referansı gerekir. Dosya yükleme/depolama eklenmedi; kaynak referansının gerçekliği strateji incelemesine aittir.
- Sayılar JSON'da ondalık metin, DB'de Numeric/Decimal'dır. Boş/sıfır ve doğrulama durumları ayrıdır. Yalnız sayısal fark hesaplanır; başarı yönü veya yüzde başarı çıkarılmaz. Sapma kaydı hedef tanım sürümü ve hesap kuralı sürümünü taşır.
- Gösterge gerçekleşmelerinin onayı `ActivityReportApproval` ile kaydedilir; eksik doğrulama/kanıt veya açıklamasız sayısal fark onayı engeller. Onaylı revizyona uygulama üzerinden yazılamaz. Bu, tam Faaliyet Raporu kitabının kurumsal/meclis onayı değildir.
- Yayın, tanım, eşleme, rapor revizyonu, gösterge bağı, gerçekleşme ve onay kayıtlarının UPDATE/DELETE işlemleri ORM koruması ve SQLite/PostgreSQL migration trigger'larıyla engellenir.
- Rapor yazımlarında kök rapor kilidi/CAS ve beklenen revizyon kontrolü vardır. Bir eşzamanlı işlem uygulanır, diğeri 409 alır; kullanıcıya son sürümü açması söylenir.
- `/activity-reports` kullanıcı ekranları: yayın seçimi, rapor listesi/geçmişi, gerçekleşme-kaynak-açıklama girişi, onay, yeni bazla revizyon ve fark gösterimi. Eski `/activity-report` canlı kayıt pilotu açıkça ayrı inceleme ekranı olarak korunur; resmî baz okuyucu değildir.
- Additive migration: `f6b1c2d3e4f5`. Önceki sütun/veriler/indexler ve C1 fixture/concurrency/CI değişiklikleri korunur. İçeriği değişen yerel paket yeniden oluşturulur; yayın/deploy yapılmaz.

### API

- `POST /api/activity-reports/revisions`: `publication_id`, `organization_id`; yeni revizyon için ayrıca `report_id`, `expected_revision`.
- `GET /api/activity-reports/revisions/{revision_id}`: sabit tanım/hedefler, gerçekleşme geçmişi, farklar ve yeni yayın uyarısı.
- `POST /api/activity-reports/indicators/{report_indicator_id}/actuals`: `expected_revision`, ondalık metin `value`, `state`, `evidence`, `explanation`, `deviation`. Kanıt alanları: `title`, `locator`, `source_revision`.
- `POST /api/activity-reports/revisions/{revision_id}/approve`: gösterge gerçekleşmelerini dondurur.
- `POST /api/publications/{publication_id}/indicator-bindings`: eski snapshot gösterge satırı için açık `indicator_id` veya yeni bağımsız kimlik, zorunlu gerekçe.
- `POST /api/indicators/{period_indicator_id}/identity`: bağsız dönem kaydını mevcut kalıcı kimliğe gerekçeli açık ilişkiyle bağlar. Atanmış kimliği yeniden eşlemez.

Tüm yazma uçları oturum ve CSRF doğrulaması kullanır. Müdürlükler yalnız kendi gösterge verilerini görür/yazar; kimlik eşleme, baz seçimi ve onay strateji yetkisi gerektirir.

### Sınırlar

Faaliyet/mali gerçekleşme girişi, tam faaliyet kitabı üretimi, dönemler arası otomatik hesap/aggregation, kimlik split/merge düzeltme iş akışı ve dosya kanıt depolama bu gösterge sözleşmesi adımında açılmadı. Geçmiş baz yokken hedef uydurulmaz. GitHub CI doğrulanmadı; remote tanımlı değil. Dolu PostgreSQL migration testinin ikinci çalıştırma sorunu ayrı yerel issue'da açık tutulur.

### Nihai doğrulama

- Python 3.12, yeni boş geçici PostgreSQL DB, `pytest -q --require-postgres`: **181 passed, 0 skipped**, 18.49 saniye. Tek uyarı mevcut Starlette/httpx deprecation uyarısıdır.
- C1 concurrency testlerinin yedi senaryosu korunarak geçti. Yeni gerçekleşme yazımı ve baz değiştirme concurrency testlerinde yalnız bir işlem uygulandı; diğer işlem 409 aldı.
- SQLite/PostgreSQL additive migration testleri eski değerleri, snapshot'ı ve indeksleri korudu. SQL üzerinden yayın/kalıcı tanım değişikliği ve onaylı rapora gerçekleşme ekleme engellendi.
- Sabit hedef/sürüm, kimlik koruma, açık tarihsel eşleme, farklı yıl/birim/kurum izolasyonu, geçmiş kanıtlar, boş/sıfır, onay kapıları, CSRF/oturum, HTML kaçışları, kullanıcı hata mesajları ve içe aktarma geri almasında kimlik koruma testleri geçti.
- Python derleme, JavaScript sözdizimi, diff boşluk kontrolü ve kaynak-paket eşleşmesi başarılı. Kullanıcı akışları HTTP/HTML testleriyle kontrol edildi; canlı tarayıcıda görsel kabul testi yapılmadı.
- TestClient uygulama başlangıcı ayrı geçici DB'ye yönlendirilir; sonraki testler geliştiricinin yerel uygulama DB'sine migration uygulamaz.
- Kod, migration ve yeniden oluşturulan yerel paket commit edilmedi; deploy yapılmadı.

# Phase5 → main yayın hazırlık raporu — CIV-081

## Özet

- **DOĞRULANDI:** İnceleme tarihi 22 Ekim 2026; karşılaştırma `main` = `6b4d834b9c84af38ef862fe718009c22b86ad125`, phase5 = `81b2a613c7207aaec8d4b0506c23e7fa7e787b7c`. Main başı #50 birleşmesidir. Kaynak: fetch edilen Git ref'leri ve `git log origin/main..origin/feature/authorization-workflow-phase5`.
- **BEYAN:** Görev paketine göre canlı sürüm main `6b4d834` / release #50, canlı Alembic sürümü `c048a1b2c3d4`. Bu çalışma canlı bağlantıyla bu durumu doğrulamaz.
- **DOĞRULANDI:** Main dışında phase5 geçmişine alınmış 27 PR ve c048 sonrasında dört migration vardır. Tek şema başı `c079a1b2c3d4`; zincir `c048 → c063 → c067 → c074 → c079`. Aşağıdaki tablolar bu sabit phase5 görüntüsünü kapsar.
- **DOĞRULANDI:** [#78 / CIV-078](https://github.com/dursuncavus/civensa/pull/78) inceleme sırasında açıktır ve bu phase5 geçmişinde yoktur; **PENDING / BEKLİYOR**. İdare AR sürüm zinciri mevcut yayına dahil sayılmaz.
- **BEYAN:** CIV-078'in c079 sonrasına yeniden zincirlenmesi planlanmaktadır. **BELİRSİZ:** Son `down_revision`, yeniden zincirleme sonrası CI ve nihai yayın kapsamı. Birleşirse bu raporun migration/rollback/rehearsal kapsamı yeniden incelenmelidir.
- **DOĞRULANDI:** Bu teslimin kapsamı yalnız bu dokümandır; uygulama, migration veya workflow düzeltmesi içermez. **BELİRSİZ:** İş sahibinin yayın kararı, üretim rol denetimi, gerçek veri kabulü, bakım penceresi ve geri dönüş süresi henüz bu raporla kanıtlanmış değildir.

**DOĞRULANDI:** Kanıt etiketleri: **DOĞRULANDI** repo içeriği/Git geçmişi veya doğrudan incelenen CI kaydı; **BEYAN** görev paketinden gelen, bağımsız olarak doğrulanmayan bilgi; **BELİRSİZ** kanıtı bulunmayan sonuç veya tamamlanması gereken kontrol. Tablolarda etiket satırın bütün olgularına uygulanır; kilit ve yeniden yazma değerlendirmeleri kaynak SQL'in statik incelemesidir, üretim ölçümü değildir. Kontrol listesindeki boş kutular tamamlandı iddiası taşımaz.

## Değişiklik listesi

**DOĞRULANDI:** Envanter, `git log --merges origin/main..81b2a613` içindeki `Merge pull request` kayıtları ile GitHub birleşmiş PR başlık/açıklamalarının karşılaştırılmasıyla çıkarıldı. PR numarası CIV numarasıyla her zaman aynı değildir. Aşağıdaki her PR bağlantısı ilgili değişikliğin ayrıntı ve test kanıtına gider; PR açıklamasındaki test sonucu bu çalışmada tekrar çalıştırılmış sonuç sayılmaz.

### PP

| Etiket | PR / CIV | Kullanıcıya yansıyan değişiklik |
| --- | --- | --- |
| DOĞRULANDI | [#51](https://github.com/dursuncavus/civensa/pull/51) / CIV-051 | İlk yükleme kitabının kurum özetlerinde kaynak aritmetiği, kapsam/eşleme sınırı ve belirsizlik ayrı gösterilir; isim eşleme kontrolü iyileşir. |
| DOĞRULANDI | [#54](https://github.com/dursuncavus/civensa/pull/54) / CIV-054 | Strateji PP kılavuzuna gerçek kitap verisinden yerel ortamda üretilen 18 ekran görüntüsü ve tekrar üretim aracı eklenir. |
| DOĞRULANDI | [#55](https://github.com/dursuncavus/civensa/pull/55) / CIV-055 | PP eksikleri, kabul kanıtları ve kalan öncelikler dokümante edilir; tek başına ürün davranışını değiştirmez. |
| DOĞRULANDI | [#56](https://github.com/dursuncavus/civensa/pull/56) / CIV-056 | Aynı Word önizlemesinin eşzamanlı uygulanması serileşir; izlenen metin değişiklikleri ve iki satırlı yıl/değer başlıkları daha güvenilir ayrıştırılır. |
| DOĞRULANDI | [#57](https://github.com/dursuncavus/civensa/pull/57) / CIV-057 | PP ekranları, bağlantılar ve yazma işlemleri seçili dönemi taşır; yazmada açık dönem kimliği gerekir. |
| DOĞRULANDI | [#59](https://github.com/dursuncavus/civensa/pull/59) / CIV-059 | Yanlış eklenen uygun taslak gösterge/boş kart kaldırılabilir; değer, kalıcı kimlik ve onay/yayın geçmişi olan kayıtlar korunur. |
| DOĞRULANDI | [#60](https://github.com/dursuncavus/civensa/pull/60) / CIV-061 | Faaliyet eşleştirme kuyruğu alt program, kart ve katalog eksiklerini ayrı gösterir; eksik bağlantı varken hazır demez. |
| DOĞRULANDI | [#61](https://github.com/dursuncavus/civensa/pull/61) / CIV-060 | PP inceleme ve yayın ekranlarında Türkçe durum, TSİ zaman ve işlem sahibi görünür. |
| DOĞRULANDI | [#63](https://github.com/dursuncavus/civensa/pull/63) / CIV-065 | Müdürlük geçmişi ve eşleştirme CSV geçmişinde Türkçe olay/aktör/TSİ gösterimi tamamlanır; geri alınan işlem doğru etiketlenir. |
| DOĞRULANDI | [#65](https://github.com/dursuncavus/civensa/pull/65) / CIV-064 | PP hataları alan/kayıt ve düzeltme adımını Türkçe verir; başarısız formda denenen değerler korunur. |
| DOĞRULANDI | [#66](https://github.com/dursuncavus/civensa/pull/66) / CIV-066 | Farklı Word önizlemelerinin ortak müdürlük oluşturma/uygulama ve geri alma işlemleri kurum kilidiyle serileşir. |
| DOĞRULANDI | [#68](https://github.com/dursuncavus/civensa/pull/68) / CIV-067 | Teknik hazır sonucu ile gerçek PP yayın kararı ayrılır; dönem/içerik bağlı, aktör ve kanıt içeren manuel teyit geçmişi eklenir. |
| DOĞRULANDI | [#70](https://github.com/dursuncavus/civensa/pull/70) / CIV-069 | Güncel program/alt program/müdürlük ara toplamları kaynakla karşılaştırılır; ekran, donmuş Word/PDF ve yayın kapısı aynı hesabı kullanır (PP-16). |
| DOĞRULANDI | [#71](https://github.com/dursuncavus/civensa/pull/71) / CIV-071 | Word içe aktarma ve dönem kopyalama genel kitap bölümleri, tablolar ve görselleri taşır; tamamlanma manifesti eksikleri gösterir. |
| DOĞRULANDI | [#72](https://github.com/dursuncavus/civensa/pull/72) / CIV-072 | Strateji Müdürü onaylı PP paketini gerekçeyle düzeltmeye açabilir; düzeltme, yeniden gönderim ve bağımsız onay yolu kullanılır. |
| DOĞRULANDI | [#73](https://github.com/dursuncavus/civensa/pull/73) / CIV-073 | PP Kaynak Karşılaştırması kaynak konumu, güncel değer, fark ve karar gerekçelerini gösterir; aynı kapsam güvenli CSV ile indirilir. |
| DOĞRULANDI | [#75](https://github.com/dursuncavus/civensa/pull/75) / CIV-076 | PP yayınlarında güncel/önceki sürüm, düzeltme gerekçesi ve son yayından sonraki değişiklik uyarısı görünür. |

### AR

| Etiket | PR / CIV | Kullanıcıya yansıyan değişiklik |
| --- | --- | --- |
| DOĞRULANDI | [#62](https://github.com/dursuncavus/civensa/pull/62) / CIV-062 | AR eksikleri, birleşmiş kanıtlar ve kalan öncelikler raporlanır; raporun durum sayıları yazıldığı tabana aittir. |
| DOĞRULANDI | [#64](https://github.com/dursuncavus/civensa/pull/64) / CIV-063 | Gösterge gerçekleşmesine PDF/XLSX kanıt dosyası, sürümlü değişmez saklama ve çok kaynaklı form eklenir; eski sürümler indirilebilir. |
| DOĞRULANDI | [#74](https://github.com/dursuncavus/civensa/pull/74) / CIV-075 | AR bölümleri için PDF indirme eklenir. |
| DOĞRULANDI | [#76](https://github.com/dursuncavus/civensa/pull/76) / CIV-074 | Birim AR gönderim/iade/bağımsız onay/gerekçeli yeniden açma akışı, sabit onaylı sürümler ve bunlardan idare konsolidasyonu eklenir; eksik birim onayı idare dondurmayı engeller. |
| DOĞRULANDI | [#77](https://github.com/dursuncavus/civensa/pull/77) / CIV-077 | Son gerçekleşme açık gösterilir, geçmiş yeni→eski sıralanır; rapor rozetleri ve daha yeni PP yayınıyla salt okunur karşılaştırma eklenir. |

### İç Kontrol

| Etiket | PR / CIV | Kullanıcıya yansıyan değişiklik |
| --- | --- | --- |
| DOĞRULANDI | [#79](https://github.com/dursuncavus/civensa/pull/79) / CIV-079 | Altı aylık izleme dönemi, müdürlük girişi, Strateji iade/onayı, gerekçeli yeni revizyon ve Word/Excel izleme raporları eklenir; onaylı geçmiş korunur. |

### Auth/workflow

| Etiket | PR / CIV | Kullanıcıya yansıyan değişiklik |
| --- | --- | --- |
| DOĞRULANDI | [#67](https://github.com/dursuncavus/civensa/pull/67) / CIV-068 | Hesabın rol/müdürlük değişikliğinde gerekçeyle kapatılıp yeni kişisel hesap açılması politikası kullanıcı yönetiminde açıklanır; PP durum raporu güncellenir. |

**DOĞRULANDI:** PP yeniden açma (#72), AR birim kararları (#76) ve İç Kontrol kararları (#79) da yetki/iş akışı davranışı içerir; toplam 27 benzersiz PR sayımında yukarıdaki ürün alanında bir kez listelenmiştir. Kaynaklar ilgili PR'lar ve `app/pp_reopen_routes.py`, `app/ar_unit_workflow_service.py`, `app/internal_control_monitoring_service.py` dosyalarıdır.

### Ops

| Etiket | PR / CIV | Kullanıcıya/operatöre yansıyan değişiklik |
| --- | --- | --- |
| DOĞRULANDI | [#52](https://github.com/dursuncavus/civensa/pull/52) / CIV-052 | Basılı PP 2027 ilk yüklemesi için varsayılan salt okunur plan, korumalı uygulama ve ayrı sahip runbook'u eklenir; yüklemenin gerçekleştiği anlamına gelmez. |
| DOĞRULANDI | [#53](https://github.com/dursuncavus/civensa/pull/53) / CIV-053 | Testler iki CI parçasında yalıtılmış PostgreSQL işçileriyle çalışır; yalnız doküman/Markdown PR'ları normal doğrulamadan hariç tutulur. |
| DOĞRULANDI | [#58](https://github.com/dursuncavus/civensa/pull/58) / CIV-058 | Ön baskı 2027 verisi için izlenebilir köken, yedek ve şema koşullu ayrı temizleme planı/uygulama ve yerel yedek provası eklenir; normal migration temizleme yapmaz. |

## Migration zinciri

**DOĞRULANDI:** `migrations/versions` altındaki bütün dosyaların `revision/down_revision` ilişkisi ve main→phase5 dosya farkı incelendi. C048'in bütün ardılları aşağıdaki dört satırdır; sıra dosya adındaki sayıya göre değil `down_revision` bağına göredir. `python -m alembic heads` → yalnız `c079a1b2c3d4 (head)`; `python -m alembic history -r c048a1b2c3d4:head` aynı zinciri gösterir. Bu komutlar DB'ye bağlanmaz; yerel araç sürümü Alembic 1.16.5 / SQLAlchemy 2.0.43'tür, ürünün sabitlenmiş bağımlılıklarıyla migration çalıştırma veya CI yerine geçmez.

| Etiket | Sıra / revision ← önceki | Dosya ve değişen nesneler | Downgrade ve veri koruması | Büyük tablo yeniden yazma / kilit |
| --- | --- | --- | --- | --- |
| DOĞRULANDI | 1. `c063a1b2c3d4` ← `c048a1b2c3d4` | [c063a1b2c3d4_activity_indicator_evidence.py](../../migrations/versions/c063a1b2c3d4_activity_indicator_evidence.py): yeni `activity_evidence_files` (gerçekleşme/gösterge/kaynak/sürüm, dosya adı, SHA-256, **file_data binary**, aktör/zaman), `activity_evidence_freezes` (rapor revizyonu, manifest, hash); FK, sürüm tekilliği/kontrolü ve gerçekleşme indeksi. PostgreSQL `civ063_immutable()` ve iki tabloda UPDATE/DELETE engeli. | Var. İki tablodan herhangi biri doluysa reddeder; boşsa tablolar ve fonksiyon kaldırılır. Statik olarak boşluk şartıyla veri kaybetmez; kontrol öncesi açık tablo kilidi yoktur, eşzamanlı yazma altında güvenli olduğu kanıtlanmamıştır. TRUNCATE engeli bu migration'da yoktur. | Mevcut satırlara UPDATE/backfill veya mevcut büyük tabloda ALTER yok; yeni tablo/indeks oluşturur. Mevcut FK hedeflerinde DDL ilişki kilitleri olabilir; üretim bekleme süresi ölçülmedi. |
| DOĞRULANDI | 2. `c067a1b2c3d4` ← `c063a1b2c3d4` | [c067a1b2c3d4_release_confirmations.py](../../migrations/versions/c067a1b2c3d4_release_confirmations.py): yeni `release_confirmations` (dönem/madde/içerik hash'i, confirmed/revoked kararı, aktör/ad, gerekçe, kanıt, zaman), dönem indeksi, FK ve karar kontrolü. PostgreSQL `civ067_immutable()` ile UPDATE/DELETE/TRUNCATE engeli. | Var. Teyit geçmişi varsa reddeder; boşsa tablo/fonksiyon kaldırılır. Boşluk şartıyla korumalıdır; kontrol öncesi açık tablo kilidi yoktur, eşzamanlı yazma riski vardır. | Mevcut veri yeniden yazılmaz; yeni tablo/indeks. FK hedeflerinde DDL ilişki kilitleri olabilir; üretim süreleri bilinmiyor. |
| DOĞRULANDI | 3. `c074a1b2c3d4` ← `c067a1b2c3d4` | [c074a1b2c3d4_ar_unit_workflow.py](../../migrations/versions/c074a1b2c3d4_ar_unit_workflow.py): yeni `ar_unit_workflow_events` (belge/revizyon, geçiş, gerekçe, aktör/zaman, içerik olay imleci, payload/hash), belge indeksi/tekillik/geçiş kontrolleri. Mevcut `ar_section_contents` tablosuna nullable `copied_from_approval_id INTEGER REFERENCES ar_unit_workflow_events(id)` ekler. `civ074_immutable()` ile yeni olay tablosunda UPDATE/DELETE/TRUNCATE engeli. | Var. Olay tablosuna ACCESS EXCLUSIVE kilit alır; olay veya null olmayan kopyalama kökeni varsa reddeder. Boş yeni yapıda sütun/tablo/fonksiyon kaldırılır; eski payload/hash yeniden yazılmaz. `ar_section_contents` boşluk kontrolü öncesinde ayrıca kilitlenmez; yazmalar durdurulmadan güvenli varsayılmaz. | Nullable/defaultsuz sütun ekleme heap yeniden yazımı gerektiren bir backfill içermez; ancak `ALTER TABLE ar_section_contents` ACCESS EXCLUSIVE kilidiyle yoğun tabloda bekleyebilir. Yeni FK/DDL de kilit alabilir. Gerçek tablo büyüklüğü ve süre ölçülmedi. |
| DOĞRULANDI | 4. `c079a1b2c3d4` ← `c074a1b2c3d4` | [c079a1b2c3d4_ic_monitoring.py](../../migrations/versions/c079a1b2c3d4_ic_monitoring.py): yedi yeni tablo: `ic_monitoring_periods`, `ic_monitoring_batches`, `ic_monitoring_period_events`, `ic_monitoring_events`, `ic_monitoring_notes`, `ic_monitoring_targets`, `ic_monitoring_entries`. Dönem/yıl/yarıyıl/son tarih/kapatma, birim sahipliği, hedef eylem, olay revizyonu/snapshot/aktör, durum/oran/açıklama/neden/kanıt ve katkı notu alanları; FK/indeks/tekillik/alan kontrolleri, plan başına tek açık dönem için kısmi unique index. Yedi `civ079_*` fonksiyonu: immutable, period_guard, event_guard, entry_guard, note_guard, period_event_guard, target_guard. Dönem dışındaki altı tabloda UPDATE/DELETE engeli, tüm yedisinde TRUNCATE engeli, dönemde geçiş/DELETE ve ilgili INSERT korumaları. | Var. Yedi tablonun tümüne ACCESS EXCLUSIVE kilit alır; herhangi birinde veri varsa reddeder. Yalnız tümü boşken ters sırada tabloları ve yedi fonksiyonu kaldırır; dolu izleme geçmişini atmaz. | Mevcut plan/import tablolarını yeniden yazmaz/ALTER etmez; yeni tablo ve indeksler. FK hedeflerinde DDL ilişki kilitleri olabilir. Çalışma zamanındaki plan/dönem/paket satır kilitleri migration backfill'i değildir. |

**BELİRSİZ:** Bu dört migration'ın gerçek üretim hacminde kilit beklemesi, işlem süresi, disk/WAL gereksinimi ve rollback süresi ölçülmemiştir. Yeni tablo oluşturmak kilitsiz geçiş garantisi vermez. Özellikle c074 için bekleyen uzun işlemler ve bakım penceresi provada ölçülmelidir.

### Rehearsal kapsamı ve boşlukları

| Etiket | Kontrol | İncelenen davranış / karar için sınır |
| --- | --- | --- |
| DOĞRULANDI | Tetikleme | [release-rehearsal.yml](../../.github/workflows/release-rehearsal.yml) yalnız main hedefli PR ve `workflow_dispatch` kabul eder; aynı repo kodu koşulu vardır. CIV-081 phase5 hedefli olduğundan bu rehearsal otomatik koşmaz. |
| DOĞRULANDI | Yedek seçimi | [ops/release_rehearsal.py](../../ops/release_rehearsal.py) main'deki başarılı `Daily verified database backup` koşusundan tek, süresi dolmamış artifact seçer; koşu/manifest için en çok 48 saat ve dosya adı/boyutu/SHA-256 kontrolü ister. |
| DOĞRULANDI | Geri yükleme | PostgreSQL 18 yerel disposable servisine `pg_restore --exit-on-error --single-transaction --no-owner --no-privileges`; geri yüklenen public tablo sayımları ve Alembic sürümleri manifestle birebir karşılaştırılır. Localhost:5432 dışı URL ve migration override reddedilir. |
| DOĞRULANDI | Dört migration | `get_current_head()` tek başı bulur, sabit revision listesi kullanmaz. Yedek c048'deyse ilk `alembic upgrade head` dört satırın tamamını sırayla kapsar. Her iki yükseltmeden sonra DB sürümü `[head]` olmalıdır; ikinci koşu tablo sayımlarını/sürümü değiştiremez. |
| DOĞRULANDI | Uygulama başlangıcı | Ayrı smoke sürecinde production ayarları, geçici oturum sırrı, güvenli cookie ve `DEMO_SEED=0`; `TestClient(app)` lifespan'ı açılır ve `/login` için 200 aranır. `app/main.py::lifespan` ayrıca upgrade çağırır. Önceden var olan public tablolarda satır azalışı hata verir; `ROW_LOSS_ALLOWLIST` boştur. |
| DOĞRULANDI | Başlangıç sürümü boşluğu | Betik yedeğin mutlaka c048'de olmasını şart koşmaz; manifest ile eşitliği arar. Yedek daha ileri sürümdeyse bazı migration'lar tekrar uygulanmadan atlanır. Yayın kanıtında başlangıç sürümü ayrıca kaydedilmelidir. |
| DOĞRULANDI | İçerik ve geri dönüş boşluğu | Tablo sayımı/sürüm karşılaştırması var; satır içerikleri, dosya baytları/hash'leri, sequence değerleri, onaylı payload bütünlüğü, downgrade ve eski uygulama uyumluluğu karşılaştırılmaz. İkinci upgrade migration gövdelerini yeniden çalıştırmaz; başta no-op kalmasını kontrol eder. |
| DOĞRULANDI | Yetki ve ürün boşluğu | Restore owner/grant'leri taşımaz; disposable servis kullanıcısı ayrı kısıtlı runtime değildir ve `MIGRATION_DATABASE_URL` özellikle yasaktır. Dolayısıyla üretim rol ayrımı/trigger bypass denetimi kanıtlanmaz. Kimlik doğrulamalı PP/AR/İç Kontrol senaryoları, indirme ve PP-16 gerçek veri kabulü smoke kapsamında yoktur. |
| DOĞRULANDI | Hacim boşluğu | Kilit/bakım süresi, kapasite sınırı ve kurtarma hedefleri için ayrı kabul eşiği yoktur; job timeout'u 30 dakikadır. |
| BELİRSİZ | Bu adayın gerçek yedek provası | İncelenen kod kapsamı, c079 adayının c048 yedeğiyle başarılı CI provası demek değildir. Nihai main PR'ının aday SHA'sına ait yeşil rehearsal koşusu ve özetindeki başlangıç/bitiş kanıtı ayrıca gerekir. Bu görev rehearsal başlatıp özel yedek indirmedi. |

**DOĞRULANDI:** Normal [performance-program.yml](../../.github/workflows/performance-program.yml) `docs/**` ve `**/*.md` değişikliklerini PR tetiklemesinden hariç tutar. `workflow_dispatch` iki PostgreSQL 18 test parçasını çalıştırabilir. **BELİRSİZ:** CIV-081'in nihai baş commit'ine ait yeşil CI kanıtı doküman içinden kendiliğinden çıkmaz; aynı SHA için koşu bağlantısı/sonucu PR açıklamasında ayrıca doğrulanmalıdır. Önceki PR'ların yeşil sonuçları bu kabulün yerine geçmez.

## Geri alma planı

**DOĞRULANDI:** Dört downgrade da kaynakta vardır ve yeni veri varsa geri çevirmeyi reddeder. Bu, kullanım sonrasında sıradan `alembic downgrade c048a1b2c3d4` ile geri dönülebileceği anlamına gelmez. C063/c067 boşluk kontrolünde açık tablo kilidi yoktur; bütün geri dönüş senaryolarında yazmaların durdurulması gerekir. Kaynaklar migration tablosundaki dosyalardır.

1. **BELİRSİZ — yayın öncesi gerekli:** Yayın sorumlusu bakım penceresini, yazma durdurma yöntemini, geri dönüşü başlatacak hata ölçütlerini, izin verilen veri kaybını (RPO) ve azami kesintiyi (RTO) belirlemeli. Eski uygulama artefaktı/commit'i ve sırları içermeyen yapılandırma envanteri hazır olmalı; kurtarma yedeğinin manifesti, sürümü ve geri yükleme kanıtı saklanmalı.
2. **BELİRSİZ — uygulama geri dönüşü:** Önce trafiği/yazmaları durdurup hata kanıtlarını koruma; eski kodun c079 şeması ve yeni iş akışı kayıtlarıyla uyumu ayrı restored DB'de kanıtlanırsa yalnız binary/kod geri dönüşü değerlendirilebilir. Eski `main` kodunun yeni şemada güvenli çalıştığı bu görevde denenmedi; şema fazladan sütun kabul ediyor diye iş akışı güvenli varsayılmaz.
3. **DOĞRULANDI — şema yolu:** Ters sıra `c079 → c074 → c067 → c063 → c048` olur. C079 izleme verisi, c074 birim olay/kopyalama kökeni, c067 teyit kaydı veya c063 kanıt dosyası/manifesti varsa ilgili adım reddeder. Kaydı silmek, trigger kaldırmak veya sürümü `stamp` ile düşürmek veri koruyan geri dönüş değildir.
4. **BELİRSİZ — kullanım sonrası kurtarma:** Downgrade reddi veya uyumsuzluk halinde ileri düzeltme ya da yayın öncesi doğrulanmış yedeği **ayrı boş hedefe** geri yükleme seçeneklerini sorumlu değerlendirmeli. Yedekten sonra yazılan veriler ayrı korunmadan eski yedeğe yönelmek veri kaybettirir; yeni kayıtların aktarımı/uzlaştırılması için bu raporda uygulanmış bir yöntem yoktur. RPO'yu iş sahibi kabul etmeden trafik geri açılmamalı.
5. **BELİRSİZ — yeniden açma kapısı:** Geri yüklenen sürüm/sayımlar, gerekli içerik/hash ve dosya örnekleri, roller/trigger'lar, giriş ve yetkili PP/AR/İç Kontrol işlemleri doğrulanmalı; sonra bağlantı/uygulama değişimi ayrı yetkiyle yapılmalı. [Yedek runbook'u](db-backup.md) ve [DB rol runbook'u](db-roles.md) operatör referanslarıdır; bu rapor hiçbirini canlıda yürütmez.

## Riskler

| Etiket | Risk / kanıt | Yayın kararından önce gereken |
| --- | --- | --- |
| DOĞRULANDI | **PostgreSQL'de binary veri:** c063 kanıtları `activity_evidence_files.file_data` içinde LargeBinary tutar; mevcut `app/activity_financial_models.py` mali dosyalarda da LargeBinary kullanır. `activity_evidence_service.py` mali servisin dosya başına 10 MiB sınırını paylaşır ve indirirken SHA-256 kontrol eder. Sürümleme eski dosyaları tutar. | **BELİRSİZ:** Gerçek dosya sayısı/toplam boyut, DB/TOAST/WAL büyümesi, yedek süresi ve saklama maliyeti. Kapasite ve gerçek dosya bütünlüğü örneklemesi ölçülmeli; satır sayımı aynı baytları kanıtlamaz. |
| DOĞRULANDI | **PP-16 gerçek veride yayın kapısı:** `app/program_service.py::cost_reconciliation/publication_checks` güncel ara toplamları ve kaynak farklarını yayın kontrolüne bağlar; eksik bağlantı/tutar/doğrulama veya açıklanmamış fark engel olabilir. Eksik kaynak toplamı uyarıdır; kaynak kararı/onaylı aktarma açıklamaları korunur. | **BELİRSİZ:** Gerçek kurumun hangi satırlarda engelleneceği ve mali sorumlunun kabulü. Gerçek verinin izinli izole kopyasında kaynak→faaliyet→alt program→program→müdürlük zinciri, uyarılar ve karar gerekçeleri incelenmeli; kapıyı kapatmak için tutarlar sessizce düzeltilmemeli. |
| DOĞRULANDI | **İlk veri yükleme sırası:** `scripts/first_load_live.py::HEAD` tam `c048a1b2c3d4`; hedef ve yedek şeması kontrolü farklı revision'ı reddeder. [Ayrı canlı ilk yükleme runbook'u](../first-load/live-runbook.md) main `6b4d834` / c048 tabanını şart koşar. Phase5 uygulama başlangıcı şemayı head'e yükseltir. | **BELİRSİZ:** İlk yükleme tamamlandı mı, yayın öncesi mi yapılacak? Mevcut aracı yükseltme sonrasında aynen çalıştırmak reddedilir. Ya ayrı onaylı ilk yükleme c048 aşamasında tamamlanıp yeni yedek/prova alınmalı ya da sonraki şema için ayrı uyarlama görevi kararlaştırılmalı. İlk yükleme/ön baskı temizliği bu yayının migration adımı değildir. |
| DOĞRULANDI | **Yetki koruması:** Rehearsal kısıtlı runtime rolünü sınamaz; c063 dosya tablolarında migration düzeyinde TRUNCATE trigger'ı yoktur. [PP yayın kontrol listesi](release-checklist.md) PP-19 üretim rol kanıtını ayrı tutar. | **BELİRSİZ:** Üretim owner/runtime ayrımı, etkin trigger'lar ve gerçek grant'ler. Yetkili operatörün ayrı denetimi gerekir; bu rapor canlı DB'ye bağlanmaz. |
| DOĞRULANDI | **Kilit ve işletim:** c074 mevcut `ar_section_contents` üzerinde ALTER yapar; uygulama lifespan'ı migration çalıştırır. Dolu yeni tablolar downgrade'ı engeller. | **BELİRSİZ:** Hacimle ölçülmüş bakım/geri dönüş süresi ve dağıtım sırasında eşzamanlı yazma planı. |
| DOĞRULANDI | **Kapsam ve kabul:** `release_service.py` teknik hazır yanıtını tam yayın onayından ayırır; D1–D8, PP-19, PP-24, operations ve owner teyitleri vardır. AR-12 idare sürüm zinciri #78'de bekliyor. | **BELİRSİZ:** Resmî kitap/Word/PDF düzeni, gerçek kullanıcı kabulü ve #78 olmadan yayın kapsamının yeterliliği. Eski gap raporlarında kalan “bu PR/birleşme bekliyor” ifadeleri güncel Git birleşme kaydının yerine kullanılmamalı. |

## Yayın öncesi kontrol listesi

- [x] **DOĞRULANDI:** Main ve phase5 karşılaştırma SHA'ları sabitlendi; 27 benzersiz birleşmiş PR alanlara ayrıldı.
- [x] **DOĞRULANDI:** C048 sonrasındaki dört dosya zincire dahil; tek head c079; #78 PENDING olarak ayrıldı.
- [x] **DOĞRULANDI:** Rehearsal kodunda restore, iki upgrade, head/sayım kontrolü ve app lifespan/login smoke kapsamı incelendi; boşluklar kaydedildi.
- [ ] **BELİRSİZ:** CIV-081 nihai PR baş SHA'sında CI yeşil; yalnız doküman filtresi varsa o dal/SHA için `Performance program validation` elle çalıştırılıp sonuç PR'a bağlanmalı.
- [ ] **BELİRSİZ:** Nihai yayın adayı için main/phase5 ref'leri yeniden alınmalı; yeni PR/migration gelmişse envanter güncellenmeli. #78 dahil edilecekse c079 sonrası zincir, tek head ve yeni downgrade/rehearsal kapsamı yeniden doğrulanmalı.
- [ ] **BELİRSİZ:** İlk yükleme durumu ve c048 ile yayın sırası iş sahibi/operatör tarafından kayda geçirilmeli; ayrı runbook için ayrı işlem yetkisi korunmalı.
- [ ] **BELİRSİZ:** Nihai main PR aday SHA'sında taze doğrulanmış c048 yedeğiyle Release migration rehearsal yeşil olmalı; yedek koşusu, başlangıç sürümü, son head ve sayım özeti bağlanmalı. Başlangıç değiştiyse hangi migration'ların gerçekten koştuğu belirtilmeli.
- [ ] **BELİRSİZ:** Binary dosya/payload/hash bütünlüğü, sequence'ler, hacim ve kilit süreleri izole kopyada ayrıca kontrol edilmeli; `/login` dışı yetkili PP/AR/İç Kontrol smoke yapılmalı.
- [ ] **BELİRSİZ:** PP-16 gerçek veri farkları ve kaynak uyarıları Mali Hizmetler/Strateji tarafından gerekçeleriyle kabul edilmeli; D1–D8 ve resmî Word/PDF/PP-24 kabulü kaydedilmeli.
- [ ] **BELİRSİZ:** PP-19 gerçek runtime/owner ayrımı ve yeni tablo/trigger yetkileri yetkili operatörce kanıtlanmalı; manuel teyitler güncel içerik hash'ine bağlı olmalı.
- [ ] **BELİRSİZ:** Yazma durdurma, geri dönüş tetikleri, sorumlu, RPO/RTO, eski kod uyumu veya ayrı hedefe restore planı prova ile kabul edilmeli.
- [ ] **BELİRSİZ:** İş sahibi, bekleyen #78 dahil kapsamı ve kalan riskleri değerlendirip isim/tarih içeren yayın kararı vermeli; merge/deploy ayrı yetkili işlem olarak yürütülmeli.

## Açık sorular

1. **BELİRSİZ:** Bu yayın #78 olmadan c079'da mı kalacak, yoksa CIV-078'in yeniden zincirlenmiş ve yeşil CI'lı hali dahil mi edilecek?
2. **BELİRSİZ:** Ayrı ilk gerçek PP yüklemesi tamamlandı mı? Tamamlanmadıysa c048 zorunluluğuyla yayın sırasını kim ve hangi kanıtla kabul edecek?
3. **BELİRSİZ:** Son uygun backup/rehearsal koşuları hangileri; nihai adayın başlangıcı gerçekten c048 mi, kilit/restore süresi ne kadar?
4. **BELİRSİZ:** PP-16'nın gerçek veride ürettiği engel/uyarıların sahipleri kim; kaynak çelişkileri için hangi onaylı gerekçeler var?
5. **BELİRSİZ:** PostgreSQL binary dosya büyümesi için kapasite/saklama bütçesi, dosya bütünlüğü kontrolü ve kurtarma hedefleri nedir?
6. **BELİRSİZ:** Üretimde runtime ayrı ve kısıtlı mı; yeni nesnelerin owner/default grant'leri ile c063 TRUNCATE yetkisizliği kim tarafından kanıtlanacak?
7. **BELİRSİZ:** C079 şemasında eski main uygulamasına dönmek denenmiş mi? Dolu yeni tablolar downgrade'ı reddettiğinde ileri düzeltme/restore kararını kim verecek ve yedek sonrası yazılar nasıl korunacak?
8. **BELİRSİZ:** D1–D8, PP-19, PP-24, operations ve owner kapılarının isimli/tarihli güncel kabul kayıtları nerede; nihai yayın ve bakım penceresi sorumlusu kim?

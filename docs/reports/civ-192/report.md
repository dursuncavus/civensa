# CIV-192 — Gösterge gerçekleşmeleri Excel içe aktarma

## Akış

Strateji, mevcut `/activity-reports` ekranındaki **Excel'den içe aktar** alanında 2026 rapor revizyonunu seçer ve tüm müdürlükleri içeren ana XLSX dosyasını yükler. Yalnız `veriler` sayfası, normalleştirilmiş başlıklarla okunur; diğer sayfalar dikkate alınmaz. Dosya iki kez okunur: `data_only=True` sayısal önbellek için, `data_only=False` formül kaynağını belirlemek için. Formüller hiçbir zaman hesaplanmaz. Zorunlu başlık eksikliği veya yinelenmesi Türkçe hata verir; açıklama ve yalnız bağlam olan Strateji oranı sütunları isteğe bağlıdır. Lead’in verdiği `PERFORMANS \nGÖSTERLERİ` yazımı, `GÖST.\nBİRİMİ` ve satır sonları korunmuş başlık fixture’ı test edilir. Çeyrek başlıkları yıl ve çeyrek numarasıyla tanınır; parantezli ay aralığı yok sayılırken Q4 toplamı ve performans değerlendirme sütunları ayrı kalır.

Önizleme actual kaydı oluşturmaz. Müdürlük ve gösterge adları, Q1–Q4, yöntem, Strateji oranı, yıllık değer seçenekleri, mevcut değer, durum ve seçim birlikte gösterilir. Her satır başlangıçta **Aktarma** seçilidir. Strateji eşleşmeyi ve sayı yorumunu seçerek onaylar; uygulanacak değer istemciden alınmaz, saklanan önizlemeden türetilir. Önizleme 24 saat geçerlidir.

Uygulama yalnız onaylanmış satırları `activity_contract_service.save_actual` üzerinden `verified` durumunda yeni revizyon olarak yazar. Önceki kanıtlar ve sapma bilgileri korunur. Excel açıklaması doluysa kullanılır; boş, yalnız boşluk veya sütun yoksa önceki gerçekleşme revizyonunun açıklaması korunur. Yeni kanıt eklenmez. Kanıtsız kayıt, onaylı/geçmiş rapor, eşzamanlı değişiklik veya mevcut iş akışı kuralı nedeniyle servis reddederse satır ayrı işlem noktasıyla geri alınır ve Türkçe neden sonuçta gösterilir. Sapma açıklamasının gönderimi engelleme davranışı ekran girişiyle aynıdır; servis dışında ek bir onay istisnası açılmaz.

## Eşleştirme ve durumlar

Müdürlükler `structure_service` içindeki yıl adı ve iptal edilmemiş Kurum Yapısı kararlarının önceki/sonraki adlarıyla çözülür. Birleşme bağlantıları devralan kitap müdürlüğüne ulaşmayı sağlar. İçe aktarıcıda ad değişikliği tablosu yoktur; kaydı olmayan ad farkı için Kurum Yapısı kaydı gerekir.

Gösterge adları Türkçe İ/ı, harf durumu, boşluk ve noktalama bakımından normalleştirilir; baştaki SH/PG kodları çıkarılır. Anahtar, çözülmüş müdürlük ve gösterge adıdır. PG sütunu eşleştirme için kullanılmaz. Tam tek eşleşme **Eşleşti** olur. Diğer adlar aynı müdürlük kümesinde `SequenceMatcher` benzerliği en az 0,60 olan en fazla üç adayı **Onay gerekiyor** durumuyla sunar. Birden fazla tam ad eşleşmesi de seçim gerektirir. Aday yoksa **Eşleşmedi** olur. Aynı göstergeyi ikinci kez isteyen tam eşleşme veya uygulamadaki ikinci seçim **Hata** olur.

**Eksik**, sayısal yıllık değeri hesaplanamayan satırdır; sıfır olarak yazılmaz. **Aktarılmadı**, Stratejinin seçim yapmadığı satırdır. **Değişmedi**, mevcut gerçekleşme değeriyle aynı olduğundan yeni revizyon yazılmayan satırdır. **Yazıldı**, yeni gerçekleşme revizyonu oluşturulan satırdır. Önizlemedeki eksik/hatalı/eşleşmeyen satırlar başka satırların uygulanmasını engellemez.

## Yıllık değer ve ölçek

[Lead takip yorumu](https://github.com/dursuncavus/civensa/pull/438#issuecomment-6735990228), ilk görev paketindeki yıllık sütun varsayımını düzeltir: **`2026 YILI TOPLAMI` gerçekleşme değildir**. Elle girilmiş 0/1/2 veya formül önbelleği 0 olsa da yalnız **Strateji oranı** olarak gösterilir ve hiçbir değer/fallback hesabına katılmaz.

Yıllık gerçekleşmede sayısal `2026 YILI 4. ÇEYREK GERÇEKLEŞEN TOPLAMI` önceliklidir; sıfır da geçerli sayıdır. Bu toplam sayısal değilse TOPLA yalnız dört çeyrek sayısalken toplar; KÜMÜLATİF, `kÜMÜLATİF`, `T.KÜMÜLATİF` ve aksansız yazımlar Q4'ü kullanır. Q4 toplamı ile yöntem sonucu ikisi de mevcut ve farklıysa **Onay gerekiyor** olur; iki sayı ve kaynak kuralı gösterilir. Strateji hangi kaynağın aktarılacağını seçer. Seçim yoksa yazılmaz; yalnız gösterge/ölçek onayıyla kaynak otomatik belirlenemez. Seçilen kaynak, ölçek ve değer audit sonucunda izlenir.

Metin hücreler (`%` dahil), boşluklar ve sayısal önbelleği olmayan formüller sayı değildir. Formül ve sayısal önbelleğinin bulunup bulunmadığı önizlemede saklanır/gösterilir. Önceki oran temelli önizlemeler sürüm kontrolüyle 409 alır; yeniden yükleme zorunludur. Böylece eski saklanmış önizleme de yanlış sütundan yazamaz.

Excel birimi Oran içeriyorsa ve yıllık değer ≤ 1 ise kitap birimindeki yüzde işareti/yüzde ifadesi veya Oran birimiyle birlikte 1'den büyük doğrulanmış hedef, yüzde ölçeği kabul edilir. Dönüşüm **×100 (oran kesirden yüzdeye)** olarak gösterilir ve ancak bu yorumu seçerek onaylayınca uygulanır. Ölçek belli değilse özgün ve ×100 değerlerinin ikisi de sunulur; Strateji birini seçer. Sayılar Türkçe biçimlenir.

## Saklama, migration ve denetim

Bir eklemeli migration eklendi: `c192a1b2c3d4`, ebeveyni `c185a1b2c3d4`; tek Alembic head korunur. `actual_imports`, rapor revizyonunu, yükleyeni, SHA-256'yı, ayrıştırılmış önizlemeyi ve tek uygulama sonucunu tutar. Ham Excel hiçbir zaman saklanmaz. Dolu tablo için downgrade veri kaybını önlemek üzere reddedilir.

Mevcut `ARFinancialImport`, farklı `ARDocument` modeline bağlı ve malî satırlarla ilişkilidir. `ICImport` iç kontrol içindir; `BudgetOperation` bütçe talimatı alanlarını zorunlu tutar. Genel adlı `ImportBatch` ise PP kitabı yükleyicisinin müdürlük planı, tanım/kitap yazımı ve geri alma geçmişidir; mevcut ekran ve uygulama yolları onu PP içeriği olarak yorumlar. Bu kayıtları kullanmak PP yükleyicilerine tür ayrımı ve yeni korumalar eklemeyi gerektirir; görev bu yükleyicilere dokunmayı yasaklar. Bu nedenle ayrı rapor revizyonu önizleme tablosu kullanıldı.

Uygulama önizleme kaydını kilitler; tekrar gönderimde saklanan sonucu döndürür. Her yeni uygulama için tek `actual_import_apply` audit kaydı dosya SHA-256, kullanıcı, durum sayıları, Excel satırları, gösterge ve yazılan actual revizyon kimliklerini içerir. Aynı dosyanın yeniden yüklenmesi, aynı değerler için yeni actual revizyonu üretmez. Geri alma, ekranın mevcut yeni gerçekleşme revizyonu mekanizmasıyla yapılır; geçmiş kayıtlar silinmez.

## Doğrulama

- Yalnız sentetik çalışma kitapları ve geçici yerel PostgreSQL 16 ve 18 sunucuları kullanıldı; gerçek çalışma kitabı veya gerçek 2026 gerçekleşmesi kullanılmadı.
- `tests/test_actual_import.py`: tam/yakın/eşleşmeyen ad, aynı PG kodları, ikinci gösterge talebi, ad değişikliği/birleşme, TOPLA/KÜMÜLATİF, boş Q4, metin hücre, sayısal sıfır önceliği, yüzde ve belirsiz ölçek, onaysız satırın yazılmaması, idempotent tekrar, servis reddi, eşzamanlı actual değişikliği, önizleme süresi, başlıklar ve üç uçta 403.
- Önizleme sonrası `actual_revisions` sayısının değişmediği; uygulama sonrası sabit tanımların ve yayın içeriğinin aynı kaldığı; kanıtın korunduğu test edildi.
- `tests/test_actual_import_migration.py`: gerçek upgrade/boş downgrade/upgrade ve dolu tabloda veri koruyan ret; tek head.
- Lead/Codex takip düzeltmeleri sonrası PostgreSQL 18 üzerinde 48 test geçti: `tests/test_actual_import.py`, `tests/test_actual_import_followup.py`, `tests/test_actual_import_migration.py`, `tests/test_fr_guide_capture.py`, `tests/test_audit_display.py`, `tests/test_storage_column_inventory.py`. Takip düzeltmelerinin 21 senaryosu ayrıca geçti; gerçek başlık dizgesi/ters sütun sırası, Q4–Q4 toplamı ayrımı, önbellekli/önbelleksiz formüller, Strateji oranının 0/1/2 değerlerinin yazılmaması, çelişen yıllık değerlerde kaynak seçimi ve ×100, boş/eksik açıklamanın korunması ve eski önizleme reddi kapsandı. Noktalı SH.1.2 / PG.1.3 ve P.G.2.1 önekleri ayrıca regresyon testleriyle doğrulandı. İptal edilen yapı adı, belirsiz ölçeğin iki seçeneği, önbelleksiz formül ve aday sahipliğinin işlem içindeki yazma reddi ayrıca kapsandı.
- İlgili mevcut sözleşme, kanıt, Türkçe hata ve kılavuz testleri çalıştırıldı; kılavuz etiket sözleşmesi geçti. Yeni head nedeniyle mevcut migration testlerinin head beklentileri güncellendi. Eski operasyon şemasına sabit test yardımcısına boş yardımcı önizleme tablosu eklendi; operasyon kodu ve şema sabitlemesi değiştirilmedi. İlgili temizleme senaryosu yeniden geçti.
- Tam PostgreSQL takımı yerelde `python -m pytest -q --require-postgres -n 4 --dist loadfile --max-worker-restart=0` ile, CI’da PostgreSQL 18 üzerinde iki shard ile çalıştırılır. Güncel head için test, güvenlik ve altyapı sonuçları [PR #438 kontrollerinde](https://github.com/dursuncavus/civensa/pull/438/checks) izlenebilir; bu kayıt, tamamlanmamış bir çalışmayı başarılı saymaz.
- `tests/test_activity_reports_design.py`: 21 test geçti; eski ekran sözleşmesi yalnız yeni Excel bloğu dışında birebir korunur, yeni bloğun Strateji görünürlüğü ayrıca doğrulanır. 1440/1024/620/390 genişliklerinde yerleşim ve kontrast kontrolleri geçti.
- Audit kodlarının Türkçe etiketleri ve SHA/JSON alanlarının base64 taşımayan depolama sınıflandırması tamamlandı; ilgili 7 test geçti.
- Yerel tam çalışma: 4011 geçti, 47 başarısız. Bu çalışma test modüllerini düzeltmelerden önce yüklediğinden 17 eski form/adaya bağlı test beklentisini içeriyordu; son odaklı takımlar bunları yeniden geçti. Audit etiketi ve depolama envanteri için iki eksik de giderilip yeniden geçti. Diğer 28 hata ortam kaynaklıydı: PostgreSQL 18 zorunlu 12 prova (yerel sunucu 16), `postgres` kullanıcı adının `postgresql` yanıt metniyle çakıştığı altı gizlilik kontrolü ve yönetilen Chrome tarafından engellenen 10 `file://` testi. PostgreSQL 18 ve ayrı test kullanıcı adıyla bu 18 veritabanı/prova kontrolü yeniden çalıştırıldı ve tamamı geçti. Tarayıcı kısıtını aşmak için uygulama/operasyon korumaları değiştirilmedi; tam doğrulama PostgreSQL 18 ve standart Chromium kullanan PR CI üzerinden izlenir.
- Taban entegrasyonu sonrasında PostgreSQL 18 üzerinde `tests/test_actual_import.py`, `tests/test_actual_import_followup.py`, `tests/test_actual_import_migration.py`, `tests/test_fr_guide_capture.py`, `tests/test_fr_rehearsal_harness.py`, `tests/test_activity_reports_design.py`, `tests/test_audit_display.py`, `tests/test_storage_column_inventory.py` birlikte **78 geçti**. Birleşmiş kılavuzun bölüm sırası, iki yer tutucunun kaldırılması, uygulama etiketleri ve CIV-193 prova beklentileri birlikte yeşil.
- `compileall` ve `git diff --check` geçti.

Gerçek çalışma kitabı okunmadı; lead’in sağladığı başlıklar ve yapısal formül örneği sentetik dosyada sınandı. Gerçek gerçekleşmeler ve Kurum Yapısı kayıtlarının belediyedeki kapsamı sentetik testlerden doğrulanamaz. Gerekli başlık veya yapı eşleşmesi bulunmazsa kullanıcıya hata/eşleşmeyen satır gösterilir; tanımlar veya hedefler değiştirilmez. Aday/yayın iş akışına geçmiş raporların kapalı yazma yolları ve `ACTIVITY_REFERENCE_SUCCESSORS=False` korunmuştur. Hedef dala PR merge işlemi, deploy veya canlı veritabanı bağlantısı yapılmadı. Kullanıcının açık talimatıyla `feature/authorization-workflow-phase5` dalı, CIV-193 / #442 sonrasındaki `c9a9a95da84ab6883d1f9f0762bdc271200ae84f` tabanından çalışma dalına merge edildi. Kılavuzdaki iki çatışma, `Faaliyet sonuçları` bölümü `Yardım` üstünde korunarak ve kalan Excel yer tutucusu FR5 metniyle değiştirilerek çözüldü; kılavuz testi her iki değişikliği birlikte doğrular.

## Sentetik ekran görüntüleri

- [Önizleme](preview.png)
- [Kaynak ve ölçek seçimleri](preview-selections.png)
- [Uygulama sonucu](result.png)

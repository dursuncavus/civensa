# PP yayın kontrol listesi — CIV-067 / PP-22

Bu liste D1–D8 kabulünü ve yayın kapılarını tek kanıt kaydında birleştirir.
Bir test dosyasının varlığı, yeşil CI veya kayıt sayısı belediyenin kabulü değildir.
Başlangıçta hiçbir manuel madde onaylanmış sayılmaz. Açık ürün eksikleri bu görevle
kapanmaz; ilgili kabul maddesinde gerçek kanıt bulunana kadar bekler.

`GET /api/release/readiness?period_id=ID` eski `status`, `version`, `checks`,
`warnings`, `migration`, `checked_at` alanlarını korur. Üst düzey `status=ready`
yalnız **teknik** kapsamdır; yeni `scope=technical` bunu açıklar. Tam karar
`release.status` alanındadır. `/operations?period_id=ID` iki bölümü ayrı gösterir:
**Teknik hazırlık** ve **PP yayın kontrol listesi**.

Tam karar: herhangi bir otomatik engelde **Engelli**; otomatikler geçip manuel
madde eksikse **Elle onay bekliyor**; yalnız tüm otomatikler ve tüm güncel manuel
teyitler tamamlandığında **Hazır**. Her satırda durum, kontrol kaynağı, kanıt,
sorumlu/gerekli onay ve eksikse Türkçe sonraki adım bulunur. JSON ve ekran canlı
seçili dönem değerlendirmesidir; bu belge bir üretim uygunluk beyanı değildir.

## Teknik kontroller

Kaynak: `app/main.py::release_readiness`; durum her değerlendirmede **Geçti / Engelli**.
Sorumlu: teknik sorumlu; kayıt/dönem düzeltmelerinde Strateji. Aşağıdaki kanıtların
gerçek değerleri `release.automatic[].evidence.observed` içinde yer alır.

| Madde | Kontrol | Kanıt | Sorumlu / onay |
| --- | --- | --- | --- |
| `database` | Mevcut uygulama bağlantısında sağlık kontrolü | Backend, durum, gecikme | Teknik sorumlu |
| `migration_head` | DB sürümü tek Alembic başına eşit | Gerçek/beklenen revision | Teknik sorumlu |
| `period_active` | Seçili dönem etkin | Dönem kimliği, yıl, durum | Strateji dönem sorumlusu |
| `departments_present` | Müdürlük sayısı > 0 | Sayı | Strateji kurum sorumlusu |
| `indicators_present` | Dönemin gösterge sayısı > 0 | Sayı | İlgili Müdürlük Müdürü |
| `activities_present` | Dönemin faaliyet sayısı > 0 | Sayı | İlgili Müdürlük Müdürü |
| `activity_mappings_complete` | PP-08: alt program/kart/katalog eksikleri yok | Ortak eşleştirme hizmetinin eksik türü sayaçları | Strateji / Müdürlük |
| `no_orphan_activities` | Müdürlüksüz faaliyet yok | Yetim kayıt sayısı | Teknik sorumlu |
| `no_orphan_indicators` | Müdürlüksüz gösterge yok | Yetim kayıt sayısı | Teknik sorumlu |
| `no_duplicate_active_department_accounts` | Bir müdürlükte birden fazla etkin Müdür yok | Çakışan müdürlük ve hesap sayıları | Strateji hesap sorumlusu |
| `workflow_schema_present` | Gönderim ve bildirim tabloları var | İki tablo için varlık sonucu | Teknik sorumlu |

## Otomatik yayın kapıları

Durum **Geçti / Engelli**. `app/program_service.py::publication_checks` hem
`POST /report-builder/publish` hem hazırlık yanıtı tarafından kullanılır.
Kurallar kopyalanmaz; hazırlık okuması yayın, onay veya denetim olayı oluşturmaz.
Satırlar ilgili dönemin müdürlüklerine göre çoğalır; kapsam yoksa o müdürlüğün
diğer denetimleri yayın yolundaki gibi kapsam kapısında durur.

| Madde | Kontrolün kaynağı / kapsamı | Kanıt | Sorumlu / onay |
| --- | --- | --- | --- |
| `publication:scope:ID` | `DepartmentScope`; dönem kapsamı açıkça belirtilmiş | Dönem, müdürlük, eksik kapsam mesajı veya boş hata listesi | Strateji kurum sorumlusu |
| `publication:data:ID` | `validate_department`; gösterge/kart/katalog ilişkileri, gelecek yıl finansmanı, personel/SGK, ekonomik hücreler, boş/sıfır ve toplam mutabakatı; veri içeren kapsam dışı birimler | Ortak doğrulayıcının tüm Türkçe hataları | İlgili Müdürlük Müdürü ve mali kontrol sorumlusu |
| `publication:approval:ID` | Zorunlu kapsamdaki müdürlüğün `Submission.status=approved` olması; mevcut gönderim/Strateji karar akışı | Gönderim kimliği/durumu/revizyonu; varsa aynı revizyonun onay olayı ve onaylayan kişi; eksik onay mesajı veya boş hata listesi | Strateji inceleme sorumlusu |
| `publication:sections` | `ReportSection` varlığı | Dönem ve eksik genel bilgi mesajı veya boş hata listesi | Strateji yayın sorumlusu |
| `publication:catalogue` | `OfficialActivity` varlığı | Dönem ve eksik katalog mesajı veya boş hata listesi | Strateji kurum sorumlusu |

Varlık kontrolleri resmî kaynak kapsamının veya sayfa düzeninin doğruluğunu
kanıtlamaz; aşağıdaki D1/D5/D7/PP-24 kabulü bunun içindir. Gönderim onayı da D3
kullanıcı kabulünün yerine geçmez.

## Manuel kabul ve yayın onayları

Tüm bu satırlar zorunludur. Başlangıç durumları aşağıdadır; yalnız güncel içerik
için kanıtlı teyit **Geçti** olur. Sorumlu kişi/gerekli onay kanıt metninde
adlandırılır; kaydı giren Strateji kullanıcısının kimliği/adı ayrıca sistemce saklanır.

| Madde | Başlangıç durumu | Kontrol / gerekli kanıt | Kaynak | Sorumlu / gerekli onay |
| --- | --- | --- | --- | --- |
| D1 — Kurulum, içe aktarma ve elle giriş | Elle onay bekliyor | Resmî kaynak dosya/sürüm ve tablo kapsam manifesti; ilk dönem, elle giriş, kopyalama, kalan Word çeşitleri ve eşzamanlı yükleme bulguları | `test_word_import.py`, `test_pp_import_submit_ready.py`, `test_master_data.py`; PP-02/03/05 | Strateji veri sorumlusu |
| D2 — Müdürlük girişi ve düzeltmesi | Elle onay bekliyor | Seçili dönemde giriş, boş/sıfır, taslak koruma, taslak kaldırma ve onay sonrası düzeltme yolu için kullanıcı kabul tutanağı | `test_indicator_update.py`, `test_pp_period_context.py`, `test_draft_removal.py`; PP-12/13/14/26 | İlgili Müdürlük Müdürü ve Strateji |
| D3 — İnceleme, iade ve yeniden onay | Elle onay bekliyor | Gönderim, gerekçeli iade, düzeltme, yeniden gönderim, bağımsız onay; bütçe dışı onaylı hata düzeltmesi kabul kanıtı | `test_submission_workflow.py`, `test_review_errors.py`; PP-06/07/14 | Strateji inceleme sorumlusu |
| D4 — Değişmez ve hash içeren yayın | Elle onay bekliyor | Donmuş yayın sürüm/hash kaydı, değişmezlik ve başarısız yeniden yayın koruması; PP-19 ayrıca zorunlu | `test_publication_gates.py`, `test_db_roles.py` | Teknik sorumlu ve Strateji |
| D5 — Kaynak karşılaştırması ve toplamlar | Elle onay bekliyor | Kaynak konumları, çelişki kararları, genel toplamlar ve program/alt program/müdürlük ara toplam mutabakatı | `test_source_conflicts.py`, `test_institution_summary_evidence.py`; PP-09/10/11/16 | Mali hizmetler kontrol sorumlusu |
| D6 — Türkçe hata ve kurtarma | Elle onay bekliyor | Kullanıcıyla ne/nerede/eylem, form değerlerini koruma ve başarılı yeniden deneme | `test_pp_errors_forms.py`; PP-17/18 | Strateji kullanıcı kabul sorumlusu |
| D7 — Kitap, Word ve PDF | Elle onay bekliyor | Bölüm sırası, tablo kapsamı ve büyük dosyada Word/PDF kabul tutanağı; PP-24 ayrıca zorunlu | `app/book_export.py`, `test_program.py` | Strateji yayın sorumlusu |
| D8 — Teknik olmayan Strateji yönetimi | Elle onay bekliyor | Kurum/dönem/hesap yönetimi, rol-müdürlük transfer politikası, eşleştirme ve hata kurtarma kabulü | `test_master_data.py`, `test_activity_mapping_gaps_ui.py`; PP-01/08/23 | Strateji birim yöneticisi |
| PP-19 — Üretim rol doğrulaması | Doğrulanmadı | Yetkili üretim sorumlusunun tarihli runtime/owner ayrımı, yetki denetimi, yedek/geri dönüş kanıtı | [DB rolleri](db-roles.md), `test_db_roles.py` | Üretim yetkilisi ve teknik sorumlu |
| PP-24 — Resmî PP kitap/Word kabulü | Elle onay bekliyor | Resmî PP referansı, kabul edilen Word/PDF sürümü, büyük kitap düzen/sayfalama sonucu, kabul eden kişi | [PP denetimi](../reports/civ-008-performance-programme-audit.md), PP-24 | Strateji yayın sorumlusu ve iş sahibi |
| `operations` — Güvenlik, yedek ve geri dönüş | Elle onay bekliyor | Son commit CI bağlantısı/sonucu; giriş sınırı, oturum ve menü kanıtı; gerçek yedekten geri dönüş provası | `.github/workflows/performance-program.yml`, `db-roles.md`; PP-19/20/21 | Teknik sorumlu |
| `owner` — İş sahibi yayın onayı | Elle onay bekliyor | Tüm kapılar ve açık PP bulguları incelenmiş, kapsamı belirli yayın kararı ve iş sahibinin isimli/tarihli onayı | Bu kontrol listesi | Strateji birim yöneticisi / iş sahibi |

**PP-19 canlı gözlemi UNKNOWN / Doğrulanmadı kalır.** Uygulama canlı üretim rolüne
bağlanmaz. Manuel PP-19 teyidi varsa yalnız yetkilinin sunduğu kanıt geçmiştir;
`release.live_role_verification` alanı ve ekrandaki canlı gözlem satırı otomatik
başarı iddia etmez. Yerel PostgreSQL rol testi üretim kanıtı değildir. PP-24 veya
iş sahibi onayı test sonucu üzerinden otomatik tamamlanmaz.

## Teyit kaydı ve geçerlilik

Strateji `/operations` formundan madde, karar, gerekçe, kanıt/onay girer. Sistem
aktör kimliği, o andaki adı ve UTC zamanı ekler; ekranda TSİ gösterilir. API:
`POST /api/release/confirmations?period_id=ID`; mevcut oturum ve CSRF kuralları
geçerlidir. JSON alanları: `item_id`, `decision` (`confirmed` / `revoked`),
`reason`, `evidence`, `context_sha256`. Son alan aynı dönemin hazırlık yanıtından
alınır; eski içerikle gönderim 409 ve Türkçe yeniden inceleme adımı üretir.

Teyitler `release_confirmations` tablosuna **yalnız eklenir**; aynı işlemde
`audit_log` içine `release_manual_confirmation` olayı yazılır. İsim/zaman
istemciden alınmaz. Düzeltme/geri çekme yeni olaydır; güncel içerikte en büyük
kayıt kimliği geçerlidir. Önceki kanıtlar geçmişte görünür, düzenleme/silme API'si
yoktur. ORM ve SQLite/PostgreSQL tetikleyicileri UPDATE/DELETE işlemlerini;
PostgreSQL ayrıca TRUNCATE işlemini reddeder.

Bağlam özeti dönem/yıl/durum/şablon, kitap verisi, onay durumu, hesapların
yetki alanları, donmuş yayın sürümleri, uygulama sürümü, şema revision'ı ve teknik
sonuçları kapsar. Bunlar değişince eski teyitler güncel onay sayılmaz. Üretim
altyapısı veya referans belge gibi sistem dışı değişiklikler otomatik gözlenmez;
sorumlu kişi yeni geri çekme kaydı ekleyip yeni kanıtla yeniden teyit etmelidir.
Gerçek kullanıcı kabulü olmadan kanıt yazmak eksik ürünü tamamlamaz.

## Migrasyon ve doğrulama kanıtı

Yeni tek migrasyon: `c067a1b2c3d4_release_confirmations.py`,
`down_revision = c063a1b2c3d4`. Mevcut migrasyonlar değiştirilmez. Tablo doluysa
downgrade reddedilir; onay/denetim geçmişi kaybedilmez. Canlıya uygulanması bu
görevin kapsamında değildir.

Regresyon kanıtı: `tests/test_release_checklist.py` teknik/tam kapsam ayrımı,
her manuel kapı, ortak yayın engelleri, eski JSON anahtarları, yetki/CSRF,
eski içerik reddi, 1280/390 px Chromium görünümü ve gerçek form gönderimini;
`tests/test_release_confirmations_migration.py` dolu mevcut baştan yükseltme,
atomik denetim kaydı, ORM/doğrudan SQL değişmezliği ve veri koruyan downgrade
reddini SQLite/PostgreSQL üzerinde doğrular. Mevcut
`tests/test_release_readiness_migration_head.py` ve
`tests/test_publication_gates.py` sözleşmeleri korunur. Gerçek çalıştırma sonuçları
ve son commit CI bağlantısı görev PR'ında kaydedilir.

**PP-22:** Dar teknik kapsam adlandırıldı; D1–D8, yayın kapıları ve manuel
onayların kanıt/sorumlu listesi API ve ekrana eklendi. Uygulama/test çözümü bu
PR'dadır; birleşme bekler. Bu durum tam PP yayınının hazır olduğu anlamına gelmez.

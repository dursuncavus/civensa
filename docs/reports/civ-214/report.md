# CIV-214 — 2027 düzeltilmiş kitapla değiştirme

Kaynak: `2027-performans-programi_SONN_duzeltilmis.idml`, SHA256 `66d9d692bd9c324f6d4f492eca4d75721f28c80e248a971a2a331adf1170bf6f` (D-465). Katalog farkı D-466 ile aynı işlemde değiştirilir. Canlı bağlantı, dağıtım ve birleştirme yapılmadı.

## Yerel gerçek kitap provası

Geçici PostgreSQL 16 / şema `c197a1b2c3d4`: boş veritabanı → mevcut yükleyiciyle ONAYLI → salt okunur plan → `--apply` (sentetik yerel yedek, terminal onayı taklit). Plan çıktısı [plan-output.txt](plan-output.txt), sonuç ve makbuz özeti [rehearsal.json](rehearsal.json).

```text
programs: 28 → 28
subprograms: 38 → 38
official_activities: 291 → 290
activity_responsibilities: 291 → 290
indicator_values: 1578 → 1578
indicators: 263 → 263
activity_cost_values: 5172 → 5220
activity_catalogue_links: 286 → 290
activities: 291 → 290
economic_values: 1340 → 1340
department_cost_values: 204 → 204
submissions: 34 → 34
report_cards: 64 → 64
Reddedilen: 0
```

Katalog farkları (plan çıktısında satır satır):

- Alt program metni: Makine İkmal "yıllık ortalama 11[0] → 11[9] adet" (gerekçe ve amaç); Deneysel Geliştirme gerekçesinde "AÇIKLAMA:" sonrasına boşluk (D-465).
- Resmî faaliyet: Özel Kalem 0006 kalkar; Makine İkmal 0002–0005 yeniden sıralanır; İşletme ve İştirakler 0011–0015 → 0001–0005.
- Sorumlu birim bağları bu faaliyetlerle birlikte değişir (291 → 290).

Uygulama sonucu: `approved-load-replace-apply`; makbuz `decision: D-466` ile kataloğun önce/sonra sayım ve özetlerini taşır. `approved_book_provenance(2027)` yeni kitabın SHA256'sını verir.

## Doğrulama

- `tests/test_replace_approved_2027.py` (37 test): gerçek düzeltilmiş kitapla atomik değiştirme, plan çıktısında katalog farkları, bağımsız taze yüklemeyle bütün 2027 tablolarının (katalog dahil) içerik eşitliği, 2026/2028 hash koruması, ikinci uygulamanın reddi; dönemler arası katalog bağı için üç ret durumu (2028 faaliyetinden 2027 resmî faaliyete bağ, 2028 faaliyetinin 2027 alt programı, 2027 faaliyetinden 2028 resmî faaliyete bağ), her birinde bütün satır hash'leri ve sequence değerleri eşit; mevcut bütün ret ve operatör korumaları; üçüncü müdürlükte hata sonrası tam geri alma.
- Yerelde geçti: `test_replace_approved_2027.py`, `test_first_load_live.py`, `test_clear_preprint_2027.py` (170); `test_book_to_load_docx_geometry`, `test_first_load_2026`, `test_first_load_checklist`, `test_first_load_dryrun`, `test_institution_summary*` ve diğerleri (124).
- Yerelde çalışmayan, CI'ya kalan: tarayıcı testleri (Python Playwright yok), `psycopg2` isteyen 11 test ve `pg_dump` sürümü gerektiren 2 yedek provası. Bu 13 test phase5 tabanında da aynı ortam hatasını veriyor; kod farkından değil.
- Gerçek canlı verinin ONAYLI ile eşitliği ve sahibin BEYAN'ı doğrulanmadı; araç bunları uygulama anında mekanik korumalarla denetler. Gerçek üretim yedeği kullanılmadı.

## Kapsam

- `app/first_load_sources.py`: 2027 kitabı son düzeltilmiş dosyaya sabitlendi.
- `scripts/replace_approved_2027.py`: katalog farkı artık engel değil, planda Türkçe listelenir (`~` metin değişikliği, `-` kaldırılacak, `+` eklenecek). 2027 kataloğu (program, alt program, resmî faaliyet, sorumlu birim) içerik satırlarından sonra çocuktan ebeveyne silinir; yükleyici kataloğu yalnız düzeltilmiş kitaptan kurar. Yeni ret: başka döneme ait satırın 2027 içeriğine bağı ya da 2027 satırının başka dönem içeriğine bağı. Son denetim katalog dahil bütün 2027 tablolarını taze yüklemeyle karşılaştırır.
- `app/program_service.py` `approved_book_provenance` (salt okunur): doğrulanmış değiştirme makbuzu varsa, kaldırılan ONAYLI kataloğunun eski `catalogue_create`/`catalogue_link` denetimleri değerlendirme dışı kalır (son eski yükleme işaretinden sonrakiler okunur). Makbuz yoksa davranış aynıdır.
- Runbook "2027 düzeltilmiş kitap ile değiştirme" bölümü güncellendi. Yazma yolları, migrasyonlar ve bağımlılıklar değişmedi.

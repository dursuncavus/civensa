# CIV-092 — Açık depo hazırlık incelemesi

İnceleme: **24 Ekim 2026 (İstanbul)**. Temel dal:
`feature/authorization-workflow-phase5`, inceleme tabanı `e1e66468539a2708bf69d9b5ea52e8d5c8ced628`.
**Hazırlık tamamlanması görünürlüğü değiştirme izni değildir.** Canlı veritabanına
bağlanılmadı; mevcut Actions artifact'leri indirilmedi, değiştirilmedi veya
silinmedi; depo ayarları değiştirilmedi. PR birleştirilmedi.

## Yayın öncesi sahibin ele alacağı bulgular

| Konum | Görünür olacak içerik | Öneri |
| --- | --- | --- |
| `.github/workflows/db-backup.yml` tarafından önceki çalışmalarda üretilen `civensa-db-backup-*` Actions artifact'leri | Görev paketine göre 16 eski, 90 günlük **şifresiz canlı dump**; hesaplar, parola özetleri ve iş akışı geçmişi. Bu sayı görev paketinin tespitidir; bu incelemede artifact API'si/dosya içeriği okunmadı. | **move**: sahibi güvenli özel arşiv/erişim ve mevcut artifact'lerin akıbetini ayrıca kararlaştırmalı. Bu PR bunları silmez. Yeni şifreleme ve 30 gün ayarı eski dosyaları korumaz. |
| `tests/fixtures/first_load/source/2027-performans-programi_16102026_duzeltilmis 2.idml` | Gerçek Büyükçekmece 2027 kitabı; kişi/görevli isimleri, kişisel Gmail iletişim adresi, belediye sistem bağlantıları, `Spreads/*.xml` içindeki macOS kullanıcı/harici disk yolları ve kişi adlı görsel kaynakları; gömülü XMP/üretici/asset kimlikleri. | **move**: özgün tasarım dosyasını özel fixture deposuna taşıma; açık test için ayrıca temizlenmiş sentetik sürüm hazırlama. Telif, portre ve metadata incelemesi gerekir. Burada değiştirilmedi. |
| `tests/fixtures/first_load/source/pp2027_print_d3.idml` | Aynı gerçek kurum verileri; kişisel e-posta, yerel dosya yolları, kişi adlı fotoğraf bağlantıları, tasarım/görsel metadata ve belediye hizmet uçları. | **move**: özgün dosyayı özel fixture deposunda tutma; kamusal içerik beyanı kişisel metadata/yerel yollar için onay sayılmaz. |
| `tests/fixtures/pp2027_source_no_media.docx` | Gerçek kurum kitabı, kişi adları, belediye sistem URL'leri; `docProps/core.xml` içinde gerçek yazar/son düzenleyen; `word/document.xml` görsel açıklamalarında Windows kullanıcı ve kişi adlı fotoğraf yolları. “no_media” metadata'yı temizlemiyor. | **redact**: yazar, görsel açıklamaları, yerel yollar ve kişi bilgileri temizlenmiş kopya; kaynak özgün dosyası için **move**. |
| `tests/fixtures/first_load/pp2027_print_d3.docx` | Gerçek müdürlük, gösterge, faaliyet ve bütçe içerikleri; Word metadata'sı python-docx olarak görünüyor. | **keep**: kurum rapor verisinin kamusal olduğu sahibi tarafından BEYAN edilmiş; kişi/iletişim ve belge hakkı kontrolü sonrası. Kaynak IDML'nin gizli metadata'sı ayrıca ele alınmalı. |
| `tests/fixtures/pp2027_baseline.json`, `tests/fixtures/first_load/name_map.json`, `tests/fixtures/first_load/pp2027_print_d3.gen_report.json`, `tests/fixtures/first_load/SHA256SUMS` | Gerçek kurumun ayrıştırılmış rapor/alan eşlemeleri, üretim sayımları ve kaynak bütünlük kimlikleri. | **keep**: kamusal rapor verisi beyanına dayanır; hesap/veritabanı yedeği sayılmaz. Kaynak fixture'ler sonradan değiştirilirse özetler/eşlemeler ayrı görevde güncellenmeli. |
| `docs/screenshots/civ-025/director-authorizations.png`, `docs/screenshots/civ-025/strategy-users.png` | İnsan biçiminde ad/soyad ve test e-posta hesapları; OCR'da kişi isimleri okunuyor. E-posta alanları `.invalid`, gerçek kişi oldukları bu dosyalardan doğrulanamıyor. | **redact**: adları açıkça sentetik rol adlarıyla değiştirerek yeniden üretme; köken doğrulanmadan gerçek kişi olmadığı varsayılmamalı. |
| `docs/lead/HIERARCHY.md`, `docs/lead/BACKUP_LEAD.md`, `docs/lead/PROJECT_RULES.md`, `docs/lead/README.md` | Depo sahibinin adı, rolü ve kişisel/operasyonel değerlendirmeler; iç çalışma talimatları. | **move**: özel operasyon deposuna ayırma; kamusal katkı kuralları için daha sonra temiz kopya. Yasaklı dizin bu PR'da değiştirilmedi. |
| `docs/lead/DECISIONS.md`, `docs/lead/STATE.md`, `docs/lead/tasks/*` (aşağıda tek tek) | İç karar, durum ve görev paketleri; operasyon, bütçe, canlı süreç ve PR kimlikleri. | **move**: kamusal olma gereği yok; sahibi/lead ayrı görevde karar vermeli. |
| Git commit author/committer metadata'sı; mevcut dallar/etiketler/PR konuşmaları | Sahibin adı ve kişisel Gmail adresi geçmiş commit'lerde mevcut; bot/noreply ve yerel yazar kimlikleri de görünür. Dosya redaksiyonu commit metadata'sını kaldırmaz. | **redact**: sahibi kişisel adresin görünürlüğünü açıkça değerlendirmeli; gerekirse ayrıca koordine edilmiş geçmiş temizliği. Bu görev geçmişi yeniden yazmaz. |

**Telefonlar:** İzlenen metin, Office XML/ilişkileri, PDF metni ve 107 PNG'nin
OCR taramasında doğrulanmış gerçek telefon numarası bulunmadı. Telefon alanı ve
“Cep Telefonu” envanter satırları gerçek iletişim numarası değildir. IDML içindeki
gömülü görsellerin tüm piksel içeriği OCR'dan geçirilmedi; özgün IDML dosyaları
bu nedenle de **move** önerisinde. OCR ve desen araması insan incelemesinin yerine
geçmez; aşağıdaki muhafazakâr öneriler bu belirsizliği içerir.

**İç adresler ve altyapı kimlikleri:** Güncel izlenen dosyalarda gerçek
`*.onrender.com`, `*.neon.tech`, Render `srv-`/`dpg-` veya Neon `ep-`/proje
kimliği bulunmadı. Render/Neon ürün isimleri ve secret **adları** gizli değer
değildir. `.local`, `testserver`, `localhost`, `127.0.0.1`, `.example` ve `.invalid`
örnekleri test/yerel adreslerdir. Gerçek belediye URL'leri iki IDML ile
`pp2027_source_no_media.docx` içinde bulunur: `bcekmece.bel.tr` hizmetleri,
KEOS/BELNET, 3B kent, afet/ABİS ve yaşam rehberi; kurum verisi BEYAN'ına rağmen
servis haritası açığa çıkar, dolayısıyla kaynak dosyalara **move/redact** önerilir.
Yerel kullanıcı/disk yolları da iç konum bilgisidir; yukarıda ayrıca kaydedildi.

## Tam geçmiş secret taraması

Yerelde tüm uzak dal referansları salt okunur `git fetch` ile alındı; gitleaks
**8.30.0**, workflow'daki aynı SHA256 doğrulaması ve mevcut `.gitleaks.toml` ile
`git . --log-opts="--all --full-history" --ignore-gitleaks-allow --redact=100`
çalıştırıldı. Sonuç: **3 bulgu, çıkış 1**. Değerler paylaşılmadı; rapor repo
dışında geçici dizinde ve Secret alanları `REDACTED`. Bu sonuç otomatik olarak
“gerçek secret” veya “zararsız” sınıflandırması değildir.

| Dosya / tarihsel commit | Satırlar / kural | Öneri |
| --- | --- | --- |
| `tests/test_activity_contract_errors.py` @ `8b9430710ceb813236646d4ec3c366393d299f6c` | 62, 193; `generic-api-key` | **redact**: #85 sahibi test dizgisi/gerçek secret ayrımını doğrulamalı; gerçekse önce rotasyon, sonra ayrı kapsamda geçmiş temizliği. Dosya bu tabanda yok ve #85 nedeniyle değiştirilemez. |
| `tests/test_storage_upload_limits.py` @ `8b9430710ceb813236646d4ec3c366393d299f6c` | 115; `generic-api-key` | **redact**: aynı sahip incelemesi; mevcut açık PR dosyasına veya `.gitleaks.toml` istisnalarına bu görevde müdahale edilmedi. |

`security.yml` içinde tam geçmiş işi yalnız `workflow_dispatch` ile çalışır;
checkout `fetch-depth: 0`, tarama `--all --full-history`, `--redact=100` ve
`--ignore-gitleaks-allow` kullanır. Sadece redakte JSON raporu 7 gün yüklenir.
Bulgu varsa iş kırmızı kalır. Güncel PR commit aralığının secret kontrolü ayrıdır;
tam geçmişteki bu üç bulgu, açık yayın öncesi kalan sahip işidir.

## İş akışları, loglar ve GitHub yüzeyi

| Konum | Görünür olacak içerik | Öneri |
| --- | --- | --- |
| `.github/workflows/db-backup.yml` ve geçmiş çalışma log/özet/artifact'leri | Eski şifresiz dump/manifest; tablo adları/sayımları, Alembic ve kaynak zaman kimlikleri. | **move**: mevcut artifact/logları sahibi ayrı değerlendirmeli. Yeni artifact'te yalnız iki `.age` dosyası, 30 gün saklama; private identity bu işte yok. |
| `.github/workflows/preprint-backup-rehearsal.yml`, `ops/preprint_rehearsal.py` ve geçmiş `CIV058_RESULT_JSON`/step summary | Gerçek yedekten kurum/aktör/batch kimlikleri, kaynak SHA/zaman, tablo/satır sayımları, kaynak şema şekilleri; değerler veya kullanıcı adı basılmıyor. | **redact**: tarihsel log/özetlerin özel operasyon erişimine taşınmasını sahibi değerlendirmeli. Yeni restore yalnız elle; PR yoluyla gerçek yedek erişimi kaldırıldı. |
| `.github/workflows/release-rehearsal.yml`, `ops/release_rehearsal.py` ve geçmiş step summary | Gerçek yedeğin tablo isimleri ve önce/sonra sayımları; çalışma/commit kimlikleri. | **redact**: tarihsel özetleri ayrıca gözden geçirme; yeni iş yalnız elle ve şifre çözme sonrası yerel restore. |
| `.github/workflows/clear-preprint.yml` | PR test adları, sentetik kurum/hesap/rapor verileri ve olası test hata ayrıntıları. | **keep**: yalnız sentetik fixture ve işte üretilmiş geçici age anahtarı; repo secret'ı veya gerçek yedek indirme yok. |
| `.github/workflows/security.yml` | PR diff taraması; elle tam geçmiş taramasında redakte raporun dosya/commit/yazar metadata'sı. | **keep**: yalnız redakte rapor; metadata da kamusal görünürlük kararına dahil. Bulgu değerleri/log çıktısı redakte kalmalı. |
| `.github/workflows/performance-program.yml`, `ops/ci/*` | Test isimleri, traceback/annotation, koşucu bilgisi; fixture alanları başarısızlıkta loga çıkabilir. | **keep**: sentetik testler; gerçek kurum fixture'lerinin aşağıdaki önerileri ayrıca geçerli. CIV-091 dosyası/fixture'leri bu PR'da değiştirilmedi. |
| `.github/workflows/lead-docs-guard.yml` | Dal/PR numarası ve lead-docs kapsam kontrolü; PR kodunu checkout etmez. | **keep**: `pull_request_target` için bu ayrım korunmalı; repository secret referansı yok. |
| GitHub Issues/PR'lar, yorumlar, review'lar, release metinleri, eski dal/etiket içerikleri ve varsa LFS nesneleri | Dosya ağacı dışında geçmiş konuşma/ekler, isim/e-posta ve operasyon bağlantıları da görünür olabilir. | **move/redact**: sahibi yayın öncesi ayrıca incelemeli. Bu rapor bu yüzeylerin tamamını gezdiğini veya mevcut log/artifact içeriğini doğruladığını iddia etmez. |
| Repository/environment secret ve variable ayarları | Secret değerleri git dosyaları gibi yayınlanmaz; kodda kullanılan secret adları ve workflow davranışı görünür olur. | **keep**: özel anahtar yalnız manual restore adımında. Bu görev ayarları değiştirmedi; gerçek secret değerleri incelenmedi. |

## Doğrulama ve sahibin sonraki adımları

- [x] Gerçek workflow yükleme deseniyle sentetik test: sadece `.dump.age` ve
  `.manifest.json.age`, age başlığı; yüklenen dosyalarda `PGDMP` başlığı yok.
- [x] Alıcı yok/boş/geçersizse veritabanı adımından önce başarısızlık; yanlış
  identity/bozuk ciphertext kısmi şifresiz çıktı bırakmıyor.
- [x] İşte üretilmiş geçici anahtarla sentetik PostgreSQL 18 dump → şifrele → çöz
  → restore; SHA256, içerik/null, sayımlar ve Alembic bilgisi eşleşiyor.
- [x] Odaklı PostgreSQL regresyonları: `tests/test_release_rehearsal.py` ve
  `tests/test_clear_preprint_2027.py`: **104 geçti**. Şifreleme sınırı: **7 geçti**.
  Değişen beş workflow için actionlint 1.7.7: **hata yok**.
- [x] Yukarıdaki PR-job `grep` denetimi: **5 iş, sıfır eşleşme** (çıkış 1).
- [x] PR işlerinde repository secret referansı ve özel yedek indirme yolu yok.
- [x] Yeni age kurulumu sürüm + SHA256 sabitli; artifact süresi 30 gün.
- [x] Yeni tam geçmiş işi manuel ve raporu redakte.
- [ ] Son PR commit'inin GitHub CI sonucu PR üzerinde doğrulanmalı; yerel sonuçlar
  tek başına yeşil GitHub CI beyanı değildir.
- [ ] Sahibi aşağıdaki dosya önerileri ile tarihsel bulguları karara bağlamalı;
  bu PR kişi/kurum fixture'lerini, docs/lead veya yasaklı PR dosyalarını temizlemez.
- [ ] Sahibi yerelde anahtarları üretip iki secret'ı kurmalı; tam komutlar ve
  yalnız yerel restore adımları [db-backup.md](../operations/db-backup.md#sahibin-yerel-anahtar-kurulumu)
  içinde. Özel anahtar hiçbir çıktıya basılmaz, depoya yazılmaz.
- [ ] Sahibi birleştirme sonrası yeni şifreli yedeği/elle restore'u doğrulamalı ve
  eski şifresiz artifact/loglara ayrıca karar vermeli. Görünürlük değişimi ayrı iş.

PR secret denetiminin tekrarlanabilir `grep` kanıtı (eşleşme beklenmez; `grep`
çıkış 1 normaldir):

```bash
python - <<'CHECK' >/tmp/civ092-pr-jobs.jsonl
import json
from pathlib import Path
import yaml
for path in sorted(Path('.github/workflows').glob('*.yml')):
    doc = yaml.load(path.read_text(), Loader=yaml.BaseLoader)
    if not any(event in doc.get('on', {}) for event in ('pull_request', 'pull_request_target')):
        continue
    for name, job in doc['jobs'].items():
        if job.get('if') == "github.event_name == 'workflow_dispatch'":
            continue
        print(json.dumps({'file': str(path), 'job': name, 'workflow_env': doc.get('env', {}), 'definition': job}))
CHECK
grep -nE 'secrets\.|BACKUP_AGE_IDENTITY|ops\.(preprint|release)_rehearsal|gh run download' /tmp/civ092-pr-jobs.jsonl
```

## Dosya bazında tam izlenen envanter

Temel daldaki **565 dosyanın tamamı** ve bu PR'daki **5 yeni dosya**
aşağıda ayrı satırdadır; atlanan/bir dizin deseniyle gizlenen dosya yoktur.
Metinler, ZIP içindeki Office/IDML XML ve link/author metadata'sı, beş PDF'nin
metni ve 107 PNG OCR'ı incelendi. Gömülü IDML base64 görselleri, fontların piksel
şekilleri ve geçmiş GitHub artifact/log içerikleri tam içerik denetimi kapsamında
değildir. Font lisansı ve Office core metadata'sı ayrıca incelendi.

**keep** = mevcut kapsamda kalabilir; **redact** = sahibi ayrıca temizlenmiş sürüm
hazırlamalı; **move** = özgün içerik özel alanda tutulmalı. Bu öneriler burada
otomatik dosya değişikliği veya silme yapmaz. “Test/sentetik” adresler gerçek
hesap gibi değerlendirilmedi; görünür oldukları yine dosya bazında kaydedildi.
Tablodaki satır numaraları metin/OCR çıkarımına aittir; ZIP üyeleri için yukarıdaki
bileşen konumları daha güvenilirdir.

| İzlenen yol | Görünür içerik / bulgu | Öneri |
| --- | --- | --- |
| `.dockerignore` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `.env.example` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `.github/actions/setup-age/action.yml` | Workflow/action kaynağı; tetikleyici, izin, secret adları, araç/CI URL’leri; değerler değil | **keep** |
| `.github/workflows/clear-preprint.yml` | Workflow/action kaynağı; tetikleyici, izin, secret adları, araç/CI URL’leri; değerler değil | **keep** |
| `.github/workflows/db-backup.yml` | Workflow/action kaynağı; tetikleyici, izin, secret adları, araç/CI URL’leri; değerler değil | **keep** |
| `.github/workflows/lead-docs-guard.yml` | Workflow/action kaynağı; tetikleyici, izin, secret adları, araç/CI URL’leri; değerler değil | **keep** |
| `.github/workflows/performance-program.yml` | Workflow/action kaynağı; tetikleyici, izin, secret adları, araç/CI URL’leri; değerler değil | **keep** |
| `.github/workflows/preprint-backup-rehearsal.yml` | Workflow/action kaynağı; tetikleyici, izin, secret adları, araç/CI URL’leri; değerler değil | **keep** |
| `.github/workflows/release-rehearsal.yml` | Workflow/action kaynağı; tetikleyici, izin, secret adları, araç/CI URL’leri; değerler değil | **keep** |
| `.github/workflows/security.yml` | Workflow/action kaynağı; tetikleyici, izin, secret adları, araç/CI URL’leri; değerler değil; kamu doküman/GitHub veya yerel/test URL alanları | **keep** |
| `.gitignore` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `.gitleaks.toml` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `AGENTS.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `Dockerfile` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `README.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları; kamu doküman/GitHub veya yerel/test URL alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `RELEASE_NOTES_v3.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları | **keep** |
| `RELEASE_NOTES_v3_5.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları | **keep** |
| `RELEASE_NOTES_v4.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları | **keep** |
| `RELEASE_NOTES_v4_1.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları | **keep** |
| `RELEASE_NOTES_v4_2.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları | **keep** |
| `RELEASE_V5.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `alembic.ini` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri; kamu doküman/GitHub veya yerel/test URL alanları | **keep** |
| `app/__init__.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/activity_contract_routes.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/activity_contract_service.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/activity_evidence_models.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/activity_evidence_service.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/activity_financial_models.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/activity_financial_routes.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/activity_financial_service.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/activity_mapping_service.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/activity_reference_service.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/activity_report_service.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/activity_revision_reference.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/activity_sections_models.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/activity_sections_routes.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/activity_sections_service.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/ar_deviation_gate.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/ar_export.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/ar_pdf_export.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/ar_typeset_contract.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `app/ar_typeset_csv.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/ar_typeset_download.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/ar_typeset_forms.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/ar_typeset_keys.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/ar_typeset_source.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/ar_unit_workflow_routes.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/ar_unit_workflow_service.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/assurance_guards.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/assurance_models.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/assurance_routes.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/assurance_service.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/authorization_models.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/authorization_service.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/book_export.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/budget_models.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/budget_routes.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/budget_service.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `app/config.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/csv_safety.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/data_importer.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/db.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/db_privileges.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/draft_removal_service.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/economic_split_service.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/file_security.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/first_load_service.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/fonts/DejaVuSans-Bold.ttf` | Dağıtılan font varlığı ve üretici/lisans metadata’sı; kişisel uygulama verisi değil | **keep** |
| `app/fonts/DejaVuSans.ttf` | Dağıtılan font varlığı ve üretici/lisans metadata’sı; kişisel uygulama verisi değil | **keep** |
| `app/fonts/LICENSE.txt` | Üçüncü taraf font lisansı, telif sahibi/kurum adları ve kamu lisans URL’si; lisans korunmalı; kamu doküman/GitHub veya yerel/test URL alanları | **keep** |
| `app/import_service.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/internal_control_models.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/internal_control_monitoring_export.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/internal_control_monitoring_guards.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `app/internal_control_monitoring_models.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/internal_control_monitoring_routes.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/internal_control_monitoring_service.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `app/internal_control_routes.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/internal_control_service.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/legal/assurance_statements_2025.json` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/login_throttling.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/main.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `app/master_data_routes.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/master_data_service.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/models.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/numbers.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/package_models.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/package_service.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/personal_accounts.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/pp_display.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/pp_errors.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/pp_manifest.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `app/pp_reopen_routes.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/program_routes.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/program_service.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/publication_history.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/release_service.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/released_permissions.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/report_export.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/report_workflow_models.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/report_workflow_service.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/revision_workflow_models.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/revision_workflow_service.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/security.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/seed.py` | Demo kurum/rol hesapları ve `.local` e-postalar; demo başlangıç kimlik bilgisi mantığı görünür; kamu doküman/GitHub veya yerel/test URL alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni; e-posta satır 29,30 | **keep** — yalnız demo; gerçek hesap/secret ile karıştırılmamalı |
| `app/serialization.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/source_comparison_service.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/static/activity_contract_bound.js` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/static/activity_sections.css` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/static/activity_sections.js` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/static/app.css` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/static/app.js` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/static/budget.js` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `app/static/personal_accounts.js` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/static/structure.js` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/structure_service.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/template_parser.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/activity_contract_bindings.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/activity_contract_detail.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/activity_contract_error.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/activity_contract_index.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/activity_evidence_row.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/activity_financial.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/activity_financial_import.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/activity_mapping.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/activity_report.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/activity_sections_editor.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/activity_sections_index.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/ar_unit_workflow.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/ar_unit_workflow_error.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/assurance_editor.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `app/templates/assurance_slot.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/assurance_statement.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/audit.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/base.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/budget_detail.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/budget_index.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/budget_reference.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/budget_wizard.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/change_password.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/dashboard.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/department.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/draft_removal.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/economic_split.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/first_period.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/internal_control/import.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/internal_control/index.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/internal_control/monitoring.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/internal_control/monitoring_detail.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/internal_control/monitoring_notes.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/internal_control/monitoring_ours.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/internal_control/monitoring_shared.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/internal_control/our_actions.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/internal_control/plan.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/login.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/modules.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/operations.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `app/templates/pp_error.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/pp_form_fallback.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/pp_manifest.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/pp_reconciliation.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/pp_section_import.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/pp_sections.js` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/program.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/report_builder.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/review.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/source_comparison.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/structure.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/structure_wizard.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/submit_authorization_control.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/submit_authorizations.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `app/templates/users.html` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `app/templates_docx/faaliyet_raporu.docx` | Boş ürün Word şablonu; creator Civensa, gerçek kişi/iletişim saptanmadı | **keep** |
| `app/time_display.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `app/value_labels.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `check_bundle.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `docs/CIV-048-internal-control.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `docs/ar-typeset-contract.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları | **keep** |
| `docs/authorization-workflow-a1p11-recovery.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları | **keep** |
| `docs/authorization-workflow-foundation.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları | **keep** |
| `docs/authorization-workflow-phase3.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları | **keep** |
| `docs/authorization-workflow-phase4.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları | **keep** |
| `docs/authorization-workflow-phase5a.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları | **keep** |
| `docs/civ-009/README.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları | **keep** |
| `docs/civ-009/department-1012x1103.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/civ-009/department-1280x600.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/civ-009/strategy-1012x1103.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/civ-009/strategy-1280x600.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/civ-038/README.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları | **keep** |
| `docs/civ-038/financial-completeness.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `docs/civ-038/financial-entry.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/civ-038/financial-import-preview.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/civ031/README.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `docs/civ031/civ-011-activity-disagreement.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/civ031/civ-011-preview-conflicts.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/civ031/operation-detail.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/civ031/wizard-preview.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/civ044/README.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları | **keep** |
| `docs/civ044/personal-first-login.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/civ044/strategy-preview.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/civ044/strategy-retirement.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; sentetik e-posta alanı; e-posta satır 75 | **keep** |
| `docs/civ046/README.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `docs/civ046/ornek-taslak.docx` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `docs/civ046/sayfa-01.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `docs/civ046/sayfa-mali.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/confirmed-contract-fixes.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları; kamu doküman/GitHub veya yerel/test URL alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `docs/first-load/dryrun-d3.md` | İçe alma/operasyon raporu; gerçek kurum sayım/rapor örnekleri, PR/commit/işlem kimlikleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** — kamusal rapor BEYAN’ı; özel operasyon metadata’sını sahibi ayrıca değerlendirmeli |
| `docs/first-load/dryrun-printed.md` | İçe alma/operasyon raporu; gerçek kurum sayım/rapor örnekleri, PR/commit/işlem kimlikleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** — kamusal rapor BEYAN’ı; özel operasyon metadata’sını sahibi ayrıca değerlendirmeli |
| `docs/first-load/live-runbook.md` | İçe alma/operasyon raporu; gerçek kurum sayım/rapor örnekleri, PR/commit/işlem kimlikleri; kamu doküman/GitHub veya yerel/test URL alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** — kamusal rapor BEYAN’ı; özel operasyon metadata’sını sahibi ayrıca değerlendirmeli |
| `docs/integration-staging-performance-bridge.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları; kamu doküman/GitHub veya yerel/test URL alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `docs/internal-control/izleme.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `docs/issues/postgres-migration-test-repeat.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları | **keep** |
| `docs/lead/BACKUP_LEAD.md` | İç görev/karar/yönetim kaydı; operasyon ve rol bilgileri; depo sahibinin adı/kişisel rolü; kamu doküman/GitHub veya yerel/test URL alanları | **move** — özel lead kayıtları; bu PR’da dokunulmadı |
| `docs/lead/DECISIONS.md` | İç görev/karar/yönetim kaydı; operasyon ve rol bilgileri | **move** — özel lead kayıtları; bu PR’da dokunulmadı |
| `docs/lead/HIERARCHY.md` | İç görev/karar/yönetim kaydı; operasyon ve rol bilgileri; depo sahibinin adı/kişisel rolü | **move** — özel lead kayıtları; bu PR’da dokunulmadı |
| `docs/lead/PROJECT_RULES.md` | İç görev/karar/yönetim kaydı; operasyon ve rol bilgileri; depo sahibinin adı/kişisel rolü | **move** — özel lead kayıtları; bu PR’da dokunulmadı |
| `docs/lead/README.md` | İç görev/karar/yönetim kaydı; operasyon ve rol bilgileri; depo sahibinin adı/kişisel rolü | **move** — özel lead kayıtları; bu PR’da dokunulmadı |
| `docs/lead/STATE.md` | İç görev/karar/yönetim kaydı; operasyon ve rol bilgileri | **move** — özel lead kayıtları; bu PR’da dokunulmadı |
| `docs/lead/tasks/CIV-088.md` | İç görev/karar/yönetim kaydı; operasyon ve rol bilgileri | **move** — özel lead kayıtları; bu PR’da dokunulmadı |
| `docs/lead/tasks/CIV-090.md` | İç görev/karar/yönetim kaydı; operasyon ve rol bilgileri | **move** — özel lead kayıtları; bu PR’da dokunulmadı |
| `docs/lead/tasks/CIV-091.md` | İç görev/karar/yönetim kaydı; operasyon ve rol bilgileri | **move** — özel lead kayıtları; bu PR’da dokunulmadı |
| `docs/lead/tasks/CIV-092.md` | İç görev/karar/yönetim kaydı; operasyon ve rol bilgileri | **move** — özel lead kayıtları; bu PR’da dokunulmadı |
| `docs/lead/tasks/README.md` | İç görev/karar/yönetim kaydı; operasyon ve rol bilgileri | **move** — özel lead kayıtları; bu PR’da dokunulmadı |
| `docs/operations/ci.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `docs/operations/db-backup.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `docs/operations/db-roles.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları; kamu doküman/GitHub veya yerel/test URL alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `docs/operations/db-storage.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları | **keep** |
| `docs/operations/phase5-release-readiness.md` | İçe alma/operasyon raporu; gerçek kurum sayım/rapor örnekleri, PR/commit/işlem kimlikleri; kamu doküman/GitHub veya yerel/test URL alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** — kamusal rapor BEYAN’ı; özel operasyon metadata’sını sahibi ayrıca değerlendirmeli |
| `docs/operations/release-checklist.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `docs/operations/render.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları | **keep** |
| `docs/performance-activity-contract.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `docs/phase5b1-activity-reference-contract.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları | **keep** |
| `docs/reports/civ-008-performance-programme-audit.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları; kamu doküman/GitHub veya yerel/test URL alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `docs/reports/civ-008/directorate-approved-data.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/reports/civ-008/directorate-draft-workbench.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/reports/civ-008/directorate-editable-data.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/reports/civ-008/directorate-sidebar-overlap.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/reports/civ-008/finance-error.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/reports/civ-008/publication-pdf-page2.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `docs/reports/civ-008/report-builder.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/reports/civ-008/review.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/reports/civ-008/strategy-dashboard.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/reports/civ-008/strategy-sidebar-overlap.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/reports/civ-008/users.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; sentetik e-posta alanı; e-posta satır 64,67 | **keep** |
| `docs/reports/civ-014-activity-report-audit.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `docs/reports/civ-014/approval-blockers.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/reports/civ-014/approved-history.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/reports/civ-014/directorate-entry.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/reports/civ-014/evidence-error.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/reports/civ-014/modules.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/reports/civ-014/number-error.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/reports/civ-014/publication-rebase.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/reports/civ-014/report-list.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `docs/reports/civ-014/sibling-draft-loss.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/reports/civ-014/source-pilot.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/reports/civ-014/turkish-realisation.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/reports/civ-018-master-data.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları | **keep** |
| `docs/reports/civ-018/duplicate-name-error.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `docs/reports/civ-018/first-period.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/reports/civ-018/institution-structure.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `docs/reports/civ-018/subprogramme-responsibility.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `docs/reports/civ-021/ar-confirmation.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/reports/civ-021/ar-unsaved-marker.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/reports/civ-021/pp-confirmation.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/reports/civ-021/pp-unsaved-marker.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/reports/civ-033-ar-2021-audit.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları; kamu doküman/GitHub veya yerel/test URL alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `docs/reports/civ-037/completeness-view.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `docs/reports/civ-037/resource-table.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/reports/civ-037/section-editor.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `docs/reports/civ-045/strategy-programme-split.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/reports/civ-055-pp-gap-status.md` | İçe alma/operasyon raporu; gerçek kurum sayım/rapor örnekleri, PR/commit/işlem kimlikleri; kamu doküman/GitHub veya yerel/test URL alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** — kamusal rapor BEYAN’ı; özel operasyon metadata’sını sahibi ayrıca değerlendirmeli |
| `docs/reports/civ-062-ar-gap-status.md` | İçe alma/operasyon raporu; gerçek kurum sayım/rapor örnekleri, PR/commit/işlem kimlikleri; kamu doküman/GitHub veya yerel/test URL alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** — kamusal rapor BEYAN’ı; özel operasyon metadata’sını sahibi ayrıca değerlendirmeli |
| `docs/reports/civ-092-public-readiness.md` | Bu envanter; hassas değerleri tekrar etmeden dosya/commit/bulgu konumları ve öneriler | **keep** |
| `docs/reports/screenshots/civ-011/civ-011-activity-disagreement.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/reports/screenshots/civ-011/civ-011-preview-conflicts.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/screenshots/civ-025/director-authorizations.png` | Kişi biçiminde ad/soyad ve `.invalid` test e-postaları; kişi kökeni doğrulanamadı; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **redact** — açık sentetik adlarla yeniden üret |
| `docs/screenshots/civ-025/strategy-users.png` | Kişi biçiminde ad/soyad ve `.invalid` test e-postaları; kişi kökeni doğrulanamadı; kurum/ünvan/kişi biçiminde ürün veya fixture metni; e-posta satır 74,78 | **redact** — açık sentetik adlarla yeniden üret |
| `docs/screenshots/civ-027/ar-closure-note.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/screenshots/civ-027/wizard-summary.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `docs/screenshots/guide-pp-v1/01-genel-bakis-ust.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; gerçek kitaptan rapor metni örnekleri ve sentetik test hesabı; kamusal veri BEYAN’ı | **keep** |
| `docs/screenshots/guide-pp-v1/02-ilerleme-panosu.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; gerçek kitaptan rapor metni örnekleri ve sentetik test hesabı; kamusal veri BEYAN’ı | **keep** |
| `docs/screenshots/guide-pp-v1/03-mudurluk-strateji-gorunumu.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; gerçek kitaptan rapor metni örnekleri ve sentetik test hesabı; kamusal veri BEYAN’ı | **keep** |
| `docs/screenshots/guide-pp-v1/04-inceleme-kuyrugu.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; gerçek kitaptan rapor metni örnekleri ve sentetik test hesabı; kamusal veri BEYAN’ı | **keep** |
| `docs/screenshots/guide-pp-v1/05-iade-penceresi.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; gerçek kitaptan rapor metni örnekleri ve sentetik test hesabı; kamusal veri BEYAN’ı | **keep** |
| `docs/screenshots/guide-pp-v1/06-faaliyet-eslestirme.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; gerçek kitaptan rapor metni örnekleri ve sentetik test hesabı; kamusal veri BEYAN’ı | **keep** |
| `docs/screenshots/guide-pp-v1/07-kurum-yapisi.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; gerçek kitaptan rapor metni örnekleri ve sentetik test hesabı; kamusal veri BEYAN’ı; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `docs/screenshots/guide-pp-v1/08-kullanicilar.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; gerçek kitaptan rapor metni örnekleri ve sentetik test hesabı; kamusal veri BEYAN’ı; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `docs/screenshots/guide-pp-v1/09-butce-aktarma.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; gerçek kitaptan rapor metni örnekleri ve sentetik test hesabı; kamusal veri BEYAN’ı | **keep** |
| `docs/screenshots/guide-pp-v1/10-sistem-durumu.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; gerçek kitaptan rapor metni örnekleri ve sentetik test hesabı; kamusal veri BEYAN’ı | **keep** |
| `docs/screenshots/guide-pp-v1/11-denetim-gecmisi.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; gerçek kitaptan rapor metni örnekleri ve sentetik test hesabı; kamusal veri BEYAN’ı; sentetik e-posta alanı; e-posta satır 16,36 | **keep** |
| `docs/screenshots/guide-pp-v1/12-moduller.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; gerçek kitaptan rapor metni örnekleri ve sentetik test hesabı; kamusal veri BEYAN’ı | **keep** |
| `docs/screenshots/guide-pp-v1/13-giris.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; gerçek kitaptan rapor metni örnekleri ve sentetik test hesabı; kamusal veri BEYAN’ı | **keep** |
| `docs/screenshots/guide-pp-v1/14-veri-girisi-ust.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; gerçek kitaptan rapor metni örnekleri ve sentetik test hesabı; kamusal veri BEYAN’ı; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `docs/screenshots/guide-pp-v1/15-faaliyet-maliyetleri.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; gerçek kitaptan rapor metni örnekleri ve sentetik test hesabı; kamusal veri BEYAN’ı | **keep** |
| `docs/screenshots/guide-pp-v1/16-gonder-bolumu.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; gerçek kitaptan rapor metni örnekleri ve sentetik test hesabı; kamusal veri BEYAN’ı; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `docs/screenshots/guide-pp-v1/17-gonderim-yetkileri.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; gerçek kitaptan rapor metni örnekleri ve sentetik test hesabı; kamusal veri BEYAN’ı | **keep** |
| `docs/screenshots/guide-pp-v1/18-parola-degistir.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; gerçek kitaptan rapor metni örnekleri ve sentetik test hesabı; kamusal veri BEYAN’ı | **keep** |
| `docs/screenshots/guide-pp-v1/INDEX.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `docs/specs/pp14-post-approval-correction.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları | **keep** |
| `docs/uat-contract-fixes.md` | Dokümantasyon; ürün/kurum alanları, operasyon ve varsa GitHub PR/issue referansları; kamu doküman/GitHub veya yerel/test URL alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `migrations/README` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/env.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/script.py.mako` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/0429caba7123_authorization_and_immutable_field_.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/153acbd48290_directorate_package_workflow.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/264bdce59301_immutable_report_candidates_and_release.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/290ef7e62102_initial_civensa_schema.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/375cefa60412_scoped_published_revision_requests_and_.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/3942a5669b80_s3c2_package_decision_guards_and_closed_survival.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/486dfab71523_correction_package_reapproval.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/597efbc82634_materialized_successor_lineage.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/6a8fcbd93745_successor_publication_applied_requests.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/7b90cde04856_current_release_recorrection_opening.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/8c4f72a10b31_add_user_active.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/8ca1def15967_returned_attempt_rework_and_grant_renewal.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/a6c006e9b241_login_throttling.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/a7c2d3e4f5a6_activity_revision_reason.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/b018a1c2d3e4_strategy_master_data.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/b0262027a001_economic_import_provenance.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/b8d011e6f420_preserve_source_financial_conflicts.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/c025a1b2c3d4_released_user_permissions.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/c0272027a001_structure_changes.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/c0292027a001_assurance_statements.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/c031b1a2c3d4_budget_reallocation.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/c0372027a001_civ_037_ek_1_owned_yearly_report_content.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/c0382027a001_civ_038_activity_report_financial_facts.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/c044a1b2c3d4_personal_account_password_change.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/c048a1b2c3d4_internal_control_catalogue.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `migrations/versions/c063a1b2c3d4_activity_indicator_evidence.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/c067a1b2c3d4_release_confirmations.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/c074a1b2c3d4_ar_unit_workflow.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/c078a1b2c3d4_ar_release_chain.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/c079a1b2c3d4_ic_monitoring.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `migrations/versions/c084a1b2c3d4_ic_official_statuses.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/c086a1b2c3d4_ar_typeset_keys.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/c5e8a1f0b247_a1p1_workflow_activation_guards.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/d4f0a1b2c3d4_add_workflow_history_notifications.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/e5a0b1c2d3e4_report_cards_exact_values_economics_and_.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/e69c04e721a5_activity_realization_references.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/f2b7c4d91e08_a1p11_preactivation_recovery_guards.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `migrations/versions/f6b1c2d3e4f5_activity_report_contract.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `ops/backup_crypto.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `ops/backup_self_test.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `ops/ci/actionlint_annotations.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `ops/ci/pytest_annotations.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `ops/ci/test_pytest_annotations.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `ops/db_roles.sql` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `ops/db_storage_report.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `ops/preprint_rehearsal.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `ops/release_rehearsal.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri; kamu doküman/GitHub veya yerel/test URL alanları | **keep** |
| `ops/test_backup_security.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `pytest.ini` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `qa_bundle_check.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `requirements-dev.txt` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `requirements.txt` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `scripts/book_legacy/README.txt` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `scripts/book_legacy/extract.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `scripts/book_legacy/gen.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `scripts/book_to_load_docx.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `scripts/clear_preprint_2027.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `scripts/first_load_audit.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `scripts/first_load_dryrun.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri; test e-posta/örnek URI eşleşmeleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni; e-posta satır 188 | **keep** |
| `scripts/first_load_live.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `scripts/guide_screenshots.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri; test e-posta/örnek URI eşleşmeleri; kamu doküman/GitHub veya yerel/test URL alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni; e-posta satır 104,105,118,122 | **keep** |
| `scripts/institution_summary.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `scripts/rehearse_clear_preprint_2027.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `sitecustomize.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `tests/ar_unit_workflow_helpers.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; e-posta satır 55,61 | **keep** |
| `tests/artifacts/civ071/manifest.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tests/artifacts/civ073/comparison-1366.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `tests/artifacts/civ073/comparison-390.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `tests/artifacts/civ073/comparison-totals-1366.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `tests/artifacts/civ073/comparison-totals-390.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `tests/artifacts/civ075/README.md` | Sentetik test çıktısı/üreticisi; kurum/rapor örneği ve test kimlikleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tests/artifacts/civ075/birim-onayli.pdf` | Sentetik test çıktısı/üreticisi; kurum/rapor örneği ve test kimlikleri; metin/core metadata incelendi; gerçek kişi/iletişim doğrulanmadı; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tests/artifacts/civ075/birim-taslak.pdf` | Sentetik test çıktısı/üreticisi; kurum/rapor örneği ve test kimlikleri; metin/core metadata incelendi; gerçek kişi/iletişim doğrulanmadı; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tests/artifacts/civ075/idare-mali-tablolar-taslak.pdf` | Sentetik test çıktısı/üreticisi; kurum/rapor örneği ve test kimlikleri; metin/core metadata incelendi; gerçek kişi/iletişim doğrulanmadı; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tests/artifacts/civ075/idare-onayli.pdf` | Sentetik test çıktısı/üreticisi; kurum/rapor örneği ve test kimlikleri; metin/core metadata incelendi; gerçek kişi/iletişim doğrulanmadı; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tests/artifacts/civ075/idare-taslak.pdf` | Sentetik test çıktısı/üreticisi; kurum/rapor örneği ve test kimlikleri; metin/core metadata incelendi; gerçek kişi/iletişim doğrulanmadı; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tests/artifacts/civ076/publication-history-1366.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `tests/artifacts/civ076/publication-history-390.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `tests/artifacts/civ077/latest-actual-1366.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `tests/artifacts/civ077/latest-actual-390.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `tests/artifacts/civ077/newer-comparison-1366.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `tests/artifacts/civ077/newer-comparison-390.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `tests/artifacts/civ077/status-badges-1366.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tests/artifacts/civ077/status-badges-390.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tests/artifacts/civ078/editor-release2-1366.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `tests/artifacts/civ078/editor-release2-390.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `tests/artifacts/civ078/editor-reopened-1366.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `tests/artifacts/civ078/editor-reopened-390.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `tests/artifacts/civ078/list-release2-1366.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tests/artifacts/civ078/list-release2-390.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tests/artifacts/civ079/giris-hata-1366.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `tests/artifacts/civ079/giris-hata-390.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `tests/artifacts/civ079/mudurluk-giris-1366.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `tests/artifacts/civ079/mudurluk-giris-390.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `tests/artifacts/civ079/sentetik-izleme-raporu.docx` | Sentetik test çıktısı/üreticisi; kurum/rapor örneği ve test kimlikleri; metin/core metadata incelendi; gerçek kişi/iletişim doğrulanmadı | **keep** |
| `tests/artifacts/civ079/sentetik-izleme-raporu.xlsx` | Sentetik test çıktısı/üreticisi; kurum/rapor örneği ve test kimlikleri; metin/core metadata incelendi; gerçek kişi/iletişim doğrulanmadı | **keep** |
| `tests/artifacts/civ079/strateji-izleme-1366.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `tests/artifacts/civ079/strateji-izleme-390.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `tests/artifacts/civ084/kismi-giris-hata-1366.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `tests/artifacts/civ084/kismi-giris-hata-390.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `tests/artifacts/civ084/strateji-1366.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `tests/artifacts/civ084/strateji-390.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `tests/artifacts/civ084/strateji-uyari-1366.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `tests/artifacts/civ084/strateji-uyari-390.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `tests/artifacts/civ086/generate_sample.py` | Sentetik test çıktısı/üreticisi; kurum/rapor örneği ve test kimlikleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tests/artifacts/civ086/hardware.csv` | Sentetik test çıktısı/üreticisi; kurum/rapor örneği ve test kimlikleri | **keep** |
| `tests/artifacts/civ086/identity-loss.json` | Sentetik test çıktısı/üreticisi; kurum/rapor örneği ve test kimlikleri | **keep** |
| `tests/artifacts/civ086/release-1.typeset.json` | Sentetik test çıktısı/üreticisi; kurum/rapor örneği ve test kimlikleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tests/artifacts/civ086/release-2-one-indicator.typeset.json` | Sentetik test çıktısı/üreticisi; kurum/rapor örneği ve test kimlikleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tests/artifacts/civ086/synthetic-source.json` | Sentetik test çıktısı/üreticisi; kurum/rapor örneği ve test kimlikleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tests/conftest.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni; e-posta satır 187,188 | **keep** |
| `tests/first_load_checkpoint.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/fixtures/activity_contract_v1_checkpoint.json` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tests/fixtures/activity_contract_v2_checkpoint.json` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tests/fixtures/civ069/reconciliation-mismatch.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `tests/fixtures/civ069/reconciliation-missing_link.png` | Ekran görüntüsü: görünür test rolü/kurum/rapor alanları; OCR’da canlı hesap/gerçek iletişim doğrulanmadı | **keep** |
| `tests/fixtures/first_load/SHA256SUMS` | Gerçek Büyükçekmece 2027 kurum rapor verisi/eşleme/üretim ve bütünlük kaydı; hesap yedeği değil | **keep** — kamusal veri BEYAN’ı; kişi/metadata onayı ayrıca |
| `tests/fixtures/first_load/name_map.json` | Gerçek Büyükçekmece 2027 kurum rapor verisi/eşleme/üretim ve bütünlük kaydı; hesap yedeği değil | **keep** — kamusal veri BEYAN’ı; kişi/metadata onayı ayrıca |
| `tests/fixtures/first_load/pp2027_print_d3.docx` | Gerçek Büyükçekmece 2027 kurum rapor verisi/eşleme/üretim ve bütünlük kaydı; hesap yedeği değil; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** — kamusal veri BEYAN’ı; kişi/metadata onayı ayrıca |
| `tests/fixtures/first_load/pp2027_print_d3.gen_report.json` | Gerçek Büyükçekmece 2027 kurum rapor verisi/eşleme/üretim ve bütünlük kaydı; hesap yedeği değil | **keep** — kamusal veri BEYAN’ı; kişi/metadata onayı ayrıca |
| `tests/fixtures/first_load/source/2027-performans-programi_16102026_duzeltilmis 2.idml` | Gerçek kurum kitabı; kişi adları, kişisel e-posta, belediye sistem URL’leri, macOS kullanıcı/disk yolları, kişi fotoğraf kaynakları, XMP/asset metadata; e-posta satır 85370 | **move** — özel kaynak fixture; sentetik kopya ayrı görev |
| `tests/fixtures/first_load/source/pp2027_print_d3.idml` | Gerçek kurum kitabı; kişi adları, kişisel e-posta, belediye sistem URL’leri, macOS kullanıcı/disk yolları, kişi fotoğraf kaynakları, XMP/asset metadata; e-posta satır 34613 | **move** — özel kaynak fixture; sentetik kopya ayrı görev |
| `tests/fixtures/pp2027_baseline.json` | Gerçek Büyükçekmece 2027 kurum rapor verisi/eşleme/üretim ve bütünlük kaydı; hesap yedeği değil; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** — kamusal veri BEYAN’ı; kişi/metadata onayı ayrıca |
| `tests/fixtures/pp2027_source_no_media.docx` | Gerçek kurum kitabı; gerçek author/lastModifiedBy, Windows kullanıcı/kişi fotoğraf yolları, kurum ve kişi adları, belediye URL’leri; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **redact** — belge metadata ve kişi/yol alanları; özgününü move |
| `tests/test_a1p11_preactivation_recovery.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_a1p1_workflow_activation.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; e-posta satır 288 | **keep** |
| `tests/test_activity_candidate_schema.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_activity_contract.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; e-posta satır 31 | **keep** |
| `tests/test_activity_contract_fixes.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_activity_contract_uat.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_activity_evidence.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_activity_evidence_workflow.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_activity_financial.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni; e-posta satır 58,73,81,100,106,108,115,122 | **keep** |
| `tests/test_activity_financial_migration.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tests/test_activity_financial_ui.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; kamu doküman/GitHub veya yerel/test URL alanları; e-posta satır 13 | **keep** |
| `tests/test_activity_mapping_gaps.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_activity_mapping_gaps_ui.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kamu doküman/GitHub veya yerel/test URL alanları | **keep** |
| `tests/test_activity_references.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_activity_references_sqlite.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_activity_report.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_activity_revision_reference.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_activity_sections.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; e-posta satır 45,52,99,139,140,141,142,143 | **keep** |
| `tests/test_activity_sections_export.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni; e-posta satır 62,68,76,127,173 | **keep** |
| `tests/test_activity_sections_migration.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tests/test_activity_sections_pdf.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; kamu doküman/GitHub veya yerel/test URL alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni; e-posta satır 86,87,111,155 | **keep** |
| `tests/test_activity_sections_ui.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; kamu doküman/GitHub veya yerel/test URL alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni; e-posta satır 13 | **keep** |
| `tests/test_activity_selection.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_ar_deviation_gate.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_ar_indicator_display.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kamu doküman/GitHub veya yerel/test URL alanları | **keep** |
| `tests/test_ar_release_chain.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; e-posta satır 26,136,242 | **keep** |
| `tests/test_ar_release_chain_migration.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tests/test_ar_release_chain_ui.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kamu doküman/GitHub veya yerel/test URL alanları | **keep** |
| `tests/test_ar_typeset_contract.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; kamu doküman/GitHub veya yerel/test URL alanları; e-posta satır 54,80,105,152,192,207,241,261 | **keep** |
| `tests/test_ar_typeset_migration.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tests/test_ar_typeset_review.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; e-posta satır 66 | **keep** |
| `tests/test_ar_unit_workflow.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni; e-posta satır 178 | **keep** |
| `tests/test_ar_unit_workflow_migration.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tests/test_ar_unit_workflow_ui.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kamu doküman/GitHub veya yerel/test URL alanları | **keep** |
| `tests/test_assurance_helpers.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni; e-posta satır 25,26 | **keep** |
| `tests/test_assurance_migration.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tests/test_assurance_publication.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_assurance_statements.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni; e-posta satır 33,34,35,36,37,38,39,40 | **keep** |
| `tests/test_assurance_ui.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; kamu doküman/GitHub veya yerel/test URL alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni; e-posta satır 13 | **keep** |
| `tests/test_authorization_foundation.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tests/test_book_first_load.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_budget_reallocation.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tests/test_budget_reallocation_migrated.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_budget_reallocation_migration.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni; e-posta satır 42 | **keep** |
| `tests/test_budget_reallocation_ui.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kamu doküman/GitHub veya yerel/test URL alanları | **keep** |
| `tests/test_bundle.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_clear_preprint_2027.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; e-posta satır 40,352 | **keep** |
| `tests/test_contract_migration.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; e-posta satır 41 | **keep** |
| `tests/test_correction_reapproval.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_current_release_recorrection.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; e-posta satır 283,284 | **keep** |
| `tests/test_db_roles.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_db_storage_report.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_draft_removal.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_draft_removal_ui.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kamu doküman/GitHub veya yerel/test URL alanları | **keep** |
| `tests/test_economic_form.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_first_load_audit.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_first_load_checklist.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_first_load_dryrun.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_first_load_live.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; e-posta satır 29,167,324,336,343 | **keep** |
| `tests/test_indicator_update.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_institution_summary.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_institution_summary_evidence.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_integration_runtime.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_internal_control.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; kamu doküman/GitHub veya yerel/test URL alanları; e-posta satır 345 | **keep** |
| `tests/test_internal_control_monitoring.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; kamu doküman/GitHub veya yerel/test URL alanları; e-posta satır 42,44,167,352,363 | **keep** |
| `tests/test_internal_control_official_report.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; kamu doküman/GitHub veya yerel/test URL alanları; e-posta satır 249 | **keep** |
| `tests/test_json_fetch.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kamu doküman/GitHub veya yerel/test URL alanları | **keep** |
| `tests/test_live_pilot_hardening.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; kamu doküman/GitHub veya yerel/test URL alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni; e-posta satır 198,227 | **keep** |
| `tests/test_login_throttling.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; e-posta satır 174,190,220,289 | **keep** |
| `tests/test_master_data.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni; e-posta satır 94,106,247,291 | **keep** |
| `tests/test_master_data_ui.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; kamu doküman/GitHub veya yerel/test URL alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni; e-posta satır 72 | **keep** |
| `tests/test_materialized_successor.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_migration.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_module_selection.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_package_approval_parity.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; e-posta satır 143 | **keep** |
| `tests/test_package_lock_scope.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_package_workflow.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; e-posta satır 126 | **keep** |
| `tests/test_pp_display.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tests/test_pp_errors_forms.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_pp_general_sections.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tests/test_pp_import_submit_ready.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tests/test_pp_manifest_ui.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kamu doküman/GitHub veya yerel/test URL alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tests/test_pp_period_context.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_pp_period_context_ui.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kamu doküman/GitHub veya yerel/test URL alanları | **keep** |
| `tests/test_pp_reopen.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kamu doküman/GitHub veya yerel/test URL alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tests/test_pp_required_period.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_pp_subtotal_reconciliation.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kamu doküman/GitHub veya yerel/test URL alanları | **keep** |
| `tests/test_program.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_programme_split.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kamu doküman/GitHub veya yerel/test URL alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tests/test_progress_readiness.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_publication_gates.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_publication_history.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kamu doküman/GitHub veya yerel/test URL alanları | **keep** |
| `tests/test_release_checklist.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kamu doküman/GitHub veya yerel/test URL alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tests/test_release_confirmations_migration.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_release_readiness_migration_head.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; e-posta satır 96 | **keep** |
| `tests/test_release_rehearsal.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; e-posta satır 39 | **keep** |
| `tests/test_released_permissions.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni; e-posta satır 165,168,228,293,297,366 | **keep** |
| `tests/test_released_permissions_migration.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni; e-posta satır 65 | **keep** |
| `tests/test_report_workflow.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_returned_attempt_rework.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; e-posta satır 310,311 | **keep** |
| `tests/test_review_errors.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_revision_workflow.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_sidebar_ui.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kamu doküman/GitHub veya yerel/test URL alanları | **keep** |
| `tests/test_source_comparison.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni; e-posta satır 187 | **keep** |
| `tests/test_source_comparison_ui.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kamu doküman/GitHub veya yerel/test URL alanları | **keep** |
| `tests/test_source_conflicts.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_source_conflicts_ui.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kamu doküman/GitHub veya yerel/test URL alanları | **keep** |
| `tests/test_sqlite_package_decision_guards.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni; e-posta satır 31 | **keep** |
| `tests/test_storage_upload_limits.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_structure_changes.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; e-posta satır 227 | **keep** |
| `tests/test_structure_changes_ui.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kamu doküman/GitHub veya yerel/test URL alanları | **keep** |
| `tests/test_submission_workflow.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_successor_publication.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_unsaved_drafts_ui.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kamu doküman/GitHub veya yerel/test URL alanları | **keep** |
| `tests/test_users_migration.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; e-posta satır 41,45 | **keep** |
| `tests/test_users_personal_accounts.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni; e-posta satır 227,249,305 | **keep** |
| `tests/test_users_ui.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kamu doküman/GitHub veya yerel/test URL alanları | **keep** |
| `tests/test_validation_queries.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_word_import.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; test e-posta/örnek URI eşleşmeleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni; e-posta satır 129 | **keep** |
| `tests/test_word_import_economic_layouts.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tests/test_word_import_real_source.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tests/test_workflow_concurrency.py` | Test kodu/fixture; sentetik kullanıcı, kurum veya şema alanları | **keep** |
| `tools/ar_typeset_csv.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `tools/authorization_bootstrap.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `tools/build_bundle.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `tools/create_ar_docx_demo.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri; kurum/ünvan/kişi biçiminde ürün veya fixture metni | **keep** |
| `tools/create_ar_docx_template.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri; kamu doküman/GitHub veya yerel/test URL alanları | **keep** |
| `tools/db_privilege_audit.py` | Ürün/altyapı kaynak kodu veya yapılandırma; şema/alan adları ve statik ürün metinleri | **keep** |
| `tools/legacy-qa/README.md` | Eski yerel QA aracı; demo rol hesapları, `.local` e-posta/yerel test adresleri | **keep** |
| `tools/legacy-qa/account_readiness_regression.py` | Eski yerel QA aracı; demo rol hesapları, `.local` e-posta/yerel test adresleri; kamu doküman/GitHub veya yerel/test URL alanları; e-posta satır 9,19 | **keep** |
| `tools/legacy-qa/activity_mapping_export_regression.py` | Eski yerel QA aracı; demo rol hesapları, `.local` e-posta/yerel test adresleri; kamu doküman/GitHub veya yerel/test URL alanları; e-posta satır 7,11 | **keep** |
| `tools/legacy-qa/audit_regression.py` | Eski yerel QA aracı; demo rol hesapları, `.local` e-posta/yerel test adresleri; kamu doküman/GitHub veya yerel/test URL alanları; e-posta satır 5,6,9 | **keep** |
| `tools/legacy-qa/bulk_account_regression.py` | Eski yerel QA aracı; demo rol hesapları, `.local` e-posta/yerel test adresleri; kamu doküman/GitHub veya yerel/test URL alanları; e-posta satır 4 | **keep** |
| `tools/legacy-qa/mapping_csv_regression.py` | Eski yerel QA aracı; demo rol hesapları, `.local` e-posta/yerel test adresleri; kamu doküman/GitHub veya yerel/test URL alanları; e-posta satır 4 | **keep** |
| `tools/legacy-qa/operations_regression.py` | Eski yerel QA aracı; demo rol hesapları, `.local` e-posta/yerel test adresleri; kamu doküman/GitHub veya yerel/test URL alanları; e-posta satır 22,42 | **keep** |
| `tools/legacy-qa/progress_regression.py` | Eski yerel QA aracı; demo rol hesapları, `.local` e-posta/yerel test adresleri; kamu doküman/GitHub veya yerel/test URL alanları; e-posta satır 23,36 | **keep** |
| `tools/legacy-qa/qa_cost_regression.py` | Eski yerel QA aracı; demo rol hesapları, `.local` e-posta/yerel test adresleri; kamu doküman/GitHub veya yerel/test URL alanları; e-posta satır 17 | **keep** |
| `tools/legacy-qa/qa_indicator_regression.py` | Eski yerel QA aracı; demo rol hesapları, `.local` e-posta/yerel test adresleri; kamu doküman/GitHub veya yerel/test URL alanları; e-posta satır 13 | **keep** |
| `tools/legacy-qa/qa_operations_regression.py` | Eski yerel QA aracı; demo rol hesapları, `.local` e-posta/yerel test adresleri; kamu doküman/GitHub veya yerel/test URL alanları; e-posta satır 22,39 | **keep** |
| `tools/legacy-qa/qa_progress_regression.py` | Eski yerel QA aracı; demo rol hesapları, `.local` e-posta/yerel test adresleri; kamu doküman/GitHub veya yerel/test URL alanları; e-posta satır 23,34 | **keep** |
| `tools/legacy-qa/release_readiness_regression.py` | Eski yerel QA aracı; demo rol hesapları, `.local` e-posta/yerel test adresleri; kamu doküman/GitHub veya yerel/test URL alanları; e-posta satır 5,11 | **keep** |
| `tools/legacy-qa/smoke_test.py` | Eski yerel QA aracı; demo rol hesapları, `.local` e-posta/yerel test adresleri; kamu doküman/GitHub veya yerel/test URL alanları; e-posta satır 138,139 | **keep** |
| `tools/legacy-qa/user_lifecycle_regression.py` | Eski yerel QA aracı; demo rol hesapları, `.local` e-posta/yerel test adresleri; kamu doküman/GitHub veya yerel/test URL alanları; e-posta satır 6,7,8,16,20,22 | **keep** |

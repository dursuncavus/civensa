# CIV-175 — PP yayın boyutu ölçümü

## Karar önerisi

2026 `Publication.snapshot_json` **25839532 bayt**: CIV-174 / PR #358 ölçümü birebir yeniden üretildi. `cost_reconciliation` **21181678 bayt**; bunun `errors` dizileri **19019795 bayt**. Ana şişme kaynağı doğrulandı. Ancak yalnız bu anahtarı kaldırmak **4657831 bayt** bırakır ve Word/PDF/JSON içeriğini değiştirir.

Önerilen en dar sonraki iş: **yalnız yeni onaylı-kitap yayınlarında**, bütün özgün UTF-8 payload baytlarını **XZ (preset=3) + Base64** ile sürümlü bir saklama zarfına koymak; ortak okuyucuda kayıpsız açmak. Bu fixture’da 2026 için **337346 bayt**, **25502186 bayt tasarruf** (%98,69). JSON/Word/PDF ve faaliyet raporu girdileri açılmış özgün içerikten sunulur. Bu PR öneriyi uygulamaz; yayın biçimi, uygulama ve şema değişmedi.

## Kapsam ve tekrar üretme

- Kaynak dal: `feature/authorization-workflow-phase5`, ölçülen uygulama başı `12d683e` (CIV-174 fix merge `ac17369` atasıdır).
- CIV-174 ile aynı `inspect_import(..., year=2026)` hazırlığı: onaylı 2027 kitabı, ardından onaylı 2026 kitabı; 2027 satır hash’i yükleme öncesi/sonrası aynı. `scripts.first_load_live` yalnız `verify_book/book_config` ve yerel engine alan fixture yardımcıları üzerinden kullanıldı; canlı CLI/hedef çözümleyicisi çağrılmadı.
- PostgreSQL **16.15**, Python **3.12.14**, zlib **1.3.2**; Alembic tek head **c162a1b2c3d4**. Fixture’da ölçüm/yayın denemesi öncesi her iki yılın yayın sayısı **0**. Bu, canlıdaki 2027 yayın durumunu kanıtlamaz.
- Betik yalnız `CIVENSA_TEST_POSTGRES_URL` alır. `local_test_url` yerel adresi zorunlu tutar; `disposable_database` loopback’i sabitler, libpq yönlendirmelerini temizler, ayrı veritabanını oluşturur/migre eder ve sonunda düşürür. `DATABASE_URL` / `MIGRATION_DATABASE_URL` uygulama importlarında maskelenir. HTTP testlerinin DB bağımlılığı yalnız bu engine’e bağlanır; uygulama lifespan’ı çalıştırılmaz.
- Yerel yayın denemesi gerçek `/report-builder/publish-approved-book` uç noktasını kullanır. Onay dayanağı CIV-174 testiyle aynı: `Meclis kararı, 16.10.2025`. `freeze_program_payload` zamanlayıcıyla sarılır; gerçek dönüşü değiştirilmez. Sıkıştırma/silme adayları yalnız bellekte ölçülür; saklanan Publication her zaman mevcut biçimdir.

Onaylı kitap SHA256 değerleri:

| Yıl | SHA256 |
|---|---|
| 2026 | `1aaa0bb81c3cf4e245edaab42452a972b8a59ffc252814216c7628f6dbaf33d6` |
| 2027 | `cbbf9018302d0a1d33d1dde0c4a64a2418d12b55cc29d046205371018673bd71` |

Bağımlılıklar `requirements-dev.txt` üzerinden kurulu ve yerel PostgreSQL 16+ test ortam değişkeni ayarlı iken, repo kökünden:

```sh
python -m tests.civ175_size --out /tmp/civ175-measurements.json
python -m tests.civ175_size --verify docs/reports/civ-175/measurements.json --out /tmp/civ175-repeat.json
```

[Ölçüm betiği](../../../tests/civ175_size.py) ve [ham ölçümler](measurements.json). `--verify` bütün yapısal bayt/sayı ölçümlerini tam eşitlikle denetler. Oluşturulan UUID, zaman damgası ve mesaj hash’i değerleri aynı uzunlukta fakat farklı olduğundan sıkıştırılmış baytlar koşular arasında değişebilir; codec boyutları için %1 tolerans vardır. Süre/bellek değerleri ölçülen koşunun kesin gözlemidir, tekrar koşularında eşitlik beklenmez.

## Boyut tanımı ve toplamlar

Bütün boyutlar UTF-8 **bayt**; karakter sayısı veya PostgreSQL TOAST/disk boyutu değildir. Serileştirme üretimdeki gibi `ensure_ascii=False, sort_keys=True, separators=(',', ':')`. Hedefi muhafazakâr biçimde **2000000 bayt** aldık (2 MiB = 2097152 de sağlanır).

`Değer` sütunları tek başına JSON değerinin boyutudur. `Üye` sütunları buna anahtarın JSON yazımı ve `:` ekler. Virgüller ve dış `{}` ayrı son satırdadır. Toplamlar %1 yaklaşım yerine **tam eşit** kapanır; betik bunu assert eder.

| Üst düzey anahtar | 2026 değer | 2026 üye | 2027 değer | 2027 üye |
|---|---:|---:|---:|---:|
| `catalogue` | 36839 | 36851 | 94897 | 94909 |
| `cost_reconciliation` | 21181678 | 21181700 | 985502 | 985524 |
| `departments` | 4299496 | 4299510 | 5638278 | 5638292 |
| `economics` | 11913 | 11925 | 12601 | 12613 |
| `period` | 4 | 13 | 4 | 13 |
| `program_costs` | 270814 | 270830 | 763636 | 763652 |
| `schema_version` | 5 | 22 | 5 | 22 |
| `sections` | 2 | 13 | 2 | 13 |
| Virgül + dış süslü parantezler | — | 9 | — | 9 |
| **book_snapshot toplam** | — | **25800873** | — | **7495047** |

`freeze_program_payload` kimlik/tanım bağları ve sözleşme işaretleri ekler; onaylı-kitap uç noktası ayrıca kaynak/onay/uyarı özetini ekler:

| Aşama | 2026 | 2027 |
|---|---:|---:|
| book_snapshot | 25800873 | 7495047 |
| freeze_program_payload | 25827277 | 7525888 |
| Publication.snapshot_json | **25839532** | **7536530** |
| book → freeze artışı | 26404 | 30841 |
| freeze → Publication artışı | 12255 | 10642 |

Son Publication’ın da her üst düzey anahtarı:

| Anahtar | 2026 üye baytı | 2027 üye baytı |
|---|---:|---:|
| `activity_contract_version` | 33 | 33 |
| `approval_reference` | 49 | 49 |
| `basis` | 23 | 23 |
| `book_sha256` | 80 | 80 |
| `catalogue` | 36851 | 94909 |
| `cost_reconciliation` | 21181700 | 985524 |
| `definition_contract_version` | 35 | 35 |
| `departments` | 4325844 | 5669063 |
| `economics` | 11925 | 12613 |
| `kaynak_kitap_uyarilari` | 10958 | 9328 |
| `kaynak_kitap_uyarilari_sha256` | 98 | 98 |
| `load_reference` | 1041 | 1058 |
| `period` | 13 | 13 |
| `program_costs` | 270830 | 763652 |
| `schema_version` | 22 | 22 |
| `sections` | 13 | 13 |
| Virgül + dış süslü parantezler | 17 | 17 |
| **Toplam** | **25839532** | **7536530** |

`kaynak_kitap_uyarilari` tek başına 2026’da **10933**, 2027’de **9303** bayt; 2026 şişmesinin nedeni onay özeti değildir.

## departments içi

İki yılda da snapshot **35** müdürlük nesnesi içerir; boş kurum müdürlükleri de `period_departments` kapsamındadır. Veri içerenler 2026’da **33**, 2027’de **34**. 2026: **105 kart, 226 gösterge, 182 faaliyet, 1270 ekonomik hücre**. 2027: **64 kart, 263 gösterge, 291 faaliyet, 1340 ekonomik hücre**.

Aşağıdaki değerler `book_snapshot.departments` içindeki alanların bütün müdürlükler üzerinden toplamıdır. Üye hesabı her nesnede alan adı + `:` içerir:

| Alt anahtar | 2026 değer | 2026 üye | 2027 değer | 2027 üye |
|---|---:|---:|---:|---:|
| `economics` | 2882388 | 2882808 | 3253989 | 3254409 |
| `activities` | 716075 | 716530 | 1408216 | 1408671 |
| `indicators` | 454992 | 455447 | 714743 | 715198 |
| `cards` | 201196 | 201476 | 220917 | 221197 |
| `department_costs` | 33649 | 34314 | 34546 | 35211 |
| `scope` | 5436 | 5716 | 140 | 420 |
| `department` | 1288 | 1743 | 1255 | 1710 |
| `department_id` | 61 | 621 | 61 | 621 |
| `period` | 140 | 455 | 140 | 455 |
| Liste/nesne parantezleri ve virgüller | — | 386 | — | 386 |
| **Toplam** | — | **4299496** | — | **5638278** |

En büyük 5 müdürlük nesnesi:

| 2026 müdürlük | Bayt | 2027 müdürlük | Bayt |
|---|---:|---|---:|
| Basın Yayın ve Halkla İlişkiler Müdürlüğü | 213492 | Sosyal Destek Müdürlüğü | 281427 |
| Veteriner İşleri Müdürlüğü | 199041 | Mali Hizmetler Müdürlüğü | 266069 |
| Mali Hizmetler Müdürlüğü | 175339 | Yazı İşleri Müdürlüğü | 244060 |
| Fen İşleri Müdürlüğü | 175001 | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 232667 |
| Bilgi İşlem Müdürlüğü | 168561 | Fen İşleri Müdürlüğü | 220097 |

İkinci şişme kaynağı ekonomik hücrelerdeki tekrar eden kaynak bağlamı/uyarıdır: 2026 `source_context_json` değerleri **1911580**, `issue` değerleri **596876** bayt; 2027’de **2769410** ve **90966** bayt. `economics` departman nesneleri içindedir; üst düzey özet `economics` ile karıştırılmamalı. Yalnız mutabakat alanını kaldırmanın hedefe yetmemesini bu kaynak/provenans verisi açıklıyor; bu veriyi sessizce silmek güvenli bir küçültme değildir.

## cost_reconciliation yapısı ve çoğalma nedeni

Bir JSON nesne listesi; her satır program/alt program/müdürlük ve bütçe/tahmin yılına ait mutabakatı taşır. Satırlar miktarlar, tamlık bilgisi, kaynak farkı, üye faaliyet kimlikleri ve tam hata/uyarı metinlerini içerir. Başka bir gömülü JSON şişmesi yok; baskın alan gerçek string listesi `errors`.

| Ölçüm | 2026 | 2027 |
|---|---:|---:|
| Satır | 2868 | 570 |
| Hata mesajı occurrence | 61167 | 1714 |
| Farklı hata mesajı | 11805 | 93 |
| Uyarı occurrence | 2868 | 318 |
| Farklı uyarı mesajı | 2868 | 318 |
| activity_ids toplam başvurusu | 43272 | 5007 |
| `program` satırı | 78 | 84 |
| `subprogram` satırı | 126 | 114 |
| `department` satırı | 2559 | 267 |
| `department_total` satırı | 105 | 105 |

| Satır alanı | 2026 değer toplamı | 2026 üye toplamı | 2027 değer toplamı | 2027 üye toplamı |
|---|---:|---:|---:|---:|
| `errors` | 19019795 | 19045607 | 658035 | 663165 |
| `warnings` | 698645 | 730193 | 66967 | 73237 |
| `path` | 347793 | 367869 | 49482 | 53472 |
| `activity_ids` | 175962 | 218982 | 19305 | 27855 |
| `label` | 186519 | 209463 | 37941 | 42501 |
| `status` | 43020 | 68832 | 7430 | 12560 |
| `value_kind` | 26768 | 64052 | 5320 | 12730 |
| `level` | 34812 | 57756 | 7218 | 11778 |
| `source_amount` | 11472 | 57360 | 4474 | 13594 |
| `subprogram_id` | 6102 | 51990 | 1425 | 10545 |
| `department_id` | 5355 | 51243 | 1473 | 10593 |
| `difference` | 11472 | 48756 | 2728 | 10138 |
| `complete` | 14340 | 45888 | 2626 | 8896 |
| `program_id` | 5946 | 43230 | 1146 | 8556 |
| `amount` | 11472 | 37284 | 4221 | 9351 |
| `year` | 11472 | 31548 | 2280 | 6270 |
| Liste/nesne parantezleri ve virgüller | — | 51625 | — | 10261 |
| **Toplam** | — | **21181678** | — | **985502** |

2026 en büyük satır **66112 bayt**, 0-tabanlı indeks **2559**, `subprogram` düzeyi, **205 hata**; yol `ŞEHİRCİLİK VE RİSK ODAKLI BÜTÜNLEŞİK AFET YÖNETİMİ / MEKÂNSAL PLANLAMA VE KENTSEL DÖNÜŞÜM`. 2027 en büyük satır **4039 bayt**, indeks **420**, `program`, **9 hata**. Diğer en büyük satırlar ham ölçüm dosyasında.

`app/program_service.py:434-459`: güvenilir alt program/kart konumu olmayan faaliyetler, kısmi toplamın doğruymuş gibi gösterilmemesi için **bütün potansiyel alt programların** üyelerine eklenir (`candidates = set(subprograms)`). Fixture 2026’da **128** faaliyet bu durumdadır; **26 program / 42 alt program** vardır. 2027’de **5** faaliyet, **28 / 38** program/alt program vardır. Ardından her ebeveyn için 3 bütçe/tahmin satırı oluşur (`make_rows`, satır 462), hatalar her grubun her yılına yeniden yazılır (satır 467, 479, 501). 2026’daki **61167** hata occurrence’ının yalnız **11805** farklı metin olması bu çoğalmayı doğrudan gösterir. Bu PR eşleştirmeleri veya muhafazakâr tamlık kuralını değiştirmez.

`publication_checks` satır 575 her mutabakat satırını `observed` altında yeniden kullanır; bütün hata sayısı 2026’da **63541**, uyarı sayısı **2868**, toplam **66409**. 2027’de **1750 + 318 = 2068**. Bu fonksiyon **Publication.snapshot_json okumaz**; canlı dönem satırlarından yeniden hesaplar. Eski yayının mutabakatını güncel DB’den yeniden hesaplamak aynı şey değildir ve mühürlü geçmişi değiştirebilir.

## Süre ve Python bellek ölçümü

Her ana ölçüm ayrı Session’da yapılır; fixture kurulumu zaman dışında. `freeze_program_payload` süresi `book_snapshot`, kimlik/tanım oluşturma ve flush’ları içerir; HTTP login, publication_checks, onay özeti, JSON serileştirme ve Publication insert/commit süresi dışındadır. Sürelerde tracemalloc kapalıdır. Tek koşu wall-clock ölçümü, Render kapasite testi değildir.

| İşlem | 2026 saniye | 2027 saniye |
|---|---:|---:|
| `book_snapshot` | 0.917007449 | 1.113621499 |
| `publication_checks` | 1.600673905 | 1.133574208 |
| `freeze_program_payload` | 1.814277346 | 1.850222955 |

`json.loads` için DB’den zaten okunmuş Python `str` hazırken GC çalıştırıldı, tracemalloc başlatıldı, yalnız ayrıştırma izlendi:

| Ölçüm | 2026 | 2027 |
|---|---:|---:|
| Girdi Python str (`sys.getsizeof`), bayt | 47619022 | 14675752 |
| Ek ayrıştırma tepe tahsisi, bayt | 54810994 | 16176845 |
| Dönüşte tutulan tahsis, bayt | 54807834 | 16173661 |
| Tracemalloc açıkken saniye | 0.22788244000003033 | 0.14793012899997393 |

2026 `str` (**47619022**) ve ek ayrıştırma tepesi (**54810994**) birlikte yaklaşık **102430016 bayt** eder; bu sayı bütün süreç RSS’i değildir. SQLAlchemy, web sunucusu, eşzamanlı istekler, `publication_display_payload` deepcopy’si ve Word/PDF inşası buna dahil değildir. Saklamayı sıkıştırmak bu 54,8 MB ayrıştırma maliyetini ortadan kaldırmaz. 512 MB instance için güvenli eşzamanlılık/çıktı boyutu bu çalışmadan çıkarılamaz.

## Publication.snapshot_json okuyucu envanteri

Tarama: `rg -n "snapshot_json" app` ve `rg -n "Publication|publications" app` ile bütün eşleşmelerin model/kullanım bağlamı incelendi; şablonlar ve ham SQL kullanımları da tarandı. Aşağıdaki **7 doğrudan tüketim yolu** uygulamadaki bütün Publication okuyucularını kapsar. Satırlar ölçülen `12d683e` tabanındadır.

| Dosya:satır / yol | Kullandığı üst düzey anahtarlar ve davranış | XZ önerisi etkisi |
|---|---|---|
| `app/program_routes.py:613,615,620` `publication_export` | Hash için **bütün ham baytlar**. JSON: bütün anahtarlar korunur; `publication_display_payload` yalnız `catalogue[].code` sunumunu değiştirir (`app/book_export.py:24`). Word/PDF `blocks`: `period`, `draft`, `sections`, `departments`, `economics`, `program_costs`, `cost_reconciliation`, `catalogue` (satır 53,86,115,123,133,145,185). | Önce ham zarf hash’i doğrula, aç; JSON’un ham dönüş dalı da açılmış özgün baytları döndürmeli. `blocks` değişmemeli. |
| `app/activity_contract_service.py:54,57` `checked_publication` | Hash bütün baytlar; `period`, `departments`, `activity_contract_version`, `definition_contract_version`. `snapshot_rows` (67): `departments` → cards/indicators ve kimlikler. | Ortak doğrulanmış açıcı; gösterge/tanım sözleşmesi aynı. |
| `app/draft_removal_service.py:59,75` `_indicator_blockers` → `_contains_indicator` (30) | `departments` → `indicators` (`id`, `persistent_indicator_id`); kökte legacy `indicators` da desteklenir. Aynı listede SubmissionEvent/PackageRevision içerikleri de okunur. | Yalnız Publication girdisi yeni açıcıya yönelmeli; eski diğer modellerin içerikleri korunmalı. |
| `app/activity_financial_service.py:361,362` `pp_references` | Hash bütün baytlar; `departments` → department_id/economics (category, year, value_kind, funding_type, amount, state). | Açıcı sonrası aynı mali karşılaştırma. |
| `app/ar_typeset_source.py:87,89` `enrich` | Hash bütün baytlar; `departments` → department_id/activities. `json.loads(..., parse_float=Decimal)` semantiği korunmalı. | Açıcı üzerinden aynı dizgi kaynak faaliyetleri. |
| `app/activity_contract_routes.py:145` `/activity-reports` `index` | Anahtar kullanmaz; bütün ham içeriğin SHA256’sı ile `valid` gösterir. | Zarf tam baytları mühürlenirse mevcut hash kontrolü aynen geçerli. |
| `app/revision_workflow_service.py:27` `current_source` | Anahtar kullanmaz; **ham snapshot_json == candidate.payload_json** ve hash eşitliğini zorunlu tutar. | Önerinin dar kapsamı gereği aday/yayın iş akışı eski saklama biçiminde kalır; bu karşılaştırma değiştirilmez. Genel codec yayılımında ayrıca ele alınması şart. |

`checked_publication` üzerinden dolaylı tüketiciler ve alanları:

- `app/activity_contract_service.py:180` `bind_legacy_indicator`: `departments`, `period`, iki definition/activity sözleşme işareti; snapshot_rows/definition_payload (67,105) üzerinden.
- `app/activity_contract_service.py:323` `report_revision`: `period`, `departments`, iki sözleşme işareti; buna bağlı `save_actual` (417), `approve_report` (484,500), `report_data` (568,569,577) aynı girdiyi doğrular/kullanır.
- `app/activity_contract_service.py:345` `create_report_revision` → `publication_bindings` (229,246): `departments`, `period`, sözleşme işaretleri; kart/gösterge/targets/definition kimlikleri. Yeni ve mevcut faaliyet raporu revizyonları bu yoldadır.
- `app/activity_contract_service.py:538,543,546` `newer_publication_comparison`: eski/yeni yayın için aynı anahtarlar, müdürlük filtresi ve tanım farkları.
- `app/activity_contract_routes.py:285,287,300` kimlik eşleme ekranı: `departments`, `period`; API/UI rapor görüntüleme ve revizyon yolları (75,80,155,165,250) yukarıdaki service okuyucularına gider.
- `app/activity_evidence_service.py:121` download, `app/activity_contract_routes.py:190` upload (`save_actual` üzerinden): `report_revision` aracılığıyla bütünlük/yıl/sözleşme denetimi. Ek üst düzey içerik okunmaz.

Metadata amaçlı ORM yüklemeleri ayrıca büyük Text kolonunu dolaylı çekebilir fakat içerik anahtarı kullanmaz: `app/release_service.py:67` (id/version/sha256), `app/audit_display.py:278,306` (sürüm etiketi), `app/activity_contract_routes.py:134,166,261` (revizyon ve seçim listesi metadatası). Bunları ertelemek ayrı bir bellek iyileştirmesidir; snapshot baytını azaltmaz. `app/publication_history.py:13` alanı özellikle `defer` eder; snapshot okuyucusu değildir.

`app/program_routes.py:544,597` ve `app/report_workflow_service.py:693` **yazıcılardır**. `app/program_service.py:707`, `app/released_permissions.py:275` ve `app/source_comparison_service.py:162` ImportBatch snapshot’ı okur; StructureChange, SubmissionEvent ve internal-control snapshot eşleşmeleri de Publication değildir.

## Küçültme adayları: kesin karşılaştırma

Bütün adaylar son Publication üzerinde ölçüldü. Silme/pooling anahtar/virgül değişimleri toplam farkına dahildir. Codec boyutları aşağıdaki 5 alanlı zarfın JSON + Base64 maliyetini de içerir; sadece sıkıştırılmış binary boyutu değildir.

| Aday | 2026 sonuç | 2026 tasarruf | 2027 sonuç | 2027 tasarruf | 2026 <2000000? |
|---|---:|---:|---:|---:|---|
| cost_reconciliation sil | 4657831 | 21181701 | 6551005 | 985525 | Hayır |
| errors/warnings sil | 6057996 | 19781536 | 6798988 | 737542 | Hayır |
| errors/warnings string havuzu + indeksler | 10962815 | 14876717 | 6916028 | 620502 | Hayır |
| Gzip level=9 + Base64 | 2150572 | 23688960 | 520111 | 7016419 | Hayır |
| Bzip2 level=9 + Base64 | 619789 | 25219743 | 355436 | 7181094 | Evet |
| **XZ preset=3 + Base64** | 337346 | 25502186 | 316861 | 7219669 | Evet |

| Aday | Okuyucular / eski yayın uyumu / risk |
|---|---|
| Alan veya mesaj silme | Word/PDF mutabakat tablosu ve JSON arşivi değişir. Departman toplamları da `cost_reconciliation` üzerinden bastırılır; silince eksik bir toplam sayısal görünebilir. Diğer içerik alanlarını azaltmadığı için hedefe de yetmez. Eski kayıtları bırakmak onları okunur tutar ama yeni kayıtların çıktısı eşdeğer olmaz. **Önerilmiyor.** |
| String havuzu | Tam mesajlar ve sıralama açıldığında korunabilir; JSON/Word/PDF açıcı ister. Eski liste biçimine fallback ve yeni ör. `cost_reconciliation_encoding` işareti gerekir; mevcut activity/definition sürümleri değiştirilmemeli. Null/sıra/duplicate kaybı riski ve 10,96 MB sonuç: **tek başına uygun değil.** |
| Gzip zarfı | Açıcı ile kayıpsız; eski düz JSON fallback ile okunur. Bütün parse eden okuyucular etkilenir; yalnız hash okuyucuları ham zarfı mühürler. **2 MB sınırını sağlayamaz.** |
| Bzip2 zarfı | XZ ile aynı okuyucu ve sürüm stratejisi; **619789 bayt** hedefi sağlar. Daha küçük encoder tahsisi ama daha yavaş açma/sıkıştırma. Alternatif. |
| XZ zarfı | Aynı ortak açıcı ve eski düz JSON fallback; içerik/tanım sözleşmesi değişmez. **337346 bayt** hedefi sağlar. Decoder output limit, codec/sürüm ve iki hash doğrulaması zorunlu; açılmış içeriğin bellek maliyeti sürer. Önerilen sonraki iş. |

### Önerilen dar saklama sözleşmesi (uygulanmadı)

Ölçülen zarf alanları: `snapshot_storage_version="1.0"`, `codec="xz+base64"`, `uncompressed_bytes`, `payload_sha256` (özgün UTF-8 baytların SHA256’sı), `data` (Base64). 2026 XZ binary **252876 bayt**, zarf **337346 bayt**. Bu bir **saklama** sürümüdür; açılan içerikte `schema_version="5.0"`, `activity_contract_version="3.0"`, `definition_contract_version="3.0"` aynen kalır. Özel yeni anahtar adı, eski iş sözleşmesini yeniden yorumlamayı önler.

Yeni yazıcı yalnız `/report-builder/publish-approved-book` olmalı. **Mevcut yayın satırları yeniden yazılmamalı**, eski SHA256 ve bağlı revizyonlar korunmalı. Yeni yayının `Publication.sha256` değeri yine saklanan zarfın **tam UTF-8 baytlarının** hash’i olmalı; `payload_sha256` içeriği ayrıca doğrular. Faaliyet raporu revizyonu yeni yayının mevcut dış hash’ine bağlanır.

Okuyucu sırası: dış hash → bilinen saklama sürümü/codec → strict Base64 → sınırlandırılmış XZ açma → `uncompressed_bytes` ve iç hash → eski JSON ayrıştırma/iş sözleşmesi denetimleri. İşaret yoksa mevcut düz JSON yolu. XZ deneyinde **32 MiB decoder memlimit** ile açma başarılıdır; bu, **çıktı boyut sınırı değildir**. Sonraki uygulamada ayrı hard output cap ve streaming decoder gereklidir; zarfın beyan ettiği uzunluk tek başına güvenilir limit sayılmamalıdır. Bilinmeyen sürüm/codec fail-closed olmalı.

JSON arşivi açılmış **aynı** içeriği, mevcut `publication_display_payload` katalog kodu sunumuyla döndürmeli; Word/PDF aynı `blocks` fonksiyonuna gitmeli. DB’den güncel mutabakat yeniden hesaplanmamalı. Bütün array sıraları, duplicate mesajlar, kaynak metinleri, null/boş/0 ayrımı ve kimlikler açmada korunur. Betik her codec için açılan **baytların özgün baytlarla tam eşitliğini** assert eder; string havuzu için de bütün satır eşitliğini kontrol eder.

Kapsam sınırı önemlidir: aday iş akışı `Publication.snapshot_json == ReportCandidate.payload_json` eşitliğini hem uygulamada (`app/revision_workflow_service.py:27`) hem PostgreSQL trigger’ında (`migrations/versions/f2b7c4d91e08_a1p11_preactivation_recovery_guards.py:533`) zorunlu tutar. Onaylı-kitap uç noktası ReportCandidate/ReportRelease oluşturmaz. Öneri o uç noktayla sınırlı kalırsa normal publish ve aday iş akışı yazıcısı ham JSON üretmeye devam eder, guard’lar değişmez ve migrasyon gerekmez. **Codec’i genel Publication yazıcısına körlemesine eklemek güvenli değildir**; genel yayılım aday sözleşmesi/okuyucuları için ayrı tasarım ister.

### Codec kaynak maliyeti

Tracemalloc ile sadece codec çağrıları izlendi; girdi baytları önceden hazır. Native/RSS sınırı kanıtı değildir. Base64, zarf inşası ve JSON parse bu tabloda zaman/bellek dışında.

| Yıl | Codec | Binary bayt | Sıkıştırma sn | Açma sn | Encoder tepe bayt | Decoder tepe bayt |
|---|---|---:|---:|---:|---:|---:|
| 2026 | bzip2 | 464705 | 2.689881388 | 0.317622341 | 9365797 | 56609276 |
| 2026 | gzip | 1612792 | 0.295917704 | 0.025049029 | 7216462 | 58262539 |
| 2026 | xz | 252876 | 0.218589415 | 0.013484797 | 33173776 | 60839332 |
| 2027 | bzip2 | 266440 | 0.781407074 | 0.078858779 | 8133658 | 21529025 |
| 2027 | gzip | 389949 | 0.065523553 | 0.006743883 | 1799282 | 21959174 |
| 2027 | xz | 237512 | 0.139354197 | 0.008271338 | 33122643 | 25759081 |

XZ preset=3 bu fixture’da hem en küçük hem hızlıdır; encoder tepe tahsisi yaklaşık 33,2 MB, Bzip2 yaklaşık 9,4 MB. Tek istek için dahi gerçek Render RSS/timeout doğrulaması bu ölçümle yapılmış sayılmaz. Gzip binary 2 MB altında görünse de Text kolonu için Base64/zarf eklendiğinde **2150572** bayta çıkar; bunu başarılı aday diye raporlamıyoruz.

## Doğrulama ve açık kalanlar

- Ölçüm betiği: geçici PostgreSQL 16 üzerinde exit **0**; üretim biçimindeki yerel yayınlar oluşturuldu, 2026 **25839532** bayt yeniden üretildi; bütün tablo toplamları tam eşit ve codec/pool round-trip kontrolleri geçti.
- `python -m pytest -q --require-postgres tests/test_approved_book_publication.py -k "not history_screens"`: **23 passed, 2 deselected**. `-k history_screens` ile sistem Chromium üzerinden kalan **2 passed, 23 deselected**; modül toplamı **25 passed**. Playwright CDN indirmesi ortam politikasınca engellendi; mevcut `/usr/bin/chromium` kullanıldı.
- `python -m alembic heads`: **c162a1b2c3d4 (head)**, tek head. `python -m py_compile tests/civ175_size.py` ve `git diff --check`: başarılı.
- İkinci bağımsız fixture koşusu `--verify` ve PR CI sonuçları PR açıklamasında kaydedilir. Süre ve sıkıştırılmış boyut ölçümleri koşu verisidir; bit düzeyinde aynı fixture metadata değerleri iddia edilmez.
- Canlı veritabanına bağlanılmadı, Render/üretim kapasitesi ve canlı 2026/2027 yayın varlığı denetlenmedi. Yayın çıktıları için yeni codec uygulaması/integrasyon testi yapılmadı; bu PR yalnız ölçüm ve öneridir. Kayıpsız açmanın bayt eşitliği kanıtlandı; yeni okuyucu, eski/yeni yayın eşdeğerliği, bozulmuş zarf reddi, decoder limitleri ve aday guard regresyonları sonraki uygulamanın kabul testleri olmalıdır.
- Öneri kaynağı düzeltmez ve 61167 subtotal hatasını kapatmaz; mevcut içerik/diagnostik aynen saklanır. 2 MB hedefi fixture’da kanıtlanmıştır, ilerideki her kitaba otomatik garanti değildir.

Yalnız `tests/civ175_size.py` ve `docs/reports/civ-175/**` eklendi. Merge/deploy yapılmadı.

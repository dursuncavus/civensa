# CIV-178 — Eşleştirme sonrası 2026 yayın ölçümü

4 Kasım 2026; geçici yerel PostgreSQL 16.15 (Debian 16.15-1.pgdg13+2), Python 3.12.14. Tam ham ölçümler: [measurements.json](measurements.json). Önceki ölçüm: [CIV-175](../civ-175/size.md).

2026 onaylı kitap CIV-175 ile aynı `inspect_import(..., year=2026)` hazırlığıyla yüklendi (önce 2027, ardından 2026). 2027 koruma özeti değişmedi. Taslağın 128 satırı; müdürlük adı, faaliyet adı ve aynı adın müdürlük içinde kimlik sırasındaki yeriyle birebir yerel kayda çevrildi. Eksik, fazla veya belirsiz eşleşmede betik durur; canlı kimlikler yerel faaliyet kimliği olarak kullanılmaz.

Taslak: `docs/lead/data/2026-faaliyet-eslestirme-taslagi.csv`; SHA-256: `22ac2e45def6bd01c22d3067e6b65605f45c7750abb3fa18e6637527370fe87c`. CSV gerçek `POST /api/activity-mappings/import-apply` yoluyla uygulandı; ardından gerçek `POST /report-builder/publish-approved-book` isteği **303** döndü. Yayın ve audit kaydı `activity_mapping.count=128` ve tek etkin CSV işlem grubu kimliğini içeriyor.

| Ölçüm | CIV-175, eşleştirme öncesi | CIV-178, eşleştirme sonrası |
|---|---:|---:|
| Yayın snapshot UTF-8 baytı | 25.839.532 | 6.012.152 |
| `cost_reconciliation` değer baytı | 21.181.678 | 1.266.684 |
| `publication_checks` kontrol sayısı | 2.971 | 607 |
| `publication_checks` hata / uyarı | 63.541 / 2.868 | 5.473 / 504 |
| `json.loads` ek bellek tepesi, bayt | 54.810.994 | 12.912.854 |
| Tam PP PDF duvar süresi | Ölçülmedi | 105,25 sn |
| Tam PP PDF boyutu, bayt | Ölçülmedi | 2.303.399 |

Snapshot 19.827.380 bayt (%76.73) küçüldü. Ölçüm sıkıştırma veya alan silme uygulamaz. Eşleştirme, belirsiz faaliyetlerin bütün alt programlara hata taşımasını azaltır; özgün mutabakat ve uyarı üretimi korunur. Kart eksiği 148, katalog eksiği 174, alt program eksiği 0; eşleştirme bütün kaynak sorunlarını çözmüş sayılmaz.

Üst düzey anahtarların bayt dökümü (değer; anahtar adı ve iki nokta dahil üye):

| Anahtar | Değer baytı | Üye baytı |
|---|---:|---:|
| `activity_contract_version` | 5 | 33 |
| `activity_mapping` | 46 | 65 |
| `approval_reference` | 28 | 49 |
| `basis` | 15 | 23 |
| `book_sha256` | 66 | 80 |
| `catalogue` | 36.839 | 36.851 |
| `cost_reconciliation` | 1.266.684 | 1.266.706 |
| `definition_contract_version` | 5 | 35 |
| `departments` | 4.336.315 | 4.336.329 |
| `economics` | 11.913 | 11.925 |
| `kaynak_kitap_uyarilari` | 10.776 | 10.801 |
| `kaynak_kitap_uyarilari_sha256` | 66 | 98 |
| `load_reference` | 1.024 | 1.041 |
| `period` | 4 | 13 |
| `program_costs` | 348.034 | 348.050 |
| `schema_version` | 5 | 22 |
| `sections` | 2 | 13 |

Üye baytlarının toplamına 18 bayt nesne ayıracı eklenince 6.012.152 bayt elde edilir. Saklanan metnin SHA-256 değeri ve kanonik UTF-8 serileştirmesi doğrulandı.

`json.loads` girdisi bellekte hazır bir `str`: 11.559.466 bayt. Tracemalloc açık ayrıştırma 0.144 sn; ek bellek tepesi süreç RSS'i veya bütün PDF belleği değildir. Tam `export_book(published_payload, 'pdf')` çağrısı **105,25 sn** sürdü; **120 sn** sınırı uygulanmıştı, timeout olmadı. Süreler bu yerel çalışmanın gözlemidir.

Tekrar üretme: yalnız yerel, geçici PostgreSQL 16+ için `CIVENSA_TEST_POSTGRES_URL` ayarlayıp depo kökünde `python -m tests.civ178_mapped_size` çalıştırın. Uygulama URL değişkenleri maskelenir; test istemcisi startup/lifespan çalıştırmaz; oluşturulan veritabanı sonunda kaldırılır. Canlı veritabanı, dağıtım veya birleştirme işlemi yapılmadı.

Doğrulama: `python -m pytest -q --require-postgres tests/test_approved_book_mapping.py tests/test_approved_book_publication.py`. Tek Alembic head: `c162a1b2c3d4`; migration/şema değişikliği yok.

Kaynak doğrulaması yalnız `activity_mapping_csv` ve `activity_mapping` kayıtlarını, yükleme sonrası olmaları ve faaliyet o sırada alt programsız yüklenmiş olması koşuluyla oynatır; CSV geri almaları uygulanır. Güncel alt program ve kart bu geçmişle aynı olmalı, alt program aynı döneme ait olmalı. Yalnız bu alanlar yükleme anındaki değerlere çevrilerek **aynı `applied_hash`** zorunlu tutulur. Genel `activity_update` kabul edilmez.

Otomatik `pp_data_change` eşlikçisi ancak doğrulanmış eşleştirmeyle aynı PostgreSQL ekleme işlemine (`xmin`), kullanıcıya, döneme ve müdürlüğe bağlıysa kabul edilir. Başka tür audit içeren işlem eşlikçi kanıtı sayılmaz; örneğin yedek geri yükleme işlemi eski auditleri tek işlemde yeniden eklemişse güvenli biçimde ret sürer. Bu bağ kurulamazsa normal yayın yolu gerekir. Diğer audit ve içerik kontrolleri korunur.

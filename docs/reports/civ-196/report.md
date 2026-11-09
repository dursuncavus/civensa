# CIV-196 — Yavaş Strateji adımları profili

**Yalnız bulgu ve ölçülmüş düzeltme önerisi; bu görevde düzeltme uygulanmaz.** Profil yalnız atılabilir yerel SQLite üzerinde, süreç içi TestClient ile alındı. Canlı veritabanına bağlanılmadı; merge/deploy yapılmadı.

## 1. Sonuç özeti

Dört Strateji adımının sunucu tarafı maliyeti, provada aynı gerçek biçimli 2026 PP verisi (33 müdürlük, 105 kart, 226 gösterge, 182 faaliyet, 1270 ekonomik değer) üzerinde ölçüldü. Her adım 3 kez koşuldu.

| Adım | Route | Duvar saati (3 koşu, s) | SQL ifadesi | SQL süresi (s) | Durum |
| --- | --- | ---: | ---: | ---: | --- |
| step1 · 2026 onaylı kitap yayın hazırlığı | GET `/report-builder?period_id=2` | 1.460 / 1.386 / 1.394 | 2853 / 2852 / 2852 | 0.043 / 0.044 / 0.044 | 200 |
| step2 · Onaylı kitaptan yayınla | POST `/report-builder/publish-approved-book` | 2.593 / 2.606 / 2.616 | 7395 / 7395 / 7395 | 0.116 / 0.117 / 0.124 | 303 |
| step3 · 2026 EK-1 raporlarını oluştur | POST `/activity-sections/years` | 0.158 / 0.133 / 0.136 | 1369 / 1369 / 1369 | 0.009 / 0.009 / 0.009 | 303 |
| step4 · İdare raporuna geçiş | GET `/activity-sections?period_id=2` | 0.557 / 0.397 / 0.420 | 2442 / 1958 / 1958 | 0.027 / 0.023 / 0.025 | 200 |

**Ana bulgu:** süre, SQLite üzerinde SQL süresinden (≤0.12 s) çok **SQL ifade sayısı** ve Python CPU maliyetinden geliyor. Provaların 6–11 s duvar saati, Playwright `networkidle` + yazı tipi + tarayıcı render süresini de içeriyor; bu betik yalnız sunucu tarafını ölçer. Render'da (PostgreSQL ağ üzerinden) her sorgu bir ağ gidiş-dönüşüdür; bu yüzden **query sayısı asıl risk ölçüsüdür** (bkz. §7).

## 2. Tekrar çalıştırma

Depo kökünde, mevcut `requirements-dev.txt` bağımlılıkları kuruluyken:

```sh
python scripts/profile_strateji_steps.py            # tam 2026 verisi, her adım 3 kez
python scripts/profile_strateji_steps.py --tiny     # küçük çekirdek veri (duman testi)
```

Betik `DATABASE_URL` sqlite değilse hiçbir uygulama modülü yüklemeden reddeder; varsayılan olarak geçici bir SQLite dosyası oluşturur ve sonunda siler. Duman testi: `python -m pytest tests/test_profile_strateji_steps.py -q`.

## 3. Yöntem ve veri

- **Veri:** `scripts/fr_rehearsal.py` provasının kullandığı aynı onaylı kitap ve içe aktarma yolu (`first_load_live.verify_book` + `department_payload` + `first_load_service.apply_first_load_batch`). `first_load_live.execute` PostgreSQL advisory lock / `LOCK TABLE` kullandığı için SQLite üzerinde doğrudan çağrılmaz; onun ORM yazma yolu ve aynı `first_load_department` audit kayıtları SQLite üzerinde aynı sonucu üretir. Kurulum sayımı birebir doğrulandı: **105 kart, 226 gösterge, 182 faaliyet, 1270 ekonomik değer**.
- **Ölçüm:** her adım için (1) duvar saati (`time.perf_counter`), (2) SQL ifade sayısı ve toplam SQL süresi (SQLAlchemy `before/after_cursor_execute` olayları), (3) `cProfile` en pahalı uygulama fonksiyonları (cumtime, file:line).
- **Süreç içi:** `fastapi.testclient.TestClient`, tek Session, `follow_redirects=False`; gerçek giriş (`/login`) + CSRF ile Strateji hesabı. Yazma adımları (step2, step3) her koşuda temiz bir kopyada çalıştırılır; step4 önce step3'ün ürettiği AR belgelerini oluşturur.
- SQLite 3 (Python 3.12), SQLAlchemy 2.0.54, FastAPI 0.141.1. Tek makine, loopback değil süreç içi ölçüm; Render kapasite/SLA testi değildir.

## 4. step1 — GET `/report-builder` (onaylı kitap yayın hazırlığı)

- Duvar saati: **1.39–1.46 s**; SQL: **~2852**; SQL süresi: **~0.044 s**; durum 200.
- En pahalı fonksiyonlar (cumtime):
  - `app/program_routes.py:365(builder)` 1.454 s
  - `app/program_service.py:401(cost_reconciliation)` 0.605 s
  - `app/program_service.py:747(approved_book_provenance)` 0.402 s
  - `app/program_service.py:226(department_snapshot)` 0.366 s (34 çağrı)
  - `app/program_service.py:459(make_rows)` 0.213 s (955 çağrı)
  - `app/import_service.py:595(_serialize_department_state)` 0.164 s (33 çağrı)
  - şablon render `report_builder.html` / `pp_reconciliation.html` ~0.30 s (279.303 düğüm)
- En sık SQL (N+1 kanıtı): 546× `activity_catalogue_links` (faaliyet başına `official_ids`), 385× `subprograms`, 385× `programs`, 226× `indicator_values`, 182× `activity_cost_values`, 162× `structure_changes`.

**Neden (kanıt):**
1. `department_snapshot` (program_service.py:226) satır 235–237 ve 243–244 her kart/gösterge/faaliyet için `db.get(SubProgram, …)` + `.program` (satır 235/237) ve `a.cost_values`/`i.values`/`official_ids` (satır 243–244) ile satır satır tembel yükleme yapar — `selectinload` yok. `cost_reconciliation` (satır 412) bunu 33 müdürlük için tekrarlar → ~1100 tek-satır sorgu.
2. `approved_book_provenance` (program_service.py:747) `json.loads(batch.payload_json)` ve `json.loads(batch.snapshot_json)` ile 33 ImportBatch'in tam içeriğini açar (satır 793–794) ve her müdürlük için `_serialize_department_state` (satır 803) çağırır — yalnız metadata yeterliyken tam snapshot yüklenir (CIV-175/176 ile aynı neden sınıfı).
3. `period_name`/`name_for_year`/`live_changes` (structure_service.py:54/75/84) `department_names` (program_routes.py:374) ve `period_departments` içinde her müdürlük için tekrar çağrılır → 162 `structure_changes`.

**En küçük düzeltme + ölçülmüş tahmin:** `department_snapshot`'ta `selectinload(ReportCard.subprogram).selectinload(SubProgram.program)`, `selectinload(Indicator.values)`, `selectinload(Activity.cost_values)` ve `activity_catalogue_links` için tek toplu sorgu. Yerel deneyde SQL **2853 → 1750** (−%39), duvar saati 1.48 → 1.33 s düştü. Kalan ~1750'nin çoğu `approved_book_provenance`'ın `_serialize_department_state` + snapshot `json.loads` maliyeti; dar sonraki adım snapshot kolonlarını `defer` edip yalnız gereken anahtarları okumaktır (CIV-175 envanterindeki okuyucu listesi bu yolda geçerli kalır).

## 5. step2 — POST `/report-builder/publish-approved-book` (onaylı kitaptan yayınla)

- Duvar saati: **2.59–2.62 s**; SQL: **7395**; SQL süresi: **~0.12 s**; durum 303.
- En pahalı fonksiyonlar (cumtime):
  - `app/program_routes.py:547(publish_approved_book)` 2.581 s
  - `app/activity_contract_service.py:143(freeze_program_payload)` 0.939 s
  - `app/program_service.py:539(publication_checks)` 0.875 s
  - `app/program_service.py:401(cost_reconciliation)` 0.857 s (2 çağrı)
  - `app/program_service.py:226(department_snapshot)` 0.738 s (68 çağrı)
  - `app/program_service.py:582(book_snapshot)` 0.613 s
  - `app/program_service.py:459(make_rows)` 0.431 s (1910 çağrı)
  - `app/program_service.py:747(approved_book_provenance)` 0.415 s
- En sık SQL: 837× `subprograms`, 770× `programs`, 728× `activity_catalogue_links`, 678× `indicator_values`, 546× `activity_cost_values`, 259× `departments`, 226× `INSERT indicator_identities`.

**Neden (kanıt):** step1'deki `cost_reconciliation` **üç kez** yeniden hesaplanır — `builder`'ın (step1) + `publication_checks` (program_service.py:575) + `book_snapshot`/`freeze_program_payload` (program_service.py:605, activity_contract_service.py:145). Her biri `department_snapshot`'ı 33 kez çağırır → bu istekte toplam **68 `department_snapshot` çağrısı** ve `make_rows` 1910 çağrı. Ayrıca `freeze_program_payload` → `ensure_identity` her gösterge için ayrı `INSERT indicator_identities` (226 adet) üretir.

**En küçük düzeltme + ölçülmüş tahmin:** `cost_reconciliation` sonucunu istek başına bir kez hesaplayıp `publication_checks` ve `book_snapshot`'a aynı `snapshots` ile iletmek + `department_snapshot`'ta eager yükleme. Yerel deney: tek başına `cost_reconciliation` belleğe almak SQL'i 7395 → 7391'e indirdi (maliyet mutabakatın kendisinde değil, tekrar eden `department_snapshot` N+1'indedir); asıl kazanç eager `department_snapshot` ile gelir (step1'de −%39 SQL). 226 kimlik `INSERT`'ini toplu (batch) yazmak ikinci dar kazançtır.

## 6. step3 — POST `/activity-sections/years` (EK-1 raporlarını oluştur)

- Duvar saati: **0.13–0.16 s**; SQL: **1369**; SQL süresi: **0.009 s**; durum 303.
- En pahalı: `app/activity_sections_service.py:179(create_year)` 0.130 s; `app/activity_sections_service.py:123(definitions)` 0.014 s (34 çağrı).
- En sık SQL: 1225× `INSERT ar_section_contents` (34 belge × ~36 bölüm), 34× `INSERT ar_documents`, 34× `SELECT ar_section_definitions` (`definitions` belge başına), 34× `INSERT ar_content_events`.

**Neden (kanıt):** `create_year` (activity_sections_service.py:199–235) her belge için `definitions(db, doc)` çağırır (satır 226 → 34 kez aynı sürüm tanımlarını yeniden sorgular) ve her bölüm için tek tek `ARSectionContent` ekler (satır 229). 1225 ayrı `INSERT` + 34 tekrarlanan tanım sorgusu = 1369 sorgu. SQLite'ta hızlıdır (0.009 s) ama PostgreSQL'de 1369 gidiş-dönüştür.

**En küçük düzeltme + tahmin:** tanımları bir kez çekip `definitions` çağrısını döngü dışına almak ve `ARSectionContent` eklemelerini `bulk_save_objects`/`executemany` ile toplu yazmak; 1369 sorgu ~40'a iner. (Ölçüm deneyi yapılmadı; yukarıdaki sayım doğrudan sorgu dağılımından gelir.)

## 7. step4 — GET `/activity-sections?period_id=2` (İdare raporuna geçiş, en yüksek öncelik)

- Duvar saati: **0.40–0.56 s**; SQL: **2442 (ilk, taze oturum) / 1958 (sonraki, önbellekli)**; SQL süresi: **~0.025 s**; durum 200.
- En pahalı fonksiyonlar (cumtime):
  - `app/activity_sections_routes.py:315(index)` 0.552 s
  - `app/activity_sections_routes.py:295(listing)` 0.453 s
  - `app/activity_sections_service.py:466(report_data)` 0.447 s (34 çağrı)
  - `app/activity_financial_service.py:395(financial_data)` 0.261 s (34 çağrı)
  - `app/structure_service.py:54(period_name)` 0.175 s (396 çağrı)
  - `app/structure_service.py:75(name_for_year)` 0.057 s (348 çağrı)
  - `app/structure_service.py:84(live_changes)` (348 kez `structure_changes`)
- En sık SQL: 450× `reporting_periods`, 429× `department_scopes`, 348× `structure_changes`, 297× `departments`, 169× `ar_financial_entries`, 99× `ar_documents`.

**Neden (kanıt):** `listing` (activity_sections_routes.py:295–313) 34 belge için `report_data` + `ar_similarity` çağırır; her belgenin ad/sayfa gösterimi `period_name` → `name_for_year` → `live_changes` zincirini (structure_service.py:54/75/84) her hücrede yeniden çalıştırır ve `live_changes` her seferinde tüm `structure_changes` tablosunu çeker (satır 85) + `json.loads(snapshot_json)` yapar (satır 78). Sonuç: 348 `structure_changes` + 429 `department_scopes` + 450 `reporting_periods` tekrarlı sorgu. İlk koşunun 2442, sonraki koşuların 1958 olması Session kimlik önbelleğinden; üretim her istekte taze Session kullandığı için **2442 temsilidir**.

**En küçük düzeltme + ölçülmüş tahmin:** `live_changes`/`period_name`/`name_for_year` sonuçlarını istek başına (Session `db.info`) belleğe almak. Yerel deneyde SQL **2442 → 2096** (−%14, 348 `structure_changes` sorgusu ve `json.loads` tekrarı kalkar), duvar saati 0.555 → 0.427 s düştü. Kalan 2096'nın çoğu `report_data`/`financial_data`/`resources` belge başına döngüsüdür; ikinci dar adım `report_data` içindeki `period_name` şablon çağrılarını tek noktada hesaplamaktır.

## 8. SQLite vs PostgreSQL (Render etkisi)

SQLite'ta bir sorgu süreç içi bir fonksiyon çağrısıdır (toplam SQL süresi ≤0.12 s). Render'da PostgreSQL ağ üzerindedir; her sorgu bir gidiş-dönüştür. ~1 ms gecikme ile:

| Adım | SQL ifadesi | ~1 ms/tur | ~5 ms/tur |
| --- | ---: | ---: | ---: |
| step1 | 2852 | ~2.9 s | ~14 s |
| step2 | 7395 | ~7.4 s | ~37 s |
| step3 | 1369 | ~1.4 s | ~6.8 s |
| step4 | 2442 | ~2.4 s | ~12 s |

Yani loopback SQLite'ta görünmeyen N+1 maliyeti, Render'da provadaki 6–11 s duvar saatinin **üstüne** eklenir. Düzeltme önceliği bu yüzden query sayısını azaltmaktır; step2 (7395) ve step1/step4 (2852/2442) önceliklidir.

## 9. Doğrulama ve sınırlar

- `python scripts/profile_strateji_steps.py --runs 3` tam 2026 verisiyle **exit 0**; kurulum 33/105/226/182/1270 doğrulandı.
- `python scripts/profile_strateji_steps.py --tiny --runs 1` **exit 0**; duman testi `tests/test_profile_strateji_steps.py` aynı yolu kullanır.
- Ölçülen düzeltme tahminleri yerel, geçici monkeypatch deneyleridir; **patch'e dahil edilmedi**.
- `python -m compileall -q scripts/profile_strateji_steps.py tests/test_profile_strateji_steps.py` ve `git diff --check` başarılı.
- Doğrulanmadı: Render/üretim PostgreSQL kapasitesi, gerçek ağ gecikmesi, tarayıcı `networkidle`/font/render süresinin sunucu dışı payı ve önerilerin tam regresyon testleri. SQLite sonuçları Render davranışını doğrudan kanıtlamaz; yalnızca aynı büyüklük sınıfını gösterir.

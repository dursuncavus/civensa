# CIV-198 — Strateji adımlarında sorgu sayısı

CIV-196 (`fa55cdba`, PR #447) profil dosyaları görev dalına alındı; bu dosyalar değiştirilmedi. Ölçümler aynı makinede, atılabilir SQLite ve aynı sentetik 2026 verisiyle (33 müdürlük, 105 kart, 226 gösterge, 182 faaliyet, 1270 ekonomik değer) yapıldı. Canlı veritabanına bağlanılmadı; PR birleştirilmedi, dağıtım yapılmadı.

## Değişiklikler

- **step1:** `program_service.py` dönem satırlarını bir kez alıp müdürlüğe göre grupluyor; alt program/program ve katalog bağlantıları toplu okunuyor. `source_comparison_service.py` aynı toplu snapshot yolunu kullanıyor. `approved_book_provenance` kaynak/hash/audit kontrolleri korunuyor.
- **step2:** `activity_contract_service.py` gösterge kimliklerini toplu INSERT ile yazıyor; mevcut kimlik kilitleri, önceki tanımlar ve tüm dönemlerdeki revizyon numaraları toplu okunuyor. Tanımlar eski sırayla tek tek oluşturuluyor; numaralama ve tekrar kullanım kontrolleri korunuyor. `program_service.py` doğrulama okumaları da toplulaştırıldı; yayın kontrolleri atlanmadı.
- **step3:** `ar_section_contents` yazan servis **`activity_sections_service.py`**. Bölüm tanımları sürüm başına bir kez okunuyor; içerik satırları belge başına executemany ile yazılıyor. Önceki yıl kopyası, kaynak kimlikleri, audit ve tablo anahtarı üretimi korunuyor.
- **step4:** `structure_service.py` ad çözümlemesinde dönem/kapsam/müdürlük satırlarını, etkin yapı kararlarını ve açılmış JSON içeriğini yalnız servis çağrısının yığını boyunca tutuyor. `report_data` ve diğer toplu okuyucular bu kapsamı kullanıyor. `finally` her çıkışta kapsamı siliyor; yapı/kapsam/ad yazıları flush sırasında temizliyor. İstekler arasında cache yok.

**Sıra koruması:** PostgreSQL üzerinde düz `selectinload`, aynı yıla ait değerlerin sırasını değiştirdi. Bu yüzden çocuk değerler, eski `WHERE owner_id / ORDER BY year` alt sorgularını `UNION ALL` ile en fazla 200 sahiplik gruplar halinde birleştirerek okunuyor. Mevcut yüklenmiş koleksiyonlar korunuyor. Özel ORM okuma adaptörü olan oturumlarda özgün ilişki okuyucusu korunuyor (tarihsel migration testlerindeki ertelenmiş sütunlar dahil). Dict anahtarları ve çıktı sıraları değiştirilmedi.

## Profil

Önce ve sonra: `python scripts/profile_strateji_steps.py --runs 3`. SQL sayımı istemci `before_cursor_execute` çağrılarını ölçer; executemany bir çağrıdır. Aşağıdaki üçlüler üç koşuyu gösterir.

| Adım | Önce SQL | Sonra SQL | Hedef | Sonuç |
| --- | --- | --- | ---: | --- |
| step1 | [2853, 2852, 2852] | [1139, 1138, 1138] | ≤ 1400 | Sağlandı |
| step2 | [7395, 7395, 7395] | [2010, 2010, 2010] | ≤ 2500 | Sağlandı |
| step3 | [1370, 1369, 1369] | [113, 112, 112] | ≤ 200 | Sağlandı |
| step4 | [2443, 1958, 1958] | [1150, 1048, 1048] | ≤ 1200 | Sağlandı |

### Önce — betiğin özet satırları

```text
## step1 — 2026 onaylı kitap yayın hazırlığı
  route: /report-builder  | status: [200]
  wall (s): [3.083, 2.883, 2.63]
  SQL sayısı: [2853, 2852, 2852]  | SQL süresi (s): [0.087, 0.077, 0.071]
## step2 — Onaylı kitaptan yayınla
  route: /report-builder/publish-approved-book  | status: [303]
  wall (s): [5.532, 5.787, 5.527]
  SQL sayısı: [7395, 7395, 7395]  | SQL süresi (s): [0.23, 0.244, 0.232]
## step3 — 2026 EK-1 raporlarını oluştur
  route: /activity-sections/years  | status: [303]
  wall (s): [0.315, 0.254, 0.276]
  SQL sayısı: [1370, 1369, 1369]  | SQL süresi (s): [0.016, 0.015, 0.017]
## step4 — İdare raporuna geçiş
  route: /activity-sections  | status: [200]
  wall (s): [1.181, 0.909, 1.131]
  SQL sayısı: [2443, 1958, 1958]  | SQL süresi (s): [0.065, 0.051, 0.056]
```

### Sonra — betiğin özet satırları

```text
## step1 — 2026 onaylı kitap yayın hazırlığı
  route: /report-builder  | status: [200]
  wall (s): [3.463, 2.785, 2.652]
  SQL sayısı: [1139, 1138, 1138]  | SQL süresi (s): [0.062, 0.056, 0.053]
## step2 — Onaylı kitaptan yayınla
  route: /report-builder/publish-approved-book  | status: [303]
  wall (s): [5.459, 5.719, 4.864]
  SQL sayısı: [2010, 2010, 2010]  | SQL süresi (s): [0.171, 0.168, 0.161]
## step3 — 2026 EK-1 raporlarını oluştur
  route: /activity-sections/years  | status: [303]
  wall (s): [0.221, 0.123, 0.106]
  SQL sayısı: [113, 112, 112]  | SQL süresi (s): [0.013, 0.008, 0.008]
## step4 — İdare raporuna geçiş
  route: /activity-sections  | status: [200]
  wall (s): [1.265, 0.668, 0.644]
  SQL sayısı: [1151, 1048, 1048]  | SQL süresi (s): [0.041, 0.043, 0.043]
```

Dört hedef de üç koşuda sağlandı. İlk soğuk step1 duvar süresi artabiliyor: sıralamayı koruyan toplu sorguların derleme maliyeti var. Amaç ağ gidiş-dönüşlerini azaltmak; SQLite süreleri Render gecikmesi/SLA ölçümü değildir.

## Doğrulama

- `tests/reference/civ198_snapshots.py`: değişiklik öncesi `fa55cdba` okuyucularının yalnız testte tutulan kopyası. Küçük sentetik veri; yapı değişikliği, kapsam dışı müdürlük ve tarihsel yıl içeriyor. `json.dumps(..., sort_keys=False)` ile kitap, her müdürlük, paket ve tarihsel/güncel maliyet mutabakatı byte eşitliği PostgreSQL 18 ve SQLite üzerinde doğrulandı.
- Yeni regresyonlar: aynı çağrıda ad değişikliği ve karar iptali hemen görünür; hata/normal dönüşte cache silinir; gösterge/faaliyet sayısı artınca snapshot sorguları satır başına artmaz. **12 geçti** (`no_autoflush` davranışı dahil). Tarihsel migration regresyonlarıyla birlikte **19 geçti**; profil/yapı değişikliği/faaliyet bölümü odaklı takım **56 geçti**.
- PostgreSQL 18 üzerinde mevcut program, yayın kapıları, faaliyet sözleşmesi ve mutabakat testleri çalıştırıldı. Tarayıcı testleri sistem Chromium ile çalıştırılıyor (`CIVENSA_CHROMIUM_PATH=/usr/bin/chromium`). Tam test takımı ve PR CI sonucu PR açıklamasında kaydedilir.

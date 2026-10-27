# CIV-129 · Bütçe aktarma

017 ve 018, yalnız bu sayfalarda yüklenen `budget-reallocation.css` ile mevcut tasarım sistemi bileşenlerine taşındı. Tablolar kendi alanlarında kayar; alanlar masaüstünde üç sütun, mobilde tek sütundur. Açıklamalar, seçim satırları ve önizleme özetleri D-292 gereği en fazla 44rem genişliğindedir. Hata paneli `role="alert"` ve başlangıçtaki `hidden` davranışını korur.

Görünür metin değişikliklerinin tamamı (yalnız `page_title`):

- `Bütçe Aktarma` → `Bütçe aktarma`
- `Yeni Bütçe Aktarması` → `Yeni bütçe aktarması`

Başlangıç şablonları `tests/fixtures/budget_reallocation_start/` altında byte düzeyinde korunur. Donmuş sözleşme testi tüm kimlikleri, JavaScript sınıflarını, alan niteliklerini, seçenekleri/değerleri, bağlantıları, boş başlık dahil tablo başlıklarını ve diğer görünür metinleri karşılaştırır. Başlangıçta dayanak ve uygulama aynı üçüncü paneldedir; mevcut dört aşamalı akış ve bu panel yapısı korunmuştur.

## Görseller

Tam sayfa Chromium görüntüleri; aynı sentetik veri ve 1050px pencere yüksekliği. `before` donmuş başlangıç şablonunu, `after` güncel şablonu kullanır. Önizleme gerçek yerel API yanıtıyla oluşur. Liste, bir normal işlem ve bir telafi işlemi içerir. Her PNG 1.5 MB sınırının altındadır.

| Durum | Önce 1440 | Sonra 1440 | Önce 390 | Sonra 390 |
| --- | --- | --- | --- | --- |
| 017 · Kayıtlı | [PNG](before-017-rows-1440.png) | [PNG](after-017-rows-1440.png) | [PNG](before-017-rows-390.png) | [PNG](after-017-rows-390.png) |
| 017 · Boş | [PNG](before-017-empty-1440.png) | [PNG](after-017-empty-1440.png) | [PNG](before-017-empty-390.png) | [PNG](after-017-empty-390.png) |
| 018 · İlk adım, iki satır | [PNG](before-018-step1-1440.png) | [PNG](after-018-step1-1440.png) | [PNG](before-018-step1-390.png) | [PNG](after-018-step1-390.png) |
| 018 · Önizleme | [PNG](before-018-preview-1440.png) | [PNG](after-018-preview-1440.png) | [PNG](before-018-preview-390.png) | [PNG](after-018-preview-390.png) |

## Doğrulama

Geçici yerel PostgreSQL 16 ve Chromium kullanılır. Testler gerçek oturum/CSRF ile önizleme, kayıt eleme, yeniden hesaplama, dayanak ve uygulama çağrılarını çalıştırır. Her iki genişlikte sayfa taşması, üç müdürlük ekleme/kaldırma, hata görünürlüğü, 44rem sınırı, odak/üzerine gelme durumları dahil en az 4.5:1 metin kontrastı ve CSS büyük harf dönüşümü kontrol edilir.

```sh
python -m pytest -q --require-postgres tests/test_budget_reallocation_design.py tests/test_budget_reallocation_ui.py tests/test_budget_reallocation.py tests/test_design_shell.py tests/test_pp_errors_forms.py tests/test_pp_reopen.py
python -m pytest -q --require-postgres -n 5 --dist loadfile --max-worker-restart=0
```

Görselleri aynı testlerden üretmek için `CIVENSA_CIV129_SCREENSHOTS=docs/design/rollout/civ-129` kullanılır. `CIVENSA_TEST_POSTGRES_URL` geçici test veritabanına ayarlanmalıdır. Bu ortamda `CIVENSA_CHROMIUM_PATH=/usr/bin/chromium` kullanıldı. Canlı veri kullanılmadı; Firefox/Safari doğrulaması yapılmadı.

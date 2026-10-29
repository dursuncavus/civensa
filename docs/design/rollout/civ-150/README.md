# CIV-150 görsel kanıtları

`/activity-mapping` sayfasının 1440 × 900 ve 390 × 900 tarayıcı pencerelerinde alınan tam sayfa PNG görüntüleri. Her dosya 1,5 MB sınırının altındadır.

| Durum | 1440 önce | 1440 sonra | 390 önce | 390 sonra |
| --- | --- | --- | --- | --- |
| Dolu kuyruk | [Önce](before-populated-1440.png) | [Sonra](after-populated-1440.png) | [Önce](before-populated-390.png) | [Sonra](after-populated-390.png) |
| Boş kuyruk | [Önce](before-empty-1440.png) | [Sonra](after-empty-1440.png) | [Önce](before-empty-390.png) | [Sonra](after-empty-390.png) |

Yalnız sentetik veriler kullanıldı: güçlü (%80) ve zayıf (%35) öneriler, alt programı mevcut bir faaliyet, seçeneksiz ikinci müdürlük, geri alınabilir ve kilitli CSV işlemleri. Önce/sonra aynı bağlamı kullanır; başlangıç şablonu `tests/fixtures/activity_mapping_start.html` dosyasında byte düzeyinde korunur. Görüntüler seçim yapılmadan alınır. Tam sayfa yakalamada yapışkan çubuk metinlerin üzerine gelmesin diye içerik sonuna kaydırılır; çubuğun içerik başında, ortasında ve sonunda görünürlüğü ayrıca test edilir.

`tests/test_activity_mapping_design.py`, gerçek şablonları, statik dosyaları ve değişmeyen JavaScript'i Chromium içinde çalıştırır. CSV önizleme yanıtları testte taklit edilir. Görüntüleri yeniden üretmek için geçici yerel PostgreSQL 16+ yapılandırıp `CIVENSA_CIV150_SCREENSHOTS=docs/design/rollout/civ-150 python -m pytest -q --require-postgres tests/test_activity_mapping_design.py` çalıştırılır.

Görünür metin değişikliği yoktur. Canlı veritabanına bağlanılmadı; dağıtım yapılmadı.

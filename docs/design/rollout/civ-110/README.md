# CIV-110 — Süresi dolan gönderim

Sentetik belediye, müdürlük ve İç Kontrol eylemleri; geçici yerel PostgreSQL 18.
Son giriş 25.10.2026, sunucunun `today(db)` kaynağı testte 26.10.2026 olarak sabitlenmiştir.
Gerçek oturum, route, şablon ve statik dosyalar TestClient üzerinden Chromium'a sunulmuştur.

- [1440 px](department-expired-1440.png)
- [390 px](department-expired-390.png)

Her iki görüntüde de taslak paket salt okunurdur. Gönderim düğmesinin yerinde
“Gönderim süresi doldu (son giriş: 25.10.2026). Süre uzatımı için Strateji birimiyle görüşün.”
görünür. Mobilde metin satırlara bölünür; yatay taşma yoktur. PNG dosyaları 1,5 MB altındadır.

Üretim komutu: `CIVENSA_CIV110_SCREENSHOTS=docs/design/rollout/civ-110 python -m pytest -q --require-postgres tests/test_ic_our_actions_design.py -k expired_department_browser`
(Geçici test veritabanı ve Chromium önceden yapılandırılır.)

`monitoring_shared.html` dondurulmuş fixture'ında yalnız gönderim formu satırı
güncellendi: süre dolmadığında aynı form, dolduğunda yukarıdaki açıklama üretilir.
Batch başlığı ile Strateji onay, iade ve yeniden açma formları korunmuştur.

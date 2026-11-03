# CIV-174 — İlk yüklemeden sonra yayın kontrolleri

CIV-169 `loaded_books` hazırlığıyla aynı `inspect_import(..., year=2026)`; geçici, Alembic head seviyesine taşınmış PostgreSQL 16. Yayın/onay hazırlığı yapılmadı.

Tekrar üretme: yerel `CIVENSA_TEST_POSTGRES_URL` ile `python -m tests.civ174_checks`.

| Yıl | Check id ailesi | Kontrol sayısı | Hata sayısı | Bir örnek |
|---|---|---:|---:|---|
| 2026 | `scope` | 35 | 2 | Araştırma ve Geliştirme Müdürlüğü: dönem kapsamı belirtilmeli. |
| 2026 | `data` | 33 | 2.338 | Afet İşleri ve Risk Yönetimi Müdürlüğü: Toplanma alanlarının modernizasyonu: sorumlu harcama birimleri kataloğu bağlantısı eksik. |
| 2026 | `approval` | 33 | 33 | Afet İşleri ve Risk Yönetimi Müdürlüğü: onay eksik. |
| 2026 | `sections` | 1 | 1 | Kitabın genel bilgi bölümleri hazırlanmalı. |
| 2026 | `catalogue` | 1 | 0 | — |
| 2026 | `subtotal` | 2.868 | 61.167 | Afet İşleri ve Risk Değerlendirme Müdürlüğü / Toplanma alanlarının modernizasyonu: program, alt program, kart veya katalog bağlantısı eksik ya da kapsamı uyuşmuyor. Faaliyet Eşleştirme ve Performans Kartları ekranlarında bağlantıları tamamlayın. |
| 2027 | `scope` | 35 | 35 | Afet İşleri ve Risk Yönetimi Müdürlüğü: dönem kapsamı belirtilmeli. |
| 2027 | `data` | 0 | 0 | — |
| 2027 | `approval` | 0 | 0 | — |
| 2027 | `sections` | 1 | 1 | Kitabın genel bilgi bölümleri hazırlanmalı. |
| 2027 | `catalogue` | 1 | 0 | — |
| 2027 | `subtotal` | 570 | 1.714 | İşletme ve İştirakler Müdürlüğü / 0001.Çocuk Bakımevleri ile Çocuk Oyun ve Etkinlik Merkezlerinde çocuklara yönelik olarak okul öncesinde sosyal uyumu sağlamaya, motor ve bilişsel becerilerini geliştirmeye yönelik programları gerçekleştirmek: program, alt program, kart veya katalog bağlantısı eksik ya da kapsamı uyuşmuyor. Faaliyet Eşleştirme ve Performans Kartları ekranlarında bağlantıları tamamlayın. |

Her kontrolün bütün hata mesajları, tekrarları ve check id değerleriyle [all-errors.md.gz](all-errors.md.gz) dosyasındadır (`gzip -dc` ile okunabilir).

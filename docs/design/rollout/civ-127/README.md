# CIV-127 — Denetim geçmişi

Denetim geçmişi aynı filtre, CSV, tablo içeriği ve sayfalama davranışını koruyarak sayfaya özel `audit.css` ve tasarım sistemi tokenlarına taşındı. Filtre alanları 1024 px ve üzerindeki genişliklerde tek satırda, dar ekranlarda dikey sıralıdır. Ayrıntı sütunu uzun metni sarar; mobil tabloda yatay kaydırma yalnızca tablo alanındadır.

## Görünür metin değişiklikleri

- Sayfa başlığı: `Denetim Geçmişi` → `Denetim geçmişi`.
- Yeni mobil/yatay kaydırma açıklaması: `Tablonun tamamını görmek için yatay kaydırın.`

Gezinme menüsündeki `Denetim Geçmişi` metni değiştirilmedi.

## Ekran görüntüleri

Tam sayfa Chromium PNG'leri sentetik kayıt ve filtrelerle üretildi. Başlangıç görüntüleri dondurulmuş özgün şablondan, son görüntüler tasarım sistemi şablonundan alınmıştır. Her dosya 1.500.000 bayttan küçüktür.

| Durum | 1440 px | 390 px |
| --- | --- | --- |
| Filtre uygulanmış sentetik kayıt | [Önce](before-filtered-1440.png) · [Sonra](after-filtered-1440.png) | [Önce](before-filtered-390.png) · [Sonra](after-filtered-390.png) |
| Filtre sonucu boş | [Önce](before-empty-1440.png) · [Sonra](after-empty-1440.png) | [Önce](before-empty-390.png) · [Sonra](after-empty-390.png) |

## Doğrulama

`tests/test_audit_design.py` özgün şablonun bayt düzeyinde korunmuş fixture'ını SHA-256 ile doğrular. Dönemli/dönemsiz durum, seçili filtre, boş sonuç, tablo satırı ve önceki/sonraki sayfa bağlantılarında form alanları, seçenekler, metinler ve hedefler dondurulmuş şablonla karşılaştırılır. Tarayıcı denetimleri 1440, 1024 ve 390 px'te sayfa taşmasını, filtre satır düzenini, 300 karakterlik ayrıntıyı, metin dönüşümünü ve görünür renk kontrastını doğrular.

Testler PostgreSQL destekli sentetik veritabanı ve Chromium kullanır. Canlı veritabanına bağlanılmadı; Firefox, Safari ve ekran okuyucu davranışı doğrulanmadı.

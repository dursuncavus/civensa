CIV-166 ekran kanıtları

Sentetik Test Belediyesi / Test Müdürlüğü verileri, geçici yerel PostgreSQL 17 ve Chromium kullanıldı.

- 3 değişen durum × 2 genişlik (1366 ve 390) = 6 PNG; her biri 1,5 MB altında.
- `unit-financial-warning-*`: III.A.1 malî panelinde tek uyarı; hesaplanan 12.550,23, bildirilen 12.500,23, fark -50 ve Mali Hizmetler sorumluluk cümlesi.
- `unit-section-warning-*`: tamamlanma listesinde ayrı “Uyarılar (gönderimi engellemez)” başlığı; bölüm Hazır.
- `unit-submitted-warning-*`: başarılı gönderim ve sabit kopyadaki 1 uyarıyı belirten mesaj.
- 6 durum/genişlik kontrolünde 0 yatay sayfa taşması, 0 JavaScript hatası; yeni başlık, uyarı ve mesaj hedefleri bulundu.
- Mevcut `.ar-warning` renkleri korunuyor: #8a5a00 / #fff4d6, kontrast 5,41:1 (AA).
- Ortak şablon/CSS/JS değişmedi; tüm ekranları kapsayan tarama yapılmadı (D-252).

Görüntüler: `tests/test_activity_financial_warnings_ui.py` testi, `CIVENSA_UI_SCREENSHOTS` bu klasöre ayarlanarak üretildi. Yakalama betiği veya özet JSON eklenmedi.

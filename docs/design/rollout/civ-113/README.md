# CIV-113 — PP tamamlanma listesi

041 ekranı; sentetik dört satır (2 Tamam, 1 Boş, 1 Eksik), sıfır adet ve
boşluksuz uzun adlarla Chromium'da kontrol edildi. Canlı veritabanı kullanılmadı;
testler Docker'da geçici PostgreSQL 18 üzerinde çalıştırıldı.

| Görsel | Kapsam |
| --- | --- |
| [1440 px](manifest-1440.png) | Sayfa üstü, dönem araç çubuğu, açıklamalar ve üç durumun tamamı |
| [390 px](manifest-390.png) | Sayfa üstü, dikey araç çubuğu, kaydırma ipucu ve saran uzun adlar |
| [390 px durum sütunları](manifest-table-status-390.png) | Aynı tablonun sağa kaydırılmış görünümü; üç metinli durum rozeti |

Her PNG 1,5 MB altındadır. 390 px'de sayfa taşmaz; tablo kendi odaklanabilir
bölgesinde yatay kayar. Açık kaydırma ipucu mobilde görünür.

`tests/test_pp_manifest_design.py`: başlangıç şablonunun SHA-256 ile korunan,
baytları aynı fixture'ı üzerinden GET formu, seçenekler/seçili dönem, alan
bağlantıları, bütün href ve sorgu parametreleri, satır anahtarları, adları,
türleri, sayıları ve durumları karşılaştırılır. Gerçek, üç durumlu ve boş
liste senaryoları kapsanır. Müdürlük kullanıcısının 403 yanıtı korunur.
Tarayıcı kontrolleri 1440/390 px'de sayfa taşmasını, büyük harf dönüşümü
olmamasını, normal/hover/focus metin çiftlerinde en az 4,5:1 kontrastı ve
`period_id` gönderimini doğrular. CSS yalnızca bu ekranda yüklenir.

Görseller yeni testteki isteğe bağlı `CIVENSA_CIV113_SCREENSHOTS` çıktı
diziniyle üretildi; depoya yakalama betiği veya JSON eklenmedi.

## Metin değişiklikleri

- Kitap Bölümleri ve Dönem Kopyalama → Kitap bölümleri ve dönem kopyalama
- Word İçe Aktarma → Word içe aktarma
- Bölüm / Tablo Adı → Bölüm / tablo adı
- İçeriği Aç → İçeriği aç
- Tamam: / Boş: / Eksik: → Tamam / Boş / Eksik (tanım listesi terimleri)
- Yeni özet: `N bölüm/tablo · X tamam · Y boş · Z eksik`
- Yeni mobil ipucu: `Tablonun devamını görmek için yatay kaydırın.`

`PP Tamamlanma Listesi` ve `Dönemi Göster`, mevcut
`tests/test_pp_manifest_ui.py` birebir eşleşmeleri nedeniyle görev paketinin
istisnasına göre korundu. Mevcut testler değiştirilmedi.

Varsayım: başlangıçtaki ayrı Tür sütunu korunarak ikincil metin biçimi uygulandı.
Rota, veri üretimi, yetkiler ve bağlantı hedefleri aynı kaldı.

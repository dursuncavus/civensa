# CIV-125 — Güvence beyanı

EK-1/EK-2/EK-3 düzenleyicisi, sayfaya özel `assurance-editor.css` ile tasarım sistemi tokenlarına taşındı. Eski stil bağlantısı korundu. Yer/tarih 1024 px ve üzerinde yan yana; görev dönemleri odaklanabilir, kendi içinde kayan bir tabloda; çekince ve gerekçe aynı kutuda. Kilitli beyan 72ch ölçüsünde belge bloğunda, imza etiketleri değerlerinin yanında, dipnotlar küçük numaralı listede gösterilir. Salt okunur durumda form ve kayıt düğmesi önceki koşullarla gizlenir.

## Görünür metin değişiklikleri

- Sayfa başlığı: `Güvence Beyanı` → `Güvence beyanı`.
- Geri bağlantısı: `← EKLER ve tamamlanma durumu` → `EKLER ve tamamlanma durumu`.
- Yeni tablo açıklaması: `Tüm görev dönemi alanlarını görmek için tabloyu yatay kaydırın.`

Hukuki metinler, yasal etiketler ve sunucu mesajları değiştirilmedi. `assurance_statement.html` başka sayfalarda da kullanılır; bu dosyaya dokunulmadı.

## Ekran görüntüleri

Tam sayfa PNG dosyaları; tamamı 1.500.000 bayttan küçük. Yalnızca sentetik test verileri, gerçek TestClient oturumu ve CSRF kullanıldı.

| Durum | 1440 px | 390 px |
| --- | --- | --- |
| EK-1, düzenlenebilir, çekinceli kayıt | [Masaüstü](ek1-editable-1440.png) | [Mobil](ek1-editable-390.png) |
| EK-3, düzenlenebilir | [Masaüstü](ek3-editable-1440.png) | [Mobil](ek3-editable-390.png) |
| EK-3, salt okunur | [Masaüstü](readonly-1440.png) | [Mobil](readonly-390.png) |
| EK-1, eksik gerekçe hatası | [Masaüstü](error-1440.png) | [Mobil](error-390.png) |

## Doğrulama

`tests/test_assurance_editor_design.py`, başlangıç şablonunun baytları korunmuş kopyasını SHA-256 ile doğrular. Üç beyan × düzenlenebilir/salt okunur × hata var/yok × 0/2/99/100 kayıt için 48 senaryoda form yöntemi/hedefi, tüm kontrol öznitelikleri ve değerleri, textarea içerikleri, satır sayısı ve geri bağlantı hedefi karşılaştırılır. Kilitli beyanın oluşturulan HTML bloğu bayt düzeyinde aynıdır.

İki tarayıcı senaryosu 1440/390 px boyutlarında yatay sayfa taşmasını, mobil tablo kaydırmasını ve klavyeyle kaydırmayı, yer/tarih hizasını, görünür metinlerin hesaplanan renklerinde en az 4,5:1 kontrastı, EK-1 için gerçek form kaydını ve hatalı kayıtta tüm girilen alanların korunmasını doğrular. EK-2 müdürlük görünümü ve EK-3 düzenlenebilir/salt okunur koşulları da gerçek rotalarda kontrol edilir.

Çalıştırma: `CIVENSA_TEST_POSTGRES_URL=<yalnızca geçici yerel PostgreSQL> CIVENSA_CHROMIUM_PATH=/usr/bin/chromium python -m pytest -q --require-postgres`. Kanıt üretimi için yalnızca yeni test modülüne `CIVENSA_UI_SCREENSHOTS=docs/design/rollout/civ-125` verilir.

Canlı veritabanına bağlanılmadı. Tarayıcı kanıtı Chromium ile sınırlıdır; Firefox/Safari ve ıslak/elektronik imza işlemleri bu çalışmada doğrulanmadı.

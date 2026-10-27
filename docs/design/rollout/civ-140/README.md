# CIV-140 · Gösterge özeti grafiksel

Gösterge gerçekleşme özeti, her rapor revizyonunda veri durumlarını bir bakışta sayar. Gösterge kartlarında gerçekleşme, birim, durum, hedef ve sayısal fark aynı dar blokta; sayıların altında nötr bir bullet bar gösterilir. Bar yalnız doğrulanmış, sıfır olmayan sayısal hedef ve doğrulanmış sayısal gerçekleşme varsa çizilir. Hedef ve gerçekleşme arasındaki başarı yönü yorumlanmaz; renkler yalnız veri durumunu belirtir.

Tanım ve en son kanıtlar kompakt gösterilir; tanım ve geçmiş ayrıntıları kapalı `<details>` alanlarında kalır. Yeni gerçekleşme formu mevcut alanları ve gönderim davranışını değiştirmeden ayrı bir başlıkla ayrılır.

## Yeni görünen metinler

- Rapor özeti, sıfır olmayan sayımlar için: `{{ sayı }} gösterge`, `{{ sayı }} Doğrulanmış`, `{{ sayı }} İncelenmeli`, `{{ sayı }} Eksik`, `{{ sayı }} Kayıt yok`, `{{ sayı }} açıklama bekliyor`. Sayım çiftleri `·` ile ayrılır.
- Gösterge özeti: `Fark: {{ sayısal fark veya Hesaplanmadı }}` ve gerçekleşme değeri yanında birim.
- Tanım açıklaması: `Gösterge tanımı`; `Birim`, `Kod`, `Müdürlük`, `Hesaplama`, `Kaynak`, `Açıklama` etiketleri. Henüz gerçekleşme girilmediyse `Kayıt yok` tek kez gösterilir.
- Form başlığı: `Yeni gerçekleşme gir`.

Diğer mevcut görünen metinler, durum ifadeleri, hedef farkı uyarısı, kanıt bilgileri, form alanları ve geçmiş korunmuştur.

## Ekran görüntüleri

Chromium, tam sayfa, `tr-TR`, 1440 ve 390 piksel. Öncesi görüntüleri CIV-135 görünümüdür; sonrası görüntüleri CIV-140 şablonuyla aynı sentetik bağlamlarda yakalanmıştır. PNG başına üst sınır 1.500.000 bayttır.

| Durum | 1440 önce | 1440 sonra | 390 önce | 390 sonra |
| --- | --- | --- | --- | --- |
| Müdürlük taslağı | [Önce](department-draft-1440-before.png) | [Sonra](department-draft-1440-after.png) | [Önce](department-draft-390-before.png) | [Sonra](department-draft-390-after.png) |
| Form hatası | [Önce](department-error-1440-before.png) | [Sonra](department-error-1440-after.png) | [Önce](department-error-390-before.png) | [Sonra](department-error-390-after.png) |
| Onaylı | [Önce](approved-1440-before.png) | [Sonra](approved-1440-after.png) | [Önce](approved-390-before.png) | [Sonra](approved-390-after.png) |

## Doğrulama

Odaklı PostgreSQL doğrulaması: `CIVENSA_CIV135_SCREENSHOTS=docs/design/rollout/civ-140 python -m pytest -q --require-postgres tests/test_activity_report_detail_design.py` — **55 geçti** (mevcut Starlette/httpx deprecation uyarısı). Tarayıcı kontrolleri iki görünüm alanında taşma, 44rem sınırı, durum metni kontrastı, kanıt ve form davranışı, bar uygunluğu ve hedef işaretçisinin konumunu denetler. Görselleri yeniden üretmek için aynı komutu çalıştırın.

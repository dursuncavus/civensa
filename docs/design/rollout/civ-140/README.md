# CIV-140 · Gösterge özeti grafiksel

Gösterge gerçekleşme özeti, her rapor revizyonunda veri durumlarını bir bakışta sayar. Gösterge kartlarında gerçekleşme etiketi, değer, birim, durum, hedef ve sayısal fark aynı baseline satırında görünür; uygun olduğunda bar bunun altında gösterilir. Bar yalnız doğrulanmış, sıfır olmayan sayısal hedef ve doğrulanmış sayısal gerçekleşme varsa çizilir. Hedef ve gerçekleşme arasındaki başarı yönü yorumlanmaz; renkler yalnız veri durumunu belirtir.

Tanım ve en son kanıtlar kompakt gösterilir; tanım ve geçmiş ayrıntıları kapalı `<details>` alanlarında kalır. Yeni gerçekleşme formu mevcut alanları ve gönderim davranışını değiştirmeden ayrı bir başlıkla ayrılır.

## Yeni görünen metinler

- Rapor özeti, sıfır olmayan sayımlar için: `{{ sayı }} gösterge`, `{{ sayı }} Doğrulanmış`, `{{ sayı }} İncelenmeli`, `{{ sayı }} Eksik`, `{{ sayı }} Kayıt yok`, `{{ sayı }} açıklama bekliyor`. Sayım çiftleri `·` ile ayrılır.
- Gösterge özeti: `Fark: {{ sayısal fark veya Hesaplanmadı }}` ve gerçekleşme değeri yanında birim.
- Tanım açıklaması: `Gösterge tanımı`; `Birim`, `Kod`, `Müdürlük`, `Hesaplama`, `Kaynak`, `Açıklama` etiketleri. Henüz gerçekleşme girilmediyse `Kayıt yok` tek kez gösterilir.
- Form başlığı: `Yeni gerçekleşme gir`.

Diğer mevcut görünen metinler, durum ifadeleri, hedef farkı uyarısı, kanıt bilgileri, form alanları ve geçmiş korunmuştur.

## Ekran görüntüleri

Chromium, tam sayfa, `tr-TR`, 1440 ve 390 piksel. Öncesi görüntüleri CIV-135 görünümüdür; onaylı ve müdürlük taslağı görüntüleri CIV-144 hizalama ve kanıt gruplamasıyla yenilenmiştir. Ayrıca barsız `İncelenmeli` durumu ayrı yakalanmıştır; iki kaynaklı kanıt listesinde ilk kaynak PDF içerir. PNG başına üst sınır 1.500.000 bayttır.

| Durum | 1440 önce | 1440 sonra | 390 önce | 390 sonra |
| --- | --- | --- | --- | --- |
| Müdürlük taslağı | [Önce](department-draft-1440-before.png) | [Sonra](department-draft-1440-after.png) | [Önce](department-draft-390-before.png) | [Sonra](department-draft-390-after.png) |
| Müdürlük taslağı · İncelenmeli, barsız | — | [Sonra](department-review-1440-after.png) | — | [Sonra](department-review-390-after.png) |
| Form hatası | [Önce](department-error-1440-before.png) | [Sonra](department-error-1440-after.png) | [Önce](department-error-390-before.png) | [Sonra](department-error-390-after.png) |
| Onaylı | [Önce](approved-1440-before.png) | [Sonra](approved-1440-after.png) | [Önce](approved-390-before.png) | [Sonra](approved-390-after.png) |

## Doğrulama

Odaklı PostgreSQL doğrulaması: `CIVENSA_CIV135_SCREENSHOTS=docs/design/rollout/civ-140 python -m pytest -q --require-postgres tests/test_activity_report_detail_design.py` — **59 geçti** (mevcut Starlette/httpx deprecation uyarısı); gösterge görüntüleme testi — **8 geçti**. Tarayıcı kontrolleri iki görünüm alanında taşma, 44rem sınırı, altı değer öğesinin ortak baseline hizası, no-bar `İncelenmeli` durumu, kanıt satırlarının girintisi ve kaynaklar arası boşluk, durum metni kontrastı, kanıt ve form davranışı, bar uygunluğu ve hedef işaretçisinin konumunu denetler.

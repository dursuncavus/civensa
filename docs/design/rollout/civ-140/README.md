# CIV-140 · Gösterge özeti grafiksel

Gösterge gerçekleşme özeti, her rapor revizyonunda veri durumlarını bir bakışta sayar. Gösterge kartlarında gerçekleşme etiketi, değer, birim, durum, hedef ve sayısal fark aynı baseline satırında görünür; uygun olduğunda bar bunun altında gösterilir. Bar yalnız doğrulanmış, sıfır olmayan sayısal hedef ve doğrulanmış sayısal gerçekleşme varsa çizilir. Hedef ve gerçekleşme arasındaki başarı yönü yorumlanmaz; renkler yalnız veri durumunu belirtir.

Tanım ve en son kanıtlar kompakt gösterilir; tanım ve geçmiş ayrıntıları kapalı `<details>` alanlarında kalır. Yeni gerçekleşme formu mevcut alanları ve gönderim davranışını değiştirmeden ayrı bir başlıkla ayrılır.

## Yeni görünen metinler

- Rapor özeti, sıfır olmayan sayımlar için: `{{ sayı }} gösterge`, `{{ sayı }} Doğrulanmış`, `{{ sayı }} İncelenmeli`, `{{ sayı }} Eksik`, `{{ sayı }} Kayıt yok`, `{{ sayı }} açıklama bekliyor`. Sayım çiftleri `·` ile ayrılır.
- Gösterge özeti: `Fark: {{ sayısal fark veya Hesaplanmadı }}` ve gerçekleşme değeri yanında birim.
- Tanım açıklaması: `Gösterge tanımı`; `Birim`, `Kod`, `Müdürlük`, `Hesaplama`, `Kaynak`, `Açıklama` etiketleri. Henüz gerçekleşme girilmediyse `Kayıt yok` tek kez gösterilir.
- Form başlığı: `Yeni gerçekleşme gir`.
- Kanıt dosyası satırı: bağlantının dışında küçük, ikincil `Dosya:` öneki. Kaynak satırı gövde boyutunda, dosya satırı 14px ve 16px girintilidir; kaynaklar arasında 16px, kaynak ile dosyası arasında 4px boşluk vardır. Aynı düzen gerçekleşme geçmişinde de kullanılır.

Diğer mevcut görünen metinler, durum ifadeleri, hedef farkı uyarısı, kanıt bilgileri, form alanları ve geçmiş korunmuştur.

## Ekran görüntüleri

Chromium 151, tam sayfa, `tr-TR`, 1440 ve 390 piksel. Öncesi görüntüleri CIV-135 görünümüdür; onaylı, müdürlük taslağı ve form hatası görüntüleri CIV-144 hizalama ve kanıt gruplamasıyla yenilenmiştir. Ayrıca barsız `İncelenmeli` durumu ayrı yakalanmıştır; iki kaynaklı kanıt listesinde ilk kaynak PDF içerir. PNG başına üst sınır 1.500.000 bayttır.

| Durum | 1440 önce | 1440 sonra | 390 önce | 390 sonra |
| --- | --- | --- | --- | --- |
| Müdürlük taslağı | [Önce](department-draft-1440-before.png) | [Sonra](department-draft-1440-after.png) | [Önce](department-draft-390-before.png) | [Sonra](department-draft-390-after.png) |
| Müdürlük taslağı · İncelenmeli, barsız | — | [Sonra](department-review-1440-after.png) | — | [Sonra](department-review-390-after.png) |
| Form hatası | [Önce](department-error-1440-before.png) | [Sonra](department-error-1440-after.png) | [Önce](department-error-390-before.png) | [Sonra](department-error-390-after.png) |
| Onaylı | [Önce](approved-1440-before.png) | [Sonra](approved-1440-after.png) | [Önce](approved-390-before.png) | [Sonra](approved-390-after.png) |

## Doğrulama

Odaklı PostgreSQL 18.6 doğrulaması: `CIVENSA_CHROMIUM_PATH=/usr/bin/chromium CIVENSA_CIV135_SCREENSHOTS=/tmp/civ144-screenshots python -m pytest -q --require-postgres tests/test_activity_report_detail_design.py tests/test_ar_indicator_display.py` — **67 geçti** (59 tasarım ve 8 gösterge görüntüleme testi; mevcut Starlette/httpx deprecation uyarısı). `CIVENSA_TEST_POSTGRES_URL` yalnız atılabilir yerel test veritabanını gösterir. `*-after.png` dosyaları bu çalışmadan alındı; önceki görüntüler korunmuştur.

Tarayıcı kontrolleri 1440px genişlikte altı metnin tek satırda ve baseline farkının en fazla 1px olduğunu, 390px genişlikte her sarılan satırın baseline ve sol hizasını doğrular. Doğrulanmış ve barsız `İncelenmeli` durumlarında güncel kanıt listesi ve her geçmiş revizyon için kaynak/dosya boşlukları, 16px girinti, bağlantı dışında `Dosya:`, değişmeyen bağlantı metni/adresi ve 16px/14px yazı boyutları denetlenir. Taşma, 44rem sınırı, kontrast, kanıt ve form davranışı, bar uygunluğu ve hedef işaretçisinin konumu da kontrol edilir.

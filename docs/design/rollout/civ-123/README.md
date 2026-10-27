# CIV-123 · Etiket ile değer yan yana

27 Ekim 2026 sahip kuralı. Önce mevcut 1440/390 görünümleri yakalandı, ardından sayfa CSS'leri düzenlendi. Görüntüler gerçek rota/şablonlarla, yalnızca geçici yerel PostgreSQL 17 ve sentetik UI-map verileriyle üretildi. Chromium 151.0.7922.173; tr-TR, Europe/Istanbul, açık tema, 1×. Bütün PNG'ler ≤ 1.500.000 bayt; uzun ekranlarda paletli PNG kullanılır, boyut ve içerik korunur.

## Ekran denetimi

| Ekran | Kural | Değişiklik / değişiklik gerekmeme gerekçesi | 1440 önce / sonra | 390 önce / sonra |
| --- | --- | --- | --- | --- |
| 009 · EK-1 dizini, strateji | R2 | Rapor adı ve iş akışı durumu içeren başlık 1046 → 704 px; durumlar ortak sütunda. Bölüm/durum tablosu korunur. | [Önce](009-before-1440.png) · [Sonra](009-after-1440.png) | [Önce](009-before-390.png) · [Sonra](009-after-390.png) |
| 010 · EK-1 dizini, müdürlük | R2 | Aynı başlık sınırı ve durum hizası; mobilde adın altında durum. Tablo korunur. | [Önce](010-before-1440.png) · [Sonra](010-after-1440.png) | [Önce](010-before-390.png) · [Sonra](010-after-390.png) |
| 011 · EK-1 editörü, strateji | R2 | Bölüm bağlantıları zaten 511 px sütunlardaydı. Farklı uzunluktaki durumların başlangıcı ortak 5rem sütuna hizalandı; her bağlantıya 44rem üst sınırı kondu. | [Önce](011-before-1440.png) · [Sonra](011-after-1440.png) | [Önce](011-before-390.png) · [Sonra](011-after-390.png) |
| 012 · EK-1 editörü, müdürlük | R2 | Aynı bölüm/durum hizası; adlar mobilde durum sütunuyla çakışmadan satıra yayılır. | [Önce](012-before-1440.png) · [Sonra](012-after-1440.png) | [Önce](012-before-390.png) · [Sonra](012-after-390.png) |
| 021 · Genel Bakış, strateji | R1, R2 | `aside.dashboard-summary` içindeki üç kutu ince ayraçlı etiket/değer satırlarına dönüştü. Sayılar tabular; açıklama metni korunur. Şablon durumu da etiketle aynı satırda. Özet kapsayıcısı ≥48rem ise iki sütun, dar ise tek sütun. İlerleme panosu değiştirilmedi. | [Önce](021-before-1440.png) · [Sonra](021-after-1440.png) | [Önce](021-before-390.png) · [Sonra](021-after-390.png) |
| 022 · Genel Bakış, müdürlük | none | Değişiklik gerekmiyor: bu rolde `aside.dashboard-summary` veya sayı kartı yok; yalnız kapsam dışında tutulan CIV-122 görev listesi var. Listeye dokunulmadı. | [Önce](022-before-1440.png) · [Sonra](022-after-1440.png) | [Önce](022-before-390.png) · [Sonra](022-after-390.png) |
| 024 · Müdürlük veri girişi | R2 | Gösterge adı/kontrol rozeti satırı 1046 → 704 px; rozet sütunu en az 6rem. İşlem geçmişi/revizyon başlığı da 44rem ile sınırlı. Üst iş akışı şeridi sabit adımlardır, sayı kartı veya uzak değişken değer içermez; korunur. | [Önce](024-before-1440.png) · [Sonra](024-after-1440.png) | [Önce](024-before-390.png) · [Sonra](024-after-390.png) |
| 029 · İç Kontrol izleme paketi | none | Değişiklik gerekmiyor: eski `.ic-wrap` ekranı; paket adı/durum aynı başlık metninde, form durumu alan etiketinin altında. Uzak kenarda bağımsız durum veya sayı kutusu yok. | [Önce](029-before-1440.png) · [Sonra](029-after-1440.png) | [Önce](029-before-390.png) · [Sonra](029-after-390.png) |
| 030 · İç Kontrol Eylemlerimiz | R2 | Paket durumu zaten adın hemen yanında. Salt okunur eylem etiket/değer listeleri 996 → 704 px ile sınırlı; iki sütunun ortak sınırı ve mobil tek sütun korunur. Dönemsiz plan özeti de aynı `dl` kuralını kullanır. Onaylı durum ayrıca yakalandı. | [Önce](030-before-1440.png) · [Sonra](030-after-1440.png) · [Onaylı önce](030-approved-before-1440.png) · [Onaylı sonra](030-approved-after-1440.png) | [Önce](030-before-390.png) · [Sonra](030-after-390.png) · [Onaylı önce](030-approved-before-390.png) · [Onaylı sonra](030-approved-after-390.png) |
| 033 · Modüller, strateji | none | Değişiklik gerekmiyor: kartlar rapor türünü, açıklamasını ve giriş bağlantılarını içeriyor; sabit etiket/değişken sayı kutusu veya uzak durum sütunu yok. | [Önce](033-before-1440.png) · [Sonra](033-after-1440.png) | [Önce](033-before-390.png) · [Sonra](033-after-390.png) |
| 034 · Modüller, müdürlük | none | Değişiklik gerekmiyor: 033 ile aynı içerik yapısı; R1/R2 örneği yok. | [Önce](034-before-1440.png) · [Sonra](034-after-1440.png) | [Önce](034-before-390.png) · [Sonra](034-after-390.png) |
| 041 · PP tamamlanma listesi | none | Değişiklik gerekmiyor: bölüm/durum/adet tablodadır. Açıklama listesindeki değerler `max-content` etiket sütununun hemen ardından gelir; özet sayıları aynı cümlenin içinde. | [Önce](041-before-1440.png) · [Sonra](041-after-1440.png) | [Önce](041-before-390.png) · [Sonra](041-after-390.png) |
| 042 · İnceleme kuyruğu | none | Değişiklik gerekmiyor: müdürlük, durum/revizyon ve işlemler tablo sütunlarıdır; R2 tablo sütunlarına uygulanmaz. | [Önce](042-before-1440.png) · [Sonra](042-after-1440.png) | [Önce](042-before-390.png) · [Sonra](042-after-390.png) |
| 046 · Gönderim Yetkileri | none | Değişiklik gerekmiyor: hesap ve gönderim yetkisi durumları tablodadır; açıklama panelinde sayı kutusu/uzak durum yok. `submit-authorizations.css` eklenmedi. | [Önce](046-before-1440.png) · [Sonra](046-after-1440.png) | [Önce](046-before-390.png) · [Sonra](046-after-390.png) |

## Doğrulama

`verify_rollout.py --phase before` ve `--phase after`, gerçek Alembic geçişleriyle oluşturulan geçici veritabanında çalışır. İşlem sonunda veritabanı kaldırılır. Tarayıcı yalnız loopback GET kullanır; iki yakalama aşamasında tüm model tablolarının özeti değişmemelidir. Onaylı İç Kontrol görünümü gerçek gönderim/onay servisleriyle kurulur. Parola ve oturum bilgileri kaydedilmez.

[Önce ölçümleri](before.json) · [Sonra ölçümleri](after.json). Sonra aşamasında her değişen ekran için 1440'ta satırın ve çocuklarının 44rem sınırında kalması veya R1 yüksekliği ≤44 px, değer konumu, tabular sayılar ve kutusuz görünüm doğrulanır. Dizin ve editörde durumların başlangıç sütunları da karşılaştırılır. 390'ta bütün kapsamda sayfa genişliği viewport'a eşittir. Değişen tasarım ekranlarının görünür metin kontrastı en az 4,5:1 olarak ölçülür; hover/focus durumları mevcut tasarım testlerinde ayrıca kontrol edilir.

### Test değişiklikleri

Dondurulmuş fixture'lar, sözleşme karşılaştırmaları ve filtre/klavye/CSRF testleri değiştirilmedi.

- `test_dashboard_design.py`: bütün `.card` öğelerinin aynı padding'e sahip olma beklentisi → yalnız özet satırlarında kutu kenarlığı/yuvarlak köşe olmaması; özet kartı 108/88 px sınırı → ≤44 px; 390'ta `[1,2]` kart düzeni → `[1,1,1]` satır düzeni. Bunlar bire bir yerleşim değişimleridir. Etiket/değerin aynı yatay satırda ve aralarında 12 px bulunması ile tabular sayılar eklendi. 1200 px görünüm geniş özet panelinde iki sütunu doğrular. İlerleme panosunun testleri korunur.
- `test_department_design.py`: gösterge başlığı ve rozet için 44rem sınırı eklendi.
- `test_section_index_design.py`: rapor başlığı/rozet sınırı ve durum sütunu hizası eklendi.
- `test_section_editor_design.py`: bölüm bağlantısı/durum sınırı ve sütun hizası eklendi.
- `test_ic_our_actions_design.py`: dönemli/dönemsiz ve salt okunur senaryolarda tanım listesi/değer sınırı eklendi.

Değişiklik öncesi odaklı paket: **184 passed**. İlk değişiklik sonrası odaklı paket: **184 passed**. Son 1200 px senaryosunu da içeren tam paket sonucu PR açıklamasında yer alır.

### Kapsam ve doğrulanamayanlar

Uygulama değişikliği yalnız `dashboard.css`, `data-entry.css`, `section-index.css`, `section-editor.css`, `ic-our-actions.css` içindedir. Şablon/bağlantı/form/alan/aria/data/metin değişikliği yok. 036/037, 021 ilerleme panosu ve 022 görev listesi düzenlenmedi. Çekim başlangıcında #175, #183 (CIV-121), #184 açıktı; görüntüler bu nedenle hedef dalda henüz birleşmemiş önceki işlerin eski görünümünü de içerir. Bu alanlardaki görsel farklar bu PR'a ait değildir.

Canlı ortam/veri, Firefox/WebKit ve işletim sistemi ekran okuyucusu kullanılmadı. 029/046 değişmeyen eski ekranların renkleri yeniden tasarlanmadı; kontrast ölçümü değişen tasarım ekranlarına uygulanır. Çok uzun özel kurum/etiket verileri için mevcut sentetik uzun metin testleri çalıştırılır; gerçek kurum verisi kullanılmaz.

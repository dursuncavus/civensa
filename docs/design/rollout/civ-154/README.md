# CIV-154 · Bütçe aktarma ayrıntısı (095)

Başlangıç: `feature/authorization-workflow-phase5`, `c882e907c27e7b505c25f2423ec6d21a90c0f610`.
Başlangıç şablonu `tests/fixtures/budget_detail_start/budget_detail.html` içinde bayt düzeyinde korunur; SHA-256: `16dcea388838089d966de4fbbaea171defaf219ad58f5fac0e3aeba3a1975a12`.

Görüntüler yerel PostgreSQL 16, gerçek giriş/CSRF ve Chromium ile yalnızca sentetik veriden üretildi. `before` görüntüleri dondurulmuş başlangıç şablonunu, `after` görüntüleri yeni şablonu aynı bağlam ve aynı uygulama varlıklarıyla gösterir. Tam sayfa görüntüleridir; her PNG 1,5 MB altındadır.

| Durum | 1440 önce | 1440 sonra | 390 önce | 390 sonra |
| --- | --- | --- | --- | --- |
| Dolu işlem ve geri alma formu | [Önce](before-operation-1440.png) | [Sonra](after-operation-1440.png) | [Önce](before-operation-390.png) | [Sonra](after-operation-390.png) |
| Geri alınmış işlem | [Önce](before-reversed-1440.png) | [Sonra](after-reversed-1440.png) | [Önce](before-reversed-390.png) | [Sonra](after-reversed-390.png) |
| Sunucu hatası gösteriliyor | [Önce](before-error-1440.png) | [Sonra](after-error-1440.png) | [Önce](before-error-390.png) | [Sonra](after-error-390.png) |

`tests/test_budget_detail_design.py` içindeki 36 dondurulmuş sözleşme senaryosu kabul öncesi/sonrası, yetki devri var/yok, normal/telafi/geri alınmış işlem ve müdürlük sonuçları eksik/eşit/kısa durumlarını kapsar. Uyarı, seçim istisnaları ve istisnasız seçimler de karşılaştırılır. Kimlikler, data/aria/role/hidden nitelikleri, bağlantılar, form kontrolleri, ortak include ve para dizgeleri korunur. Ortak CSS'nin ilk 6710 baytı ayrıca sabit hash ile denetlenir; eklenen seçiciler `.budget-detail-page` kapsamındadır.

Tarayıcı testi her iki genişlikte eski ve yeni şablonla istemci doğrulamasını, gerçek sunucu hatasını ve başarılı geri alma yönlendirmesini çalıştırır. Yeni sayfada yatay taşma yoktur; tablo kendi kabında kayar. Para sütunları sağa hizalı ve tabular rakamlıdır; açıklama ve etiket/değer grupları en çok 44rem, geri alma alanları tek sütundur. Normal/hover/focus durumlarında ölçülen en düşük metin kontrastı her iki genişlikte **5,36:1**; büyük harfe dönüştürme yoktur.

Görünür metin değişikliği: ayrı etiket/değer satırlarına dönüştürülen iki Evet/Hayır olgusu, müdürlük özetleri ve işlem sonu/Net satırları arasındaki dekoratif `·` ayırıcıları kaldırıldı. Sözcükler, değerler, işaretler, para biçimi, kullanıcı unvanı ve TSİ tarih gösterimi korunur.

Canlı ortam/veri kullanılmadı. Görsel kanıtlar Chromium ve belirtilen iki genişlikle sınırlıdır.

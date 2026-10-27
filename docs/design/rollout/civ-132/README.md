# CIV-132 · Sistem durumu

035 `/operations`, strategy rolü. Başlangıç: `4622bf22b36018ce0a1ca3630405ae2002214dce`.

Sayfaya özel `operations.css`, mevcut panel, metinli durum etiketi, kapalı disclosure, alan ve düğme desenlerini uygular. Etiket/durum satırları ve form en çok 44rem; uzun JSON klavyeyle de kaydırılabilen kutuda kalır. Kimlikler, kontrol maddeleri, bağlantılar, form sözleşmesi ve veri davranışı başlangıç şablonuna karşı dondurulmuştur.

Görünür metin değişiklikleri yalnızca sayfa başlığında `Sistem Durumu` → `Sistem durumu` ve indirme bağlantısında `Mantıksal Yedek İndir` → `Mantıksal yedek indir`. Ortak kabuk bu çalışmanın kapsamında değildir. Durum metinleri değişmedi. Başlıklara durum etiketi eklendiğinden mevcut iki test, aynı tam metni ilgili başlığın DOM içeriğinde bire bir doğrular.

## Ekran görüntüleri

Tümü aynı sentetik engelli durumu, iki uyarıyı, açık ilk otomatik kontrolün uzun JSON kanıtını ve kayıtlı D1 kişi onayını içerir. Önce görüntüleri SHA-256 ile sabitlenen başlangıç şablonundan, sonra görüntüleri yeni şablondan üretilmiştir. Tam sayfa PNG; her dosya 1,5 MB altındadır.

| Genişlik | Önce | Sonra |
| --- | --- | --- |
| 1440 px | [Önce](before-blocked-1440.png) | [Sonra](after-blocked-1440.png) |
| 390 px | [Önce](before-blocked-390.png) | [Sonra](after-blocked-390.png) |

## Doğrulama kapsamı

`tests/test_operations_design.py`: hazır/engelli teknik hazırlık, üç yayın durumu, kanıtlı/kanıtsız manuel maddeler, teyit/geri çekme, eski içerik geçmişi ve hatalı form değerleri için sabit sözleşme. Gerçek Chromium ile 1440/390 px sayfa taşması, açık uzun JSON, 44rem sınırı, büyük harf dönüşümü olmaması ve görünür metin çiftlerinde en az 4,5:1 kontrast; odak/hover ve hata durumu dahil. Formda yerel zorunlu alan kontrolü, sunucu hatasında değer koruma, gerçek CSRF/oturum ile teyit ve geri çekme de kontrol edilir.

Veriler yalnızca yerel, geçici test verileridir. Canlı rol/üretim doğrulaması, gerçek D1–D8 kullanıcı kabulü ve başka tarayıcılar bu ekran çalışmasıyla doğrulanmaz.

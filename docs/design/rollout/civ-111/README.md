# CIV-111 · 042 İnceleme kuyruğu

Ekran, mevcut tasarım sistemi bileşenleriyle yenilendi (D-243, D-271, D-272). Yeni desen veya çalışma zamanı bağımlılığı eklenmedi. CSS yalnızca bu sayfada yüklenir ve `.review-page` altında sınırlıdır.

390 px genişlikte tablo kendi odaklanabilir bölgesinde yatay kayar; sayfa taşmaz. Görünür kaydırma ipucu vardır; uzun ve boşluksuz notlar hücre içinde kırılır. Onaylı paketlerin düzeltme formu başlangıçta kapalıdır. Hatalı gönderimde yalnız ilgili formun disclosure'ı açılır; gerekçe ve alan hatası korunur. İade modalının mevcut JavaScript odak davranışı korunmuştur.

## Görsel kanıt

Tamamı sentetik veriyle, Chromium'da 1000 px viewport yüksekliğiyle alındı. Her PNG 1,5 MB altında. Mobil görüntülerde yatay kaydırma konumu senaryodaki işlem alanını gösterebilir.

| Görünüm | 1440 px | 390 px |
| --- | --- | --- |
| Müdür, dört durum ve uzun iade notu | [Görüntü](director-1440.png) | [Görüntü](director-390.png) |
| Düzeltme disclosure'ı açık | [Görüntü](reopen-1440.png) | [Görüntü](reopen-390.png) |
| İade modalı açık | [Görüntü](return-modal-1440.png) | [Görüntü](return-modal-390.png) |
| Boş kuyruk | [Görüntü](empty-1440.png) | [Görüntü](empty-390.png) |
| Strateji personeli | [Görüntü](staff-1440.png) | [Görüntü](staff-390.png) |

## Görünür metin farkları

- İnceleme Kuyruğu → İnceleme kuyruğu (sayfa başlığı)
- Durum / Revizyon → Durum / revizyon
- İade Et → İade et (satır düğmesi ve modal düğmesi)
- Word Raporu → Word raporu
- Yeni: Düzeltme için aç (disclosure özeti)
- Yeni: Tablonun tamamını görmek için yatay kaydırın.
- Yeni: Bu dönem için incelenecek paket yok.

Boş durumda tablo başlıkları yerine boş durum mesajı gösterilir. Paylaşılan `base.html` kapsam dışı olduğundan menüdeki «İnceleme Kuyruğu» değişmedi. Durum etiketleri, form etiketleri, yardım metinleri, onay sorusu ve JavaScript hata/başarı mesajları aynen korundu; metin eşleşmesi nedeniyle ertelenen başka bir sayfa içi değişiklik yoktur.

## Doğrulama

`tests/fixtures/review_042.html`, başlangıç şablonunun birebir kopyasıdır; SHA-256: `b5b9220a49f7d98e5e560cd8c1e7feb3fc7201395dd0fbdc86b74112ebe9484e`.

`tests/test_review_design.py`: formlar, CSRF, alanlar, gizli girdiler, bağlantılar ve sorguları, JavaScript kimlik/sınıf/veri bağları, metin farkları, dört durum, kapalı dönem, müdür/personel/pasif kullanıcı, müdürlük için 403, hatalı düzeltmede değer koruma ve yalnız ilgili disclosure'ın açılması. Tarayıcı kontrolleri: 1440/390 px, taşma, tablo kaydırma, uppercase yasağı, görünür metin çiftlerinde normal/hover/focus ve modal dahil kontrast ≥ 4,5:1, onay sorusu ve hata bölgesi odağı, iade açma/iptal/gönderme, CSRF ve dönem sorgusu, düzeltme POST adresi/alanları.

Kullanıcı onayıyla `tests/test_pp_reopen.py` içindeki mevcut tarayıcı testine yalnızca iki disclosure açma tıklaması eklendi; mevcut doğrulamalar değiştirilmedi. Gerçek yerel PostgreSQL akışında boş gerekçe hatası, gerekçenin korunması ve başarılı yeniden açma aynı testle doğrulandı.

Yerel testler geçici PostgreSQL 18 üzerinde çalıştırılır. Tarayıcı karar yanıtları sentetik 409 ile sabitlenir; gerçek yeniden açma mevcut testle ayrıca sınanır. Canlı ortam veya gerçek belediye verisi kullanılmaz.

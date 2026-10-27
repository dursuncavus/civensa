# CIV-130 · Kullanıcılar tasarım sistemine

`/users` (047, strateji) sayfası mevcut panel, alan, tablo, rozet ve düğme desenlerine taşındı. Sayfaya özel `users.css`, yalnız `tokens.css` değişkenlerini kullanır. Üç sayı kartı 44rem sınırında etiket/sayı satırlarıdır. Eksik müdürlükler adın yanında oluşturma düğmesi bulunan düz listedir. Form 1024px ve üzerinde üç, mobilde tek sütundur. Parola teslim uyarısı uyarı panelidir; iki hesap politikası paragrafı tabloyla aynı bilgi panelindedir. Böylece mevcut `accountChangePolicy + .table-wrap` sözleşmesi de korunur. Etkin hesap yeşil, devre dışı hesap nötr metin rozetidir; işlemler rozetin altındadır.

## Görüntüler

27 Ekim 2026; yerel Chromium 151.0.7922.34, tr-TR, Europe/Istanbul, açık tema, 1×; geçici yerel PostgreSQL 18 ve yalnız sentetik kişiler/müdürlükler. Başlangıç görüntüleri dondurulmuş başlangıç şablonunun aynı gerçek rota bağlamıyla render edilmesidir. Her görüntü tam sayfadır; eksik müdürlükler, yeni kullanıcı formu ve Ada Sentetik satırının parola sıfırlama alanı açıktır. Parola alanları boştur. Mobil ek görüntüler tablonun sağ tarafını gösterir. Her PNG 1.500.000 baytın altındadır.

| Görünüm | CIV-130 öncesi | CIV-134 sonrası |
| --- | --- | --- |
| 1440px, altı sütun ve iç kaydırma yok | [Tam sayfa](users-before-1440.png) | [Tam sayfa](users-after-1440.png) |
| 390px, iç tablo kaydırma | [Tam sayfa](users-before-390.png) | [Tam sayfa](users-after-390.png) |
| 390px, durum/işlem sütunları | [Tam sayfa](users-before-status-390.png) | [Tam sayfa](users-after-status-390.png) |

## Görünür metin değişiklikleri

- Sayfa başlığı: `Kullanıcılar ve Yetkiler` → `Kullanıcılar ve yetkiler`.
- Ekleme düğmesi: `Kullanıcı Ekle` → `Kullanıcı ekle`.
- Yeni kullanıcı formu alanı: `Ad Soyad` → `Ad soyad`.
- Yeni kullanıcı formu alanı: `Geçici Parola` → `Geçici parola`.
- Tablo başlıkları: `Ad Soyad`, `E-posta`, `Rol` → `Kullanıcı`; ilgili hücrelerde ad, e-posta ve rol üç satırda gösterilir.

CSV başlıkları aynen korunur. Tablo, 1280px ve üzerinde panel genişliğine sığar; daha dar ekranlarda iç yatay kaydırma korunur.

## Doğrulama

`tests/fixtures/users_start.html`, başlangıç şablonunun bayt düzeyinde kopyasıdır (SHA-256: `53e0086d52cc338dbd8603a87afa0bee1ea11ea19c46b7791c8ff2e83105c924`). Yeni sözleşme testi bütün kimlikleri, JavaScript sınıflarını/veri özniteliklerini, alan ve düğme özniteliklerini, seçenekleri, bağlantıları, tablo başlıklarını ve metinleri karşılaştırır. Eksik müdürlük olan/olmayan durumlar, mevcut kullanıcı, devre dışı hesap, müdür ve yetkili/yetkisiz personel kapsanır.

- Başlangıç sözleşmesi ve önce görüntüleri: **4 passed**.
- Son odaklı paket: `python -m pytest -q --tb=short --require-postgres tests/test_users_design.py tests/test_users_ui.py tests/test_users_personal_accounts.py` → **42 passed**.
- Tarayıcı: 1440/390px, eksik müdürlük olan/olmayan durum; sayfa yatay taşması yok, mobil tablo klavyeyle kendi içinde kayar; büyük harfe dönüştürme yok; normal/hover/focus metinleri, nötr/etkin rozetler, devre dışı düğme ve placeholder kontrastları ≥4,5:1. Oluşturma formunu açma/kapama, müdürlük seçimi, rol değişimi, parola alanını açma/kapama ve gönderim yetkisi API çağrıları doğrulanır. Mevcut CSV/tek kullanımlık parola/pasifleştirme/ilk giriş akışı geçer.
- `git diff --check`, Python derleme kontrolü ve mevcut JavaScript sözdizimi kontrolü geçti. CSS değişkenlerinin tamamı `tokens.css` içinde tanımlıdır; sabit renk yoktur.
- Tam paket aynı kodun geçici kopyasında PostgreSQL 18 ile çalıştırılır; bazı eski testlerin yeniden ürettiği dosyalar çalışma deposundaki `tests/artifacts/**` alanına yazılmaz. Tam paket ve PR head CI sonuçları PR açıklamasında raporlanır.

Rota, servis, API, JavaScript, izin, veri tabanı veya bağımlılık değişikliği yoktur. Canlı ortam/veri, Firefox/WebKit, işletim sistemi ekran okuyucusu ve gerçek parola teslimi kullanılmadı. Birleştirme veya dağıtım yapılmaz.

# CIV-102 — Giriş ve parola ekranları

032 ve 019/020, Fira Sans ve D-224 tokenlarıyla düz zemin, kenarlıklı yüzey kartı, cümle düzeninde etiketler ve tam genişlikte birincil düğme kullanır. Girişte etiketler `loginEmail` / `loginPassword` ile ilişkilidir. Alan ve istek sözleşmesi `b8e063f` tabanından dondurulmuştur; `attempted_email`, sunucu mesajları ve `personal_accounts.js` korunur. Boş `firstPasswordError` yer kaplamaz; metin geldiğinde tehlike renkleriyle görünür.

`auth.css`, anonim ekranlar ve oturumlu ekranlardaki ortak parola diyaloğu için yüklenir. Mevcut `#passwordModal` kuralları ve mobil kart dolgusu `shell.css` içinden bu dosyaya aynen taşınmıştır. Diyaloğun Escape/Vazgeç ile kapanması, Tab döngüsü ve açan düğmeye odak dönüşü zaten `shell.js` içindedir; JavaScript değişmemiştir. Yardım metni sunucudaki 12 karakter kuralıyla eşitlenmiştir.

## Görseller

Yerel, geçici PostgreSQL 16, yalnız sentetik veri; Chromium, 900 px viewport yüksekliği, ölçek 1. Anonim sayfalar tam sayfa, diyaloglar 1440/390 × 900 px viewport olarak çekilmiştir.

| Durum | 1440 px | 390 px |
| --- | --- | --- |
| 032 giriş, boş | [PNG](032-login-empty-1440.png) | [PNG](032-login-empty-390.png) |
| 032 giriş, sunucu hatası | [PNG](032-login-error-1440.png) | [PNG](032-login-error-390.png) |
| 019 ilk parola, strateji, boş | [PNG](019-first-password-empty-1440.png) | [PNG](019-first-password-empty-390.png) |
| 019 ilk parola, strateji, sunucu hatası | [PNG](019-first-password-error-1440.png) | [PNG](019-first-password-error-390.png) |
| 020 ilk parola, müdürlük, boş | [PNG](020-first-password-empty-1440.png) | [PNG](020-first-password-empty-390.png) |
| 020 ilk parola, müdürlük, sunucu hatası | [PNG](020-first-password-error-1440.png) | [PNG](020-first-password-error-390.png) |
| 024 üzerinde parola diyaloğu | [PNG](024-password-dialog-1440.png) | [PNG](024-password-dialog-390.png) |

## Kısa kontrol kaydı

- Taban `b8e063f` ile **97 ekran/durum × 2 genişlik = 194 çekim**, **9.880 öğe/hedef**, **0 eksik**, **0 yatay taşma**, **0 kırpılma/örtüşme**. Formlar ve gizli CSRF alanı ayrıca dondurulmuş test sözleşmesiyle karşılaştırılmıştır.
- Değişen görünüm: **032, 019, 020 ve ortak parola diyaloğu**. Bunlar dışındaki ham piksel farkı bulunan 39 çekim, aynı DOM/saat/odak üzerinde taban ve yeni stillerle tekrar denetlenmiştir: **0 hesaplanmış stil/geometri farkı**. Ayrı veri kurulumları arasındaki zaman damgaları ve raster yuvarlamaları ürün görünümü değişikliği sayılmamıştır. Tam çekimler ve öğe JSON'ları yalnız `/tmp` altında tutulmuştur.
- Yeni yüzeylerde normal, hover ve odak durumları: **11 renk/tür çifti, 0 AA ihlali**. En düşük oran tehlike metni/zemini için **5,75:1**; normal metin eşiği 4,5:1, kontrol/odak eşiği 3:1. Metin/yüzey 15,80:1; ikincil metin ve alan sınırı/yüzey 6,87:1; beyaz/birincil 6,28:1; beyaz/hover 8,58:1; odak/yüzey 6,28:1.
- Tab sırası görsel sırayla aynı; diyalogda Tab/Shift+Tab döngüsü, Escape/Vazgeç ve odak dönüşü iki genişlikte doğrulandı. PostgreSQL 16 üzerinde **8 yeni test geçti**; diyalog kadrajı yenilenirken iki diyalog testi ayrıca geçti. Tam takım ve PR başının CI sonucu PR açıklamasında tutulur.
- Son hedef dal `4c81e89` (CIV-101 dahil) üzerine rebase sonrası, değişen 012 ekranının **22 durum × 2 genişlik = 44 çekimi** yenilendi: **0 eksik hedef, 0 taşma/kırpılma/örtüşme, 0 hesaplanmış stil/geometri farkı**. Diğer 150 çekimin kanıtı korundu; hedef dalın uygulama farkı yalnız 012 şablonu ve onun kullanıcı adı bağlamındadır. Giriş/parola şablonları, ortak base, shell stilleri/JS, tokenlar ve personal_accounts.js iki tabanda bayt düzeyinde aynıdır; dondurulmuş `b8e063f` alan sözleşmesi hâlâ geçerlidir. Güncel tabanda giriş/parola, 012 ve malî ekranlar için **51 test geçti**. Son PR başının tam PostgreSQL 18 CI sonucu PR açıklamasındadır.
- **14 PNG**, en büyük **92.733 bayt**; her biri ≤ 1.500.000 bayt.

## Metin değişiklikleri

- `PERFORMANS` → `Kurumsal raporlama`.
- `Giriş Yap` → `Giriş yap`.
- Diyalog başlığı: `Parolamı Değiştir` → `Parolamı değiştir`.
- Diyalog düğmesi: `Parolayı Değiştir` → `Parolayı değiştir`.
- `Yeni parolanız en az 10 karakter olmalıdır.` → `Yeni parolanız en az 12 karakter olmalıdır.`
- CSS büyük harf dönüşümünün kaldırılmasıyla görünen etiketler: `E-POSTA` → `E-posta`; `PAROLA` → `Parola`; `MEVCUT GEÇİCİ PAROLA` → `Mevcut geçici parola`; `YENİ PAROLA` → `Yeni parola`; `YENİ PAROLA TEKRAR` → `Yeni parola tekrar`.

## Testler ve seçiciler

`tests/fixtures/auth_contract.json`, tabandaki form yöntem/hedeflerini, alan adlarını, kimliklerini, türlerini, autocomplete, required, minlength ve CSRF alanını dondurur. Taban giriş alanlarında kimlik yoktur; yalnız yeni etiket ilişkileri için iki kimlik eklenir ve ayrıca doğrulanır.

`tests/test_auth_design.py`: iki genişlikte giriş/hata/Tab sırası; iki rolde ilk parola alan sözleşmesi, etiketler ve CSRF eşitliği, gerçek POST yükü ve sunucu hatası, başarılı değişim; diyalog açma, Tab/Shift+Tab döngüsü, Escape/Vazgeç ve odak dönüşü, 12 karakter metni. Yeni seçiciler: `.auth-page`, `.auth-card`, `.auth-brand`, `.auth-error`, `#loginEmail`, `#loginPassword`. Mevcut ilk parola ve diyalog kimlikleri korunur.

`tests/test_users_ui.py`: mevcut uçtan uca kişisel hesap testinin tam metin düğme seçicisi `Giriş Yap` → `Giriş yap`; davranış doğrulamaları korunur.

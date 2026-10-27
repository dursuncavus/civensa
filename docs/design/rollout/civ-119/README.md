# CIV-119 · Gönderim yetkileri

046 ekranı mevcut bilgi paneli, metin rozeti, ikincil küçük düğme ve tablo bileşenleriyle düzenlendi. Adın altında e-posta korunuyor; hesap ve gönderim durumu metinle gösteriliyor. Özet tüm personeli, devre dışı hesaplar dahil, şablondaki aynı listeden sayıyor.

Mobilde `pp-manifest.css` / `review.css` örneğindeki gibi kapsayıcı içinde yatay kaydırılan tablo ve görünür kaydırma açıklaması kullanılıyor. Sayfanın kendisi yatay taşmıyor. Ortak include ve app.js aynen korunuyor; yetki değişikliği mevcut POST ve sayfa yenilemesiyle çalışıyor.

## Görsel kanıt

Tüm veriler sentetik; yerel geçici PostgreSQL 17 ve Chromium kullanıldı. Her PNG 1,5 MB altında.

- [1440 · karışık durumlar](authorizations-1440.png)
- [390 · personel ve e-posta](authorizations-390.png)
- [390 · sağa kaydırılmış yetki sütunu](authorizations-status-390.png)
- [1440 · boş liste](authorizations-empty-1440.png)
- [390 · boş liste](authorizations-empty-390.png)

## Görünür metinler

- `Gönderim Yetkileri` → `Gönderim yetkileri` (yalnız sayfa başlığı).
- `Aşağıdaki Personele gönderim yetkisi verebilir veya verdiğiniz yetkiyi kaldırabilirsiniz.` → `Aşağıdaki personele gönderim yetkisi verebilir veya verdiğiniz yetkiyi kaldırabilirsiniz.`
- Ayrı `Personel` ve `E-posta` sütun başlıkları → `Personel / E-posta`; iki alan aynı hücrede korunur.
- Yeni özet: `N personel · X yetkili · Y yetkisiz`.
- Yeni kaydırma açıklaması: `Tablonun devamını görmek için yatay kaydırın.`

`Yetki ver`, `Yetkiyi kaldır`, `Yetkili`, `Yetkisiz`, `Etkin`, `Devre dışı`, soru başlığı, ikinci açıklama paragrafı ve boş liste cümlesi aynıdır. Ortak menünün ve API hata metinlerinin mevcut yazımı kapsam gereği korunur; mevcut test beklentileri gevşetilmedi.

## Doğrulama

`tests/test_submit_authorizations_design.py`: 9 test geçti. Başlangıç şablonunun baytları SHA-256 ile sabitlenir; her satırdaki durum span'ı ve düğmenin tüm nitelikleri/metni eski render ile karşılaştırılır. Satır sayısı, özet, devre dışı hesap, boş liste, yalnız müdür erişimi ve sayfaya özel CSS yüklemesi doğrulanır.

1440 ve 390 pikselde dolu/boş durumlar, sayfa taşması, tablo kaydırması, görünür metinlerde en az 4,5:1 kontrast (düğmelerin hover/focus durumları dahil), gerçek app.js üzerinden yetki verme/kaldırma POST gövdesi ve yenilenen satır/özet doğrulandı. Mevcut izin ve tasarım kabuğu testleri de geçti (51 test).

Tekrar üretmek için, geçici PostgreSQL bağlantısını `CIVENSA_TEST_POSTGRES_URL` olarak ayarlayıp:

```sh
CIVENSA_CIV119_SCREENSHOTS=docs/design/rollout/civ-119 python -m pytest -q --require-postgres tests/test_submit_authorizations_design.py
```

Üretim verisi veya canlı veritabanı kullanılmadı. Görsel inceleme Chromium ile sınırlıdır; diğer tarayıcı motorları doğrulanmadı.

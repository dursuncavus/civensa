# CIV-131 · Kurum yapısı

`GET /structure` (045, strategy), başlangıç: `4622bf2`.
Sayfaya özel `structure.css`, mevcut tasarım sistemi tokenlarını ve alan, panel,
tablo, metin rozeti, `<details>` örüntülerini kullanır. Dönem seçimi ve ad satırları
44rem içinde; 390 px'te formlar tek sütun, müdürlük tablosu kendi içinde kayar.
`structure_wizard.html` yalnızca `structure.html` tarafından dahil edilir.

Görünen metin değişiklikleri (yalnızca başlıklar):

- `Kurum Yapısı` → `Kurum yapısı`
- `Döneme Ait Yapı` → `Döneme ait yapı`
- `Alt Program Oluştur` → `Alt program oluştur`

Başlangıç metinleri testlerde arandı; bu değişiklikler mevcut testlerde değişiklik
gerektirmedi. Sihirbazdaki yönerge ve ortak gezinme metinleri aynı kaldı.

## Görüntüler

Tam sayfa Chromium görüntüleri, 1440×1000 ve 390×1000 görünüm alanları. Tüm
kayıtlar sentetik; yalnızca geçici yerel PostgreSQL kullanıldı. Her görüntü
1,5 MB altında. Programlar ve alt programlar dolu, bir alt program açık.
Hata görüntüsü gerçek yinelenen ad kaydının 409 yanıtıdır; girilen ad, gerekçe ve
hedef korunur, ilgili `<details>` açık kalır.

| Durum | Önce | Sonra |
| --- | --- | --- |
| Dolu sayfa · 1440 | [PNG](before-structure-1440.png) | [PNG](after-structure-1440.png) |
| Dolu sayfa · 390 | [PNG](before-structure-390.png) | [PNG](after-structure-390.png) |
| Başarısız kayıt · 1440 | [PNG](before-error-1440.png) | [PNG](after-error-1440.png) |
| Başarısız kayıt · 390 | [PNG](before-error-390.png) | [PNG](after-error-390.png) |

Önce görüntüleri, başlangıçtaki **iki** şablonun byte-identical fixture'larından,
aynı istek bağlamı ve verilerle üretildi; yeni CSS bu görüntülere yüklenmez.

## Doğrulama

`tests/test_structure_design.py`: 17 donmuş sözleşme senaryosu ve iki tarayıcı
senaryosu. Dönemsiz, boş/dolu dönem, yinelenen müdürlükler, geçmiş/iptal ve her
form ailesinde başarısız kayıt ele alınır. Form sırası ve bağları, tüm kontrol
nitelikleri, gerçek CSRF dahil gizli girdiler, seçenek/seçim durumları, ham
textarea değerleri, bağlantılar, JS kancaları ve `<details open>` karşılaştırılır.

Tarayıcıda gerçek kayıt, hata sonrası düzeltme, müdürlük adı/durumu ve dönem
seçimi; 1440/390 px'te taşma, tablo iç kaydırma, alan yerleşimleri, 44rem sınırı,
büyük harfe dönüştürmeme ve normal/hover/focus metin kontrastı denetlenir.
En düşük görünen metin kontrastı **4,71:1**; sayfada yatay taşma yoktur.

Ekran görüntülerini yeniden üretmek için geçici PostgreSQL test URL'siyle:

```sh
CIVENSA_CIV131_SCREENSHOTS=docs/design/rollout/civ-131 \
python -m pytest -q --require-postgres tests/test_structure_design.py
```

Mevcut akış testleri ve tam test takımı sonuçları PR açıklamasında kayıtlıdır.
Yerel tarayıcı doğrulaması Chromium ile sınırlıdır; diğer tarayıcılar ve canlı
ortam kullanılmadı. Varsayım: mevcut form ve JS sözleşmesi aynen korunur.

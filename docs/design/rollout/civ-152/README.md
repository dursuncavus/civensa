# CIV-152 · Gösterge kimlikleri ve malî önizleme

006 ve 015, mevcut tasarım sistemi bileşenlerine taşındı. Yalnızca iki şablon ve
bu sayfalara özel iki CSS dosyası değişti. Veri, form alanları, izinler ve işlem
koşulları korundu. Eklenen görünür metinler: **Sabitlendi**, **Eşleme bekliyor**.
“Raporlara dön” bağlantısı sayfanın üstüne taşındı; alttaki kopya kaldırıldı.

## Ekran görüntüleri

Tüm veriler sentetiktir. Her satır için `1440` ve `390` genişliklerinde,
`before` ve `after` son ekleriyle toplam 12 PNG bulunur. Başlangıç şablonları
`tests/fixtures/bindings_financial_import_start/` altında baytları değiştirilmeden
saklanır; öncesi görüntüleri aynı güncel kabukla bu şablonlardan üretilir.

| Dosya öneki | Gösterilen durum |
| --- | --- |
| `bindings-evidence` | Bir sabitlenmiş ve bir eşleme bekleyen gösterge; kodlu/kodsuz satırlar |
| `financial-errors` | İki ayrı satır hatası; uygulama düğmesi gösterilmez |
| `financial-evidence` | Eklenecek, Kaldırılacak, Değişecek; sayı/metin/boş değerler ve uygulama düğmesi |

Her PNG 1,5 MB sınırının altındadır. Mobilde tablo kendi içinde yatay kayar;
sayfada yatay taşma yoktur. Masaüstünde bilgi, alan ve durum satırları en fazla
44rem genişliğindedir. Görseller Chromium ile, yerel fontlar yüklendikten sonra
üretilmiştir; 390 pikselde gezinme alanı ortak kabuğun davranışı gereği alttadır.

## Doğrulama

`tests/test_bindings_financial_import_design.py` başlangıç dosyalarının SHA-256
özetlerini ve donmuş sözleşmelerini denetler: form yöntemleri/hedefleri, gizli
alan değerleri, alan öznitelikleri, seçeneklerin sırası/etiketleri, kimlikler,
`data-*`/`aria-*`/`role`, bağlantılar ve sayısal/boş hücre metinleri korunur.
İki kurumun kimlikleri, kodlu/kodsuz ve sabitlenmiş/bekleyen satırlar; hatalı,
hatasız, güncelliğini yitirmiş, dondurulmuş ve boş fark durumları kapsanır.

Tarayıcı testleri 1440/390 genişliklerinde taşma, tek sütunlu alanlar, 44rem sınırı,
sayı hizası, büyük harfe dönüştürme olmaması ve normal/hover/focus metin kontrastının
≥ 4,5:1 olmasını denetler. Gerçek oturum ve CSRF ile gösterge eşlemesi kaydetme ve
malî içe aktarmayı uygulama, geçici yerel PostgreSQL üzerinde sınanır. Tarayıcının
sahte `testserver` adresini dış ağa göndermemesi için 303 yönlendirmesi TestClient
köprüsünde çözülür; hedefi ve HTTP durumu ayrıca doğrulanır.

Görselleri yeniden üretmek için PostgreSQL test ortamı ve Chromium hazırken:

```sh
CIVENSA_CHROMIUM_PATH=/usr/bin/chromium \
CIVENSA_CIV152_SCREENSHOTS=docs/design/rollout/civ-152 \
python -m pytest -q --require-postgres tests/test_bindings_financial_import_design.py
```

Canlı veri veya canlı veritabanı kullanılmadı. İnsanla kullanılabilirlik testi yapılmadı.

# CIV-161 — Soru formu tablo hizası

Dört sonuç tablosu sabit sütun ölçüleri, sağa hizalı tabular sayılar ve ortak başlık düzeni kullanır. Gövde satır başlıkları beyaz zemin üzerinde ana metin rengindedir. Kurum toplamları orta yazı ağırlığı ve 2 px üst çizgiyle ayrılır. Sonuç kartındaki h3 aralıkları tasarım tokenlarından alınır.

Yedi sütunlu tablolarda ilk sütun %28'dir. Bileşen ve soru özetlerinde cevap sütunlarının aynı x konumunda başlaması için ilk sütun ikisinde de %46'dır; farklı ilk sütun yüzdeleriyle bu hizayı sağlamak mümkün değildir. Ortak 1000 px alt sınır ve sayı hücrelerindeki token tabanlı yatay boşluk, 1440 px ekranda bütün sütunları gösterir; 390 px ekranda her tablo kendi `.ic-scroll` alanında kaydırılır.

## Kanıt

Yerel, geçici PostgreSQL 18 ve Chromium 151 kullanıldı. Üç sentetik müdürlük vardır. `bos` durumunda hiç onay yoktur; `onayli` durumunda iki müdürlük onaylı, biri onaysızdır. Resmî özette de sentetik eylem onayı vardır. 70 soru metni test sırasında `docs/internal-control/ic-kontrol-soru-formu-70.xlsx` dosyasından okunur; test yanıtları sentetiktir. Canlı veritabanına bağlanılmadı.

`once` görüntüleri başlangıç şablonları ve CIV-161 öncesi CSS ile, `sonra` görüntüleri aynı kayıtlarla güncel şablonlar ve CSS kullanılarak alındı. Yalnızca ilgili kart yakalandı. Her PNG 1,5 MB sınırının altındadır.

| Kart / durum | 1440 px önce | 1440 px sonra | 390 px önce | 390 px sonra |
| --- | --- | --- | --- | --- |
| Sonuçlar, boş | [Görsel](once-sonuclar-bos-1440.png) | [Görsel](sonra-sonuclar-bos-1440.png) | [Görsel](once-sonuclar-bos-390.png) | [Görsel](sonra-sonuclar-bos-390.png) |
| Sonuçlar, onaylı | [Görsel](once-sonuclar-onayli-1440.png) | [Görsel](sonra-sonuclar-onayli-1440.png) | [Görsel](once-sonuclar-onayli-390.png) | [Görsel](sonra-sonuclar-onayli-390.png) |
| Resmî özet, boş | [Görsel](once-resmi-ozet-bos-1440.png) | [Görsel](sonra-resmi-ozet-bos-1440.png) | [Görsel](once-resmi-ozet-bos-390.png) | [Görsel](sonra-resmi-ozet-bos-390.png) |
| Resmî özet, onaylı | [Görsel](once-resmi-ozet-onayli-1440.png) | [Görsel](sonra-resmi-ozet-onayli-1440.png) | [Görsel](once-resmi-ozet-onayli-390.png) | [Görsel](sonra-resmi-ozet-onayli-390.png) |

## Doğrulama

`tests/test_internal_control_result_tables.py` eski şablon kaynaklarını SHA-256 ile doğrular ve boş/onaylı genel görünümün render edilmiş bütün hücre metinlerini sırayla karşılaştırır. Dört tablo sınıfı, iki toplam satırı, cevap sütunlarında ±1 px hizalama, sağa hizalama, tabular sayılar, satır başlığı ağırlıkları, en fazla iki satırlık kelime bölünmeyen başlıklar, h3 boşlukları ve en az 4,5:1 kontrast denetlenir. Masaüstünde bütün sütunların sığdığı, mobilde sayfa taşması olmadığı ve sağdaki sütuna tablo kaydırılarak ulaşılabildiği de doğrulanır.

Kanıt üretme komutu (yalnızca geçici yerel test veritabanıyla):

```sh
CIVENSA_CHROMIUM_PATH=/usr/lib/chromium/chromium \
CIVENSA_CIV161_EVIDENCE=docs/design/rollout/civ-161 \
python -m pytest -q --require-postgres tests/test_internal_control_result_tables.py
```

`CIVENSA_TEST_POSTGRES_URL` geçici test veritabanına ayarlanmalıdır. CI, kurduğu Playwright Chromium sürümünü kullanır; `CIVENSA_CHROMIUM_PATH` yerel ortam içindir. Test ve CI sonuçları PR açıklamasında raporlanır. Canlı ortam ve farklı tarayıcılar doğrulanmadı.

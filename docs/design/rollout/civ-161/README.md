# CIV-161 — Soru formu tablo hizası

Dört sonuç tablosu sabit sütun ölçüleri, sağa hizalı tabular sayılar ve ortak başlık düzeni kullanır. Gövde satır başlıkları beyaz zemin üzerinde ana metin rengindedir. Kurum toplamları orta yazı ağırlığı ve 2 px üst çizgiyle ayrılır. Sonuç kartındaki h3 aralıkları tasarım tokenlarından alınır.

Yedi sütunlu tablolarda ilk sütun %28'dir. Bileşen ve soru özetlerinde cevap sütunlarının aynı x konumunda başlaması için ilk sütun ikisinde de %46'dır; farklı ilk sütun yüzdeleriyle bu hizayı sağlamak mümkün değildir. Ortak 1000 px alt sınır ve sayı hücrelerindeki token tabanlı yatay boşluk, 1440 px ekranda bütün sütunları gösterir; 390 px ekranda her tablo kendi `.ic-scroll` alanında kaydırılır.

## Kanıt

Yerel, geçici PostgreSQL 18 ve Chromium 151 kullanıldı. Üç sentetik müdürlük vardır. `bos` durumunda hiç onay yoktur; `onayli` durumunda iki müdürlük onaylı, biri onaysızdır. Resmî özette de sentetik eylem onayı vardır. 70 soru metni test sırasında `docs/internal-control/ic-kontrol-soru-formu-70.xlsx` dosyasından okunur; test yanıtları sentetiktir. Canlı veritabanına bağlanılmadı.

`once` görüntüleri başlangıç şablonları ve CIV-161 öncesi CSS ile, `sonra` görüntüleri aynı kayıtlarla güncel şablonlar ve CSS kullanılarak alındı. Yalnızca ilgili kart yakalandı. İlk kapsamda 16, ek kapsamda 28 olmak üzere 44 PNG vardır; her biri 1,5 MB sınırının altındadır.

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


## Ek kapsam: yanıt formu ve yükleme

Yanıt formu hem müdürlük ekranında hem Strateji detayında sabit sütunlarla %46 soru, %16 yanıt, %38 açıklama kullanır. Üç radyo seçeneği dikeydir; “Geliştirilmekte” tek satırda kalır. Gövde satır başlıkları beyaz ve normal ağırlıktadır. Açıklama alanı hücrenin kullanılabilir genişliğini doldurur. Mobilde tablo kendi alanında kaydırılır.

Önizleme tablosunda Sıra ve Kod 4,5 rem, Bileşen 12 rem genişliğindedir; Soru kalan alanı kullanır. Sıra ve Kod sağa hizalı tabular sayılardır. Kaydedilmiş listeler bu sürümde tablo değil, `<ol>` olarak gösterilir. Sınıf öznitelikleriyle sınırlı kapsam içinde bu yapıya satır sarma, token tabanlı boşluk ve tabular sıra işaretleri uygulanır; yeni tablo veya başlık eklenmez.

Ek kanıtlarda ilk altı gerçek soru XLSX'ten yalnızca yakalama sırasında okunur. Boş, kısmi ve iade müdürlük formları, Strateji detayı ve altı soruluk sonuç özeti bu metinleri kullanır. Önizleme ve kayıtlı liste kanıtı ise gerçek 70 soruluk dosyanın tamamıyla üretilir. Normal ek test çalıştırmasında altı soruluk içerik sentetiktir; resmî soru metni içeren yeni fixture kaydedilmez.

Onaylanan kapsam istisnasıyla `tests/test_internal_control_design.py` içindeki eski `auto` beklentisi yalnız `ic-result-table` için `fixed` bekleyecek biçimde güncellenmiştir. Diğer tabloların eski beklentisi sürer. Yeni test; dört şablonun sınıf dışındaki kaynaklarını, hücre metinlerini, kontrol özniteliklerini, bağlantıları ve form bağlarını karşılaştırır. Form sütun oranları, radyo dizilimi, textarea genişliği, başlık kontrastı, önizleme sütun genişlikleri ve mobil taşma da gerçek Chromium'da denetlenir.

| Ek kanıt | 1440 px önce | 1440 px sonra | 390 px önce | 390 px sonra |
| --- | --- | --- | --- | --- |
| Müdürlük, boş | [Görsel](once-ek-mudurluk-bos-1440.png) | [Görsel](sonra-ek-mudurluk-bos-1440.png) | [Görsel](once-ek-mudurluk-bos-390.png) | [Görsel](sonra-ek-mudurluk-bos-390.png) |
| Müdürlük, kısmi | [Görsel](once-ek-mudurluk-kismi-1440.png) | [Görsel](sonra-ek-mudurluk-kismi-1440.png) | [Görsel](once-ek-mudurluk-kismi-390.png) | [Görsel](sonra-ek-mudurluk-kismi-390.png) |
| Müdürlük, iade | [Görsel](once-ek-mudurluk-iade-1440.png) | [Görsel](sonra-ek-mudurluk-iade-1440.png) | [Görsel](once-ek-mudurluk-iade-390.png) | [Görsel](sonra-ek-mudurluk-iade-390.png) |
| Strateji detayı | [Görsel](once-ek-strateji-detay-1440.png) | [Görsel](sonra-ek-strateji-detay-1440.png) | [Görsel](once-ek-strateji-detay-390.png) | [Görsel](sonra-ek-strateji-detay-390.png) |
| İlk altı sorunun özeti | [Görsel](once-ek-alti-soru-ozeti-1440.png) | [Görsel](sonra-ek-alti-soru-ozeti-1440.png) | [Görsel](once-ek-alti-soru-ozeti-390.png) | [Görsel](sonra-ek-alti-soru-ozeti-390.png) |
| 70 soru önizleme | [Görsel](once-ek-onizleme-70-soru-1440.png) | [Görsel](sonra-ek-onizleme-70-soru-1440.png) | [Görsel](once-ek-onizleme-70-soru-390.png) | [Görsel](sonra-ek-onizleme-70-soru-390.png) |
| 70 soru kayıtlı liste | [Görsel](once-ek-kayitli-70-soru-1440.png) | [Görsel](sonra-ek-kayitli-70-soru-1440.png) | [Görsel](once-ek-kayitli-70-soru-390.png) | [Görsel](sonra-ek-kayitli-70-soru-390.png) |

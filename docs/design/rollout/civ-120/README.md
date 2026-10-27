# CIV-120 — PP kaynak karşılaştırması

043 strateji ve 044 müdürlük ekranları, sayfaya özel tasarım sistemi CSS'i ve istemci durum filtresiyle yenilendi. Yalnızca sentetik veriler ve yerel, geçici PostgreSQL 17 kullanıldı.

- Bilgi paneli, beş durumlu tanım listesi, uyarı panelleri, durum sayaçları, metinli rozetler ve sağa hizalı tutarlar.
- Filtre: yalnızca mevcut durumlar ve adetleri; Tümü ile geri dönüş; JS tarafından `aria-pressed`; yerel düğmelerle Tab/Space/Enter. JavaScript kapalıyken tüm satırlar görünür.
- Başlangıç şablonu `tests/fixtures/source_comparison_start.html` içinde byte-identical saklanır. SHA-256: `7f7f56e95ecfc07de38e8feeb79db8f6b53d5cfcc9c4fd259e33beecebc7635d`.
- Donmuş sözleşme iki rolde CSV/dashboard bağlantılarını ve sorgularını, tablo kimliğini, tüm satırların data-status/data-model değerlerini, hücre metinlerini (biçimlendirme boşlukları normalize edilir), uyarıları ve satır sayısını karşılaştırır.

## Görünür metin değişiklikleri

| Önce | Sonra |
| --- | --- |
| PP Kaynak Karşılaştırması | PP kaynak karşılaştırması |
| CSV İndir | CSV indir |
| Genel Bakış | Genel bakış |
| Müdürlük / Kayıt | Müdürlük / kayıt |
| Belge ve Konum | Belge ve konum |
| Kaynak Değer | Kaynak değer |
| Güncel Değer | Güncel değer |
| Durum / Karar | Durum / karar |
| N karşılaştırma satırı | N satır · X eşleşiyor · Y kararla değişti · Z fark var · K kaynakta yok · L kayıtta yok |
| Durumlar: Eşleşiyor · Kararla değişti · Fark var · Kaynakta yok · Kayıtta yok | Aynı beş durum tanım listesine taşındı; “Durumlar” erişilebilir liste adı oldu. |

Eklenen durum açıklamaları (yalnızca mevcut kaynak/güncel kayıt karşılaştırması ve durum adlarının anlamları):

- “Kaynak hücresi ve güncel kayıt eşleşiyor.”
- “Güncel kayıt kararla değişti.”
- “Kaynak hücresi ve güncel kayıt arasında fark var.”
- “Kaynak hücresinde yok.”
- “Güncel kayıtta yok.”

Diğer eklenen metinler: “Tümü (N)”, mevcut her durum için “Durum (N)”, “Bu durumda satır yok.” ve “Tablonun devamını görmek için yatay kaydırın.” Filtre grubunun erişilebilir adı: “Duruma göre filtrele”. Açıklama paragrafı, durum değerleri, uyarılar, satır verileri ve mevcut boş tablo metni değişmedi.

Testler ve app.js değişiklik öncesi tarandı. İzin verilen testler dışında değiştirilmesi istenen bir başlığı eşleyen test/app.js bulunmadı. Başka şablonlardaki gezinme bağlantısının “PP Kaynak Karşılaştırması” metni kapsam gereği aynen korundu; mevcut UI testindeki bağlantı assertion'ı da korundu. Değişen sayfa başlığı, kolonlar ve CSV etiketi için mevcut UI assertion'ları bire bir güncellendi.

## Ekran görüntüleri

Her PNG 1,5 MB sınırının altındadır. Görüntüler sayfanın başlangıcından, değişmeyen ortak mutabakat bölümünün hemen önüne kadar alınır. 390 px'de tablonun devamı kendi kapsayıcısında yatay kaydırılır; sayfa taşmaz.

| Rol / genişlik | Tüm satırlar | Fark var etkin | Boş durum |
| --- | --- | --- | --- |
| Strateji / 1440 | [Tümü](strategy-all-1440.png) | [Fark var](strategy-difference-1440.png) | [Boş](strategy-empty-1440.png) |
| Strateji / 390 | [Tümü](strategy-all-390.png) | [Fark var](strategy-difference-390.png) | [Boş](strategy-empty-390.png) |
| Müdürlük / 1440 | [Tümü](department-all-1440.png) | [Fark var](department-difference-1440.png) | [Boş](department-empty-1440.png) |
| Müdürlük / 390 | [Tümü](department-all-390.png) | [Fark var](department-difference-390.png) | [Boş](department-empty-390.png) |

## Doğrulama

- Odaklı paket: `python -m pytest -q --require-postgres tests/test_source_comparison_design.py tests/test_source_comparison.py tests/test_source_comparison_ui.py tests/test_design_shell.py` — 56 geçti.
- Chromium: iki rol, 1440 ve 390 px; beş durum filtresi, Tümü, Tab/Space/Enter, aria-pressed, JS kapalı tüm satırlar, SHA-256 details, boş durum, yatay taşma ve normal/hover/focus/etkin durumlarda görünür metin kontrastı ≥ 4,5:1 doğrulandı.
- `node --check app/static/design/source-comparison.js` ve `git diff --check` başarılı.
- Son şablon biçimlendirmesinden sonra yeni tasarım paketi: **22 geçti**.
- Yerel tam PostgreSQL 17 paketi: `python -m pytest -q --require-postgres -n 4 --dist loadfile` — **3102 geçti**, 4 mevcut Starlette uyarısı. Koleksiyon rebase öncesi tabanda başladı.
- Güncel tabana rebase sonrasında, yeni CIV-114 testleri dahil odaklı paket: **76 geçti**. Güncel head koleksiyonu: **3122 test**.
- CI ilk denemesinde bir grup **1561 geçti**; diğer grupta kapsam dışı `test_delegation_expires_after_initial_check[performance_program]` testinin bir saniyelik süresi yetki oluşturulmadan doldu (1560 geçti). Testin iki senaryosu yerelde yeniden geçti. Assertion veya uygulama kodu değiştirilmedi. Son head CI sonucu PR açıklamasında kaydedilir.

Canlı veri kullanılmadı. Firefox, WebKit ve gerçek ekran okuyucu ile doğrulama yapılmadı. Sunucu davranışı, erişim izinleri ve veri hesaplamaları için değişiklik varsayılmadı; mevcut sözleşme korundu.

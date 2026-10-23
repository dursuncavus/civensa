# Faaliyet raporu dizgi veri sözleşmesi — ar-typeset/1

CIV-086 / D-190, mevcut rapor JSON'undan ayrı, kararlı kimlikli bir dizgi
sözleşmesi sağlar. Bölüm, tablo, satır, faaliyet ve gösterge kimlikleri yayın
sürümünü veya liste konumunu içermez. Aynı sabit kaynak iki kez indirildiğinde
UTF-8 JSON baytları aynıdır. Yeni sürümde değişmeyen öğeler aynı kimliği taşır.
Gerçek InDesign tasarımının görsel kabulü tasarımcıda kalır.

## İndirme ve erişim

Düzenleyicide ve tamamlanma listesinde Word/PDF yanında **Dizgi verisi (JSON)**
bağlantısı vardır:

- `GET /activity-sections/reports/{document_id}/typeset.json`: güncel taslak
  veya etkin donmuş sürüm.
- `?version=N`: CIV-078 idare yayın zincirindeki belirli sürüm.
- `?approval_id=N`: belirli, sabit birim onayı; birim düzenleyicisinde onay
  geçmişi bağlantıları bulunur. İki seçim birlikte kullanılamaz.

İndirme yetkisi Word/PDF ile aynıdır: Strateji; müdürlük hesabında yalnız kendi
birim raporu. Başka birim ve idare indirmesi müdürlük hesabına kapalıdır.
Yanıt `application/json`, `private, no-store` ve `nosniff` başlıklarını taşır.

Donmuş indirme yalnız `ARDocumentFreeze.payload_json` veya sabit birim onayının
`payload_json` baytlarını ve değişmez sürüm/SHA metadata'sını kullanır. Canlı
bölüm, kaynak, malî bilgi veya gösterge tablolarından değer tamamlamaz.
Mevcut rapor API'sinin yapısı ve eski Word/PDF/JSON indirmeleri korunur.

## D-190: eski sürüm sınırı

c086 öncesinde dondurulmuş, `_typeset` anahtar alanı taşımayan sürüm için
konum/ad/içerik benzerliğinden kimlik tahmin edilmez. İndirme **409** döner:

> Bu sürüm dizgi veri sözleşmesinden önce dondurulmuş. Strateji Geliştirme Müdürü raporu gerekçeyle açıp yeni sürüm yayınlamalıdır.

Eski dosyalar ve SHA-256 değerleri değişmez. İdare kaynaklarında eski birim
onayları varsa önce bu birimler gerekçeyle açılmalı, yeni anahtarlarla tekrar
gönderilip bağımsız onaylanmalıdır; ardından yeni idare sürümü yayımlanır.
Eski, anahtarsız gönderilmiş kopya doğrudan onaylanmaz; gerekçeyle iade ve
tekrar gönderim gerekir. D-190 bu uyumluluk istisnasını açıkça kabul eder.

## Alanlar

| Alan | Anlam |
| --- | --- |
| `schema_version` | Sabit metin `ar-typeset/1`. |
| `document` | Belge `id`, `scope` (`birim`/`idare`), `year`, kurum/birim adı ve kaynak PK'ları; bölüm/faaliyet/gösterge kimlik listeleri. |
| `release_version` | İdarede CIV-078 yayın sürüm numarası; birimde sabit onayın revizyon numarası; taslakta `draft`. |
| `frozen` | Sabit kaynak SHA'sı bulunan indirmede `true`; taslakta `false`. |
| `generated_at` | Kaynağın yakalandığı sabit zaman, ISO 8601 ve TSİ `+03:00`. İndirme anının saati değildir. Taslakta ilgili son kayıt/gösterge/kaynak-onay zamanı kullanılır; tekrar indirme saati değiştirmez. |
| `source_sha256` | Donmuş payload'ın özgün UTF-8 baytlarının SHA-256 değeri; taslakta `null`. |
| `sections` | Sıralı bölüm kaydı: `id`, EK-1 kodu/başlığı, metin/liste blokları, tablo referansları, durum, gerekçe, mevcut düzenleme/kopyalama alanları. |
| `tables` | Tablo `id`, `kind`, başlık, bölüm kimliği, mevcut sütun tanımları, sunum sırasındaki `row_ids`, toplamlar ve tablo metadata'sı. |
| `rows` | Satır `id`, `table_id`, kaynak alanlarını koruyan `values`; bilinen köken varsa `provenance`. |
| `indicators` | Kalıcı kaynak gösterge kimliğiyle `id`, bölüm referansı, kaynak birim/belge kimliği, hedef/gerçekleşme, durum, kanıt, açıklama ve sapma. |
| `activities` | Bağlı, doğrulanmış PP yayınındaki faaliyet PK'sıyla `id`, bölüm referansı ve faaliyet bilgileri. Maliyetler ayrı, PK'lı tablo satırlarıdır. Canlı faaliyet adı/maliyeti okunmaz. |
| `context`, `financial_context`, `core_context`, `resource_source_context` | Yayın/revizyon, kaynak birim manifesti, eksikler/kontroller, eşikler, kaynak sürümleri ve diğer mevcut rapor metadata'sı. Öğelerin alt içerik hash'lerini üst öğelere taşımayan kaynak bağlamıdır. |
| `manifest.items` | Belge dahil bütün dizgi öğesi kimliklerinin SHA-256 eşlemesi. |
| `manifest.contract_sha256` | Aşağıdaki kanonikleştirme kuralıyla bütün sözleşmenin SHA-256 değeri. |

Sözlük anahtarları alfabetik; öğe dizileri `id` ile sıralıdır. Bölüm konumu ve
`row_ids` dizileri sunum sırasını korur. Metin blokları kaydedilmiş sıradadır.
Gösterge/faaliyet tablolarının `row_ids` değerleri ilgili `indicators` ve
`activities` kayıtlarına; diğer tablolarınkiler `rows` kayıtlarına başvurur.
Serbest metin tablosunda başlık satırı da kaynakta saklandığı gibi bir satırdır;
başlık veya sayısal sütun türü tahmin edilmez.

## Kimlik kuralları

`ar:{belge_PK}` öneki yayın sürümünden bağımsızdır. Kullanılan PK'lar kaynak
belgede/PP yayınında zaten bulunan kimliklerdir. Serbest kimlik UUID'leri bir kez
üretilip veritabanında saklanır; dışa aktarmada üretilmez.

| Öğe | Kimlik kuralı |
| --- | --- |
| Belge | `ar:{belge_PK}` |
| Bölüm | `{belge}:section:{EK-1_kodu}` |
| Serbest bölüm tablosu | `{bölüm}:table:{saklanan_UUID}` |
| Serbest tablo satırı | `{tablo}:row:{saklanan_UUID}` |
| Kaynak tablosu | `{belge}:resource:{table_kind}` |
| Kaynak satırı | `{kaynak_tablosu}:row:{kaynak_belge_PK}:{saklanan_UUID}` |
| Bütçe tablosu/satırı | `{belge}:budget:{kind}` ve `:row:{saklanan_row_key}` |
| Serbest malî tablo/satırı | `{belge}:financial:{kind}` ve `:row:{kaynak_belge_PK}:{saklanan_UUID}` |
| Malî tablo/özet rakamı | `{belge}:statement:{tablo_PK}` ve `:row:{saklanan_UUID}` |
| Gösterge | `{belge}:indicator:{kaynak_belge_PK}:{mevcut_indicator_identity_PK}` |
| Faaliyet | `{belge}:activity:{birim_PK}:{PP_faaliyet_PK}` |
| Faaliyet maliyeti | `{faaliyet}:costs:row:{maliyet_PK}` |
| Hesaplanan tür/mülkiyet grubu | Kaynak tablosunun `:groups` tablosu; satır kodu mevcut `(category, ownership)` grup boyutlarının kanonik JSON metnidir. |
| Hesaplanan birim toplamı | Bütçe tablosunun `:departments` tablosu; satır kodu birim PK'sı veya idare toplamı için `None` sabitidir. |

Kod parçaları UTF-8 URL kodlamasıyla kaçırılır; sıra numarası kimliğe katılmaz.
Aynı içerikli iki serbest satır ayrı UUID'ler taşır. Bir satır silinirse kimliği
manifestten çıkar; aynı değerlerle yeni satır oluşturulursa yeni UUID alır.

c086 göçü `down_revision=c084a1b2c3d4` olan tek baştır. Serbest bölüm tabloları,
satırları ve malî özet rakamları için ayrı anahtar kayıtları; kaynak/serbest
malî satırlarda `stable_key` sütunu kullanılır. UUID metni **NOT NULL** ve kendi
üst kaydı içinde **UNIQUE** olur. Var olan canlı kayıtlar geri doldurulur;
eski payload'lara dokunulmaz. Anahtar taşıyan donmuş idare/birim payload'ı varsa
downgrade Türkçe hata ile reddedilir; yoksa içerik korunarak c084'e dönülebilir.

## Kaydederken anahtarları koruma

HTML formları kaynak/malî satır ve özet rakam anahtarlarını gizli alanlarda;
serbest bölüm tablosu/satır anahtarlarını `table_keys` alanında taşır. Yeni
satırın alanı boştur ve ilk kayıtta UUID alır. Mevcut satırlar yerinde güncellenir.
Anahtarı olmayan, değişmemiş eski istemci girdileri aynı canlı kayıtla eşleşir;
değişen kaydı güncelleyen API istemcisi mevcut anahtarı göndermelidir.
Başka üst kayda ait veya yinelenen anahtar 422 ile reddedilir.

API istemcisi mevcut anahtarları
`GET /api/activity-sections/reports/{document_id}/typeset-keys` ile alabilir.
Bu salt metadata ucu mevcut rapor okuma yetkisini kullanır; eski rapor JSON'una
alan eklemez. Kaynak ve serbest malî `rows` öğesinde `stable_key`; bölüm
kaydında `table_keys=[{position, stable_key, rows:[UUID veya null]}]`; malî
`figures` öğesinde `stable_key` gönderilir. `position` yalnız hangi metin
bloğunun düzenlendiğini belirtir; kimlik üretme girdisi değildir.

Her yeni birim gönderimi ve idare dondurması bu kayıtlı kimlikleri `_typeset`
(`ar-source/1`) alanına alır. Birim onayı incelemedeki aynı payload'ı korur;
idare konsolidasyonu yalnız onaylı birim payload'larındaki kimlikleri taşır.

## Sayılar ve köken

Türlü sayısal alanların gösterimi `{exact, display}` biçimindedir:

```json
{"exact":"12500.230000","display":"12.500,230000"}
```

`exact`, saklanan ondalık metindir; float'a çevrilmez, yuvarlanmaz ve saklanan
ölçek korunur. `null` → `{"exact":null,"display":"—"}`;
sıfır ise gerçek sayıdır. PK, yıl, revizyon ve konumlar metadata olarak kalır.
Serbest metin hücreleri, kaynak metinleri ve sınıflandırma kodları metindir;
“01.01” veya “12.500” metninden sayısal anlam çıkarılmaz.

Köken yalnız eldeki kanıttan eklenir: bölümde `edited_by` varsa `manual`;
kopyalama referansı varsa `previous_year_copy`; bütçe satırında `import_id`
varsa `xlsx_import`; mevcut hesaplanan toplam, yıl sonu/net/oran ve
`difference-v1` sapmasında `computed`. Kökeni tutulmayan kaynak/serbest malî
satıra yalnız import kimliği boş diye “elle girildi” etiketi konmaz.

## Hash doğrulama ve sürüm kuralı

Kanonik JSON: UTF-8, `ensure_ascii=false`, alfabetik sözlük anahtarları,
boşluksuz `,`/`:` ayırıcıları, satır sonu olmadan; NaN/Infinity yasaktır.
Her öğe hash'i yalnız kendi kaydı üzerindedir. Alt öğe içeriği yerine sabit
kimlik referansları bulunur. Böylece tek gösterge değeri değişince yalnız o
öğenin hash'i ve bütün sözleşmenin hash'i değişir. Yayın sürümü, kaynak SHA ve
zaman metadata'sı belge öğesinin hash'ine dahil edilmez; bütün hash'e dahildir.

Bütün hash için yalnız `manifest.contract_sha256` alanını çıkarıp kalan
nesnenin kanonik baytlarını SHA-256 ile özetleyin. `manifest.items` bu kapsama
dahildir. Hash kendi kendisini kapsamaz. `verify_contract()` çevrimdışı
bütünlük ve öğe manifesti doğrulaması sağlar.

Kimlik türetme, alan anlamı/türü, sayı temsili, sıralama veya hash kapsamını
bozan değişiklikte `schema_version` artırılır; eski sürümün anlamı sessizce
üretilen yeni kurallarla değiştirilmez. Eklenen isteğe bağlı metadata ancak
mevcut okuyucuların ve hash kurallarının uyumluluğu korunuyorsa aynı sürümde
kalabilir. Eski sabit payload için üretilen `ar-typeset/1` baytlarını değiştiren
serileştirme değişikliği de sürüm artışı gerektirir. Kaynak `_typeset` biçimi
ayrıca sürümlüdür.

## CSV ve InDesign tekrar birleştirme

Tablo başına CSV için:

```sh
python tools/ar_typeset_csv.py faaliyet-raporu-dizgi.json dizgi-csv
```

Araç önce hash'leri doğrular. UTF-8 BOM içeren, virgülle ayrılmış CSV'ler ve
`tablolar.json` kimlik/başlık/dosya eşlemesi üretir. Dosya adları tablo
kimliğinin SHA-256 değerinden gelir. İlk sütun daima `id`; sayılarda
`actual.exact` ve `actual.display` gibi ayrı alanlar vardır. Serbest metin
hücreleri `cell_1`, `cell_2` sütunlarıyla korunur. CSV satır sırası tablonun
sunum sırasıdır; kimlik sütunu sıralamadan etkilenmez.

InDesign'ın yerleşik Veri Birleştirme özelliği JSON okumaz ve kalıcı kimlikle
mevcut sayfa öğelerini otomatik güncellemez. Tekrar birleştirme betiği/eklenti:

1. `schema_version` ve hash'leri doğrular; JSON veya ilgili CSV'yi açar.
2. Her çerçeve/satırın `id` değerini InDesign script label alanına kaydeder.
3. Sonraki indirmede aynı etiketi bulup değerleri değiştirir; görünen sayı için
   `.display`, hesap veya karşılaştırma için `.exact` kullanır.
4. Yeni kimlik için yeni öğe oluşturur. Artık bulunmayan kimliği tasarımcıya
   listeler; silme/gizleme kararı açıkça verilir.
5. Aynı dosyayı tekrar aldığında ek öğe üretmediğini ve bir gösterge güncellemesinin
   yalnız etiketli ilgili değeri değiştirdiğini tasarım dosyasında doğrular.

Hazır InDesign betiği veya gerçek tasarım dosyasında görsel kabul bu kod
kapsamına dahil değildir. Elle yeniden yerleştirme yerine aynı script label
kimlikleriyle güncelleyen bir betik kullanılmalıdır.

## Sentetik örnek ve kanıt

`tests/artifacts/civ086/` altında `synthetic-source.json`,
`release-1.typeset.json`, `release-2-one-indicator.typeset.json` ve
`hardware.csv` bulunur. İki örnek aynı kimlikleri taşır; ikinci örnekte yalnız
bir gösterge ve bütün sözleşme hash'i değişir. Gerçek kurum verisi değildir.

Örnekleri yeniden üretme: `python tests/artifacts/civ086/generate_sample.py`.
`identity-loss.json`, D-190 öncesi engelin tarihî karşı örneğidir; güncel çıktı
olarak kullanılmaz. Kabul testleri `tests/test_ar_typeset_contract.py` ve
`tests/test_ar_typeset_migration.py` içindedir. Mevcut Word/PDF/yayın zinciri
testleri değiştirilmeden çalıştırılır.

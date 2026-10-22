# Faaliyet raporu dizgi veri sözleşmesi — CIV-086 engel kaydı

**Durum: ENGELLİ. `ar-typeset/1` henüz uygulanmadı veya yayımlanmadı.**
AR-14 kapanmamıştır. Görevdeki “kararlı kimlik mevcut anahtar/kodlardan
türetilemiyorsa dur ve PR açıklamasında bildir” kuralı uygulanır. Bu belge
tasarım sınırını ve yeniden üretilebilir kanıtı kaydeder; çalışan bir indirme
veya InDesign entegrasyonu vaat etmez.

## Kaybolan kimlikler

| Veri | Mevcut kimlik | Engel |
| --- | --- | --- |
| Belge ve bölüm | `ARDocument.id`, bölüm `code` | Bu düzeylerde kimlik türetilebilir. |
| Kaynak tablosu | Belge + `table_kind` | Tablo düzeyinde kimlik türetilebilir. |
| Kaynak satırı | `ARResourceRow.id` | `row_data()` kimliği çıkarır; donmuş payload'da yoktur. Aynı içerikli satırlar geçerlidir. `save_resources()` değişmeyen satırları bile silip yeniden ekler. |
| Gösterge | `IndicatorDefinitionRevision.indicator_id` | `core_summary()` bu mevcut kalıcı kimliği çıktıya taşımaz. Eski donmuş payload'dan kimliğe ulaşmak başka tablolara başvurmayı gerektirir. |
| Metin içindeki tablo ve satırı | Yok | `ARSectionContent.blocks_json` yalnız `type`/`rows` ve hücre listelerini saklar. Aynı bölümde aynı tablo ve aynı satır birden fazla kez bulunabilir. |
| Serbest malî kayıt | `ARFinancialEntry.id` | `entries()` yalnız `payload_json` döndürür; `save_entries()` kayıtları silip yeniden ekler. Genel bir değişmez satır kodu yoktur. |
| Faaliyet | Tam raporda her faaliyet için korunmuş kimlik yok | III.B.1 bölümünün bulunması yapılandırılmış faaliyet manifesti sağlamaz; yalnız bölüm kimliği faaliyet kimliği yerine kullanılamaz. |

`tests/artifacts/civ086/identity-loss.json` yalnız sentetik veridir. İki ayrı
kaynak satırının PK'ları farklı olduğu halde donmuş izdüşümleri aynıdır.
İlk satırın değeri değiştiğinde eski PK'yı elde etmek mümkün değildir:

- Liste sırası kimlik olamaz; görev bunu açıkça yasaklar.
- İçerik hash'i kimlik olamaz; değer düzenlenince kimlik de değişir ve aynı
  içerikli iki kayıt çakışır.
- Ad/kategori kimlik olamaz; benzersizlik garantisi yoktur ve ad değişebilir.
- Rastgele UUID'yi her indirmede üretmek tekrar birleştirmeyi bozar.
- Canlı tablolardan eşleştirmek eski sürümü canlı duruma bağımlı kılar ve
  “yalnız donmuş payload” şartını ihlal eder.

Yeni dışa aktarma fonksiyonunun anahtarları sıralaması bu bilgi kaybını
gidermez. Yeni bir şema değişikliği de eski payload'da hiç bulunmayan kimliği
tek başına geri getiremez. Gelecek kayıtlar için JSON içinde kalıcı anahtar
saklamak SQL göçü olmadan değerlendirilebilir; bunun için yazma/doğrulama
akışının değiştirilmesi gerekir ve eski sürümlerin kimlik garantisi yine çözülmez.

## Devam etmek için gereken kapsam kararı

Eski sürümler için açık bir uyumluluk istisnası veya ayrı, onaylı kimlik
eşleştirme kaynağı tanımlanmalıdır. İkinci seçenek yalnız payload kullanma
şartını değiştirir. Kimliği belirlenemeyen geçmiş raporlarda tam sözleşme
reddedilebilir; ancak bu da “her donmuş sürüm için indirme” kabulünü değiştirir.
Bu seçeneklerden hiçbiri bu PR'da varsayılmamıştır.

Gelecek sürümlerde tablo/satır kimliği ilk oluşturulurken saklanmalı,
düzenleme ve yeniden açmada korunmalı, kaynak ve gösterge kimlikleri onaylı
birim ve idare payload'larına taşınmalıdır. Değişmeyen kaynak/malî satırların
silinip yeniden oluşturulması bırakılmalıdır. Mevcut donmuş payload, SHA-256,
Word/PDF/JSON baytlarına dokunulmamalıdır.

## Karar sonrası sözleşmenin gereksinimleri

Aşağıdakiler uygulama değil, görevden gelen hedef alanlardır:

| Alan | Hedef anlam |
| --- | --- |
| `schema_version` | `ar-typeset/1` |
| `id`, `scope`, `year` | Kalıcı belge kimliği, birim/idare kapsamı, rapor yılı |
| `release_version` | CIV-078 yayın sürümü veya `draft` |
| `generated_at` | TSİ, `+03:00`; tekrar indirmede değişmeyen kaynak zamanı gerekir |
| `source_sha256` | Donmuş kaynak payload'ın SHA-256 değeri |
| Öğe `id` | Bölüm, tablo, satır, faaliyet ve gösterge için kalıcı kaynak anahtarı |
| Sayısal alan | Saklanan hassasiyette ondalık metin + Türkçe gösterim; null ve sıfır ayrı |
| Köken | Yalnız kaynakta kayıtlı elle giriş/XLSX/kopyalama/hesaplama bilgisi |
| Manifest | Tüm kimlikler ve öğe SHA-256'ları; tüm sözleşmenin SHA-256 değeri |

Hash kapsamı uygulamadan önce kesinleştirilmelidir: bir göstergenin değeri
değişince üst bölüm/tablo hash'lerinin değişmemesi için öğe hash'leri çocuk
içeriği yerine çocuk kimliklerini kapsamalıdır. Bütün sözleşme hash'i kendi
hash alanı çıkarılarak hesaplanmalıdır. Sıralama ve UTF-8 kanonik JSON
kuralları sabitlenmelidir.

## InDesign tekrar birleştirme sınırı ve sürüm kuralı

InDesign'ın yerleşik Veri Birleştirme özelliği JSON içe almaz ve kalıcı kimlikle
mevcut sayfa öğelerini otomatik güncellemez. Tablo başına CSV yalnız veri
taşıma adımıdır. Tasarımcıyla bir betik/eklenti akışı seçilmeli; betik her
öğenin kalıcı `id` değerini etiket olarak saklayıp sonraki içe aktarmada aynı
etiketli öğeyi güncellemelidir. Ekleme/silme politikası ayrıca tanımlanmalı;
değişmeyen sürüm ve tek gösterge değişikliğiyle gerçek tekrar birleştirme
provası yapılmalıdır. Bu PR bir CSV veya InDesign betiği sağlamaz.

Yayımlandıktan sonra kimlik türetme, alan anlamı/türü, sayı temsili, sıralama
veya hash kapsamını değiştiren uyumsuz değişiklik yeni `schema_version`
gerektirir. Eski sürümler yeni kurallarla sessizce yeniden yorumlanmamalıdır.

## Doğrulama

`tests/test_ar_typeset_identity_blocker.py` geçici PostgreSQL üzerinde
ayırt edilemeyen kaynak satırlarını, aynı kayıtta PK değişimini, kimliksiz
serbest tabloları ve çıktıdan düşen mevcut gösterge kimliğini doğrular.
Bu testler `ar-typeset/1` kabul testleri değildir; kapsam kararı verildiğinde
yeni sözleşme kabul testleriyle değiştirilmelidir.

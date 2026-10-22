# PostgreSQL dosya depolama denetimi (CIV-080)

Bu envanter `feature/authorization-workflow-phase5` kaynak kodunun incelemesine
dayanır. Canlı veritabanına bağlanılmadı; Render planı, disk kapasitesi ve mevcut
doluluk **bilinmiyor**. Herhangi bir ölçüm sonucu veya tahmini kapasite olarak
sunulmamalıdır. Bu görev depolama mimarisini değiştirmez, migrasyon içermez.

## Dosya ve görsel içeren sütunlar

| Tablo | Sütun | Model dosyası | İçerik ve kopyalanma yolu |
| --- | --- | --- | --- |
| `activity_evidence_files` | `file_data` | `app/activity_evidence_models.py` | PDF/XLSX kanıt dosyasının ham baytları (`LargeBinary` → `bytea`); her dosya sürümü ayrı, değişmez kayıt. |
| `ar_financial_statements` | `file_data` | `app/activity_financial_models.py` | İsteğe bağlı PDF/XLSX malî tablo eki (`LargeBinary` → `bytea`). |
| `report_sections` | `content_json` | `app/models.py` | PP bölüm görseli: `kind=image` olduğunda JSON içindeki `data` alanında base64 PNG/JPEG. Dönem kopyalama görseli de kopyalar. |
| `import_batches` | `payload_json` | `app/models.py` | Word içe aktarma önizlemesinde `general_sections[].content.data` görselleri. |
| `import_batches` | `snapshot_json` | `app/models.py` | Uygulanan içe aktarmanın geri alma kaydındaki `created_sections[].content_json` görsel kopyaları. |
| `publications` | `snapshot_json` | `app/models.py` | Dondurulmuş PP `sections[].content_json` içinde base64 görsel kopyaları. Her yayın sürümü ayrı kopya taşır. |
| `report_candidates` | `payload_json` | `app/report_workflow_models.py` | Performans programı adayının `sections[].content_json` kopyaları. |
| `report_artifacts` | `content_json` | `app/report_workflow_models.py` | Kanonik JSON yayın çıktısının `payload.sections[].content_json` kopyaları. `byte_size` bu çıktının tamamının bayt sayısıdır. |

Base64 depolaması doğrulandı: elle yüklemede `app/program_routes.py`, Word'den
aktarmada `app/import_service.py` kodlar; `app/program_service.py` ve
`app/report_workflow_service.py` bölüm JSON'unu yayın/aday/çıktıya kopyalar.
`app/structure_service.py` dönemler arası bölüm kopyasını oluşturur.

Kaynak kodda başka `LargeBinary` veya kalıcı dosya/görsel base64 üretim yolu
bulunmadı. `app/book_export.py` grafik görsellerini yalnızca çıktı üretimi sırasında
bellekte base64 yapar. Oturum çerezi base64'ü veritabanında dosya depolaması değildir.
Şablon yüklemeleri ve diğer içe aktarmalar özgün DOCX/XLSX dosyasını saklamaz;
ayrıştırılmış içerik ve kaynak bilgisi saklar. AR bölüm blokları metin/tablo
içerir; mevcut şemada bölüm görseli yükleme yolu yoktur.
Kanıt manifestleri, gerçekleşme/paket kayıtları ve AR dondurmaları eklerin
kimliğini, dosya adını ve SHA-256 bilgisini taşır; dosya baytlarını kopyalamaz.

## Mevcut yükleme sınırları

Yeni ayar gerekmedi; mevcut daha sıkı sınırlar korundu:

| Yükleme | Sınır | Uygulama yeri |
| --- | --- | --- |
| Gösterge kanıtı (PDF/XLSX) | Dosya başına 10 MB | `app/activity_financial_service.py:MAX_FILE`, `app/activity_evidence_service.py:validate_file`; API ve form en fazla sınır + 1 bayt okur. |
| Elle yüklenen PP bölüm görseli | Görsel başına 5 MB, en fazla 16 megapiksel, PNG/JPEG | `app/program_routes.py`, `/report-builder/section`; sınır + 1 bayt okur, Pillow ile doğrular. |
| Word'den gelen PP bölüm görseli | Görsel başına 5 MB, en fazla 16 megapiksel, PNG/JPEG | `app/import_service.py:parse_performance_document`; aşan görsel saklanmaz, önizlemeye Türkçe uyarı eklenir. |
| Malî tablo eki (PDF/XLSX) | Dosya başına 10 MB | `app/activity_financial_service.py:save_statement`; yükleme rotası da sınır + 1 bayt okur. |

Burada MB = 1.048.576 bayt (MiB). Sınıra eşit dosya kabul edilir, bir bayt
fazlası reddedilir. Elle kanıt/görsel yüklemede HTTP 422 mesajı:
`Dosya çok büyük. En fazla {N} MB yüklenebilir.` (`N`: 10 veya 5).
Başlık, açıklama, kaynak satırları ve diğer form değerleri hata halinde korunur
(CIV-064 form kurtarma düzeni). Tarayıcı dosya alanı yeniden doldurulamaz;
kullanıcı daha küçük dosyayı yeniden seçer. Word içe aktarma mevcut uyarı
davranışını sürdürür. Malî tablo ekinin mevcut Türkçe boyut hatası korunur.

**Toplam kota yoktur.** Dosya/sürüm/sayfa/dönem sayısı arttıkça veritabanı
büyümeye devam eder. Bu sınırlar kullanıcı başına, kurum başına veya veritabanı
toplamı için kota değildir. Eski kayıtlar bu değişiklikle silinmez veya küçülmez.

## Salt okunur rapor

Bağımlılıkları kurulu ortamda depo kökünden, yalnızca yetkilendirilmiş bir
**yerel/tek kullanımlık PostgreSQL** bağlantısıyla çalıştırın. Bu görev kapsamında
canlı veritabanına bağlanmayın. Bağlantıyı ortamın gizli değişken mekanizmasından
`DATABASE_URL` olarak sağlayın; URL/parolayı komuta, terminal çıktısına, belgeye
veya PR'a yazmayın.

```sh
python -m ops.db_storage_report
# Aynı giriş noktası:
python ops/db_storage_report.py
# Ayrı bir test şeması için:
python -m ops.db_storage_report --schema civensa_test_example
```

Varsayılan şema `public`'tir. `postgres://`, `postgresql://` ve
`postgresql+psycopg://` desteklenir. SQLite dahil diğer sistemlerde
`PostgreSQL only` açıklamasıyla bağlantı kurmadan 1 çıkış kodu döner.
Bağlantı hataları ayrıntı/kimlik bilgisi yazdırmadan genel Türkçe mesaj verir.
Uygulama başlatılmaz; migrasyon/seed çalıştırılmaz.

İlk SQL komutu **`SET TRANSACTION READ ONLY`** olur. Ardından tekrarlanabilir
okuma izolasyonu seçilir; işlem sonunda rollback yapılır. Rapor rolünün ilgili
şemada `USAGE`, ölçülen tablolarda `SELECT` ve veritabanı boyutunu okuma yetkisi
olmalıdır. Ek savunma için yazma yetkisi olmayan bir rol kullanın.

JSON çıktısı:

- `database_bytes`: `pg_database_size(current_database())`, tüm veritabanının
  fiziksel boyutu; şema seçimi bunu değiştirmez.
- `tables`: seçilen şemadaki her tablonun `pg_total_relation_size` boyutu;
  tablo, indeksler ve TOAST dahildir. Boş tablolar da listelenir.
- `columns`: katalogdan bulunan tüm `bytea` sütunları ile yukarıdaki altı base64
  taşıyabilen metin sütunu. Her biri için `row_count` (NULL dahil tüm satırlar),
  `value_count` (NULL olmayanlar), `total_bytes`, `max_bytes` ve boyuta göre en
  büyük beş `largest_rows` (`id`, `bytes`) bulunur. Eşitlikte küçük ID önce gelir.
  Boş tabloda boyutlar 0, liste boştur. NULL değer en büyükler listesine alınmaz.
- `missing_base64_columns`: henüz uygulanmamış şema sürümü gibi nedenlerle
  bulunamayan envanter sütunları; eksikliği sessizce gizlemez.

Sütun boyutları `octet_length` ile ölçülür: `bytea` için özgün dosya baytları,
metin için **base64 dahil tüm JSON'un UTF-8 baytları**. Metin alanındaki her
satır görsel içermeyebilir; JSON ölçümü yalnızca görsel baytları anlamına gelmez.
Base64 yaklaşık %33 ek yük getirir. TOAST sıkıştırması nedeniyle mantıksal
bayt toplamı ile fiziksel tablo boyutu farklı olabilir. Aynı dosyanın kopyaları
ayrı ayrı sayılır; tablo/sütun/veritabanı ölçümlerini birbirine eklemeyin.
Boyut fonksiyonları fiziksel depolamanın anlık değeridir, eşzamanlı yazmalar
nedeniyle rapor sırasında değişebilir. Tam sütun taraması büyük veritabanında
zaman ve okuma yükü oluşturur; sakin bir zamanda çalıştırın.

Çıktı dosya içeriği, dosya adı, kişi adı veya bağlantı URL'si içermez; yalnızca
şema/tablo/sütun adları, sayılar ve kayıt ID'leri içerir. ID'ler yine kurum içi
operasyon verisidir. Raporu erişim kontrollü saklayın.

## Tahmini büyüme ve değerlendirme eşiği

Aşağıdaki sayılar **ölçüm değildir**, bir dönem ve dosya başına tek sürüm
varsayımıyla yaklaşık mantıksal alan tahminidir. 50 birim varsayılmıştır.

| Senaryo | Varsayım / hesap | Yaklaşık mantıksal boyut |
| --- | --- | --- |
| Hafif kanıt yükü | 50 birim × 20 dosya × 0,5 MiB | 500 MiB |
| Orta kanıt yükü | 50 × 100 × 2 MiB | 10.000 MiB ≈ 9,77 GiB |
| Sınıra yakın kanıt yükü | 50 × 100 × 10 MiB | 50.000 MiB ≈ 48,83 GiB |
| PP görselleri, tek kopya | 50 × 10 görsel × 1 MiB × 4/3 base64 | ≈ 667 MiB |
| Aynı görseller, dört kopya | Bölüm + aday + yayın + kanonik çıktı | ≈ 2,60 GiB |
| Word'den gelen görseller, altı kopya | Önizleme + geri alma + yukarıdaki dört kopya | ≈ 3,91 GiB |

Son iki satır alternatif kopyalama senaryolarıdır; birbirine eklenmez. PP
görselleri gerçekte kurum bölümleridir; 50 × 10 yalnızca karşılaştırma varsayımıdır.
Ek kanıt sürümleri, yeni dönemler, tekrar yayınlar, JSON metni, diğer tablolar,
indeksler, WAL ve yedekler bu hesaplara dahil değildir. Gerçek kapasite planı
rapor ve sağlayıcı disk ölçümlerine dayanmalıdır.

Önerilen operasyon eşiği: sağlayıcı kapasitesi öğrenildikten sonra **kullanım
%60'a ulaştığında veya son ölçümlerdeki büyüme hızıyla 90 gün içinde %80'e
ulaşılması bekleniyorsa**, dosyaları PostgreSQL dışına taşıma tasarımını
değerlendirin. Bu bir Render teknik sınırı veya otomatik taşıma/kota değildir;
pilot için erken planlama önerisidir. Haftalık ve toplu yükleme öncesi/sonrası
ölçümleri karşılaştırın; kullanılabilir alan ve büyüme hızını kaydedin. %80
dolulukta kapasite artışı veya yeni yüklemelerin operasyonel olarak sınırlandırılması
için sorumlu ekiple karar verin. Geçmiş kanıtları ve değişmez yayınları silmeyin.

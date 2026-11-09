# CIV-194 — Kesin hesap PDF dönüştürücü

`scripts/kesin_hesap_xlsx.py`, kesin hesap metin PDF’lerini Faaliyet Raporu
III.A.1 için mevcut malî bilgiler XLSX şablonlarına dönüştürür. Uygulama kodu,
veritabanı, şema veya içe aktarma yetkileri değiştirilmez. Script ağ bağlantısı
kurmaz; uygulamayı ve veritabanı modüllerini yüklemez.

## Kullanım

Depodaki geliştirme bağımlılıkları gerekir (`pypdf`, `openpyxl`); yeni bağımlılık yoktur.
Depo kökünden veya başka bir çalışma dizininden çalıştırılabilir:

```sh
python scripts/kesin_hesap_xlsx.py \
  --gider /operator/gider-2026.pdf \
  --gelir /operator/gelir-2026.pdf \
  --year 2026 \
  --departments /operator/mudurlukler-2026.csv \
  --out /operator/sonuc-2026
```

`--gider` ve `--gelir` seçeneklerinden biri veya ikisi verilir. `--year`,
`--departments` ve `--out` zorunludur. 2026 kesin hesabı 2027’de geldiğinde de
`--year 2026` kullanılır. Gelir başlıklarındaki önceki yıl, hesap yılı ve sonraki
yıl bu seçenekle doğrulanır. Giderde yıl sütunu bulunmadığından kaynak dosyanın
yılını operatör ayrıca kontrol etmelidir.

CSV, operatörün Civensa kurum yapısından **kesin hesap yılı için** dışa aktardığı
eşlemedir. UTF-8 veya UTF-8 BOM, virgül ayracı ve şu üç başlık kullanılır
(başlık sırası değişebilir):

```csv
budget_code,department_id,department_name
10,101,Sentetik A Müdürlüğü
20,102,Sentetik B Müdürlüğü
```

Örnekteki adlar, numaralar ve testlerdeki bütün tutarlar sentetiktir.
`department_id`, Civensa’nın müdürlük numarasıdır. `budget_code`, PDF kurum
kodunun son parçasıdır; bir basamaklı kodlar iki basamağa tamamlanır. Kod
yeniden numaralandırılmışsa sonraki yılın listesi kullanılmaz. Script dönem
eşlemesini veritabanından aramaz, isim benzerliğiyle veya kod sırasıyla tahmin
etmez. Aynı kodun veya müdürlük numarasının birden çok kayıtta bulunması hatadır.

Başarıda çıkış kodu `0`; `expenditure.xlsx` ve/veya `revenue.xlsx` ile Türkçe
`report.md` üretilir. Çalışma sayfası `Malî Bilgiler`, başlıklar mevcut
`template(kind)` ile aynıdır. Tutarlar, Excel’in kayan nokta yuvarlamasıyla
kuruş kaybetmemesi için Türkçe sayı metni olarak saklanır; mevcut önizleme bu
biçimi destekler. Kodların baştaki sıfırları korunur.

Üretilen dosyalar mevcut XLSX **önizleme → uygulama** akışıyla içe aktarılır.
Önizleme kontrol edilmeli, gerekli sapma açıklamaları doldurulmalıdır. Script
içe aktarma uygulamaz ve raporun yayımlanma durumunu değiştirmez.

## Sütun eşlemesi

Giderde çıktı anahtarı `(müdürlük, düzey 1 ekonomik kod)`; ekonomik kod aralığı
`01`–`09`’dur. Fonksiyonel/finansal dallardaki tutarlar toplanır. Kurum,
fonksiyon, finansman ve daha alt ekonomik düzeylerin ara toplamları tekrar
toplanmaz.

| XLSX sütunu | PDF kaynağı |
| --- | --- |
| Müdürlük No | CSV `department_id` |
| Ekonomik Kod | Ekonomik Kodu, düzey 1 |
| Başlangıç Ödeneği | Geçen Yıldan Devreden + Bütçe İle Verilen |
| Eklenen Ödenek | Ek Ve Olağanüstü Verilen + Aktarma Suretiyle Eklenen (+) |
| Düşülen Ödenek | Aktarma Düşülen (-) |
| Bildirilen Yıl Sonu Ödeneği | Net Ödenek Toplamı |
| Harcama (Gerçekleşme) | Bütçe Gideri Toplamı |
| İptal Edilen Ödenek | İptal Edilen Ödenek |
| Ertesi Yıla Devreden Ödenek | Gelecek Yıla Devrolan Ödenek |
| Sapma Açıklaması | Boş |

Gelirde her düzey 1 kod için tek satır üretilir; alt düzeyler tekrar toplanmaz.

| XLSX sütunu | PDF kaynağı |
| --- | --- |
| Ekonomik Kod | Gelirin Kodu, düzey 1 |
| Bütçe Tahmini | Bütçe ile Tahmin Edilen |
| Tahsilat (Gerçekleşme) | Hesap Yılı Tahsilatı (brüt) |
| Red ve İadeler | Red ve İadeler |
| Sapma Açıklaması | Boş |

Net tahsilat, brüt tahsilat yerine aktarılmaz; mevcut uygulama neti tahsilattan
red ve iadeyi düşerek hesaplar.

## Mutabakat ve durdurma kuralları

1. Her müdürlükte ekonomik düzey 1 satırlarının toplamı, PDF’deki müdürlük
   satırına **11 kaynak tutar sütununun tamamında** eşit olmalıdır. Aktarılmayan
   Ödenen Bütçe Gideri ve Ödenek Üstü Harcama sütunları da kontrol edilir.
2. Müdürlük satırlarının toplamı, üç parçalı belediye kurum kodunun (örneğin
   `46 34 14`) toplamına aynı 11 sütunda eşit olmalıdır. Belediyenin ve her
   müdürlüğün üst toplamı bulunmalıdır.
3. Çıktıdaki başlangıç + eklenen − düşülen, bildirilen yıl sonu ödeneğine
   eşit olmalıdır; böylece mevcut önizlemenin ödenek denetimi de korunur.
4. Her gelir düzey 1 ve toplam satırında `Toplam Tahakkuk = Devreden + Yılı
   Tahakkuku` ve `Net = Tahsilat − Red` eşitlikleri aranır. Bölünmüş tutar ancak
   ilgili eşitlik doğrulanırsa birleştirilir; önceki parçalar ve birleşim
   rapora yazılır. Tahmin ve devreden gelecek yıl tutarları bu iki eşitlikle
   kanıtlanamadığından bunlardaki bölünmeler hatadır.
5. Gelir genel toplam satırı varsa sekiz parasal sütun düzey 1 satırlarıyla
   karşılaştırılır. Yüzde olan Oran toplanmaz. Toplam satırı yoksa bu denetimin
   yapılamadığı raporda açıkça belirtilir; satır eşitlikleri yine zorunludur.
6. Hesaplamalar tam kuruşla `Decimal` kullanır; tolerans veya otomatik
   düzeltme yoktur. Eksik/boş tutar sıfıra çevrilmez. Bilinmeyen bütçe kodları
   PDF’deki müdürlük adlarıyla raporlanır; satırlar sessizce atılmaz veya
   başka müdürlükle birleştirilmez. Yinelenen ekonomik dallar da hatadır.

Her mutabakat tablosunda PDF tutarı, hesaplanan tutar ve fark bulunur. Kaynak
sayfa/satır bilgileri hatalarda, dosya ve CSV SHA-256 özetleri raporda yer
alır. Herhangi bir girdi hatalıysa çıkış kodu sıfırdan farklıdır ve **iki
dosya birlikte istenmiş olsa bile hiçbir XLSX yayımlanmaz**. Kaynak PDF/CSV
düzeltilip yeni çıktı diziniyle yeniden denenmelidir.

Mevcut XLSX dosyasının üzerine yazılmaz. Çıktı dosyası simgesel bağlantıları
reddedilir. Çalışma sayfası geçici dosyaları dahil bütün yazılar `--out`
içindedir; son dosyalar burada hazırlanır. Çıktı yazımında hata olursa o
çalıştırmanın oluşturduğu XLSX dosyaları geri alınır. Çıktı dizini/rapor yolu
yazılamıyorsa veya girdiyle çakışıyorsa hata standart hata akışına yazılır.

## Sınırlar

- Desteklenen kaynak, görev paketindeki sütun adları ve sırası bulunan metin
  PDF’dir. pypdf’nin konumu koruyan `layout` çıkarımı kullanılır; sabit sayfa
  koordinatı veya düzleştirilmiş metin üzerinde tutar arama kullanılmaz.
  Sütun sınırları çok satırlı başlıklar ve veri satırlarındaki ortak
  boşluklarla doğrulanır. Sola/ortaya hizalı başlıklar, sağa hizalı tutarlar,
  ölçeklenmiş sayfalar ve çok sayfalı gider test edilir.
- Her sayfada tablo başlığı gerekir. Başlıkların örtüşmesi, değişik sütun
  düzeni, şifreli/taranmış PDF veya belirsiz hücre sınırı dönüştürmeyi durdurur.
  OCR, raster okuma, ağ üzerinden dönüştürme ve yeni bağımlılık yoktur.
- Giderde `46` kurum hiyerarşisi, üç parçalı tek belediye toplamı, dört
  parçalı müdürlük kodu ve ekonomik satır için dört parçalı fonksiyon/tek
  parçalı finansman bağlamı gerekir. Sayfa geçişinde bağlam korunur.
  Tekrarlanan belediye/müdürlük toplamları otomatik birleştirilmez.
- Kaynak parasal değerler Türkçe, iki ondalıklı biçimde olmalıdır. Eksik
  rakam tahmini, belirsiz sıra değişimi ve eşitlikle kanıtlanamayan sayı
  birleşimi desteklenmez. Negatif veya mevcut içe aktarmanın sayı/satır
  sınırlarını aşan çıktılar reddedilir.
- Gerçek belediye PDF’leri ve gerçek tutarlar kullanılmadı, depoya eklenmedi.
  Gerçek OpenPDF üretiminin bütün yerleşim çeşitleri bu çalışma kapsamında
  doğrulanamaz. Operatör gerçek dosyada ilk çalıştırmanın mutabakat raporunu
  incelemelidir; desteklenmeyen yerleşim veri tahminiyle aşılmaz.

## Doğrulama

Test PDF’lerinin tamamı test sırasında reportlab ile geçici dizinde üretilir;
PDF veya XLSX ikili dosyası depoya eklenmez. Kabul ve hata senaryoları
`tests/test_kesin_hesap_xlsx.py` içindedir. Başlık/sayfa adı uygulamanın gerçek
`template()` çıktısıyla karşılaştırılır; üretilen gider dosyası mevcut
`preview_import` ile geçici PostgreSQL üzerinde doğrulanır.

```sh
python -m pytest -q --require-postgres tests/test_kesin_hesap_xlsx.py
```

Bu komutta `CIVENSA_TEST_POSTGRES_URL` yalnızca yerel, geçici PostgreSQL 16+
veritabanını göstermelidir. Testler canlı veritabanına bağlanmaz. Ek olarak,
CLI çalışma denetimi uygulama/veritabanı modülü yüklemeyi, ağ bağlantısını ve
`--out` dışına dosya açarak yazmayı yasaklayarak çalıştırılır.

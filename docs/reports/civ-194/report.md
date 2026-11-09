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
`--year 2026` kullanılır. Her iki PDF’deki **Başlangıç Tarihi** ve **Bitiş
Tarihi** zorunludur; ikisinin yılı da `--year` ile eşleşmelidir. Başlangıç
bitişten sonra olamaz, tekrar edilen tarihler sayfalar arasında değişemez.
Gelirde **Dönemi** de zorunludur ve aynı yıla ait olmalıdır. Gelir başlıklarında
bulunan önceki/hesap/sonraki yıl etiketleri ayrıca ilgili sütuna göre doğrulanır.
Yıl başlıkta tekrar yazılmamışsa doğrulanmış tarih/dönem kullanılır.

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
   rapora yazılır. Tahmin ve gelecek yıla devreden tutarların birleşimi,
   bağımsız genel toplam sütunuyla doğrulanabilir. Bu alanlar bölünmüşse ve
   genel toplam yoksa dönüşüm durur; doğrulanmamış birleşim kabul edilmez.
5. Gelir genel toplam satırı varsa sekiz parasal sütun düzey 1 satırlarıyla
   karşılaştırılır. Yüzde olan Oran toplanmaz. Toplam satırı yoksa bu denetimin
   yapılamadığı raporda açıkça belirtilir; satır eşitlikleri yine zorunludur.
6. Hesaplamalar tam kuruşla `Decimal` kullanır; tolerans veya otomatik
   düzeltme yoktur. Eksik/boş tutar sıfıra çevrilmez. Bilinmeyen bütçe kodları
   PDF’deki müdürlük adlarıyla raporlanır; satırlar sessizce atılmaz veya
   başka müdürlükle birleştirilmez. Yinelenen ekonomik dallar da hatadır.
   Her gelir alt kodu, dosyada tutarları ve eşitlikleri doğrulanmış düzey 1
   üst satırına sahip olmalıdır; üst satırın dosyadaki sırası önemli değildir.
   Bilinmeyen üst kod, üst satır yokluğu ve genel toplam bulunmaması halinde
   bile alt gelirlerin sessizce atılması engellenir.

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
  boşluklarla **her sayfada yeniden** doğrulanır. Sola/ortaya hizalı başlıklar,
  sağa hizalı tutarlar, ölçeklenmiş/kaymış sayfalar ve çok sayfalı gider test edilir.
- Başlık bloğu, Kurum sözcüğünden önce başlayan tutar başlıkları dahil bütün
  satırları kapsar. Dört satırlı başlık, `Finan / sal Kodu`, `TL` birimi,
  `Aktarma Suratiyle`/`Aktarma Suretiyle`/yalnız `Eklenen (+)`, `Tahsilattan
  Red ve İadeler` ve `Gelirin Kodu` olmadan `I II III IV V` desteklenir.
  Belgelenen varyantlar dışında başlık eşlemesi tahmin edilmez; eksik,
  bilinmeyen ve yinelenen sütunlar reddedilir.
- Her sayfada tablo başlığı gerekir. Başlıkların örtüşmesi, değişik sütun
  düzeni, şifreli/taranmış PDF veya belirsiz hücre sınırı dönüştürmeyi durdurur.
  OCR, raster okuma, ağ üzerinden dönüştürme ve yeni bağımlılık yoktur.
- Giderde `46` kurum hiyerarşisi, üç parçalı tek belediye toplamı, dört
  parçalı müdürlük kodu ve ekonomik satır için dört parçalı fonksiyon/tek
  parçalı finansman bağlamı gerekir. Sayfa geçişinde bağlam korunur.
  Boşluk veya nokta ayracı, sayfanın ilk veri satırı dahil desteklenir.
  Tekrarlanan belediye/müdürlük toplamları otomatik birleştirilmez.
- Gelirde fiziksel satırlar açıklama başlangıcına göre mantıksal satırlara
  toplanır. Kodun `0 / 1` olarak iki satıra bölünmesi, yalnız aynı alt sütun
  konumu korunuyorsa `01` olarak okunur. Tutarın tam kısmından sonraki
  `,dd` veya `,d` eki aynı tutar sütununda birleştirilir; eksik rakam eklenmez.
  Birleşim satır eşitliği veya bağımsız genel toplamla kanıtlanmalıdır.
- Kaynak parasal değerler Türkçe, iki ondalıklı biçimde olmalıdır. Eksik
  rakam tahmini, belirsiz sıra değişimi ve bağımsız olarak kanıtlanamayan sayı
  birleşimi desteklenmez. Negatif veya mevcut içe aktarmanın sayı/satır
  sınırlarını aşan çıktılar reddedilir.
- Gerçek belediye PDF’leri ve gerçek tutarlar kullanılmadı, depoya eklenmedi.
  Gerçek OpenPDF üretiminin bütün yerleşim çeşitleri bu çalışma kapsamında
  doğrulanamaz. Operatör gerçek dosyada ilk çalıştırmanın mutabakat raporunu
  incelemelidir; desteklenmeyen yerleşim veri tahminiyle aşılmaz.
  Lead’in yorumunda verdiği yedi yerleşim farkı sentetik olarak yeniden
  üretilmiştir. Gerçek dosyaların yerel tekrar koşusu lead tarafından yapılır;
  gerçek verinin mutabakatının geçtiği bu çalışma adına iddia edilmez.

## Doğrulama

Test PDF’lerinin tamamı test sırasında reportlab ile geçici dizinde üretilir;
PDF veya XLSX ikili dosyası depoya eklenmez. Kabul ve hata senaryoları
`tests/test_kesin_hesap_xlsx.py` içindedir. Başlık/sayfa adı uygulamanın gerçek
`template()` çıktısıyla karşılaştırılır; üretilen gider dosyası mevcut
`preview_import` ile geçici PostgreSQL üzerinde doğrulanır.

Lead’in 1–7 maddeleri için adlandırılmış regresyon testleri; eksik/yanlış/
tutarsız tarih, bilinmeyen başlık, doğrulanamayan tahmin/devreden birleşimi,
yetim/bilinmeyen gelir üst kodu, sonradan gelen geçerli üst satır ve noktalı
kodla başlayan devam sayfası senaryolarını da kapsar. Yeni yerleşimde
mutabakat tablolarının tüm farklarının `0,00` olduğu; kasıtlı farkta iki XLSX’in
de engellendiği doğrulanır.

```sh
python -m pytest -q --require-postgres tests/test_kesin_hesap_xlsx.py
```

Bu komutta `CIVENSA_TEST_POSTGRES_URL` yalnızca yerel, geçici PostgreSQL 16+
veritabanını göstermelidir. Testler canlı veritabanına bağlanmaz. Ek olarak,
CLI çalışma denetimi uygulama/veritabanı modülü yüklemeyi, ağ bağlantısını ve
`--out` dışına dosya açarak yazmayı yasaklayarak çalıştırılır.

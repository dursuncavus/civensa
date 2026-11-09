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

Gelirde her gelir düzey 1 kod için tek satır üretilir; alt düzeyler tekrar
toplanmaz. Aşağıdaki belgelenmiş plan kesintisi istisnası ayrıca raporlanır.

| XLSX sütunu | PDF kaynağı |
| --- | --- |
| Ekonomik Kod | Gelirin Kodu, düzey 1 |
| Bütçe Tahmini | Bütçe ile Tahmin Edilen |
| Tahsilat (Gerçekleşme) | Hesap Yılı Tahsilatı (brüt) |
| Red ve İadeler | Red ve İadeler |
| Sapma Açıklaması | Boş |

Net tahsilat, brüt tahsilat yerine aktarılmaz; mevcut uygulama neti tahsilattan
red ve iadeyi düşerek hesaplar.

**Negatif plan kesintisi:** `09`, açıklaması `Red ve İadeler (-)` olan düzey 1
satırda bütçe tahmini negatif, diğer yedi parasal alanın tamamı açıkça sıfırsa
bu satır planlanan gelir kesintisidir. `-250,25`, `- 250,25` ve eksi işaretinden
sonra birden çok boşluk aynı negatif tutar olarak okunur; rakamların arasındaki
boşluklar veya başka işaret dizilimleri kabul edilmez. Satırın negatif tutarı
sekiz sütunluk kaynak mutabakatına aynen katılır; bağımsız PDF genel toplamı
zorunludur. Bir kuruş fark bile dönüşümü durdurur.

Mevcut uygulama negatif bütçe tahminini kabul etmediğinden bu kesinti için XLSX
satırı üretilmez. XLSX **brüt gelir tahminlerini** içerir; PDF'nin kesinti sonrası
net bütçe tahminiyle aynı toplamı içermez. Raporda kaynak sayfa/satır, kesinti
tutarı ve `XLSX brüt tahmin + negatif plan kesintisi = PDF net tahmini` köprüsü
ayrı mutabakatla gösterilir. Kesinti pozitif gelire çevrilmez, diğer kodlara
dağıtılmaz veya gerçekleşen `Red ve İadeler` alanına taşınmaz. Tahsilat ve
gerçekleşen iadeler değişmeden aktarılır. Net bütçe tahminini uygulamada da
temsil etmek ayrı bir `app/` değişikliği gerektirir; bu görevde yapılmaz.
Başka kod/açıklamadaki negatif tahmin, boş veya sıfır dışı ek parasal alan,
eksik genel toplam ve yinelenen kod hâlâ hatadır.

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
   Lead’in belgelediği kesik **TOPLAM altbilgisi** dar bir istisnadır: etiket
   satırında tam `Red ve İadeler` ve `Oran`, aynı satırda veya en fazla 6 punto
   aşağıda diğer yedi hücre bulunabilir. Sütunlar veri satırlarından belirlenir;
   bu altbilgi sütun geometrisine veya gelir verisine katılmaz. pypdf metin
   konumları ayrıca kontrol edilir; hücre eksikliği/yinelenmesi, belirsiz sütun,
   yabancı altbilgi metni ve daha uzak tutarlar reddedilir. Ardından gelen
   belgelenmiş imza bloğu gelir satırına eklenmez.

   Her kontrol hücresinde tam sayı kısmı tamamen basılmış olmalıdır. Düzey 1
   toplamı Türkçe biçimlenir; PDF’deki tam sayı kısmı aynı olmalı ve yazılı
   ondalıklar bu gösterimin öneki olmalıdır. Örneğin sentetik `11.223.333`
   ve `11.223.333,5`, hesaplanan `11.223.333,56` için geçerlidir; `11.223`
   tam sayı kısmını tamamlamadığı için geçersizdir. Tam basılan tutarlarda
   kuruş eşitliği, tam basılan yüzdede `net tahsilat / bütçe tahmini × 100`
   hesabının iki ondalığa yuvarlanmış değeri aranır. Pozitif toplam tahmin
   yoksa yüzde doğrulanamaz ve dönüşüm durur. Bir kuruş veya tek basılı rakam
   farkı sayfa/sütun belirtilerek hatadır; hiçbir eksik hane tamamlanmaz.

   Rapor bu denetimi **TOPLAM önek kontrolü** olarak ayrı gösterir: basılı
   önek, hesaplanan düzey 1 toplamı ve kontrol sonucu yer alır. Basılmayan
   ondalıklar için sıfır fark veya tam bağımsız mutabakat iddia edilmez.
   TOPLAM metninden hiçbir tutar XLSX’e yazılmaz. Veri satırlarının tutar,
   satır eşitliği ve tekil konum denetimleri korunur. Tahmin/devreden kaynak
   birleşimi iki ondalıkla tamamlanmamışsa, eksik TOPLAM ondalığı ona kanıt
   sayılamaz; bu durum yine hatadır. Negatif plan kesintisi kaynak toplamında
   eksi kalır; brüt/net köprüsü bu durumda hesaplanan net olarak etiketlenir.
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
  Sütun sınırları yalnız tutar taşıyan veri satırlarındaki boşluklardan
  **her sayfada yeniden** çıkarılır. Çok satırlı başlıkların sözcükleri,
  aynı başlangıç konumunda olmaları gerekmeden, sütun bantlarıyla çoğunluk
  örtüşmesine göre atanır. Başlık boşlukları veri boşluklarıyla ortak olmak
  zorunda değildir. Sola/ortaya hizalı başlıklar,
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
  Kod biçimine benzeyen başlık tarihleri (`01.01.2026` gibi) veri başlangıcı
  sayılmaz; başlangıç için tutar taşıyan kayıt aranır. Başlık çözümlemesi
  başarısız olduğunda aday blok satır numaraları ve boşluklarıyla rapora yazılır.
  Başlığın önündeki tek başına kısa form/sayfa numarası (`11` gibi) başlık
  etiketi sayılmaz. Yalnız başlık bloğunun başındaki 1–3 basamaklı satırlar
  ayıklanır; dört basamaklı mali yıl etiketleri ve başlığın içindeki parçalar
  korunur. `Finan / sal / Kodu` ve iki aktarma sütununa yayılan `Aktarma
  Suratiyle` başlığı bu düzenle birlikte test edilir.
  Dar istisna: giderin yalnız son sayfası, önceki doğrulanmış sayfanın tam
  başlığını aynı metin/sırayla tekrar edip ardından yalnız iki sütunlu
  `Düzenleyen / Muhasebe Yetkilisi`, iki adet `Adı Soyadı :`, `Tarih :`,
  `İmza :` satırlarını içeriyorsa atlanır ve sayfa numarası rapora yazılır.
  Standart `Sayfa N` altbilgisi dışında ek metin, doldurulmuş imza alanı,
  tutar veya kod kabul edilmez. Başlıksız, yalnız başlıklı, değişmiş başlıklı,
  eksik imzalı veya arada kalan verisiz sayfa yine dönüşümü durdurur.
  Kapanış sayfasındaki tarih bilgileri de belge genelindeki denetime katılır.
- Giderde `46` kurum hiyerarşisi, üç parçalı tek belediye toplamı, dört
  parçalı müdürlük kodu ve ekonomik satır için dört parçalı fonksiyon/tek
  parçalı finansman bağlamı gerekir. Sayfa geçişinde bağlam korunur.
  Boşluk veya nokta ayracı, sayfanın ilk veri satırı dahil desteklenir.
  Tekrarlanan belediye/müdürlük toplamları otomatik birleştirilmez.
- Gelirde fiziksel satırlar açıklama başlangıcına göre mantıksal satırlara
  toplanır. Kodun `0 / 1` olarak iki satıra bölünmesi, yalnız aynı alt sütun
  konumu korunuyorsa `01` olarak okunur. İlk parça I sütununda bulunmalıdır;
  II veya sonraki sütundaki parçalar I düzeyi olarak yorumlanmaz. Tutarın tam kısmından sonraki
  `,dd` veya `,d` eki aynı tutar sütununda birleştirilir; eksik rakam eklenmez.
  Birleşim satır eşitliği veya bağımsız genel toplamla kanıtlanmalıdır.
  Ondalık devam satırları, sütun boşluğu hesabı ve hücre doğrulamasından
  **önce** önceki kayda bağlanır ve geometri hesabına katılmaz. Önceki sayı
  tam kısmıysa yalnız `,dd`/`,d`; önceki parça `,d` ile bitiyorsa tek son
  basamak eklenebilir. Parçaların yatay sırası ve geçici sütun bantları tek
  bir eşleme vermelidir; belirsiz/sahipsiz parçalar reddedilir. Ayrı konumdaki
  `0 / 1` kod parçaları korunur. Ham tutar parçaları raporda izlenebilir.
  Kod tutar satırının üzerinde ve altında iki haneye ayrılmışsa, üstteki
  yalnız 1–2 basamaklı parça hemen sonraki tutar kaydının boş kod alanına
  özgün yatay konumuyla bağlanır. İlk kayıt üstündeki kod başlığa katılmaz;
  sonraki kayıt üstündeki kod önceki kayda eklenmez. Özgün satır numaraları
  korunur ve bağlama raporlanır. I düzeyi, iki hane ve iki parçanın aynı alt
  sütunda bulunması yine doğrulanır; iki kayıt arasında belirsiz kalan kod
  kabul edilmez. Araya giren yalnız kod hanesi satırı, etkin tutar kaydını
  bitirmez: iki satır sonra gelen ondalık eki aynı sütunda tekil eşlenmeli,
  desteklenen tutar biçimini tamamlamalı ve mevcut satır/genel toplam
  eşitlikleriyle doğrulanmalıdır. Eksik rakam veya başka kayıttan tutar alınmaz.
  Tutar içermeyen açıklama devam satırları açıklama alanına eklenir; metin
  tutar sütunlarının üzerine uzasa da sütun boşluğu hesabına katılmaz.
  Açıklama sütununda başlamayan sahipsiz metin tutar olarak tahmin edilmez.
- Bölünmemiş parasal değerler Türkçe, iki ondalıklı biçimde olmalıdır. Eksik
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

Lead’in `46617e4` üzerindeki yerel tekrar koşusundan gelen iki ek yerleşim
de testlerde yeniden üretilmiştir: veri gibi görünen başlık tarihiyle birlikte
dört satırlı ortalanmış başlık ve tutar alanlarına taşan, yalnız metin içeren
hesap adı devamı. Bu senaryolar eski commit’te başarısızdır. Yeni ayrıştırıcıda
başlıklar sütun bantlarına atanır; açıklama devamı korunur ve aynı dosyada
kasıtlı tutar farkı varsa iki XLSX de engellenir.

Lead’in b77cac8 tekrar koşusunda belirlediği iki kesin neden için ek regresyonlar
vardır: başlığın üzerinde Kurum Kodu hizasında duran yalın `11` ve dar,
yan yana tutar sütunlarında `tam kısım / ,dd` ile `…,d / d` biçimindeki
ondalık devamları. Bu altı test eski commit’te başarısızdı; yeni akışta geçer.
Yanlış son basamak mutabakat hatasıdır; eksik ek, önünde `,d` bulunmayan
tek basamak ve yanlış dört basamaklı yıl kanıtı kabul edilmez.

Lead’in `3e37776` tekrar koşusundaki iki engel için altı yeni regresyon önce
aynı commit üzerinde başarısız oldu: iki başlık hizasıyla imza kapanış sayfası
ve bitişik/ayrık/çok boşluklu/bölünmüş negatif plan kesintisi. Düzeltme sonrası
geçerler. Diğer verisiz sayfalar, değişmiş başlık/tarih, eksik imza, fazladan
metin/kod/tutar, desteklenmeyen negatif satır, bozuk işaret, eksik genel toplam
ve bir kuruşluk fark için engelleyici testler vardır. Üretilen gelir XLSX’i de
mevcut `preview_import` ile geçici PostgreSQL üzerinde doğrulanır. Gerçek
PDF’lerde çıkış kodunun sıfır olduğunun doğrulaması lead’in yerel tekrar
koşusuna bırakılır; gerçek dosyalar bu çalışmada kullanılmadı.

Lead’in `8f4d2ae` yerel tekrar koşusunda bildirdiği `üst kod hanesi / tutarlar /
alt kod hanesi / ondalık ekleri` düzeni de sentetik PDF’lerde yeniden üretilir.
İlk ve sonraki kayıtlar, sola/ortaya hizalı başlıklar, hem `,dd` hem tek son
basamak ve kodu dikey bölünmüş fakat tutarları bölünmemiş komşu kayıt test edilir.
İlk iki regresyon düzeltmeden önce başarısızdı. Yanlış/eksik/kaymış ondalık,
eksik/ek/farklı sütundaki kod hanesi, araya giren yabancı metin ve iki kayıt
arasındaki belirsiz kod dönüşümü durdurur; iki XLSX birlikte engellenir.

`issuecomment-6741296912` için sentetik TOPLAM etiket satırında iki tam hücre,
4,7 punto aşağıda devamı PDF’de hiç bulunmayan yedi kesik hücre ve ardından
imza bloğu üretilir. Başarı regresyonu `146df9f` üzerinde başarısızdı. Tam sayı,
basılı ondalık, tam iade ve yüzde farkı; kısmi tam sayı; boş hücre; 6 puntoyu
aşan uzaklık; ek metin ve veri satırının eksik ondalığı dönüşümü durdurur.
Tam 6 punto, tam tutarlı altbilgi, bütün haneleri açıkça basılmış kaynak
birleşimi ve ayrık eksili plan kesintisiyle birlikte kullanım da test edilir.
Lead’in sonraki konum denetimi için aynı fixture’ın sütun başlığında ayrı bir
`Toplam` metin nesnesi de vardır. Etiket adayı bütün sayfadaki sözcük sayısıyla
seçilmez: yalnız ayrıştırılmış dokuz altbilgi hücresini, metinlerini ve
konumlarını eşleyen aday kabul edilir. Böylece başlıktaki `Toplam` dışarıda
kalır; sıfır veya birden çok uygun altbilgi etiketi yine hatadır. İki tam
hücrenin etiket satırında, diğerlerinin en fazla 6 punto altında bulunması
ayrıca denetlenir.

`issuecomment-6742814796` için `/Rotate` metaverisi de uygulanır. Ziyaretçi
metin matrisi ve CTM ile bulunan ham nokta, mediabox başlangıcı çıkarıldıktan
sonra görüntülenen sayfanın sol-alt koordinat sistemine dönüştürülür. `u=x−sol`,
`v=y−alt`, genişlik `W`, yükseklik `H` için dönüşümler sırasıyla
`0: (u,v)`, `90: (v,W−u)`, `180: (W−u,H−v)`, `270: (H−v,u)` olur.
Başka açı kabul edilmez; sayfa numaralı hata verilir. Böylece sağ/sol ve
en fazla 6 punto aşağıda olma denetimleri ham eksenlerde yapılmaz.

pypdf yerleşim kipi `/Rotate` uygulamadığından aynı dönüşüm yerleşim çıkarımı
için bellekteki bağımsız sayfa kopyasının içeriğine uygulanır. Ziyaretçi ise
orijinal sayfadan okunup aynı görüntüleme uzayına taşınır. Kaynak PDF üzerine
yazılmaz. Dokuz hücreyle tekil etiket eşleşmesi, tam sayı/ondalık öneki, tam
iade/yüzde ve boş hücre denetimleri değişmez.

Döndürülmemiş fixture korunur; aynı yatay içerik portre mediabox ve `/Rotate 90`
ile de üretilir. Başlıktaki ayrı `Toplam`, kesik TOPLAM altbilgisi ve imza bloğu
vardır. 180/270 derece, mediabox başlangıç kayması, örnek eksen dönüşümü ve
desteklenmeyen açılar da test edilir. Üç dönen başarı senaryosu eski kodda
başarısızdı. 90 derece dönmüş sayfada yanlış basılı hane, boş hücre, eksik veri
ondalığı ve 6 puntoyu aşan aralık hâlâ iki XLSX’i de engeller.

```sh
python -m pytest -q --require-postgres tests/test_kesin_hesap_xlsx.py
```

Bu komutta `CIVENSA_TEST_POSTGRES_URL` yalnızca yerel, geçici PostgreSQL 16+
veritabanını göstermelidir. Testler canlı veritabanına bağlanmaz. Ek olarak,
CLI çalışma denetimi uygulama/veritabanı modülü yüklemeyi, ağ bağlantısını ve
`--out` dışına dosya açarak yazmayı yasaklayarak çalıştırılır.

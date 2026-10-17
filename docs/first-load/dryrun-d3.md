# 2027 PP ilk yükleme — kaynak kontrol listesi

**Provada çıkarıldı — nihai kitapta düzeltilmeli: T195, kitap s.243; başlık: Ekonomik Ad &#124; Ekonomik Ad &#124; 2025 Bütçe &#124; 2025 Haziran Sonu Harcama &#124; 2025 Yıl Sonu Harcama &#124; 2026 Bütçe &#124; 2027 Tahmin &#124; 2028 Tahmin.**

Gönderime hazır: **5/33** (yalnızca bu prova).

Kaynak: `pp2027_print_d3.idml`; SHA256: `999a43b2c07074191a1e47622c544b9a53813f23d3bb6518e63b29979ca384cb`.

Doğrulama: 482 SOURCE mesajı, 0 SYSTEM mesajı; 0 saklama aktarım sorunu; 22 engelleyici olmayan uyarı.

Aynı kök nedenden üreyen mesajlar müdürlük listesinde tek kontrol maddesinde toplanır. Hazır = gerçek paket uygulandı ve validate_department hata listesi boş. Çıkarılan tablo ile ek üyelik/açıklama sorunları ayrıca nihai kitapta kontrol edilmelidir.

## Çalıştırma

```sh
# CIVENSA_TEST_POSTGRES_URL: yerel, disposable PostgreSQL 16+; CREATE DATABASE yetkisi.
python scripts/first_load_dryrun.py tests/fixtures/first_load/source/pp2027_print_d3.idml --exclude-source-table 195 --out docs/first-load/dryrun-d3.md
```

CIV-041 ekonomik tablo düzeltmeleri bu dala alındı. PR #43 önce birleşmelidir; PR #42 tabanı feature/authorization-workflow-phase5 olarak kalır. Yalnızca localhost test URL adresi okunur; her prova ayrı veritabanı oluşturur ve sonunda siler. Dışlama yalnızca prova betiğinde, geçici Word üzerinde yapılır; üretici ve canlı yükleyici tablo çıkarmaz. Dışlamasız kitapta s.243 tablosunu CIV-041 reddeder; kaynakta düzeltmeden nihai yükleme yapılamaz.

Tek kurum, doğrulanmış dönem şablonu, ad eşlemesi ve denetimli/idempotent faaliyet kataloğu gerçek servislerle hazırlanır. Boş, çizgi ve sıfır ayrıdır. Kaynak sayıları değiştirilmedi; doğrulama kuralları gevşetilmedi. Sayfalar IDML hikâyesinin ilk basılı sayfasıdır. T numarası dışlamadan önce üretilen Word tablosunu; r/satır ve c/sütun 1 tabanlı hücreyi gösterir.

Uygulama: 33 müdürlük, 64 kart, 264 gösterge, 288 faaliyet, 1300 ekonomik değer; alt programa bağlanamayan faaliyet: 0. Katalog: 289 faaliyet, 289 sorumluluk, 288 yerel bağlantı.

İçe aktarma hatası: 0; kaynak çelişkisi: 0; çözümlenemeyen müdürlük: 0.

## Yapılan SYSTEM düzeltmeleri

- Para ayrıştırıcısı baştaki ₺ işaretini tanır; ham metin korunur. Veteriner s.107 ekonomik toplamı «₺10.424.938,95» artık 10424938.95 olarak okunur; rastgele ek metin kabul edilmez.
- Kodlu faaliyet açıklamaları sıra yerine faaliyet kodu ve tekil başlık ile eşlenir. Halkla İlişkiler s.192’de 0006 başlığındaki “Faaliyet Adı:” eksikliği sonraki dört açıklamayı kaydırmaz. Kültür s.167’deki yanlış 0008/0009 sağlık başlıkları 0015/0016’ya taşınmaz; kaynakta uygun açıklama olmayan 0015–0017 aşağıda SOURCE olarak kalır.
- CIV-041 ile s.243 ekonomik tablosunun son müdürlüğe yanlış bağlanması önlendi; ret listesi ile üyelik/sayfa kökeni birlikte korunur.

## Bütün hata gruplarının sınıflandırması

| Grup | Sınıf | Doğrulama mesajı |
| --- | --- | ---: |
| Faaliyet finansman toplam farkı | SOURCE | 5 |
| Faaliyet kaynak tutarı doğrulama | SOURCE | 22 |
| Çapraz maliyet/toplam farkı | SOURCE | 52 |
| Ekonomik kaynak/grup doğrulama | SOURCE | 160 |
| Faaliyet açıklaması | SOURCE | 3 |
| Eksik finansman | SOURCE | 87 |
| Gösterge kaynak değeri | SOURCE | 12 |
| Personel/SGK toplam farkı | SOURCE | 1 |
| Program Grubu Belirlenmeli | SOURCE | 140 |

SYSTEM = üretilen Word, ayrıştırıcı, eşleme/ekim, saklama veya doğrulama kaynaklı hata. SOURCE = kitap hücresi/dağılımının kendisi. Tanınmayan hata veya kitap–Word/saklama farkı otomatik SOURCE sayılmaz; SYSTEM olarak raporlanır. Program Grubu Belirlenmeli üç müdürlükte (Fen, İnsan Kaynakları, Yazı) hem Hizmet hem Yönetim kartları varken yalnız tek toplu ekonomik kategori tablosu bulunmasından kaynaklanır. Kategori × program grubu dağılımı kitapta yoktur; grup eksik ekimi değildir. Paylaştırma oranı veya varsayılan grup uydurulmadı.

## Her gruptan kitap → Word → saklanan değer kanıtı

### Faaliyet kaynak tutarı doğrulama — SOURCE

Afet İşleri ve Risk Yönetimi Müdürlüğü

- Kitap hücreleri: s.144 T69 r44c5 = «134.615,00»; s.144 T69 r45c5 = «134.615,00»; s.144 T69 r46c5 = «BOŞ»
- Üretilen Word hücreleri: s.144 T69 r44c5 = «134.615,00»; s.144 T69 r45c5 = «134.615,00»; s.144 T69 r46c5 = «BOŞ»
- Saklanan değerler (ondalık depolama gösterimi): [{"activity": "0015.Kurum Personelinin Afet Eğitim Projesi", "year": 2027, "value_kind": "budget", "funding_type": "total", "amount": "134615.00", "raw_text": "134.615,00", "state": "needs_review", "source_amount": "134615.00"}, {"activity": "0015.Kurum Personelinin Afet Eğitim Projesi", "year": 2027, "value_kind": "budget", "funding_type": "inside", "amount": "134615.00", "raw_text": "134.615,00", "state": "verified", "source_amount": null}, {"activity": "0015.Kurum Personelinin Afet Eğitim Projesi", "year": 2027, "value_kind": "budget", "funding_type": "outside", "amount": null, "state": "kayıt yok (kaynak boş)"}]
- Neden: 0015.Kurum Personelinin Afet Eğitim Projesi: 2027 Bütçe / Toplam kaynak tutarı doğrulanmalı.

### Eksik finansman — SOURCE

Afet İşleri ve Risk Yönetimi Müdürlüğü

- Kitap hücreleri: s.144 T69 r44c5 = «134.615,00»; s.144 T69 r45c5 = «134.615,00»; s.144 T69 r46c5 = «BOŞ»
- Üretilen Word hücreleri: s.144 T69 r44c5 = «134.615,00»; s.144 T69 r45c5 = «134.615,00»; s.144 T69 r46c5 = «BOŞ»
- Saklanan değerler (ondalık depolama gösterimi): [{"activity": "0015.Kurum Personelinin Afet Eğitim Projesi", "year": 2027, "value_kind": "budget", "funding_type": "total", "amount": "134615.00", "raw_text": "134.615,00", "state": "needs_review", "source_amount": "134615.00"}, {"activity": "0015.Kurum Personelinin Afet Eğitim Projesi", "year": 2027, "value_kind": "budget", "funding_type": "inside", "amount": "134615.00", "raw_text": "134.615,00", "state": "verified", "source_amount": null}, {"activity": "0015.Kurum Personelinin Afet Eğitim Projesi", "year": 2027, "value_kind": "budget", "funding_type": "outside", "amount": null, "state": "kayıt yok (kaynak boş)"}]
- Neden: 0015.Kurum Personelinin Afet Eğitim Projesi: 2027 Bütçe finansman bilgisi eksik.

### Faaliyet finansman toplam farkı — SOURCE

Kültür, Sanat ve Sosyal İşler Müdürlüğü

- Kitap hücreleri: s.167 T99 r8c6 = «4.912.500,00»; s.167 T99 r9c6 = «3.825.000,00»; s.167 T99 r10c6 = «0,00»
- Üretilen Word hücreleri: s.167 T99 r8c6 = «4.912.500,00»; s.167 T99 r9c6 = «3.825.000,00»; s.167 T99 r10c6 = «0,00»
- Saklanan değerler (ondalık depolama gösterimi): [{"activity": "0003.İş Birliği ve Ortaklıklar: Öğretim Kurumları, teknoloji transfer ofisleri, sivil toplum kuruluşları ve özel sektörle iş birliği yapmak.", "year": 2028, "value_kind": "forecast", "funding_type": "total", "amount": "4912500.00", "raw_text": "4.912.500,00", "state": "needs_review", "source_amount": "4912500.00"}, {"activity": "0003.İş Birliği ve Ortaklıklar: Öğretim Kurumları, teknoloji transfer ofisleri, sivil toplum kuruluşları ve özel sektörle iş birliği yapmak.", "year": 2028, "value_kind": "forecast", "funding_type": "outside", "amount": "0.00", "raw_text": "0,00", "state": "verified", "source_amount": null}, {"activity": "0003.İş Birliği ve Ortaklıklar: Öğretim Kurumları, teknoloji transfer ofisleri, sivil toplum kuruluşları ve özel sektörle iş birliği yapmak.", "year": 2028, "value_kind": "forecast", "funding_type": "inside", "amount": "3825000.00", "raw_text": "3.825.000,00", "state": "verified", "source_amount": null}]
- Neden: 0003.İş Birliği ve Ortaklıklar: Öğretim Kurumları, teknoloji transfer ofisleri, sivil toplum kuruluşları ve özel sektörle iş birliği yapmak.: 2028 toplamı bütçe içi + dışı ile eşit değil. Kaynak: Toplam = «4.912.500,00»; Bütçe İçi = «3.825.000,00»; Bütçe Dışı = «0,00»

### Gösterge kaynak değeri — SOURCE

Park ve Bahçeler Müdürlüğü

- Kitap hücreleri: s.125 T45 r11c4 = «132,915»
- Üretilen Word hücreleri: s.125 T45 r11c4 = «132,915»
- Saklanan değerler (ondalık depolama gösterimi): [{"year": 2025, "value_kind": "actual", "value": null, "raw_text": "132,915", "state": "needs_review"}]
- Neden: SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı: 2025 Gerçekleşme: kaynak değeri doğrulanmalı (132,915).

### Faaliyet açıklaması — SOURCE

Kültür, Sanat ve Sosyal İşler Müdürlüğü

- Kitap hücreleri: s.167 T99 r44c1 = «0015.Örgün Eğitime Destek ve Sınavlara Hazırlık Kursları: Dezavantajlı bölgelerde yaşayan öğrenciler için örgün eğitimlerine destek ve sınavlara hazırlık kursları düzenlemek.»; s.167 T99 r58c1 = «Faaliyetlere İlişkin Açıklamalar»; s.167 T99 r90c1 = «Yaşlı, engelli, yatağa bağımlı, hareket kısıtlılığı bulunan ve sağlık kuruluşlarına kendi imkânlarıyla ulaşmakta güçlük çeken vatandaşların sağlık hizmetlerine erişiminin kolaylaştırılması amacıyla hasta nakil hizmetlerinin etkin, güvenli ve kesintisiz şekilde yürütülmesi hedeflenmektedir. Bu kapsamda hasta nakil ambulansları ile vatandaşların sağlık kuruluşlarına nakilleri sağlanacak; hizmet kapasitesinin artırılması amacıyla gerekli personel, araç, tıbbi cihaz, ekipman ve diğer ihtiyaçlara yönelik planlama yapılacaktır. Ambulansların ve tıbbi cihazların bakım, onarım ve kontrolleri düzenli olarak gerçekleştirilerek hizmet sürekliliği sağlanacak, ilgili sağlık kurum ve kuruluşlarıyla koordinasyon içerisinde hasta nakil hizmetlerinin erişilebilirliği ve hizmet kalitesi artırılacaktır.»
- Üretilen Word hücreleri: s.167 T99 r44c1 = «0015.Örgün Eğitime Destek ve Sınavlara Hazırlık Kursları: Dezavantajlı bölgelerde yaşayan öğrenciler için örgün eğitimlerine destek ve sınavlara hazırlık kursları düzenlemek.»; s.167 T99 r58c1 = «Faaliyetlere İlişkin Açıklamalar»; s.167 T99 r90c1 = «Yaşlı, engelli, yatağa bağımlı, hareket kısıtlılığı bulunan ve sağlık kuruluşlarına kendi imkânlarıyla ulaşmakta güçlük çeken vatandaşların sağlık hizmetlerine erişiminin kolaylaştırılması amacıyla hasta nakil hizmetlerinin etkin, güvenli ve kesintisiz şekilde yürütülmesi hedeflenmektedir. Bu kapsamda hasta nakil ambulansları ile vatandaşların sağlık kuruluşlarına nakilleri sağlanacak; hizmet kapasitesinin artırılması amacıyla gerekli personel, araç, tıbbi cihaz, ekipman ve diğer ihtiyaçlara yönelik planlama yapılacaktır. Ambulansların ve tıbbi cihazların bakım, onarım ve kontrolleri düzenli olarak gerçekleştirilerek hizmet sürekliliği sağlanacak, ilgili sağlık kurum ve kuruluşlarıyla koordinasyon içerisinde hasta nakil hizmetlerinin erişilebilirliği ve hizmet kalitesi artırılacaktır.»
- Saklanan değerler (ondalık depolama gösterimi): [{"activity": "0015.Örgün Eğitime Destek ve Sınavlara Hazırlık Kursları: Dezavantajlı bölgelerde yaşayan öğrenciler için örgün eğitimlerine destek ve sınavlara hazırlık kursları düzenlemek.", "explanation": ""}]
- Neden: 0015.Örgün Eğitime Destek ve Sınavlara Hazırlık Kursları: Dezavantajlı bölgelerde yaşayan öğrenciler için örgün eğitimlerine destek ve sınavlara hazırlık kursları düzenlemek.: faaliyet açıklaması eksik. Bu kod için tekil ve uygun açıklama başlığı/metni kaynakta yok; başka faaliyetin metni taşınmadı.

### Ekonomik kaynak/grup doğrulama — SOURCE

Afet İşleri ve Risk Yönetimi Müdürlüğü

- Kitap hücreleri: s.144 T70 r2c3 = «5.091.250,40»; s.144 T70 r3c3 = «303.363,06»; s.144 T70 r4c3 = «1.159.908,75»; s.144 T70 r5c3 = «5.091.250,40»; s.144 T70 r6c3 = «0,00»; s.144 T70 r7c3 = «5.091.250,40»
- Üretilen Word hücreleri: s.144 T70 r2c3 = «5.091.250,40»; s.144 T70 r3c3 = «303.363,06»; s.144 T70 r4c3 = «1.159.908,75»; s.144 T70 r5c3 = «5.091.250,40»; s.144 T70 r6c3 = «0,00»; s.144 T70 r7c3 = «5.091.250,40»
- Saklanan değerler (ondalık depolama gösterimi): [{"year": 2026, "value_kind": "midyear_spend", "category": "goods_services", "funding_type": "outside", "amount": "0.00", "raw_text": "0,00", "state": "needs_review", "program_group": "service"}]
- Neden: Tablo 70, 2026 Haziran Sonu Harcama: Bütçe İçi Toplam 5.091.250,40 TL, kategori satırlarının toplamı 6.554.522,21 TL; fark -1.463.271,81 TL. Kaynak tabloyu kontrol edin.

### Program Grubu Belirlenmeli — SOURCE

Fen İşleri Müdürlüğü

- Kitap hücreleri: s.118 T38 r2c2 = «46.388.000,00»; s.118 T38 r3c2 = «2.300.000,00»; s.118 T38 r4c2 = «442.490.000,00»; s.118 T38 r5c2 = «4.600.000,00»; s.118 T38 r6c2 = «453.562.000,00»; s.118 T38 r7c2 = «950.000.000,00»; s.118 T38 r8c2 = «0,00»; s.118 T38 r9c2 = «950.000.000,00»; s.115 T31 r2c2 = «Yönetim ve Destek Programı»; s.116 T33 r2c2 = «Kent İçi Ulaşım»; s.117 T35 r2c2 = «Kent Güvenliği ve Sağlığı»
- Üretilen Word hücreleri: s.118 T38 r2c2 = «46.388.000,00»; s.118 T38 r3c2 = «2.300.000,00»; s.118 T38 r4c2 = «442.490.000,00»; s.118 T38 r5c2 = «4.600.000,00»; s.118 T38 r6c2 = «453.562.000,00»; s.118 T38 r7c2 = «950.000.000,00»; s.118 T38 r8c2 = «0,00»; s.118 T38 r9c2 = «950.000.000,00»; s.115 T31 r2c2 = «Yönetim ve Destek Programı»; s.116 T33 r2c2 = «Kent İçi Ulaşım»; s.117 T35 r2c2 = «Kent Güvenliği ve Sağlığı»
- Saklanan değerler (ondalık depolama gösterimi): [{"year": 2026, "value_kind": "budget", "category": "current_transfers", "funding_type": "outside", "amount": "0.00", "raw_text": "0,00", "state": "needs_review", "program_group": "unallocated"}]
- Neden: Tablo 38, 2026 Bütçe: Bütçe İçi Toplam 950.000.000,00 TL, kategori satırlarının toplamı 949.340.000,00 TL; fark 660.000,00 TL. Kaynak tabloyu kontrol edin.<br>Tablo 38, 2026 Bütçe: Program grubu dağılımı kaynakta ayrılmamış. Programlar: Yönetim ve Destek Programı; Kent İçi Ulaşım; Kent Güvenliği ve Sağlığı. Tutarları program gruplarına göre doğrulayın. Kaynak tabloyu kontrol edin.

### Çapraz maliyet/toplam farkı — SOURCE

Bilgi İşlem Müdürlüğü

- Kitap hücreleri: s.207 T147 r20c5 = «21.336.000,00»; s.207 T148 r2c4 = «20.346.000,00»; s.207 T148 r3c4 = «990.000,00»; s.207 T148 r4c4 = «236.000.000,00»; s.207 T148 r5c4 = «26.476.848,00»; s.207 T148 r6c4 = «283.812.848,00»; s.207 T148 r7c4 = «0,00»; s.207 T148 r8c4 = «283.812.848,00»; s.207 T147 r2c5 = «53.495.369,00»; s.207 T147 r3c5 = «53.495.369,00»; s.207 T147 r4c5 = «0,00»; s.207 T147 r5c5 = «53.594.369,00»; s.207 T147 r6c5 = «53.594.369,00»; s.207 T147 r7c5 = «0,00»; s.207 T147 r8c5 = «53.495.369,00»; s.207 T147 r9c5 = «53.495.369,00»; s.207 T147 r10c5 = «0,00»; s.207 T147 r11c5 = «53.495.369,00»; s.207 T147 r12c5 = «53.495.369,00»; s.207 T147 r13c5 = «0,00»; s.207 T147 r14c5 = «53.495.369,00»; s.207 T147 r15c5 = «53.495.369,00»; s.207 T147 r16c5 = «0,00»
- Üretilen Word hücreleri: s.207 T147 r20c5 = «21.336.000,00»; s.207 T148 r2c4 = «20.346.000,00»; s.207 T148 r3c4 = «990.000,00»; s.207 T148 r4c4 = «236.000.000,00»; s.207 T148 r5c4 = «26.476.848,00»; s.207 T148 r6c4 = «283.812.848,00»; s.207 T148 r7c4 = «0,00»; s.207 T148 r8c4 = «283.812.848,00»; s.207 T147 r2c5 = «53.495.369,00»; s.207 T147 r3c5 = «53.495.369,00»; s.207 T147 r4c5 = «0,00»; s.207 T147 r5c5 = «53.594.369,00»; s.207 T147 r6c5 = «53.594.369,00»; s.207 T147 r7c5 = «0,00»; s.207 T147 r8c5 = «53.495.369,00»; s.207 T147 r9c5 = «53.495.369,00»; s.207 T147 r10c5 = «0,00»; s.207 T147 r11c5 = «53.495.369,00»; s.207 T147 r12c5 = «53.495.369,00»; s.207 T147 r13c5 = «0,00»; s.207 T147 r14c5 = «53.495.369,00»; s.207 T147 r15c5 = «53.495.369,00»; s.207 T147 r16c5 = «0,00»
- Saklanan değerler (ondalık depolama gösterimi): [{"year": 2027, "activity_total": "267575845.00", "personnel": "21336000.00", "economic_total": "283812848.00", "economic_personnel": "21336000.00"}]
- Neden: 2027: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. Faaliyet toplamı 267.575.845,00; ortak personel/SGK 21.336.000,00; ekonomik kategori toplamı 283.812.848,00; ekonomik personel/SGK 21.336.000,00 TL.

### Personel/SGK toplam farkı — SOURCE

Yazı İşleri Müdürlüğü

- Kitap hücreleri: s.227 T179 r38c6 = «30.875.000,00»; s.227 T180 r2c5 = «27.125.000,00»; s.227 T180 r3c5 = «3.757.000,00»; s.227 T180 r4c5 = «14.073.382,00»; s.227 T180 r5c5 = «2.197.650,00»; s.227 T180 r6c5 = «5.077.400,00»; s.227 T180 r7c5 = «52.223.432,00»; s.227 T180 r8c5 = «0,00»; s.227 T180 r9c5 = «52.223.432,00»
- Üretilen Word hücreleri: s.227 T179 r38c6 = «30.875.000,00»; s.227 T180 r2c5 = «27.125.000,00»; s.227 T180 r3c5 = «3.757.000,00»; s.227 T180 r4c5 = «14.073.382,00»; s.227 T180 r5c5 = «2.197.650,00»; s.227 T180 r6c5 = «5.077.400,00»; s.227 T180 r7c5 = «52.223.432,00»; s.227 T180 r8c5 = «0,00»; s.227 T180 r9c5 = «52.223.432,00»
- Saklanan değerler (ondalık depolama gösterimi): [{"year": 2028, "activity_total": "19452675.00", "personnel": "30875000.00", "economic_total": "52230432.00", "economic_personnel": "30882000.00"}]
- Neden: 2028: ekonomik personel/SGK satırları ortak tablodan farklı. Faaliyet toplamı 19.452.675,00; ortak personel/SGK 30.875.000,00; ekonomik kategori toplamı 52.230.432,00; ekonomik personel/SGK 30.882.000,00 TL.

### SYSTEM düzeltmesinin saklama kanıtı

- Kitap: s.192 T129 r48c1 = «0006.Personel Eğitim ve Yetkinlik Geliştirme Faaliyetleri»; s.192 T129 r49c1 = «Çözüm Masası bünyesinde görev yapan personelin vatandaşlarla etkili iletişim kurma, talep, öneri ve şikâyetleri doğru şekilde karşılama, kayıt altına alma, yönlendirme ve takip etme konularındaki bilgi, beceri ve yetkinliklerinin geliştirilmesi amacıyla eğitim faaliyetleri yürütülmektedir. Bu kapsamda; vatandaş iletişimi, etkili iletişim teknikleri, çözüm odaklı yaklaşım, başvuru ve çağrı yönetimi, dijital sistemlerin etkin kullanımı ile hizmet kalitesinin artırılmasına yönelik eğitim, seminer ve benzeri çalışmaların gerçekleştirilmesi amaçlanmaktadır.»
- Word: s.192 T129 r48c1 = «0006.Personel Eğitim ve Yetkinlik Geliştirme Faaliyetleri»; s.192 T129 r49c1 = «Çözüm Masası bünyesinde görev yapan personelin vatandaşlarla etkili iletişim kurma, talep, öneri ve şikâyetleri doğru şekilde karşılama, kayıt altına alma, yönlendirme ve takip etme konularındaki bilgi, beceri ve yetkinliklerinin geliştirilmesi amacıyla eğitim faaliyetleri yürütülmektedir. Bu kapsamda; vatandaş iletişimi, etkili iletişim teknikleri, çözüm odaklı yaklaşım, başvuru ve çağrı yönetimi, dijital sistemlerin etkin kullanımı ile hizmet kalitesinin artırılmasına yönelik eğitim, seminer ve benzeri çalışmaların gerçekleştirilmesi amaçlanmaktadır.»
- Saklanan Activity.explanation: Çözüm Masası bünyesinde görev yapan personelin vatandaşlarla etkili iletişim kurma, talep, öneri ve şikâyetleri doğru şekilde karşılama, kayıt altına alma, yönlendirme ve takip etme konularındaki bilgi, beceri ve yetkinliklerinin geliştirilmesi amacıyla eğitim faaliyetleri yürütülmektedir. Bu kapsamda; vatandaş iletişimi, etkili iletişim teknikleri, çözüm odaklı yaklaşım, başvuru ve çağrı yönetimi, dijital sistemlerin etkin kullanımı ile hizmet kalitesinin artırılmasına yönelik eğitim, seminer ve benzeri çalışmaların gerçekleştirilmesi amaçlanmaktadır.

- Kitap: s.107 T24 r7c3 = «₺10.424.938,95»
- Word: s.107 T24 r7c3 = «₺10.424.938,95»
- Saklanan EconomicValue.source_context_json.totals.inside: {"year": 2026, "kind": "midyear_spend", "amount": "10424938.95", "raw_text": "₺10.424.938,95", "state": "verified"}

## Pazartesi — müdürlük bazında yalnız SOURCE kontrol listesi

### Afet İşleri ve Risk Yönetimi Müdürlüğü

Gönderime hazır: **Hayır**; 12 SOURCE mesajı / 4 kaynak kontrol maddesi.

- [ ] 0015.Kurum Personelinin Afet Eğitim Projesi: 2027 Bütçe / Toplam kaynak tutarı doğrulanmalı. 0015.Kurum Personelinin Afet Eğitim Projesi: 2027 Bütçe finansman bilgisi eksik. **Hücreler:** s.144 / T69 / sütun 5 / satır 44,45,46
- [ ] 0015.Kurum Personelinin Afet Eğitim Projesi: 2028 Tahmin / Toplam kaynak tutarı doğrulanmalı. 0015.Kurum Personelinin Afet Eğitim Projesi: 2028 Tahmin finansman bilgisi eksik. **Hücreler:** s.144 / T69 / sütun 6 / satır 44,45,46
- [ ] 0015.Kurum Personelinin Afet Eğitim Projesi: 2029 Tahmin / Toplam kaynak tutarı doğrulanmalı. 0015.Kurum Personelinin Afet Eğitim Projesi: 2029 Tahmin finansman bilgisi eksik. **Hücreler:** s.144 / T69 / sütun 7 / satır 44,45,46
- [ ] Tablo 70, 2026 Haziran Sonu Harcama: Bütçe İçi Toplam 5.091.250,40 TL, kategori satırlarının toplamı 6.554.522,21 TL; fark -1.463.271,81 TL. Kaynak tabloyu kontrol edin. **Hücreler:** s.144 / T70 / sütun 3 / satır 2,3,4,5,6,7

### Araştırma ve Geliştirme Müdürlüğü

Gönderime hazır: **Hayır**; 6 SOURCE mesajı / 1 kaynak kontrol maddesi.

- [ ] Tablo 134, 2026 Haziran Sonu Harcama: Bütçe İçi Toplam 832.400,90 TL, kategori satırlarının toplamı 813.893,90 TL; fark 18.507,00 TL. Kaynak tabloyu kontrol edin. **Hücreler:** s.195 / T134 / sütun 3 / satır 2,3,4,5,6,7

### Bilgi İşlem Müdürlüğü

Gönderime hazır: **Hayır**; 6 SOURCE mesajı / 3 kaynak kontrol maddesi.

- [ ] 2027: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. Faaliyet toplamı 267.575.845,00; ortak personel/SGK 21.336.000,00; ekonomik kategori toplamı 283.812.848,00; ekonomik personel/SGK 21.336.000,00 TL. 2027: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. Faaliyet toplamı 267.575.845,00; ortak personel/SGK 21.336.000,00; ekonomik kategori toplamı 283.812.848,00; ekonomik personel/SGK 21.336.000,00 TL. **Hücreler:** s.207 / T147 / sütun 5 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.207 / T148 / sütun 4 / satır 2,3,4,5,6,7,8
- [ ] 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. Faaliyet toplamı 454.155.140,00; ortak personel/SGK 26.670.000,00; ekonomik kategori toplamı 480.825.142,00; ekonomik personel/SGK 26.670.000,00 TL. 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. Faaliyet toplamı 454.155.140,00; ortak personel/SGK 26.670.000,00; ekonomik kategori toplamı 480.825.142,00; ekonomik personel/SGK 26.670.000,00 TL. **Hücreler:** s.207 / T147 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.207 / T148 / sütun 5 / satır 2,3,4,5,6,7,8
- [ ] 2029: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. Faaliyet toplamı 777.302.765,00; ortak personel/SGK 33.337.500,00; ekonomik kategori toplamı 810.640.269,00; ekonomik personel/SGK 33.337.500,00 TL. 2029: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. Faaliyet toplamı 777.302.765,00; ortak personel/SGK 33.337.500,00; ekonomik kategori toplamı 810.640.269,00; ekonomik personel/SGK 33.337.500,00 TL. **Hücreler:** s.207 / T147 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.207 / T148 / sütun 6 / satır 2,3,4,5,6,7,8

### Çevre Koruma ve Kontrol Müdürlüğü

Gönderime hazır: **Hayır**; 6 SOURCE mesajı / 1 kaynak kontrol maddesi.

- [ ] Tablo 78, 2026 Haziran Sonu Harcama: Bütçe İçi Toplam 3.967.964,02 TL, kategori satırlarının toplamı 4.085.221,72 TL; fark -117.257,70 TL. Kaynak tabloyu kontrol edin. **Hücreler:** s.153 / T78 / sütun 3 / satır 2,3,4,5,6,7

### Destek Hizmetleri Müdürlüğü

Gönderime hazır: **Hayır**; 3 SOURCE mesajı / 3 kaynak kontrol maddesi.

- [ ] 0007.İhtiyaç duyulan malzeme, ekipman ve hizmet alımlarının yasalara uygun, şeffaf ve rekabetçi bir şekilde gerçekleştirmek: 2026 Bütçe finansman bilgisi eksik. **Hücreler:** s.218 / T165 / sütun 2 / satır 20,21,22
- [ ] 0007.İhtiyaç duyulan malzeme, ekipman ve hizmet alımlarının yasalara uygun, şeffaf ve rekabetçi bir şekilde gerçekleştirmek: 2026 Haziran Sonu Harcama finansman bilgisi eksik. **Hücreler:** s.218 / T165 / sütun 3 / satır 20,21,22
- [ ] 0007.İhtiyaç duyulan malzeme, ekipman ve hizmet alımlarının yasalara uygun, şeffaf ve rekabetçi bir şekilde gerçekleştirmek: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. **Hücreler:** s.218 / T165 / sütun 4 / satır 20,21,22

### Dış İlişkiler Müdürlüğü

Gönderime hazır: **Hayır**; 9 SOURCE mesajı / 6 kaynak kontrol maddesi.

- [ ] 2027: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. Faaliyet toplamı 4.039.548,00; ortak personel/SGK 1.475.000,00; ekonomik kategori toplamı 6.514.548,00; ekonomik personel/SGK 1.475.000,00 TL. 2027: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. Faaliyet toplamı 4.039.548,00; ortak personel/SGK 1.475.000,00; ekonomik kategori toplamı 6.514.548,00; ekonomik personel/SGK 1.475.000,00 TL. **Hücreler:** s.186 / T119 / sütun 5 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.186 / T120 / sütun 4 / satır 2,3,4,5,6,7,8
- [ ] 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. Faaliyet toplamı 4.570.481,00; ortak personel/SGK 1.843.750,00; ekonomik kategori toplamı 7.414.231,00; ekonomik personel/SGK 1.843.750,00 TL. 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. Faaliyet toplamı 4.570.481,00; ortak personel/SGK 1.843.750,00; ekonomik kategori toplamı 7.414.231,00; ekonomik personel/SGK 1.843.750,00 TL. **Hücreler:** s.186 / T119 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.186 / T120 / sütun 5 / satır 2,3,4,5,6,7,8
- [ ] 2029: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. Faaliyet toplamı 4.605.000,00; ortak personel/SGK 2.304.688,00; ekonomik kategori toplamı 8.009.688,00; ekonomik personel/SGK 2.304.688,00 TL. 2029: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. Faaliyet toplamı 4.605.000,00; ortak personel/SGK 2.304.688,00; ekonomik kategori toplamı 8.009.688,00; ekonomik personel/SGK 2.304.688,00 TL. **Hücreler:** s.186 / T119 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.186 / T120 / sütun 6 / satır 2,3,4,5,6,7,8
- [ ] 0006.Uluslararası kuruluşlar ve belediye ağları ile kurumsal ilişkilerin sürdürülmesi: 2026 Bütçe finansman bilgisi eksik. **Hücreler:** s.186 / T119 / sütun 2 / satır 17,18,19
- [ ] 0006.Uluslararası kuruluşlar ve belediye ağları ile kurumsal ilişkilerin sürdürülmesi: 2026 Haziran Sonu Harcama finansman bilgisi eksik. **Hücreler:** s.186 / T119 / sütun 3 / satır 17,18,19
- [ ] 0006.Uluslararası kuruluşlar ve belediye ağları ile kurumsal ilişkilerin sürdürülmesi: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. **Hücreler:** s.186 / T119 / sütun 4 / satır 17,18,19

### Emlak İstimlak Müdürlüğü

Gönderime hazır: **Hayır**; 16 SOURCE mesajı / 4 kaynak kontrol maddesi.

- [ ] 0005.4734 sayılı yasa kapsamında mal ve/veya hizmet alımı ihale işlemlerinin yapılması: 2027 Bütçe / Toplam kaynak tutarı doğrulanmalı. 0005.4734 sayılı yasa kapsamında mal ve/veya hizmet alımı ihale işlemlerinin yapılması: 2027 Bütçe finansman bilgisi eksik. **Hücreler:** s.112 / T29 / sütun 5 / satır 14,15,16
- [ ] 0005.4734 sayılı yasa kapsamında mal ve/veya hizmet alımı ihale işlemlerinin yapılması: 2028 Tahmin / Toplam kaynak tutarı doğrulanmalı. 0005.4734 sayılı yasa kapsamında mal ve/veya hizmet alımı ihale işlemlerinin yapılması: 2028 Tahmin finansman bilgisi eksik. **Hücreler:** s.112 / T29 / sütun 6 / satır 14,15,16
- [ ] 0005.4734 sayılı yasa kapsamında mal ve/veya hizmet alımı ihale işlemlerinin yapılması: 2029 Tahmin / Toplam kaynak tutarı doğrulanmalı. 0005.4734 sayılı yasa kapsamında mal ve/veya hizmet alımı ihale işlemlerinin yapılması: 2029 Tahmin finansman bilgisi eksik. **Hücreler:** s.112 / T29 / sütun 7 / satır 14,15,16
- [ ] Tablo 30, 2026 Haziran Sonu Harcama: Bütçe İçi Toplam 113.352.771,64 TL, kategori satırlarının toplamı 113.787.163,62 TL; fark -434.391,98 TL. Kaynak tabloyu kontrol edin. **Hücreler:** s.112 / T30 / sütun 3 / satır 2,3,4,5,6,7,8,9

### Etüd Proje Müdürlüğü

Gönderime hazır: **Hayır**; 1 SOURCE mesajı / 1 kaynak kontrol maddesi.

- [ ] 0010.Tüm bölgede, Sigara İçme Alanı talep ve başvurularının değerlendirilerek sonuçlandırılması (102 adet): 2028 Tahmin finansman bilgisi eksik. **Hücreler:** s.133 / T55 / sütun 6 / satır 29,30,31

### Fen İşleri Müdürlüğü

Gönderime hazır: **Hayır**; 54 SOURCE mesajı / 7 kaynak kontrol maddesi.

- [ ] 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. Faaliyet toplamı 2.021.870.002,00; ortak personel/SGK 59.125.000,00; ekonomik kategori toplamı 2.223.048.637,00; ekonomik personel/SGK 59.125.000,00 TL. 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. Faaliyet toplamı 2.021.870.002,00; ortak personel/SGK 59.125.000,00; ekonomik kategori toplamı 2.223.048.637,00; ekonomik personel/SGK 59.125.000,00 TL. **Hücreler:** s.118 / T37 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,32; s.118 / T38 / sütun 5 / satır 2,3,4,5,6,7,8,9
- [ ] 2029: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. Faaliyet toplamı 2.493.022.422,00; ortak personel/SGK 73.906.250,00; ekonomik kategori toplamı 2.666.810.796,00; ekonomik personel/SGK 73.906.250,00 TL. 2029: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. Faaliyet toplamı 2.493.022.422,00; ortak personel/SGK 73.906.250,00; ekonomik kategori toplamı 2.666.810.796,00; ekonomik personel/SGK 73.906.250,00 TL. **Hücreler:** s.118 / T37 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,32; s.118 / T38 / sütun 6 / satır 2,3,4,5,6,7,8,9
- [ ] Tablo 38, 2026 Bütçe: Bütçe İçi Toplam 950.000.000,00 TL, kategori satırlarının toplamı 949.340.000,00 TL; fark 660.000,00 TL. Kaynak tabloyu kontrol edin.<br>Tablo 38, 2026 Bütçe: Program grubu dağılımı kaynakta ayrılmamış. Programlar: Yönetim ve Destek Programı; Kent İçi Ulaşım; Kent Güvenliği ve Sağlığı. Tutarları program gruplarına göre doğrulayın. Kaynak tabloyu kontrol edin. **Hücreler:** s.118 / T38 / sütun 2 / satır 2,3,4,5,6,7,8,9; s.115 / T31 / sütun 2 / satır 2; s.116 / T33 / sütun 2 / satır 2; s.117 / T35 / sütun 2 / satır 2
- [ ] Tablo 38, 2026 Haziran Sonu Harcama: Program grubu dağılımı kaynakta ayrılmamış. Programlar: Yönetim ve Destek Programı; Kent İçi Ulaşım; Kent Güvenliği ve Sağlığı. Tutarları program gruplarına göre doğrulayın. Kaynak tabloyu kontrol edin. **Hücreler:** s.118 / T38 / sütun 3 / satır 2,3,4,5,6,7,8,9; s.115 / T31 / sütun 2 / satır 2; s.116 / T33 / sütun 2 / satır 2; s.117 / T35 / sütun 2 / satır 2
- [ ] Tablo 38, 2027 Bütçe: Program grubu dağılımı kaynakta ayrılmamış. Programlar: Yönetim ve Destek Programı; Kent İçi Ulaşım; Kent Güvenliği ve Sağlığı. Tutarları program gruplarına göre doğrulayın. Kaynak tabloyu kontrol edin. **Hücreler:** s.118 / T38 / sütun 4 / satır 2,3,4,5,6,7,8,9; s.115 / T31 / sütun 2 / satır 2; s.116 / T33 / sütun 2 / satır 2; s.117 / T35 / sütun 2 / satır 2
- [ ] Tablo 38, 2028 Tahmin: Program grubu dağılımı kaynakta ayrılmamış. Programlar: Yönetim ve Destek Programı; Kent İçi Ulaşım; Kent Güvenliği ve Sağlığı. Tutarları program gruplarına göre doğrulayın. Kaynak tabloyu kontrol edin. **Hücreler:** s.118 / T38 / sütun 5 / satır 2,3,4,5,6,7,8,9; s.115 / T31 / sütun 2 / satır 2; s.116 / T33 / sütun 2 / satır 2; s.117 / T35 / sütun 2 / satır 2
- [ ] Tablo 38, 2029 Tahmin: Program grubu dağılımı kaynakta ayrılmamış. Programlar: Yönetim ve Destek Programı; Kent İçi Ulaşım; Kent Güvenliği ve Sağlığı. Tutarları program gruplarına göre doğrulayın. Kaynak tabloyu kontrol edin. **Hücreler:** s.118 / T38 / sütun 6 / satır 2,3,4,5,6,7,8,9; s.115 / T31 / sütun 2 / satır 2; s.116 / T33 / sütun 2 / satır 2; s.117 / T35 / sütun 2 / satır 2

### Gelirler Müdürlüğü

Gönderime hazır: **Hayır**; 25 SOURCE mesajı / 8 kaynak kontrol maddesi.

- [ ] 2027: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. Faaliyet toplamı 83.400.000,00; ortak personel/SGK 81.910.000,00; ekonomik kategori toplamı 162.322.500,00; ekonomik personel/SGK 81.910.000,00 TL. 2027: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. Faaliyet toplamı 83.400.000,00; ortak personel/SGK 81.910.000,00; ekonomik kategori toplamı 162.322.500,00; ekonomik personel/SGK 81.910.000,00 TL. **Hücreler:** s.234 / T189 / sütun 5 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,50; s.234 / T190 / sütun 4 / satır 2,3,4,5,6,7,8
- [ ] 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. Faaliyet toplamı 104.272.200,00; ortak personel/SGK 102.387.500,00; ekonomik kategori toplamı 204.036.734,00; ekonomik personel/SGK 102.387.500,00 TL. 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. Faaliyet toplamı 104.272.200,00; ortak personel/SGK 102.387.500,00; ekonomik kategori toplamı 204.036.734,00; ekonomik personel/SGK 102.387.500,00 TL. **Hücreler:** s.234 / T189 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,50; s.234 / T190 / sütun 5 / satır 2,3,4,5,6,7,8
- [ ] 2029: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. Faaliyet toplamı 121.674.592,00; ortak personel/SGK 127.984.375,00; ekonomik kategori toplamı 235.437.102,00; ekonomik personel/SGK 127.984.375,00 TL. 2029: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. Faaliyet toplamı 121.674.592,00; ortak personel/SGK 127.984.375,00; ekonomik kategori toplamı 235.437.102,00; ekonomik personel/SGK 127.984.375,00 TL. **Hücreler:** s.234 / T189 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,50; s.234 / T190 / sütun 6 / satır 2,3,4,5,6,7,8
- [ ] Tablo 190, 2026 Bütçe: Bütçe İçi Toplam 130.725.430,00 TL, kategori satırlarının toplamı 132.225.430,00 TL; fark -1.500.000,00 TL. Kaynak tabloyu kontrol edin. **Hücreler:** s.234 / T190 / sütun 2 / satır 2,3,4,5,6,7,8
- [ ] Tablo 190, 2026 Haziran Sonu Harcama: Bütçe İçi Toplam 52.551.283,30 TL, kategori satırlarının toplamı 52.551.283,13 TL; fark 0,17 TL. Kaynak tabloyu kontrol edin. **Hücreler:** s.234 / T190 / sütun 3 / satır 2,3,4,5,6,7,8
- [ ] 0015.Vergi beyannameleri, müşavirlik, eğitim vb. çeşitli ödemeleri zamanında eksiksiz ve tam olarak yürütmek.: 2026 Bütçe finansman bilgisi eksik. **Hücreler:** s.234 / T189 / sütun 2 / satır 44,45,46
- [ ] 0015.Vergi beyannameleri, müşavirlik, eğitim vb. çeşitli ödemeleri zamanında eksiksiz ve tam olarak yürütmek.: 2026 Haziran Sonu Harcama finansman bilgisi eksik. **Hücreler:** s.234 / T189 / sütun 3 / satır 44,45,46
- [ ] 0015.Vergi beyannameleri, müşavirlik, eğitim vb. çeşitli ödemeleri zamanında eksiksiz ve tam olarak yürütmek.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. **Hücreler:** s.234 / T189 / sütun 4 / satır 44,45,46

### Gençlik ve Spor İşleri Müdürlüğü

Gönderime hazır: **Hayır**; 20 SOURCE mesajı / 4 kaynak kontrol maddesi.

- [ ] 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. Faaliyet toplamı 77.148.000,00; ortak personel/SGK 8.661.250,00; ekonomik kategori toplamı 89.807.672,00; ekonomik personel/SGK 8.661.250,00 TL. 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. Faaliyet toplamı 77.148.000,00; ortak personel/SGK 8.661.250,00; ekonomik kategori toplamı 89.807.672,00; ekonomik personel/SGK 8.661.250,00 TL. **Hücreler:** s.173 / T105 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.173 / T106 / sütun 5 / satır 2,3,4,5,6,7,8
- [ ] 2029: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. Faaliyet toplamı 88.367.100,00; ortak personel/SGK 10.826.563,00; ekonomik kategori toplamı 102.973.097,00; ekonomik personel/SGK 10.826.563,00 TL. 2029: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. Faaliyet toplamı 88.367.100,00; ortak personel/SGK 10.826.563,00; ekonomik kategori toplamı 102.973.097,00; ekonomik personel/SGK 10.826.563,00 TL. **Hücreler:** s.173 / T105 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.173 / T106 / sütun 6 / satır 2,3,4,5,6,7,8
- [ ] Tablo 106, 2026 Haziran Sonu Harcama: Bütçe İçi Toplam 15.375.121,93 TL, kategori satırlarının toplamı 16.195.121,93 TL; fark -820.000,00 TL. Kaynak tabloyu kontrol edin. **Hücreler:** s.173 / T106 / sütun 3 / satır 2,3,4,5,6,7,8
- [ ] Tablo 106, 2028 Tahmin: Bütçe İçi Toplam 89.807.692,00 TL, kategori satırlarının toplamı 89.807.672,00 TL; fark 20,00 TL. Kaynak tabloyu kontrol edin. **Hücreler:** s.173 / T106 / sütun 5 / satır 2,3,4,5,6,7,8

### Halkla İlişkiler Müdürlüğü

Gönderime hazır: **Hayır**; 10 SOURCE mesajı / 2 kaynak kontrol maddesi.

- [ ] 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. Faaliyet toplamı 60.269.674,00; ortak personel/SGK 34.815.579,00; ekonomik kategori toplamı 94.835.253,00; ekonomik personel/SGK 34.815.579,00 TL. 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. Faaliyet toplamı 60.269.674,00; ortak personel/SGK 34.815.579,00; ekonomik kategori toplamı 94.835.253,00; ekonomik personel/SGK 34.815.579,00 TL. **Hücreler:** s.192 / T129 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.192 / T130 / sütun 5 / satır 2,3,4,5,6,7,8
- [ ] Tablo 130, 2026 Haziran Sonu Harcama: Bütçe İçi Toplam 18.478.993,34 TL, kategori satırlarının toplamı 18.477.280,34 TL; fark 1.713,00 TL. Kaynak tabloyu kontrol edin. **Hücreler:** s.192 / T130 / sütun 3 / satır 2,3,4,5,6,7,8

### Hukuk İşleri Müdürlüğü

Gönderime hazır: **Evet**; 0 SOURCE mesajı / 0 kaynak kontrol maddesi.

SOURCE engeli yok.

### İklim Değişikliği ve Sıfır Atık Müdürlüğü

Gönderime hazır: **Evet**; 0 SOURCE mesajı / 0 kaynak kontrol maddesi.

SOURCE engeli yok.

### İmar ve Şehircilik Müdürlüğü

Gönderime hazır: **Hayır**; 6 SOURCE mesajı / 1 kaynak kontrol maddesi.

- [ ] Tablo 44, 2026 Bütçe: Bütçe Dışı Toplam için beklenen doğrulanmış bir tutar; gözlenen boş/eksik hücre. Birleştirilmiş, boş veya belirsiz kaynak hücre; kaynağa göre doğrulayın. Kaynak tabloyu kontrol edin. **Hücreler:** s.122 / T44 / sütun 2 / satır 2,3,4,5,6,7

### İnsan Kaynakları ve Eğitim Müdürlüğü

Gönderime hazır: **Hayır**; 42 SOURCE mesajı / 6 kaynak kontrol maddesi.

- [ ] 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. Faaliyet toplamı 12.577.220,00; ortak personel/SGK 26.757.500,00; ekonomik kategori toplamı 39.334.716,00; ekonomik personel/SGK 26.757.500,00 TL. 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. Faaliyet toplamı 12.577.220,00; ortak personel/SGK 26.757.500,00; ekonomik kategori toplamı 39.334.716,00; ekonomik personel/SGK 26.757.500,00 TL. **Hücreler:** s.203 / T143 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.203 / T144 / sütun 5 / satır 2,3,4,5,6,7,8
- [ ] Tablo 144, 2026 Bütçe: Program grubu dağılımı kaynakta ayrılmamış. Programlar: Araştırma, Geliştirme ve Yenilik; Yönetim ve Destek Programı. Tutarları program gruplarına göre doğrulayın. Kaynak tabloyu kontrol edin. **Hücreler:** s.203 / T144 / sütun 2 / satır 2,3,4,5,6,7,8; s.201 / T139 / sütun 2 / satır 2; s.202 / T141 / sütun 2 / satır 2
- [ ] Tablo 144, 2026 Haziran Sonu Harcama: Bütçe İçi Toplam 13.287.541,43 TL, kategori satırlarının toplamı 18.811.107,22 TL; fark -5.523.565,79 TL. Kaynak tabloyu kontrol edin.<br>Tablo 144, 2026 Haziran Sonu Harcama: Program grubu dağılımı kaynakta ayrılmamış. Programlar: Araştırma, Geliştirme ve Yenilik; Yönetim ve Destek Programı. Tutarları program gruplarına göre doğrulayın. Kaynak tabloyu kontrol edin. **Hücreler:** s.203 / T144 / sütun 3 / satır 2,3,4,5,6,7,8; s.201 / T139 / sütun 2 / satır 2; s.202 / T141 / sütun 2 / satır 2
- [ ] Tablo 144, 2027 Bütçe: Program grubu dağılımı kaynakta ayrılmamış. Programlar: Araştırma, Geliştirme ve Yenilik; Yönetim ve Destek Programı. Tutarları program gruplarına göre doğrulayın. Kaynak tabloyu kontrol edin. **Hücreler:** s.203 / T144 / sütun 4 / satır 2,3,4,5,6,7,8; s.201 / T139 / sütun 2 / satır 2; s.202 / T141 / sütun 2 / satır 2
- [ ] Tablo 144, 2028 Tahmin: Program grubu dağılımı kaynakta ayrılmamış. Programlar: Araştırma, Geliştirme ve Yenilik; Yönetim ve Destek Programı. Tutarları program gruplarına göre doğrulayın. Kaynak tabloyu kontrol edin. **Hücreler:** s.203 / T144 / sütun 5 / satır 2,3,4,5,6,7,8; s.201 / T139 / sütun 2 / satır 2; s.202 / T141 / sütun 2 / satır 2
- [ ] Tablo 144, 2029 Tahmin: Program grubu dağılımı kaynakta ayrılmamış. Programlar: Araştırma, Geliştirme ve Yenilik; Yönetim ve Destek Programı. Tutarları program gruplarına göre doğrulayın. Kaynak tabloyu kontrol edin. **Hücreler:** s.203 / T144 / sütun 6 / satır 2,3,4,5,6,7,8; s.201 / T139 / sütun 2 / satır 2; s.202 / T141 / sütun 2 / satır 2

### Kentsel Dönüşüm Müdürlüğü

Gönderime hazır: **Hayır**; 6 SOURCE mesajı / 1 kaynak kontrol maddesi.

- [ ] Tablo 64, 2026 Haziran Sonu Harcama: Bütçe İçi Toplam 4.920.160,55 TL, kategori satırlarının toplamı 5.124.271,48 TL; fark -204.110,93 TL. Kaynak tabloyu kontrol edin. **Hücreler:** s.139 / T64 / sütun 3 / satır 2,3,4,5,6,7

### Kültür, Sanat ve Sosyal İşler Müdürlüğü

Gönderime hazır: **Hayır**; 57 SOURCE mesajı / 51 kaynak kontrol maddesi.

- [ ] 0003.İş Birliği ve Ortaklıklar: Öğretim Kurumları, teknoloji transfer ofisleri, sivil toplum kuruluşları ve özel sektörle iş birliği yapmak.: 2028 toplamı bütçe içi + dışı ile eşit değil. Kaynak: Toplam = «4.912.500,00»; Bütçe İçi = «3.825.000,00»; Bütçe Dışı = «0,00» 0003.İş Birliği ve Ortaklıklar: Öğretim Kurumları, teknoloji transfer ofisleri, sivil toplum kuruluşları ve özel sektörle iş birliği yapmak.: 2028 Tahmin / Toplam kaynak tutarı doğrulanmalı. **Hücreler:** s.167 / T99 / sütun 6 / satır 8,9,10
- [ ] 0003.İş Birliği ve Ortaklıklar: Öğretim Kurumları, teknoloji transfer ofisleri, sivil toplum kuruluşları ve özel sektörle iş birliği yapmak.: 2029 toplamı bütçe içi + dışı ile eşit değil. Kaynak: Toplam = «6.215.625,00»; Bütçe İçi = «3.825.000,00»; Bütçe Dışı = «0,00» 0003.İş Birliği ve Ortaklıklar: Öğretim Kurumları, teknoloji transfer ofisleri, sivil toplum kuruluşları ve özel sektörle iş birliği yapmak.: 2029 Tahmin / Toplam kaynak tutarı doğrulanmalı. **Hücreler:** s.167 / T99 / sütun 7 / satır 8,9,10
- [ ] 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek.: 2028 toplamı bütçe içi + dışı ile eşit değil. Kaynak: Toplam = «32.373.570,00»; Bütçe İçi = «1.775.000,00»; Bütçe Dışı = «0,00» 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek.: 2028 Tahmin / Toplam kaynak tutarı doğrulanmalı. **Hücreler:** s.167 / T99 / sütun 6 / satır 47,48,49
- [ ] 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek.: 2029 toplamı bütçe içi + dışı ile eşit değil. Kaynak: Toplam = «46.275.725,00»; Bütçe İçi = «1.976.250,00»; Bütçe Dışı = «0,00» 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek.: 2029 Tahmin / Toplam kaynak tutarı doğrulanmalı. **Hücreler:** s.167 / T99 / sütun 7 / satır 47,48,49
- [ ] 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak.: 2028 Tahmin / Toplam kaynak tutarı doğrulanmalı. 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak.: 2028 Tahmin finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 6 / satır 20,21,22
- [ ] 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak.: 2029 Tahmin / Toplam kaynak tutarı doğrulanmalı. 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak.: 2029 Tahmin finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 7 / satır 20,21,22
- [ ] 0015.Örgün Eğitime Destek ve Sınavlara Hazırlık Kursları: Dezavantajlı bölgelerde yaşayan öğrenciler için örgün eğitimlerine destek ve sınavlara hazırlık kursları düzenlemek.: faaliyet açıklaması eksik. Bu kod için tekil ve uygun açıklama başlığı/metni kaynakta yok; başka faaliyetin metni taşınmadı. **Hücreler:** s.167 / T99 / sütun 1 / satır 44,58,90
- [ ] 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek.: faaliyet açıklaması eksik. Bu kod için tekil ve uygun açıklama başlığı/metni kaynakta yok; başka faaliyetin metni taşınmadı. **Hücreler:** s.167 / T99 / sütun 1 / satır 47,58,90
- [ ] 0017. Sanatsal Eğitimler: El sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında gösteriler ve yaz okulları düzenleme.: faaliyet açıklaması eksik. Bu kod için tekil ve uygun açıklama başlığı/metni kaynakta yok; başka faaliyetin metni taşınmadı. **Hücreler:** s.167 / T99 / sütun 1 / satır 50,58,90
- [ ] 0004.Ulusal ve Uluslararası Etkinlikler: Ulusal ve uluslararası festivaller, fuarlar ve etkinliklere katılım ve düzenleme.: 2026 Bütçe finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 2 / satır 11,12,13
- [ ] 0004.Ulusal ve Uluslararası Etkinlikler: Ulusal ve uluslararası festivaller, fuarlar ve etkinliklere katılım ve düzenleme.: 2026 Haziran Sonu Harcama finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 3 / satır 11,12,13
- [ ] 0004.Ulusal ve Uluslararası Etkinlikler: Ulusal ve uluslararası festivaller, fuarlar ve etkinliklere katılım ve düzenleme.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 4 / satır 11,12,13
- [ ] 0005.Sanatsal Eğitimler: Sahne sanatları eğitimleri, el sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında atölye, çalıştay ve gösteriler düzenleme.: 2026 Bütçe finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 2 / satır 14,15,16
- [ ] 0005.Sanatsal Eğitimler: Sahne sanatları eğitimleri, el sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında atölye, çalıştay ve gösteriler düzenleme.: 2026 Haziran Sonu Harcama finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 3 / satır 14,15,16
- [ ] 0005.Sanatsal Eğitimler: Sahne sanatları eğitimleri, el sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında atölye, çalıştay ve gösteriler düzenleme.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 4 / satır 14,15,16
- [ ] 0006.Sanatsal Etkinlikler: Kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kültür Park, Büyükçekmece Kordon ve Albatros sahili): 2026 Bütçe finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 2 / satır 17,18,19
- [ ] 0006.Sanatsal Etkinlikler: Kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kültür Park, Büyükçekmece Kordon ve Albatros sahili): 2026 Haziran Sonu Harcama finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 3 / satır 17,18,19
- [ ] 0006.Sanatsal Etkinlikler: Kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kültür Park, Büyükçekmece Kordon ve Albatros sahili): 2026 Yıl Sonu Tahmini finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 4 / satır 17,18,19
- [ ] 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak.: 2026 Bütçe finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 2 / satır 20,21,22
- [ ] 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak.: 2026 Haziran Sonu Harcama finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 3 / satır 20,21,22
- [ ] 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 4 / satır 20,21,22
- [ ] 0008.Toplumsal Etkinlikler: Önemli gün ve bayramlarda etkinlikler düzenlemek: 2026 Bütçe finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 2 / satır 23,24,25
- [ ] 0008.Toplumsal Etkinlikler: Önemli gün ve bayramlarda etkinlikler düzenlemek: 2026 Haziran Sonu Harcama finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 3 / satır 23,24,25
- [ ] 0008.Toplumsal Etkinlikler: Önemli gün ve bayramlarda etkinlikler düzenlemek: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 4 / satır 23,24,25
- [ ] 0009.Sanatsal Etkinlikler: Marmara Denizi kıyısında kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kıyı Marina ve Albatros sahili): 2026 Bütçe finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 2 / satır 26,27,28
- [ ] 0009.Sanatsal Etkinlikler: Marmara Denizi kıyısında kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kıyı Marina ve Albatros sahili): 2026 Haziran Sonu Harcama finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 3 / satır 26,27,28
- [ ] 0009.Sanatsal Etkinlikler: Marmara Denizi kıyısında kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kıyı Marina ve Albatros sahili): 2026 Yıl Sonu Tahmini finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 4 / satır 26,27,28
- [ ] 0010.Kent Tiyatroları Sezon Programı: Her yaş grubu için yıl boyunca düzenli tiyatro oyunlarının sergilenmesi: 2026 Bütçe finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 2 / satır 29,30,31
- [ ] 0010.Kent Tiyatroları Sezon Programı: Her yaş grubu için yıl boyunca düzenli tiyatro oyunlarının sergilenmesi: 2026 Haziran Sonu Harcama finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 3 / satır 29,30,31
- [ ] 0010.Kent Tiyatroları Sezon Programı: Her yaş grubu için yıl boyunca düzenli tiyatro oyunlarının sergilenmesi: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 4 / satır 29,30,31
- [ ] 0011.Okullara Yönelik Rehberli Müze Turları: İlçemizdeki okullarla iş birliği içerisinde yürütülen rehberli müze gezileri: 2026 Bütçe finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 2 / satır 32,33,34
- [ ] 0011.Okullara Yönelik Rehberli Müze Turları: İlçemizdeki okullarla iş birliği içerisinde yürütülen rehberli müze gezileri: 2026 Haziran Sonu Harcama finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 3 / satır 32,33,34
- [ ] 0011.Okullara Yönelik Rehberli Müze Turları: İlçemizdeki okullarla iş birliği içerisinde yürütülen rehberli müze gezileri: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 4 / satır 32,33,34
- [ ] 0012.Atölye Çalışmaları: Çocuk, Genç ve yetişkinlere yönelik atölye çalışmaları: 2026 Bütçe finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 2 / satır 35,36,37
- [ ] 0012.Atölye Çalışmaları: Çocuk, Genç ve yetişkinlere yönelik atölye çalışmaları: 2026 Haziran Sonu Harcama finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 3 / satır 35,36,37
- [ ] 0012.Atölye Çalışmaları: Çocuk, Genç ve yetişkinlere yönelik atölye çalışmaları: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 4 / satır 35,36,37
- [ ] 0013.Meslek Kursları: Yabancı dil eğitimleri, teknoloji eğitimleri, güzellik hizmetleri eğitimleri, mutfak sanatları eğitimleri vb. kurslar düzenlemek.: 2026 Bütçe finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 2 / satır 38,39,40
- [ ] 0013.Meslek Kursları: Yabancı dil eğitimleri, teknoloji eğitimleri, güzellik hizmetleri eğitimleri, mutfak sanatları eğitimleri vb. kurslar düzenlemek.: 2026 Haziran Sonu Harcama finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 3 / satır 38,39,40
- [ ] 0013.Meslek Kursları: Yabancı dil eğitimleri, teknoloji eğitimleri, güzellik hizmetleri eğitimleri, mutfak sanatları eğitimleri vb. kurslar düzenlemek.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 4 / satır 38,39,40
- [ ] 0014.Sahne Sanatları Kursları: Türk Halk Oyunları, modern dans, bale, tiyatro, enstrüman vb. kurslar düzenlemek.: 2026 Bütçe finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 2 / satır 41,42,43
- [ ] 0014.Sahne Sanatları Kursları: Türk Halk Oyunları, modern dans, bale, tiyatro, enstrüman vb. kurslar düzenlemek.: 2026 Haziran Sonu Harcama finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 3 / satır 41,42,43
- [ ] 0014.Sahne Sanatları Kursları: Türk Halk Oyunları, modern dans, bale, tiyatro, enstrüman vb. kurslar düzenlemek.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 4 / satır 41,42,43
- [ ] 0015.Örgün Eğitime Destek ve Sınavlara Hazırlık Kursları: Dezavantajlı bölgelerde yaşayan öğrenciler için örgün eğitimlerine destek ve sınavlara hazırlık kursları düzenlemek.: 2026 Bütçe finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 2 / satır 44,45,46
- [ ] 0015.Örgün Eğitime Destek ve Sınavlara Hazırlık Kursları: Dezavantajlı bölgelerde yaşayan öğrenciler için örgün eğitimlerine destek ve sınavlara hazırlık kursları düzenlemek.: 2026 Haziran Sonu Harcama finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 3 / satır 44,45,46
- [ ] 0015.Örgün Eğitime Destek ve Sınavlara Hazırlık Kursları: Dezavantajlı bölgelerde yaşayan öğrenciler için örgün eğitimlerine destek ve sınavlara hazırlık kursları düzenlemek.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 4 / satır 44,45,46
- [ ] 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek.: 2026 Bütçe finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 2 / satır 47,48,49
- [ ] 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek.: 2026 Haziran Sonu Harcama finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 3 / satır 47,48,49
- [ ] 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 4 / satır 47,48,49
- [ ] 0017. Sanatsal Eğitimler: El sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında gösteriler ve yaz okulları düzenleme.: 2026 Bütçe finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 2 / satır 50,51,52
- [ ] 0017. Sanatsal Eğitimler: El sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında gösteriler ve yaz okulları düzenleme.: 2026 Haziran Sonu Harcama finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 3 / satır 50,51,52
- [ ] 0017. Sanatsal Eğitimler: El sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında gösteriler ve yaz okulları düzenleme.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. **Hücreler:** s.167 / T99 / sütun 4 / satır 50,51,52

### Makine İkmal Bakım ve Onarım Müdürlüğü

Gönderime hazır: **Hayır**; 2 SOURCE mesajı / 1 kaynak kontrol maddesi.

- [ ] 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. Faaliyet toplamı 265.909.182,00; ortak personel/SGK 17.842.500,00; ekonomik kategori toplamı 283.751.680,00; ekonomik personel/SGK 17.842.500,00 TL. 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. Faaliyet toplamı 265.909.182,00; ortak personel/SGK 17.842.500,00; ekonomik kategori toplamı 283.751.680,00; ekonomik personel/SGK 17.842.500,00 TL. **Hücreler:** s.239 / T193 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.239 / T194 / sütun 5 / satır 2,3,4,5,6,7,8

### Mali Hizmetler Müdürlüğü

Gönderime hazır: **Hayır**; 20 SOURCE mesajı / 2 kaynak kontrol maddesi.

- [ ] 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. Faaliyet toplamı 1.075.992.302,00; ortak personel/SGK 29.625.000,00; ekonomik kategori toplamı 1.075.992.302,00; ekonomik personel/SGK 29.625.000,00 TL. 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. Faaliyet toplamı 1.075.992.302,00; ortak personel/SGK 29.625.000,00; ekonomik kategori toplamı 1.075.992.302,00; ekonomik personel/SGK 29.625.000,00 TL. **Hücreler:** s.221 / T169 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.221 / T170 / sütun 5 / satır 2,3,4,5,6,7,8,9,10,11,12,13
- [ ] Tablo 170, 2027 Bütçe: Bütçe İçi Toplam 888.224.210,00 TL, kategori satırlarının toplamı 888.224.835,00 TL; fark -625,00 TL. Kaynak tabloyu kontrol edin. **Hücreler:** s.221 / T170 / sütun 4 / satır 2,3,4,5,6,7,8,9,10,11,12,13

### Özel Kalem Müdürlüğü

Gönderime hazır: **Evet**; 0 SOURCE mesajı / 0 kaynak kontrol maddesi.

- [ ] SOURCE (validate_department dışında): Tablo 136, satır 8: Özel Kalem Müdürlüğü / 0006.Sosyal Güvenlik Kurumuna 5434 Sayılı Kanun Kapsamında Emekli İkramiyeleri Karşılığı Yapılan Ödemeler: faaliyet maliyet kaydı tekil eşleşmedi. Kart üyeliği ile müdürlük maliyet tablosundaki faaliyet kod/adını kontrol edin. **Hücre:** s.198 / T136 / sütun 1 / satır 8

### Park ve Bahçeler Müdürlüğü

Gönderime hazır: **Hayır**; 20 SOURCE mesajı / 16 kaynak kontrol maddesi.

- [ ] 0007.Kırılgan grupların da rahatlıkla kullanabileceği ortak alanların oluşturulması, bakımı ve onarımı.: 2027 toplamı bütçe içi + dışı ile eşit değil. Kaynak: Toplam = «44.333.709,00»; Bütçe İçi = «45.333.709,00»; Bütçe Dışı = «0,00» 0007.Kırılgan grupların da rahatlıkla kullanabileceği ortak alanların oluşturulması, bakımı ve onarımı.: 2027 Bütçe / Toplam kaynak tutarı doğrulanmalı. **Hücreler:** s.128 / T49 / sütun 5 / satır 20,21,22
- [ ] 2027: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. Faaliyet toplamı 542.389.649,00; ortak personel/SGK 23.223.750,00; ekonomik kategori toplamı 551.300.000,00; ekonomik personel/SGK 23.223.750,00 TL. 2027: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. Faaliyet toplamı 542.389.649,00; ortak personel/SGK 23.223.750,00; ekonomik kategori toplamı 551.300.000,00; ekonomik personel/SGK 23.223.750,00 TL. **Hücreler:** s.128 / T49 / sütun 5 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,44; s.128 / T50 / sütun 4 / satır 2,3,4,5,6,7,8
- [ ] 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. Faaliyet toplamı 923.777.553,00; ortak personel/SGK 29.029.688,00; ekonomik kategori toplamı 850.652.032,00; ekonomik personel/SGK 29.029.688,00 TL. 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. Faaliyet toplamı 923.777.553,00; ortak personel/SGK 29.029.688,00; ekonomik kategori toplamı 850.652.032,00; ekonomik personel/SGK 29.029.688,00 TL. **Hücreler:** s.128 / T49 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,44; s.128 / T50 / sütun 5 / satır 2,3,4,5,6,7,8
- [ ] 2029: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. Faaliyet toplamı 957.173.928,00; ortak personel/SGK 36.287.110,00; ekonomik kategori toplamı 1.020.978.440,00; ekonomik personel/SGK 36.287.110,00 TL. 2029: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. Faaliyet toplamı 957.173.928,00; ortak personel/SGK 36.287.110,00; ekonomik kategori toplamı 1.020.978.440,00; ekonomik personel/SGK 36.287.110,00 TL. **Hücreler:** s.128 / T49 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,44; s.128 / T50 / sütun 6 / satır 2,3,4,5,6,7,8
- [ ] SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı: 2025 Gerçekleşme: kaynak değeri doğrulanmalı (132,915). **Hücreler:** s.125 / T45 / sütun 4 / satır 11
- [ ] SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı: 2026 Planlanan: kaynak değeri doğrulanmalı (250,000). **Hücreler:** s.125 / T45 / sütun 5 / satır 11
- [ ] SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı: 2026 Yıl Sonu Tahmini: kaynak değeri doğrulanmalı (250,000). **Hücreler:** s.125 / T45 / sütun 6 / satır 11
- [ ] SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı: 2027 Hedef: kaynak değeri doğrulanmalı (200,000). **Hücreler:** s.125 / T45 / sütun 7 / satır 11
- [ ] SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı: 2029 Tahmin: kaynak değeri doğrulanmalı (300,000). **Hücreler:** s.125 / T45 / sütun 9 / satır 11
- [ ] SH016/PG05. Onaylanan Peyzaj Proje ve İskân Sayısı: 2026 Yıl Sonu Tahmini: kaynak değeri doğrulanmalı (650,000). **Hücreler:** s.125 / T45 / sütun 6 / satır 13
- [ ] SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı: 2025 Gerçekleşme: kaynak değeri doğrulanmalı (17,840). **Hücreler:** s.125 / T45 / sütun 4 / satır 9
- [ ] SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı: 2026 Planlanan: kaynak değeri doğrulanmalı (50,000). **Hücreler:** s.125 / T45 / sütun 5 / satır 9
- [ ] SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı: 2026 Yıl Sonu Tahmini: kaynak değeri doğrulanmalı (50,000). **Hücreler:** s.125 / T45 / sütun 6 / satır 9
- [ ] SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı: 2027 Hedef: kaynak değeri doğrulanmalı (50,000). **Hücreler:** s.125 / T45 / sütun 7 / satır 9
- [ ] SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı: 2028 Tahmin: kaynak değeri doğrulanmalı (60,000). **Hücreler:** s.125 / T45 / sütun 8 / satır 9
- [ ] SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı: 2029 Tahmin: kaynak değeri doğrulanmalı (60,000). **Hücreler:** s.125 / T45 / sütun 9 / satır 9

### Plan Proje Müdürlüğü

Gönderime hazır: **Hayır**; 6 SOURCE mesajı / 1 kaynak kontrol maddesi.

- [ ] Tablo 60, 2026 Haziran Sonu Harcama: Bütçe İçi Toplam 11.501.713,28 TL, kategori satırlarının toplamı 12.362.364,94 TL; fark -860.651,66 TL. Kaynak tabloyu kontrol edin. **Hücreler:** s.136 / T60 / sütun 3 / satır 2,3,4,5,6,7

### Rehberlik ve Teftiş Kurulu Müdürlüğü

Gönderime hazır: **Hayır**; 10 SOURCE mesajı / 2 kaynak kontrol maddesi.

- [ ] 2029: bütçe dışı faaliyet ve ekonomik toplamları uyuşmuyor. Faaliyet toplamı 333.750,00; ortak personel/SGK 2.578.125,00; ekonomik kategori toplamı 2.811.875,00; ekonomik personel/SGK 2.578.125,00 TL. 2029: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. Faaliyet toplamı 333.750,00; ortak personel/SGK 2.578.125,00; ekonomik kategori toplamı 2.811.875,00; ekonomik personel/SGK 2.578.125,00 TL. **Hücreler:** s.210 / T151 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,14; s.210 / T152 / sütun 6 / satır 2,3,4,5,6,7,8
- [ ] Tablo 152, 2026 Haziran Sonu Harcama: Bütçe İçi Toplam 955.735,48 TL, kategori satırlarının toplamı 936.918,72 TL; fark 18.816,76 TL. Kaynak tabloyu kontrol edin. **Hücreler:** s.210 / T152 / sütun 3 / satır 2,3,4,5,6,7,8

### Ruhsat ve Denetim Müdürlüğü

Gönderime hazır: **Hayır**; 12 SOURCE mesajı / 2 kaynak kontrol maddesi.

- [ ] Tablo 14, 2026 Bütçe: Bütçe İçi Toplam 11.623.833,00 TL, kategori satırlarının toplamı 11.386.500,16 TL; fark 237.332,84 TL. Kaynak tabloyu kontrol edin. **Hücreler:** s.101 / T14 / sütun 2 / satır 2,3,4,5,6,7
- [ ] Tablo 14, 2026 Haziran Sonu Harcama: Bütçe İçi Toplam 4.815.578,31 TL, kategori satırlarının toplamı 5.151.457,55 TL; fark -335.879,24 TL. Kaynak tabloyu kontrol edin. **Hücreler:** s.101 / T14 / sütun 3 / satır 2,3,4,5,6,7

### Sağlık İşleri Müdürlüğü

Gönderime hazır: **Hayır**; 12 SOURCE mesajı / 2 kaynak kontrol maddesi.

- [ ] 2029: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. Faaliyet toplamı 24.931.292,00; ortak personel/SGK 21.946.875,00; ekonomik kategori toplamı 47.049.588,00; ekonomik personel/SGK 21.946.875,00 TL. 2029: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. Faaliyet toplamı 24.931.292,00; ortak personel/SGK 21.946.875,00; ekonomik kategori toplamı 47.049.588,00; ekonomik personel/SGK 21.946.875,00 TL. **Hücreler:** s.98 / T9 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.98 / T10 / sütun 6 / satır 2,3,4,5,6,7,8,9
- [ ] Tablo 10, 2026 Haziran Sonu Harcama: Bütçe İçi Toplam 6.721.207,36 TL, kategori satırlarının toplamı 6.721.207,46 TL; fark -0,10 TL. Kaynak tabloyu kontrol edin. **Hücreler:** s.98 / T10 / sütun 3 / satır 2,3,4,5,6,7,8,9

### Sosyal Destek Müdürlüğü

Gönderime hazır: **Evet**; 0 SOURCE mesajı / 0 kaynak kontrol maddesi.

SOURCE engeli yok.

### Strateji Geliştirme Müdürlüğü

Gönderime hazır: **Hayır**; 2 SOURCE mesajı / 1 kaynak kontrol maddesi.

- [ ] 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. Faaliyet toplamı 2.325.528,00; ortak personel/SGK 4.495.313,00; ekonomik kategori toplamı 6.770.841,00; ekonomik personel/SGK 4.495.313,00 TL. 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. Faaliyet toplamı 2.325.528,00; ortak personel/SGK 4.495.313,00; ekonomik kategori toplamı 6.770.841,00; ekonomik personel/SGK 4.495.313,00 TL. **Hücreler:** s.214 / T159 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,29; s.214 / T160 / sütun 5 / satır 2,3,4,5,6,7

### Tarımsal Hizmetler Müdürlüğü

Gönderime hazır: **Hayır**; 20 SOURCE mesajı / 7 kaynak kontrol maddesi.

- [ ] 0008.Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini: 2027 Bütçe / Toplam kaynak tutarı doğrulanmalı. 0008.Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini: 2027 Bütçe finansman bilgisi eksik. **Hücreler:** s.156 / T83 / sütun 5 / satır 23,24,25
- [ ] 0008.Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini: 2028 Tahmin / Toplam kaynak tutarı doğrulanmalı. 0008.Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini: 2028 Tahmin finansman bilgisi eksik. **Hücreler:** s.156 / T83 / sütun 6 / satır 23,24,25
- [ ] 0008.Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini: 2029 Tahmin / Toplam kaynak tutarı doğrulanmalı. 0008.Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini: 2029 Tahmin finansman bilgisi eksik. **Hücreler:** s.156 / T83 / sütun 7 / satır 23,24,25
- [ ] 0009.Üretimin zehirsiz gıda, toprak kirliliği önleyici ve çevre korunma etmenlerinin önemi çevre korunma etmenlerinin önemi çerçevesinde tasarruflu ve sürdürülebilir olarak yürütülmesi: 2027 Bütçe / Toplam kaynak tutarı doğrulanmalı. 0009.Üretimin zehirsiz gıda, toprak kirliliği önleyici ve çevre korunma etmenlerinin önemi çevre korunma etmenlerinin önemi çerçevesinde tasarruflu ve sürdürülebilir olarak yürütülmesi: 2027 Bütçe finansman bilgisi eksik. **Hücreler:** s.156 / T83 / sütun 5 / satır 26,27,28
- [ ] 0009.Üretimin zehirsiz gıda, toprak kirliliği önleyici ve çevre korunma etmenlerinin önemi çevre korunma etmenlerinin önemi çerçevesinde tasarruflu ve sürdürülebilir olarak yürütülmesi: 2028 Tahmin / Toplam kaynak tutarı doğrulanmalı. 0009.Üretimin zehirsiz gıda, toprak kirliliği önleyici ve çevre korunma etmenlerinin önemi çevre korunma etmenlerinin önemi çerçevesinde tasarruflu ve sürdürülebilir olarak yürütülmesi: 2028 Tahmin finansman bilgisi eksik. **Hücreler:** s.156 / T83 / sütun 6 / satır 26,27,28
- [ ] 0009.Üretimin zehirsiz gıda, toprak kirliliği önleyici ve çevre korunma etmenlerinin önemi çevre korunma etmenlerinin önemi çerçevesinde tasarruflu ve sürdürülebilir olarak yürütülmesi: 2029 Tahmin / Toplam kaynak tutarı doğrulanmalı. 0009.Üretimin zehirsiz gıda, toprak kirliliği önleyici ve çevre korunma etmenlerinin önemi çevre korunma etmenlerinin önemi çerçevesinde tasarruflu ve sürdürülebilir olarak yürütülmesi: 2029 Tahmin finansman bilgisi eksik. **Hücreler:** s.156 / T83 / sütun 7 / satır 26,27,28
- [ ] Tablo 84, 2026 Bütçe: Bütçe İçi Toplam 16.565.381,00 TL, kategori satırlarının toplamı 16.365.381,00 TL; fark 200.000,00 TL. Kaynak tabloyu kontrol edin. **Hücreler:** s.156 / T84 / sütun 2 / satır 2,3,4,5,6,7,8

### Temizlik İşleri Müdürlüğü

Gönderime hazır: **Evet**; 0 SOURCE mesajı / 0 kaynak kontrol maddesi.

SOURCE engeli yok.

### Veteriner İşleri Müdürlüğü

Gönderime hazır: **Hayır**; 16 SOURCE mesajı / 4 kaynak kontrol maddesi.

- [ ] 0004.Mevcut barınak kapasitesinin artırılması ve teknik altyapının iyileştirilmesini sağlamak.: 2027 Bütçe / Toplam kaynak tutarı doğrulanmalı. 0004.Mevcut barınak kapasitesinin artırılması ve teknik altyapının iyileştirilmesini sağlamak.: 2027 Bütçe finansman bilgisi eksik. **Hücreler:** s.107 / T23 / sütun 5 / satır 11,12,13
- [ ] 0004.Mevcut barınak kapasitesinin artırılması ve teknik altyapının iyileştirilmesini sağlamak.: 2028 Tahmin / Toplam kaynak tutarı doğrulanmalı. 0004.Mevcut barınak kapasitesinin artırılması ve teknik altyapının iyileştirilmesini sağlamak.: 2028 Tahmin finansman bilgisi eksik. **Hücreler:** s.107 / T23 / sütun 6 / satır 11,12,13
- [ ] 0004.Mevcut barınak kapasitesinin artırılması ve teknik altyapının iyileştirilmesini sağlamak.: 2029 Tahmin / Toplam kaynak tutarı doğrulanmalı. 0004.Mevcut barınak kapasitesinin artırılması ve teknik altyapının iyileştirilmesini sağlamak.: 2029 Tahmin finansman bilgisi eksik. **Hücreler:** s.107 / T23 / sütun 7 / satır 11,12,13
- [ ] Tablo 24, 2026 Bütçe: Bütçe İçi Toplam 78.140.000,00 TL, kategori satırlarının toplamı 80.767.000,00 TL; fark -2.627.000,00 TL. Kaynak tabloyu kontrol edin. **Hücreler:** s.107 / T24 / sütun 2 / satır 2,3,4,5,6,7,8,9

### Yazı İşleri Müdürlüğü

Gönderime hazır: **Hayır**; 75 SOURCE mesajı / 27 kaynak kontrol maddesi.

- [ ] 2027: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. Faaliyet toplamı 16.330.730,00; ortak personel/SGK 24.700.000,00; ekonomik kategori toplamı 41.026.130,00; ekonomik personel/SGK 24.700.000,00 TL. 2027: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. Faaliyet toplamı 16.330.730,00; ortak personel/SGK 24.700.000,00; ekonomik kategori toplamı 41.026.130,00; ekonomik personel/SGK 24.700.000,00 TL. **Hücreler:** s.227 / T179 / sütun 5 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,38; s.227 / T180 / sütun 4 / satır 2,3,4,5,6,7,8,9
- [ ] 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. Faaliyet toplamı 19.452.675,00; ortak personel/SGK 30.875.000,00; ekonomik kategori toplamı 52.230.432,00; ekonomik personel/SGK 30.882.000,00 TL. 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. Faaliyet toplamı 19.452.675,00; ortak personel/SGK 30.875.000,00; ekonomik kategori toplamı 52.230.432,00; ekonomik personel/SGK 30.882.000,00 TL. **Hücreler:** s.227 / T179 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,38; s.227 / T180 / sütun 5 / satır 2,3,4,5,6,7,8,9
- [ ] 2029: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. Faaliyet toplamı 19.555.001,00; ortak personel/SGK 38.593.750,00; ekonomik kategori toplamı 60.188.800,00; ekonomik personel/SGK 38.593.750,00 TL. 2029: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. Faaliyet toplamı 19.555.001,00; ortak personel/SGK 38.593.750,00; ekonomik kategori toplamı 60.188.800,00; ekonomik personel/SGK 38.593.750,00 TL. **Hücreler:** s.227 / T179 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,38; s.227 / T180 / sütun 6 / satır 2,3,4,5,6,7,8,9
- [ ] 0002.Alınan Kararların İlgili Birimlere İletilmesi: 2026 Bütçe finansman bilgisi eksik. **Hücreler:** s.227 / T179 / sütun 2 / satır 5,6,7
- [ ] 0002.Alınan Kararların İlgili Birimlere İletilmesi: 2026 Haziran Sonu Harcama finansman bilgisi eksik. **Hücreler:** s.227 / T179 / sütun 3 / satır 5,6,7
- [ ] 0002.Alınan Kararların İlgili Birimlere İletilmesi: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. **Hücreler:** s.227 / T179 / sütun 4 / satır 5,6,7
- [ ] 0007.Dijital Nikah Yönetim Sisteminin Kurulması ve İşletilmesi.: 2026 Bütçe finansman bilgisi eksik. **Hücreler:** s.227 / T179 / sütun 2 / satır 20,21,22
- [ ] 0007.Dijital Nikah Yönetim Sisteminin Kurulması ve İşletilmesi.: 2026 Haziran Sonu Harcama finansman bilgisi eksik. **Hücreler:** s.227 / T179 / sütun 3 / satır 20,21,22
- [ ] 0007.Dijital Nikah Yönetim Sisteminin Kurulması ve İşletilmesi.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. **Hücreler:** s.227 / T179 / sütun 4 / satır 20,21,22
- [ ] 0008.Nikah Akdi ve Tescil İşlemlerinin Yürütülmesi.: 2026 Bütçe finansman bilgisi eksik. **Hücreler:** s.227 / T179 / sütun 2 / satır 23,24,25
- [ ] 0008.Nikah Akdi ve Tescil İşlemlerinin Yürütülmesi.: 2026 Haziran Sonu Harcama finansman bilgisi eksik. **Hücreler:** s.227 / T179 / sütun 3 / satır 23,24,25
- [ ] 0008.Nikah Akdi ve Tescil İşlemlerinin Yürütülmesi.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. **Hücreler:** s.227 / T179 / sütun 4 / satır 23,24,25
- [ ] 0009.Nikah Salonlarının Teknolojik ve Fiziksel Modernizasyonu.: 2026 Bütçe finansman bilgisi eksik. **Hücreler:** s.227 / T179 / sütun 2 / satır 26,27,28
- [ ] 0009.Nikah Salonlarının Teknolojik ve Fiziksel Modernizasyonu.: 2026 Haziran Sonu Harcama finansman bilgisi eksik. **Hücreler:** s.227 / T179 / sütun 3 / satır 26,27,28
- [ ] 0009.Nikah Salonlarının Teknolojik ve Fiziksel Modernizasyonu.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. **Hücreler:** s.227 / T179 / sütun 4 / satır 26,27,28
- [ ] 0010.Saha Hizmetleri İçin Mobil Altyapı Desteği.: 2026 Bütçe finansman bilgisi eksik. **Hücreler:** s.227 / T179 / sütun 2 / satır 29,30,31
- [ ] 0010.Saha Hizmetleri İçin Mobil Altyapı Desteği.: 2026 Haziran Sonu Harcama finansman bilgisi eksik. **Hücreler:** s.227 / T179 / sütun 3 / satır 29,30,31
- [ ] 0010.Saha Hizmetleri İçin Mobil Altyapı Desteği.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. **Hücreler:** s.227 / T179 / sütun 4 / satır 29,30,31
- [ ] 0011.Evlilik Öncesi Bilgilendirme ve Rehberlik Hizmetleri: 2026 Bütçe finansman bilgisi eksik. **Hücreler:** s.227 / T179 / sütun 2 / satır 32,33,34
- [ ] 0011.Evlilik Öncesi Bilgilendirme ve Rehberlik Hizmetleri: 2026 Haziran Sonu Harcama finansman bilgisi eksik. **Hücreler:** s.227 / T179 / sütun 3 / satır 32,33,34
- [ ] 0011.Evlilik Öncesi Bilgilendirme ve Rehberlik Hizmetleri: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. **Hücreler:** s.227 / T179 / sütun 4 / satır 32,33,34
- [ ] 2028: ekonomik personel/SGK satırları ortak tablodan farklı. Faaliyet toplamı 19.452.675,00; ortak personel/SGK 30.875.000,00; ekonomik kategori toplamı 52.230.432,00; ekonomik personel/SGK 30.882.000,00 TL. **Hücreler:** s.227 / T179 / sütun 6 / satır 38; s.227 / T180 / sütun 5 / satır 2,3,4,5,6,7,8,9
- [ ] Tablo 180, 2026 Bütçe: Program grubu dağılımı kaynakta ayrılmamış. Programlar: Yönetim ve Destek Programı; Yoksullukla Mücadele Ve Sosyal Yardımlaşma Programı; Vatandaşlık ve Sivil Toplum Programı. Tutarları program gruplarına göre doğrulayın. Kaynak tabloyu kontrol edin. **Hücreler:** s.227 / T180 / sütun 2 / satır 2,3,4,5,6,7,8,9; s.223 / T171 / sütun 2 / satır 2; s.224 / T173 / sütun 2 / satır 2; s.225 / T175 / sütun 2 / satır 2; s.226 / T177 / sütun 2 / satır 2
- [ ] Tablo 180, 2026 Haziran Sonu Harcama: Program grubu dağılımı kaynakta ayrılmamış. Programlar: Yönetim ve Destek Programı; Yoksullukla Mücadele Ve Sosyal Yardımlaşma Programı; Vatandaşlık ve Sivil Toplum Programı. Tutarları program gruplarına göre doğrulayın. Kaynak tabloyu kontrol edin. **Hücreler:** s.227 / T180 / sütun 3 / satır 2,3,4,5,6,7,8,9; s.223 / T171 / sütun 2 / satır 2; s.224 / T173 / sütun 2 / satır 2; s.225 / T175 / sütun 2 / satır 2; s.226 / T177 / sütun 2 / satır 2
- [ ] Tablo 180, 2027 Bütçe: Program grubu dağılımı kaynakta ayrılmamış. Programlar: Yönetim ve Destek Programı; Yoksullukla Mücadele Ve Sosyal Yardımlaşma Programı; Vatandaşlık ve Sivil Toplum Programı. Tutarları program gruplarına göre doğrulayın. Kaynak tabloyu kontrol edin. **Hücreler:** s.227 / T180 / sütun 4 / satır 2,3,4,5,6,7,8,9; s.223 / T171 / sütun 2 / satır 2; s.224 / T173 / sütun 2 / satır 2; s.225 / T175 / sütun 2 / satır 2; s.226 / T177 / sütun 2 / satır 2
- [ ] Tablo 180, 2028 Tahmin: Bütçe İçi Toplam 52.223.432,00 TL, kategori satırlarının toplamı 52.230.432,00 TL; fark -7.000,00 TL. Kaynak tabloyu kontrol edin.<br>Tablo 180, 2028 Tahmin: Program grubu dağılımı kaynakta ayrılmamış. Programlar: Yönetim ve Destek Programı; Yoksullukla Mücadele Ve Sosyal Yardımlaşma Programı; Vatandaşlık ve Sivil Toplum Programı. Tutarları program gruplarına göre doğrulayın. Kaynak tabloyu kontrol edin. Tablo 180, 2028 Tahmin: Bütçe İçi Toplam 52.223.432,00 TL, kategori satırlarının toplamı 52.230.432,00 TL; fark -7.000,00 TL. Kaynak tabloyu kontrol edin.<br>Tablo 180, 2028 Tahmin: Program grubu dağılımı kaynakta ayrılmamış. Programlar: Yönetim ve Destek Programı; Yoksullukla Mücadele Ve Sosyal Yardımlaşma Programı; Vatandaşlık ve Sivil Toplum Programı. Tutarları program gruplarına göre doğrulayın. Kaynak tabloyu kontrol edin.<br>Tablo 180, 2028 Tahmin: Personel ve SGK satırları ortak personel tablosundan farklı; ekonomik toplam 30.882.000,00 TL, ortak personel toplamı 30.875.000,00 TL; fark 7.000,00 TL. İki kaynağı karşılaştırın. **Hücreler:** s.227 / T180 / sütun 5 / satır 2,3,4,5,6,7,8,9; s.223 / T171 / sütun 2 / satır 2; s.224 / T173 / sütun 2 / satır 2; s.225 / T175 / sütun 2 / satır 2; s.226 / T177 / sütun 2 / satır 2; s.227 / T179 / sütun 6 / satır 38
- [ ] Tablo 180, 2029 Tahmin: Program grubu dağılımı kaynakta ayrılmamış. Programlar: Yönetim ve Destek Programı; Yoksullukla Mücadele Ve Sosyal Yardımlaşma Programı; Vatandaşlık ve Sivil Toplum Programı. Tutarları program gruplarına göre doğrulayın. Kaynak tabloyu kontrol edin. **Hücreler:** s.227 / T180 / sütun 6 / satır 2,3,4,5,6,7,8,9; s.223 / T171 / sütun 2 / satır 2; s.224 / T173 / sütun 2 / satır 2; s.225 / T175 / sütun 2 / satır 2; s.226 / T177 / sütun 2 / satır 2

### Zabıta Müdürlüğü

Gönderime hazır: **Hayır**; 8 SOURCE mesajı / 1 kaynak kontrol maddesi.

- [ ] Tablo 20, 2026 Haziran Sonu Harcama: Bütçe İçi Toplam 45.863.621,38 TL, kategori satırlarının toplamı 51.258.201,04 TL; fark -5.394.579,66 TL. Kaynak tabloyu kontrol edin. **Hücreler:** s.104 / T20 / sütun 3 / satır 2,3,4,5,6,7,8

## Dönüşüm ve varsayımlar

Eşlenmeyen ad (ham metin korundu, yerleşik müdürlük eşlemesi uygulandı): Gelirler Müdürlüğü (Bütçe İşletme Şefliği).

Basılı sayfaya bağlı olmayan tablolar (dışlama seçeneğinden bağımsız; yüklemeye alınmaz): [{"id": "ubbb4ibbe3", "type": "cost"}, {"id": "ubbb4ibbcb", "type": "economic"}, {"id": "ubb2aibb60", "type": "card"}, {"id": "ubb2aibb40", "type": "membership"}].

Teyit bekleyen ad eşlemeleri: Gençlik ve Spor Hizmetleri Müdürlüğü; Sosyal Hizmetler Müdürlüğü; Basın Yayın ve Halkla İlişkiler Müdürlüğü; Harita ve Planlama Müdürlüğü; Araştırma ve Geliştirme Müdürlüğü. Program/alt program kodları kitapta yoktur ve boş bırakılır. Tekil müdürlük içi faaliyet kodu üyeliği belirler. Resmî katalog 0006 Özel Kalem gibi maliyet karşılığı bulunmayan üyelikleri korur; yeni maliyet üretilmez. Nihai kitap dışlamasız yeniden denenmelidir.

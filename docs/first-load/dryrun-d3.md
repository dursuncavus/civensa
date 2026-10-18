# 2027 PP ilk yükleme — kaynak kontrol listesi

Kitap temiz mi: **Hayır**.

Kitap kontrol maddesi: **158**.

Yalnız program grubu dağılımı bekleyen müdürlük: **0**.

Gönderime hazır: **5/33** (yalnızca bu prova).

**Provada çıkarıldı — nihai kitapta düzeltilmeli: T195, kitap s.243; başlık: Ekonomik Ad &#124; Ekonomik Ad &#124; 2025 Bütçe &#124; 2025 Haziran Sonu Harcama &#124; 2025 Yıl Sonu Harcama &#124; 2026 Bütçe &#124; 2027 Tahmin &#124; 2028 Tahmin.**

Yapılacak: s.243, tablo 195, satır 1, yıl sütunları: dönemin Bütçe yılı/sütunlarını ve ilgili kart bağlantısını düzeltin. Nihai kitabı tablo çıkarmadan yeniden deneyin.

Kaynak: `pp2027_print_d3.idml`; SHA256: `999a43b2c07074191a1e47622c544b9a53813f23d3bb6518e63b29979ca384cb`.

Mesaj sayımı: **370 kitap mesajı + 112 yalnız program grubu mesajı = 482**. Kitap mesajlarından 28 adedi ayrıca dağılım gerektirir; kitap nedenleri listede, dağılım hücreleri ayrı bölümde gösterilir ve mesaj ikinci kez sayılmaz.

Doğrulama: 482 SOURCE mesajı, 0 SYSTEM mesajı; 0 saklama aktarım sorunu; 22 engelleyici olmayan uyarı.

Aynı kök nedenden üreyen mesajlar müdürlük listesinde tek kontrol maddesinde toplanır. Hazır = gerçek paket uygulandı ve validate_department hata listesi boş. Çıkarılan tablo ve ek üyelik sorunu doğrulama mesajı sayısına eklenmez. Kitap maddeleri dağılım işlerini içermez. Fark = kitaptaki/kontrol edilen toplam − hesaplanan tutar. Koşullu 0,00 önerisi veri düzeltmesi değildir; kaynak yokluğunu Strateji teyit etmelidir.

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

SYSTEM = üretilen Word, ayrıştırıcı, eşleme/ekim, saklama veya doğrulama kaynaklı hata. SOURCE = kitap hücresi/dağılımının kendisi. Tanınmayan hata veya kitap–Word/saklama farkı otomatik SOURCE sayılmaz; SYSTEM olarak raporlanır. Program Grubu Belirlenmeli kitap düzeltme listesine girmez; kategori × program grubu dağılımı yükleme sonrası ayrı Strateji işidir. Paylaştırma oranı veya varsayılan grup uydurulmadı.

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
- Saklanan değerler (ondalık depolama gösterimi): [{"year": 2027, "activity_total": "267575845.00", "personnel": "21336000.00", "economic_total": "283812848.00", "economic_personnel": "21336000.00", "activity_inside": "267575845.00", "economic_inside": "262476848.00", "activity_outside": "0.00", "economic_outside": "0.00"}]
- Neden: 2027: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. Faaliyet toplamı 267.575.845,00; ortak personel/SGK 21.336.000,00; ekonomik kategori toplamı 283.812.848,00; ekonomik personel/SGK 21.336.000,00 TL.

### Personel/SGK toplam farkı — SOURCE

Yazı İşleri Müdürlüğü

- Kitap hücreleri: s.227 T179 r38c6 = «30.875.000,00»; s.227 T180 r2c5 = «27.125.000,00»; s.227 T180 r3c5 = «3.757.000,00»; s.227 T180 r4c5 = «14.073.382,00»; s.227 T180 r5c5 = «2.197.650,00»; s.227 T180 r6c5 = «5.077.400,00»; s.227 T180 r7c5 = «52.223.432,00»; s.227 T180 r8c5 = «0,00»; s.227 T180 r9c5 = «52.223.432,00»
- Üretilen Word hücreleri: s.227 T179 r38c6 = «30.875.000,00»; s.227 T180 r2c5 = «27.125.000,00»; s.227 T180 r3c5 = «3.757.000,00»; s.227 T180 r4c5 = «14.073.382,00»; s.227 T180 r5c5 = «2.197.650,00»; s.227 T180 r6c5 = «5.077.400,00»; s.227 T180 r7c5 = «52.223.432,00»; s.227 T180 r8c5 = «0,00»; s.227 T180 r9c5 = «52.223.432,00»
- Saklanan değerler (ondalık depolama gösterimi): [{"year": 2028, "activity_total": "19452675.00", "personnel": "30875000.00", "economic_total": "52230432.00", "economic_personnel": "30882000.00", "activity_inside": "19452675.00", "economic_inside": "21348432.00", "activity_outside": "0.00", "economic_outside": "0.00"}]
- Neden: 2028: ekonomik personel/SGK satırları ortak tablodan farklı. Faaliyet toplamı 19.452.675,00; ortak personel/SGK 30.875.000,00; ekonomik kategori toplamı 52.230.432,00; ekonomik personel/SGK 30.882.000,00 TL.

### SYSTEM düzeltmesinin saklama kanıtı

- Kitap: s.192 T129 r48c1 = «0006.Personel Eğitim ve Yetkinlik Geliştirme Faaliyetleri»; s.192 T129 r49c1 = «Çözüm Masası bünyesinde görev yapan personelin vatandaşlarla etkili iletişim kurma, talep, öneri ve şikâyetleri doğru şekilde karşılama, kayıt altına alma, yönlendirme ve takip etme konularındaki bilgi, beceri ve yetkinliklerinin geliştirilmesi amacıyla eğitim faaliyetleri yürütülmektedir. Bu kapsamda; vatandaş iletişimi, etkili iletişim teknikleri, çözüm odaklı yaklaşım, başvuru ve çağrı yönetimi, dijital sistemlerin etkin kullanımı ile hizmet kalitesinin artırılmasına yönelik eğitim, seminer ve benzeri çalışmaların gerçekleştirilmesi amaçlanmaktadır.»
- Word: s.192 T129 r48c1 = «0006.Personel Eğitim ve Yetkinlik Geliştirme Faaliyetleri»; s.192 T129 r49c1 = «Çözüm Masası bünyesinde görev yapan personelin vatandaşlarla etkili iletişim kurma, talep, öneri ve şikâyetleri doğru şekilde karşılama, kayıt altına alma, yönlendirme ve takip etme konularındaki bilgi, beceri ve yetkinliklerinin geliştirilmesi amacıyla eğitim faaliyetleri yürütülmektedir. Bu kapsamda; vatandaş iletişimi, etkili iletişim teknikleri, çözüm odaklı yaklaşım, başvuru ve çağrı yönetimi, dijital sistemlerin etkin kullanımı ile hizmet kalitesinin artırılmasına yönelik eğitim, seminer ve benzeri çalışmaların gerçekleştirilmesi amaçlanmaktadır.»
- Saklanan Activity.explanation: Çözüm Masası bünyesinde görev yapan personelin vatandaşlarla etkili iletişim kurma, talep, öneri ve şikâyetleri doğru şekilde karşılama, kayıt altına alma, yönlendirme ve takip etme konularındaki bilgi, beceri ve yetkinliklerinin geliştirilmesi amacıyla eğitim faaliyetleri yürütülmektedir. Bu kapsamda; vatandaş iletişimi, etkili iletişim teknikleri, çözüm odaklı yaklaşım, başvuru ve çağrı yönetimi, dijital sistemlerin etkin kullanımı ile hizmet kalitesinin artırılmasına yönelik eğitim, seminer ve benzeri çalışmaların gerçekleştirilmesi amaçlanmaktadır.

- Kitap: s.107 T24 r7c3 = «₺10.424.938,95»
- Word: s.107 T24 r7c3 = «₺10.424.938,95»
- Saklanan EconomicValue.source_context_json.totals.inside: {"year": 2026, "kind": "midyear_spend", "amount": "10424938.95", "raw_text": "₺10.424.938,95", "state": "verified"}

## Kitapta düzeltilmez — yükleme sonrası Strateji girer (program grubu dağılımı)

Bu bölüm kitap kontrol maddesi sayısına dahil değildir. Her kaynak kategori hücresi için Hizmet + Yönetim ve Destek tutarları kaynak tutarını korumalıdır. Bütçe dışı 0,00 değerleri kitabın Bütçe Dışı Toplam satırından gelir; kategori hücresindeki bütçe içi tutarla karıştırılmamalı. Mevcut uygulamada Strateji için iki gruba atomik bölme akışı bulunmuyor; bu bölüm yapılacak yükleme sonrası işi tanımlar (PR açıklamasında route/validator incelemesi vardır).

### Fen İşleri Müdürlüğü

50 doğrulama mesajında dağılım gereksinimi var; başka kitap nedeni de taşıyan mesajlar kitap sayımında bir kez sayılmıştır.

| Kart | Program / alt program | Grup |
| --- | --- | --- |
| 2027/1 | Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | Yönetim ve Destek |
| 2027/2 | Kent İçi Ulaşım / Karayolu Altyapısı ve Hizmetleri | Hizmet |
| 2027/3 | Kent Güvenliği ve Sağlığı / Çevre ve Halk Sağlığının Korunması | Hizmet |

| Yıl / sütun | Kategori | Finansman | Dağıtılacak tutar | Kaynak hücresi |
| --- | --- | --- | ---: | --- |
| 2026 Bütçe | Sermaye Giderleri | Bütçe İçi | 453.562.000,00 | s.118 / T38 / sütun 2 / satır 6 |
| 2026 Bütçe | Sermaye Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 2 / satır 6,8 |
| 2026 Bütçe | Cari Transferler | Bütçe İçi | 4.600.000,00 | s.118 / T38 / sütun 2 / satır 5 |
| 2026 Bütçe | Cari Transferler | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 2 / satır 5,8 |
| 2026 Bütçe | Mal ve Hizmet Alım Giderleri | Bütçe İçi | 442.490.000,00 | s.118 / T38 / sütun 2 / satır 4 |
| 2026 Bütçe | Mal ve Hizmet Alım Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 2 / satır 4,8 |
| 2026 Bütçe | Personel Giderleri | Bütçe İçi | 46.388.000,00 | s.118 / T38 / sütun 2 / satır 2 |
| 2026 Bütçe | Personel Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 2 / satır 2,8 |
| 2026 Bütçe | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe İçi | 2.300.000,00 | s.118 / T38 / sütun 2 / satır 3 |
| 2026 Bütçe | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 2 / satır 3,8 |
| 2026 Haziran Sonu Harcama | Sermaye Giderleri | Bütçe İçi | 537.600,00 | s.118 / T38 / sütun 3 / satır 6 |
| 2026 Haziran Sonu Harcama | Sermaye Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 3 / satır 6,8 |
| 2026 Haziran Sonu Harcama | Cari Transferler | Bütçe İçi | 0,00 | s.118 / T38 / sütun 3 / satır 5 |
| 2026 Haziran Sonu Harcama | Cari Transferler | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 3 / satır 5,8 |
| 2026 Haziran Sonu Harcama | Mal ve Hizmet Alım Giderleri | Bütçe İçi | 33.097.435,87 | s.118 / T38 / sütun 3 / satır 4 |
| 2026 Haziran Sonu Harcama | Mal ve Hizmet Alım Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 3 / satır 4,8 |
| 2026 Haziran Sonu Harcama | Personel Giderleri | Bütçe İçi | 17.824.074,35 | s.118 / T38 / sütun 3 / satır 2 |
| 2026 Haziran Sonu Harcama | Personel Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 3 / satır 2,8 |
| 2026 Haziran Sonu Harcama | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe İçi | 1.261.101,27 | s.118 / T38 / sütun 3 / satır 3 |
| 2026 Haziran Sonu Harcama | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 3 / satır 3,8 |
| 2027 Bütçe | Sermaye Giderleri | Bütçe İçi | 1.071.850.000,00 | s.118 / T38 / sütun 4 / satır 6 |
| 2027 Bütçe | Sermaye Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 4 / satır 6,8 |
| 2027 Bütçe | Cari Transferler | Bütçe İçi | 1.200.000,00 | s.118 / T38 / sütun 4 / satır 5 |
| 2027 Bütçe | Cari Transferler | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 4 / satır 5,8 |
| 2027 Bütçe | Mal ve Hizmet Alım Giderleri | Bütçe İçi | 116.088.909,00 | s.118 / T38 / sütun 4 / satır 4 |
| 2027 Bütçe | Mal ve Hizmet Alım Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 4 / satır 4,8 |
| 2027 Bütçe | Personel Giderleri | Bütçe İçi | 44.000.000,00 | s.118 / T38 / sütun 4 / satır 2 |
| 2027 Bütçe | Personel Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 4 / satır 2,8 |
| 2027 Bütçe | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe İçi | 3.300.000,00 | s.118 / T38 / sütun 4 / satır 3 |
| 2027 Bütçe | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 4 / satır 3,8 |
| 2028 Tahmin | Sermaye Giderleri | Bütçe İçi | 1.859.300.000,00 | s.118 / T38 / sütun 5 / satır 6 |
| 2028 Tahmin | Sermaye Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 5 / satır 6,8 |
| 2028 Tahmin | Cari Transferler | Bütçe İçi | 1.675.208,00 | s.118 / T38 / sütun 5 / satır 5 |
| 2028 Tahmin | Cari Transferler | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 5 / satır 5,8 |
| 2028 Tahmin | Mal ve Hizmet Alım Giderleri | Bütçe İçi | 302.948.429,00 | s.118 / T38 / sütun 5 / satır 4 |
| 2028 Tahmin | Mal ve Hizmet Alım Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 5 / satır 4,8 |
| 2028 Tahmin | Personel Giderleri | Bütçe İçi | 55.000.000,00 | s.118 / T38 / sütun 5 / satır 2 |
| 2028 Tahmin | Personel Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 5 / satır 2,8 |
| 2028 Tahmin | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe İçi | 4.125.000,00 | s.118 / T38 / sütun 5 / satır 3 |
| 2028 Tahmin | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 5 / satır 3,8 |
| 2029 Tahmin | Sermaye Giderleri | Bütçe İçi | 2.223.750.000,00 | s.118 / T38 / sütun 6 / satır 6 |
| 2029 Tahmin | Sermaye Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 6 / satır 6,8 |
| 2029 Tahmin | Cari Transferler | Bütçe İçi | 2.070.000,00 | s.118 / T38 / sütun 6 / satır 5 |
| 2029 Tahmin | Cari Transferler | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 6 / satır 5,8 |
| 2029 Tahmin | Mal ve Hizmet Alım Giderleri | Bütçe İçi | 367.084.546,00 | s.118 / T38 / sütun 6 / satır 4 |
| 2029 Tahmin | Mal ve Hizmet Alım Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 6 / satır 4,8 |
| 2029 Tahmin | Personel Giderleri | Bütçe İçi | 68.750.000,00 | s.118 / T38 / sütun 6 / satır 2 |
| 2029 Tahmin | Personel Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 6 / satır 2,8 |
| 2029 Tahmin | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe İçi | 5.156.250,00 | s.118 / T38 / sütun 6 / satır 3 |
| 2029 Tahmin | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 6 / satır 3,8 |

### Yazı İşleri Müdürlüğü

50 doğrulama mesajında dağılım gereksinimi var; başka kitap nedeni de taşıyan mesajlar kitap sayımında bir kez sayılmıştır.

| Kart | Program / alt program | Grup |
| --- | --- | --- |
| 2027/1 | Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | Yönetim ve Destek |
| 2027/2 | Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | Yönetim ve Destek |
| 2027/3 | Yoksullukla Mücadele Ve Sosyal Yardımlaşma Programı / Sosyal Yardımlaşma | Hizmet |
| 2027/4 | Vatandaşlık ve Sivil Toplum Programı / Nüfus ve Vatandaşlık Hizmetleri | Hizmet |

| Yıl / sütun | Kategori | Finansman | Dağıtılacak tutar | Kaynak hücresi |
| --- | --- | --- | ---: | --- |
| 2026 Bütçe | Sermaye Giderleri | Bütçe İçi | 3.057.600,00 | s.227 / T180 / sütun 2 / satır 6 |
| 2026 Bütçe | Sermaye Giderleri | Bütçe Dışı | 0,00 | s.227 / T180 / sütun 2 / satır 6,8 |
| 2026 Bütçe | Cari Transferler | Bütçe İçi | 1.528.800,00 | s.227 / T180 / sütun 2 / satır 5 |
| 2026 Bütçe | Cari Transferler | Bütçe Dışı | 0,00 | s.227 / T180 / sütun 2 / satır 5,8 |
| 2026 Bütçe | Mal ve Hizmet Alım Giderleri | Bütçe İçi | 10.434.060,00 | s.227 / T180 / sütun 2 / satır 4 |
| 2026 Bütçe | Mal ve Hizmet Alım Giderleri | Bütçe Dışı | 0,00 | s.227 / T180 / sütun 2 / satır 4,8 |
| 2026 Bütçe | Personel Giderleri | Bütçe İçi | 16.976.137,00 | s.227 / T180 / sütun 2 / satır 2 |
| 2026 Bütçe | Personel Giderleri | Bütçe Dışı | 0,00 | s.227 / T180 / sütun 2 / satır 2,8 |
| 2026 Bütçe | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe İçi | 1.940.000,00 | s.227 / T180 / sütun 2 / satır 3 |
| 2026 Bütçe | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe Dışı | 0,00 | s.227 / T180 / sütun 2 / satır 3,8 |
| 2026 Haziran Sonu Harcama | Sermaye Giderleri | Bütçe İçi | 3.532.103,48 | s.227 / T180 / sütun 3 / satır 6 |
| 2026 Haziran Sonu Harcama | Sermaye Giderleri | Bütçe Dışı | 0,00 | s.227 / T180 / sütun 3 / satır 6,8 |
| 2026 Haziran Sonu Harcama | Cari Transferler | Bütçe İçi | 81.805,31 | s.227 / T180 / sütun 3 / satır 5 |
| 2026 Haziran Sonu Harcama | Cari Transferler | Bütçe Dışı | 0,00 | s.227 / T180 / sütun 3 / satır 5,8 |
| 2026 Haziran Sonu Harcama | Mal ve Hizmet Alım Giderleri | Bütçe İçi | 5.312.554,37 | s.227 / T180 / sütun 3 / satır 4 |
| 2026 Haziran Sonu Harcama | Mal ve Hizmet Alım Giderleri | Bütçe Dışı | 0,00 | s.227 / T180 / sütun 3 / satır 4,8 |
| 2026 Haziran Sonu Harcama | Personel Giderleri | Bütçe İçi | 8.836.228,24 | s.227 / T180 / sütun 3 / satır 2 |
| 2026 Haziran Sonu Harcama | Personel Giderleri | Bütçe Dışı | 0,00 | s.227 / T180 / sütun 3 / satır 2,8 |
| 2026 Haziran Sonu Harcama | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe İçi | 1.039.203,47 | s.227 / T180 / sütun 3 / satır 3 |
| 2026 Haziran Sonu Harcama | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe Dışı | 0,00 | s.227 / T180 / sütun 3 / satır 3,8 |
| 2027 Bütçe | Sermaye Giderleri | Bütçe İçi | 4.415.130,00 | s.227 / T180 / sütun 4 / satır 6 |
| 2027 Bütçe | Sermaye Giderleri | Bütçe Dışı | 0,00 | s.227 / T180 / sütun 4 / satır 6,8 |
| 2027 Bütçe | Cari Transferler | Bütçe İçi | 1.911.000,00 | s.227 / T180 / sütun 4 / satır 5 |
| 2027 Bütçe | Cari Transferler | Bütçe Dışı | 0,00 | s.227 / T180 / sütun 4 / satır 5,8 |
| 2027 Bütçe | Mal ve Hizmet Alım Giderleri | Bütçe İçi | 10.000.000,00 | s.227 / T180 / sütun 4 / satır 4 |
| 2027 Bütçe | Mal ve Hizmet Alım Giderleri | Bütçe Dışı | 0,00 | s.227 / T180 / sütun 4 / satır 4,8 |
| 2027 Bütçe | Personel Giderleri | Bütçe İçi | 21.700.000,00 | s.227 / T180 / sütun 4 / satır 2 |
| 2027 Bütçe | Personel Giderleri | Bütçe Dışı | 0,00 | s.227 / T180 / sütun 4 / satır 2,8 |
| 2027 Bütçe | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe İçi | 3.000.000,00 | s.227 / T180 / sütun 4 / satır 3 |
| 2027 Bütçe | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe Dışı | 0,00 | s.227 / T180 / sütun 4 / satır 3,8 |
| 2028 Tahmin | Sermaye Giderleri | Bütçe İçi | 5.077.400,00 | s.227 / T180 / sütun 5 / satır 6 |
| 2028 Tahmin | Sermaye Giderleri | Bütçe Dışı | 0,00 | s.227 / T180 / sütun 5 / satır 6,8 |
| 2028 Tahmin | Cari Transferler | Bütçe İçi | 2.197.650,00 | s.227 / T180 / sütun 5 / satır 5 |
| 2028 Tahmin | Cari Transferler | Bütçe Dışı | 0,00 | s.227 / T180 / sütun 5 / satır 5,8 |
| 2028 Tahmin | Mal ve Hizmet Alım Giderleri | Bütçe İçi | 14.073.382,00 | s.227 / T180 / sütun 5 / satır 4 |
| 2028 Tahmin | Mal ve Hizmet Alım Giderleri | Bütçe Dışı | 0,00 | s.227 / T180 / sütun 5 / satır 4,8 |
| 2028 Tahmin | Personel Giderleri | Bütçe İçi | 27.125.000,00 | s.227 / T180 / sütun 5 / satır 2 |
| 2028 Tahmin | Personel Giderleri | Bütçe Dışı | 0,00 | s.227 / T180 / sütun 5 / satır 2,8 |
| 2028 Tahmin | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe İçi | 3.757.000,00 | s.227 / T180 / sütun 5 / satır 3 |
| 2028 Tahmin | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe Dışı | 0,00 | s.227 / T180 / sütun 5 / satır 3,8 |
| 2029 Tahmin | Sermaye Giderleri | Bütçe İçi | 5.585.140,00 | s.227 / T180 / sütun 6 / satır 6 |
| 2029 Tahmin | Sermaye Giderleri | Bütçe Dışı | 0,00 | s.227 / T180 / sütun 6 / satır 6,8 |
| 2029 Tahmin | Cari Transferler | Bütçe İçi | 2.417.415,00 | s.227 / T180 / sütun 6 / satır 5 |
| 2029 Tahmin | Cari Transferler | Bütçe Dışı | 0,00 | s.227 / T180 / sütun 6 / satır 5,8 |
| 2029 Tahmin | Mal ve Hizmet Alım Giderleri | Bütçe İçi | 13.592.495,00 | s.227 / T180 / sütun 6 / satır 4 |
| 2029 Tahmin | Mal ve Hizmet Alım Giderleri | Bütçe Dışı | 0,00 | s.227 / T180 / sütun 6 / satır 4,8 |
| 2029 Tahmin | Personel Giderleri | Bütçe İçi | 33.906.250,00 | s.227 / T180 / sütun 6 / satır 2 |
| 2029 Tahmin | Personel Giderleri | Bütçe Dışı | 0,00 | s.227 / T180 / sütun 6 / satır 2,8 |
| 2029 Tahmin | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe İçi | 4.687.500,00 | s.227 / T180 / sütun 6 / satır 3 |
| 2029 Tahmin | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe Dışı | 0,00 | s.227 / T180 / sütun 6 / satır 3,8 |

### İnsan Kaynakları ve Eğitim Müdürlüğü

40 doğrulama mesajında dağılım gereksinimi var; başka kitap nedeni de taşıyan mesajlar kitap sayımında bir kez sayılmıştır.

| Kart | Program / alt program | Grup |
| --- | --- | --- |
| 2027/1 | Araştırma, Geliştirme ve Yenilik / Bilim, Teknoloji ve Yenilik Kültürü İle İnsan Kaynağının Geliştirilmesi | Hizmet |
| 2027/2 | Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | Yönetim ve Destek |

| Yıl / sütun | Kategori | Finansman | Dağıtılacak tutar | Kaynak hücresi |
| --- | --- | --- | ---: | --- |
| 2026 Bütçe | Cari Transferler | Bütçe İçi | 1.500.000,00 | s.203 / T144 / sütun 2 / satır 5 |
| 2026 Bütçe | Cari Transferler | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 2 / satır 5,7 |
| 2026 Bütçe | Mal ve Hizmet Alım Giderleri | Bütçe İçi | 7.600.000,00 | s.203 / T144 / sütun 2 / satır 4 |
| 2026 Bütçe | Mal ve Hizmet Alım Giderleri | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 2 / satır 4,7 |
| 2026 Bütçe | Personel Giderleri | Bütçe İçi | 15.364.541,00 | s.203 / T144 / sütun 2 / satır 2 |
| 2026 Bütçe | Personel Giderleri | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 2 / satır 2,7 |
| 2026 Bütçe | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe İçi | 1.800.000,00 | s.203 / T144 / sütun 2 / satır 3 |
| 2026 Bütçe | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 2 / satır 3,7 |
| 2026 Haziran Sonu Harcama | Cari Transferler | Bütçe İçi | 2.228.000,00 | s.203 / T144 / sütun 3 / satır 5 |
| 2026 Haziran Sonu Harcama | Cari Transferler | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 3 / satır 5,7 |
| 2026 Haziran Sonu Harcama | Mal ve Hizmet Alım Giderleri | Bütçe İçi | 2.435.619,92 | s.203 / T144 / sütun 3 / satır 4 |
| 2026 Haziran Sonu Harcama | Mal ve Hizmet Alım Giderleri | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 3 / satır 4,7 |
| 2026 Haziran Sonu Harcama | Personel Giderleri | Bütçe İçi | 13.287.541,43 | s.203 / T144 / sütun 3 / satır 2 |
| 2026 Haziran Sonu Harcama | Personel Giderleri | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 3 / satır 2,7 |
| 2026 Haziran Sonu Harcama | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe İçi | 859.945,87 | s.203 / T144 / sütun 3 / satır 3 |
| 2026 Haziran Sonu Harcama | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 3 / satır 3,7 |
| 2027 Bütçe | Cari Transferler | Bütçe İçi | 1.600.000,00 | s.203 / T144 / sütun 4 / satır 5 |
| 2027 Bütçe | Cari Transferler | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 4 / satır 5,7 |
| 2027 Bütçe | Mal ve Hizmet Alım Giderleri | Bütçe İçi | 8.400.000,00 | s.203 / T144 / sütun 4 / satır 4 |
| 2027 Bütçe | Mal ve Hizmet Alım Giderleri | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 4 / satır 4,7 |
| 2027 Bütçe | Personel Giderleri | Bütçe İçi | 19.306.000,00 | s.203 / T144 / sütun 4 / satır 2 |
| 2027 Bütçe | Personel Giderleri | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 4 / satır 2,7 |
| 2027 Bütçe | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe İçi | 2.100.000,00 | s.203 / T144 / sütun 4 / satır 3 |
| 2027 Bütçe | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 4 / satır 3,7 |
| 2028 Tahmin | Cari Transferler | Bütçe İçi | 1.700.000,00 | s.203 / T144 / sütun 5 / satır 5 |
| 2028 Tahmin | Cari Transferler | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 5 / satır 5,7 |
| 2028 Tahmin | Mal ve Hizmet Alım Giderleri | Bütçe İçi | 10.877.216,00 | s.203 / T144 / sütun 5 / satır 4 |
| 2028 Tahmin | Mal ve Hizmet Alım Giderleri | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 5 / satır 4,7 |
| 2028 Tahmin | Personel Giderleri | Bütçe İçi | 24.132.500,00 | s.203 / T144 / sütun 5 / satır 2 |
| 2028 Tahmin | Personel Giderleri | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 5 / satır 2,7 |
| 2028 Tahmin | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe İçi | 2.625.000,00 | s.203 / T144 / sütun 5 / satır 3 |
| 2028 Tahmin | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 5 / satır 3,7 |
| 2029 Tahmin | Cari Transferler | Bütçe İçi | 1.800.000,00 | s.203 / T144 / sütun 6 / satır 5 |
| 2029 Tahmin | Cari Transferler | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 6 / satır 5,7 |
| 2029 Tahmin | Mal ve Hizmet Alım Giderleri | Bütçe İçi | 9.981.840,00 | s.203 / T144 / sütun 6 / satır 4 |
| 2029 Tahmin | Mal ve Hizmet Alım Giderleri | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 6 / satır 4,7 |
| 2029 Tahmin | Personel Giderleri | Bütçe İçi | 30.165.625,00 | s.203 / T144 / sütun 6 / satır 2 |
| 2029 Tahmin | Personel Giderleri | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 6 / satır 2,7 |
| 2029 Tahmin | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe İçi | 3.281.250,00 | s.203 / T144 / sütun 6 / satır 3 |
| 2029 Tahmin | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 6 / satır 3,7 |

## Pazartesi — müdürlük bazında yalnız kitap düzeltme listesi

### Afet İşleri ve Risk Yönetimi Müdürlüğü

Gönderime hazır: **Hayır**; 12 kitap mesajı / 4 kitap kontrol maddesi.

- [ ] 0015.Kurum Personelinin Afet Eğitim Projesi · 2027 Bütçe

  **Hücreler:** s.144 / T69 / sütun 5 / satır 44,45,46

  Yapılacak: Bütçe Dışı hücresi boş. Bütçe dışı kaynak yoksa 0,00 yazın.

- [ ] 0015.Kurum Personelinin Afet Eğitim Projesi · 2028 Tahmin

  **Hücreler:** s.144 / T69 / sütun 6 / satır 44,45,46

  Yapılacak: Bütçe Dışı hücresi boş. Bütçe dışı kaynak yoksa 0,00 yazın.

- [ ] 0015.Kurum Personelinin Afet Eğitim Projesi · 2029 Tahmin

  **Hücreler:** s.144 / T69 / sütun 7 / satır 44,45,46

  Yapılacak: Bütçe Dışı hücresi boş. Bütçe dışı kaynak yoksa 0,00 yazın.

- [ ] Ekonomik tablo · 2026 Haziran Sonu Harcama

  **Hücreler:** s.144 / T70 / sütun 3 / satır 2,3,4,5,6,7

  Yapılacak: Kategori satırlarının toplamı 6.554.522,21, Bütçe İçi Toplam 5.091.250,40 (fark -1.463.271,81). Yanlış satırı veya toplamı düzeltin.

  Not: satır 2 (Personel Giderleri) toplamla aynı değeri taşıyor.


### Araştırma ve Geliştirme Müdürlüğü

Gönderime hazır: **Hayır**; 6 kitap mesajı / 1 kitap kontrol maddesi.

- [ ] Ekonomik tablo · 2026 Haziran Sonu Harcama

  **Hücreler:** s.195 / T134 / sütun 3 / satır 2,3,4,5,6,7

  Yapılacak: Kategori satırlarının toplamı 813.893,90, Bütçe İçi Toplam 832.400,90 (fark 18.507,00). Yanlış satırı veya toplamı düzeltin.


### Bilgi İşlem Müdürlüğü

Gönderime hazır: **Hayır**; 6 kitap mesajı / 3 kitap kontrol maddesi.

- [ ] Çapraz maliyet/toplam farkı · 2027

  **Hücreler:** s.207 / T147 / sütun 5 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.207 / T148 / sütun 4 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 267.575.845,00 + ortak personel/SGK 21.336.000,00 = 288.911.845,00 olmalı; ekonomik tablo toplamı 283.812.848,00 (fark -5.098.997,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 267.575.845,00, ekonomik personel/SGK hariç toplam 262.476.848,00 (fark -5.098.997,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Çapraz maliyet/toplam farkı · 2028

  **Hücreler:** s.207 / T147 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.207 / T148 / sütun 5 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 454.155.140,00 + ortak personel/SGK 26.670.000,00 = 480.825.140,00 olmalı; ekonomik tablo toplamı 480.825.142,00 (fark 2,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 454.155.140,00, ekonomik personel/SGK hariç toplam 454.155.142,00 (fark 2,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Çapraz maliyet/toplam farkı · 2029

  **Hücreler:** s.207 / T147 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.207 / T148 / sütun 6 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 777.302.765,00 + ortak personel/SGK 33.337.500,00 = 810.640.265,00 olmalı; ekonomik tablo toplamı 810.640.269,00 (fark 4,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 777.302.765,00, ekonomik personel/SGK hariç toplam 777.302.769,00 (fark 4,00). İki tabloda bu finansman tutarları eşit olmalı.


### Çevre Koruma ve Kontrol Müdürlüğü

Gönderime hazır: **Hayır**; 6 kitap mesajı / 1 kitap kontrol maddesi.

- [ ] Ekonomik tablo · 2026 Haziran Sonu Harcama

  **Hücreler:** s.153 / T78 / sütun 3 / satır 2,3,4,5,6,7

  Yapılacak: Kategori satırlarının toplamı 4.085.221,72, Bütçe İçi Toplam 3.967.964,02 (fark -117.257,70). Yanlış satırı veya toplamı düzeltin.

  Not: satır 2 (Personel Giderleri) toplamla aynı değeri taşıyor.


### Destek Hizmetleri Müdürlüğü

Gönderime hazır: **Hayır**; 3 kitap mesajı / 3 kitap kontrol maddesi.

- [ ] 0007.İhtiyaç duyulan malzeme, ekipman ve hizmet alımlarının yasalara uygun, şeffaf ve rekabetçi bir şekilde gerçekleştirmek · 2026 Bütçe

  **Hücreler:** s.218 / T165 / sütun 2 / satır 20,21,22

  Yapılacak: s.218, tablo 165, satır 20, sütun 2; s.218, tablo 165, satır 21, sütun 2; s.218, tablo 165, satır 22, sütun 2: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0007.İhtiyaç duyulan malzeme, ekipman ve hizmet alımlarının yasalara uygun, şeffaf ve rekabetçi bir şekilde gerçekleştirmek · 2026 Haziran Sonu Harcama

  **Hücreler:** s.218 / T165 / sütun 3 / satır 20,21,22

  Yapılacak: s.218, tablo 165, satır 20, sütun 3; s.218, tablo 165, satır 21, sütun 3; s.218, tablo 165, satır 22, sütun 3: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0007.İhtiyaç duyulan malzeme, ekipman ve hizmet alımlarının yasalara uygun, şeffaf ve rekabetçi bir şekilde gerçekleştirmek · 2026 Yıl Sonu Tahmini

  **Hücreler:** s.218 / T165 / sütun 4 / satır 20,21,22

  Yapılacak: s.218, tablo 165, satır 20, sütun 4; s.218, tablo 165, satır 21, sütun 4; s.218, tablo 165, satır 22, sütun 4: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.


### Dış İlişkiler Müdürlüğü

Gönderime hazır: **Hayır**; 9 kitap mesajı / 6 kitap kontrol maddesi.

- [ ] Çapraz maliyet/toplam farkı · 2027

  **Hücreler:** s.186 / T119 / sütun 5 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.186 / T120 / sütun 4 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 4.039.548,00 + ortak personel/SGK 1.475.000,00 = 5.514.548,00 olmalı; ekonomik tablo toplamı 6.514.548,00 (fark 1.000.000,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 4.039.548,00, ekonomik personel/SGK hariç toplam 5.039.548,00 (fark 1.000.000,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Çapraz maliyet/toplam farkı · 2028

  **Hücreler:** s.186 / T119 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.186 / T120 / sütun 5 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 4.570.481,00 + ortak personel/SGK 1.843.750,00 = 6.414.231,00 olmalı; ekonomik tablo toplamı 7.414.231,00 (fark 1.000.000,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 4.570.481,00, ekonomik personel/SGK hariç toplam 5.570.481,00 (fark 1.000.000,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Çapraz maliyet/toplam farkı · 2029

  **Hücreler:** s.186 / T119 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.186 / T120 / sütun 6 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 4.605.000,00 + ortak personel/SGK 2.304.688,00 = 6.909.688,00 olmalı; ekonomik tablo toplamı 8.009.688,00 (fark 1.100.000,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 4.605.000,00, ekonomik personel/SGK hariç toplam 5.705.000,00 (fark 1.100.000,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] 0006.Uluslararası kuruluşlar ve belediye ağları ile kurumsal ilişkilerin sürdürülmesi · 2026 Bütçe

  **Hücreler:** s.186 / T119 / sütun 2 / satır 17,18,19

  Yapılacak: s.186, tablo 119, satır 17, sütun 2; s.186, tablo 119, satır 18, sütun 2; s.186, tablo 119, satır 19, sütun 2: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0006.Uluslararası kuruluşlar ve belediye ağları ile kurumsal ilişkilerin sürdürülmesi · 2026 Haziran Sonu Harcama

  **Hücreler:** s.186 / T119 / sütun 3 / satır 17,18,19

  Yapılacak: s.186, tablo 119, satır 17, sütun 3; s.186, tablo 119, satır 18, sütun 3; s.186, tablo 119, satır 19, sütun 3: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0006.Uluslararası kuruluşlar ve belediye ağları ile kurumsal ilişkilerin sürdürülmesi · 2026 Yıl Sonu Tahmini

  **Hücreler:** s.186 / T119 / sütun 4 / satır 17,18,19

  Yapılacak: s.186, tablo 119, satır 17, sütun 4; s.186, tablo 119, satır 18, sütun 4; s.186, tablo 119, satır 19, sütun 4: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.


### Emlak İstimlak Müdürlüğü

Gönderime hazır: **Hayır**; 16 kitap mesajı / 4 kitap kontrol maddesi.

- [ ] 0005.4734 sayılı yasa kapsamında mal ve/veya hizmet alımı ihale işlemlerinin yapılması · 2027 Bütçe

  **Hücreler:** s.112 / T29 / sütun 5 / satır 14,15,16

  Yapılacak: Bütçe Dışı hücresi boş. Bütçe dışı kaynak yoksa 0,00 yazın.

- [ ] 0005.4734 sayılı yasa kapsamında mal ve/veya hizmet alımı ihale işlemlerinin yapılması · 2028 Tahmin

  **Hücreler:** s.112 / T29 / sütun 6 / satır 14,15,16

  Yapılacak: Bütçe Dışı hücresi boş. Bütçe dışı kaynak yoksa 0,00 yazın.

- [ ] 0005.4734 sayılı yasa kapsamında mal ve/veya hizmet alımı ihale işlemlerinin yapılması · 2029 Tahmin

  **Hücreler:** s.112 / T29 / sütun 7 / satır 14,15,16

  Yapılacak: Bütçe Dışı hücresi boş. Bütçe dışı kaynak yoksa 0,00 yazın.

- [ ] Ekonomik tablo · 2026 Haziran Sonu Harcama

  **Hücreler:** s.112 / T30 / sütun 3 / satır 2,3,4,5,6,7,8,9

  Yapılacak: Kategori satırlarının toplamı 113.787.163,62, Bütçe İçi Toplam 113.352.771,64 (fark -434.391,98). Yanlış satırı veya toplamı düzeltin.


### Etüd Proje Müdürlüğü

Gönderime hazır: **Hayır**; 1 kitap mesajı / 1 kitap kontrol maddesi.

- [ ] 0010.Tüm bölgede, Sigara İçme Alanı talep ve başvurularının değerlendirilerek sonuçlandırılması (102 adet) · 2028 Tahmin

  **Hücreler:** s.133 / T55 / sütun 6 / satır 29,30,31

  Yapılacak: s.133, tablo 55, satır 29, sütun 6; s.133, tablo 55, satır 30, sütun 6; s.133, tablo 55, satır 31, sütun 6: Toplam hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.


### Fen İşleri Müdürlüğü

Gönderime hazır: **Hayır**; 14 kitap mesajı / 3 kitap kontrol maddesi.

- [ ] Çapraz maliyet/toplam farkı · 2028

  **Hücreler:** s.118 / T37 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,32; s.118 / T38 / sütun 5 / satır 2,3,4,5,6,7,8,9

  Yapılacak: Faaliyet maliyetleri toplamı 2.021.870.002,00 + ortak personel/SGK 59.125.000,00 = 2.080.995.002,00 olmalı; ekonomik tablo toplamı 2.223.048.637,00 (fark 142.053.635,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 2.021.870.002,00, ekonomik personel/SGK hariç toplam 2.163.923.637,00 (fark 142.053.635,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Çapraz maliyet/toplam farkı · 2029

  **Hücreler:** s.118 / T37 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,32; s.118 / T38 / sütun 6 / satır 2,3,4,5,6,7,8,9

  Yapılacak: Faaliyet maliyetleri toplamı 2.493.022.422,00 + ortak personel/SGK 73.906.250,00 = 2.566.928.672,00 olmalı; ekonomik tablo toplamı 2.666.810.796,00 (fark 99.882.124,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 2.493.022.422,00, ekonomik personel/SGK hariç toplam 2.592.904.546,00 (fark 99.882.124,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Ekonomik tablo · 2026 Bütçe

  **Hücreler:** s.118 / T38 / sütun 2 / satır 2,3,4,5,6,7,8,9

  Yapılacak: Kategori satırlarının toplamı 949.340.000,00, Bütçe İçi Toplam 950.000.000,00 (fark 660.000,00). Yanlış satırı veya toplamı düzeltin.


### Gelirler Müdürlüğü

Gönderime hazır: **Hayır**; 25 kitap mesajı / 8 kitap kontrol maddesi.

- [ ] Çapraz maliyet/toplam farkı · 2027

  **Hücreler:** s.234 / T189 / sütun 5 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,50; s.234 / T190 / sütun 4 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 83.400.000,00 + ortak personel/SGK 81.910.000,00 = 165.310.000,00 olmalı; ekonomik tablo toplamı 162.322.500,00 (fark -2.987.500,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 83.400.000,00, ekonomik personel/SGK hariç toplam 80.412.500,00 (fark -2.987.500,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Çapraz maliyet/toplam farkı · 2028

  **Hücreler:** s.234 / T189 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,50; s.234 / T190 / sütun 5 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 104.272.200,00 + ortak personel/SGK 102.387.500,00 = 206.659.700,00 olmalı; ekonomik tablo toplamı 204.036.734,00 (fark -2.622.966,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 104.272.200,00, ekonomik personel/SGK hariç toplam 101.649.234,00 (fark -2.622.966,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Çapraz maliyet/toplam farkı · 2029

  **Hücreler:** s.234 / T189 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,50; s.234 / T190 / sütun 6 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 121.674.592,00 + ortak personel/SGK 127.984.375,00 = 249.658.967,00 olmalı; ekonomik tablo toplamı 235.437.102,00 (fark -14.221.865,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 121.674.592,00, ekonomik personel/SGK hariç toplam 107.452.727,00 (fark -14.221.865,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Ekonomik tablo · 2026 Bütçe

  **Hücreler:** s.234 / T190 / sütun 2 / satır 2,3,4,5,6,7,8

  Yapılacak: Kategori satırlarının toplamı 132.225.430,00, Bütçe İçi Toplam 130.725.430,00 (fark -1.500.000,00). Yanlış satırı veya toplamı düzeltin.

- [ ] Ekonomik tablo · 2026 Haziran Sonu Harcama

  **Hücreler:** s.234 / T190 / sütun 3 / satır 2,3,4,5,6,7,8

  Yapılacak: Kategori satırlarının toplamı 52.551.283,13, Bütçe İçi Toplam 52.551.283,30 (fark 0,17). Yanlış satırı veya toplamı düzeltin.

- [ ] 0015.Vergi beyannameleri, müşavirlik, eğitim vb. çeşitli ödemeleri zamanında eksiksiz ve tam olarak yürütmek. · 2026 Bütçe

  **Hücreler:** s.234 / T189 / sütun 2 / satır 44,45,46

  Yapılacak: s.234, tablo 189, satır 44, sütun 2; s.234, tablo 189, satır 45, sütun 2; s.234, tablo 189, satır 46, sütun 2: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0015.Vergi beyannameleri, müşavirlik, eğitim vb. çeşitli ödemeleri zamanında eksiksiz ve tam olarak yürütmek. · 2026 Haziran Sonu Harcama

  **Hücreler:** s.234 / T189 / sütun 3 / satır 44,45,46

  Yapılacak: s.234, tablo 189, satır 44, sütun 3; s.234, tablo 189, satır 45, sütun 3; s.234, tablo 189, satır 46, sütun 3: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0015.Vergi beyannameleri, müşavirlik, eğitim vb. çeşitli ödemeleri zamanında eksiksiz ve tam olarak yürütmek. · 2026 Yıl Sonu Tahmini

  **Hücreler:** s.234 / T189 / sütun 4 / satır 44,45,46

  Yapılacak: s.234, tablo 189, satır 44, sütun 4; s.234, tablo 189, satır 45, sütun 4; s.234, tablo 189, satır 46, sütun 4: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.


### Gençlik ve Spor İşleri Müdürlüğü

Gönderime hazır: **Hayır**; 20 kitap mesajı / 4 kitap kontrol maddesi.

- [ ] Çapraz maliyet/toplam farkı · 2028

  **Hücreler:** s.173 / T105 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.173 / T106 / sütun 5 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 77.148.000,00 + ortak personel/SGK 8.661.250,00 = 85.809.250,00 olmalı; ekonomik tablo toplamı 89.807.672,00 (fark 3.998.422,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 77.148.000,00, ekonomik personel/SGK hariç toplam 81.146.422,00 (fark 3.998.422,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Çapraz maliyet/toplam farkı · 2029

  **Hücreler:** s.173 / T105 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.173 / T106 / sütun 6 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 88.367.100,00 + ortak personel/SGK 10.826.563,00 = 99.193.663,00 olmalı; ekonomik tablo toplamı 102.973.097,00 (fark 3.779.434,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 88.367.100,00, ekonomik personel/SGK hariç toplam 92.146.534,00 (fark 3.779.434,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Ekonomik tablo · 2026 Haziran Sonu Harcama

  **Hücreler:** s.173 / T106 / sütun 3 / satır 2,3,4,5,6,7,8

  Yapılacak: Kategori satırlarının toplamı 16.195.121,93, Bütçe İçi Toplam 15.375.121,93 (fark -820.000,00). Yanlış satırı veya toplamı düzeltin.

- [ ] Ekonomik tablo · 2028 Tahmin

  **Hücreler:** s.173 / T106 / sütun 5 / satır 2,3,4,5,6,7,8

  Yapılacak: Kategori satırlarının toplamı 89.807.672,00, Bütçe İçi Toplam 89.807.692,00 (fark 20,00). Yanlış satırı veya toplamı düzeltin.


### Halkla İlişkiler Müdürlüğü

Gönderime hazır: **Hayır**; 10 kitap mesajı / 2 kitap kontrol maddesi.

- [ ] Çapraz maliyet/toplam farkı · 2028

  **Hücreler:** s.192 / T129 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.192 / T130 / sütun 5 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 60.269.674,00 + ortak personel/SGK 34.815.579,00 = 95.085.253,00 olmalı; ekonomik tablo toplamı 94.835.253,00 (fark -250.000,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 60.269.674,00, ekonomik personel/SGK hariç toplam 60.019.674,00 (fark -250.000,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Ekonomik tablo · 2026 Haziran Sonu Harcama

  **Hücreler:** s.192 / T130 / sütun 3 / satır 2,3,4,5,6,7,8

  Yapılacak: Kategori satırlarının toplamı 18.477.280,34, Bütçe İçi Toplam 18.478.993,34 (fark 1.713,00). Yanlış satırı veya toplamı düzeltin.


### Hukuk İşleri Müdürlüğü

Gönderime hazır: **Evet**; 0 kitap mesajı / 0 kitap kontrol maddesi.

Kitap düzeltmesi yok.

### İklim Değişikliği ve Sıfır Atık Müdürlüğü

Gönderime hazır: **Evet**; 0 kitap mesajı / 0 kitap kontrol maddesi.

Kitap düzeltmesi yok.

### İmar ve Şehircilik Müdürlüğü

Gönderime hazır: **Hayır**; 6 kitap mesajı / 1 kitap kontrol maddesi.

- [ ] Ekonomik tablo · 2026 Bütçe

  **Hücreler:** s.122 / T44 / sütun 2 / satır 2,3,4,5,6,7

  Yapılacak: Bütçe Dışı hücresi boş. Bütçe dışı kaynak yoksa 0,00 yazın.


### İnsan Kaynakları ve Eğitim Müdürlüğü

Gönderime hazır: **Hayır**; 10 kitap mesajı / 2 kitap kontrol maddesi.

- [ ] Çapraz maliyet/toplam farkı · 2028

  **Hücreler:** s.203 / T143 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.203 / T144 / sütun 5 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 12.577.220,00 + ortak personel/SGK 26.757.500,00 = 39.334.720,00 olmalı; ekonomik tablo toplamı 39.334.716,00 (fark -4,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 12.577.220,00, ekonomik personel/SGK hariç toplam 12.577.216,00 (fark -4,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Ekonomik tablo · 2026 Haziran Sonu Harcama

  **Hücreler:** s.203 / T144 / sütun 3 / satır 2,3,4,5,6,7,8

  Yapılacak: Kategori satırlarının toplamı 18.811.107,22, Bütçe İçi Toplam 13.287.541,43 (fark -5.523.565,79). Yanlış satırı veya toplamı düzeltin.

  Not: satır 2 (Personel Giderleri) toplamla aynı değeri taşıyor.


### Kentsel Dönüşüm Müdürlüğü

Gönderime hazır: **Hayır**; 6 kitap mesajı / 1 kitap kontrol maddesi.

- [ ] Ekonomik tablo · 2026 Haziran Sonu Harcama

  **Hücreler:** s.139 / T64 / sütun 3 / satır 2,3,4,5,6,7

  Yapılacak: Kategori satırlarının toplamı 5.124.271,48, Bütçe İçi Toplam 4.920.160,55 (fark -204.110,93). Yanlış satırı veya toplamı düzeltin.

  Not: satır 2 (Personel Giderleri) toplamla aynı değeri taşıyor.


### Kültür, Sanat ve Sosyal İşler Müdürlüğü

Gönderime hazır: **Hayır**; 57 kitap mesajı / 51 kitap kontrol maddesi.

- [ ] 0003.İş Birliği ve Ortaklıklar: Öğretim Kurumları, teknoloji transfer ofisleri, sivil toplum kuruluşları ve özel sektörle iş birliği yapmak. · 2028 Tahmin

  **Hücreler:** s.167 / T99 / sütun 6 / satır 8,9,10

  Yapılacak: Toplam = Bütçe İçi + Bütçe Dışı olmalı: 3.825.000,00 + 0,00 = 3.825.000,00, kitapta 4.912.500,00 yazıyor (fark 1.087.500,00). Yanlış hücreyi düzeltin.

- [ ] 0003.İş Birliği ve Ortaklıklar: Öğretim Kurumları, teknoloji transfer ofisleri, sivil toplum kuruluşları ve özel sektörle iş birliği yapmak. · 2029 Tahmin

  **Hücreler:** s.167 / T99 / sütun 7 / satır 8,9,10

  Yapılacak: Toplam = Bütçe İçi + Bütçe Dışı olmalı: 3.825.000,00 + 0,00 = 3.825.000,00, kitapta 6.215.625,00 yazıyor (fark 2.390.625,00). Yanlış hücreyi düzeltin.

- [ ] 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek. · 2028 Tahmin

  **Hücreler:** s.167 / T99 / sütun 6 / satır 47,48,49

  Yapılacak: Toplam = Bütçe İçi + Bütçe Dışı olmalı: 1.775.000,00 + 0,00 = 1.775.000,00, kitapta 32.373.570,00 yazıyor (fark 30.598.570,00). Yanlış hücreyi düzeltin.

- [ ] 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek. · 2029 Tahmin

  **Hücreler:** s.167 / T99 / sütun 7 / satır 47,48,49

  Yapılacak: Toplam = Bütçe İçi + Bütçe Dışı olmalı: 1.976.250,00 + 0,00 = 1.976.250,00, kitapta 46.275.725,00 yazıyor (fark 44.299.475,00). Yanlış hücreyi düzeltin.

- [ ] 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak. · 2028 Tahmin

  **Hücreler:** s.167 / T99 / sütun 6 / satır 20,21,22

  Yapılacak: s.167, tablo 99, satır 20, sütun 6; s.167, tablo 99, satır 21, sütun 6; s.167, tablo 99, satır 22, sütun 6: Bütçe İçi hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak. · 2029 Tahmin

  **Hücreler:** s.167 / T99 / sütun 7 / satır 20,21,22

  Yapılacak: s.167, tablo 99, satır 20, sütun 7; s.167, tablo 99, satır 21, sütun 7; s.167, tablo 99, satır 22, sütun 7: Bütçe İçi hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0015.Örgün Eğitime Destek ve Sınavlara Hazırlık Kursları: Dezavantajlı bölgelerde yaşayan öğrenciler için örgün eğitimlerine destek ve sınavlara hazırlık kursları düzenlemek.

  **Hücreler:** s.167 / T99 / sütun 1 / satır 44,58,90

  Yapılacak: Bu faaliyetin açıklama metnini 'Faaliyetlere İlişkin Açıklamalar' bölümüne ekleyin.

- [ ] 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek.

  **Hücreler:** s.167 / T99 / sütun 1 / satır 47,58,90

  Yapılacak: Bu faaliyetin açıklama metnini 'Faaliyetlere İlişkin Açıklamalar' bölümüne ekleyin.

- [ ] 0017. Sanatsal Eğitimler: El sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında gösteriler ve yaz okulları düzenleme.

  **Hücreler:** s.167 / T99 / sütun 1 / satır 50,58,90

  Yapılacak: Bu faaliyetin açıklama metnini 'Faaliyetlere İlişkin Açıklamalar' bölümüne ekleyin.

- [ ] 0004.Ulusal ve Uluslararası Etkinlikler: Ulusal ve uluslararası festivaller, fuarlar ve etkinliklere katılım ve düzenleme. · 2026 Bütçe

  **Hücreler:** s.167 / T99 / sütun 2 / satır 11,12,13

  Yapılacak: s.167, tablo 99, satır 11, sütun 2; s.167, tablo 99, satır 12, sütun 2; s.167, tablo 99, satır 13, sütun 2: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0004.Ulusal ve Uluslararası Etkinlikler: Ulusal ve uluslararası festivaller, fuarlar ve etkinliklere katılım ve düzenleme. · 2026 Haziran Sonu Harcama

  **Hücreler:** s.167 / T99 / sütun 3 / satır 11,12,13

  Yapılacak: s.167, tablo 99, satır 11, sütun 3; s.167, tablo 99, satır 12, sütun 3; s.167, tablo 99, satır 13, sütun 3: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0004.Ulusal ve Uluslararası Etkinlikler: Ulusal ve uluslararası festivaller, fuarlar ve etkinliklere katılım ve düzenleme. · 2026 Yıl Sonu Tahmini

  **Hücreler:** s.167 / T99 / sütun 4 / satır 11,12,13

  Yapılacak: s.167, tablo 99, satır 11, sütun 4; s.167, tablo 99, satır 12, sütun 4; s.167, tablo 99, satır 13, sütun 4: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0005.Sanatsal Eğitimler: Sahne sanatları eğitimleri, el sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında atölye, çalıştay ve gösteriler düzenleme. · 2026 Bütçe

  **Hücreler:** s.167 / T99 / sütun 2 / satır 14,15,16

  Yapılacak: s.167, tablo 99, satır 14, sütun 2; s.167, tablo 99, satır 15, sütun 2; s.167, tablo 99, satır 16, sütun 2: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0005.Sanatsal Eğitimler: Sahne sanatları eğitimleri, el sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında atölye, çalıştay ve gösteriler düzenleme. · 2026 Haziran Sonu Harcama

  **Hücreler:** s.167 / T99 / sütun 3 / satır 14,15,16

  Yapılacak: s.167, tablo 99, satır 14, sütun 3; s.167, tablo 99, satır 15, sütun 3; s.167, tablo 99, satır 16, sütun 3: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0005.Sanatsal Eğitimler: Sahne sanatları eğitimleri, el sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında atölye, çalıştay ve gösteriler düzenleme. · 2026 Yıl Sonu Tahmini

  **Hücreler:** s.167 / T99 / sütun 4 / satır 14,15,16

  Yapılacak: s.167, tablo 99, satır 14, sütun 4; s.167, tablo 99, satır 15, sütun 4; s.167, tablo 99, satır 16, sütun 4: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0006.Sanatsal Etkinlikler: Kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kültür Park, Büyükçekmece Kordon ve Albatros sahili) · 2026 Bütçe

  **Hücreler:** s.167 / T99 / sütun 2 / satır 17,18,19

  Yapılacak: s.167, tablo 99, satır 17, sütun 2; s.167, tablo 99, satır 18, sütun 2; s.167, tablo 99, satır 19, sütun 2: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0006.Sanatsal Etkinlikler: Kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kültür Park, Büyükçekmece Kordon ve Albatros sahili) · 2026 Haziran Sonu Harcama

  **Hücreler:** s.167 / T99 / sütun 3 / satır 17,18,19

  Yapılacak: s.167, tablo 99, satır 17, sütun 3; s.167, tablo 99, satır 18, sütun 3; s.167, tablo 99, satır 19, sütun 3: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0006.Sanatsal Etkinlikler: Kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kültür Park, Büyükçekmece Kordon ve Albatros sahili) · 2026 Yıl Sonu Tahmini

  **Hücreler:** s.167 / T99 / sütun 4 / satır 17,18,19

  Yapılacak: s.167, tablo 99, satır 17, sütun 4; s.167, tablo 99, satır 18, sütun 4; s.167, tablo 99, satır 19, sütun 4: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak. · 2026 Bütçe

  **Hücreler:** s.167 / T99 / sütun 2 / satır 20,21,22

  Yapılacak: s.167, tablo 99, satır 20, sütun 2; s.167, tablo 99, satır 21, sütun 2; s.167, tablo 99, satır 22, sütun 2: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak. · 2026 Haziran Sonu Harcama

  **Hücreler:** s.167 / T99 / sütun 3 / satır 20,21,22

  Yapılacak: s.167, tablo 99, satır 20, sütun 3; s.167, tablo 99, satır 21, sütun 3; s.167, tablo 99, satır 22, sütun 3: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak. · 2026 Yıl Sonu Tahmini

  **Hücreler:** s.167 / T99 / sütun 4 / satır 20,21,22

  Yapılacak: s.167, tablo 99, satır 20, sütun 4; s.167, tablo 99, satır 21, sütun 4; s.167, tablo 99, satır 22, sütun 4: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0008.Toplumsal Etkinlikler: Önemli gün ve bayramlarda etkinlikler düzenlemek · 2026 Bütçe

  **Hücreler:** s.167 / T99 / sütun 2 / satır 23,24,25

  Yapılacak: s.167, tablo 99, satır 23, sütun 2; s.167, tablo 99, satır 24, sütun 2; s.167, tablo 99, satır 25, sütun 2: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0008.Toplumsal Etkinlikler: Önemli gün ve bayramlarda etkinlikler düzenlemek · 2026 Haziran Sonu Harcama

  **Hücreler:** s.167 / T99 / sütun 3 / satır 23,24,25

  Yapılacak: s.167, tablo 99, satır 23, sütun 3; s.167, tablo 99, satır 24, sütun 3; s.167, tablo 99, satır 25, sütun 3: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0008.Toplumsal Etkinlikler: Önemli gün ve bayramlarda etkinlikler düzenlemek · 2026 Yıl Sonu Tahmini

  **Hücreler:** s.167 / T99 / sütun 4 / satır 23,24,25

  Yapılacak: s.167, tablo 99, satır 23, sütun 4; s.167, tablo 99, satır 24, sütun 4; s.167, tablo 99, satır 25, sütun 4: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0009.Sanatsal Etkinlikler: Marmara Denizi kıyısında kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kıyı Marina ve Albatros sahili) · 2026 Bütçe

  **Hücreler:** s.167 / T99 / sütun 2 / satır 26,27,28

  Yapılacak: s.167, tablo 99, satır 26, sütun 2; s.167, tablo 99, satır 27, sütun 2; s.167, tablo 99, satır 28, sütun 2: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0009.Sanatsal Etkinlikler: Marmara Denizi kıyısında kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kıyı Marina ve Albatros sahili) · 2026 Haziran Sonu Harcama

  **Hücreler:** s.167 / T99 / sütun 3 / satır 26,27,28

  Yapılacak: s.167, tablo 99, satır 26, sütun 3; s.167, tablo 99, satır 27, sütun 3; s.167, tablo 99, satır 28, sütun 3: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0009.Sanatsal Etkinlikler: Marmara Denizi kıyısında kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kıyı Marina ve Albatros sahili) · 2026 Yıl Sonu Tahmini

  **Hücreler:** s.167 / T99 / sütun 4 / satır 26,27,28

  Yapılacak: s.167, tablo 99, satır 26, sütun 4; s.167, tablo 99, satır 27, sütun 4; s.167, tablo 99, satır 28, sütun 4: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0010.Kent Tiyatroları Sezon Programı: Her yaş grubu için yıl boyunca düzenli tiyatro oyunlarının sergilenmesi · 2026 Bütçe

  **Hücreler:** s.167 / T99 / sütun 2 / satır 29,30,31

  Yapılacak: s.167, tablo 99, satır 29, sütun 2; s.167, tablo 99, satır 30, sütun 2; s.167, tablo 99, satır 31, sütun 2: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0010.Kent Tiyatroları Sezon Programı: Her yaş grubu için yıl boyunca düzenli tiyatro oyunlarının sergilenmesi · 2026 Haziran Sonu Harcama

  **Hücreler:** s.167 / T99 / sütun 3 / satır 29,30,31

  Yapılacak: s.167, tablo 99, satır 29, sütun 3; s.167, tablo 99, satır 30, sütun 3; s.167, tablo 99, satır 31, sütun 3: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0010.Kent Tiyatroları Sezon Programı: Her yaş grubu için yıl boyunca düzenli tiyatro oyunlarının sergilenmesi · 2026 Yıl Sonu Tahmini

  **Hücreler:** s.167 / T99 / sütun 4 / satır 29,30,31

  Yapılacak: s.167, tablo 99, satır 29, sütun 4; s.167, tablo 99, satır 30, sütun 4; s.167, tablo 99, satır 31, sütun 4: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0011.Okullara Yönelik Rehberli Müze Turları: İlçemizdeki okullarla iş birliği içerisinde yürütülen rehberli müze gezileri · 2026 Bütçe

  **Hücreler:** s.167 / T99 / sütun 2 / satır 32,33,34

  Yapılacak: s.167, tablo 99, satır 32, sütun 2; s.167, tablo 99, satır 33, sütun 2; s.167, tablo 99, satır 34, sütun 2: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0011.Okullara Yönelik Rehberli Müze Turları: İlçemizdeki okullarla iş birliği içerisinde yürütülen rehberli müze gezileri · 2026 Haziran Sonu Harcama

  **Hücreler:** s.167 / T99 / sütun 3 / satır 32,33,34

  Yapılacak: s.167, tablo 99, satır 32, sütun 3; s.167, tablo 99, satır 33, sütun 3; s.167, tablo 99, satır 34, sütun 3: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0011.Okullara Yönelik Rehberli Müze Turları: İlçemizdeki okullarla iş birliği içerisinde yürütülen rehberli müze gezileri · 2026 Yıl Sonu Tahmini

  **Hücreler:** s.167 / T99 / sütun 4 / satır 32,33,34

  Yapılacak: s.167, tablo 99, satır 32, sütun 4; s.167, tablo 99, satır 33, sütun 4; s.167, tablo 99, satır 34, sütun 4: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0012.Atölye Çalışmaları: Çocuk, Genç ve yetişkinlere yönelik atölye çalışmaları · 2026 Bütçe

  **Hücreler:** s.167 / T99 / sütun 2 / satır 35,36,37

  Yapılacak: s.167, tablo 99, satır 35, sütun 2; s.167, tablo 99, satır 36, sütun 2; s.167, tablo 99, satır 37, sütun 2: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0012.Atölye Çalışmaları: Çocuk, Genç ve yetişkinlere yönelik atölye çalışmaları · 2026 Haziran Sonu Harcama

  **Hücreler:** s.167 / T99 / sütun 3 / satır 35,36,37

  Yapılacak: s.167, tablo 99, satır 35, sütun 3; s.167, tablo 99, satır 36, sütun 3; s.167, tablo 99, satır 37, sütun 3: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0012.Atölye Çalışmaları: Çocuk, Genç ve yetişkinlere yönelik atölye çalışmaları · 2026 Yıl Sonu Tahmini

  **Hücreler:** s.167 / T99 / sütun 4 / satır 35,36,37

  Yapılacak: s.167, tablo 99, satır 35, sütun 4; s.167, tablo 99, satır 36, sütun 4; s.167, tablo 99, satır 37, sütun 4: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0013.Meslek Kursları: Yabancı dil eğitimleri, teknoloji eğitimleri, güzellik hizmetleri eğitimleri, mutfak sanatları eğitimleri vb. kurslar düzenlemek. · 2026 Bütçe

  **Hücreler:** s.167 / T99 / sütun 2 / satır 38,39,40

  Yapılacak: s.167, tablo 99, satır 38, sütun 2; s.167, tablo 99, satır 39, sütun 2; s.167, tablo 99, satır 40, sütun 2: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0013.Meslek Kursları: Yabancı dil eğitimleri, teknoloji eğitimleri, güzellik hizmetleri eğitimleri, mutfak sanatları eğitimleri vb. kurslar düzenlemek. · 2026 Haziran Sonu Harcama

  **Hücreler:** s.167 / T99 / sütun 3 / satır 38,39,40

  Yapılacak: s.167, tablo 99, satır 38, sütun 3; s.167, tablo 99, satır 39, sütun 3; s.167, tablo 99, satır 40, sütun 3: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0013.Meslek Kursları: Yabancı dil eğitimleri, teknoloji eğitimleri, güzellik hizmetleri eğitimleri, mutfak sanatları eğitimleri vb. kurslar düzenlemek. · 2026 Yıl Sonu Tahmini

  **Hücreler:** s.167 / T99 / sütun 4 / satır 38,39,40

  Yapılacak: s.167, tablo 99, satır 38, sütun 4; s.167, tablo 99, satır 39, sütun 4; s.167, tablo 99, satır 40, sütun 4: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0014.Sahne Sanatları Kursları: Türk Halk Oyunları, modern dans, bale, tiyatro, enstrüman vb. kurslar düzenlemek. · 2026 Bütçe

  **Hücreler:** s.167 / T99 / sütun 2 / satır 41,42,43

  Yapılacak: s.167, tablo 99, satır 41, sütun 2; s.167, tablo 99, satır 42, sütun 2; s.167, tablo 99, satır 43, sütun 2: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0014.Sahne Sanatları Kursları: Türk Halk Oyunları, modern dans, bale, tiyatro, enstrüman vb. kurslar düzenlemek. · 2026 Haziran Sonu Harcama

  **Hücreler:** s.167 / T99 / sütun 3 / satır 41,42,43

  Yapılacak: s.167, tablo 99, satır 41, sütun 3; s.167, tablo 99, satır 42, sütun 3; s.167, tablo 99, satır 43, sütun 3: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0014.Sahne Sanatları Kursları: Türk Halk Oyunları, modern dans, bale, tiyatro, enstrüman vb. kurslar düzenlemek. · 2026 Yıl Sonu Tahmini

  **Hücreler:** s.167 / T99 / sütun 4 / satır 41,42,43

  Yapılacak: s.167, tablo 99, satır 41, sütun 4; s.167, tablo 99, satır 42, sütun 4; s.167, tablo 99, satır 43, sütun 4: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0015.Örgün Eğitime Destek ve Sınavlara Hazırlık Kursları: Dezavantajlı bölgelerde yaşayan öğrenciler için örgün eğitimlerine destek ve sınavlara hazırlık kursları düzenlemek. · 2026 Bütçe

  **Hücreler:** s.167 / T99 / sütun 2 / satır 44,45,46

  Yapılacak: s.167, tablo 99, satır 44, sütun 2; s.167, tablo 99, satır 45, sütun 2; s.167, tablo 99, satır 46, sütun 2: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0015.Örgün Eğitime Destek ve Sınavlara Hazırlık Kursları: Dezavantajlı bölgelerde yaşayan öğrenciler için örgün eğitimlerine destek ve sınavlara hazırlık kursları düzenlemek. · 2026 Haziran Sonu Harcama

  **Hücreler:** s.167 / T99 / sütun 3 / satır 44,45,46

  Yapılacak: s.167, tablo 99, satır 44, sütun 3; s.167, tablo 99, satır 45, sütun 3; s.167, tablo 99, satır 46, sütun 3: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0015.Örgün Eğitime Destek ve Sınavlara Hazırlık Kursları: Dezavantajlı bölgelerde yaşayan öğrenciler için örgün eğitimlerine destek ve sınavlara hazırlık kursları düzenlemek. · 2026 Yıl Sonu Tahmini

  **Hücreler:** s.167 / T99 / sütun 4 / satır 44,45,46

  Yapılacak: s.167, tablo 99, satır 44, sütun 4; s.167, tablo 99, satır 45, sütun 4; s.167, tablo 99, satır 46, sütun 4: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek. · 2026 Bütçe

  **Hücreler:** s.167 / T99 / sütun 2 / satır 47,48,49

  Yapılacak: s.167, tablo 99, satır 47, sütun 2; s.167, tablo 99, satır 48, sütun 2; s.167, tablo 99, satır 49, sütun 2: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek. · 2026 Haziran Sonu Harcama

  **Hücreler:** s.167 / T99 / sütun 3 / satır 47,48,49

  Yapılacak: s.167, tablo 99, satır 47, sütun 3; s.167, tablo 99, satır 48, sütun 3; s.167, tablo 99, satır 49, sütun 3: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek. · 2026 Yıl Sonu Tahmini

  **Hücreler:** s.167 / T99 / sütun 4 / satır 47,48,49

  Yapılacak: s.167, tablo 99, satır 47, sütun 4; s.167, tablo 99, satır 48, sütun 4; s.167, tablo 99, satır 49, sütun 4: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0017. Sanatsal Eğitimler: El sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında gösteriler ve yaz okulları düzenleme. · 2026 Bütçe

  **Hücreler:** s.167 / T99 / sütun 2 / satır 50,51,52

  Yapılacak: s.167, tablo 99, satır 50, sütun 2; s.167, tablo 99, satır 51, sütun 2; s.167, tablo 99, satır 52, sütun 2: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0017. Sanatsal Eğitimler: El sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında gösteriler ve yaz okulları düzenleme. · 2026 Haziran Sonu Harcama

  **Hücreler:** s.167 / T99 / sütun 3 / satır 50,51,52

  Yapılacak: s.167, tablo 99, satır 50, sütun 3; s.167, tablo 99, satır 51, sütun 3; s.167, tablo 99, satır 52, sütun 3: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0017. Sanatsal Eğitimler: El sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında gösteriler ve yaz okulları düzenleme. · 2026 Yıl Sonu Tahmini

  **Hücreler:** s.167 / T99 / sütun 4 / satır 50,51,52

  Yapılacak: s.167, tablo 99, satır 50, sütun 4; s.167, tablo 99, satır 51, sütun 4; s.167, tablo 99, satır 52, sütun 4: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.


### Makine İkmal Bakım ve Onarım Müdürlüğü

Gönderime hazır: **Hayır**; 2 kitap mesajı / 1 kitap kontrol maddesi.

- [ ] Çapraz maliyet/toplam farkı · 2028

  **Hücreler:** s.239 / T193 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.239 / T194 / sütun 5 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 265.909.182,00 + ortak personel/SGK 17.842.500,00 = 283.751.682,00 olmalı; ekonomik tablo toplamı 283.751.680,00 (fark -2,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 265.909.182,00, ekonomik personel/SGK hariç toplam 265.909.180,00 (fark -2,00). İki tabloda bu finansman tutarları eşit olmalı.


### Mali Hizmetler Müdürlüğü

Gönderime hazır: **Hayır**; 20 kitap mesajı / 2 kitap kontrol maddesi.

- [ ] Çapraz maliyet/toplam farkı · 2028

  **Hücreler:** s.221 / T169 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.221 / T170 / sütun 5 / satır 2,3,4,5,6,7,8,9,10,11,12,13

  Yapılacak: Faaliyet maliyetleri toplamı 1.075.992.302,00 + ortak personel/SGK 29.625.000,00 = 1.105.617.302,00 olmalı; ekonomik tablo toplamı 1.075.992.302,00 (fark -29.625.000,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 1.075.992.302,00, ekonomik personel/SGK hariç toplam 1.046.367.302,00 (fark -29.625.000,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Ekonomik tablo · 2027 Bütçe

  **Hücreler:** s.221 / T170 / sütun 4 / satır 2,3,4,5,6,7,8,9,10,11,12,13

  Yapılacak: Kategori satırlarının toplamı 888.224.835,00, Bütçe İçi Toplam 888.224.210,00 (fark -625,00). Yanlış satırı veya toplamı düzeltin.


### Özel Kalem Müdürlüğü

Gönderime hazır: **Evet**; 0 kitap mesajı / 1 kitap kontrol maddesi.

- [ ] Tablo 136, satır 8: Özel Kalem Müdürlüğü / 0006.Sosyal Güvenlik Kurumuna 5434 Sayılı Kanun Kapsamında Emekli İkramiyeleri Karşılığı Yapılan Ödemeler: faaliyet maliyet kaydı tekil eşleşmedi. Kart üyeliği ile müdürlük maliyet tablosundaki faaliyet kod/adını kontrol edin.

  **Hücreler:** s.198 / T136 / sütun 1 / satır 8

  Yapılacak: s.198, tablo 136, satır 8, sütun 1: bu faaliyet kodunun müdürlük faaliyet/maliyet tablosundaki karşılığını kaynak kayda göre ekleyin veya yanlış üyelik satırını düzeltin. Üyelik ve maliyet kaydı tekil eşleşmeli.


### Park ve Bahçeler Müdürlüğü

Gönderime hazır: **Hayır**; 20 kitap mesajı / 16 kitap kontrol maddesi.

- [ ] 0007.Kırılgan grupların da rahatlıkla kullanabileceği ortak alanların oluşturulması, bakımı ve onarımı. · 2027 Bütçe

  **Hücreler:** s.128 / T49 / sütun 5 / satır 20,21,22

  Yapılacak: Toplam = Bütçe İçi + Bütçe Dışı olmalı: 45.333.709,00 + 0,00 = 45.333.709,00, kitapta 44.333.709,00 yazıyor (fark -1.000.000,00). Yanlış hücreyi düzeltin.

- [ ] Çapraz maliyet/toplam farkı · 2027

  **Hücreler:** s.128 / T49 / sütun 5 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,44; s.128 / T50 / sütun 4 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 542.389.649,00 + ortak personel/SGK 23.223.750,00 = 565.613.399,00 olmalı; ekonomik tablo toplamı 551.300.000,00 (fark -14.313.399,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 543.389.649,00, ekonomik personel/SGK hariç toplam 528.076.250,00 (fark -15.313.399,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Çapraz maliyet/toplam farkı · 2028

  **Hücreler:** s.128 / T49 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,44; s.128 / T50 / sütun 5 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 923.777.553,00 + ortak personel/SGK 29.029.688,00 = 952.807.241,00 olmalı; ekonomik tablo toplamı 850.652.032,00 (fark -102.155.209,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 923.777.553,00, ekonomik personel/SGK hariç toplam 821.622.344,00 (fark -102.155.209,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Çapraz maliyet/toplam farkı · 2029

  **Hücreler:** s.128 / T49 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,44; s.128 / T50 / sütun 6 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 957.173.928,00 + ortak personel/SGK 36.287.110,00 = 993.461.038,00 olmalı; ekonomik tablo toplamı 1.020.978.440,00 (fark 27.517.402,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 957.173.928,00, ekonomik personel/SGK hariç toplam 984.691.330,00 (fark 27.517.402,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı · 2025 Gerçekleşme

  **Hücreler:** s.125 / T45 / sütun 4 / satır 11

  Yapılacak: Değer belirsiz: ondalık mı (132,915) binlik mi (132.915)? Doğru yazımı kitaba girin.

- [ ] SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı · 2026 Planlanan

  **Hücreler:** s.125 / T45 / sütun 5 / satır 11

  Yapılacak: Değer belirsiz: ondalık mı (250,000) binlik mi (250.000)? Doğru yazımı kitaba girin.

- [ ] SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı · 2026 Yıl Sonu Tahmini

  **Hücreler:** s.125 / T45 / sütun 6 / satır 11

  Yapılacak: Değer belirsiz: ondalık mı (250,000) binlik mi (250.000)? Doğru yazımı kitaba girin.

- [ ] SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı · 2027 Hedef

  **Hücreler:** s.125 / T45 / sütun 7 / satır 11

  Yapılacak: Değer belirsiz: ondalık mı (200,000) binlik mi (200.000)? Doğru yazımı kitaba girin.

- [ ] SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı · 2029 Tahmin

  **Hücreler:** s.125 / T45 / sütun 9 / satır 11

  Yapılacak: Değer belirsiz: ondalık mı (300,000) binlik mi (300.000)? Doğru yazımı kitaba girin.

- [ ] SH016/PG05. Onaylanan Peyzaj Proje ve İskân Sayısı · 2026 Yıl Sonu Tahmini

  **Hücreler:** s.125 / T45 / sütun 6 / satır 13

  Yapılacak: Değer belirsiz: ondalık mı (650,000) binlik mi (650.000)? Doğru yazımı kitaba girin.

- [ ] SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı · 2025 Gerçekleşme

  **Hücreler:** s.125 / T45 / sütun 4 / satır 9

  Yapılacak: Değer belirsiz: ondalık mı (17,840) binlik mi (17.840)? Doğru yazımı kitaba girin.

- [ ] SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı · 2026 Planlanan

  **Hücreler:** s.125 / T45 / sütun 5 / satır 9

  Yapılacak: Değer belirsiz: ondalık mı (50,000) binlik mi (50.000)? Doğru yazımı kitaba girin.

- [ ] SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı · 2026 Yıl Sonu Tahmini

  **Hücreler:** s.125 / T45 / sütun 6 / satır 9

  Yapılacak: Değer belirsiz: ondalık mı (50,000) binlik mi (50.000)? Doğru yazımı kitaba girin.

- [ ] SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı · 2027 Hedef

  **Hücreler:** s.125 / T45 / sütun 7 / satır 9

  Yapılacak: Değer belirsiz: ondalık mı (50,000) binlik mi (50.000)? Doğru yazımı kitaba girin.

- [ ] SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı · 2028 Tahmin

  **Hücreler:** s.125 / T45 / sütun 8 / satır 9

  Yapılacak: Değer belirsiz: ondalık mı (60,000) binlik mi (60.000)? Doğru yazımı kitaba girin.

- [ ] SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı · 2029 Tahmin

  **Hücreler:** s.125 / T45 / sütun 9 / satır 9

  Yapılacak: Değer belirsiz: ondalık mı (60,000) binlik mi (60.000)? Doğru yazımı kitaba girin.


### Plan Proje Müdürlüğü

Gönderime hazır: **Hayır**; 6 kitap mesajı / 1 kitap kontrol maddesi.

- [ ] Ekonomik tablo · 2026 Haziran Sonu Harcama

  **Hücreler:** s.136 / T60 / sütun 3 / satır 2,3,4,5,6,7

  Yapılacak: Kategori satırlarının toplamı 12.362.364,94, Bütçe İçi Toplam 11.501.713,28 (fark -860.651,66). Yanlış satırı veya toplamı düzeltin.

  Not: satır 2 (Personel Giderleri) toplamla aynı değeri taşıyor.


### Rehberlik ve Teftiş Kurulu Müdürlüğü

Gönderime hazır: **Hayır**; 10 kitap mesajı / 2 kitap kontrol maddesi.

- [ ] Çapraz maliyet/toplam farkı · 2029

  **Hücreler:** s.210 / T151 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,14; s.210 / T152 / sütun 6 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 333.750,00 + ortak personel/SGK 2.578.125,00 = 2.911.875,00 olmalı; ekonomik tablo toplamı 2.811.875,00 (fark -100.000,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe Dışı faaliyet toplamı 100.000,00, ekonomik personel/SGK hariç toplam 0,00 (fark -100.000,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Ekonomik tablo · 2026 Haziran Sonu Harcama

  **Hücreler:** s.210 / T152 / sütun 3 / satır 2,3,4,5,6,7,8

  Yapılacak: Kategori satırlarının toplamı 936.918,72, Bütçe İçi Toplam 955.735,48 (fark 18.816,76). Yanlış satırı veya toplamı düzeltin.


### Ruhsat ve Denetim Müdürlüğü

Gönderime hazır: **Hayır**; 12 kitap mesajı / 2 kitap kontrol maddesi.

- [ ] Ekonomik tablo · 2026 Bütçe

  **Hücreler:** s.101 / T14 / sütun 2 / satır 2,3,4,5,6,7

  Yapılacak: Kategori satırlarının toplamı 11.386.500,16, Bütçe İçi Toplam 11.623.833,00 (fark 237.332,84). Yanlış satırı veya toplamı düzeltin.

- [ ] Ekonomik tablo · 2026 Haziran Sonu Harcama

  **Hücreler:** s.101 / T14 / sütun 3 / satır 2,3,4,5,6,7

  Yapılacak: Kategori satırlarının toplamı 5.151.457,55, Bütçe İçi Toplam 4.815.578,31 (fark -335.879,24). Yanlış satırı veya toplamı düzeltin.


### Sağlık İşleri Müdürlüğü

Gönderime hazır: **Hayır**; 12 kitap mesajı / 2 kitap kontrol maddesi.

- [ ] Çapraz maliyet/toplam farkı · 2029

  **Hücreler:** s.98 / T9 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.98 / T10 / sütun 6 / satır 2,3,4,5,6,7,8,9

  Yapılacak: Faaliyet maliyetleri toplamı 24.931.292,00 + ortak personel/SGK 21.946.875,00 = 46.878.167,00 olmalı; ekonomik tablo toplamı 47.049.588,00 (fark 171.421,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 24.931.292,00, ekonomik personel/SGK hariç toplam 25.102.713,00 (fark 171.421,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Ekonomik tablo · 2026 Haziran Sonu Harcama

  **Hücreler:** s.98 / T10 / sütun 3 / satır 2,3,4,5,6,7,8,9

  Yapılacak: Kategori satırlarının toplamı 6.721.207,46, Bütçe İçi Toplam 6.721.207,36 (fark -0,10). Yanlış satırı veya toplamı düzeltin.


### Sosyal Destek Müdürlüğü

Gönderime hazır: **Evet**; 0 kitap mesajı / 0 kitap kontrol maddesi.

Kitap düzeltmesi yok.

### Strateji Geliştirme Müdürlüğü

Gönderime hazır: **Hayır**; 2 kitap mesajı / 1 kitap kontrol maddesi.

- [ ] Çapraz maliyet/toplam farkı · 2028

  **Hücreler:** s.214 / T159 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,29; s.214 / T160 / sütun 5 / satır 2,3,4,5,6,7

  Yapılacak: Faaliyet maliyetleri toplamı 2.325.528,00 + ortak personel/SGK 4.495.313,00 = 6.820.841,00 olmalı; ekonomik tablo toplamı 6.770.841,00 (fark -50.000,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 2.325.528,00, ekonomik personel/SGK hariç toplam 2.275.528,00 (fark -50.000,00). İki tabloda bu finansman tutarları eşit olmalı.


### Tarımsal Hizmetler Müdürlüğü

Gönderime hazır: **Hayır**; 20 kitap mesajı / 7 kitap kontrol maddesi.

- [ ] 0008.Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini · 2027 Bütçe

  **Hücreler:** s.156 / T83 / sütun 5 / satır 23,24,25

  Yapılacak: Bütçe İçi hücresi boş. Bütçe içi kaynak yoksa 0,00 yazın.

- [ ] 0008.Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini · 2028 Tahmin

  **Hücreler:** s.156 / T83 / sütun 6 / satır 23,24,25

  Yapılacak: Bütçe İçi hücresi boş. Bütçe içi kaynak yoksa 0,00 yazın.

- [ ] 0008.Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini · 2029 Tahmin

  **Hücreler:** s.156 / T83 / sütun 7 / satır 23,24,25

  Yapılacak: Bütçe İçi hücresi boş. Bütçe içi kaynak yoksa 0,00 yazın.

- [ ] 0009.Üretimin zehirsiz gıda, toprak kirliliği önleyici ve çevre korunma etmenlerinin önemi çevre korunma etmenlerinin önemi çerçevesinde tasarruflu ve sürdürülebilir olarak yürütülmesi · 2027 Bütçe

  **Hücreler:** s.156 / T83 / sütun 5 / satır 26,27,28

  Yapılacak: Bütçe İçi hücresi boş. Bütçe içi kaynak yoksa 0,00 yazın.

- [ ] 0009.Üretimin zehirsiz gıda, toprak kirliliği önleyici ve çevre korunma etmenlerinin önemi çevre korunma etmenlerinin önemi çerçevesinde tasarruflu ve sürdürülebilir olarak yürütülmesi · 2028 Tahmin

  **Hücreler:** s.156 / T83 / sütun 6 / satır 26,27,28

  Yapılacak: Bütçe İçi hücresi boş. Bütçe içi kaynak yoksa 0,00 yazın.

- [ ] 0009.Üretimin zehirsiz gıda, toprak kirliliği önleyici ve çevre korunma etmenlerinin önemi çevre korunma etmenlerinin önemi çerçevesinde tasarruflu ve sürdürülebilir olarak yürütülmesi · 2029 Tahmin

  **Hücreler:** s.156 / T83 / sütun 7 / satır 26,27,28

  Yapılacak: Bütçe İçi hücresi boş. Bütçe içi kaynak yoksa 0,00 yazın.

- [ ] Ekonomik tablo · 2026 Bütçe

  **Hücreler:** s.156 / T84 / sütun 2 / satır 2,3,4,5,6,7,8

  Yapılacak: Kategori satırlarının toplamı 16.365.381,00, Bütçe İçi Toplam 16.565.381,00 (fark 200.000,00). Yanlış satırı veya toplamı düzeltin.


### Temizlik İşleri Müdürlüğü

Gönderime hazır: **Evet**; 0 kitap mesajı / 0 kitap kontrol maddesi.

Kitap düzeltmesi yok.

### Veteriner İşleri Müdürlüğü

Gönderime hazır: **Hayır**; 16 kitap mesajı / 4 kitap kontrol maddesi.

- [ ] 0004.Mevcut barınak kapasitesinin artırılması ve teknik altyapının iyileştirilmesini sağlamak. · 2027 Bütçe

  **Hücreler:** s.107 / T23 / sütun 5 / satır 11,12,13

  Yapılacak: Bütçe Dışı hücresi boş. Bütçe dışı kaynak yoksa 0,00 yazın.

- [ ] 0004.Mevcut barınak kapasitesinin artırılması ve teknik altyapının iyileştirilmesini sağlamak. · 2028 Tahmin

  **Hücreler:** s.107 / T23 / sütun 6 / satır 11,12,13

  Yapılacak: Bütçe Dışı hücresi boş. Bütçe dışı kaynak yoksa 0,00 yazın.

- [ ] 0004.Mevcut barınak kapasitesinin artırılması ve teknik altyapının iyileştirilmesini sağlamak. · 2029 Tahmin

  **Hücreler:** s.107 / T23 / sütun 7 / satır 11,12,13

  Yapılacak: Bütçe Dışı hücresi boş. Bütçe dışı kaynak yoksa 0,00 yazın.

- [ ] Ekonomik tablo · 2026 Bütçe

  **Hücreler:** s.107 / T24 / sütun 2 / satır 2,3,4,5,6,7,8,9

  Yapılacak: Kategori satırlarının toplamı 80.767.000,00, Bütçe İçi Toplam 78.140.000,00 (fark -2.627.000,00). Yanlış satırı veya toplamı düzeltin.


### Yazı İşleri Müdürlüğü

Gönderime hazır: **Hayır**; 35 kitap mesajı / 23 kitap kontrol maddesi.

- [ ] Çapraz maliyet/toplam farkı · 2027

  **Hücreler:** s.227 / T179 / sütun 5 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,38; s.227 / T180 / sütun 4 / satır 2,3,4,5,6,7,8,9

  Yapılacak: Faaliyet maliyetleri toplamı 16.330.730,00 + ortak personel/SGK 24.700.000,00 = 41.030.730,00 olmalı; ekonomik tablo toplamı 41.026.130,00 (fark -4.600,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 16.330.730,00, ekonomik personel/SGK hariç toplam 16.326.130,00 (fark -4.600,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Çapraz maliyet/toplam farkı · 2028

  **Hücreler:** s.227 / T179 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,38; s.227 / T180 / sütun 5 / satır 2,3,4,5,6,7,8,9

  Yapılacak: Faaliyet maliyetleri toplamı 19.452.675,00 + ortak personel/SGK 30.875.000,00 = 50.327.675,00 olmalı; ekonomik tablo toplamı 52.230.432,00 (fark 1.902.757,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 19.452.675,00, ekonomik personel/SGK hariç toplam 21.348.432,00 (fark 1.895.757,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Çapraz maliyet/toplam farkı · 2029

  **Hücreler:** s.227 / T179 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,38; s.227 / T180 / sütun 6 / satır 2,3,4,5,6,7,8,9

  Yapılacak: Faaliyet maliyetleri toplamı 19.555.001,00 + ortak personel/SGK 38.593.750,00 = 58.148.751,00 olmalı; ekonomik tablo toplamı 60.188.800,00 (fark 2.040.049,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 19.555.001,00, ekonomik personel/SGK hariç toplam 21.595.050,00 (fark 2.040.049,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] 0002.Alınan Kararların İlgili Birimlere İletilmesi · 2026 Bütçe

  **Hücreler:** s.227 / T179 / sütun 2 / satır 5,6,7

  Yapılacak: s.227, tablo 179, satır 5, sütun 2; s.227, tablo 179, satır 6, sütun 2; s.227, tablo 179, satır 7, sütun 2: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0002.Alınan Kararların İlgili Birimlere İletilmesi · 2026 Haziran Sonu Harcama

  **Hücreler:** s.227 / T179 / sütun 3 / satır 5,6,7

  Yapılacak: s.227, tablo 179, satır 5, sütun 3; s.227, tablo 179, satır 6, sütun 3; s.227, tablo 179, satır 7, sütun 3: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0002.Alınan Kararların İlgili Birimlere İletilmesi · 2026 Yıl Sonu Tahmini

  **Hücreler:** s.227 / T179 / sütun 4 / satır 5,6,7

  Yapılacak: s.227, tablo 179, satır 5, sütun 4; s.227, tablo 179, satır 6, sütun 4; s.227, tablo 179, satır 7, sütun 4: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0007.Dijital Nikah Yönetim Sisteminin Kurulması ve İşletilmesi. · 2026 Bütçe

  **Hücreler:** s.227 / T179 / sütun 2 / satır 20,21,22

  Yapılacak: s.227, tablo 179, satır 20, sütun 2; s.227, tablo 179, satır 21, sütun 2; s.227, tablo 179, satır 22, sütun 2: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0007.Dijital Nikah Yönetim Sisteminin Kurulması ve İşletilmesi. · 2026 Haziran Sonu Harcama

  **Hücreler:** s.227 / T179 / sütun 3 / satır 20,21,22

  Yapılacak: s.227, tablo 179, satır 20, sütun 3; s.227, tablo 179, satır 21, sütun 3; s.227, tablo 179, satır 22, sütun 3: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0007.Dijital Nikah Yönetim Sisteminin Kurulması ve İşletilmesi. · 2026 Yıl Sonu Tahmini

  **Hücreler:** s.227 / T179 / sütun 4 / satır 20,21,22

  Yapılacak: s.227, tablo 179, satır 20, sütun 4; s.227, tablo 179, satır 21, sütun 4; s.227, tablo 179, satır 22, sütun 4: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0008.Nikah Akdi ve Tescil İşlemlerinin Yürütülmesi. · 2026 Bütçe

  **Hücreler:** s.227 / T179 / sütun 2 / satır 23,24,25

  Yapılacak: s.227, tablo 179, satır 23, sütun 2; s.227, tablo 179, satır 24, sütun 2; s.227, tablo 179, satır 25, sütun 2: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0008.Nikah Akdi ve Tescil İşlemlerinin Yürütülmesi. · 2026 Haziran Sonu Harcama

  **Hücreler:** s.227 / T179 / sütun 3 / satır 23,24,25

  Yapılacak: s.227, tablo 179, satır 23, sütun 3; s.227, tablo 179, satır 24, sütun 3; s.227, tablo 179, satır 25, sütun 3: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0008.Nikah Akdi ve Tescil İşlemlerinin Yürütülmesi. · 2026 Yıl Sonu Tahmini

  **Hücreler:** s.227 / T179 / sütun 4 / satır 23,24,25

  Yapılacak: s.227, tablo 179, satır 23, sütun 4; s.227, tablo 179, satır 24, sütun 4; s.227, tablo 179, satır 25, sütun 4: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0009.Nikah Salonlarının Teknolojik ve Fiziksel Modernizasyonu. · 2026 Bütçe

  **Hücreler:** s.227 / T179 / sütun 2 / satır 26,27,28

  Yapılacak: s.227, tablo 179, satır 26, sütun 2; s.227, tablo 179, satır 27, sütun 2; s.227, tablo 179, satır 28, sütun 2: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0009.Nikah Salonlarının Teknolojik ve Fiziksel Modernizasyonu. · 2026 Haziran Sonu Harcama

  **Hücreler:** s.227 / T179 / sütun 3 / satır 26,27,28

  Yapılacak: s.227, tablo 179, satır 26, sütun 3; s.227, tablo 179, satır 27, sütun 3; s.227, tablo 179, satır 28, sütun 3: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0009.Nikah Salonlarının Teknolojik ve Fiziksel Modernizasyonu. · 2026 Yıl Sonu Tahmini

  **Hücreler:** s.227 / T179 / sütun 4 / satır 26,27,28

  Yapılacak: s.227, tablo 179, satır 26, sütun 4; s.227, tablo 179, satır 27, sütun 4; s.227, tablo 179, satır 28, sütun 4: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0010.Saha Hizmetleri İçin Mobil Altyapı Desteği. · 2026 Bütçe

  **Hücreler:** s.227 / T179 / sütun 2 / satır 29,30,31

  Yapılacak: s.227, tablo 179, satır 29, sütun 2; s.227, tablo 179, satır 30, sütun 2; s.227, tablo 179, satır 31, sütun 2: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0010.Saha Hizmetleri İçin Mobil Altyapı Desteği. · 2026 Haziran Sonu Harcama

  **Hücreler:** s.227 / T179 / sütun 3 / satır 29,30,31

  Yapılacak: s.227, tablo 179, satır 29, sütun 3; s.227, tablo 179, satır 30, sütun 3; s.227, tablo 179, satır 31, sütun 3: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0010.Saha Hizmetleri İçin Mobil Altyapı Desteği. · 2026 Yıl Sonu Tahmini

  **Hücreler:** s.227 / T179 / sütun 4 / satır 29,30,31

  Yapılacak: s.227, tablo 179, satır 29, sütun 4; s.227, tablo 179, satır 30, sütun 4; s.227, tablo 179, satır 31, sütun 4: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0011.Evlilik Öncesi Bilgilendirme ve Rehberlik Hizmetleri · 2026 Bütçe

  **Hücreler:** s.227 / T179 / sütun 2 / satır 32,33,34

  Yapılacak: s.227, tablo 179, satır 32, sütun 2; s.227, tablo 179, satır 33, sütun 2; s.227, tablo 179, satır 34, sütun 2: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0011.Evlilik Öncesi Bilgilendirme ve Rehberlik Hizmetleri · 2026 Haziran Sonu Harcama

  **Hücreler:** s.227 / T179 / sütun 3 / satır 32,33,34

  Yapılacak: s.227, tablo 179, satır 32, sütun 3; s.227, tablo 179, satır 33, sütun 3; s.227, tablo 179, satır 34, sütun 3: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] 0011.Evlilik Öncesi Bilgilendirme ve Rehberlik Hizmetleri · 2026 Yıl Sonu Tahmini

  **Hücreler:** s.227 / T179 / sütun 4 / satır 32,33,34

  Yapılacak: s.227, tablo 179, satır 32, sütun 4; s.227, tablo 179, satır 33, sütun 4; s.227, tablo 179, satır 34, sütun 4: Toplam, Bütçe İçi, Bütçe Dışı hücrelerini kaynak kayda göre doldurun. Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.

- [ ] Personel/SGK toplam farkı · 2028

  **Hücreler:** s.227 / T179 / sütun 6 / satır 38; s.227 / T180 / sütun 5 / satır 2,3,4,5,6,7,8,9

  Yapılacak: Ekonomik personel/SGK 30.882.000,00, ortak personel/SGK 30.875.000,00 (fark 7.000,00). İki kaynakta aynı tutar olmalı; yanlış hücreyi düzeltin.

- [ ] Ekonomik tablo · 2028 Tahmin

  **Hücreler:** s.227 / T180 / sütun 5 / satır 2,3,4,5,6,7,8,9; s.227 / T179 / sütun 6 / satır 38

  Yapılacak: Kategori satırlarının toplamı 52.230.432,00, Bütçe İçi Toplam 52.223.432,00 (fark -7.000,00). Yanlış satırı veya toplamı düzeltin. Ekonomik personel/SGK 30.882.000,00, ortak personel/SGK 30.875.000,00 (fark 7.000,00). İki kaynakta aynı tutar olmalı; yanlış hücreyi düzeltin.


### Zabıta Müdürlüğü

Gönderime hazır: **Hayır**; 8 kitap mesajı / 1 kitap kontrol maddesi.

- [ ] Ekonomik tablo · 2026 Haziran Sonu Harcama

  **Hücreler:** s.104 / T20 / sütun 3 / satır 2,3,4,5,6,7,8

  Yapılacak: Kategori satırlarının toplamı 51.258.201,04, Bütçe İçi Toplam 45.863.621,38 (fark -5.394.579,66). Yanlış satırı veya toplamı düzeltin.

  Not: satır 2 (Personel Giderleri) toplamla aynı değeri taşıyor.


## Dönüşüm ve varsayımlar

Eşlenmeyen ad (ham metin korundu, yerleşik müdürlük eşlemesi uygulandı): Gelirler Müdürlüğü (Bütçe İşletme Şefliği).

Basılı sayfaya bağlı olmayan tablolar (dışlama seçeneğinden bağımsız; yüklemeye alınmaz): [{"id": "ubbb4ibbe3", "type": "cost"}, {"id": "ubbb4ibbcb", "type": "economic"}, {"id": "ubb2aibb60", "type": "card"}, {"id": "ubb2aibb40", "type": "membership"}].

Teyit bekleyen ad eşlemeleri: Gençlik ve Spor Hizmetleri Müdürlüğü; Sosyal Hizmetler Müdürlüğü; Basın Yayın ve Halkla İlişkiler Müdürlüğü; Harita ve Planlama Müdürlüğü; Araştırma ve Geliştirme Müdürlüğü. Program/alt program kodları kitapta yoktur ve boş bırakılır. Tekil müdürlük içi faaliyet kodu üyeliği belirler. Resmî katalog 0006 Özel Kalem gibi maliyet karşılığı bulunmayan üyelikleri korur; yeni maliyet üretilmez. Nihai kitap dışlamasız yeniden denenmelidir.

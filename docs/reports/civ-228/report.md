# CIV-228 — Pilot haftası provası (C3, D-479 modeli)

**SENTETİK prova. Yalnız atılabilir yerel PostgreSQL; canlı veritabanı, birleştirme ve dağıtım yok.**

Yeniden çalıştırma: `python scripts/guide_screenshots.py --fr-pilot` (`CIVENSA_TEST_POSTGRES_URL` yerel test PostgreSQL, isteğe bağlı `CIVENSA_CHROMIUM_PATH`).

## Senaryo

Hesaplar canlıdaki D-479/D-480/D-481 düzenini taklit eder: Strateji Müdürü (yalnız inceleme, iade, onay), Strateji Kullanıcısı (Excel içe aktarma) ve Fen İşleri, Afet İşleri ve Risk Değerlendirme, Özel Kalem için birer "<Müdürlük> (Strateji)" Müdür hesabı. Personel hesabı yoktur. Müdürlük hesapları ilk girişte aynı güçlü parolaya geçirilir.

Akış: onaylı kitap yayını → 2026 FR revizyonu → EK-1 raporları → Strateji Kullanıcısı ana Excel dosyasını önizler ve uygular (her müdürlükte bir gösterge hedefin yarısı, açıklama yok) → müdürlük hesabıyla bölümler, Tablo 1/2/7/8, fotoğraf, EK-2 → gönderim denemesi (açıklamasız sapma engeli) → açıklamalı Excel yeniden aktarılır → gönder → Strateji iade → düzelt → yeniden gönder → Strateji Müdürü onaylar → Word/PDF.

## Bulgular

İlk koşu (düzeltmelerden önce, aynı senaryo) ile son koşu karşılaştırılarak yazıldı. Etiketler: DOĞRULANDI = bu provada gözlendi; KOD = kod okumasıyla belirlendi, provada ayrıca denenmedi; TAHMİN = model hesabı.

1. **Engel, düzeltildi (DOĞRULANDI).** Ekranda daha önce kanıt girilmemiş göstergede Excel aktarımı hiçbir satırı yazmıyordu: 20 satırın 20'si "Doğrulanmış gerçekleşme için kaynak bulunmuyor" hatası verdi. D-479 modelinde gerçekleşmeleri ilk kez Excel getirdiği için pilot burada dururdu. Düzeltme: önceki kaydın kanıtı yoksa kaynak olarak Strateji ana Excel dosyası, `veriler` sayfasındaki satır numarası ve dosyanın SHA-256 değeri kaydedilir. Ekranda girilmiş kanıt varsa olduğu gibi korunur. Son koşuda 20 satırın 20'si yazıldı.
2. **Hata, düzeltildi (DOĞRULANDI).** Değer aynı kalıp yalnız "Açıklama" sütunu sonradan doldurulduğunda yeniden aktarma satırı "Değişmedi" sayıp açıklamayı yazmıyordu; hedef farkı açıklaması eksik müdürlük raporu gönderilemiyordu. Düzeltme: yeni ve farklı bir açıklama yeni revizyon yazar; boş açıklama hücresi ekrandaki açıklamayı silmez. Son koşuda açıklamalı dosya 3 satır yazdı, 17 satır değişmedi; üç müdürlük de ardından gönderebildi.
3. **Yavaşlık, düzeltildi (DOĞRULANDI).** Uygulama adımı her satırda onaylı kitabı (çok MB) yeniden okuyup doğruluyordu: 20 satır yerelde 7,4 sn (sürenin %90'ı). Düzeltme: bir aktarım içinde kitap bir kez doğrulanır. Son koşuda 20 satır 0,7 sn, 368 sorgu. TAHMİN: 227 satırlık gerçek dosya yerelde ~8 sn; canlıda sorgu başına ~6 ms gecikmeyle ~25 sn. Bir kerelik işlem olduğu için pilotu engellemez.
4. **Kullanım, düzeltildi (DOĞRULANDI).** Önizlemede adı tam eşleşen satırlar dahil her satır "Aktarma" seçili geliyordu; ilk koşuda 20 satırın 20'si elle seçildi (gerçek dosyada ~227 seçim). Kılavuz ise "Eşleşti satırında önerilen seçimi kontrol edin" diyordu. Düzeltme: tam eşleşen ve ölçek sorusu olmayan satır onaylı gelir; Strateji yine "Aktarma"ya çevirebilir. Son koşuda elle seçim 4 / 20.
5. **Bilgi (DOĞRULANDI).** Aynı müdürlükte aynı adlı iki gösterge (farklı kartlar; Fen İşleri ve Afet İşlerinde birer çift) her iki satırı da "Onay gerekiyor" yapar. İkisine aynı gösterge seçilirse ikinci satır "Aynı gösterge ikinci kez seçildi" hatası alır. Strateji seçenekteki kart bilgisine bakıp her satıra ayrı göstergeyi seçmelidir. Kılavuza eklendi.
6. **Kural (KOD).** Gerçekleşmeyi yazan hesap birimi onaylayamaz (görevler ayrılığı). Excel'i Strateji Müdürü hesabıyla aktarmak, o müdürlüklerin onayını engeller. Provada aktarım "Strateji Kullanıcısı", onay Strateji Müdürü hesabıyla yapıldı ve çalıştı. Kılavuza eklendi.
7. **Çalışan akış (DOĞRULANDI).** Personel hesabı olmadan "<Müdürlük> (Strateji)" Müdür hesabı ilk girişte ortak parolaya geçti; bölümler, Tablo 1/2/7/8, fotoğraf, EK-2, gönderim, iade sonrası düzeltme ve yeniden gönderim bu hesapla yapıldı. Strateji Müdürü üç birimi onayladı; Word ve PDF indirildi. Kod değişikliği gerekmedi.
8. **Not.** Prova her hesabı ayrı tarayıcı oturumunda açar. Gerçekte Strateji her müdürlük için çıkış yapıp yeniden girecek (D-481); bu yük ölçülmedi. SLOW kalan 3 adım (kitap yayını, FR revizyonu) canlıda bir kez yapılmış kurulum adımlarıdır.

## Excel aktarımları

- **İlk Excel**: önizleme Eşleşti: 16 · Onay gerekiyor: 4; elle seçilen 4 / 20 satır; sonuç Yazıldı: 20.
- **Açıklamalı Excel**: önizleme Değişmedi: 13 · Eşleşti: 3 · Onay gerekiyor: 4; elle seçilen 4 / 20 satır; sonuç Değişmedi: 17 · Yazıldı: 3.

## Özet

OK 301 · SLOW 3 · BLOCKER 0 · toplam 304 adım. Onaylanan birimler: fen, afet, ozel. Koşu: tamamlandı.

## Adım çizelgesi

| Hesap | Adım | Sonuç | Sayfa | Ekran | Süre (ms) | Not |
| --- | --- | --- | --- | --- | ---: | --- |
| Strateji Müdürü | Giriş ekranı | OK | `/login` | — | 895 | — |
| Strateji Müdürü | Hesapla giriş | OK | `/modules` | — | 894 | — |
| Strateji Müdürü | 2026 onaylı kitap yayın hazırlığı | SLOW | `/report-builder?period_id=2` | — | 5055 | — |
| Strateji Müdürü | Onaylı kitaptan yayınla | SLOW | `/report-builder?period_id=2` | — | 8022 | — |
| Strateji Müdürü | 2026 gösterge raporu oluşturma | OK | `/activity-reports` | — | 954 | — |
| Strateji Müdürü | Yayına bağlı 2026 FR revizyonu oluştur | SLOW | `/activity-reports/revisions/1` | — | 3101 | — |
| Strateji Müdürü | 2026 birim ve idare raporları oluşturma | OK | `/activity-sections` | — | 899 | — |
| Strateji Müdürü | 2026 EK-1 raporlarını oluştur | OK | `/activity-sections` | — | 1975 | — |
| Strateji Kullanıcısı | Giriş ekranı | OK | `/login` | — | 783 | — |
| Strateji Kullanıcısı | Hesapla giriş | OK | `/modules` | — | 911 | — |
| Strateji Kullanıcısı | İlk Excel: Excel yükleme alanı | OK | `/activity-reports` | — | 907 | — |
| Strateji Kullanıcısı | Strateji Excel önizlemesi | OK | `/activity-reports/imports/1` | [PNG](../../screenshots/civ-228/012-strategy_user.png) | 2117 | Önizleme: Eşleşti: 16 · Onay gerekiyor: 4. Elle seçilen satır: 4 / 20. |
| Strateji Kullanıcısı | Strateji Excel sonucu | OK | `/activity-reports/imports/1` | [PNG](../../screenshots/civ-228/013-strategy_user.png) | 1438 | Sonuç: Yazıldı: 20. Excel 2. satır · Yazıldı · Yeni gerçekleşme revizyonu kaydedildi. · 2 · TOPLA: Q1 + Q2 + Q3 + Q4 &#124; Excel 3. satır · Yazıldı · Yeni gerçekleşme revizyonu kaydedildi. · 12.000 · TOPLA: Q1 + Q2 + Q3 + Q4 &#124; Excel 4. satır · Yazıldı · Yeni gerçekleşme revizyonu kaydedildi. · 200 · TOPLA: Q1 + Q2 + Q3 + Q4 &#124; Excel 5. satır · Yazıldı · Yeni gerçekleşme revizyonu kaydedildi. · 13 · TOPLA: Q1 + Q2 + Q3 + Q4 &#124; Excel 6. satır · Yazıldı · Yeni gerçekleşme revizyonu kaydedildi. · 200 · TOPLA: Q1 + Q2 + Q3 + Q4 &#124; Excel 7. satır · Yazıldı · Yeni gerçekleşme revizyonu kaydedildi. · 100 · TOPLA: Q1 + Q2 + Q3 + Q4 |
| Fen İşleri Müdürlüğü (Strateji) | Giriş ekranı | OK | `/login` | — | 746 | — |
| Fen İşleri Müdürlüğü (Strateji) | Hesapla giriş | OK | `/change-password` | — | 871 | — |
| Fen İşleri Müdürlüğü (Strateji) | Müdürlük hesabı ilk parola | OK | `/change-password` | [PNG](../../screenshots/civ-228/016-fen.png) | 2 | — |
| Fen İşleri Müdürlüğü (Strateji) | İlk paroladan sonra modüller | OK | `/modules` | — | 844 | — |
| Fen İşleri Müdürlüğü (Strateji) | Aktarılan göstergeleri müdürlük hesabıyla kontrol et | OK | `/activity-reports/revisions/1` | — | 1664 | — |
| Fen İşleri Müdürlüğü (Strateji) | Müdürlük 2026 birim raporunu bul | OK | `/activity-sections` | — | 984 | — |
| Fen İşleri Müdürlüğü (Strateji) | Birim raporu ve bölüm ağacı | OK | `/activity-sections/reports/8` | — | 1207 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: Yönetici özetiBoş | OK | `/activity-sections/reports/8?code=OZET` | — | 1080 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm metni kaydet: Yönetici özetiBoş | OK | `/activity-sections/reports/8?code=OZET` | — | 1210 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: I- Genel bilgilerBoş | OK | `/activity-sections/reports/8?code=I` | — | 1145 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm metni kaydet: I- Genel bilgilerBoş | OK | `/activity-sections/reports/8?code=I` | — | 1211 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: A- Misyon ve VizyonBoş | OK | `/activity-sections/reports/8?code=I.A` | — | 1048 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm metni kaydet: A- Misyon ve VizyonBoş | OK | `/activity-sections/reports/8?code=I.A` | — | 1172 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: B- Yetki, Görev ve SorumluluklarBoş | OK | `/activity-sections/reports/8?code=I.B` | — | 1146 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm metni kaydet: B- Yetki, Görev ve SorumluluklarBoş | OK | `/activity-sections/reports/8?code=I.B` | — | 1203 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: C- İdareye İlişkin BilgilerBoş | OK | `/activity-sections/reports/8?code=I.C` | — | 1064 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm metni kaydet: C- İdareye İlişkin BilgilerBoş | OK | `/activity-sections/reports/8?code=I.C` | — | 1169 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: 1- Fiziksel YapıBoş | OK | `/activity-sections/reports/8?code=I.C.1` | — | 1252 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm metni kaydet: 1- Fiziksel YapıBoş | OK | `/activity-sections/reports/8?code=I.C.1` | — | 1227 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: 2- Teşkilat YapısıBoş | OK | `/activity-sections/reports/8?code=I.C.2` | — | 1033 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm metni kaydet: 2- Teşkilat YapısıBoş | OK | `/activity-sections/reports/8?code=I.C.2` | — | 1181 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: 3- Teknoloji ve Bilişim AltyapısıBoş | OK | `/activity-sections/reports/8?code=I.C.3` | — | 1149 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm metni kaydet: 3- Teknoloji ve Bilişim AltyapısıBoş | OK | `/activity-sections/reports/8?code=I.C.3` | — | 1154 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: 4- İnsan KaynaklarıBoş | OK | `/activity-sections/reports/8?code=I.C.4` | — | 1092 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm metni kaydet: 4- İnsan KaynaklarıBoş | OK | `/activity-sections/reports/8?code=I.C.4` | — | 1220 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: 5- Sunulan HizmetlerBoş | OK | `/activity-sections/reports/8?code=I.C.5` | — | 1068 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm metni kaydet: 5- Sunulan HizmetlerBoş | OK | `/activity-sections/reports/8?code=I.C.5` | — | 1195 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: 6- Yönetim ve İç Kontrol SistemiBoş | OK | `/activity-sections/reports/8?code=I.C.6` | — | 1058 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm metni kaydet: 6- Yönetim ve İç Kontrol SistemiBoş | OK | `/activity-sections/reports/8?code=I.C.6` | — | 1148 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: D- Diğer HususlarBoş | OK | `/activity-sections/reports/8?code=I.D` | — | 1115 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm metni kaydet: D- Diğer HususlarBoş | OK | `/activity-sections/reports/8?code=I.D` | — | 1168 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: II- Amaçlar ve hedeflerBoş | OK | `/activity-sections/reports/8?code=II` | — | 1104 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm metni kaydet: II- Amaçlar ve hedeflerBoş | OK | `/activity-sections/reports/8?code=II` | — | 1278 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: A- Temel Politika ve ÖnceliklerBoş | OK | `/activity-sections/reports/8?code=II.A` | — | 1102 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm metni kaydet: A- Temel Politika ve ÖnceliklerBoş | OK | `/activity-sections/reports/8?code=II.A` | — | 1281 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: B- İdarenin Stratejik Planında Yer Alan Amaç ve HedeflerBoş | OK | `/activity-sections/reports/8?code=II.B` | — | 1265 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm metni kaydet: B- İdarenin Stratejik Planında Yer Alan Amaç ve HedeflerBoş | OK | `/activity-sections/reports/8?code=II.B` | — | 1310 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: C- Diğer HususlarBoş | OK | `/activity-sections/reports/8?code=II.C` | — | 1167 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm metni kaydet: C- Diğer HususlarBoş | OK | `/activity-sections/reports/8?code=II.C` | — | 1272 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: III- Faaliyetlere ilişkin bilgi ve değerlendirmelerBoş | OK | `/activity-sections/reports/8?code=III` | — | 1123 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm metni kaydet: III- Faaliyetlere ilişkin bilgi ve değerlendirmelerBoş | OK | `/activity-sections/reports/8?code=III` | — | 1265 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: A- Malî BilgilerBoş | OK | `/activity-sections/reports/8?code=III.A` | — | 1218 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: 1- Bütçe Uygulama SonuçlarıBoş | OK | `/activity-sections/reports/8?code=III.A.1` | — | 1121 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: 2- Temel Malî Tablolara İlişkin AçıklamalarBoş | OK | `/activity-sections/reports/8?code=III.A.2` | — | 1142 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: 3- Malî Denetim SonuçlarıBoş | OK | `/activity-sections/reports/8?code=III.A.3` | — | 1082 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm metni kaydet: 3- Malî Denetim SonuçlarıBoş | OK | `/activity-sections/reports/8?code=III.A.3` | — | 1290 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: 4- Diğer HususlarBoş | OK | `/activity-sections/reports/8?code=III.A.4` | — | 1117 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm metni kaydet: 4- Diğer HususlarBoş | OK | `/activity-sections/reports/8?code=III.A.4` | — | 1204 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: B- Performans BilgileriBoş | OK | `/activity-sections/reports/8?code=III.B` | — | 1082 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm metni kaydet: B- Performans BilgileriBoş | OK | `/activity-sections/reports/8?code=III.B` | — | 1246 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: 1- Program, Alt Program, Faaliyet BilgileriBoş | OK | `/activity-sections/reports/8?code=III.B.1` | — | 1143 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm metni kaydet: 1- Program, Alt Program, Faaliyet BilgileriBoş | OK | `/activity-sections/reports/8?code=III.B.1` | — | 1243 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: 2- Performans Sonuçlarının DeğerlendirilmesiBoş | OK | `/activity-sections/reports/8?code=III.B.2` | — | 1200 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm metni kaydet: 2- Performans Sonuçlarının DeğerlendirilmesiBoş | OK | `/activity-sections/reports/8?code=III.B.2` | — | 1267 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: i. Alt program hedef ve göstergeleriyle ilgili gerçekleşme sonuçları ve değerlendirmelerHazır | OK | `/activity-sections/reports/8?code=III.B.2.i` | — | 1441 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: ii. Performans denetim sonuçlarıBoş | OK | `/activity-sections/reports/8?code=III.B.2.ii` | — | 1344 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm metni kaydet: ii. Performans denetim sonuçlarıBoş | OK | `/activity-sections/reports/8?code=III.B.2.ii` | — | 1336 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: 3- Stratejik Plan Değerlendirme TablolarıBoş | OK | `/activity-sections/reports/8?code=III.B.3` | — | 1190 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm metni kaydet: 3- Stratejik Plan Değerlendirme TablolarıBoş | OK | `/activity-sections/reports/8?code=III.B.3` | — | 1248 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: 4- Performans Bilgi Sisteminin DeğerlendirilmesiBoş | OK | `/activity-sections/reports/8?code=III.B.4` | — | 1176 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm metni kaydet: 4- Performans Bilgi Sisteminin DeğerlendirilmesiBoş | OK | `/activity-sections/reports/8?code=III.B.4` | — | 1192 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: 5- Diğer HususlarBoş | OK | `/activity-sections/reports/8?code=III.B.5` | — | 1613 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm metni kaydet: 5- Diğer HususlarBoş | OK | `/activity-sections/reports/8?code=III.B.5` | — | 1276 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: IV- Kurumsal kabiliyet ve kapasitenin değerlendirilmesiBoş | OK | `/activity-sections/reports/8?code=IV` | — | 1169 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm metni kaydet: IV- Kurumsal kabiliyet ve kapasitenin değerlendirilmesiBoş | OK | `/activity-sections/reports/8?code=IV` | — | 1174 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: A- ÜstünlüklerBoş | OK | `/activity-sections/reports/8?code=IV.A` | — | 1147 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm metni kaydet: A- ÜstünlüklerBoş | OK | `/activity-sections/reports/8?code=IV.A` | — | 1209 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: B- ZayıflıklarBoş | OK | `/activity-sections/reports/8?code=IV.B` | — | 1141 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm metni kaydet: B- ZayıflıklarBoş | OK | `/activity-sections/reports/8?code=IV.B` | — | 1199 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: C- DeğerlendirmeBoş | OK | `/activity-sections/reports/8?code=IV.C` | — | 1087 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm metni kaydet: C- DeğerlendirmeBoş | OK | `/activity-sections/reports/8?code=IV.C` | — | 1158 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: V- Öneri ve tedbirlerBoş | OK | `/activity-sections/reports/8?code=V` | — | 1195 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm metni kaydet: V- Öneri ve tedbirlerBoş | OK | `/activity-sections/reports/8?code=V` | — | 1236 | — |
| Fen İşleri Müdürlüğü (Strateji) | Bölüm aç: EklerBoş | OK | `/activity-sections/reports/8?code=EKLER` | — | 1114 | — |
| Fen İşleri Müdürlüğü (Strateji) | Harcama yetkilisi güvence beyanı | OK | `/activity-sections/reports/8/assurances/EK-2` | — | 1038 | — |
| Fen İşleri Müdürlüğü (Strateji) | EK-2 beyan alanlarını kaydet | OK | `/activity-sections/reports/8/assurances/EK-2` | — | 1100 | — |
| Fen İşleri Müdürlüğü (Strateji) | Birim tabloları aç | OK | `/activity-sections/reports/8/unit-tables` | — | 1079 | — |
| Fen İşleri Müdürlüğü (Strateji) | Tablo 1 fiziksel yapı kaydet | OK | `/activity-sections/reports/8/unit-tables` | — | 1213 | — |
| Fen İşleri Müdürlüğü (Strateji) | Tablo 2 personel kaydet | OK | `/activity-sections/reports/8/unit-tables` | — | 1211 | — |
| Fen İşleri Müdürlüğü (Strateji) | Tablo 7 faaliyet çıktı ve maliyet kaydet (5 faaliyet) | OK | `/activity-sections/reports/8/unit-tables` | — | 1191 | — |
| Fen İşleri Müdürlüğü (Strateji) | Tablo 8 Bu yıl proje yok kaydet | OK | `/activity-sections/reports/8/unit-tables` | — | 1237 | — |
| Fen İşleri Müdürlüğü (Strateji) | Faaliyet fotoğrafı yükle | OK | `/activity-sections/reports/8/unit-tables` | — | 1229 | — |
| Fen İşleri Müdürlüğü (Strateji) | Gönderim öncesi birim raporu | OK | `/activity-sections/reports/8` | — | 1093 | — |
| Fen İşleri Müdürlüğü (Strateji) | Açıklamasız sapmayla gönderim denemesi | OK | `/activity-sections/reports/8/workflow/submit` | [PNG](../../screenshots/civ-228/097-fen.png) | 1567 | HTTP: 409 /activity-sections/reports/8/workflow/submit Beklenen engel: açıklamasız sapma ile gönderilemedi. |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Giriş ekranı | OK | `/login` | — | 759 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Hesapla giriş | OK | `/change-password` | — | 886 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Müdürlük hesabı ilk parola | OK | `/change-password` | [PNG](../../screenshots/civ-228/100-afet.png) | 2 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | İlk paroladan sonra modüller | OK | `/modules` | — | 774 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Aktarılan göstergeleri müdürlük hesabıyla kontrol et | OK | `/activity-reports/revisions/1` | — | 1384 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Müdürlük 2026 birim raporunu bul | OK | `/activity-sections` | — | 995 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Birim raporu ve bölüm ağacı | OK | `/activity-sections/reports/2` | — | 1127 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: Yönetici özetiBoş | OK | `/activity-sections/reports/2?code=OZET` | — | 1140 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm metni kaydet: Yönetici özetiBoş | OK | `/activity-sections/reports/2?code=OZET` | — | 1247 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: I- Genel bilgilerBoş | OK | `/activity-sections/reports/2?code=I` | — | 1167 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm metni kaydet: I- Genel bilgilerBoş | OK | `/activity-sections/reports/2?code=I` | — | 1171 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: A- Misyon ve VizyonBoş | OK | `/activity-sections/reports/2?code=I.A` | — | 1091 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm metni kaydet: A- Misyon ve VizyonBoş | OK | `/activity-sections/reports/2?code=I.A` | — | 1230 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: B- Yetki, Görev ve SorumluluklarBoş | OK | `/activity-sections/reports/2?code=I.B` | — | 1201 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm metni kaydet: B- Yetki, Görev ve SorumluluklarBoş | OK | `/activity-sections/reports/2?code=I.B` | — | 1228 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: C- İdareye İlişkin BilgilerBoş | OK | `/activity-sections/reports/2?code=I.C` | — | 1132 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm metni kaydet: C- İdareye İlişkin BilgilerBoş | OK | `/activity-sections/reports/2?code=I.C` | — | 1207 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: 1- Fiziksel YapıBoş | OK | `/activity-sections/reports/2?code=I.C.1` | — | 1164 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm metni kaydet: 1- Fiziksel YapıBoş | OK | `/activity-sections/reports/2?code=I.C.1` | — | 1183 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: 2- Teşkilat YapısıBoş | OK | `/activity-sections/reports/2?code=I.C.2` | — | 1099 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm metni kaydet: 2- Teşkilat YapısıBoş | OK | `/activity-sections/reports/2?code=I.C.2` | — | 1212 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: 3- Teknoloji ve Bilişim AltyapısıBoş | OK | `/activity-sections/reports/2?code=I.C.3` | — | 1104 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm metni kaydet: 3- Teknoloji ve Bilişim AltyapısıBoş | OK | `/activity-sections/reports/2?code=I.C.3` | — | 1132 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: 4- İnsan KaynaklarıBoş | OK | `/activity-sections/reports/2?code=I.C.4` | — | 1058 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm metni kaydet: 4- İnsan KaynaklarıBoş | OK | `/activity-sections/reports/2?code=I.C.4` | — | 1275 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: 5- Sunulan HizmetlerBoş | OK | `/activity-sections/reports/2?code=I.C.5` | — | 1140 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm metni kaydet: 5- Sunulan HizmetlerBoş | OK | `/activity-sections/reports/2?code=I.C.5` | — | 1221 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: 6- Yönetim ve İç Kontrol SistemiBoş | OK | `/activity-sections/reports/2?code=I.C.6` | — | 1164 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm metni kaydet: 6- Yönetim ve İç Kontrol SistemiBoş | OK | `/activity-sections/reports/2?code=I.C.6` | — | 1236 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: D- Diğer HususlarBoş | OK | `/activity-sections/reports/2?code=I.D` | — | 1123 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm metni kaydet: D- Diğer HususlarBoş | OK | `/activity-sections/reports/2?code=I.D` | — | 1186 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: II- Amaçlar ve hedeflerBoş | OK | `/activity-sections/reports/2?code=II` | — | 1166 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm metni kaydet: II- Amaçlar ve hedeflerBoş | OK | `/activity-sections/reports/2?code=II` | — | 1317 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: A- Temel Politika ve ÖnceliklerBoş | OK | `/activity-sections/reports/2?code=II.A` | — | 1132 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm metni kaydet: A- Temel Politika ve ÖnceliklerBoş | OK | `/activity-sections/reports/2?code=II.A` | — | 1276 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: B- İdarenin Stratejik Planında Yer Alan Amaç ve HedeflerBoş | OK | `/activity-sections/reports/2?code=II.B` | — | 1140 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm metni kaydet: B- İdarenin Stratejik Planında Yer Alan Amaç ve HedeflerBoş | OK | `/activity-sections/reports/2?code=II.B` | — | 1295 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: C- Diğer HususlarBoş | OK | `/activity-sections/reports/2?code=II.C` | — | 1648 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm metni kaydet: C- Diğer HususlarBoş | OK | `/activity-sections/reports/2?code=II.C` | — | 1270 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: III- Faaliyetlere ilişkin bilgi ve değerlendirmelerBoş | OK | `/activity-sections/reports/2?code=III` | — | 1195 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm metni kaydet: III- Faaliyetlere ilişkin bilgi ve değerlendirmelerBoş | OK | `/activity-sections/reports/2?code=III` | — | 1213 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: A- Malî BilgilerBoş | OK | `/activity-sections/reports/2?code=III.A` | — | 1117 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: 1- Bütçe Uygulama SonuçlarıBoş | OK | `/activity-sections/reports/2?code=III.A.1` | — | 1131 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: 2- Temel Malî Tablolara İlişkin AçıklamalarBoş | OK | `/activity-sections/reports/2?code=III.A.2` | — | 1161 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: 3- Malî Denetim SonuçlarıBoş | OK | `/activity-sections/reports/2?code=III.A.3` | — | 1072 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm metni kaydet: 3- Malî Denetim SonuçlarıBoş | OK | `/activity-sections/reports/2?code=III.A.3` | — | 1262 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: 4- Diğer HususlarBoş | OK | `/activity-sections/reports/2?code=III.A.4` | — | 1146 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm metni kaydet: 4- Diğer HususlarBoş | OK | `/activity-sections/reports/2?code=III.A.4` | — | 1172 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: B- Performans BilgileriBoş | OK | `/activity-sections/reports/2?code=III.B` | — | 1100 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm metni kaydet: B- Performans BilgileriBoş | OK | `/activity-sections/reports/2?code=III.B` | — | 1298 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: 1- Program, Alt Program, Faaliyet BilgileriBoş | OK | `/activity-sections/reports/2?code=III.B.1` | — | 1286 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm metni kaydet: 1- Program, Alt Program, Faaliyet BilgileriBoş | OK | `/activity-sections/reports/2?code=III.B.1` | — | 1262 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: 2- Performans Sonuçlarının DeğerlendirilmesiBoş | OK | `/activity-sections/reports/2?code=III.B.2` | — | 1238 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm metni kaydet: 2- Performans Sonuçlarının DeğerlendirilmesiBoş | OK | `/activity-sections/reports/2?code=III.B.2` | — | 1243 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: i. Alt program hedef ve göstergeleriyle ilgili gerçekleşme sonuçları ve değerlendirmelerHazır | OK | `/activity-sections/reports/2?code=III.B.2.i` | — | 1134 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: ii. Performans denetim sonuçlarıBoş | OK | `/activity-sections/reports/2?code=III.B.2.ii` | — | 1098 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm metni kaydet: ii. Performans denetim sonuçlarıBoş | OK | `/activity-sections/reports/2?code=III.B.2.ii` | — | 1257 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: 3- Stratejik Plan Değerlendirme TablolarıBoş | OK | `/activity-sections/reports/2?code=III.B.3` | — | 1115 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm metni kaydet: 3- Stratejik Plan Değerlendirme TablolarıBoş | OK | `/activity-sections/reports/2?code=III.B.3` | — | 1221 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: 4- Performans Bilgi Sisteminin DeğerlendirilmesiBoş | OK | `/activity-sections/reports/2?code=III.B.4` | — | 1124 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm metni kaydet: 4- Performans Bilgi Sisteminin DeğerlendirilmesiBoş | OK | `/activity-sections/reports/2?code=III.B.4` | — | 1199 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: 5- Diğer HususlarBoş | OK | `/activity-sections/reports/2?code=III.B.5` | — | 1187 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm metni kaydet: 5- Diğer HususlarBoş | OK | `/activity-sections/reports/2?code=III.B.5` | — | 1316 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: IV- Kurumsal kabiliyet ve kapasitenin değerlendirilmesiBoş | OK | `/activity-sections/reports/2?code=IV` | — | 1087 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm metni kaydet: IV- Kurumsal kabiliyet ve kapasitenin değerlendirilmesiBoş | OK | `/activity-sections/reports/2?code=IV` | — | 1242 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: A- ÜstünlüklerBoş | OK | `/activity-sections/reports/2?code=IV.A` | — | 1232 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm metni kaydet: A- ÜstünlüklerBoş | OK | `/activity-sections/reports/2?code=IV.A` | — | 1251 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: B- ZayıflıklarBoş | OK | `/activity-sections/reports/2?code=IV.B` | — | 1146 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm metni kaydet: B- ZayıflıklarBoş | OK | `/activity-sections/reports/2?code=IV.B` | — | 1246 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: C- DeğerlendirmeBoş | OK | `/activity-sections/reports/2?code=IV.C` | — | 1286 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm metni kaydet: C- DeğerlendirmeBoş | OK | `/activity-sections/reports/2?code=IV.C` | — | 1422 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: V- Öneri ve tedbirlerBoş | OK | `/activity-sections/reports/2?code=V` | — | 1287 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm metni kaydet: V- Öneri ve tedbirlerBoş | OK | `/activity-sections/reports/2?code=V` | — | 1183 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Bölüm aç: EklerBoş | OK | `/activity-sections/reports/2?code=EKLER` | — | 1180 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Harcama yetkilisi güvence beyanı | OK | `/activity-sections/reports/2/assurances/EK-2` | — | 1114 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | EK-2 beyan alanlarını kaydet | OK | `/activity-sections/reports/2/assurances/EK-2` | — | 1218 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Birim tabloları aç | OK | `/activity-sections/reports/2/unit-tables` | — | 1078 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Tablo 1 fiziksel yapı kaydet | OK | `/activity-sections/reports/2/unit-tables` | — | 1255 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Tablo 2 personel kaydet | OK | `/activity-sections/reports/2/unit-tables` | — | 1271 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Tablo 7 faaliyet çıktı ve maliyet kaydet (9 faaliyet) | OK | `/activity-sections/reports/2/unit-tables` | — | 1220 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Tablo 8 Bu yıl proje yok kaydet | OK | `/activity-sections/reports/2/unit-tables` | — | 1288 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Faaliyet fotoğrafı yükle | OK | `/activity-sections/reports/2/unit-tables` | — | 1285 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Gönderim öncesi birim raporu | OK | `/activity-sections/reports/2` | — | 1163 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Açıklamasız sapmayla gönderim denemesi | OK | `/activity-sections/reports/2/workflow/submit` | [PNG](../../screenshots/civ-228/181-afet.png) | 1556 | HTTP: 409 /activity-sections/reports/2/workflow/submit Beklenen engel: açıklamasız sapma ile gönderilemedi. |
| Özel Kalem Müdürlüğü (Strateji) | Giriş ekranı | OK | `/login` | — | 821 | — |
| Özel Kalem Müdürlüğü (Strateji) | Hesapla giriş | OK | `/change-password` | — | 850 | — |
| Özel Kalem Müdürlüğü (Strateji) | Müdürlük hesabı ilk parola | OK | `/change-password` | [PNG](../../screenshots/civ-228/184-ozel.png) | 2 | — |
| Özel Kalem Müdürlüğü (Strateji) | İlk paroladan sonra modüller | OK | `/modules` | — | 848 | — |
| Özel Kalem Müdürlüğü (Strateji) | Aktarılan göstergeleri müdürlük hesabıyla kontrol et | OK | `/activity-reports/revisions/1` | — | 1394 | — |
| Özel Kalem Müdürlüğü (Strateji) | Müdürlük 2026 birim raporunu bul | OK | `/activity-sections` | — | 1040 | — |
| Özel Kalem Müdürlüğü (Strateji) | Birim raporu ve bölüm ağacı | OK | `/activity-sections/reports/31` | — | 1187 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: Yönetici özetiBoş | OK | `/activity-sections/reports/31?code=OZET` | — | 1142 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm metni kaydet: Yönetici özetiBoş | OK | `/activity-sections/reports/31?code=OZET` | — | 1246 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: I- Genel bilgilerBoş | OK | `/activity-sections/reports/31?code=I` | — | 1203 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm metni kaydet: I- Genel bilgilerBoş | OK | `/activity-sections/reports/31?code=I` | — | 1181 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: A- Misyon ve VizyonBoş | OK | `/activity-sections/reports/31?code=I.A` | — | 1114 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm metni kaydet: A- Misyon ve VizyonBoş | OK | `/activity-sections/reports/31?code=I.A` | — | 1189 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: B- Yetki, Görev ve SorumluluklarBoş | OK | `/activity-sections/reports/31?code=I.B` | — | 1165 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm metni kaydet: B- Yetki, Görev ve SorumluluklarBoş | OK | `/activity-sections/reports/31?code=I.B` | — | 1223 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: C- İdareye İlişkin BilgilerBoş | OK | `/activity-sections/reports/31?code=I.C` | — | 1076 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm metni kaydet: C- İdareye İlişkin BilgilerBoş | OK | `/activity-sections/reports/31?code=I.C` | — | 1799 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: 1- Fiziksel YapıBoş | OK | `/activity-sections/reports/31?code=I.C.1` | — | 1244 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm metni kaydet: 1- Fiziksel YapıBoş | OK | `/activity-sections/reports/31?code=I.C.1` | — | 1308 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: 2- Teşkilat YapısıBoş | OK | `/activity-sections/reports/31?code=I.C.2` | — | 1218 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm metni kaydet: 2- Teşkilat YapısıBoş | OK | `/activity-sections/reports/31?code=I.C.2` | — | 1313 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: 3- Teknoloji ve Bilişim AltyapısıBoş | OK | `/activity-sections/reports/31?code=I.C.3` | — | 1169 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm metni kaydet: 3- Teknoloji ve Bilişim AltyapısıBoş | OK | `/activity-sections/reports/31?code=I.C.3` | — | 1220 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: 4- İnsan KaynaklarıBoş | OK | `/activity-sections/reports/31?code=I.C.4` | — | 1148 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm metni kaydet: 4- İnsan KaynaklarıBoş | OK | `/activity-sections/reports/31?code=I.C.4` | — | 1223 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: 5- Sunulan HizmetlerBoş | OK | `/activity-sections/reports/31?code=I.C.5` | — | 1208 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm metni kaydet: 5- Sunulan HizmetlerBoş | OK | `/activity-sections/reports/31?code=I.C.5` | — | 1273 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: 6- Yönetim ve İç Kontrol SistemiBoş | OK | `/activity-sections/reports/31?code=I.C.6` | — | 1147 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm metni kaydet: 6- Yönetim ve İç Kontrol SistemiBoş | OK | `/activity-sections/reports/31?code=I.C.6` | — | 1246 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: D- Diğer HususlarBoş | OK | `/activity-sections/reports/31?code=I.D` | — | 1148 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm metni kaydet: D- Diğer HususlarBoş | OK | `/activity-sections/reports/31?code=I.D` | — | 1279 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: II- Amaçlar ve hedeflerBoş | OK | `/activity-sections/reports/31?code=II` | — | 1165 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm metni kaydet: II- Amaçlar ve hedeflerBoş | OK | `/activity-sections/reports/31?code=II` | — | 1290 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: A- Temel Politika ve ÖnceliklerBoş | OK | `/activity-sections/reports/31?code=II.A` | — | 1090 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm metni kaydet: A- Temel Politika ve ÖnceliklerBoş | OK | `/activity-sections/reports/31?code=II.A` | — | 1280 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: B- İdarenin Stratejik Planında Yer Alan Amaç ve HedeflerBoş | OK | `/activity-sections/reports/31?code=II.B` | — | 1108 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm metni kaydet: B- İdarenin Stratejik Planında Yer Alan Amaç ve HedeflerBoş | OK | `/activity-sections/reports/31?code=II.B` | — | 1176 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: C- Diğer HususlarBoş | OK | `/activity-sections/reports/31?code=II.C` | — | 1095 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm metni kaydet: C- Diğer HususlarBoş | OK | `/activity-sections/reports/31?code=II.C` | — | 1232 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: III- Faaliyetlere ilişkin bilgi ve değerlendirmelerBoş | OK | `/activity-sections/reports/31?code=III` | — | 1129 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm metni kaydet: III- Faaliyetlere ilişkin bilgi ve değerlendirmelerBoş | OK | `/activity-sections/reports/31?code=III` | — | 1224 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: A- Malî BilgilerBoş | OK | `/activity-sections/reports/31?code=III.A` | — | 1135 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: 1- Bütçe Uygulama SonuçlarıBoş | OK | `/activity-sections/reports/31?code=III.A.1` | — | 1151 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: 2- Temel Malî Tablolara İlişkin AçıklamalarBoş | OK | `/activity-sections/reports/31?code=III.A.2` | — | 1095 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: 3- Malî Denetim SonuçlarıBoş | OK | `/activity-sections/reports/31?code=III.A.3` | — | 1166 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm metni kaydet: 3- Malî Denetim SonuçlarıBoş | OK | `/activity-sections/reports/31?code=III.A.3` | — | 1165 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: 4- Diğer HususlarBoş | OK | `/activity-sections/reports/31?code=III.A.4` | — | 1092 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm metni kaydet: 4- Diğer HususlarBoş | OK | `/activity-sections/reports/31?code=III.A.4` | — | 1176 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: B- Performans BilgileriBoş | OK | `/activity-sections/reports/31?code=III.B` | — | 1147 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm metni kaydet: B- Performans BilgileriBoş | OK | `/activity-sections/reports/31?code=III.B` | — | 1166 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: 1- Program, Alt Program, Faaliyet BilgileriBoş | OK | `/activity-sections/reports/31?code=III.B.1` | — | 1168 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm metni kaydet: 1- Program, Alt Program, Faaliyet BilgileriBoş | OK | `/activity-sections/reports/31?code=III.B.1` | — | 1246 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: 2- Performans Sonuçlarının DeğerlendirilmesiBoş | OK | `/activity-sections/reports/31?code=III.B.2` | — | 1113 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm metni kaydet: 2- Performans Sonuçlarının DeğerlendirilmesiBoş | OK | `/activity-sections/reports/31?code=III.B.2` | — | 1247 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: i. Alt program hedef ve göstergeleriyle ilgili gerçekleşme sonuçları ve değerlendirmelerHazır | OK | `/activity-sections/reports/31?code=III.B.2.i` | — | 1099 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: ii. Performans denetim sonuçlarıBoş | OK | `/activity-sections/reports/31?code=III.B.2.ii` | — | 1154 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm metni kaydet: ii. Performans denetim sonuçlarıBoş | OK | `/activity-sections/reports/31?code=III.B.2.ii` | — | 1236 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: 3- Stratejik Plan Değerlendirme TablolarıBoş | OK | `/activity-sections/reports/31?code=III.B.3` | — | 1118 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm metni kaydet: 3- Stratejik Plan Değerlendirme TablolarıBoş | OK | `/activity-sections/reports/31?code=III.B.3` | — | 1303 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: 4- Performans Bilgi Sisteminin DeğerlendirilmesiBoş | OK | `/activity-sections/reports/31?code=III.B.4` | — | 1335 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm metni kaydet: 4- Performans Bilgi Sisteminin DeğerlendirilmesiBoş | OK | `/activity-sections/reports/31?code=III.B.4` | — | 1192 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: 5- Diğer HususlarBoş | OK | `/activity-sections/reports/31?code=III.B.5` | — | 1243 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm metni kaydet: 5- Diğer HususlarBoş | OK | `/activity-sections/reports/31?code=III.B.5` | — | 1183 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: IV- Kurumsal kabiliyet ve kapasitenin değerlendirilmesiBoş | OK | `/activity-sections/reports/31?code=IV` | — | 1092 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm metni kaydet: IV- Kurumsal kabiliyet ve kapasitenin değerlendirilmesiBoş | OK | `/activity-sections/reports/31?code=IV` | — | 1158 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: A- ÜstünlüklerBoş | OK | `/activity-sections/reports/31?code=IV.A` | — | 1212 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm metni kaydet: A- ÜstünlüklerBoş | OK | `/activity-sections/reports/31?code=IV.A` | — | 1174 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: B- ZayıflıklarBoş | OK | `/activity-sections/reports/31?code=IV.B` | — | 1049 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm metni kaydet: B- ZayıflıklarBoş | OK | `/activity-sections/reports/31?code=IV.B` | — | 1203 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: C- DeğerlendirmeBoş | OK | `/activity-sections/reports/31?code=IV.C` | — | 1084 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm metni kaydet: C- DeğerlendirmeBoş | OK | `/activity-sections/reports/31?code=IV.C` | — | 1186 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: V- Öneri ve tedbirlerBoş | OK | `/activity-sections/reports/31?code=V` | — | 1116 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm metni kaydet: V- Öneri ve tedbirlerBoş | OK | `/activity-sections/reports/31?code=V` | — | 1292 | — |
| Özel Kalem Müdürlüğü (Strateji) | Bölüm aç: EklerBoş | OK | `/activity-sections/reports/31?code=EKLER` | — | 1181 | — |
| Özel Kalem Müdürlüğü (Strateji) | Harcama yetkilisi güvence beyanı | OK | `/activity-sections/reports/31/assurances/EK-2` | — | 999 | — |
| Özel Kalem Müdürlüğü (Strateji) | EK-2 beyan alanlarını kaydet | OK | `/activity-sections/reports/31/assurances/EK-2` | — | 1049 | — |
| Özel Kalem Müdürlüğü (Strateji) | Birim tabloları aç | OK | `/activity-sections/reports/31/unit-tables` | — | 1026 | — |
| Özel Kalem Müdürlüğü (Strateji) | Tablo 1 fiziksel yapı kaydet | OK | `/activity-sections/reports/31/unit-tables` | — | 1252 | — |
| Özel Kalem Müdürlüğü (Strateji) | Tablo 2 personel kaydet | OK | `/activity-sections/reports/31/unit-tables` | — | 1230 | — |
| Özel Kalem Müdürlüğü (Strateji) | Tablo 7 faaliyet çıktı ve maliyet kaydet (4 faaliyet) | OK | `/activity-sections/reports/31/unit-tables` | — | 1231 | — |
| Özel Kalem Müdürlüğü (Strateji) | Tablo 8 Bu yıl proje yok kaydet | OK | `/activity-sections/reports/31/unit-tables` | — | 1243 | — |
| Özel Kalem Müdürlüğü (Strateji) | Faaliyet fotoğrafı yükle | OK | `/activity-sections/reports/31/unit-tables` | — | 1311 | — |
| Özel Kalem Müdürlüğü (Strateji) | Gönderim öncesi birim raporu | OK | `/activity-sections/reports/31` | — | 1131 | — |
| Özel Kalem Müdürlüğü (Strateji) | Açıklamasız sapmayla gönderim denemesi | OK | `/activity-sections/reports/31/workflow/submit` | [PNG](../../screenshots/civ-228/265-ozel.png) | 1699 | HTTP: 409 /activity-sections/reports/31/workflow/submit Beklenen engel: açıklamasız sapma ile gönderilemedi. |
| Strateji Kullanıcısı | Açıklamalı Excel: Excel yükleme alanı | OK | `/activity-reports` | — | 890 | — |
| Strateji Kullanıcısı | Excel düzeltme önizlemesi | OK | `/activity-reports/imports/2` | — | 2076 | Önizleme: Değişmedi: 13 · Eşleşti: 3 · Onay gerekiyor: 4. Elle seçilen satır: 4 / 20. |
| Strateji Kullanıcısı | Excel düzeltme sonucu | OK | `/activity-reports/imports/2` | [PNG](../../screenshots/civ-228/268-strategy_user.png) | 1361 | Sonuç: Değişmedi: 17 · Yazıldı: 3. Excel 2. satır · Yazıldı · Yeni gerçekleşme revizyonu kaydedildi. · 2 · TOPLA: Q1 + Q2 + Q3 + Q4 &#124; Excel 3. satır · Değişmedi · Mevcut değer ve açıklama aynı; yeni revizyon yazılmadı. &#124; Excel 4. satır · Değişmedi · Mevcut değer ve açıklama aynı; yeni revizyon yazılmadı. &#124; Excel 5. satır · Değişmedi · Mevcut değer ve açıklama aynı; yeni revizyon yazılmadı. &#124; Excel 6. satır · Değişmedi · Mevcut değer ve açıklama aynı; yeni revizyon yazılmadı. &#124; Excel 7. satır · Değişmedi · Mevcut değer ve açıklama aynı; yeni revizyon yazılmadı. |
| Fen İşleri Müdürlüğü (Strateji) | Birim raporunu gönder öncesi | OK | `/activity-sections/reports/8` | — | 1166 | — |
| Fen İşleri Müdürlüğü (Strateji) | Birim raporunu gönder | OK | `/activity-sections/reports/8` | [PNG](../../screenshots/civ-228/270-fen.png) | 2386 | — |
| Strateji Müdürü | Strateji birim incelemesi | OK | `/activity-sections/reports/8` | [PNG](../../screenshots/civ-228/271-strategy.png) | 1005 | — |
| Strateji Müdürü | Gerekçeli iade | OK | `/activity-sections/reports/8` | [PNG](../../screenshots/civ-228/272-strategy.png) | 1443 | — |
| Fen İşleri Müdürlüğü (Strateji) | İade notunu gör ve düzelt | OK | `/activity-sections/reports/8?code=III.B.1` | — | 1158 | — |
| Fen İşleri Müdürlüğü (Strateji) | İade notuna göre düzeltmeyi kaydet | OK | `/activity-sections/reports/8?code=III.B.1` | [PNG](../../screenshots/civ-228/274-fen.png) | 1163 | — |
| Fen İşleri Müdürlüğü (Strateji) | Düzelt ve yeniden gönder öncesi | OK | `/activity-sections/reports/8` | — | 1167 | — |
| Fen İşleri Müdürlüğü (Strateji) | Düzelt ve yeniden gönder | OK | `/activity-sections/reports/8` | [PNG](../../screenshots/civ-228/276-fen.png) | 1601 | — |
| Strateji Müdürü | Strateji yeniden inceleme | OK | `/activity-sections/reports/8` | — | 981 | — |
| Strateji Müdürü | Strateji bağımsız birim onayı | OK | `/activity-sections/reports/8` | [PNG](../../screenshots/civ-228/278-strategy.png) | 988 | — |
| Strateji Müdürü | Onaylı Word olarak indir · Fen İşleri Müdürlüğü | OK | `/activity-sections/reports/8` | [PNG](../../screenshots/civ-228/279-strategy.png) | 415 | 45472 bayt; SHA256: f85bc7c57309f80ccebab7a02f0d85ef6d9b77ec0b6344e199cbbc7af0ebf421; dosya başlığı doğrulandı. |
| Strateji Müdürü | Onaylı PDF olarak indir · Fen İşleri Müdürlüğü | OK | `/activity-sections/reports/8` | [PNG](../../screenshots/civ-228/280-strategy.png) | 334 | 67972 bayt; SHA256: cdeb98dbe756c75f1ffbe743ecca715ea2ff2ae0701df650105c35f7f868f060; dosya başlığı doğrulandı. |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Birim raporunu gönder öncesi | OK | `/activity-sections/reports/2` | — | 1151 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Birim raporunu gönder | OK | `/activity-sections/reports/2` | — | 1689 | — |
| Strateji Müdürü | Strateji birim incelemesi | OK | `/activity-sections/reports/2` | — | 918 | — |
| Strateji Müdürü | Gerekçeli iade | OK | `/activity-sections/reports/2` | — | 1180 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | İade notunu gör ve düzelt | OK | `/activity-sections/reports/2?code=III.B.1` | — | 1099 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | İade notuna göre düzeltmeyi kaydet | OK | `/activity-sections/reports/2?code=III.B.1` | — | 1285 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Düzelt ve yeniden gönder öncesi | OK | `/activity-sections/reports/2` | — | 1123 | — |
| Afet İşleri ve Risk Değerlendirme Müdürlüğü (Strateji) | Düzelt ve yeniden gönder | OK | `/activity-sections/reports/2` | — | 1754 | — |
| Strateji Müdürü | Strateji yeniden inceleme | OK | `/activity-sections/reports/2` | — | 972 | — |
| Strateji Müdürü | Strateji bağımsız birim onayı | OK | `/activity-sections/reports/2` | — | 1077 | — |
| Strateji Müdürü | Onaylı Word olarak indir · Afet İşleri ve Risk Değerlendirme Müdürlüğü | OK | `/activity-sections/reports/2` | [PNG](../../screenshots/civ-228/291-strategy.png) | 528 | 45826 bayt; SHA256: 031923d5b8a713bc07afadf1c328c0fde6a6820b2277f73a25bc4dd695a9669e; dosya başlığı doğrulandı. |
| Strateji Müdürü | Onaylı PDF olarak indir · Afet İşleri ve Risk Değerlendirme Müdürlüğü | OK | `/activity-sections/reports/2` | [PNG](../../screenshots/civ-228/292-strategy.png) | 197 | 70255 bayt; SHA256: c4e4276b054be19c87da123b5b1694c540ba0ab258224127b3edcd305b25598c; dosya başlığı doğrulandı. |
| Özel Kalem Müdürlüğü (Strateji) | Birim raporunu gönder öncesi | OK | `/activity-sections/reports/31` | — | 1064 | — |
| Özel Kalem Müdürlüğü (Strateji) | Birim raporunu gönder | OK | `/activity-sections/reports/31` | — | 1741 | — |
| Strateji Müdürü | Strateji birim incelemesi | OK | `/activity-sections/reports/31` | — | 1020 | — |
| Strateji Müdürü | Gerekçeli iade | OK | `/activity-sections/reports/31` | — | 1232 | — |
| Özel Kalem Müdürlüğü (Strateji) | İade notunu gör ve düzelt | OK | `/activity-sections/reports/31?code=III.B.1` | — | 1140 | — |
| Özel Kalem Müdürlüğü (Strateji) | İade notuna göre düzeltmeyi kaydet | OK | `/activity-sections/reports/31?code=III.B.1` | — | 1292 | — |
| Özel Kalem Müdürlüğü (Strateji) | Düzelt ve yeniden gönder öncesi | OK | `/activity-sections/reports/31` | — | 1109 | — |
| Özel Kalem Müdürlüğü (Strateji) | Düzelt ve yeniden gönder | OK | `/activity-sections/reports/31` | — | 1634 | — |
| Strateji Müdürü | Strateji yeniden inceleme | OK | `/activity-sections/reports/31` | — | 1019 | — |
| Strateji Müdürü | Strateji bağımsız birim onayı | OK | `/activity-sections/reports/31` | — | 951 | — |
| Strateji Müdürü | Onaylı Word olarak indir · Özel Kalem Müdürlüğü | OK | `/activity-sections/reports/31` | [PNG](../../screenshots/civ-228/303-strategy.png) | 430 | 45326 bayt; SHA256: 5a0d90b21a16d355f3fe052b4642dc4668b82c3c7e7ac9cdd827d0cc1d166e05; dosya başlığı doğrulandı. |
| Strateji Müdürü | Onaylı PDF olarak indir · Özel Kalem Müdürlüğü | OK | `/activity-sections/reports/31` | [PNG](../../screenshots/civ-228/304-strategy.png) | 164 | 67679 bayt; SHA256: db262504950fbebed0e179d9625a9de7bad1be64946c05935c4dde5b9401050f; dosya başlığı doğrulandı. |

# Civensa 5.0 Performans Programı iyileştirmeleri

Bu sürüm, v4.2.0 kodundaki nihai performans programı uyumluluğu sorunlarını gideren bir geliştirme paketidir. Belediye PDF'sini veya canlı veritabanını değiştirmez. Verileri yeni alanlara kendiliğinden tahmin ederek dağıtmaz.

## Hazır olan değişiklikler

- Bağımsız performans kartları: aynı alt program altında farklı gerekçe, hedef, açıklama, hesaplama yöntemi, veri kaynağı, sorumlu idare, dipnot, kaynak sayfa, hizmet alanı ve stratejik plan/PH metni.
- Gösterge için geçmiş gerçekleşme dahil altı yıl/tür kolonu. Kaynak birimleri serbestçe korunur. Sayı/oran çelişkisi engelleyici hata yerine uyarıdır.
- Kesin ondalık veri saklama ve Türkçe sayı gösterimi; parasal değerlerde iki, göstergelerde altı ondalık basamak. Ham kaynak ve inceleme durumu korunur. Belirsiz ayraçlar otomatik düzeltilmez.
- Yeni dönemde sahte sıfır değer üretmeme; eksik ve gerçek sıfırı ayırma. Kısmi toplamı tamamlanmış bütçe olarak göstermeme.
- Faaliyet maliyetinde bütçe içi/dışı ayrı giriş; toplamın bunlardan hesaplanması. Müdürlük ortak maliyet tablosu tek kez üretilir.
- Dokuz ekonomik gider türü, beş kolon, program grubu ve finansman kaynağına göre toplu giriş tablosu. Gönderim/onayda genel toplam ve finansman dağılımı mutabakatı; açık sıfır hücreleri kontrolü.
- Resmî faaliyet kataloğu, birden çok sorumlu harcama birimi ve yerel faaliyet bağlantıları; kaynak kodu ve sırası.
- Döneme göre müdürlük adı/sırası/kapsamı. Gerekçeli sıfır bütçeli ve kapsam dışı birimler için hayalî kart açılması gerekmez.
- Metin, tablo, PNG/JPEG görsel bölümleri; kitap başı/sonu konumu. Seçili sürümün verisinden kurum/müdürlük ekonomik tabloları ve bütçe grafikleri.
- Tam gönderim/karar anlık görüntüsü. Bütünlük özetiyle dondurulan nihai yayın sürümü; aynı arşivden Word/PDF/JSON üretimi.
- Kilit, müdürlük sahipliği, dönem sınırı ve CSRF kontrolleri. Onaylı eski paket için eksik kartlı Word üretimi engellenir.

## Mevcut kayıtların hazırlanması

1. Yeni sürüm ilk açıldığında eski göstergeler ve faaliyetler yerinde kalır. PDF'deki kart ayrımı eski veride bulunmadığından otomatik kart eşleştirmesi yapılmaz.
2. Müdürlük kullanıcısı **Rapor Hazırlığı** ekranında kartları kaynaktan oluşturur; mevcut gösterge ve faaliyetleri doğru karta atar.
3. `value` türündeki eski geçmiş değerler otomatik olarak gerçekleşme sayılmaz; yıl/değer türü kaynakla doğrulanır. Belirsiz kaynak değerleri ayrıca doğrulanır.
4. Strateji resmî katalog ve dönem kapsamını hazırlar. Müdürlük finansman ayrımını ve ekonomik tablosunu tamamlar. Eksik hücre ile 0 farklıdır.
5. Gönderim → Strateji incelemesi → iade/onay akışı korunur. Nihai Rapor ekranı tekrar kontrollerden sonra yeni sürümü dondurur.

## Sınırlar ve kaynak kararı gereken konular

- PDF'deki hatalı veya çelişkili tutarlar bu paketle düzeltilmemiştir. Doğru değerler ilgili müdürlüklerce teyit edilmelidir.
- Eski toplu Word aktarımı yeni kart/ekonomik veri bulunan müdürlüğün üzerine yazamaz. Güncellemeler kart ekranından veya ayrı taslak dönemden yapılır. PDF'den otomatik ve eksiksiz veri aktarımı bu sürümün özelliği değildir.
- Stratejik plan/PH bağlantıları kaynak metni olarak tutulur; kod düzeyinde ayrı bir stratejik plan ilişki grafiği kurulmamıştır.
- Genel bilgi tabloları ve görselleri editoryal içeriktir. İçerik doğruluğu/satır kapsamı otomatik belediye kayıt sistemi entegrasyonuyla doğrulanmaz.
- Döner sermaye ve genel yönetim/destek giderlerinin programlara dağıtım anahtarı kaynakta teyit edilmeden üretilmez. Bu özel dağıtım cetvelleri bölüm tablosu olarak girilebilir; otomatik mali dağıtım motoru değildir.
- Word/PDF işlevsel kitap çıktısı üretir; kaynak PDF'nin bire bir sayfa tasarımını taklit etmez. Otomatik sayfa referanslı içindekiler ve mevzuat şablonu eşdeğerliği ayrıca kabul kontrolü gerektirir.
- Dolu v4 şema geçişi GitHub Actions içinde geçici PostgreSQL 16 veritabanında da test edilmiştir. Gerçek üretim sürümü ve tam üretim yedeğiyle geçiş provası canlıya alma öncesinde ayrıca yapılmalıdır.

## Doğrulama

`python -m pip install -r requirements-dev.txt` ve `python -m pytest -q`.

35 test (yerelde PostgreSQL servisi yoksa 34 geçer, 1 atlanır); sayı hassasiyeti, belirsiz kaynak, eksik/sıfır, finansman mutabakatı, kart ayrımı, kilit/sahiplik, dönem, CSRF/görsel, yayın bütünlüğü, Word/PDF içerik eşliği ve dolu v4 şema geçişi.

21 Eylül 2026 tarihli 2027 taslağı içeren mantıksal yedeğin yalnız yerel test kopyası taşındı: 17 eski tablonun satır sayıları, toplam 544 gösterge ve 462 faaliyet korundu. Kullanıcı parola alanları testte devre dışı değerlerle dolduruldu. Bu mantıksal yedek kimlik doğrulama sırlarını içermediği için tam üretim geri dönüş yedeği yerine geçmez.

## Canlıya geçiş

Bu paket otomatik canlıya alınmaz. Önce uygulama sürümü, PostgreSQL sürümü ve tam veritabanı yedeği kaydedilmeli; yedeğin geri yüklenmesi denenmelidir. Eski sayısal kayıtlar yeni alanlara dönüştürülmeden önce ham değerleri saklanır. Hassasiyet kaybı ihtimali olan hücreler incelemeye işaretlenir. Beklenmeyen sınır dışı sayıda geçiş durur.

`alembic upgrade head` yeni `e5a0b1c2d3e4` geçişini uygular. Eski veri tipi yeni kart/ham değer/yayın verisini saklayamadığından kayıplı `downgrade` engellenir. Geri dönüş, geçiş öncesi tam veritabanı yedeğinin ayrı veritabanına geri yüklenmesi ve v4.2.0 uygulamasının o veritabanına bağlanmasıyla yapılır. Geçiş sonrası yeni kayıtlar varsa geri dönüşten önce ayrı arşivlenmelidir.

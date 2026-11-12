# CIV-217 — CIV-214 değiştirme aracının canlı 2027 engelleri

## Ne oldu (kanıt)

Sahibin canlı salt okunur planı (CIV-214 sürümü) 341 engel verdi, 0 satır yazdı.
Sahibin iki salt okunur incelemesi (0 satır yazıldı) ve 30 Ekim yükleme kodunun
(`310546c`) yerel yeniden üretimi şu üç kökü gösterdi:

1. **Ön baskıdan kalan katalog.** D-135 ön baskı temizliği 2027 program/alt
   program satırlarını bıraktı. 30 Ekim ONAYLI yüklemesi `_get_or_create_subprogram`
   ile mevcut alt programların metnini yalnız boşsa doldurur; dolu eski metni
   değiştirmez. Canlıda 23 kullanılmayan (büyük harfli) program, 41 kullanılmayan
   alt program ve eski ön baskı Gerekçe/Amaç metnini taşıyan alt programlar kaldı.
   İçerik satırları doğru adlı alt programlara bağlı. Alt program metni imzanın
   parçası olduğu için her müdürlüğün bütün çocuk satırları "uyuşmuyor" göründü.
2. **Köken özeti.** `approved_book_provenance()` her paketin `applied_hash` değerini
   bugünkü serileştiriciyle yeniden hesaplar; sonraki migrasyonlardan önce eski
   kodla yapılan bir yüklemeyi hiçbir zaman doğrulayamaz.
3. **Denetim sınıflaması.** 2026 yüklemesinin katalog işlemleri, kullanıcı hesabı
   işlemleri, `period_id=1` PP değişikliği ve tekil varlık türünün çoğul tabloya
   çözülememesi 2027 yazma geçmişi sayıldı.

Sahibin BEYAN'ı (2027'de faaliyet girilmedi) bu bulgularla çelişmiyor.

## Değişiklik (`scripts/replace_approved_2027.py`)

- İçerik satırları program/alt programa **adıyla** bağlanır; metinler ayrıca
  karşılaştırılır. Resmî faaliyet ve sorumlu birim imza denetimi aynen kalır.
- `catalogue_review`: her ONAYLI program/alt program canlıda bulunmalı. ONAYLI
  olmayan satır ancak 2027'de hiçbir kayıt ona bağlı değilse silinecek olarak
  listelenir; bağlıysa ENGEL. ONAYLI satırda farklı Gerekçe/Amaç listelenir ve
  düzeltilmiş kitap metni yazılır. Makbuz iki listeyi de içerir.
- `approved_book_provenance` engeli kaldırıldı; köken, paket işareti + yük içeriği
  ve müdürlük bazlı içerik imzalarıyla denetlenir (değişmedi).
- Denetim: hesap işlemleri, `period_id=<2 dışı>` PP değişikliği ve başka döneme
  ait mevcut varlığa ait katalog işlemi engel değil. `period_id=2`, ayrıntısız
  veya belirsiz kayıt engel olmaya devam eder.

## Doğrulama

- Canlıya benzeyen yerel prova: eski kod (`310546c`) + ön baskı kataloğu + canlı
  denetim türleriyle yükleme → ana dal kodu bütün canlı engel sınıflarını
  yeniden üretti → CIV-217 planı 0 engel, 9 kullanılmayan satır, 8 eski metin →
  uygulama başarılı; 2027 28 program / 38 alt program, köken yeni kitabın SHA256'sı.
- `tests/test_replace_approved_2027.py` (45 test, 8 yeni): kalan katalog ve eski
  metin listelenir ve değiştirilir; bağlı eski alt program ve eksik ONAYLI satır
  0 satır yazarak reddeder; başka dönem/hesap denetimleri engel değil; `period_id=2`
  veya belirsiz PP değişikliği engel; yeniden hesaplanamayan köken özetiyle plan
  ve uygulama geçer. `test_first_load_live.py` ile birlikte 101 test geçti.

Canlıya bağlanılmadı, dağıtım yapılmadı. Canlı plan sahibin yeni salt okunur
çalıştırmasıyla tekrar alınacak.

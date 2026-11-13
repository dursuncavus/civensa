# CIV-195 — Strateji kılavuzu (FR 2026)

## Teslim ve kapsam

14 Aralık 2026 haftasındaki pilot açılışı öncesinde Strateji Geliştirme kullanıcılarının (`Müdür` ve `Personel`) okuyacağı 2026 Faaliyet Raporu yıllık döngü kılavuzu hazırlandı. Başlangıç dalı `feature/authorization-workflow-phase5`, başlangıç SHA `020d92022397130f5bf6b1a1f0958e53c9281d25`. Kılavuz a–i bölümlerini sırasıyla, `[EKLENECEK — gösterge Excel ile toplu içe aktarma (Strateji)]` yer tutucusunu ve `Teknik sorunları sistem yöneticisine iletin.` yardım satırını birebir içerir.

Kılavuzun başlıklar ve görsel bağlantıları dahil boşlukla ayrılmış kelime sayısı: **1029** (üst sınır: 2.000).

Değişen ve eklenen dosyalar:

- `docs/guides/strateji-fr-2026/KILAVUZ.md`
- `docs/guides/strateji-fr-2026/INDEX.md`
- `docs/guides/strateji-fr-2026/img/01-giris.png` .. `docs/guides/strateji-fr-2026/img/23-disa-aktarma.png` (23 PNG)
- `docs/reports/civ-195/report.md`
- `docs/reports/civ-195/steps.json`
- `docs/reports/civ-195/run.json`
- `scripts/guide_screenshots.py` (`--strateji-guide` modu ve yardımcı fonksiyonlar eklendi; mevcut modların davranışı değişmedi)
- `tests/test_strateji_guide_capture.py`

Uygulama kodunda (`app/`), veritabanı göçlerinde (`alembic/`), bağımlılıklarda, `scripts/fr_rehearsal.py` dosyasında veya `docs/guides/mudurluk-fr-2026/**` altında hiçbir değişiklik yapılmadı.

## Çekim ve yeniden üretim

```sh
python scripts/guide_screenshots.py --strateji-guide
```

Önkoşul: mevcut `requirements-dev.txt` bağımlılıkları, Chromium ve yalnız yerel PostgreSQL 16+ için `CIVENSA_TEST_POSTGRES_URL`. Uygulama bağlantı değişkenleri araç tarafından geçersiz kılınır; geçici veritabanı oluşturulup koşu sonunda silinir. Canlı veritabanına bağlanılmaz.

Yeni bir tarayıcı altyapısı yazılmadı. Mevcut `fr_rehearsal.Rehearsal.walk` ve `local_http` altyapısı `scripts/guide_screenshots.py` içinden genişletilerek Strateji’nin gerçek oturumuyla tekil hesap açma, hatalı ve geçerli toplu CSV önizlemesi, toplu hesap oluşturma ve parola dosyası indirme, hatalı hesap grubunu toplu pasifleştirme, parola sıfırlama, faaliyet eşleştirme kuyruğu CSV indirme/önizleme/uygulama ve `Geri al`, onaylı 2026 kitabından yayınlama, 2026 gösterge ve EK-1 raporlarını oluşturma, tamamlanma görünümü izleme, gerekçeli iade, bağımsız birim onayı ve onaylı Word/PDF dışa aktarma adımları yürütüldü.

Depoya alınan görsel sayısı **23** (üst sınır: 30); tamamı **1440×900** çözünürlüktedir. En büyük PNG **176605 bayt**, en küçük PNG **23966 bayt** olup her dosya 1.500.000 bayt sınırının altındadır. Kılavuz her görsele göreli bağlantı verir. Kaynak kod SHA’sı, 2026 kitap SHA-256’sı, tarayıcı sürümü, viewport ve **SENTETİK** veri notu [INDEX.md](../../guides/strateji-fr-2026/INDEX.md) içindedir.

## Ekran metni bulguları — lead için

- **Toplu hesap CSV sütunları ekranda tam listelenmiyor**: `app/templates/users.html` üzerinde toplu CSV açıklaması yalnız `Görev alanına Müdür veya Personel yazın. CSV dosyasına parola sütunu eklemeyin.` bilgisini verir; `app/static/personal_accounts.js:29` içindeki önizleme tablosu 4 sütun (`Müdürlük`, `Ad Soyad`, `E-posta`, `Görev`) gösterirken, indirilen şablon ve sunucu doğrulaması (`app/personal_accounts.py:14`, `ACCOUNT_CSV_HEADERS`) 5 sütun (`Müdürlük ID,Müdürlük,Ad Soyad,E-posta,Görev`) bekler. Kılavuz 5 sütunu ve şablon üzerinden doldurma kuralını açıkça yazar.
- **Toplu hesap grubunu tek düğmeyle geri alma düğmesi arayüzde yok**: Sunucu tarafında `POST /api/users/batches/{batch_id}/revert` (`app/main.py:1488`) uç noktası bulunmasına rağmen `app/templates/users.html` ve `app/static/personal_accounts.js` üzerinde `Faaliyet Eşleştirme` ekranındaki `Son CSV işlemleri` / `Geri al` benzeri bir grup geri alma alanı yoktur. Ayrıca toplu pasifleştirme kartının başlığı `Paylaşılan hesapları pasifleştir` (`app/templates/users.html:165`) olduğu için yalnız eski paylaşılan hesaplara özelmiş gibi algılanabilir; oysa hatalı açılan kişisel hesapları topluca kapatmak için de listedeki `Seç` kutuları + `Pasifleştirme gerekçesi` + `Seçilen hesapları pasifleştir` (veya tek satırda `Devre dışı bırak`) kullanılır. Kılavuz yalnızca ekranda var olan bu akışı anlatır.
- **Unvan ve Görev / Ad soyad adlandırma farkı**: Tekil hesap formunda (`app/templates/users.html:48,67`) alan adları `Ad soyad` ve `Unvan` iken, toplu CSV bölümünde ve önizleme tablosunda (`app/templates/users.html:15`, `app/static/personal_accounts.js:29`) aynı bilgiler `Ad Soyad` ve `Görev` olarak geçer.
- **Faaliyet Eşleştirme CSV hedef sütun adı**: İndirilen CSV’de doldurulacak sütun adı `Seçilecek Program / Alt Program` (`app/main.py:1056`) iken ekrandaki form etiketi `Program / Alt Program` (`app/templates/activity_mapping.html:160`) şeklindedir. Kılavuz her iki adı da bağlamında belirtir.
- **Modüller ekranındaki müdürlük odaklı düğme metni**: Sol menüdeki `Rapor bölümleri ve beyanlar (EK-1)` ile `Modüller` ekranından açılan `Gösterge gerçekleşmeleri` ayrı ekranlardır; `Modüller` ekranındaki `2026 birim raporunu tamamla · EK-1 ve EK-2` düğmesi Strateji kullanıcısına da müdürlük diliyle görünür. Kılavuz iki ekranın amacını ayrı ayrı açıklar.
- **Onaysız ve onaylı dışa aktarma etiketleri**: Birim raporu `Onaylandı` durumuna geçmeden önce `Dışa aktar` menüsündeki bağlantılar `Taslak — Word (onaysız)` ve `Taslak — PDF (onaysız)` olarak görünür; onay sonrasında `Word olarak indir` ve `PDF olarak indir` etiketlerine dönüşür. Kılavuz her iki durumu da açıklar.

Bu bulgular için uygulama metni veya arayüz değiştirilmedi (Kural 4).

## Düğme ve ekran adı denetimi

Kılavuzda ters tırnakla işaretlenen tüm etiketler `app/templates/**` veya `app/static/**/*.js` dosyalarında birebir aranır. `tests/test_strateji_guide_capture.py::test_committed_strateji_guide_contract` eşleşmeyen etikette başarısız olur.

Birebir doğrulanan benzersiz etiket sayısı: **86**.

| Kılavuz etiketi | Kaynak |
| --- | --- |
| Müdür | `app/static/app.js:352` |
| Personel | `app/static/app.js:336` |
| Ad Soyad | `app/static/personal_accounts.js:29` |
| E-posta | `app/static/personal_accounts.js:29` |
| Görev | `app/static/personal_accounts.js:29` |
| Onay dayanağı | `app/templates/report_builder.html:199` |
| Çalışma alanına giriş | `app/templates/login.html:7` |
| Parola | `app/static/app.js:99` |
| Giriş yap | `app/templates/login.html:15` |
| Raporlama modülleri | `app/templates/modules.html:2` |
| Kullanıcılar | `app/static/app.js:529` |
| Kullanıcılar ve yetkiler | `app/templates/users.html:2` |
| Kullanıcı ekle | `app/templates/users.html:44` |
| Ad soyad | `app/templates/users.html:48` |
| Rol | `app/static/app.js:397` |
| Müdürlük | `app/static/app.js:352` |
| Strateji Geliştirme | `app/static/app.js:271` |
| Unvan | `app/static/app.js:529` |
| Geçici parola | `app/static/app.js:400` |
| Kaydet | `app/static/app.js:168` |
| Kişisel müdürlük hesaplarını toplu oluştur | `app/templates/users.html:9` |
| Şablonu indir | `app/templates/users.html:17` |
| Hazırlanan CSV dosyası | `app/templates/users.html:12` |
| Önizle | `app/static/app.js:366` |
| Dosya uygulanamaz. | `app/static/app.js:475` |
| kişisel hesap oluşturulmaya hazır. | `app/static/personal_accounts.js:28` |
| Hesapları oluştur | `app/templates/users.html:19` |
| Parola dosyasını indir | `app/static/personal_accounts.js:52` |
| Seç | `app/static/app.js:436` |
| Paylaşılan hesapları pasifleştir | `app/templates/users.html:165` |
| Pasifleştirme gerekçesi | `app/templates/users.html:167` |
| Seçilen hesapları pasifleştir | `app/templates/users.html:171` |
| Devre dışı bırak | `app/templates/users.html:149` |
| Parola sıfırla | `app/static/personal_accounts.js:54` |
| Yeni geçici parola | `app/templates/users.html:154` |
| Faaliyet Eşleştirme | `app/templates/activity_mapping.html:2` |
| Faaliyet Eşleştirme Kuyruğu | `app/templates/activity_mapping.html:2` |
| Kuyruğu CSV indir | `app/templates/activity_mapping.html:54` |
| Program / Alt Program | `app/static/app.js:274` |
| Doldurulmuş eşleştirme CSV'si | `app/templates/activity_mapping.html:60` |
| CSV'yi kontrol et | `app/templates/activity_mapping.html:64` |
| faaliyet eşleştirilmeye hazır. | `app/static/app.js:477` |
| Onayla ve eşleştir | `app/templates/activity_mapping.html:65` |
| Son CSV işlemleri | `app/templates/activity_mapping.html:75` |
| Geri al | `app/static/app.js:388` |
| Nihai Rapor | `app/templates/base.html:34` |
| Onaylı kitaptan yayınla | `app/templates/report_builder.html:194` |
| Yayın sürümleri | `app/templates/report_builder.html:217` |
| Güncel sürüm | `app/templates/activity_sections_editor.html:64` |
| Gösterge gerçekleşmelerine gir | `app/templates/modules.html:35` |
| Gösterge gerçekleşmeleri | `app/templates/activity_contract_index.html:2` |
| Yeni rapor oluştur | `app/templates/activity_contract_index.html:55` |
| Kurum | `app/templates/activity_contract_index.html:60` |
| Baz program yayını | `app/templates/activity_contract_index.html:67` |
| Seçilen yayınla rapor oluştur | `app/templates/activity_contract_index.html:77` |
| Rapor revizyonu | `app/templates/activity_contract_detail.html:293` |
| Yeni revizyon için baz yayın | `app/templates/activity_contract_detail.html:306` |
| Revizyon / düzeltme gerekçesi | `app/templates/activity_contract_detail.html:314` |
| Yeni rapor revizyonu oluştur | `app/templates/activity_contract_detail.html:313` |
| Gösterge gerçekleşmelerini onayla ve dondur | `app/templates/activity_contract_detail.html:298` |
| Rapor bölümleri ve beyanlar (EK-1) | `app/templates/activity_sections_index.html:2` |
| Yıl raporlarını oluştur | `app/templates/activity_sections_index.html:8` |
| Raporlama yılı | `app/templates/activity_sections_index.html:12` |
| Raporları oluştur | `app/templates/activity_sections_index.html:13` |
| Tamamlanma görünümü | `app/templates/activity_sections_editor.html:52` |
| Yıl | `app/static/app.js:334` |
| Bölüm | `app/templates/activity_sections_editor.html:78` |
| Durum | `app/static/design/section-editor.js:29` |
| Filtrele | `app/templates/activity_sections_index.html:18` |
| Taslak | `app/static/design/section-editor.js:19` |
| Gönderildi | `app/templates/dashboard.html:23` |
| İade edildi | `app/templates/dashboard.html:23` |
| Onaylandı | `app/templates/dashboard.html:23` |
| Sahibi | `app/templates/activity_sections_index.html:25` |
| Eksikler | `app/templates/activity_financial.html:44` |
| Birim raporu · | `app/templates/ar_unit_workflow.html:3` |
| İade gerekçesi | `app/templates/ar_unit_workflow.html:21` |
| Gerekçeyle iade et | `app/templates/ar_unit_workflow.html:22` |
| Gönderim ve onay geçmişi | `app/templates/ar_unit_workflow.html:24` |
| Birimi onayla | `app/templates/ar_unit_workflow.html:18` |
| Dışa aktar | `app/templates/activity_sections_editor.html:54` |
| Word ve PDF çıktıları | `app/templates/activity_sections_index.html:40` |
| Word olarak indir | `app/templates/activity_sections_editor.html:54` |
| PDF olarak indir | `app/templates/activity_sections_editor.html:54` |
| Taslak — Word (onaysız) | `app/templates/activity_sections_editor.html:54` |
| Taslak — PDF (onaysız) | `app/templates/activity_sections_editor.html:54` |

## Doğrulama ve çalıştırılan testler

- `python scripts/guide_screenshots.py --strateji-guide`: **çıkış 0**. 185 prova adımı yürütüldü; Strateji kılavuzu için 23 görsel üretildi ve korundu.
- Depoya alınan PNG sayısı: **23** (tümü `1440×900`, en büyük dosya `13-yayin-surumleri.png` — **176605 bayt**).
- `python -m pytest -q --require-postgres tests/test_strateji_guide_capture.py tests/test_fr_guide_capture.py tests/test_fr_rehearsal_harness.py tests/test_civ188_rehearsal_fixes.py`: **23 passed** (PostgreSQL üzerinde).
- `python -m compileall -q scripts/guide_screenshots.py scripts/fr_rehearsal.py tests/test_strateji_guide_capture.py` ve `git diff --check`: **çıkış 0**.

Makine kanıtları: [steps.json](steps.json), [run.json](run.json). `run.json` içinde `server_errors`, `unexpected` ve `js` hata listeleri boştur (`[]`).

## Harness adımı → görsel

Bu tablo depoya alınan 23 Strateji kılavuz çekimini ve boyutlarını gösterir. Aynı bilgiler [steps.json](steps.json) ve [INDEX.md](../../guides/strateji-fr-2026/INDEX.md) içinde yer alır.

| PNG | Harness adımı | Hesap | URL | Boyut (bayt) |
| --- | --- | --- | --- | --- |
| [01-giris.png](../../guides/strateji-fr-2026/img/01-giris.png) | Giriş ekranı | strategy | `/login` | 23966 |
| [02-moduller.png](../../guides/strateji-fr-2026/img/02-moduller.png) | Hesapla giriş | strategy | `/modules` | 140813 |
| [03-kullanici-ekle.png](../../guides/strateji-fr-2026/img/03-kullanici-ekle.png) | Tekil hesap oluşturma | strategy | `/users?period_id=2` | 144451 |
| [04-toplu-hesap-hata.png](../../guides/strateji-fr-2026/img/04-toplu-hesap-hata.png) | Toplu CSV önizleme hatası | strategy | `/users?period_id=2` | 175494 |
| [05-toplu-hesap-onizleme.png](../../guides/strateji-fr-2026/img/05-toplu-hesap-onizleme.png) | Toplu CSV geçerli önizleme | strategy | `/users?period_id=2` | 148631 |
| [06-parola-dosyasi.png](../../guides/strateji-fr-2026/img/06-parola-dosyasi.png) | Toplu hesap oluşturma ve parola dosyası | strategy | `/users?period_id=2` | 172580 |
| [07-toplu-pasiflestirme.png](../../guides/strateji-fr-2026/img/07-toplu-pasiflestirme.png) | Hatalı hesap grubunu pasifleştirme | strategy | `/users?period_id=2` | 126706 |
| [08-parola-sifirla.png](../../guides/strateji-fr-2026/img/08-parola-sifirla.png) | Parola sıfırlama | strategy | `/users?period_id=2` | 161114 |
| [09-faaliyet-eslestirme-kuyrugu.png](../../guides/strateji-fr-2026/img/09-faaliyet-eslestirme-kuyrugu.png) | Faaliyet eşleştirme kuyruğu | strategy | `/activity-mapping?period_id=2` | 167884 |
| [10-faaliyet-eslestirme-onizleme.png](../../guides/strateji-fr-2026/img/10-faaliyet-eslestirme-onizleme.png) | Faaliyet eşleştirme CSV önizleme | strategy | `/activity-mapping?period_id=2` | 158218 |
| [11-faaliyet-eslestirme-geri-al.png](../../guides/strateji-fr-2026/img/11-faaliyet-eslestirme-geri-al.png) | Faaliyet eşleştirme uygulama ve geri alma | strategy | `/activity-mapping?period_id=2` | 133256 |
| [12-onayli-kitaptan-yayinla.png](../../guides/strateji-fr-2026/img/12-onayli-kitaptan-yayinla.png) | 2026 onaylı kitap yayın hazırlığı | strategy | `/report-builder?period_id=2` | 68594 |
| [13-yayin-surumleri.png](../../guides/strateji-fr-2026/img/13-yayin-surumleri.png) | Onaylı kitaptan yayınla | strategy | `/report-builder?period_id=2` | 176605 |
| [14-gosterge-raporu-olustur.png](../../guides/strateji-fr-2026/img/14-gosterge-raporu-olustur.png) | 2026 gösterge raporu oluşturma | strategy | `/activity-reports` | 131674 |
| [15-gosterge-rapor-revizyonu.png](../../guides/strateji-fr-2026/img/15-gosterge-rapor-revizyonu.png) | Yayına bağlı 2026 FR revizyonu oluştur | strategy | `/activity-reports/revisions/1` | 114069 |
| [16-yeni-rapor-revizyonu.png](../../guides/strateji-fr-2026/img/16-yeni-rapor-revizyonu.png) | Rapor revizyonu ve dondurma alanı | strategy | `/activity-reports/revisions/1` | 74812 |
| [17-ek1-raporlarini-olustur.png](../../guides/strateji-fr-2026/img/17-ek1-raporlarini-olustur.png) | 2026 birim ve idare raporları oluşturma | strategy | `/activity-sections` | 105817 |
| [18-tamamlanma-gorunumu.png](../../guides/strateji-fr-2026/img/18-tamamlanma-gorunumu.png) | 2026 EK-1 raporlarını oluştur | strategy | `/activity-sections` | 128020 |
| [19-birim-incelemesi.png](../../guides/strateji-fr-2026/img/19-birim-incelemesi.png) | Strateji birim incelemesi | strategy | `/activity-sections/reports/8` | 110727 |
| [20-gerekceli-iade.png](../../guides/strateji-fr-2026/img/20-gerekceli-iade.png) | Gerekçeli iade | strategy | `/activity-sections/reports/8` | 139037 |
| [21-yeniden-inceleme.png](../../guides/strateji-fr-2026/img/21-yeniden-inceleme.png) | Strateji yeniden inceleme | strategy | `/activity-sections/reports/8` | 123753 |
| [22-bagimsiz-birim-onayi.png](../../guides/strateji-fr-2026/img/22-bagimsiz-birim-onayi.png) | Strateji bağımsız birim onayı | strategy | `/activity-sections/reports/8` | 124216 |
| [23-disa-aktarma.png](../../guides/strateji-fr-2026/img/23-disa-aktarma.png) | Onaylı Word olarak indir · Fen İşleri Müdürlüğü | strategy | `/activity-sections/reports/8` | 132732 |

## Doğrulanmayanlar ve sınırlar

- Canlı veritabanına bağlanılmadı; gerçek kullanıcı hesapları, gerçek e-posta adresleri veya gerçek kurumsal parola dağıtımı kullanılmadı.
- Başkan Yardımcısı ve Üst Yönetici ıslak imzaları sistem dışında yürütüldüğü için yalnız kılavuzda süreç notu olarak açıklandı.
- Ali Abi’nin yanıtına bağlı olan gösterge gerçekleşmelerinin Excel ile toplu içe aktarımı (FR5) uygulanmadı; kılavuzda `[EKLENECEK — gösterge Excel ile toplu içe aktarma (Strateji)]` yer tutucusu olarak bırakıldı.
- Kılavuz çekim modu süreyi ve görsel kapsamını sınırlamak için örnek müdürlük (`Fen İşleri Müdürlüğü`) üzerinden uçtan uca onay ve çıktı akışını çalıştırır; 33 müdürlüğün tamamının kapanışı ve B2 faaliyet sonucu girişine bağlı İdare raporu dondurma adımı bu görevin kapsamı dışındadır.

# CIV-190 — 2026 PP kitap düzeltmeleri

9 Kasım 2026. Baz dal: `feature/authorization-workflow-phase5`. Görev dalı: `task/civ-190-pp-errata`.

Kaynak beyan: “Civensa – 2026 Faaliyet Raporu soruları”, 9.11.2026 08:46, Dr. Ali KAYA. Düzeltme kayıtlarının kaynak alanı: “Strateji e-postası 9.11.2026, Dr. Ali KAYA”.

## İnceleme yöntemi ve sınır

Depodaki `tests/fixtures/first_load/source/2026-performans-programi_ONAYLI.idml`, mevcut ilk yükleme yolu ile yalnız geçici, yerel PostgreSQL 18'e yüklendi. Mevcut operasyon şeması kontrolü nedeniyle testin mevcut `disposable_first_load_database` yardımcısı kullanıldı. Aşağıdaki kimlikler bu yerel provaya aittir; canlı kayıt kimliği değildir. Canlı veritabanına bağlanılmadı. Yeni migrasyon veya bağımlılık yoktur; deploy yapılmadı. İlk teslimde merge yapılmadı; dal güncellemesi için sonradan verilen açık kullanıcı talebi aşağıdaki takip bölümünde açıklanır.

Onaylı kitap SHA-256: `1aaa0bb81c3cf4e245edaab42452a972b8a59ffc252814216c7628f6dbaf33d6`. Yüklenen satırlar, `ImportBatch.applied_hash`, `_serialize_department_state` ve `approved_book_provenance` değiştirilmedi. PP yayınına düzeltme uygulanmaz. FR için kopya bir okuma görünümü üretilir.

## Kayıt bazında kararlar

| Madde | Saklanan satırlarda bulunan | Karar |
| --- | --- | --- |
| K1, Bilgi İşlem, s.191 / s.243 | 2026 faaliyet toplamı 162.032.750,00; personel/SGK 14.053.496,00; maliyet toplamı 176.086.246,00. Ekonomik kalemler 176.085.750,00 topluyor; kaynak toplam bağlamı da bu basılı tutarı içeriyor. | `economic / total / 2026`: 176.085.750,00 → 176.086.246,00 kaydı yazıldı. Maliyet tablosuna düzeltme yok. |
| K2, Çevre Koruma, s.144 / s.230 | Faaliyetler 3.480.000,00 + personel/SGK 7.361.775,00 = 10.841.775,00. Ekonomik toplam da 10.841.775,00. E-postadaki hatalı 10.841.000,00 maliyet toplamı saklanan maliyet satırlarında bulunmuyor. | **BELİRSİZ**: kayıt yazılmadı. Mevcut satırlardan okunan doğru toplam korunur; 775 TL hiçbir kaleme dağıtılmaz. |
| K3, İmar, s.119 / s.224 | Faaliyet 1.000.000,00 + personel/SGK 26.702.989,00 = 27.702.989,00. Ekonomik toplam da 27.702.989,00. E-postadaki hatalı 27.702.000,00 saklanan maliyet satırlarında bulunmuyor. | **BELİRSİZ**: kayıt yazılmadı. Mevcut doğru toplam korunur; 989 TL hiçbir kaleme dağıtılmaz. |
| K4, Ruhsat ve Denetim, s.218 | 2026 ekonomik kalemler: personel 8.604.362,00 + SGK 680.000,00 + mal/hizmet 2.339.471,00 = 11.623.833,00. `source_context_json` 2026 toplam ham metni `11.623.833,00 / 30.970.987,00`; 2027 toplam ham metni `15.110.982,90 / 40.262.283,10`. Toplam hücreleri belirsiz olduğu için sayısal `amount` boş. | **BELİRSİZ**: 30.970.987,00 kaynak bağlamında var; fakat e-postadaki 15.110.982,90 aynı 2026 toplamı değil, 2027 bağlamında. 2026 kalemleri zaten 11.623.833,00 topluyor. Kaynak bağlamı veya yılı tahmin edilmedi; kayıt yazılmadı. |
| K5, Zabıta, s.220 | 2026 ekonomik 8 hücrenin `amount` alanı boş. İç kaynak ham metinleri 74.548.929,00; 6.400.000,00; 5.504.831,00; 2.000.000,00. Dış kaynak hücreleri ve kaynak dış toplamı boş/belirsiz. | **BELİRSİZ**: “Diğer Bütçe Dışı Kaynak” ayrı satırı ve aynı tutarın ikinci kez sayıldığını kanıtlayan sayısal kayıt yok. Hiçbir tutar çıkarılmadı; boşlar sıfıra çevrilmedi. |
| K5, Veteriner, s.221 | 2026 ekonomik 10 hücrenin `amount` alanı boş. İç kaynak ham metinleri 1.967.000,00; 660.000,00; 51.640.000,00; 1.500.000,00; 25.000.000,00. Dış kaynak ham metni `0.00`, fakat mevcut kaynak doğrulamasında belirsiz ve sayısal değer boş. | **BELİRSİZ**: ayrı “Diğer Bütçe Dışı Kaynak” ve çift sayım kanıtlanamıyor. Kaynaklardan hiçbirini çıkarmadık veya yeniden yorumlamadık. |
| K6, Fen İşleri, s.223 | 2027 ekonomik kalem toplamı **1.290.738.800,00**; kaynak toplam ham metni `0,00 / 1.290.738.000`. 2028 kalem toplamı **1.677.960.440,00**, kaynak ham metni `0,00 / 1.677.960,440`. | Kural 6 gereği 2027 için toplam kaydı yazıldı: basılı ve teyitli 1.290.738.000,00 uygulanır; ayrıca eşleşme koşulu olarak saklanan 1.290.738.800,00 toplamı ve basılı kaynak bağlamı tutulur. 2028 zaten eşit: kayıt yok. |

Yerel kayıt konumları:

- K1: müdürlük 3, ekonomik kaynak tablo 139, 2026 `EconomicValue` 2267–2274; personel 352; faaliyet toplam satırları 7205, 7223, 7241, 7259, 7277, 7295, 7313, 7331, 7349, 7367.
- K2: müdürlük 30, kaynak tablo 77, ekonomik 1893–1898; personel 292; faaliyet toplam satırları 6082, 6094, 6109, 6124, 6139.
- K3: müdürlük 33, kaynak tablo 44, ekonomik 1623–1628; personel 244; faaliyet toplam satırı 5635.
- K4: müdürlük 20, kaynak tablo 11, ekonomik 1403–1408; personel 214; faaliyet toplam satırları 5245, 5263, 5281.
- K5: Zabıta müdürlük 29, kaynak tablo 20, ekonomik 1437–1444; Veteriner müdürlük 26, kaynak tablo 28, ekonomik 1481–1490.
- K6: Fen İşleri müdürlük 8, kaynak tablo 41; 2026 ekonomik 1575–1586; 2027/2028 aynı tablonun tahmin satırları.

K1 ve K6 yalnız toplam düzeltmesidir. Ekonomik kategoriler, program grupları, bütçe içi/dışı dağılım, faaliyet ve personel satırları basılı/saklanan haliyle kalır. Toplam ile kalem toplamının farkı bilinmeyen dağılım nedeniyle korunur ve açıklanır. Kaynakların mevcut `needs_review` durumları kaldırılmaz. K2–K5 için farklı bir dağılım veya yeni sayısal değer üretilmedi.

## Okuma yolları

Tek uygulama işlevi: `app/data/pp_errata.py::apply_pp_errata`. Tek sürümlü veri kaynağı: `app/data/pp_errata.json` (`version: 1`). Dosyada yalnız K1 ve K6/2027 vardır. Yıl, basılı müdürlük adı, tablo, değer yılı, alan ve beklenen saklanan toplam eşleşir; K6 ayrıca saklanan basılı kaynak bağlamını doğrular. Eşleşmezse değer korunur ve FR görünümünde **BELİRSİZ** gerekçesi gösterilir. Boş tutar sıfır olmaz. Toplam düzeltmesi kaleme veya kaynak dağılımına yansıtılmaz.

İşlev üzerinden geçen yollar:

1. `activity_financial_service.pp_references`: bütünlük kodu doğrulanan dondurulmuş PP yayını → FR görünümü. Ekonomik kod referansları aynı görünümden alınır; dağılım bilinmediğinden kategori tutarları değiştirilmez.
2. `activity_financial_service.financial_data`: birim ve İdare III-A planlanan maliyet/ekonomik toplamları; mevcut finans kontrolleri ve rapor hazırlama/gönderme kontrolleri bu ortak veriyi kullanır.
3. `/api/activity-sections/reports/{id}/financial`, rapor JSON'u ve `/activity-sections/reports/{id}?code=III.A.1`: aynı finans verisi; düzeltilmiş toplamın yanında `Düzeltildi (K1, s.243)` / `Düzeltildi (K6, s.223)`, başlıkta basılı değer. K6'da başlık ayrıca saklanan kalemler toplamını gösterir.
4. `ar_typeset_source.enrich`: yeni dizgi JSON’undaki faaliyet/maliyet satırlarının bağlı PP okuması da aynı işlevden geçer. Yalnız toplam düzeltildiğinden faaliyet kalemleri değişmez; toplamlar dizgi sözleşmesinin ortak finans bağlamında korunur. Tarihsel dizgi kopyaları yeniden yazılmaz.
5. `activity_sections_service.report_data` → `ar_export._ReportContent.financial`: birim/İdare Word ve PDF ortak üretimi, düzeltilmiş toplam ve işaretle birlikte. Yeni FR onay kopyası bu okunmuş değerleri içerir. Daha önce saklanan FR onay/yayın kopyaları yeniden hesaplanmaz; kendi bütünlük kodları ve tarihsel değerleri korunur.

`program_service.cost_reconciliation` ve `publication_checks` mevcut kodda PP kitabının ara toplam/yayın kapılarıdır; FR finans okuma yolu değillerdir. PP kaynak uyarılarının tarihsel anlamını değiştirmemek için basılı veriyle çalışmaya devam ederler. Test, bu kapıların sonuçlarının ve kitap çıktısı bloklarının FR okumasından önce/sonra aynı olduğunu doğrular. `book_snapshot`, PP Word/PDF ve yayın bütünlük denetimine düzeltme uygulanmaz.

Strateji için mevcut `/report-builder?period_id=2026_dönem_kimliği` ekranına “Basılı kitap düzeltmeleri (2026)” salt okunur bloğu eklendi. Menü veya düzenleme uç noktası eklenmedi. Tutarlar Türkçe biçimde gösterilir.

## Doğrulama (ilk teslim)

- `python -m pytest -q --require-postgres tests/test_pp_errata.py`: **5 geçti** (son koşu 102,55 sn). Gerçek 2026 ilk yüklemesi; aynı kitap durumu ve hash; K1–K6 kararları; eksik/uyuşmayan kayıtlar; dosyada bulunmayan madde; birim/İdare; Word/PDF; korunan FR onay kopyası; gerçek tarayıcı listesi ve işaret.
- `python -m pytest -q --require-postgres tests/test_activity_financial.py tests/test_activity_financial_ui.py tests/test_activity_sections_export.py`: **29 geçti** (46,65 sn).
- `python -m pytest -q --require-postgres tests/test_approved_book_publication.py tests/test_approved_book_mapping.py tests/test_pp_subtotal_reconciliation.py`: **60 geçti** (296,46 sn).
- `python -m pytest -q --require-postgres tests/test_ar_typeset_contract.py`: **25 geçti** (42,72 sn); dizgi veri sözleşmesi ve tarihsel kopya kontrolleri.
- `alembic heads`: tek baş, `c185a1b2c3d4`; migrasyon dosyalarında değişiklik yok.
- `git diff --check`: temiz.

Koşular yalnız `CIVENSA_TEST_POSTGRES_URL` ile yerel PostgreSQL 18 üzerinde yapıldı; tarayıcı `/usr/bin/chromium` ile başlatıldı. İlk PP çıktı testi dönüş demetini bayt olarak kullanıyordu; test kodu düzeltildi ve son 5 testlik koşu bütünüyle geçti. FastAPI/Starlette test istemcisinin mevcut kullanım dışı bırakma uyarısı var.

CI kabulü PR baş commit'i üzerinde izlenir; tam test grubunun sonucu PR denetimlerinde bulunur. Canlı verinin yerel provayla birebir eşliği kontrol edilmedi; görev gereği canlı bağlantı kurulmadı. Eşleşmeyen çalışma zamanı toplamları düzeltilmez ve BELİRSİZ gösterilir.

Ekran görüntüleri: `strateji.png`, `fr-marker.png` (yerel test hesabı ve geçici veritabanı; gerçek uygulama şablonları ve oturum açma yolu). İki PNG kullanıcı tarafından herkese açık PR’a eklenmek üzere açıkça onaylandı.

## Lead takip düzeltmeleri

PR #433’ün lead takip yorumu ve dört inceleme bulgusu uygulandı:

- Resmî birim/İdare Word ve PDF’de PP planlanan tutarlar tablosu yalnız Müdürlük / Yıl / Tablo / Toplam sütunlarını içerir. Düzeltme işareti toplam hücresinde kalır. `needs_review` ve `errata_warning` metinleri resmî çıktıya yazılmaz; uygulama ekranında ve kaynak veride korunur.
- Dizgi sözleşmesinde `stored_amount`, `sources.inside/outside`, `printed_value`, `corrected_value`, `stored_total` sayısal alan olarak; `value_year` yıl/referans alanı olarak sınıflandırıldı. Boş sayılar `{exact: null, display: "—"}` biçimini korur; yıl `2.026` biçimine çevrilmez. Kaydedilmiş tarihsel raporlar yeniden yazılmaz.
- `scope.status == 'zero'` kararı varsa bulunmayan maliyet/ekonomik satırlar ve kaynaklar açık sıfır olarak okunur. `required` kapsamındaki eksiklik ve mevcut satırdaki boş hücre bilinmeyen kalır; sıfır kapsamındaki boş hücre de sıfıra çevrilmez.
- Basılı tutar ve K6’nın saklanan kalem toplamı işaretin yanında görünür metin olarak gösterilir. 1440 ve 390 piksel tarayıcı kontrolleri bunları hover olmadan doğrular. FR ekran görüntüsü güncellendi.

Takip doğrulaması (geçici yerel PostgreSQL 18 ve Chromium):

- Hatalar önce regresyonlarla yeniden üretildi: resmî çıktıdaki iki not, dizgi yılı ve açık sıfır toplamı kontrolleri başarısızdı.
- `python -m pytest -q --require-postgres tests/test_pp_errata.py`: **15 geçti**, 117,94 sn. Dört Word/PDF × birim/İdare not süzme kontrolü; 2026 düzeltme/bilinmeyen sayı dizgisi; sıfır/required/boş hücre ayrımı; masaüstü/mobil görünür tutarlar; mevcut gerçek kitap ve köken hash’i kontrolleri.
- `python -m pytest -q --require-postgres tests/test_ar_typeset_contract.py tests/test_activity_sections_export.py tests/test_activity_financial_ui.py`: **37 geçti**, 69,36 sn.
- `git diff --check`: temiz; `alembic heads`: yine tek baş `c185a1b2c3d4`.

Kullanıcının bu takipteki açık merge talebi yalnız `feature/authorization-workflow-phase5` → `task/civ-190-pp-errata` yönündedir. PR’ın hedef dala merge edilmesi veya deploy yapılması bu talebin kapsamında değildir. Onaylı kitap satırları ve düzeltme JSON’u değiştirilmedi.

# CIV-145 · İç Kontrol ekranları tasarım sistemine

Beş ekran mevcut panel, form, tablo, metinli durum rozeti ve açılır ayrıntı desenlerini kullanır (D-243). İzleme (monitoring) sayfası kullanılabilir içerik genişliğini kullanır; diğer dört ekranın içerik ve panelleri en fazla 44rem kalır. Paneller solda, yukarıdan aşağıya sıralanır. İzleme özet tablosu otomatik sütun düzeninde, Bileşen / standart durum sayıları tablosu eşit genişlikte sabit sütun düzenindedir; kelime ortasında bölünme ve tireleme yoktur. Gerektiğinde kendi alanlarında yatay kayarlar. Planın eylem ayrıntıları mevcut eylem metnini özet olarak kullanır; klavyeyle açılabilir.

**Owner tarafından istenen görünen metin değişiklikleri:** Strateji menüsünde `İç Kontrol · Uyum Eylem Planı` → `Uyum Eylem Planı`. İzleme Standart hücresinde yalnız bileşen öneki kaldırılır: `KOS1–4` → `1–4`, `RDS5–6` → `5–6`, `KFS7–12` → `7–12`, `BİS13–16` → `13–16`, `İS17–18` → `17–18`. Kayıtlar, anahtarlar, form alanları ve dışa aktarılan kodlar değişmez. Diğer metinler korunur. Başlangıç sürümü `69021f0` ile aynı bağlamda render edilen beş şablon; metinler, form alanları/değerleri/yöntemleri/adresleri, bağlantılar, kimlikler, data-* ve aria-* öznitelikleri bakımından karşılaştırılır. `tests/fixtures/civ145_internal_control/` yalnız bu karşılaştırmanın kaynak kopyalarını içerir.

**Ortak kabuk:** `base.html` yalnız yukarıdaki tek menü etiketi için değişti. `monitoring_shared.html`, `monitoring_notes.html`, `monitoring_ours.html` ve CIV-105 `our_actions.html` kaynak hashleri korunur. İki ekran, CIV-105 örneğindeki gibi makroları import eder; eski satır içi CSS bloğunu include etmez. Makro işaretlemesi değişmez. Ortak kabuk için D-252 sayımı aşağıdadır. Yeni token veya bileşen tanımlanmadı.

## Owner eşit sütun düzeltmesi

Sayı tablosunun yalnız `th` hücreleri `vertical-align: bottom` ile alta hizalanır. Veri hücreleri ve resmî özet tablosu üst hizasını korur. Tarayıcı testleri tüm başlıkların son metin satırı alt kenarları arasında en fazla 1px fark olduğunu ve veri hücrelerinin değişmeyen `top` hizasını denetler. Yeni token eklenmedi; İzleme 1440/390 çekimleri yenilendi.

Yalnız Bileşen / standart durum sayıları tablosuna `ic-counts-table` sınıfı eklendi: `table-layout: fixed; width: 100%`. Başlıklar `overflow-wrap: normal; word-break: normal; hyphens: none` kurallarını korur. Dar ekranda uzun tek kelimelerin komşu hücrelere taşmasını önlemek için mevcut tasarım sistemi tablo minimumu (kaynak karşılaştırma/kullanıcı tablolarındaki **1000px**) yeniden kullanılır; tablo kendi alanında yatay kayar. Yeni token yok. Resmî rapor özeti tablosunun otomatik düzeni korunur.

`python -m pytest -q --require-postgres tests/test_internal_control_design.py -k 'monitoring or standard_numbers'` — **15 geçti**. Her başlık/veri satırında sütun genişlikleri arasındaki fark en fazla 1px; hücre metni taşmıyor, kelime ortasında bölünmüyor ve mevcut form/metin/hook sözleşmeleri korunuyor. Altı İzleme durumu × 1440/390 = **12 PNG yeniden alındı**. Bu düzeltmede ortak kabuk/makro dosyaları değişmedi; aşağıdaki D-252 kaydı ortak menü değişikliğinin kanıtıdır.

## Owner tablo ve menü düzeltmesi

İzleme `th/td` hücrelerinde `overflow-wrap: normal`, `word-break: normal`, `hyphens: none`; resmî özet tablosunda `table-layout: auto`, sayı tablosunda `table-layout: fixed` kullanılır. `ic-scroll` korunur. Hücrelerdeki sözcüklerin gerçek Chromium metin aralıklarının aynı satırda kalması, yatay kaydırma ve 14px metin kontrol edilir. Üç bileşenli gerçek sentetik plan testi `KOS1 → 1`, `RDS5 → 5`, `BİS13 → 13` gösterimini ve servis anahtarlarının değişmediğini doğrular. Menü bağlantısının hedefi ve aktiflik kuralı aynı kalır; rol/pozisyon/dönem testleri kısalan etiketi kontrol eder.

Altı İzleme durumu (boş/dolu/alan hatası/incelemede/iade/kapalı) 1440/390 genişlikte yeniden yakalandı: **12 PNG**. `python -m pytest -q --require-postgres tests/test_internal_control_design.py -k 'monitoring or standard_numbers'` — **15 geçti**. Güncel tam test/CI sonucu PR açıklamasındadır.

## D-252 · ortak kabuk kısa sayımı

Mevcut UI haritasının **97 ekran/durumu × 1440/390 = 194 çekim** tamamlandı: **15.278 form/bağlantı/kimlik hedefi**, **0 eksik çekim**, **0 taşma**, **0 kırpılma/örtüşme**, **0 kabuk yerleşim sorunu**. Kısalan menü etiketi **124 çekimde** mevcut; müdürlük menü etiketi korundu. Aynı DOM üzerinde eski/yeni menü etiketi karşılaştırmasında **0 yeni sorun, 0 değişen hedef/hook/form özniteliği**. `8505763` ile `base.html` kaynak karşılaştırması yalnız tek etiket farkını doğrular. Tam PNG’ler, envanter ve geçici çalıştırıcı yalnız `/tmp/civ145-owner3-shell-proof/` ve `/tmp/civ145_owner3_shell_*.py` altında; repoya yalnız bu kısa sayım eklendi.

Son yerel çalışma: `python -m pytest -q --require-postgres tests/test_internal_control_design.py tests/test_design_shell.py tests/test_sidebar_ui.py` — **75 geçti**; mevcut İç Kontrol/izleme/resmî rapor/CIV-105 regresyonları — **178 geçti**. Toplam **253 test geçti**; mevcut Starlette/httpx deprecation uyarısı. Regresyon dosyaları geçici çalıştırıcıyla `/tmp` altına yönlendirildi; `tests/artifacts/**` değişmedi.

## Owner form düzeni düzeltmesi

İzleme sayfasındaki mevcut `.ic-grid`, 1100px ve üstünde üç, 701–1099px aralığında iki, 700px ve altında tek sütun kullanır. Etkin plan seçimi ve gönderim düğmesi kendi satırlarında kalır. Düğme öncesi boşluk mevcut `--space-4` değeridir; yeni token eklenmedi. Diğer ekranlar ve şablon işaretlemesi değişmedi.

`python -m pytest -q --require-postgres tests/test_internal_control_design.py -k monitoring-populated` — **4 geçti** (1440/1280: üç sütun, 1000: iki sütun, 390: tek sütun). Alanların satır/sütun konumları, plan seçiminin üstte ve düğmenin altta ayrı satırlarda olması, tablolar, kontrast ve değişmeyen form/hook sözleşmeleri kontrol edildi. `monitoring-populated-1440.png` ve `monitoring-populated-390.png` yeniden alındı. Güncel tam test sonucu PR açıklamasındadır.

## Owner genişlik düzeltmesi

Yalnız `monitoring.html` köküne sayfa sınıfı ve bu sınıfa `max-width: none` eklendi; diğer dört ekranın stilleri ve tüm metin/form/hook sözleşmeleri korundu. `monitoring-populated-1440.png` ve `monitoring-populated-390.png` yenilendi. Tüm İzleme durum görüntüleri son tablo/menü düzeltmesiyle yenilendi.

`python -m pytest -q --require-postgres tests/test_internal_control_design.py -k monitoring-populated` — **3 geçti** (1280, 1440, 390). Geniş ekranda 14px yazının korunduğu; dar ekranda yerel kaydırmanın çalıştığı doğrulandı. Aynı test dört diğer ekranın 44rem sınırını korumaya devam eder. Güncel tam test sonucu PR açıklamasındadır.

## Ekran görüntüleri

Geçici yerel PostgreSQL 18.6, sentetik kayıtlar, Chromium 151; tam sayfa PNG, 1440×900 ve 390×900 görünüm alanları. Yerel tarayıcı kontrollerinin dosya/tarih metinleri tarayıcının diline bağlıdır; uygulama metinleri Türkçe kalır. `index-file-required` mevcut zorunlu dosya alanının tarayıcı doğrulamasıdır. Plan sayfasında yerinde hata durumu bulunmaz; boş filtre sonucu gösterilir. Ayrı hata şablonları bu kapsamda değildir.

| Durum | 1440 | 390 |
| --- | --- | --- |
| Plan listesi · boş | [Görüntü](index-empty-1440.png) | [Görüntü](index-empty-390.png) |
| Plan listesi · dolu | [Görüntü](index-populated-1440.png) | [Görüntü](index-populated-390.png) |
| Plan yükleme · zorunlu dosya | [Görüntü](index-file-required-1440.png) | [Görüntü](index-file-required-390.png) |
| Plan · taslak | [Görüntü](plan-populated-1440.png) | [Görüntü](plan-populated-390.png) |
| Plan · sonuç bulunamadı | [Görüntü](plan-empty-1440.png) | [Görüntü](plan-empty-390.png) |
| Plan · etkin | [Görüntü](plan-active-1440.png) | [Görüntü](plan-active-390.png) |
| Doğrulama · boş kaynak | [Görüntü](import-empty-1440.png) | [Görüntü](import-empty-390.png) |
| Doğrulama · geçerli | [Görüntü](import-populated-1440.png) | [Görüntü](import-populated-390.png) |
| Doğrulama · uyarı | [Görüntü](import-warning-1440.png) | [Görüntü](import-warning-390.png) |
| Doğrulama · engelleyici/eşleşmeyen birim | [Görüntü](import-error-1440.png) | [Görüntü](import-error-390.png) |
| Doğrulama · kaydedilmiş | [Görüntü](import-committed-1440.png) | [Görüntü](import-committed-390.png) |
| İzleme · dönem yok | [Görüntü](monitoring-empty-1440.png) | [Görüntü](monitoring-empty-390.png) |
| İzleme · açık | [Görüntü](monitoring-populated-1440.png) | [Görüntü](monitoring-populated-390.png) |
| İzleme · incelemede | [Görüntü](monitoring-submitted-1440.png) | [Görüntü](monitoring-submitted-390.png) |
| İzleme · iade | [Görüntü](monitoring-returned-1440.png) | [Görüntü](monitoring-returned-390.png) |
| İzleme · alan hatası | [Görüntü](monitoring-error-1440.png) | [Görüntü](monitoring-error-390.png) |
| İzleme · kapalı | [Görüntü](monitoring-closed-1440.png) | [Görüntü](monitoring-closed-390.png) |
| Paket · giriş eksik | [Görüntü](detail-empty-1440.png) | [Görüntü](detail-empty-390.png) |
| Paket · kurul girişi | [Görüntü](detail-populated-1440.png) | [Görüntü](detail-populated-390.png) |
| Paket · müdürlük/katkı notu | [Görüntü](detail-department-1440.png) | [Görüntü](detail-department-390.png) |
| Paket · alan hatası | [Görüntü](detail-error-1440.png) | [Görüntü](detail-error-390.png) |
| Paket · incelemede | [Görüntü](detail-submitted-1440.png) | [Görüntü](detail-submitted-390.png) |
| Paket · onaylı | [Görüntü](detail-approved-1440.png) | [Görüntü](detail-approved-390.png) |
| Paket · kapalı | [Görüntü](detail-closed-1440.png) | [Görüntü](detail-closed-390.png) |
| Plan · ayrıntı açık | [Görüntü](plan-populated-expanded-1440.png) | [Görüntü](plan-populated-expanded-390.png) |

## Doğrulama

Tarayıcı testleri diğer dört ekranın 44rem sınırını, İzleme sayfasının kullanılabilir genişliği doldurmasını, soldan okuma sırasını, belge taşmasını, tablo kaydırmasını, normal/hover/focus/açık ayrıntı metinlerinin en az 4,5:1 kontrastını, klavye odağını, gerçek 422 yanıtlarında alan değerlerini ve CSRF/form gönderimlerini kontrol eder. Mevcut yükleme–eşleştirme–kaydetme–etkinleştirme, izleme ve resmî rapor regresyonları da çalıştırılır. İki eski byte eşitliği kontrolü, yeni görünümün metin/form sözleşmelerini koruma kontrolüne çevrildi.

İlk görüntüleri üreten odaklı çalışma: `CIVENSA_CHROMIUM_PATH=/usr/bin/chromium CIVENSA_CIV145_SCREENSHOTS=docs/design/rollout/civ-145 python -m pytest -q --require-postgres tests/test_internal_control_design.py` — **50 geçti**. `CIVENSA_TEST_POSTGRES_URL` yalnız geçici yerel test veritabanına ayarlandı. 50 PNG bağlantısının varlığı, genişliği ve 1.500.000 bayt altı boyutu doğrulandı (ilk çekimde en büyük 281.271 bayt).

İlk regresyon çalışması: `python -m pytest -q --require-postgres tests/test_internal_control.py tests/test_internal_control_monitoring.py tests/test_internal_control_official_report.py tests/test_ic_our_actions_design.py` — **178 geçti**. Eski testlerin ürettiği dosyalar geçici bir pytest çalıştırıcı eklentisiyle `/tmp` altına yönlendirildi; `tests/artifacts/**` değişikliği yok. Toplam **228 test geçti**; mevcut Starlette/httpx deprecation uyarısı dışında uyarı yok. `git diff --check` ve `python -m compileall -q app` başarılı.

Lead okuma sırası/kontrast incelemesi ve owner ekran görüntüsü onayı beklenir.

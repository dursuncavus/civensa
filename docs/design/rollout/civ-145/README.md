# CIV-145 · İç Kontrol ekranları tasarım sistemine

Beş ekran mevcut panel, form, tablo, metinli durum rozeti ve açılır ayrıntı desenlerini kullanır (D-243). İçerik ve paneller en fazla 44rem; paneller solda, yukarıdan aşağıya sıralanır. Geniş tablolar kendi alanında yatay kayar. Planın eylem ayrıntıları mevcut eylem metnini özet olarak kullanır; klavyeyle açılabilir.

**Görünen metin değişikliği: yok.** Başlangıç sürümü `69021f0` ile aynı bağlamda render edilen beş şablon; metinler, form alanları/değerleri/yöntemleri/adresleri, bağlantılar, kimlikler, data-* ve aria-* öznitelikleri bakımından karşılaştırılır. `tests/fixtures/civ145_internal_control/` yalnız bu karşılaştırmanın kaynak kopyalarını içerir.

**Ortak dosya değişikliği: yok.** `monitoring_shared.html`, `monitoring_notes.html`, `monitoring_ours.html` ve CIV-105 `our_actions.html` kaynak hashleri korunur. İki ekran, CIV-105 örneğindeki gibi makroları import eder; eski satır içi CSS bloğunu include etmez. Makro işaretlemesi değişmez; D-252 ortak dosya sayım özeti gerekmez. Yeni token veya bileşen tanımlanmadı.

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

Tarayıcı testleri 44rem sınırını, soldan okuma sırasını, belge taşmasını, tablo kaydırmasını, normal/hover/focus/açık ayrıntı metinlerinin en az 4,5:1 kontrastını, klavye odağını, gerçek 422 yanıtlarında alan değerlerini ve CSRF/form gönderimlerini kontrol eder. Mevcut yükleme–eşleştirme–kaydetme–etkinleştirme, izleme ve resmî rapor regresyonları da çalıştırılır. İki eski byte eşitliği kontrolü, yeni görünümün metin/form sözleşmelerini koruma kontrolüne çevrildi.

Görüntüleri üreten odaklı çalışma: `CIVENSA_CHROMIUM_PATH=/usr/bin/chromium CIVENSA_CIV145_SCREENSHOTS=docs/design/rollout/civ-145 python -m pytest -q --require-postgres tests/test_internal_control_design.py` — **50 geçti**. `CIVENSA_TEST_POSTGRES_URL` yalnız geçici yerel test veritabanına ayarlandı. 50 PNG bağlantısının varlığı, genişliği ve 1.500.000 bayt altı boyutu doğrulandı (en büyük 281.271 bayt).

Regresyon çalışması: `python -m pytest -q --require-postgres tests/test_internal_control.py tests/test_internal_control_monitoring.py tests/test_internal_control_official_report.py tests/test_ic_our_actions_design.py` — **178 geçti**. Eski testlerin ürettiği dosyalar geçici bir pytest çalıştırıcı eklentisiyle `/tmp` altına yönlendirildi; `tests/artifacts/**` değişikliği yok. Toplam **228 test geçti**; mevcut Starlette/httpx deprecation uyarısı dışında uyarı yok. `git diff --check` ve `python -m compileall -q app` başarılı.

Lead okuma sırası/kontrast incelemesi ve owner ekran görüntüsü onayı beklenir.

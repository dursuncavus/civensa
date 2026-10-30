# CIV-097 · Veri girişi (024)

`/department/{id}` içeriği D-224 / CIV-095 bileşenleriyle yenilenir. CIV-096 ortak düzeni korunur. Başlangıç: `feature/authorization-workflow-phase5`, `691ce0d` (PR #117 dahil).

Açık kartlar, vurgu çizgili görünüm düğmeleri, cümle düzeninde etiketler, 16 px girişler, metin + renk kullanan kontrol/iade mesajları, açık gönderim paneli ve kendi kaydırma alanındaki maliyet tablosu kullanılır. Sayılar sağa hizalı ve tabular rakamlıdır. Dekoratif hareket, gölge veya gradyan eklenmez.

Kaldırma `details`, uyarı metni ve formu korunur; yalnız 024'te aynı DOM düğümleri yerel `dialog` içine alınır. İlk odak Vazgeç'te; Tab/Shift+Tab pencere içinde döner; Escape/Vazgeç çağıran summary öğesine döner. İstekler ve hata işleme mevcut `app.js` içindedir. Yeni `data-entry.js` yalnız sunum/erişilebilirlik içindir; mevcut seçici değişikliği **yoktur**.

## Görseller

Tam sayfa, Chromium, DPR 1, tr-TR, Europe/Istanbul, 900 px viewport yüksekliği. Bütün veriler sentetiktir. PNG boyutları [screenshots.json](screenshots.json) içindedir; her biri ≤ 1.500.000 bayt.

| Durum | 1440 px | 390 px |
| --- | --- | --- |
| Taslak, kontrol sorunu | [PNG](024-draft-issues-1440.png) | [PNG](024-draft-issues-390.png) |
| İade, notlu | [PNG](024-returned-1440.png) | [PNG](024-returned-390.png) |
| Gönderilmiş, salt okunur | [PNG](024-submitted-1440.png) | [PNG](024-submitted-390.png) |
| Faaliyet Maliyetleri | [PNG](024-costs-1440.png) | [PNG](024-costs-390.png) |

`capture_states.py`: taslak/sorunlu, taslak/temiz, gönderilmiş, iade/notlu, onaylı × personel/müdür × iki sekme × iki genişlik = 40 kontrol. Bunlar sunum fixture'larıdır; iş akışı geçişlerinin kabul testi oldukları iddia edilmez. Kaynak toplamı uyuşmazlığı ve işlem geçmişi de sentetik kayıtlardır. Ek tarama: maliyet ekleme/düzenleme, yer tutucular, kaldırma penceresi, kaydedilmemiş değişiklik penceresi, kayıt hatası, kaydedilmiş durum işareti ve seçili checkbox işareti. Tarayıcıdan yalnız yerel GET isteklerine izin verilir; kalıcı durum özeti önce/sonra eşitliği denetlenir.

## Koruma ve doğrulama

- [template-contract.json](template-contract.json): eski 78 Jinja bloğu aynı sırada; özgün 37 kimlik/hedef/`data-*` özniteliğinde eksik yok. `app.js` değişmez.
- `tests/test_department_design.py::test_024_preserves_all_fields_and_action_targets`: personel/müdür/Strateji × beş durum + kapalı dönem = 18 PostgreSQL senaryosu. Gizli alanlar, kapalı disclosure, iki sekme, option sırası/seçim durumu, ID/name/data-*, form action/method, href, readonly/disabled koşulları başlangıç şablonunun çıktısıyla birebir karşılaştırılır. [Dondurulmuş fixture](../../../../tests/fixtures/department_024_contract.json) `691ce0d` şablonunun gerçek PostgreSQL çıktısından alınmıştır; CSRF dahil alan değerleri fixture'a yazılmaz.
- `tests/test_department_design.py::test_024_confirm_focus_and_tab_order`: 1440/390'da başlangıç odağı, Tab/Shift+Tab döngüsü, Escape, Vazgeç ve alanların görsel sırayla tab geçişi; iptal sırasında sıfır yazma isteği.
- `tests/test_department_design.py::test_024_new_activity_preserves_cost_keys`: 1440/390'da yeni faaliyet satırının 12 yıl/tür/kaynak anahtarını özgün API sözleşmesiyle karşılaştırır. Başlık yazımının bütçe/ara dönem alanlarını yanlışlıkla tahmine çevirmesini engeller.
- Mevcut test dosyaları veya eski işaretleme assertion'ları değiştirilmedi. Eklenen tek test dosyası yukarıdakidir.
- [capture-summary.json](capture-summary.json): 97 ekran × iki genişlik; özgün öğe/hedefler, belge/yerel kaydırma dışı taşma, kırpılma, örtüşme ve ortak düzen kontrolü. 024 dışındaki ekranlar aynı DOM/veri/saat/odak/kaydırma durumunda, `691ce0d` app.css dosyası özgün cascade konumuna geçici yerleştirilerek önce/sonra PNG'lerle piksel bazında karşılaştırılır. Değişen yayın saati, DB gecikmesi veya geçici parola mesajları maskelenmez; aynı DOM karşılaştırması bu değişkenleri sabit tutar. Ortak kuralların değişmediği kaynak kural karşılaştırmasıyla doğrulanır. Diğer ekranlarda kaldırılan seçicilerin hiçbir öğeyle eşleşmediği de denetlenir; yalnız kaldırılan kurallar özgün app.css CSSOM nesnesine geçici eklenir. Ortak root/font/renk kuralları yeniden yüklenmez. Stil çizimi iki requestAnimationFrame ile beklenir; eşit olmayan çift en çok üç kez yeniden çekilir. Maske kullanılmaz; ham piksel sayıları ve deneme sonuçları `paint_attempts` alanında korunur. En çok 2/255 kanal farkı ancak bütün hesaplanmış stiller ve geometri birebir aynıysa raster yuvarlaması olarak sınıflanır; ham fark silinmez. Başarısız karşılaştırmalar `--recheck-failures` ile tek başına yeniden çekilebilir, geçen çekim/öğe/yerleşim kanıtları korunur.
- [states-summary.json](states-summary.json): 024 durum/sekme/rol/genişlik sonuçları.
- [contrast.md](contrast.md): gerçek Chromium stilleri, alfa bileşimi, metin 4,5:1; büyük metin, kontrol sınırı, odak ve seçim işareti 3:1. Hover/odak, salt okunur/pasif alanlar, hata/uyarı/başarı, yer tutucular ve pencereler ölçülür. Dekoratif `--border` kart ayırıcıları etkileşimli kontrol sınırı sayılmaz. Bu ölçüm tam WCAG uygunluğu beyanı değildir.

## Dosya kapsamı ve metin

- `app/templates/department.html`: sayfa kapsamı, yerel stiller/script, erişilebilir tablo bölgesi ve etiket yazımı.
- `app/static/design/data-entry.css`, `data-entry.js`: yalnız `.data-entry-page` kapsamı. Ortak tasarım dosyaları değişmez.
- `app/static/app.css`: yalnız 024'e özgü 59 seçici kuralı kaldırıldı. Özgün seçici, medya sorgusu ve deklarasyonların tam listesi [removed-css.json](removed-css.json) içindedir. Ortak kurallar değiştirilmez.
- Yeni test, dondurulmuş test fixture'ı ve bu klasörün yakalama/kanıt dosyaları.

Sözcük veya eylem ifadesi değişikliği yoktur. Owner onayına sunulan harf düzeni değişiklikleri: “Göstergeye İlişkin Açıklama” → “Göstergeye ilişkin açıklama”; “Hesaplama Yöntemi” → “Hesaplama yöntemi”; “Verinin Kaynağı” → “Verinin kaynağı”; gösterge yıl alanı etiketlerinin yıl sonrası kısmı küçük harfle başlar (maliyet sütunu metinleri, mevcut faaliyet ekleme kodunun bunları okuması nedeniyle kaynak yazımıyla korunur); “Bütçe İçi/Dışı” → “Bütçe içi/dışı”. CSS uppercase kaldırıldığı için özgün “Gösterge adı”, “Ölçü birimi”, program/alt program, checkbox ve diğer alan metinleri artık kaynak yazımlarıyla görünür. Veri, uyarı, düğme, bağlantı ve API metinleri korunur.

Görünüm için lead incelemesi ve owner onayı beklenir; bunlar otomatik kontrollerin yerini almaz.

Sonuç: **194 çekim / 9850 öğe-hedef / 0 eksik / 0 taşma-kırpılma-örtüşme**. 024 dışındaki 178 karşılaştırmanın 177'sinde ham piksel farkı sıfırdır. 390 px Genel Bakış'ta yuvarlatılmış kenarlarda 79 pikselde en çok 2/255 kanal yuvarlaması vardır; 218 DOM öğesinin tüm hesaplanmış stillerinde ve geometrisinde fark **0**. Bu ham değerler raporda tutulur; görünüm değişikliği olarak gizlenmez. 024: **40 durum kontrolü / 35 AA çifti / 0 hata**.

## Çalıştırılan testler

Yerel PostgreSQL 18 tam takımı: **2898 geçti**, 0 hata (mevcut Starlette uyarıları: 4). Tam takımın koleksiyonundan sonra eklenen iki yeni faaliyet anahtarı senaryosu dahil odaklı `tests/test_department_design.py`: **22 geçti**, 0 hata. Nihai PR başındaki tam koleksiyon 2900 testtir; CI sonucu PR açıklamasındadır. `compileall`, yeni script ve mevcut `app.js` için `node --check`, yakalama betikleri için Python derleme ve `git diff --check` geçti.

## Yeniden çalıştırma

Yerel PostgreSQL 16+ ve Chromium kullanın; uygulama/canlı DB URL'si kullanılmaz. `CIVENSA_TEST_POSTGRES_URL` yalnız disposable localhost veritabanını göstermelidir. `CIVENSA_CHROMIUM_PATH` isteğe bağlı sistem Chromium yoludur.

```sh
# Önce 691ce0d worktree'sinde (aynı sentetik fixture ve Chromium):
python docs/design/rollout/civ-096/verify_rollout.py --capture-out /tmp/civ097-baseline
# Sonra bu dalda:
python docs/design/rollout/civ-097/verify_rollout.py --baseline /tmp/civ097-baseline
python docs/design/rollout/civ-097/capture_states.py
python -m pytest -q --require-postgres -n 4 --dist loadfile --max-worker-restart=0
node --check app/static/design/data-entry.js
```

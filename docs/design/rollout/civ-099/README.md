# CIV-099 · Bölüm editörü (012)

Başlangıç: `feature/authorization-workflow-phase5`, `2f1cd34`. İçerik D-224 / CIV-095 ekran 012 bileşenlerine taşınır. CIV-096 ortak düzeni, veri, form alanları, hedefler, rol ve durum koşulları korunur. Yeni bağımlılık yoktur.

Rapor araçları, yerel dışa aktarma disclosure'ı, birim raporu özeti, metin/önizleme düzeni, metin ve renk içeren bölüm durumları, kaynak/malî tablolar ve denetim geçmişi aynı ekran kapsamındadır. Önizleme mevcut `activity_sections.js` ile çalışır. Denetim özeti mevcut önce/sonra kaydından, yalnız tarayıcıda ve `textContent` ile üretilir; ham veriler varsayılan kapalı **Teknik ayrıntı** içinde aynen korunur. Eklemeler ancak eski bloklar değişmeden korunmuşsa paragraf sayısıyla belirtilir; diğer içerik değişiklikleri “İçerik güncellendi.” olarak gösterilir. Tanınmayan/eski veri güvenli bir Türkçe açıklamaya düşer.

İkonlar mevcut ISC lisanslı Lucide arrow-left / chevron-right çizimleridir; inline SVG, `currentColor`. Textarea odağı 2 px vurgu outline'ıdır; kenar rengi değişmez, gölge yoktur. Menüde sonraki Tab ilk indirme bağlantısına geçer. Escape disclosure'ı kapatır ve kendi summary öğesine döner. Dışarı tıklama dışa aktarma menüsünü kapatır. Yeni kod hiçbir istek göndermez.

## Görseller

Tam sayfa Chromium, DPR 1, `tr-TR`, `Europe/Istanbul`, viewport yüksekliği 900 px. Yalnız sentetik veriler. Boyutlar: [screenshots.json](screenshots.json); her PNG ≤ 1.500.000 bayt.

| Durum | 1440 px | 390 px |
| --- | --- | --- |
| Taslak, içerik ve denetim geçmişi | [PNG](012-draft-content-1440.png) | [PNG](012-draft-content-390.png) |
| İade, notlu | [PNG](012-returned-1440.png) | [PNG](012-returned-390.png) |
| Gönderilmiş, salt okunur | [PNG](012-submitted-1440.png) | [PNG](012-submitted-390.png) |
| Dışa aktarma menüsü açık | [PNG](012-export-1440.png) | [PNG](012-export-390.png) |

## Koruma ve ölçüm

- [template-contract.json](template-contract.json): özgün 123 Jinja bloğu ve 45 kimlik/hedef/rol/`data-*` özniteliği korunur. Bölüm listesi editörden sonra taşınır; DOM ve görsel gezinme sırası aynıdır. Hiçbir mevcut script seçicisi değiştirilmez.
- `tests/fixtures/section_editor_012_contract.json`: eski şablonun gerçek PostgreSQL çıktısından dondurulmuş sözleşme. Personel/yetkili personel/müdür/Strateji × boş taslak/içerikli taslak/iade/gönderilmiş/onaylı × metin/kaynak/malî/yapılandırılmış/gösterge/beyan bölümü = 120 çıktı karşılaştırması. Kimlik, alan adı, `data-*`, action/method, href, option seçimi, required/readonly/disabled ve rol/durum ayrımları; gizli alanlar ve kapalı disclosure'lar dahil. Sunum sınıfları/stilleri ve değişken alan değerleri fixture'a alınmaz; CSRF değeri saklanmaz. Her alan/option/düğmenin form action/method bağlantısı ve form içindeki sırası ayrıca birebir karşılaştırılır; bu ek kontrol başlangıç şablonunda ve yeni şablonda 20’şer senaryoyla doğrulanır. Özgün Jinja blokları ve hedef öznitelikleri ayrıca kaynak düzeyinde karşılaştırılır.
- `tests/test_section_editor_design.py::test_012_preserves_all_fields_and_action_targets`: yukarıdaki 20 parametrik senaryo; her biri altı bölüm kontrol eder.
- `tests/test_section_editor_design.py::test_012_export_audit_focus_and_safe_summary`: 1440/390'da Enter/Tab/Escape ve odağın dönüşü, kapalı ham veri, Türkçe değişim özeti, bozuk/eski JSON ve script içeren verinin güvenli metin olarak kalması, yalnız outline kullanan textarea odağı.
- Mevcut iki tarayıcı testi menü yerleşimine uyarlandı: `test_ar_typeset_contract.py::test_download_button_in_browser` ve `test_activity_sections_pdf.py::test_pdf_button_download_in_browser`, indirmeden önce `[data-section-export] > summary` öğesine tıklar. İndirme seçicileri, dosya adı ve dosya içeriği assertion'ları değişmez; başka mevcut test değişikliği yoktur.
- [capture-summary.json](capture-summary.json): 97 ekran × iki genişlik. Öğe/hedefler, belge taşması, yerel kaydırma dışındaki taşma, kırpılma, örtüşme ve ortak düzen denetlenir. Yalnız `.section-editor-page` içeren gerçek 012 şablonu değişmiş ekran sayılır; ayrı beyan formları, içe aktarma önizlemesi ve hata ekranı kapsam dışındadır ve piksel karşılaştırmasına dahildir. Ortak uygulama dosyaları kaynak düzeyinde byte olarak değişmez; diğer ekranlara yeni CSS/JS yüklenmez. Aynı DOM/veri/saat/odak/kaydırma üzerinde eski cascade yeniden kurularak önce/sonra PNG'ler karşılaştırılır; app.css değişmediğinden eklenecek eski kural listesi boştur. Maske yoktur; ham farklar saklanır. En çok 2/255 kanal farkı yalnız bütün hesaplanmış stiller ve geometriler birebir aynıysa raster yuvarlaması sayılır. Başarısız karşılaştırmalar tek başına yeniden çalıştırılabilir.
- [states-summary.json](states-summary.json): 012'nin personel/müdür durumları ve Strateji/idare ek yüzeyleri; her iki genişlikte boş/içerikli taslak, notlu iade, salt okunur gönderilmiş/onaylı rapor. Bunlar **sunum fixture'larıdır**; iş akışı geçiş kabul testi değildir. Mevcut `test_ar_unit_workflow_ui.py` gerçek gönderim/iade geçişlerini ayrıca doğrular. Tarayıcı yalnız yerel GET istekleri yapar; kalıcı durum özeti önce/sonra aynıdır.
- [contrast.md](contrast.md): gerçek Chromium stilleri, alfa bileşimi; normal metin 4,5:1, büyük metin/simge/kontrol sınırı/odak/seçim işareti 3:1. Hover/odak, hata/uyarı, kaynak ve malî alanlar, açık teknik ayrıntı ve dışa aktarma, yerel dosya düğmeleri ölçülür. Kart ayırıcıları dekoratiftir. Kapalı native details içeriği Chromium'da geometri döndürebildiğinden ölçüm `checkVisibility()` ile gerçekten çizilen öğeleri seçer; gerçek taşma/örtüşmeler bastırılmaz. Bu ölçüm tam WCAG uygunluğu beyanı değildir.

## Dosya ve metin değişiklikleri

`app/templates/activity_sections_editor.html`; yeni `app/static/design/section-editor.css` / `section-editor.js`; yeni test/fixture; bu klasörün araçları, ölçümleri ve sekiz PNG. `app.css`, `activity_sections.css`, `shell.css`, `data-entry.css` ve mevcut sayfa scriptleri değişmez. **Kaldırılan CSS kuralı: 0**; app.css içinde yalnız 012'ye özgü kural bulunmadı. **Değiştirilen mevcut seçici: 0**. Yeni sunum seçicileri `.section-editor-page`, `[data-section-export]`, `[data-section-audit]`, `[data-section-change]` içindedir; mevcut `data-ar-*` seçicileri korunur.

Owner onayına sunulan başlık harf düzeni: “ÜST YÖNETİCİ SUNUŞU” → “Üst yönetici sunuşu”; “YÖNETİCİ ÖZETİ” → “Yönetici özeti”; “I- GENEL BİLGİLER” → “I- Genel bilgiler”; “II- AMAÇLAR ve HEDEFLER” → “II- Amaçlar ve hedefler”; “III- FAALİYETLERE İLİŞKİN BİLGİ VE DEĞERLENDİRMELER” → “III- Faaliyetlere ilişkin bilgi ve değerlendirmeler”; “IV- KURUMSAL KABİLİYET VE KAPASİTENİN DEĞERLENDİRİLMESİ” → “IV- Kurumsal kabiliyet ve kapasitenin değerlendirilmesi”; “V- ÖNERİ VE TEDBİRLER” → “V- Öneri ve tedbirler”; “EKLER” → “Ekler”. Veri kaydı değişmez; yalnız gösterim eşlemesi kullanılır. CSS uppercase kaldırılan tüm alan/tablo başlıkları [case-changes.json](case-changes.json) içinde önce/sonra listelenir; kaynak Türkçe sözcükler korunur. Listede 67 taslak alanı/tablo başlığı ve Strateji incelemesinde koşullu görünen “İade gerekçesi” / “Yeniden açma gerekçesi” olmak üzere 69 çift vardır; son iki etiket değişmeyen iş akışı şablonundan çıkarılır, alan/hedef koşulları dondurulmuş durum testiyle korunur.

Yeni açıklamalar: “Dışa aktar”, “Rapor bölümleri”, “Teknik ayrıntı”; denetimde “Durum: {önce} → {sonra}”, “İçerik: {n} paragraf eklendi”, “İçerik temizlendi.”, “İçerik güncellendi.”, “Uygulanamaz gerekçesi güncellendi.”, “Uygulanamaz gerekçesi temizlendi.”, “Tablo satırları güncellendi.” ve eski/tanınmayan kayıtta “Kayıt ayrıntılarını Teknik ayrıntı bölümünde inceleyebilirsiniz.”. Geri bağlantıdaki metin ok karakteri inline SVG ile değiştirilir; “Tamamlanma görünümü” sözcükleri aynıdır. Diğer düğme/bağlantı/uyarı/veri metinleri korunur.

## Yeniden çalıştırma

Disposable localhost PostgreSQL 16+; `CIVENSA_TEST_POSTGRES_URL` ve isteğe bağlı `CIVENSA_CHROMIUM_PATH`. Uygulama/canlı DB kullanılmaz.

```sh
# Önce 2f1cd34 worktree'sinde başlangıç görüntü/envanteri:
python docs/design/rollout/civ-096/verify_rollout.py --capture-out /tmp/civ099-baseline
# Sonra bu dalda:
python docs/design/rollout/civ-099/verify_rollout.py --baseline /tmp/civ099-baseline
python docs/design/rollout/civ-099/capture_states.py
python docs/design/rollout/civ-099/collect_case_changes.py
python -m pytest -q --require-postgres -n 4 --dist loadfile --max-worker-restart=0
node --check app/static/design/section-editor.js
```

Başlangıç aracı CIV-096'nın daha eski tasarım karşılaştırmasını da çalıştırır; CIV-097 harf düzeni değişiklikleri o eski karşılaştırmada fark üretir. CIV-099 karşılaştırması başlangıç aracının **2f1cd34 üzerinde ürettiği gerçek envanteri** kullanır.

Görünüm lead incelemesi ve owner onayına sunulur; merge veya deploy yapılmaz.

Ölçüm sonucu: **194 çekim / 9.838 özgün öğe-hedef / 0 eksik / 0 taşma-kırpılma-örtüşme**. 012 dışındaki 152 karşılaştırmanın 145'inde ham piksel farkı sıfırdır; yedisinde toplam 133 pikselde en çok 2/255 kanal yuvarlaması bulunur. Bu yedi karşılaştırmada bütün hesaplanmış stiller ve geometriler birebir aynıdır; ham farklar raporda korunur. 012: **124 durum kontrolü / 26 AA çifti / 0 hata**. Sekiz PNG'nin en büyüğü **291.114 bayt**.

Odaklı PostgreSQL kontrolleri: yeni sözleşme/klavye testleri **22 geçti**; mevcut bölüm editörü ve gerçek gönderim/iade tarayıcı testleri ilk odaklı geçişte **3 geçti**. Tam takımın ve iki indirme testinin nihai sonucu PR açıklamasında verilir.

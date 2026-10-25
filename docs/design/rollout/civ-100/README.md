# CIV-100 — 024 kaynak farkı ve SVG onay işareti

Kaynak farkı kutusu aynı maliyet hücresinde, aynı `.source-disagreement.issue-list` düğümünde kalır. Mevcut `<b>` başlık bir `<summary>` içine taşınır; iki paragraf, `.computed-total`, gerekçe alanı ve onay düğmesi `<details class="source-disclosure">` içinde açılır. Başlık tek satırdır; tehlike rengi ve açıklayıcı metni birlikte kullanır. Enter/Space açar; Escape kapatır ve odağı özete döndürür.

Mevcut gerekçe alanı şablonda `input` olduğundan türü, `minlength="10"`, sınıfı ve `data-field` niteliği aynen korunmuştur. `app.js` ve istek sözleşmesi değişmemiştir. Yeni kullanıcı metni yoktur. Eklenen üç sarmalayıcı kaldırıldığında `department.html`, referans `9b0a5da` sürümüyle bayt düzeyinde aynıdır; mevcut öğeler, nitelikler ve metinler için ayrıca bu karşılaştırma çalıştırılmıştır.

Checkbox işareti boş bir pseudo-element üzerinde `currentColor` ile boyanan SVG maskesidir. Yazı glifi kaldırılmıştır; çalışma zamanı bağımlılığı eklenmemiştir.

## Görseller

Tam sayfa PNG'ler, ölçek 1, sentetik veri; tablo kendi mevcut kaydırma alanında 2027 Bütçe sütununa kaydırılmıştır. Sayfada yatay taşma yoktur. Checkbox yakın planı mevcut etiket düğümünün kırpımıdır.

| Durum | 1440 px | 390 px |
| --- | --- | --- |
| Kaynak farkı, kapalı | [PNG](024-costs-closed-1440.png) | [PNG](024-costs-closed-390.png) |
| Kaynak farkı, açık | [PNG](024-costs-open-1440.png) | [PNG](024-costs-open-390.png) |
| Seçili SVG checkbox | [Yakın plan](024-checkbox-checked.png) | — |

Boyutlar ve bayt sayıları: [screenshots.json](screenshots.json). Beş PNG'nin en büyüğü 130.727 bayttır; her biri 1.500.000 bayt sınırının altındadır.

## Durum ve kontrast kanıtı

[states-summary.json](states-summary.json): 1440/390 × müdür/personel/strateji × taslak/iade/gönderildi/onaylandı/kapalı dönem × disclosure kapalı/açık = **60 kontrol, 0 hata**. Kapalı satır **213 px**, aynı satır kaynak farkı olmadan **201 px**; fark **12 px**. Açma, Escape ile kapatma, odak dönüşü, öğe/hedef korunması, belge genişliği, kırpılma ve örtüşme denetlendi. Tarayıcı yalnız loopback GET istekleri kullanır; veritabanı özeti yakalama öncesi ve sonrası aynıdır.

[contrast.md](contrast.md): gerçek hesaplanmış renklerden **22 çift, 0 AA ihlali**. Yeni başlık `--danger / --danger-bg`: **5,75:1** (metin eşiği 4,5:1); SVG işareti `--surface / --accent`: **6,28:1** (işaret eşiği 3:1); başlığın odak çizgisi `--accent / --danger-bg`: **5,49:1** (3:1). Açık/kapalı, odak ve hover durumları ölçüldü; SVG pseudo-elementinin maskesi ve boyadığı renk ayrıca doğrulandı.

## Test ve seçici değişiklikleri

- `tests/test_department_design.py::test_024_source_disclosure_contract_height_and_confirm[1440/390]`: kaynak farkı taslağı dondurulmuş alan/hedef sözleşmesiyle tam karşılaştırılır; sadece yeni `summary` ve mevcut gerekçe/onay kontrolleri eklenir. Kutu hücresi, sınıfları, `data-year/kind/source`, paragrafları ve başlık korunur. Fontlar yüklenince kapalı satır yüksekliği 1440'ta temiz satırdan en çok 16 px fazla olabilir. Enter/Space/Escape ve odak dönüşü; hesaplanan toplamın güncellenmesi ve `hidden` açılıp kapanması; 9 karakterle sıfır yazma isteği; geçerli gerekçeyle tam PUT hedefi/yükü, toplamın güncellenmesi ve kaynak tutarının korunması denetlenir.
- `tests/test_source_conflicts_ui.py::test_activity_decision_keeps_sibling_drafts`: mevcut gerekçeyi doldurmadan önce `summary` açılır. Mevcut taslak ve kaynak koruma kontrolleri değişmez.
- Yeni sunum seçicileri: `.data-entry-page .source-disagreement`, `.data-entry-page .source-disclosure summary`, `.data-entry-page .source-disclosure-body`. Escape delegasyonu: `.source-disclosure[open]` ve içindeki `summary`.
- Mevcut `.data-entry-page input[type=checkbox]:checked::before` seçicisi SVG maskesi çizer. `.source-disagreement`, `.source-total-reason`, `.confirm-source-total`, `.computed-total`, maliyet anahtarları ve `app.js` seçicileri değişmez.
- Dondurulmuş `tests/fixtures/department_024_contract.json` ve mevcut sözleşme testleri değiştirilmemiştir.

## Tekrar çalıştırma

Yalnız disposable localhost PostgreSQL 16+ ve Chromium kullanın. `CIVENSA_TEST_POSTGRES_URL` test sunucusunu, `CIVENSA_CHROMIUM_PATH` Chromium yolunu belirtir; canlı bağlantı kullanılmaz.

Değişiklik öncesi `9b0a5da` worktree'sinde mevcut CIV-096 yardımcı modülünün `guide.ui_main(SimpleNamespace(out=Path('/tmp/civ100-before') / str(width), viewport_width=width), shell.local_test_url())` çağrısını 1440 ve 390 için çalıştırın. Bu yalnız geçici tam PNG/DOM referansını üretir; CIV-096 betiğinin kendi `main()` fonksiyonu çağrılmaz, eski rollout belgeleri yazılmaz.

Bu dalda:

```sh
python docs/design/rollout/civ-100/verify_rollout.py --baseline /tmp/civ100-before --base-ref 9b0a5da
python docs/design/rollout/civ-100/capture_states.py
python -m pytest -q --require-postgres tests/test_department_design.py tests/test_source_conflicts_ui.py
python -m pytest -q --require-postgres -n 4 --dist loadfile --max-worker-restart=0 --durations=20
node --check app/static/design/data-entry.js
git diff --check
```

Kod kapsamı yalnız `department.html`, `design/data-entry.css/js`, iki test dosyası ve bu kanıt klasörüdür. Veritabanı, migration, rota, API, ortak shell ve CIV-099 dosyaları değiştirilmemiştir. Türkçe UI metinleri aynıdır; owner onayı gerektiren yeni metin yoktur.

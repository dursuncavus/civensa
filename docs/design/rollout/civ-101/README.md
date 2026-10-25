# CIV-101 · 012 düzeltmeleri

Başlangıç: `d671eb8` (`feature/authorization-workflow-phase5`; CIV-099: `67f292c`). Sentetik verili, disposable localhost PostgreSQL 18 kullanıldı.

`editor_context`, seçilen bölümün olaylarındaki tekil kullanıcı kimliklerini bir `users.id IN (...)` sorgusuyla okur. Şablon tam adı gösterir; eşlemede bulunmayan kullanıcı için `Kullanıcı {id}` korunur. Adlar HTML olarak kaçışlanır. İdare yeniden açma satırında kayıtlı ad gösterilir; görünür kimlik kaldırılır. ARContentEvent ve kaydedilmiş olay verileri değişmez.

31 sabit tablo başlığı yalnız 012 gösteriminde cümle düzenine çevrilir. Kaynak tabloları doğrudan eşlemeyi kullanır. Ortak malî şablonun render edilmiş çıktısındaki yalnız tam `<th>…</th>` parçaları eşlenir; sabit HTML parçaları dışında `safe` uygulanmaz. Form/ARIA etiketleri, alan değerleri, kurum adları ve ekonomik sınıflandırma listeleri korunur. “No” kısaltması ve resmî “Red ve İadeler” etiketi aynı kalır. Ortak malî şablon, hizmet etiketleri, Excel üretimi/içe aktarma, Word/PDF kodu, CSS ve JS değişmez. Bütün başlık çiftleri [header-changes.json](header-changes.json) içinde ve PR açıklamasında owner onayına sunulur.

## Görseller

Chromium, DPR 1, viewport yüksekliği 900 px, `tr-TR`, `Europe/Istanbul`, açık tema ve azaltılmış hareket. Her PNG ≤ 1.500.000 bayt; boyutlar [screenshots.json](screenshots.json) içinde. Malî tabloya sentetik iç denetim kaydı eklenir. Yerel yatay tablo kaydırması son sütunlara getirilerek “Alınan önlemler” gösterilir; belge yatay taşmaz.

| 012 alanı | 1440 px | 390 px |
| --- | --- | --- |
| Bölüm denetim geçmişi, kullanıcı adı | [PNG](012-history-1440.png) | [PNG](012-history-390.png) |
| III.A.3 malî denetim tablosu ve geçmişi | [PNG](012-financial-audit-1440.png) | [PNG](012-financial-audit-390.png) |

## Kanıt ve sınırlar

- [capture-summary.json](capture-summary.json): tüm 97 ekranın 1440/390 çekimi; başlangıç envanterindeki özgün öğe/hedefler, belge taşması, yerel kaydırma dışındaki taşma, kırpılma, örtüşme ve ortak düzen kontrolleri. Yalnız `.section-editor-page` içeren ekran 012 kapsamındadır. Diğer ekranların kaynakları değişmez; 012 CSS/JS'si bu ekranlara yüklenmez. CIV-099'daki aynı DOM/saat/odak/kaydırma üzerinde cascade/piksel kontrolü korunur. Ham farklar raporlanır; en çok 2/255 kanal yuvarlaması ancak bütün hesaplanmış stiller ve geometriler eşitse kabul edilir. Bu ölçüm ayrı oturumların değişken tarihlerini piksel piksel karşılaştırdığı iddiası değildir.
- [states-summary.json](states-summary.json): boş/içerikli taslak, iade, gönderilmiş, onaylı; müdür, personel, Strateji/idare; 1440/390. Sayfa düzeni, klavye odağı, disclosure Enter/Escape ve değişmeyen kalıcı durum özeti. Tarayıcı yalnız yerel GET yapar.
- [contrast.md](contrast.md): gerçek Chromium renkleri, hover/odak, açık disclosure, native dosya düğmesi ve seçim işareti. CIV-099 eşikleri korunur. CSS ve JS byte olarak değişmez; paylaşılan kaynakların ve dondurulmuş sözleşmenin hash kanıtı [unchanged-contracts.json](unchanged-contracts.json) içindedir.
- `tests/fixtures/section_editor_012_contract.json` ve mevcut sözleşme assertion'ları aynen korunur. `tests/fixtures/civ101_financial_headers.json`, başlangıç dalındaki hizmet listelerinden bağımsız olarak dondurulmuştur.

## Değişen testler

`tests/test_section_editor_design.py` içine üç test eklenir:

- `test_012_audit_names_batch_lookup_and_missing_user_fallback`: iki mevcut kullanıcı, tek toplu sorgu, tam ad, HTML kaçışlama, eksik kullanıcı yedeği. Güncel FK gerçek bir sahipsiz olay eklemeyi engellediğinden yedek aynı gerçek route context'i ve şablonuyla, bulunamayan tarihî kullanıcı kimliği taşıyan olay üzerinde render edilir.
- `test_012_reopen_shows_only_actor_name`: gerçek onay/yeniden açma HTTP akışı sonrası görünür ad ve kaldırılan kimlik. Bu iki regresyon başlangıç `d671eb8` üzerinde başarısız, düzeltmede başarılıdır.
- `test_012_sentence_case_preserves_excel_and_export_headers`: dondurulmuş ENTRY_FIELDS/EXPENSE_FIELDS/REVENUE_FIELDS/budget_columns, üç gerçek Excel şablonu, gerçek Word üretimindeki bütçe ve dört kayıt türü başlığı; 31 ekran başlığı, resmî sınıflandırma adları ve değişmeyen ARIA etiketi.

`tests/test_activity_financial.py::test_blank_zero_revenue_and_final_consistency`: ekran beklentisi tam `<th>Net tahsilat</th>` olur; sayı, boş/sıfır, hesap ve API assertion'ları korunur. Mevcut CIV-099 testleri değiştirilmez.

## Yeniden çalıştırma

`CIVENSA_TEST_POSTGRES_URL` yalnız disposable localhost PostgreSQL 16+ veritabanını, `CIVENSA_CHROMIUM_PATH` kurulu Chromium'u göstermelidir. Uygulama/canlı DB ayarları capture aracı tarafından kullanılmaz.

Başlangıç dalında `docs/design/rollout/civ-096/verify_rollout.py` modülünü import edip `OUT` değerini geçici bir klasöre ayarlayarak `main()` fonksiyonunu `--capture-out /tmp/civ101-before` ile çalıştırın. Bu eski aracın kendi tarihî tasarım karşılaştırmaları fark raporlayabilir; CIV-101 karşılaştırması üretilen gerçek `screens.json` envanterlerini kullanır. Başlangıç worktree'sindeki uygulama kaynakları değiştirilmez.

```sh
python docs/design/rollout/civ-101/verify_rollout.py --baseline /tmp/civ101-before
python docs/design/rollout/civ-101/capture_states.py
python -m pytest -q --require-postgres -n 4 --dist loadfile --max-worker-restart=0
python -m compileall -q app
node --check app/static/design/section-editor.js
git diff --check
```

Merge veya deploy yapılmaz. Başlık harf düzeni ve görünüm owner onayına sunulur.

## Nihai çekim sonucu

**194 çekim / 9.880 özgün öğe-hedef / 0 eksik / 0 belge taşması / 0 kırpılma-örtüşme-ortak düzen hatası**. 012 dışındaki 152 kontrolün 147'sinde ham piksel farkı sıfır; 5'inde en çok 2/255 kanal yuvarlaması var ve bütün hesaplanmış stiller ile geometriler birebir aynı. 012: **124 durum kontrolü / 26 AA çifti / 0 hata**. Kontrast raporu CIV-099 ile byte olarak aynı. Dört PNG'nin en büyüğü **326.590 bayt**.

Odaklı PostgreSQL grubu: **42 geçti**; son kısaltma/sınıflandırma istisnalarıyla başlık/Excel/Word testi ayrıca **1 geçti**. İstisnalardan etkilenen bütçe görünümü müdür/personel/Strateji için iki genişlikte yeniden ölçüldü; 124 durum kaydı ve 26 AA çifti yine hatasız. Tam takım ve PR başının CI sonucu PR açıklamasında raporlanır.

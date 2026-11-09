# CIV-201 — Uzun Strateji sayfaları ve ortak kayıt bildirimi

9 Kasım 2026. Taban: `feature/authorization-workflow-phase5`, `e1eb2bff298c9a23680db3fc433d84a2ff21bf6c` (önce güncellendi). Dal: `task/civ-201-uzun-sayfalar`.

Müdürlük içerikleri `repeat(auto-fill,minmax(17rem,1fr))` kart ızgarasında gösterilir. Başlık zemini `var(--accent-soft)`, başlık rengi `var(--accent-hover)`; tek satır özet ve “Ayrıntıyı aç” düğmesi vardır. Düğme `data-open-dialog` ile yerel `<dialog>` açar; başlık ve `form method="dialog"` içindeki “Kapat” düğmesi bulunur. Uzun ikincil metinler tek satırlık `details/summary` önizlemesine katlanır. Arama Türkçe büyük/küçük harfiyle müdürlük adına göre süzer. Üç veya daha az müdürlükte mevcut satır içi düzen korunur.

Kaynak karşılaştırması tüm kaynak satırlarını ve mutabakat satırlarını korur. Müdürlüğe bağlı ara toplamlar ilgili ayrıntıdadır; ortak program/alt program kontrolleri ayrı bir katmandadır. Operasyon sayfası bütün otomatik ve manuel kontrolleri korur; gerçek manuel teyit formu görünür kalır. Gösterge formlarının hedefleri, CSRF ve revizyon alanları değişmez. Malî sayfalarda müdürlük tutarları ve eksikleri birlikte açılır; idare bütçesi ve malî tablo formları ayrıca adlandırılmış bir diyalogdan açılır. Sayısal hücre ve başlıklar sağa hizalıdır ve tabular rakam kullanır. Her malî tabloda yalnız bir yıl varsa yıl başlıkta gösterilir; birden fazla yıl varsa yıl sütunu korunur. Güncel tam seed, bazı müdürlüklerin 2027 düzeltme notlarını da içerir; bu kayıtlar kaldırılmaz.

`SavedNoticeMiddleware` yerel HTML form POST → 303 → başarılı HTML GET akışını bir kez işaretler. `base.html` içindeki `role="status"` bildirimi yalnız 200 HTML yanıtta açılır; metni “Kaydedildi.” olur. Hata sayfaları, JSON/API ve fetch istekleri başarı bildirimi üretmez. `saved-notice.js` gerçek submit sırasında sekmeye ait konumu kaydeder ve başarıdan sonra kaydırmayı geri yükler. Bildirim ana içeriğin başındadır ve kaydırıldığında görünür kalır. Bildirimli yanıt önbelleğe alınmaz. Inline script ve `on*` olay özniteliği eklenmedi.

## 1440 × 900 ölçümleri

Chromium 151, deviceScaleFactor=1, fontlar yüklendikten sonra `document.documentElement.scrollHeight`; ekran sayısı yükseklik / 900. Eşik: **7.200 px**. Fotoğraflar 1440×900 görünüm görüntüleridir, tam sayfa birleştirmesi değildir.

| Sayfa | Önce (px) | Sonra (px) | Sonra (ekran) | Önce / sonra |
| --- | ---: | ---: | ---: | --- |
| `/source-comparison?period_id=1` | 2.260.016 | 2.806 | 3,12 | [Önce](shots/source-comparison-before.png) · [Sonra](shots/source-comparison-after.png) |
| `/operations?period_id=1` | 617.608 | 5.542 | 6,16 | [Önce](shots/operations-before.png) · [Sonra](shots/operations-after.png) |
| `/activity-reports/revisions/1` | 306.768 | 3.121 | 3,47 | [Önce](shots/indicator-report-before.png) · [Sonra](shots/indicator-report-after.png) |
| `/activity-sections/reports/1?code=III.A` | 22.763 | 6.372 | 7,08 | [Önce](shots/financial-overview-before.png) · [Sonra](shots/financial-overview-after.png) |
| `/activity-sections/reports/1?code=III.A.1` | 18.899 | 6.372 | 7,08 | [Önce](shots/financial-budget-before.png) · [Sonra](shots/financial-budget-after.png) |

Ham ölçümler: [heights.json](heights.json). CIV-200 ile küçük farklar, bu görevde aynı sabit tabanın yeniden ölçülmesindendir.

Tekrarlama: `CIVENSA_CHROMIUM_PATH=/usr/bin/chromium python scripts/capture_civ201.py`. Betik geçici SQLite üzerinde `scripts/profile_strateji_steps.py` içindeki `create_schema()` ve `seed(tiny=False)` kullanır; sabit tabanın şablon ve CSS/JS dosyalarını Git nesnelerinden okur ve önce/sonra görüntülerini üretir. Onaylı test fixture'ları dışındaki belediye dosyaları ve canlı veritabanı kullanılmaz. Sentetik Strateji hesabı, personel hesabı ve açıkça sentetik yayın dayanağı kullanılır. Tam şekil: 34 müdürlük, 33 dönem kapsamı, 105 kart, 226 gösterge, 182 faaliyet, 1.270 ekonomik değer. Gerçek form yollarıyla yayın, EK-1 belgeleri ve gösterge raporu oluşturulur.

## Doğrulama

- `tests/test_civ201_pilot_browser.py`: atılabilir PostgreSQL üzerinde aynı tam seed; beş sayfanın kart sayıları, benzersiz diyalog hedefleri, açma/kapatma ve odak iadesi, Türkçe arama, yatay taşma, yükseklik, sayısal hizalama, CSP ve script/olay öznitelikleri. Kaynak ve mutabakat satır sayıları, kontrol sayıları ve gösterge form sayıları korunur.
- Gerçek localhost HTTP sunucusunda Chromium submit: `/structure` müdürlük adı kaydı ve `/operations` sentetik teyit geri çekmesi; 303, görünür `role=status`, korunan scroll ve yenilemede tek kullanımlık bildirim. Geçersiz operasyon maddesinde 422 ve gizli başarı bildirimi.
- `tests/test_civ201_saved_notice.py`: 13 sunucu regresyonu; 4xx/422/500 hedefleri, fetch/JSON/API ayrımı, hedef URL, Content-Length ve tek kullanımlık gösterim.
- Donmuş fixture dosyaları değiştirilmedi. `tests/civ199_contract.py` bu tabanda bulunmadığı için aynı yaklaşım yeni `tests/civ201_contract.py` içinde sayısal başlık sınıfını eski sözleşme karşılaştırmasında geri alır.
- CIV-199 için ayrılan dosyalara dokunulmadı. `ACTIVITY_REFERENCE_SUCCESSORS` değiştirilmedi; migration veya yetkilendirme/yayın kapısı değişikliği yoktur.

Tam PostgreSQL süiti ve PR CI sonuçları PR açıklamasında kaydedilir. İnceleme: Claude; birleştirme ve dağıtım yapılmaz.

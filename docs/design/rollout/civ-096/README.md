# CIV-096 · Uygulama tasarım sistemi geçişi

CIV-095 / D-229 tasarımı gerçek oturumlu uygulamanın ortak düzenine ve 033/034 Modüller içeriğine taşındı. Tokenlar, Fira Sans 400/500/600 woff2 dosyaları ve OFL lisansı prototipten aynen alındı; dış font isteği yok.

Ortak düzen 248 px açık yan menü, dört gezinme grubu, geçerli sayfa işareti, kullanıcı/bildirim alanı, sayfa başlığı ve dönem rozetini kullanır. 390 px görünümde menü içerikten sonra gelir; “Menüye git” ve “İçeriğe geç” klavyeyle çalışır. Parola penceresi Escape, odak döngüsü ve açan düğmeye odak iadesi sağlar. Parola/bildirim istekleri mevcut `app.js` içinde kaldı; bu dosya ve kullandığı kimlikler değiştirilmedi.

Diğer ekranların içerik şablonları korunur. Ortak düzenin dar sütununda geniş tablolar, sütunlarını daraltmadan yerel kaydırma alanında tutulur. Eski grid/fieldset alanlarının asgari içerik genişliği sınırlandırılır; mobil eylem grupları satıra geçer. Faaliyet Eşleştirme ekranındaki alt kayıt çubuğu başka düğmeleri örtmemesi için normal akışa alınır. Bunlar yeni düzene sığdırma düzeltmeleridir.

## Görseller

Tüm görseller sentetik “Örnek” verileriyle gerçek uygulamadan, 900 px viewport yüksekliği, DPR 1, tr-TR ve Europe/Istanbul ayarlarıyla tam sayfa çekildi. Her PNG ≤ 1.500.000 bayt.

| Ekran | 1440 px | 390 px |
| --- | --- | --- |
| 034 · Müdürlük Modüller | [PNG](034-modules-department-1440.png) | [PNG](034-modules-department-390.png) |
| 033 · Strateji Modüller | [PNG](033-modules-strategy-1440.png) | [PNG](033-modules-strategy-390.png) |
| 024 · Müdürlük veri girişi | [PNG](024-department-department-1440.png) | [PNG](024-department-department-390.png) |
| 012 · EK-1 bölüm editörü | [PNG](012-activity-sections-department-1440.png) | [PNG](012-activity-sections-department-390.png) |
| 039 · Strateji Nihai Rapor | [PNG](039-report-builder-strategy-1440.png) | [PNG](039-report-builder-strategy-390.png) |

Son koşu: **194/194 çekim**, **9.560 eski öğe/hedef**, **0 kayıp/taşma/kırpılma/çakışma**. Kontrast: **19 çift, 0 başarısız**. Chromium 151.0.7922.173. [Görsel boyutları](screenshots.json): en büyük PNG **1.141.820 bayt**.

## Tekrarlanabilir doğrulama

Yerel, geçici PostgreSQL 16+ sunucusuna ait `CIVENSA_TEST_POSTGRES_URL` ve kurulu Chromium gerekir. Canlı uygulama veritabanı ayarları kullanılmaz. Her genişlik için ayrı, gerçek Alembic geçişleriyle kurulan ve sonunda silinen veritabanı kullanılır.

```sh
python -m pip install -r requirements-dev.txt
# Sistem Chromium yoksa: python -m playwright install chromium
python docs/design/rollout/civ-096/verify_rollout.py
python -m pytest -q --require-postgres -n 4 --dist loadfile
```

`CIVENSA_CHROMIUM_PATH` sistem Chromium'unu seçebilir. Tam CIV-093 ekran haritası `/tmp/civ096-captures/{1440,390}/` altında üretilir; depoya yalnız yukarıdaki on PNG ve bu doğrulama paketi alınır.

- [capture-summary.json](capture-summary.json): 97 eski ekran durumu × iki genişlik. Her durumun eski DOM öğeleri, yinelenenler dahil, etiket/kimlik/alan adı/alan türü/hedef bazında karşılaştırılır. Yeni atlama bağlantıları ek öğedir. Belge genişliği, kaydırma alanı dışına taşan öğeler, kırpılan ve üst üste gelen kontroller ayrıca ölçülür.
- Zamanı her kurulumda üretilen sentetik yayın/denetim damgaları karşılaştırmada normalleştirilir. Parola alanlarının eski CSS büyük harf dönüşümüyle çizilmiş üç etiketi aynı Türkçe sözcüklerin cümle düzenine eşlenir. Form dışında çalışan iki parola düğmesinin örtük `submit` türü açık `button` türüne eşlenir; hedefleri aynıdır. Diğer etiket ve hedefler aynen karşılaştırılır.
- [contrast.md](contrast.md): prototipteki gerçek Chromium stilleri, alfa bileşimi ve AA oran hesabı kullanılır. Her oturumlu ekranda ortak düzen; 033/034’te tam içerik, hover/odak, açık bildirim ve parola penceresi, bildirim sayacı ve toast ölçülür. Normal metin 4,5:1; büyük metin, simge, kontrol sınırı ve odak çizgisi 3:1. Diğer ekranların eski içerik renkleri bu geçişin kontrast kapsamına alınmaz.
- Yakalama aracı yalnız yerel GET ve CIV-093’ün iki salt okunur bütçe hesaplama POST rotasını kullanır. Diğer tarayıcı yazmaları engellenir; her aşamada bütün model tablolarının özeti değişmeden kalmalıdır.

## Metinler, seçiciler ve testler

Onaylı marka değişikliği: “RAPORLAMA” → “Kurumsal raporlama”. Parola penceresindeki üç etiketin CSS büyük harf dönüşümü kaldırıldı; sözcükler aynıdır. Yeni erişilebilirlik metinleri prototipin “İçeriğe geç”, “Menüye git”, gezinme grupları ve kaydırma bölgesinin “Yatay kaydırılabilir tablo” adıdır. Diğer metinler ve rol/hedef koşulları korunur.

`app.js` seçicilerinde değişiklik yok. Eski ortak düzen sınıfları `.sidebar-account`/`.logout`, `.notification-button`, başlık `.badge` ve bildirim `.section-head` yerine sırasıyla `.account-actions`/`.shell-button.ghost`, `.shell-button.ghost`, `.period-badge` ve `.notification-heading` kullanılır. Eski dış `.app` sınıfı `.app-shell` ile değiştirilir; böylece diğer şablonlardaki eski 64 px menü uyarlamaları yeni düzeni etkilemez. `.modal`/`.modal-card` korunur; `.workspace`, `.topbar`, `.page-header` eklenir. Modüller `.module-card.module` ve `.shell-button` bileşenlerini kullanır.

- Yeni `tests/test_design_shell.py::test_shell_preserves_navigation_for_every_role`: strateji personeli/müdürü, müdürlük personeli/müdürü; dönemli/dönemsiz tüm eski menü hedefleri, geçerli sayfa, CSRF ve çıkış formu (8 durum).
- Genişletilen `tests/test_sidebar_ui.py::test_sidebar_controls_separate_and_clickable`: mevcut boyutlara 1440/390 eklendi; atlama bağlantıları, odak döngüsü, Escape ve odak iadesi doğrulandı (14 durum). Eski bir beklenti kaldırılmadı veya gevşetilmedi.
- Diğer mevcut testlerde değişiklik yok. Odaklı komut `tests/test_design_shell.py tests/test_sidebar_ui.py tests/test_module_selection.py`: 25 test geçti.

Görsel benzerliğin son değerlendirmesi lead/ürün sahibi incelemesindedir; otomatik kontrast ölçümü tüm WCAG uygunluğunun beyanı değildir.

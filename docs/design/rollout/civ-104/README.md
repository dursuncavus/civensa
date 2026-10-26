# CIV-104 · Genel Bakış (021/022)

Başlangıç: `feature/authorization-workflow-phase5`, `09363b0` (CIV-103 sonrası).
Yalnız dashboard şablonu ve kökü `.dashboard-page` altındaki yeni CSS değişti.
Kartlar, dönem satırları, yükleme boş durumları ve ilerleme tablosu D-224 tokenlarını kullanır.
390 px’de tablo kendi odaklanabilir bölgesinde yatay kayar; DOM okuma sırası korunur.
Civensa kontrolü sıfır olduğunda normal metin, pozitif olduğunda uyarı rengindedir.

## Görseller

Chromium 151; 1440×900 ve 390×900, DPR 1, `tr-TR`, `Europe/Istanbul`.
Tüm kayıtlar sentetik; geçici yerel PostgreSQL 18 ve gerçek şablon/statik dosyalar kullanıldı.
Dönemler, yükleme listeleri ve yedi ilerleme durumu yalnız testin render bağlamında çeşitlendirildi.
Görüntüler tek viewport kesitleridir (390 px üst görünümü, kartlar ve dönemleri birlikte göstermek için 390×2200 viewport’un yalnız ilgili üst bölümüdür); başka ekranların toplu çekimi yapılmadı.
Her PNG 1.500.000 bayttan küçüktür; çekim aracı ve JSON commit edilmedi.

| Görünüm | 1440 px | 390 px |
| --- | --- | --- |
| 022 müdürlük | [PNG](022-department-1440.png) | [PNG](022-department-390.png) |
| 021 kartlar ve dönemler | [PNG](021-top-1440.png) | [PNG](021-top-390.png) |
| 021 yeni dönem açık | [PNG](021-new-period-1440.png) | [PNG](021-new-period-390.png) |
| 021 boş yükleme alanları | [PNG](021-empty-uploads-1440.png) | [PNG](021-empty-uploads-390.png) |
| 021 ilerleme tablosu | [PNG](021-progress-1440.png) | [Başlangıç](021-progress-390.png) · [Yatay kaydırılmış](021-progress-scroll-390.png) |

## Sözleşme ve testler

`tests/fixtures/dashboard_021_022.html`, başlangıçtaki şablonun değişmemiş kopyasıdır.
`tests/test_dashboard_design.py`, aynı route bağlamından eski/yeni şablondaki tüm form ve alan özniteliklerini,
method/action bağlarını, CSRF alanını, bağlantı ve query parametrelerini, kontrol metinlerini,
tüm id/data-* özniteliklerini, script kaynaklarını ve JavaScript sınıf kancalarını karşılaştırır.
Yalnız beş açıkça listelenen kontrol metni dönüşümüne ve metin düğümleri arasındaki biçimlendirme boşluklarına izin verilir.
Rol, dolu/boş listeler, doğrulanmış/bekleyen şablon ve devre dışı aktivasyon kapsanır.
Mevcut test assertion’ları değiştirilmedi.

Tarayıcı testleri iki rolde ve iki genişlikte sayfa taşması, cümle düzeni, normal/hover/odak metin kontrastı,
form açma/iptal/odak, gerçek ortak JavaScript üzerinden oluşturma/doğrulama/aktivasyon POST adresleri,
yıl/başlangıç dönemi payload’u ve gerçek oturum CSRF başlığını kontrol eder.
POST yanıtları sentetik hata yanıtlarıdır; iş kuralları ve yazma uçlarının başarı sonuçları bu yeni tarayıcı testinde çalıştırılmaz.

```sh
python -m pytest -q --require-postgres tests/test_dashboard_design.py tests/test_pp_display.py
python -m pytest -q --require-postgres -n 4 --dist loadfile --max-worker-restart=0
```

Son çalıştırmaların sonuçları PR açıklamasındadır. Canlı veritabanına bağlanılmadı.

## Kontrast

Yeni metin çiftleri normal, hover ve odakta tarayıcıda hesaplanan renklerle ≥4,5:1 olarak test edilir.
Token renklerinin bazı oranları:

| Metin / zemin | Oran |
| --- | --- |
| `--text` / `--surface` | 15,80:1 |
| `--text-secondary` / `--surface-muted` | 5,87:1 |
| `--surface` / `--accent` | 6,28:1 |
| `--surface` / `--accent-hover` | 8,58:1 |
| `--accent` / `--accent-soft` | 5,37:1 |
| `--success` / `--success-bg` | 4,71:1 |
| `--warning` / `--warning-bg` | 5,41:1 |

## Sahip onayına sunulan metin değişiklikleri

| Önce | Sonra |
| --- | --- |
| Yeni Dönem | Yeni dönem |
| Şablonu Doğrula | Şablonu doğrula |
| Aktif Et | Aktif et |
| Şablon Yükle | Şablon yükle |
| Word Verisini Tara | Word verisini tara |
| Bakanlık Şablon Kontrolü | Bakanlık şablon kontrolü |
| Word Veri İçe Aktarma · Önizleme | Word veri içe aktarma · önizleme |
| Müdürlük İlerleme Panosu | Müdürlük ilerleme panosu |
| Son İşlem | Son işlem |
| Renkle belirtilen mevcut dönem | Ek görünür metin: Görüntülenen dönem |
| Boş işlem sütunu başlığı | Görsel olarak gizli erişilebilir metin: İşlem |

Listelenen eski metinler `app.js`, `pp_sections.js` veya mevcut testler tarafından eşleştirilmiyor;
bu nedenle eski biçimi korumak gerekmemiştir. PP Tamamlanma Listesi ve Genel Bölüm Önizlemesi,
görevde listelenmeyen mevcut bağlantı metinleri olarak korunmuştur. Kart/label/th üzerindeki eski CSS büyük harf
gösterimi kaldırıldı; sözcükleri değiştirilmedi. PP, DOCX, XLSX, JSON ve Civensa korundu.
Canlı ortam, diğer tarayıcılar ve ekran okuyucu yazılımıyla doğrulama yapılmadı.

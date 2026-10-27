# CIV-135 · Gerçekleşme revizyonu (007/008)

Başlangıç: `feature/authorization-workflow-phase5`, `2d1de5f`.

İki şablon tasarım sisteminin mevcut panel, durum rozeti, form, uyarı ve tablo bileşenlerine geçirildi. `activity-reports.css` bağlantısı ortak stilleri ve mevcut kabuk kurallarını sağlar; yeni `activity-report-detail.css` yalnız bu sayfayı düzenler. Gerçekleşme, veri durumu ve hedef birlikte; formlar tek sütunda ve en fazla 44rem genişliktedir. Geçmiş kapalı başlar. Sunucu ve AJAX hataları formun üzerinde görünür.

Başlangıç şablonları `tests/fixtures/activity_contract_detail_start.html` ve `tests/fixtures/activity_evidence_row_start.html` dosyalarında byte düzeyinde aynıdır; SHA256 değerleri yeni testte sabitlenmiştir. Donmuş karşılaştırma her kontrolün sınıf/stil dışındaki bütün özniteliklerini, form sahipliğini, gizli değerleri, textarea içeriğini, seçili seçenekleri, bağlantıları, id/data/aria bağlantılarını ve kaynak `<template>` içeriğini denetler. Var olan testler değiştirilmedi.

## Görünen metin değişiklikleri

- Başlık: `{{ yıl }} Faaliyet Raporu · Revizyon {{ revizyon }}` → `{{ yıl }} Faaliyet raporu · Revizyon {{ revizyon }}`.
- Alt başlık: `Baz Performans Programı v{{ sürüm }}` → `Baz performans programı v{{ sürüm }}`.

Bu iki tam ifade testlerde arandı; yeni donmuş fixture'lar dışında eski metinle eşleşen test bulunmadı. Diğer metinler korundu. Hedef, son gerçekleşmenin yanına taşındı; boş gerçekleşmenin mevcut metin sınırı korundu.

## Ekran görüntüleri

Tam sayfa, Chromium, `tr-TR`, 1440×1000 ve 390×1000 görünüm alanları. Tüm veriler sentetiktir; gerçek kurum, kişi, dosya veya veritabanı kullanılmadı. Her PNG 1,5 MB altındadır. Öncesi görüntüleri donmuş iki şablonla, sonrası görüntüleri PR şablonlarıyla aynı bağlamda üretildi.

| Durum | 1440 önce | 1440 sonra | 390 önce | 390 sonra |
| --- | --- | --- | --- | --- |
| Müdürlük taslağı: iki gösterge, bir sapma uyarısı, gösterge başına iki kaynak | [Önce](department-draft-1440-before.png) | [Sonra](department-draft-1440-after.png) | [Önce](department-draft-390-before.png) | [Sonra](department-draft-390-after.png) |
| Form hatası: ikinci kaynağın konumu, denenen değerler ve yeniden dosya seçimi uyarısı | [Önce](department-error-1440-before.png) | [Sonra](department-error-1440-after.png) | [Önce](department-error-390-before.png) | [Sonra](department-error-390-after.png) |
| Strateji: onaylı revizyon ve gerekçeli yeni revizyon formu | [Önce](approved-1440-before.png) | [Sonra](approved-1440-after.png) | [Önce](approved-390-before.png) | [Sonra](approved-390-after.png) |

## Doğrulama

Geçici yerel PostgreSQL 16 ile `--require-postgres` kullanıldı. Yeni test modülü; Strateji müdürü taslağı, müdürlük taslağı, hatalı deneme, onaylı/geçmiş revizyon, önceki baz farkları ve açık yeni program karşılaştırmasını kapsar. Ayrıca sekiz hata alanı × üç kaynak indeksi, boş kaynaklar, boş/0 değerler ve boş hedefler karşılaştırılır.

Tarayıcı kontrolleri 1440 ve 390 pikselde sayfa taşmasını, JavaScript ile kaynak ekleme/kaldırmayı, uzun kesintisiz adları ve dosya adlarını, kapalı geçmişi, 44rem sınırını ve büyük harfe dönüştürme bulunmamasını denetler. Görünen metinler için normal, hover/focus, açık geçmiş ve AJAX hata durumlarında kontrast ≥4,5:1 doğrulanır. AJAX hatasının formun üstündeki konumu da denetlenir.

Tekrarlama: geçici test veritabanını `CIVENSA_TEST_POSTGRES_URL` ile verip `python -m pytest -q --require-postgres tests/test_activity_report_detail_design.py` çalıştırın. Görselleri yeniden üretmek için yalnız bu komuta `CIVENSA_CIV135_SCREENSHOTS=docs/design/rollout/civ-135` ortam değişkenini ekleyin. Sistem Chromium'u kullanılıyorsa `CIVENSA_CHROMIUM_PATH` belirtilebilir. Tam paket komutu: `python -m pytest -q --require-postgres -n 4 --dist loadfile --max-worker-restart=0`.

Çalıştırma sayıları, mevcut akış testlerinin sonuçları ve son commit CI durumu PR açıklamasında yer alır. Görsel doğrulama Chromium ile sınırlıdır; Firefox, Safari ve fiziksel telefon denenmedi. Dağıtım yapılmadı.

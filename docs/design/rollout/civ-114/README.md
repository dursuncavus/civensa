# CIV-114 — Strateji görünümü salt okunur

Gerçek `/department/1?period_id=1` rotası, yerel PostgreSQL 18 ve yalnızca sentetik
`sample` verileri kullanıldı. Chromium; görünüm alanı 1440 × 900 ve 390 × 900,
tam sayfa PNG. Her dosya 1.500.000 bayttan küçük.

| Durum / veri | 1440 | 390 |
| --- | --- | --- |
| Strateji rolü, aktif 2027 dönemi, taslak; göstergeler | [Göstergeler](strategy-indicators-1440.png) | [Göstergeler](strategy-indicators-390.png) |
| Aynı strateji kullanıcısı; faaliyet maliyetleri, işaretli ve devre dışı sözleşme kutusu | [Maliyetler](strategy-activities-1440.png) | [Maliyetler](strategy-activities-390.png) |
| Müdürlük rolü, aktif 2027 dönemi, taslak; göstergeler | [Taslak](department-draft-1440.png) | [Taslak](department-draft-390.png) |

Sentetik Test Belediyesi / Test Müdürlüğü: Hizmet sayısı (Adet), 2027 hedefi
1,75; Test Programı / Test Alt Programı; Ortak faaliyet. Maliyetlerde 2027–2029
bütçe içi 123,45, bütçe dışı 10,05 ve personel/SGK 20,00; eksik geçmiş yıllar
boş bırakıldı. Strateji senaryosunda gösterge açıklaması “Sentetik açıklama”.
Mevcut metinler, işlem bağlantıları ve izin koşulları korunur.

`is-readonly` mevcut koşulla eklenir: müdürlük dışı rol, kapalı dönem veya
`submitted` / `approved` gönderim. Alanlar `--surface-muted` üzerinde `--text`
kullanır (13,50:1); klavye odağı `--focus` ile kesikli dış çizgidir (5,36:1).
Devre dışı onay kutusunun işareti korunur. Sayfa yatay taşmaz; maliyet tablosu
kendi kaydırma bölgesinde kalır.

`tests/test_department_readonly_design.py` gerçek rotada durum matrisini,
yalnızca sarmalayıcı sınıfının değişmesini, her iki genişlikte salt okunur alan
stillerini, kontrastı, klavye odağını ve yatay taşmayı doğrular. Taslak HTML’si
sabit bağlamda önceki şablonla byte düzeyinde; iki sekmedeki bütün kontrollerin
hesaplanan CSS özellikleri önceki stil dosyasıyla birebir karşılaştırılır.
Değişiklik öncesi şablon/CSS referansları SHA-256 ile sabitlenmiştir.

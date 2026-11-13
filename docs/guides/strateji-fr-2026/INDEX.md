# CIV-195 · Strateji FR 2026 · ekran görüntüleri

Yenileme: `python scripts/guide_screenshots.py --strateji-guide`.

Yalnız yerel PostgreSQL 16+ için `CIVENSA_TEST_POSTGRES_URL` kullanılır. Geçici veritabanı koşu sonunda silinir. Canlı veritabanına bağlanılmaz.

Kaynak kod: `8b886d774340eaf9e98f21f74388c79a924cc230`. Chromium: `153.0.8010.12`.
2026 kitap SHA-256: `1aaa0bb81c3cf4e245edaab42452a972b8a59ffc252814216c7628f6dbaf33d6`.

Veri notu: **SENTETİK**. Kurumsal başlık ve hedefler test kitabından; hesaplar, eşleştirmeler, gerçekleşmeler, kanıt, beyan, iade ve onay deneme verisidir. Gerçek kişi adı ve gerçek e-posta adresi yoktur. Parolalar rastgele üretilir, görsellere ve dosyalara yazılmaz.

1440×900 · deviceScaleFactor 1 · tr-TR · Europe/Istanbul · açık tema. Tarih ve kayıt kimlikleri değişebilir; bayt eşitliği beklenmez. Adım listesi sabittir. Her PNG ≤ 1.500.000 bayt; toplam ≤ 30.

| Dosya | Harness adımı | Hesap | URL | Viewport |
| --- | --- | --- | --- | --- |
| [01-giris.png](img/01-giris.png) | Giriş ekranı | strategy | `/login` | 1440×900 |
| [02-moduller.png](img/02-moduller.png) | Hesapla giriş | strategy | `/modules` | 1440×900 |
| [03-kullanici-ekle.png](img/03-kullanici-ekle.png) | Tekil hesap oluşturma | strategy | `/users?period_id=2` | 1440×900 |
| [04-toplu-hesap-hata.png](img/04-toplu-hesap-hata.png) | Toplu CSV önizleme hatası | strategy | `/users?period_id=2` | 1440×900 |
| [05-toplu-hesap-onizleme.png](img/05-toplu-hesap-onizleme.png) | Toplu CSV geçerli önizleme | strategy | `/users?period_id=2` | 1440×900 |
| [06-parola-dosyasi.png](img/06-parola-dosyasi.png) | Toplu hesap oluşturma ve parola dosyası | strategy | `/users?period_id=2` | 1440×900 |
| [07-toplu-pasiflestirme.png](img/07-toplu-pasiflestirme.png) | Hatalı hesap grubunu pasifleştirme | strategy | `/users?period_id=2` | 1440×900 |
| [08-parola-sifirla.png](img/08-parola-sifirla.png) | Parola sıfırlama | strategy | `/users?period_id=2` | 1440×900 |
| [09-faaliyet-eslestirme-kuyrugu.png](img/09-faaliyet-eslestirme-kuyrugu.png) | Faaliyet eşleştirme kuyruğu | strategy | `/activity-mapping?period_id=2` | 1440×900 |
| [10-faaliyet-eslestirme-onizleme.png](img/10-faaliyet-eslestirme-onizleme.png) | Faaliyet eşleştirme CSV önizleme | strategy | `/activity-mapping?period_id=2` | 1440×900 |
| [11-faaliyet-eslestirme-geri-al.png](img/11-faaliyet-eslestirme-geri-al.png) | Faaliyet eşleştirme uygulama ve geri alma | strategy | `/activity-mapping?period_id=2` | 1440×900 |
| [12-onayli-kitaptan-yayinla.png](img/12-onayli-kitaptan-yayinla.png) | 2026 onaylı kitap yayın hazırlığı | strategy | `/report-builder?period_id=2` | 1440×900 |
| [13-yayin-surumleri.png](img/13-yayin-surumleri.png) | Onaylı kitaptan yayınla | strategy | `/report-builder?period_id=2` | 1440×900 |
| [14-gosterge-raporu-olustur.png](img/14-gosterge-raporu-olustur.png) | 2026 gösterge raporu oluşturma | strategy | `/activity-reports` | 1440×900 |
| [15-gosterge-rapor-revizyonu.png](img/15-gosterge-rapor-revizyonu.png) | Yayına bağlı 2026 FR revizyonu oluştur | strategy | `/activity-reports/revisions/1` | 1440×900 |
| [16-yeni-rapor-revizyonu.png](img/16-yeni-rapor-revizyonu.png) | Rapor revizyonu ve dondurma alanı | strategy | `/activity-reports/revisions/1` | 1440×900 |
| [17-ek1-raporlarini-olustur.png](img/17-ek1-raporlarini-olustur.png) | 2026 birim ve idare raporları oluşturma | strategy | `/activity-sections` | 1440×900 |
| [18-tamamlanma-gorunumu.png](img/18-tamamlanma-gorunumu.png) | 2026 EK-1 raporlarını oluştur | strategy | `/activity-sections` | 1440×900 |
| [19-birim-incelemesi.png](img/19-birim-incelemesi.png) | Strateji birim incelemesi | strategy | `/activity-sections/reports/8` | 1440×900 |
| [20-gerekceli-iade.png](img/20-gerekceli-iade.png) | Gerekçeli iade | strategy | `/activity-sections/reports/8` | 1440×900 |
| [21-yeniden-inceleme.png](img/21-yeniden-inceleme.png) | Strateji yeniden inceleme | strategy | `/activity-sections/reports/8` | 1440×900 |
| [22-bagimsiz-birim-onayi.png](img/22-bagimsiz-birim-onayi.png) | Strateji bağımsız birim onayı | strategy | `/activity-sections/reports/8` | 1440×900 |
| [23-disa-aktarma.png](img/23-disa-aktarma.png) | Onaylı Word olarak indir · Fen İşleri Müdürlüğü | strategy | `/activity-sections/reports/8` | 1440×900 |

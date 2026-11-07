# CIV-189 · Müdürlük FR 2026 · ekran görüntüleri

Yenileme: `python scripts/guide_screenshots.py --fr-guide`.

Yalnız yerel PostgreSQL 16+ için `CIVENSA_TEST_POSTGRES_URL` kullanılır. Geçici veritabanı koşu sonunda silinir. Canlı veritabanına bağlanılmaz.

Kaynak kod: `b6692f39344abdf75ffb65b4ba9dd657a543a5b5`. Chromium: `151.0.7922.173`.
2026 kitap SHA-256: `1aaa0bb81c3cf4e245edaab42452a972b8a59ffc252814216c7628f6dbaf33d6`.

Veri notu: **SENTETİK**. Kurumsal başlık ve hedefler test kitabından; hesaplar, gerçekleşmeler, kanıt, beyan, iade ve onay deneme verisidir. Gerçek kişi adı yoktur. Parolalar rastgele üretilir, görsellere ve dosyalara yazılmaz.

1440×900; yalnız giriş ve ilk parola ekranları ayrıca 390×900. deviceScaleFactor 1 · tr-TR · Europe/Istanbul · açık tema. Tarih ve kayıt kimlikleri değişebilir; bayt eşitliği beklenmez. Adım listesi sabittir. Her PNG ≤ 1.500.000 bayt; toplam ≤ 40.

| Dosya | Harness adımı | Hesap | URL | Viewport |
| --- | --- | --- | --- | --- |
| [01-giris.png](img/01-giris.png) | Giriş ekranı | fen_staff | `/login` | 1440×900 |
| [02-giris-mobil.png](img/02-giris-mobil.png) | Kılavuz mobil giriş | fen_staff | `/login` | 390×900 |
| [03-ilk-parola.png](img/03-ilk-parola.png) | Kılavuz ilk parola | fen_staff | `/change-password` | 1440×900 |
| [04-ilk-parola-mobil.png](img/04-ilk-parola-mobil.png) | Kılavuz mobil ilk parola | fen_staff | `/change-password` | 390×900 |
| [05-moduller.png](img/05-moduller.png) | Hesapla giriş | fen_staff | `/modules` | 1440×900 |
| [06-gosterge-raporlari.png](img/06-gosterge-raporlari.png) | Müdürlük 2026 gösterge raporunu bul | fen_staff | `/activity-reports` | 1440×900 |
| [07-gosterge-ozet.png](img/07-gosterge-ozet.png) | 2026 gösterge girişini aç | fen_staff | `/activity-reports/revisions/1` | 1440×900 |
| [08-gerceklesme.png](img/08-gerceklesme.png) | Kılavuz gerçekleşme alanları | fen_staff | `/activity-reports/revisions/1` | 1440×900 |
| [09-kanit.png](img/09-kanit.png) | Kılavuz kanıt alanları | fen_staff | `/activity-reports/revisions/1` | 1440×900 |
| [10-sapma.png](img/10-sapma.png) | Kılavuz sapma açıklaması | fen_staff | `/activity-reports/revisions/1` | 1440×900 |
| [11-birim-raporlari.png](img/11-birim-raporlari.png) | Müdürlük 2026 birim raporunu bul | fen_staff | `/activity-sections` | 1440×900 |
| [12-bolum.png](img/12-bolum.png) | Kılavuz bölüm alanları | fen_staff | `/activity-sections/reports/8?code=OZET` | 1440×900 |
| [13-uygulanamaz.png](img/13-uygulanamaz.png) | Kılavuz uygulanamaz | fen_staff | `/activity-sections/reports/8?code=III.A.3` | 1440×900 |
| [14-ek2.png](img/14-ek2.png) | Harcama yetkilisi güvence beyanı | fen_staff | `/activity-sections/reports/8/assurances/EK-2` | 1440×900 |
| [15-mali-uyarilar.png](img/15-mali-uyarilar.png) | Mali Hizmetler uyarıları | fen_staff | `/activity-sections/reports/8?code=III.A.1` | 1440×900 |
| [16-gonder.png](img/16-gonder.png) | Sapma açıklaması boşken gönderim kontrolü | fen_director | `/activity-sections/reports/8` | 1440×900 |
| [17-gonderim-engeli.png](img/17-gonderim-engeli.png) | Açıklamasız gerçekleşmeyi gönderme denemesi | fen_director | `/activity-sections/reports/8/workflow/submit` | 1440×900 |
| [18-gonderildi.png](img/18-gonderildi.png) | Birim raporunu gönder | fen_director | `/activity-sections/reports/8` | 1440×900 |
| [19-iade.png](img/19-iade.png) | İade notunu gör ve düzelt | fen_staff | `/activity-sections/reports/8?code=III.B.1` | 1440×900 |
| [20-duzeltme.png](img/20-duzeltme.png) | İade notuna göre düzeltmeyi kaydet | fen_staff | `/activity-sections/reports/8?code=III.B.1` | 1440×900 |
| [21-yeniden-gonder.png](img/21-yeniden-gonder.png) | Düzelt ve yeniden gönder | fen_director | `/activity-sections/reports/8` | 1440×900 |
| [22-onayli-indirme.png](img/22-onayli-indirme.png) | Kılavuz onaylı indirme | fen_director | `/activity-sections/reports/8` | 1440×900 |

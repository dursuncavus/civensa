# CIV-054 · Strateji PP kullanım kılavuzu · ekran görüntüleri

Yenileme (depo kökünden):

```sh
python scripts/guide_screenshots.py --out docs/screenshots/guide-pp-v1
```

`CIVENSA_TEST_POSTGRES_URL` yalnızca yerel PostgreSQL 16+ ve CREATE DATABASE yetkili test rolünü göstermelidir. Uygulama bağlantı ayarları girdi olarak okunmaz. Geçici veritabanı başarıda, hatada ve SIGINT/SIGTERM sırasında silinir.

Kaynak: `tests/fixtures/first_load/source/pp2027_print_d3.idml` · SHA-256: `999a43b2c07074191a1e47622c544b9a53813f23d3bb6518e63b29979ca384cb`.
2027 dönemi aktif, şablon doğrulanmış; dry-run ile aynı gerçek servisler, yalnız kaynak tablo 195 hariç. Bu, mevcut prova verisidir; kitap eksikleri düzeltilmez, boş değerler doldurulmaz.

Chromium · 1440×900 · deviceScaleFactor 1 · açık tema · tr-TR · Europe/Istanbul. FULL dışındaki görüntüler viewport çekimidir. PNG sınırı: <1.500.000 bayt.

Yüklenen veri: 33 müdürlük, 264 gösterge, 288 faaliyet.

Başlangıçta doğrulaması temiz: 5 müdürlük. Tam bir paket gerçek gönderim servisiyle gönderildi: **Hukuk İşleri Müdürlüğü** (ID 12); onay/iade yapılmadı.

Veri giriş hesabının müdürlüğü: **Strateji Geliştirme Müdürlüğü** (ID 23); paket taslak bırakıldı.
Strateji Geliştirme Müdürlüğü bulundu ve kitap verisi içeriyor; yedek müdürlük kullanılmadı.

Strateji hesabının teknik müdürlük bağı: **Afet İşleri ve Risk Yönetimi Müdürlüğü**. Aynı müdürlükte iki aktif Müdürü engelleyen uygulama kısıtı nedeniyle veri giriş hesabından farklıdır; rolü strategy, görevi director.

Hesaplar: **strategy** = Strateji Müdürü (test); **department** = Strateji Geliştirme Müdürlüğü (test), görevi director; **anonymous** = oturum kapalı (13, müdürlük kullanıcısının giriş öncesi ekranı). Ek **Gönderim kurulumu (test)** hesabı yalnız gönderim servisinde kullanılır ve tarayıcıdan önce pasifleştirilir. Parola çalışma anında rastgele üretilir; yazdırılmaz veya dosyaya kaydedilmez.

Chromium sürümü: 151.0.7922.173. Kaynak kod: `beff5e36a3263f026f2653db4ab46cad1c08d0fa`. Zaman damgaları her yerel yüklemede yenilenir; görsellerin birebir bayt eşitliği beklenmez.

Tarayıcı başlamadan önce oturumlar gerçek yerel giriş akışıyla açılır. Çekim sırasında yalnız loopback GET istekleri geçer; form/API yazmaları ve dış ağ engellenir. İade ve parola pencereleri Vazgeç ile kapatılır. Gönderimler, olaylar, parola hashleri ve denetim kayıtları çekim öncesi/sonrası karşılaştırılır.

| Dosya | URL yolu | Görünen içerik | Hesap | Çekim | Sonuç |
| --- | --- | --- | --- | --- | --- |
| [01-genel-bakis-ust.png](01-genel-bakis-ust.png) | `/dashboard` | Genel Bakış · üst bölüm | strategy | Viewport | Üretildi |
| [02-ilerleme-panosu.png](02-ilerleme-panosu.png) | `/dashboard` | Müdürlük İlerleme Panosu | strategy | Viewport | Üretildi |
| [03-mudurluk-strateji-gorunumu.png](03-mudurluk-strateji-gorunumu.png) | `/department/12` | Gönderilmiş paketin Strateji inceleme görünümü | strategy | Viewport | Üretildi |
| [04-inceleme-kuyrugu.png](04-inceleme-kuyrugu.png) | `/review` | İnceleme Kuyruğu · Onayla / İade Et | strategy | FULL | Üretildi |
| [05-iade-penceresi.png](05-iade-penceresi.png) | `/review` | İade penceresi · boş gerekçe · ardından Vazgeç | strategy | Viewport | Üretildi |
| [06-faaliyet-eslestirme.png](06-faaliyet-eslestirme.png) | `/activity-mapping` | Faaliyet Eşleştirme · üst bölüm | strategy | Viewport | Üretildi |
| [07-kurum-yapisi.png](07-kurum-yapisi.png) | `/structure` | Kurum Yapısı · üst bölüm | strategy | Viewport | Üretildi |
| [08-kullanicilar.png](08-kullanicilar.png) | `/users` | Kullanıcılar · üst bölüm | strategy | Viewport | Üretildi |
| [09-butce-aktarma.png](09-butce-aktarma.png) | `/budget-reallocations` | Bütçe Aktarma | strategy | FULL | Üretildi |
| [10-sistem-durumu.png](10-sistem-durumu.png) | `/operations` | Sistem Durumu · üst bölüm | strategy | Viewport | Üretildi |
| [11-denetim-gecmisi.png](11-denetim-gecmisi.png) | `/audit` | Denetim Geçmişi · üst bölüm | strategy | Viewport | Üretildi |
| [12-moduller.png](12-moduller.png) | `/modules` | Modüller | strategy | FULL | Üretildi |
| [13-giris.png](13-giris.png) | `/login` | Oturum kapalı giriş ekranı · alanlar boş | anonymous | Viewport | Üretildi |
| [14-veri-girisi-ust.png](14-veri-girisi-ust.png) | `/department/23` | Müdürlük veri girişi · üst bölüm | department | Viewport | Üretildi |
| [15-faaliyet-maliyetleri.png](15-faaliyet-maliyetleri.png) | `/department/23` | Faaliyet Maliyetleri sekmesi · başlık ve maliyet tablosu | department | Viewport | Üretildi |
| [16-gonder-bolumu.png](16-gonder-bolumu.png) | `/department/23` | Müdürlük paketi · Stratejiye Gönder (tıklanmaz) | department | Viewport | Üretildi |
| [17-gonderim-yetkileri.png](17-gonderim-yetkileri.png) | `/submit-authorizations` | Gönderim Yetkileri · üst bölüm | department | Viewport | Üretildi |
| [18-parola-degistir.png](18-parola-degistir.png) | `/submit-authorizations` | Parolamı Değiştir penceresi · alanlar boş · ardından Vazgeç | department | Viewport | Üretildi |

Üretilemeyen: Yok; 18/18 PNG üretildi.

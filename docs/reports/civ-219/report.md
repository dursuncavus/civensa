# CIV-219 — Birim faaliyet raporu tabloları

Müdürlük, birim raporundaki bağlantılardan Tablo 1, 2, 7 ve 8'i açar. Tablo 1 Fiziksel Yapı, Tablo 2 Yönetim Yapısı, Tablo 7–8 Faaliyet ve Proje Bilgileri bölümüne bağlıdır. Her tablo ayrı kaydedilir; boş değer sıfır sayılmaz. TOPLAM ve Toplam Maliyet hesaplanır. Türkçe tutar girişi, sabit personel türleri, kitaptan gelen değiştirilemez faaliyetler, gerekçeli Uygulanmadı ve açık Bu yıl proje yok seçimi kullanılır.

Personel kendi müdürlüğünün taslak/iade raporunu düzenler. Kadın + Erkek tutarsızlığı taslakta uyarılır; eksik hücreler gönderimde tabloya göre gruplanıp ilgili alana bağlanır. Strateji salt okunur inceler, gerekçeyle iade eder veya bağımsız müdür hesabıyla onaylar. Gönderilen/onaylanan tablo ve fotoğraf verileri mevcut sabit rapor kopyasında korunur; konsolidasyon onaylı birimlerden alınır.

Gösterge açıklaması mutlak sapma **en az %10** ise zorunludur; %9,9'da isteğe bağlıdır. Hedef 0 iken sıfırdan farklı gerçekleşme açıklama gerektirir. Alanın yanında sapma yüzdesi gösterilir. JPG/PNG fotoğraflar mevcut kanıt dosyaları gibi veritabanında ve aynı 10 MB yükleme sınırıyla tutulur; rapor sırasıyla numaralanır.

Aşağıdaki görüntüler gerçek uygulama rotalarında, yalnız sentetik 2026 verileriyle Chromium'da üretildi. Tablo 7'nin kapsamı, gösterge raporuna bağlı kitabın müdürlük faaliyet satırlarıdır; Program / Alt Program seçenekleri de bu kitabın müdürlüğe ait sorumluluk ve program satırlarıyla sınırlıdır. Tablo 1 için hiç bina/tesis yoksa boş satır listesi açıkça kaydedilir.

| Görünüm | 1440 px | 390 px |
| --- | --- | --- |
| Tablo 1 | ![Tablo 1, 1440](tablo-1-1440.png) | ![Tablo 1, 390](tablo-1-390.png) |
| Tablo 2 | ![Tablo 2, 1440](tablo-2-1440.png) | ![Tablo 2, 390](tablo-2-390.png) |
| Tablo 7 | ![Tablo 7, 1440](tablo-7-1440.png) | ![Tablo 7, 390](tablo-7-390.png) |
| Tablo 8 | ![Tablo 8, 1440](tablo-8-1440.png) | ![Tablo 8, 390](tablo-8-390.png) |
| Fotoğraflar | ![Fotoğraflar, 1440](photos-1440.png) | ![Fotoğraflar, 390](photos-390.png) |
| Gönderim hatası | ![Gönderim hatası, 1440](submit-errors-1440.png) | ![Gönderim hatası, 390](submit-errors-390.png) |
| Strateji incelemesi | ![Strateji, 1440](strategy-review-1440.png) | ![Strateji, 390](strategy-review-390.png) |

Onaylı sentetik çıktı: [Word](export-synthetic.docx) · [PDF](export-synthetic.pdf). Dört tablo, hesaplanan toplamlar ve fotoğraf listesi/görselleri mevcut rapor yazı tipleri ve stilleriyle dışa aktarılır.

Doğrulama: PostgreSQL 17 üzerinde son odaklı çalıştırmada 102 kabul/regresyon testi geçti; 1440/390 tarayıcı kontrolleri ve gerçek form gönderimleri geçti. Migrasyon ileri/geri/ileri çalıştırıldı; veri varken geri alma ve incelemedeki/onaylı verinin SQL ile değiştirilmesi engellendi. Son depolama/dışa aktarma çalıştırmasında PostgreSQL 18 üzerinde 38 test geçti. Tam paket ve PR CI sonucu PR açıklamasında güncellenir. Canlı veritabanına bağlanılmadı; dağıtım veya birleştirme yapılmadı.

## PR #500 fotoğraf incelemesi — 12 Kasım 2026

Taslak/iade durumunda kendi müdürlüğünün hesabı her fotoğraftaki **Fotoğrafı kaldır** düğmesini kullanabilir. Yeni `c219b1c2d3e4` migrasyonu kaldırma kararını kullanıcı ve zamanıyla ayrı, yalnız ekleme yapılabilen `ar_unit_photo_removals` tablosunda tutar; `unit_photo_remove` içerik olayı da kaydedilir. Asıl fotoğraf ve önceki gönderim/onay manifestleri korunur. Kaldırılan fotoğraf güncel taslak ve onun Word/PDF çıktısından çıkar; eski sabit kopyalar ve önceki onaydan yapılan konsolidasyon fotoğrafı dışa aktarabilir. `c219a1b2c3d4` değiştirilmedi.

Her fotoğrafın açıklamasında Tablo 7 faaliyet kodu/adı ekranda ve Word/PDF'de gösterilir. Eski manifestlerde eksik olan etiket, saklanan manifest değiştirilmeden fotoğrafın özgün kitabından okunur. Güncel kitapta anahtarı bulunmayan fotoğraflar listenin sonunda özgün faaliyet adı ve “Bu fotoğrafın faaliyeti güncel kitapta yok; kaldırın veya yeniden yükleyin.” uyarısıyla kalır. Bu durum `#photos` bağlantılı gönderim engelidir; tabloyu yeniden kaydetmek engeli gizlemez.

Bu düzeltme turunun doğrulaması (yukarıdaki önceki PostgreSQL sonuçlarından ayrıdır):

- Üç bulgunun regresyon testleri düzeltmeden önce başarısız çalıştırıldı. Eski biçimli gönderilmiş manifestin ekrandaki etiketi için ek regresyon da önce başarısız çalıştırıldı.
- CIV-219 tablo/fotoğraf, sapma ve SQLite migrasyon kontrolleri: **54 geçti, 2 kapsam dışında** (tarayıcı ve PostgreSQL SQL koruyucu testi). Geçici, repo dışındaki pytest eklentisi yalnız uygulama testlerindeki PostgreSQL işaretlerini SQLite denemesi için kaldırdı; PostgreSQL doğrulaması yapılmış sayılmaz. Dosyalar: `test_civ219_unit_tables.py`, `test_ar_deviation_gate.py`, `test_civ219_photo_review.py`, `test_civ219_photo_removal_migration.py`. SQLite ileri/geri/ileri geçişi ve kaldırma verisi varken geri alma engeli geçti; tek Alembic head doğrulandı.
- Standart PostgreSQL işaretli odaklı komut da çalıştırıldı: ilk denemede 26 geçti, 42 atlandı, iki migrasyon testi veritabanı yapılandırması olmadığı için kurulum hatası verdi. PostgreSQL 18 ile geçici küme başlatma `shmget: Operation not permitted` hatasıyla engellendi. Tam `--require-postgres` komutu `CIVENSA_TEST_POSTGRES_URL` olmadığı için başlayamadı; PostgreSQL SQL tetikleyicileri ve tam paket doğrulanamadı.
- Daha geniş ilk SQLite denemesinde 65 geçti; mevcut birim iş akışının PostgreSQL'e özgü saat dilimi ve eşzamanlı satır kilidi bekleyen iki testi başarısız oldu. Bu testlerin beklentileri değiştirilmedi.
- Chrome/Playwright başlatma `SIGABRT` ile durdu; bağlı tarayıcı erişimi de “browser access host is unavailable” döndürdü. Bu nedenle 1440/390 fotoğraf PNG'leri yenilenemedi; yukarıdaki görüntüler önceki sürüme aittir. Tarayıcı kabul testi yeni faaliyet etiketi, kaldırma düğmesi ve yeniden açma sonrası gerçek kaldırma akışını kontrol edecek şekilde güncellendi fakat bu tur çalıştırılamadı.
- Farklı model ailesiyle bağımsız inceleme denenirken Claude ve Gemini oturum açma istedi; inceleme tamamlanmadı. PR CI bu yerel değişiklikler için çalıştırılmadı. Push, PR açma, dağıtım ve canlı veritabanı erişimi yapılmadı.

Commit için staging denemesi Git ortak dizinindeki `index.lock` yazımına `Operation not permitted` döndürdü; değişiklikler çalışma ağacında kaldı. İstenen commit başlığı: `CIV-219: fotoğraf kaldırma ve faaliyet bağlarını düzelt`.

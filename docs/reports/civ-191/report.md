# CIV-191 — Müdürlük ekran metinleri

Başlangıç: `feature/authorization-workflow-phase5`, `eacea4f`. Çalışma dalı: `task/civ-191-ekran-metinleri`.

## Metin değişiklikleri

| Ekran / konum | Eski metin | Yeni metin / davranış |
| --- | --- | --- |
| Sol menü ve `/activity-sections` başlığı | Faaliyet Raporu · EK-1 | Rapor bölümleri ve beyanlar (EK-1) |
| `/activity-reports` başlığı | Faaliyet raporları | Gösterge gerçekleşmeleri |
| Tamamlanma listesi ve bölüm editöründe onaysız Word/PDF bağlantıları | Word olarak indir / PDF olarak indir | Taslak — Word (onaysız) / Taslak — PDF (onaysız) |
| Tamamlanma listesi ve malî bölüm editöründe müdürlük kullanıcısına gösterilen Mali Hizmetler uyarıları | … Mali Hizmetler verileri geldiğinde giriş veya XLSX içe aktarma yapın. | Bu bölümü Mali Hizmetler dolduracak; gönderiminizi engellemez. |
| III.B.1 ve III.B.3 gibi yapılandırılmış bölüm açıklamaları | Bu bölümün yapılandırılmış verileri daha sonra eklenecek. Şimdi açıklama, durum ve uygulanabilirlik gerekçesini kaydedebilirsiniz. | Bölüm içeriği alanına açıklamanızı yazın; Durum seçin ve Bölümü kaydet düğmesine basın. Bölüm uygulanmıyorsa Uygulanamaz seçip Uygulanamaz gerekçesi yazın. |

İlk ekran hem birim hem İdare bölümlerini ve güvence beyanlarını listeler; bu nedenle yalnız “Birim” demeyen bir ad seçildi. İkinci ekran arşiv değildir: yayımlanmış PP hedeflerine bağlı gösterge gerçekleşmesi, kanıt ve revizyon girişidir. “Gösterge gerçekleşmeleri” bu işi doğrudan anlatır.

Taslak ayrımı çıktının zaten kullandığı `report.frozen` değerine bağlıdır. Taslak, iade ve henüz onaylanmamış gönderimlerde indirme açık kalır. Onaylı bağlantı adları ve sürüm bağlantıları korunur. Word/PDF üreticilerinde zaten bulunan “TASLAK — onaylanmamış içerik” damgası kullanılır; temiz kapak sonrasındaki sayfalarda görünür. Üreticiler değiştirilmedi.

Mali Hizmetler ayrımı mevcut `activity_sections_service.finance` kontrolü ve mevcut `department` / `strategy` rolleriyle yapılır. Müdürlük kullanıcısına liste ve editörde bilgi metni gösterilir; Mali Hizmetler ve Strateji mevcut eylem metnini görür. Liste üzerinden görülebilen İdare malî satırları da bu sunum ayrımına dahildir. Gönderim kontrolleri ve veri okuma yolları değişmedi.

Düzenleme alanı açıksa yapılabilecek açıklama/durum/gerekçe girişi anlatılır. Salt okunur içerikte kaydedilmiş içeriğin incelenebileceği belirtilir; sahibi Strateji olan düzenlenemeyen bölüm için “Bu bölüm Strateji tarafından doldurulur.” kullanılır.

Kılavuzdaki ekran adları, taslak çıktı açıklaması ve malî bilgi metni güncellendi. Kılavuzun düğme adı testi yeni dört etiketi de zorunlu tutar. CIV-189 görselleri tarihsel olarak korundu; kılavuza güncel görsellerin bu raporda olduğu notu eklendi.

## Önce / sonra ekran kanıtları

Yalnız yerel PostgreSQL 18 üzerinde mevcut test örnekleri ve gerçek uygulama şablonları kullanıldı. Görseller **SENTETİK** 2027 test dönemine aittir; metinler yıla bağlı değildir. Chromium, 1440×900; toplam **8 PNG**. Uygulama istekleri Playwright üzerinden yerel TestClient'a yönlendirildi; canlı uygulama veya veritabanı kullanılmadı. Sonraki dört görüntü görsel olarak incelendi.

| Yer | Önce | Sonra |
| --- | --- | --- |
| Gösterge başlığı ve sol menü | [Önce](before/01-menu.png) | [Sonra](after/01-menu.png) |
| Taslak dışa aktarma | [Önce](before/02-taslak.png) | [Sonra](after/02-taslak.png) |
| Mali Hizmetler bilgisi | [Önce](before/03-mali.png) | [Sonra](after/03-mali.png) |
| III.B.1 bölüm açıklaması | [Önce](before/04-bolum.png) | [Sonra](after/04-bolum.png) |

Yeniden çekim: yerel geçici PostgreSQL için `CIVENSA_TEST_POSTGRES_URL` ve Chromium yolu için `CIVENSA_CHROMIUM_PATH` ayarlanarak:

```sh
CIV191_SCREENSHOTS=docs/reports/civ-191/after .venv/bin/python -m pytest -q --require-postgres tests/test_civ191_screen_texts.py::test_capture_four_places
```

## İdare Word/PDF kâğıt imzaları — yalnız inceleme

**Dört rolü bir araya getiren ayrı bir imza/onay sayfası yok.** Mevcut çıktıların Ekler bölümünde güvence beyanlarına ait imza satırları bulunuyor:

| Rol | Mevcut durum |
| --- | --- |
| Harcama Yetkilisi | EK-2 güvence beyanı ve İmza / Ad-Soyad / Ünvan alanları **birim raporunda** bulunur. İdare Ekler listesinde EK-2 yoktur. |
| Strateji | Ayrı kâğıt imza alanı veya onay sayfası yoktur. Uygulamadaki birim onay geçmişi, imza alanı olarak basılmaz. |
| Başkan Yardımcısı | Ayrı imza alanı veya onay sayfası yoktur. |
| Üst Yönetici | İdare raporunda EK-1 “ÜST YÖNETİCİNİN İÇ KONTROL GÜVENCE BEYANI”; İmza / Ad-Soyad / Ünvan ve yer-tarih bilgileri vardır. |
| Mali Hizmetler | İdare raporunda ayrıca EK-3 “MALÎ HİZMETLER BİRİM YÖNETİCİSİNİN BEYANI” ve imza alanları vardır. |

Kaynaklar: `assurance_service.codes` birim için EK-2, İdare için EK-1/EK-3 seçer. `ar_export._ReportContent.assurances` imza çizgisi, ad ve unvanı basar; `_render_activity_report` bu beyanları ilgili bölümde işler. PDF de aynı içerik üreticisini kullanır. Beyanlar ayrı bir dört-rol onay sayfası olarak düzenlenmez.

Ek olarak, geçici bir salt-okuma testinde sentetik İdare beyanları doldurulup gerçek Word ve PDF uçlarından indirildi. Her iki çıktıda EK-1 ve EK-3 başlıkları, tam iki “İmza: ________________” satırı, EK-2 başlığının ve Başkan Yardımcısı alanının bulunmaması doğrulandı: **1 geçti**. Bu inceleme için ürün veya çıktı şablonu değiştirilmedi. Başkan Yardımcıları / Üst Yönetici kâğıt adımlarını uygulamaya ekleyen bir onay zinciri kurulmadı.

## Doğrulama ve sınırlar

- Regresyon testleri önce mevcut uygulamada çalıştırıldı; müdürlük bilgisi, taslak etiketleri ve bölüm açıklaması beklentileri başarısız oldu. Ardından düzeltmeler uygulandı.
- Yerel PostgreSQL 18 ve Chromium ile `--require-postgres`: `test_civ191_screen_texts.py`, `test_fr_guide_capture.py`, `test_civ188_rehearsal_fixes.py`, `test_activity_sections_export.py`, `test_activity_sections_pdf.py`, `test_assurance_statements.py`, `test_activity_reports_design.py`, `test_section_index_design.py`, `test_section_editor_design.py` çalıştırıldı. Toplam **148 test** kapsandı. İlk geniş koşuda eski dışa aktarma etiketiyle birebir karşılaştırma yapan indeks sözleşmesinde 12 başarısızlık vardı; diğer **136 test geçti**. Sözleşme yalnız kasıtlı iki etiket farkını tanıyacak şekilde güncellendikten sonra indeks dosyasının tamamı yeniden çalıştırıldı: **20 geçti**. Alanlar, bağlantılar ve form bağları için karşılaştırmalar korunur.
- Son ek salt-okunur Strateji bölümü kontrolü ve kılavuz güncellemesinden sonra `test_civ191_screen_texts.py tests/test_fr_guide_capture.py`: **9 geçti**. Müdürlük, Mali Hizmetler ve Strateji görünümü; taslak/onaylı bağlantıları; düzenlenebilir/salt okunur bölüm açıklaması doğrulandı. Mevcut Starlette/httpx kullanımdan kaldırma uyarısı dışında yeni uyarı yoktur.
- Kılavuzun birebir düğme adı testi: **1 geçti**.
- `python -m compileall -q app/activity_sections_routes.py tests/test_civ191_screen_texts.py` ve `git diff --check`: başarılı.
- Yeni bağımlılık, migration, FR/PP rakam okuma yolu veya `app/data/**` değişikliği yoktur. `docs/lead/**`, `AGENTS.md`, `ops/**`, `.github/**` değiştirilmedi.
- Canlı veritabanına bağlanılmadı; birleştirme veya dağıtım yapılmadı. Gerçek hesaplar, gerçek kâğıt imza süreci ve üretim ortamı doğrulanmadı. CI, PR'ın son commit'i üzerinden ayrıca izlenir.

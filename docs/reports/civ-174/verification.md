# CIV-174 — Doğrulama ve sınırlar

Başlangıç: `feature/authorization-workflow-phase5`, `38e5c64`. Canlı veritabanına bağlantı, merge ve deploy yapılmadı. İlk yükleme ve yeni kabul testleri yalnız bu görev için loopback üzerinde açılmış geçici PostgreSQL 16 üzerinde çalıştırıldı. Mevcut testlerin işaretlenmemiş küçük fixture senaryoları SQLite kullanmayı sürdürüyor.

## Kaynak ve değişiklik denetimi

Mevcut `first_load_department` denetim kayıtları yıl, onaylı kitap SHA-256 ve müdürlük/yükleme kimliklerini kalıcı olarak tutuyor. `ImportBatch` uygulama durumu, kaynak yükü, uygulama özeti ve uygulama zamanı da mevcut. Yeni migrasyon veya ilk yükleme mantığı değişikliği gerekmiyor.

Salt okunur uygunluk denetimi, sabit kitap için tam 33 (2026) / 34 (2027) başarılı müdürlük yüklemesi arıyor. İçe aktarmanın kaydettiği `applied_hash`, ilk yükleme hizmetinin sonradan eklediği katalog bağlantıları ve 2026 kapsam satırlarından önce hesaplandığı için bu eklemeler kendi kaynak/denetim kayıtlarıyla ayrı doğrulanıyor. Kullanıcı üyeliği PP içeriği sayılmıyor; hash karşılaştırmasında yükleme öncesindeki üyelik kullanılıyor. Program, alt program, genel bölüm, katalog ve sorumluluklar da denetleniyor. Sonradan kaydedilip geri çevrilen değişiklikler denetim günlüğü üzerinden yayını kapatıyor.

Normal yayın uç noktasının kontrolleri ve 422 metni korunuyor. Yeni yol aynı dönem satırı kilidini, `freeze_program_payload` ve `attach_publication_definitions` işlevlerini kullanıyor. Kontrol hataları ve kontrol uyarıları `kaynak_kitap_uyarilari` içinde check id, sayı ve mesajlarla mühürleniyor; okunabilir arşiv `Veri Arşivi` bağlantısından erişiliyor. Geçmiş satırında toplam sayı ve Onay dayanağı gösteriliyor.

## Varsayımlar ve doğrulanamayanlar

- İlk yükleme denetim kayıtları ve import snapshot'ları güvenilir mevcut kaynak kaydı kabul ediliyor. Bu yol eksik veya uyuşmayan kayıtlardan yeni bir başlangıç özeti üretmiyor.
- Kapsamı belirsiz, müdürlük düzeyindeki sonraki denetim olayları güvenli biçimde bu yolu kapatabilir; normal yayın yolu kullanılabilir.
- Mevcut Faaliyet Raporu revizyon oluşturma yetkisi yalnız Stratejiye ait (`create_report_revision` içindeki `strategy(user)`). Görevdeki “birim kullanıcısı revizyon oluşturur” ifadesi mevcut yetkiyle uyuşmuyor. Yetki değiştirilmedi: testte Strateji revizyonu açıyor; birim kullanıcısı gerçekleşmeleri kaydedip gönderiyor; Strateji onaylıyor; birim Word çıktısı üretiliyor.
- Canlı pilotun yükleme geçmişi ve içeriği incelenmedi; gerçek onay kararının doğruluğu yerel testte kanıtlanamaz. Onay dayanağı, Stratejinin girdiği metindir.
- Normal PP PDF ve gerçek belediye karar belgesinin incelemesi bu görevde çalıştırılmadı.

## Ekran kanıtları

Gerçek HTTP/CSRF işleyicilerine yönlendirilen Chromium; 390×900 ve 1280×900. Görünen yeni işlem, yayın sonrasında gizlenen işlem ve geçmiş satırı doğrulanır. Testler yatay taşmayı da denetler.

- [390: yeni işlem](screenshots/button-390.png)
- [390: yayın geçmişi](screenshots/history-390.png)
- [1280: yeni işlem](screenshots/button-1280.png)
- [1280: yayın geçmişi](screenshots/history-1280.png)

## Çalıştırmalar

Yerel PostgreSQL URL değişkeni ayarlı olarak:

- `python -m tests.civ174_checks`: çıkış 0; 2026 için 63.541, 2027 için 1.750 hata yeniden üretildi. Sıkıştırılmış ayrıntı dosyasının satır sayıları ayrıca doğrulandı.
- `python -m pytest -q --require-postgres tests/test_approved_book_publication.py -x`: **25 geçti**, 221,84 sn. Türkçe uyarı sayısı (66.409), iki yılın mühürlü yayını ve normal 422 metni; yan etkisiz retler; geri çevrilen değişiklikler; gerçekleşme–gönderim–onay–Word akışı.
- `CIVENSA_CHROMIUM_PATH=/usr/bin/chromium python -m pytest -q --require-postgres tests/test_publication_gates.py tests/test_publication_history.py tests/test_first_load_2026.py tests/test_2026_screen_walk.py`: **43 geçti**, 663,15 sn. Mevcut test dosyaları değiştirilmedi.
- `python -m alembic heads`: tek head, `c162a1b2c3d4`.
- `python -m compileall -q app tests/test_approved_book_publication.py tests/civ174_checks.py` ve `git diff --check`: başarılı.
- Yerel tam takım `python -m pytest -q --require-postgres -n 4 --dist loadfile --max-worker-restart=0`: odaklı/ekran çalıştırmalarına kaynak ayırmak için durduruldu; o ana kadar **428 geçti**, 339,48 sn. Tam takımın geçtiği iddia edilmiyor; son commit için CI sonucu PR'da izlenir.
- 2026 onaylı kitap regresyonunda `kaynak_kitap_uyarilari` JSON'u **10.933 bayt**, tüm `Publication.snapshot_json` ise **25.839.532 bayt** ölçüldü. Tam yayın boyutu, onay özeti dışında mühürlenen kitap içeriğini de kapsar.

Chromium 151.0.7922.173 kullanıldı. Standart Playwright tarayıcı indirme alanı ortamın ağ kuralıyla engellendiği için mevcut `/usr/bin/chromium` seçildi. Tarayıcı adaptörü 303 zincirini TestClient içinde çözer; sahte `testserver` adresine dış ağ isteği çıkarmaz. Test kümesinde hız için `fsync`, `full_page_writes` ve `synchronous_commit` kapatıldı; çökme kurtarma/disk dayanıklılığı sınanmadı.

Önceki geliştirme koşularındaki test hazırlığı/yönlendirme hataları düzeltilip yeni dosyanın tamamı yukarıdaki 24 testle yeniden çalıştırıldı. Tek uyarı mevcut Starlette/httpx kullanımının deprecation uyarısıdır.

## Tam CI'da bulunan denetim etiketi

İlk tam CI koşusunun bir parçası 1.908 test geçerken iki hata verdi: yeni `publication_approved_book` olayı için Türkçe etiket eksikti; mevcut `approve-submit` eşzamanlılık testinde ilk okuma 5 saniyede gözlenmedi. Etiket `program_routes.register` içinde kaydedildi; izinli dosya listesi dışına çıkılmadı ve mevcut testler değiştirilmedi. Yerel PostgreSQL 18.6 üzerinde `python -m pytest -q --require-postgres tests/test_audit_display.py tests/test_workflow_concurrency.py`: **13 geçti**, 12,34 sn. Bu PG18 kümesinde fsync/full_page_writes/synchronous_commit varsayılan `on` durumunda kaldı. Tam CI son commit için yeniden izlenir.

CI'da 5 saniyelik beklemede takılan `tests/test_workflow_concurrency.py::test_concurrent_transition_applied_once[approve-submit]` değiştirilmeden beş ayrı pytest sürecinde PostgreSQL 18.6 üzerinde tekrarlandı: **5/5 geçti** (3,98 / 2,86 / 2,71 / 2,91 / 2,68 sn). Bu, ilk CI zamanlama hatasının tekrar üretilemediğini gösterir; önceki başarısız tam CI koşusunu başarılı saymaz.

# CIV-118 · Rapor hazırlığı

Onaylı [CIV-116 prototipi](../civ-116/README.md), gerçek `/program/{department_id}` ekranına uygulandı. Başlangıç: `feature/authorization-workflow-phase5`, `c89516c`. Altı işin bağlantılı özeti ve metinli durumları üstte; 1280 px ve üzerinde sağda yapışkan “Bu sayfada” listesi bulunur. Kart ve faaliyet finansmanı kayıtları kapalı başlar; düzenlenebilir yeni kart ve reddedilmiş POST (`pp_attempt`) mevcut kuralla açık kalır. Ekonomik filtre kompakt araç çubuğundadır; tablolar kendi içinde kayar, mobilde kaydırma ipucu görünür. Salt okunur alanlarda CIV-114 doğrultusunda token zemini, normal metin rengi ve gölgesiz görünüm kullanılır.

## Ekran görüntüleri

Tümü gerçek şablon ve uygulama varlıklarıyla, yalnız sentetik PostgreSQL verisinden üretildi. Chromium 151.0.7922.173; 1440×900 / 390×900, DPR 1, tr-TR, Europe/Istanbul, azaltılmış hareket, yerel Fira Sans. Tam sayfa PNG; her biri ≤ 1.500.000 bayt.

| Durum | 1440 px | 390 px |
| --- | --- | --- |
| Devam ediyor · müdürlük | [1440 PNG · 726.417 bayt](in-progress-1440.png) | [390 PNG · 516.924 bayt](in-progress-390.png) |
| Tamamlandı · müdürlük | [1440 PNG · 679.509 bayt](complete-1440.png) | [390 PNG · 490.364 bayt](complete-390.png) |
| Gönderildi · salt okunur | [1440 PNG · 816.196 bayt](read-only-1440.png) | [390 PNG · 524.733 bayt](read-only-390.png) |
| Strateji · program grubu uyarısı | [1440 PNG · 1.042.575 bayt](strategy-1440.png) | [390 PNG · 649.038 bayt](strategy-390.png) |

## Sözleşme ve durum hesabı

- `tests/fixtures/report_preparation_start.html`, başlangıç şablonunun baytları değiştirilmemiş kopyasıdır. SHA-256: `eff96facc6b8f8c7648978eb468d98b74000d0bceb94c6a0fc506e3c89f5da82`.
- Dondurulmuş karşılaştırma: strateji/müdürlük × düzenlenebilir/salt okunur × iki grup/kaynak filtresi. Her formun alanları ve form ilişkisi, gizli CSRF/dönem değerleri, seçenek metinleri/sırası/seçimleri, textarea içeriği, pasiflik, bağlantı hedefleri ve sorguları, ekonomik form/hata kimlikleri ve kaldırma makrosu çıktısı karşılaştırılır. Yeni on iki bölüm içi bağlantı ayrıca tam olarak sayılır. Yalnız sarmalayıcı, sınıf, sıra ve izin verilen görünür metin farkları dışarıda bırakılır.
- Kart özeti mevcut kart sayısını ve gerekçe/hedef/sorumlu boşluklarını gösterir; tam kart doğrulaması için yeni bir tamamlanma oranı uydurulmaz. Atama sayısı `card_id` boş kayıtlar; katalog sayısı `official_ids` boş faaliyetlerdir.
- Kaynak doğrulaması, mevcut gösterge/faaliyet/personel doğrulama formlarının koşullarını kullanır. Finansmanda zorunlu dönemlerin bütçe içi/dışı/toplam hücrelerinin varlığı, tutarı ve `state` alanı incelenir. Ekonomide mevcut hücrelerin `state`, tutar ve program grubu denetlenir. Sıfır geçerli tutardır; boş tutar sıfır sayılmaz.
- “Tutarlar doğrulandı” ve “Kaynak hücreleri doğrulandı” yalnız bu gözlemlenebilir durumu anlatır. Bağlamda bölüm bazlı sunucu doğrulama sonucu / zorunlu ekonomik hücre kapsamı bulunmadığından bu alanlara genel tamamlanma yüzdesi veya eksik hücre toplamı eklenmedi. Katalog kapsamı ve diğer çapraz kontroller mevcut `errors`/`warnings` listelerinde kalır. İş özeti, gönderim doğrulamasının yerine geçmez.
- “N eksik / tutarsız kayıt”, `errors` listesinin uzunluğudur; aynı liste birer madde olarak gösterilir. Kayıt sayısı ile hata sayısı farklı olsa bile özet/listenin sayısı birebirdir (D-289).
- Rota, servis, veri modeli, API, yetki ve ortak şablonlar değişmedi. Stratejinin başlangıçtaki kaldırma yetkisi de sözleşme gereği korunur; salt okunur kayıt formlarına kaydet düğmesi eklenmez.

## Doğrulama

Yeni `tests/test_report_preparation_design.py`: 24 test geçti. Gerçek oturum / CSRF ile kart ve ekonomik ızgara kaydı, hatalı POST sonrası alanın korunması ve kart/finansman formlarının yeniden açılması 1440 ve 390 px'te doğrulandı. Yerel HTTP köprüsü yalnız geçici TestClient veritabanına gider; tarayıcı yerel POST yönlendirmelerini kendisi izler.

Beş özet senaryosu: kayıt yok, kartsız kayıtlar, doğrulanmamış değerler, tamamlanmış ve gönderilmiş. Dört ekran durumu × iki genişlik: yatay sayfa taşması yok, altı bağlantı hedefe ulaşır, kapalı/açık formlar ve odak/pasif alan metin kontrastı ≥ 4,5:1. 1279/1280 kırılımı da kontrol edilir. Stil dosyası diğer ekranda yüklenmez. `compileall`, `node --check app/static/app.js`, `git diff --check` geçti. Tam takım ve PR başındaki CI sonuçları PR açıklamasında kayıtlıdır.

Tekrar çalıştırma: geçici PostgreSQL 16+ için `CIVENSA_TEST_POSTGRES_URL` tanımlayın. `python -m pytest -q --require-postgres tests/test_report_preparation_design.py`; tüm takım için `python -m pytest -q --require-postgres -n 4 --dist loadfile --max-worker-restart=0`. PNG üretmek için odaklı komuta `CIVENSA_CIV118_SCREENSHOTS=docs/design/rollout/civ-118` eklenir. Gerekirse kurulu Chromium yolu `CIVENSA_CHROMIUM_PATH` ile seçilir. Yeni çalışma zamanı bağımlılığı yoktur; yakalama betiği veya JSON eklenmedi.

Canlı veritabanı, dağıtım ve gerçek belediye kayıtları kullanılmadı. Ortak mutabakat / kaldırma şablonları ve sunucu mesajları kapsam gereği aynen durur. Başlangıç seçenekleri ve mali başlıklar (`Bütçe İçi`, `Bütçe Dışı`, `Haziran Sonu Harcama`, `Yıl Sonu Gerçekleşme Tahmini`, `Personel ve SGK Giderleri`), sunucu/JS metin sözleşmesi nedeniyle korunur. `Program Grubu Dağılımı` bağlantısı `test_programme_split.py` tarafından birebir eşlendiği için korunur. Görünür metin değişikliklerinin tam eski → yeni tablosu PR açıklamasındadır. Mevcut test dosyası değiştirilmedi.

Metin istisnaları: `Performans Kartları` sunucu mesajıyla; `Program / Alt Program` app.js ve `test_live_pilot_hardening.py` / `test_pp_display.py` ile; `Sorumlu İdare`, `Gerekçe ve Açıklamalar`, `Alt Programın Hedefi`, `Verinin Kaynağı` görev dışı `test_word_import.py` ile; `Ekonomik Ad` görev dışı `test_institution_summary.py` / `test_word_import_economic_layouts.py` ile; `Program Grubu` görev dışı `test_first_load_dryrun.py` / `test_first_load_checklist.py` ile eşleştiği için korundu. İlk bölüm başlığı “1. Performans Kartları”dır.

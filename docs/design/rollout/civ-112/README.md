# CIV-112 · 022 Müdürlük ana sayfası görev listesi

Onaylı CIV-108/D-277 tasarımı gerçek `GET /dashboard` müdürlük ekranına taşındı. Üç numaralı görev, `ol[role=list]` içinde aynı müdürlük/dönem veri girişine bağlanır. Ortak açıklama korunur; durum etiketleri bağlantılara `aria-describedby` ile bağlıdır. Gönderim eylemi yoktur. Özet sütunu kaldırıldığı için müdürlük tek sütundur. Stratejinin 1280 px iki sütun düzeni korunur.

## Durum hesabı

Müdürlük bağlamındaki `department_state`, mevcut `department_progress_overview(db, period)` sonucundan seçilir. Yeni sorgu veya ilerleme kuralı yazılmaz. Mevcut fonksiyon önce approved/submitted/returned durumlarını, sonra işlem geçmişini, doğrulama uyarılarını ve hesaplanan ilerlemeyi değerlendirir.

| Mevcut ilerleme durumu | Veri girişi |
| --- | --- |
| not_started | Başlanmadı |
| in_progress, needs_attention, returned | Devam ediyor |
| ready, submitted, approved | Tamamlandı |

Kontrol etiketi: sorunlu gösterge sayısı pozitifse `Düzeltme gerekli · N gösterge`; sıfırsa ve veri girişi tamamlandıysa `Sorun yok`; diğer durumlarda `Bekliyor`. N alan hatası sayısı değil, sorunlu gösterge sayısıdır. Gönderim: draft → Gönderilmedi; submitted → Gönderildi; returned → İade edildi — düzeltip yeniden gönderin; approved → Onaylandı.

## Sentetik veri ve ekran görüntüleri

Veri kaynağı `tests/test_dashboard_design.py::seed_home_state`; yalnız geçici yerel PostgreSQL 18. Temel fixture'ın müdürlük/dönem, rapor kartı, eşleşmiş faaliyet, maliyet ve ekonomik verileri kullanılır. İki sentetik gösterge daha eklenir: toplam 3 gösterge. Kaynak hedef değerleri hazırdır; a durumunda henüz müdürlük düzenleme olayı yoktur. b/e durumunda her üç göstergenin adı ve birimi boştur (6 alan hatası, 3 sorunlu gösterge). Diğer durumlarda gösterge doğrulaması temizdir. a dışındaki durumlarda sentetik `indicator_update` işlem kaydı vardır. c taslak, d submitted, e returned, ek senaryo approved durumundadır.

| Durum | Veri girişi | Kontrol | Gönderim | 1440 px | 390 px |
| --- | --- | --- | --- | --- | --- |
| a · Henüz düzenleme yok | Başlanmadı | Bekliyor | Gönderilmedi | [PNG](022-a-1440.png) | [PNG](022-a-390.png) |
| b · 3 sorunlu gösterge | Devam ediyor | Düzeltme gerekli · 3 gösterge | Gönderilmedi | [PNG](022-b-1440.png) | [PNG](022-b-390.png) |
| d · Gönderildi | Tamamlandı | Sorun yok | Gönderildi | [PNG](022-d-1440.png) | [PNG](022-d-390.png) |
| e · İade, 3 sorunlu gösterge | Devam ediyor | Düzeltme gerekli · 3 gösterge | İade edildi — düzeltip yeniden gönderin | [PNG](022-e-1440.png) | [PNG](022-e-390.png) |

Görüntüler gerçek rotadan oturum açılarak alınır; Playwright ağ yönlendirmesi gerçek TestClient yanıtlarını ve yerel varlıkları tarayıcıya iletir. Şablon bağlamı değiştirilmez. Chromium 151, 1440×900 ve 390×900, DPR 1, tr-TR, Europe/Istanbul, azaltılmış hareket. Her PNG en çok 1.500.000 bayt.

Yeniden üretmek için yerel geçici test veritabanını `CIVENSA_TEST_POSTGRES_URL` ile ayarlayıp `CIVENSA_CAPTURE_CIV112=1 python -m pytest -q --require-postgres tests/test_dashboard_design.py -k test_022_real_task_list_states` çalıştırılır. Sistem Chromium'u gerekiyorsa `CIVENSA_CHROMIUM_PATH` ile seçilir. Yakalama betiği veya JSON kanıt dosyası eklenmez.

## Metin değişiklikleri

- Kaldırılan müdürlük kartları: Gösterge sayısı, Hatası olan gösterge, Gönderim durumu; sayıları ve eski gönderim etiketi.
- `Çalışmaya devam et` → `Bu dönem yapılacaklar`.
- `Veri girişini aç` → `Veri girişi · N gösterge` bağlantısı.
- Yeni bağlantılar: `Civensa kontrolü`, `Gönderim`.
- Yeni durum etiketleri: Başlanmadı; Devam ediyor; Tamamlandı; Düzeltme gerekli · N gösterge; Sorun yok; Bekliyor; Gönderilmedi; Gönderildi; İade edildi — düzeltip yeniden gönderin; Onaylandı.
- Mevcut gönderim öncesi kontrol açıklaması aynen korunur. Strateji metinleri değişmez.

## Test sözleşmesi değişiklikleri

Yalnız kaldırılan müdürlük kartlarına/paneline bağlı beklentiler değiştirilir:

- Eski `Veri girişini aç` bağlantısı ve üç kart etiketi yerine üç görev başlığı/sayısı; diğer kabuk kontrolleri, form bağları ve kancalar korunur.
- Üç tıklanabilir özet kartının hedefi/erişilebilir adı yerine üç görev bağlantısının aynı hedefi ve durum açıklamaları.
- Kartların eşit dolgusu, masaüstünde sağ sütun/kart yükseklikleri ve mobilde 2+1 kart dizilimi yalnız stratejide sürer; müdürlükte özet yokluğu ve tek görev listesi doğrulanır.
- Eski birincil veri giriş düğmesi sayısı ve `.dashboard-issues` için 0/3 renk beklentileri yerine tüm görev durumları ve normal/hover/focus kontrastı doğrulanır.

Kullanıcının onayladığı tek satırlık kapsam istisnası: `tests/test_pp_display.py::test_department_dashboard_status` içindeki `<b>Taslak</b>` kart beklentisi, üçüncü “Gönderim” bağlantısına bağlı `home-send-status` etiketinin draft için “Gönderilmedi” göstermesini doğrulayan beklentiyle değiştirildi. Bu dosyada başka değişiklik yok. İlgili test tek başına PostgreSQL 18 üzerinde geçti (1 test).

Ek testler: a–e ve approved × 1440/390, gerçek rotada ilerleme durumu/sorun sayısı, etiketler, N, hedefler, ol/li, form/düğme yokluğu, yatay taşma, büyük harf dönüşümü, mobil etiket yerleşimi ve JavaScript hataları. Yedi durum için veri girişi eşlemesi ve sıfır sorunlu tamamlanmamış girişte `Bekliyor` ayrıca sınanır. `dashboard_pre_civ112.html` başlangıç dalındaki şablonun değiştirilmemiş kopyasıdır; iki sabit strateji bağlamında UTF-8 HTML baytları karşılaştırılır.

## Doğrulama sonuçları

- PostgreSQL 18, Chromium 151: `python -m pytest -q --require-postgres tests/test_dashboard_design.py -x` — **37 geçti** (94,07 s). a–e ve approved gerçek rota testleri, 1440/390 görünümü ve 021 bayt eşitliği dahil.
- Tarayıcıda çizilen metin renkleri normal/hover/focus durumlarında en az 4,5:1. Etiket çiftleri: nötr 5,87:1; uyarı 5,41:1; başarı 4,71:1. Görev bağlantısı 6,28:1, hover 8,58:1.
- `python -m compileall -q app` ve `git diff --check` geçti.
- Tam PostgreSQL paketi ayrıca çalıştırılıyor; nihai sonuç PR açıklamasında kaydedilir.
- Gerçek kullanıcı kullanılabilirlik testi ve canlı veri doğrulaması bu kapsamda yapılmadı. Çalışma zamanı bağımlılığı eklenmedi.

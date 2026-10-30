# CIV-153 · Program grubu dağılımı

038 ekranı, yalnız sentetik veriler ve geçici yerel PostgreSQL 16 ile doğrulandı.
Başlangıç: `cc0a9a9f635a4c815b9614917bc4e944ab6d5839`.
`tests/fixtures/economic_split_start/economic_split.html`, bu commit'teki şablonun
bayt düzeyinde kopyasıdır; SHA-256:
`b8c0f2a0e5f13550ddf29ba6dea22d4dc3dea15ea96c3297b9b016b69f3fa5d4`.

`before-*` dondurulmuş şablondan, `after-*` yeni şablondan, aynı bağlam ve ortak
sayfa kabuğuyla Chromium'da üretildi. Görünüm alanları 1440×1000 ve 390×1000;
PNG'ler tam sayfadır ve her biri 1,5 MB sınırının altındadır.

| Dosya kalıbı | Durum |
| --- | --- |
| `{before,after}-populated-{1440,390}.png` | Üç program kartı; çoklu kaynak sayfası; pozitif, sıfır ve belirsiz kaynak; kaynak kontrol uyarısı. Girilen pay `12.000.000,00`, kalan `500.000,23`; sıfır hücrede grup seçilmiş. |
| `{before,after}-populated-money-{1440,390}.png` | Aynı dolu formun sağa kaydırılmış tablosu. `after-1440` tüm sütunları kaydırma olmadan gösterir; `after-390` tablo kendi içinde kayar ve ilk sütun da içerikle birlikte kayar. |
| `{before,after}-server-error-{1440,390}.png` | Sunucu hatasıyla yeniden çizilen form: gönderilen paylar, fingerprint, sıfır grubu ve çok satırlı gerekçe korunur. |
| `{before,after}-blocked-{1440,390}.png` | Kapalı dönem / incelemedeki paket uyarısı ve devre dışı alanlar. |

`after-populated-{1440,390}.png` en uzun seçeneği, “Yönetim ve Destek Programı”nı,
seçili gösterir. Sıfır tutar grup seçicisinin tüm seçenekleri her iki genişlikte
canvas ölçümüyle doğrulanır.

Görünür metin değişikliği yoktur. Boş payların `value=""` değerleri ve `0,00`
yer tutucuları korunur; belirsiz kaynak sıfıra çevrilmez.

`tests/test_economic_split_design.py`: 22 kontrol geçti. Dondurulmuş karşılaştırma
form/alan değerlerini, seçenekleri, erişilebilirlik niteliklerini ve JS'nin satır
bağlarını kapsar. Her iki genişlikte önce/sonra gerçek kayıt akışı; hata kutusuna
odak, başarılı yönlendirme ve HTTP 422 sonrası değerlerin korunması doğrulanır.
Yeni tasarımda sayfa yatay taşmaz; 1440 px'de dağılım tablosu kaydırma gerektirmeden
sığar ve ilk satırın Kalan değeri görünür; 390 px'de tablo kendi içinde kayar ve
ilk sütun sabitlenmez. Tablo hücrelerinde sözcükler satır ortasında bölünmez.
Normal, hover, focus
ve disabled metin kontrastı en az 4,5:1; para girişleri sağa hizalı ve tabular,
`12.500.000,00` giriş genişliğine sığar. Açıklama ve gerekçe en çok 44rem'dir.

Tekrar üretim: geçici PostgreSQL için `CIVENSA_TEST_POSTGRES_URL` tanımlandıktan sonra:

```sh
CIVENSA_CIV153_EVIDENCE_DIR=docs/design/rollout/civ-153 \
python -m pytest -q --require-postgres tests/test_economic_split_design.py
```

Sistem Chromium'u kullanılıyorsa `CIVENSA_CHROMIUM_PATH` ayrıca tanımlanabilir.
Canlı veri ve canlı ortam kullanılmadı; kontroller Chromium ile sınırlıdır.

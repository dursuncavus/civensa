# CIV-189 — Müdürlük giriş kılavuzu (sabit bölümler)

## Teslim ve kapsam

2026 Faaliyet Raporu için Personel ve Müdür kılavuzu hazırlandı. Başlangıç dalı `feature/authorization-workflow-phase5`, başlangıç SHA `b385e63c25f62b7543ea167093129abb84398118`. Kılavuz a–j kapsamını ve iki yer tutucuyu içerir. Son giriş tarihi yazılmaz; Strateji duyurur. Faaliyet sonucu girişi (B2) ve gösterge Excel aktarımı (FR5) açıklanmaz.

Kılavuzun başlıklar ve görsel bağlantıları dahil boşlukla ayrılmış kelime sayısı: **854** (sınır 2.500).

Kısa emir cümleleri ve her bölümde tek iş yaklaşımı kullanıldı. Başlamadan önce gereken hesap ve kaynaklar ilk bölümde verildi.

## Çekim ve yeniden üretim

```sh
python scripts/guide_screenshots.py --fr-guide
```

Önkoşul: mevcut `requirements-dev.txt` bağımlılıkları, Chromium ve yalnız yerel PostgreSQL 16+ için `CIVENSA_TEST_POSTGRES_URL`. Bu koşuda PostgreSQL 17 ve sistem Chromium’u (`CIVENSA_CHROMIUM_PATH=/usr/bin/chromium`) kullanıldı. Uygulama bağlantı değişkenleri araç tarafından geçersiz kılınır; geçici veritabanı oluşturulup kapanışta silinir.

Yeni tarayıcı altyapısı yoktur. Mevcut `fr_rehearsal.Rehearsal.walk`, `local_http`, gerçek oturum açma, form kaydetme, gönderme, iade, bağımsız onay ve indirme adımları kullanılır. `--fr-guide` yalnız Fen İşleri örneğini yürütür; diğer prova modlarının çıktı yollarına yazmaz. İlk parola zorunluluğu bu modun sentetik Personel hesabında etkinleştirilir; parola tarayıcıdan gerçekten değiştirilir. Onaylı Word ve PDF ayrıca Müdür hesabından indirilir, dosya başlıkları denetlenir. Görseller dışındaki geçici çekimler ve indirilen dosyalar saklanmaz.

22 PNG vardır: 20 adet 1440×900, giriş ve ilk parola için ayrıca iki adet 390×900. Her dosya 1.500.000 bayt sınırıyla denetlenir. Kılavuz her görsele göreli bağlantı verir. Sabit adım/dosya listesi `tests/test_fr_guide_capture.py` ile karşılaştırılır; zaman damgaları nedeniyle PNG bayt eşitliği beklenmez. Kaynak kod SHA’sı, kitap SHA-256’sı, tarayıcı sürümü, viewport ve **SENTETİK** veri notu [INDEX.md](../../guides/mudurluk-fr-2026/INDEX.md) içindedir.

## Ekran metni bulguları — lead için

- Menüdeki “Faaliyet Raporu · EK-1” ile “Faaliyet raporları” benzer adlar taşıyor. Biri bölüm/beyan, diğeri gösterge girişi içindir. Kılavuz iki yolu ayrı anlatır.
- “açıklama bekliyor” özet sayacıdır; “Veri durumu” listesindeki üç seçenekten biri değildir. Kılavuz bu ayrımı açıklar.
- “Doğrulanmış” kaynak doğrulamasını, “Onaylandı” birim iş akışını anlatır. Kılavuz kaynak doğrulamasının Strateji onayı olmadığını belirtir.
- “Dışa aktar” ve Word/PDF bağlantıları taslakta da görünür. Kılavuz indirmeden önce “Onaylandı” durumunu kontrol ettirir.
- EK-1’de bazı bölümlerde “Bu bölümün yapılandırılmış verileri daha sonra eklenecek” uyarısı vardır (`activity_sections_editor.html`). Bu kılavuz yalnız mevcut metin/durum/gerekçe girişini anlatır.
- B2 faaliyet sonucu girişi ve tam İdare dondurma mevcut provanın kapsam engelleridir. B2 yer tutucu olarak kalır; İdare onayı müdürlük kullanıcısının adımı olarak sunulmaz.
- Tarayıcının yerel dosya seçme denetimi tarayıcı/işletim sistemi diline göre değişebilir. Kılavuz yalnız uygulamanın sabit alan etiketini kullanır.

- Mali Hizmetler uyarısındaki “giriş veya XLSX içe aktarma yapın” ifadesi müdürlük kullanıcısına da görünüyor (15 numaralı görsel). Kılavuz bu bilgilerin Mali Hizmetler tarafından girileceğini belirtir; kullanıcıya bu uyarı üzerinden aktarım adımı verilmez.

Bu bulgular için uygulama metni veya arayüz değiştirilmedi.

## Düğme ve ekran adı denetimi

Kılavuzda ters tırnakla işaretlenen tüm etiketler `app/templates/**` veya uygulama JS dosyalarında birebir aranır. `test_committed_guide_contract` eşleşmeyen etikette başarısız olur. Aşağıda ilk eşleşen kaynak ve satırı yer alır; dinamik başlıkların sabit metni de dahildir.

Birebir doğrulanan benzersiz etiket sayısı: **57**.

| Kılavuz etiketi | Kaynak |
| --- | --- |
| Çalışma alanına giriş | `app/templates/login.html:7` |
| E-posta | `app/static/personal_accounts.js:29` |
| Parola | `app/static/app.js:99` |
| Giriş yap | `app/templates/login.html:15` |
| Kendi parolanızı belirleyin | `app/templates/change_password.html:3` |
| Mevcut geçici parola | `app/templates/change_password.html:10` |
| Yeni parola | `app/templates/base.html:100` |
| Yeni parola tekrar | `app/templates/base.html:103` |
| Parolamı belirle ve devam et | `app/templates/change_password.html:14` |
| Gösterge gerçekleşmelerine gir | `app/templates/modules.html:35` |
| 2026 birim raporunu tamamla · EK-1 ve EK-2 | `app/templates/modules.html:34` |
| Faaliyet raporları | `app/templates/activity_contract_index.html:2` |
| Yeni gerçekleşme gir | `app/templates/activity_contract_detail.html:247` |
| Gerçekleşme (ondalık için virgül kullanın) | `app/templates/activity_contract_detail.html:251` |
| Eksik | `app/static/app.js:309` |
| Veri durumu | `app/templates/activity_contract_detail.html:254` |
| Doğrulanmış | `app/templates/activity_contract_detail.html:62` |
| İncelenmeli | `app/templates/activity_contract_detail.html:62` |
| açıklama bekliyor | `app/templates/activity_contract_detail.html:62` |
| Kanıt kaynağı | `app/templates/activity_evidence_row.html:2` |
| Kaynak adı | `app/templates/activity_evidence_row.html:4` |
| Kaynak konumu / sayfa / kayıt | `app/templates/activity_evidence_row.html:4` |
| Kaynak sürümü / kayıt numarası | `app/templates/activity_evidence_row.html:4` |
| Kanıt dosyası (PDF veya XLSX, en fazla 10 MB) | `app/templates/activity_evidence_row.html:17` |
| Kaynak ekle | `app/templates/activity_contract_detail.html:278` |
| Açıklama / sapma gerekçesi · Gönderim için zorunlu (fark varsa) | `app/templates/activity_contract_detail.html:279` |
| Düzeltici işlem (isteğe bağlı) | `app/templates/activity_contract_detail.html:282` |
| Yeni gerçekleşme revizyonu kaydet | `app/templates/activity_contract_detail.html:285` |
| Faaliyet Raporu · EK-1 | `app/templates/activity_sections_index.html:2` |
| Tamamlanma görünümü | `app/templates/activity_sections_editor.html:52` |
| Yıl | `app/static/app.js:334` |
| Filtrele | `app/templates/activity_sections_index.html:18` |
| Sahibi | `app/templates/activity_sections_index.html:25` |
| Eksikler | `app/templates/activity_financial.html:37` |
| Bölüm içeriği | `app/templates/activity_sections_editor.html:91` |
| Durum | `app/static/design/section-editor.js:29` |
| Hazır | `app/static/design/section-editor.js:19` |
| Bölümü kaydet | `app/templates/activity_sections_editor.html:94` |
| Uygulanamaz | `app/static/design/section-editor.js:19` |
| Uygulanamaz gerekçesi | `app/static/design/section-editor.js:44` |
| Yer | `app/templates/assurance_editor.html:22` |
| Tarih | `app/templates/activity_financial.html:31` |
| Kişi kodu | `app/templates/assurance_editor.html:30` |
| Ad-Soyad | `app/templates/assurance_editor.html:30` |
| Ünvan | `app/templates/assurance_editor.html:30` |
| Başlangıç | `app/templates/activity_sections_editor.html:9` |
| Bitiş | `app/templates/assurance_editor.html:43` |
| Beyan alanlarını kaydet | `app/templates/assurance_editor.html:73` |
| Strateji’ye gönder | `app/templates/ar_unit_workflow.html:13` |
| Gönderildi | `app/templates/dashboard.html:23` |
| İade edildi | `app/templates/dashboard.html:23` |
| Gerekçe: | `app/templates/ar_unit_workflow.html:8` |
| Yeniden gönder | `app/templates/ar_unit_workflow.html:13` |
| Onaylandı | `app/templates/dashboard.html:23` |
| Dışa aktar | `app/templates/activity_sections_editor.html:54` |
| Word olarak indir | `app/templates/activity_sections_editor.html:54` |
| PDF olarak indir | `app/templates/activity_sections_editor.html:54` |

## Doğrulama

- `python scripts/guide_screenshots.py --fr-guide`: **çıkış 0**. 159 prova adımı; 22 kılavuz görseli. İki başarılı koşunun `(adım, hesap, PNG adı)` listeleri birebir karşılaştırıldı; aynı 22 adım yeniden üretildi. Tek birimin onayı tamamlandı. B2 ve diğer birimler/İdare içeriği eksikliği nedeniyle İdare dondurma denemesi, mevcut provanın iki beklenen kapsam engeli olarak kaldı; bunlar kılavuz çekim listesinde değildir.
- Depoya alınan PNG sayısı **22**; en büyük PNG **131207 bayt**. Görsellerden giriş/parola, kanıt, sapma, bölüm düzenleme ve onaylı indirme ekranları görsel olarak incelendi.
- `python -m pytest -q --require-postgres tests/test_fr_guide_capture.py tests/test_fr_rehearsal_harness.py tests/test_civ188_rehearsal_fixes.py`: **13 geçti** (PostgreSQL; son koşu).
- `python -m compileall -q scripts/guide_screenshots.py scripts/fr_rehearsal.py` ve `git diff --check`: başarılı.
- Mevcut Starlette/httpx kullanımdan kaldırma uyarısı sürüyor. Yeni bağımlılık eklenmedi.

Makine kanıtları: [steps.json](steps.json), [run.json](run.json). `run.json` içinde tarayıcı JS hatası, beklenmeyen dış ağ isteği ve sunucu hatası listeleri boştur.

## Harness adımı → görsel

Bu tablo yalnız depoya alınan kılavuz çekimlerini gösterir. Aynı bilgiler [steps.json](steps.json) ve görsel indeksinde bulunur.

| PNG | Harness adımı | Hesap |
| --- | --- | --- |
| [01-giris.png](../../guides/mudurluk-fr-2026/img/01-giris.png) | Giriş ekranı | fen_staff |
| [02-giris-mobil.png](../../guides/mudurluk-fr-2026/img/02-giris-mobil.png) | Kılavuz mobil giriş | fen_staff |
| [03-ilk-parola.png](../../guides/mudurluk-fr-2026/img/03-ilk-parola.png) | Kılavuz ilk parola | fen_staff |
| [04-ilk-parola-mobil.png](../../guides/mudurluk-fr-2026/img/04-ilk-parola-mobil.png) | Kılavuz mobil ilk parola | fen_staff |
| [05-moduller.png](../../guides/mudurluk-fr-2026/img/05-moduller.png) | Hesapla giriş | fen_staff |
| [06-gosterge-raporlari.png](../../guides/mudurluk-fr-2026/img/06-gosterge-raporlari.png) | Müdürlük 2026 gösterge raporunu bul | fen_staff |
| [07-gosterge-ozet.png](../../guides/mudurluk-fr-2026/img/07-gosterge-ozet.png) | 2026 gösterge girişini aç | fen_staff |
| [08-gerceklesme.png](../../guides/mudurluk-fr-2026/img/08-gerceklesme.png) | Kılavuz gerçekleşme alanları | fen_staff |
| [09-kanit.png](../../guides/mudurluk-fr-2026/img/09-kanit.png) | Kılavuz kanıt alanları | fen_staff |
| [10-sapma.png](../../guides/mudurluk-fr-2026/img/10-sapma.png) | Kılavuz sapma açıklaması | fen_staff |
| [11-birim-raporlari.png](../../guides/mudurluk-fr-2026/img/11-birim-raporlari.png) | Müdürlük 2026 birim raporunu bul | fen_staff |
| [12-bolum.png](../../guides/mudurluk-fr-2026/img/12-bolum.png) | Kılavuz bölüm alanları | fen_staff |
| [13-uygulanamaz.png](../../guides/mudurluk-fr-2026/img/13-uygulanamaz.png) | Kılavuz uygulanamaz | fen_staff |
| [14-ek2.png](../../guides/mudurluk-fr-2026/img/14-ek2.png) | Harcama yetkilisi güvence beyanı | fen_staff |
| [15-mali-uyarilar.png](../../guides/mudurluk-fr-2026/img/15-mali-uyarilar.png) | Mali Hizmetler uyarıları | fen_staff |
| [16-gonder.png](../../guides/mudurluk-fr-2026/img/16-gonder.png) | Sapma açıklaması boşken gönderim kontrolü | fen_director |
| [17-gonderim-engeli.png](../../guides/mudurluk-fr-2026/img/17-gonderim-engeli.png) | Açıklamasız gerçekleşmeyi gönderme denemesi | fen_director |
| [18-gonderildi.png](../../guides/mudurluk-fr-2026/img/18-gonderildi.png) | Birim raporunu gönder | fen_director |
| [19-iade.png](../../guides/mudurluk-fr-2026/img/19-iade.png) | İade notunu gör ve düzelt | fen_staff |
| [20-duzeltme.png](../../guides/mudurluk-fr-2026/img/20-duzeltme.png) | İade notuna göre düzeltmeyi kaydet | fen_staff |
| [21-yeniden-gonder.png](../../guides/mudurluk-fr-2026/img/21-yeniden-gonder.png) | Düzelt ve yeniden gönder | fen_director |
| [22-onayli-indirme.png](../../guides/mudurluk-fr-2026/img/22-onayli-indirme.png) | Kılavuz onaylı indirme | fen_director |

## Sınırlar ve varsayımlar

Bu teslim gerçek hesap dağıtımını, gerçek kişisel veriyi, Ali Abi’nin 9 Kasım yanıtlarını veya tüm müdürlüklerin kapanışını doğrulamaz. Destek kanalı Stratejinin duyurusuna bırakıldı. Birleştirme ve dağıtım yapılmadı; canlı veritabanına bağlanılmadı. CI sonucu teslim SHA’sı üzerinden PR’da izlenir.

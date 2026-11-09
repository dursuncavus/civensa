# CIV-199 — Ekran sadeleştirme (Strateji)

Kaynak: 9 Kasım 2026 canlı kullanımında sahibin notları. Yazan: Claude (yerel hat, sahibin Mac'i). Codex incelemesinden sonra birleştirilir.
Kapsam dışı (dokunulmadı): modeller, migration'lar, yayın ve doğrulama mantığı, route URL'leri, docs/lead/**.

## Maddeler

1. **Çift gönderim koruması** (`app/static/app.js`, `app/static/app.css`). Normal POST formları gönderilince düğmeler kilitlenir, basılan düğme “İşleniyor…” olur, formun altına tek satırlık durum yazılır: “İşlem sürüyor, lütfen bekleyin. Sayfayı yenilemeyin ve düğmeye tekrar basmayın.” 20 sn sonra metin “İşlem uzun sürüyor…” uyarısına döner. Aynı forma ikinci gönderim engellenir. Geri/ileri önbellekten dönülürse (pageshow persisted) düğmeler eski hâline gelir. Kendi fetch işleyicisi olan formlar (preventDefault çağıranlar) etkilenmez. `data-no-busy` ve `target` dışı formlar hariç tutulur. Node tabanlı JS testleri için DOM yoksa sessizce atlanır.
2. **Tek kurumda Kurum kutusu** (`activity_contract_index.html`, `activity_sections_index.html`). Tek kurum varsa seçim kutusu yerine kurum adı düz metin + gizli `organization_id` olarak gösterilir; iki ve daha fazla kurumda seçim kutusu aynen kalır.
3. **Nihai Rapor sırası** (`report_builder.html`, `pp_reconciliation.html`, `report-builder.css`). “Onaylı kitaptan yayınla”, “Nihai Sürüm” ve “Yayın sürümleri” basılı kitap düzeltmelerinin hemen altına alındı. Mutabakat tablosu yalnız bu ekranda katlanır: özet satırı “N satırda yayın engeli var · Tabloyu göster (M satır)”, üstünde not: “Bu tablodaki yayın engelleri yalnız “Nihai Sürüm” için geçerlidir. “Onaylı kitaptan yayınla” bu eksikleri yayın arşivine kaynak kitap uyarısı olarak yazar ve yayını durdurmaz.” Program ve Kaynak Karşılaştırma ekranlarındaki aynı tablo değişmedi. Form kurtarma yedeği (`pp_form_fallback.html`) sayfanın sonunda kalır (diğer formlardan sonra olmalı).
4. **Faaliyet Eşleştirme özeti** (`activity_mapping.html`, `activity-mapping.css`). Sayaçların üstüne tek cümle: “X müdürlükte Y faaliyetin alt programı seçilmeli; Z faaliyet için güçlü öneri var. Ayrıca … kart, … resmî katalog bağlantısı eksik; bunlar “Performans Kartlarını Aç” adımıyla tamamlanır.” Alt program tamamsa “Alt program seçimi tamam. …”, hepsi tamamsa “Bütün faaliyetlerin … bağlantıları tamam.” Sayaçlar yerinde, ikincil (küçük, soluk).
5. **EK-1 tamamlanma görünümü** (`activity_sections_routes.py`: `completion_view`, `fold_department_messages`; `activity_sections_index.html`; `section-index.css`). Genel ipucu (“Bölüm içeriğini gözden geçirip…”) tablonun üstünde bir kez; satırlarda yalnız bölüme özgü eksikler, yoksa “Gözden geçirilmeli”. Her raporda özet satırı (bölüm sayısı, durum ve sahip sayıları). Satırlar sahibe göre (Strateji / Mali Hizmetler / Müdürlük) katlanır başlıklarda; tek durumlu ve 3 satırdan uzun gruplar kapalı açılır, başlıkta “N bölümde özel eksik” yazar. Aynı sorun birden çok müdürlükte geçiyorsa tek satır: “N müdürlükte: <sorun>” + “Müdürlükleri göster”. Mali Hizmetler uyarılarındaki tekrar eden genel cümle “bölümü gözden geçirmeli.” olarak kısaltıldı. Bağlantılar, durum etiketleri, filtreler ve “Uyarılar (gönderimi engellemez)” başlığı aynen kalır.
6. **“İşlem tamamlanamadı” ekranı** (`activity_contract_errors.py`, `activity_contract_routes.py`, `activity_contract_error.html`). Kimlik alanları (Kurum, Baz program yayını, rapor/revizyon kimlikleri) düzenlenebilir kutu yerine salt okunur metin + gizli alan; rapor oluşturma ekranında Kurum adı ve “2026 · v1” etiketi gösterilir. Aynı kurum ve yıl için rapor zaten varsa “Mevcut raporu aç: <kurum> · <yıl> · Rapor revizyon N” bağlantısı çıkar, sonuçsuz kalacak “Düzeltilen bilgileri yeniden gönder” formu gösterilmez. Hata metni değişmedi.
7. **Prova betiği** (`scripts/fr_rehearsal.py`). Alembic yükseltmesinden önce boşsa `actual_imports` ve `indicator_directions` tabloları da (checkfirst) bırakılır; CIV-195 tur 2'deki geçici çözümün kalıcı karşılığı.

## Değişen test beklentileri (bilinçli)

- `tests/civ199_contract.py` (yeni): eski dondurulmuş sözleşmelere karşılaştırmadan önce yalnız CIV-199 değişikliklerini geri alan üç yardımcı (CIV-192'deki `without_excel_import` örneği).
- `tests/test_activity_reports_design.py`, `tests/test_section_index_design.py` (2 yer): Kurum (madde 2).
- `tests/test_activity_mapping_design.py`: özet cümlesi (madde 4).
- `tests/test_report_builder_design.py`: kart sırası ve katlanan tablo (madde 3).
- `tests/test_pp_subtotal_reconciliation.py::test_turkish_reconciliation_in_chromium`: tarayıcıda önce katlanan tablo açılır, sonra satırın “Ayrıntı”sı (`details.pp-reconciliation-details`) hedeflenir (madde 3).

Yeni testler: `tests/test_civ199_screen_cleanup.py` (13 test; PostgreSQL ve SQLite yardımcı birimleri).

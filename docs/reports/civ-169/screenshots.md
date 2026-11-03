# CIV-169 ekran kanıtları

Yerel PostgreSQL'de onaylı 2027 + 2026 yüklemesi; gerçek oturum ve CSRF. Görüntüler Playwright'ın mevcut TestClient yönlendirme yöntemini kullanır. Genişlikler 390 ve 1280, yükseklik 900 pikseldir. Yalnız değişen ekran durumları alınmıştır; bütün uygulama taraması değildir.

| Durum | 390 px | 1280 px | Kontrol |
| --- | --- | --- | --- |
| 2026 katalog düzenleme | [Görüntü](screenshots/catalogue-390.png) | [Görüntü](screenshots/catalogue-1280.png) | Ad alanları var; teknik anahtar/kod tekrar girişi yok |
| Faaliyetin katalog seçimi | [Görüntü](screenshots/program-390.png) | [Görüntü](screenshots/program-1280.png) | Resmî faaliyet seçeneklerinde yalnız kitap adları |
| Ekonomik dağılım | [Görüntü](screenshots/economic-split-390.png) | [Görüntü](screenshots/economic-split-1280.png) | Harita ve Planlama başlığı |
| Kullanıcı birim etiketleri | [Görüntü](screenshots/users-390.png) | [Görüntü](screenshots/users-1280.png) | Açılmış müdürlük listesinde 2026 kitap adları |
| Gönderim yetkileri | [Görüntü](screenshots/submit-authorizations-390.png) | [Görüntü](screenshots/submit-authorizations-1280.png) | 2026 kitap adıyla müdürlük başlığı |
| İç Kontrol plan filtresi | [Görüntü](screenshots/ic-plan-390.png) | [Görüntü](screenshots/ic-plan-1280.png) | 2026 sorumlu birim etiketleri |
| İç Kontrol soru katılımcıları | [Görüntü](screenshots/ic-questionnaire-overview-390.png) | [Görüntü](screenshots/ic-questionnaire-overview-1280.png) | Dört dönem adıyla seçim / durum listesi |
| İç Kontrol soru detayı | [Görüntü](screenshots/ic-questionnaire-detail-390.png) | [Görüntü](screenshots/ic-questionnaire-detail-1280.png) | Değiştirilmeyen batch kaydından dönem adıyla başlık |
| Denetim teknik ayrıntısı | [Görüntü](screenshots/audit-390.png) | [Görüntü](screenshots/audit-1280.png) | Açılmış teknik ayrıntıda anahtar yerine “Kod belirtilmedi”; dar ekranda ayrıntı sütununa kaydırılır |

Komut: `python -m pytest -q --require-postgres tests/test_2026_screen_walk.py -k 'catalogue or book_order or changed_screen'`. `CIVENSA_UI_SCREENSHOTS` bu raporun `screenshots` dizinine ayarlanır; `CIVENSA_CHROMIUM_PATH` yerel Chromium'u seçer. Denetim sütunu için aynı fixture ile odaklı ek ekran yürüyüşü yapılır.

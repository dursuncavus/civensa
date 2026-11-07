# Müdürlüklere açılış kontrol listesi — Faaliyet Raporu 2026

Sürüm: v1.0 · 7 Kas 2026 · CV Lider 70 (D-438, D-439) · takvim ve Ocak yayın dondurma **sahip onayladı** (BEYAN 7 Kas 22:46); destek kanalı açık.
Kaynak kararlar: D-351, D-352, D-358, D-361, D-367, D-387, D-431, D-434, D-435, D-436.
Etiketler: DOĞRULANDI (lider kontrol etti) · BEYAN (sahip/Ali söyledi) · BELİRSİZ (bilinmiyor) · ÖNERİ (lider önerisi, onay gerekir).

## Amaç ve kapsam
- "Altyapı tamam" tanımı budur (D-352 sonuç 4): aşağıdaki **A–E** bölümlerinin her satırı "Tamam" olmadan sistem müdürlüklere açılmaz.
- Kapsam: 2026 Faaliyet Raporu müdürlük girişi (D-387 sıra 1). İç Kontrol açılışı ayrı listedir (D-358), burada yok.
- Takvim kısıtı (BEYAN, Ali 2 Kas, D-361 FR3): müdürlükler 2026 verisini 15–20 Ocak 2027'ye kadar girer → sistem 1 Ocak 2027'den önce hazır olmalı.

## Takvim (sahip onayladı, D-439)
| Tarih | Adım |
| --- | --- |
| 9–20 Kas | Ali'nin cevapları (bölüm A) gelir; lider bunları görevlere çevirir. |
| 30 Kas'a kadar | Bölüm A kodu birleşmiş ve canlıda; kullanıcı listesi (B1) elde. |
| 14 Ara (Pzt) haftası | **Pilot açılış**: Bilgi İşlem, Strateji Geliştirme, Fen İşleri (D-361 PR1). Gerçek hesaplar, gerçek 2026 verisi. |
| 21 Ara haftası | Pilot bulguları düzeltilir; kılavuz son hâli. |
| 4 Oca 2027 (Pzt) | **Tüm müdürlüklere açılış** (33 müdürlük, DOĞRULANDI 2026 PP yüklemesi). |
| 15–20 Oca 2027 | Giriş son tarihi (Strateji duyurur). |
| 1–20 Oca | Yayın dondurma: yalnız hata düzeltmesi yayınlanır, mesai dışında. |

Gerekçe: pilot, gerçek kişilerle yolu bir kez dener; tam açılışı tatil öncesine değil yılbaşı sonrası ilk iş gününe koymak, girişi sürenin başına hizalar. Tarihler sahibin ve Ali'nin onayıyla kesinleşir.

## A. İçerik ve özellik hazırlığı
| # | Madde | Sahip | Durum |
| --- | --- | --- | --- |
| A1 | CIV-188 (Mali Hizmetler bölümleri birim gönderimini engellemez) canlıda | Lider → sahip yayını birleştirir | phase5'te birleşti 891f9ee (DOĞRULANDI); bir sonraki yayınla canlı |
| A2 | B2: müdürlük göstergenin yanında faaliyet başına sonuç da girecek mi? | Ali (9 Kas sorusu) | BELİRSİZ; "evet" ise Codex görevi, pilottan önce |
| A3 | Gösterge gerçekleşmelerinin Excel ile toplu girişi (FR5) | Ali bir güncel müdürlük Excel'i gönderir → lider paket → Codex | Örnek bekleniyor |
| A4 | 2026 eşleştirmesi uygulandı, 2026 "Onaylı kitaptan yayınla" ile yayımlandı ("Onay dayanağı" meclis kararı metni) | Ali + Strateji | Bekliyor (D-401/D-406) |
| A5 | Mali Hizmetler bütçe gerçekleşme şablonu (ML1) mevcut mali XLSX içe aktarımla yükleniyor | Ali → Mali Hizmetler örneği | Örnek bekleniyor |
| A6 | Onay sırası (PR2): Başkan Yardımcısı ve Üst Yönetici adımları sistemde mi, kâğıtta mı? | Ali | BELİRSİZ; cevap gelene kadar sistemde: müdür gönderir → Strateji onaylar |
| A7 | Uygulanamaz seçilen Mali Hizmetler bölümüne gerekçe yazılıyor (gerekçesiz hâli birim gönderimini engeller, D-436) | Mali Hizmetler + pilot provada kontrol | İzlenecek |
| A8 | Basılı 2026 kitap tutarsızlıkları (D-375) düzeltilmiş rakamlar | Ali | Bekliyor |
| A9 | Müdürlük ad değişiklikleri "Kurum yapısı" ekranında kayıtlı (D-359) | Ali listesi → lider + sahip | Bekliyor |

## B. Hesaplar ve roller
| # | Madde | Sahip | Durum |
| --- | --- | --- | --- |
| B1 | Kullanıcı listesi: her müdürlük için Ad Soyad, e-posta, görev (Müdür / Personel) | Ali | Bekliyor |
| B2 | Hesaplar toplu CSV ile açılır (sütunlar: Müdürlük ID, Müdürlük, Ad Soyad, E-posta, Görev); hatalı parti geri alınabilir | Strateji (Ali/sahip), lider kontrol eder | Özellik var (DOĞRULANDI app/personal_accounts.py, toplu geri alma) |
| B3 | Her müdürlükte en fazla bir aktif Müdür (uygulama kuralı) | — | DOĞRULANDI (check_director_available) |
| B4 | İlk girişte parola değiştirme zorunlu | — | DOĞRULANDI (must_change_password) |
| B5 | İlk parolalar sohbet/e-posta ile değil, elden veya telefonla iletilir | Strateji | ÖNERİ |
| B6 | Parola unutan kullanıcı: Strateji sıfırlar (sistemde e-posta ile kendi kendine sıfırlama yok) | Strateji | DOĞRULANDI (yalnız Strateji sıfırlar; e-posta gönderimi yok) |
| B7 | Test hesapları canlıda pasif | Lider kontrol eder, sahip uygular | Açılıştan önce |

## C. Prova
| # | Madde | Sahip | Durum |
| --- | --- | --- | --- |
| C1 | Otomatik müdürlük + Strateji provası (sentetik veri) | Codex | 321 OK / 4 BLOCKER (B2 ×3 + İdare dondurma, beklenen) — DOĞRULANDI CIV-188 |
| C2 | A2–A5 sonrası prova yeniden çalışır, yeni BLOCKER yok | Codex görevi | Bekliyor |
| C3 | Pilot hafta: 3 müdürlük gerçek hesapla taslak → gönder → iade → yeniden gönder → onay → Word/PDF | Pilot müdürlükler + Ali | Pilot haftası |
| C4 | Render'da hız ölçümü (H3: provada yavaş adımlar yerel ölçümdü) | Lider | Starter'a geçince |

## D. Altyapı ve güvenlik
| # | Madde | Sahip | Durum |
| --- | --- | --- | --- |
| D1 | Render Free → Starter (7 $/ay) pilot açılış günü (D-351) | Sahip (ödeme) | Pilot günü |
| D2 | Açılıştan hemen önce db-backup çalışır, Neon yedek dalı alınır | Lider tetikler, sahip onaylar | Her açılış öncesi |
| D3 | /health: status ok, migration = head; çalışan commit Render olaylarında doğrulanır | Sahip yapıştırır, lider kontrol eder | Her yayından sonra |
| D4 | Ocak giriş penceresinde yayın dondurma; acil düzeltme mesai dışında | Lider | Onaylandı (D-439) |
| D5 | Geri dönüş yolu: önceki Render yayını + yedek daldan geri yükleme (docs/operations/render.md) | Sahip + lider | Belgeli (DOĞRULANDI) |

## E. Kılavuz ve destek
| # | Madde | Sahip | Durum |
| --- | --- | --- | --- |
| E1 | Müdürlük için kısa giriş kılavuzu (Türkçe, ekran görüntülü: giriş, parola, gösterge + kanıt, EK-1/EK-2, gönderim, iade düzeltmesi) | Lider paket → Codex (prova düzeneğinin ekran görüntüleriyle) | A2–A3 netleşince |
| E2 | Destek kanalı: kim cevaplar, nereden (telefon / e-posta / grup) | Sahip + Ali karar verir | BELİRSİZ |
| E3 | Sorun kaydı: gelen her sorun lider oturumunda kayda geçer, hata ise görev olur | Lider | ÖNERİ |
| E4 | Duyuru: Strateji müdürlüklere tarih, son gün, kılavuz, destek kanalını yazar | Ali | Pilot ve tam açılış öncesi |

## F. Açılış günü sırası (pilot ve tam açılışta aynı)
1. Bölüm A–E'de açık satır yok (lider kontrol eder, bir satırda raporlar).
2. db-backup + Neon yedek dalı (D2).
3. Render Starter (yalnız pilot günü, D1).
4. Yayın phase5 → main, sahip birleştirir (CI yeşil), Render deploy, /health (D3).
5. Hesaplar CSV ile açılır (B2), parolalar elden iletilir (B5).
6. Ali duyuruyu gönderir (E4).
7. İlk gün: lider giriş/gönderim sayılarını ve hata kayıtlarını kontrol eder.

## Sahibin onaylayacağı noktalar
- (onaylandı D-439) Takvim: pilot 14 Ara haftası, tam açılış 4 Oca 2027.
- (onaylandı D-439) Ocak yayın dondurma (D4).
- Açık: destek kanalı (E2), Ali ile birlikte 9 Kas.

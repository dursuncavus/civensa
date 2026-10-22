# CIV-072 — PP-14: onaylı paketi gerekçeyle düzeltmeye açma

Karar: D-157. CIV-070 / birleşmemiş PR #69 tasarımının yerine bu hafif akış uygulanır.
Temel: `feature/authorization-workflow-phase5`, `789f4af`; #66–#68 birleşmiştir.

## Yetki ve önkoşullar

- İşlem: **Onaylı paketi düzeltme için aç**.
- Yalnız etkin Strateji Geliştirme Müdürü, kendi kurumunun paketini açabilir.
- Paket `approved`, dönem kapalı olmamalıdır; taslak ve etkin dönemler kabul edilir.
- Boş/yalnız boşluk gerekçe 422; uygun olmayan paket durumu veya kapalı dönem 409;
  yetkisiz, pasif veya başka kurum hesabı 403 döndürür.
- Standart oturum, CSRF ve açık dönem bağlamı kontrolleri korunur.

## HTTP ve işlem bütünlüğü

`POST /api/submissions/{id}/reopen?period_id=…`, JSON: `{"reason":"…"}`.
İnceleme ekranı aynı işlemi `/review/submissions/{id}/reopen` HTML formuyla çağırır.

1. İstek gövdesi kilitlerden önce okunur; gerekçe metin olmalı ve kırpılarak saklanır.
2. Önkoşullar kontrol edilir; müdürlük satırı, ardından teslim satırı `FOR UPDATE`
   kilitlenir. Kilit beklemesinden sonra durum, dönem ve yetki tekrar okunur.
3. Onaylı içerik mevcut `department_snapshot` ile kaydedilir; durum `returned`,
   `return_note` gerekçe olur. Açma işlemi revizyon artırmaz.
4. `SubmissionEvent(event_type="reopen")`, gerekçeli müdürlük bildirimi ve
   `AuditLog(action="submission_reopen")` aynı işlemde yazılır; tek commit yapılır.
5. Hata bütün işlemi geri alır. Eşzamanlı iki açma yalnız bir olay üretir.

Yeni tablo veya migration yoktur; olay türü mevcut metin sütununa sığar.
Hatalar `app/pp_errors.py` sözleşmesiyle Türkçe alan mesajları döndürür.
İnceleme Kuyruğunda onaylı/açık dönem paketinde yetkili Müdüre gerekçe alanı ve
işlem düğmesi görünür; hata aynı formda kalır.

## Düzeltme, bağımsız onay ve yayın

- Müdürlük mevcut ekrandan düzeltir, yeniden gönderir; revizyon bir artar.
- Strateji mevcut iade/onay yolunu kullanır; doğrulamalar değişmez.
- Bağımsız onay kontrolünde en son `return` **veya** `reopen` sınırdır.
  Bu sınırdan sonra veriyi oluşturan/değiştiren kullanıcı aynı revizyonu onaylayamaz.
- Açılmış zorunlu paket yayını engeller. Yeniden onaydan sonra mevcut yayın yolu
  `max(version)+1` üretir; eski yayın sürümü, snapshot ve hash değişmez.
- Faaliyet Raporu referansları taşınmaz; mevcut hedefleri korunur.
- Önceden verilmiş bütçe aktarma önizlemesi açmadan sonra uygulanamaz;
  mevcut durum/parmak izi kontrolleri bunu sağlar. Bütçe servisi değiştirilmez.

## Ertelenenler

CIV-070 ağır tasarımından bu kapsamda uygulanmayanlar:

- Ayrı düzeltme talebi/durum makinesi, yalıtılmış çalışma kopyası ve alan izin listeleri.
- Değişmez deneme zincirleri, alan farkları, düzeltme hash'leri ve idempotency anahtarları.
- Çalışma kopyasının yayın anında atomik kurulması, düzeltme manifesti ve soy zinciri.
- Yayın ardıllığı etiketleri, aday hash'ine bağlı kontrol listesi ve iş sahibi onayı.
- Yeni tablolar, migration, DB rol/trigger korumaları ve ortak rezervasyon kilitleri.
- Kapalı dönem düzeltme penceresi, dönem kopyalama/aktivasyon koordinasyonu,
  çapraz servis rezervasyonları ve aşağı akış etki uyarıları.

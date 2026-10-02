# Civensa v4.0.0

## İş akışı ve bildirimler

- Her müdürlük gönderimi revizyon numarası alır.
- Gönderim, gerekçeli iade, yeniden gönderim ve onay kararları değiştirilemez bir zaman çizelgesinde saklanır.
- Strateji yeni gönderimleri; müdürlükler iade ve onay kararlarını uygulama içi bildirim olarak görür.
- Bildirim erişimi rol ve müdürlük sınırlarıyla korunur.
- İnceleme kuyruğu son işlemi, revizyonu ve iade gerekçesini gösterir.

## Güvenlik ve operasyon

- Aynı paket incelemedeyken yinelenen gönderim engellenir.
- Onay işlemi kullanıcıdan açık teyit ister.
- Çıkış formu CSRF doğrulamasına uygun hale getirildi.
- Operasyon API'si iş akışı olayı ve okunmamış bildirim sayılarını raporlar.
- Release-readiness kapısı yeni iş akışı tablolarını ve migration başını doğrular.

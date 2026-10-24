# Ekranlar arası gezinme

Düğümler URL kalıplarını temsil eder; rol, sekme, bölüm ve onay durumları INDEX içindeki ayrı görsellere ayrılmıştır. Düz oklar DOM bağlantılarıdır. Ortak sol menü her ekranda tekrar çizilmez: rol menüsü düğümünden erişilir. Kesik oklar aynı ekran içindeki pencere/sekme veya POST sonrası dönüşü gösterir; düğme ve form eylemlerinin tam URL’leri INDEX tablolarındadır. Dosya indirmeleri ekran değildir.

```mermaid
flowchart LR
  strategy_menu["Strateji ortak sol menüsü"]
  department_menu["Müdürlük ortak sol menüsü"]
  subgraph m1["Performans Programı"]
    n3["Genel Bakış<br/>/dashboard"]
    n4["Müdürlük veri girişi<br/>/department/{department_id}"]
    n5["PP Kaynak Karşılaştırması<br/>/source-comparison"]
    n6["Rapor Hazırlığı<br/>/program/{department_id}"]
    n7["Ekonomik dağılım<br/>/program/{department_id}/economic-split"]
    n8["Nihai Rapor<br/>/report-builder"]
    n9["Tamamlanma listesi<br/>/report-builder/manifest"]
    n10["Genel bölüm içe aktarma<br/>/report-builder/import/{batch_id}"]
    n11["Faaliyet Eşleştirme<br/>/activity-mapping"]
    n12["İnceleme Kuyruğu<br/>/review"]
    n13["Bütçe Aktarma<br/>/budget-reallocations"]
    n14["Yeni Bütçe Aktarması<br/>/budget-reallocations/new"]
    n15["Bütçe aktarma ayrıntısı<br/>/budget-reallocations/{operation_id}"]
  end
  subgraph m2["Faaliyet Raporu"]
    n16["Faaliyet Raporu hazırlık alanı<br/>/activity-report"]
    n17["Yayına bağlı Faaliyet Raporları<br/>/activity-reports"]
    n18["Gerçekleşme revizyonu<br/>/activity-reports/revisions/{revision_id}"]
    n19["Gösterge kimlik eşlemesi<br/>/activity-reports/publications/{publication_id}/bindings"]
    n20["Faaliyet Raporu · EK-1<br/>/activity-sections"]
    n21["EK-1 bölüm editörü<br/>/activity-sections/reports/{document_id}"]
    n22["Malî içe aktarma önizlemesi<br/>/activity-sections/reports/{document_id}/financial/imports/{import_id}"]
    n23["Güvence beyanı<br/>/activity-sections/reports/{document_id}/assurances/{code}"]
  end
  subgraph m3["İç Kontrol"]
    n24["İç Kontrol planları<br/>/internal-control"]
    n25["İç Kontrol yükleme kontrolü<br/>/internal-control/imports/{batch_id}"]
    n26["İç Kontrol plan kataloğu<br/>/internal-control/plans/{plan_id}"]
    n27["İç Kontrol Eylemlerimiz<br/>/internal-control/our-actions"]
    n28["İç Kontrol izleme<br/>/internal-control/monitoring"]
    n29["İç Kontrol izleme paketi<br/>/internal-control/monitoring/batches/{batch_id}"]
  end
  subgraph m4["Yönetim"]
    n1["Giriş<br/>/login"]
    n2["Modüller<br/>/modules"]
    n30["Kurum Yapısı<br/>/structure"]
    n31["Kullanıcılar<br/>/users"]
    n32["Gönderim Yetkileri<br/>/submit-authorizations"]
    n33["Parola değiştir<br/>/change-password"]
    n34["Sistem Durumu<br/>/operations"]
    n35["Denetim Geçmişi<br/>/audit"]
  end
  strategy_menu --> n11
  strategy_menu --> n20
  strategy_menu --> n35
  strategy_menu --> n13
  strategy_menu --> n3
  strategy_menu --> n24
  strategy_menu --> n2
  strategy_menu --> n34
  strategy_menu --> n8
  strategy_menu --> n12
  strategy_menu --> n5
  strategy_menu --> n30
  strategy_menu --> n31
  department_menu --> n20
  department_menu --> n3
  department_menu --> n4
  department_menu --> n27
  department_menu --> n2
  department_menu --> n5
  department_menu --> n32
  n11 --> n4
  n11 --> n6
  n16 --> n17
  n16 --> n2
  n17 --> n16
  n17 --> n19
  n17 --> n18
  n19 --> n17
  n18 --> n17
  n20 --> n21
  n21 --> n17
  n21 --> n18
  n21 --> n20
  n21 --> n23
  n21 --> n22
  n23 --> n21
  n22 --> n21
  n13 --> n14
  n13 --> n15
  n15 --> n13
  n3 --> n11
  n3 --> n4
  n3 --> n10
  n3 --> n9
  n3 --> n12
  n3 --> n31
  n4 --> n6
  n24 --> n28
  n24 --> n26
  n25 --> n24
  n25 --> n26
  n28 --> n29
  n29 --> n28
  n29 --> n27
  n27 --> n29
  n26 --> n24
  n2 --> n16
  n2 --> n17
  n2 --> n3
  n2 --> n24
  n34 --> n11
  n6 --> n4
  n6 --> n7
  n7 --> n6
  n8 --> n6
  n8 --> n9
  n10 --> n3
  n10 --> n9
  n9 --> n11
  n9 --> n3
  n9 --> n4
  n9 --> n6
  n9 --> n8
  n12 --> n4
  n5 --> n3
  n1 -. "POST giriş" .-> n2
  n2 -. "role göre ortak menü" .-> strategy_menu
  n2 -. "role göre ortak menü" .-> department_menu
  n14 -. "önizleme + uygulama" .-> n15
  n24 -. "plan yükle" .-> n25
  n25 -. "planı kaydet" .-> n26
  n17 -. "revizyon oluştur" .-> n18
```

Ortak menülerde **Parolamı Değiştir** aynı ekranın penceresini açar; **Çıkış** POST `/logout` sonrası `/login` ekranına döner. Bildirimler GET `/api/notifications` ile aynı ekranda panel açar; okunmamış bir bildirime geçiş POST `/api/notifications/{id}/read` sonrasında bildirimin bağlantısını açar. Müdürlük veri girişinin Gösterge / Faaliyet sekmeleri aynı URL içinde kalır.

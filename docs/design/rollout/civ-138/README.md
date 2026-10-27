# CIV-138 · Okunur denetim ve aktarma listesi

016 denetim geçmişinde işlem ve varlık kodları Türkçe gösterilir; ayrıntı alanında bilinen anahtarlar kısa metne çevrilir, çevrilemeyen içerik kapalı “Teknik ayrıntı” bölümünde kalır. CSV dışa aktarımı izlenebilirlik için ham değerleri korur. 017 listesi, işlem satırlarından müdürlük ve tutar özetleri üretir; telafi bağlantısı aynı hedefe gider ancak dayanak bilgisiyle gösterilir.

## Ekran kanıtları

Tam sayfa Chromium görüntüleri, sentetik kayıtlar ve 1050 px pencere yüksekliğiyle alındı. 016’da aynı kullanıcıya ait farklı işlem türleri, bilinen ayrıntılar ve kapalı teknik ayrıntı bulunur. 017’de iki müdürlüklü ve dört müdürlüklü işlem ile telafi satırı bulunur. Her PNG 1,5 MB veya daha küçüktür.

| Ekran | Önce 1440 | Sonra 1440 | Önce 390 | Sonra 390 |
| --- | --- | --- | --- | --- |
| 016 · Filtrelenmiş geçmiş | [PNG](before-filtered-1440.png) | [PNG](after-filtered-1440.png) | [PNG](before-filtered-390.png) | [PNG](after-filtered-390.png) |
| 017 · Kayıtlı işlemler | [PNG](before-017-rows-1440.png) | [PNG](after-017-rows-1440.png) | [PNG](before-017-rows-390.png) | [PNG](after-017-rows-390.png) |

## İşlem etiketleri

| Ham işlem kodu | Görünen etiket |
| --- | --- |
| `activity_contract_bound` | Faaliyet sözleşme durumu güncellendi |
| `activity_create` | Faaliyet oluşturuldu |
| `activity_delete` | Faaliyet silindi |
| `activity_evidence_access` | Faaliyet kanıtına erişildi |
| `activity_evidence_download` | Faaliyet kanıtı indirildi |
| `activity_evidence_upload` | Faaliyet kanıtı yüklendi |
| `activity_mapping` | Faaliyet alt programa bağlandı |
| `activity_mapping_csv` | Faaliyet eşleştirmesi aktarıldı |
| `activity_mapping_csv_revert` | Faaliyet eşleştirme aktarımı geri alındı |
| `activity_report_approve` | Faaliyet raporu onaylandı |
| `activity_report_revision` | Faaliyet raporu revizyonu oluşturuldu |
| `activity_source_total_decision` | Faaliyet kaynak toplamı kararı kaydedildi |
| `activity_update` | Faaliyet güncellendi |
| `actual_revision_create` | Gerçekleşme revizyonu kaydedildi |
| `budget_reallocation` | Bütçe aktarıldı |
| `card_assign` | Performans kaydı karta atandı |
| `card_remove` | Performans kartı kaldırıldı |
| `card_save` | Performans kartı kaydedildi |
| `catalogue_create` | Resmî faaliyet oluşturuldu |
| `catalogue_link` | Faaliyet resmî katalogla ilişkilendirildi |
| `data_import_apply` | Veri aktarımı uygulandı |
| `data_import_preview` | Veri aktarımı önizlemesi oluşturuldu |
| `data_import_revert` | Veri aktarımı geri alındı |
| `department_active` | Müdürlük durumu güncellendi |
| `department_create` | Müdürlük oluşturuldu |
| `department_export_docx` | Müdürlük raporu indirildi |
| `department_rename` | Müdürlük adı güncellendi |
| `department_submit` | Müdürlük verileri incelemeye gönderildi |
| `economic_grid_save` | Ekonomik değerler kaydedildi |
| `economic_programme_split` | Ekonomik değerler programa dağıtıldı |
| `economic_save` | Ekonomik değer kaydedildi |
| `finance_save` | Faaliyet bütçesi kaydedildi |
| `import_source_conflict_decision` | Aktarım kaynağı çakışması karara bağlandı |
| `indicator_create` | Gösterge oluşturuldu |
| `indicator_remove` | Gösterge kaldırıldı |
| `indicator_update` | Gösterge güncellendi |
| `login` | Giriş yapıldı |
| `login_throttle_lock` | Giriş denemeleri geçici olarak durduruldu |
| `operations_backup_export` | Veritabanı yedeği indirildi |
| `period_activate` | Raporlama dönemi etkinleştirildi |
| `period_create` | Raporlama dönemi oluşturuldu |
| `period_indicator_identity` | Gösterge dönemler arasında ilişkilendirildi |
| `personnel_cost_update` | Personel gideri güncellendi |
| `pp_data_change` | Performans programı verisi değiştirildi |
| `program_create` | Program oluşturuldu |
| `program_update` | Program güncellendi |
| `publication_freeze` | Yayın sürümü oluşturuldu |
| `publication_indicator_bind` | Yayın göstergesi ilişkilendirildi |
| `release_manual_confirmation` | Yayın teyidi kaydedildi |
| `scope_save` | Müdürlük kapsamı kaydedildi |
| `section_period_copy` | Rapor bölümleri döneme kopyalandı |
| `section_save` | Rapor bölümü kaydedildi |
| `self_password_change` | Parola değiştirildi |
| `source_money_verified` | Kaynak tutar doğrulandı |
| `source_value_verified` | Kaynak gösterge değeri doğrulandı |
| `structure_cancel` | Yapı kararı iptal edildi |
| `structure_change` | Müdürlük yapısı değiştirildi |
| `structure_department` | Yapı kararındaki müdürlük güncellendi |
| `structure_department_cancel` | Müdürlük değişikliği iptal edildi |
| `structure_link` | Yapı kararı bağlantısı kaydedildi |
| `structure_period_copy` | Müdürlük yapısı döneme kopyalandı |
| `structure_profile` | Müdürlük dönem bilgisi güncellendi |
| `structure_profile_cancel` | Müdürlük dönem bilgisi iptal edildi |
| `structure_scope_save` | Müdürlük kapsamı kaydedildi |
| `structure_transfer` | Yapı kararı aktarımı kaydedildi |
| `submission_approve` | Müdürlük verileri onaylandı |
| `submission_reopen` | Müdürlük verileri yeniden açıldı |
| `submission_return` | Müdürlük verileri düzeltme için iade edildi |
| `subprogram_create` | Alt program oluşturuldu |
| `subprogram_responsibilities` | Alt program sorumlulukları güncellendi |
| `subprogram_update` | Alt program güncellendi |
| `template_upload` | Rapor şablonu yüklendi |
| `template_verify` | Rapor şablonu doğrulandı |
| `user_activate` | Kullanıcı etkinleştirildi |
| `user_bulk_create` | Kullanıcı aktarımı tamamlandı |
| `user_bulk_create_item` | Kullanıcı oluşturuldu |
| `user_bulk_create_revert` | Kullanıcı aktarımı geri alındı |
| `user_can_submit_change` | Gönderim yetkisi güncellendi |
| `user_create` | Kullanıcı oluşturuldu |
| `user_deactivate` | Kullanıcı devre dışı bırakıldı |
| `user_is_active_change` | Kullanıcı durumu güncellendi |
| `user_password_reset` | Kullanıcı parolası sıfırlandı |
| `user_position_change` | Kullanıcı unvanı güncellendi |

## Varlık etiketleri

| Ham varlık kodu | Görünen etiket |
| --- | --- |
| `activities` | Faaliyet |
| `activity` | Faaliyet |
| `activity_cost_values` | Faaliyet bütçesi |
| `activity_evidence_file` | Faaliyet kanıtı |
| `activity_report_approval` | Faaliyet raporu onayı |
| `activity_report_revision` | Faaliyet raporu revizyonu |
| `actual_revision` | Gerçekleşme revizyonu |
| `budget_operation` | Bütçe aktarması |
| `database` | Veritabanı |
| `department` | Müdürlük |
| `department_cost_values` | Müdürlük gideri |
| `department_scopes` | Müdürlük kapsamı |
| `departments` | Müdürlük |
| `economic_values` | Ekonomik değer |
| `import_batch` | Veri aktarımı |
| `indicator` | Gösterge |
| `indicator_value` | Gösterge değeri |
| `indicators` | Gösterge |
| `login_throttle` | Giriş denetimi |
| `mapping_batch` | Faaliyet eşleştirme aktarımı |
| `official_activities` | Resmî faaliyet |
| `official_activity` | Resmî faaliyet |
| `programs` | Program |
| `publication` | Yayın |
| `publication_indicator_binding` | Yayın gösterge bağlantısı |
| `publications` | Yayın |
| `release_confirmation` | Yayın teyidi |
| `report_card` | Performans kartı |
| `report_cards` | Performans kartı |
| `report_section` | Rapor bölümü |
| `report_sections` | Rapor bölümü |
| `reporting_period` | Raporlama dönemi |
| `reporting_periods` | Raporlama dönemi |
| `structure_change` | Yapı kararı |
| `structure_change_cancellations` | Yapı kararı iptali |
| `structure_change_links` | Yapı kararı bağlantısı |
| `structure_change_transfers` | Yapı kararı aktarımı |
| `structure_changes` | Yapı kararı |
| `submission` | Müdürlük gönderimi |
| `subprogram` | Alt program |
| `subprograms` | Alt program |
| `template_snapshot` | Rapor şablonu |
| `template_snapshots` | Rapor şablonu |
| `user` | Kullanıcı |
| `user_batch` | Kullanıcı aktarımı |
| `users` | Kullanıcı |

Etiketlenmeyen yeni işlem/varlık kodları sırasıyla “Diğer işlem” ve “Diğer kayıt” olarak gösterilir; ham kod kapalı teknik ayrıntıda kalır. Ayrıntı özetleri `revision`, `role`, `count`, `subprogram_id`, `department_id`, `period_id` ve `bytes` alanlarını tanır. Bilinmeyen alanlar ham metin olarak kapalı teknik ayrıntıda saklanır.

## Kapsam dışı ekranlar · ham kod / iç numara bulguları

Bu dosyalar yalnızca tespit için listelenmiştir; başka açık PR'lar tarafından düzenlendiği için bu PR'da değiştirilmemiştir.

| Dosya ve satır | Görünen örnek |
| --- | --- |
| `app/templates/operations.html:72,108,130` | Kontrol kimliği (`item.id`) etiketin yanında; geçmiş kaydında `#{{ event.id }} · {{ event.item_id }}` |
| `app/templates/structure.html:33,76,155` | Müdürlük `#{{ d.id }}` ve `Program #{{ p.id }}` |
| `app/templates/structure_wizard.html:58,72,97,99,137,148,158,167,170,175` | Müdürlük, faaliyet, gösterge, yapı kararı, devralan ve kaydeden kimlikleri `#<id>` biçiminde |
| `app/templates/activity_mapping.html:27` | CSV geçmişinde `İşlem {{ batch.id }}` |
| `app/templates/source_comparison.html:64` | Ayrıntı açılır alanında `İçe aktarma {{ row.batch_id }}` |
| `app/templates/budget_detail.html:2,8,9,12,17` | İşlem, yetki devri, müdürlük, faaliyet ve telafi kimlikleri; ayrıntıda ekonomik kategori kodları |

018 ve bütçe aktarma ayrıntı ekranı (`budget_detail.html`) bu işin kapsamı dışındadır. Bu bulgular için ayrıca ekran işi gerekir.

## Doğrulama

```sh
python -m pytest -q --require-postgres tests/test_audit_display.py tests/test_audit_design.py tests/test_budget_reallocation_design.py
```

PostgreSQL 16+ ve Chromium ile denendi. Testler kod kapsamını, ham CSV çıktısını, maskeleme sırasını, mevcut/silinmiş varlığı, büyüyen satır sayısında sabit sorgu sayısını, filtre değerlerini, 2/4 müdürlüklü liste metnini, bağlantıları, 1440/390 görünümünü ve kontrastı doğrular. Firefox/Safari ve farklı ekran okuyucular doğrulanmadı. Canlı veri kullanılmadı.

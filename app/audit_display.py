"""Turkish presentation labels for the audit history."""
import json
from collections import defaultdict
from decimal import Decimal, InvalidOperation

from sqlalchemy import select

from .budget_models import BudgetOperation
from .models import (
    Activity, ActivityCostValue, ActivityReportApproval, ActivityReportRevision, ActualRevision,
    ActivityEvidenceFile, Department, DepartmentCostValue, DepartmentScope, EconomicValue,
    ImportBatch, Indicator, IndicatorValue, OfficialActivity, Program, Publication,
    PublicationIndicatorBinding, ReleaseConfirmation, ReportCard, ReportSection, ReportingPeriod,
    Submission, StructureChange, StructureChangeCancellation, StructureChangeLink,
    StructureChangeTransfer, SubProgram, TemplateSnapshot, User,
)
from .value_labels import value_kind_label


ACTION_LABELS = {
    "activity_contract_bound": "Faaliyet sözleşme durumu güncellendi",
    "activity_create": "Faaliyet oluşturuldu",
    "activity_delete": "Faaliyet silindi",
    "activity_evidence_access": "Faaliyet kanıtına erişildi",
    "activity_evidence_download": "Faaliyet kanıtı indirildi",
    "activity_evidence_upload": "Faaliyet kanıtı yüklendi",
    "activity_mapping": "Faaliyet alt programa bağlandı",
    "activity_mapping_csv": "Faaliyet eşleştirmesi aktarıldı",
    "activity_mapping_csv_revert": "Faaliyet eşleştirme aktarımı geri alındı",
    "activity_report_approve": "Faaliyet raporu onaylandı",
    "activity_report_revision": "Faaliyet raporu revizyonu oluşturuldu",
    "activity_source_total_decision": "Faaliyet kaynak toplamı kararı kaydedildi",
    "activity_update": "Faaliyet güncellendi",
    "actual_revision_create": "Gerçekleşme revizyonu kaydedildi",
    "budget_reallocation": "Bütçe aktarıldı",
    "card_assign": "Performans kaydı karta atandı",
    "card_remove": "Performans kartı kaldırıldı",
    "card_save": "Performans kartı kaydedildi",
    "catalogue_create": "Resmî faaliyet oluşturuldu",
    "catalogue_link": "Faaliyet resmî katalogla ilişkilendirildi",
    "data_import_apply": "Veri aktarımı uygulandı",
    "data_import_preview": "Veri aktarımı önizlemesi oluşturuldu",
    "data_import_revert": "Veri aktarımı geri alındı",
    "department_active": "Müdürlük durumu güncellendi",
    "department_create": "Müdürlük oluşturuldu",
    "department_export_docx": "Müdürlük raporu indirildi",
    "department_rename": "Müdürlük adı güncellendi",
    "department_submit": "Müdürlük verileri incelemeye gönderildi",
    "economic_grid_save": "Ekonomik değerler kaydedildi",
    "economic_programme_split": "Ekonomik değerler programa dağıtıldı",
    "economic_save": "Ekonomik değer kaydedildi",
    "finance_save": "Faaliyet bütçesi kaydedildi",
    "import_source_conflict_decision": "Aktarım kaynağı çakışması karara bağlandı",
    "indicator_create": "Gösterge oluşturuldu",
    "indicator_remove": "Gösterge kaldırıldı",
    "indicator_update": "Gösterge güncellendi",
    "login": "Giriş yapıldı",
    "login_throttle_lock": "Giriş denemeleri geçici olarak durduruldu",
    "operations_backup_export": "Veritabanı yedeği indirildi",
    "period_activate": "Raporlama dönemi etkinleştirildi",
    "period_create": "Raporlama dönemi oluşturuldu",
    "period_indicator_identity": "Gösterge dönemler arasında ilişkilendirildi",
    "personnel_cost_update": "Personel gideri güncellendi",
    "pp_data_change": "Performans programı verisi değiştirildi",
    "publication_freeze": "Yayın sürümü oluşturuldu",
    "publication_indicator_bind": "Yayın göstergesi ilişkilendirildi",
    "program_create": "Program oluşturuldu",
    "program_update": "Program güncellendi",
    "release_manual_confirmation": "Yayın teyidi kaydedildi",
    "scope_save": "Müdürlük kapsamı kaydedildi",
    "section_period_copy": "Rapor bölümleri döneme kopyalandı",
    "section_save": "Rapor bölümü kaydedildi",
    "self_password_change": "Parola değiştirildi",
    "source_money_verified": "Kaynak tutar doğrulandı",
    "source_value_verified": "Kaynak gösterge değeri doğrulandı",
    "structure_cancel": "Yapı kararı iptal edildi",
    "structure_change": "Müdürlük yapısı değiştirildi",
    "structure_department": "Yapı kararındaki müdürlük güncellendi",
    "structure_department_cancel": "Müdürlük değişikliği iptal edildi",
    "structure_link": "Yapı kararı bağlantısı kaydedildi",
    "structure_period_copy": "Müdürlük yapısı döneme kopyalandı",
    "structure_profile": "Müdürlük dönem bilgisi güncellendi",
    "structure_profile_cancel": "Müdürlük dönem bilgisi iptal edildi",
    "structure_scope_save": "Müdürlük kapsamı kaydedildi",
    "structure_transfer": "Yapı kararı aktarımı kaydedildi",
    "submission_approve": "Müdürlük verileri onaylandı",
    "submission_reopen": "Müdürlük verileri yeniden açıldı",
    "submission_return": "Müdürlük verileri düzeltme için iade edildi",
    "subprogram_create": "Alt program oluşturuldu",
    "subprogram_responsibilities": "Alt program sorumlulukları güncellendi",
    "subprogram_update": "Alt program güncellendi",
    "template_upload": "Rapor şablonu yüklendi",
    "template_verify": "Rapor şablonu doğrulandı",
    "user_activate": "Kullanıcı etkinleştirildi",
    "user_bulk_create": "Kullanıcı aktarımı tamamlandı",
    "user_bulk_create_item": "Kullanıcı oluşturuldu",
    "user_bulk_create_revert": "Kullanıcı aktarımı geri alındı",
    "user_can_submit_change": "Gönderim yetkisi güncellendi",
    "user_create": "Kullanıcı oluşturuldu",
    "user_deactivate": "Kullanıcı devre dışı bırakıldı",
    "user_is_active_change": "Kullanıcı durumu güncellendi",
    "user_password_reset": "Kullanıcı parolası sıfırlandı",
    "user_position_change": "Kullanıcı unvanı güncellendi",
}

ENTITY_LABELS = {
    "activity": "Faaliyet",
    "activity_cost_values": "Faaliyet bütçesi",
    "activity_evidence_file": "Faaliyet kanıtı",
    "activity_report_approval": "Faaliyet raporu onayı",
    "activity_report_revision": "Faaliyet raporu revizyonu",
    "activities": "Faaliyet",
    "actual_revision": "Gerçekleşme revizyonu",
    "budget_operation": "Bütçe aktarması",
    "database": "Veritabanı",
    "department": "Müdürlük",
    "department_cost_values": "Müdürlük gideri",
    "department_scopes": "Müdürlük kapsamı",
    "departments": "Müdürlük",
    "economic_values": "Ekonomik değer",
    "import_batch": "Veri aktarımı",
    "indicator": "Gösterge",
    "indicator_value": "Gösterge değeri",
    "indicators": "Gösterge",
    "login_throttle": "Giriş denetimi",
    "mapping_batch": "Faaliyet eşleştirme aktarımı",
    "official_activity": "Resmî faaliyet",
    "official_activities": "Resmî faaliyet",
    "publication": "Yayın",
    "publication_indicator_binding": "Yayın gösterge bağlantısı",
    "publications": "Yayın",
    "programs": "Program",
    "report_card": "Performans kartı",
    "report_cards": "Performans kartı",
    "report_section": "Rapor bölümü",
    "report_sections": "Rapor bölümü",
    "reporting_period": "Raporlama dönemi",
    "reporting_periods": "Raporlama dönemi",
    "release_confirmation": "Yayın teyidi",
    "submission": "Müdürlük gönderimi",
    "subprogram": "Alt program",
    "subprograms": "Alt program",
    "template_snapshot": "Rapor şablonu",
    "template_snapshots": "Rapor şablonu",
    "user": "Kullanıcı",
    "user_batch": "Kullanıcı aktarımı",
    "users": "Kullanıcı",
    "structure_change": "Yapı kararı",
    "structure_change_cancellations": "Yapı kararı iptali",
    "structure_change_links": "Yapı kararı bağlantısı",
    "structure_change_transfers": "Yapı kararı aktarımı",
    "structure_changes": "Yapı kararı",
}

ROLE_LABELS = {
    "admin": "Yönetici",
    "department": "Müdürlük kullanıcısı",
    "strategy": "Strateji kullanıcısı",
}

_LOOKUP_SPECS = {
    "activity": (Activity, "name"),
    "activities": (Activity, "name"),
    "activity_cost_values": (ActivityCostValue, "id"),
    "activity_evidence_file": (ActivityEvidenceFile, "filename"),
    "activity_report_approval": (ActivityReportApproval, "created_at"),
    "activity_report_revision": (ActivityReportRevision, "revision"),
    "actual_revision": (ActualRevision, "revision"),
    "budget_operation": (BudgetOperation, "reference_number"),
    "department": (Department, "name"),
    "department_cost_values": (DepartmentCostValue, "id"),
    "department_scopes": (DepartmentScope, "display_name"),
    "departments": (Department, "name"),
    "economic_values": (EconomicValue, "id"),
    "import_batch": (ImportBatch, "filename"),
    "indicator": (Indicator, "name"),
    "indicator_value": (IndicatorValue, "id"),
    "indicator_values": (IndicatorValue, "id"),
    "indicators": (Indicator, "name"),
    "official_activity": (OfficialActivity, "name"),
    "official_activities": (OfficialActivity, "name"),
    "programs": (Program, "name"),
    "publication_indicator_binding": (PublicationIndicatorBinding, "id"),
    "publication": (Publication, "version"),
    "publications": (Publication, "version"),
    "report_card": (ReportCard, "source_title"),
    "report_cards": (ReportCard, "source_title"),
    "report_section": (ReportSection, "title"),
    "report_sections": (ReportSection, "title"),
    "reporting_period": (ReportingPeriod, "year"),
    "reporting_periods": (ReportingPeriod, "year"),
    "release_confirmation": (ReleaseConfirmation, "decision"),
    "structure_change": (StructureChange, "change_type"),
    "structure_change_cancellations": (StructureChangeCancellation, "id"),
    "structure_change_links": (StructureChangeLink, "id"),
    "structure_change_transfers": (StructureChangeTransfer, "id"),
    "structure_changes": (StructureChange, "change_type"),
    "submission": (Submission, "revision"),
    "submissions": (Submission, "revision"),
    "subprogram": (SubProgram, "name"),
    "subprograms": (SubProgram, "name"),
    "template_snapshot": (TemplateSnapshot, "filename"),
    "template_snapshots": (TemplateSnapshot, "filename"),
    "user": (User, "full_name"),
    "users": (User, "full_name"),
}

_DETAIL_LOOKUP_MODELS = {
    "department_id": Department,
    "period_id": ReportingPeriod,
    "subprogram_id": SubProgram,
}


def action_label(value):
    return ACTION_LABELS.get(value, "Diğer işlem")


def entity_label(value):
    return ENTITY_LABELS.get(value, "Diğer kayıt")


def _detail_fields(value):
    text = str(value or "")
    try:
        parsed = json.loads(text)
    except (TypeError, ValueError):
        parsed = None
    if isinstance(parsed, dict):
        fields = []

        def flatten(mapping):
            for key, item in mapping.items():
                if isinstance(item, dict):
                    flatten(item)
                elif not isinstance(item, (list, tuple)):
                    fields.append((str(key), item))

        flatten(parsed)
        return fields
    if parsed is not None:
        return []
    return [(key.strip(), item.strip()) for part in text.split(";")
            if "=" in part for key, item in [part.split("=", 1)]]


def detail_references(value):
    references = defaultdict(set)
    for key, raw_value in _detail_fields(value):
        model = _DETAIL_LOOKUP_MODELS.get(key)
        if model is None:
            continue
        try:
            identifier = int(raw_value)
        except (TypeError, ValueError):
            continue
        if identifier > 0:
            references[model].add(identifier)
    return references


def audit_lookups(db, rows, safe_details):
    ids_by_model = defaultdict(set)
    for row in rows:
        if row.user_id:
            ids_by_model[User].add(row.user_id)
        spec = _LOOKUP_SPECS.get(row.entity_type)
        if spec and row.entity_id:
            ids_by_model[spec[0]].add(row.entity_id)
        for model, identifiers in detail_references(safe_details[row.id]).items():
            ids_by_model[model].update(identifiers)

    objects_by_model = {}
    for model, identifiers in ids_by_model.items():
        objects_by_model[model] = {
            item.id: item for item in db.scalars(select(model).where(model.id.in_(identifiers))).all()
        }

    entity_names = {}
    for row in rows:
        spec = _LOOKUP_SPECS.get(row.entity_type)
        if spec and row.entity_id:
            entity_names[row.id] = _display_value(row.entity_type, objects_by_model.get(spec[0], {}).get(row.entity_id))

    detail_names = {}
    for model, identifiers in ids_by_model.items():
        for identifier in identifiers:
            item = objects_by_model.get(model, {}).get(identifier)
            if item is None:
                continue
            if model is Department:
                detail_names["department_id", identifier] = item.name
            elif model is ReportingPeriod:
                detail_names["period_id", identifier] = str(item.year)
            elif model is SubProgram:
                detail_names["subprogram_id", identifier] = item.name
    users = objects_by_model.get(User, {})
    return users, entity_names, detail_names


def _display_value(entity_type, item):
    if item is None:
        return None
    if entity_type in {"budget_operation"}:
        return str(item.reference_number or "")
    if entity_type in {"publication", "publications"}:
        return f"{item.version}. sürüm"
    if entity_type in {"reporting_period", "reporting_periods"}:
        return str(item.year)
    spec = _LOOKUP_SPECS.get(entity_type)
    value = getattr(item, spec[1], None) if spec else None
    if entity_type in {"activity_report_revision", "actual_revision"}:
        return f"Revizyon {value}" if value else ""
    if entity_type in {"activity_report_approval"}:
        return item.created_at.strftime("%d.%m.%Y") if item.created_at else ""
    if entity_type in {"activity_cost_values"}:
        return f"{item.year} yılı {value_kind_label(item.value_kind)}"
    if entity_type in {"department_cost_values"}:
        category = "Personel ve SGK gideri" if item.category == "personnel_sgk" else "Müdürlük gideri"
        return f"{item.year} yılı {category} · {value_kind_label(item.value_kind)}"
    if entity_type in {"economic_values"}:
        return f"{item.year} yılı ekonomik değer · {value_kind_label(item.value_kind)}"
    if entity_type in {"indicator_value", "indicator_values"}:
        return f"{item.year} yılı {value_kind_label(item.value_kind)}"
    if entity_type in {"publication_indicator_binding"}:
        return ""
    if entity_type in {"structure_change", "structure_changes"}:
        return {
            "RENAMED": "Ad değişikliği",
            "MERGED": "Birleşme",
            "SPLIT": "Bölünme",
            "CLOSED": "Kapanış",
            "CREATED": "Yeni müdürlük",
        }.get(value, "")
    if entity_type in {"structure_change_cancellations", "structure_change_links",
                       "structure_change_transfers"}:
        return ""
    if entity_type == "release_confirmation":
        return {"confirmed": "Teyit", "revoked": "Teyit geri çekildi"}.get(value, "")
    if entity_type in {"submission", "submissions"}:
        return f"Revizyon {value}" if value else ""
    return str(value).strip() if value is not None else ""


def entity_text(row, names):
    label = entity_label(row.entity_type)
    if row.entity_type not in ENTITY_LABELS:
        return label
    if row.entity_id is None:
        return label
    if row.entity_type not in _LOOKUP_SPECS:
        return label
    name = names.get(row.id)
    if name is None:
        return f"{label} (silinmiş)"
    if name:
        return f"{label}: {name}"
    return label


def _translated_detail(key, value, names):
    value = str(value).strip()
    if key == "revision" and value:
        return f"Revizyon {value}"
    if key == "role" and value in ROLE_LABELS:
        return f"Rol: {ROLE_LABELS[value]}"
    if key == "count":
        try:
            return f"{int(value)} kayıt"
        except (TypeError, ValueError):
            return None
    if key in _DETAIL_LOOKUP_MODELS:
        identifier = None
        try:
            identifier = int(value)
        except (TypeError, ValueError):
            return None
        name = names.get((key, identifier))
        return f"{ {'department_id': 'Müdürlük', 'period_id': 'Dönem', 'subprogram_id': 'Alt program'}[key] }: {name}" if name else None
    if key == "bytes":
        try:
            megabytes = Decimal(value) / Decimal(1_000_000)
        except (InvalidOperation, TypeError, ValueError):
            return None
        return f"{megabytes:.1f}".replace(".", ",") + " MB"
    return None


def details_display(value, action, entity_type, detail_names):
    fields = _detail_fields(value)
    summaries = []
    untranslated = False
    for key, item in fields:
        label = _translated_detail(key, item, detail_names)
        if label:
            summaries.append(label)
        else:
            untranslated = True
    technical = []
    if untranslated or (value and not fields):
        technical.append(str(value))
    if action not in ACTION_LABELS:
        technical.append(str(action or ""))
    if entity_type not in ENTITY_LABELS:
        technical.append(str(entity_type or ""))
    return {
        "summary": " · ".join(summaries),
        "technical": "; ".join(part for part in technical if part) or None,
    }


def present_entity(row, names):
    return {
        "action": action_label(row.action),
        "entity": entity_text(row, names),
    }

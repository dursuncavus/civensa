import hashlib
import json
from .serialization import json_dumps
from decimal import Decimal
import re
import unicodedata
from datetime import datetime, UTC
from difflib import SequenceMatcher
from copy import deepcopy
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .models import (
    Organization, Department, ReportingPeriod, Program, SubProgram,
    Indicator, IndicatorValue, Activity, ActivityCostValue,
    DepartmentCostValue, Submission, ImportBatch, User, ReportCard, EconomicValue, ActivityCatalogueLink, DepartmentScope, SubmissionEvent, AuditLog,
)

# Only obvious spelling/title variants observed in the supplied 2026 source are normalized.
# This table is intentionally conservative: potentially real organizational name changes are not guessed.
DEPARTMENT_ALIASES = {
    "park bahceler mudurlugu": "park ve bahceler mudurlugu",
    "etut proje mudurlugu": "etud proje mudurlugu",
    "strateji mudurlugu": "strateji gelistirme mudurlugu",
    "ruhsat denetim mudurlugu": "ruhsat ve denetim mudurlugu",
    "destek hizmetler mudurlugu": "destek hizmetleri mudurlugu",
}

DISPLAY_OVERRIDES = {
    "park ve bahceler mudurlugu": "Park ve Bahçeler Müdürlüğü",
    "etud proje mudurlugu": "Etüd Proje Müdürlüğü",
    "strateji gelistirme mudurlugu": "Strateji Geliştirme Müdürlüğü",
    "ruhsat ve denetim mudurlugu": "Ruhsat ve Denetim Müdürlüğü",
    "destek hizmetleri mudurlugu": "Destek Hizmetleri Müdürlüğü",
}


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").replace("\xa0", " ")).strip()


def _validate_import_field_lengths(plan: dict) -> None:
    """Reject malformed/stale previews before PostgreSQL reports a server error."""
    limits = (("name", 300, "Gösterge adı"), ("unit", 50, "Ölçü birimi"))
    for department in plan["parsed"].get("departments", []):
        for block in department.get("blocks", []):
            for item in block.get("indicators", []):
                for field, limit, label in limits:
                    value = _clean(item.get(field, ""))
                    if len(value) > limit:
                        raise ValueError(
                            f"{department.get('name', 'Müdürlük')}: {label} {limit} karakter sınırını aşıyor. "
                            "İçe aktarma önizlemesini güncel sürümde yeniden oluşturun."
                        )


def _ascii_key(text: str) -> str:
    text = _clean(text).lower().replace("ı", "i")
    text = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def department_key(text: str) -> str:
    key = _ascii_key(text)
    # Normalize the spelling variant before alias lookup.
    key = re.sub(r"\betut\b", "etud", key)
    return DEPARTMENT_ALIASES.get(key, key)


def department_display(text: str) -> str:
    key = department_key(text)
    return DISPLAY_OVERRIDES.get(key, _clean(text))


def _merge_unique_costs(existing: list, incoming: list):
    """Keep distinct source candidates and every repeated-cell location."""
    keyed = {}
    for row in [*existing, *incoming]:
        key = (row.get("year"), row.get("kind"), row.get("funding_type", ""))
        target = keyed.setdefault(key, {**row, "candidates": []})
        candidates = row.get("candidates")
        if candidates is None:
            candidates = [] if row.get("amount") is None else [{
                "amount": str(Decimal(str(row["amount"]))),
                "locations": [{"table_number": row.get("table_number"),
                               "row_number": row.get("row_number"), "raw_text": row.get("raw_text", "")}],
            }]
        for candidate in candidates:
            amount = Decimal(candidate["amount"])
            same = next((c for c in target["candidates"] if Decimal(c["amount"]) == amount), None)
            if same is None:
                same = {"amount": str(amount), "locations": []}
                target["candidates"].append(same)
            for location in candidate["locations"]:
                if location not in same["locations"]:
                    same["locations"].append(dict(location))
        if len(target["candidates"]) == 1:
            chosen = target["candidates"][0]
            target.update(amount=chosen["amount"], raw_text=chosen["locations"][0]["raw_text"], state="verified")
        elif len(target["candidates"]) > 1:
            target.update(amount=None, state="source_conflict")
    return list(keyed.values())


def source_conflicts(parsed, decisions=()):
    """Attach validated batch decisions to a fresh plan, never to the source payload."""
    from .numbers import format_number
    kinds = {"budget": "Bütçe", "midyear_spend": "Haziran Sonu Harcama",
             "year_end_estimate": "Yıl Sonu Harcama Tahmini", "forecast": "Tahmin"}
    funding_labels = {"": "Personel ve SGK / Toplam", "total": "Toplam", "inside": "Bütçe İçi", "outside": "Bütçe Dışı"}
    conflicts = []
    for dept in parsed["departments"]:
        groups = [("personnel", dept["personnel"])]
        for index, activity in enumerate(dept["activities"]):
            activity["costs"] = _merge_unique_costs([], activity.get("costs", []))
            groups.append((f"activity:{index}", activity["costs"]))
        for scope, rows in groups:
            for row in rows:
                if len(row.get("candidates", [])) < 2:
                    continue
                identity = [department_key(dept["name"]), scope, row["year"], row["kind"], row.get("funding_type", "")]
                conflict_id = hashlib.sha256(json_dumps(identity).encode()).hexdigest()[:24]
                candidates = row["candidates"]
                decision = next((d for d in reversed(decisions) if d["conflict_id"] == conflict_id
                                 and d["candidates"] == candidates), None)
                locations = "; ".join(
                    format_number(c["amount"], money=True) + " (" + ", ".join(
                        f"Tablo {loc['table_number']}, satır {loc['row_number']}" for loc in c["locations"]) + ")"
                    for c in candidates)
                conflict = {"id": conflict_id, "department": dept["name"], "year": row["year"],
                            "kind": row["kind"], "funding_type": row.get("funding_type", "total"),
                            "candidates": candidates, "decision": decision,
                            "message": f"{dept['name']} · {row['year']} · {kinds.get(row['kind'], row['kind'])} · "
                                       f"{funding_labels.get(row.get('funding_type', ''), row.get('funding_type'))}: {locations}. "
                                       "Kaynak tutarını seçip en az 10 karakterlik gerekçe yazın."}
                conflicts.append(conflict)
                if decision:
                    chosen = next(c for c in candidates if Decimal(c["amount"]) == Decimal(decision["chosen_amount"]))
                    row.update(amount=chosen["amount"], raw_text=chosen["locations"][0]["raw_text"], state="verified")
    return conflicts


def decide_import_conflict(db, batch, conflict_id, chosen_amount, reason, actor):
    from .numbers import parse_number
    if batch.status != "preview":
        raise ValueError("Karar yalnızca önizlemede verilebilir. Yeni bir önizleme oluşturun.")
    if not isinstance(reason, str) or len(reason.strip()) < 10:
        raise ValueError("Kaynak tutarı kararı için en az 10 karakterlik gerekçe yazın.")
    decisions = json.loads(batch.decisions_json or "[]")
    plan = build_department_plan(db, json.loads(batch.payload_json), decisions)
    conflict = next((c for c in plan["conflicts"] if c["id"] == conflict_id), None)
    if not conflict:
        raise ValueError("Kaynak çelişkisi bulunamadı. Önizlemeyi yenileyin.")
    # Candidate amounts are serialized as decimal strings; also accept Turkish input.
    exact = next((c for c in conflict["candidates"] if c["amount"] == chosen_amount), None)
    amount = Decimal(exact["amount"]) if exact else parse_number(chosen_amount, money=True)
    candidate = next((c for c in conflict["candidates"] if Decimal(c["amount"]) == amount), None)
    if not candidate:
        raise ValueError("Önizlemede listelenen kaynak tutarlarından birini seçin.")
    decision = {"conflict_id": conflict_id, "actor": actor.id, "time": datetime.now(UTC).isoformat(),
                "department": conflict["department"], "year": conflict["year"], "kind": conflict["kind"],
                "funding_type": conflict["funding_type"], "chosen_amount": candidate["amount"],
                "candidates": conflict["candidates"], "reason": reason.strip()}
    batch.decisions_json = json_dumps([*decisions, decision], ensure_ascii=False)
    db.add(AuditLog(user_id=actor.id, action="import_source_conflict_decision", entity_type="import_batch",
                    entity_id=batch.id, details=json_dumps(decision, ensure_ascii=False)))
    return decision


def consolidate_source_departments(parsed: dict) -> dict:
    """Merge only safe/known source title variants before matching database departments."""
    grouped = {}
    order = []
    normalization_notes = []
    for dept in parsed.get("departments", []):
        raw = _clean(dept.get("name", ""))
        key = department_key(raw)
        if key not in grouped:
            grouped[key] = {
                "name": DISPLAY_OVERRIDES.get(key, raw),
                "source_names": [raw] if raw else [],
                "blocks": [],
                "activities": [],
                "personnel": [],
                "economic_tables": [],
            }
            order.append(key)
        else:
            if raw and raw not in grouped[key]["source_names"]:
                grouped[key]["source_names"].append(raw)
                normalization_notes.append(
                    f"'{raw}' başlığı '{grouped[key]['name']}' ile aynı müdürlük olarak birleştirildi."
                )
        target = grouped[key]
        target["blocks"].extend(dept.get("blocks", []))
        target["economic_tables"].extend(deepcopy(dept.get("economic_tables", [])))
        target["activities"].extend(deepcopy(dept.get("activities", [])))
        target["personnel"] = _merge_unique_costs(target["personnel"], dept.get("personnel", []))

    departments = [grouped[k] for k in order]
    for department in departments:
        block_tables = {b.get('table_number') for b in department['blocks']}
        for table in department['economic_tables']:
            if not set(table['block_table_numbers']).issubset(block_tables):
                for value in table['values']:
                    value['state'] = 'needs_review'
                    value['issue'] = (value.get('issue', '') + ' Kaynak program bloklarının müdürlük kapsamını kontrol edin.').strip()
    from .data_importer import _review_items
    review_items = _review_items(departments)
    summary = dict(parsed.get("summary", {}))
    summary["raw_department_count"] = summary.get("department_count", len(parsed.get("departments", [])))
    summary["department_count"] = len(departments)
    summary["indicator_count"] = sum(len(b.get("indicators", [])) for d in departments for b in d["blocks"])
    summary["activity_count"] = sum(len(d["activities"]) for d in departments)
    summary["needs_review_count"] = len(review_items)
    warnings = list(parsed.get("warnings", [])) + normalization_notes
    return {"departments": departments, "summary": summary, "warnings": warnings, "errors": list(parsed.get("errors", [])), "coverage_items": list(parsed.get("coverage_items", [])), "review_items": review_items}


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, department_key(a), department_key(b)).ratio()


def _source_activity_linkable(dept: dict) -> bool:
    activities = dept.get("activities", [])
    if not activities:
        return True
    if any('source_memberships' in a for a in activities):
        return all(_membership_block_index(a, dept.get('blocks', [])) is not None for a in activities)
    unique_blocks = []
    for block in dept.get("blocks", []):
        key = (_clean(block.get("program", "")), _clean(block.get("subprogram", "")))
        if key not in unique_blocks:
            unique_blocks.append(key)
    return len(unique_blocks) == 1


def _membership_block_index(activity, blocks):
    tables = {m['block_table_number'] for m in activity.get('source_memberships', [])}
    indices = [i for i, b in enumerate(blocks) if b.get('table_number') in tables]
    return indices[0] if len(indices) == 1 else None


def _link_subprograms(block_subprograms: list, activity_count: int, activities=None, blocks=None):
    if not activity_count:
        return []
    if activities is not None and any('source_memberships' in a for a in activities):
        return [block_subprograms[i] if (i := _membership_block_index(a, blocks)) is not None else None
                for a in activities]
    unique = []
    seen = set()
    for sp in block_subprograms:
        if sp.id not in seen:
            seen.add(sp.id); unique.append(sp)
    if len(unique) == 1:
        return [unique[0]] * activity_count
    return [None] * activity_count

def build_department_plan(db: Session, parsed: dict, decisions=()) -> dict:
    consolidated = consolidate_source_departments(parsed)
    conflicts = source_conflicts(consolidated, decisions)
    existing = db.scalars(select(Department).order_by(Department.name)).all()
    existing_by_key = {}
    for dept in existing:
        existing_by_key.setdefault(department_key(dept.name), []).append(dept)

    mappings = []
    used_existing_ids = set()
    unresolved = []
    for src in consolidated["departments"]:
        skey = department_key(src["name"])
        exact = existing_by_key.get(skey, [])
        if len(exact) == 1 and exact[0].id not in used_existing_ids:
            target = exact[0]
            mappings.append({
                "source_name": src["name"], "source_names": src.get("source_names", []),
                "action": "match", "department_id": target.id, "target_name": target.name,
                "confidence": 1.0,
            })
            used_existing_ids.add(target.id)
            continue
        if len(exact) > 1:
            item = {"source_name": src["name"], "action": "unresolved", "reason": "Aynı kanonik adda birden fazla mevcut müdürlük var."}
            mappings.append(item); unresolved.append(item); continue

        candidates = sorted(
            ((d, _similarity(src["name"], d.name)) for d in existing if d.id not in used_existing_ids),
            key=lambda x: x[1], reverse=True,
        )
        best = candidates[0] if candidates else None
        second_score = candidates[1][1] if len(candidates) > 1 else 0.0
        if best and best[1] >= 0.94 and (best[1] - second_score >= 0.05):
            mappings.append({
                "source_name": src["name"], "source_names": src.get("source_names", []),
                "action": "match", "department_id": best[0].id, "target_name": best[0].name,
                "confidence": round(best[1], 3),
            })
            used_existing_ids.add(best[0].id)
        elif best and best[1] >= 0.84:
            item = {
                "source_name": src["name"], "source_names": src.get("source_names", []),
                "action": "unresolved", "reason": "Benzer bir mevcut müdürlük bulundu; otomatik eşleştirme güvenli değil.",
                "candidate_id": best[0].id, "candidate_name": best[0].name, "confidence": round(best[1], 3),
            }
            mappings.append(item); unresolved.append(item)
        else:
            mappings.append({
                "source_name": src["name"], "source_names": src.get("source_names", []),
                "action": "create", "department_id": None, "target_name": department_display(src["name"]),
                "confidence": 1.0,
            })

    return {
        "parsed": consolidated,
        "conflicts": conflicts,
        "unresolved_conflicts": [c for c in conflicts if not c["decision"]],
        "mappings": mappings,
        "unresolved": unresolved,
        "summary": {
            **consolidated.get("summary", {}),
            "matched_department_count": sum(1 for m in mappings if m["action"] == "match"),
            "new_department_count": sum(1 for m in mappings if m["action"] == "create"),
            "unresolved_department_count": len(unresolved),
            "unlinked_activity_estimate": sum(len(d.get("activities", [])) for d in consolidated["departments"] if not _source_activity_linkable(d)),
        },
    }


def import_validation_errors(parsed: dict) -> list[str]:
    errors = list(parsed.get("errors", []))
    for table in parsed.get('rejected_economic_tables', []):
        if table['error'] not in errors:
            errors.append(table['error'])
    blocks = [block for dept in parsed.get("departments", []) for block in dept.get("blocks", [])]
    if not blocks and not errors:
        errors.append("Dosyada tanınan performans göstergesi tablosu bulunamadı. Bakanlık gösterge şablonunu ve Performans Göstergeleri başlığını kontrol edip dosyayı yeniden yükleyin.")
    for dept in parsed.get("departments", []):
        for index, block in enumerate(dept.get("blocks", []), 1):
            if not block.get("budget_year") and not parsed.get("errors"):
                errors.append(f"{dept['name']}, gösterge tablosu {index}: Bütçe Yılı eksik veya boş. Bütçe Yılı alanını doldurup dosyayı yeniden yükleyin.")
    return errors


def _get_or_create_program(db: Session, period_id: int, name: str) -> Program:
    name = _clean(name) or "Program adı belirtilmedi"
    program = db.scalar(select(Program).where(Program.period_id == period_id, Program.name == name))
    if not program:
        program = Program(period_id=period_id, name=name)
        db.add(program); db.flush()
    return program


def _get_or_create_subprogram(db: Session, period_id: int, program: Program, block: dict) -> SubProgram:
    name = _clean(block.get("subprogram", "")) or "Alt program adı belirtilmedi"
    sub = db.scalar(select(SubProgram).where(
        SubProgram.period_id == period_id,
        SubProgram.program_id == program.id,
        SubProgram.name == name,
    ))
    if not sub:
        sub = SubProgram(
            period_id=period_id, program_id=program.id, name=name,
            rationale=_clean(block.get("rationale", "")), goal=_clean(block.get("goal", "")),
        )
        db.add(sub); db.flush()
    else:
        # Program/alt-program records are shared by multiple departments. An import
        # must never silently overwrite existing institutional text. Only fill a
        # genuinely blank field; otherwise preserve the approved/common record.
        if not _clean(sub.rationale) and _clean(block.get("rationale", "")):
            sub.rationale = _clean(block["rationale"])
        if not _clean(sub.goal) and _clean(block.get("goal", "")):
            sub.goal = _clean(block["goal"])
    return sub


def _delete_department_period_data(db: Session, department_id: int, period_id: int):
    inds = db.scalars(select(Indicator).where(Indicator.department_id == department_id, Indicator.period_id == period_id).options(selectinload(Indicator.values))).all()
    for ind in inds:
        db.delete(ind)
    acts = db.scalars(select(Activity).where(Activity.department_id == department_id, Activity.period_id == period_id).options(selectinload(Activity.cost_values))).all()
    for act in acts:
        db.execute(ActivityCatalogueLink.__table__.delete().where(ActivityCatalogueLink.activity_id==act.id))
        db.delete(act)
    for row in db.scalars(select(DepartmentCostValue).where(DepartmentCostValue.department_id == department_id, DepartmentCostValue.period_id == period_id)).all():
        db.delete(row)
    for row in db.scalars(select(EconomicValue).where(EconomicValue.department_id==department_id, EconomicValue.period_id==period_id)).all():
        db.delete(row)
    db.flush()
    for card in db.scalars(select(ReportCard).where(ReportCard.department_id==department_id, ReportCard.period_id==period_id)).all():
        db.delete(card)
    db.flush()



def _dt(value):
    return value.isoformat() if value else None


def _serialize_department_state(db: Session, department_id: int, period_id: int) -> dict:
    dept = db.get(Department, department_id)
    inds = db.scalars(
        select(Indicator)
        .where(Indicator.department_id == department_id, Indicator.period_id == period_id)
        .options(selectinload(Indicator.values))
        .order_by(Indicator.id)
    ).all()
    acts = db.scalars(
        select(Activity)
        .where(Activity.department_id == department_id, Activity.period_id == period_id)
        .options(selectinload(Activity.cost_values))
        .order_by(Activity.id)
    ).all()
    costs = db.scalars(
        select(DepartmentCostValue)
        .where(DepartmentCostValue.department_id == department_id, DepartmentCostValue.period_id == period_id)
        .order_by(DepartmentCostValue.id)
    ).all()
    submission = db.scalar(select(Submission).where(Submission.department_id == department_id, Submission.period_id == period_id))
    users = db.scalars(select(User).where(User.department_id == department_id).order_by(User.id)).all()
    return {
        "department_id": department_id,
        "department_name": dept.name if dept else "",
        "economics": [{c.name:getattr(v,c.name) for c in EconomicValue.__table__.columns} for v in db.scalars(select(EconomicValue).where(EconomicValue.period_id==period_id,EconomicValue.department_id==department_id).order_by(EconomicValue.id)).all()],
        "scope": [{c.name:getattr(v,c.name) for c in DepartmentScope.__table__.columns} for v in db.scalars(select(DepartmentScope).where(DepartmentScope.period_id==period_id,DepartmentScope.department_id==department_id)).all()],
        "catalogue_links": [{"activity_id": a.id,"official_activity_id": oid} for a in acts for oid in db.scalars(select(ActivityCatalogueLink.official_activity_id).where(ActivityCatalogueLink.activity_id==a.id)).all()],
        "cards": [{c.name: getattr(card,c.name) for c in ReportCard.__table__.columns} for card in db.scalars(select(ReportCard).where(ReportCard.department_id==department_id,ReportCard.period_id==period_id).order_by(ReportCard.id)).all()],
        "user_ids": [u.id for u in users],
        "indicators": [
            {
                "id": i.id, "card_id": i.card_id, "code": i.code, "position": i.position, "subprogram_id": i.subprogram_id, "name": i.name, "unit": i.unit,
                **({'persistent_indicator_id': i.persistent_indicator_id} if i.persistent_indicator_id else {}),
                "explanation": i.explanation, "calculation_method": i.calculation_method,
                "data_source": i.data_source, "status": i.status,
                "values": [
                    {"id": v.id, "year": v.year, "value_kind": v.value_kind, "value": v.value, "raw_text": v.raw_text, "state": v.state}
                    for v in i.values
                ],
            }
            for i in inds
        ],
        "activities": [
            {
                "id": a.id, "card_id": a.card_id, "code": a.code, "position": a.position, "subprogram_id": a.subprogram_id, "name": a.name, "explanation": a.explanation,
                "cost_values": [
                    {
                        "id": v.id, "year": v.year, "value_kind": v.value_kind,
                        "funding_type": v.funding_type, "amount": v.amount, "raw_text": v.raw_text, "state": v.state,
                        "source_amount": v.source_amount, "source_raw_text": v.source_raw_text,
                        "source_resolution_json": v.source_resolution_json,
                    }
                    for v in sorted(a.cost_values, key=lambda v: (v.year, v.id))
                ],
            }
            for a in acts
        ],
        "department_costs": [
            {
                "id": c.id, "year": c.year, "value_kind": c.value_kind,
                "category": c.category, "amount": c.amount, "raw_text": c.raw_text, "state": c.state,
            }
            for c in costs
        ],
        "submission": None if not submission else {
            "id": submission.id, "revision": submission.revision, "status": submission.status, "return_note": submission.return_note,
            "submitted_at": _dt(submission.submitted_at), "reviewed_at": _dt(submission.reviewed_at),
        },
    }


def _state_hash(db: Session, department_ids: list[int], period_id: int, include_source=True) -> str:
    state = [_serialize_department_state(db, did, period_id) for did in sorted(set(department_ids)) if db.get(Department, did)]
    if not include_source:
        for department in state:
            for activity in department["activities"]:
                for cost in activity["cost_values"]:
                    for field in ("source_amount", "source_raw_text", "source_resolution_json"):
                        cost.pop(field, None)
    raw = json_dumps(state, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _build_preimport_snapshot(db: Session, plan: dict, period_id: int) -> dict:
    matched_ids = sorted({m["department_id"] for m in plan["mappings"] if m["action"] == "match"})
    return {
        "source_conflict_version": 1,
        "period_id": period_id,
        "preexisting_program_ids": list(db.scalars(select(Program.id).where(Program.period_id == period_id)).all()),
        "preexisting_subprogram_ids": list(db.scalars(select(SubProgram.id).where(SubProgram.period_id == period_id)).all()),
        "departments": [_serialize_department_state(db, did, period_id) for did in matched_ids],
        "created_department_ids": [],
    }


def import_revert_status(db: Session, batch: ImportBatch) -> tuple[bool, str]:
    if batch.status != "applied":
        return False, "Yalnızca uygulanmış içe aktarma geri alınabilir."
    try:
        snapshot = json.loads(batch.snapshot_json or "{}")
    except json.JSONDecodeError:
        return False, "Geri alma snapshot'ı okunamıyor."
    affected = [d["department_id"] for d in snapshot.get("departments", [])] + snapshot.get("created_department_ids", [])
    if not affected or not batch.applied_hash:
        return False, "Bu içe aktarma için güvenli geri alma verisi yok."
    current = _state_hash(db, affected, batch.period_id, include_source=bool(snapshot.get("source_conflict_version")))
    if current != batch.applied_hash:
        return False, "İçe aktarma sonrasında veriler değiştiği için otomatik geri alma güvenli değil."
    existing_submissions = {d["department_id"]: d.get("submission") for d in snapshot.get("departments", [])}
    for did in affected:
        if not existing_submissions.get(did) and db.scalar(select(SubmissionEvent.id).where(
                SubmissionEvent.department_id == did, SubmissionEvent.period_id == batch.period_id).limit(1)):
            return False, f"Müdürlük {did}: inceleme geçmişi bulunan teslim kaydı silinmeden geri alma yapılamıyor. İnceleme geçmişini koruyarak düzeltme yapmak için kart ekranını kullanın."
    for did in snapshot.get("created_department_ids", []):
        if db.scalar(select(User.id).where(User.department_id == did).limit(1)):
            return False, "İçe aktarmayla oluşan bir müdürlüğe kullanıcı atandığı için geri alma engellendi."
    return True, ""


def _restore_department_state(db: Session, state: dict, period_id: int) -> None:
    department_id = int(state["department_id"])
    for card in state.get("cards", []):
        db.add(ReportCard(**card))
    db.flush()
    for item in state.get("economics", []):
        db.add(EconomicValue(**item))
    for item in state.get("indicators", []):
        ind = Indicator(
            id=item["id"], period_id=period_id, department_id=department_id,
            persistent_indicator_id=item.get('persistent_indicator_id'),
            card_id=item.get("card_id"), code=item.get("code", ""), position=item.get("position", 0),
            subprogram_id=item["subprogram_id"], name=item["name"], unit=item["unit"],
            explanation=item.get("explanation", ""), calculation_method=item.get("calculation_method", ""),
            data_source=item.get("data_source", ""), status=item.get("status", "draft"),
        )
        db.add(ind); db.flush()
        for value in item.get("values", []):
            db.add(IndicatorValue(
                id=value["id"], indicator_id=ind.id, year=value["year"],
                value_kind=value["value_kind"], value=value["value"], raw_text=value.get("raw_text", ""), state=value.get("state", "verified"),
            ))
    for item in state.get("activities", []):
        act = Activity(
            id=item["id"], period_id=period_id, department_id=department_id,
            card_id=item.get("card_id"), code=item.get("code", ""), position=item.get("position", 0),
            subprogram_id=item.get("subprogram_id"), name=item["name"], explanation=item.get("explanation", ""),
        )
        db.add(act); db.flush()
        for value in item.get("cost_values", []):
            db.add(ActivityCostValue(
                id=value["id"], activity_id=act.id, year=value["year"], value_kind=value["value_kind"],
                funding_type=value.get("funding_type", "total"), amount=value.get("amount"), raw_text=value.get("raw_text", ""), state=value.get("state", "verified"),
                source_amount=value.get("source_amount"), source_raw_text=value.get("source_raw_text", ""),
                source_resolution_json=value.get("source_resolution_json", "{}"),
            ))
    db.flush()
    for link in state.get("catalogue_links", []):db.add(ActivityCatalogueLink(**link))
    for item in state.get("department_costs", []):
        db.add(DepartmentCostValue(
            id=item["id"], department_id=department_id, period_id=period_id, year=item["year"],
            value_kind=item["value_kind"], category=item.get("category", "personnel_sgk"), amount=item.get("amount"), raw_text=item.get("raw_text", ""), state=item.get("state", "verified"),
        ))
    sub = state.get("submission")
    current = db.scalar(select(Submission).where(
        Submission.department_id == department_id, Submission.period_id == period_id))
    if sub:
        if current is None:
            current = Submission(id=sub["id"], department_id=department_id, period_id=period_id)
            db.add(current)
        current.status = sub.get("status", "draft")
        current.return_note = sub.get("return_note", "")
        if "revision" in sub:
            current.revision = sub["revision"]
        current.submitted_at = datetime.fromisoformat(sub["submitted_at"]) if sub.get("submitted_at") else None
        current.reviewed_at = datetime.fromisoformat(sub["reviewed_at"]) if sub.get("reviewed_at") else None
    elif current:
        db.delete(current)


def revert_import_batch(db: Session, batch: ImportBatch) -> dict:
    can_revert, reason = import_revert_status(db, batch)
    if not can_revert:
        raise ValueError(reason)
    snapshot = json.loads(batch.snapshot_json)
    existing_states = snapshot.get("departments", [])
    existing_ids = [int(d["department_id"]) for d in existing_states]
    created_ids = [int(x) for x in snapshot.get("created_department_ids", [])]
    affected = existing_ids + created_ids

    # Retain existing submissions and their immutable history during restoration.
    for did in affected:
        if db.get(Department, did):
            _delete_department_period_data(db, did, batch.period_id)
            sub = db.scalar(select(Submission).where(Submission.department_id == did, Submission.period_id == batch.period_id))
            if sub and did in created_ids:
                db.delete(sub)
    db.flush()

    # Restore every pre-existing department byte-for-byte at the structured data level.
    for state in existing_states:
        _restore_department_state(db, state, batch.period_id)
    db.flush()

    # Departments created exclusively by this import can be removed if nothing was
    # attached to them after the import (guarded by import_revert_status).
    for did in created_ids:
        dept = db.get(Department, did)
        if dept:
            db.delete(dept)
    db.flush()

    # Clean up Program/Alt Program records that were created by the import and are
    # no longer referenced. Never touch records that existed before the import.
    old_sub_ids = set(snapshot.get("preexisting_subprogram_ids", []))
    for sp in db.scalars(select(SubProgram).where(SubProgram.period_id == batch.period_id)).all():
        if sp.id in old_sub_ids:
            continue
        has_indicator = db.scalar(select(Indicator.id).where(Indicator.subprogram_id == sp.id).limit(1))
        has_activity = db.scalar(select(Activity.id).where(Activity.subprogram_id == sp.id).limit(1))
        if not has_indicator and not has_activity:
            db.delete(sp)
    db.flush()
    old_program_ids = set(snapshot.get("preexisting_program_ids", []))
    for program in db.scalars(select(Program).where(Program.period_id == batch.period_id)).all():
        if program.id in old_program_ids:
            continue
        has_sub = db.scalar(select(SubProgram.id).where(SubProgram.program_id == program.id).limit(1))
        if not has_sub:
            db.delete(program)
    batch.status = "reverted"
    batch.reverted_at = datetime.now(UTC).replace(tzinfo=None)
    db.flush()
    return {"departments_restored": len(existing_ids), "departments_removed": len(created_ids)}


def apply_import_batch(db: Session, batch: ImportBatch, preserve_existing: bool = False) -> dict:
    if batch.status != "preview":
        raise ValueError("Bu içe aktarma paketi artık önizleme durumunda değil.")
    period = db.get(ReportingPeriod, batch.period_id)
    if not period:
        raise ValueError("Raporlama dönemi bulunamadı.")
    if period.template_status != "verified":
        raise ValueError("Bakanlık şablonu doğrulanmadan veri içe aktarılamaz.")

    raw = json.loads(batch.payload_json)
    errors = import_validation_errors(raw)
    if errors:
        raise ValueError(" ".join(errors))
    source_years = raw.get("summary", {}).get("source_years", [])
    if source_years and source_years != [period.year]:
        raise ValueError(f"Word dosyasındaki bütçe yılı {source_years}; seçilen Civensa dönemi {period.year}. Yanlış döneme veri yazılması engellendi.")
    plan = build_department_plan(db, raw, json.loads(batch.decisions_json or "[]"))
    if plan["unresolved_conflicts"]:
        raise ValueError("Kaynak tutarı çelişkileri çözülmeden içe aktarma uygulanamaz. Önizlemede her çelişki için tutar seçip gerekçe yazın.")
    for mapping in plan['mappings']:
        did = mapping.get('department_id')
        if did and not preserve_existing and db.scalar(select(Indicator.id).where(
                Indicator.department_id == did, Indicator.period_id == period.id,
                Indicator.persistent_indicator_id.is_not(None)).limit(1)):
            raise ValueError('Kalıcı kimliği atanmış göstergeler toplu içe aktarmayla değiştirilemez. Mevcut kayıtları koruyun veya yeni taslak dönem açın.')
        if did and not preserve_existing and (db.scalar(select(ReportCard.id).where(ReportCard.department_id==did, ReportCard.period_id==period.id).limit(1)) or db.scalar(select(EconomicValue.id).where(EconomicValue.department_id==did, EconomicValue.period_id==period.id).limit(1))):
            raise ValueError('Bu müdürlükte yeni rapor kartı/ekonomik tablo verisi var. Mevcut veriyi değiştiren toplu içe aktarma engellendi; kart ekranını kullanın veya yeni taslak dönem açın.')
    _validate_import_field_lengths(plan)
    if plan["unresolved"]:
        names = ", ".join(x["source_name"] for x in plan["unresolved"][:5])
        raise ValueError(f"Müdürlük eşleştirmesi netleşmeden içe aktarma uygulanamaz: {names}")

    organization = db.scalar(select(Organization).order_by(Organization.id))
    if not organization:
        raise ValueError("Kurum kaydı bulunamadı.")

    source_by_key = {department_key(d["name"]): d for d in plan["parsed"]["departments"]}
    mapping_by_key = {department_key(m["source_name"]): m for m in plan["mappings"]}
    snapshot = _build_preimport_snapshot(db, plan, period.id)
    if preserve_existing:
        # Existing departments are left byte-for-byte untouched. The snapshot only
        # tracks newly created departments so the batch remains safely reversible.
        snapshot["departments"] = []

    # Safety gate: never overwrite a package already being reviewed or approved.
    locked = []
    for m in plan["mappings"]:
        if m["action"] != "match" or preserve_existing:
            continue
        sub = db.scalar(select(Submission).where(Submission.department_id == m["department_id"], Submission.period_id == period.id))
        if sub and sub.status in {"submitted", "approved"}:
            locked.append(m["target_name"])
    if locked:
        raise ValueError("İncelemede/onaylı müdürlükler üzerine veri yazılamaz: " + ", ".join(locked[:8]))

    result = {
        "departments": 0, "created_departments": 0, "skipped_existing_departments": 0,
        "indicators": 0, "activities": 0, "personnel_values": 0, "cards": 0, "economic_values": 0,
        "unlinked_activities": 0, "preserve_existing": preserve_existing,
    }

    for skey, src in source_by_key.items():
        mapping = mapping_by_key[skey]
        if mapping["action"] == "match" and preserve_existing:
            result["skipped_existing_departments"] += 1
            continue
        if mapping["action"] == "match":
            dept = db.get(Department, mapping["department_id"])
        else:
            dept = Department(organization_id=organization.id, name=mapping["target_name"])
            db.add(dept); db.flush(); result["created_departments"] += 1
            snapshot["created_department_ids"].append(dept.id)

        _delete_department_period_data(db, dept.id, period.id)
        submission = db.scalar(select(Submission).where(Submission.department_id == dept.id, Submission.period_id == period.id))
        if not submission:
            submission = Submission(department_id=dept.id, period_id=period.id, status="draft")
            db.add(submission)

        block_subprograms = []
        block_cards = []
        for block_index, block in enumerate(src.get("blocks", []), 1):
            program = _get_or_create_program(db, period.id, block.get("program", ""))
            subprogram = _get_or_create_subprogram(db, period.id, program, block)
            block_subprograms.append(subprogram)
            meta = block.get('metadata') or (block.get('indicators') or [{}])[0]
            card = ReportCard(period_id=period.id, department_id=dept.id, subprogram_id=subprogram.id,
                position=block_index, source_title=block.get('source_title') or f'{period.year}/{block_index}',
                administration=block.get('administration') or src['name'],
                rationale=block.get('rationale',''), goal=block.get('goal',''),
                explanation=meta.get('explanation',''), calculation_method=meta.get('calculation_method',''),
                data_source=meta.get('data_source',''), responsible=meta.get('responsible',''))
            db.add(card); db.flush(); block_cards.append(card); result["cards"] += 1
            for item in block.get("indicators", []):
                ind = Indicator(
                    period_id=period.id, department_id=dept.id, subprogram_id=subprogram.id, card_id=card.id,
                    name=_clean(item.get("name", "")), unit=_clean(item.get("unit", "")),
                    explanation=_clean(item.get("explanation", "")),
                    calculation_method=_clean(item.get("calculation_method", "")),
                    data_source=_clean(item.get("data_source", "")), status="draft",
                )
                db.add(ind); db.flush(); result["indicators"] += 1
                seen_values = set()
                for value in item.get("values", []):
                    year, kind = value.get("year"), value.get("kind")
                    amount = value.get("value")
                    if year is None or not kind or (amount is None and value.get("state") != "needs_review") or (year, kind) in seen_values:
                        continue
                    seen_values.add((year, kind))
                    db.add(IndicatorValue(indicator_id=ind.id, year=int(year), value_kind=str(kind), value=Decimal(str(amount)) if amount is not None else None, raw_text=value.get("raw_text", str(amount)), state=value.get("state", "verified")))

        activities = src.get("activities", [])
        # Explicit book memberships select a card. Older Word sources keep the
        # single-subprogramme fallback; activity order never implies membership.
        links = _link_subprograms(block_subprograms, len(activities), activities, src.get('blocks', []))
        result["unlinked_activities"] += sum(1 for sp in links if sp is None)

        for item, subprogram in zip(activities, links):
            card_index = _membership_block_index(item, src.get('blocks', []))
            card_id = (block_cards[card_index].id if card_index is not None else
                       block_cards[0].id if len(block_cards) == 1 and 'source_memberships' not in item else None)
            act = Activity(
                period_id=period.id, department_id=dept.id,
                subprogram_id=subprogram.id if subprogram else None,
                card_id=card_id,
                name=_clean(item.get("name", "")) or _clean(item.get("official_name", "")) or "Faaliyet adı belirtilmedi",
                explanation=_clean(item.get("explanation", "")),
            )
            db.add(act); db.flush(); result["activities"] += 1
            from .program_service import mark_source_disagreements
            seen_costs = set()
            for cost in item.get("costs", []):
                key = (cost.get("year"), cost.get("kind"), cost.get("funding_type", "total"))
                amount = cost.get("amount")
                if key[0] is None or not key[1] or (amount is None and cost.get("state") not in {"needs_review", "not_applicable"}) or key in seen_costs:
                    continue
                seen_costs.add(key)
                db.add(ActivityCostValue(
                    activity_id=act.id, year=int(key[0]), value_kind=str(key[1]),
                    funding_type=str(key[2]), amount=Decimal(str(amount)) if amount is not None else None, raw_text=cost.get("raw_text", str(amount)), state=cost.get("state", "verified"),
                    source_amount=Decimal(str(amount)) if key[2] == "total" and amount is not None else None,
                    source_raw_text=cost.get("raw_text", "") if key[2] == "total" else "",
                ))

            db.flush()
            db.expire(act, ["cost_values"])
            mark_source_disagreements(act)

        seen_personnel = set()
        for row in src.get("personnel", []):
            key = (row.get("year"), row.get("kind"))
            amount = row.get("amount")
            if key[0] is None or not key[1] or (amount is None and row.get("state") not in {"needs_review", "not_applicable"}) or key in seen_personnel:
                continue
            seen_personnel.add(key)
            db.add(DepartmentCostValue(
                department_id=dept.id, period_id=period.id, year=int(key[0]),
                value_kind=str(key[1]), category="personnel_sgk", amount=Decimal(str(amount)) if amount is not None else None,
                raw_text=row.get("raw_text", ""), state=row.get("state", "verified"),
            ))
            result["personnel_values"] += 1
        cards_by_table = {block.get('table_number'): card for block, card in zip(src['blocks'], block_cards)}
        economic_rows = {}
        for table in src.get('economic_tables', []):
            source_cards = [cards_by_table[n] for n in table['block_table_numbers'] if n in cards_by_table]
            context = {key: table[key] for key in ('categories', 'totals', 'block_table_numbers')}
            context['card_ids'] = [c.id for c in source_cards]
            for value in table['values']:
                key = tuple(value[k] for k in ('year', 'kind', 'category', 'program_group', 'funding_type'))
                if key in economic_rows:
                    row = economic_rows[key]
                    row.amount = None; row.state = 'needs_review'
                    row.issue = 'Aynı ekonomik hücre birden fazla kaynak tabloda bulunuyor; kaynakları karşılaştırın.'
                    row.raw_text += ' / ' + value['raw_text']
                    continue
                row = EconomicValue(period_id=period.id, department_id=dept.id, year=value['year'],
                    value_kind=value['kind'], category=value['category'], program_group=value['program_group'],
                    funding_type=value['funding_type'], amount=Decimal(value['amount']).quantize(Decimal('.01')) if value['amount'] is not None else None,
                    raw_text=value['raw_text'], state=value['state'], issue=value.get('issue', ''),
                    source_card_id=source_cards[-1].id if source_cards else None, source_table_number=table['table_number'],
                    source_context_json=json_dumps(context, ensure_ascii=False))
                if len(source_cards) != len(table['block_table_numbers']):
                    row.state = 'needs_review'
                    if 'Kaynak program bloklarının' not in row.issue:
                        row.issue = (row.issue + ' Kaynak program bloklarının müdürlük kapsamını kontrol edin.').strip()
                economic_rows[key] = row
                db.add(row); result['economic_values'] += 1
        result["departments"] += 1

    batch.snapshot_json = json_dumps(snapshot, ensure_ascii=False, sort_keys=True)
    batch.status = "applied"
    batch.applied_at = datetime.now(UTC).replace(tzinfo=None)
    db.flush()
    affected = [d["department_id"] for d in snapshot["departments"]] + snapshot["created_department_ids"]
    batch.applied_hash = _state_hash(db, affected, period.id)
    result["plan_summary"] = plan["summary"]
    return result

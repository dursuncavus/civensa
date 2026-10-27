import ast
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import event

from app.audit_display import (
    ACTION_LABELS, ENTITY_LABELS, action_label, audit_lookups, details_display,
    entity_label, entity_text,
)
from app.main import safe_audit_details
from app.models import Activity, AuditLog


APP = Path(__file__).parents[1] / "app"
DYNAMIC_ACTIONS = {
    "submission_approve", "submission_return", "user_can_submit_change",
    "user_is_active_change", "user_position_change",
}
DYNAMIC_ENTITIES = {
    "activity_cost_values", "activities", "department_cost_values", "department_scopes",
    "economic_values", "indicators", "programs", "report_sections", "reporting_periods",
    "structure_change_cancellations", "structure_change_links", "structure_change_transfers",
    "structure_changes", "subprograms",
}


def _literal_strings(expression):
    if isinstance(expression, ast.Constant) and isinstance(expression.value, str):
        return {expression.value}
    if isinstance(expression, ast.IfExp):
        return _literal_strings(expression.body) | _literal_strings(expression.orelse)
    if isinstance(expression, ast.BinOp) and isinstance(expression.op, ast.Add):
        left, right = _literal_strings(expression.left), _literal_strings(expression.right)
        return {first + second for first in left for second in right}
    return set()


def _audit_codes():
    actions, entities = set(), set()
    for path in APP.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            function = node.func.id if isinstance(node.func, ast.Name) else (
                node.func.attr if isinstance(node.func, ast.Attribute) else ""
            )
            if function == "log":
                if len(node.args) > 2:
                    actions.update(_literal_strings(node.args[2]))
                if len(node.args) > 3:
                    entities.update(_literal_strings(node.args[3]))
            elif function == "audit_change":
                if len(node.args) > 2:
                    actions.update(_literal_strings(node.args[2]))
            elif function == "transact" and len(node.args) > 3:
                actions.update(_literal_strings(node.args[2]))
                entities.update(_literal_strings(node.args[3]))
            elif function == "AuditLog":
                keywords = {item.arg: item.value for item in node.keywords}
                if "action" in keywords:
                    actions.update(_literal_strings(keywords["action"]))
                if "entity_type" in keywords:
                    entities.update(_literal_strings(keywords["entity_type"]))
            elif function == "audit_user_change" and len(node.args) > 3:
                for field in _literal_strings(node.args[3]):
                    actions.add(f"user_{field}_change")
    return actions | DYNAMIC_ACTIONS, entities | DYNAMIC_ENTITIES


def test_every_audit_code_used_in_app_has_a_label():
    actions, entities = _audit_codes()
    assert actions <= ACTION_LABELS.keys(), sorted(actions - ACTION_LABELS.keys())
    assert entities <= ENTITY_LABELS.keys(), sorted(entities - ENTITY_LABELS.keys())


def test_unknown_codes_use_safe_labels_and_are_technical_details():
    assert action_label("future_action") == "Diğer işlem"
    assert entity_label("future_entity") == "Diğer kayıt"
    displayed = details_display("revision=3", "future_action", "future_entity", {})
    assert displayed == {
        "summary": "Revizyon 3",
        "technical": "future_action; future_entity",
    }


def test_known_key_value_and_json_details_are_summarized():
    details = details_display(
        "revision=3;role=strategy;count=12;bytes=1200000",
        "activity_update", "activity", {},
    )
    assert details == {
        "summary": "Revizyon 3 · Rol: Strateji kullanıcısı · 12 kayıt · 1,2 MB",
        "technical": None,
    }
    json_details = details_display(
        '{"revision": 4, "department_id": 9, "unmapped": "kept"}',
        "activity_update", "activity", {("department_id", 9): "Fen İşleri"},
    )
    assert json_details["summary"] == "Revizyon 4 · Müdürlük: Fen İşleri"
    assert json_details["technical"] == '{"revision": 4, "department_id": 9, "unmapped": "kept"}'


def test_sensitive_detail_masking_precedes_detail_translation():
    safe = safe_audit_details("revision=3;parola=x")
    assert safe == "[hassas ayrıntı gizlendi]"
    assert details_display(safe, "activity_update", "activity", {}) == {
        "summary": "", "technical": safe,
    }


def test_entity_names_and_deleted_records_never_show_internal_ids():
    existing = SimpleNamespace(id=1, action="activity_update", entity_type="activity", entity_id=8)
    deleted = SimpleNamespace(id=2, action="activity_update", entity_type="activity", entity_id=9)
    assert entity_text(existing, {existing.id: "Faaliyet adı"}) == "Faaliyet: Faaliyet adı"
    assert entity_text(deleted, {}) == "Faaliyet (silinmiş)"


@pytest.mark.postgres
def test_entity_lookups_are_batched_by_type(db, sample):
    activities = [
        Activity(period_id=sample["period"].id, department_id=sample["department"].id,
                 name=f"Faaliyet {index}", code=str(index))
        for index in range(3)
    ]
    db.add_all(activities)
    db.flush()
    rows = [
        AuditLog(id=index + 1, action="activity_update", entity_type="activity",
                 entity_id=item.id, user_id=None, details="", created_at=datetime(2026, 10, 27))
        for index, item in enumerate(activities)
    ]
    statements = []

    def record_query(connection, cursor, statement, parameters, context, executemany):
        if "activities" in statement.lower():
            statements.append(statement)

    event.listen(db.bind, "before_cursor_execute", record_query)
    try:
        _, names, _ = audit_lookups(db, rows, {row.id: "" for row in rows})
    finally:
        event.remove(db.bind, "before_cursor_execute", record_query)
    assert len(statements) == 1
    assert [names[row.id] for row in rows] == ["Faaliyet 0", "Faaliyet 1", "Faaliyet 2"]

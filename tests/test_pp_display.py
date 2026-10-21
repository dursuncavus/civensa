"""CIV-060: Turkish PP presentation without changing stored workflow data."""
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.models import Publication, Submission, SubmissionEvent
from app.pp_display import actor_label, status_label
from app.time_display import turkey_time


@pytest.mark.parametrize("raw,expected", [
    ("draft", "Taslak"), ("submitted", "İncelemede"),
    ("returned", "İade edildi"), ("approved", "Onaylandı"),
    ("approve", "Onaylandı"), ("return", "İade edildi"),
    ("active", "Etkin"), ("closed", "Kapalı"), ("pending", "Bekliyor"),
    ("verified", "Doğrulandı"), ("preview", "Önizleme"),
    ("applied", "Uygulandı"), ("reverted", "Geri alındı"),
    ("required", "Kart gerekli"), ("zero", "Sıfır bütçeli"),
    ("excluded", "Kapsam dışı"), ("ready", "Hazır"), ("blocked", "Engellendi"),
    ("not_started", "Başlamadı"), ("in_progress", "Veri girişi devam ediyor"),
    ("needs_attention", "Eksikleri / hataları var"),
    ("ok", "Sağlıklı"), ("error", "Hata"), ("degraded", "Aksama var"),
    ("future", "Bilinmeyen durum (future)"),
    ("", "Bilinmeyen durum ()"), (None, "Bilinmeyen durum (None)"),
])
def test_status_labels(raw, expected):
    assert status_label(raw) == expected


@pytest.mark.parametrize("value,expected", [
    (datetime(2026, 10, 20, 11, 5), "20.10.2026 14:05 TSİ"),
    (datetime(2026, 10, 20, 22, 5), "21.10.2026 01:05 TSİ"),
    (datetime(2026, 12, 31, 22, 5, tzinfo=timezone.utc), "01.01.2027 01:05 TSİ"),
    ("2026-10-20T22:05:00Z", "21.10.2026 01:05 TSİ"),
    (datetime(2026, 10, 20, 11, 5, tzinfo=timezone(timedelta(hours=-4))),
     "20.10.2026 18:05 TSİ"),
])
def test_utc_to_istanbul(value, expected):
    assert turkey_time(value) == expected


@pytest.mark.parametrize("position,expected", [
    ("director", "Ayşe Yılmaz (Müdür)"), ("staff", "Ayşe Yılmaz (Personel)"),
    (None, "Ayşe Yılmaz"), ("", "Ayşe Yılmaz"),
])
def test_actor_name_and_position(position, expected):
    assert actor_label(SimpleNamespace(full_name="Ayşe Yılmaz", position=position)) == expected


def test_actor_without_position_or_user():
    assert actor_label(SimpleNamespace(full_name="Ayşe Yılmaz")) == "Ayşe Yılmaz"
    assert actor_label(None) == "Sistem"


@pytest.mark.postgres
@pytest.mark.parametrize("status,event_type,actor,expected", [
    ("submitted", "submitted", "user", "İncelemede"),
    ("approved", "approve", "strategy", "Onaylandı"),
    ("returned", "return", None, "İade edildi"),
    ("future", "future", None, "Bilinmeyen durum (future)"),
])
def test_review_html_latest_action(client, db, sample, status, event_type, actor, expected):
    from app.main import app, require_user
    app.dependency_overrides[require_user] = lambda: sample["strategy"]
    submission = db.scalar(select(Submission))
    submission.status = status
    stamp = datetime(2026, 10, 20, 22, 5)
    # Equal timestamps occur in legacy history: the higher event id is latest.
    for event_actor, kind, note in [(sample["strategy"].id, "approve", "Önceki işlem"),
                                    (sample[actor].id if actor else None, event_type, "Son işlem açıklaması")]:
        db.add(SubmissionEvent(submission_id=submission.id, department_id=sample["department"].id,
            period_id=sample["period"].id, actor_user_id=event_actor, event_type=kind,
            revision=1, note=note, created_at=stamp))
        db.flush()
    db.commit()
    before = [(e.id, e.created_at, e.actor_user_id) for e in db.scalars(select(SubmissionEvent))]
    response = client.get(f"/review?period_id={sample['period'].id}")
    assert response.status_code == 200
    assert f'>{expected}</span>' in response.text
    assert f'<b>{expected}</b>' in response.text
    assert "21.10.2026 01:05 TSİ" in response.text
    expected_actor = {"user": "Test (Personel)", "strategy": "Strateji (Müdür)", None: "Sistem"}[actor]
    assert f" · {expected_actor}" in response.text
    assert "Son işlem açıklaması" in response.text
    assert "Önceki işlem" not in response.text
    db.expire_all()
    assert [(e.id, e.created_at, e.actor_user_id) for e in db.scalars(select(SubmissionEvent))] == before
    assert db.get(Submission, submission.id).status == status


@pytest.mark.postgres
def test_review_html_draft_without_history(client, sample):
    from app.main import app, require_user
    app.dependency_overrides[require_user] = lambda: sample["strategy"]
    response = client.get(f"/review?period_id={sample['period'].id}")
    assert response.status_code == 200
    assert '>Taslak</span>' in response.text
    assert 'Eski kayıt · geçmiş yok' in response.text


@pytest.mark.postgres
def test_publication_html_actor_and_time(client, db, sample):
    from app.main import app, require_user
    app.dependency_overrides[require_user] = lambda: sample["strategy"]
    stamp = datetime(2026, 10, 20, 22, 5)
    publication = Publication(period_id=sample["period"].id, version=1, snapshot_json="{}",
        sha256="0" * 64, created_by=sample["strategy"].id, created_at=stamp)
    db.add(publication)
    db.commit()
    response = client.get(f"/report-builder?period_id={sample['period'].id}")
    assert response.status_code == 200
    assert '21.10.2026 01:05 TSİ · Strateji (Müdür)' in response.text
    assert f'/publications/{publication.id}.docx' in response.text
    db.expire_all()
    assert db.get(Publication, publication.id).created_at == stamp


def test_publication_html_system_fallback(client, sample):
    # The DB requires a publication creator; render an unavailable user explicitly
    # to cover the display contract without weakening that constraint.
    from app.main import templates
    from starlette.requests import Request
    request = Request({"type": "http", "method": "GET", "path": "/report-builder",
                       "headers": [], "session": {}})
    html = templates.get_template("report_builder.html").render(
        request=request, user=sample["strategy"], period=sample["period"],
        departments=[], sections=[], catalogue=[],
        publication_reopens={1: []}, superseded_by={}, stale_departments=[],
        publications=[SimpleNamespace(id=1, version=1, creator=None,
            created_at=datetime(2026, 10, 20, 11, 5))])
    assert '20.10.2026 14:05 TSİ · Sistem' in html


def test_unknown_status_remains_escaped():
    from app.main import templates
    html = templates.env.from_string("{{ value|status_label }}").render(value="<script>")
    assert html == "Bilinmeyen durum (&lt;script&gt;)"


@pytest.mark.postgres
def test_audit_html_actor_and_system_fallback(client, db, sample):
    from app.main import app, require_user
    from app.models import AuditLog
    app.dependency_overrides[require_user] = lambda: sample["strategy"]
    stamp = datetime(2026, 10, 20, 22, 5)
    for actor_id in [sample["user"].id, None]:
        db.add(AuditLog(user_id=actor_id, action="submission_submitted", entity_type="submission",
                        created_at=stamp, details="İncelemeye gönderildi"))
    db.commit()
    response = client.get(f"/audit?period_id={sample['period'].id}")
    assert response.status_code == 200
    assert "21.10.2026 01:05 TSİ" in response.text
    assert "Test (Personel)" in response.text
    assert ">Sistem</td>" in response.text


@pytest.mark.postgres
def test_department_dashboard_status(client, sample):
    response = client.get(f"/dashboard?period_id={sample['period'].id}")
    assert response.status_code == 200
    assert "<b>Taslak</b>" in response.text


@pytest.mark.postgres
@pytest.mark.parametrize("actor", ["user", "strategy", None])
def test_department_history_display(client, db, sample, actor):
    submission = db.scalar(select(Submission))
    stamp = datetime(2026, 10, 20, 22, 5)
    for kind, actor_id in [("submitted", sample["user"].id),
                           ("return", sample[actor].id if actor else None)]:
        db.add(SubmissionEvent(submission_id=submission.id,
            department_id=sample["department"].id, period_id=sample["period"].id,
            actor_user_id=actor_id, event_type=kind, revision=1, created_at=stamp))
        db.flush()
    db.commit()
    before = [(e.id, e.created_at, e.actor_user_id) for e in db.scalars(select(SubmissionEvent))]
    db.expire_all()
    response = client.get(f"/department/{sample['department'].id}?period_id={sample['period'].id}")
    assert response.status_code == 200
    assert "Revizyon 1 · İade edildi</b>" in response.text
    assert "Revizyon 1 · İncelemeye gönderildi</b>" in response.text
    expected_actor = {"user": "Test (Personel)", "strategy": "Strateji (Müdür)", None: "Sistem"}[actor]
    assert f"21.10.2026 01:05 TSİ · {expected_actor}" in response.text
    assert response.text.index("Revizyon 1 · İade edildi") < response.text.index("Revizyon 1 · İncelemeye gönderildi")
    db.expire_all()
    assert [(e.id, e.created_at, e.actor_user_id) for e in db.scalars(select(SubmissionEvent))] == before


@pytest.mark.postgres
@pytest.mark.parametrize("actor", ["user", "strategy", None])
def test_activity_mapping_history_display(client, db, sample, actor):
    from app.main import app, require_user
    from app.models import AuditLog
    app.dependency_overrides[require_user] = lambda: sample["strategy"]
    # Keep a gap so the mapping queue and its recent CSV history are rendered.
    sample["activity"].card_id = None
    stamp = datetime(2026, 10, 20, 22, 5)
    for batch, actor_id in [("older", sample["user"].id),
                            ("latest", sample["user"].id),
                            ("latest", sample[actor].id if actor else None)]:
        db.add(AuditLog(user_id=actor_id, action="activity_mapping_csv", entity_type="activity",
            entity_id=sample["activity"].id, created_at=stamp,
            details=f"batch={batch};subprogram_id={sample['subprogram'].id}"))
        db.flush()
    db.commit()
    before = [(a.id, a.created_at, a.user_id, a.details) for a in db.scalars(select(AuditLog))]
    db.expire_all()
    response = client.get(f"/activity-mapping?period_id={sample['period'].id}")
    assert response.status_code == 200
    expected_actor = {"user": "Test (Personel)", "strategy": "Strateji (Müdür)", None: "Sistem"}[actor]
    assert f"21.10.2026 01:05 TSİ · {expected_actor}" in response.text
    assert "Uygulandı · İşlem latest" in response.text
    assert response.text.index("İşlem latest") < response.text.index("İşlem older")
    db.expire_all()
    assert [(a.id, a.created_at, a.user_id, a.details) for a in db.scalars(select(AuditLog))] == before


@pytest.mark.postgres
def test_activity_mapping_reverted_batch_display(client, db, sample, monkeypatch):
    import csv
    import io
    import re
    from app import models
    from app.main import app, require_user, MAPPING_CSV_HEADERS
    from app.models import Activity, AuditLog

    app.dependency_overrides[require_user] = lambda: sample["strategy"]
    stamp = datetime(2026, 10, 20, 11, 5, tzinfo=timezone.utc)
    monkeypatch.setattr(models, "datetime", SimpleNamespace(now=lambda _: stamp))
    sample["activity"].subprogram_id = None
    second = Activity(period_id=sample["period"].id, department_id=sample["department"].id,
                      name="İkinci faaliyet")
    db.add(second)
    db.commit()

    def apply_batch(activity):
        data = io.StringIO()
        writer = csv.DictWriter(data, fieldnames=MAPPING_CSV_HEADERS)
        writer.writeheader()
        writer.writerow({"Faaliyet ID": activity.id, "Müdürlük": sample["department"].name,
                         "Faaliyet": activity.name,
                         "Seçilecek Program / Alt Program":
                         f"{sample['subprogram'].program.name} / {sample['subprogram'].name}"})
        response = client.post(f"/api/activity-mappings/import-apply?period_id={sample['period'].id}",
            files={"file": ("queue.csv", data.getvalue().encode("utf-8-sig"), "text/csv")})
        assert response.status_code == 200, response.text
        return response.json()["batch_id"]

    reverted = apply_batch(sample["activity"])
    applied = apply_batch(second)
    # A different user performs the revert; the display must use that audit actor/time.
    sample["user"].role = "strategy"
    db.commit()
    app.dependency_overrides[require_user] = lambda: sample["user"]
    stamp = datetime(2026, 10, 20, 22, 5, tzinfo=timezone.utc)
    response = client.post(f"/api/activity-mappings/batches/{reverted}/revert?period_id={sample['period'].id}")
    assert response.status_code == 200, response.text
    db.expire_all()
    from sqlalchemy import event
    revert_queries = []

    def record_revert_query(execute_state):
        if execute_state.is_select:
            params = execute_state.statement.compile().params
            if "activity_mapping_csv_revert" in params.values():
                revert_queries.append(execute_state.statement)

    event.listen(db, "do_orm_execute", record_revert_query)
    try:
        response = client.get(f"/activity-mapping?period_id={sample['period'].id}")
    finally:
        event.remove(db, "do_orm_execute", record_revert_query)
    assert len(revert_queries) == 1  # Both displayed batches share one revert lookup.
    assert response.status_code == 200
    items = re.findall(r'<div class="snapshot-item">(.*?)</div>', response.text)
    reverted_item = next(item for item in items if f"İşlem {reverted}" in item)
    applied_item = next(item for item in items if f"İşlem {applied}" in item)
    assert f"Geri alındı · İşlem {reverted}" in reverted_item
    assert "21.10.2026 01:05 TSİ · Test (Personel)" in reverted_item
    assert "Uygulandı" not in reverted_item
    assert "revert-mapping-batch" not in reverted_item
    assert "20.10.2026 14:05 TSİ · Strateji (Müdür)" in applied_item
    assert f"Uygulandı · İşlem {applied}" in applied_item
    assert f'data-batch="{applied}"' in applied_item
    assert len(list(db.scalars(select(AuditLog).where(AuditLog.action == "activity_mapping_csv")))) == 2


@pytest.mark.parametrize("raw,expected", [
    ("submitted", "İncelemeye gönderildi"), ("approve", "Onaylandı"),
    ("return", "İade edildi"), ("future", "Bilinmeyen işlem (future)"),
    (None, "Bilinmeyen işlem (None)"), ("", "Bilinmeyen işlem ()"),
])
def test_event_labels(raw, expected):
    from app.pp_display import event_label
    assert event_label(raw) == expected


def test_unknown_event_remains_escaped():
    from app.main import templates
    html = templates.env.from_string("{{ value|event_label }}").render(value="<script>")
    assert html == "Bilinmeyen işlem (&lt;script&gt;)"

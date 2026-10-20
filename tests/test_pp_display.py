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

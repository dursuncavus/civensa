"""Release readiness must compare the database with the real Alembic script head."""
import ast, os, shutil, subprocess, sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine

ROOT = Path(__file__).resolve().parents[1]
CHECK_NAMES = [
    "database", "migration_head", "period_active", "departments_present", "indicators_present",
    "activities_present", "no_orphan_activities", "no_orphan_indicators",
    "no_duplicate_active_department_accounts", "workflow_schema_present",
]


def _literal(node):
    value = ast.literal_eval(node) if node is not None else None
    if value is None:
        return ()
    return tuple(value) if isinstance(value, (tuple, list)) else (value,)


def _script_graph():
    """Read revision ids from migrations/versions without going through Alembic."""
    revisions, parents = {}, set()
    for path in sorted((ROOT / "migrations" / "versions").glob("*.py")):
        found = {}
        for node in ast.parse(path.read_text(encoding="utf-8")).body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                found[node.targets[0].id] = node.value
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                found[node.target.id] = node.value
        (revision,) = _literal(found["revision"])
        revisions[revision] = _literal(found.get("down_revision"))
        parents.update(revisions[revision])
    return revisions, sorted(set(revisions) - parents)


@pytest.fixture(scope="module")
def migrated_template(tmp_path_factory):
    path = tmp_path_factory.mktemp("readiness") / "head.db"
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{path}"}
    result = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=ROOT, env=env,
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return path


@pytest.fixture
def readiness(client, sample, migrated_template, tmp_path, monkeypatch):
    from app import main
    path = tmp_path / "readiness.db"
    shutil.copyfile(migrated_template, path)
    engine = create_engine(f"sqlite:///{path}")
    monkeypatch.setattr(main, "engine", engine)
    main.app.dependency_overrides[main.require_user] = lambda: sample["strategy"]

    def read(version=None):
        if version:
            with engine.begin() as connection:
                connection.exec_driver_sql("UPDATE alembic_version SET version_num = ?", (version,))
        response = client.get("/api/release/readiness")
        assert response.status_code == 200
        return response.json()

    yield read
    engine.dispose()


def test_readiness_head_is_the_single_alembic_script_head():
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from app.main import migration_head

    revisions, heads = _script_graph()
    # A second head would make startup `upgrade head` ambiguous; merge it before release.
    assert len(heads) == 1, heads
    alembic_head = ScriptDirectory.from_config(Config(str(ROOT / "alembic.ini"))).get_current_head()
    assert migration_head() == alembic_head == heads[0]
    assert len(revisions) > 1


def test_database_at_alembic_head_is_ready(readiness):
    from app.main import migration_head

    payload = readiness()
    assert payload["migration"] == migration_head()
    assert list(payload["checks"]) == CHECK_NAMES
    assert payload["checks"]["migration_head"] is True
    assert all(payload["checks"].values()), payload["checks"]
    assert payload["status"] == "ready"


def test_database_behind_head_is_still_blocked(readiness):
    from app.main import migration_head

    at_head = readiness()["checks"]
    (previous,) = _script_graph()[0][migration_head()]
    payload = readiness(previous)
    assert payload["migration"] == previous
    assert payload["checks"]["migration_head"] is False
    assert payload["status"] == "blocked"
    assert {k: v for k, v in payload["checks"].items() if k != "migration_head"} == \
        {k: v for k, v in at_head.items() if k != "migration_head"}


def test_other_failed_checks_still_block_at_head(readiness, db, sample):
    sample["period"].status = "draft"
    db.commit()
    payload = readiness()
    assert payload["checks"]["migration_head"] is True
    assert payload["checks"]["period_active"] is False
    assert payload["status"] == "blocked"


def test_operations_gate_shows_ready_at_head(readiness, client):
    readiness()
    response = client.get("/operations")
    assert response.status_code == 200
    assert "Yayın Uygunluk Kapısı · READY" in response.text
    assert "✕ migration_head" not in response.text

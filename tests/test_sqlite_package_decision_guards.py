"""S3C-2 B1: the migrated SQLite head keeps M153's package_decisions guards."""
import os,sqlite3,subprocess,sys
import pytest
from tests.test_migration import ROOT

GUARDS=('immutable_package_decisions_delete','immutable_package_decisions_update','package_decision_binding')


def migrate(url,rev):
    run=subprocess.run([sys.executable,'-m','alembic','upgrade',rev],cwd=ROOT,env={**os.environ,'DATABASE_URL':url},capture_output=True,text=True)
    assert run.returncode==0,run.stderr


def guards(c):
    return dict(c.execute("SELECT name,sql FROM sqlite_master WHERE type='trigger' AND tbl_name='package_decisions' AND name IN (?,?,?)",GUARDS).fetchall())


def event(c,eid,action):
    c.execute("""INSERT INTO workflow_events(id,actor_user_id,actor_snapshot_json,organization_id,department_id,event_type,resource_type,resource_id,
        context_json,reason,source,correlation_id) VALUES (?,1,'{}',1,1,?,'directorate_package','1','{}','','manual',?)""",(eid,action,f'corr-{eid}'))


def test_populated_upgrade_to_head_keeps_package_decision_guards(tmp_path):
    path=tmp_path/'guards.db';url=f'sqlite:///{path}'
    migrate(url,'7b90cde04856')  # last revision before the 8ca1 batch rebuild
    c=sqlite3.connect(path)
    with c:
        c.execute("INSERT INTO organizations(id,name) VALUES (1,'Test Belediyesi')")
        c.execute("INSERT INTO departments(id,organization_id,name) VALUES (1,1,'Test Müdürlüğü')")
        c.execute("INSERT INTO reporting_periods(id,year,status,template_status) VALUES (1,2027,'active','verified')")
        c.execute("INSERT INTO users(id,email,full_name,role,password_hash,department_id) VALUES (1,'u@example.invalid','U','department','unused',1)")
        c.execute("""INSERT INTO directorate_packages(id,organization_id,department_id,resource_scope,period_id,source_key,state,version,current_revision)
            VALUES (1,1,1,'performance_program',1,'2027','director_review',1,1)""")
        c.execute("INSERT INTO package_revisions(id,package_id,revision,content_json,sha256,created_by,reason) VALUES (1,1,1,'{}',?,1,'')",('a'*64,))
        event(c,1,'submit_to_director')
        c.execute("""INSERT INTO package_decisions(id,package_revision_id,snapshot_sha256,action,from_state,to_state,workflow_event_id)
            VALUES (1,1,?,'submit_to_director','draft','director_review',1)""",('a'*64,))
    original=guards(c);decision=c.execute('SELECT * FROM package_decisions').fetchall();c.close()
    assert set(original)==set(GUARDS)
    migrate(url,'head')
    c=sqlite3.connect(path)
    try:
        # Exactly M153's definitions, not weaker replacements.
        assert guards(c)==original
        assert c.execute('SELECT * FROM package_decisions').fetchall()==decision
        for sql in ("UPDATE package_decisions SET to_state='returned' WHERE id=1","DELETE FROM package_decisions WHERE id=1"):
            with pytest.raises(sqlite3.DatabaseError,match='Immutable package history'):
                with c:c.execute(sql)
        assert c.execute('SELECT * FROM package_decisions').fetchall()==decision
        with c:event(c,2,'director_approve')
        for sha,action in (('b'*64,'director_approve'),('a'*64,'director_return')):
            with pytest.raises(sqlite3.DatabaseError,match='Decision snapshot/event binding mismatch'):
                with c:c.execute("""INSERT INTO package_decisions(package_revision_id,snapshot_sha256,action,from_state,to_state,workflow_event_id)
                    VALUES (1,?,?,'director_review','strategy_review',2)""",(sha,action))
        # The binding guard is load-bearing, not a blanket refusal: the exact binding inserts.
        with c:c.execute("""INSERT INTO package_decisions(package_revision_id,snapshot_sha256,action,from_state,to_state,workflow_event_id)
            VALUES (1,?,'director_approve','director_review','strategy_review',2)""",('a'*64,))
        assert c.execute('SELECT count(*) FROM package_decisions').fetchone()==(2,)
        # 8ca1's CHECK change itself is kept.
        assert "'strategy_reopen'" in c.execute("SELECT sql FROM sqlite_master WHERE name='package_decisions'").fetchone()[0]
    finally:c.close()


def test_fresh_sqlite_head_has_package_decision_guards(tmp_path):
    path=tmp_path/'fresh.db';migrate(f'sqlite:///{path}','head')
    c=sqlite3.connect(path)
    try:assert set(guards(c))==set(GUARDS)
    finally:c.close()

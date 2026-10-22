"""CIV-079 six-month IC monitoring; preserve all recorded monitoring on downgrade."""
from alembic import op
import sqlalchemy as sa

revision = 'c079a1b2c3d4'
down_revision = 'c074a1b2c3d4'
branch_labels = None
depends_on = None

TABLES = ['ic_monitoring_periods', 'ic_monitoring_batches', 'ic_monitoring_period_events', 'ic_monitoring_events', 'ic_monitoring_notes', 'ic_monitoring_targets', 'ic_monitoring_entries']
POSTGRES_GUARDS = [
    """CREATE FUNCTION civ079_immutable() RETURNS trigger LANGUAGE plpgsql SET search_path FROM CURRENT AS $$
BEGIN RAISE EXCEPTION 'İzleme geçmişi değiştirilemez; gerekçeli yeni sürüm oluşturun.'; END $$""",
    """CREATE FUNCTION civ079_period_guard() RETURNS trigger LANGUAGE plpgsql SET search_path FROM CURRENT AS $$
DECLARE p ic_plans%ROWTYPE;
BEGIN
 IF TG_OP = 'INSERT' THEN
  SELECT * INTO p FROM ic_plans WHERE id=NEW.plan_id FOR UPDATE;
  IF p.status != 'active' OR NEW.year NOT BETWEEN p.start_year AND p.end_year OR NEW.closed_at IS NOT NULL THEN
   RAISE EXCEPTION 'İzleme dönemi etkin plan kapsamında açılmalıdır.';
  END IF;
  RETURN NEW;
 END IF;
 IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'İzleme dönemi silinemez.'; END IF;
 IF OLD.closed_at IS NOT NULL OR NEW.closed_at IS NULL OR
    (to_jsonb(NEW)-'closed_at') IS DISTINCT FROM (to_jsonb(OLD)-'closed_at') OR
    NOT EXISTS (SELECT 1 FROM ic_monitoring_period_events WHERE period_id=OLD.id AND action='close' AND created_at=NEW.closed_at) THEN
  RAISE EXCEPTION 'İzleme dönemi yalnız gerekçeli kapatma olayıyla kapatılır.';
 END IF;
 RETURN NEW;
END $$""",
    """CREATE FUNCTION civ079_event_guard() RETURNS trigger LANGUAGE plpgsql SET search_path FROM CURRENT AS $$
DECLARE b ic_monitoring_batches%ROWTYPE; p ic_monitoring_periods%ROWTYPE;
 prev ic_monitoring_events%ROWTYPE; u users%ROWTYPE; boundary integer; sub ic_monitoring_events%ROWTYPE;
BEGIN
 SELECT * INTO b FROM ic_monitoring_batches WHERE id=NEW.batch_id;
 SELECT * INTO p FROM ic_monitoring_periods WHERE id=b.period_id FOR UPDATE;
 PERFORM 1 FROM ic_monitoring_batches WHERE id=b.id FOR UPDATE;
 IF p.closed_at IS NOT NULL THEN RAISE EXCEPTION 'İzleme dönemi kapalı.'; END IF;
 SELECT * INTO prev FROM ic_monitoring_events WHERE batch_id=b.id ORDER BY revision DESC LIMIT 1;
 IF NEW.revision != COALESCE(prev.revision,0)+1 OR NEW.from_status != COALESCE(prev.to_status,'draft') THEN
  RAISE EXCEPTION 'İzleme revizyonu değişti; ekranı yenileyin.';
 END IF;
 SELECT * INTO u FROM users WHERE id=NEW.actor_id;
 IF NOT u.is_active THEN RAISE EXCEPTION 'Etkin kullanıcı gerekli.'; END IF;
 IF NEW.action IN ('save','submit') THEN
  IF (clock_timestamp() AT TIME ZONE 'Europe/Istanbul')::date > p.deadline THEN
   RAISE EXCEPTION 'İzleme giriş süresi doldu.';
  END IF;
  IF (b.department_id IS NOT NULL AND (u.role != 'department' OR u.department_id IS DISTINCT FROM b.department_id)) OR
     (b.department_id IS NULL AND u.role != 'strategy') THEN RAISE EXCEPTION 'Sorumlu birim yetkisi gerekli.'; END IF;
  IF NEW.action='submit' AND u.position != 'director' AND NOT u.can_submit THEN RAISE EXCEPTION 'Gönderim yetkisi gerekli.'; END IF;
 ELSE
  IF u.role != 'strategy' OR u.position != 'director' OR u.department_id IS NULL THEN
   RAISE EXCEPTION 'Strateji Müdürü yetkisi gerekli.';
  END IF;
 END IF;
 IF NEW.action='approve' THEN
  SELECT COALESCE(max(revision),0) INTO boundary FROM ic_monitoring_events WHERE batch_id=b.id AND action IN ('return','reopen');
  IF EXISTS (SELECT 1 FROM ic_monitoring_events WHERE batch_id=b.id AND revision>boundary AND actor_id=u.id AND action IN ('save','submit')) THEN
   RAISE EXCEPTION 'Görevler ayrılığı: veriyi giren veya gönderen onaylayamaz.';
  END IF;
  SELECT * INTO sub FROM ic_monitoring_events WHERE batch_id=b.id AND action='submit' ORDER BY revision DESC LIMIT 1;
  IF NEW.snapshot_json::jsonb IS DISTINCT FROM sub.snapshot_json::jsonb THEN RAISE EXCEPTION 'Onay gönderilen içeriği korumalıdır.'; END IF;
 END IF;
 IF NEW.action IN ('submit','approve') THEN
  IF jsonb_array_length(NEW.snapshot_json::jsonb) != (SELECT count(*) FROM ic_monitoring_targets WHERE batch_id=b.id) OR
   EXISTS (SELECT 1 FROM ic_monitoring_targets t WHERE t.batch_id=b.id AND NOT EXISTS (
    SELECT 1 FROM jsonb_array_elements(NEW.snapshot_json::jsonb) s
    JOIN ic_monitoring_entries e ON e.id=(s->>'entry_id')::integer
    WHERE e.target_id=t.id AND (s->>'target_id')::integer=t.id
    AND e.id=(SELECT max(id) FROM ic_monitoring_entries WHERE target_id=t.id))) THEN
   RAISE EXCEPTION 'İzleme girişleri eksik veya anlık görüntü geçersiz.';
  END IF;
 END IF;
 RETURN NEW;
END $$""",
    """CREATE FUNCTION civ079_entry_guard() RETURNS trigger LANGUAGE plpgsql SET search_path FROM CURRENT AS $$
DECLARE t ic_monitoring_targets%ROWTYPE; b ic_monitoring_batches%ROWTYPE;
 e ic_monitoring_events%ROWTYPE; a ic_actions%ROWTYPE; p ic_monitoring_periods%ROWTYPE;
BEGIN
 SELECT * INTO t FROM ic_monitoring_targets WHERE id=NEW.target_id;
 SELECT * INTO b FROM ic_monitoring_batches WHERE id=t.batch_id;
 SELECT * INTO p FROM ic_monitoring_periods WHERE id=b.period_id FOR UPDATE;
 PERFORM 1 FROM ic_monitoring_batches WHERE id=b.id FOR UPDATE;
 SELECT * INTO e FROM ic_monitoring_events WHERE batch_id=b.id ORDER BY revision DESC LIMIT 1;
 IF p.closed_at IS NOT NULL OR e.id IS DISTINCT FROM NEW.event_id OR e.action != 'save' OR e.to_status NOT IN ('draft','returned') THEN
  RAISE EXCEPTION 'Onaylı veya gönderilmiş izleme değiştirilemez.';
 END IF;
 SELECT * INTO a FROM ic_actions WHERE id=t.action_id;
 IF NEW.status != 'completed' AND a.due_date < (clock_timestamp() AT TIME ZONE 'Europe/Istanbul')::date AND length(trim(NEW.reason))=0 THEN
  RAISE EXCEPTION 'Süresi geçen eylem için tamamlanmama nedeni gerekli.';
 END IF;
 RETURN NEW;
END $$""",
    """CREATE FUNCTION civ079_note_guard() RETURNS trigger LANGUAGE plpgsql SET search_path FROM CURRENT AS $$
DECLARE p ic_monitoring_periods%ROWTYPE; u users%ROWTYPE;
BEGIN
 SELECT * INTO p FROM ic_monitoring_periods WHERE id=NEW.period_id FOR UPDATE;
 SELECT * INTO u FROM users WHERE id=NEW.actor_id;
 IF p.closed_at IS NOT NULL OR (clock_timestamp() AT TIME ZONE 'Europe/Istanbul')::date > p.deadline OR
   u.role != 'department' OR NOT u.is_active OR u.department_id IS DISTINCT FROM NEW.department_id OR
   NOT EXISTS (SELECT 1 FROM ic_actions a JOIN ic_action_parties ap ON ap.action_id=a.id
    WHERE a.id=NEW.action_id AND a.plan_id=p.plan_id AND ap.role='cooperating'
    AND (ap.department_id=NEW.department_id OR ap.all_departments)) THEN
  RAISE EXCEPTION 'Katkı notu için açık dönem ve işbirliği yetkisi gerekli.';
 END IF;
 RETURN NEW;
END $$""",
    """CREATE FUNCTION civ079_period_event_guard() RETURNS trigger LANGUAGE plpgsql SET search_path FROM CURRENT AS $$
DECLARE p ic_monitoring_periods%ROWTYPE;
BEGIN
 SELECT * INTO p FROM ic_monitoring_periods WHERE id=NEW.period_id FOR UPDATE;
 IF p.closed_at IS NOT NULL OR (NEW.action='close' AND length(trim(NEW.reason))=0) OR
  NOT EXISTS (SELECT 1 FROM users WHERE id=NEW.actor_id AND is_active AND role='strategy') THEN
  RAISE EXCEPTION 'Açık dönem, Strateji yetkisi ve kapatmada gerekçe gerekli.';
 END IF;
 RETURN NEW;
END $$""",
    """CREATE FUNCTION civ079_target_guard() RETURNS trigger LANGUAGE plpgsql SET search_path FROM CURRENT AS $$
DECLARE b ic_monitoring_batches%ROWTYPE; p ic_monitoring_periods%ROWTYPE;
BEGIN
 SELECT * INTO b FROM ic_monitoring_batches WHERE id=NEW.batch_id;
 SELECT * INTO p FROM ic_monitoring_periods WHERE id=b.period_id FOR UPDATE;
 IF p.closed_at IS NOT NULL OR EXISTS (SELECT 1 FROM ic_monitoring_events WHERE batch_id=b.id) OR
  NOT EXISTS (SELECT 1 FROM ic_actions a JOIN ic_action_parties ap ON ap.action_id=a.id
   WHERE a.id=NEW.action_id AND a.plan_id=p.plan_id AND ap.role='responsible' AND
    ((b.department_id IS NOT NULL AND (ap.department_id=b.department_id OR ap.all_departments)) OR
     (b.department_id IS NULL AND ap.body_name=b.body_name))) THEN
  RAISE EXCEPTION 'Eylem dönem ve sorumlu birim kapsamına ait olmalıdır.';
 END IF;
 RETURN NEW;
END $$""",
    """CREATE TRIGGER civ079_immutable BEFORE UPDATE OR DELETE ON ic_monitoring_period_events FOR EACH ROW EXECUTE FUNCTION civ079_immutable()""",
    """CREATE TRIGGER civ079_truncate BEFORE TRUNCATE ON ic_monitoring_period_events FOR EACH STATEMENT EXECUTE FUNCTION civ079_immutable()""",
    """CREATE TRIGGER civ079_immutable BEFORE UPDATE OR DELETE ON ic_monitoring_batches FOR EACH ROW EXECUTE FUNCTION civ079_immutable()""",
    """CREATE TRIGGER civ079_truncate BEFORE TRUNCATE ON ic_monitoring_batches FOR EACH STATEMENT EXECUTE FUNCTION civ079_immutable()""",
    """CREATE TRIGGER civ079_immutable BEFORE UPDATE OR DELETE ON ic_monitoring_targets FOR EACH ROW EXECUTE FUNCTION civ079_immutable()""",
    """CREATE TRIGGER civ079_truncate BEFORE TRUNCATE ON ic_monitoring_targets FOR EACH STATEMENT EXECUTE FUNCTION civ079_immutable()""",
    """CREATE TRIGGER civ079_immutable BEFORE UPDATE OR DELETE ON ic_monitoring_events FOR EACH ROW EXECUTE FUNCTION civ079_immutable()""",
    """CREATE TRIGGER civ079_truncate BEFORE TRUNCATE ON ic_monitoring_events FOR EACH STATEMENT EXECUTE FUNCTION civ079_immutable()""",
    """CREATE TRIGGER civ079_immutable BEFORE UPDATE OR DELETE ON ic_monitoring_entries FOR EACH ROW EXECUTE FUNCTION civ079_immutable()""",
    """CREATE TRIGGER civ079_truncate BEFORE TRUNCATE ON ic_monitoring_entries FOR EACH STATEMENT EXECUTE FUNCTION civ079_immutable()""",
    """CREATE TRIGGER civ079_immutable BEFORE UPDATE OR DELETE ON ic_monitoring_notes FOR EACH ROW EXECUTE FUNCTION civ079_immutable()""",
    """CREATE TRIGGER civ079_truncate BEFORE TRUNCATE ON ic_monitoring_notes FOR EACH STATEMENT EXECUTE FUNCTION civ079_immutable()""",
    """CREATE TRIGGER civ079_period BEFORE INSERT OR UPDATE OR DELETE ON ic_monitoring_periods FOR EACH ROW EXECUTE FUNCTION civ079_period_guard()""",
    """CREATE TRIGGER civ079_truncate BEFORE TRUNCATE ON ic_monitoring_periods FOR EACH STATEMENT EXECUTE FUNCTION civ079_immutable()""",
    """CREATE TRIGGER civ079_insert BEFORE INSERT ON ic_monitoring_events FOR EACH ROW EXECUTE FUNCTION civ079_event_guard()""",
    """CREATE TRIGGER civ079_insert BEFORE INSERT ON ic_monitoring_entries FOR EACH ROW EXECUTE FUNCTION civ079_entry_guard()""",
    """CREATE TRIGGER civ079_insert BEFORE INSERT ON ic_monitoring_notes FOR EACH ROW EXECUTE FUNCTION civ079_note_guard()""",
    """CREATE TRIGGER civ079_insert BEFORE INSERT ON ic_monitoring_period_events FOR EACH ROW EXECUTE FUNCTION civ079_period_event_guard()""",
    """CREATE TRIGGER civ079_insert BEFORE INSERT ON ic_monitoring_targets FOR EACH ROW EXECUTE FUNCTION civ079_target_guard()"""
]

def upgrade():
    op.create_table('ic_monitoring_periods',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('plan_id', sa.Integer(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=False),
    sa.Column('half', sa.Integer(), nullable=False),
    sa.Column('deadline', sa.Date(), nullable=False),
    sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint('half IN (1,2) AND year BETWEEN 1900 AND 2200', name='ck_ic_monitoring_period'),
    sa.ForeignKeyConstraint(['plan_id'], ['ic_plans.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('plan_id', 'year', 'half', name='uq_ic_monitoring_period')
    )
    op.create_index('uq_ic_monitoring_open', 'ic_monitoring_periods', ['plan_id'], unique=True, postgresql_where=sa.text('closed_at IS NULL'), sqlite_where=sa.text('closed_at IS NULL'))
    op.create_table('ic_monitoring_batches',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('period_id', sa.Integer(), nullable=False),
    sa.Column('scope_key', sa.Text(), nullable=False),
    sa.Column('department_id', sa.Integer(), nullable=True),
    sa.Column('body_name', sa.Text(), nullable=True),
    sa.Column('label', sa.Text(), nullable=False),
    sa.CheckConstraint('(department_id IS NOT NULL AND body_name IS NULL) OR (department_id IS NULL AND body_name IS NOT NULL)', name='ck_ic_monitoring_owner'),
    sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
    sa.ForeignKeyConstraint(['period_id'], ['ic_monitoring_periods.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('period_id', 'scope_key')
    )
    op.create_index(op.f('ix_ic_monitoring_batches_period_id'), 'ic_monitoring_batches', ['period_id'], unique=False)
    op.create_table('ic_monitoring_period_events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('period_id', sa.Integer(), nullable=False),
    sa.Column('action', sa.String(length=10), nullable=False),
    sa.Column('actor_id', sa.Integer(), nullable=False),
    sa.Column('actor_name', sa.Text(), nullable=False),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.CheckConstraint("action IN ('open','close')", name='ck_ic_monitoring_period_event'),
    sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['period_id'], ['ic_monitoring_periods.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('period_id', 'action')
    )
    op.create_table('ic_monitoring_events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('batch_id', sa.Integer(), nullable=False),
    sa.Column('revision', sa.Integer(), nullable=False),
    sa.Column('action', sa.String(length=10), nullable=False),
    sa.Column('from_status', sa.String(length=12), nullable=False),
    sa.Column('to_status', sa.String(length=12), nullable=False),
    sa.Column('actor_id', sa.Integer(), nullable=False),
    sa.Column('actor_name', sa.Text(), nullable=False),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.Column('snapshot_json', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.CheckConstraint("(action='save' AND from_status IN ('draft','returned') AND to_status=from_status) OR (action='submit' AND from_status IN ('draft','returned') AND to_status='submitted') OR (action='return' AND from_status='submitted' AND to_status='returned') OR (action='approve' AND from_status='submitted' AND to_status='approved') OR (action='reopen' AND from_status='approved' AND to_status='draft')", name='ck_ic_monitoring_transition'),
    sa.CheckConstraint("action NOT IN ('return','reopen') OR length(trim(reason)) > 0", name='ck_ic_monitoring_reason'),
    sa.CheckConstraint('revision > 0', name='ck_ic_monitoring_revision'),
    sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['batch_id'], ['ic_monitoring_batches.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('batch_id', 'revision')
    )
    op.create_index(op.f('ix_ic_monitoring_events_batch_id'), 'ic_monitoring_events', ['batch_id'], unique=False)
    op.create_table('ic_monitoring_notes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('period_id', sa.Integer(), nullable=False),
    sa.Column('action_id', sa.Integer(), nullable=False),
    sa.Column('department_id', sa.Integer(), nullable=False),
    sa.Column('actor_id', sa.Integer(), nullable=False),
    sa.Column('actor_name', sa.Text(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.CheckConstraint('length(trim(content)) BETWEEN 1 AND 2000', name='ck_ic_monitoring_note'),
    sa.ForeignKeyConstraint(['action_id'], ['ic_actions.id'], ),
    sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
    sa.ForeignKeyConstraint(['period_id'], ['ic_monitoring_periods.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ic_monitoring_notes_period_id'), 'ic_monitoring_notes', ['period_id'], unique=False)
    op.create_table('ic_monitoring_targets',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('batch_id', sa.Integer(), nullable=False),
    sa.Column('action_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['action_id'], ['ic_actions.id'], ),
    sa.ForeignKeyConstraint(['batch_id'], ['ic_monitoring_batches.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('batch_id', 'action_id')
    )
    op.create_index(op.f('ix_ic_monitoring_targets_batch_id'), 'ic_monitoring_targets', ['batch_id'], unique=False)
    op.create_table('ic_monitoring_entries',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('target_id', sa.Integer(), nullable=False),
    sa.Column('event_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=15), nullable=False),
    sa.Column('percentage', sa.Integer(), nullable=True),
    sa.Column('explanation', sa.Text(), nullable=False),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.Column('evidence', sa.Text(), nullable=False),
    sa.CheckConstraint("(percentage BETWEEN 0 AND 100) AND (percentage IS NOT NULL OR status='not_started')", name='ck_ic_monitoring_percentage'),
    sa.CheckConstraint("status != 'delayed' OR length(trim(reason)) > 0", name='ck_ic_monitoring_delay_reason'),
    sa.CheckConstraint("status IN ('completed','ongoing','not_started','delayed')", name='ck_ic_monitoring_entry_status'),
    sa.ForeignKeyConstraint(['event_id'], ['ic_monitoring_events.id'], ),
    sa.ForeignKeyConstraint(['target_id'], ['ic_monitoring_targets.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('event_id')
    )
    op.create_index(op.f('ix_ic_monitoring_entries_target_id'), 'ic_monitoring_entries', ['target_id'], unique=False)
    if op.get_bind().dialect.name == 'postgresql':
        for statement in POSTGRES_GUARDS:
            op.execute(statement)
    else:
        for table in TABLES:
            for action in ('UPDATE', 'DELETE'):
                if table == 'ic_monitoring_periods' and action == 'UPDATE':
                    continue
                op.execute(f"CREATE TRIGGER civ079_{table}_{action.lower()} BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT, 'İzleme geçmişi değiştirilemez.'); END")


def downgrade():
    if op.get_bind().dialect.name == 'postgresql':
        op.execute('LOCK TABLE ' + ', '.join(TABLES) + ' IN ACCESS EXCLUSIVE MODE')
    for table in TABLES:
        if op.get_bind().execute(sa.text('SELECT 1 FROM ' + table + ' LIMIT 1')).first():
            raise RuntimeError('İzleme verisi var. Veriyi koruyan geçiş hazırlanmadan sürüm düşürülemez.')
    for table in reversed(TABLES):
        op.drop_table(table)
    if op.get_bind().dialect.name == 'postgresql':
        for name in ('immutable', 'period_guard', 'event_guard', 'entry_guard', 'note_guard', 'period_event_guard', 'target_guard'):
            op.execute('DROP FUNCTION civ079_' + name + '()')

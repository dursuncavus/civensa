"""CIV-085 immutable questionnaire lists, participants and answer revisions."""
from alembic import op
import sqlalchemy as sa

revision = 'c085a1b2c3d4'
down_revision = 'c086a1b2c3d4'
branch_labels = None
depends_on = None

# Frozen DDL and guards: independent of subsequent application model changes.
DDL = {
'postgresql': [
r"""CREATE TABLE ic_question_lists (
	id SERIAL NOT NULL,
	name TEXT NOT NULL,
	questions_json TEXT NOT NULL,
	actor_id INTEGER NOT NULL,
	actor_name TEXT NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT ck_ic_question_list_name CHECK (length(trim(name)) BETWEEN 1 AND 200),
	FOREIGN KEY(actor_id) REFERENCES users (id)
)""",
r"""CREATE TABLE ic_question_attachments (
	id SERIAL NOT NULL,
	period_id INTEGER NOT NULL,
	list_id INTEGER NOT NULL,
	revision INTEGER NOT NULL,
	departments_json TEXT NOT NULL,
	actor_id INTEGER NOT NULL,
	actor_name TEXT NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (period_id, revision),
	CONSTRAINT ck_ic_question_attachment_revision CHECK (revision > 0),
	FOREIGN KEY(period_id) REFERENCES ic_monitoring_periods (id),
	FOREIGN KEY(list_id) REFERENCES ic_question_lists (id),
	FOREIGN KEY(actor_id) REFERENCES users (id)
)""",
r"""CREATE TABLE ic_question_batches (
	id SERIAL NOT NULL,
	period_id INTEGER NOT NULL,
	department_id INTEGER NOT NULL,
	label TEXT NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (period_id, department_id),
	FOREIGN KEY(period_id) REFERENCES ic_monitoring_periods (id),
	FOREIGN KEY(department_id) REFERENCES departments (id)
)""",
r"""CREATE TABLE ic_question_events (
	id SERIAL NOT NULL,
	batch_id INTEGER NOT NULL,
	revision INTEGER NOT NULL,
	action TEXT NOT NULL,
	from_status TEXT NOT NULL,
	to_status TEXT NOT NULL,
	actor_id INTEGER NOT NULL,
	actor_name TEXT NOT NULL,
	reason TEXT NOT NULL,
	snapshot_json TEXT NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (batch_id, revision),
	CONSTRAINT ck_ic_question_revision CHECK (revision > 0),
	CONSTRAINT ck_ic_question_transition CHECK ((action='save' AND from_status IN ('draft','returned') AND to_status=from_status) OR (action='submit' AND from_status IN ('draft','returned') AND to_status='submitted') OR (action='return' AND from_status='submitted' AND to_status='returned') OR (action='approve' AND from_status='submitted' AND to_status='approved') OR (action='reopen' AND from_status='approved' AND to_status='draft')),
	CONSTRAINT ck_ic_question_reason CHECK (action NOT IN ('return','reopen') OR length(trim(reason)) > 0),
	FOREIGN KEY(batch_id) REFERENCES ic_question_batches (id),
	FOREIGN KEY(actor_id) REFERENCES users (id)
)""",
r"""CREATE INDEX ix_ic_question_attachments_period_id ON ic_question_attachments (period_id)""",
r"""CREATE INDEX ix_ic_question_batches_period_id ON ic_question_batches (period_id)""",
r"""CREATE INDEX ix_ic_question_events_batch_id ON ic_question_events (batch_id)"""
],
'sqlite': [
r"""CREATE TABLE ic_question_lists (
	id INTEGER NOT NULL,
	name TEXT NOT NULL,
	questions_json TEXT NOT NULL,
	actor_id INTEGER NOT NULL,
	actor_name TEXT NOT NULL,
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT ck_ic_question_list_name CHECK (length(trim(name)) BETWEEN 1 AND 200),
	FOREIGN KEY(actor_id) REFERENCES users (id)
)""",
r"""CREATE TABLE ic_question_attachments (
	id INTEGER NOT NULL,
	period_id INTEGER NOT NULL,
	list_id INTEGER NOT NULL,
	revision INTEGER NOT NULL,
	departments_json TEXT NOT NULL,
	actor_id INTEGER NOT NULL,
	actor_name TEXT NOT NULL,
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (period_id, revision),
	CONSTRAINT ck_ic_question_attachment_revision CHECK (revision > 0),
	FOREIGN KEY(period_id) REFERENCES ic_monitoring_periods (id),
	FOREIGN KEY(list_id) REFERENCES ic_question_lists (id),
	FOREIGN KEY(actor_id) REFERENCES users (id)
)""",
r"""CREATE TABLE ic_question_batches (
	id INTEGER NOT NULL,
	period_id INTEGER NOT NULL,
	department_id INTEGER NOT NULL,
	label TEXT NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (period_id, department_id),
	FOREIGN KEY(period_id) REFERENCES ic_monitoring_periods (id),
	FOREIGN KEY(department_id) REFERENCES departments (id)
)""",
r"""CREATE TABLE ic_question_events (
	id INTEGER NOT NULL,
	batch_id INTEGER NOT NULL,
	revision INTEGER NOT NULL,
	action TEXT NOT NULL,
	from_status TEXT NOT NULL,
	to_status TEXT NOT NULL,
	actor_id INTEGER NOT NULL,
	actor_name TEXT NOT NULL,
	reason TEXT NOT NULL,
	snapshot_json TEXT NOT NULL,
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (batch_id, revision),
	CONSTRAINT ck_ic_question_revision CHECK (revision > 0),
	CONSTRAINT ck_ic_question_transition CHECK ((action='save' AND from_status IN ('draft','returned') AND to_status=from_status) OR (action='submit' AND from_status IN ('draft','returned') AND to_status='submitted') OR (action='return' AND from_status='submitted' AND to_status='returned') OR (action='approve' AND from_status='submitted' AND to_status='approved') OR (action='reopen' AND from_status='approved' AND to_status='draft')),
	CONSTRAINT ck_ic_question_reason CHECK (action NOT IN ('return','reopen') OR length(trim(reason)) > 0),
	FOREIGN KEY(batch_id) REFERENCES ic_question_batches (id),
	FOREIGN KEY(actor_id) REFERENCES users (id)
)""",
r"""CREATE INDEX ix_ic_question_attachments_period_id ON ic_question_attachments (period_id)""",
r"""CREATE INDEX ix_ic_question_batches_period_id ON ic_question_batches (period_id)""",
r"""CREATE INDEX ix_ic_question_events_batch_id ON ic_question_events (batch_id)"""
]
}

GUARDS = [
r"""CREATE FUNCTION civ085_immutable() RETURNS trigger LANGUAGE plpgsql SET search_path FROM CURRENT AS $$
BEGIN RAISE EXCEPTION 'Soru formu geçmişi değiştirilemez; yeni sürüm oluşturun.'; END $$""",
r"""CREATE FUNCTION civ085_list_guard() RETURNS trigger LANGUAGE plpgsql SET search_path FROM CURRENT AS $$
DECLARE qs jsonb;
BEGIN
 IF NOT EXISTS (SELECT 1 FROM users WHERE id=NEW.actor_id AND is_active AND role='strategy') THEN
  RAISE EXCEPTION 'Soru yüklemek için Strateji yetkisi gerekli.';
 END IF;
 qs := NEW.questions_json::jsonb;
 IF jsonb_typeof(qs) != 'array' OR jsonb_array_length(qs) NOT BETWEEN 1 AND 200 OR
    EXISTS (SELECT 1 FROM jsonb_array_elements(qs) q WHERE
       COALESCE(length(trim(q->>'question')),0) NOT BETWEEN 1 AND 10000 OR
       COALESCE(length(trim(q->>'code')),0) NOT BETWEEN 1 AND 60 OR
       COALESCE(q->>'component','') NOT IN ('KOS','RDS','KFS','BİS','İS') OR
       COALESCE((q->>'order')::integer,0) < 1) OR
    (SELECT count(DISTINCT lower(q->>'code')) FROM jsonb_array_elements(qs) q) != jsonb_array_length(qs) OR
    (SELECT count(DISTINCT q->>'order') FROM jsonb_array_elements(qs) q) != jsonb_array_length(qs) THEN
  RAISE EXCEPTION 'Soru listesi geçersiz; sıra, kod, bileşen ve soru alanlarını düzeltin.';
 END IF;
 RETURN NEW;
END $$""",
r"""CREATE FUNCTION civ085_attachment_guard() RETURNS trigger LANGUAGE plpgsql SET search_path FROM CURRENT AS $$
DECLARE p ic_monitoring_periods%ROWTYPE; prev ic_question_attachments%ROWTYPE; ids jsonb;
BEGIN
 SELECT * INTO p FROM ic_monitoring_periods WHERE id=NEW.period_id FOR UPDATE;
 SELECT * INTO prev FROM ic_question_attachments WHERE period_id=p.id ORDER BY revision DESC LIMIT 1;
 IF p.closed_at IS NOT NULL OR NOT EXISTS (SELECT 1 FROM users WHERE id=NEW.actor_id AND is_active AND role='strategy' AND position='director' AND department_id IS NOT NULL) THEN
  RAISE EXCEPTION 'Soru bağlamak için açık dönem ve Strateji Müdürü yetkisi gerekli.';
 END IF;
 IF NEW.revision != COALESCE(prev.revision,0)+1 THEN RAISE EXCEPTION 'Soru bağlantısı değişti; ekranı yenileyin.'; END IF;
 ids := NEW.departments_json::jsonb;
 IF jsonb_typeof(ids) != 'array' OR jsonb_array_length(ids)=0 OR
    (SELECT count(DISTINCT v) FROM jsonb_array_elements(ids) v) != jsonb_array_length(ids) OR
    EXISTS (SELECT 1 FROM jsonb_array_elements_text(ids) v WHERE NOT EXISTS
      (SELECT 1 FROM departments d WHERE d.id=v::integer AND (d.is_active OR COALESCE(prev.departments_json::jsonb,'[]') @> jsonb_build_array(d.id)))) THEN
  RAISE EXCEPTION 'Katılımcı birimleri etkin müdürlüklerden seçin.';
 END IF;
 IF EXISTS (SELECT 1 FROM ic_question_events e JOIN ic_question_batches b ON b.id=e.batch_id WHERE b.period_id=p.id AND e.action='save') AND
    (NEW.list_id != prev.list_id OR NOT ids @> prev.departments_json::jsonb) THEN
  RAISE EXCEPTION 'Yanıt kaydedildi; soru listesi ve katılımcılar korunmalıdır. Yalnız müdürlük ekleyin.';
 END IF;
 RETURN NEW;
END $$""",
r"""CREATE FUNCTION civ085_batch_guard() RETURNS trigger LANGUAGE plpgsql SET search_path FROM CURRENT AS $$
DECLARE p ic_monitoring_periods%ROWTYPE; a ic_question_attachments%ROWTYPE;
BEGIN
 SELECT * INTO p FROM ic_monitoring_periods WHERE id=NEW.period_id FOR UPDATE;
 SELECT * INTO a FROM ic_question_attachments WHERE period_id=p.id ORDER BY revision DESC LIMIT 1;
 IF p.closed_at IS NOT NULL OR a.id IS NULL OR NOT a.departments_json::jsonb @> jsonb_build_array(NEW.department_id) THEN
  RAISE EXCEPTION 'Soru paketi açık dönemin katılımcı müdürlüğüne ait olmalıdır.';
 END IF;
 RETURN NEW;
END $$""",
r"""CREATE FUNCTION civ085_event_guard() RETURNS trigger LANGUAGE plpgsql SET search_path FROM CURRENT AS $$
DECLARE b ic_question_batches%ROWTYPE; p ic_monitoring_periods%ROWTYPE;
 prev ic_question_events%ROWTYPE; u users%ROWTYPE; a ic_question_attachments%ROWTYPE;
 qs jsonb; answers jsonb; boundary integer;
BEGIN
 SELECT * INTO b FROM ic_question_batches WHERE id=NEW.batch_id;
 SELECT * INTO p FROM ic_monitoring_periods WHERE id=b.period_id FOR UPDATE;
 PERFORM 1 FROM ic_question_batches WHERE id=b.id FOR UPDATE;
 SELECT * INTO a FROM ic_question_attachments WHERE period_id=p.id ORDER BY revision DESC LIMIT 1;
 SELECT * INTO prev FROM ic_question_events WHERE batch_id=b.id ORDER BY revision DESC LIMIT 1;
 SELECT * INTO u FROM users WHERE id=NEW.actor_id;
 IF p.closed_at IS NOT NULL OR NOT a.departments_json::jsonb @> jsonb_build_array(b.department_id) THEN
  RAISE EXCEPTION 'Soru dönemi kapalı veya müdürlük katılımcı değil.';
 END IF;
 IF NEW.revision != COALESCE(prev.revision,0)+1 OR NEW.from_status != COALESCE(prev.to_status,'draft') THEN
  RAISE EXCEPTION 'Soru formu revizyonu değişti; ekranı yenileyin.';
 END IF;
 IF NOT u.is_active THEN RAISE EXCEPTION 'Etkin kullanıcı gerekli.'; END IF;
 IF NEW.action IN ('save','submit') THEN
  IF u.role != 'department' OR u.department_id IS DISTINCT FROM b.department_id THEN
   RAISE EXCEPTION 'Soru formunu yalnız sorumlu müdürlük doldurup gönderebilir.';
  END IF;
  IF (clock_timestamp() AT TIME ZONE 'Europe/Istanbul')::date > p.deadline THEN
   RAISE EXCEPTION 'İzleme giriş süresi doldu; Strateji ile görüşün.';
  END IF;
  IF NEW.action='submit' AND u.position != 'director' AND NOT u.can_submit THEN RAISE EXCEPTION 'Gönderim yetkisi gerekli.'; END IF;
 ELSE
  IF u.role != 'strategy' OR u.position != 'director' OR u.department_id IS NULL THEN
   RAISE EXCEPTION 'Strateji Müdürü yetkisi gerekli.';
  END IF;
 END IF;
 SELECT questions_json::jsonb INTO qs FROM ic_question_lists WHERE id=a.list_id;
 answers := NEW.snapshot_json::jsonb;
 IF jsonb_typeof(answers) != 'array' OR jsonb_array_length(answers) != jsonb_array_length(qs) OR
    (SELECT count(DISTINCT r->>'code') FROM jsonb_array_elements(answers) r) != jsonb_array_length(qs) OR
    EXISTS (SELECT 1 FROM jsonb_array_elements(answers) r WHERE
      NOT EXISTS (SELECT 1 FROM jsonb_array_elements(qs) q WHERE q->>'code'=r->>'code') OR
      NOT r ? 'answer' OR NOT r ? 'explanation' OR
      (r->>'answer' IS NOT NULL AND r->>'answer' NOT IN ('yes','no','developing')) OR
      jsonb_typeof(r->'explanation') != 'string' OR length(r->>'explanation') > 1000) THEN
  RAISE EXCEPTION 'Soru yanıtları geçersiz; soru kodlarını ve açıklamaları kontrol edin.';
 END IF;
 IF NEW.action IN ('submit','approve') AND EXISTS (SELECT 1 FROM jsonb_array_elements(answers) r WHERE r->>'answer' IS NULL) THEN
  RAISE EXCEPTION 'Eksik soru yanıtlarını tamamlayıp yeniden gönderin.';
 END IF;
 IF NEW.action != 'save' AND answers IS DISTINCT FROM COALESCE(prev.snapshot_json::jsonb,'[]') THEN
  RAISE EXCEPTION 'İnceleme kararı gönderilen yanıtları korumalıdır.';
 END IF;
 IF NEW.action='approve' THEN
  SELECT COALESCE(max(revision),0) INTO boundary FROM ic_question_events WHERE batch_id=b.id AND action IN ('return','reopen');
  IF EXISTS (SELECT 1 FROM ic_question_events WHERE batch_id=b.id AND revision>boundary AND actor_id=u.id AND action='save') THEN
   RAISE EXCEPTION 'Görevler ayrılığı: veriyi giren veya değiştiren onaylayamaz.';
  END IF;
 END IF;
 RETURN NEW;
END $$""",
r"""CREATE TRIGGER civ085_immutable BEFORE UPDATE OR DELETE ON ic_question_lists FOR EACH ROW EXECUTE FUNCTION civ085_immutable()""",
r"""CREATE TRIGGER civ085_truncate BEFORE TRUNCATE ON ic_question_lists FOR EACH STATEMENT EXECUTE FUNCTION civ085_immutable()""",
r"""CREATE TRIGGER civ085_immutable BEFORE UPDATE OR DELETE ON ic_question_attachments FOR EACH ROW EXECUTE FUNCTION civ085_immutable()""",
r"""CREATE TRIGGER civ085_truncate BEFORE TRUNCATE ON ic_question_attachments FOR EACH STATEMENT EXECUTE FUNCTION civ085_immutable()""",
r"""CREATE TRIGGER civ085_immutable BEFORE UPDATE OR DELETE ON ic_question_batches FOR EACH ROW EXECUTE FUNCTION civ085_immutable()""",
r"""CREATE TRIGGER civ085_truncate BEFORE TRUNCATE ON ic_question_batches FOR EACH STATEMENT EXECUTE FUNCTION civ085_immutable()""",
r"""CREATE TRIGGER civ085_immutable BEFORE UPDATE OR DELETE ON ic_question_events FOR EACH ROW EXECUTE FUNCTION civ085_immutable()""",
r"""CREATE TRIGGER civ085_truncate BEFORE TRUNCATE ON ic_question_events FOR EACH STATEMENT EXECUTE FUNCTION civ085_immutable()""",
r"""CREATE TRIGGER civ085_insert BEFORE INSERT ON ic_question_lists FOR EACH ROW EXECUTE FUNCTION civ085_list_guard()""",
r"""CREATE TRIGGER civ085_insert BEFORE INSERT ON ic_question_attachments FOR EACH ROW EXECUTE FUNCTION civ085_attachment_guard()""",
r"""CREATE TRIGGER civ085_insert BEFORE INSERT ON ic_question_batches FOR EACH ROW EXECUTE FUNCTION civ085_batch_guard()""",
r"""CREATE TRIGGER civ085_insert BEFORE INSERT ON ic_question_events FOR EACH ROW EXECUTE FUNCTION civ085_event_guard()"""
]

TABLES = ('ic_question_lists', 'ic_question_attachments', 'ic_question_batches', 'ic_question_events')


def upgrade():
    dialect = op.get_bind().dialect.name
    for statement in DDL['postgresql' if dialect == 'postgresql' else 'sqlite']:
        op.execute(statement)
    if dialect == 'postgresql':
        for statement in GUARDS:
            op.execute(sa.text(statement))


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute('LOCK TABLE ' + ', '.join(TABLES) + ' IN ACCESS EXCLUSIVE MODE')
    for table in TABLES:
        if bind.execute(sa.text('SELECT EXISTS (SELECT 1 FROM ' + table + ')')).scalar():
            raise RuntimeError('Soru formu verisi var. Veriyi koruyan geçiş hazırlanmadan sürüm düşürülemez.')
    for table in reversed(TABLES):
        op.drop_table(table)
    if bind.dialect.name == 'postgresql':
        for name in ('event_guard', 'batch_guard', 'attachment_guard', 'list_guard', 'immutable'):
            op.execute('DROP FUNCTION civ085_' + name + '()')

"""CIV-160 immutable monitoring period narrative revisions."""
from alembic import op
import sqlalchemy as sa

revision = 'c160a1b2c3d4'
down_revision = 'c085a1b2c3d4'
branch_labels = None
depends_on = None

# Frozen DDL and guards, independent of application code.
DDL = {
'postgresql': [
r"""CREATE TABLE ic_narrative_events (
	id SERIAL NOT NULL,
	period_id INTEGER NOT NULL,
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
	UNIQUE (period_id, revision),
	CONSTRAINT ck_ic_narrative_revision CHECK (revision > 0),
	CONSTRAINT ck_ic_narrative_transition CHECK ((action='save' AND from_status IN ('draft','returned') AND to_status=from_status) OR (action='submit' AND from_status IN ('draft','returned') AND to_status='submitted') OR (action='return' AND from_status='submitted' AND to_status='returned') OR (action='approve' AND from_status='submitted' AND to_status='approved') OR (action='reopen' AND from_status='approved' AND to_status='draft')),
	CONSTRAINT ck_ic_narrative_reason CHECK (action NOT IN ('return','reopen') OR length(trim(reason)) > 0),
	FOREIGN KEY(period_id) REFERENCES ic_monitoring_periods (id),
	FOREIGN KEY(actor_id) REFERENCES users (id)
)""",
r"""CREATE INDEX ix_ic_narrative_events_period_id ON ic_narrative_events (period_id)"""
],
'sqlite': [
r"""CREATE TABLE ic_narrative_events (
	id INTEGER NOT NULL,
	period_id INTEGER NOT NULL,
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
	UNIQUE (period_id, revision),
	CONSTRAINT ck_ic_narrative_revision CHECK (revision > 0),
	CONSTRAINT ck_ic_narrative_transition CHECK ((action='save' AND from_status IN ('draft','returned') AND to_status=from_status) OR (action='submit' AND from_status IN ('draft','returned') AND to_status='submitted') OR (action='return' AND from_status='submitted' AND to_status='returned') OR (action='approve' AND from_status='submitted' AND to_status='approved') OR (action='reopen' AND from_status='approved' AND to_status='draft')),
	CONSTRAINT ck_ic_narrative_reason CHECK (action NOT IN ('return','reopen') OR length(trim(reason)) > 0),
	FOREIGN KEY(period_id) REFERENCES ic_monitoring_periods (id),
	FOREIGN KEY(actor_id) REFERENCES users (id)
)""",
r"""CREATE INDEX ix_ic_narrative_events_period_id ON ic_narrative_events (period_id)"""
]
}

GUARDS = [
r"""CREATE FUNCTION civ160_immutable() RETURNS trigger LANGUAGE plpgsql SET search_path FROM CURRENT AS $$
BEGIN RAISE EXCEPTION 'Rapor anlatı geçmişi değiştirilemez; yeni sürüm oluşturun.'; END $$""",
r"""CREATE FUNCTION civ160_event_guard() RETURNS trigger LANGUAGE plpgsql SET search_path FROM CURRENT AS $$
DECLARE p ic_monitoring_periods%ROWTYPE; prev ic_narrative_events%ROWTYPE;
 u users%ROWTYPE; snapshot jsonb; boundary integer; expected_keys text[]; k text; lim integer;
BEGIN
 SELECT * INTO p FROM ic_monitoring_periods WHERE id=NEW.period_id FOR UPDATE;
 SELECT * INTO prev FROM ic_narrative_events WHERE period_id=p.id ORDER BY revision DESC LIMIT 1;
 SELECT * INTO u FROM users WHERE id=NEW.actor_id;
 IF p.closed_at IS NOT NULL THEN RAISE EXCEPTION 'İzleme dönemi kapalı; Strateji ile dönem durumunu kontrol edin.'; END IF;
 IF NEW.revision != COALESCE(prev.revision,0)+1 OR NEW.from_status != COALESCE(prev.to_status,'draft') THEN
  RAISE EXCEPTION 'Anlatı revizyonu değişti; sayfayı yenileyin.';
 END IF;
 IF NOT u.is_active OR u.role != 'strategy' THEN RAISE EXCEPTION 'Anlatı için etkin Strateji yetkisi gerekli.'; END IF;
 IF NEW.action IN ('return','approve','reopen') AND (u.position != 'director' OR u.department_id IS NULL) THEN
  RAISE EXCEPTION 'Anlatı kararı için Strateji Müdürü yetkisi gerekli.';
 END IF;
 expected_keys := ARRAY['mission','vision','strengths','improvements','recommendations','band_label','band_explanation'];
 FOR k IN SELECT DISTINCT s.component_code FROM ic_conditions c JOIN ic_standards s ON s.code=c.standard_code WHERE c.plan_id=p.plan_id LOOP
  expected_keys := array_append(expected_keys, 'component_' || k);
 END LOOP;
 snapshot := NEW.snapshot_json::jsonb;
 IF jsonb_typeof(snapshot) != 'object' THEN RAISE EXCEPTION 'Anlatı alanları geçersiz; bütün alanları kontrol edin.'; END IF;
 IF (SELECT count(*) FROM jsonb_object_keys(snapshot)) != cardinality(expected_keys) THEN
  RAISE EXCEPTION 'Anlatı alanları eksik veya fazla; sayfayı yenileyin.';
 END IF;
 FOREACH k IN ARRAY expected_keys LOOP
  lim := CASE WHEN k IN ('mission','vision','band_explanation') THEN 2000 WHEN k='band_label' THEN 100 ELSE 8000 END;
  IF NOT snapshot ? k OR jsonb_typeof(snapshot->k) != 'string' OR length(snapshot->>k)>lim OR
    (snapshot->>k) IS DISTINCT FROM btrim(snapshot->>k, E' \t\r\n') THEN
   RAISE EXCEPTION 'Anlatı alanı % geçersiz veya % karakter sınırını aşıyor; metni düzeltin.', k, lim;
  END IF;
  IF NEW.action IN ('submit','approve') AND k != 'band_explanation' AND length(trim(snapshot->>k))=0 THEN
   RAISE EXCEPTION 'Anlatı alanı % boş; tamamlayıp yeniden gönderin.', k;
  END IF;
 END LOOP;
 IF NEW.action != 'save' AND snapshot IS DISTINCT FROM prev.snapshot_json::jsonb THEN
  RAISE EXCEPTION 'Anlatı kararı kaydedilmiş metinleri korumalıdır.';
 END IF;
 IF NEW.action='approve' THEN
  SELECT COALESCE(max(revision),0) INTO boundary FROM ic_narrative_events WHERE period_id=p.id AND action IN ('return','reopen');
  IF EXISTS (SELECT 1 FROM ic_narrative_events WHERE period_id=p.id AND revision>boundary AND actor_id=u.id AND action='save') THEN
   RAISE EXCEPTION 'Görevler ayrılığı: veriyi giren veya değiştiren onaylayamaz.';
  END IF;
 END IF;
 RETURN NEW;
END $$""",
r"""CREATE TRIGGER civ160_immutable BEFORE UPDATE OR DELETE ON ic_narrative_events FOR EACH ROW EXECUTE FUNCTION civ160_immutable()""",
r"""CREATE TRIGGER civ160_truncate BEFORE TRUNCATE ON ic_narrative_events FOR EACH STATEMENT EXECUTE FUNCTION civ160_immutable()""",
r"""CREATE TRIGGER civ160_insert BEFORE INSERT ON ic_narrative_events FOR EACH ROW EXECUTE FUNCTION civ160_event_guard()"""
]


def upgrade():
    dialect = op.get_bind().dialect.name
    for statement in DDL['postgresql' if dialect == 'postgresql' else 'sqlite']:
        op.execute(sa.text(statement))
    if dialect == 'postgresql':
        for statement in GUARDS:
            op.execute(sa.text(statement))


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute('LOCK TABLE ic_narrative_events IN ACCESS EXCLUSIVE MODE')
    if bind.execute(sa.text('SELECT EXISTS (SELECT 1 FROM ic_narrative_events)')).scalar():
        raise RuntimeError('Rapor anlatı verisi var. Veriyi koruyan geçiş hazırlanmadan sürüm düşürülemez.')
    op.drop_table('ic_narrative_events')
    if bind.dialect.name == 'postgresql':
        op.execute('DROP FUNCTION civ160_event_guard()')
        op.execute('DROP FUNCTION civ160_immutable()')

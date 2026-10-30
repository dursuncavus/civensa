"""CIV-162: align narrative approval authorship with the last approve boundary."""
from alembic import op
import sqlalchemy as sa

revision = 'c162a1b2c3d4'
down_revision = 'c160a1b2c3d4'
branch_labels = None
depends_on = None

# Frozen c160 function; downgrade changes no rows, tables, or triggers.
OLD_FUNCTION = r"""CREATE OR REPLACE FUNCTION civ160_event_guard() RETURNS trigger LANGUAGE plpgsql SET search_path FROM CURRENT AS $$
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
END $$"""

NEW_FUNCTION = OLD_FUNCTION.replace(
    "WHERE period_id=p.id AND action IN ('return','reopen');",
    "WHERE period_id=p.id AND action = 'approve';",
)


def upgrade():
    if op.get_bind().dialect.name == 'postgresql':
        op.execute(sa.text(NEW_FUNCTION))


def downgrade():
    if op.get_bind().dialect.name == 'postgresql':
        op.execute(sa.text(OLD_FUNCTION))

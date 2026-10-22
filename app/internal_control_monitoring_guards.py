"""PostgreSQL guards shared by metadata-created disposable test databases.

The migration freezes its own copy; later edits here cannot alter deployed history.
"""
IMMUTABLE_TABLES = ('ic_monitoring_period_events', 'ic_monitoring_batches',
                    'ic_monitoring_targets', 'ic_monitoring_events',
                    'ic_monitoring_entries', 'ic_monitoring_notes')
POSTGRES_FUNCTIONS = [
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
  IF EXISTS (SELECT 1 FROM ic_monitoring_events WHERE batch_id=b.id AND revision>boundary AND actor_id=u.id AND action='save') THEN
   RAISE EXCEPTION 'Görevler ayrılığı: veriyi giren veya değiştiren onaylayamaz.';
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
END $$"""]


def postgres_statements():
    statements = list(POSTGRES_FUNCTIONS)
    for table in IMMUTABLE_TABLES:
        statements += [f'CREATE TRIGGER civ079_immutable BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION civ079_immutable()',
                       f'CREATE TRIGGER civ079_truncate BEFORE TRUNCATE ON {table} FOR EACH STATEMENT EXECUTE FUNCTION civ079_immutable()']
    statements += ['CREATE TRIGGER civ079_period BEFORE INSERT OR UPDATE OR DELETE ON ic_monitoring_periods FOR EACH ROW EXECUTE FUNCTION civ079_period_guard()',
                   'CREATE TRIGGER civ079_truncate BEFORE TRUNCATE ON ic_monitoring_periods FOR EACH STATEMENT EXECUTE FUNCTION civ079_immutable()']
    for suffix in ('event', 'entry', 'note', 'period_event', 'target'):
        table = {'event': 'events', 'entry': 'entries', 'note': 'notes', 'period_event': 'period_events', 'target': 'targets'}[suffix]
        statements.append(f'CREATE TRIGGER civ079_insert BEFORE INSERT ON ic_monitoring_{table} FOR EACH ROW EXECUTE FUNCTION civ079_{suffix}_guard()')
    return statements


def metadata_guards(metadata, connection, **kwargs):
    if connection.dialect.name == 'postgresql' and any(t.name == 'ic_monitoring_entries' for t in kwargs.get('tables', ())):
        schema = connection.get_execution_options().get('schema_translate_map', {}).get(None)
        previous = connection.exec_driver_sql('SHOW search_path').scalar()
        if schema:
            connection.exec_driver_sql('SET LOCAL search_path TO ' + connection.dialect.identifier_preparer.quote(schema))
        try:
            for statement in postgres_statements():
                from sqlalchemy import text
                connection.execute(text(statement))
        finally:
            if schema:
                connection.exec_driver_sql('SET LOCAL search_path TO ' + previous)

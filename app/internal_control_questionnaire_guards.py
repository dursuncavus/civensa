"""CIV-085 PostgreSQL defenses; migration contains a frozen copy."""
TABLES = ('ic_question_lists', 'ic_question_attachments', 'ic_question_batches', 'ic_question_events')
FUNCTIONS = [
"""CREATE FUNCTION civ085_immutable() RETURNS trigger LANGUAGE plpgsql SET search_path FROM CURRENT AS $$
BEGIN RAISE EXCEPTION 'Soru formu geçmişi değiştirilemez; yeni sürüm oluşturun.'; END $$""",
"""CREATE FUNCTION civ085_list_guard() RETURNS trigger LANGUAGE plpgsql SET search_path FROM CURRENT AS $$
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
"""CREATE FUNCTION civ085_attachment_guard() RETURNS trigger LANGUAGE plpgsql SET search_path FROM CURRENT AS $$
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
"""CREATE FUNCTION civ085_batch_guard() RETURNS trigger LANGUAGE plpgsql SET search_path FROM CURRENT AS $$
DECLARE p ic_monitoring_periods%ROWTYPE; a ic_question_attachments%ROWTYPE;
BEGIN
 SELECT * INTO p FROM ic_monitoring_periods WHERE id=NEW.period_id FOR UPDATE;
 SELECT * INTO a FROM ic_question_attachments WHERE period_id=p.id ORDER BY revision DESC LIMIT 1;
 IF p.closed_at IS NOT NULL OR a.id IS NULL OR NOT a.departments_json::jsonb @> jsonb_build_array(NEW.department_id) THEN
  RAISE EXCEPTION 'Soru paketi açık dönemin katılımcı müdürlüğüne ait olmalıdır.';
 END IF;
 RETURN NEW;
END $$""",
"""CREATE FUNCTION civ085_event_guard() RETURNS trigger LANGUAGE plpgsql SET search_path FROM CURRENT AS $$
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
END $$"""]


def postgres_statements():
    statements = list(FUNCTIONS)
    for table in TABLES:
        statements += [f'CREATE TRIGGER civ085_immutable BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION civ085_immutable()',
                       f'CREATE TRIGGER civ085_truncate BEFORE TRUNCATE ON {table} FOR EACH STATEMENT EXECUTE FUNCTION civ085_immutable()']
    for table, suffix in zip(TABLES, ('list', 'attachment', 'batch', 'event')):
        statements.append(f'CREATE TRIGGER civ085_insert BEFORE INSERT ON {table} FOR EACH ROW EXECUTE FUNCTION civ085_{suffix}_guard()')
    return statements


def metadata_guards(metadata, connection, **kwargs):
    if connection.dialect.name != 'postgresql' or not any(t.name == 'ic_question_events' for t in kwargs.get('tables', ())):
        return
    from sqlalchemy import text
    schema = connection.get_execution_options().get('schema_translate_map', {}).get(None)
    previous = connection.exec_driver_sql('SHOW search_path').scalar()
    if schema:
        connection.exec_driver_sql('SET LOCAL search_path TO ' + connection.dialect.identifier_preparer.quote(schema))
    try:
        for statement in postgres_statements():
            connection.execute(text(statement))
    finally:
        if schema:
            connection.exec_driver_sql('SET LOCAL search_path TO ' + previous)

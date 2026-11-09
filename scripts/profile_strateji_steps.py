#!/usr/bin/env python3
"""CIV-196 — Dört yavaş Strateji adımının profili (yalnız bulgu; düzeltme uygulamaz).

Neden var?
    Pilot öncesi, `/report-builder` ve `/activity-sections` üzerindeki dört Strateji
    adımı sentetik provada 6–11 s sürüyor. Bu betik, o adımların **sunucu tarafı**
    maliyetini aynı gerçek biçimli 2026 PP verisi (33 müdürlük, 105 kart, 226 gösterge,
    182 faaliyet, 1270 ekonomik değer) üzerinde, süreç içi TestClient ile ölçer:
    her adım için duvar saati, SQL ifade sayısı ve toplam SQL süresi
    (SQLAlchemy before/after_cursor_execute) ve cProfile en pahalı fonksiyonlar.

Güvenlik / kapsam:
    - Yalnız atılabilir SQLite. `DATABASE_URL` sqlite değilse betik hiçbir uygulama
      modülü yüklemeden reddeder. PostgreSQL / canlı veritabanına bağlanmaz.
    - Veri `scripts/fr_rehearsal.py` provasının kullandığı aynı onaylı kitap ve içe
      aktarma yolundan kurulur (`first_load_live.verify_book` + `department_payload` +
      `first_load_service.apply_first_load_batch`). `first_load_live.execute` PostgreSQL
      advisory lock / LOCK TABLE kullandığı için SQLite üzerinde doğrudan çalıştırılmaz;
      onun ORM yazma yolu (`apply_first_load_batch`) ve aynı `first_load_department`
      audit kayıtları SQLite üzerinde aynı sonucu üretir (33/105/226/182/1270).
    - Hiçbir app/ değişikliği, migration, yeni bağımlılık yoktur.

Kullanım (depo kökünden):
    python scripts/profile_strateji_steps.py            # tam 2026 verisi
    python scripts/profile_strateji_steps.py --tiny     # duman testi için küçük veri
"""
import argparse
import cProfile
import importlib.util
import io
import json
import os
import pstats
import re
import shutil
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

# Depo kökü: betik scripts/ altındayken parents[1]; dışarıdan çalıştırmada env ile geçer.
ROOT = Path(os.environ.get("CIVENSA_REPO_ROOT", Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT))

# Wall-clock ve SQL sayımı bu adımlar için toplanır. "step4", "step3"ün ürettiği AR
# belgelerini gerektirir; ölçüm sırası provadaki sırayı korur (1→2→3→4).
STEPS = [
    ("step1", "2026 onaylı kitap yayın hazırlığı", "get", "/report-builder", None),
    ("step2", "Onaylı kitaptan yayınla", "post", "/report-builder/publish-approved-book",
     {"approval_reference": "SENTETİK CIV-196 profil onay dayanağı; gerçek meclis kararı değildir."}),
    ("step3", "2026 EK-1 raporlarını oluştur", "post", "/activity-sections/years", {}),
    ("step4", "İdare raporuna geçiş", "get", "/activity-sections", None),
]


def guard_sqlite():
    """Uygulama modülleri yüklenmeden önce sqlite dışı DATABASE_URL'i reddet."""
    url = os.getenv("DATABASE_URL", "")
    if not url:
        return
    from sqlalchemy.engine import make_url
    backend = make_url(url).get_backend_name()
    if backend != "sqlite":
        raise SystemExit(
            f"DURDU: DATABASE_URL sqlite değil ({backend!r}). Bu betik yalnız atılabilir "
            "SQLite üzerinde çalışır; canlı/PostgreSQL hedefi kullanmaz."
        )


def create_schema(engine):
    """Bütün uygulama modellerini kaydedip SQLite şemasını oluşturur."""
    from app.db import Base
    from app.first_load_service import load_all_models
    load_all_models()
    Base.metadata.create_all(engine)


def load_section_seed():
    """EK-1 bölüm tanımlarını, uygulamanın tek kaynağı olan migration'dan oku."""
    migration = ROOT / "migrations" / "versions" / (
        "c0372027a001_civ_037_ek_1_owned_yearly_report_content.py"
    )
    spec = importlib.util.spec_from_file_location("_civ196_section_seed", migration)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.SECTION_SEED


def seed(engine, tiny=False):
    """Gerçek biçimli 2026 PP verisini (ya da --tiny için küçük çekirdek) kurar.

    `fr_rehearsal.setup` ile aynı onaylı kitabı ve aynı `apply_first_load_batch`
    yazma yolunu kullanır; yalnız PostgreSQL'e özgü `first_load_live.execute`
    sarmalayıcısı yerine ORM yolunu doğrudan çağırır.
    """
    from sqlalchemy import select
    from sqlalchemy.orm import Session
    from app.first_load_service import apply_first_load_batch
    from app.import_service import department_key
    from app.models import (
        ARSectionDefinition, AuditLog, Department, DepartmentScope, ImportBatch,
        Organization, ReportingPeriod, User,
    )
    from app.security import hash_password
    from scripts import first_load_live as live
    from scripts.first_load_dryrun import NAME_MAP

    section_seed = load_section_seed()
    with Session(engine, expire_on_commit=False) as db:
        org = Organization(name="İlk yükleme denemesi Belediyesi")
        strategy = User(email="strategy@example.invalid", full_name="Strateji (SENTETİK)",
                        role="strategy", password_hash="unused")
        db.add_all([org, strategy])
        db.flush()

        if tiny:
            names = {"Strateji Geliştirme Müdürlüğü"}
        else:
            names = set(json.loads(NAME_MAP.read_text(encoding="utf-8"))["map"].values())
            names.add("Yapı Kontrol Müdürlüğü")
        departments = {name: Department(organization_id=org.id, name=name) for name in sorted(names)}
        db.add_all(departments.values())
        db.commit()

        period = ReportingPeriod(year=2026, status="draft", template_status="verified")
        db.add(period)
        db.commit()

        sg = departments["Strateji Geliştirme Müdürlüğü"]
        strategy.department_id = sg.id
        strategy.position = "director"
        strategy.password_hash = hash_password("Civ196-local-test-only!")
        db.commit()

        for row in section_seed:
            db.add(ARSectionDefinition(**dict(row)))
        db.commit()

        if tiny:
            db.add(DepartmentScope(period_id=period.id, department_id=sg.id,
                                   status="required", position=0))
            db.commit()
            return dict(period_id=period.id, organization_id=org.id, counts=None)

        book_sha256 = live.book_config(2026)[1]
        filename = live.book_config(2026)[0].name
        parsed = live.verify_book(live.book_config(2026)[0], year=2026)
        counts = dict(cards=0, indicators=0, activities=0, economic_values=0)
        for source in parsed["departments"]:
            payload = live.department_payload(parsed, source)
            batch = ImportBatch(period_id=period.id, filename=filename, status="preview",
                                payload_json=json.dumps(payload, ensure_ascii=False),
                                created_by=strategy.id)
            db.add(batch)
            db.flush()
            applied, _catalogue, validations = apply_first_load_batch(db, batch, strategy)
            for key in counts:
                counts[key] += applied[key]
            department = next(d for d in db.scalars(select(Department))
                              if department_key(d.name) == department_key(source["name"]))
            db.add(AuditLog(
                user_id=strategy.id, action="first_load_department", entity_type="import_batch",
                entity_id=batch.id,
                details=json.dumps(dict(book_sha256=book_sha256, year=2026,
                                        department_id=department.id,
                                        validation_errors=validations),
                                   ensure_ascii=False)))
            db.commit()
        expected = dict(cards=105, indicators=226, activities=182, economic_values=1270)
        if counts != expected:
            raise SystemExit(f"DURDU: beklenen veri şekli üretilemedi: {counts}")
        return dict(period_id=period.id, organization_id=org.id, counts=counts)


def attach_sql_counters(engine):
    """SQLAlchemy before/after_cursor_execute ile SQL sayısı ve toplam süresi."""
    from sqlalchemy import event
    stats = {"count": 0, "time": 0.0, "statements": Counter(), "_started": 0.0}

    def before(conn, cursor, statement, params, context, executemany):
        stats["count"] += 1
        stats["_started"] = time.perf_counter()

    def after(conn, cursor, statement, params, context, executemany):
        stats["time"] += time.perf_counter() - stats["_started"]
        stats["statements"][re.sub(r"\s+", " ", statement).strip()] += 1

    event.listen(engine, "before_cursor_execute", before)
    event.listen(engine, "after_cursor_execute", after)
    return stats


def top_app_functions(profile, limit=10):
    """cProfile'ın en pahalı app/scripts fonksiyonlarını file:line ile döndür.

    (httpx/starlette/stdlib sarmalayıcıları hariç; eylem yapılabilir uygulama
    fonksiyonları cumtime'a göre ilk `limit` adet.)
    """
    stream = io.StringIO()
    pstats.Stats(profile, stream=stream).sort_stats("cumulative").print_stats(800)
    rows = []
    for line in stream.getvalue().splitlines():
        parts = line.split(None, 5)
        if len(parts) < 6 or (f"{os.sep}app{os.sep}" not in line and f"{os.sep}scripts{os.sep}" not in line):
            continue
        try:
            cumtime = float(parts[3])
            ncalls = float(parts[0])
        except ValueError:
            continue
        rows.append((cumtime, ncalls, parts[5]))
    return rows[:limit]


class Client:
    """TestClient + oturum + engine, tek bir (kopyalanmış) SQLite dosyasına bağlı."""

    def __init__(self, db_path, period_id, organization_id):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session
        self.engine = create_engine(f"sqlite:///{db_path}", future=True,
                                    connect_args={"check_same_thread": False})
        self.stats = attach_sql_counters(self.engine)
        self.session = Session(self.engine, expire_on_commit=False)
        self.period_id = period_id
        self.org_id = organization_id
        self.csrf_token = ""

        from fastapi.testclient import TestClient
        from app.db import get_db
        from app.main import app

        def database():
            yield self.session

        self.app = app
        app.dependency_overrides[get_db] = database
        self.client = TestClient(app, follow_redirects=False)
        self._login()

    def _login(self):
        response = self.client.post("/login", data=dict(
            email="strategy@example.invalid", password="Civ196-local-test-only!"))
        if response.status_code != 303:
            raise SystemExit("DURDU: Strateji girişi başarısız.")
        match = re.search(r'name="csrf_token" value="([^"]+)"',
                          self.client.get("/modules").text)
        if not match:
            raise SystemExit("DURDU: csrf_token alınamadı.")
        self.csrf_token = match.group(1)

    def close(self):
        from app.db import get_db
        self.client.close()
        self.session.close()
        self.engine.dispose()
        self.app.dependency_overrides.pop(get_db, None)


def measure_once(client, method, url, form):
    """Tek isteği ölç: duvar saati + SQL sayısı/süresi + cProfile."""
    stats = client.stats
    stats["count"] = 0
    stats["time"] = 0.0
    stats["statements"].clear()
    profile = cProfile.Profile()
    profile.enable()
    started = time.perf_counter()
    if method == "post":
        data = dict(form or {})
        data.setdefault("period_id", client.period_id)
        data.setdefault("organization_id", client.org_id)
        data.setdefault("csrf_token", client.csrf_token)
        response = client.client.post(url, data=data)
    else:
        response = client.client.get(url)
    wall = time.perf_counter() - started
    profile.disable()
    return dict(wall=wall, sql_count=stats["count"], sql_time=stats["time"],
                status=response.status_code, top=top_app_functions(profile),
                top_statements=[[s, c] for s, c in stats["statements"].most_common(6)])


def run(profile_db_path, runs, tiny):
    """Dört adımı, her adımı `runs` kez ölçer (yazma adımları temiz kopyada)."""
    from sqlalchemy import create_engine

    master = str(profile_db_path)
    runtime = master + ".run"

    engine = create_engine(f"sqlite:///{master}", future=True,
                           connect_args={"check_same_thread": False})
    create_schema(engine)
    meta = seed(engine, tiny=tiny)
    engine.dispose()
    if not tiny:
        print(f"Kurulum sayımları: {meta['counts']}", flush=True)

    def fresh_client():
        shutil.copy2(master, runtime)
        return Client(runtime, meta["period_id"], meta["organization_id"])

    results = {}

    client = fresh_client()
    results["step1"] = [measure_once(client, "get", f"/report-builder?period_id={client.period_id}", None)
                        for _ in range(runs)]
    client.close()

    results["step2"] = []
    for _ in range(runs):
        client = fresh_client()
        results["step2"].append(measure_once(
            client, "post", "/report-builder/publish-approved-book",
            {"period_id": meta["period_id"],
             "approval_reference": STEPS[1][4]["approval_reference"]}))
        client.close()

    results["step3"] = []
    for _ in range(runs):
        client = fresh_client()
        results["step3"].append(measure_once(
            client, "post", "/activity-sections/years",
            {"organization_id": meta["organization_id"], "period_id": meta["period_id"]}))
        client.close()

    client = fresh_client()
    client.client.post("/activity-sections/years", data=dict(
        csrf_token=client.csrf_token, organization_id=meta["organization_id"],
        period_id=meta["period_id"]))
    results["step4"] = [measure_once(client, "get", f"/activity-sections?period_id={client.period_id}", None)
                        for _ in range(runs)]
    client.close()

    return results


def report(results, runs, tiny):
    """İnsan okur özet + stdout'ta makine okur JSON."""
    labels = {s[0]: s[1] for s in STEPS}
    routes = {s[0]: s[3] for s in STEPS}
    print(f"\n# CIV-196 Strateji adımları profili ({'tiny' if tiny else 'tam 2026 verisi'})")
    print(f"# Her adım {runs} kez ölçüldü; SQL sayısı Render için asıl risk ölçüsüdür.")
    summary = {}
    for key, _label, _method, route, _form in STEPS:
        rows = results[key]
        walls = [round(r["wall"], 3) for r in rows]
        sqls = [r["sql_count"] for r in rows]
        sql_times = [round(r["sql_time"], 3) for r in rows]
        statuses = sorted({r["status"] for r in rows})
        print(f"\n## {key} — {labels[key]}")
        print(f"  route: {routes[key]}  | status: {statuses}")
        print(f"  wall (s): {walls}")
        print(f"  SQL sayısı: {sqls}  | SQL süresi (s): {sql_times}")
        print("  en pahalı fonksiyonlar (cumtime; file:line):")
        for cumtime, ncalls, func in rows[0]["top"]:
            print(f"    {cumtime:7.3f}s  {func}")
        print("  en sık SQL (N+1 kanıtı):")
        for statement, count in rows[0]["top_statements"]:
            print(f"    {count:6d}  {statement[:112]}")
        summary[key] = dict(label=labels[key], route=route, status=statuses,
                            walls=walls, sql_counts=sqls, sql_times=sql_times,
                            top=[[t, int(n), f] for t, n, f in rows[0]["top"]],
                            top_statements=rows[0]["top_statements"])
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tiny", action="store_true",
                        help="Küçük bir çekirdek veriyle çalış (duman testi).")
    parser.add_argument("--runs", type=int, default=3, help="Her adımın koşu sayısı (varsayılan 3).")
    parser.add_argument("--db", type=Path, default=None,
                        help="Atılabilir SQLite dosya yolu (varsayılan: geçici dosya).")
    args = parser.parse_args(argv)

    guard_sqlite()
    os.environ.pop("MIGRATION_DATABASE_URL", None)
    os.environ["DEMO_SEED"] = "0"

    cleanup = None
    if args.db:
        db_path = Path(args.db).resolve()
    else:
        cleanup = tempfile.TemporaryDirectory(prefix="civ196_")
        db_path = Path(cleanup.name) / "profile.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    started = time.perf_counter()
    try:
        results = run(db_path, args.runs, args.tiny)
        summary = report(results, args.runs, args.tiny)
    finally:
        if cleanup is not None:
            cleanup.cleanup()
    print(f"\nToplam betik süresi (kurulum dahil): {time.perf_counter() - started:.1f} s")
    print("\n__CIV196_JSON__")
    print(json.dumps(summary, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from datetime import datetime, UTC
from pathlib import Path
from contextlib import asynccontextmanager
import json
from decimal import Decimal
from .serialization import json_dumps
from .numbers import parse_number, format_number, format_contract_targets
from .value_labels import value_kind_label, funding_label
import os
import secrets
import hmac
import io
import csv
import time
from functools import lru_cache
from urllib.parse import quote

from fastapi import FastAPI, Request, Depends, Form, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, inspect, func, exists, false, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from starlette.middleware.sessions import SessionMiddleware
from starlette.routing import Match
from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from alembic.script import ScriptDirectory

from .db import Base, engine, get_db, SessionLocal
from .db_privileges import assert_runtime_restricted
from .models import DepartmentScope
from .models import (
    User, Department, ReportingPeriod, Indicator, IndicatorValue, Activity,
    ActivityCostValue, DepartmentCostValue, Submission, AuditLog, Program,
    SubProgram, TemplateSnapshot, ImportBatch, SubmissionEvent, Notification, NotificationRecipient,
)
from .security import verify_password, hash_password, temporary_password
from .personal_accounts import ACCOUNT_CSV_HEADERS, validate_account_csv, prepare_user_creation
from . import login_throttling
from . import released_permissions
from .seed import seed
from .template_parser import analyze_template
from .data_importer import parse_performance_docx
from .import_service import build_department_plan, apply_import_batch, import_revert_status, revert_import_batch, import_validation_errors
from .config import validate_runtime_settings, session_secret, cookie_secure, demo_seed_enabled, is_production
from .file_security import read_upload_limited, validate_office_zip
from .report_export import build_department_docx
from .csv_safety import csv_row, csv_text, csv_cell_matches
from .activity_mapping_service import activity_mapping_states, mapping_gap_counts, activity_mapping_counts

BASE_DIR = Path(__file__).resolve().parent
APP_VERSION = "5.0.0"


@lru_cache(maxsize=1)
def migration_head() -> str:
    """Current Alembic script head; read from migrations/ so readiness follows new revisions."""
    alembic_config = AlembicConfig(str(BASE_DIR.parent / "alembic.ini"))
    alembic_config.set_main_option("script_location", str(BASE_DIR.parent / "migrations"))
    return ScriptDirectory.from_config(alembic_config).get_current_head()


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_runtime_settings()
    if os.getenv("MIGRATION_DATABASE_URL"):
        # Check the request role before migration or traffic, using catalogs only.
        assert_runtime_restricted(engine)
    if is_production():
        # Apply committed schema migrations before serving traffic; back up before upgrading.
        alembic_config = AlembicConfig(str(BASE_DIR.parent / "alembic.ini"))
        alembic_config.set_main_option("script_location", str(BASE_DIR.parent / "migrations"))
        schema = inspect(engine)
        if schema.has_table("users") and not schema.has_table("alembic_version"):
            # Legacy pilot databases predate Alembic tracking but already match
            # the initial schema. Baseline them before applying later revisions.
            alembic_command.stamp(alembic_config, "290ef7e62102")
        alembic_command.upgrade(alembic_config, "head")
        if not inspect(engine).has_table("users"):
            raise RuntimeError("Civensa veritabanı hazırlanmadı. Önce `alembic upgrade head` çalıştırın.")
    else:
        alembic_config = AlembicConfig(str(BASE_DIR.parent / "alembic.ini"))
        alembic_config.set_main_option("script_location", str(BASE_DIR.parent / "migrations"))
        if inspect(engine).has_table("users") and not inspect(engine).has_table("alembic_version"):
            alembic_command.stamp(alembic_config, "290ef7e62102")
        alembic_command.upgrade(alembic_config, "head")
        if demo_seed_enabled():
            with SessionLocal() as db:
                seed(db)
    yield


app = FastAPI(title="Civensa", version=APP_VERSION, lifespan=lifespan)


class FirstPasswordMiddleware:
    """The signed pending-login marker also gates public pages and unknown URLs.

    require_user separately checks the database flag for every protected route.
    SessionMiddleware wraps this middleware so its session is available here.
    """
    def __init__(self, app):
        self.app = app

    def protected_route(self, scope):
        # Protected routes must validate the password fingerprint first, so a
        # stale temporary-password session still gets the existing 401 behavior.
        for route in scope["app"].routes:
            if route.matches(scope)[0] == Match.FULL and hasattr(route, "dependant"):
                dependencies = [route.dependant]
                while dependencies:
                    dependency = dependencies.pop()
                    if dependency.call is require_user:
                        return True
                    dependencies.extend(dependency.dependencies)
        return False

    async def __call__(self, scope, receive, send):
        path = scope.get("path", "")
        if (scope["type"] == "http" and scope.get("session", {}).get("must_change_password")
                and path not in {"/change-password", "/api/me/change-password", "/logout", "/static"}
                and not path.startswith("/static/") and not self.protected_route(scope)):
            await RedirectResponse("/change-password", 303)(scope, receive, send)
            return
        await self.app(scope, receive, send)


app.add_middleware(FirstPasswordMiddleware)
app.add_middleware(
    SessionMiddleware,
    secret_key=session_secret(),
    same_site="lax",
    https_only=cookie_secure(),
    max_age=8 * 60 * 60,
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if request.url.path == "/change-password":
        response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data:; script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; font-src 'self'; frame-ancestors 'none'; "
        "form-action 'self'; base-uri 'self'"
    )
    return response
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
from .structure_service import period_name

templates = Jinja2Templates(directory=BASE_DIR / "templates")


_PASSWORD_FINGERPRINT_KEY = session_secret().encode()


def password_fingerprint(password_hash: str) -> str:
    """Keyed digest of the stored hash; every reset/change re-salts the hash, so it changes."""
    message = b"civensa-session-password-v1\x00" + str(password_hash or "").encode()
    return hmac.new(_PASSWORD_FINGERPRINT_KEY, message, "sha256").hexdigest()[:32]


def start_user_session(request: Request, user_id: int, password_hash: str) -> None:
    request.session["user_id"] = user_id
    request.session["password_fp"] = password_fingerprint(password_hash)


def current_user(request: Request, db: Session):
    uid = request.session.get("user_id")
    user = db.get(User, uid) if uid else None
    # Sessions issued before the latest password reset/change are no longer valid (A1-F10).
    if user and not hmac.compare_digest(str(request.session.get("password_fp", "")), password_fingerprint(user.password_hash)):
        return None
    return user


async def csrf_valid(request: Request) -> bool:
    expected = request.session.get("csrf_token", "")
    supplied = request.headers.get("X-CSRF-Token", "")
    if not supplied and request.headers.get("content-type", "").startswith(("application/x-www-form-urlencoded", "multipart/form-data")):
        form = await request.form()
        supplied = str(form.get("csrf_token", ""))
    return bool(expected and supplied and hmac.compare_digest(str(expected), str(supplied)))


CSRF_ERROR = "Güvenlik doğrulaması başarısız. Sayfayı yenileyip tekrar deneyin."


async def require_user(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user or not user.is_active:
        request.session.clear()
        raise HTTPException(status_code=401)
    if user.must_change_password and request.url.path not in {"/change-password", "/api/me/change-password"}:
        request.session["must_change_password"] = True
        raise HTTPException(303, "Devam etmek için kendi parolanızı belirleyin.",
                            headers={"Location": "/change-password"})
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        if not await csrf_valid(request):
            raise HTTPException(403, CSRF_ERROR)
    # Keep authorship request-scoped, including writes made by import services.
    db.info["released_actor_id"] = user.id
    try:
        yield user
    finally:
        db.info.pop("released_actor_id", None)


def require_strategy(user: User = Depends(require_user)):
    if user.role != "strategy":
        raise HTTPException(403, "Bu işlem yalnızca Strateji Geliştirme kullanıcılarına açıktır. Yetkili hesabınızla giriş yapın veya Strateji Geliştirme ile iletişime geçin.")
    return user


def notification_query(user: User):
    # Recipient-bound notices never become visible via a role/department fallback.
    addressed = exists().where(NotificationRecipient.notification_id == Notification.id,
                               NotificationRecipient.user_id == user.id)
    if user.role == "strategy":
        legacy_scope = Notification.role == "strategy"
    elif user.role == "department":
        legacy_scope = (Notification.role == "department") & (Notification.department_id == user.department_id)
    else:
        legacy_scope = false()
    return select(Notification).where(
        ((Notification.delivery_mode == "legacy") & legacy_scope) |
        ((Notification.delivery_mode == "recipients") & addressed))


def user_notifications(db: Session, user: User, limit: int = 8):
    rows = db.scalars(notification_query(user).order_by(Notification.created_at.desc()).limit(limit)).all()
    receipts = {r.notification_id: r for r in db.scalars(select(NotificationRecipient).where(
        NotificationRecipient.user_id == user.id, NotificationRecipient.notification_id.in_([r.id for r in rows])))}
    # Old shared read flags cannot prove who read a notice. Leave them untouched.
    for row in rows:
        row.recipient_is_read = row.id in receipts and receipts[row.id].read_at is not None
    return rows


def log(db, user, action, entity_type, entity_id=None, details=""):
    db.add(AuditLog(
        user_id=user.id if user else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
    ))
    db.commit()


def format_tr(value, money=False):
    return format_number(value, money)


def parse_tr_number(raw, field="Değer"):
    try:
        value = parse_number(raw)
        if value is None:
            raise ValueError("Değer boş olamaz.")
        return value
    except ValueError as exc:
        raise HTTPException(422, f"{field}: {exc}") from None


def parse_optional_number(raw, field="Değer"):
    try:
        return parse_number(raw)
    except ValueError as exc:
        raise HTTPException(422, f"{field}: {exc}") from None


def parse_nonnegative_money(raw, field="Tutar"):
    value = parse_optional_nonnegative_money(raw, field)
    if value is None:
        raise HTTPException(422, f"{field} boş olamaz.")
    return value


def parse_optional_nonnegative_money(raw, field="Tutar"):
    try:
        return parse_number(raw, money=True)
    except ValueError as exc:
        raise HTTPException(422, f"{field}: {exc}") from None


from .time_display import turkey_time
templates.env.filters['turkey_time'] = turkey_time
templates.env.filters["trnum"] = lambda v: format_number(v)
templates.env.filters['contract_targets'] = format_contract_targets
templates.env.filters['value_kind_label'] = value_kind_label
templates.env.filters['funding_label'] = funding_label
templates.env.filters["trmoney"] = lambda v: format_number(v, True)
def section_text(raw):
    content=json.loads(raw)
    if 'caption' in content: return content['caption']
    return content.get('text','') if 'text' in content else '\n'.join('\t'.join(str(c) for c in row) for row in content.get('rows',[]))
templates.env.filters['section_text']=section_text
templates.env.filters['section_placement']=lambda raw: json.loads(raw).get('placement','before')


def active_period(db: Session):
    period = db.scalar(select(ReportingPeriod).where(ReportingPeriod.status == "active").order_by(ReportingPeriod.year.desc()))
    return period or db.scalar(select(ReportingPeriod).order_by(ReportingPeriod.year.desc()))


def session_period(request: Request, db: Session, data=None, *, require=False):
    """Resolve PP context from this request; another tab's session is not context."""
    query_id = getattr(request, "query_params", {}).get("period_id") if request else None
    if data is not None and not hasattr(data, "get"):
        raise HTTPException(422, "İstek bilgileri geçersiz. Raporlama dönemi ve form alanlarını kontrol edin.")
    body_id = data.get("period_id") if data is not None else None
    ids = []
    for value in (query_id, body_id):
        if value is None:
            continue
        if isinstance(value, bool) or not str(value).isascii() or not str(value).isdecimal() or len(str(value)) > 18 or int(value) < 1:
            raise HTTPException(422, "Raporlama dönemi geçersiz. Bağlantıdaki veya formdaki dönemi kontrol edin.")
        ids.append(int(value))
    if len(set(ids)) > 1:
        raise HTTPException(422, "Bağlantı ve form farklı raporlama dönemleri içeriyor. Sayfayı seçtiğiniz yıl için yeniden açın.")
    if not ids:
        if require:
            raise HTTPException(422, "Raporlama dönemi belirtilmedi. Sayfayı yenileyip seçtiğiniz yıl üzerinden tekrar deneyin.")
        return active_period(db)
    period = db.get(ReportingPeriod, ids[0])
    if not period:
        raise HTTPException(404, "Seçilen raporlama dönemi bulunamadı. Dönem bağlantısını kontrol edin veya Strateji Geliştirme birimine başvurun.")
    return period


async def require_pp_period(request: Request, db: Session = Depends(get_db),
                            user: User = Depends(require_user)):
    """Require explicit HTTP write context before any mutation or audit.

    FastAPI caches this request's JSON/form for the handler.
    """
    if "application/json" in request.headers.get("content-type", ""):
        try:
            data = await request.json()
        except ValueError:
            data = None
        if not hasattr(data, "get"):
            data = None
    else:
        data = await request.form()
    return session_period(request, db, data, require=True)


def check_pp_access(db: Session, user: User, department_id: int, period: ReportingPeriod):
    department = db.get(Department, department_id)
    if not department:
        raise HTTPException(404, "Müdürlük bulunamadı. Müdürlük bağlantısını kontrol edin.")
    if user.role == "department":
        from .structure_service import department_in_year
        from .models import ReportCard, EconomicValue
        scope = db.scalar(select(DepartmentScope).where(
            DepartmentScope.department_id == department_id, DepartmentScope.period_id == period.id))
        # Historical imports can contain owned PP data without a scope row.
        # A submission alone is not a grant: older GET routes created those rows.
        historical = scope is None and any(db.scalar(select(model.id).where(
            model.department_id == department_id, model.period_id == period.id).limit(1))
            for model in (Indicator, Activity, ReportCard, DepartmentCostValue, EconomicValue))
        if (user.department_id != department_id or (scope and scope.status == "excluded")
                or (not scope and not historical)
                or not department_in_year(db, department, period.year)):
            raise HTTPException(403, f"{period.year} yılı Performans Programı için bu müdürlüğe erişim yetkiniz yok. Dönem ve müdürlük yetkinizi kontrol ettirmek için Strateji Geliştirme birimine başvurun.")


def pp_period(request, db, user, department_id, data=None, record_period_id=None):
    period = session_period(request, db, data)
    if not period:
        raise HTTPException(404, "Raporlama dönemi bulunamadı. Strateji Geliştirme biriminden dönem oluşturmasını isteyin.")
    check_pp_access(db, user, department_id, period)
    if record_period_id is not None and record_period_id != period.id:
        record_period = db.get(ReportingPeriod, record_period_id)
        raise HTTPException(409, f"Kayıt {record_period.year} yılına ait; seçilen dönem {period.year}. Kaydın yılını açıp tekrar deneyin.")
    return period


def pp_write_result(period, department_id, **values):
    return {"ok": True, **values, "period_id": period.id, "year": period.year,
            "redirect_url": f"/department/{department_id}?period_id={period.id}"}


def indicator_columns(year: int):
    return [
        {"year": year - 2, "kind": "actual", "label": f"{year-2} Gerçekleşme"},
        {"year": year - 1, "kind": "planned", "label": f"{year-1} Planlanan"},
        {"year": year - 1, "kind": "year_end_estimate", "label": f"{year-1} Yıl Sonu Gerçekleşme Tahmini"},
        {"year": year, "kind": "target", "label": f"{year} Hedef"},
        {"year": year + 1, "kind": "forecast", "label": f"{year+1} Tahmin"},
        {"year": year + 2, "kind": "forecast", "label": f"{year+2} Tahmin"},
    ]


def activity_columns(year: int):
    return [
        {"year": year - 1, "kind": "budget", "label": f"{year-1} Bütçe"},
        {"year": year - 1, "kind": "midyear_spend", "label": f"{year-1} Haziran Sonu Harcama"},
        {"year": year - 1, "kind": "year_end_estimate", "label": f"{year-1} Yıl Sonu Harcama Tahmini"},
        {"year": year, "kind": "budget", "label": f"{year} Bütçe"},
        {"year": year + 1, "kind": "forecast", "label": f"{year+1} Tahmin"},
        {"year": year + 2, "kind": "forecast", "label": f"{year+2} Tahmin"},
    ]


def indicator_value_map(ind: Indicator):
    return {(v.year, v.value_kind): v for v in ind.values}


def activity_cost_map(activity: Activity, funding_type="total"):
    return {(v.year, v.value_kind): v.amount for v in activity.cost_values if v.funding_type == funding_type}


def indicator_issues(ind: Indicator, period_year: int):
    issues = []
    vals = indicator_value_map(ind)
    if not ind.name.strip():
        issues.append("Gösterge adı boş.")
    if not ind.unit.strip():
        issues.append("Ölçü birimi boş.")
    if (period_year, "target") not in vals:
        issues.append(f"{period_year} hedefi girilmemiş.")
    if not (ind.explanation.strip() or (ind.card and ind.card.explanation.strip())):
        issues.append("Göstergeye ilişkin açıklama boş.")
    if not (ind.calculation_method.strip() or (ind.card and ind.card.calculation_method.strip())):
        issues.append("Hesaplama yöntemi boş.")
    if not (ind.data_source.strip() or (ind.card and ind.card.data_source.strip())):
        issues.append("Verinin kaynağı boş.")
    for value in ind.values:
        if value.raw_text.strip() in {"-", "–", "—"} and value.value is None:
            continue
        if value.state != "verified" or value.value is None:
            issues.append(f"{value.year} {value_kind_label(value.value_kind)}: kaynak değeri doğrulanmalı ({value.raw_text}).")
    return issues




def _mapping_tokens(text: str) -> set[str]:
    import re as _re
    raw = str(text or "").lower().replace("ı", "i")
    raw = raw.translate(str.maketrans("çğıöşü", "cgiosu"))
    words = _re.findall(r"[a-z0-9]+", raw)
    stop = {
        "ve", "ile", "icin", "ilgili", "kapsaminda", "yapilmasi", "yapmak", "yurutulmesi",
        "yurutmek", "hizmet", "hizmetleri", "faaliyet", "faaliyetleri", "projesi", "saglamak",
        "edilmesi", "gerceklestirmek", "yonetimi", "destek", "belediye", "mudurlugu", "yil", "genel"
    }
    return {w for w in words if len(w) > 2 and w not in stop}


def _activity_mapping_suggestion(activity: Activity, candidates: list[SubProgram], indicators_by_sp: dict[int, list[Indicator]]):
    activity_tokens = _mapping_tokens(activity.name + " " + (activity.explanation or ""))
    if not activity_tokens or not candidates:
        return None, 0.0
    scored = []
    for sp in candidates:
        corpus = f"{sp.program.name} {sp.name} {sp.rationale or ''} {sp.goal or ''} " + " ".join(i.name for i in indicators_by_sp.get(sp.id, []))
        target_tokens = _mapping_tokens(corpus)
        overlap = len(activity_tokens & target_tokens)
        union = max(1, len(activity_tokens | target_tokens))
        score = overlap / union
        # Reward direct keyword evidence without pretending the model knows more than the source.
        score += min(0.35, overlap * 0.08)
        scored.append((score, sp))
    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best = scored[0]
    second = scored[1][0] if len(scored) > 1 else 0.0
    if best_score >= 0.22 and best_score - second >= 0.05:
        return best, round(min(best_score, 0.99), 2)
    return None, round(best_score, 2)


def _department_mapping_choices(db: Session, department_id: int, period_id: int):
    indicators = db.scalars(
        select(Indicator).where(Indicator.department_id == department_id, Indicator.period_id == period_id)
        .options(selectinload(Indicator.subprogram).selectinload(SubProgram.program))
    ).all()
    by_sp: dict[int, list[Indicator]] = {}
    choices: list[SubProgram] = []
    seen = set()
    for ind in indicators:
        by_sp.setdefault(ind.subprogram_id, []).append(ind)
        if ind.subprogram_id not in seen:
            seen.add(ind.subprogram_id)
            choices.append(ind.subprogram)
    choices.sort(key=lambda sp: (sp.program.name, sp.name))
    return choices, by_sp

def editable_submission(db: Session, department_id: int, period_id: int | None = None):
    period = db.get(ReportingPeriod, period_id) if period_id else active_period(db)
    if not period:
        return None
    return db.scalar(select(Submission).where(Submission.department_id == department_id, Submission.period_id == period.id))


def ensure_department_editable(db: Session, user: User, department_id: int, period_id: int | None = None, *, allow_strategy: bool = False):
    if not (allow_strategy and user.role == "strategy") and (user.role != "department" or user.department_id != department_id):
        raise HTTPException(403)
    period = db.get(ReportingPeriod, period_id) if period_id else active_period(db)
    if not period:
        raise HTTPException(404, "Raporlama dönemi bulunamadı. Strateji Geliştirme birimine başvurun.")
    check_pp_access(db, user, department_id, period)
    if period.status == "closed":
        raise HTTPException(409, f"{period.year} yılı dönemi kapalı; kayıt değiştirilemez. Strateji Geliştirme birimine başvurun.")
    sub = editable_submission(db, department_id, period_id)
    if sub and sub.status in {"submitted", "approved"}:
        raise HTTPException(409, "Kayıt incelemede veya onaylı; değiştirilemez.")
    return sub


def ensure_submission(db: Session, department_id: int, period_id: int):
    sub = db.scalar(select(Submission).where(Submission.department_id == department_id, Submission.period_id == period_id))
    if not sub:
        sub = Submission(department_id=department_id, period_id=period_id, status="draft")
        db.add(sub); db.flush()
    return sub


@app.get("/", include_in_schema=False)
def root(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    return RedirectResponse(("/change-password" if user.must_change_password else "/modules") if user else "/login", 303)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if user and user.is_active and user.must_change_password:
        return RedirectResponse("/change-password", 303)
    return templates.TemplateResponse(request, "login.html", {"error": None})


@app.post("/login", response_class=HTMLResponse)
def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    # Use the ASGI client accepted by the server's existing proxy trust policy.
    # Never parse X-Forwarded-For here. Missing client addresses share one bucket.
    client_ip = request.client.host if request.client else "unknown"
    email_key, ip_key, now, locked = login_throttling.begin_attempt(db, email, client_ip)
    user = db.scalar(select(User).where(User.email == email.strip().lower()))
    # Exactly one PBKDF2 check for ordinary failures, unknown/inactive users and
    # locked requests (including correct passwords); no user existence shortcut.
    stored = user.password_hash if user and user.is_active and not locked else login_throttling.DUMMY_PASSWORD_HASH
    valid_password = verify_password(password, stored)
    if locked or not user or not user.is_active or not valid_password:
        if not locked:
            locked = login_throttling.record_failure(db, email_key, ip_key, now)
        db.commit()
        error = login_throttling.LOCK_MESSAGE if locked else "E-posta veya parola hatalı."
        return templates.TemplateResponse(request, "login.html", {"error": error}, status_code=400)
    login_throttling.clear_email_failures(db, email_key, now)
    # Never carry role/period context from a previous session into a new login.
    request.session.clear()
    start_user_session(request, user.id, user.password_hash)
    request.session["csrf_token"] = secrets.token_urlsafe(32)
    if user.must_change_password:
        request.session["must_change_password"] = True
    log(db, user, "login", "user", user.id)
    return RedirectResponse("/change-password" if user.must_change_password else "/modules", 303)


@app.post("/logout")
async def logout(request: Request):
    # A signed-in session is only ended by a same-origin request carrying its CSRF token (A1-F11a).
    if request.session.get("user_id") and not await csrf_valid(request):
        raise HTTPException(403, CSRF_ERROR)
    request.session.clear()
    return RedirectResponse("/login", 303)


@app.get("/modules", response_class=HTMLResponse)
def modules(request: Request, user: User = Depends(require_user)):
    return templates.TemplateResponse(request, "modules.html", {"user": user})


@app.get("/activity-report", response_class=HTMLResponse)
def activity_report_workspace(request: Request, year: int = 2026, db: Session = Depends(get_db), user: User = Depends(require_user)):
    from .activity_report_service import annual_indicators
    from .structure_service import closure_notes
    if year < 2020 or year > 2100:
        raise HTTPException(422, "Faaliyet Raporu yılı 2020–2100 arasında olmalı.")
    return templates.TemplateResponse(request, "activity_report.html", {
        "user": user, "year": year, "indicator_rows": annual_indicators(db, user, year),
        "closure_notes": closure_notes(db, db.scalar(select(ReportingPeriod.id).where(ReportingPeriod.year == year)), user),
        "years": sorted(set(db.scalars(select(ReportingPeriod.year)).all()) | {year}),
    })


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)):
    period = session_period(request, db)
    if not period:
        return templates.TemplateResponse(request, "first_period.html", {"user": user, "attempted_year": datetime.now(UTC).year, "error": ""})
    if user.role == "department":
        period = pp_period(request, db, user, user.department_id)
        dept = db.get(Department, user.department_id)
        submission = ensure_submission(db, dept.id, period.id)
        db.commit()
        indicators = db.scalars(select(Indicator).where(Indicator.department_id == dept.id, Indicator.period_id == period.id).options(selectinload(Indicator.values))).all()
        issues = sum(1 for i in indicators if indicator_issues(i, period.year))
        return templates.TemplateResponse(request, "dashboard.html", {
            "user": user, "period": period, "department": dept, "department_label": period_name(db, period.id, dept), "submission": submission,
            "indicators": indicators, "issues": issues, "notifications": user_notifications(db, user),
        })

    from .program_service import period_departments
    departments = period_departments(db, period.id)
    periods = db.scalars(select(ReportingPeriod).order_by(ReportingPeriod.year.desc())).all()
    snapshots = db.scalars(select(TemplateSnapshot).where(TemplateSnapshot.period_id == period.id).order_by(TemplateSnapshot.created_at.desc())).all()
    imports = db.scalars(select(ImportBatch).where(ImportBatch.period_id == period.id).order_by(ImportBatch.created_at.desc())).all()
    submissions = db.scalars(select(Submission).where(Submission.period_id == period.id)).all()
    status_map = {s.department_id: s.status for s in submissions}
    unresolved_count = activity_mapping_counts(db, period.id)["total"]
    progress = department_progress_overview(db, period)
    return templates.TemplateResponse(request, "dashboard.html", {
        "user": user, "period": period, "periods": periods, "snapshots": snapshots,
        "imports": imports, "departments": departments, "status_map": status_map,
        "unresolved_count": unresolved_count, "progress_rows": progress["rows"],
        "progress_summary": progress["summary"], "notifications": user_notifications(db, user),
    })


@app.get("/department/{department_id}", response_class=HTMLResponse)
def department_page(department_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)):
    dept = db.get(Department, department_id)
    if not dept:
        raise HTTPException(404)
    period = pp_period(request, db, user, department_id)
    indicators = db.scalars(
        select(Indicator).where(Indicator.department_id == department_id, Indicator.period_id == period.id)
        .options(selectinload(Indicator.values), selectinload(Indicator.subprogram).selectinload(SubProgram.program))
        .order_by(Indicator.id)
    ).all()
    activities = db.scalars(
        select(Activity).where(Activity.department_id == department_id, Activity.period_id == period.id)
        .options(selectinload(Activity.cost_values), selectinload(Activity.subprogram).selectinload(SubProgram.program))
        .order_by(Activity.id)
    ).all()
    submission = ensure_submission(db, department_id, period.id)
    db.commit()
    issue_map = {i.id: indicator_issues(i, period.year) for i in indicators}
    subprograms = db.scalars(select(SubProgram).where(SubProgram.period_id == period.id).order_by(SubProgram.name)).all()
    ind_cols = indicator_columns(period.year)
    act_cols = activity_columns(period.year)
    ind_value_maps = {i.id: {f"{v.year}:{v.value_kind}": v.value for v in i.values} for i in indicators}
    activity_maps = {a.id: {f"{y}:{k}": val for (y, k), val in activity_cost_map(a).items()} for a in activities}
    personnel_rows = db.scalars(select(DepartmentCostValue).where(DepartmentCostValue.department_id == department_id, DepartmentCostValue.period_id == period.id, DepartmentCostValue.category == "personnel_sgk")).all()
    personnel_map = {f"{r.year}:{r.value_kind}": r.amount for r in personnel_rows}
    workflow_events = db.scalars(
        select(SubmissionEvent).where(SubmissionEvent.submission_id == submission.id)
        .order_by(SubmissionEvent.created_at.desc())
    ).all()
    activity_totals = {}
    general_totals = {}
    for col in act_cols:
        key = f"{col['year']}:{col['kind']}"
        activity_values = [activity_maps[a.id].get(key) for a in activities]
        complete = bool(activities) and all(v is not None for v in activity_values)
        activity_totals[key] = sum(activity_values) if complete else None
        general_totals[key] = (sum(activity_values) + personnel_map[key]
                               if complete and personnel_map.get(key) is not None else None)
    from .program_service import activity_source_disagreements
    from .draft_removal_service import removal_available
    return templates.TemplateResponse(request, "department.html", {
        "user": user, "department": dept, "department_label": period_name(db, period.id, dept), "indicators": indicators, "activities": activities,
        "submission": submission, "issue_map": issue_map, "subprograms": subprograms, "period": period,
        "removable": removal_available(db, user, department_id, period),
        "indicator_columns": ind_cols, "activity_columns": act_cols, "indicator_value_maps": ind_value_maps,
        "activity_maps": activity_maps, "personnel_map": personnel_map, "activity_totals": activity_totals,
        "general_totals": general_totals, "workflow_events": workflow_events,
        "source_disagreements": {a.id: activity_source_disagreements(a) for a in activities},
        "funding_maps": {a.id:{f"{v.year}:{v.value_kind}:{v.funding_type}":v.amount for v in a.cost_values} for a in activities},
        "notifications": user_notifications(db, user),
    })


@app.post("/api/indicators/{indicator_id}/save", dependencies=[Depends(require_pp_period)])
async def save_indicator(indicator_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)):
    ind = db.scalar(select(Indicator).where(Indicator.id == indicator_id).options(selectinload(Indicator.values)))
    if not ind:
        raise HTTPException(404)
    data = await request.json()
    period = pp_period(request, db, user, ind.department_id, data, ind.period_id)
    ensure_department_editable(db, user, ind.department_id, period.id)
    name = str(data.get("name", ind.name)).strip()
    unit = str(data.get("unit", ind.unit)).strip()
    if not name or not unit or len(name) > 300 or len(unit) > 50:
        raise HTTPException(422, "Gösterge adı ve birimini kontrol edin.")
    ind.name = name
    ind.unit = unit
    ind.explanation = str(data.get("explanation", ind.explanation)).strip()
    ind.calculation_method = str(data.get("calculation_method", ind.calculation_method)).strip()
    ind.data_source = str(data.get("data_source", ind.data_source)).strip()
    value_map = indicator_value_map(ind)
    for col in indicator_columns(period.year):
        key = f"value_{col['year']}_{col['kind']}"
        if key not in data:
            continue
        value = parse_optional_number(data[key], col["label"])
        existing = value_map.get((col["year"], col["kind"]))
        if existing and existing.state != "verified" and (value is None or value == existing.value):
            continue  # Unrelated edits must not erase or approve unresolved source values.
        if value is None:
            if existing:
                db.delete(existing)
            continue
        if existing:
            existing.value = value
            existing.raw_text = existing.raw_text or str(data[key])
            existing.state = "verified"
        else:
            db.add(IndicatorValue(indicator_id=ind.id, year=col["year"], value_kind=col["kind"], value=value, raw_text=str(data[key]), state="verified"))
    db.commit()
    log(db, user, "indicator_update", "indicator", ind.id)
    refreshed = db.scalar(select(Indicator).where(Indicator.id == ind.id).options(selectinload(Indicator.values)))
    return pp_write_result(period, ind.department_id, issues=indicator_issues(refreshed, period.year))


def activity_subprogram_id(value):
    if value is None or value == "":
        raise HTTPException(422, "Program / Alt Program seçimi zorunlu.")
    if type(value) not in (int, str) or not str(value).strip().isascii() or not str(value).strip().isdecimal():
        raise HTTPException(422, "Program / Alt Program seçimi geçersiz.")
    digits = str(value).strip().lstrip("0")
    if not digits or len(digits) > 19 or int(digits) > 9223372036854775807:
        raise HTTPException(422, "Program / Alt Program seçimi geçersiz.")
    return int(digits)


@app.post("/api/activities", dependencies=[Depends(require_pp_period)])
async def create_activity(request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)):
    if user.role != "department" or not user.department_id:
        raise HTTPException(403)
    data = await request.json()
    period = pp_period(request, db, user, user.department_id, data)
    ensure_department_editable(db, user, user.department_id, period.id)
    name = str(data.get("name", "")).strip()
    if not name:
        raise HTTPException(422, "Faaliyet adı zorunlu.")
    subprogram_id = activity_subprogram_id(data.get("subprogram_id"))
    if not subprogram_id:
        raise HTTPException(422, "Program / Alt Program seçimi zorunlu.")
    sp = db.get(SubProgram, subprogram_id)
    if not sp or sp.period_id != period.id:
        raise HTTPException(422, "Alt program bu döneme ait değil.")
    act = Activity(period_id=period.id, department_id=user.department_id, subprogram_id=subprogram_id, name=name, explanation=str(data.get("explanation", "")).strip())
    db.add(act); db.flush()
    from .program_service import save_activity_costs
    save_activity_costs(db, act, period.year, data, actor=user)
    db.commit(); db.refresh(act)
    log(db, user, "activity_create", "activity", act.id)
    return pp_write_result(period, act.department_id, id=act.id)


@app.put("/api/activities/{activity_id}", dependencies=[Depends(require_pp_period)])
async def update_activity(activity_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)):
    body = await request.body()
    return _update_activity(activity_id, body, db, user, request)


def _update_activity(activity_id: int, body: bytes, db: Session, user: User, request=None):
    # Read the complete body before locking; keep the original validation order.
    act = db.scalar(select(Activity).where(Activity.id == activity_id).with_for_update().options(selectinload(Activity.cost_values)))
    if not act:
        raise HTTPException(404)
    data = json.loads(body)
    period = pp_period(request, db, user, act.department_id, data, act.period_id)
    ensure_department_editable(db, user, act.department_id, period.id)
    name = str(data.get("name", act.name)).strip()
    if not name:
        raise HTTPException(422, "Faaliyet adı zorunlu.")
    if "subprogram_id" in data:
        subprogram_id = activity_subprogram_id(data.get("subprogram_id"))
        if not subprogram_id:
            raise HTTPException(422, "Program / Alt Program seçimi zorunlu.")
        sp = db.get(SubProgram, subprogram_id)
        if not sp or sp.period_id != period.id:
            raise HTTPException(422, "Alt program bu döneme ait değil.")
        if act.card and act.card.subprogram_id != subprogram_id: act.card_id = None
        act.subprogram_id = subprogram_id
    act.name = name
    act.explanation = str(data.get("explanation", act.explanation)).strip()
    from .program_service import save_activity_costs
    save_activity_costs(db, act, period.year, data, actor=user)
    db.commit()
    log(db, user, "activity_update", "activity", act.id)
    db.expire(act, ["cost_values"])
    return pp_write_result(period, act.department_id, cost_totals={
        f"{v.year}:{v.value_kind}": str(v.amount) if v.amount is not None else None
        for v in act.cost_values if v.funding_type == "total"
    })


@app.delete("/api/activities/{activity_id}")
def delete_activity(activity_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(require_user),
                    period: ReportingPeriod = Depends(require_pp_period)):
    act = db.get(Activity, activity_id)
    if not act:
        raise HTTPException(404)
    period = pp_period(request, db, user, act.department_id, {"period_id": period.id}, record_period_id=act.period_id)
    ensure_department_editable(db, user, act.department_id, act.period_id)
    from .models import ActivityCatalogueLink
    db.execute(ActivityCatalogueLink.__table__.delete().where(ActivityCatalogueLink.activity_id == act.id))
    db.delete(act); db.commit()
    log(db, user, "activity_delete", "activity", activity_id)
    return pp_write_result(period, user.department_id)


@app.post("/api/departments/{department_id}/personnel-costs", dependencies=[Depends(require_pp_period)])
async def save_personnel_costs(department_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)):
    data = await request.json()
    period = pp_period(request, db, user, department_id, data)
    ensure_department_editable(db, user, department_id, period.id)
    existing = db.scalars(select(DepartmentCostValue).where(DepartmentCostValue.department_id == department_id, DepartmentCostValue.period_id == period.id, DepartmentCostValue.category == "personnel_sgk")).all()
    value_map = {(v.year, v.value_kind): v for v in existing}
    for col in activity_columns(period.year):
        key = f"cost_{col['year']}_{col['kind']}"
        if key not in data:
            continue
        amount = parse_optional_nonnegative_money(data[key], col["label"])
        row = value_map.get((col["year"], col["kind"]))
        if row and row.state != "verified" and (amount is None or amount == row.amount):
            continue
        if amount is None:
            if row:
                db.delete(row)
            continue
        if row:
            row.amount = amount
            row.state = "verified"
            row.raw_text = row.raw_text or str(data[key])
        else:
            db.add(DepartmentCostValue(department_id=department_id, period_id=period.id, year=col["year"], value_kind=col["kind"], category="personnel_sgk", amount=amount))
    db.commit(); log(db, user, "personnel_cost_update", "department", department_id)
    return pp_write_result(period, department_id)


@app.post("/api/departments/{department_id}/submit", dependencies=[Depends(require_pp_period)])
async def submit_department_request(department_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)):
    data = await request.json() if "application/json" in request.headers.get("content-type", "") else await request.form()
    period = pp_period(request, db, user, department_id, data)
    from starlette.concurrency import run_in_threadpool
    result = await run_in_threadpool(submit_department, department_id, db, user, period.id)
    if isinstance(result, dict):
        return pp_write_result(period, department_id, revision=result["revision"])
    return result


def submit_department(department_id: int, db: Session, user: User, period_id: int | None = None):
    # Callers may pass an actor from another Session; use this transaction's copy.
    user = db.get(User, user.id, populate_existing=True)
    if user.role != "department" or user.department_id != department_id:
        raise HTTPException(403, "Bu PP paketini gönderemezsiniz. Paketin müdürlüğüne ait Müdür veya gönderim yetkili Personel hesabıyla giriş yapın; yetki için Müdürünüze başvurun.")
    released_permissions.require_submit(user)
    period = db.get(ReportingPeriod, period_id) if period_id else active_period(db)
    ensure_department_editable(db, user, department_id, period.id)
    # Serialize submission creation and repeated sends for this department.
    department = db.scalar(select(Department).where(Department.id == department_id).with_for_update())
    if not department:
        raise HTTPException(404)
    # Recheck permission after waiting for any concurrent grant/revoke.
    user = db.get(User, user.id, populate_existing=True)
    released_permissions.require_submit(user)
    submission = ensure_submission(db, department_id, period.id)
    if submission.status == "approved":
        raise HTTPException(409, "Onaylanmış paket yeniden gönderilemez.")
    if submission.status == "submitted":
        raise HTTPException(409, "Paket zaten Strateji incelemesinde.")
    from .program_service import validate_department, department_snapshot
    errors, warnings = validate_department(db, period.id, department_id)
    if errors:
        return JSONResponse({"ok": False, "message": "Kart ve mali tablo kontrollerini tamamlayın.", "errors": errors, "warnings": warnings}, status_code=422)
    submission.status = "submitted"
    submission.submitted_at = datetime.now(UTC).replace(tzinfo=None)
    submission.return_note = ""
    submission.revision = (submission.revision or 0) + 1
    snapshot = department_snapshot(db, period.id, department_id)
    department = db.get(Department, department_id)
    db.add(SubmissionEvent(
        submission_id=submission.id, department_id=department_id, period_id=period.id,
        actor_user_id=user.id, event_type="submitted", revision=submission.revision,
        snapshot_json=json_dumps(snapshot, ensure_ascii=False),
    ))
    db.add(Notification(
        role="strategy", event_type="submission_submitted",
        message=f"{period_name(db, period.id, department)} revizyon {submission.revision} incelemeye gönderildi.",
        link=f"/department/{department_id}?period_id={period.id}",
    ))
    db.commit(); log(db, user, "department_submit", "submission", submission.id, f"revision={submission.revision}")
    return {"ok": True, "revision": submission.revision}


@app.get("/activity-mapping", response_class=HTMLResponse)
def activity_mapping_page(request: Request, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    period = session_period(request, db)
    mapping_states = activity_mapping_states(db, period.id)
    pending_ids = [aid for aid, state in mapping_states.items() if not state["ready"]]
    activities = db.scalars(
        select(Activity).where(Activity.period_id == period.id, Activity.id.in_(pending_ids))
        .options(selectinload(Activity.department))
        .order_by(Activity.department_id, Activity.id)
    ).all()
    departments: dict[int, dict] = {}
    for act in activities:
        group = departments.setdefault(act.department_id, {"department": act.department, "activities": [], "choices": []})
        group["activities"].append(act)
    suggestion_count = 0
    strong_suggestion_count = 0
    for did, group in departments.items():
        choices, by_sp = _department_mapping_choices(db, did, period.id)
        group["choices"] = choices
        suggestions = {}
        for act in group["activities"]:
            suggested, score = _activity_mapping_suggestion(act, choices, by_sp) if not act.subprogram_id else (None, 0)
            suggestions[act.id] = {"subprogram_id": suggested.id if suggested else None, "score": score}
            if suggested:
                suggestion_count += 1
                if score >= 0.50:
                    strong_suggestion_count += 1
        group["suggestions"] = suggestions
    batch_rows = db.scalars(
        select(AuditLog).where(AuditLog.action == "activity_mapping_csv")
        .order_by(AuditLog.created_at.desc()).limit(500)
    ).all()
    batch_groups = {}
    for audit in batch_rows:
        details = dict(part.split("=", 1) for part in audit.details.split(";") if "=" in part)
        batch_id = details.get("batch")
        if not batch_id:
            continue
        group = batch_groups.setdefault(batch_id, {
            "id": batch_id, "created_at": audit.created_at, "count": 0, "can_revert": True,
        })
        group["count"] += 1
        activity = db.get(Activity, audit.entity_id)
        try:
            expected = int(details.get("subprogram_id", ""))
        except ValueError:
            expected = None
        if not activity or activity.period_id != period.id or activity.subprogram_id != expected:
            group["can_revert"] = False
        submission = editable_submission(db, activity.department_id, period.id) if activity else None
        if submission and submission.status in {"submitted", "approved"}:
            group["can_revert"] = False
    recent_batches = list(batch_groups.values())[:10]
    return templates.TemplateResponse(request, "activity_mapping.html", {
        "user": user, "period": period, "groups": list(departments.values()),
        "department_names": {did: period_name(db, period.id, group["department"]) for did, group in departments.items()},
        "unresolved_count": len(activities), "mapping_counts": mapping_gap_counts(mapping_states),
        "mapping_states": mapping_states, "suggestion_count": suggestion_count,
        "strong_suggestion_count": strong_suggestion_count, "recent_batches": recent_batches,
    })


@app.get("/api/activity-mappings/export.csv")
def export_activity_mapping_queue(request: Request, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    period = session_period(request, db)
    mapping_states = activity_mapping_states(db, period.id)
    pending_ids = [aid for aid, state in mapping_states.items() if not state["ready"]]
    activities = db.scalars(
        select(Activity).where(Activity.period_id == period.id, Activity.id.in_(pending_ids))
        .options(selectinload(Activity.department))
        .order_by(Activity.department_id, Activity.id)
    ).all()
    grouped: dict[int, list[Activity]] = {}
    for activity in activities:
        grouped.setdefault(activity.department_id, []).append(activity)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(csv_row(MAPPING_CSV_HEADERS + MAPPING_CSV_STATE_HEADERS))
    for department_id, pending in grouped.items():
        choices, by_sp = _department_mapping_choices(db, department_id, period.id)
        for activity in pending:
            suggested, score = _activity_mapping_suggestion(activity, choices, by_sp) if not activity.subprogram_id else (None, 0)
            suggestion = f"{suggested.program.name} / {suggested.name}" if suggested else ""
            level = "Güçlü" if suggested and score >= 0.50 else "Kontrol gerekli" if suggested else "Öneri yok"
            writer.writerow(csv_row([
                period_name(db, period.id, activity.department), activity.id, activity.name, suggestion,
                round(score * 100), level, "",
                *["Tamam" if mapping_states[activity.id][kind] else "Eksik"
                  for kind in ("subprogram", "card", "catalogue")],
            ]))
    data = ("\ufeff" + output.getvalue()).encode("utf-8")
    headers = {"Content-Disposition": 'attachment; filename="civensa-faaliyet-eslestirme-kuyrugu.csv"'}
    return StreamingResponse(io.BytesIO(data), media_type="text/csv; charset=utf-8", headers=headers)


MAPPING_CSV_HEADERS = [
    "Müdürlük", "Faaliyet ID", "Faaliyet", "Civensa Önerisi",
    "Güven (%)", "Öneri Düzeyi", "Seçilecek Program / Alt Program",
]


MAPPING_CSV_STATE_HEADERS = ["Alt program durumu", "Kart durumu", "Resmî katalog durumu"]


def validate_mapping_csv(data: bytes, db: Session, period: ReportingPeriod):
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return [], ["Dosya UTF-8 kodlamalı CSV olmalı."]
    if "\x00" in text:
        return [], ["CSV dosyasında geçersiz karakter bulundu."]
    reader = csv.DictReader(io.StringIO(text))
    # Accept both existing templates and the export's informational state columns.
    if reader.fieldnames not in (MAPPING_CSV_HEADERS, MAPPING_CSV_HEADERS + MAPPING_CSV_STATE_HEADERS):
        return [], ["Sütun başlıkları indirilen eşleştirme şablonuyla aynı olmalı."]
    try:
        source_rows = list(reader)
    except csv.Error:
        return [], ["CSV satırları okunamadı."]
    if len(source_rows) > 1000:
        return [], ["CSV en fazla 1000 satır içerebilir."]

    resolved, errors, seen = [], [], set()
    for line_no, source in enumerate(source_rows, start=2):
        selection = str(source.get("Seçilecek Program / Alt Program", "")).strip()
        if not selection:
            continue
        prefix = f"Satır {line_no}: "
        try:
            activity_id = int(str(source.get("Faaliyet ID", "")).strip())
        except ValueError:
            errors.append(prefix + "Faaliyet ID sayısal olmalı.")
            continue
        if activity_id in seen:
            errors.append(prefix + "Aynı faaliyet dosyada birden fazla kez seçilmiş.")
            continue
        seen.add(activity_id)
        activity = db.scalar(
            select(Activity).where(Activity.id == activity_id, Activity.period_id == period.id)
            .options(selectinload(Activity.department))
        )
        if not activity:
            errors.append(prefix + "Faaliyet bu dönemde bulunamadı.")
            continue
        row_errors = []
        if activity.subprogram_id is not None:
            row_errors.append("Faaliyet artık eşleştirme kuyruğunda değil; güncel CSV'yi indirin.")
        if not csv_cell_matches(source.get("Müdürlük", ""), period_name(db, period.id, activity.department)):
            row_errors.append("Müdürlük adı güncel kayıtla eşleşmiyor.")
        if not csv_cell_matches(source.get("Faaliyet", ""), activity.name):
            row_errors.append("Faaliyet adı güncel kayıtla eşleşmiyor.")
        choices, _ = _department_mapping_choices(db, activity.department_id, period.id)
        choice_map = {f"{sp.program.name} / {sp.name}": sp for sp in choices}
        # A selection copied from the exported suggestion column may carry the formula guard.
        subprogram = choice_map.get(selection) or {csv_text(key): sp for key, sp in choice_map.items()}.get(selection)
        if not subprogram:
            row_errors.append("Seçilen Program / Alt Program bu müdürlüğün göstergelerinde kullanılmıyor.")
        submission = editable_submission(db, activity.department_id, period.id)
        if submission and submission.status in {"submitted", "approved"}:
            row_errors.append("Müdürlük paketi incelemede veya onaylı; eşleştirme değiştirilemez.")
        if row_errors:
            errors.extend(prefix + message for message in row_errors)
            continue
        resolved.append({"activity": activity, "subprogram": subprogram, "selection": selection})
    if not resolved and not errors:
        errors.append("“Seçilecek Program / Alt Program” sütununda doldurulmuş satır bulunamadı.")
    return resolved, errors


@app.post("/api/activity-mappings/import-preview", dependencies=[Depends(require_pp_period)])
async def preview_activity_mapping_csv(
    request: Request, file: UploadFile = File(...), db: Session = Depends(get_db),
    user: User = Depends(require_strategy),
):
    period = session_period(request, db, await request.form())
    data = await read_upload_limited(file, 512 * 1024, "CSV dosyası")
    rows, errors = validate_mapping_csv(data, db, period)
    return {
        "ok": not errors,
        "count": len(rows),
        "rows": [{
            "activity_id": row["activity"].id,
            "department": period_name(db, period.id, row["activity"].department),
            "activity": row["activity"].name,
            "selection": row["selection"],
        } for row in rows[:100]],
        "errors": errors[:50],
    }


@app.post("/api/activity-mappings/import-apply", dependencies=[Depends(require_pp_period)])
async def apply_activity_mapping_csv(
    request: Request, file: UploadFile = File(...), db: Session = Depends(get_db),
    user: User = Depends(require_strategy),
):
    period = session_period(request, db, await request.form())
    data = await read_upload_limited(file, 512 * 1024, "CSV dosyası")
    rows, errors = validate_mapping_csv(data, db, period)
    if errors:
        raise HTTPException(422, {
            "message": "CSV doğrulaması başarısız; hiçbir eşleştirme kaydedilmedi.",
            "errors": errors[:50],
        })
    batch_id = secrets.token_hex(8)
    for row in rows:
        activity, subprogram = row["activity"], row["subprogram"]
        if activity.card and activity.card.subprogram_id != subprogram.id: activity.card_id = None
        activity.subprogram_id = subprogram.id
        db.add(AuditLog(
            user_id=user.id, action="activity_mapping_csv", entity_type="activity",
            entity_id=activity.id, details=f"batch={batch_id};subprogram_id={subprogram.id}",
        ))
    db.commit()
    counts = activity_mapping_counts(db, period.id)
    return {"ok": True, "updated": len(rows), "remaining": counts["total"], "mapping_gaps": counts, "batch_id": batch_id}


@app.post("/api/activity-mappings/batches/{batch_id}/revert", dependencies=[Depends(require_pp_period)])
async def revert_activity_mapping_batch(
    batch_id: str, request: Request, db: Session = Depends(get_db),
    user: User = Depends(require_strategy),
):
    if len(batch_id) != 16 or any(char not in "0123456789abcdef" for char in batch_id):
        raise HTTPException(404)
    data = await request.json() if "application/json" in request.headers.get("content-type", "") else await request.form()
    period = session_period(request, db, data)
    audits = db.scalars(
        select(AuditLog).where(
            AuditLog.action == "activity_mapping_csv",
            AuditLog.details.contains(f"batch={batch_id};"),
        ).order_by(AuditLog.id)
    ).all()
    if not audits:
        raise HTTPException(404, "Eşleştirme işlem grubu bulunamadı.")
    validated = []
    errors = []
    for audit in audits:
        details = dict(part.split("=", 1) for part in audit.details.split(";") if "=" in part)
        activity = db.get(Activity, audit.entity_id)
        try:
            expected = int(details.get("subprogram_id", ""))
        except ValueError:
            expected = None
        if not activity or activity.period_id != period.id:
            errors.append(f"Faaliyet #{audit.entity_id} artık bulunamıyor.")
            continue
        if activity.subprogram_id != expected:
            errors.append(f"Faaliyet #{activity.id} eşleştirmesi sonradan değişmiş.")
            continue
        submission = editable_submission(db, activity.department_id, period.id)
        if submission and submission.status in {"submitted", "approved"}:
            errors.append(f"{period_name(db, period.id, activity.department)}: paket incelemede veya onaylı.")
            continue
        validated.append(activity)
    if errors:
        db.rollback()
        raise HTTPException(409, {
            "message": "İşlem grubunun tamamı güvenle geri alınamıyor; hiçbir kayıt değiştirilmedi.",
            "errors": errors[:50],
        })
    for activity in validated:
        activity.card_id = None
        activity.subprogram_id = None
    db.add(AuditLog(
        user_id=user.id, action="activity_mapping_csv_revert", entity_type="mapping_batch",
        details=f"batch={batch_id};count={len(validated)}",
    ))
    db.commit()
    return {"ok": True, "reverted": len(validated)}


@app.post("/api/activity-mappings/bulk", dependencies=[Depends(require_pp_period)])
async def save_activity_mappings(request: Request, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    data = await request.json()
    assignments = data.get("assignments", [])
    if not isinstance(assignments, list) or not assignments:
        raise HTTPException(422, "Kaydedilecek eşleştirme seçilmedi.")
    period = session_period(request, db, data)
    validated = []
    errors = []
    seen = set()
    for item in assignments:
        try:
            activity_id = int(item.get("activity_id"))
            subprogram_id = int(item.get("subprogram_id"))
        except (TypeError, ValueError):
            errors.append("Geçersiz faaliyet/alt program kimliği.")
            continue
        if activity_id in seen:
            errors.append(f"Faaliyet #{activity_id} birden fazla kez seçildi.")
            continue
        seen.add(activity_id)
        act = db.get(Activity, activity_id)
        sp = db.get(SubProgram, subprogram_id)
        if not act or act.period_id != period.id:
            errors.append(f"Faaliyet #{activity_id} bu dönemde bulunamadı.")
            continue
        if not sp or sp.period_id != period.id:
            errors.append(f"Alt program #{subprogram_id} bu döneme ait değil.")
            continue
        # Safety: Strategy may only map an activity to a subprogram already used by
        # that department's indicators. This prevents cross-department accidental links.
        valid = db.scalar(select(Indicator.id).where(
            Indicator.period_id == period.id, Indicator.department_id == act.department_id,
            Indicator.subprogram_id == sp.id
        ).limit(1))
        if not valid:
            errors.append(f"'{act.name[:60]}' için seçilen alt program müdürlüğün göstergelerinde kullanılmıyor.")
            continue
        submission = ensure_submission(db, act.department_id, period.id)
        if submission.status in {"submitted", "approved"}:
            errors.append(f"{period_name(db, period.id, act.department)}: paket incelemede/onaylı; eşleştirme değiştirilemez.")
            continue
        validated.append((act, sp))
    if errors:
        db.rollback()
        return JSONResponse({
            "ok": False, "message": "Tüm seçimler doğrulanamadı; hiçbir eşleştirme kaydedilmedi.",
            "updated": 0, "errors": errors[:20],
        }, status_code=422)
    for act, sp in validated:
        if act.card and act.card.subprogram_id != sp.id: act.card_id = None
        act.subprogram_id = sp.id
        db.add(AuditLog(user_id=user.id, action="activity_mapping", entity_type="activity", entity_id=act.id, details=f"subprogram_id={sp.id}"))
    if validated:
        db.commit()
    else:
        db.rollback()
    counts = activity_mapping_counts(db, period.id)
    return {"ok": bool(validated), "updated": len(validated), "remaining": counts["total"], "mapping_gaps": counts, "errors": []}


@app.get("/users", response_class=HTMLResponse)
def users_page(request: Request, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    users = db.scalars(select(User).order_by(User.full_name)).all()
    departments = db.scalars(select(Department).order_by(Department.name)).all()
    assigned_department_ids = {item.department_id for item in users if item.role == "department" and item.department_id and item.is_active}
    missing_departments = [item for item in departments if item.is_active and item.id not in assigned_department_ids]
    return templates.TemplateResponse(request, "users.html", {
        "user": user, "period": session_period(request, db), "users": users, "departments": departments,
        "missing_departments": missing_departments,
        "department_account_count": len(assigned_department_ids),
    })


@app.get("/api/users/template.csv")
@app.get("/api/users/missing-departments.csv")
def missing_department_accounts_csv(db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    # All active directorates: existing personal accounts never prevent adding staff.
    departments = db.scalars(select(Department).where(Department.is_active.is_(True)).order_by(Department.name)).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(csv_row(ACCOUNT_CSV_HEADERS))
    for department in departments:
        writer.writerow(csv_row([department.id, department.name, "", "", ""]))
    data = ("\ufeff" + output.getvalue()).encode("utf-8")
    headers = {"Content-Disposition": 'attachment; filename="civensa-kisisel-hesap-sablonu.csv"',
               "Cache-Control": "no-store"}
    return StreamingResponse(io.BytesIO(data), media_type="text/csv; charset=utf-8", headers=headers)


@app.post("/api/users/bulk-preview")
async def preview_users_csv(file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    data = await read_upload_limited(file, 256 * 1024, "CSV dosyası")
    rows, errors = validate_account_csv(data, db, user)
    return {
        "ok": not errors,
        "count": len(rows),
        "rows": [{key: row[key] for key in ("department_id", "department_name", "full_name", "email", "duty")} for row in rows],
        "errors": errors[:50],
    }


@app.post("/api/users/bulk-import")
async def import_users_csv(file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    data = await read_upload_limited(file, 256 * 1024, "CSV dosyası")
    rows, errors = validate_account_csv(data, db, user)
    if errors:
        raise HTTPException(422, {"message": "CSV doğrulaması başarısız; hiçbir hesap oluşturulmadı.", "errors": errors[:50]})
    batch_id = secrets.token_hex(8)
    # Credentials live only in this response buffer. No token, file, session,
    # database column, or audit detail can retrieve them after the response.
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(csv_row(["Müdürlük", "Ad Soyad", "E-posta", "Görev", "Geçici Parola"]))
    try:
        for row in rows:
            password = temporary_password()
            new_user = User(
                email=row["email"], full_name=row["full_name"], role="department",
                department_id=row["department_id"], password_hash=hash_password(password),
                position=row["position"], can_submit=False, is_active=True, must_change_password=True,
            )
            user, reason = prepare_user_creation(db, user, new_user)
            appointment_reason = f"Toplu hesap oluşturma, CSV {batch_id}"
            if reason:
                appointment_reason += "; " + reason
            db.add(new_user); db.flush()
            released_permissions.audit_user_change(db, user, new_user, "position", None,
                                                   new_user.position, appointment_reason)
            db.add(AuditLog(
                user_id=user.id, action="user_bulk_create_item", entity_type="user", entity_id=new_user.id,
                details=f"batch={batch_id};department_id={row['department_id']}",
            ))
            writer.writerow(csv_row([row["department_name"], row["full_name"], row["email"], row["duty"], password]))
        db.add(AuditLog(user_id=user.id, action="user_bulk_create", entity_type="user",
                        details=f"batch={batch_id};count={len(rows)}"))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Hesaplar başka bir işlemde değişti; Kullanıcılar listesini yenileyin. Oluşturulmuş hesaplar için Parola sıfırla seçin.") from None
    except HTTPException:
        db.rollback()
        raise
    data = ("\ufeff" + output.getvalue()).encode("utf-8")
    output.close()
    return StreamingResponse(io.BytesIO(data), media_type="text/csv; charset=utf-8", headers={
        "Content-Disposition": f'attachment; filename="civensa-gecici-parolalar-{batch_id}.csv"',
        "Cache-Control": "no-store, private", "Pragma": "no-cache",
        "X-Account-Batch": batch_id, "X-Accounts-Created": str(len(rows)),
    })


@app.get("/api/users/batches/{batch_id}/credentials.csv")
def expired_user_credentials(batch_id: str, user: User = Depends(require_strategy)):
    raise HTTPException(410, "Geçici parola dosyası yalnızca hesap oluşturulurken bir kez teslim edilir; tekrar indirilemez. Kullanıcılar ekranında her kullanıcı için Parola sıfırla seçin.")


def deactivate_users(db, actor, targets, reason):
    """Validate the entire selection before changing any account; never delete."""
    # Lock all organizations/departments in the existing administration order.
    dids = {u.department_id for u in [actor, *targets] if u.department_id}
    from .models import Organization
    orgs = set(db.scalars(select(Department.organization_id).where(Department.id.in_(dids))))
    for oid in sorted(orgs):
        db.scalar(select(Organization).where(Organization.id == oid).with_for_update())
    for did in sorted(dids):
        db.scalar(select(Department).where(Department.id == did).with_for_update())
    locked = []
    for target in targets:
        actor, target = released_permissions.lock_user_administration(db, actor, target)
        strategy_director = target.position == "director" and released_permissions.is_strategy_user(db, target)
        if strategy_director:
            released_permissions.require_strategy_user_management(db, actor, target)
        if target.id == actor.id and not strategy_director:
            raise HTTPException(409, "Kendi hesabınızı pasifleştiremezsiniz. Seçimden kendi hesabınızı çıkarın.")
        locked.append(target)
    changed = 0
    for target in locked:
        old = target.is_active
        target.is_active = False
        if old:
            changed += 1
            released_permissions.audit_user_change(db, actor, target, "is_active", True, False, reason)
            db.add(AuditLog(user_id=actor.id, action="user_deactivate", entity_type="user", entity_id=target.id,
                            details=json_dumps({"reason": reason}, ensure_ascii=False)))
    return changed


@app.post("/api/users/bulk-deactivate")
async def bulk_deactivate_users(request: Request, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    data = await request.json()
    ids = data.get("user_ids") if isinstance(data, dict) else None
    reason = data.get("reason", "") if isinstance(data, dict) else ""
    if not isinstance(reason, str) or not reason.strip() or len(reason.strip()) > 1000:
        raise HTTPException(422, "Pasifleştirme gerekçesi eksik veya çok uzun. Gerekçe alanına 1–1000 karakterlik açıklama yazın.")
    if not isinstance(ids, list) or not 1 <= len(ids) <= 200 or any(type(uid) is not int for uid in ids):
        raise HTTPException(422, "Kullanıcı seçimi geçersiz. Kullanıcılar ekranında 1–200 hesap seçin.")
    targets = db.scalars(select(User).where(User.id.in_(set(ids))).order_by(User.id)).all()
    if len(targets) != len(set(ids)):
        raise HTTPException(404, "Seçilen hesaplardan biri bulunamadı. Kullanıcılar listesini yenileyip tekrar seçin.")
    try:
        count = deactivate_users(db, user, targets, reason.strip())
        released_permissions.commit_user_change(db)
    except HTTPException:
        db.rollback()
        raise
    return {"ok": True, "deactivated": count}


@app.post("/api/users/{user_id}/active")
async def set_user_active(user_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(404)
    data = await request.json()
    active = data.get("active")
    if not isinstance(active, bool):
        raise HTTPException(422, "Etkinlik durumu true/false olmalı.")
    user, target = released_permissions.lock_user_administration(db, user, target)
    strategy_director = target.position == "director" and released_permissions.is_strategy_user(db, target)
    reason = None
    if strategy_director:
        reason = released_permissions.require_strategy_user_management(db, user, target, appointment=active)
    if target.id == user.id and not active and not strategy_director:
        raise HTTPException(409, "Kendi hesabınızı devre dışı bırakamazsınız.")
    if active and target.department_id:
        from .master_data_service import active_department
        active_department(db, target.department_id)
    if active and target.position == "director":
        released_permissions.check_director_available(db, target)
    old = target.is_active
    target.is_active = active
    if old != active:
        released_permissions.audit_user_change(db, user, target, "is_active", old, active, reason)
    released_permissions.commit_user_change(db)
    log(db, user, "user_activate" if active else "user_deactivate", "user", target.id)
    return {"ok": True, "active": target.is_active}


@app.post("/api/users/{user_id}/reset-password")
async def reset_user_password(user_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(404)
    data = await request.json()
    password = str(data.get("password", ""))
    if password != password.strip() or len(password) < 8:
        raise HTTPException(422, "Yeni parola en az 8 karakter olmalı ve kenar boşluğu içermemeli.")
    user, target = released_permissions.lock_user_administration(db, user, target)
    if target.position == "director":
        released_permissions.require_strategy_user_management(db, user, target)
    target.password_hash = hash_password(password)
    target.must_change_password = True
    db.commit()
    log(db, user, "user_password_reset", "user", target.id)
    return {"ok": True}


@app.post("/api/users/batches/{batch_id}/revert")
async def revert_user_batch(batch_id: str, request: Request, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    if len(batch_id) != 16 or any(char not in "0123456789abcdef" for char in batch_id):
        raise HTTPException(404)
    audits = db.scalars(select(AuditLog).where(
        AuditLog.action == "user_bulk_create_item", AuditLog.details.contains(f"batch={batch_id};")
    )).all()
    if not audits:
        raise HTTPException(404, "Hesap işlem grubu bulunamadı.")
    targets, errors = [], []
    for audit in audits:
        target = db.get(User, audit.entity_id)
        if not target:
            errors.append(f"Kullanıcı #{audit.entity_id} artık bulunamıyor.")
            continue
        user, target = released_permissions.lock_user_administration(db, user, target)
        if target.position == "director":
            released_permissions.require_strategy_user_management(db, user, target)
        used = db.scalar(select(AuditLog.id).where(AuditLog.user_id == target.id).limit(1))
        if used:
            errors.append(f"{target.email}: hesap kullanılmış; toplu geri alınamaz. Kullanıcılar ekranından gerekçeyle pasifleştirin.")
            continue
        targets.append(target)
    if errors:
        raise HTTPException(409, {"message": "İşlem grubu güvenle geri alınamıyor; hiçbir hesap pasifleştirilmedi.", "errors": errors[:50]})
    deactivate_users(db, user, targets, f"Toplu hesap oluşturmayı geri alma, CSV {batch_id}")
    db.add(AuditLog(user_id=user.id, action="user_bulk_create_revert", entity_type="user_batch", details=f"batch={batch_id};count={len(targets)}"))
    db.commit()
    return {"ok": True, "reverted": len(targets)}


@app.post("/api/users")
async def create_user(request: Request, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    data = await request.json()
    email = str(data.get("email", "")).strip().lower()
    full_name = str(data.get("full_name", "")).strip()
    role = str(data.get("role", "department"))
    password = str(data.get("password", "")).strip()
    if not email or "@" not in email:
        raise HTTPException(422, "Geçerli e-posta gerekli.")
    if not full_name:
        raise HTTPException(422, "Ad soyad gerekli.")
    if role not in {"department", "strategy"}:
        raise HTTPException(422, "Geçersiz rol.")
    if len(password) < 8:
        raise HTTPException(422, "Geçici parola en az 8 karakter olmalı.")
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "Bu e-posta zaten kayıtlı.")
    try:
        department_id = int(data["department_id"]) if data.get("department_id") else None
    except (ValueError, TypeError):
        raise HTTPException(422, "Müdürlük seçimi geçersiz. Kullanıcılar ekranından bir müdürlük seçin.") from None
    if role == "strategy":
        department_id = released_permissions.strategy_department(db).id
    if role == "department" and not department_id:
        raise HTTPException(422, "Müdürlük kullanıcısına müdürlük atanmalı.")
    position = data.get("position", "staff")
    released_permissions.validate_position(position)
    new = User(email=email, full_name=full_name, role=role, department_id=department_id,
               password_hash=hash_password(password), position=position, can_submit=False, is_active=True, must_change_password=True)
    user, reason = prepare_user_creation(db, user, new)
    db.add(new); db.flush()
    released_permissions.audit_user_change(db, user, new, "position", None, position, reason)
    released_permissions.commit_user_change(db); db.refresh(new)
    log(db, user, "user_create", "user", new.id, f"role={role}")
    return {"ok": True, "id": new.id}


@app.get("/review", response_class=HTMLResponse)
def review(request: Request, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    period = session_period(request, db)
    submissions = db.scalars(select(Submission).where(Submission.period_id == period.id)).all()
    rows = [(s, db.get(Department, s.department_id)) for s in submissions]
    event_map = {}
    if submissions:
        events = db.scalars(
            select(SubmissionEvent).where(SubmissionEvent.submission_id.in_([s.id for s in submissions]))
            .order_by(SubmissionEvent.created_at.desc())
        ).all()
        for event in events:
            event_map.setdefault(event.submission_id, []).append(event)
    return templates.TemplateResponse(request, "review.html", {
        "user": user, "rows": rows, "period": period, "event_map": event_map,
        "department_names": {d.id: period_name(db, period.id, d) for _, d in rows},
        "notifications": user_notifications(db, user),
    })


@app.post("/api/submissions/{submission_id}/decision", dependencies=[Depends(require_pp_period)])
async def submission_decision(submission_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    user = db.get(User, user.id, populate_existing=True)
    released_permissions.require_strategy_director(user)
    # Read the body before the row lock: no await may run while FOR UPDATE is held,
    # or a second request blocking on the same row freezes the event loop (A1-F4).
    try:
        data = await request.json()
    except ValueError:
        data = None
    scope = db.get(Submission, submission_id, populate_existing=True)
    if not scope:
        raise HTTPException(404, "Paket bulunamadı. İnceleme kuyruğunu yenileyin.")
    pp_period(request, db, user, scope.department_id, data, scope.period_id)
    # A decision cannot target a draft that becomes submitted while this request
    # waits for the department lock. Recheck the state under the locks below too.
    if scope.status != "submitted":
        raise HTTPException(409, "Yalnızca incelemedeki paket için karar verilebilir.")
    db.scalar(select(Department).where(Department.id == scope.department_id).with_for_update())
    sub = db.scalar(select(Submission).where(Submission.id == submission_id)
                    .with_for_update().execution_options(populate_existing=True))
    if not sub:
        raise HTTPException(404)
    if sub.status != "submitted":
        raise HTTPException(409, "Yalnızca incelemedeki paket için karar verilebilir.")
    from .program_service import department_snapshot
    if not isinstance(data, dict):
        raise HTTPException(422, "Geçersiz karar.")
    decision = data.get("decision")
    note = str(data.get("note", "")).strip()
    if decision == "approve":
        released_permissions.require_independent_pp_approver(db, user, sub)
        from .program_service import validate_department
        errors, warnings = validate_department(db, sub.period_id, sub.department_id)
        if errors:
            raise HTTPException(409, errors)
        sub.status = "approved"; sub.return_note = ""
    elif decision == "return":
        if not note:
            raise HTTPException(422, "İade açıklaması zorunlu.")
        sub.status = "returned"; sub.return_note = note
    else:
        raise HTTPException(422, "Geçersiz karar.")
    sub.reviewed_at = datetime.now(UTC).replace(tzinfo=None)
    department = db.get(Department, sub.department_id)
    db.add(SubmissionEvent(
        submission_id=sub.id, department_id=sub.department_id, period_id=sub.period_id,
        actor_user_id=user.id, event_type=decision, revision=sub.revision or 1, note=note,
        snapshot_json=json_dumps(department_snapshot(db,sub.period_id,sub.department_id),ensure_ascii=False),
    ))
    decision_label = "onaylandı" if decision == "approve" else "düzeltme için iade edildi"
    db.add(Notification(
        role="department", department_id=sub.department_id,
        event_type=f"submission_{decision}",
        message=f"{period_name(db, sub.period_id, department)} revizyon {sub.revision or 1} {decision_label}.",
        link=f"/department/{sub.department_id}?period_id={sub.period_id}",
    ))
    db.commit(); log(db, user, f"submission_{decision}", "submission", sub.id, f"revision={sub.revision or 1};note={note}")
    return {"ok": True, "status": sub.status}


@app.get("/api/notifications")
def notifications_api(db: Session = Depends(get_db), user: User = Depends(require_user)):
    rows = user_notifications(db, user, 50)
    return {
        "unread": sum(1 for row in rows if not row.recipient_is_read),
        "items": [{
            "id": row.id, "event_type": row.event_type, "message": row.message,
            "link": row.link, "is_read": row.recipient_is_read, "created_at": row.created_at.isoformat(),
        } for row in rows],
    }


@app.post("/api/notifications/{notification_id}/read")
def notification_read(notification_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    row = db.scalar(notification_query(user).where(Notification.id == notification_id))
    if not row:
        raise HTTPException(404)
    from .authorization_service import server_now
    receipt = db.scalar(select(NotificationRecipient).where(
        NotificationRecipient.notification_id == row.id, NotificationRecipient.user_id == user.id))
    if receipt is None:
        # Dialect upsert makes concurrent repeat reads idempotent.
        if db.get_bind().dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import insert
        else:
            from sqlalchemy.dialects.sqlite import insert
        db.execute(insert(NotificationRecipient).values(notification_id=row.id, user_id=user.id,
            read_at=server_now(db)).on_conflict_do_nothing(index_elements=['notification_id','user_id']))
    elif receipt.read_at is None:
        receipt.read_at = server_now(db)
    db.commit()
    return {"ok": True}


@app.get("/change-password", response_class=HTMLResponse)
def change_password_page(request: Request, user: User = Depends(require_user)):
    return templates.TemplateResponse(request, "change_password.html", {"user": user})


@app.post("/api/me/change-password")
async def change_own_password(request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)):
    data = await request.json()
    current_password = str(data.get("current_password", ""))
    new_password = str(data.get("new_password", ""))
    confirmation = str(data.get("confirmation", ""))
    if not verify_password(current_password, user.password_hash):
        raise HTTPException(422, "Mevcut parola hatalı.")
    if new_password != confirmation:
        raise HTTPException(422, "Yeni parola ve tekrarı eşleşmiyor.")
    if new_password != new_password.strip() or len(new_password) < 12:
        raise HTTPException(422, "Yeni parola en az 12 karakter olmalı ve kenar boşluğu içermemeli.")
    if new_password == current_password:
        raise HTTPException(422, "Yeni parola mevcut paroladan farklı olmalı.")
    # Compare-and-set against the hash this request was authenticated with: an admin reset
    # committed while this request waited for its body must win, not be overwritten.
    new_hash = hash_password(new_password)
    changed = db.execute(update(User).where(User.id == user.id, User.password_hash == user.password_hash)
                         .values(password_hash=new_hash, must_change_password=False)).rowcount
    if changed != 1:
        db.rollback()
        raise HTTPException(409, "Parolanız bu sırada başka bir işlemle değiştirildi. Yeniden giriş yapıp tekrar deneyin.")
    db.commit()
    # Other sessions of this user are now rejected; keep only the session that made the change,
    # stamped with the hash written here (a reset committed right after must still end it).
    start_user_session(request, user.id, new_hash)
    request.session.pop("must_change_password", None)
    log(db, user, "self_password_change", "user", user.id)
    return {"ok": True}


@app.post("/api/periods/{period_id}/template-upload")
async def upload_template(period_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    period = db.get(ReportingPeriod, period_id)
    if not period:
        raise HTTPException(404)
    filename = (file.filename or "template").replace("/", "_").replace("\\", "_")
    suffix = Path(filename).suffix.lower()
    if suffix not in {".docx", ".xlsx", ".xlsm"}:
        raise HTTPException(415, "Yalnızca DOCX ve XLSX yükleyebilirsiniz.")
    data = await read_upload_limited(file, 10 * 1024 * 1024, "Şablon dosyası")
    validate_office_zip(data, suffix)
    try:
        result = analyze_template(filename, data)
    except Exception as e:
        raise HTTPException(422, f"Şablon okunamadı: {e}")
    snap = TemplateSnapshot(
        period_id=period.id, filename=filename, file_type=result["file_type"],
        fields_json=json_dumps(result["present"], ensure_ascii=False),
        missing_json=json_dumps(result["missing"], ensure_ascii=False),
        extra_json=json_dumps(result["extra"], ensure_ascii=False),
        departments_json=json_dumps(result["departments"], ensure_ascii=False),
    )
    db.add(snap); db.commit(); db.refresh(snap)
    log(db, user, "template_upload", "template_snapshot", snap.id, f"{filename}; eksik={len(result['missing'])}")
    return {"ok": True, "snapshot_id": snap.id, **result}


@app.get("/api/template-snapshots/{snapshot_id}")
def template_snapshot(snapshot_id: int, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    s = db.get(TemplateSnapshot, snapshot_id)
    if not s:
        raise HTTPException(404)
    return {"id": s.id, "period_id": s.period_id, "filename": s.filename, "present": json.loads(s.fields_json), "missing": json.loads(s.missing_json), "extra": json.loads(s.extra_json), "departments": json.loads(s.departments_json)}


@app.post("/api/periods/{period_id}/data-import-preview")
async def data_import_preview(period_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    period = db.get(ReportingPeriod, period_id)
    if not period:
        raise HTTPException(404)
    filename = (file.filename or "data.docx").replace("/", "_").replace("\\", "_")
    if Path(filename).suffix.lower() != ".docx":
        raise HTTPException(415, "Veri içe aktarma önizlemesi şu anda DOCX destekliyor.")
    data = await read_upload_limited(file, 30 * 1024 * 1024, "Veri dosyası")
    validate_office_zip(data, ".docx")
    try:
        parsed = parse_performance_docx(data)
    except Exception as e:
        raise HTTPException(422, f"Performans verisi okunamadı: {e}")
    plan = build_department_plan(db, parsed)
    payload = json_dumps(parsed, ensure_ascii=False)
    batch = ImportBatch(period_id=period.id, filename=filename, status="preview", payload_json=payload, created_by=user.id)
    db.add(batch); db.commit(); db.refresh(batch)
    log(db, user, "data_import_preview", "import_batch", batch.id, f"{filename}; {plan['summary']}")
    preview_departments = [{
        "name": d["name"],
        "block_count": len(d["blocks"]),
        "indicator_count": sum(len(b["indicators"]) for b in d["blocks"]),
        "activity_count": len(d["activities"]),
    } for d in plan["parsed"]["departments"][:12]]
    source_years = plan["summary"].get("source_years", [])
    year_mismatch = bool(source_years and source_years != [period.year])
    errors = import_validation_errors(parsed)
    warnings = list(dict.fromkeys([*plan["parsed"]["warnings"], *errors]))
    if year_mismatch:
        warnings.insert(0, f"Dosya bütçe yılı {source_years}; seçilen Civensa dönemi {period.year}. Uygulama engellendi.")
    return {
        "ok": True, "batch_id": batch.id, "status": batch.status,
        "summary": plan["summary"], "warnings": warnings,
        "errors": errors, "coverage_items": plan["parsed"].get("coverage_items", []),
        "conflicts": plan["conflicts"], "decisions": json.loads(batch.decisions_json or "[]"),
        "review_items": plan["parsed"].get("review_items", []),
        "departments": preview_departments, "mappings": plan["mappings"],
        "can_apply": not plan["unresolved"] and not plan["unresolved_conflicts"] and not year_mismatch and not errors,
    }


@app.get("/api/import-batches/{batch_id}")
def import_batch_detail(batch_id: int, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    batch = db.get(ImportBatch, batch_id)
    if not batch:
        raise HTTPException(404)
    parsed = json.loads(batch.payload_json)
    plan = build_department_plan(db, parsed, json.loads(batch.decisions_json or "[]"))
    period = db.get(ReportingPeriod, batch.period_id)
    source_years = plan["summary"].get("source_years", [])
    year_mismatch = bool(period and source_years and source_years != [period.year])
    errors = import_validation_errors(parsed)
    warnings = list(dict.fromkeys([*plan["parsed"].get("warnings", []), *errors]))
    if year_mismatch:
        warnings.insert(0, f"Dosya bütçe yılı {source_years}; seçilen Civensa dönemi {period.year}. Uygulama engellendi.")
    can_revert, revert_reason = import_revert_status(db, batch)
    return {
        "id": batch.id, "filename": batch.filename, "status": batch.status,
        "summary": plan["summary"], "warnings": warnings,
        "errors": errors, "coverage_items": plan["parsed"].get("coverage_items", []),
        "conflicts": plan["conflicts"], "decisions": json.loads(batch.decisions_json or "[]"),
        "review_items": plan["parsed"].get("review_items", []),
        "departments": [{
            "name": d["name"], "block_count": len(d["blocks"]),
            "indicator_count": sum(len(b["indicators"]) for b in d["blocks"]),
            "activity_count": len(d["activities"]),
        } for d in plan["parsed"].get("departments", [])],
        "mappings": plan["mappings"], "can_apply": batch.status == "preview" and not plan["unresolved"] and not plan["unresolved_conflicts"] and not year_mismatch and not errors,
        "can_revert": can_revert, "revert_reason": revert_reason,
    }


@app.post("/api/import-batches/{batch_id}/conflicts/{conflict_id}/decision")
async def import_conflict_decision(batch_id: int, conflict_id: str, request: Request,
                                   db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    body = await request.body()
    return _import_conflict_decision(batch_id, conflict_id, body, db, user)


def _import_conflict_decision(batch_id: int, conflict_id: str, body: bytes, db: Session, user: User):
    # No await can occur while the batch lock is held.
    batch = db.scalar(select(ImportBatch).where(ImportBatch.id == batch_id).with_for_update())
    if not batch:
        raise HTTPException(404)
    data = json.loads(body)
    from .import_service import decide_import_conflict
    try:
        decide_import_conflict(db, batch, conflict_id, data.get("chosen_amount"), data.get("reason"), user)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(422, str(exc)) from None
    return import_batch_detail(batch_id, db, user)


@app.post("/api/import-batches/{batch_id}/apply")
def apply_data_import(batch_id: int, preserve_existing: bool = False, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    batch = db.scalar(select(ImportBatch).where(ImportBatch.id == batch_id).with_for_update())
    if not batch:
        raise HTTPException(404)
    try:
        result = apply_import_batch(db, batch, preserve_existing=preserve_existing)
        db.commit()
    except ValueError as e:
        db.rollback()
        raise HTTPException(409, str(e))
    except Exception:
        db.rollback()
        raise
    log(db, user, "data_import_apply", "import_batch", batch.id, json_dumps(result, ensure_ascii=False))
    return {"ok": True, "status": batch.status, **result}


@app.post("/api/import-batches/{batch_id}/revert")
def revert_data_import(batch_id: int, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    batch = db.scalar(select(ImportBatch).where(ImportBatch.id == batch_id).with_for_update())
    if not batch:
        raise HTTPException(404)
    try:
        result = revert_import_batch(db, batch)
        db.commit()
    except ValueError as e:
        db.rollback()
        raise HTTPException(409, str(e))
    except Exception:
        db.rollback()
        raise
    log(db, user, "data_import_revert", "import_batch", batch.id, json_dumps(result, ensure_ascii=False))
    return {"ok": True, "status": batch.status, **result}


@app.post("/period/select/{period_id}")
def select_period(period_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    period = db.get(ReportingPeriod, period_id)
    if not period:
        raise HTTPException(404)
    request.session["period_id"] = period.id
    return RedirectResponse(f"/dashboard?period_id={period.id}", 303)


def create_period_record(db: Session, user: User, data):
    raw_year = str(data.get("year", "")).strip()
    if not raw_year.isascii() or not raw_year.isdigit() or len(raw_year) != 4 or not 2020 <= int(raw_year) <= 2100:
        raise HTTPException(422, "Dönem yılı geçersiz. Dönem yılı alanına 2020–2100 arasında dört haneli bir yıl girin.")
    year = int(raw_year)
    if db.scalar(select(ReportingPeriod).where(ReportingPeriod.year == year)):
        raise HTTPException(409, f"{year} dönemi zaten var. Genel Bakış ekranında mevcut dönemi seçin veya farklı bir yıl girin.")
    base_id = data.get("base_period_id")
    base = active_period(db)
    if base_id:
        try: base = db.get(ReportingPeriod, int(base_id))
        except (TypeError, ValueError): base = None
        if not base:
            raise HTTPException(422, "Başlangıç dönemi bulunamadı. Başlangıç yapısı alanından mevcut bir dönem seçin.")
    from .models import Organization
    from .structure_service import lock_organization
    for oid in db.scalars(select(Organization.id).order_by(Organization.id)):
        lock_organization(db, oid)
    period = ReportingPeriod(year=year, status="draft", template_status="pending")
    db.add(period); db.flush()
    program_map = {}; sub_map = {}
    if base:
        programs = db.scalars(select(Program).where(Program.period_id == base.id)).all()
        for old in programs:
            new = Program(period_id=period.id, name=old.name); db.add(new); db.flush(); program_map[old.id] = new.id
        subs = db.scalars(select(SubProgram).where(SubProgram.period_id == base.id)).all()
        for old in subs:
            new = SubProgram(period_id=period.id, program_id=program_map[old.program_id], name=old.name, rationale=old.rationale, goal=old.goal)
            db.add(new); db.flush(); sub_map[old.id] = new.id
        from .structure_service import copy_period_work
        copy_period_work(db, user, base, period, sub_map)
    from .master_data_service import audit_change
    audit_change(db, user, "period_create", period, None, {"year": year, "status": "draft", "template_status": "pending", "base_period_id": base.id if base else None})
    db.commit()
    return period


@app.post("/api/periods")
async def create_period(request: Request, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    data = await request.json()
    try:
        period = create_period_record(db, user, data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Dönem başka bir işlemde oluşturuldu. Genel Bakış ekranında mevcut dönemi seçin veya farklı bir yıl girin.") from None
    from .models import AuditLog
    copy_audit = db.scalar(select(AuditLog).where(AuditLog.action == 'structure_period_copy', AuditLog.entity_id == period.id).order_by(AuditLog.id.desc()))
    return {"ok": True, "id": period.id, "year": period.year, "untransferred": json.loads(copy_audit.details)['new']['untransferred'] if copy_audit else []}


@app.post("/periods/create")
async def create_period_form(request: Request, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    data = await request.form()
    try:
        period = create_period_record(db, user, data)
    except (HTTPException, IntegrityError) as exc:
        db.rollback()
        return templates.TemplateResponse(request, "first_period.html", {"user": user, "attempted_year": data.get("year", ""),
            "error": exc.detail if isinstance(exc, HTTPException) else "Dönem başka bir işlemde oluşturuldu. Genel Bakış ekranından dönemi seçin."},
            status_code=exc.status_code if isinstance(exc, HTTPException) else 409)
    request.session["period_id"] = period.id
    return RedirectResponse(f"/dashboard?period_id={period.id}", 303)


@app.post("/api/periods/{period_id}/verify-template")
def verify_period_template(period_id: int, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    period = db.get(ReportingPeriod, period_id)
    if not period:
        raise HTTPException(404)
    period.template_status = "verified"; db.commit()
    log(db, user, "template_verify", "reporting_period", period.id)
    return {"ok": True}


@app.post("/api/periods/{period_id}/activate")
def activate_period(period_id: int, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    period = db.get(ReportingPeriod, period_id)
    if not period:
        raise HTTPException(404)
    if period.template_status != "verified":
        raise HTTPException(409, "Bakanlık şablonu doğrulanmadan dönem aktif edilemez.")
    for p in db.scalars(select(ReportingPeriod)).all():
        if p.status == "active":
            p.status = "closed"
    period.status = "active"; db.commit()
    log(db, user, "period_activate", "reporting_period", period.id)
    return {"ok": True}


@app.get("/health")
def health():
    backend = engine.url.get_backend_name()
    started = time.perf_counter()
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
        database_status = "ok"
    except Exception:
        database_status = "error"
    database_latency_ms = round((time.perf_counter() - started) * 1000, 1)
    payload = {
        "status": "ok" if database_status == "ok" else "degraded",
        "app": "civensa",
        "version": APP_VERSION,
        "environment": "production" if is_production() else "qa",
        "database": {
            "backend": backend, "status": database_status,
            "latency_ms": database_latency_ms,
        },
    }
    return payload if database_status == "ok" else JSONResponse(payload, status_code=503)


@app.get("/export/department/{department_id}.json")
def export_department(department_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    dept = db.get(Department, department_id)
    if not dept:
        raise HTTPException(404)
    period = session_period(request, db)
    submission = db.scalar(select(Submission).where(Submission.department_id == department_id, Submission.period_id == period.id))
    if not submission or submission.status != "approved":
        raise HTTPException(409, "Çıktı yalnızca Strateji onayından sonra alınabilir.")
    from .program_service import department_snapshot
    return department_snapshot(db, period.id, department_id)


@app.get("/export/department/{department_id}.docx")
def export_department_docx(department_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    dept = db.get(Department, department_id)
    if not dept:
        raise HTTPException(404)
    period = session_period(request, db)
    submission = db.scalar(select(Submission).where(Submission.department_id == department_id, Submission.period_id == period.id))
    if not submission or submission.status != "approved":
        raise HTTPException(409, "Çıktı yalnızca Strateji onayından sonra alınabilir.")
    from .program_service import department_snapshot, validate_department
    issues, _ = validate_department(db, period.id, department_id)
    if issues: raise HTTPException(409, issues)
    from .book_export import export_book
    payload = {"period": period.year, "departments": [department_snapshot(db, period.id, department_id)]}
    output, mime = export_book(payload, "docx")
    filename = quote(f"{period.year}-{dept.name}-performans-raporu.docx")
    log(db, user, "department_export_docx", "department", dept.id, f"period_id={period.id}")
    return StreamingResponse(io.BytesIO(output), media_type=mime, headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"})


@app.get("/api/operations/status")
def operations_status(request: Request, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    period = session_period(request, db)
    def count(model, *conditions):
        return db.scalar(select(func.count()).select_from(model).where(*conditions)) or 0
    submission_rows = db.execute(
        select(Submission.status, func.count(Submission.id))
        .where(Submission.period_id == period.id)
        .group_by(Submission.status)
    ).all()
    latest_audit = db.scalar(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(1))
    mapping_states = activity_mapping_states(db, period.id)
    unresolved = db.scalars(
        select(Activity).where(Activity.period_id == period.id,
                               Activity.id.in_([aid for aid, state in mapping_states.items() if not state["ready"]]))
    ).all()
    mapping_suggestions = 0
    strong_mapping_suggestions = 0
    unresolved_by_department: dict[int, list[Activity]] = {}
    for activity in unresolved:
        unresolved_by_department.setdefault(activity.department_id, []).append(activity)
    for department_id, pending in unresolved_by_department.items():
        choices, by_sp = _department_mapping_choices(db, department_id, period.id)
        for activity in pending:
            if activity.subprogram_id:
                continue
            suggested, score = _activity_mapping_suggestion(activity, choices, by_sp)
            if suggested:
                mapping_suggestions += 1
                if score >= 0.50:
                    strong_mapping_suggestions += 1
    return {
        "status": "ok",
        "version": APP_VERSION,
        "environment": "production" if is_production() else "qa",
        "database": health()["database"],
        "period": {"id": period.id, "year": period.year, "status": period.status},
        "records": {
            "departments": count(Department),
            "department_accounts": count(User, User.role == "department", User.is_active.is_(True), User.department_id.is_not(None)),
            "missing_department_accounts": max(
                0,
                db.scalar(select(func.count(Department.id)).where(Department.is_active.is_(True),
                    ~exists().where(User.department_id == Department.id, User.role == "department", User.is_active.is_(True)))),
            ),
            "indicators": count(Indicator, Indicator.period_id == period.id),
            "activities": count(Activity, Activity.period_id == period.id),
            "unresolved_activities": len(unresolved),
            "mapping_gaps": mapping_gap_counts(mapping_states),
            "mapping_suggestions": mapping_suggestions,
            "strong_mapping_suggestions": strong_mapping_suggestions,
            "workflow_events": count(SubmissionEvent, SubmissionEvent.period_id == period.id),
            "unread_notifications": count(Notification, Notification.is_read.is_(False)),
        },
        "submissions": {status: total for status, total in submission_rows},
        "latest_audit_at": latest_audit.created_at.isoformat() if latest_audit else None,
    }


@app.get("/api/release/readiness")
def release_readiness(request: Request, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    operations = operations_status(request, db, user)
    with engine.connect() as connection:
        migration = connection.exec_driver_sql("SELECT version_num FROM alembic_version").scalar()
        orphan_activities = connection.exec_driver_sql(
            "SELECT count(*) FROM activities a LEFT JOIN departments d ON d.id=a.department_id WHERE d.id IS NULL"
        ).scalar()
        orphan_indicators = connection.exec_driver_sql(
            "SELECT count(*) FROM indicators i LEFT JOIN departments d ON d.id=i.department_id WHERE d.id IS NULL"
        ).scalar()
    duplicate_accounts = db.execute(
        select(User.department_id, func.count(User.id)).where(
            User.position == "director", User.is_active.is_(True), User.department_id.is_not(None)
        ).group_by(User.department_id).having(func.count(User.id) > 1)
    ).all()
    checks = {
        "database": operations["database"]["status"] == "ok",
        "migration_head": migration == migration_head(),
        "period_active": operations["period"]["status"] == "active",
        "departments_present": operations["records"]["departments"] > 0,
        "indicators_present": operations["records"]["indicators"] > 0,
        "activities_present": operations["records"]["activities"] > 0,
        "activity_mappings_complete": operations["records"]["unresolved_activities"] == 0,
        "no_orphan_activities": orphan_activities == 0,
        "no_orphan_indicators": orphan_indicators == 0,
        "no_duplicate_active_department_accounts": len(duplicate_accounts) == 0,
        "workflow_schema_present": inspect(engine).has_table("submission_events") and inspect(engine).has_table("notifications"),
    }
    warnings = []
    if operations["records"]["missing_department_accounts"]:
        warnings.append(f"{operations['records']['missing_department_accounts']} müdürlüğün etkin hesabı yok.")
    if operations["records"]["unresolved_activities"]:
        warnings.append(f"{operations['records']['unresolved_activities']} faaliyet insan eşleştirmesi bekliyor.")
    return {
        "status": "ready" if all(checks.values()) else "blocked",
        "version": APP_VERSION, "checks": checks, "warnings": warnings,
        "migration": migration, "checked_at": datetime.now(UTC).isoformat(),
    }


@app.get("/operations", response_class=HTMLResponse)
def operations_page(request: Request, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    payload = operations_status(request, db, user)
    readiness = release_readiness(request, db, user)
    return templates.TemplateResponse(request, "operations.html", {
        "user": user,
        "operations": payload,
        "readiness": readiness,
        "period": payload["period"],
    })


@app.get("/api/operations/backup.json")
def operations_backup(db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    """Portable logical snapshot without authentication secrets."""
    excluded_columns = {"password_hash"}
    payload = {
        "format": "civensa-logical-backup-v1",
        "app_version": APP_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "tables": {},
    }
    with engine.connect() as connection:
        for table in Base.metadata.sorted_tables:
            rows = []
            for row in connection.execute(select(table)).mappings():
                item = {}
                for key, value in row.items():
                    if key in excluded_columns:
                        continue
                    item[key] = value.isoformat() if isinstance(value, datetime) else value
                rows.append(item)
            payload["tables"][table.name] = rows
    raw = json_dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    log(db, user, "operations_backup_export", "database", details=f"bytes={len(raw)}")
    filename = f"civensa-backup-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}.json"
    return StreamingResponse(
        io.BytesIO(raw), media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def audit_query(request: Request, db: Session):
    action = request.query_params.get("action", "").strip()
    user_text = request.query_params.get("user", "").strip().lower()
    query = select(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
    if action:
        query = query.where(AuditLog.action == action)
    if user_text:
        matching_users = db.scalars(select(User.id).where(func.lower(User.email).contains(user_text))).all()
        query = query.where(AuditLog.user_id.in_(matching_users or [-1]))
    return query, action, user_text


def safe_audit_details(value: str):
    text = str(value or "")
    lowered = text.lower()
    if "password" in lowered or "parola" in lowered:
        return "[hassas ayrıntı gizlendi]"
    return text


@app.get("/audit", response_class=HTMLResponse)
def audit_page(request: Request, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    query, action, user_text = audit_query(request, db)
    try:
        page = max(1, int(request.query_params.get("page", "1")))
    except ValueError:
        page = 1
    per_page = 100
    rows = db.scalars(query.offset((page - 1) * per_page).limit(per_page + 1)).all()
    user_ids = {row.user_id for row in rows if row.user_id}
    users = {item.id: item for item in db.scalars(select(User).where(User.id.in_(user_ids))).all()} if user_ids else {}
    actions = db.scalars(select(AuditLog.action).distinct().order_by(AuditLog.action)).all()
    return templates.TemplateResponse(request, "audit.html", {
        "user": user, "period": session_period(request, db), "rows": rows[:per_page], "users": users, "actions": actions,
        "selected_action": action, "user_text": user_text, "page": page,
        "has_next": len(rows) > per_page, "safe_details": safe_audit_details,
    })


@app.get("/api/audit/export.csv")
def audit_export(request: Request, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    query, _, _ = audit_query(request, db)
    rows = db.scalars(query.limit(5000)).all()
    user_ids = {row.user_id for row in rows if row.user_id}
    users = {item.id: item for item in db.scalars(select(User).where(User.id.in_(user_ids))).all()} if user_ids else {}
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(csv_row(["Tarih", "Kullanıcı", "İşlem", "Varlık", "Varlık ID", "Ayrıntı"]))
    for row in rows:
        actor = users.get(row.user_id)
        writer.writerow(csv_row([row.created_at.isoformat(sep=" "), actor.email if actor else "sistem", row.action, row.entity_type, row.entity_id or "", safe_audit_details(row.details)]))
    data = ("\ufeff" + output.getvalue()).encode("utf-8")
    return StreamingResponse(io.BytesIO(data), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": 'attachment; filename="civensa-denetim-gecmisi.csv"'})


PROGRESS_LABELS = {
    "not_started": "Başlamadı",
    "in_progress": "Veri girişi devam ediyor",
    "needs_attention": "Eksikleri / hataları var",
    "ready": "Gönderime hazır",
    "submitted": "İnceleme bekliyor",
    "returned": "İade edildi",
    "approved": "Tamamlandı",
}


def department_progress_overview(db: Session, period: ReportingPeriod):
    from .program_service import validate_department, period_departments
    departments = period_departments(db, period.id)
    submissions = db.scalars(select(Submission).where(Submission.period_id == period.id)).all()
    submission_by_department = {item.department_id: item for item in submissions}
    indicators = db.scalars(
        select(Indicator).where(Indicator.period_id == period.id).options(selectinload(Indicator.values))
    ).all()
    activities = db.scalars(
        select(Activity).where(Activity.period_id == period.id).options(selectinload(Activity.cost_values))
    ).all()
    indicators_by_department = {}
    activities_by_department = {}
    mapping_states = activity_mapping_states(db, period.id)
    for indicator in indicators:
        indicators_by_department.setdefault(indicator.department_id, []).append(indicator)
    for activity in activities:
        activities_by_department.setdefault(activity.department_id, []).append(activity)

    department_users = db.scalars(select(User).where(User.role == "department", User.is_active.is_(True))).all()
    user_department = {item.id: item.department_id for item in department_users if item.department_id}
    departments_with_users = {item.department_id for item in department_users if item.department_id}
    last_activity = {}
    # Only count edits that still point to real period data. This deliberately
    # ignores deleted activities, including release persistence probes, so
    # operational tests cannot make a department look as if it started work.
    activity_department = {item.id: item.department_id for item in activities}
    direct_actions = {"indicator_update", "personnel_cost_update", "department_submit"}
    if user_department:
        audit_rows = db.scalars(
            select(AuditLog)
            .where(AuditLog.user_id.in_(list(user_department)))
            .order_by(AuditLog.created_at)
        ).all()
        for audit in audit_rows:
            department_id = user_department.get(audit.user_id)
            counts_as_progress = audit.action in direct_actions
            if audit.action in {"activity_create", "activity_update"}:
                counts_as_progress = activity_department.get(audit.entity_id) == department_id
            if department_id and counts_as_progress:
                last_activity[department_id] = audit.created_at

    rows = []
    summary = {key: 0 for key in PROGRESS_LABELS}
    summary["missing_accounts"] = 0
    for department in departments:
        dept_indicators = indicators_by_department.get(department.id, [])
        dept_activities = activities_by_department.get(department.id, [])
        indicator_problem_count = sum(
            len(indicator_issues(indicator, period.year)) for indicator in dept_indicators
        )
        mapping_counts = mapping_gap_counts({activity.id: mapping_states[activity.id] for activity in dept_activities})
        unresolved_count = mapping_counts["total"]
        total_checks = len(dept_indicators) * 6 + len(dept_activities)
        completed_checks = max(
            0,
            len(dept_indicators) * 6 - indicator_problem_count
            + len(dept_activities) - unresolved_count,
        )
        calculated_progress = round((completed_checks / total_checks) * 100) if total_checks else 0
        submission = submission_by_department.get(department.id)
        submission_status = submission.status if submission else "draft"
        activity_at = last_activity.get(department.id)
        validation_errors, _ = validate_department(db, period.id, department.id)
        warning_count = max(indicator_problem_count + unresolved_count, len(validation_errors))
        if validation_errors:
            calculated_progress = min(calculated_progress, 99)

        if submission_status == "approved":
            state, progress_percent = "approved", 100
        elif submission_status == "submitted":
            state, progress_percent = "submitted", 100
        elif submission_status == "returned":
            state, progress_percent = "returned", calculated_progress
        elif not activity_at:
            state, progress_percent = "not_started", 0
        elif warning_count:
            state, progress_percent = "needs_attention", calculated_progress
        elif calculated_progress >= 100:
            state, progress_percent = "ready", 100
        else:
            state, progress_percent = "in_progress", calculated_progress

        has_department_user = department.id in departments_with_users
        summary[state] += 1
        if department.is_active and not has_department_user:
            summary["missing_accounts"] += 1
        rows.append({
            "department_id": department.id,
            "department_name": period_name(db, period.id, department), "is_active": department.is_active,
            "state": state,
            "label": PROGRESS_LABELS[state],
            "progress_percent": progress_percent,
            "warning_count": warning_count,
            "indicator_issues": indicator_problem_count,
            "unresolved_activities": unresolved_count,
            "mapping_gaps": mapping_counts,
            "indicator_count": len(dept_indicators),
            "activity_count": len(dept_activities),
            "has_department_user": has_department_user,
            "last_activity_at": activity_at.isoformat() if activity_at else None,
        })
    return {"rows": rows, "summary": summary, "total": len(rows)}


@app.get("/api/progress")
def progress_status(request: Request, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    period = session_period(request, db)
    payload = department_progress_overview(db, period)
    return {
        "status": "ok",
        "version": APP_VERSION,
        "period": {"id": period.id, "year": period.year},
        **payload,
    }

from .program_routes import register as register_program_routes
register_program_routes(app)
from .activity_contract_routes import register as register_activity_contract_routes
register_activity_contract_routes(app)

from . import master_data_routes
master_data_routes.register(app)
released_permissions.register(app)

from .activity_sections_routes import register as register_activity_sections_routes
register_activity_sections_routes(app)

from .activity_financial_routes import register as register_activity_financial_routes
register_activity_financial_routes(app)

from .assurance_routes import register as register_assurance_routes
register_assurance_routes(app)
from . import budget_routes
budget_routes.register(app)

from .internal_control_routes import register as register_internal_control_routes
register_internal_control_routes(app)

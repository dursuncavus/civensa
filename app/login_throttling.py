"""Persistent rolling login limits; the caller commits with the login outcome.

PostgreSQL transaction advisory locks serialize both identities, including the
first attempt, across processes. Keep the locks through password verification
and commit so a concurrent success cannot bypass a newly started lock.
"""
from datetime import UTC, datetime, timedelta
import hashlib
import json
import secrets

from sqlalchemy import Boolean, DateTime, Index, String, delete, func, select, update
from sqlalchemy.orm import Mapped, Session, mapped_column

from .db import Base
from .security import hash_password


WINDOW = timedelta(minutes=15)
RETENTION = timedelta(hours=24)
EMAIL_LIMIT = 5
IP_LIMIT = 20
LOCK_MESSAGE = "Çok sayıda hatalı giriş denemesi yapıldı. Lütfen 15 dakika sonra tekrar deneyin."
DUMMY_PASSWORD_HASH = hash_password(secrets.token_hex(32))


class LoginAttempt(Base):
    __tablename__ = "login_attempts"
    id: Mapped[int] = mapped_column(primary_key=True)
    email_key: Mapped[str] = mapped_column(String(64))
    ip_key: Mapped[str] = mapped_column(String(64))
    failed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    email_cleared: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    email_locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ip_locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    __table_args__ = (
        Index("ix_login_attempts_email_time", "email_key", "failed_at"),
        Index("ix_login_attempts_ip_time", "ip_key", "failed_at"),
        Index("ix_login_attempts_failed_at", "failed_at"),
    )


def identity_key(scope: str, value: str) -> str:
    # Bounded keys also keep submitted e-mail/IP values out of the audit log.
    return hashlib.sha256((scope + "\0" + value).encode()).hexdigest()


def _lock_number(key: str) -> int:
    return int.from_bytes(bytes.fromhex(key)[:8], "big", signed=True)


def server_now(db: Session) -> datetime:
    # clock_timestamp(), unlike now(), advances while waiting for another login.
    if db.get_bind().dialect.name == "postgresql":
        return db.scalar(select(func.clock_timestamp()))
    return datetime.now(UTC)


def begin_attempt(db: Session, email: str, client_ip: str) -> tuple[str, str, datetime, bool]:
    email_key = identity_key("email", email.strip().lower())
    ip_key = identity_key("ip", client_ip)
    postgres = db.get_bind().dialect.name == "postgresql"
    if postgres:
        # One stable order even when e-mail and IP overlap across requests.
        for number in sorted({_lock_number(email_key), _lock_number(ip_key)}):
            db.execute(select(func.pg_advisory_xact_lock(number)))
    now = server_now(db)
    # Cleanup never touches recent counters/locks. A nonblocking global lock
    # avoids concurrent cleanup scans contending on the same expired rows.
    cleanup = not postgres or db.scalar(select(func.pg_try_advisory_xact_lock(
        _lock_number(identity_key("cleanup", "login_attempts")))))
    if cleanup:
        db.execute(delete(LoginAttempt).where(LoginAttempt.failed_at < now - RETENTION))
    locked = db.scalar(select(LoginAttempt.id).where(
        ((LoginAttempt.email_key == email_key) & (LoginAttempt.email_locked_until > now))
        | ((LoginAttempt.ip_key == ip_key) & (LoginAttempt.ip_locked_until > now))
    ).limit(1)) is not None
    return email_key, ip_key, now, locked


def record_failure(db: Session, email_key: str, ip_key: str, now: datetime) -> bool:
    from .models import AuditLog

    email_count = db.scalar(select(func.count(LoginAttempt.id)).where(
        LoginAttempt.email_key == email_key,
        LoginAttempt.failed_at > now - WINDOW,
        LoginAttempt.email_cleared.is_(False),
    )) + 1
    ip_count = db.scalar(select(func.count(LoginAttempt.id)).where(
        LoginAttempt.ip_key == ip_key, LoginAttempt.failed_at > now - WINDOW,
    )) + 1
    row = LoginAttempt(email_key=email_key, ip_key=ip_key, failed_at=now)
    for scope, count, limit, key in (
        ("email", email_count, EMAIL_LIMIT, email_key),
        ("ip", ip_count, IP_LIMIT, ip_key),
    ):
        if count >= limit:
            until = now + WINDOW
            setattr(row, scope + "_locked_until", until)
            db.add(AuditLog(
                action="login_throttle_lock", entity_type="login_throttle",
                created_at=now.replace(tzinfo=None),
                details=json.dumps({"scope": scope, "key_sha256": key,
                                    "failure_limit": limit, "locked_until": until.isoformat()}),
            ))
    db.add(row)
    db.flush()
    return email_count >= EMAIL_LIMIT or ip_count >= IP_LIMIT


def clear_email_failures(db: Session, email_key: str, now: datetime) -> None:
    # Preserve failures for the IP even after this e-mail authenticates.
    db.execute(update(LoginAttempt).where(
        LoginAttempt.email_key == email_key,
        LoginAttempt.failed_at > now - WINDOW,
        LoginAttempt.email_cleared.is_(False),
    ).values(email_cleared=True))

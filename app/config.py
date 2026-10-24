import os

DEV_SECRETS = {
    "civensa-dev-secret-change-in-production",
    "change-me-in-production",
    "dev-secret",
}


def env_name() -> str:
    return os.getenv("CIVENSA_ENV", "development").strip().lower()


def is_production() -> bool:
    return env_name() in {"production", "prod"}


def session_secret() -> str:
    value = os.getenv("SESSION_SECRET", "civensa-dev-secret-change-in-production")
    if is_production() and (not value or value in DEV_SECRETS or len(value) < 32):
        raise RuntimeError("Production ortamında en az 32 karakterlik güçlü SESSION_SECRET zorunludur.")
    return value


def cookie_secure() -> bool:
    raw = os.getenv("COOKIE_SECURE", "1" if is_production() else "0").strip().lower()
    value = raw in {"1", "true", "yes", "on"}
    if is_production() and not value:
        raise RuntimeError("Production ortamında COOKIE_SECURE=1 zorunludur.")
    return value


def demo_seed_enabled() -> bool:
    raw = os.getenv("DEMO_SEED", "0").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def login_ip_limit() -> int:
    raw = os.getenv("CIVENSA_LOGIN_IP_LIMIT", "0").strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError("CIVENSA_LOGIN_IP_LIMIT sıfır veya pozitif bir tam sayı olmalıdır.") from exc
    if value < 0:
        raise RuntimeError("CIVENSA_LOGIN_IP_LIMIT sıfır veya pozitif bir tam sayı olmalıdır.")
    return value


def validate_runtime_settings() -> None:
    session_secret()
    cookie_secure()
    login_ip_limit()
    attachment_max_bytes()
    pp_image_max_bytes()
    pp_image_max_pixels()


def positive_setting(name: str, default: int) -> int:
    """Read a positive upload setting; defaults retain the existing limits."""
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        value = 0
    if value <= 0:
        raise RuntimeError(f'{name} pozitif bir tam sayı olmalıdır. Yükleme sınırı ayarını düzeltip uygulamayı yeniden başlatın.')
    return value


def attachment_max_bytes() -> int:
    return positive_setting('CIVENSA_ATTACHMENT_MAX_MB', 10) * 1024 * 1024


def pp_image_max_bytes() -> int:
    return positive_setting('CIVENSA_PP_IMAGE_MAX_MB', 5) * 1024 * 1024


def pp_image_max_pixels() -> int:
    return positive_setting('CIVENSA_PP_IMAGE_MAX_PIXELS', 16000000)

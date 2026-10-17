import hashlib, hmac, secrets


def temporary_password() -> str:
    # Exclude visually ambiguous characters and CSV formula prefixes. Guaranteed
    # character classes, with every choice and the shuffle using system entropy.
    groups = ('ABCDEFGHJKLMNPQRSTUVWXYZ', 'abcdefghjkmnpqrstuvwxyz', '23456789', '!?#%&*')
    chars = [secrets.choice(group) for group in groups]
    chars.extend(secrets.choice(''.join(groups)) for _ in range(14))
    secrets.SystemRandom().shuffle(chars)
    return ''.join(chars)

def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 180_000).hex()
    return f"pbkdf2_sha256${salt}${digest}"

def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, salt, expected = stored.split("$", 2)
        if scheme != "pbkdf2_sha256": return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 180_000).hex()
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False

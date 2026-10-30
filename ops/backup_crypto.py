"""Şifreli yedek sınırı: yalnız age dosyaları yayınlanır, anahtarlar yazdırılmaz."""
import argparse
from contextlib import contextmanager
import os
from pathlib import Path
import subprocess
import tempfile


AGE_HEADER = b"age-encryption.org/v1\n"


class BackupCryptoError(Exception):
    pass


def _private_output(path):
    return os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb")


def _age(arguments, *, output=subprocess.DEVNULL, **kwargs):
    # Neither identity contents nor age diagnostics may reach Actions logs.
    env = {k: v for k, v in os.environ.items() if k != "BACKUP_AGE_IDENTITY"}
    result = subprocess.run(["age", *arguments], env=env,
                            stdout=output, stderr=subprocess.DEVNULL, **kwargs)
    if result.returncode:
        raise BackupCryptoError("Yedek şifreleme/çözme başarısız; anahtarı ve dosya bütünlüğünü kontrol edin.")


def require_recipient():
    recipient = os.environ.get("BACKUP_AGE_RECIPIENT", "").strip()
    if not recipient:
        raise BackupCryptoError("BACKUP_AGE_RECIPIENT eksik; depo sorumlusu alıcı anahtarını tanımlamalıdır.")
    # Reject malformed recipients before any database connection or dump.
    _age(["--encrypt", "--recipient", recipient], input=b"")
    return recipient


def ciphertext_pair(directory):
    """Reject extra files, symlinks, plaintext and renamed dumps before upload/restore."""
    directory = Path(directory)
    files = sorted(directory.iterdir())
    dumps = [p for p in files if p.name.endswith(".dump.age")]
    if len(files) != 2 or len(dumps) != 1:
        raise BackupCryptoError("Yedek yalnız bir .dump.age ve eşleşen .manifest.json.age içermelidir.")
    dump = dumps[0]
    manifest = dump.with_name(dump.name.removesuffix(".dump.age") + ".manifest.json.age")
    if manifest not in files:
        raise BackupCryptoError("Şifreli yedek manifest dosyası eksik.")
    for path in files:
        if path.is_symlink() or not path.is_file():
            raise BackupCryptoError("Yedekte beklenmeyen dosya türü var.")
        with path.open("rb") as stream:
            if stream.read(len(AGE_HEADER)) != AGE_HEADER:
                raise BackupCryptoError("Yedekte age şifreli dosya başlığı bulunamadı; yayın durduruldu.")
    return dump, manifest


def encrypt_backup(dump, destination):
    recipient = require_recipient()
    dump, destination = Path(dump), Path(destination)
    manifest = dump.with_suffix(".manifest.json")
    if dump.suffix != ".dump" or not dump.is_file() or not manifest.is_file():
        raise BackupCryptoError("Şifrelenecek dump/manifest çifti eksik.")
    destination.mkdir(mode=0o700)  # Never mix this run with old or plaintext files.
    try:
        for source in (dump, manifest):
            target = destination / (source.name + ".age")
            with _private_output(target) as stream:
                _age(["--encrypt", "--recipient", recipient, str(source)], output=stream)
        ciphertext_pair(destination)
    except BaseException:
        for target in destination.iterdir():
            target.unlink()
        destination.rmdir()
        raise


@contextmanager
def _identity_file():
    identity = os.environ.get("BACKUP_AGE_IDENTITY", "")
    path = os.environ.get("BACKUP_AGE_IDENTITY_FILE", "")
    if identity:
        with tempfile.TemporaryDirectory(prefix="civ092-identity-") as directory:
            key = Path(directory) / "identity.txt"
            with _private_output(key) as stream:
                stream.write(identity.encode())
            yield key
    elif path and Path(path).is_file():
        yield Path(path)
    else:
        raise BackupCryptoError("BACKUP_AGE_IDENTITY eksik; depo sorumlusu özel anahtarı güvenli olarak tanımlamalıdır.")


def decrypt_backup(source, destination):
    encrypted = ciphertext_pair(source)
    destination = Path(destination)
    destination.mkdir(mode=0o700)
    try:
        with _identity_file() as identity:
            for source in encrypted:
                target = destination / source.name.removesuffix(".age")
                with _private_output(target) as stream:
                    _age(["--decrypt", "--identity", str(identity), str(source)], output=stream)
        dump = destination / encrypted[0].name.removesuffix(".age")
        with dump.open("rb") as stream:
            if stream.read(5) != b"PGDMP":
                raise BackupCryptoError("Çözülen yedek PostgreSQL dump dosyası değil.")
        return dump
    except BaseException:
        for target in destination.iterdir():
            target.unlink()
        destination.rmdir()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("require-recipient", "encrypt", "decrypt", "check"))
    parser.add_argument("source", nargs="?", type=Path)
    parser.add_argument("destination", nargs="?", type=Path)
    args = parser.parse_args()
    try:
        if args.operation == "require-recipient":
            require_recipient()
        elif args.operation == "check" and args.source:
            ciphertext_pair(args.source)
        elif args.operation in {"encrypt", "decrypt"} and args.source and args.destination:
            (encrypt_backup if args.operation == "encrypt" else decrypt_backup)(args.source, args.destination)
        else:
            parser.error("Kaynak ve hedef yollarını belirtin.")
    except BackupCryptoError as exc:
        parser.exit(1, f"DURDU: {exc}\n")
    except OSError:
        # OS errors may include private paths. Keep command-line diagnostics generic.
        parser.exit(1, "DURDU: Yedek işlemi başarısız; alıcı/özel anahtarı ve şifreli dosya çiftini kontrol edin.\n")


if __name__ == "__main__":
    main()

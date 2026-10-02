from __future__ import annotations

from io import BytesIO
from pathlib import PurePosixPath
from zipfile import BadZipFile, ZipFile

from fastapi import HTTPException, UploadFile

MAX_ENTRIES = 5000
MAX_UNCOMPRESSED = 120 * 1024 * 1024
MAX_RATIO = 250


async def read_upload_limited(file: UploadFile, limit: int, label: str = "Dosya") -> bytes:
    data = await file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(413, f"{label} {limit // (1024 * 1024)} MB sınırını aşıyor.")
    return data


def validate_office_zip(data: bytes, suffix: str) -> None:
    """Reject malformed or suspicious OOXML containers before parsing them.

    DOCX/XLSX/XLSM are ZIP containers. We never execute embedded content, but
    validating the archive early prevents corrupted files and decompression bombs
    from reaching python-docx/openpyxl.
    """
    if not data.startswith(b"PK"):
        raise HTTPException(422, "Office dosyası geçerli bir OOXML/ZIP kapsayıcısı değil.")
    try:
        with ZipFile(BytesIO(data)) as zf:
            infos = zf.infolist()
            if not infos or len(infos) > MAX_ENTRIES:
                raise HTTPException(422, "Office dosyasındaki arşiv yapısı olağandışı.")
            total_uncompressed = 0
            names = set()
            for info in infos:
                path = PurePosixPath(info.filename)
                if path.is_absolute() or ".." in path.parts:
                    raise HTTPException(422, "Office dosyasında güvensiz arşiv yolu bulundu.")
                if info.flag_bits & 0x1:
                    raise HTTPException(422, "Parola ile şifrelenmiş Office dosyaları desteklenmiyor.")
                total_uncompressed += info.file_size
                if total_uncompressed > MAX_UNCOMPRESSED:
                    raise HTTPException(422, "Office dosyasının açılmış boyutu güvenlik sınırını aşıyor.")
                if info.compress_size > 0 and info.file_size / info.compress_size > MAX_RATIO and info.file_size > 1_000_000:
                    raise HTTPException(422, "Office dosyasında olağandışı sıkıştırma oranı tespit edildi.")
                names.add(info.filename)
            if "[Content_Types].xml" not in names:
                raise HTTPException(422, "Office dosyası gerekli OOXML bileşenlerini içermiyor.")
            if suffix == ".docx":
                if "word/document.xml" not in names:
                    raise HTTPException(422, "DOCX ana belge bileşeni bulunamadı.")
                if any(name.lower().endswith("vbaproject.bin") for name in names):
                    raise HTTPException(422, "Makro içeren dosya DOCX olarak kabul edilmiyor.")
            elif suffix in {".xlsx", ".xlsm"} and "xl/workbook.xml" not in names:
                raise HTTPException(422, "Excel çalışma kitabı bileşeni bulunamadı.")
    except BadZipFile:
        raise HTTPException(422, "Office dosyası bozuk veya okunamıyor.")

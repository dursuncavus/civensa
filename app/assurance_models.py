"""Only variable fields are persisted; legal prose lives in the verified asset."""
from sqlalchemy import CheckConstraint, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


class AssuranceStatement(Base):
    __tablename__ = 'ar_assurance_statements'
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey('ar_documents.id'))
    code: Mapped[str] = mapped_column(String(4))
    version_id: Mapped[str] = mapped_column(String(80))
    file_sha256: Mapped[str] = mapped_column(String(64))
    variables_json: Mapped[str] = mapped_column(Text)
    __table_args__ = (
        UniqueConstraint('document_id', 'code'),
        CheckConstraint("code IN ('EK-1','EK-2','EK-3')"),
    )

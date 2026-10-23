"""Guard the manual base64 inventory against newly introduced model columns."""
from pathlib import Path

from sqlalchemy import String, JSON
from app.db import Base
from app import models  # Register every model, including binary storage.
from ops.db_storage_report import BASE64_COLUMNS


def test_new_text_or_json_model_column_requires_storage_classification():
    # Conservative: even a new ordinary text column requires review. Models do
    # not encode whether text contains base64, so naming heuristics can miss it.
    path = Path(__file__).parent / 'fixtures/storage_non_base64_columns.txt'
    reviewed = {tuple(line.split('.', 1)) for line in path.read_text().splitlines() if line and not line.startswith('#')}
    actual = {(table.name, column.name) for table in Base.metadata.tables.values()
              for column in table.c if isinstance(column.type, (String, JSON))}
    assert not (reviewed & BASE64_COLUMNS), 'Base64 taşıyan sütun normal metin listesinde olamaz.'
    assert actual == reviewed | BASE64_COLUMNS, (
        'Yeni metin/JSON sütununu inceleyin: görsel/base64 taşıyorsa BASE64_COLUMNS listesine, '
        'taşımıyorsa gerekçesiyle gözden geçirilmiş metin envanterine ekleyin. '
        f'İncelenmeyen: {sorted(actual - reviewed - BASE64_COLUMNS)}; kaldırılan: {sorted((reviewed | BASE64_COLUMNS) - actual)}'
    )

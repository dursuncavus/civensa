"""CIV-084 widen monitoring status/percentage checks without changing history."""
from alembic import op
import sqlalchemy as sa

revision = 'c084a1b2c3d4'
down_revision = 'c078a1b2c3d4'
branch_labels = None
depends_on = None

OLD_STATUS = "status IN ('completed','ongoing','not_started','delayed')"
NEW_STATUS = """status IN ('completed','ongoing','not_started','delayed','partial','not_approved')
 AND (status != 'partial' OR (percentage IS NOT NULL AND percentage BETWEEN 1 AND 99))
 AND (status != 'not_approved' OR length(trim(explanation)) > 0)"""
OLD_PERCENTAGE = "(percentage BETWEEN 0 AND 100) AND (percentage IS NOT NULL OR status='not_started')"
NEW_PERCENTAGE = "(percentage BETWEEN 0 AND 100) AND (percentage IS NOT NULL OR status IN ('not_started','not_approved'))"


def checks(status, percentage):
    bind = op.get_bind()
    # SQLite batch recreation must retain the existing immutable-history triggers.
    triggers = bind.execute(sa.text("SELECT sql FROM sqlite_master WHERE type='trigger' AND tbl_name='ic_monitoring_entries'")).scalars().all() if bind.dialect.name == 'sqlite' else []
    with op.batch_alter_table('ic_monitoring_entries') as batch:
        batch.drop_constraint('ck_ic_monitoring_entry_status', type_='check')
        batch.drop_constraint('ck_ic_monitoring_percentage', type_='check')
        batch.create_check_constraint('ck_ic_monitoring_entry_status', status)
        batch.create_check_constraint('ck_ic_monitoring_percentage', percentage)
    for trigger in triggers:
        op.execute(trigger)


def upgrade():
    checks(NEW_STATUS, NEW_PERCENTAGE)


def downgrade():
    if op.get_bind().dialect.name == 'postgresql':
        op.execute('LOCK TABLE ic_monitoring_entries IN ACCESS EXCLUSIVE MODE')
    if op.get_bind().execute(sa.text("SELECT 1 FROM ic_monitoring_entries WHERE status IN ('partial','not_approved') LIMIT 1")).first():
        raise RuntimeError('Kısmen tamamlandı veya uygun görülmemiştir izleme geçmişi var. Veriyi koruyan geçiş hazırlanmadan sürüm düşürülemez.')
    checks(OLD_STATUS, OLD_PERCENTAGE)

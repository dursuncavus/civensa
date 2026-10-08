"""Add immutable correction reasons without rewriting historical revisions."""
from alembic import op
import sqlalchemy as sa

revision = 'a7c2d3e4f5a6'
down_revision = 'f6b1c2d3e4f5'
branch_labels = None
depends_on = None


def upgrade():
    # Direct ALTER preserves the existing SQLite and PostgreSQL immutability triggers.
    op.add_column('activity_report_revisions', sa.Column('revision_reason', sa.Text(),
                                                        nullable=False, server_default=''))
    approved_predecessor = """SELECT 1 FROM activity_report_approvals
        WHERE report_revision_id=NEW.previous_revision_id"""
    if op.get_bind().dialect.name == 'postgresql':
        op.execute(f"""CREATE FUNCTION guard_correction_reason() RETURNS trigger AS $$
            BEGIN IF EXISTS ({approved_predecessor}) AND length(trim(NEW.revision_reason))=0 THEN
            RAISE EXCEPTION 'Onaylı rapor için düzeltme gerekçesi gerekir.';
            END IF; RETURN NEW; END; $$ LANGUAGE plpgsql""")
        op.execute('CREATE TRIGGER guard_correction_reason BEFORE INSERT ON activity_report_revisions '
                   'FOR EACH ROW EXECUTE FUNCTION guard_correction_reason()')
    elif op.get_bind().dialect.name == 'sqlite':
        op.execute(f"CREATE TRIGGER guard_correction_reason BEFORE INSERT ON activity_report_revisions "
                   f"WHEN EXISTS ({approved_predecessor}) AND length(trim(NEW.revision_reason))=0 "
                   "BEGIN SELECT RAISE(ABORT, 'Onaylı rapor için düzeltme gerekçesi gerekir.'); END")


def downgrade():
    raise RuntimeError('Düzeltme gerekçelerini korumak için geçiş öncesi yedeği ayrı veritabanına geri yükleyin.')

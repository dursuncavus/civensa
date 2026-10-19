"""CIV-026 lossless economic source values and programme provenance."""
from alembic import op
import sqlalchemy as sa

revision = 'b0262027a001'
down_revision = 'c025a1b2c3d4'
branch_labels = depends_on = None


def upgrade():
    with op.batch_alter_table('economic_values') as table:
        table.alter_column('amount', existing_type=sa.Numeric(22, 2), nullable=True)
        for name, kind, default in [('raw_text', sa.Text(), ''), ('state', sa.String(30), 'verified'),
                                    ('issue', sa.Text(), ''), ('source_context_json', sa.Text(), '{}')]:
            table.add_column(sa.Column(name, kind, nullable=False, server_default=default))
        table.add_column(sa.Column('source_table_number', sa.Integer(), nullable=True))
        table.add_column(sa.Column('source_card_id', sa.Integer(), nullable=True))
        table.create_foreign_key('fk_economic_source_card', 'report_cards', ['source_card_id'], ['id'])


def downgrade():
    # Refuse loss of source/review evidence; an operator must retain it before downgrading.
    if op.get_bind().execute(sa.text("SELECT 1 FROM economic_values WHERE amount IS NULL OR state <> 'verified' OR raw_text <> '' OR issue <> '' OR source_table_number IS NOT NULL OR source_card_id IS NOT NULL OR source_context_json <> '{}' LIMIT 1")).first():
        raise RuntimeError('Ekonomik kaynak ve doğrulama verileri korunmadan sürüm düşürülemez.')
    with op.batch_alter_table('economic_values') as table:
        table.drop_constraint('fk_economic_source_card', type_='foreignkey')
        for name in ['source_card_id', 'source_table_number', 'source_context_json', 'issue', 'state', 'raw_text']:
            table.drop_column(name)
        table.alter_column('amount', existing_type=sa.Numeric(22, 2), nullable=False)

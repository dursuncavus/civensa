"""CIV-011: preserve source totals and batch conflict decisions.

Revision ID: b8d011e6f420
Revises: b018a1c2d3e4
"""
from alembic import op
import sqlalchemy as sa

revision = "b8d011e6f420"
down_revision = "b018a1c2d3e4"
branch_labels = depends_on = None


def upgrade():
    op.add_column("import_batches", sa.Column("decisions_json", sa.Text(), nullable=False, server_default="[]"))
    op.add_column("activity_cost_values", sa.Column("source_amount", sa.Numeric(22, 2), nullable=True))
    op.add_column("activity_cost_values", sa.Column("source_raw_text", sa.Text(), nullable=False, server_default=""))
    op.add_column("activity_cost_values", sa.Column("source_resolution_json", sa.Text(), nullable=False, server_default="{}"))
    # Older rows do not distinguish source text from manual text. Conservatively
    # protect every total with retained text; never guess that a disagreement was reviewed.
    op.execute("""UPDATE activity_cost_values SET source_amount = amount, source_raw_text = raw_text
                  WHERE funding_type = 'total' AND amount IS NOT NULL AND raw_text <> ''""")
    # raw_text can still hold the original source after an older ordinary save
    # overwrote amount. Recover only unambiguous source numbers, retaining the text.
    from decimal import Decimal
    from app.numbers import source_cell
    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id, raw_text FROM activity_cost_values WHERE source_amount IS NOT NULL")).all()
    for row in rows:
        cell = source_cell(row.raw_text, money=True)
        if cell['number'] is not None:
            bind.execute(sa.text("UPDATE activity_cost_values SET source_amount=:amount WHERE id=:id")
                         .bindparams(sa.bindparam("amount", type_=sa.Numeric(22, 2))),
                         {"amount": Decimal(cell['number']), "id": row.id})
    op.execute("""UPDATE activity_cost_values SET state = 'needs_review'
        WHERE funding_type = 'total' AND source_amount IS NOT NULL AND source_amount <> (
            SELECT i.amount + o.amount FROM activity_cost_values i JOIN activity_cost_values o
              ON o.activity_id = i.activity_id AND o.year = i.year AND o.value_kind = i.value_kind
            WHERE i.activity_id = activity_cost_values.activity_id AND i.year = activity_cost_values.year
              AND i.value_kind = activity_cost_values.value_kind AND i.funding_type = 'inside' AND o.funding_type = 'outside'
        )""")


def downgrade():
    bind = op.get_bind()
    history = bind.execute(sa.text("""SELECT 1 FROM import_batches WHERE decisions_json <> '[]'
        UNION ALL SELECT 1 FROM activity_cost_values WHERE source_resolution_json <> '{}'
        UNION ALL SELECT 1 FROM audit_log WHERE action IN
          ('import_source_conflict_decision', 'activity_source_total_decision') LIMIT 1""")).first()
    if history:
        raise RuntimeError("CIV-011 karar geçmişi var. Geçmişi koruyan bir geçiş hazırlamadan sürüm düşürülemez.")
    for column in ("source_resolution_json", "source_raw_text", "source_amount"):
        op.drop_column("activity_cost_values", column)
    op.drop_column("import_batches", "decisions_json")

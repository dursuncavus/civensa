"""CIV-025 released positions and submission authorisation.

Downgrade intentionally retains columns, values, and uniqueness guards. Old code
ignores these additive fields; a later re-upgrade must not reset user decisions.
"""
import json

from alembic import op
import sqlalchemy as sa

revision = 'c025a1b2c3d4'
down_revision = 'a6c006e9b241'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    columns = {column['name'] for column in sa.inspect(bind).get_columns('users')}
    if 'position' not in columns:
        # Inline checks avoid rebuilding users underneath existing SQLite triggers.
        op.add_column('users', sa.Column('position', sa.String(20),
            sa.CheckConstraint("position IN ('staff', 'director')", name='ck_user_position'),
            sa.CheckConstraint("position != 'director' OR department_id IS NOT NULL", name='ck_director_department'),
            nullable=False, server_default='staff'))
    if 'can_submit' not in columns:
        op.add_column('users', sa.Column('can_submit', sa.Boolean(), nullable=False, server_default=sa.false()))
        bind.execute(sa.text("UPDATE users SET can_submit = true WHERE role = 'department'"))
    for user_id, role in bind.execute(sa.text('SELECT id, role FROM users')):
        for field, value in [('position', 'staff'), ('can_submit', role == 'department')]:
            if field not in columns:
                bind.execute(sa.text("INSERT INTO audit_log (user_id, action, entity_type, entity_id, details, created_at) "
                                     "VALUES (NULL, :action, 'user', :target, :details, CURRENT_TIMESTAMP)"),
                             {'action': 'user_' + field + '_change', 'target': user_id,
                              'details': json.dumps({'field': field, 'old': None, 'new': value,
                                                     'reason': 'CIV-025 geçişi; mevcut gönderim erişimi korundu.'}, ensure_ascii=False)})
    indexes = {index['name'] for index in sa.inspect(bind).get_indexes('users')}
    if 'uq_active_department_director' not in indexes:
        op.create_index('uq_active_department_director', 'users', ['department_id'], unique=True,
                        postgresql_where=sa.text("is_active AND position = 'director'"),
                        sqlite_where=sa.text("is_active = 1 AND position = 'director'"))
    # Legacy Strategy accounts had no department. Do not guess across institutions.
    if bind.execute(sa.text("SELECT id FROM users WHERE role = 'strategy' AND department_id IS NULL")).first():
        organizations = bind.execute(sa.text('SELECT id FROM organizations ORDER BY id')).scalars().all()
        if len(organizations) != 1:
            raise RuntimeError('Strateji kullanıcılarının müdürlüğü belirlenemedi; kurum/müdürlük atamalarını kontrol edin.')
        organization_id = organizations[0]
        department_id = bind.execute(sa.text('SELECT id FROM departments WHERE organization_id = :org AND name = :name'),
                                     {'org': organization_id, 'name': 'Strateji Geliştirme Müdürlüğü'}).scalar()
        if department_id is None:
            departments = sa.table('departments', sa.column('id', sa.Integer), sa.column('organization_id'), sa.column('name'))
            department_id = bind.execute(sa.text('SELECT COALESCE(MAX(id), 0) + 1 FROM departments')).scalar_one()
            bind.execute(departments.insert().values(id=department_id, organization_id=organization_id,
                name='Strateji Geliştirme Müdürlüğü'))
            # A newly introduced directory department must not add a missing
            # reporting obligation to already configured pilot periods.
            bind.execute(sa.text("INSERT INTO department_scopes (department_id, period_id, position, display_name, status, reason) "
                                 "SELECT :did, id, 0, '', 'excluded', :reason FROM reporting_periods"),
                         {'did': department_id, 'reason': 'CIV-025: kullanıcı yetkileri için oluşturulan Strateji müdürlük kaydı; mevcut raporlama kapsamı korunmuştur.'})
            if bind.dialect.name == 'postgresql':
                bind.execute(sa.text("SELECT setval(pg_get_serial_sequence('departments','id'), GREATEST((SELECT MAX(id) FROM departments), nextval(pg_get_serial_sequence('departments','id'))))"))
        bind.execute(sa.text("UPDATE users SET department_id = :did WHERE role = 'strategy' AND department_id IS NULL"), {'did': department_id})

    if not bind.execute(sa.text("SELECT id FROM audit_log WHERE action = 'civ025_tracking_started'")).first():
        bind.execute(sa.text("INSERT INTO audit_log (action, entity_type, details, created_at) "
                             "VALUES ('civ025_tracking_started', 'system', 'PP kapsamlı veri geçmişi başlangıcı', CURRENT_TIMESTAMP)"))


def downgrade():
    # Preserve assignments, authorisations, audit history and all business data.
    pass

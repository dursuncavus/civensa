"""CIV-184: presentation photos, separate from approved report payloads."""
from alembic import op
import sqlalchemy as sa

revision = 'c184a1b2c3d4'
down_revision = 'c162a1b2c3d4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('sunum_photos',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('organization_id', sa.Integer, sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('period_id', sa.Integer, sa.ForeignKey('reporting_periods.id'), nullable=False),
        sa.Column('year', sa.Integer, nullable=False),
        sa.Column('department_id', sa.Integer, sa.ForeignKey('departments.id'), nullable=False),
        sa.Column('caption', sa.String(140), nullable=False),
        sa.Column('taken_on', sa.Date), sa.Column('mahalle', sa.String(80)),
        sa.Column('kind', sa.String(6), nullable=False), sa.Column('pair_key', sa.String(36)),
        sa.Column('webp_data', sa.LargeBinary, nullable=False), sa.Column('thumb_data', sa.LargeBinary, nullable=False),
        sa.Column('width', sa.Integer, nullable=False), sa.Column('height', sa.Integer, nullable=False),
        sa.Column('sha256', sa.String(64), nullable=False), sa.Column('byte_size', sa.Integer, nullable=False),
        sa.Column('consent_confirmed', sa.Boolean, nullable=False),
        sa.Column('selected', sa.Boolean, nullable=False), sa.Column('sort_order', sa.Integer, nullable=False),
        sa.Column('created_by', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.UniqueConstraint('organization_id', 'year', 'sha256', name='uq_sunum_photo_year_sha'),
        sa.UniqueConstraint('pair_key', 'kind', name='uq_sunum_photo_pair_kind'),
        sa.CheckConstraint("(kind = 'single' AND pair_key IS NULL) OR (kind IN ('before','after') AND pair_key IS NOT NULL)", name='ck_sunum_photo_kind'),
        sa.CheckConstraint('length(trim(caption)) BETWEEN 1 AND 140', name='ck_sunum_photo_caption'),
        sa.CheckConstraint('consent_confirmed', name='ck_sunum_photo_consent'),
        sa.CheckConstraint('width > 0 AND height > 0 AND width <= 1600 AND height <= 1600 AND byte_size > 0', name='ck_sunum_photo_size'))
    if op.get_bind().dialect.name == 'postgresql':
        # Deferred to commit so both inserts and both deletes are atomic. A pair
        # key is global and cannot link different institutions, years or units.
        op.execute("""
        CREATE FUNCTION check_sunum_photo_pair() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE k text;
        BEGIN
          FOR k IN SELECT DISTINCT key FROM unnest(ARRAY[
            CASE WHEN TG_OP <> 'INSERT' THEN OLD.pair_key END,
            CASE WHEN TG_OP <> 'DELETE' THEN NEW.pair_key END]) AS key WHERE key IS NOT NULL
          LOOP
            IF EXISTS (SELECT 1 FROM sunum_photos WHERE pair_key = k) AND
              (SELECT count(*) <> 2 OR count(DISTINCT kind) <> 2 OR
                count(DISTINCT (organization_id, period_id, year, department_id)) <> 1
                FROM sunum_photos WHERE pair_key = k) THEN
              RAISE EXCEPTION 'Önce/sonra çifti aynı müdürlük ve yıldan iki fotoğraf içermelidir.';
            END IF;
          END LOOP;
          RETURN NULL;
        END $$;
        CREATE CONSTRAINT TRIGGER sunum_photo_pair
          AFTER INSERT OR UPDATE OR DELETE ON sunum_photos
          DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION check_sunum_photo_pair();
        """)


def downgrade():
    # Refuse a destructive downgrade; callers can keep using the previous app
    # with this extra table until a deliberate, data-preserving transfer exists.
    if op.get_bind().execute(sa.text('SELECT EXISTS (SELECT 1 FROM sunum_photos)')).scalar():
        raise RuntimeError('Sunum fotoğrafları var; veriyi koruyan aktarım hazırlanmadan sürüm düşürülemez.')
    op.drop_table('sunum_photos')
    if op.get_bind().dialect.name == 'postgresql':
        op.execute('DROP FUNCTION check_sunum_photo_pair()')

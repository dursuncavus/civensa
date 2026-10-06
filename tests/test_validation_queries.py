import pytest
from sqlalchemy import event, select
from app.models import Activity, ActivityCatalogueLink, ActivityResponsibility, OfficialActivity, ReportingPeriod
from app.main import department_progress_overview
from app.program_service import validate_department


def test_progress_catalogue_queries_do_not_grow_per_activity(db, sample):
    def count_queries():
        db.expire_all()
        counter = [0]
        def query(*args): counter[0] += 1
        event.listen(db.get_bind(), 'before_cursor_execute', query)
        try:
            department_progress_overview(db, sample['period'])
        finally:
            event.remove(db.get_bind(), 'before_cursor_execute', query)
        return counter[0]
    before = count_queries()
    for index in range(20):
        activity = Activity(period_id=1, department_id=1, subprogram_id=sample['subprogram'].id,
                            card_id=sample['card'].id, name=f'Test {index}', explanation='Açıklama')
        db.add(activity); db.flush()
        db.add(ActivityCatalogueLink(activity_id=activity.id, official_activity_id=sample['official'].id))
    db.commit()
    assert count_queries() <= before + 5


@pytest.mark.parametrize('problem', ['wrong_period', 'wrong_department'])
def test_bulk_catalogue_validation_preserves_scope_checks(db, sample, problem):
    official = sample['official']
    if problem == 'wrong_period':
        period = ReportingPeriod(year=2030, status='draft'); db.add(period); db.flush()
        official.period_id = period.id
    else:
        db.delete(db.scalar(select(ActivityResponsibility)))
    db.commit()
    errors, _ = validate_department(db, 1, 1)
    assert any('katalog kapsamı geçersiz' in message for message in errors)

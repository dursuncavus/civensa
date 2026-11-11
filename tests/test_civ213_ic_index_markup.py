"""CIV-213: the İç Kontrol landing page must not print the questionnaire card as escaped HTML."""
import pytest
from test_internal_control_monitoring import monitoring  # noqa: F401

pytestmark = pytest.mark.postgres


def test_index_renders_questionnaire_card_as_markup(db, monitoring, client):
    from app.main import app, require_user
    app.dependency_overrides[require_user] = lambda: monitoring['strategy']
    try:
        html = client.get('/internal-control').text
    finally:
        app.dependency_overrides.pop(require_user, None)
    assert '&lt;section' not in html and '&lt;h2' not in html
    assert html.count('<section class="card"><h2>Plan yükle') == 1
    assert '<a class="button" href="/internal-control/questionnaires">Soru formu listeleri</a>' in html
    assert html.index('Soru formu listeleri') < html.index('<h2>Plan yükle')

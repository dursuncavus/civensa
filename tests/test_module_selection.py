def test_module_selector_distinguishes_readiness(client):
    response=client.get('/modules')
    assert response.status_code==200
    assert 'href="/dashboard"' in response.text
    assert 'href="/activity-report"' in response.text
    assert 'href="/activity-reports"' in response.text
    assert 'Tam rapor hazırlık aşamasında' in response.text

def test_activity_preparation_does_not_expose_write_form(client):
    response=client.get('/activity-report')
    assert response.status_code==200
    assert 'gerçekleşme olarak kullanılmayacak' in response.text
    assert 'Veri girişi ve rapor üretimi henüz açık değil' in response.text
    assert '<input' not in response.text.replace('<input id="currentPassword"','<password').replace('<input id="newPassword"','<password').replace('<input id="confirmPassword"','<password').replace('<input type="hidden"','<hidden')

def test_modules_requires_authentication(db):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.db import get_db
    def database():yield db
    app.dependency_overrides[get_db]=database
    try:
        client=TestClient(app)
        try:
            r=client.get('/modules',follow_redirects=False)
            assert r.status_code in (303,401)
        finally:client.close()
    finally:app.dependency_overrides.clear()

"""Real-login EKLER setup reused by CIV-037's freeze acceptance tests."""
from test_activity_sections import login


def variables(year=2027, two=False):
    people = [{'person_ref': 'person-1', 'name': 'Ayşe Yılmaz', 'title': 'Müdür',
               'start_date': f'{year}-01-01', 'end_date': f'{year}-12-31'}]
    if two:
        people[0]['end_date'] = f'{year}-06-30'
        people.append({'person_ref': 'person-2', 'name': 'Mehmet Kaya', 'title': 'Müdür',
                       'start_date': f'{year}-07-01', 'end_date': f'{year}-12-31'})
    return {'place': 'Ankara', 'date': f'{year+1}-02-15', 'signatories': people, 'reservations': []}


def put(client, token, doc, code, values=None, **extra):
    revision = client.get(f'/api/activity-sections/reports/{doc.id}').json()['revision']
    return client.post(f'/api/activity-sections/reports/{doc.id}/assurances/{code}',
        headers={'X-CSRF-Token': token}, json={'expected_revision': revision,
                                             'variables': values if values is not None else variables(), **extra})


def complete_assurances(client, doc):
    cookies = dict(client.cookies)
    try:
        required = [('test@example.invalid', 'EK-2')] if doc.department_id else [
            ('strategy@example.invalid', 'EK-1'), ('finance@example.invalid', 'EK-3')]
        for email, code in required:
            token = login(client, email)
            response = put(client, token, doc, code)
            assert response.status_code == 200, response.text
    finally:
        client.cookies.clear()
        client.cookies.update(cookies)

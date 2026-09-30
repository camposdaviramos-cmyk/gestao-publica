"""Authorization and query regressions exposed while repairing module controls."""
from test_system import app, admin, user, login


def test_finance_reader_cannot_mutate_from_module_controls(app, admin):
    user(admin, permissions={'finance': ['read']})
    reader = app.test_client()
    headers = login(reader, 'second@example.test')
    assert reader.get('/api/finance/journal/query').status_code == 200
    for path in ['/journal/post', '/treasury/checks', '/treasury/advance-funds', '/budget/decrees']:
        response = reader.post('/api/finance' + path, json={}, headers=headers)
        assert response.status_code == 403, response.json


def test_people_queries_require_module_permission(app, admin):
    user(admin, permissions={'people': []})
    reader = app.test_client()
    login(reader, 'second@example.test')
    for path in ['/employees', '/positions', '/sst/epis', '/sst/ppp/1', '/locations']:
        assert reader.get('/api/people' + path).status_code == 403


def test_pending_portal_updates_join_actual_employee_table(app, admin):
    with app.app_context():
        from people_seed import seed_people
        seed_people()
    client, headers = admin
    response = client.post('/api/people/portal/update', json={
        'employee_id': 1, 'field_name': 'email', 'new_value': 'updated@example.test',
        'proof_file': 'comprovante.pdf'
    }, headers=headers)
    assert response.status_code == 200, response.json
    response = client.get('/api/people/portal/updates/pending')
    assert response.status_code == 200
    rows = response.json['pending_updates']
    assert len(rows) == 1
    assert rows[0]['employee_id'] == 1
    assert rows[0]['matricula'] == 'EMP-01'
    assert rows[0]['nome_servidor']


def test_advance_controls_use_real_rows_and_validate_accountability(admin):
    client, headers = admin
    created = client.post('/api/finance/treasury/advance-funds', json={
        'server_cpf': '52998224725', 'server_name': 'Responsável do teste',
        'commitment_id': 'TESTE-001', 'amount_cents': 10000
    }, headers=headers)
    assert created.status_code == 201
    fund_id = created.json['id']
    rows = client.get('/api/finance/treasury/advance-funds').json
    assert rows[0]['id'] == fund_id
    assert rows[0]['amount_cents'] == 10000
    path = '/api/finance/treasury/advance-funds/accountability'
    data = {'fund_id': fund_id, 'spent_cents': 8000, 'returned_cents': 1000}
    assert client.post(path, json=data, headers=headers).status_code == 400
    assert client.get('/api/finance/treasury/advance-funds').json[0]['status'] == 'Aberto'
    data['returned_cents'] = 2000
    assert client.post(path, json=data, headers=headers).status_code == 200
    assert client.post(path, json=data, headers=headers).status_code == 409
    data['fund_id'] = 99999
    assert client.post(path, json=data, headers=headers).status_code == 404

import json
import xml.etree.ElementTree as ET
from test_erp import ERP, erp, reviewer
from test_system import app, admin, login, user
from db import get_db

def test_transparency_summary_and_config(erp):
    # 1. Test summary endpoint
    res = erp.client.get('/api/public/transparency/summary')
    assert res.status_code == 200
    data = res.json
    assert data['fiscal_year'] == 2026
    assert 'last_update' in data
    assert 'kpis' in data
    assert 'total_revenue' in data['kpis']
    assert 'total_expense' in data['kpis']
    assert data['covid_enabled'] is True

    # 2. Test updating config
    cfg_res = erp.client.post('/api/transparency/config', json={
        'key': 'test_config_param',
        'value': 'ParametroHomologado',
        'description': 'Parametro de teste'
    }, headers=erp.headers)
    assert cfg_res.status_code == 200

    # 3. Test creating custom menu (transparency.100, 101)
    menu_res = erp.client.post('/api/transparency/menus', json={
        'title': 'Portal de Acesso Aberto',
        'url': 'https://riodasostras.rj.gov.br/aberto',
        'icon': 'globe',
        'category': 'Destaque',
        'is_highlighted': True,
        'sort_order': 10
    }, headers=erp.headers)
    assert menu_res.status_code == 201

    custom_menus = erp.client.get('/api/public/transparency/custom-menus').json
    assert any(m['title'] == 'Portal de Acesso Aberto' for m in custom_menus)

def test_transparency_expenses_drilldown_and_payments(erp):
    # 1. Query expenses
    res = erp.client.get('/api/public/transparency/expenses')
    assert res.status_code == 200
    data = res.json
    assert 'items' in data
    assert len(data['items']) > 0
    exp = data['items'][0]
    assert 'empenho_number' in exp
    assert 'managing_unit' in exp
    assert 'creditor' in exp
    assert 'committed_amount' in exp

    # 2. Drilldown into single empenho (transparency.3, 4, 10-15)
    detail_res = erp.client.get(f"/api/public/transparency/expenses/{exp['id']}")
    assert detail_res.status_code == 200
    detail = detail_res.json
    assert detail['id'] == exp['id']
    assert len(detail['items']) > 0
    assert len(detail['liquidations']) > 0
    assert len(detail['payments']) > 0
    assert 'process_number' in detail

    # 3. Chronological payments list (transparency.35, 117, 118)
    pay_res = erp.client.get('/api/public/transparency/chronological-payments')
    assert pay_res.status_code == 200
    pay_data = pay_res.json
    assert len(pay_data['items']) > 0
    first_pay = pay_data['items'][0]
    assert 'order_number' in first_pay
    assert 'justification' in first_pay
    assert pay_data['show_justification'] is True
    assert pay_data['show_order'] is True

def test_transparency_revenues_and_transfer_date(erp):
    res = erp.client.get('/api/public/transparency/revenues')
    assert res.status_code == 200
    data = res.json
    assert len(data['items']) > 0
    first_rec = data['items'][0]
    assert 'nature_code' in first_rec
    assert 'gross_collected' in first_rec
    assert 'transfer_date' in first_rec # transparency.143

def test_transparency_procurement_srp_and_contracts(erp):
    # Setup bidding process and contract in procurement
    supplier = erp.make('procurement', 'suppliers', name='Comercial Rio das Ostras Ltda', document='11222333000181', email='comercial@rio.test')
    proc = erp.make(
        'procurement', 'processes',
        code='PE-045/2026',
        name='Aquisição de Equipamentos Hospitalares',
        modality='Pregão',
        judgment='Menor preço',
        legal_basis='Lei 14.133/2021, Art. 28, I',
        estimated=85000000
    )
    
    # 1. Query procurement in transparency
    res = erp.client.get('/api/public/transparency/procurement')
    assert res.status_code == 200
    proc_items = res.json['items']
    found = [p for p in proc_items if p['id'] == proc['id']]
    assert len(found) == 1
    assert 'winners' in found[0]
    assert found[0]['legal_basis'] == 'Lei 14.133/2021, Art. 28, I'

    # 2. Query contracts
    contract = erp.make(
        'procurement', 'contracts',
        code='CT-088/2026',
        name='Contrato de Prestação de Serviços Contínuos',
        process=proc['id'],
        supplier=supplier['id'],
        start='2026-01-01',
        end='2026-12-31',
        amount=120000000,
        manager='Gestor Municipal',
        inspector='Fiscal Municipal'
    )
    c_res = erp.client.get('/api/public/transparency/contracts')
    assert c_res.status_code == 200
    c_items = c_res.json['items']
    assert any(c['id'] == contract['id'] for c in c_items)

def test_transparency_active_debt_and_amendments(erp):
    # 1. Active Debt (transparency.146)
    debt_res = erp.client.get('/api/public/transparency/active-debt')
    assert debt_res.status_code == 200
    debts = debt_res.json['items']
    assert len(debts) >= 5
    first_debt = debts[0]
    assert 'debtor_name' in first_debt
    assert 'cda_number' in first_debt
    assert 'original_amount' in first_debt
    assert 'updated_amount' in first_debt
    assert 'status' in first_debt

    # 2. Parliamentary Amendments (transparency.147)
    amend_res = erp.client.get('/api/public/transparency/parliamentary-amendments?sphere=Federal')
    assert amend_res.status_code == 200
    amends = amend_res.json['items']
    assert len(amends) >= 2
    assert all(a['sphere'] == 'Federal' for a in amends)
    assert 'indicated_amount' in amends[0]
    assert 'committed_amount' in amends[0]
    assert 'paid_amount' in amends[0]

def test_transparency_covid_panel_and_sic(erp):
    # 1. COVID panel (transparency.108 to 125, 140)
    cov_res = erp.client.get('/api/public/transparency/covid')
    assert cov_res.status_code == 200
    cov_data = cov_res.json
    assert cov_data['enabled'] is True
    assert len(cov_data['themes']) >= 10
    # Test alphabetical order of themes (transparency.140)
    theme_names = [t['theme_name'] for t in cov_data['themes']]
    assert theme_names == sorted(theme_names)

    # 2. Travel expenses (transparency.24, 135, 137)
    tr_res = erp.client.get('/api/public/transparency/travels')
    assert tr_res.status_code == 200
    tr_items = tr_res.json['items']
    assert len(tr_items) >= 3
    assert 'transport_type' in tr_items[0]
    assert 'transport_cost' in tr_items[0]
    assert 'expense_breakdown' in tr_items[0]

    # 3. e-SIC submission and consultation (transparency.94, 95)
    sic_create = erp.client.post('/api/public/transparency/sic', json={
        'requester_name': 'Cidadão Fluminense Consciente',
        'requester_document': '12345678901',
        'requester_email': 'cidadao@exemplo.com',
        'subject': 'Relatório Trimestral de Obras e Vistoria',
        'description': 'Solicito cópia do relatório de fiscalização das obras de pavimentação da praia de Costazul.'
    })
    assert sic_create.status_code == 201
    prot = sic_create.json['protocol']
    assert prot.startswith('SIC-')

    # Consult by protocol
    sic_consult = erp.client.get(f"/api/public/transparency/sic?protocol={prot}")
    assert sic_consult.status_code == 200
    assert sic_consult.json['protocol'] == prot
    assert sic_consult.json['status'] == 'Aberto'

def test_transparency_open_data_exports(erp):
    # Test open data export in JSON, CSV and XML (transparency.2, 41, 65, 74, 77, 81, 86, 98, 99)
    for fmt, mime in [('json', 'application/json'), ('csv', 'text/csv'), ('xml', 'application/xml')]:
        res = erp.client.get(f'/api/public/transparency/export?entity=expenses&format={fmt}')
        assert res.status_code == 200
        assert mime in res.content_type
        if fmt == 'json':
            parsed = json.loads(res.data)
            assert isinstance(parsed, list)
        elif fmt == 'csv':
            assert b'empenho_number' in res.data or b'id' in res.data
        elif fmt == 'xml':
            root = ET.fromstring(res.data)
            assert root.tag == 'despesas'

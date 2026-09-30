import json
from decimal import Decimal
from test_erp import ERP, erp, reviewer
from test_system import app, admin, login, user
from db import get_db

def works_setup(e):
    supplier = e.make('procurement', 'suppliers', name='Construtora Rio das Ostras Ltda', document='11222333000181', email='contato@construtora.test')
    project = e.make(
        'works', 'projects',
        code='OBRA-2026-001',
        name='Pavimentação e Drenagem da Av. Costazul',
        supplier=supplier['id'],
        engineer='Eng. Carlos Silva',
        registration='CREA-RJ 123456/D',
        address='Av. Costazul, Rio das Ostras - RJ',
        latitude='-22.5273',
        longitude='-41.9442',
        start='2026-01-01',
        end='2026-06-30',
        retention_days=30,
        public=True
    )
    return project, supplier

def test_works_project_and_spreadsheet_import(erp):
    project, supplier = works_setup(erp)
    assert project['id'] > 0
    
    # Importar planilha orçamentária base
    items_payload = [
        {'code': '01.01', 'name': 'Serviços Preliminares e Canteiro', 'unit': 'm2', 'quantity': 100, 'unit_price': 5000, 'bdi': 10, 'discount': 5, 'start': '2026-01-01', 'end': '2026-02-28'},
        {'code': '02.01', 'name': 'Drenagem Pluvial e Manilhas', 'unit': 'm', 'quantity': 200, 'unit_price': 15000, 'bdi': 10, 'discount': 0, 'start': '2026-02-01', 'end': '2026-04-30'},
        {'code': '03.01', 'name': 'Pavimentação Asfáltica CBUQ', 'unit': 'm2', 'quantity': 500, 'unit_price': 8000, 'bdi': 15, 'discount': 0, 'start': '2026-03-01', 'end': '2026-06-30'}
    ]
    res = erp.client.post('/api/works/import-spreadsheet', json={'project_id': project['id'], 'items': items_payload, 'bdi_linear': 10, 'discount_linear': 0}, headers=erp.headers)
    assert res.status_code == 201, res.json
    assert res.json['items_created'] == 3
    assert res.json['total_amount'] > 0

def test_monthly_funding_projection_and_reports(erp):
    project, supplier = works_setup(erp)
    items_payload = [
        {'code': '01.01', 'name': 'Serviços Preliminares', 'unit': 'un', 'quantity': 1, 'unit_price': 100000, 'bdi': 0, 'discount': 0, 'start': '2026-01-01', 'end': '2026-03-31'}
    ]
    erp.client.post('/api/works/import-spreadsheet', json={'project_id': project['id'], 'items': items_payload}, headers=erp.headers)
    
    # Projeção de aportes mensais
    res = erp.client.get(f"/api/works/projects/{project['id']}/projection")
    assert res.status_code == 200
    data = res.json
    assert len(data['projection']) >= 3
    assert data['total_contracted'] == 100000
    
    # Relatório de aportes em CSV e PDF
    res_csv = erp.client.get(f"/api/works/reports?report=funding&project_id={project['id']}&format=csv")
    assert res_csv.status_code == 200
    assert 'Competência' in res_csv.data.decode('utf-8')
    
    res_pdf = erp.client.get(f"/api/works/reports?report=funding&project_id={project['id']}&format=pdf")
    assert res_pdf.status_code == 200
    assert res_pdf.data.startswith(b'%PDF')

def test_diaries_photos_and_stoppages(erp, reviewer):
    project, supplier = works_setup(erp)
    
    # Diário com dia trabalhado integral
    d1 = erp.make('works', 'diaries', project=project['id'], date='2026-01-10', weather='Bom', worked='Integral', activities='Escavação', equipment='Escavadeira', workforce='8 operários', occurrences='Nenhuma')
    reviewer.op(d1, 'approve_diary')
    
    # Diário com dia parado (chuva)
    d2 = erp.make('works', 'diaries', project=project['id'], date='2026-01-11', weather='Chuva', worked='Não trabalhado', activities='Paralisação por chuvas torrenciais', equipment='Estacionados', workforce='Dispensada', occurrences='Chuva intensa')
    reviewer.op(d2, 'approve_diary')
    
    # Anexar foto ao diário
    photo_res = erp.client.post(f"/api/works/diaries/{d1['id']}/photos", json={'filename': 'canteiro_dia10.jpg', 'caption': 'Início dos serviços de escavação'}, headers=erp.headers)
    assert photo_res.status_code == 201
    photo_id = photo_res.json['id']
    
    # Aprovar foto
    appr_res = reviewer.client.post(f"/api/works/photos/{photo_id}/approve", json={}, headers=reviewer.headers)
    assert appr_res.status_code == 200
    assert appr_res.json['approved'] is True
    
    # Listar fotos da obra
    list_photos = erp.client.get(f"/api/works/projects/{project['id']}/photos?approved=1")
    assert list_photos.status_code == 200
    assert len(list_photos.json['items']) == 1
    
    # Relatório de paralisações (dias não trabalhados e meio período)
    stop_res = erp.client.get('/api/works/reports?report=stoppages&format=pdf')
    assert stop_res.status_code == 200
    assert stop_res.data.startswith(b'%PDF')
    
    # Impressão do diário de obra em PDF
    diary_pdf = erp.client.get(f"/api/works/reports?report=diary&diary_id={d1['id']}&format=pdf")
    assert diary_pdf.status_code == 200
    assert diary_pdf.data.startswith(b'%PDF')

def test_measurements_retentions_and_project_close(erp, reviewer):
    project, supplier = works_setup(erp)
    item = erp.make('works', 'items', project=project['id'], code='01', name='Serviço A', unit='m', quantity='100', unit_price='1000', bdi=0, discount=0, start='2026-01-01', end='2026-01-31')
    
    # Diário aprovado no período
    d = erp.make('works', 'diaries', project=project['id'], date='2026-01-15', weather='Bom', worked='Integral', activities='Serviço A executado', equipment='Ferramentas', workforce='Equipe', occurrences='')
    reviewer.op(d, 'approve_diary')
    
    # Submeter medição de 40 unidades (40%)
    m = erp.make('works', 'measurements', project=project['id'], item=item['id'], start='2026-01-01', end='2026-01-20', quantity='40')
    res_sub = erp.op(m, 'submit_measurement')['result']
    assert res_sub['cumulative_quantity'] == 40000000
    
    # Aprovar medição
    reviewer.op(m, 'approve_measurement')
    
    # Pagamento parcial gerando retenção
    # Medido = 40 * R$ 1.000,00 = R$ 40.000,00 (4.000.000 centavos)
    p_med = erp.make('works', 'payments', measurement=m['id'], date='2026-01-25', amount='36000', type='Medição')
    res_pay = reviewer.op(p_med, 'pay_measurement')['result']
    assert res_pay['retention'] == 400000 # R$ 4.000,00 de retenção retida
    
    # Recebimento definitivo da obra
    reviewer.op(project, 'close_project', completed_date='2026-02-01')
    # A liberação de retenção exige prazo decorrido
    # Testar pagamento de retenção na data devida (30 dias após 2026-02-01 = 2026-03-03)
    p_ret = erp.make('works', 'payments', measurement=m['id'], date='2026-03-10', amount='4000', type='Retenção')
    res_ret_pay = reviewer.op(p_ret, 'pay_measurement')['result']
    assert res_ret_pay['amount'] == 400000

def test_linear_adjustment_amendments_and_public_transparency(erp, reviewer):
    project, supplier = works_setup(erp)
    erp.make('works', 'items', project=project['id'], code='A1', name='Item 1', unit='un', quantity='10', unit_price='1000', bdi=0, discount=0, start='2026-01-01', end='2026-02-28')
    erp.make('works', 'items', project=project['id'], code='A2', name='Item 2', unit='un', quantity='20', unit_price='2000', bdi=0, discount=0, start='2026-01-01', end='2026-02-28')
    
    # Reajuste linear de 10%
    version_obj = erp.make('works', 'spreadsheet_versions', project=project['id'], code='REV-02', name='Reajuste anual de 10%', type='Reajuste linear', adjustment_percent=10, date='2026-02-01', total_amount=1)
    res_adj = erp.op(version_obj, 'linear_adjustment')['result']
    assert res_adj['percent'] == 10.0
    
    # Aditivo de prazo
    res_amend_p = erp.client.post(f"/api/works/projects/{project['id']}/amend", json={'type': 'Prazo', 'new_end': '2026-12-31', 'justification': 'Prorrogação por chuvas'}, headers=erp.headers)
    assert res_amend_p.status_code == 200
    assert res_amend_p.json['new_end'] == '2026-12-31'
    
    # Aditivo de valor
    res_amend_v = erp.client.post(f"/api/works/projects/{project['id']}/amend", json={'type': 'Valor', 'amount': 50000, 'justification': 'Serviços complementares'}, headers=erp.headers)
    assert res_amend_v.status_code == 200
    
    # Indicadores do módulo de obras
    ind_res = erp.client.get('/api/works/indicators')
    assert ind_res.status_code == 200
    assert ind_res.json['total_projects'] >= 1
    
    # Portal público de obras
    pub_res = erp.client.get('/api/public/works')
    assert pub_res.status_code == 200
    assert len(pub_res.json['items']) >= 1
    assert any(p['code'] == 'OBRA-2026-001' for p in pub_res.json['items'])

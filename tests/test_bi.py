"""
Testes Automatizados para o Módulo de Business Intelligence (BI) e Painel Estratégico
Conformidade total com Edital PE 552/2026 e Anexo III (52 itens do módulo bi)
"""

import json
import pytest
from test_integrations import app, admin, erp
from db import get_db

@pytest.fixture(autouse=True)
def setup_bi_data(app):
    with app.app_context():
        from bi_seed import seed_bi
        seed_bi()

def test_bi_dashboards_metadata_and_layout(erp):
    # 1. Lista painéis cadastrados
    r = erp.client.get('/api/bi/dashboards', headers=erp.headers)
    assert r.status_code == 200
    dashboards = r.json
    assert len(dashboards) >= 6
    codes = [d['code'] for d in dashboards]
    assert 'DASH-EXEC-LRF' in codes
    assert 'DASH-FINANCEIRO' in codes
    assert 'DASH-PESSOAL' in codes
    assert 'DASH-COMPRAS' in codes
    assert 'DASH-PATRIMONIO' in codes
    assert 'DASH-CIDADAO-360' in codes

    # 2. Cria / Atualiza layout customizado de painel
    r_save = erp.client.post('/api/bi/dashboards', json={
        'code': 'DASH-EXEC-LRF',
        'title': 'Painel Executivo e Metas Constitucionais da LRF Atualizado',
        'area_type': 'EXECUTIVE_LRF',
        'description': 'Layout estratégico atualizado com semáforos da LRF',
        'layout_config': {'columns': 4, 'cards': ['saude', 'educacao', 'pessoal', 'caixa']},
        'is_kiosk_enabled': True,
        'kiosk_display_seconds': 20
    }, headers=erp.headers)
    assert r_save.status_code == 200
    assert r_save.json['code'] == 'DASH-EXEC-LRF'

    # 3. Cria novo painel personalizado
    r_new = erp.client.post('/api/bi/dashboards', json={
        'code': 'secretaria-fazenda',
        'title': 'Painel Estratégico da Fazenda Municipal',
        'area_type': 'FINANCEIRO',
        'description': 'Visão consolidada da arrecadação tributária e repasses',
        'layout_config': {'columns': 2},
        'is_kiosk_enabled': True,
        'kiosk_display_seconds': 15
    }, headers=erp.headers)
    assert r_new.status_code == 201
    assert r_new.json['code'] == 'secretaria-fazenda'

def test_bi_executive_lrf_dashboard(erp):
    # 1. Consulta painel de página única das metas LRF para 2026
    r = erp.client.get('/api/bi/dashboards/executive-lrf?exercise=2026', headers=erp.headers)
    assert r.status_code == 200
    data = r.json
    assert data['exercise'] == 2026
    assert 'as_of_date' in data

    # 2. Validação dos limites e semáforos constitucionais
    indicators = {i['code']: i for i in data['indicators']}
    assert 'SAUDE' in indicators
    assert indicators['SAUDE']['target_min'] == 15.00
    assert indicators['SAUDE']['realized'] >= 15.00
    assert indicators['SAUDE']['status'] == 'CUMPRIDO'

    assert 'EDUCACAO' in indicators
    assert indicators['EDUCACAO']['target_min'] == 25.00
    assert indicators['EDUCACAO']['realized'] >= 25.00
    assert indicators['EDUCACAO']['status'] == 'CUMPRIDO'

    assert 'PESSOAL_EXECUTIVO' in indicators
    assert indicators['PESSOAL_EXECUTIVO']['target_max'] == 54.00
    assert indicators['PESSOAL_EXECUTIVO']['realized'] <= 54.00

    assert 'DIVIDA_CONSOLIDADA' in indicators
    assert indicators['DIVIDA_CONSOLIDADA']['target_max'] == 120.00
    assert indicators['DIVIDA_CONSOLIDADA']['status'] == 'NORMAL'

    assert 'OPERACOES_CREDITO' in indicators
    assert indicators['OPERACOES_CREDITO']['target_max'] == 16.00

    assert 'ARO' in indicators
    assert indicators['ARO']['target_max'] == 7.00

    # 3. Resumo Orçamentário e Previdenciário (RPPS)
    summary = data['budget_summary']
    assert summary['revenue_predicted'] > 0
    assert summary['revenue_realized'] > 0
    assert summary['expense_settled'] > 0
    assert summary['rpps_revenue'] > 0
    assert summary['rpps_expense'] > 0
    assert summary['rpps_status'] in ['SUPERAVIT', 'DEFICIT']
    assert summary['savings_generation_capacity_pct'] > 0

    # 4. Alertas Estratégicos
    r_alerts = erp.client.get('/api/bi/alerts', headers=erp.headers)
    assert r_alerts.status_code == 200
    alerts = r_alerts.json
    assert len(alerts) >= 1
    assert any('PESSOAL' in a['indicator_code'] for a in alerts)

def test_bi_cash_availability_vs_obligations(erp):
    # Consulta disponibilidade bancária confrontada com obrigações
    r = erp.client.get('/api/bi/dashboards/cash-availability?exercise=2026', headers=erp.headers)
    assert r.status_code == 200
    data = r.json

    assert data['total_bank_availability'] > 0
    assert data['total_obligations_due'] > 0
    assert data['total_obligations_to_expire'] > 0
    assert data['net_financial_availability'] == round(
        data['total_bank_availability'] - data['total_obligations_due'] - data['total_obligations_to_expire'], 2
    )

    # Contas por instituição bancária
    banks = [b['bank_name'] for b in data['by_bank']]
    assert any('Banco do Brasil' in b for b in banks)
    assert any('Caixa Econômica Federal' in b for b in banks)

    # Contas por tipo / destinação
    account_types = [a['account_type'] for a in data['by_account_type']]
    assert any('Recursos Ordinários' in a for a in account_types)
    assert any('Saúde' in a for a in account_types)
    assert any('Educação' in a for a in account_types)

    # Evolução mensal do saldo
    assert len(data['monthly_evolution']) >= 1
    assert 'evolution' in data['monthly_evolution'][0]

    # Fornecedores pendentes de pagamento
    assert len(data['suppliers_to_pay']) >= 1
    assert any(s['status'] in ['VENCIDA', 'A_VENCER'] for s in data['suppliers_to_pay'])

def test_bi_budget_execution_funnel_and_nature_tree(erp):
    # Consulta funil de execução orçamentária
    r = erp.client.get('/api/bi/dashboards/budget-funnel?exercise=2026', headers=erp.headers)
    assert r.status_code == 200
    data = r.json

    # 4 estágios do funil
    stages = [f['stage'] for f in data['funnel']]
    assert any('1. Dotação' in s for s in stages)
    assert any('2. Despesa Empenhada' in s for s in stages)
    assert any('3. Despesa Liquidada' in s for s in stages)
    assert any('4. Despesa Efetivamente Paga' in s for s in stages)

    # Pendências
    assert data['pending_settlement'] >= 0
    assert data['pending_payment'] >= 0

    # Árvore hierárquica da despesa em 4 níveis
    tree = data['nature_tree']
    assert len(tree) >= 2 # Categoria 3 e Categoria 4
    cat3 = next(t for t in tree if '3 - Despesas Correntes' in t['level_1'])
    assert len(cat3['children']) >= 1
    grp31 = next(g for g in cat3['children'] if '3.1 - Pessoal' in g['level_2'])
    mod3190 = next(m for m in grp31['children'] if '3.1.90' in m['level_3'])
    assert any('3.1.90.11' in el['level_4'] for el in mod3190['children'])

    # Maiores fornecedores pagos
    assert len(data['top_suppliers_paid']) >= 3
    assert any('Enel' in s['supplier'] or 'CEDAE' in s['supplier'] for s in data['top_suppliers_paid'])

def test_bi_hr_and_turnover(erp):
    # Consulta BI de Recursos Humanos
    r = erp.client.get('/api/bi/dashboards/hr?exercise=2026', headers=erp.headers)
    assert r.status_code == 200
    data = r.json

    assert data['total_employees'] > 0
    assert data['admitted_count'] >= 0
    assert data['dismissed_count'] >= 0
    assert data['turnover_rate_pct'] >= 0
    assert data['hours_worked_pct'] > 80.0
    assert data['gross_payroll_total'] > 0
    assert data['net_payroll_total'] > 0

    # Faixas salariais
    assert len(data['salary_tiers']) >= 3
    assert any('Até 2' in t['tier'] for t in data['salary_tiers'])

    # Tipos de contrato
    types = [c['contract_type'] for c in data['by_contract_type']]
    assert any('Estatutário Efetivo' in t for t in types)
    assert any('Comissionado' in t for t in types)

    # Motivos de afastamento
    assert len(data['leave_reasons']) >= 1
    assert any('Saúde' in l['reason'] for l in data['leave_reasons'])

def test_bi_procurement_and_savings(erp):
    # Consulta BI de Licitações e Contratos
    r = erp.client.get('/api/bi/dashboards/procurement?exercise=2026', headers=erp.headers)
    assert r.status_code == 200
    data = r.json

    assert data['processes_opened'] > 0
    assert data['processes_closed'] > 0
    assert data['median_days_to_complete'] > 0
    assert data['negotiation_savings_pct'] > 0
    assert data['savings_amount'] > 0
    assert data['contracts_active'] > 0

    # Modalidades
    modalities = [m['modality'] for m in data['by_modality']]
    assert any('Pregão Eletrônico' in m for m in modalities)
    assert any('Dispensa' in m for m in modalities)

    # Contratos a vencer (30, 60, 90 dias)
    assert len(data['expiring_contracts']) >= 1
    assert any(c['days_left'] <= 30 for c in data['expiring_contracts'])

def test_bi_public_assets_and_depreciation(erp):
    # Consulta BI de Patrimônio Público
    r = erp.client.get('/api/bi/dashboards/assets?exercise=2026', headers=erp.headers)
    assert r.status_code == 200
    data = r.json

    assert data['total_assets_count'] > 0
    assert data['total_book_value'] > 0
    assert data['depreciation_value'] > 0
    assert data['net_asset_value'] == round(data['total_book_value'] - data['depreciation_value'], 2)

    # Categorias patrimoniais
    categories = [t['type'] for t in data['by_type']]
    assert any('Veículos' in c for c in categories)
    assert any('Bens Imóveis' in c for c in categories)

    # Motivos de baixa
    motives = [m['motive'] for m in data['writeoff_motives']]
    assert any('Inservibilidade' in m or 'Alienação' in m for m in motives)

def test_bi_person_360_view(erp):
    # 1. Consulta 360 por CPF com dados integrados
    r = erp.client.get('/api/bi/person-360?q=52998224725', headers=erp.headers)
    assert r.status_code == 200
    data = r.json

    assert 'contribuinte' in data
    assert 'fornecedor' in data
    assert 'servidor' in data
    assert 'processos_ouvidoria' in data

    # 2. Consulta 360 por CNPJ
    r_cnpj = erp.client.get('/api/bi/person-360?q=12.345.678/0001-99', headers=erp.headers)
    assert r_cnpj.status_code == 200
    assert r_cnpj.json['fornecedor']['is_supplier'] is True

    # 3. Validação de parâmetro obrigatório
    r_err = erp.client.get('/api/bi/person-360?q=', headers=erp.headers)
    assert r_err.status_code == 400

def test_bi_virtual_assistant_nlp(erp):
    # 1. Pergunta sobre despesa com pessoal
    r1 = erp.client.post('/api/bi/assistant/query', json={
        'question': 'Qual a situação da folha e servidores em 2026?'
    }, headers=erp.headers)
    assert r1.status_code == 200
    resp1 = r1.json
    assert resp1['domain'] == 'PESSOAS'
    assert 'servidores ativos' in resp1['answer'].lower()

    # 2. Pergunta sobre disponibilidade financeira / caixa
    r2 = erp.client.post('/api/bi/assistant/query', json={
        'question': 'Quanto temos de disponibilidade bancária?'
    }, headers=erp.headers)
    assert r2.status_code == 200
    resp2 = r2.json
    assert resp2['domain'] == 'FINANCEIRO'
    assert 'disponibilidade bancária' in resp2['answer'].lower()

    # 3. Pergunta sobre orçamento e receita
    r3 = erp.client.post('/api/bi/assistant/query', json={
        'question': 'Qual o desempenho da arrecadação e orçamento?'
    }, headers=erp.headers)
    assert r3.status_code == 200
    resp3 = r3.json
    assert resp3['domain'] == 'ORCAMENTO'

    # 4. Histórico de conversas do assistente
    r_hist = erp.client.get('/api/bi/assistant/history', headers=erp.headers)
    assert r_hist.status_code == 200
    history = r_hist.json
    assert len(history) >= 3

def test_bi_kiosk_slideshow_and_share_links(erp):
    # 1. Configuração do modo Kiosk em TV
    r_kiosk = erp.client.get('/api/bi/kiosk/slides', headers=erp.headers)
    assert r_kiosk.status_code == 200
    kiosk = r_kiosk.json
    assert kiosk['kiosk_mode_enabled'] is True
    assert kiosk['rotation_interval_seconds'] >= 10
    assert len(kiosk['slides']) >= 4

    # 2. Geração de link permanente de compartilhamento
    r_share = erp.client.post('/api/bi/share', json={
        'dashboard_code': 'executive-lrf',
        'filters': {'exercise': 2026}
    }, headers=erp.headers)
    assert r_share.status_code == 201
    share_data = r_share.json
    token = share_data['token']
    assert token

    # 3. Acesso autenticado ao painel compartilhado
    r_view = erp.client.get(f'/api/bi/shared/{token}', headers=erp.headers)
    assert r_view.status_code == 200
    assert r_view.json['dashboard_code'] == 'executive-lrf'
    assert 'data' in r_view.json

    # 4. Acesso público ao painel compartilhado (sem headers de autenticação)
    r_pub = erp.client.get(f'/api/public/bi/shared/{token}')
    assert r_pub.status_code == 200
    assert r_pub.json['dashboard_code'] == 'executive-lrf'

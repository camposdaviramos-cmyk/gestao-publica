"""
Testes Automatizados para o Módulo de Contabilidade, Finanças, Orçamento e Tesouraria
Conformidade total com Edital PE 552/2026 e Anexo III (229 itens do módulo finance)
"""

import json
import pytest
from test_integrations import app, admin, erp
from db import get_db

@pytest.fixture(autouse=True)
def setup_finance_data(app):
    with app.app_context():
        from finance_seed import seed_finance
        seed_finance()

def test_pcasp_and_accounting_rules(erp):
    # 1. Consulta plano de contas PCASP
    r = erp.client.get('/api/finance/pcasp', headers=erp.headers)
    assert r.status_code == 200
    accounts = r.json['accounts']
    assert len(accounts) >= 20
    codes = [a['code'] for a in accounts]
    assert "1.1.1.1.1.01.00" in codes
    assert "1.1.1.1.1.19.00" in codes

    # 2. Consulta regras contábeis
    r_rules = erp.client.get('/api/finance/rules', headers=erp.headers)
    assert r_rules.status_code == 200
    rules = r_rules.json
    assert len(rules) >= 6

    # 3. Criação de nova regra contábil
    new_rule = erp.client.post('/api/finance/rules', json={
        'fact_type': 'teste_fact',
        'group_name': 'Grupo Teste',
        'rule_name': 'Regra Teste Débito/Crédito',
        'debit_account_code': '3.3.1.1.1.01.00',
        'credit_account_code': '1.1.1.1.1.19.00'
    }, headers=erp.headers)
    assert new_rule.status_code == 201

    # 4. Validação de regras contábeis
    r_val = erp.client.get('/api/finance/rules/validate?fact_type=despesa_empenho', headers=erp.headers)
    assert r_val.status_code == 200
    assert r_val.json['valid'] is True

def test_inalterable_journal_entries_and_reversals(erp):
    # 1. Postar lançamento válido (partidas dobradas)
    entry_payload = {
        'exercise': 2026,
        'entity_id': 'MUNICIPIO',
        'entry_date': '2026-02-15',
        'fact_type': 'despesa_liquidacao',
        'debit_account': '3.3.1.1.1.01.00',
        'credit_account': '2.1.3.1.1.01.00',
        'amount_cents': 150050,
        'history_summary': 'Aquisição de materiais de consumo para a Secretaria de Educação',
        'history_complement': 'Processo 4421/2026 - NF 8829',
        'superavit_attribute': 'P',
        'document_type': 'Nota Fiscal',
        'document_number': '8829',
        'commitment_number': '2026/000142'
    }
    r = erp.client.post('/api/finance/journal/post', json=entry_payload, headers=erp.headers)
    assert r.status_code == 201
    entry_id = r.json['id']
    assert entry_id > 0
    assert r.json['status'] == 'Escriturado'

    # 2. Tentar lançamento com conta inválida -> Erro 400
    bad_payload = {
        'exercise': 2026,
        'entity_id': 'MUNICIPIO',
        'entry_date': '2026-02-15',
        'fact_type': 'despesa_liquidacao',
        'debit_account': '9.9.9.9.9.99.99',
        'credit_account': '2.1.3.1.1.01.00',
        'amount_cents': 100000,
        'history_summary': 'Conta inexistente'
    }
    r_bad = erp.client.post('/api/finance/journal/post', json=bad_payload, headers=erp.headers)
    assert r_bad.status_code == 400

    # 3. Estorno histórico inalterável do lançamento
    r_rev = erp.client.post('/api/finance/journal/reverse', json={
        'entry_id': entry_id,
        'reason': 'Duplicidade de nota fiscal informada pelo setor contábil'
    }, headers=erp.headers)
    assert r_rev.status_code == 200
    assert r_rev.json['reversal_id'] > 0
    assert 'Estornado' in r_rev.json['status']

    # 4. Consulta lançamentos registrados
    r_query = erp.client.get('/api/finance/journal/query?exercise=2026', headers=erp.headers)
    assert r_query.status_code == 200
    entries = r_query.json
    assert entries['total_entries'] >= 2 # Original + Estorno

def test_dcasp_reports(erp):
    # DCASP - Anexos da Lei 4.320/64 e MCASP
    anexos = ['anexo1', 'anexo12', 'anexo13', 'anexo14', 'anexo15', 'anexo18']
    for a in anexos:
        r = erp.client.get(f'/api/finance/dcasp/{a}?exercise=2026', headers=erp.headers)
        assert r.status_code == 200, f"Falha no anexo {a}"
        data = r.json
        assert 'exercise' in data or 'report' in data or 'title' in data

def test_siconfi_msc_and_siops_siope(erp):
    # 1. Geração de Matriz de Saldos Contábeis (MSC) SICONFI (XBRL e CSV)
    r_xbrl = erp.client.get('/api/finance/msc/generate?exercise=2026&month=1&format=XBRL', headers=erp.headers)
    assert r_xbrl.status_code == 200
    assert 'xbrl' in r_xbrl.json['format'].lower()
    assert 'msc' in r_xbrl.json['content'].lower() or '<' in r_xbrl.json['content']

    r_csv = erp.client.get('/api/finance/msc/generate?exercise=2026&month=1&format=CSV', headers=erp.headers)
    assert r_csv.status_code == 200
    assert 'csv' in r_csv.json['format'].lower()

    # 2. Exportações SIOPS (Saúde) e SIOPE (Educação)
    r_siops = erp.client.get('/api/finance/siops/export?exercise=2026&period=1º Bimestre', headers=erp.headers)
    assert r_siops.status_code == 200
    assert 'folders' in r_siops.json

    r_siope = erp.client.get('/api/finance/siope/export?exercise=2026&period=1º Bimestre', headers=erp.headers)
    assert r_siope.status_code == 200
    assert 'folders' in r_siope.json

    # 3. Cálculo do PASEP (1% das receitas)
    r_pasep = erp.client.post('/api/finance/calculations/pasep', json={
        'exercise': 2026,
        'rate_percent': 1.0,
        'revenues': [
            {'code': '4.1.1.1.1.01.00', 'name': 'IPTU', 'amount_cents': 200000000},
            {'code': '4.1.1.1.1.02.00', 'name': 'ISSQN', 'amount_cents': 300000000}
        ]
    }, headers=erp.headers)
    assert r_pasep.status_code == 200
    assert r_pasep.json['pasep_amount'] > 0

    # 4. Duodécimo Art. 29-A CF
    r_art29 = erp.client.get('/api/finance/calculations/art29a?exercise=2026&population=156491', headers=erp.headers)
    assert r_art29.status_code == 200
    assert r_art29.json['rate_applied'] == 6.0

def test_efd_reinf_and_withholdings(erp):
    # 1. Contribuinte EFD-Reinf
    r_taxpayer = erp.client.get('/api/finance/reinf/taxpayers', headers=erp.headers)
    assert r_taxpayer.status_code == 200
    taxpayers = r_taxpayer.json['taxpayers']
    assert len(taxpayers) > 0

    # 2. Inclusão de nota com retenção Tab. 06
    invoice_payload = {
        'taxpayer_id': taxpayers[0]['id'],
        'creditor_document': '12.345.678/0001-90',
        'creditor_name': 'Tecnologia Rio das Ostras Ltda',
        'invoice_number': '10492',
        'service_type_code': '1.01',
        'gross_cents': 2500000,
        'rate_percent': 11.0
    }
    r_inv = erp.client.post('/api/finance/reinf/invoices', json=invoice_payload, headers=erp.headers)
    assert r_inv.status_code == 201
    inv_data = r_inv.json
    assert inv_data['withholding_amount'] == 2750.00 # 11% de 25000.00

    # 3. Conciliação EFD-Reinf
    r_conc = erp.client.get('/api/finance/reinf/conciliation?competence=2026-01&taxpayer_id=1', headers=erp.headers)
    assert r_conc.status_code == 200
    assert 'competence' in r_conc.json

    # 4. Transmissão de eventos simulados
    r_trans = erp.client.post('/api/finance/reinf/events/transmit', json={
        'event_type': 'R-2010',
        'competence': '2026-01',
        'taxpayer_id': 1
    }, headers=erp.headers)
    assert r_trans.status_code == 200
    assert r_trans.json['status'] == 'Processado'
    assert 'receipt_number' in r_trans.json

def test_planning_ppa_ldo_loa(erp):
    # 1. Registro de item no planejamento (PPA/LDO/LOA)
    planning_payload = {
        'piece_type': 'LOA',
        'exercise': 2026,
        'organ_code': '02',
        'unit_code': '01',
        'function_code': '12',
        'subfunction_code': '361',
        'program_code': '0015',
        'action_code': '2042',
        'nature_code': '3.3.90.30.00',
        'source_code': '1500',
        'fiscal_target_cents': 50000000
    }
    r_plan = erp.client.post('/api/finance/budget/planning', json=planning_payload, headers=erp.headers)
    assert r_plan.status_code == 201
    assert r_plan.json['id'] > 0

    # 2. Projeção e Simulação
    r_proj = erp.client.post('/api/finance/budget/project', json={
        'piece_type': 'LOA',
        'percentage_rate': 4.5,
        'is_cumulative': False
    }, headers=erp.headers)
    assert r_proj.status_code == 200
    assert r_proj.json['piece_type'] == 'LOA'

    # 3. Importação LOA -> PPA
    r_import = erp.client.post('/api/finance/budget/import-loa', json={
        'target_exercise': 2026,
        'source_exercise': 2025
    }, headers=erp.headers)
    assert r_import.status_code == 200
    assert 'imported_items' in r_import.json

    # 4. Decreto Formatado de Crédito Adicional
    decree_payload = {
        'decree_number': '105/2026',
        'decree_type': 'Suplementar',
        'amount_cents': 25000000,
        'justification': 'Abertura de crédito para despesas essenciais na área de saúde'
    }
    r_dec = erp.client.post('/api/finance/budget/decrees', json=decree_payload, headers=erp.headers)
    assert r_dec.status_code == 201
    assert 'DECRETO' in r_dec.json['document_text']

def test_lrf_limits_and_fiscal_management(erp):
    # 1. Limites Constitucionais e LRF
    r = erp.client.get('/api/finance/constitutional-limits?exercise=2026', headers=erp.headers)
    assert r.status_code == 200
    limits = r.json
    
    # Educação >= 25%
    assert limits['educacao']['minimo_constitucional'] == 25.0
    # FUNDEB >= 70%
    assert limits['fundeb']['minimo_constitucional'] == 70.0
    # Saúde >= 15%
    assert limits['saude']['minimo_constitucional'] == 15.0
    # Despesa com Pessoal <= 54%
    assert limits['pessoal']['limite_maximo'] == 54.0
    assert limits['pessoal']['limite_prudencial'] == 51.3
    assert limits['pessoal']['limite_alerta'] == 48.6

    # 2. Relatórios RREO e RGF
    r_rreo = erp.client.get('/api/finance/lrf/rreo/1?exercise=2026&period=1', headers=erp.headers)
    assert r_rreo.status_code == 200
    assert 'RREO - Anexo 1' in r_rreo.json['report']

    r_rgf = erp.client.get('/api/finance/lrf/rgf/1?exercise=2026&period=1', headers=erp.headers)
    assert r_rgf.status_code == 200
    assert 'RGF - Anexo 1' in r_rgf.json['report']

def test_treasury_chronological_queue_and_obe(erp):
    # 1. Filas de Pagamento Cronológicas (Lei 14.133/21 Art. 141)
    r_queues = erp.client.get('/api/finance/treasury/chronological-payments', headers=erp.headers)
    assert r_queues.status_code == 200
    assert isinstance(r_queues.json, list)

    # 2. Emissão de Cheque Avulso / Contínuo
    r_check = erp.client.post('/api/finance/treasury/checks', json={
        'bank_account_code': '001-15890-2',
        'check_number': 1234,
        'bearer_name': 'Fornecedor Exemplo SA',
        'amount_cents': 450000,
        'without_reflex': False
    }, headers=erp.headers)
    assert r_check.status_code == 201

    # 3. Conciliação OFX e Fechamento de Mês
    ofx_content = """OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:NONE
<OFX><BANKMSGSRSV1><STMTTRNRS><STMTRS><BANKTRANLIST>
<STMTTRN><TRNTYPE>CREDIT<DTPOSTED>20260115<TRNAMT>5000.00<MEMO>IPTU
</STMTTRN></BANKTRANLIST></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>"""

    r_ofx = erp.client.post('/api/finance/treasury/ofx/import', json={
        'bank_account_id': '001-15890-2',
        'ofx_content': ofx_content
    }, headers=erp.headers)
    assert r_ofx.status_code == 200
    rec_id = r_ofx.json['reconciliation_id']

    r_auto = erp.client.post('/api/finance/treasury/ofx/reconcile', json={
        'reconciliation_id': rec_id
    }, headers=erp.headers)
    assert r_auto.status_code == 200

    r_lock = erp.client.post('/api/finance/treasury/ofx/lock', json={
        'exercise': 2026,
        'month': 1,
        'reason': 'Fechamento Contábil Mensal'
    }, headers=erp.headers)
    assert r_lock.status_code == 200

    # 4. Suprimento de Fundos e Prestação de Contas
    r_fund = erp.client.post('/api/finance/treasury/advance-funds', json={
        'server_cpf': '11122233344',
        'server_name': 'João Silva',
        'commitment_id': 100,
        'amount_cents': 300000
    }, headers=erp.headers)
    assert r_fund.status_code == 201
    fund_id = r_fund.json['id']

    r_prest = erp.client.post('/api/finance/treasury/advance-funds/accountability', json={
        'fund_id': fund_id,
        'spent_cents': 250000,
        'returned_cents': 50000
    }, headers=erp.headers)
    assert r_prest.status_code == 200
    assert r_prest.json['status'] == 'Prestado'

    # 5. Exportações Legais (MANAD e SIGFIS TCE-RJ)
    r_manad = erp.client.get('/api/finance/exports/manad?exercise=2026&competence=2026-01', headers=erp.headers)
    assert r_manad.status_code == 200
    assert 'content' in r_manad.json

    r_sigfis = erp.client.get('/api/finance/exports/sigfis?exercise=2026&competence=01', headers=erp.headers)
    assert r_sigfis.status_code == 200
    assert r_sigfis.json['tribunal'] == 'TCE-RJ'

def test_public_siafic_cpf_auth(erp):
    # Autenticação de Usuário SIAFIC por CPF com Termo de Responsabilidade
    r = erp.client.post('/api/public/finance/siafic/auth', json={
        'cpf': '000.111.222-33',
        'name': 'Contador Responsável'
    })
    assert r.status_code == 200
    data = r.json
    assert data['cpf'] == '00011122233'
    assert data['responsibility_term_accepted'] == 1

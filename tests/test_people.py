"""Testes automatizados completos para o Módulo de Gestão de Pessoas, Folha, Previdência, eSocial e SST.
Conformidade integral com os 117 itens do Anexo III (Edital PE 552/2026).
"""
import json
import pytest
from test_system import app, admin
from test_erp import ERP, erp
from db import get_db

@pytest.fixture(autouse=True)
def setup_people_data(app):
    with app.app_context():
        from people_seed import seed_people
        seed_people()

def test_work_locations_and_movements(erp):
    # Consulta locais de trabalho
    res = erp.client.get('/api/people/locations', headers=erp.headers)
    assert res.status_code == 200
    locations = res.json['locations']
    assert len(locations) >= 4
    adm = [l for l in locations if l['code'] == 'LOC-ADM'][0]
    assert 'CC-ADM-01' in adm['cost_centers']

    # Movimenta servidor
    mov_res = erp.client.post('/api/people/locations/movement', headers=erp.headers, json={
        'employee_id': 1,
        'origin_code': 'LOC-ADM',
        'destination_code': 'LOC-SAUDE',
        'reason': 'Reforço operacional da equipe de saúde'
    })
    assert mov_res.status_code == 200

    # Histórico de lotação
    hist_res = erp.client.get('/api/people/locations/history/1', headers=erp.headers)
    assert hist_res.status_code == 200
    assert len(hist_res.json['history']) >= 1

def test_rpps_funds_and_guide_emission(erp):
    # Consulta fundos previdenciários
    res = erp.client.get('/api/people/rpps/funds', headers=erp.headers)
    assert res.status_code == 200
    funds = res.json['funds']
    assert len(funds) >= 2
    previ = [f for f in funds if f['code'] == 'RPPS-PREVI'][0]
    assert previ['employee_rate'] == 14.0
    assert previ['supplementary_rate'] == 6.5

    # Emissão de Guia de Recolhimento do RioPrevi
    guide_res = erp.client.post('/api/people/rpps/guide', headers=erp.headers, json={
        'fund_code': 'RPPS-PREVI',
        'competence': '2026-03',
        'due_date': '2026-04-20'
    })
    assert guide_res.status_code == 200
    gdata = guide_res.json
    assert gdata['fund_code'] == 'RPPS-PREVI'
    assert gdata['total_guide'] > 0
    assert gdata['barcode'].startswith('8580')
    assert gdata['status'] == 'EMITIDA'

def test_consignable_margin_and_econsignado_import(erp):
    # Cria servidor se não existir
    emp = erp.client.get('/api/people/employees', headers=erp.headers).json['items']
    emp_id = emp[0]['id'] if emp else 1

    # Consulta de margem consignável
    res = erp.client.get(f'/api/people/consignments/margin/{emp_id}', headers=erp.headers)
    assert res.status_code == 200
    m = res.json['margin']
    assert m['allowed_margin_35pct'] > 0
    assert m['allowed_card_5pct'] > 0

    # Importação de lote eConsignado com registros válidos e com margem excedida
    records = [
        {'matricula': 'EMP-01', 'cpf': '123.456.789-00', 'nome': 'Servidor Regular', 'valor': 150.00, 'evento': 'DESC-CONSIGNADO'},
        {'matricula': 'EMP-01', 'cpf': '123.456.789-00', 'nome': 'Servidor Regular', 'valor': 99999.00, 'evento': 'DESC-CONSIGNADO'}, # Deve estourar margem
        {'matricula': 'INEXISTENTE', 'cpf': '000.000.000-00', 'nome': 'Desconhecido', 'valor': 200.00, 'evento': 'DESC-CONSIGNADO'} # Não localizado
    ]
    imp_res = erp.client.post('/api/people/consignments/econsignado/import', headers=erp.headers, json={
        'file_name': 'remessa_mar_2026.json',
        'format': 'JSON',
        'records': records
    })
    assert imp_res.status_code == 200
    idata = imp_res.json
    assert idata['total_records'] == 3
    assert idata['imported_records'] == 1
    assert idata['rejected_records'] == 2
    assert idata['divergent_records'] == 1

def test_vacancies_and_salary_caps(erp):
    # Quadro de vagas
    res = erp.client.get('/api/people/positions/vacancies?position_id=1&location=LOC-ADM', headers=erp.headers)
    assert res.status_code == 200
    vac = res.json['vacancies']
    assert vac['budgeted'] == 10
    assert vac['restriction_mode'] in ['BLOQUEIO', 'ADVERTENCIA', 'SEM_RESTRICAO']

    # Piso e teto salarial
    floor_res = erp.client.get('/api/people/positions/salary-limits?employee_id=1&salary=1200.00', headers=erp.headers)
    assert floor_res.status_code == 200
    assert floor_res.json['limits']['is_below_floor'] is True

    ceil_res = erp.client.get('/api/people/positions/salary-limits?employee_id=1&salary=45000.00', headers=erp.headers)
    assert ceil_res.status_code == 200
    assert ceil_res.json['limits']['is_above_ceiling'] is True
    assert ceil_res.json['limits']['exceeded_amount'] == 10000.00

def test_multi_contract_and_copy_employee(erp):
    emp = erp.client.get('/api/people/employees', headers=erp.headers).json['items']
    emp_id = emp[0]['id'] if emp else 1

    # Cópia de registro de funcionário
    copy_res = erp.client.post('/api/people/employees/copy', headers=erp.headers, json={
        'source_employee_id': emp_id,
        'new_registration': 'EMP-01-VINCULO2',
        'overrides': {'department': 'LOC-EDUC', 'salary': 4200.00}
    })
    assert copy_res.status_code == 200
    new_emp_id = copy_res.json['id']

    # Acúmulo de bases INSS nos múltiplos vínculos
    inss_res = erp.client.get(f'/api/people/payroll/multi-contract-inss/{new_emp_id}?competence=2026-03', headers=erp.headers)
    assert inss_res.status_code == 200
    data = inss_res.json
    assert data['total_accumulated_base'] > 4000.00
    assert len(data['calculation_memory']) > 0

def test_substitute_and_reintegration(erp):
    emp = erp.client.get('/api/people/employees', headers=erp.headers).json['items']
    orig_id = emp[0]['id'] if emp else 1
    sub_id = emp[1]['id'] if len(emp) > 1 else orig_id

    # Substituto eventual com matrícula própria
    sub_res = erp.client.post('/api/people/substitutes', headers=erp.headers, json={
        'original_employee_id': orig_id,
        'substitute_employee_id': sub_id,
        'new_registration': 'SUBST-001',
        'position_id': 1,
        'start_date': '2026-03-01',
        'end_date': '2026-06-30'
    })
    assert sub_res.status_code == 200
    assert sub_res.json['status'] == 'ATIVO'

    # Reintegração judicial
    reint_res = erp.client.post('/api/people/reintegrations', headers=erp.headers, json={
        'employee_id': orig_id,
        'reintegration_type': 'JUDICIAL',
        'process_number': '0001234-88.2025.8.19.0068',
        'retroactive_date': '2025-06-01'
    })
    assert reint_res.status_code == 200
    assert reint_res.json['status'] == 'EFETIVADA'

def test_judicial_alimony_age_cutoff(erp, app):
    emp = erp.client.get('/api/people/employees', headers=erp.headers).json['items']
    emp_id = emp[0]['id'] if emp else 1

    with app.app_context():
        db = get_db()
        # Insere beneficiário com mais de 24 anos (deve cessar) e menor de 24 anos (deve calcular)
        db.execute("""
            INSERT INTO people_judicial_alimonies (
                employee_id, beneficiary_name, beneficiary_cpf, birth_date,
                cutoff_age, calculation_mode, value_rate, status, created_at
            ) VALUES
            (?, 'Filho Maior', '999.888.777-66', '1998-01-01', 24, 'PERCENTAGE_NET', 15.00, 'ATIVO', '2026-01-01'),
            (?, 'Filha Menor', '888.777.666-55', '2015-05-10', 24, 'PERCENTAGE_NET', 15.00, 'ATIVO', '2026-01-01')
        """, (emp_id, emp_id))
        db.commit()

    res = erp.client.get(f'/api/people/alimonies/{emp_id}?gross=6000.00&net=5000.00', headers=erp.headers)
    assert res.status_code == 200
    items = res.json['items']
    maior = [i for i in items if i['beneficiary_name'] == 'Filho Maior'][0]
    menor = [i for i in items if i['beneficiary_name'] == 'Filha Menor'][0]
    assert maior['status'] == 'CESSADO_AUTOMATICO'
    assert menor['status'] == 'ATIVO'
    assert menor['amount'] == 750.00

def test_health_plan_and_transport_voucher(erp):
    emp = erp.client.get('/api/people/employees', headers=erp.headers).json['items']
    emp_id = emp[0]['id'] if emp else 1

    # Cálculo do plano de saúde por faixa etária
    hp_res = erp.client.post('/api/people/health-plans/calculate', headers=erp.headers, json={
        'employee_id': emp_id,
        'operator_code': 'MED-UNIMED',
        'age': 35
    })
    assert hp_res.status_code == 200
    hp = hp_res.json
    assert hp['monthly_total'] == 330.00
    assert hp['entity_coparticipation'] == 165.00
    assert hp['employee_discount'] == 165.00
    assert hp['dirf_code'] == '3568'

    # Cálculo do vale-transporte com teto de 6% do salário
    trans_res = erp.client.post('/api/people/transports/calculate', headers=erp.headers, json={
        'employee_id': emp_id,
        'line_id': 1,
        'daily_trips': 2,
        'working_days': 22
    })
    assert trans_res.status_code == 200
    tr = trans_res.json
    assert tr['monthly_total_cost'] == 198.00 # 4.50 * 2 * 22
    assert tr['employee_deduction_6pct_cap'] > 0
    assert tr['entity_burden'] >= 0

def test_salary_adjustments_and_vacation_interruption(erp, app):
    emp = erp.client.get('/api/people/employees', headers=erp.headers).json['items']
    emp_id = emp[0]['id'] if emp else 1

    # Simulação de reajuste salarial linear de 5%
    sim_res = erp.client.post('/api/people/adjustments/simulate', headers=erp.headers, json={
        'title': 'Reajuste Data-Base 2026',
        'mode': 'PERCENTUAL',
        'value': 5.0
    })
    assert sim_res.status_code == 200
    s_data = sim_res.json
    assert s_data['status'] == 'SIMULADO'
    assert s_data['difference'] > 0
    adj_id = s_data['id']

    # Efetivação do reajuste
    app_res = erp.client.post('/api/people/adjustments/apply', headers=erp.headers, json={
        'adjustment_id': adj_id
    })
    assert app_res.status_code == 200
    assert app_res.json['status'] == 'EFETIVADO'

    # Interrupção de férias por licença-maternidade
    with app.app_context():
        db = get_db()
        vac_id = db.execute("""
            INSERT INTO people_vacations_records (
                employee_id, vesting_start, vesting_end, enjoyment_start,
                enjoyment_end, days_enjoyed, status, created_at
            ) VALUES (?, '2025-01-01', '2025-12-31', '2026-03-01', '2026-03-30', 30, 'PROGRAMADA', '2026-01-01')
        """, (emp_id,)).lastrowid
        db.commit()

    vac_res = erp.client.post('/api/people/vacations/interrupt', headers=erp.headers, json={
        'vacation_id': vac_id,
        'maternity_start': '2026-03-10',
        'maternity_end': '2026-07-08'
    })
    assert vac_res.status_code == 200
    assert vac_res.json['status'] == 'INTERROMPIDA'
    assert vac_res.json['new_resumption_date'] == '2026-07-09'

def test_severance_and_payroll_lock_provisions(erp):
    emp = erp.client.get('/api/people/employees', headers=erp.headers).json['items']
    emp_id = emp[0]['id'] if emp else 1

    # Rescisão com HomologNet
    sev_res = erp.client.post('/api/people/severance/calculate', headers=erp.headers, json={
        'employee_id': emp_id,
        'termination_date': '2026-03-15',
        'termination_type': 'EXONERACAO_A_PEDIDO',
        'notice_type': 'DISPENSADO'
    })
    assert sev_res.status_code == 200
    s_data = sev_res.json
    assert s_data['gross_severance'] > 0
    assert '<homolognet' in s_data['homolognet_xml']

    # Bloqueio e desbloqueio da folha mensal
    lock_res = erp.client.post('/api/people/payroll/lock', headers=erp.headers, json={'competence': '2026-03'})
    assert lock_res.status_code == 200
    assert lock_res.json['is_locked'] is True

    unlock_res = erp.client.post('/api/people/payroll/unlock', headers=erp.headers, json={'competence': '2026-03'})
    assert unlock_res.status_code == 200
    assert unlock_res.json['is_locked'] is False

    # Provisões contábeis de férias e 13º
    prov_res = erp.client.post('/api/people/payroll/provisions', headers=erp.headers, json={'competence': '2026-03'})
    assert prov_res.status_code == 200
    assert len(prov_res.json['provisions']) == 2

def test_sisobi_confrontation(erp):
    records = [
        {'cpf': '123.456.789-00', 'nome': 'Servidor Teste', 'data_obito': '2026-03-01', 'certidao': '012345.01.55.2026.1.00001.001.0000001-01'},
        {'cpf': '999.999.999-99', 'nome': 'Cidadão Externo', 'data_obito': '2026-02-15', 'certidao': '012345.01.55.2026.1.00001.001.0000002-02'}
    ]
    res = erp.client.post('/api/people/sisobi/confront', headers=erp.headers, json={
        'filename': 'SISOBI_2026_MARCO.TXT',
        'records': records
    })
    assert res.status_code == 200
    d = res.json
    assert d['total_imported'] == 2
    assert d['deaths_detected'] >= 1
    # Confere que o servidor foi preventivamente bloqueado
    assert any(r['status_confronto'] == 'ATIVO_BLOQUEADO' for r in d['results'])

def test_portal_servidor_and_qr_code(erp):
    emp = erp.client.get('/api/people/employees', headers=erp.headers).json['items']
    emp_id = emp[0]['id'] if emp else 1
    cpf = emp[0]['cpf'] if emp else '123.456.789-00'

    # Login no portal com auto-provisionamento para servidor existente
    res = erp.client.post('/api/people/portal/auth', headers=erp.headers, json={
        'cpf': cpf,
        'password': 'MinhaSenhaSegura2026'
    })
    assert res.status_code == 200
    returned_emp_id = res.json['employee_id']

    # Solicitação de alteração cadastral com comprovante
    up_res = erp.client.post('/api/people/portal/update', headers=erp.headers, json={
        'employee_id': returned_emp_id,
        'field_name': 'email',
        'new_value': 'servidor.novo@riodasostras.rj.gov.br',
        'proof_file': 'comprovante_email.pdf'
    })
    assert up_res.status_code == 200
    up_id = up_res.json['id']

    # RH valida a alteração
    val_res = erp.client.post('/api/people/portal/updates/review', headers=erp.headers, json={
        'update_id': up_id,
        'action': 'VALIDAR'
    })
    assert val_res.status_code == 200
    assert val_res.json['status'] == 'VALIDADO_RH'

    # Geração de QR Code para contracheque
    qr_res = erp.client.post('/api/people/portal/payslip/qr', headers=erp.headers, json={
        'employee_id': returned_emp_id,
        'competence': '2026-03',
        'net_value': 3450.75
    })
    assert qr_res.status_code == 200
    token = qr_res.json['token']

    # Validação pública do QR Code sem necessidade de login
    pub_res = erp.client.get(f'/api/public/people/verify-payslip?token={token}&emp={returned_emp_id}&comp=2026-03')
    assert pub_res.status_code == 200
    assert pub_res.json['autentico'] is True

def test_service_time_certificate_and_esocial(erp):
    emp = erp.client.get('/api/people/employees', headers=erp.headers).json['items']
    emp_id = emp[0]['id'] if emp else 1

    # Emissão de Certidão de Tempo de Serviço
    cert_res = erp.client.post('/api/people/certificates/service-time', headers=erp.headers, json={'employee_id': emp_id})
    assert cert_res.status_code == 200
    cdata = cert_res.json
    assert 'CTS-' in cdata['certification_number']
    assert len(cdata['grade_efetividade']) > 0
    assert len(cdata['sha256_hash']) == 64

    # Diagnóstico da Qualificação Cadastral do eSocial
    diag_res = erp.client.get('/api/people/esocial/diagnosis', headers=erp.headers)
    assert diag_res.status_code == 200
    assert 'taxa_conformidade_pct' in diag_res.json

    # Totalizadores do eSocial S-1.3
    tot_res = erp.client.post('/api/people/esocial/totalizers', headers=erp.headers, json={'competence': '2026-03'})
    assert tot_res.status_code == 200
    assert tot_res.json['status'] == 'CONCILIADO_100_PORCENTO'

def test_sst_and_integrations(erp):
    emp = erp.client.get('/api/people/employees', headers=erp.headers).json['items']
    emp_id = emp[0]['id'] if emp else 1

    # Emissão de CAT
    cat_res = erp.client.post('/api/people/sst/cat', headers=erp.headers, json={
        'employee_id': emp_id,
        'cat_type': 'INICIAL',
        'accident_date': '2026-03-12',
        'accident_time': '14:20',
        'accident_type': 'TIPICO',
        'accident_location': 'Pátio de Obras e Manutenção',
        'cep': '28890-000',
        'affected_body_part': 'Perna Esquerda',
        'causative_agent': 'Queda de objeto / Andaime'
    })
    assert cat_res.status_code == 200
    assert cat_res.json['status'] == 'EMITIDA'

    # Emissão de PPP (Perfil Profissiográfico Previdenciário)
    ppp_res = erp.client.get(f'/api/people/sst/ppp/{emp_id}', headers=erp.headers)
    assert ppp_res.status_code == 200
    ppp = ppp_res.json['ppp']
    assert ppp['status'] == 'HOMOLOGADO_SST'
    assert len(ppp['fatores_risco']) > 0

    # Catálogo de EPIs com Certificado de Aprovação (CA)
    epis_res = erp.client.get('/api/people/sst/epis', headers=erp.headers)
    assert epis_res.status_code == 200
    epis = epis_res.json['epis']
    assert len(epis) >= 5
    assert any(e['ca_number'] == 'CA-11512' for e in epis)

    # Consulta CEP Correios com sandbox fallback
    cep_res = erp.client.get('/api/people/integrations/cep?cep=28890-000', headers=erp.headers)
    assert cep_res.status_code == 200
    assert cep_res.json['cidade'] == 'Rio das Ostras'

    # Consulta CBO MTE
    cbo_res = erp.client.get('/api/people/integrations/cbo?keyword=Advogado', headers=erp.headers)
    assert cbo_res.status_code == 200
    assert len(cbo_res.json['cbos']) >= 1

    # Tabela Oficial INSS
    inss_res = erp.client.get('/api/people/integrations/inss-table', headers=erp.headers)
    assert inss_res.status_code == 200
    assert inss_res.json['inss_table']['teto_contribuicao'] == 7786.02

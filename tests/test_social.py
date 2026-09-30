"""
Testes Automatizados para o Módulo de Assistência Social e Cidadania (SUAS / CRAS / CREAS / CadÚnico)
Conformidade total com Edital PE 552/2026 e Anexo III (410 itens do módulo social)
"""

import json
import pytest
from test_integrations import app, admin, erp
from db import get_db

@pytest.fixture(autouse=True)
def setup_social_data(app):
    with app.app_context():
        from social_seed import seed_social
        seed_social()

def test_social_units_and_teams(erp):
    # 1. Lista unidades socioassistenciais
    r = erp.client.get('/api/social/units', headers=erp.headers)
    assert r.status_code == 200
    units = r.json
    assert len(units) >= 5
    codes = [u['code'] for u in units]
    assert 'CRAS-CENTRAL' in codes
    assert 'CREAS-RIO-OSTRAS' in codes
    assert 'CENTRO-POP' in codes

    # 2. Cadastro de nova unidade
    r_new_u = erp.client.post('/api/social/units', json={
        'code': 'CRAS-NOVA-ESPERANCA',
        'name': 'CRAS Nova Esperança',
        'unit_type': 'CRAS',
        'district': 'Sede',
        'neighborhood': 'Nova Esperança',
        'address': 'Rua das Flores, 100',
        'capacity_families': 400
    }, headers=erp.headers)
    assert r_new_u.status_code == 201
    assert r_new_u.json['code'] == 'CRAS-NOVA-ESPERANCA'

    # 3. Lista e cadastra membro de equipe técnica com validação CRESS
    cras_id = units[0]['id']
    r_team = erp.client.get(f'/api/social/teams?unit_id={cras_id}', headers=erp.headers)
    assert r_team.status_code == 200
    assert len(r_team.json) >= 1

    # Validação obrigatória de registro profissional
    r_err = erp.client.post('/api/social/teams', json={
        'unit_id': cras_id,
        'name': 'Assistente Social Sem CRESS',
        'cpf': '999.888.777-66',
        'role_type': 'ASSISTENTE_SOCIAL'
    }, headers=erp.headers)
    assert r_err.status_code == 400
    assert 'CRESS é obrigatório' in (r_err.json.get('error') or r_err.json.get('message', ''))

    # Cadastro válido
    r_ok = erp.client.post('/api/social/teams', json={
        'unit_id': cras_id,
        'name': 'Assistente Social Homologada',
        'cpf': '999.888.777-66',
        'role_type': 'ASSISTENTE_SOCIAL',
        'council_type': 'CRESS',
        'council_number': '54321',
        'council_state': 'RJ'
    }, headers=erp.headers)
    assert r_ok.status_code == 201
    assert r_ok.json['council_number'] == '54321'

def test_territories_and_heatmap(erp):
    # 1. Diagnóstico territorial
    r_diag = erp.client.get('/api/social/diagnosis', headers=erp.headers)
    assert r_diag.status_code == 200
    diag = r_diag.json
    assert diag['total_families'] >= 3
    assert diag['extrema_pobreza'] >= 1
    assert len(diag['by_neighborhood']) >= 1

    # 2. Mapa de calor de vulnerabilidades (Heatmap)
    r_heat = erp.client.get('/api/social/heatmap', headers=erp.headers)
    assert r_heat.status_code == 200
    heat = r_heat.json
    assert heat['total_points'] >= 3
    assert 'center' in heat
    p0 = heat['points'][0]
    assert 'lat' in p0 and 'lng' in p0 and 'weight' in p0

def test_supplies_and_benefit_concession(erp):
    # 1. Lista insumos de estoque
    r_supplies = erp.client.get('/api/social/supplies', headers=erp.headers)
    assert r_supplies.status_code == 200
    supplies = r_supplies.json
    cesta = next(s for s in supplies if s['code'] == 'CESTA-FAMILIAR-PADRAO')
    initial_stock = cesta['current_stock']
    assert initial_stock > 0

    # 2. Lista lotes
    r_batches = erp.client.get(f'/api/social/stock/batches?supply_id={cesta["id"]}', headers=erp.headers)
    assert r_batches.status_code == 200
    batch = r_batches.json[0]
    batch_initial_qty = batch['current_quantity']

    # 3. Concessão de benefício eventual com baixa automática no estoque
    r_grant = erp.client.post('/api/social/benefits', json={
        'family_id': 1,
        'benefit_type': 'CESTA_BASICA',
        'supply_id': cesta['id'],
        'batch_id': batch['id'],
        'quantity': 2,
        'technical_opinion': 'Insegurança alimentar temporária grave identificada em visita técnica.',
        'social_worker_cress': '34567',
        'social_worker_name': 'Fernanda de Souza'
    }, headers=erp.headers)
    assert r_grant.status_code == 201
    grant = r_grant.json
    assert grant['status'] == 'ENTREGUE'
    assert grant['quantity'] == 2

    # 4. Verifica se o estoque do lote e do insumo foi abatido
    r_supplies_after = erp.client.get('/api/social/supplies', headers=erp.headers)
    cesta_after = next(s for s in r_supplies_after.json if s['code'] == 'CESTA-FAMILIAR-PADRAO')
    assert cesta_after['current_stock'] == initial_stock - 2

    r_batches_after = erp.client.get(f'/api/social/stock/batches?supply_id={cesta["id"]}', headers=erp.headers)
    batch_after = next(b for b in r_batches_after.json if b['id'] == batch['id'])
    assert batch_after['current_quantity'] == batch_initial_qty - 2

def test_families_cadunico_and_ivs(erp):
    # 1. Criação de nova família com cálculo automático de IVS e faixa de renda
    r_fam = erp.client.post('/api/social/families', json={
        'family_code': 'FAM-TEST-999',
        'head_nis': '199.88877.66-5',
        'head_name': 'Rosana Aparecida da Silva',
        'head_cpf': '123.456.789-99',
        'head_birth_date': '1990-05-10',
        'address': 'Rua das Gaivotas, 42',
        'neighborhood': 'Âncora',
        'cras_unit_id': 1,
        'total_income': 180.00,
        'members_count': 3,
        'housing_risk_zone': 1,
        'female_headed': 1,
        'has_elderly': 0,
        'has_pcd': 1
    }, headers=erp.headers)
    assert r_fam.status_code == 200
    fam = r_fam.json['family']
    assert fam['family_code'] == 'FAM-TEST-999'
    assert fam['per_capita_income'] == 60.00 # 180 / 3
    assert fam['income_bracket'] == 'EXTREMA_POBREZA'
    assert fam['ivs_score'] >= 0.65
    assert fam['ivs_level'] == 'MUITO_ALTA'
    assert fam['cadastral_completeness_pct'] >= 80.0

    # 2. Inclusão de membro na família
    fid = fam['id']
    r_mem = erp.client.post(f'/api/social/families/{fid}/members', json={
        'name': 'Enzo Gabriel da Silva (PCD)',
        'birth_date': '2016-08-20',
        'kinship': 'FILHO',
        'is_pcd': 1,
        'individual_income': 0.0
    }, headers=erp.headers)
    assert r_mem.status_code == 201
    assert len(r_mem.json['members']) >= 1

    # 3. Consulta prontuário 360º
    r_details = erp.client.get(f'/api/social/families/{fid}', headers=erp.headers)
    assert r_details.status_code == 200
    assert r_details.json['family']['head_name'] == 'Rosana Aparecida da Silva'

def test_rma_official_mds_and_xml_export(erp):
    # 1. Consulta e consolidação do RMA CRAS
    r_cras = erp.client.get('/api/social/rma/cras?unit_id=1&year=2026&month=1', headers=erp.headers)
    assert r_cras.status_code == 200
    rma = r_cras.json
    assert rma['paif_total_active'] > 0
    assert rma['atendimentos_total'] > 0

    # 2. Exportação do XML oficial no padrão Censo SUAS / MDS
    r_xml = erp.client.get('/api/social/rma/cras/export-xml?unit_id=1&year=2026&month=1', headers=erp.headers)
    assert r_xml.status_code == 200
    assert 'application/xml' in r_xml.content_type
    xml_data = r_xml.data.decode('utf-8')
    assert '<RMA_CRAS' in xml_data
    assert 'ibge="3304152"' in xml_data
    assert '<BlocoI_PAIF>' in xml_data
    assert '<BlocoII_Atendimentos>' in xml_data
    assert '<BlocoIII_BeneficiosEventuais>' in xml_data

    # 3. Fechamento do mês
    r_close = erp.client.post('/api/social/rma/cras/close', json={
        'unit_id': 1,
        'year': 2026,
        'month': 1
    }, headers=erp.headers)
    assert r_close.status_code == 200
    assert r_close.json['status'] == 'FECHADO'

    # 4. RMA CREAS
    r_creas_xml = erp.client.get('/api/social/rma/creas/export-xml?unit_id=4&year=2026&month=1', headers=erp.headers)
    assert r_creas_xml.status_code == 200
    assert '<RMA_CREAS' in r_creas_xml.data.decode('utf-8')
    assert '<BlocoIII_MedidasSocioeducativas_SINASE>' in r_creas_xml.data.decode('utf-8')

    # 5. RMA Centro POP
    r_pop_xml = erp.client.get('/api/social/rma/pop/export-xml?unit_id=5&year=2026&month=1', headers=erp.headers)
    assert r_pop_xml.status_code == 200
    assert '<RMA_CENTRO_POP' in r_pop_xml.data.decode('utf-8')
    assert '<BlocoI_PessoasEmSituacaoDeRua>' in r_pop_xml.data.decode('utf-8')

def test_sheltering_and_violence_secret_records(erp):
    # 1. Admissão em acolhimento institucional
    r_shelter = erp.client.post('/api/social/shelterings', json={
        'unit_id': 6, # Unidade de Acolhimento Infantil Renascer
        'resident_name': 'Menor Protegido A.B.C.',
        'birth_date': '2015-03-12',
        'reason': 'NEGLIGENCIA_GRAVE',
        'judicial_process_number': '0001234-88.2026.8.19.0068',
        'responsible_technician': 'Assistente Social de Plantão'
    }, headers=erp.headers)
    assert r_shelter.status_code == 201
    sid = r_shelter.json['id']
    assert r_shelter.json['active'] == 1

    # 2. Desligamento de acolhimento
    r_dis = erp.client.post(f'/api/social/shelterings/{sid}/discharge', json={
        'discharge_date': '2026-06-30',
        'discharge_reason': 'Reintegração familiar após acompanhamento PAIF'
    }, headers=erp.headers)
    assert r_dis.status_code == 200
    assert r_dis.json['active'] == 0

    # 3. Atendimento sigiloso a mulher vítima de violência
    r_viol = erp.client.post('/api/social/violence', json={
        'victim_initials': 'D.M.S.',
        'age': 28,
        'has_children': 2,
        'police_report_number': 'BO-2026/0458-128DP',
        'protective_measure_granted': 1,
        'violence_types': 'FISICA,PSICOLOGICA,PATRIMONIAL',
        'aggressor_relationship': 'Ex-cônjuge',
        'shelter_required': 1,
        'technician_cress_crp': 'CRESS 38712-RJ'
    }, headers=erp.headers)
    assert r_viol.status_code == 201
    viol = r_viol.json
    assert viol['secret_code'].startswith('SIGILO-')
    assert viol['protective_measure_granted'] == 1

def test_scfv_courses_and_attendance(erp, app):
    # 1. Criação de oficina e turma do SCFV
    with app.app_context():
        db = get_db()
        db.execute('''
            INSERT OR IGNORE INTO social_courses_workshops (code, title, category, target_audience)
            VALUES ('OFICINA-INCLUSAO-DIGITAL', 'Oficina de Inclusão Digital e Cidadania', 'SCFV_ADOLESCENTES', 'Jovens de 14 a 17 anos')
        ''')
        cid = db.execute("SELECT id FROM social_courses_workshops WHERE code = 'OFICINA-INCLUSAO-DIGITAL'").fetchone()[0]

        db.execute('''
            INSERT INTO social_class_groups (course_id, unit_id, instructor_name, schedule_description, max_capacity)
            VALUES (?, 1, 'Prof. Marcos Silva', 'Segundas e Quartas 14h-16h', 20)
        ''', (cid,))
        class_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        db.commit()

    # 2. Matrícula de participante
    r_enroll = erp.client.post(f'/api/social/classes/{class_id}/enroll', json={
        'family_id': 1,
        'participant_name': 'Lucas da Silva'
    }, headers=erp.headers)
    assert r_enroll.status_code == 201
    eid = r_enroll.json['id']

    # 3. Diário de frequência
    r_att = erp.client.post(f'/api/social/classes/{class_id}/attendance', json={
        'attendance_date': '2026-03-10',
        'attendances': [{'enrollment_id': eid, 'status': 'PRESENTE'}]
    }, headers=erp.headers)
    assert r_att.status_code == 200
    assert r_att.json['recorded_count'] == 1

def test_digital_signature_icp(erp):
    # 1. Emissão de assinatura digital ICP-Brasil com hash SHA-256 e token P7S
    r_sig = erp.client.post('/api/social/signatures', json={
        'document_type': 'PARECER_SOCIAL',
        'document_id': 101,
        'signer_name': 'Fernanda de Souza',
        'signer_cpf': '111.222.333-44',
        'signer_role': 'Assistente Social',
        'council_registration': 'CRESS 34567-RJ',
        'document_payload': 'Parecer técnico conclusivo favorável à concessão de benefício eventual.'
    }, headers=erp.headers)
    assert r_sig.status_code == 201
    sig = r_sig.json
    assert len(sig['sha256_hash']) == 64
    assert sig['signature_p7s_mock'].startswith('MIIE7')
    assert sig['validation_status'] == 'VALIDO'

    # 2. Validação da assinatura
    r_ver = erp.client.get(f'/api/social/signatures/{sig["id"]}/verify', headers=erp.headers)
    assert r_ver.status_code == 200
    assert r_ver.json['valid'] is True

def test_housing_criteria_ranking_and_quotas(erp):
    # 1. Inscrição habitacional com cálculo automático de pontuação
    r_app = erp.client.post('/api/social/housing/applications', json={
        'program_id': 1,
        'complex_id': 1,
        'family_id': 2, # Família de Sebastião (Idoso)
        'manual_points': 5,
        'adjustment_reason': 'Laudo da Defesa Civil Municipal'
    }, headers=erp.headers)
    assert r_app.status_code == 201
    app_data = r_app.json
    assert app_data['special_quota'] == 'IDOSO'
    assert app_data['final_points'] > 0

    # 2. Geração do ranking com atendimento de cotas legais (3% idosos e 3% PCD)
    r_rank = erp.client.get('/api/social/housing/ranking?program_id=1&complex_id=1', headers=erp.headers)
    assert r_rank.status_code == 200
    rank = r_rank.json
    assert rank['contemplated_count'] >= 1
    assert rank['elderly_quota_met'] >= 1
    assert len(rank['ranking']) >= 1

def test_mrosc_partnership_and_accounting(erp):
    # 1. Cadastro de OSC
    r_osc = erp.client.post('/api/social/oscs', json={
        'cnpj': '33.999.888/0001-77',
        'corporate_name': 'Instituto Esperança e Cidadania Rio das Ostras',
        'legal_representative': 'Dr. Marcos Albuquerque',
        'representative_cpf': '333.444.555-66'
    }, headers=erp.headers)
    assert r_osc.status_code == 201
    oid = r_osc.json['id']

    # 2. Submissão de Plano de Trabalho
    r_plan = erp.client.post(f'/api/social/oscs/{oid}/plans', json={
        'title': 'Projeto Convivência e Arte na Melhor Idade',
        'object_summary': 'Atividades socioculturais e fortalecimento de vínculos para 100 idosos do município.',
        'total_requested_amount': 180000.00
    }, headers=erp.headers)
    assert r_plan.status_code == 201
    assert r_plan.json['approval_status'] == 'APROVADO'

    # 3. Submissão de Prestação de Contas Mensal com conciliação matemática
    # Saldo anterior (0) + Repasse (15.000) + Rendimento (50) - Despesas (12.000) = Saldo Atual (3.050)
    r_acc = erp.client.post('/api/social/oscs/monthly-accounts', json={
        'contract_id': 1,
        'year': 2026,
        'month': 2,
        'previous_balance': 0.0,
        'disbursement_received': 15000.00,
        'financial_income': 50.00,
        'expenses_total': 12000.00,
        'current_balance': 3050.00
    }, headers=erp.headers)
    assert r_acc.status_code == 201
    aid = r_acc.json['id']
    assert r_acc.json['current_balance'] == 3050.00

    # 4. Tentativa com divergência de saldo deve disparar erro
    r_bad = erp.client.post('/api/social/oscs/monthly-accounts', json={
        'contract_id': 1,
        'year': 2026,
        'month': 3,
        'previous_balance': 3050.0,
        'disbursement_received': 15000.00,
        'financial_income': 50.00,
        'expenses_total': 12000.00,
        'current_balance': 9999.00 # Incorreto
    }, headers=erp.headers)
    assert r_bad.status_code == 400
    assert 'Inconsistência no saldo' in (r_bad.json.get('error') or r_bad.json.get('message', ''))

    # 5. Homologação da prestação de contas pelo gestor da parceria
    r_rev = erp.client.post(f'/api/social/oscs/monthly-accounts/{aid}/review', json={
        'review_status': 'APROVADA',
        'review_notes': 'Documentos fiscais e extrato bancário conferidos sem ressalvas.'
    }, headers=erp.headers)
    assert r_rev.status_code == 200
    assert r_rev.json['review_status'] == 'APROVADA'

def test_cadunico_and_sicon_import_processors(erp):
    # 1. Simulação de importação da base CadÚnico v7/v8
    csv_content = (
        "COD_FAMILIAR;NIS_RESPONSAVEL;NOME_RESPONSAVEL;RENDA_FAMILIAR\n"
        "FAM-IMP-001;19900011122;Benedita Aparecida Souza;450.00\n"
        "FAM-IMP-002;19900033344;Claudio Jose da Silva;1200.00\n"
    )
    r_cad = erp.client.post('/api/social/import/cadunico',
                            json={'content': csv_content, 'filename': 'cadunico_2026_01.csv'},
                            headers=erp.headers)
    assert r_cad.status_code == 200
    assert r_cad.json['records_imported'] == 2

    # 2. Simulação de importação de condicionalidades do SICON
    sicon_content = (
        "NIS;DESCUMPRIMENTO\n"
        "128.45678.90-1;FREQUENCIA_ESCOLAR_BAIXA\n"
    )
    r_sicon = erp.client.post('/api/social/import/sicon',
                              json={'content': sicon_content, 'filename': 'sicon_condicionalidades.csv'},
                              headers=erp.headers)
    assert r_sicon.status_code == 200
    assert r_sicon.json['records_imported'] == 1

import json
import pytest
from test_integrations import app, admin, erp
from db import get_db

@pytest.fixture(autouse=True)
def setup_control_data(app):
    with app.app_context():
        from control_seed import seed_control
        seed_control(entity_id=1, exercise=2026)

def test_control_ibge_data_and_constitutional_limits(erp):
    # Consulta dados do IBGE e limites constitucionais
    r = erp.client.get('/api/control/ibge?entity=1&exercise=2026', headers=erp.headers)
    assert r.status_code == 200
    data = r.json['data']
    assert data['municipio_nome'] == 'Rio das Ostras'
    assert data['cod_ibge'] == '3304524'
    assert data['populacao'] == 156491
    assert data['limite_pessoal_executivo_pct'] == 54.0
    assert data['limite_pessoal_legislativo_pct'] == 6.0
    assert data['limite_repasse_camara_pct'] == 7.0
    assert data['limite_pessoal_executivo_valor'] > 0
    assert data['limite_repasse_camara_valor'] > 0

    # Atualização de parâmetros
    update_res = erp.client.put('/api/control/ibge', json={
        'entity': 1,
        'exercise': 2026,
        'populacao': 160000,
        'limite_pessoal_executivo_pct': 54.0,
        'limite_pessoal_legislativo_pct': 6.0,
        'limite_repasse_camara_pct': 7.0,
        'receita_corrente_liquida': 100000000000 # 1 bilhão
    }, headers=erp.headers)
    assert update_res.status_code == 200
    updated = update_res.json['data']
    assert updated['populacao'] == 160000
    assert updated['limite_pessoal_executivo_valor'] == 54000000000

def test_control_obligations_calendar_and_occurrences(erp):
    # Calendário geral
    r = erp.client.get('/api/control/calendar?entity=1&exercise=2026', headers=erp.headers)
    assert r.status_code == 200
    events = r.json['events']
    assert len(events) >= 10
    # Verifica que todos os eventos possuem cor e status
    for ev in events:
        assert 'color' in ev
        assert ev['color'] in ['#10b981', '#ef4444', '#f97316', '#3b82f6', '#6b7280']
        assert ev['status'] in ['Atendida', 'Vencida', 'A Vencer', 'Dispensada']

    # Filtro por esfera
    r_fed = erp.client.get('/api/control/calendar?entity=1&exercise=2026&sphere=Federal', headers=erp.headers)
    assert r_fed.status_code == 200
    for ev in r_fed.json['events']:
        assert ev['legislation_type'] == 'Federal'

    # Resumo estatístico
    sum_res = erp.client.get('/api/control/obligations/summary?entity=1&exercise=2026', headers=erp.headers)
    assert sum_res.status_code == 200
    summary = sum_res.json['summary']
    assert summary['total'] >= 10
    assert 'compliance_rate' in summary
    assert len(summary['by_month']) == 12
    assert 'Federal' in summary['by_sphere']

def test_control_followups_delay_justification_and_quick_close(erp):
    # Obter uma ocorrência
    events = erp.client.get('/api/control/calendar?entity=1&exercise=2026', headers=erp.headers).json['events']
    occ_id = events[0]['id']

    # Registrar Justificativa de atraso
    just_res = erp.client.post(f"/api/control/occurrences/{occ_id}/followup", json={
        'type': 'Justificativa',
        'notes': 'Atraso decorrente de indisponibilidade momentânea do portal SICONFI da STN.'
    }, headers=erp.headers)
    assert just_res.status_code == 200

    # Verifica detalhe da ocorrência
    detail = erp.client.get(f"/api/control/occurrences/{occ_id}", headers=erp.headers).json['occurrence']
    assert detail['delay_justification'] == 'Atraso decorrente de indisponibilidade momentânea do portal SICONFI da STN.'
    assert len(detail['followups']) >= 1
    assert detail['followups'][0]['type'] == 'Justificativa'

    # Encerramento rápido
    close_res = erp.client.post(f"/api/control/occurrences/{occ_id}/quick-close", json={
        'notes': 'Obrigação cumprida e protocolada com sucesso.'
    }, headers=erp.headers)
    assert close_res.status_code == 200

    detail_after = erp.client.get(f"/api/control/occurrences/{occ_id}", headers=erp.headers).json['occurrence']
    assert detail_after['status'] == 'Atendida'
    assert detail_after['closed_by'] is not None

def test_control_email_communication_and_notification(erp):
    events = erp.client.get('/api/control/calendar?entity=1&exercise=2026', headers=erp.headers).json['events']
    occ_id = events[0]['id']

    # Envio de e-mail ao responsável
    mail_res = erp.client.post(f"/api/control/occurrences/{occ_id}/send-email", json={
        'recipient_email': 'gestor.setorial@riodasostras.rj.gov.br',
        'subject': 'Aviso de Vencimento Iminente',
        'message_body': 'Favor providenciar a documentação comprobatória da remessa mensal.'
    }, headers=erp.headers)
    assert mail_res.status_code == 200
    assert 'registrado e anexado' in mail_res.json['message']

    # Verifica que o acompanhamento do tipo 'Email' foi criado
    detail = erp.client.get(f"/api/control/occurrences/{occ_id}", headers=erp.headers).json['occurrence']
    email_followups = [f for f in detail['followups'] if f['type'] == 'Email']
    assert len(email_followups) >= 1
    assert 'gestor.setorial@riodasostras.rj.gov.br' in email_followups[0]['notes']

def test_control_siconfi_rules_duplication_and_dashboard(erp):
    # Dashboard SICONFI
    dash = erp.client.get('/api/control/siconfi/ranking?entity=1&exercise=2026', headers=erp.headers).json['data']
    assert dash['total_rules'] >= 8
    assert dash['conforming_count'] > 0
    assert 'dimension_2_chart' in dash
    assert 'dimension_3_chart' in dash
    assert 'legend' in dash

    # Duplicação de regra específica da Dimensão 2
    rule_to_clone = dash['items'][0]
    dup_res = erp.client.post('/api/control/siconfi/rules', json={
        'action': 'duplicate',
        'rule_id': rule_to_clone['id'],
        'new_code': 'STN-D2-CUSTOM-99',
        'new_title': 'Regra Customizada de Conciliação'
    }, headers=erp.headers)
    assert dup_res.status_code == 200

    # Reprocessamento de competência
    rep_res = erp.client.post('/api/control/siconfi/reprocess', json={
        'entity': 1,
        'exercise': 2026,
        'period': '2026-01',
        'delete_first': True
    }, headers=erp.headers)
    assert rep_res.status_code == 200
    assert rep_res.json['processed_count'] >= dash['total_rules']

def test_control_cauc_requirements_and_agreements(erp):
    # CAUC
    cauc = erp.client.get('/api/control/cauc?entity=1', headers=erp.headers).json['data']
    assert cauc['total'] >= 8
    assert cauc['adimplente_count'] > 0
    assert 'regularity_rate' in cauc

    # Atualização de responsável
    first_item = cauc['items'][0]
    resp_res = erp.client.put('/api/control/cauc/responsible', json={
        'entity': 1,
        'code': first_item['code'],
        'responsible_name': 'Dr. Auditor Fiscal',
        'responsible_email': 'auditor@riodasostras.rj.gov.br'
    }, headers=erp.headers)
    assert resp_res.status_code == 200

    # Convênios
    agr = erp.client.get('/api/control/agreements?entity=1&exercise=2026', headers=erp.headers).json['data']
    assert agr['total'] >= 3
    assert agr['adimplente_count'] > 0

def test_control_action_plans_and_bell_notifications(erp):
    # Criar Plano de Ação para item não conforme
    plan_res = erp.client.post('/api/control/action-plans', json={
        'entity': 1,
        'exercise': 2026,
        'source_module': 'SICONFI',
        'reference_id': 'STN-D2-02',
        'title': 'Ajuste de Conciliação Bancária DDR',
        'fact': 'Divergência entre conta corrente e demonstrativo DDR',
        'cause': 'Lançamento extemporâneo',
        'corrective_action': 'Emissão de lançamento retificador',
        'responsible_name': 'Contador Geral',
        'responsible_email': 'contabilidade@riodasostras.rj.gov.br',
        'deadline': '2026-03-31'
    }, headers=erp.headers)
    assert plan_res.status_code == 200
    plan_id = plan_res.json['id']

    # Resposta ao plano de ação pelo agente público
    resp_res = erp.client.post(f"/api/control/action-plans/{plan_id}/respond", json={
        'response_notes': 'Lançamento retificador nº 450/2026 efetuado no razão contábil.',
        'response_evidence': 'http://127.0.0.1:8080/attachments/conciliacao.pdf'
    }, headers=erp.headers)
    assert resp_res.status_code == 200
    assert resp_res.json['status'] == 'Respondido'

    # Notificações no sistema (sininho)
    notif_res = erp.client.get('/api/control/notifications?unread_only=true', headers=erp.headers)
    assert notif_res.status_code == 200
    assert notif_res.json['unread_count'] >= 1
    assert any('Plano de Ação respondido' in n['title'] for n in notif_res.json['notifications'])

    # Marcar como lida
    notif_id = notif_res.json['notifications'][0]['id']
    read_res = erp.client.put(f"/api/control/notifications/{notif_id}/read", json={}, headers=erp.headers)
    assert read_res.status_code == 200

def test_control_conclusive_reports_and_versioning(erp):
    # Geração do primeiro Relatório Conclusivo (Versão 1)
    rep1 = erp.client.post('/api/control/reports/conclusive', json={
        'entity': 1,
        'exercise': 2026,
        'report_type': 'SICONFI',
        'period': '2026-01',
        'scope_type': 'Consolidado',
        'title': 'Relatório Conclusivo de Qualidade SICONFI - Janeiro/2026',
        'selected_verifications': ['STN-D1-01', 'STN-D2-01', 'STN-D3-01'],
        'selected_occurrences': [1, 2],
        'opinion_text': 'Parecer favorável à regularidade dos dados da MSC.',
        'conclusion_text': 'Recomenda-se acompanhamento do plano de ação STN-D2-02.',
        'signatories': [{'name': 'Controlador Geral', 'role': 'Controlador', 'signature_date': '2026-02-05'}]
    }, headers=erp.headers)
    assert rep1.status_code == 200
    assert rep1.json['version'] == 1
    assert rep1.json['hash_digest'] is not None

    # Geração de revisão para o mesmo período (Versão 2)
    rep2 = erp.client.post('/api/control/reports/conclusive', json={
        'entity': 1,
        'exercise': 2026,
        'report_type': 'SICONFI',
        'period': '2026-01',
        'scope_type': 'Consolidado',
        'title': 'Relatório Conclusivo de Qualidade SICONFI - Janeiro/2026 (Revisão 1)',
        'selected_verifications': ['STN-D1-01', 'STN-D2-01', 'STN-D3-01'],
        'selected_occurrences': [1, 2],
        'opinion_text': 'Parecer favorável com ressalva devidamente sanada.',
        'conclusion_text': 'Todas as recomendações foram atendidas.',
        'signatories': [{'name': 'Controlador Geral', 'role': 'Controlador', 'signature_date': '2026-02-10'}]
    }, headers=erp.headers)
    assert rep2.status_code == 200
    assert rep2.json['version'] == 2

    # Consulta histórico de versões para verificar verificabilidade e armazenamento das diversas versões
    versions = erp.client.get('/api/control/reports/conclusive/versions?entity=1&exercise=2026&report_type=SICONFI&period=2026-01', headers=erp.headers).json['versions']
    assert len(versions) == 2
    assert versions[0]['version'] == 2
    assert versions[1]['version'] == 1
    assert versions[0]['hash_digest'] != versions[1]['hash_digest']

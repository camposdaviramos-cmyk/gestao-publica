"""Testes automatizados do módulo de Compras, Licitações e Contratos (Lei 14.133/2021)."""
import json
from datetime import date, timedelta
from decimal import Decimal
import pytest
from test_erp import ERP, erp, reviewer
from test_system import app, admin, login, user
from db import get_db

def procurement_setup(erp):
    # Cadastrar fornecedor habilitado
    supplier = erp.make(
        'procurement', 'suppliers',
        code='FORN-001',
        name='Comércio & Serviços Rio das Ostras Ltda',
        document='11222333000181',
        email='contato@fornecedor.test',
        phone='(22) 2764-0000',
        address='Rua das Flores, 100, Rio das Ostras - RJ'
    )
    return supplier

def test_procurement_process_bids_and_discount_judgment(erp, reviewer):
    supplier = procurement_setup(erp)
    
    # Criar processo licitatório com critério de Maior Desconto e Inversão de Fases
    proc = erp.make(
        'procurement', 'processes',
        code='PE-01/2026',
        name='Registro de Preços para Aquisição de Materiais de Escritório',
        modality='Pregão',
        judgment='Maior desconto',
        legal_basis='Lei nº 14.133/2021, Art. 28, I',
        publication='2026-01-10',
        opening='2026-01-25',
        business_days=10,
        estimated='50000',
        technical_opinion='Termo de Referência aprovado pela comissão de planejamento',
        legal_opinion='Parecer Jurídico favorável nº 12/2026',
        inverted=True,
        consortium=False
    )
    assert proc['id'] > 0
    
    # Cadastrar item da contratação com valor de referência
    item = erp.make(
        'procurement', 'items',
        code='01',
        name='Papel A4 Sulfite 75g',
        process=proc['id'],
        unit='Resma',
        quantity='1000',
        unit_price='30.00', # R$ 30,00 referência
        lot='Lote 1',
        manufacturer='Chamex',
        barcode='7891000000001'
    )
    assert item['id'] > 0
    
    # Inserir lances na sessão pública
    bid_payload = {
        'item_id': item['id'],
        'supplier_id': supplier['id'],
        'bid_amount': 2700, # R$ 27,00 (10% de desconto)
        'discount_percent': 10.0,
        'bid_type': 'Lance',
        'notes': 'Primeira rodada de lances'
    }
    res_bid = erp.client.post(f"/api/procurement/processes/{proc['id']}/bids", json=bid_payload, headers=erp.headers)
    assert res_bid.status_code == 201
    assert res_bid.json['discount'] == 10.0
    
    # Consultar lances
    res_list = erp.client.get(f"/api/procurement/processes/{proc['id']}/bids?item_id={item['id']}", headers=erp.headers)
    assert res_list.status_code == 200
    assert len(res_list.json['bids']) >= 1
    
    # Inversão de fases: Habilitação antes de Julgamento
    res_phase1 = erp.op(proc, 'advance_process', reason='Edital publicado e impugnações respondidas')
    assert res_phase1['result']['phase'] == 'Edital'
    erp.op(proc, 'advance_process', reason='Publicação no PNCP e diário oficial')
    # Na inversão de fases, a próxima fase após Divulgado é Habilitação
    res_inv = erp.op(proc, 'advance_process', reason='Abertura da sessão de habilitação prévia')
    assert res_inv['result']['phase'] == 'Habilitação'

def test_price_agreement_srp_and_alerts(erp, reviewer):
    supplier = procurement_setup(erp)
    proc = erp.make(
        'procurement', 'processes',
        code='PE-02/2026',
        name='Registro de Preços para Fornecimento de Combustíveis',
        modality='Pregão',
        judgment='Menor preço',
        legal_basis='Lei nº 14.133/2021',
        publication='2026-01-05',
        opening='2026-01-20',
        business_days=8,
        estimated='100000',
        technical_opinion='Aprovado',
        legal_opinion='Aprovado'
    )
    item = erp.make(
        'procurement', 'items',
        code='01',
        name='Gasolina Comum',
        process=proc['id'],
        unit='Litros',
        quantity='20000',
        unit_price='5.50'
    )
    
    # Gerar Ata de Registro de Preços (SRP)
    res_srp = reviewer.op(
        proc, 'generate_price_agreement',
        code='ARP-05/2026',
        name='Ata de Registro de Preços para Combustíveis 2026',
        supplier_id=supplier['id'],
        start='2026-01-20',
        end='2027-01-19',
        carona_permitted=True
    )
    assert res_srp['result']['id'] > 0
    agr_id = res_srp['result']['id']
    
    # Testar verificação de alerta de Ata de Registro de Preços vigente
    res_alert = erp.client.get('/api/procurement/check-srp-alerts?terms=Gasolina,Diesel', headers=erp.headers)
    assert res_alert.status_code == 200
    alert_data = res_alert.json
    assert alert_data['has_active_srp'] is True
    assert alert_data['alerts_count'] >= 1
    assert alert_data['alerts'][0]['agreement_code'] == 'ARP-05/2026'
    
    # Listar itens da Ata
    res_items = erp.client.get(f"/api/procurement/agreements/{agr_id}/items", headers=erp.headers)
    assert res_items.status_code == 200
    assert len(res_items.json['items']) >= 1
    assert res_items.json['items'][0]['available_quantity'] == 20000.0
    
    # Autorizar adesão por carona
    res_carona = reviewer.op(
        proc, 'register_carona',
        agreement_id=agr_id,
        entity_name='Prefeitura Municipal de Casimiro de Abreu',
        entity_cnpj='29123456000199',
        authorized_amount=1000000
    )
    assert res_carona['result']['status'] == 'Autorizada'

def test_summon_remaining_bidders(erp, reviewer):
    supplier = procurement_setup(erp)
    other_supplier = erp.make('procurement', 'suppliers', code='FORN-002', name='Outra Fornecedora Eireli', document='00000000000191')
    
    proc = erp.make('procurement', 'processes', code='PE-03/2026', name='Contratação de Serviços de Limpeza Urbana', modality='Pregão', judgment='Menor preço', legal_basis='Lei 14.133/2021')
    item = erp.make('procurement', 'items', code='01', name='Serviço de Varrição', process=proc['id'], unit='Mês', quantity='12', unit_price='10000.00')
    
    # Convocar licitante remanescente (2º colocado) nos termos do Art. 90 da Lei 14.133/2021
    res_summon = erp.client.post(
        f"/api/procurement/processes/{proc['id']}/summon-remanescentes",
        json={
            'supplier_id': other_supplier['id'],
            'item_id': item['id'],
            'rank_position': 2,
            'accepted_winner_conditions': True,
            'unit_price': 980000,
            'deadline_days': 5,
            'justification': 'Primeiro colocado desclassificado por recusa injustificada em assinar o contrato'
        },
        headers=erp.headers
    )
    assert res_summon.status_code == 201
    assert res_summon.json['status'] == 'Convocado'
    
    # Listar convocações
    res_list = erp.client.get(f"/api/procurement/processes/{proc['id']}/summons", headers=erp.headers)
    assert res_list.status_code == 200
    assert len(res_list.json['summons']) >= 1

def test_pca_versions_and_lifecycle(erp, reviewer):
    # Criar item de PCA
    pca_item = erp.make(
        'procurement', 'pca',
        code='PCA-01',
        name='Aquisição de Equipamentos de Informática',
        department='Secretaria Municipal de Administração',
        quantity='50',
        estimated='150000',
        priority='Alta',
        due_date='2026-06-30'
    )
    assert pca_item['state'] == 'Rascunho'
    
    # Reprovação antes da aprovação
    reviewer.op(pca_item, 'reject_pca', justification='Ajustar quantitativos das unidades requisitantes')
    latest = erp.get(pca_item)
    assert latest['state'] == 'Reprovado'
    
    # Criar item de PCA revisado para aprovação e publicação
    pca_item2 = erp.make(
        'procurement', 'pca',
        code='PCA-02',
        name='Aquisição de Equipamentos e Mobiliário Escolar',
        department='Secretaria de Educação',
        quantity='100',
        estimated='200000',
        priority='Alta',
        due_date='2026-08-31'
    )
    res_app = reviewer.op(pca_item2, 'approve_pca', justification='Plano consolidado com todas as secretarias municipais')
    assert res_app['result']['status'] == 'Aprovado'
    
    # Publicar no PNCP
    res_pub = reviewer.op(pca_item2, 'publish_pca_pncp')
    assert res_pub['result']['status'] == 'Publicado PNCP'
    assert 'PNCP-PCA-2026' in res_pub['result']['transmission_id']
    
    # Consultar versões do PCA via API
    res_ver = erp.client.get(f"/api/procurement/pca/versions?exercise={pca_item2['exercise']}", headers=erp.headers)
    assert res_ver.status_code == 200
    assert len(res_ver.json['versions']) >= 1
    
    # Copiar PCA para novo exercício
    res_copy = reviewer.op(pca_item2, 'copy_pca', exercise=2027)
    assert res_copy['result']['exercise'] == 2027

def test_supplier_certificates_sanctions_and_contract_summary(erp, reviewer):
    supplier = procurement_setup(erp)
    
    # 1. Cadastrar CNDs do fornecedor
    cnd_payload = {
        'type': 'Federal/INSS',
        'number': 'CND-FED-2026-999',
        'issue_date': '2026-01-01',
        'expiration_date': '2026-12-31',
        'verification_url': 'https://receita.fazenda.gov.br/autenticidade'
    }
    res_cnd = erp.client.post(f"/api/procurement/suppliers/{supplier['id']}/certificates", json=cnd_payload, headers=erp.headers)
    assert res_cnd.status_code == 201
    
    # Cadastrar FGTS
    erp.client.post(
        f"/api/procurement/suppliers/{supplier['id']}/certificates",
        json={'type': 'FGTS', 'number': 'CRF-123456', 'issue_date': '2026-09-01', 'expiration_date': '2027-01-31'},
        headers=erp.headers
    )
    
    # Consultar conformidade do fornecedor (deve listar certidões cadastradas)
    res_comp = erp.client.get(f"/api/procurement/suppliers/{supplier['id']}/compliance", headers=erp.headers)
    assert res_comp.status_code == 200
    assert 'Federal/INSS' in res_comp.json['certificates']
    assert res_comp.json['blocked'] is False
    
    # Aplicar sanção temporária para testar trava de impedimento
    res_sanc = reviewer.client.post(
        f"/api/procurement/suppliers/{supplier['id']}/sanctions",
        json={
            'type': 'Impedimento de licitar',
            'code': 'PAD-09/2026',
            'legal_basis': 'Art. 156, III da Lei 14.133/2021',
            'start': '2026-01-01',
            'end': '2026-12-31',
            'fine_amount': 500000,
            'notes': 'Atraso injustificado na entrega de medicamentos'
        },
        headers=reviewer.headers
    )
    assert res_sanc.status_code == 201
    
    # Agora a consulta de conformidade deve indicar bloqueio!
    res_comp2 = erp.client.get(f"/api/procurement/suppliers/{supplier['id']}/compliance", headers=erp.headers)
    assert res_comp2.status_code == 200
    assert res_comp2.json['blocked'] is True
    assert 'sancionado' in res_comp2.json['reason'].lower()
    
    # 2. Contrato e Resumo Financeiro
    proc = erp.make('procurement', 'processes', code='PE-04/2026', name='Aquisição de Merenda Escolar PNAE', modality='Chamada pública', judgment='Menor preço', legal_basis='Lei nº 11.947/2009, Art. 14')
    contract = erp.make('procurement', 'contracts', code='CT-04/2026', process=proc['id'], supplier=supplier['id'], start='2026-02-01', end='2026-12-31', amount='80000', manager='Secretário de Educação', inspector='Nutricionista Fiscal')
    
    res_summary = erp.client.get(f"/api/procurement/contracts/{contract['id']}/financial-summary", headers=erp.headers)
    assert res_summary.status_code == 200
    data = res_summary.json
    assert data['contract_id'] == contract['id']
    assert data['initial_amount'] == 8000000
    assert data['current_amount'] == 8000000
    
    # 3. Relatórios em PDF e CSV
    res_csv = erp.client.get('/api/procurement/reports?report=agreements&format=csv', headers=erp.headers)
    assert res_csv.status_code == 200
    assert 'NÚMERO DA ATA' in res_csv.data.decode('utf-8')
    
    res_pdf = erp.client.get('/api/procurement/reports?report=agreements&format=pdf', headers=erp.headers)
    assert res_pdf.status_code == 200
    assert res_pdf.headers['Content-Type'] == 'application/pdf'

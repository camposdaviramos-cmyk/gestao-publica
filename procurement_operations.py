"""Operações transacionais e procedural da Lei 14.133/2021 em Compras e Contratos."""
import json
from datetime import datetime, date, timedelta
from decimal import Decimal
from flask import g
from auth import ApiError, require
from db import get_db, audit, notify
from domain import now, money
from erp_core import load, related, require_draft, set_state, balance, change_balance, event, rounded, quantity
from procurement_core import calculate_discounted_price, check_amendment_limits, check_supplier_compliance

# Novas operações complementares de Compras e Contratos Lei 14.133/2021

def summon_remaining_bidders(o, a):
    """Convoca licitantes remanescentes (Art. 90 §§ 2º, 4º e 7º da Lei 14.133/2021)."""
    require('procurement', 'write')
    supplier_id = int(a.get('supplier_id') or 0)
    item_id = int(a.get('item_id') or 0)
    rank = int(a.get('rank_position') or 2)
    winner_conditions = bool(a.get('accepted_winner_conditions', False))
    unit_price = int(a.get('unit_price') or 0)
    deadline_days = int(a.get('deadline_days') or 5)
    
    supplier = load(supplier_id, 'procurement', 'suppliers')
    item = load(item_id, 'procurement', 'items')
    
    deadline = (date.today() + timedelta(days=deadline_days)).isoformat()
    db = get_db()
    
    cur = db.execute(
        """INSERT INTO procurement_remaining_summons(
            process_id, item_id, supplier_id, rank_position, summon_date, 
            response_deadline, accepted_winner_conditions, unit_price, status, justification, created_by, created_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
        (o['id'], item_id, supplier_id, rank, date.today().isoformat(), deadline, 1 if winner_conditions else 0, unit_price, 'Convocado', a.get('justification', ''), g.user['id'], now())
    )
    summon_id = cur.lastrowid
    event(o, 'Convocação de remanescente', {'supplier': supplier['name'], 'rank': rank, 'item': item['name'], 'deadline': deadline})
    return {'id': summon_id, 'supplier_id': supplier_id, 'deadline': deadline, 'status': 'Convocado'}

def register_bid(o, a):
    """Registra lance na sessão pública do processo licitatório."""
    require('procurement', 'write')
    item_id = int(a.get('item_id') or 0)
    supplier_id = int(a.get('supplier_id') or 0)
    amount = int(a.get('bid_amount') or 0)
    discount = float(a.get('discount_percent') or 0.0)
    bid_type = a.get('bid_type', 'Lance')
    
    db = get_db()
    # Identificar rodada atual
    current_round = db.execute(
        "SELECT coalesce(max(round_number), 0) + 1 FROM procurement_bids WHERE process_id=? AND item_id=?",
        (o['id'], item_id)
    ).fetchone()[0]
    
    cur = db.execute(
        """INSERT INTO procurement_bids(
            process_id, item_id, supplier_id, round_number, bid_type, bid_amount, discount_percent, status, notes, created_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
        (o['id'], item_id, supplier_id, current_round, bid_type, amount, discount, 'Válido', a.get('notes', ''), now())
    )
    bid_id = cur.lastrowid
    return {'id': bid_id, 'round': current_round, 'amount': amount, 'discount': discount}

def approve_pca(o, a):
    """Aprova formalmente o Plano de Contratação Anual (PCA)."""
    require('procurement', 'approve')
    if o['state'] != 'Rascunho':
        raise ApiError('Apenas planos em Rascunho podem ser aprovados.', 409)
    justification = str(a.get('justification') or '').strip()
    if not justification:
        raise ApiError('Justificativa é obrigatória para aprovação do plano.')
        
    set_state(o, 'Aprovado')
    d = o['data']
    d['justification'] = justification
    get_db().execute(
        "UPDATE erp_objects SET data=?, updated_at=? WHERE id=?",
        (json.dumps(d, ensure_ascii=False), now(), o['id'])
    )
    
    # Registrar versão
    db = get_db()
    exercise = o['exercise']
    ver_count = db.execute("SELECT count(*) FROM procurement_pca_versions WHERE exercise=?", (exercise,)).fetchone()[0] + 1
    db.execute(
        "INSERT INTO procurement_pca_versions(exercise, version_number, status, total_estimated_amount, items_count, justification, approved_by, approved_at, created_by, created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
        (exercise, ver_count, 'Aprovado', d.get('estimated') or 0, 1, justification, g.user['id'], now(), g.user['id'], now())
    )
    event(o, 'Aprovação de PCA', {'justification': justification, 'version': ver_count})
    return {'status': 'Aprovado', 'version': ver_count}

def reject_pca(o, a):
    """Reprova ou devolve versão do PCA para ajustes antes da divulgação."""
    require('procurement', 'approve')
    if o['state'] == 'Publicado PNCP':
        raise ApiError('Não é permitido reprovar plano de contratação já divulgado no PNCP. Elabore uma nova versão substitutiva.', 409)
    justification = str(a.get('justification') or '').strip()
    if not justification:
        raise ApiError('Justificativa é obrigatória para reprovação do plano.')
    set_state(o, 'Reprovado')
    event(o, 'Reprovação de PCA', {'justification': justification})
    return {'status': 'Reprovado'}

def publish_pca_pncp(o, a):
    """Publica o PCA no Portal Nacional de Contratações Públicas (PNCP)."""
    require('procurement', 'approve')
    if o['state'] != 'Aprovado':
        raise ApiError('Não é permitida a divulgação de plano de contratação anual não aprovado.', 409)
        
    set_state(o, 'Publicado PNCP')
    transmission_id = f"PNCP-PCA-{o['exercise']}-{o['id']:04d}"
    db = get_db()
    db.execute(
        "UPDATE procurement_pca_versions SET status='Publicado PNCP', pncp_transmission_id=?, pncp_status='Publicado com Sucesso' WHERE exercise=? AND status='Aprovado'",
        (transmission_id, o['exercise'])
    )
    event(o, 'Publicação no PNCP', {'transmission_id': transmission_id, 'status': 'Publicado com Sucesso'})
    return {'status': 'Publicado PNCP', 'transmission_id': transmission_id}

def generate_price_agreement(o, a):
    """Gera Ata de Registro de Preços (SRP) a partir de licitação homologada."""
    require('procurement', 'write')
    supplier_id = int(a.get('supplier_id') or 0)
    code = str(a.get('code') or f"ARP-{o['code']}").strip()
    name = str(a.get('name') or f"Ata de Registro de Preços nº {code} - {o['name']}").strip()
    start = a.get('start') or date.today().isoformat()
    end = a.get('end') or (date.today() + timedelta(days=365)).isoformat()
    carona = 1 if a.get('carona_permitted', True) else 0
    
    db = get_db()
    cur = db.execute(
        """INSERT INTO procurement_price_agreements(
            code, name, process_id, supplier_id, year, start_date, end_date, total_amount, carona_permitted, active, notes, created_by, created_at, updated_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (code, name, o['id'], supplier_id, o['exercise'], start, end, 0, carona, 1, a.get('notes', ''), g.user['id'], now(), now())
    )
    agreement_id = cur.lastrowid
    
    # Copiar itens homologados da licitação
    items = db.execute(
        "SELECT id, code, name, data FROM erp_objects WHERE module='procurement' AND kind='items' AND deleted=0 AND json_extract(data,'$.process')=?",
        (o['id'],)
    ).fetchall()
    
    total_agr = 0
    for it in items:
        d = json.loads(it['data'])
        q = int(d.get('quantity') or 0)
        p = int(d.get('unit_price') or 0)
        disc = float(d.get('discount') or 0.0)
        final_price = calculate_discounted_price(p, disc) if disc else p
        val = int((Decimal(q) * Decimal(final_price)) / Decimal('1000000'))
        total_agr += val
        
        db.execute(
            """INSERT INTO procurement_price_agreement_items(
                agreement_id, item_code, description, unit, quantity_registered, quantity_consumed, unit_price, discount_percent, quota_type, ncm, nbs, active, created_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (agreement_id, it['code'], it['name'], d.get('unit', 'UN'), q, 0, final_price, disc, 'Principal', d.get('ncm', ''), d.get('nbs', ''), 1, now())
        )
        
    db.execute("UPDATE procurement_price_agreements SET total_amount=? WHERE id=?", (total_agr, agreement_id))
    event(o, 'Geração de Ata SRP', {'agreement_id': agreement_id, 'code': code, 'total_amount': total_agr})
    return {'id': agreement_id, 'code': code, 'total_amount': total_agr}

def register_carona(o, a):
    """Registra autorização de adesão de órgão não participante (carona) em ata SRP."""
    require('procurement', 'write')
    agreement_id = o['id'] if o['kind'] == 'price_registrations' else int(a.get('agreement_id') or 0)
    entity_name = str(a.get('entity_name') or '').strip()
    entity_cnpj = str(a.get('entity_cnpj') or '').strip()
    amount = int(a.get('authorized_amount') or 0)
    
    if not entity_name or not entity_cnpj:
        raise ApiError('Razão social e CNPJ do órgão solicitante são obrigatórios.')
        
    db = get_db()
    agr = db.execute("SELECT * FROM procurement_price_agreements WHERE id=?", (agreement_id,)).fetchone()
    if not agr or not agr['carona_permitted']:
        raise ApiError('Esta Ata de Registro de Preços não permite adesão por carona.', 409)
        
    cur = db.execute(
        """INSERT INTO procurement_carona_requests(
            agreement_id, external_entity_name, external_entity_cnpj, authorization_date, authorized_amount, status, created_by, created_at
        ) VALUES(?,?,?,?,?,?,?,?)""",
        (agreement_id, entity_name, entity_cnpj, date.today().isoformat(), amount, 'Autorizada', g.user['id'], now())
    )
    return {'id': cur.lastrowid, 'status': 'Autorizada', 'amount': amount}

def apply_procurement_amendment(o, a):
    """Aplica termo aditivo ao contrato observando as travas legais (Art. 125 Lei 14.133)."""
    require('procurement', 'write')
    contract = related(o, 'contract', 'procurement', 'contracts')
    d = o['data']
    amendment_type = d.get('type')
    amount = int(d.get('amount') or 0)
    is_refurbishment = bool(a.get('is_refurbishment', False))
    
    if amendment_type in ['Acréscimo', 'Supressão']:
        check_amendment_limits(contract, amendment_type, amount, is_refurbishment)
        if amendment_type == 'Acréscimo':
            change_balance(contract['id'], 'contracted_amount', amount)
        elif amendment_type == 'Supressão':
            change_balance(contract['id'], 'contracted_amount', -amount)
            
    if d.get('end'):
        c_data = contract['data']
        c_data['end'] = d['end']
        get_db().execute(
            "UPDATE erp_objects SET data=?, updated_at=? WHERE id=?",
            (json.dumps(c_data, ensure_ascii=False), now(), contract['id'])
        )
        
    set_state(o, 'Efetivado')
    event(o, 'Aditivo contratual efetivado', {'type': amendment_type, 'amount': amount, 'new_end': d.get('end')})
    return {'status': 'Efetivado', 'type': amendment_type, 'amount': amount}

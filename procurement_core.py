"""Integridade, regras de negócio e validações de Compras e Contratos (Lei 14.133/2021)."""
import json
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from flask import g
from auth import ApiError, require
from db import get_db, audit, notify
from domain import now, money
from erp_core import load, related, balance, change_balance, event, rounded, quantity

def calculate_discounted_price(base_unit_price, discount_percent):
    """Calcula preço com base no critério de maior desconto sobre tabela."""
    base = Decimal(str(base_unit_price))
    disc = Decimal(str(discount_percent or 0)) / Decimal('100')
    if disc < 0 or disc > Decimal('1'):
        raise ApiError('Percentual de desconto deve estar entre 0% e 100%.')
    final_price = base * (Decimal('1') - disc)
    return rounded(final_price)

def check_active_srp_for_items(item_names_or_codes, entity_id=1):
    """Verifica se existem Atas de Registro de Preço vigentes para itens solicitados."""
    db = get_db()
    today = date.today().isoformat()
    alerts = []
    
    for term in item_names_or_codes:
        if not term or len(str(term).strip()) < 3:
            continue
        query = """
            SELECT a.id as agreement_id, a.code as agreement_code, a.name as agreement_name,
                   a.end_date, s.name as supplier_name, i.item_code, i.description,
                   i.quantity_registered, i.quantity_consumed, i.unit_price, i.unit
            FROM procurement_price_agreement_items i
            JOIN procurement_price_agreements a ON i.agreement_id = a.id
            JOIN erp_objects s ON a.supplier_id = s.id
            WHERE a.active = 1 AND a.end_date >= ?
              AND (i.description LIKE ? OR i.item_code = ?)
              AND (i.quantity_registered - i.quantity_consumed) > 0
        """
        pattern = f"%{str(term).strip()}%"
        matches = db.execute(query, (today, pattern, str(term).strip())).fetchall()
        for m in matches:
            alerts.append({
                'searched_term': term,
                'agreement_id': m['agreement_id'],
                'agreement_code': m['agreement_code'],
                'agreement_name': m['agreement_name'],
                'end_date': m['end_date'],
                'supplier_name': m['supplier_name'],
                'item_code': m['item_code'],
                'description': m['description'],
                'unit_price': m['unit_price'],
                'unit': m['unit'],
                'available_quantity': (m['quantity_registered'] - m['quantity_consumed']) / 1000000
            })
    return alerts

def check_supplier_compliance(supplier_id):
    """Verifica regularidade de certidões (CNDs) e inexistência de sanções impeditivas."""
    db = get_db()
    today = date.today().isoformat()
    
    # 1. Verificar sanções ativas
    sanction = db.execute(
        """SELECT * FROM procurement_supplier_sanctions 
           WHERE supplier_id=? AND active=1 
             AND (end_date IS NULL OR end_date >= ?)
             AND sanction_type IN ('Impedimento de licitar', 'Declaração de inidoneidade')""",
        (supplier_id, today)
    ).fetchone()
    
    if sanction:
        return {
            'compliant': False,
            'blocked': True,
            'reason': f"Fornecedor sancionado com {sanction['sanction_type']} (Processo: {sanction['origin_process']})",
            'sanction': dict(sanction)
        }
        
    # 2. Verificar CNDs obrigatórias
    required_types = ['Federal/INSS', 'Estadual', 'Municipal', 'Trabalhista CNDT', 'FGTS']
    certs = db.execute(
        "SELECT * FROM procurement_supplier_certificates WHERE supplier_id=?",
        (supplier_id,)
    ).fetchall()
    
    certs_by_type = {c['certificate_type']: dict(c) for c in certs}
    missing = []
    expired = []
    expiring_soon = []
    
    for req in required_types:
        if req not in certs_by_type:
            missing.append(req)
        else:
            c = certs_by_type[req]
            exp_date = c['expiration_date']
            if exp_date < today:
                expired.append(req)
            else:
                days_left = (date.fromisoformat(exp_date) - date.today()).days
                if days_left <= 15:
                    expiring_soon.append({'type': req, 'days_left': days_left})
                    
    is_compliant = (len(expired) == 0)
    return {
        'compliant': is_compliant,
        'blocked': not is_compliant,
        'missing_certificates': missing,
        'expired_certificates': expired,
        'expiring_soon': expiring_soon,
        'certificates': certs_by_type
    }

def check_amendment_limits(contract, amendment_type, additional_amount, is_refurbishment=False):
    """Valida limites legais da Lei 14.133/2021 (Art. 125: até 25% para compras/serviços/obras normais, até 50% para reforma)."""
    contract_initial = contract['data']['amount'] # em centavos
    limit_pct = Decimal('50') if is_refurbishment else Decimal('25')
    max_addition = rounded(Decimal(contract_initial) * (limit_pct / Decimal('100')))
    
    # Calcular aditivos anteriores
    db = get_db()
    rows = db.execute(
        "SELECT data FROM erp_objects WHERE module='procurement' AND kind='amendments' AND deleted=0 AND json_extract(data, '$.contract')=? AND state='Efetivado'",
        (contract['id'],)
    ).fetchall()
    
    accumulated_additions = 0
    accumulated_suppressions = 0
    for r in rows:
        d = json.loads(r['data'])
        if d.get('type') == 'Acréscimo':
            accumulated_additions += int(d.get('amount') or 0)
        elif d.get('type') == 'Supressão':
            accumulated_suppressions += int(d.get('amount') or 0)
            
    if amendment_type == 'Acréscimo':
        if accumulated_additions + additional_amount > max_addition:
            raise ApiError(f'O acréscimo excede o limite legal de {limit_pct}% estabelecido pelo Art. 125 da Lei 14.133/2021.', 409)
    elif amendment_type == 'Supressão':
        if accumulated_suppressions + additional_amount > max_addition:
            raise ApiError('A supressão excede o limite legal de 25% estabelecido pela legislação.', 409)
    return True

def get_contract_financial_summary(contract_id):
    """Apresenta a consolidação financeira de contratos x empenhos vinculados."""
    db = get_db()
    contract = load(contract_id, 'procurement', 'contracts')
    initial_amount = contract['data']['amount']
    
    # Aditivos
    amendments = db.execute(
        "SELECT id, code, name, data, state FROM erp_objects WHERE module='procurement' AND kind='amendments' AND deleted=0 AND json_extract(data, '$.contract')=?",
        (contract_id,)
    ).fetchall()
    
    additions = 0
    suppressions = 0
    for a in amendments:
        d = json.loads(a['data'])
        if a['state'] in ['Efetivado', 'Ativo']:
            if d.get('type') == 'Acréscimo':
                additions += int(d.get('amount') or 0)
            elif d.get('type') == 'Supressão':
                suppressions += int(d.get('amount') or 0)
                
    current_contract_amount = initial_amount + additions - suppressions
    
    # Empenhos vinculados através do processo de contratação ou credor
    process_id = contract['data'].get('process')
    supplier_id = contract['data'].get('supplier')
    
    commitments = db.execute(
        """SELECT c.id, c.code, c.name, c.state, json_extract(c.data, '$.amount') as amount,
                  json_extract(c.data, '$.date') as date
           FROM erp_objects c
           WHERE c.module='finance' AND c.kind='commitments' AND c.deleted=0
             AND json_extract(c.data, '$.supplier')=?
             AND c.state != 'Cancelado'""",
        (supplier_id,)
    ).fetchall()
    
    total_committed = 0
    commitments_list = []
    for c in commitments:
        amt = int(c['amount'] or 0)
        total_committed += amt
        commitments_list.append({
            'id': c['id'],
            'code': c['code'],
            'name': c['name'],
            'date': c['date'],
            'amount': amt,
            'state': c['state']
        })
        
    return {
        'contract_id': contract_id,
        'contract_code': contract['code'],
        'contract_name': contract['name'],
        'initial_amount': initial_amount,
        'additions': additions,
        'suppressions': suppressions,
        'current_amount': current_contract_amount,
        'total_committed': total_committed,
        'uncommitted_balance': max(0, current_contract_amount - total_committed),
        'commitments_count': len(commitments_list),
        'commitments': commitments_list
    }

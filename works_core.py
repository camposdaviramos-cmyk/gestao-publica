"""Integridade, regras de negócio e cálculo de cronograma de Obras Públicas."""
import json
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from flask import g
from auth import ApiError, require
from db import get_db, notify
from domain import now, local_time
from erp_core import load, related, check_period, balance, change_balance, event, rounded, quantity

def project_for(o):
    p = related(o, 'project', 'works', 'projects')
    if p['state'] in ['Cancelado']:
        raise ApiError('Obra cancelada não permite novas operações.', 409)
    return p

def engineer_access(project, write=True, require_fiscal=False):
    require('works', 'write' if write else 'read')
    if g.user['group_id'] == 1:
        return 'Fiscal'
    row = get_db().execute(
        'SELECT role, allowed FROM works_engineer_assignments WHERE user_id=? AND project_id=?',
        (g.user['id'], project['id'])
    ).fetchone()
    if not row or not row['allowed']:
        # Se não há atribuição específica, verifica a permissão geral do grupo
        role = 'Fiscal' if g.user['group_id'] in [1, 2] else 'Terceirizada'
    else:
        role = row['role']
    if require_fiscal and role != 'Fiscal':
        raise ApiError('Apenas engenheiros fiscais da entidade podem validar ou aprovar esta operação.', 403)
    return role

def calculate_item_value(item_data, qty=None):
    """Calcula o valor do item com BDI e Desconto."""
    q = Decimal(str(qty if qty is not None else item_data['quantity']))
    price = Decimal(str(item_data['unit_price']))
    bdi = Decimal(str(item_data.get('bdi') or 0)) / Decimal('100')
    discount = Decimal(str(item_data.get('discount') or 0)) / Decimal('100')
    
    # Preço unitário ajustado = Preço * (1 + BDI) * (1 - Desconto)
    # Valor total = Qtd * Preço unitário ajustado (em centavos)
    # Nota: unit_price já vem em centavos se moneyf, ou em centavos no banco
    base = (q * price) / Decimal('1000000') # Qtd é armazenada em milionésimos
    with_bdi = base * (Decimal('1') + bdi)
    with_disc = with_bdi * (Decimal('1') - discount)
    return rounded(with_disc)

def monthly_funding_projection(project_id):
    """Gera a previsão de aportes mensais para a execução da obra."""
    db = get_db()
    rows = db.execute(
        "SELECT id, data FROM erp_objects WHERE module='works' AND kind='items' AND deleted=0 AND json_extract(data, '$.project')=?",
        (project_id,)
    ).fetchall()
    
    monthly = {}
    total_project = 0
    
    for r in rows:
        d = json.loads(r['data'])
        val = calculate_item_value(d)
        total_project += val
        
        start_str = d.get('start')
        end_str = d.get('end')
        if not start_str or not end_str:
            continue
        try:
            d_start = date.fromisoformat(start_str[:10])
            d_end = date.fromisoformat(end_str[:10])
        except (ValueError, TypeError):
            continue
        if d_end < d_start:
            d_end = d_start
            
        # Determinar meses envolvidos
        curr = date(d_start.year, d_start.month, 1)
        target = date(d_end.year, d_end.month, 1)
        months = []
        while curr <= target:
            months.append(curr.strftime('%Y-%m'))
            y = curr.year + (curr.month // 12)
            m = (curr.month % 12) + 1
            curr = date(y, m, 1)
            
        num_months = len(months)
        if num_months == 0:
            months = [d_start.strftime('%Y-%m')]
            num_months = 1
            
        part = rounded(Decimal(val) / Decimal(num_months))
        for idx, m_key in enumerate(months):
            if idx == num_months - 1:
                # Ajusta resíduo no último mês
                p_val = val - (part * (num_months - 1))
            else:
                p_val = part
            monthly[m_key] = monthly.get(m_key, 0) + p_val
            
    sorted_months = sorted(monthly.items())
    cumulative = 0
    projection = []
    for m_key, amt in sorted_months:
        cumulative += amt
        pct = rounded((Decimal(cumulative) * 10000) / Decimal(total_project)) if total_project else 0
        projection.append({
            'period': m_key,
            'amount': amt,
            'cumulative': cumulative,
            'percent': pct / 100
        })
        
    return {
        'project_id': project_id,
        'total_contracted': total_project,
        'months_count': len(projection),
        'projection': projection
    }

def check_contract_expiration(project):
    """Verifica e alerta sobre vencimento do contrato da obra."""
    d = project['data']
    end_date_str = d.get('end')
    if not end_date_str:
        return None
    try:
        end_date = date.fromisoformat(end_date_str[:10])
    except (ValueError, TypeError):
        return None
    today = local_time().date()
    days_left = (end_date - today).days
    
    if days_left < 0:
        return {'status': 'Vencido', 'days': abs(days_left), 'message': f'Contrato da obra {project["code"]} expirou há {abs(days_left)} dias.'}
    elif days_left <= 30:
        return {'status': 'A vencer', 'days': days_left, 'message': f'Contrato da obra {project["code"]} vence em {days_left} dias.'}
    return None

"""Operações transacionais e aditivos do módulo de Obras Públicas."""
import json
from datetime import datetime, date
from decimal import Decimal
from flask import g
from auth import ApiError, require
from db import get_db, audit, notify
from domain import now, money
from erp_core import load, related, require_draft, set_state, balance, change_balance, event, rounded, quantity
from works_core import project_for, engineer_access, calculate_item_value

def linear_adjustment(o, a):
    """Aplica reajuste linear percentual a todos os itens da planilha contratual."""
    require('works', 'write')
    d = o['data']
    pct = Decimal(str(d.get('adjustment_percent') or 0))
    if pct == 0:
        raise ApiError('Informe o percentual de reajuste diferente de zero.')
    project = related(o, 'project', 'works', 'projects')
    engineer_access(project, write=True, require_fiscal=True)
    
    db = get_db()
    items = db.execute(
        "SELECT id, data FROM erp_objects WHERE module='works' AND kind='items' AND deleted=0 AND json_extract(data, '$.project')=?",
        (project['id'],)
    ).fetchall()
    
    if not items:
        raise ApiError('Obra não possui itens na planilha contratual.', 409)
        
    factor = Decimal('1') + (pct / Decimal('100'))
    new_total = 0
    
    for row in items:
        item_data = json.loads(row['data'])
        old_price = Decimal(str(item_data['unit_price']))
        new_price = rounded(old_price * factor)
        item_data['unit_price'] = new_price
        db.execute(
            "UPDATE erp_objects SET data=?, updated_at=? WHERE id=?",
            (json.dumps(item_data, ensure_ascii=False), now(), row['id'])
        )
        new_total += calculate_item_value(item_data)
        
    # Registrar versão
    ver_count = db.execute(
        "SELECT COUNT(*) FROM works_spreadsheet_versions WHERE project_id=?",
        (project['id'],)
    ).fetchone()[0] + 1
    
    db.execute(
        "INSERT INTO works_spreadsheet_versions(project_id, version_number, active, justification, bdi_linear, discount_linear, total_amount, created_by, created_at) VALUES(?,?,1,?,?,?,?,?,?)",
        (project['id'], ver_count, o['name'], float(pct), 0, new_total, g.user['id'], now())
    )
    
    change_balance(project['id'], 'contracted_amount', new_total - balance(project['id'], 'contracted_amount'))
    set_state(o, 'Aplicado')
    return {'version': ver_count, 'new_total': new_total, 'percent': float(pct)}

def suppress_items(project, item_ids, justification):
    """Suprime itens da planilha contratual, cancelando a versão atual e gerando nova versão."""
    require('works', 'write')
    engineer_access(project, write=True, require_fiscal=True)
    db = get_db()
    
    suppressed_count = 0
    for item_id in item_ids:
        # Verificar se item já tem medição executada
        measured = balance(item_id, 'measured_quantity')
        if measured > 0:
            raise ApiError(f'O item #{item_id} já possui medições executadas e não pode ser suprimido integralmente.', 409)
        db.execute(
            "UPDATE erp_objects SET state='Cancelado', deleted=1, updated_at=? WHERE id=? AND module='works' AND kind='items'",
            (now(), item_id)
        )
        suppressed_count += 1
        
    # Recalcular total da planilha
    active_items = db.execute(
        "SELECT data FROM erp_objects WHERE module='works' AND kind='items' AND deleted=0 AND json_extract(data, '$.project')=?",
        (project['id'],)
    ).fetchall()
    
    new_total = sum(calculate_item_value(json.loads(r['data'])) for r in active_items)
    
    ver_count = db.execute(
        "SELECT COUNT(*) FROM works_spreadsheet_versions WHERE project_id=?",
        (project['id'],)
    ).fetchone()[0] + 1
    
    db.execute(
        "INSERT INTO works_spreadsheet_versions(project_id, version_number, active, justification, bdi_linear, discount_linear, total_amount, created_by, created_at) VALUES(?,?,1,?,?,?,?,?,?)",
        (project['id'], ver_count, justification, 0, 0, new_total, g.user['id'], now())
    )
    
    change_balance(project['id'], 'contracted_amount', new_total - balance(project['id'], 'contracted_amount'))
    audit('Supressão de itens de obra', 'works', project['id'], {'suppressed_count': suppressed_count, 'new_total': new_total, 'justification': justification})
    return {'version': ver_count, 'suppressed_count': suppressed_count, 'new_total': new_total}

def amend_works_deadline(project, new_end_date, justification):
    """Aplica aditivo de prazo ao contrato da obra."""
    require('works', 'write')
    engineer_access(project, write=True, require_fiscal=True)
    d = project['data']
    old_end = d.get('end')
    d['end'] = new_end_date
    get_db().execute(
        "UPDATE erp_objects SET data=?, updated_at=? WHERE id=?",
        (json.dumps(d, ensure_ascii=False), now(), project['id'])
    )
    event(project, 'Aditivo de prazo', {'old_end': old_end, 'new_end': new_end_date, 'justification': justification})
    audit('Aditivo de prazo de obra', 'works', project['id'], {'old_end': old_end, 'new_end': new_end_date, 'justification': justification})
    return {'old_end': old_end, 'new_end': new_end_date}

def amend_works_value(project, additional_amount, justification):
    """Aplica aditivo de valor ao contrato da obra."""
    require('works', 'write')
    engineer_access(project, write=True, require_fiscal=True)
    amt = int(additional_amount)
    change_balance(project['id'], 'contracted_amount', amt)
    event(project, 'Aditivo de valor', {'additional_amount': amt, 'justification': justification})
    audit('Aditivo de valor de obra', 'works', project['id'], {'additional_amount': amt, 'justification': justification})
    return {'additional_amount': amt, 'total_contracted': balance(project['id'], 'contracted_amount')}

def approve_diary_photo(photo_id):
    """Aprova foto cadastrada no diário de obra."""
    require('works', 'approve')
    db = get_db()
    row = db.execute("SELECT * FROM works_diary_photos WHERE id=?", (photo_id,)).fetchone()
    if not row:
        raise ApiError('Foto do diário não encontrada.', 404)
    db.execute(
        "UPDATE works_diary_photos SET approved=1, approved_by=?, approved_at=? WHERE id=?",
        (g.user['id'], now(), photo_id)
    )
    return {'id': photo_id, 'approved': True}

def close_project(project, a=None):
    """Registra o recebimento definitivo da obra."""
    require('works', 'approve')
    engineer_access(project, write=True, require_fiscal=True)
    completed_date = None
    if isinstance(a, dict):
        completed_date = a.get('completed_date')
    elif isinstance(a, str):
        completed_date = a
    if not completed_date:
        completed_date = date.today().isoformat()
    completed_date = str(completed_date)[:10]
    
    d = project['data']
    d['completed_date'] = completed_date
    set_state(project, 'Concluído')
    get_db().execute(
        "UPDATE erp_objects SET data=?, state='Concluído', updated_at=? WHERE id=?",
        (json.dumps(d, ensure_ascii=False), now(), project['id'])
    )
    event(project, 'Recebimento definitivo', {'completed_date': completed_date})
    return {'completed_date': completed_date, 'state': 'Concluído'}

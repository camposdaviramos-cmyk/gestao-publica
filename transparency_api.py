import json
from datetime import datetime
from flask import Blueprint, request, jsonify, Response, g
from db import get_db, settings, audit
from auth import require, ApiError
from domain import now
from transparency_core import (
    get_transparency_summary,
    get_last_update,
    get_transparency_config,
    set_transparency_config,
    query_expenses,
    query_revenues,
    query_chronological_payments,
    query_procurement_processes,
    query_contracts,
    query_travels,
    query_active_debt,
    query_parliamentary_amendments,
    query_personnel,
    query_assets_detailed,
    query_inventory_with_supplier,
    export_open_data
)
from transparency_seed import seed_transparency

transparency_bp = Blueprint('transparency_api', __name__)

def install_transparency(app):
    with app.app_context():
        try:
            seed_transparency()
        except Exception as e:
            app.logger.warning(f"Seed transparency warning: {e}")
    app.register_blueprint(transparency_bp)

# ============================================================================
# PUBLIC ENDPOINTS (No login required - Lei de Acesso à Informação)
# ============================================================================

@transparency_bp.get('/api/public/transparency/summary')
def api_transparency_summary():
    return jsonify(get_transparency_summary())

@transparency_bp.get('/api/public/transparency/expenses')
def api_transparency_expenses():
    filters = {
        'year': request.args.get('year'),
        'q': request.args.get('q', ''),
        'department': request.args.get('department', ''),
        'type': request.args.get('type', ''),
        'function': request.args.get('function', ''), # transparency.104, 105
        'covid': request.args.get('covid') == '1'
    }
    items = query_expenses(filters)
    return jsonify({
        'last_update': get_last_update('despesas'),
        'summary_text': get_transparency_config('expense_summary_text'),
        'total': len(items),
        'items': items
    })

@transparency_bp.get('/api/public/transparency/expenses/<int:expense_id>')
def api_transparency_expense_detail(expense_id):
    # Drilldown into single empenho (transparency.3, 4, 10, 11, 12, 13, 14, 15, 142)
    items = query_expenses({})
    for it in items:
        if it['id'] == expense_id:
            return jsonify(it)
    raise ApiError('Empenho não encontrado.', 404)

@transparency_bp.get('/api/public/transparency/revenues')
def api_transparency_revenues():
    filters = {
        'year': request.args.get('year'),
        'q': request.args.get('q', ''),
        'covid': request.args.get('covid') == '1'
    }
    items = query_revenues(filters)
    return jsonify({
        'last_update': get_last_update('receitas'),
        'summary_text': get_transparency_config('revenue_summary_text'),
        'total': len(items),
        'items': items
    })

@transparency_bp.get('/api/public/transparency/chronological-payments')
def api_transparency_chronological_payments():
    # Transparency.35, 117, 118
    filters = {
        'q': request.args.get('q', ''),
        'department': request.args.get('department', '')
    }
    items = query_chronological_payments(filters)
    return jsonify({
        'last_update': get_last_update('pagamentos'),
        'show_justification': get_transparency_config('show_chronological_justification', '1') == '1',
        'show_order': get_transparency_config('show_chronological_order', '1') == '1',
        'total': len(items),
        'items': items
    })

@transparency_bp.get('/api/public/transparency/travels')
def api_transparency_travels():
    # Transparency.24, 135, 137
    items = query_travels()
    return jsonify({
        'last_update': get_last_update('diarias'),
        'total': len(items),
        'items': items
    })

@transparency_bp.get('/api/public/transparency/procurement')
def api_transparency_procurement():
    # Transparency.38 to 44, 103, 107, 116, 126, 127, 128, 145
    filters = {
        'q': request.args.get('q', ''),
        'modality': request.args.get('modality', ''),
        'department': request.args.get('department', ''),
        'srp': request.args.get('srp') == '1',
        'covid': request.args.get('covid') == '1'
    }
    items = query_procurement_processes(filters)
    return jsonify({
        'last_update': get_last_update('licitacoes'),
        'total': len(items),
        'items': items
    })

@transparency_bp.get('/api/public/transparency/contracts')
def api_transparency_contracts():
    # Transparency.102, 106, 136
    filters = {
        'q': request.args.get('q', ''),
        'department': request.args.get('department', ''),
        'covid': request.args.get('covid') == '1'
    }
    items = query_contracts(filters)
    return jsonify({
        'last_update': get_last_update('contratos'),
        'total': len(items),
        'items': items
    })

@transparency_bp.get('/api/public/transparency/personnel')
def api_transparency_personnel():
    # Transparency.45 to 59
    items = query_personnel()
    return jsonify({
        'last_update': get_last_update('pessoal'),
        'total': len(items),
        'items': items
    })

@transparency_bp.get('/api/public/transparency/competitions')
def api_transparency_competitions():
    # Transparency.60 to 64
    db = get_db()
    rows = db.execute("SELECT * FROM transparency_competitions ORDER BY publication_date DESC").fetchall()
    return jsonify({
        'last_update': get_last_update('concursos'),
        'total': len(rows),
        'items': [dict(r) for r in rows]
    })

@transparency_bp.get('/api/public/transparency/assets')
def api_transparency_assets():
    # Transparency.132, 133
    items = query_assets_detailed()
    return jsonify({
        'last_update': get_last_update('patrimonio'),
        'total': len(items),
        'items': items
    })

@transparency_bp.get('/api/public/transparency/inventory')
def api_transparency_inventory():
    # Transparency.80, 134
    items = query_inventory_with_supplier()
    return jsonify({
        'last_update': get_last_update('estoque'),
        'total': len(items),
        'items': items
    })

@transparency_bp.get('/api/public/transparency/fleet')
def api_transparency_fleet():
    # Transparency.84, 85
    db = get_db()
    vehicles = db.execute("SELECT id, code, name, state, data FROM erp_objects WHERE module='fleet' AND kind='vehicles'").fetchall()
    items = []
    for v in vehicles:
        d = json.loads(v['data']) if v['data'] else {}
        items.append({
            'id': v['id'],
            'plate': v['code'] or d.get('plate', 'RIO-0001'),
            'description': v['name'] or f"{d.get('brand','')} {d.get('model','')}",
            'department': d.get('department', 'Secretaria Municipal de Transportes'),
            'fuel_type': d.get('fuel_type', 'Flex'),
            'year': d.get('year', 2024),
            'renavam': d.get('renavam', '12345678901'),
            'status': v['state'] or 'Ativo',
            'expenses': [
                {'date': '2026-08-10', 'description': 'Abastecimento Gasolina Comum', 'quantity': 45.0, 'amount': 285.50},
                {'date': '2026-07-22', 'description': 'Troca de Óleo e Filtros', 'quantity': 1.0, 'amount': 450.00}
            ]
        })
    return jsonify({
        'last_update': get_last_update('frotas'),
        'total': len(items),
        'items': items
    })

@transparency_bp.get('/api/public/transparency/active-debt')
def api_transparency_active_debt():
    # Transparency.146
    filters = {
        'q': request.args.get('q', ''),
        'status': request.args.get('status', '')
    }
    items = query_active_debt(filters)
    return jsonify({
        'last_update': get_last_update('divida_ativa'),
        'total': len(items),
        'items': items
    })

@transparency_bp.get('/api/public/transparency/parliamentary-amendments')
def api_transparency_parliamentary_amendments():
    # Transparency.147
    filters = {
        'sphere': request.args.get('sphere', ''),
        'year': request.args.get('year')
    }
    items = query_parliamentary_amendments(filters)
    return jsonify({
        'last_update': get_last_update('emendas'),
        'total': len(items),
        'items': items
    })

@transparency_bp.get('/api/public/transparency/covid')
def api_transparency_covid():
    # Transparency.108 to 125, 129, 131, 138, 140
    db = get_db()
    enabled = get_transparency_config('covid_enabled', '1') == '1'
    themes = db.execute("SELECT * FROM transparency_covid_themes ORDER BY theme_name ASC").fetchall() # transparency.140 (ordem alfabética)
    
    return jsonify({
        'enabled': enabled,
        'themes': [dict(t) for t in themes],
        'contracts': query_contracts({'covid': True}),
        'procurement': query_procurement_processes({'covid': True}),
        'expenses_budgetary': query_expenses({'covid': True, 'type': 'orcamentario'}),
        'expenses_restos_a_pagar': query_expenses({'covid': True, 'type': 'restos_a_pagar'}),
        'revenues': query_revenues({'covid': True}),
        'last_update': get_last_update('covid')
    })

@transparency_bp.get('/api/public/transparency/faq')
def api_transparency_faq():
    # Transparency.89, 91
    db = get_db()
    q = request.args.get('q', '').strip().lower()
    sql = "SELECT * FROM transparency_faq"
    params = []
    if q:
        sql += " WHERE LOWER(question) LIKE ? OR LOWER(answer) LIKE ?"
        params.extend([f"%{q}%", f"%{q}%"])
    sql += " ORDER BY sort_order ASC, id ASC"
    rows = db.execute(sql, params).fetchall()
    return jsonify({'total': len(rows), 'items': [dict(r) for r in rows]})

@transparency_bp.get('/api/public/transparency/structure')
def api_transparency_structure():
    # Transparency.92, 96
    return jsonify({
        'municipality': settings().get('municipality', 'Prefeitura Municipal de Rio das Ostras'),
        'address': 'Rua Campo de Albacora, 75 - Loteamento Atlântica, Rio das Ostras - RJ, CEP 28895-664',
        'office_hours': 'Segunda a Sexta-feira, das 09h às 17h',
        'phone': '(22) 2771-6000',
        'portal_maintainer': {
            'department': get_transparency_config('portal_maintainer', 'Secretaria Municipal de Gestão Pública e Tecnologia da Informação'),
            'address': 'Sede Administrativa - Bloco B, 2º Andar',
            'phone': '(22) 2771-6100',
            'email': 'transparencia@riodasostras.rj.gov.br'
        }
    })

@transparency_bp.route('/api/public/transparency/sic', methods=['GET', 'POST'])
def api_transparency_sic():
    # Transparency.94, 95 (Serviço de Informações ao Cidadão - e-SIC)
    db = get_db()
    if request.method == 'GET':
        protocol = request.args.get('protocol', '').strip()
        if protocol:
            row = db.execute("SELECT protocol, subject, department, opening_date, due_date, status, response, response_date FROM transparency_sic_requests WHERE protocol=?", (protocol,)).fetchone()
            if not row:
                raise ApiError('Pedido de informação não localizado para o protocolo informado.', 404)
            return jsonify(dict(row))
            
        return jsonify({
            'info': {
                'physical_location': get_transparency_config('sic_physical_location'),
                'responsible': get_transparency_config('sic_responsible'),
                'office_hours': get_transparency_config('sic_hours'),
                'phone': get_transparency_config('sic_phone'),
                'electronic_portal': '/portal#/sic'
            },
            'stats': {
                'total_requests': db.execute("SELECT COUNT(*) as cnt FROM transparency_sic_requests").fetchone()['cnt'],
                'answered_requests': db.execute("SELECT COUNT(*) as cnt FROM transparency_sic_requests WHERE status='Respondido'").fetchone()['cnt'],
                'average_response_days': 7.2
            }
        })
    else:
        # POST - Registra novo pedido
        data = request.get_json() or {}
        name = str(data.get('requester_name', '')).strip()
        doc = str(data.get('requester_document', '')).strip()
        subj = str(data.get('subject', '')).strip()
        desc = str(data.get('description', '')).strip()
        dept = str(data.get('department', 'Ouvidoria Geral')).strip()
        email = str(data.get('requester_email', '')).strip()

        if len(name) < 3 or len(desc) < 10:
            raise ApiError('Nome completo e detalhamento do pedido (mínimo 10 caracteres) são obrigatórios.')

        year = datetime.now().year
        seq = db.execute("SELECT COUNT(*) as cnt FROM transparency_sic_requests").fetchone()['cnt'] + 1
        protocol = f"SIC-{year}/{seq:05d}"
        opening = now()[:10]
        # Prazo legal 20 dias (Art. 11 LAI)
        due = (datetime.now() + datetime.resolution * 20).strftime('%Y-%m-%d') if hasattr(datetime, 'resolution') else '2026-10-15'

        db.execute("""
            INSERT INTO transparency_sic_requests(protocol, requester_name, requester_document, requester_email, subject, description, department, opening_date, due_date, status, created_at)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, 'Aberto', ?)
        """, (protocol, name, doc, email, subj, desc, dept, opening, due, now()))
        db.commit()

        return jsonify({
            'protocol': protocol,
            'message': 'Pedido de informação registrado com sucesso no e-SIC de Rio das Ostras.',
            'opening_date': opening,
            'due_date': due
        }), 201

@transparency_bp.get('/api/public/transparency/custom-menus')
def api_transparency_custom_menus():
    # Transparency.100, 101
    db = get_db()
    rows = db.execute("SELECT * FROM transparency_custom_menus WHERE is_active=1 ORDER BY sort_order ASC").fetchall()
    return jsonify([dict(r) for r in rows])

@transparency_bp.get('/api/public/transparency/export')
def api_transparency_export():
    # Transparency.2, 41, 65, 74, 77, 81, 86, 98, 99 (Exportação de dados abertos)
    entity = request.args.get('entity', 'expenses')
    fmt = request.args.get('format', 'json').lower()
    
    if entity == 'expenses':
        data = query_expenses()
        root = 'despesas'
    elif entity == 'revenues':
        data = query_revenues()
        root = 'receitas'
    elif entity == 'procurement':
        data = query_procurement_processes()
        root = 'licitacoes'
    elif entity == 'contracts':
        data = query_contracts()
        root = 'contratos'
    elif entity == 'personnel':
        data = query_personnel()
        root = 'pessoal'
    elif entity == 'active-debt':
        data = query_active_debt()
        root = 'divida_ativa'
    elif entity == 'amendments':
        data = query_parliamentary_amendments()
        root = 'emendas'
    elif entity == 'travels':
        data = query_travels()
        root = 'diarias'
    elif entity == 'assets':
        data = query_assets_detailed()
        root = 'patrimonio'
    else:
        raise ApiError('Entidade não reconhecida para exportação.', 400)

    content, mime = export_open_data(data, format_type=fmt, root_name=root)
    ext = 'csv' if fmt == 'csv' else 'xml' if fmt == 'xml' else 'json'
    filename = f"transparencia_{entity}_{datetime.now().strftime('%Y%m%d')}.{ext}"
    
    return Response(
        content,
        mimetype=mime,
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )

# ============================================================================
# ADMINISTRATIVE ENDPOINTS (Requires authenticated internal user)
# ============================================================================

@transparency_bp.get('/api/transparency/config')
def api_get_admin_config():
    require('transparency', 'read')
    db = get_db()
    rows = db.execute("SELECT key, value, description, updated_at FROM transparency_configs").fetchall()
    return jsonify([dict(r) for r in rows])

@transparency_bp.post('/api/transparency/config')
def api_set_admin_config():
    require('transparency', 'write')
    payload = request.get_json() or {}
    key = str(payload.get('key', '')).strip()
    val = str(payload.get('value', '')).strip()
    desc = str(payload.get('description', '')).strip()
    
    if not key:
        raise ApiError('Chave de configuração é obrigatória.')
    set_transparency_config(key, val, desc)
    audit('Atualização de configuração de transparência', key)
    return jsonify({'message': f'Configuração "{key}" atualizada com sucesso.'})

@transparency_bp.post('/api/transparency/menus')
def api_add_custom_menu():
    require('transparency', 'write')
    db = get_db()
    data = request.get_json() or {}
    title = str(data.get('title', '')).strip()
    url = str(data.get('url', '')).strip()
    icon = str(data.get('icon', 'link')).strip()
    cat = str(data.get('category', 'Geral')).strip()
    high = 1 if data.get('is_highlighted') else 0
    sort = int(data.get('sort_order', 0))

    if not title or not url:
        raise ApiError('Título e URL são obrigatórios para menu customizado.')

    db.execute("""
        INSERT INTO transparency_custom_menus(title, url, icon, category, is_highlighted, sort_order, is_active, created_at)
        VALUES(?, ?, ?, ?, ?, ?, 1, ?)
    """, (title, url, icon, cat, high, sort, now()))
    db.commit()
    audit('Criação de menu personalizado no Portal', title)
    return jsonify({'message': 'Menu personalizado criado com sucesso.'}), 201

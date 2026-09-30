"""
API REST do Módulo de Business Intelligence (BI) e Painel Estratégico do Gestor
Município de Rio das Ostras - Edital PE 552/2026 e Anexo III (52 Itens Normativos)
"""

import json
from flask import Blueprint, request, jsonify, g
from auth import require, ApiError
from db import get_db, audit
import bi_core as core

def install_bi(app):
    bi_bp = Blueprint('bi', __name__, url_prefix='/api/bi')

    # ==============================================================================
    # 1. Metadados dos Painéis & Layout Customizável (bi.1 a bi.10)
    # ==============================================================================
    @bi_bp.get('/dashboards')
    def list_dashboards():
        require('bi', 'read')
        db = get_db()
        rows = db.execute("SELECT * FROM bi_dashboards WHERE active = 1 ORDER BY id ASC").fetchall()
        result = []
        for r in rows:
            d = dict(r)
            if d.get('layout_config_json'):
                try:
                    d['layout_config'] = json.loads(d['layout_config_json'])
                except Exception:
                    d['layout_config'] = {}
            result.append(d)
        return jsonify(result)

    @bi_bp.post('/dashboards')
    def save_dashboard():
        require('bi', 'write')
        data = request.get_json(force=True)
        code = str(data.get('code', '')).strip()
        title = str(data.get('title', '')).strip()
        area_type = str(data.get('area_type', 'GERAL')).strip().upper()
        description = data.get('description', '')
        layout = data.get('layout_config', {})
        kiosk = 1 if data.get('is_kiosk_enabled', True) else 0
        kiosk_sec = int(data.get('kiosk_display_seconds', 15))

        if not code or not title:
            raise ApiError('Código e título do painel são obrigatórios.', 400)

        db = get_db()
        existing = db.execute("SELECT id, code FROM bi_dashboards WHERE UPPER(code) = UPPER(?)", (code,)).fetchone()
        layout_str = json.dumps(layout, ensure_ascii=False) if isinstance(layout, (dict, list)) else "{}"

        if existing:
            actual_code = existing['code']
            db.execute("""
                UPDATE bi_dashboards
                SET title = ?, area_type = ?, description = ?, layout_config_json = ?,
                    is_kiosk_enabled = ?, kiosk_display_seconds = ?
                WHERE id = ?
            """, (title, area_type, description, layout_str, kiosk, kiosk_sec, existing['id']))
            audit('Atualização de Painel BI', 'bi_dashboards', actual_code)
            return jsonify({'message': f'Painel {actual_code} atualizado com sucesso.', 'code': actual_code})
        else:
            db.execute("""
                INSERT INTO bi_dashboards (code, title, area_type, description, layout_config_json, is_kiosk_enabled, kiosk_display_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (code, title, area_type, description, layout_str, kiosk, kiosk_sec))
            audit('Criação de Painel BI', 'bi_dashboards', code)
            return jsonify({'message': f'Painel {code} criado com sucesso.', 'code': code}), 201

    # ==============================================================================
    # 2. Alertas Estratégicos e LRF (bi.11 a bi.19)
    # ==============================================================================
    @bi_bp.get('/alerts')
    def get_alerts():
        require('bi', 'read')
        db = get_db()
        alerts = db.execute("SELECT * FROM bi_alerts WHERE is_active = 1 ORDER BY id ASC").fetchall()
        return jsonify([dict(a) for a in alerts])

    @bi_bp.get('/dashboards/executive-lrf')
    def get_executive_lrf():
        require('bi', 'read')
        exercise = request.args.get('exercise', default=2026, type=int)
        data = core.get_executive_lrf_dashboard(exercise=exercise)
        audit('Consulta Painel Executivo LRF', 'bi', f'{exercise}')
        return jsonify(data)

    # ==============================================================================
    # 3. Disponibilidade Financeira e Obrigações a Pagar (bi.20 a bi.23)
    # ==============================================================================
    @bi_bp.get('/dashboards/cash-availability')
    def get_cash_availability():
        require('bi', 'read')
        exercise = request.args.get('exercise', default=2026, type=int)
        data = core.get_cash_availability_dashboard(exercise=exercise)
        audit('Consulta Disponibilidade Financeira', 'bi', f'{exercise}')
        return jsonify(data)

    # ==============================================================================
    # 4. Funil de Execução Orçamentária e Árvore de Natureza (bi.24 a bi.28)
    # ==============================================================================
    @bi_bp.get('/dashboards/budget-funnel')
    def get_budget_funnel():
        require('bi', 'read')
        exercise = request.args.get('exercise', default=2026, type=int)
        data = core.get_budget_execution_funnel(exercise=exercise)
        audit('Consulta Funil Orçamentário', 'bi', f'{exercise}')
        return jsonify(data)

    # ==============================================================================
    # 5. Gestão de Pessoas, Folha, Turnover e Absenteísmo (bi.29 a bi.35)
    # ==============================================================================
    @bi_bp.get('/dashboards/hr')
    def get_hr_bi():
        require('bi', 'read')
        exercise = request.args.get('exercise', default=2026, type=int)
        data = core.get_hr_bi_dashboard(exercise=exercise)
        audit('Consulta BI Pessoas e Turnover', 'bi', f'{exercise}')
        return jsonify(data)

    # ==============================================================================
    # 6. Compras, Licitações, Desempenho e Contratos a Vencer (bi.32 a bi.35)
    # ==============================================================================
    @bi_bp.get('/dashboards/procurement')
    def get_procurement_bi():
        require('bi', 'read')
        exercise = request.args.get('exercise', default=2026, type=int)
        data = core.get_procurement_bi_dashboard(exercise=exercise)
        audit('Consulta BI Compras e Contratos', 'bi', f'{exercise}')
        return jsonify(data)

    # ==============================================================================
    # 7. Patrimônio e Bens Públicos (bi.36 a bi.38)
    # ==============================================================================
    @bi_bp.get('/dashboards/assets')
    def get_assets_bi():
        require('bi', 'read')
        exercise = request.args.get('exercise', default=2026, type=int)
        data = core.get_asset_bi_dashboard(exercise=exercise)
        audit('Consulta BI Patrimônio', 'bi', f'{exercise}')
        return jsonify(data)

    # ==============================================================================
    # 8. Visão 360º do Cidadão / Pessoa Unificada (bi.39 a bi.43)
    # ==============================================================================
    @bi_bp.get('/person-360')
    def get_person_360():
        require('bi', 'read')
        q = request.args.get('q', default='', type=str).strip()
        if not q:
            raise ApiError('Informe o CPF, CNPJ ou Nome para consulta 360º.', 400)
        data = core.get_person_360_view(q)
        audit('Consulta Visão 360 Cidadão', 'bi', q)
        return jsonify(data)

    # ==============================================================================
    # 9. Assistente Virtual de BI / NLP (bi.44 a bi.48)
    # ==============================================================================
    @bi_bp.post('/assistant/query')
    def query_assistant():
        require('bi', 'read')
        body = request.get_json(force=True)
        question = str(body.get('question', '')).strip()
        if not question:
            raise ApiError('Pergunta não informada.', 400)

        user_id = g.user.get('id') if hasattr(g, 'user') and g.user else 1
        user_name = g.user.get('name') if hasattr(g, 'user') and g.user else 'Gestor'
        resp = core.query_bi_assistant(question, user_id=user_id, user_name=user_name)
        audit('Consulta Assistente BI', 'bi_assistant', question[:50])
        return jsonify(resp)

    @bi_bp.get('/assistant/history')
    def assistant_history():
        require('bi', 'read')
        db = get_db()
        rows = db.execute("""
            SELECT id, question_text, domain_identified, answer_text, created_at
            FROM bi_assistant_conversations
            ORDER BY id DESC LIMIT 50
        """).fetchall()
        return jsonify([dict(r) for r in rows])

    # ==============================================================================
    # 10. Modo Kiosk em TV e Compartilhamento de Links (bi.49 a bi.52)
    # ==============================================================================
    @bi_bp.get('/kiosk/slides')
    def get_kiosk_slides():
        require('bi', 'read')
        data = core.get_kiosk_slideshow_config()
        return jsonify(data)

    @bi_bp.post('/share')
    def create_share_link():
        require('bi', 'write')
        body = request.get_json(force=True)
        dashboard_code = str(body.get('dashboard_code', 'executive-lrf')).strip()
        filters = body.get('filters', {})
        user_name = g.user.get('name') if hasattr(g, 'user') and g.user else 'Gestor'
        link_data = core.generate_dashboard_share_link(dashboard_code, filters=filters, user=user_name)
        audit('Geração de Link Compartilhado BI', 'bi_shared_links', link_data['token'])
        return jsonify(link_data), 201

    @bi_bp.get('/shared/<token>')
    def get_shared_dashboard(token):
        db = get_db()
        row = db.execute("SELECT * FROM bi_shared_links WHERE token = ?", (token,)).fetchone()
        if not row:
            raise ApiError('Link de painel não encontrado ou expirado.', 404)

        code = row['dashboard_code']
        # Recupera dados correspondentes ao painel
        if code in ['executive-lrf', 'lrf']:
            data = core.get_executive_lrf_dashboard(2026)
        elif code in ['cash-availability', 'cash']:
            data = core.get_cash_availability_dashboard(2026)
        elif code in ['budget-funnel', 'funnel']:
            data = core.get_budget_execution_funnel(2026)
        elif code in ['hr', 'people']:
            data = core.get_hr_bi_dashboard(2026)
        elif code in ['procurement', 'contracts']:
            data = core.get_procurement_bi_dashboard(2026)
        elif code in ['assets', 'patrimonio']:
            data = core.get_asset_bi_dashboard(2026)
        else:
            data = core.get_executive_lrf_dashboard(2026)

        return jsonify({
            'token': token,
            'dashboard_code': code,
            'created_by': row['created_by'],
            'created_at': row['created_at'],
            'data': data
        })

    app.register_blueprint(bi_bp)

    # Rota pública para visualização compartilhada de painel
    @app.get('/api/public/bi/shared/<token>')
    def public_shared_dashboard(token):
        db = get_db()
        row = db.execute("SELECT * FROM bi_shared_links WHERE token = ?", (token,)).fetchone()
        if not row:
            raise ApiError('Link de painel não encontrado ou expirado.', 404)
        code = row['dashboard_code']
        if code in ['cash-availability', 'cash']:
            data = core.get_cash_availability_dashboard(2026)
        elif code in ['budget-funnel', 'funnel']:
            data = core.get_budget_execution_funnel(2026)
        elif code in ['hr', 'people']:
            data = core.get_hr_bi_dashboard(2026)
        elif code in ['procurement', 'contracts']:
            data = core.get_procurement_bi_dashboard(2026)
        elif code in ['assets', 'patrimonio']:
            data = core.get_asset_bi_dashboard(2026)
        else:
            data = core.get_executive_lrf_dashboard(2026)

        return jsonify({
            'token': token,
            'dashboard_code': code,
            'created_by': row['created_by'],
            'created_at': row['created_at'],
            'data': data
        })

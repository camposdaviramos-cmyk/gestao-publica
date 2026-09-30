"""Endpoints REST, relatórios, importação de planilhas e transparência de Obras Públicas."""
import csv
import io
import json
from decimal import Decimal
from datetime import datetime, date
from html import escape
from flask import request, jsonify, g, send_file
from auth import require, ApiError
from db import get_db, audit, notify
from domain import now, money
from erp_core import load, balance, change_balance, rounded, create_object, set_state
from works_core import engineer_access, calculate_item_value, monthly_funding_projection, check_contract_expiration
from works_operations import suppress_items, amend_works_deadline, amend_works_value, approve_diary_photo, close_project
from integration_signatures import authorize_report, report_response

def _render_report(title, headers, rows, fmt, filename, entity=1):
    authorize_report('works', entity, fmt, filename)
    if fmt == 'csv':
        out = io.StringIO()
        w = csv.writer(out, delimiter=';')
        w.writerow(headers)
        w.writerows(rows)
        stream = io.BytesIO(out.getvalue().encode('utf-8-sig'))
        mime = 'text/csv'
    elif fmt == 'pdf':
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        stream = io.BytesIO()
        styles = getSampleStyleSheet()
        story = [Paragraph(escape(title), styles['Title']), Spacer(1, 10)]
        for r in rows:
            line_str = ' | '.join(f"{h}: {v}" for h, v in zip(headers, r))
            story.extend([Paragraph(escape(line_str), styles['Normal']), Spacer(1, 6)])
        SimpleDocTemplate(stream, pagesize=landscape(A4)).build(story)
        stream.seek(0)
        mime = 'application/pdf'
    else:
        raise ApiError('Formato inválido.')
    return report_response(stream, mime, filename, 'works', entity, filename)

def install_works(app):
    @app.post('/api/works/import-spreadsheet')
    def import_spreadsheet():
        require('works', 'write')
        body = request.get_json(force=True) or {}
        project_id = body.get('project_id')
        if not project_id:
            raise ApiError('Identificador da obra obrigatório.')
        project = load(project_id, 'works', 'projects')
        engineer_access(project, write=True, require_fiscal=False)
        
        items = body.get('items', [])
        if not items:
            raise ApiError('Nenhum item informado para importação.')
            
        bdi_linear = Decimal(str(body.get('bdi_linear') or 0))
        discount_linear = Decimal(str(body.get('discount_linear') or 0))
        
        db = get_db()
        created_count = 0
        total_amount = 0
        
        for idx, it in enumerate(items, 1):
            code = it.get('code') or f"ITEM-{idx:03d}"
            name = it.get('name') or it.get('description') or f"Serviço {idx}"
            unit = it.get('unit') or 'un'
            qty_raw = Decimal(str(it.get('quantity') or 1))
            unit_price_raw = int(it.get('unit_price') or 0)
            item_bdi = Decimal(str(it.get('bdi') if it.get('bdi') is not None else bdi_linear))
            item_disc = Decimal(str(it.get('discount') if it.get('discount') is not None else discount_linear))
            start_date = it.get('start') or project['data'].get('start')
            end_date = it.get('end') or project['data'].get('end')
            
            item_dict = {
                'code': code,
                'name': name,
                'project': project['id'],
                'unit': unit,
                'quantity': str(qty_raw),
                'unit_price': format(Decimal(unit_price_raw) / Decimal('100'), '.2f'),
                'bdi': float(item_bdi),
                'discount': float(item_disc),
                'start': start_date,
                'end': end_date
            }
            
            created_item = create_object('works', 'items', project['entity_id'], project['exercise'], item_dict)
            set_state(created_item, 'Ativo')
            val = calculate_item_value(created_item['data'])
            total_amount += val
            created_count += 1
            
        # Registrar versão inicial da planilha
        ver_count = db.execute(
            "SELECT COUNT(*) FROM works_spreadsheet_versions WHERE project_id=?",
            (project['id'],)
        ).fetchone()[0] + 1
        
        db.execute(
            "INSERT INTO works_spreadsheet_versions(project_id, version_number, active, justification, bdi_linear, discount_linear, total_amount, created_by, created_at) VALUES(?,?,1,?,?,?,?,?,?)",
            (project['id'], ver_count, 'Importação de planilha orçamentária base', float(bdi_linear), float(discount_linear), total_amount, g.user['id'], now())
        )
        
        change_balance(project['id'], 'contracted_amount', total_amount - balance(project['id'], 'contracted_amount'))
        audit('Importação de planilha orçamentária', 'works', project['id'], {'items_count': created_count, 'total_amount': total_amount, 'version': ver_count})
        return jsonify(items_created=created_count, total_amount=total_amount, version=ver_count), 201

    @app.post('/api/works/projects/<int:project_id>/suppress')
    def suppress_route(project_id):
        require('works', 'write')
        project = load(project_id, 'works', 'projects')
        body = request.get_json(force=True) or {}
        item_ids = body.get('item_ids', [])
        justification = body.get('justification') or 'Supressão contratual de itens'
        if not item_ids:
            raise ApiError('Selecione pelo menos um item para supressão.')
        result = suppress_items(project, item_ids, justification)
        return jsonify(result)

    @app.post('/api/works/projects/<int:project_id>/amend')
    def amend_route(project_id):
        require('works', 'write')
        project = load(project_id, 'works', 'projects')
        body = request.get_json(force=True) or {}
        typ = body.get('type')
        justification = body.get('justification') or 'Termo aditivo contratual'
        if typ == 'Prazo':
            new_end = body.get('new_end')
            if not new_end:
                raise ApiError('Informe a nova data de conclusão.')
            result = amend_works_deadline(project, new_end, justification)
        elif typ == 'Valor':
            amount = body.get('amount')
            if amount is None:
                raise ApiError('Informe o valor adicional.')
            result = amend_works_value(project, amount, justification)
        else:
            raise ApiError('Tipo de aditivo inválido. Use "Prazo" ou "Valor".')
        return jsonify(result)

    @app.post('/api/works/diaries/<int:diary_id>/photos')
    def upload_diary_photo(diary_id):
        require('works', 'write')
        diary = load(diary_id, 'works', 'diaries')
        body = request.get_json(force=True) or {}
        filename = body.get('filename') or 'foto.jpg'
        caption = body.get('caption') or ''
        project_id = diary['data']['project']
        db = get_db()
        db.execute(
            "INSERT INTO works_diary_photos(diary_id, project_id, filename, caption, approved, created_at) VALUES(?,?,?,?,0,?)",
            (diary_id, project_id, filename, caption, now())
        )
        photo_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        return jsonify(id=photo_id, diary_id=diary_id, filename=filename, approved=False), 201

    @app.post('/api/works/photos/<int:photo_id>/approve')
    def approve_photo_route(photo_id):
        result = approve_diary_photo(photo_id)
        return jsonify(result)

    @app.get('/api/works/projects/<int:project_id>/photos')
    def list_project_photos(project_id):
        require('works', 'read')
        db = get_db()
        approved_only = request.args.get('approved') == '1'
        query = "SELECT p.*, d.name as diary_name, d.code as diary_code FROM works_diary_photos p JOIN erp_objects d ON p.diary_id=d.id WHERE p.project_id=?"
        params = [project_id]
        if approved_only:
            query += " AND p.approved=1"
        query += " ORDER BY p.id DESC"
        rows = [dict(r) for r in db.execute(query, params).fetchall()]
        return jsonify(items=rows)

    @app.get('/api/works/projects/<int:project_id>/projection')
    def project_funding_projection(project_id):
        require('works', 'read')
        project = load(project_id, 'works', 'projects')
        res = monthly_funding_projection(project['id'])
        return jsonify(res)

    @app.get('/api/works/indicators')
    def works_indicators():
        require('works', 'read')
        db = get_db()
        projects = db.execute("SELECT id, code, name, state, data FROM erp_objects WHERE module='works' AND kind='projects' AND deleted=0").fetchall()
        
        total_projects = len(projects)
        in_progress = sum(1 for p in projects if p['state'] in ['Ativo', 'Em andamento', 'Planejado'])
        completed = sum(1 for p in projects if p['state'] == 'Concluído')
        
        total_contracted = 0
        total_measured = 0
        total_paid = 0
        
        alerts = []
        for p in projects:
            p_dict = {'id': p['id'], 'code': p['code'], 'name': p['name'], 'data': json.loads(p['data'])}
            c_amt = balance(p['id'], 'contracted_amount')
            m_amt = balance(p['id'], 'measured_amount')
            pd_amt = balance(p['id'], 'paid')
            total_contracted += c_amt
            total_measured += m_amt
            total_paid += pd_amt
            
            exp = check_contract_expiration(p_dict)
            if exp:
                alerts.append({'project_id': p['id'], 'code': p['code'], **exp})
                
        # Medições e diários pendentes
        pending_measurements = db.execute("SELECT COUNT(*) FROM erp_objects WHERE module='works' AND kind='measurements' AND state='Submetido' AND deleted=0").fetchone()[0]
        pending_diaries = db.execute("SELECT COUNT(*) FROM erp_objects WHERE module='works' AND kind='diaries' AND state='Rascunho' AND deleted=0").fetchone()[0]
        
        return jsonify({
            'total_projects': total_projects,
            'in_progress': in_progress,
            'completed': completed,
            'total_contracted': total_contracted,
            'total_measured': total_measured,
            'total_paid': total_paid,
            'retention_balance': max(0, total_measured - total_paid),
            'execution_rate': round(total_measured / total_contracted * 100, 1) if total_contracted else 0,
            'pending_measurements': pending_measurements,
            'pending_diaries': pending_diaries,
            'alerts': alerts
        })

    @app.get('/api/works/reports')
    def works_reports():
        require('works', 'read')
        report_type = request.args.get('report', 'summary')
        project_id = request.args.get('project_id')
        fmt = request.args.get('format', 'json')
        db = get_db()
        
        if report_type == 'stoppages':
            # works.44: Relatório de dias não trabalhados e meio período
            query = "SELECT d.id, d.code, d.name, json_extract(d.data,'$.date') as day, json_extract(d.data,'$.weather') as weather, json_extract(d.data,'$.worked') as worked, json_extract(d.data,'$.occurrences') as occurrences, p.name as project_name FROM erp_objects d JOIN erp_objects p ON json_extract(d.data,'$.project')=p.id WHERE d.module='works' AND d.kind='diaries' AND d.deleted=0 AND json_extract(d.data,'$.worked') IN ('Meio período','Não trabalhado')"
            params = []
            if project_id:
                query += " AND json_extract(d.data,'$.project')=?"
                params.append(project_id)
            query += " ORDER BY day DESC"
            rows = [dict(r) for r in db.execute(query, params).fetchall()]
            
            headers = ['DATA', 'OBRA', 'CONDIÇÃO', 'JORNADA', 'OCORRÊNCIAS']
            table_rows = [[r['day'], r['project_name'], r['weather'] or '', r['worked'] or '', r['occurrences'] or ''] for r in rows]
            
            if fmt in ['pdf', 'csv']:
                return _render_report('Relatório de Paralisações e Dias Não Trabalhados em Obras', headers, table_rows, fmt, f"paralisacoes_obras.{fmt}")
            return jsonify(items=rows, count=len(rows))
            
        elif report_type == 'diary':
            # works.43: Impressão do diário de obra em PDF
            diary_id = request.args.get('diary_id')
            if not diary_id:
                raise ApiError('Identificador do diário obrigatório.')
            diary = load(diary_id, 'works', 'diaries')
            project = load(diary['data']['project'], 'works', 'projects')
            d = diary['data']
            
            photos = db.execute("SELECT * FROM works_diary_photos WHERE diary_id=? AND approved=1", (diary_id,)).fetchall()
            
            headers = ['ITEM', 'INFORMAÇÃO']
            table_rows = [
                ['Obra', f"{project['code']} - {project['name']}"],
                ['Diário', f"{diary['code']} - {diary['name']}"],
                ['Data', d.get('date', '')],
                ['Condição climática', d.get('weather', '')],
                ['Jornada', d.get('worked', '')],
                ['Atividades executadas', d.get('activities', '')],
                ['Equipamentos em campo', d.get('equipment', '')],
                ['Mão de obra atuante', d.get('workforce', '')],
                ['Ocorrências', d.get('occurrences', '')],
                ['Fotos aprovadas', f"{len(photos)} fotos registradas e aprovadas pelo fiscal"],
                ['Situação do diário', diary['state']]
            ]
            if fmt in ['pdf', 'csv']:
                return _render_report(f"Diário de Obra #{diary['code']} - {project['code']}", headers, table_rows, fmt, f"diario_{diary['code']}.{fmt}")
            return jsonify(diary=diary, project=project, rows=table_rows)
            
        elif report_type == 'funding':
            # works.39: Previsão de aportes mensais
            if not project_id:
                raise ApiError('Identificador da obra obrigatório.')
            res = monthly_funding_projection(project_id)
            headers = ['Competência', 'Aporte Previsto (R$)', 'Acumulado (R$)', 'Avanço (%)']
            table_rows = [[p['period'], f"{p['amount']/100:.2f}", f"{p['cumulative']/100:.2f}", f"{p['percent']:.2f}%"] for p in res['projection']]
            
            if fmt in ['pdf', 'csv']:
                return _render_report(f"Previsão de Aportes Mensais - Obra #{project_id}", headers, table_rows, fmt, f"aportes_obra_{project_id}.{fmt}")
            return jsonify(res)
            
        # Resumo padrão
        return jsonify(report='works_summary')

    @app.get('/api/public/works')
    def public_works():
        """works.14: Portal de Transparência online para acompanhamento das obras públicas."""
        db = get_db()
        rows = db.execute(
            "SELECT id, code, name, state, data FROM erp_objects WHERE module='works' AND kind='projects' AND deleted=0 ORDER BY id DESC"
        ).fetchall()
        
        items = []
        for r in rows:
            d = json.loads(r['data'])
            contracted = balance(r['id'], 'contracted_amount')
            measured = balance(r['id'], 'measured_amount')
            paid = balance(r['id'], 'paid')
            
            photos = [dict(p) for p in db.execute(
                "SELECT id, filename, caption FROM works_diary_photos WHERE project_id=? AND approved=1 LIMIT 3",
                (r['id'],)
            ).fetchall()]
            
            pct = round(measured / contracted * 100, 1) if contracted else 0
            items.append({
                'id': r['id'],
                'code': r['code'],
                'name': r['name'],
                'state': r['state'],
                'address': d.get('address'),
                'latitude': d.get('latitude'),
                'longitude': d.get('longitude'),
                'engineer': d.get('engineer'),
                'start': d.get('start'),
                'end': d.get('end'),
                'contracted_amount': contracted,
                'measured_amount': measured,
                'paid_amount': paid,
                'percentage': pct,
                'photos': photos
            })
            
        return jsonify(items=items, count=len(items))

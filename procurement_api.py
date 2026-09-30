"""Endpoints REST, validação da Lei 14.133/2021, SRP, CNDs e relatórios de Compras e Contratos."""
import csv
import io
import json
from decimal import Decimal
from datetime import datetime, date, timedelta
from html import escape
from flask import request, jsonify, g, send_file
from auth import require, ApiError
from db import get_db, audit, notify
from domain import now, money
from erp_core import load, balance, change_balance, rounded
from procurement_core import (
    calculate_discounted_price, check_active_srp_for_items,
    check_supplier_compliance, get_contract_financial_summary
)
from procurement_operations import (
    summon_remaining_bidders, register_bid, approve_pca,
    reject_pca, publish_pca_pncp, generate_price_agreement,
    register_carona, apply_procurement_amendment
)
from integration_signatures import authorize_report, report_response

def _render_report(title, headers, rows, fmt, filename, entity=1):
    authorize_report('procurement', entity, fmt, filename)
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
        story = [
            Paragraph(f"<b>Prefeitura Municipal de Rio das Ostras</b>", styles['Title']),
            Paragraph(f"<b>{escape(title)}</b>", styles['Heading2']),
            Paragraph(f"Emissão: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']),
            Spacer(1, 12)
        ]
        for r in rows:
            line_txt = " | ".join(f"<b>{escape(str(h))}</b>: {escape(str(v))}" for h, v in zip(headers, r))
            story.append(Paragraph(line_txt, styles['Normal']))
            story.append(Spacer(1, 4))
            
        SimpleDocTemplate(stream, pagesize=landscape(A4)).build(story)
        stream.seek(0)
        mime = 'application/pdf'
    else:
        raise ApiError('Formato inválido. Use csv ou pdf.')
    return report_response(stream, mime, f"compras-{filename}.{fmt}", 'procurement', entity, title)

def install_procurement(app):
    
    @app.get('/api/procurement/check-srp-alerts')
    def check_srp_alerts_route():
        """Verifica se os itens requisitados ou pretendidos para dispensa já possuem Ata de Registro de Preços vigente."""
        require('procurement', 'read')
        terms_param = request.args.get('terms', '')
        terms = [t.strip() for t in terms_param.split(',') if t.strip()]
        if not terms and request.is_json:
            body = request.get_json(silent=True) or {}
            terms = body.get('terms', [])
            
        entity_id = int(request.args.get('entity_id', 1))
        alerts = check_active_srp_for_items(terms, entity_id)
        return jsonify(has_active_srp=len(alerts) > 0, alerts_count=len(alerts), alerts=alerts)

    @app.get('/api/procurement/pca/versions')
    def pca_versions_route():
        """Consulta as versões e histórico de publicação do Plano de Contratações Anual."""
        require('procurement', 'read')
        exercise = int(request.args.get('exercise', date.today().year))
        db = get_db()
        rows = db.execute(
            "SELECT * FROM procurement_pca_versions WHERE exercise=? ORDER BY version_number DESC",
            (exercise,)
        ).fetchall()
        return jsonify(exercise=exercise, versions=[dict(r) for r in rows])

    @app.post('/api/procurement/processes/<int:process_id>/bids')
    def register_bid_route(process_id):
        """Registra lance na sessão pública do processo licitatório."""
        require('procurement', 'write')
        process = load(process_id, 'procurement', 'processes')
        body = request.get_json(force=True) or {}
        res = register_bid(process, body)
        return jsonify(res), 201

    @app.get('/api/procurement/processes/<int:process_id>/bids')
    def list_bids_route(process_id):
        """Lista os lances e rodadas de disputa do processo."""
        require('procurement', 'read')
        item_id = request.args.get('item_id')
        db = get_db()
        query = """
            SELECT b.*, s.name as supplier_name, i.name as item_name
            FROM procurement_bids b
            JOIN erp_objects s ON b.supplier_id = s.id
            JOIN erp_objects i ON b.item_id = i.id
            WHERE b.process_id=?
        """
        params = [process_id]
        if item_id:
            query += " AND b.item_id=?"
            params.append(item_id)
        query += " ORDER BY b.item_id, b.round_number ASC, b.bid_amount ASC"
        bids = db.execute(query, params).fetchall()
        return jsonify(bids=[dict(b) for b in bids])

    @app.post('/api/procurement/processes/<int:process_id>/summon-remanescentes')
    def summon_remanescentes_route(process_id):
        """Convoca licitante remanescente nos termos do Art. 90 da Lei 14.133/2021."""
        require('procurement', 'write')
        process = load(process_id, 'procurement', 'processes')
        body = request.get_json(force=True) or {}
        res = summon_remaining_bidders(process, body)
        return jsonify(res), 201

    @app.get('/api/procurement/processes/<int:process_id>/summons')
    def list_summons_route(process_id):
        """Lista convocações de remanescentes realizadas no processo."""
        require('procurement', 'read')
        db = get_db()
        rows = db.execute(
            """SELECT s.*, sup.name as supplier_name, it.name as item_name
               FROM procurement_remaining_summons s
               JOIN erp_objects sup ON s.supplier_id=sup.id
               JOIN erp_objects it ON s.item_id=it.id
               WHERE s.process_id=? ORDER BY s.id DESC""",
            (process_id,)
        ).fetchall()
        return jsonify(summons=[dict(r) for r in rows])

    @app.get('/api/procurement/suppliers/<int:supplier_id>/compliance')
    def supplier_compliance_route(supplier_id):
        """Verifica regularidade fiscal, CNDs e sanções de fornecedor."""
        require('procurement', 'read')
        supplier = load(supplier_id, 'procurement', 'suppliers')
        res = check_supplier_compliance(supplier_id)
        return jsonify(supplier_id=supplier_id, supplier_name=supplier['name'], **res)

    @app.post('/api/procurement/suppliers/<int:supplier_id>/certificates')
    def add_supplier_certificate_route(supplier_id):
        """Cadastra ou atualiza CND de fornecedor."""
        require('procurement', 'write')
        supplier = load(supplier_id, 'procurement', 'suppliers')
        body = request.get_json(force=True) or {}
        cert_type = str(body.get('type') or '').strip()
        cert_num = str(body.get('number') or '').strip()
        issue_date = body.get('issue_date')
        exp_date = body.get('expiration_date')
        url = body.get('verification_url', '')
        
        if not cert_type or not cert_num or not issue_date or not exp_date:
            raise ApiError('Tipo, número, emissão e validade são obrigatórios.')
            
        status = 'Vencida' if exp_date < date.today().isoformat() else 'Válida'
        db = get_db()
        db.execute(
            """INSERT INTO procurement_supplier_certificates(
                supplier_id, certificate_type, certificate_number, issue_date, expiration_date, status, verification_url, created_at, updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?)""",
            (supplier_id, cert_type, cert_num, issue_date, exp_date, status, url, now(), now())
        )
        audit('Cadastro de CND', 'procurement', supplier_id, {'type': cert_type, 'number': cert_num, 'exp': exp_date})
        return jsonify(message='Certidão registrada com sucesso.', status=status), 201

    @app.post('/api/procurement/suppliers/<int:supplier_id>/sanctions')
    def add_supplier_sanction_route(supplier_id):
        """Registra penalidade administrativa em desfavor do fornecedor."""
        require('procurement', 'approve')
        supplier = load(supplier_id, 'procurement', 'suppliers')
        body = request.get_json(force=True) or {}
        stype = str(body.get('type') or '').strip()
        code = str(body.get('code') or '').strip()
        basis = str(body.get('legal_basis') or '').strip()
        start = body.get('start') or date.today().isoformat()
        end = body.get('end')
        fine = int(body.get('fine_amount') or 0)
        
        if not stype or not code or not basis:
            raise ApiError('Tipo de sanção, processo de origem e fundamentação legal são obrigatórios.')
            
        db = get_db()
        db.execute(
            """INSERT INTO procurement_supplier_sanctions(
                supplier_id, sanction_type, legal_basis, origin_process, start_date, end_date, fine_amount, active, notes, created_by, created_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (supplier_id, stype, basis, code, start, end, fine, 1, body.get('notes', ''), g.user['id'], now())
        )
        audit('Registro de Sanção', 'procurement', supplier_id, {'sanction': stype, 'process': code})
        return jsonify(message='Penalidade administrativa registrada.', active=True), 201

    @app.get('/api/procurement/contracts/<int:contract_id>/financial-summary')
    def contract_financial_summary_route(contract_id):
        """Retorna posição financeira consolidada do contrato x empenhos x aditivos."""
        require('procurement', 'read')
        summary = get_contract_financial_summary(contract_id)
        return jsonify(summary)

    @app.get('/api/procurement/agreements')
    def list_agreements_route():
        """Lista as Atas de Registro de Preços vigentes e encerradas."""
        require('procurement', 'read')
        db = get_db()
        rows = db.execute(
            """SELECT a.*, s.name as supplier_name, p.code as process_code, p.name as process_name
               FROM procurement_price_agreements a
               JOIN erp_objects s ON a.supplier_id = s.id
               JOIN erp_objects p ON a.process_id = p.id
               ORDER BY a.year DESC, a.id DESC"""
        ).fetchall()
        return jsonify(agreements=[dict(r) for r in rows])

    @app.get('/api/procurement/agreements/<int:agreement_id>/items')
    def list_agreement_items_route(agreement_id):
        """Lista itens da Ata de Registro de Preços com saldos."""
        require('procurement', 'read')
        db = get_db()
        rows = db.execute(
            "SELECT * FROM procurement_price_agreement_items WHERE agreement_id=? ORDER BY id ASC",
            (agreement_id,)
        ).fetchall()
        
        items = []
        for r in rows:
            d = dict(r)
            d['available_quantity'] = (d['quantity_registered'] - d['quantity_consumed']) / 1000000
            d['percent_consumed'] = round((d['quantity_consumed'] / d['quantity_registered'] * 100), 1) if d['quantity_registered'] else 0
            items.append(d)
        return jsonify(items=items)

    @app.get('/api/procurement/reports')
    def procurement_reports():
        """Emissão de relatórios gerenciais e mapas comparativos em PDF/CSV."""
        require('procurement', 'read')
        report_type = request.args.get('report', 'agreements')
        fmt = request.args.get('format', 'json')
        db = get_db()
        
        if report_type == 'agreements':
            rows = db.execute(
                """SELECT a.code, a.name, s.name as supplier, a.start_date, a.end_date, 
                          a.total_amount, a.active
                   FROM procurement_price_agreements a
                   JOIN erp_objects s ON a.supplier_id = s.id
                   ORDER BY a.end_date DESC"""
            ).fetchall()
            headers = ['NÚMERO DA ATA', 'OBJETO', 'FORNECEDOR DETENTOR', 'VIGÊNCIA INICIAL', 'VIGÊNCIA FINAL', 'VALOR GLOBAL (R$)', 'STATUS']
            table_rows = [
                [r['code'], r['name'], r['supplier'], r['start_date'], r['end_date'], f"R$ {r['total_amount']/100:,.2f}", 'Ativa' if r['active'] else 'Encerrada']
                for r in rows
            ]
            title = 'Relatório de Atas de Registro de Preços (SRP)'
            filename = 'atas-srp'
        elif report_type == 'certificates':
            rows = db.execute(
                """SELECT sup.name as supplier, sup.code as doc, c.certificate_type, c.certificate_number,
                          c.issue_date, c.expiration_date, c.status
                   FROM procurement_supplier_certificates c
                   JOIN erp_objects sup ON c.supplier_id = sup.id
                   ORDER BY c.expiration_date ASC"""
            ).fetchall()
            headers = ['FORNECEDOR', 'DOCUMENTO', 'TIPO DE CND', 'NÚMERO', 'EMISSÃO', 'VALIDADE', 'SITUAÇÃO']
            table_rows = [
                [r['supplier'], r['doc'], r['certificate_type'], r['certificate_number'], r['issue_date'], r['expiration_date'], r['status']]
                for r in rows
            ]
            title = 'Relatório de Regularidade Fiscal e Certidões de Fornecedores'
            filename = 'regularidade-cnds'
        else:
            raise ApiError('Tipo de relatório não reconhecido.')
            
        if fmt == 'json':
            return jsonify(title=title, count=len(table_rows), headers=headers, rows=table_rows)
        return _render_report(title, headers, table_rows, fmt, filename)

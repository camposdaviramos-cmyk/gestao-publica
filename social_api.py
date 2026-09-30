"""
API REST do Módulo de Assistência Social e Cidadania (SUAS / CRAS / CREAS / CadÚnico)
Município de Rio das Ostras - Edital PE 552/2026 e Anexo III (410 Itens Normativos)
"""

from datetime import datetime, date
from flask import Blueprint, request, jsonify, Response, g
from auth import require, ApiError
from db import audit
import social_core as core

def install_social(app):
    social_bp = Blueprint('social', __name__, url_prefix='/api/social')

    # 1. Unidades e Equipes
    @social_bp.get('/units')
    def get_units():
        require('social', 'read')
        utype = request.args.get('type')
        return jsonify(core.list_units(utype))

    @social_bp.post('/units')
    def create_unit():
        require('social', 'write')
        data = request.get_json(force=True)
        res = core.create_unit(data)
        audit('Cadastro de Unidade SUAS', 'social_units', res['code'])
        return jsonify(res), 201

    @social_bp.get('/teams')
    def get_teams():
        require('social', 'read')
        uid = request.args.get('unit_id', type=int)
        return jsonify(core.list_team_members(uid))

    @social_bp.post('/teams')
    def add_team():
        require('social', 'write')
        data = request.get_json(force=True)
        res = core.add_team_member(data)
        audit('Cadastro de Profissional Técnico SUAS', 'social_teams', res['name'])
        return jsonify(res), 201

    # 2. Territórios, Diagnóstico e Mapa de Calor
    @social_bp.get('/territories')
    def get_territories():
        require('social', 'read')
        return jsonify(core.list_territories())

    @social_bp.get('/heatmap')
    def get_heatmap():
        require('social', 'read')
        return jsonify(core.get_territorial_heatmap())

    @social_bp.get('/diagnosis')
    def get_diagnosis():
        require('social', 'read')
        return jsonify(core.get_territorial_diagnosis())

    # 3. Estoque e Benefícios Eventuais
    @social_bp.get('/supplies')
    def get_supplies():
        require('social', 'read')
        return jsonify(core.list_supplies())

    @social_bp.get('/stock/batches')
    def get_batches():
        require('social', 'read')
        sid = request.args.get('supply_id', type=int)
        return jsonify(core.list_stock_batches(sid))

    @social_bp.post('/stock/batches')
    def add_batch():
        require('social', 'write')
        data = request.get_json(force=True)
        user = g.user['name'] if hasattr(g, 'user') and g.user else 'Almoxarife'
        res = core.add_stock_entry(
            warehouse_id=data['warehouse_id'],
            supply_id=data['supply_id'],
            batch_number=data['batch_number'],
            quantity=data['quantity'],
            manufacture_date=data.get('manufacture_date'),
            expiration_date=data.get('expiration_date'),
            supplier_name=data.get('supplier_name', ''),
            unit_cost=data.get('unit_cost', 0.0),
            user=user
        )
        audit('Entrada de Estoque Socioassistencial', 'social_stock', data['batch_number'])
        return jsonify(res), 201

    @social_bp.get('/benefits')
    def get_benefits():
        require('social', 'read')
        fid = request.args.get('family_id', type=int)
        return jsonify(core.list_benefits_granted(fid))

    @social_bp.post('/benefits')
    def grant_benefit():
        require('social', 'write')
        data = request.get_json(force=True)
        user = g.user['name'] if hasattr(g, 'user') and g.user else 'Assistente Social'
        res = core.grant_benefit(
            family_id=data['family_id'],
            member_id=data.get('member_id'),
            benefit_type=data['benefit_type'],
            supply_id=data.get('supply_id'),
            batch_id=data.get('batch_id'),
            amount=data.get('amount', 0.0),
            quantity=data.get('quantity', 1),
            technical_opinion=data.get('technical_opinion', ''),
            social_worker_cress=data.get('social_worker_cress', ''),
            social_worker_name=data.get('social_worker_name', ''),
            user=user
        )
        audit('Concessão de Benefício Eventual', 'social_benefits', str(res['id']))
        return jsonify(res), 201

    # 4. Prontuário SUAS e Famílias CadÚnico
    @social_bp.get('/families')
    def get_families():
        require('social', 'read')
        q = request.args.get('q')
        cras_id = request.args.get('cras_id', type=int)
        ivs = request.args.get('ivs')
        return jsonify(core.list_families(q, cras_id, ivs))

    @social_bp.get('/families/<int:fid>')
    def get_family(fid):
        require('social', 'read')
        return jsonify(core.get_family_details(fid))

    @social_bp.post('/families')
    def save_family():
        require('social', 'write')
        data = request.get_json(force=True)
        res = core.save_family(data)
        audit('Atualização de Prontuário Familiar', 'social_families', res['family']['family_code'])
        return jsonify(res), 200

    @social_bp.post('/families/<int:fid>/members')
    def add_member(fid):
        require('social', 'write')
        data = request.get_json(force=True)
        res = core.add_family_member(fid, data)
        audit('Inclusão de Membro Familiar', 'social_family_members', str(fid))
        return jsonify(res), 201

    # 5. RMA Oficial (CRAS, CREAS, POP)
    @social_bp.get('/rma/cras')
    def get_rma_cras():
        require('social', 'read')
        uid = request.args.get('unit_id', type=int)
        year = request.args.get('year', type=int, default=datetime.now().year)
        month = request.args.get('month', type=int, default=datetime.now().month)
        if not uid:
            raise ApiError("unit_id é obrigatório.")
        return jsonify(core.get_or_calculate_rma_cras(uid, year, month))

    @social_bp.post('/rma/cras/close')
    def close_rma_cras():
        require('social', 'write')
        data = request.get_json(force=True)
        user = g.user['name'] if hasattr(g, 'user') and g.user else 'Coordenador CRAS'
        res = core.close_rma_cras(data['unit_id'], data['year'], data['month'], user)
        audit('Fechamento Mensal RMA CRAS', 'social_rma_cras', f"{data['unit_id']}-{data['year']}/{data['month']}")
        return jsonify(res), 200

    @social_bp.get('/rma/cras/export-xml')
    def export_cras_xml():
        require('social', 'read')
        uid = request.args.get('unit_id', type=int)
        year = request.args.get('year', type=int, default=datetime.now().year)
        month = request.args.get('month', type=int, default=datetime.now().month)
        if not uid:
            raise ApiError("unit_id é obrigatório.")
        xml_content = core.export_rma_cras_xml(uid, year, month)
        return Response(xml_content, mimetype='application/xml',
                        headers={'Content-Disposition': f'attachment; filename=RMA_CRAS_{year}_{month:02d}.xml'})

    @social_bp.get('/rma/creas')
    def get_rma_creas():
        require('social', 'read')
        uid = request.args.get('unit_id', type=int)
        year = request.args.get('year', type=int, default=datetime.now().year)
        month = request.args.get('month', type=int, default=datetime.now().month)
        if not uid:
            raise ApiError("unit_id é obrigatório.")
        return jsonify(core.get_or_calculate_rma_creas(uid, year, month))

    @social_bp.post('/rma/creas/close')
    def close_rma_creas():
        require('social', 'write')
        data = request.get_json(force=True)
        user = g.user['name'] if hasattr(g, 'user') and g.user else 'Coordenador CREAS'
        res = core.close_rma_creas(data['unit_id'], data['year'], data['month'], user)
        audit('Fechamento Mensal RMA CREAS', 'social_rma_creas', f"{data['unit_id']}-{data['year']}/{data['month']}")
        return jsonify(res), 200

    @social_bp.get('/rma/creas/export-xml')
    def export_creas_xml():
        require('social', 'read')
        uid = request.args.get('unit_id', type=int)
        year = request.args.get('year', type=int, default=datetime.now().year)
        month = request.args.get('month', type=int, default=datetime.now().month)
        if not uid:
            raise ApiError("unit_id é obrigatório.")
        xml_content = core.export_rma_creas_xml(uid, year, month)
        return Response(xml_content, mimetype='application/xml',
                        headers={'Content-Disposition': f'attachment; filename=RMA_CREAS_{year}_{month:02d}.xml'})

    @social_bp.get('/rma/pop')
    def get_rma_pop():
        require('social', 'read')
        uid = request.args.get('unit_id', type=int)
        year = request.args.get('year', type=int, default=datetime.now().year)
        month = request.args.get('month', type=int, default=datetime.now().month)
        if not uid:
            raise ApiError("unit_id é obrigatório.")
        return jsonify(core.get_or_calculate_rma_pop(uid, year, month))

    @social_bp.post('/rma/pop/close')
    def close_rma_pop():
        require('social', 'write')
        data = request.get_json(force=True)
        user = g.user['name'] if hasattr(g, 'user') and g.user else 'Coordenador Centro POP'
        res = core.close_rma_pop(data['unit_id'], data['year'], data['month'], user)
        audit('Fechamento Mensal RMA Centro POP', 'social_rma_pop', f"{data['unit_id']}-{data['year']}/{data['month']}")
        return jsonify(res), 200

    @social_bp.get('/rma/pop/export-xml')
    def export_pop_xml():
        require('social', 'read')
        uid = request.args.get('unit_id', type=int)
        year = request.args.get('year', type=int, default=datetime.now().year)
        month = request.args.get('month', type=int, default=datetime.now().month)
        if not uid:
            raise ApiError("unit_id é obrigatório.")
        xml_content = core.export_rma_pop_xml(uid, year, month)
        return Response(xml_content, mimetype='application/xml',
                        headers={'Content-Disposition': f'attachment; filename=RMA_POP_{year}_{month:02d}.xml'})

    # 6. Acolhimento e Sigilo (Violência Doméstica)
    @social_bp.get('/shelterings')
    def get_shelterings():
        require('social', 'read')
        uid = request.args.get('unit_id', type=int)
        return jsonify(core.list_shelterings(uid))

    @social_bp.post('/shelterings')
    def add_sheltering():
        require('social', 'write')
        data = request.get_json(force=True)
        res = core.register_sheltering(data)
        audit('Admissão em Acolhimento Institucional', 'social_shelterings', str(res['id']))
        return jsonify(res), 201

    @social_bp.post('/shelterings/<int:sid>/discharge')
    def discharge(sid):
        require('social', 'write')
        data = request.get_json(force=True)
        res = core.discharge_sheltering(sid, data['discharge_date'], data['discharge_reason'])
        audit('Desligamento de Acolhimento Institucional', 'social_shelterings', str(sid))
        return jsonify(res), 200

    @social_bp.post('/violence')
    def register_violence():
        require('social', 'write')
        data = request.get_json(force=True)
        res = core.register_violence_record(data)
        audit('Registro Sigiloso de Violência contra Mulher', 'social_violence', res['secret_code'])
        return jsonify(res), 201

    # 7. SCFV - Cursos e Chamada Diária
    @social_bp.get('/courses')
    def get_courses():
        require('social', 'read')
        return jsonify(core.list_courses())

    @social_bp.get('/classes')
    def get_classes():
        require('social', 'read')
        cid = request.args.get('course_id', type=int)
        return jsonify(core.list_classes(cid))

    @social_bp.post('/classes/<int:cid>/enroll')
    def enroll(cid):
        require('social', 'write')
        data = request.get_json(force=True)
        res = core.enroll_participant(cid, data['family_id'], data.get('member_id'), data['participant_name'])
        audit('Matrícula SCFV / Oficina', 'social_enrollments', str(res['id']))
        return jsonify(res), 201

    @social_bp.post('/classes/<int:cid>/attendance')
    def post_attendance(cid):
        require('social', 'write')
        data = request.get_json(force=True)
        res = core.record_attendance_batch(cid, data['attendance_date'], data['attendances'])
        audit('Diário de Frequência SCFV', 'social_attendance', f"Turma {cid} - {data['attendance_date']}")
        return jsonify(res), 200

    # 8. Assinatura Digital ICP-Brasil
    @social_bp.post('/signatures')
    def sign_document():
        require('social', 'write')
        data = request.get_json(force=True)
        res = core.sign_document_icp(
            document_type=data['document_type'],
            document_id=data['document_id'],
            signer_name=data['signer_name'],
            signer_cpf=data['signer_cpf'],
            signer_role=data['signer_role'],
            council_registration=data.get('council_registration'),
            document_payload=data.get('document_payload', '')
        )
        audit('Assinatura Digital ICP-Brasil', 'social_signatures', str(res['id']))
        return jsonify(res), 201

    @social_bp.get('/signatures/<int:sid>/verify')
    def verify_sig(sid):
        require('social', 'read')
        return jsonify(core.verify_digital_signature(sid))

    # 9. Habitação de Interesse Social
    @social_bp.get('/housing/complexes')
    def get_complexes():
        require('social', 'read')
        pid = request.args.get('program_id', type=int)
        return jsonify(core.list_housing_complexes(pid))

    @social_bp.post('/housing/applications')
    def apply_housing():
        require('social', 'write')
        data = request.get_json(force=True)
        res = core.apply_for_housing(
            program_id=data['program_id'],
            complex_id=data['complex_id'],
            family_id=data['family_id'],
            manual_points=data.get('manual_points', 0),
            adjustment_reason=data.get('adjustment_reason'),
            adjusted_by=g.user['name'] if hasattr(g, 'user') and g.user else 'Assistente Social'
        )
        audit('Inscrição Habitacional Municipal', 'social_housing', res['application_number'])
        return jsonify(res), 201

    @social_bp.get('/housing/ranking')
    def get_ranking():
        require('social', 'read')
        pid = request.args.get('program_id', type=int)
        cid = request.args.get('complex_id', type=int)
        if not cid:
            raise ApiError("complex_id é obrigatório.")
        return jsonify(core.generate_housing_ranking(pid, cid))

    # 10. MROSC (Lei 13.019/2014)
    @social_bp.get('/oscs')
    def get_oscs():
        require('social', 'read')
        st = request.args.get('status')
        return jsonify(core.list_oscs(st))

    @social_bp.post('/oscs')
    def add_osc():
        require('social', 'write')
        data = request.get_json(force=True)
        res = core.register_osc(data)
        audit('Cadastro de OSC Parceira MROSC', 'social_oscs', res['cnpj'])
        return jsonify(res), 201

    @social_bp.post('/oscs/<int:oid>/plans')
    def submit_plan(oid):
        require('social', 'write')
        data = request.get_json(force=True)
        res = core.submit_work_plan(oid, data)
        audit('Submissão de Plano de Trabalho MROSC', 'social_plans', str(res['id']))
        return jsonify(res), 201

    @social_bp.get('/oscs/contracts')
    def get_osc_contracts():
        require('social', 'read')
        oid = request.args.get('osc_id', type=int)
        return jsonify(core.list_osc_contracts(oid))

    @social_bp.post('/oscs/monthly-accounts')
    def submit_account():
        require('social', 'write')
        data = request.get_json(force=True)
        res = core.submit_monthly_account(data['contract_id'], data['year'], data['month'], data)
        audit('Prestação de Contas Mensal MROSC', 'social_accounts', str(res['id']))
        return jsonify(res), 201

    @social_bp.post('/oscs/monthly-accounts/<int:aid>/review')
    def review_account(aid):
        require('social', 'write')
        data = request.get_json(force=True)
        user = g.user['name'] if hasattr(g, 'user') and g.user else 'Gestor MROSC'
        res = core.review_monthly_account(aid, data['review_status'], data.get('review_notes', ''), user)
        audit('Homologação de Contas MROSC', 'social_accounts', str(aid))
        return jsonify(res), 200

    # 11. Conectores e Importadores CadÚnico / SICON
    @social_bp.post('/import/cadunico')
    def import_cad():
        require('social', 'write')
        data = request.get_json(force=True) if request.is_json else {'content': request.get_data(as_text=True)}
        content = data.get('content', '')
        fname = data.get('filename') or request.args.get('filename', 'cadunico.csv')
        user = g.user['name'] if hasattr(g, 'user') and g.user else 'Entrevistador CadÚnico'
        res = core.process_cadunico_import(content, fname, user)
        audit('Importação da Base CadÚnico', 'social_import', fname)
        return jsonify(res), 200

    @social_bp.post('/import/sicon')
    def import_sicon():
        require('social', 'write')
        data = request.get_json(force=True) if request.is_json else {'content': request.get_data(as_text=True)}
        content = data.get('content', '')
        fname = data.get('filename') or request.args.get('filename', 'sicon.csv')
        user = g.user['name'] if hasattr(g, 'user') and g.user else 'Técnico SICON'
        res = core.process_sicon_import(content, fname, user)
        audit('Importação de Condicionalidades SICON', 'social_import', fname)
        return jsonify(res), 200

    app.register_blueprint(social_bp)

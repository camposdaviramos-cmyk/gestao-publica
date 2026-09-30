"""Blueprint e Endpoints REST do Módulo de Controle Interno e Controladoria.
Atende aos 85 itens do Anexo III e Edital PE 552/2026.
"""
from flask import Blueprint, request, jsonify, g
from auth import require, ApiError
from domain import now
from erp_core import entity_access
import control_core as core

control_bp = Blueprint('control_api', __name__)

@control_bp.before_request
def check_auth():
    # Rotas de controle exigem usuário autenticado
    if not getattr(g, 'user', None):
        raise ApiError('Autenticação necessária para acessar o Controle Interno.', 401)

@control_bp.get('/api/control/ibge')
def get_ibge():
    entity_id = entity_access(request.args.get('entity', 1))
    exercise = int(request.args.get('exercise', 2026))
    data = core.get_ibge_info(entity_id, exercise)
    return jsonify(data=data)

@control_bp.put('/api/control/ibge')
def update_ibge():
    require('control', 'write')
    d = request.get_json() or {}
    entity_id = entity_access(d.get('entity', 1))
    exercise = int(d.get('exercise', 2026))
    data = core.update_ibge_info(entity_id, exercise, d)
    return jsonify(message='Dados do município atualizados com sucesso.', data=data)

@control_bp.get('/api/control/calendar')
def get_calendar():
    entity_id = entity_access(request.args.get('entity', 1))
    exercise = int(request.args.get('exercise', 2026))
    month = request.args.get('month')
    sphere = request.args.get('sphere')
    status = request.args.get('status')
    events = core.get_calendar_events(entity_id, exercise, month, sphere, status)
    return jsonify(events=events)

@control_bp.get('/api/control/obligations/summary')
def get_summary():
    entity_id = entity_access(request.args.get('entity', 1))
    exercise = int(request.args.get('exercise', 2026))
    summary = core.get_obligations_summary(entity_id, exercise)
    return jsonify(summary=summary)

@control_bp.post('/api/control/obligations/load-defaults')
def load_defaults():
    require('control', 'write')
    d = request.get_json() or {}
    entity_id = entity_access(d.get('entity', 1))
    exercise = int(d.get('exercise', 2026))
    from control_seed import seed_control
    seed_control(entity_id, exercise)
    return jsonify(message='Carga automática de obrigações legais, regras SICONFI e requisitos CAUC concluída com sucesso.')

@control_bp.get('/api/control/occurrences/<int:id>')
def get_occurrence(id):
    occ = core.get_occurrence_detail(id)
    return jsonify(occurrence=occ)

@control_bp.post('/api/control/occurrences/<int:id>/followup')
def add_followup(id):
    require('control', 'write')
    d = request.get_json() or {}
    f_type = d.get('type', 'Comentário')
    notes = d.get('notes', '')
    att_name = d.get('attachment_name')
    att_url = d.get('attachment_url')
    author = g.user.get('name', 'Usuário do Sistema')

    res = core.add_occurrence_followup(
        occurrence_id=id,
        followup_type=f_type,
        notes=notes,
        author_name=author,
        attachment_name=att_name,
        attachment_url=att_url
    )
    return jsonify(res)

@control_bp.post('/api/control/occurrences/<int:id>/quick-close')
def quick_close(id):
    require('control', 'write')
    d = request.get_json() or {}
    notes = d.get('notes', 'Encerramento rápido registrado.')
    author = g.user.get('name', 'Controlador')
    res = core.quick_close_occurrence(id, author, notes)
    return jsonify(res)

@control_bp.post('/api/control/occurrences/<int:id>/send-email')
def send_email(id):
    require('control', 'write')
    d = request.get_json() or {}
    recip = d.get('recipient_email')
    subject = d.get('subject', 'Aviso de Obrigação Legal')
    body = d.get('message_body', '')
    author = g.user.get('name', 'Controlador')

    res = core.send_obligation_email(
        occurrence_id=id,
        recipient_email=recip,
        subject=subject,
        message_body=body,
        author_name=author
    )
    return jsonify(res)

# =========================================================================
# SICONFI & Ranking STN
# =========================================================================

@control_bp.get('/api/control/siconfi/ranking')
def get_siconfi_ranking():
    entity_id = entity_access(request.args.get('entity', 1))
    exercise = int(request.args.get('exercise', 2026))
    dim = request.args.get('dimension')
    power = request.args.get('power')
    period = request.args.get('period')
    data = core.get_siconfi_dashboard(entity_id, exercise, dim, power, period)
    return jsonify(data=data)

@control_bp.get('/api/control/siconfi/rules')
def list_siconfi_rules():
    entity_id = entity_access(request.args.get('entity', 1))
    data = core.get_siconfi_dashboard(entity_id, 2026)
    return jsonify(rules=data['items'])

@control_bp.post('/api/control/siconfi/rules')
def manage_rule():
    require('control', 'write')
    d = request.get_json() or {}
    action = d.get('action', 'create')
    entity_id = entity_access(d.get('entity', 1))
    res = core.manage_siconfi_rule(action, d, entity_id)
    return jsonify(res)

@control_bp.post('/api/control/siconfi/reprocess')
def reprocess_siconfi():
    require('control', 'write')
    d = request.get_json() or {}
    entity_id = entity_access(d.get('entity', 1))
    exercise = int(d.get('exercise', 2026))
    period = d.get('period', f"{exercise}-01")
    delete_first = bool(d.get('delete_first', False))
    res = core.reprocess_siconfi_period(entity_id, exercise, period, delete_first)
    return jsonify(res)

# =========================================================================
# Planos de Ação e Notificações (Sininho)
# =========================================================================

@control_bp.get('/api/control/action-plans')
def list_action_plans():
    entity_id = entity_access(request.args.get('entity', 1))
    exercise = int(request.args.get('exercise', 2026))
    source = request.args.get('source_module')
    status = request.args.get('status')
    plans = core.get_action_plans(entity_id, exercise, source, status)
    return jsonify(plans=plans)

@control_bp.post('/api/control/action-plans')
def create_plan():
    require('control', 'write')
    d = request.get_json() or {}
    entity_id = entity_access(d.get('entity', 1))
    exercise = int(d.get('exercise', 2026))
    author = g.user.get('name', 'Controlador')
    res = core.create_action_plan(d, author, entity_id, exercise)
    return jsonify(res)

@control_bp.post('/api/control/action-plans/<int:id>/respond')
def respond_plan(id):
    require('control', 'write')
    d = request.get_json() or {}
    notes = d.get('response_notes', '')
    evidence = d.get('response_evidence')
    author = g.user.get('name', 'Responsável Técnico')
    res = core.respond_action_plan(id, notes, evidence, author)
    return jsonify(res)

@control_bp.get('/api/control/notifications')
def get_user_notifications():
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    role = g.user.get('role', 'CONTROLADOR')
    user_id = g.user.get('id')
    data = core.get_notifications(user_id=user_id, role=role, unread_only=unread_only)
    return jsonify(data)

@control_bp.put('/api/control/notifications/<int:id>/read')
def mark_read(id):
    res = core.mark_notification_read(id)
    return jsonify(res)

# =========================================================================
# CAUC & Convênios
# =========================================================================

@control_bp.get('/api/control/cauc')
def get_cauc():
    entity_id = entity_access(request.args.get('entity', 1))
    data = core.get_cauc_dashboard(entity_id)
    return jsonify(data=data)

@control_bp.put('/api/control/cauc/responsible')
def update_cauc_resp():
    require('control', 'write')
    d = request.get_json() or {}
    entity_id = entity_access(d.get('entity', 1))
    code = d.get('code')
    name = d.get('responsible_name')
    email = d.get('responsible_email')
    res = core.update_cauc_responsible(code, name, email, entity_id)
    return jsonify(res)

@control_bp.get('/api/control/agreements')
def get_agreements():
    entity_id = entity_access(request.args.get('entity', 1))
    exercise = int(request.args.get('exercise', 2026))
    data = core.get_agreements_dashboard(entity_id, exercise)
    return jsonify(data=data)

@control_bp.put('/api/control/agreements/responsible')
def update_agreement_resp():
    require('control', 'write')
    d = request.get_json() or {}
    entity_id = entity_access(d.get('entity', 1))
    num = d.get('agreement_number')
    name = d.get('responsible_name')
    email = d.get('responsible_email')
    res = core.update_agreement_responsible(num, name, email, entity_id)
    return jsonify(res)

# =========================================================================
# Relatórios Conclusivos Mensais e Versionamento
# =========================================================================

@control_bp.post('/api/control/reports/conclusive')
def create_report():
    require('control', 'write')
    d = request.get_json() or {}
    entity_id = entity_access(d.get('entity', 1))
    exercise = int(d.get('exercise', 2026))
    author = g.user.get('name', 'Controlador Geral')
    res = core.generate_conclusive_report(d, author, entity_id, exercise)
    return jsonify(res)

@control_bp.get('/api/control/reports/conclusive/versions')
def list_report_versions():
    entity_id = entity_access(request.args.get('entity', 1))
    exercise = int(request.args.get('exercise', 2026))
    rep_type = request.args.get('report_type')
    period = request.args.get('period')
    versions = core.get_report_versions(entity_id, exercise, rep_type, period)
    return jsonify(versions=versions)

def install_control(app):
    app.register_blueprint(control_bp)

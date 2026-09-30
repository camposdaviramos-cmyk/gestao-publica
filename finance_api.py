"""
Blueprint e Endpoints REST do Módulo Financeiro, Contábil e Orçamentário
Sistema Integrado Rio das Ostras - Edital PE 552/2026 & Anexo III (229 Itens)
"""

import functools
from flask import Blueprint, request, jsonify, g
from auth import require, ApiError

def require_auth(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        require('finance', 'read' if request.method in ('GET', 'HEAD', 'OPTIONS') else 'write')
        return fn(*args, **kwargs)
    return wrapper
from finance_core import (
    create_accounting_rule, validate_accounting_rules, get_accounting_rules,
    get_siconfi_mappings, update_siconfi_mapping, copy_siconfi_mappings_from_previous_year,
    generate_msc_file, import_msc_file, query_msc_movements,
    get_siops_mappings, get_siope_mappings, generate_siops_export, generate_siope_export,
    generate_law9452_report, calculate_pasep, calculate_article_29a_duodecimo,
    generate_anexo1_receita_despesa, generate_anexo12_balanco_orcamentario,
    generate_anexo13_balanco_financeiro, generate_anexo14_balanco_patrimonial,
    generate_anexo15_dvp, generate_anexo18_dfc,
    create_standardized_entry, post_journal_entry, reverse_journal_entry, query_journal_entries,
    query_expense_balances, query_revenue_balances,
    register_reinf_taxpayer, register_reinf_process, register_reinf_invoice,
    get_reinf_conciliation_panel, validate_and_transmit_reinf_event,
    save_budget_planning_item, project_budget_estimates, import_loa_into_ppa,
    generate_formatted_decree, get_ldo_fiscal_target, save_ldo_fiscal_target,
    generate_rreo_report, generate_rgf_report, calculate_constitutional_limits,
    generate_obe_batch, process_bank_return_file, issue_treasury_check,
    import_ofx_statement, auto_reconcile_ofx, lock_reconciliation_calendar,
    create_advance_fund, submit_advance_fund_accountability,
    query_chronological_payments, export_manad_file, export_sigfis_tcerj,
    authenticate_siafic_cpf
)

finance_bp = Blueprint('finance', __name__)

# ==============================================================================
# PCASP e Regras Contábeis
# ==============================================================================

@finance_bp.route('/api/finance/pcasp', methods=['GET'])
@require_auth
def handle_pcasp():
    from db import get_db
    rows = get_db().execute("SELECT * FROM finance_pcasp_accounts ORDER BY code").fetchall()
    return jsonify({"accounts": [dict(r) for r in rows]})

@finance_bp.route('/api/finance/rules', methods=['GET', 'POST'])

@require_auth
def handle_rules():
    if request.method == 'GET':
        group = request.args.get('group')
        fact = request.args.get('fact_type')
        return jsonify(get_accounting_rules(group, fact))
    data = request.get_json(silent=True) or {}
    rule_id = create_accounting_rule(
        data['fact_type'], data['group_name'], data['rule_name'],
        data['debit_account_code'], data['credit_account_code'],
        g.user.get('username', 'admin') if hasattr(g, 'user') else 'admin'
    )
    return jsonify({"id": rule_id, "status": "Criada com sucesso"}), 201

@finance_bp.route('/api/finance/rules/validate', methods=['GET'])
@require_auth
def handle_validate_rules():
    fact = request.args.get('fact_type')
    return jsonify(validate_accounting_rules(fact))


# ==============================================================================
# SICONFI MSC & SIOPS / SIOPE
# ==============================================================================

@finance_bp.route('/api/finance/siconfi/mappings', methods=['GET', 'POST'])
@require_auth
def handle_siconfi_mappings():
    if request.method == 'GET':
        mtype = request.args.get('type')
        ex = int(request.args.get('exercise', 2026))
        return jsonify(get_siconfi_mappings(mtype, ex))
    data = request.get_json(silent=True) or {}
    update_siconfi_mapping(
        data['mapping_type'], data['local_code'], data['siconfi_code'],
        data.get('local_description'), data.get('siconfi_description'),
        int(data.get('exercise', 2026))
    )
    return jsonify({"status": "Mapeamento atualizado"})

@finance_bp.route('/api/finance/siconfi/copy-previous', methods=['POST'])
@require_auth
def handle_copy_siconfi():
    data = request.get_json(silent=True) or {}
    ex = int(data.get('exercise', 2026))
    copied = copy_siconfi_mappings_from_previous_year(ex)
    return jsonify({"copied": copied, "exercise": ex})

@finance_bp.route('/api/finance/msc/generate', methods=['GET'])
@require_auth
def handle_generate_msc():
    ex = int(request.args.get('exercise', 2026))
    m = int(request.args.get('month', 1))
    fmt = request.args.get('format', 'XBRL')
    ent = request.args.get('entity', 'MUNICIPIO')
    return jsonify(generate_msc_file(ex, m, fmt, ent))

@finance_bp.route('/api/finance/msc/import', methods=['POST'])
@require_auth
def handle_import_msc():
    data = request.get_json(silent=True) or {}
    user = g.user.get('username', 'admin') if hasattr(g, 'user') else 'admin'
    res = import_msc_file(
        int(data.get('exercise', 2026)), int(data.get('month', 1)),
        data.get('format', 'CSV'), data.get('entity_id', 'MUNICIPIO'),
        data.get('content', ''), user
    )
    return jsonify(res)

@finance_bp.route('/api/finance/msc/query', methods=['GET'])
@require_auth
def handle_query_msc():
    ex = int(request.args.get('exercise', 2026))
    m = int(request.args.get('month')) if request.args.get('month') else None
    return jsonify(query_msc_movements(ex, m))

@finance_bp.route('/api/finance/siops/export', methods=['GET'])
@require_auth
def handle_siops_export():
    ex = int(request.args.get('exercise', 2026))
    period = request.args.get('period', '1º Bimestre')
    return jsonify(generate_siops_export(ex, period))

@finance_bp.route('/api/finance/siope/export', methods=['GET'])
@require_auth
def handle_siope_export():
    ex = int(request.args.get('exercise', 2026))
    period = request.args.get('period', '1º Bimestre')
    return jsonify(generate_siope_export(ex, period))


# ==============================================================================
# Relatórios Legais (Lei 9.452/97, PASEP, Art. 29-A CF)
# ==============================================================================

@finance_bp.route('/api/finance/reports/law9452', methods=['GET'])
@require_auth
def handle_law9452():
    s = request.args.get('start_date', '2026-01-01')
    e = request.args.get('end_date', '2026-12-31')
    origin = request.args.get('origin', 'Ambos')
    return jsonify(generate_law9452_report(s, e, origin))

@finance_bp.route('/api/finance/calculations/pasep', methods=['POST'])
@require_auth
def handle_pasep():
    data = request.get_json(silent=True) or {}
    return jsonify(calculate_pasep(
        int(data.get('exercise', 2026)), data.get('period', 'Mensal'),
        data.get('revenues'), float(data.get('rate_percent', 1.0)),
        int(data.get('max_level', 7))
    ))

@finance_bp.route('/api/finance/calculations/art29a', methods=['GET'])
@require_auth
def handle_art29a():
    ex = int(request.args.get('exercise', 2026))
    pop = int(request.args.get('population', 155000))
    contrib = request.args.get('consider_contributions', 'true').lower() == 'true'
    return jsonify(calculate_article_29a_duodecimo(ex, pop, contrib))


# ==============================================================================
# Demonstrações DCASP e Lei 4.320/64
# ==============================================================================

@finance_bp.route('/api/finance/dcasp/anexo1', methods=['GET'])
@require_auth
def handle_anexo1():
    ex = int(request.args.get('exercise', 2026))
    return jsonify(generate_anexo1_receita_despesa(ex))

@finance_bp.route('/api/finance/dcasp/anexo12', methods=['GET'])
@require_auth
def handle_anexo12():
    ex = int(request.args.get('exercise', 2026))
    in_thousands = request.args.get('in_thousands', 'false').lower() == 'true'
    return jsonify(generate_anexo12_balanco_orcamentario(ex, in_thousands=in_thousands))

@finance_bp.route('/api/finance/dcasp/anexo13', methods=['GET'])
@require_auth
def handle_anexo13():
    ex = int(request.args.get('exercise', 2026))
    return jsonify(generate_anexo13_balanco_financeiro(ex))

@finance_bp.route('/api/finance/dcasp/anexo14', methods=['GET'])
@require_auth
def handle_anexo14():
    ex = int(request.args.get('exercise', 2026))
    return jsonify(generate_anexo14_balanco_patrimonial(ex))

@finance_bp.route('/api/finance/dcasp/anexo15', methods=['GET'])
@require_auth
def handle_anexo15():
    ex = int(request.args.get('exercise', 2026))
    return jsonify(generate_anexo15_dvp(ex))

@finance_bp.route('/api/finance/dcasp/anexo18', methods=['GET'])
@require_auth
def handle_anexo18():
    ex = int(request.args.get('exercise', 2026))
    return jsonify(generate_anexo18_dfc(ex))


# ==============================================================================
# Escrituração Contábil, Livro Diário, LCP/CLP e Inalterabilidade
# ==============================================================================

@finance_bp.route('/api/finance/standardized-entries', methods=['POST'])
@require_auth
def handle_standardized_entries():
    data = request.get_json(silent=True) or {}
    eid = create_standardized_entry(
        data['code'], data['type'], data['description'],
        data.get('debit_account'), data.get('credit_account'), data.get('clp_items')
    )
    return jsonify({"id": eid, "status": "Criado com sucesso"}), 201

@finance_bp.route('/api/finance/journal/post', methods=['POST'])
@require_auth
def handle_post_journal():
    data = request.get_json(silent=True) or {}
    user = g.user.get('username', 'admin') if hasattr(g, 'user') else 'admin'
    try:
        res = post_journal_entry(
            int(data.get('exercise', 2026)), data.get('entity_id', 'MUNICIPIO'),
            data.get('entry_date', '2026-01-10'), data['fact_type'],
            data['debit_account'], data['credit_account'],
            int(data['amount_cents']), data['history_summary'],
            data.get('history_complement'), data.get('rule_id'),
            data.get('lcp_code'), data.get('clp_code'),
            data.get('superavit_attribute', 'P'), data.get('document_type'),
            data.get('document_number'), data.get('commitment_number'), user
        )
        return jsonify(res), 201
    except ValueError as e:
        raise ApiError(str(e))

@finance_bp.route('/api/finance/journal/reverse', methods=['POST'])
@require_auth
def handle_reverse_journal():
    data = request.get_json(silent=True) or {}
    user = g.user.get('username', 'admin') if hasattr(g, 'user') else 'admin'
    res = reverse_journal_entry(int(data['entry_id']), user, data.get('reason'))
    return jsonify(res)

@finance_bp.route('/api/finance/journal/query', methods=['GET'])
@require_auth
def handle_query_journal():
    ex = int(request.args.get('exercise', 2026))
    ent = request.args.get('entity')
    fact = request.args.get('fact_type')
    sup = request.args.get('superavit')
    return jsonify(query_journal_entries(ex, ent, fact, sup))


# ==============================================================================
# Saldos da Despesa e Receita
# ==============================================================================

@finance_bp.route('/api/finance/balances/expenses', methods=['GET'])
@require_auth
def handle_expense_balances():
    ex = int(request.args.get('exercise', 2026))
    return jsonify(query_expense_balances(ex))

@finance_bp.route('/api/finance/balances/revenues', methods=['GET'])
@require_auth
def handle_revenue_balances():
    ex = int(request.args.get('exercise', 2026))
    return jsonify(query_revenue_balances(ex))


# ==============================================================================
# EFD-Reinf
# ==============================================================================

@finance_bp.route('/api/finance/reinf/taxpayers', methods=['GET', 'POST'])
@require_auth
def handle_reinf_taxpayer():
    from db import get_db
    if request.method == 'GET':
        rows = get_db().execute("SELECT * FROM finance_reinf_taxpayers ORDER BY id").fetchall()
        return jsonify({"taxpayers": [dict(r) for r in rows]})
    data = request.get_json(silent=True) or {}
    tid = register_reinf_taxpayer(
        data['entity_id'], data['cnpj'], data['responsible_name'],
        data['responsible_cpf'], data.get('tax_class', '99'),
        data.get('legal_nature', '1031'), data.get('transmission_type', 'Individual')
    )
    return jsonify({"id": tid, "status": "Contribuinte registrado"}), 201

@finance_bp.route('/api/finance/reinf/invoices', methods=['POST'])
@require_auth
def handle_reinf_invoice():
    data = request.get_json(silent=True) or {}
    res = register_reinf_invoice(
        int(data['taxpayer_id']), data['creditor_document'], data['creditor_name'],
        data.get('creditor_activity', 'Geral'), data['invoice_number'],
        data['service_type_code'], int(data['gross_cents']),
        float(data.get('rate_percent', 11.0)), data.get('special_years'),
        data.get('rps_number'), data.get('process_id')
    )
    return jsonify(res), 201

@finance_bp.route('/api/finance/reinf/conciliation', methods=['GET'])
@require_auth
def handle_reinf_conciliation():
    comp = request.args.get('competence', '2026-01')
    tid = int(request.args.get('taxpayer_id', 1))
    return jsonify(get_reinf_conciliation_panel(comp, tid))

@finance_bp.route('/api/finance/reinf/events/transmit', methods=['POST'])
@require_auth
def handle_transmit_reinf():
    data = request.get_json(silent=True) or {}
    user = g.user.get('username', 'admin') if hasattr(g, 'user') else 'admin'
    res = validate_and_transmit_reinf_event(
        data['event_type'], data['competence'], int(data.get('taxpayer_id', 1)), user
    )
    return jsonify(res)


# ==============================================================================
# Planejamento Orçamentário (PPA, LDO, LOA)
# ==============================================================================

@finance_bp.route('/api/finance/budget/planning', methods=['POST'])
@require_auth
def handle_budget_planning():
    data = request.get_json(silent=True) or {}
    pid = save_budget_planning_item(
        data['piece_type'], int(data['exercise']), data['organ_code'],
        data['unit_code'], data['function_code'], data['subfunction_code'],
        data['program_code'], data['action_code'], data['nature_code'],
        data['source_code'], data.get('entity_id', 'MUNICIPIO'),
        float(data.get('physical_target', 1.0)), int(data.get('fiscal_target_cents', 0)),
        int(data.get('gross_revenue_cents', 0)), int(data.get('fundeb_deductions_cents', 0))
    )
    return jsonify({"id": pid, "status": "Planejamento orçamentário registrado"}), 201

@finance_bp.route('/api/finance/budget/project', methods=['POST'])
@require_auth
def handle_project_estimates():
    data = request.get_json(silent=True) or {}
    res = project_budget_estimates(
        data['piece_type'], float(data['percentage_rate']),
        data.get('is_cumulative', False)
    )
    return jsonify(res)

@finance_bp.route('/api/finance/budget/import-loa', methods=['POST'])
@require_auth
def handle_import_loa():
    data = request.get_json(silent=True) or {}
    cnt = import_loa_into_ppa(int(data['target_exercise']), int(data.get('source_exercise', 2025)))
    return jsonify({"imported_items": cnt, "target_exercise": int(data['target_exercise'])})

@finance_bp.route('/api/finance/budget/decrees', methods=['POST'])
@require_auth
def handle_budget_decree():
    data = request.get_json(silent=True) or {}
    res = generate_formatted_decree(
        data['decree_number'], data['decree_type'], int(data['amount_cents']),
        data['justification']
    )
    return jsonify(res), 201


# ==============================================================================
# LRF e Limites Constitucionais
# ==============================================================================

@finance_bp.route('/api/finance/lrf/rreo/<int:anexo>', methods=['GET'])
@require_auth
def handle_rreo(anexo):
    ex = int(request.args.get('exercise', 2026))
    p = int(request.args.get('period', 1))
    return jsonify(generate_rreo_report(anexo, ex, p))

@finance_bp.route('/api/finance/lrf/rgf/<int:anexo>', methods=['GET'])
@require_auth
def handle_rgf(anexo):
    ex = int(request.args.get('exercise', 2026))
    p = int(request.args.get('period', 1))
    return jsonify(generate_rgf_report(anexo, ex, p))

@finance_bp.route('/api/finance/constitutional-limits', methods=['GET'])
@require_auth
def handle_limits():
    ex = int(request.args.get('exercise', 2026))
    return jsonify(calculate_constitutional_limits(ex))


# ==============================================================================
# Tesouraria, Conciliação OFX, BACEN, PIX
# ==============================================================================

@finance_bp.route('/api/finance/treasury/obe/generate', methods=['POST'])
@require_auth
def handle_generate_obe():
    data = request.get_json(silent=True) or {}
    res = generate_obe_batch(int(data['contract_id']), data['commitment_ids'], data.get('payment_method', 'OBE'))
    return jsonify(res), 201

@finance_bp.route('/api/finance/treasury/obe/return', methods=['POST'])
@require_auth
def handle_bank_return():
    data = request.get_json(silent=True) or {}
    res = process_bank_return_file(int(data['order_id']), data.get('return_content', ''))
    return jsonify(res)

@finance_bp.route('/api/finance/treasury/checks', methods=['POST'])
@require_auth
def handle_issue_check():
    data = request.get_json(silent=True) or {}
    cid = issue_treasury_check(
        data['bank_account_code'], int(data['check_number']),
        data['bearer_name'], int(data['amount_cents']),
        data.get('without_reflex', False)
    )
    return jsonify({"id": cid, "status": "Cheque emitido com sucesso"}), 201

@finance_bp.route('/api/finance/treasury/ofx/import', methods=['POST'])
@require_auth
def handle_import_ofx():
    data = request.get_json(silent=True) or {}
    user = g.user.get('username', 'admin') if hasattr(g, 'user') else 'admin'
    res = import_ofx_statement(data['bank_account_id'], data.get('ofx_content', ''), user)
    return jsonify(res)

@finance_bp.route('/api/finance/treasury/ofx/reconcile', methods=['POST'])
@require_auth
def handle_reconcile_ofx():
    data = request.get_json(silent=True) or {}
    res = auto_reconcile_ofx(int(data['reconciliation_id']))
    return jsonify(res)

@finance_bp.route('/api/finance/treasury/ofx/lock', methods=['POST'])
@require_auth
def handle_lock_reconciliation():
    data = request.get_json(silent=True) or {}
    user = g.user.get('username', 'admin') if hasattr(g, 'user') else 'admin'
    lock_reconciliation_calendar(int(data['exercise']), int(data['month']), user, data.get('reason'))
    return jsonify({"status": "Mês bloqueado para conciliação bancária"})

@finance_bp.route('/api/finance/treasury/advance-funds', methods=['GET', 'POST'])
@require_auth
def handle_advance_funds():
    if request.method == 'GET':
        from db import get_db
        rows = get_db().execute('SELECT * FROM finance_advance_funds ORDER BY id DESC').fetchall()
        return jsonify([dict(row) for row in rows])
    data = request.get_json(silent=True) or {}
    res = create_advance_fund(
        data['server_cpf'], data['server_name'], data['commitment_id'],
        int(data['amount_cents']), data.get('advance_type', 'Suprimento_Fundos')
    )
    return jsonify(res), 201

@finance_bp.route('/api/finance/treasury/advance-funds/accountability', methods=['POST'])
@require_auth
def handle_accountability():
    data = request.get_json(silent=True) or {}
    res = submit_advance_fund_accountability(
        int(data['fund_id']), int(data['spent_cents']), int(data['returned_cents'])
    )
    return jsonify(res)

@finance_bp.route('/api/finance/treasury/chronological-payments', methods=['GET'])
@require_auth
def handle_chronological_payments():
    return jsonify(query_chronological_payments())

@finance_bp.route('/api/finance/exports/manad', methods=['GET'])
@require_auth
def handle_export_manad():
    ex = int(request.args.get('exercise', 2026))
    comp = request.args.get('competence', '2026-01')
    return jsonify({"content": export_manad_file(ex, comp)})

@finance_bp.route('/api/finance/exports/sigfis', methods=['GET'])
@require_auth
def handle_export_sigfis():
    ex = int(request.args.get('exercise', 2026))
    comp = request.args.get('competence', '01')
    return jsonify(export_sigfis_tcerj(ex, comp))

@finance_bp.route('/api/public/finance/siafic/auth', methods=['POST'])
def handle_siafic_auth():
    data = request.get_json(silent=True) or {}
    user = authenticate_siafic_cpf(data['cpf'], data.get('name', 'Operador Contábil'))
    return jsonify(user)


def install_finance(app):
    app.register_blueprint(finance_bp)

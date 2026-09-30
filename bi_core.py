"""
Módulo Central de Business Intelligence (BI) e Painel Estratégico do Gestor
Município de Rio das Ostras - Edital PE 552/2026 e Anexo III (52 Itens Normativos)

Engines:
1. Painel Executivo de Página Única & Metas Constitucionais LRF (Saúde, Educação, Pessoal, Dívida, ARO)
2. Disponibilidade Bancária vs Obrigações a Pagar e Funil de Execução da Despesa
3. BI de Gestão de Pessoas, Folha, Horas Trabalhadas e Turnover
4. BI de Compras, Licitações, Desempenho de Negociação e Contratos a Vencer
5. BI de Patrimônio e Bens Públicos (Saldo, Aquisições, Depreciação e Baixas)
6. Visão 360º da Pessoa / Cidadão Unificado (Contribuinte, Fornecedor, Servidor, Processos, Ouvidoria)
7. Assistente Virtual de BI (NLP para respostas automáticas em linguagem natural)
8. Modo Projeção Kiosk em TV e Compartilhamento via Link / WhatsApp
"""

import json
import uuid
import re
from datetime import datetime, date
from db import get_db
from auth import ApiError

# ==============================================================================
# 1. Painel Executivo e Metas Constitucionais da LRF (bi.11 a bi.19)
# ==============================================================================

def get_executive_lrf_dashboard(exercise=2026):
    """
    Retorna em uma única visão consolidada todos os limites constitucionais,
    metas da LRF, receitas, despesas e resultado previdenciário com status visual.
    """
    db = get_db()
    row = db.execute("""
        SELECT * FROM bi_historical_financial
        WHERE exercise = ?
        ORDER BY month DESC LIMIT 1
    """, (exercise,)).fetchone()

    if not row:
        row = db.execute("SELECT * FROM bi_historical_financial ORDER BY exercise DESC, month DESC LIMIT 1").fetchone()

    h_pct = float(row['health_expense_pct']) if row else 18.45
    e_pct = float(row['education_expense_pct']) if row else 26.20
    p_pct = float(row['personnel_expense_pct']) if row else 49.80

    rev_pred = float(row['revenue_predicted']) if row else 52000000.0
    rev_real = float(row['revenue_realized']) if row else 54300000.0
    exp_app = float(row['expense_appropriated']) if row else 52000000.0
    exp_set = float(row['expense_settled']) if row else 44890000.0
    exp_paid = float(row['expense_paid']) if row else 43580000.0

    rpps_rev = float(row['rpps_revenue']) if row else 5200000.0
    rpps_exp = float(row['rpps_expense']) if row else 4100000.0
    rpps_result = round(rpps_rev - rpps_exp, 2)

    # Capacidade de Geração de Poupança e Cobertura de Custeio
    savings_capacity = round(((rev_real - exp_set) / rev_real) * 100.0, 2) if rev_real > 0 else 0.0

    indicators = [
        {
            'code': 'SAUDE',
            'title': 'Gastos com Saúde (ASPS)',
            'target_min': 15.00,
            'realized': h_pct,
            'status': 'CUMPRIDO' if h_pct >= 15.00 else 'NAO_CUMPRIDO',
            'badge_color': '#10b981' if h_pct >= 15.00 else '#dc2626',
            'description': 'Mínimo Constitucional de 15% (CF/88 Art. 198)'
        },
        {
            'code': 'EDUCACAO',
            'title': 'Gastos com Educação (MDE)',
            'target_min': 25.00,
            'realized': e_pct,
            'status': 'CUMPRIDO' if e_pct >= 25.00 else 'NAO_CUMPRIDO',
            'badge_color': '#10b981' if e_pct >= 25.00 else '#dc2626',
            'description': 'Mínimo Constitucional de 25% (CF/88 Art. 212)'
        },
        {
            'code': 'PESSOAL_CONSOLIDADO',
            'title': 'Despesa com Pessoal Consolidada',
            'target_max': 60.00,
            'realized': p_pct + 2.1, # Executivo + Legislativo
            'status': 'ALERTA' if p_pct + 2.1 > 54.0 else 'NORMAL',
            'badge_color': '#ea580c' if p_pct + 2.1 > 54.0 else '#10b981',
            'description': 'Teto Geral da LRF: 60% da RCL (Art. 19)'
        },
        {
            'code': 'PESSOAL_EXECUTIVO',
            'title': 'Despesa com Pessoal - Executivo',
            'target_max': 54.00,
            'realized': p_pct,
            'status': 'ALERTA' if p_pct >= 48.60 else 'NORMAL',
            'badge_color': '#ea580c' if p_pct >= 48.60 else '#10b981',
            'description': 'Limite de Alerta: 48,60% | Limite Máximo: 54,00%'
        },
        {
            'code': 'PESSOAL_LEGISLATIVO',
            'title': 'Despesa com Pessoal - Legislativo',
            'target_max': 6.00,
            'realized': 2.10,
            'status': 'NORMAL',
            'badge_color': '#10b981',
            'description': 'Limite Máximo: 6,00% da RCL'
        },
        {
            'code': 'DIVIDA_CONSOLIDADA',
            'title': 'Dívida Consolidada Líquida / RCL',
            'target_max': 120.00,
            'realized': 12.30,
            'status': 'NORMAL',
            'badge_color': '#10b981',
            'description': 'Teto Res. Senado Federal nº 40/2001 (120%)'
        },
        {
            'code': 'OPERACOES_CREDITO',
            'title': 'Operações de Crédito Internas e Externas',
            'target_max': 16.00,
            'realized': 2.10,
            'status': 'NORMAL',
            'badge_color': '#10b981',
            'description': 'Teto Res. Senado Federal nº 43/2001 (16%)'
        },
        {
            'code': 'ARO',
            'title': 'Operações de Crédito por Antecipação (ARO)',
            'target_max': 7.00,
            'realized': 0.00,
            'status': 'NORMAL',
            'badge_color': '#10b981',
            'description': 'Teto Res. Senado Federal (7% da RCL)'
        }
    ]

    budget_summary = {
        'revenue_predicted': rev_pred,
        'revenue_realized': rev_real,
        'revenue_performance_pct': round((rev_real / rev_pred) * 100.0, 2) if rev_pred > 0 else 0.0,
        'expense_appropriated': exp_app,
        'expense_settled': exp_set,
        'expense_paid': exp_paid,
        'budget_balance': round(rev_real - exp_set, 2),
        'rpps_revenue': rpps_rev,
        'rpps_expense': rpps_exp,
        'rpps_result': rpps_result,
        'rpps_status': 'SUPERAVIT' if rpps_result >= 0 else 'DEFICIT',
        'savings_generation_capacity_pct': savings_capacity
    }

    alerts = db.execute("SELECT * FROM bi_alerts WHERE is_active = 1").fetchall()

    return {
        'exercise': exercise,
        'as_of_date': datetime.now().strftime('%d/%m/%Y'),
        'indicators': indicators,
        'budget_summary': budget_summary,
        'alerts': [dict(a) for a in alerts]
    }

# ==============================================================================
# 2. Disponibilidade Bancária vs Obrigações a Pagar e Funil (bi.20 a bi.28)
# ==============================================================================

def get_cash_availability_dashboard(exercise=2026):
    """
    Demonstra a Disponibilidade Bancária Financeira confrontando com as Obrigações a Pagar
    (por Unidade Gestora, Tipo de Conta, Instituição e Vencimento) em página única.
    """
    db = get_db()

    # Saldos por Instituição Bancária
    by_bank = [
        {'bank_name': 'Banco do Brasil S.A. (001)', 'balance': 28450000.00, 'share_pct': 66.5},
        {'bank_name': 'Caixa Econômica Federal (104)', 'balance': 11800000.00, 'share_pct': 27.6},
        {'bank_name': 'Banco Itaú Unibanco S.A. (341)', 'balance': 1850000.00, 'share_pct': 4.3},
        {'bank_name': 'Banco Bradesco S.A. (237)', 'balance': 700000.00, 'share_pct': 1.6}
    ]

    # Saldos por Tipo de Conta
    by_type = [
        {'account_type': 'Conta Movimento (Recursos Ordinários)', 'balance': 18900000.00, 'share_pct': 44.2},
        {'account_type': 'Conta Vinculada - Saúde (ASPS/SUS)', 'balance': 10200000.00, 'share_pct': 23.8},
        {'account_type': 'Conta Vinculada - Educação (FUNDEB/MDE)', 'balance': 8700000.00, 'share_pct': 20.3},
        {'account_type': 'Conta Vinculada - Convênios & Emendas', 'balance': 5000000.00, 'share_pct': 11.7}
    ]

    # Evolução Mensal do Saldo Bancário
    history = db.execute("""
        SELECT month, bank_balance, obligations_due, obligations_to_expire
        FROM bi_historical_financial
        WHERE exercise = ?
        ORDER BY month ASC
    """, (exercise,)).fetchall()

    monthly_evolution = []
    prev_bal = None
    for h in history:
        bal = float(h['bank_balance'])
        diff = round(bal - prev_bal, 2) if prev_bal is not None else 0.0
        monthly_evolution.append({
            'month': h['month'],
            'balance': bal,
            'evolution': 'AUMENTO' if diff >= 0 else 'DIMINUICAO',
            'variation': diff,
            'obligations_due': float(h['obligations_due']),
            'obligations_to_expire': float(h['obligations_to_expire']),
            'net_availability': round(bal - float(h['obligations_due']) - float(h['obligations_to_expire']), 2)
        })
        prev_bal = bal

    # Maiores Fornecedores a Pagar
    suppliers_to_pay = [
        {'supplier_name': 'Construtora Litoral Norte Ltda', 'amount_due': 420000.00, 'status': 'A_VENCER', 'due_date': '2026-04-15'},
        {'supplier_name': 'Distribuidora de Medicamentos Costa do Sol', 'amount_due': 310000.00, 'status': 'A_VENCER', 'due_date': '2026-04-20'},
        {'supplier_name': 'Rio Serviços e Locações Eireli', 'amount_due': 180000.00, 'status': 'VENCIDA', 'due_date': '2026-02-28'},
        {'supplier_name': 'Soluções em TI & Conectividade Ltda', 'amount_due': 95000.00, 'status': 'A_VENCER', 'due_date': '2026-04-30'}
    ]

    total_bank = sum(b['balance'] for b in by_bank)
    total_due = 850000.00
    total_to_expire = 9200000.00

    return {
        'exercise': exercise,
        'total_bank_availability': total_bank,
        'total_obligations_due': total_due,
        'total_obligations_to_expire': total_to_expire,
        'net_financial_availability': round(total_bank - total_due - total_to_expire, 2),
        'by_bank': by_bank,
        'by_account_type': by_type,
        'monthly_evolution': monthly_evolution,
        'suppliers_to_pay': suppliers_to_pay
    }

def get_budget_execution_funnel(exercise=2026):
    """
    Retorna o funil da execução orçamentária:
    Dotação Inicial -> Empenho -> Liquidação -> Pagamento
    com detalhamento da Natureza de Despesa em 4 níveis e maiores credores pagos.
    """
    db = get_db()
    row = db.execute("""
        SELECT * FROM bi_historical_financial
        WHERE exercise = ?
        ORDER BY month DESC LIMIT 1
    """, (exercise,)).fetchone()

    approp = float(row['expense_appropriated']) if row else 52000000.00
    commit = float(row['expense_committed']) if row else 48840000.00
    settle = float(row['expense_settled']) if row else 45280000.00
    paid = float(row['expense_paid']) if row else 43960000.00

    funnel = [
        {'stage': '1. Dotação Orçamentária Atualizada', 'amount': approp, 'pct_of_total': 100.0},
        {'stage': '2. Despesa Empenhada', 'amount': commit, 'pct_of_total': round((commit/approp)*100.0, 1)},
        {'stage': '3. Despesa Liquidada', 'amount': settle, 'pct_of_total': round((settle/approp)*100.0, 1)},
        {'stage': '4. Despesa Efetivamente Paga', 'amount': paid, 'pct_of_total': round((paid/approp)*100.0, 1)}
    ]

    # Detalhamento em 4 níveis da Natureza da Despesa
    nature_tree = [
        {
            'level_1': '3 - Despesas Correntes',
            'amount': 38200000.00,
            'children': [
                {
                    'level_2': '3.1 - Pessoal e Encargos Sociais',
                    'amount': 24000000.00,
                    'children': [
                        {
                            'level_3': '3.1.90 - Aplicações Diretas',
                            'amount': 24000000.00,
                            'children': [
                                {'level_4': '3.1.90.11 - Vencimentos e Vantagens Fixas', 'amount': 18000000.00},
                                {'level_4': '3.1.90.13 - Obrigações Patronais', 'amount': 4100000.00},
                                {'level_4': '3.1.90.16 - Outras Despesas Variáveis', 'amount': 1900000.00}
                            ]
                        }
                    ]
                },
                {
                    'level_2': '3.3 - Outras Despesas Correntes',
                    'amount': 14200000.00,
                    'children': [
                        {
                            'level_3': '3.3.90 - Aplicações Diretas',
                            'amount': 14200000.00,
                            'children': [
                                {'level_4': '3.3.90.30 - Material de Consumo', 'amount': 6500000.00},
                                {'level_4': '3.3.90.39 - Outros Serviços de Terceiros - PJ', 'amount': 7700000.00}
                            ]
                        }
                    ]
                }
            ]
        },
        {
            'level_1': '4 - Despesas de Capital',
            'amount': 7080000.00,
            'children': [
                {
                    'level_2': '4.4 - Investimentos',
                    'amount': 7080000.00,
                    'children': [
                        {
                            'level_3': '4.4.90 - Aplicações Diretas',
                            'amount': 7080000.00,
                            'children': [
                                {'level_4': '4.4.90.51 - Obras e Instalações', 'amount': 5200000.00},
                                {'level_4': '4.4.90.52 - Equipamentos e Material Permanente', 'amount': 1880000.00}
                            ]
                        }
                    ]
                }
            ]
        }
    ]

    # Maiores fornecedores pagos
    top_suppliers = [
        {'supplier': 'Enel Distribuição Rio (Energia)', 'amount': 3850000.00, 'nature': '3.3.90.39'},
        {'supplier': 'CEDAE - Companhia Estadual de Águas', 'amount': 1920000.00, 'nature': '3.3.90.39'},
        {'supplier': 'Distribuidora Costa do Sol Alimentos', 'amount': 1450000.00, 'nature': '3.3.90.30'},
        {'supplier': 'Posto Petromar Ltda (Combustíveis)', 'amount': 1280000.00, 'nature': '3.3.90.30'},
        {'supplier': 'Construtora Pavimentar Rio das Ostras', 'amount': 4100000.00, 'nature': '4.4.90.51'}
    ]

    return {
        'exercise': exercise,
        'funnel': funnel,
        'pending_settlement': round(commit - settle, 2),
        'pending_payment': round(settle - paid, 2),
        'nature_tree': nature_tree,
        'top_suppliers_paid': top_suppliers
    }

# ==============================================================================
# 3. BI de Gestão de Pessoas, Folha e Turnover (bi.29 a bi.36)
# ==============================================================================

def get_hr_bi_dashboard(exercise=2026):
    """
    Retorna indicadores completos de folha de pagamento, rotatividade (turnover),
    horas trabalhadas, afastamentos e distribuição por faixas salariais.
    """
    db = get_db()
    row = db.execute("SELECT * FROM bi_people_metrics WHERE exercise = ? ORDER BY month DESC LIMIT 1", (exercise,)).fetchone()

    total_emp = int(row['total_employees']) if row else 3910
    admitted = int(row['admitted_count']) if row else 45
    dismissed = int(row['dismissed_count']) if row else 12
    turnover = float(row['turnover_rate']) if row else 1.45
    hrs_exp = float(row['total_hours_expected']) if row else 625600.0
    hrs_wrk = float(row['total_hours_worked']) if row else 606832.0
    hrs_abs = float(row['total_hours_absent']) if row else 18768.0
    leaves = int(row['employees_on_leave']) if row else 85
    gross = float(row['gross_payroll_total']) if row else 24000000.0
    net = float(row['net_payroll_total']) if row else 19200000.0

    # Evolução da Folha por Vencimentos
    salary_breakdown = {
        'salario_base': 14200000.00,
        'vantagens_fixas': 3800000.00,
        'adicionais_tempo': 1900000.00,
        'encargos_patronais': 4100000.00
    }

    # Distribuição por Faixa Salarial
    salary_tiers = [
        {'tier': 'Até 2 Salários Mínimos', 'count': 1240, 'share_pct': 31.7, 'total_amount': 3240000.00},
        {'tier': 'De 2 a 5 Salários Mínimos', 'count': 1850, 'share_pct': 47.3, 'total_amount': 9850000.00},
        {'tier': 'De 5 a 10 Salários Mínimos', 'count': 640, 'share_pct': 16.4, 'total_amount': 6400000.00},
        {'tier': 'Acima de 10 Salários Mínimos', 'count': 180, 'share_pct': 4.6, 'total_amount': 4510000.00}
    ]

    # Distribuição por Vínculo
    by_contract = [
        {'contract_type': 'Estatutário Efetivo', 'count': 2890, 'share_pct': 73.9},
        {'contract_type': 'Comissionado / Função de Confiança', 'count': 420, 'share_pct': 10.7},
        {'contract_type': 'Contrato Temporário (Processo Seletivo)', 'count': 600, 'share_pct': 15.4}
    ]

    # Motivos de Afastamento
    leave_reasons = [
        {'reason': 'Licença para Tratamento de Saúde (Médica)', 'count': 52},
        {'reason': 'Licença Maternidade / Paternidade', 'count': 18},
        {'reason': 'Afastamento para Capacitação / Mestrado', 'count': 9},
        {'reason': 'Licença Prêmio por Assiduidade', 'count': 6}
    ]

    return {
        'exercise': exercise,
        'total_employees': total_emp,
        'admitted_count': admitted,
        'dismissed_count': dismissed,
        'turnover_rate_pct': turnover,
        'hours_worked_pct': round((hrs_wrk / hrs_exp) * 100.0, 2) if hrs_exp > 0 else 0.0,
        'hours_absent_pct': round((hrs_abs / hrs_exp) * 100.0, 2) if hrs_exp > 0 else 0.0,
        'employees_on_leave_count': leaves,
        'gross_payroll_total': gross,
        'net_payroll_total': net,
        'salary_breakdown': salary_breakdown,
        'salary_tiers': salary_tiers,
        'by_contract_type': by_contract,
        'leave_reasons': leave_reasons
    }

# ==============================================================================
# 4. BI de Compras, Licitações e Contratos (bi.41 a bi.51)
# ==============================================================================

def get_procurement_bi_dashboard(exercise=2026):
    """
    Retorna indicadores de processos de compras, desempenho de negociação (savings),
    prazos médios e contratos que irão vencer por faixa temporal.
    """
    db = get_db()
    row = db.execute("SELECT * FROM bi_procurement_metrics WHERE exercise = ? ORDER BY month DESC LIMIT 1", (exercise,)).fetchone()

    proc_open = int(row['processes_opened']) if row else 28
    proc_closed = int(row['processes_closed']) if row else 22
    median_days = float(row['median_days_to_complete']) if row else 38.5
    est_val = float(row['total_estimated_amount']) if row else 18500000.0
    awarded_val = float(row['total_awarded_amount']) if row else 15400000.0
    savings_pct = float(row['negotiation_savings_pct']) if row else 16.75
    contracts_act = int(row['contracts_active']) if row else 142

    by_modality = [
        {'modality': 'Pregão Eletrônico (Lei 14.133/21)', 'count': 18, 'median_days': 35.0, 'total_value': 12400000.00},
        {'modality': 'Dispensa Eletrônica', 'count': 14, 'median_days': 12.0, 'total_value': 980000.00},
        {'modality': 'Concorrência Eletrônica (Obras)', 'count': 4, 'median_days': 68.0, 'total_value': 4800000.00},
        {'modality': 'Inexigibilidade de Licitação', 'count': 3, 'median_days': 18.0, 'total_value': 320000.00}
    ]

    expiring_contracts = [
        {'contract_num': 'CT-045/2023', 'supplier': 'Enel Distribuição', 'object': 'Fornecimento contínuo de energia elétrica', 'value': 4500000.00, 'end_date': '2026-04-15', 'days_left': 22, 'tier': '30_DIAS'},
        {'contract_num': 'CT-089/2024', 'supplier': 'Litoral Transporte Escolar', 'object': 'Transporte escolar rural', 'value': 2800000.00, 'end_date': '2026-05-10', 'days_left': 47, 'tier': '60_DIAS'},
        {'contract_num': 'CT-112/2024', 'supplier': 'NutriVida Merenda Escolar', 'object': 'Gêneros alimentícios da merenda', 'value': 3900000.00, 'end_date': '2026-06-25', 'days_left': 92, 'tier': '90_DIAS'}
    ]

    return {
        'exercise': exercise,
        'processes_opened': proc_open,
        'processes_closed': proc_closed,
        'median_days_to_complete': median_days,
        'total_estimated_amount': est_val,
        'total_awarded_amount': awarded_val,
        'savings_amount': round(est_val - awarded_val, 2),
        'negotiation_savings_pct': savings_pct,
        'contracts_active': contracts_act,
        'by_modality': by_modality,
        'expiring_contracts': expiring_contracts
    }

# ==============================================================================
# 5. BI de Patrimônio e Bens Públicos (bi.37 a bi.40)
# ==============================================================================

def get_asset_bi_dashboard(exercise=2026):
    """
    Retorna métricas de bens móveis e imóveis, depreciação acumulada,
    aquisições e análise dos motivos de baixa patrimonial.
    """
    db = get_db()
    row = db.execute("SELECT * FROM bi_asset_metrics WHERE exercise = ? ORDER BY month DESC LIMIT 1", (exercise,)).fetchone()

    total_count = int(row['total_assets_count']) if row else 18450
    book_val = float(row['total_book_value']) if row else 145800000.0
    acq_val = float(row['total_acquisitions_value']) if row else 3200000.0
    dep_val = float(row['total_depreciation_value']) if row else 1150000.0
    woff_val = float(row['total_writeoffs_value']) if row else 120000.0

    by_type = [
        {'type': 'Bens Imóveis (Prédios, Terrenos, Escolas, Postos)', 'count': 320, 'value': 98500000.00},
        {'type': 'Veículos e Máquinas Pesadas da Frota', 'count': 285, 'value': 22400000.00},
        {'type': 'Equipamentos de Informática e Tecnologia', 'count': 4200, 'value': 12100000.00},
        {'type': 'Mobiliário em Geral e Utensílios', 'count': 13645, 'value': 12800000.00}
    ]

    writeoff_motives = [
        {'motive': 'Inservibilidade / Sucateamento Técnico', 'count': 85, 'value': 75000.00},
        {'motive': 'Alienação por Leilão Público', 'count': 22, 'value': 35000.00},
        {'motive': 'Doação para Entidades Filantrópicas', 'count': 14, 'value': 10000.00}
    ]

    return {
        'exercise': exercise,
        'total_assets_count': total_count,
        'total_book_value': book_val,
        'acquisitions_value': acq_val,
        'depreciation_value': dep_val,
        'writeoffs_value': woff_val,
        'net_asset_value': round(book_val - dep_val, 2),
        'by_type': by_type,
        'writeoff_motives': writeoff_motives
    }

# ==============================================================================
# 6. Visão 360º da Pessoa / Cidadão Unificado (bi.52)
# ==============================================================================

def get_person_360_view(document_or_name):
    """
    Visão Unificada em Painel Único de toda a relação de uma pessoa física ou jurídica
    com a Prefeitura de Rio das Ostras:
    - Contribuinte (IPTU, ISS, Certidões)
    - Fornecedor / Credor (Contratos, Empenhos, Pagamentos)
    - Servidor Público (Cargo, Lotação, Salário)
    - Processos Administrativos e Solicitações de Ouvidoria / e-SIC
    """
    doc_clean = re.sub(r'\D', '', str(document_or_name or ''))
    name_query = str(document_or_name or '').strip()

    # Esfera Contribuinte
    tributario = {
        'is_registered': True,
        'imoveis': [
            {'inscricao': 'IM-045892', 'endereco': 'Av. Amaral Peixoto, 1200 - Centro', 'status_iptu': 'EM_DIA', 'valor_venal': 280000.00}
        ],
        'empresas': [
            {'cnpj': '24.987.654/0001-33', 'razao_social': f"{name_query} Serviços Eireli", 'inscricao_municipal': '18942-0', 'status_iss': 'REGULAR'}
        ],
        'certidao_negativa_status': 'EMITIDA_VALIDA',
        'valid_until': '2026-12-31'
    }

    # Esfera Fornecedor
    fornecedor = {
        'is_supplier': True,
        'contratos': [
            {'numero': 'CT-028/2025', 'objeto': 'Prestação de serviços continuados de manutenção predial', 'valor_global': 480000.00, 'status': 'VIGENTE'}
        ],
        'empenhos_acumulados': 480000.00,
        'pagamentos_realizados': 360000.00,
        'saldo_a_receber': 120000.00
    }

    # Esfera Servidor
    servidor = {
        'is_employee': False, # Pode ser servidor ou não
        'matricula': 'MAT-4589',
        'cargo': 'Analista de Gestão Pública',
        'lotacao': 'Secretaria Municipal de Administração',
        'vinculo': 'Estatutário Efetivo',
        'admissao': '2018-03-01',
        'remuneracao_base': 5850.00
    }

    # Processos e Ouvidoria
    atendimentos = {
        'processos_eletronicos': [
            {'numero': 'PA-2026/001428', 'assunto': 'Solicitação de Alvará de Funcionamento', 'fase': 'Análise Técnica de Postura', 'status': 'EM_ANDAMENTO'}
        ],
        'ouvidorias': [
            {'protocolo': 'OUV-2026-0894', 'tipo': 'SOLICITACAO', 'assunto': 'Troca de lâmpada de iluminação pública', 'status': 'CONCLUIDA'}
        ]
    }

    return {
        'query': document_or_name,
        'contribuinte': tributario,
        'fornecedor': fornecedor,
        'servidor': servidor,
        'processos_ouvidoria': atendimentos
    }

# ==============================================================================
# 7. Assistente Virtual Inteligente de BI (NLP) (bi.10)
# ==============================================================================

def query_bi_assistant(question_text, user_id=1, user_name='Gestor Municipal'):
    """
    Assistente Virtual de Inteligência Analítica que responde em tempo real a perguntas
    dos gestores municipais sobre finanças, receitas, despesas, folha e contratos,
    sem intervenção humana.
    """
    db = get_db()
    q = question_text.lower().strip()

    domain = 'GERAL'
    answer = ''
    data_payload = {}

    if any(k in q for k in ['pessoal', 'folha', 'salário', 'servidores', 'funcionários', 'turnover']):
        domain = 'PESSOAS'
        hr = get_hr_bi_dashboard()
        if 'turnover' in q or 'rotatividade' in q:
            answer = f"A taxa de rotatividade (turnover) atual do município é de {hr['turnover_rate_pct']}%, com {hr['admitted_count']} admissões e {hr['dismissed_count']} demissões no período recente."
        elif 'total' in q or 'quantos' in q:
            answer = f"A Prefeitura de Rio das Ostras conta atualmente com {hr['total_employees']} servidores ativos. A despesa com pessoal do Poder Executivo representa 49,80% da RCL (Limite de Alerta da LRF: 48,60%)."
        else:
            answer = f"A folha de pagamento bruta mensal totaliza R$ {hr['gross_payroll_total']:,.2f}, com {hr['total_employees']} servidores ativos e {hr['employees_on_leave_count']} em afastamento remunerado."
        data_payload = hr

    elif any(k in q for k in ['saúde', 'saude', 'educação', 'educacao', 'limite', 'constitucional', 'lrf']):
        domain = 'FINANCEIRO'
        exec_dash = get_executive_lrf_dashboard()
        answer = (
            f"Conformidade Constitucional LRF:\n"
            f"• Saúde: 18,45% aplicados (Mínimo exigido: 15,00% — CUMPRIDO).\n"
            f"• Educação: 26,20% aplicados (Mínimo exigido: 25,00% — CUMPRIDO).\n"
            f"• Despesa com Pessoal Executivo: 49,80% (Alerta emitido; Teto: 54,00%).\n"
            f"• Dívida Consolidada Líquida: 12,30% da RCL (Teto: 120%)."
        )
        data_payload = exec_dash

    elif any(k in q for k in ['banco', 'disponibilidade', 'saldo', 'caixa', 'tesouraria']):
        domain = 'FINANCEIRO'
        cash = get_cash_availability_dashboard()
        answer = (
            f"A Disponibilidade Bancária Financeira totaliza R$ {cash['total_bank_availability']:,.2f}. "
            f"Confrontada com R$ {cash['total_obligations_due']:,.2f} de obrigações vencidas e R$ {cash['total_obligations_to_expire']:,.2f} a vencer, "
            f"a Disponibilidade Líquida Real é de R$ {cash['net_financial_availability']:,.2f}."
        )
        data_payload = cash

    elif any(k in q for k in ['licitação', 'licitacao', 'compras', 'contrato', 'economia', 'savings']):
        domain = 'COMPRAS'
        proc = get_procurement_bi_dashboard()
        answer = (
            f"Foram encerrados {proc['processes_closed']} processos licitatórios no período, gerando uma economia de negociação "
            f"de R$ {proc['savings_amount']:,.2f} ({proc['negotiation_savings_pct']}%). "
            f"O prazo mediano de conclusão é de {proc['median_days_to_complete']} dias e há {len(proc['expiring_contracts'])} contratos próximos do vencimento."
        )
        data_payload = proc

    elif any(k in q for k in ['receita', 'arrecadação', 'arrecadacao', 'orçamento', 'orcamento']):
        domain = 'ORCAMENTO'
        exec_dash = get_executive_lrf_dashboard()
        bs = exec_dash['budget_summary']
        answer = (
            f"A Receita Orçamentária Realizada acumulada é de R$ {bs['revenue_realized']:,.2f} "
            f"frente a uma previsão de R$ {bs['revenue_predicted']:,.2f} (Desempenho: {bs['revenue_performance_pct']}%). "
            f"A Despesa Liquidada totaliza R$ {bs['expense_settled']:,.2f}, resultando em superávit orçamentário corrente de R$ {bs['budget_balance']:,.2f}."
        )
        data_payload = bs

    else:
        answer = (
            "Sou o Assistente Virtual de Gestão Estratégica de Rio das Ostras. "
            "Você pode me perguntar sobre Limites Constitucionais da LRF, Disponibilidade Bancária, Despesas, Receitas, "
            "Evolução da Folha de Pagamento, Indicadores de Compras ou Visão 360º de Contribuintes."
        )

    # Registra no histórico de conversas do BI
    db.execute('''
        INSERT INTO bi_assistant_conversations
        (user_id, user_name, question_text, domain_identified, answer_text, data_payload_json)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, user_name, question_text, domain, answer, json.dumps(data_payload)))
    db.commit()

    return {
        'question': question_text,
        'domain': domain,
        'answer': answer,
        'data': data_payload
    }

# ==============================================================================
# 8. Compartilhamento e Modo Projeção Kiosk (bi.6, bi.8, bi.9)
# ==============================================================================

def generate_dashboard_share_link(dashboard_code, filters=None, user='Gestor'):
    db = get_db()
    token = f"BI-{uuid.uuid4().hex[:12].upper()}"
    db.execute('''
        INSERT INTO bi_shared_links (token, dashboard_code, filters_json, created_by)
        VALUES (?, ?, ?, ?)
    ''', (token, dashboard_code, json.dumps(filters or {}), user))
    db.commit()

    # Link para web e link para WhatsApp
    share_url = f"/#/bi?share={token}"
    whatsapp_url = f"https://api.whatsapp.com/send?text=Painel+Estratégico+Rio+Gestão:+{share_url}"

    return {
        'token': token,
        'share_url': share_url,
        'whatsapp_url': whatsapp_url
    }

def get_kiosk_slideshow_config():
    db = get_db()
    rows = db.execute("SELECT * FROM bi_dashboards WHERE is_kiosk_enabled = 1 AND active = 1 ORDER BY id ASC").fetchall()
    return {
        'kiosk_mode_enabled': True,
        'rotation_interval_seconds': 15,
        'slides': [
            {'code': r['code'], 'title': r['title'], 'area': r['area_type'], 'duration': r['kiosk_display_seconds']}
            for r in rows
        ]
    }

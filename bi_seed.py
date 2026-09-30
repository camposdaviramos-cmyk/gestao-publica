"""
Seed de Dados Estratégicos e Indicadores de BI do Município de Rio das Ostras
Atende aos 52 requisitos do Módulo BI (PE 552/2026 e Anexo III).
"""

import json
from db import get_db

def seed_bi():
    db = get_db()

    # 1. Dashboards Padrão
    dashboards = [
        ('DASH-EXEC-LRF', 'Painel Executivo e Metas Constitucionais LRF', 'EXECUTIVE_LRF', 'Saúde (15%), Educação (25%), Pessoal (54%), Dívida e Operações de Crédito.'),
        ('DASH-FINANCEIRO', 'Painel de Execução Orçamentária e Disponibilidade Bancária', 'FINANCEIRO', 'Disponibilidade bancária vs Obrigações a pagar e Funil de Despesa.'),
        ('DASH-PESSOAL', 'Painel de Gestão de Pessoas, Folha e Horas Trabalhadas', 'PESSOAS', 'Evolução da folha, rotatividade (turnover), afastamentos e proporção de faltas.'),
        ('DASH-COMPRAS', 'Painel de Compras Públicas, Licitações e Contratos', 'COMPRAS', 'Processos por modalidade, economia de negociação, prazos e vencimento de contratos.'),
        ('DASH-PATRIMONIO', 'Painel de Gestão Patrimonial e Bens Públicos', 'PATRIMONIO', 'Saldo contábil, aquisições, depreciação acumulada e motivos de baixa.'),
        ('DASH-CIDADAO-360', 'Visão Unificada do Cidadão (Pessoa 360º)', 'CIDADAO_360', 'Relação unificada: Contribuinte, Fornecedor, Servidor e Processos/Ouvidorias.')
    ]
    for code, title, area, desc in dashboards:
        db.execute('''
            INSERT OR IGNORE INTO bi_dashboards (code, title, area_type, description)
            VALUES (?, ?, ?, ?)
        ''', (code, title, area, desc))

    # 2. Alertas Estratégicos da LRF
    alerts = [
        ('LRF_SAUDE', 'Aplicação Mínima em Ações e Serviços Públicos de Saúde (ASPS)', 18.45, 15.00, 'NORMAL', 'Aplicação atual de 18,45% cumpre com folga a exigência constitucional mínima de 15%.'),
        ('LRF_EDUCACAO', 'Aplicação Mínima na Manutenção e Desenvolvimento do Ensino (MDE)', 26.20, 25.00, 'NORMAL', 'Aplicação atual de 26,20% cumpre o limite constitucional mínimo de 25%.'),
        ('LRF_PESSOAL', 'Despesa Total com Pessoal do Poder Executivo', 49.80, 54.00, 'ALERTA', 'Despesa com pessoal atingiu 49,80% da RCL, superando o Limite de Alerta da LRF (48,60%). Recomenda-se cautela em nomeações.'),
        ('DIVIDA_CONSOLIDADA', 'Dívida Consolidada Líquida / RCL', 12.30, 120.00, 'NORMAL', 'Dívida consolidada líquida controlada em 12,30% da RCL (Teto Res. Senado Federal: 120%).'),
        ('OP_CREDITO', 'Operações de Crédito Internas e Externas / RCL', 2.10, 16.00, 'NORMAL', 'Operações de crédito controladas em 2,10% da RCL (Teto Res. Senado: 16%).')
    ]
    for code, title, cur, tgt, lvl, msg in alerts:
        db.execute('''
            INSERT OR IGNORE INTO bi_alerts (indicator_code, title, current_value, target_limit, alert_level, alert_message)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (code, title, cur, tgt, lvl, msg))

    # 3. Dados Históricos Financeiros Multi-Exercício (2025 vs 2026)
    # Exercício Anterior: 2025 (12 meses)
    for m in range(1, 13):
        rev_pred = 45000000.00
        rev_real = 46200000.00 + (m * 450000)
        exp_app = 45000000.00
        exp_com = 42000000.00 + (m * 400000)
        exp_set = 40000000.00 + (m * 380000)
        exp_paid = 39000000.00 + (m * 370000)
        bank_bal = 35000000.00 + (m * 200000)
        ob_due = 1200000.00
        ob_exp = 8500000.00
        db.execute('''
            INSERT OR IGNORE INTO bi_historical_financial
            (exercise, month, revenue_predicted, revenue_realized, expense_appropriated, expense_committed, expense_settled, expense_paid, bank_balance, obligations_due, obligations_to_expire, health_expense_pct, education_expense_pct, personnel_expense_pct, rpps_revenue, rpps_expense)
            VALUES (2025, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 17.8, 25.8, 48.5, 4500000.0, 3800000.0)
        ''', (m, rev_pred, rev_real, exp_app, exp_com, exp_set, exp_paid, bank_bal, ob_due, ob_exp))

    # Exercício Atual: 2026 (meses 1, 2, 3)
    for m in range(1, 4):
        rev_pred = 52000000.00
        rev_real = 53800000.00 + (m * 500000)
        exp_app = 52000000.00
        exp_com = 48000000.00 + (m * 420000)
        exp_set = 44500000.00 + (m * 390000)
        exp_paid = 43200000.00 + (m * 380000)
        bank_bal = 42000000.00 + (m * 250000)
        ob_due = 850000.00
        ob_exp = 9200000.00
        db.execute('''
            INSERT OR IGNORE INTO bi_historical_financial
            (exercise, month, revenue_predicted, revenue_realized, expense_appropriated, expense_committed, expense_settled, expense_paid, bank_balance, obligations_due, obligations_to_expire, health_expense_pct, education_expense_pct, personnel_expense_pct, rpps_revenue, rpps_expense)
            VALUES (2026, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 18.45, 26.2, 49.8, 5200000.0, 4100000.0)
        ''', (m, rev_pred, rev_real, exp_app, exp_com, exp_set, exp_paid, bank_bal, ob_due, ob_exp))

    # 4. Métricas de Gestão de Pessoas (RH)
    rh_dist = json.dumps({
        "salarios_base": 14200000.00,
        "vantagens_fixas": 3800000.00,
        "adicionais_tempo": 1900000.00,
        "encargos_patronais": 4100000.00,
        "faixas_salariais": {
            "ate_2_sm": 1240,
            "de_2_a_5_sm": 1850,
            "de_5_a_10_sm": 640,
            "acima_10_sm": 180
        }
    })
    for m in range(1, 4):
        db.execute('''
            INSERT OR IGNORE INTO bi_people_metrics
            (exercise, month, total_employees, admitted_count, dismissed_count, turnover_rate, total_hours_expected, total_hours_worked, total_hours_absent, employees_on_leave, gross_payroll_total, net_payroll_total, payroll_by_category_json)
            VALUES (2026, ?, 3910, 45, 12, 1.45, 625600.0, 606832.0, 18768.0, 85, 24000000.00, 19200000.00, ?)
        ''', (m, rh_dist))

    # 5. Métricas de Compras e Licitações
    for m in range(1, 4):
        db.execute('''
            INSERT OR IGNORE INTO bi_procurement_metrics
            (exercise, month, processes_opened, processes_closed, median_days_to_complete, total_estimated_amount, total_awarded_amount, negotiation_savings_pct, contracts_active, contracts_expiring_30_days, contracts_expiring_60_days, contracts_expiring_90_days)
            VALUES (2026, ?, 28, 22, 38.5, 18500000.00, 15400000.00, 16.75, 142, 6, 14, 22)
        ''', (m,))

    # 6. Métricas de Bens Patrimoniais
    for m in range(1, 4):
        db.execute('''
            INSERT OR IGNORE INTO bi_asset_metrics
            (exercise, month, total_assets_count, total_book_value, total_acquisitions_value, total_depreciation_value, total_writeoffs_value)
            VALUES (2026, ?, 18450, 145800000.00, 3200000.00, 1150000.00, 120000.00)
        ''', (m,))

    db.commit()
    print("Módulo de Business Intelligence (BI) semeado com sucesso!")

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        seed_bi()

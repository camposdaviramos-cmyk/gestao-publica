-- ==============================================================================
-- Schema do Módulo de Business Intelligence (BI) e Painel Estratégico do Gestor
-- Município de Rio das Ostras - Edital PE 552/2026 e Anexo III (52 Itens Normativos)
-- ==============================================================================

-- 1. Painéis e Dashboards Customizados
CREATE TABLE IF NOT EXISTS bi_dashboards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    area_type TEXT NOT NULL, -- 'FINANCEIRO', 'ORCAMENTO', 'RECEITAS', 'PESSOAS', 'PATRIMONIO', 'COMPRAS', 'CIDADAO_360', 'EXECUTIVE_LRF'
    description TEXT,
    layout_config_json TEXT, -- Ordem e posicionamento dos cards na tela
    allowed_roles TEXT DEFAULT 'ADMIN,GESTOR,SECRETARIO',
    is_kiosk_enabled INTEGER DEFAULT 1,
    kiosk_display_seconds INTEGER DEFAULT 15,
    active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 2. Alertas Estratégicos e Indicadores da LRF
CREATE TABLE IF NOT EXISTS bi_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    indicator_code TEXT NOT NULL, -- 'LRF_SAUDE', 'LRF_EDUCACAO', 'LRF_PESSOAL', 'DIVIDA_CONSOLIDADA', 'OP_CREDITO', 'ARO'
    title TEXT NOT NULL,
    current_value REAL NOT NULL,
    target_limit REAL NOT NULL,
    alert_level TEXT NOT NULL, -- 'NORMAL', 'ALERTA', 'PRUDENCIAL', 'LIMITE_MAXIMO'
    alert_message TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 3. Histórico e Projeções Financeiras Multi-Exercício (Comparativo Ano Atual vs Anterior)
CREATE TABLE IF NOT EXISTS bi_historical_financial (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise INTEGER NOT NULL,
    month INTEGER NOT NULL,
    revenue_predicted REAL DEFAULT 0.0,
    revenue_realized REAL DEFAULT 0.0,
    expense_appropriated REAL DEFAULT 0.0,
    expense_committed REAL DEFAULT 0.0,
    expense_settled REAL DEFAULT 0.0,
    expense_paid REAL DEFAULT 0.0,
    bank_balance REAL DEFAULT 0.0,
    obligations_due REAL DEFAULT 0.0,
    obligations_to_expire REAL DEFAULT 0.0,
    health_expense_pct REAL DEFAULT 0.0,
    education_expense_pct REAL DEFAULT 0.0,
    personnel_expense_pct REAL DEFAULT 0.0,
    rpps_revenue REAL DEFAULT 0.0,
    rpps_expense REAL DEFAULT 0.0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(exercise, month)
);

-- 4. Métricas e Indicadores de Gestão de Pessoas (RH)
CREATE TABLE IF NOT EXISTS bi_people_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise INTEGER NOT NULL,
    month INTEGER NOT NULL,
    total_employees INTEGER DEFAULT 0,
    admitted_count INTEGER DEFAULT 0,
    dismissed_count INTEGER DEFAULT 0,
    turnover_rate REAL DEFAULT 0.0,
    total_hours_expected REAL DEFAULT 0.0,
    total_hours_worked REAL DEFAULT 0.0,
    total_hours_absent REAL DEFAULT 0.0,
    employees_on_leave INTEGER DEFAULT 0,
    gross_payroll_total REAL DEFAULT 0.0,
    net_payroll_total REAL DEFAULT 0.0,
    payroll_by_category_json TEXT, -- Distribuição por cargo/vínculo/faixa salarial
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(exercise, month)
);

-- 5. Métricas de Compras, Licitações e Contratos
CREATE TABLE IF NOT EXISTS bi_procurement_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise INTEGER NOT NULL,
    month INTEGER NOT NULL,
    processes_opened INTEGER DEFAULT 0,
    processes_closed INTEGER DEFAULT 0,
    median_days_to_complete REAL DEFAULT 0.0,
    total_estimated_amount REAL DEFAULT 0.0,
    total_awarded_amount REAL DEFAULT 0.0,
    negotiation_savings_pct REAL DEFAULT 0.0,
    contracts_active INTEGER DEFAULT 0,
    contracts_expiring_30_days INTEGER DEFAULT 0,
    contracts_expiring_60_days INTEGER DEFAULT 0,
    contracts_expiring_90_days INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(exercise, month)
);

-- 6. Métricas de Patrimônio e Bens Públicos
CREATE TABLE IF NOT EXISTS bi_asset_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise INTEGER NOT NULL,
    month INTEGER NOT NULL,
    total_assets_count INTEGER DEFAULT 0,
    total_book_value REAL DEFAULT 0.0,
    total_acquisitions_value REAL DEFAULT 0.0,
    total_depreciation_value REAL DEFAULT 0.0,
    total_writeoffs_value REAL DEFAULT 0.0,
    assets_by_location_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(exercise, month)
);

-- 7. Histórico do Assistente Virtual / NLP de Consultas
CREATE TABLE IF NOT EXISTS bi_assistant_conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    user_name TEXT NOT NULL,
    question_text TEXT NOT NULL,
    domain_identified TEXT NOT NULL, -- 'FINANCEIRO', 'ORCAMENTO', 'PESSOAS', 'RECEITA', 'GERAL'
    answer_text TEXT NOT NULL,
    data_payload_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 8. Links de Compartilhamento de Painéis com Parâmetros
CREATE TABLE IF NOT EXISTS bi_shared_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT UNIQUE NOT NULL,
    dashboard_code TEXT NOT NULL,
    filters_json TEXT,
    created_by TEXT NOT NULL,
    expires_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_bi_historical_ex_m ON bi_historical_financial(exercise, month);
CREATE INDEX IF NOT EXISTS idx_bi_people_ex_m ON bi_people_metrics(exercise, month);
CREATE INDEX IF NOT EXISTS idx_bi_procurement_ex_m ON bi_procurement_metrics(exercise, month);

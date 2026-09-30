-- ==============================================================================
-- Schema Relacional do Módulo Financeiro, Contábil, Orçamentário e Tesouraria
-- Sistema Integrado Rio das Ostras - Edital PE 552/2026 & Anexo III (229 Itens)
-- ==============================================================================

-- 1. Regras Contábeis Personalizadas e Grupos de Regras (finance.1 a finance.3)
CREATE TABLE IF NOT EXISTS finance_accounting_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fact_type TEXT NOT NULL,
    group_name TEXT NOT NULL,
    rule_name TEXT NOT NULL,
    debit_account_code TEXT NOT NULL,
    credit_account_code TEXT NOT NULL,
    active INTEGER DEFAULT 1,
    created_by TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 2. De/Para SICONFI MSC (Receita, Despesa, PCASP, Fontes) (finance.4 a finance.7)
CREATE TABLE IF NOT EXISTS finance_siconfi_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mapping_type TEXT NOT NULL, -- 'revenue', 'expense', 'pcasp', 'source'
    local_code TEXT NOT NULL,
    local_description TEXT,
    siconfi_code TEXT NOT NULL,
    siconfi_description TEXT,
    is_system_suggested INTEGER DEFAULT 1,
    customized_by_user INTEGER DEFAULT 0,
    exercise INTEGER DEFAULT 2026,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 3. De/Para SIOPS (Saúde) e SIOPE (Educação) (finance.14 a finance.16, finance.30, finance.31)
CREATE TABLE IF NOT EXISTS finance_siops_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL, -- 'revenue', 'expense', 'source'
    local_code TEXT NOT NULL,
    target_code TEXT NOT NULL,
    description TEXT,
    is_system_suggested INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS finance_siope_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL, -- 'revenue', 'expense', 'source'
    local_code TEXT NOT NULL,
    target_code TEXT NOT NULL,
    description TEXT,
    is_system_suggested INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 4. Lotes e Histórico de Envio e Recepção MSC SICONFI (finance.8 a finance.13)
CREATE TABLE IF NOT EXISTS finance_msc_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise INTEGER NOT NULL,
    period_month INTEGER NOT NULL,
    format TEXT NOT NULL, -- 'XBRL', 'CSV'
    entity_id TEXT NOT NULL,
    imported_by TEXT,
    imported_at TEXT DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'VALIDATED',
    raw_content TEXT,
    validation_errors TEXT
);

-- 5. Lançamentos Contábeis Padronizados (LCP) e Conjuntos (CLP) (finance.33, finance.34)
CREATE TABLE IF NOT EXISTS finance_standardized_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL, -- 'LCP', 'CLP'
    description TEXT NOT NULL,
    debit_account TEXT,
    credit_account TEXT,
    clp_items TEXT, -- JSON array of LCP codes if type is CLP
    valid_from TEXT,
    valid_to TEXT,
    active INTEGER DEFAULT 1
);

-- 6. Escrituração Contábil, Livro Diário/Razão e Inalterabilidade (finance.36 a finance.40)
CREATE TABLE IF NOT EXISTS finance_journal_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_number INTEGER NOT NULL,
    exercise INTEGER NOT NULL,
    entity_id TEXT NOT NULL,
    entry_date TEXT NOT NULL,
    fact_type TEXT NOT NULL,
    rule_id INTEGER,
    lcp_code TEXT,
    clp_code TEXT,
    debit_account TEXT NOT NULL,
    credit_account TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    superavit_attribute TEXT DEFAULT 'P', -- 'F' (Financeiro) ou 'P' (Patrimonial)
    is_reversal INTEGER DEFAULT 0,
    reversal_of_id INTEGER,
    history_summary TEXT NOT NULL,
    history_complement TEXT,
    document_type TEXT,
    document_number TEXT,
    commitment_number TEXT,
    subsystem TEXT DEFAULT 'Orcamentario', -- 'Orcamentario', 'Patrimonial', 'Controle'
    created_by TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 7. Plano de Contas PCASP e Atributos Legais (finance.41)
CREATE TABLE IF NOT EXISTS finance_pcasp_accounts (
    code TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    level INTEGER NOT NULL,
    is_synthetic INTEGER DEFAULT 1,
    nature_info TEXT NOT NULL, -- 'Orcamentaria', 'Patrimonial', 'Controle'
    subsystem TEXT NOT NULL,
    balance_nature TEXT NOT NULL, -- 'D', 'C'
    superavit_indicator TEXT, -- 'F', 'P'
    closing_category TEXT,
    movement_type TEXT,
    is_system_defined INTEGER DEFAULT 1,
    created_by_entity INTEGER DEFAULT 0,
    associated_bank_sources TEXT, -- JSON array
    active INTEGER DEFAULT 1
);

-- 8. Contribuinte EFD-Reinf por Unidade Gestora (finance.59)
CREATE TABLE IF NOT EXISTS finance_reinf_taxpayers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT NOT NULL,
    cnpj TEXT NOT NULL UNIQUE,
    start_date TEXT NOT NULL,
    ecd_situation TEXT,
    responsible_name TEXT NOT NULL,
    responsible_cpf TEXT NOT NULL,
    tax_classification TEXT NOT NULL,
    legal_nature TEXT NOT NULL,
    transmission_type TEXT DEFAULT 'Individual', -- 'Consolidado', 'Individual'
    efr_type TEXT DEFAULT 'EFR',
    efr_cnpj TEXT,
    status TEXT DEFAULT 'Ativo',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 9. Processos Administrativos e Judiciais REINF (finance.60)
CREATE TABLE IF NOT EXISTS finance_reinf_processes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    taxpayer_id INTEGER NOT NULL,
    process_number TEXT NOT NULL,
    process_type TEXT NOT NULL, -- 'Administrativo', 'Judicial'
    authorship TEXT NOT NULL, -- 'Contribuinte', 'Terceiros'
    uf TEXT NOT NULL,
    city TEXT NOT NULL,
    court_name TEXT,
    suspension_code TEXT,
    decision_date TEXT,
    deposit_indicator INTEGER DEFAULT 0,
    status TEXT DEFAULT 'Ativo',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 10. Notas Fiscais e RPS ABRASF com Retenções REINF (finance.61 a finance.64, finance.75 a finance.77)
CREATE TABLE IF NOT EXISTS finance_reinf_invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    taxpayer_id INTEGER NOT NULL,
    creditor_document TEXT NOT NULL,
    creditor_name TEXT NOT NULL,
    creditor_activity TEXT, -- 'Geral', 'Associacao_Desportiva', 'Produtor_Rural'
    is_cprb INTEGER DEFAULT 0,
    invoice_number TEXT NOT NULL,
    rps_number TEXT,
    issue_date TEXT NOT NULL,
    service_type_code TEXT NOT NULL,
    process_id INTEGER,
    gross_amount_cents INTEGER NOT NULL,
    withholding_base_cents INTEGER NOT NULL,
    withholding_rate_cents INTEGER NOT NULL,
    withholding_amount_cents INTEGER NOT NULL,
    special_service_years INTEGER,
    additional_withholding_cents INTEGER DEFAULT 0,
    rural_senar_cents INTEGER DEFAULT 0,
    rural_gilrat_cents INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 11. Eventos e Transmissão EFD-Reinf com Mensageria (finance.187 a finance.189)
CREATE TABLE IF NOT EXISTS finance_reinf_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    taxpayer_id INTEGER NOT NULL,
    competence TEXT NOT NULL,
    event_type TEXT NOT NULL, -- R-1000, R-1070, R-2010, R-2020, R-2050, R-2055, R-2060, R-4010, R-4020, R-4099
    transmission_type TEXT DEFAULT 'Individual',
    status TEXT DEFAULT 'Pendente',
    xml_content TEXT,
    receipt_number TEXT,
    return_message TEXT,
    transmitted_at TEXT,
    created_by TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 12. Cadastro de Retenções e Regra IPC 11 STN (finance.73, finance.86)
CREATE TABLE IF NOT EXISTS finance_withholding_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    tax_type TEXT NOT NULL, -- 'INSS', 'IR', 'RPPS', 'ISSQN', 'Outros'
    classification TEXT NOT NULL, -- 'propria', 'terceiros'
    rate_basis TEXT NOT NULL,
    accounting_account TEXT NOT NULL,
    extra_budget_account TEXT,
    due_day_type TEXT DEFAULT 'corridos',
    due_days INTEGER DEFAULT 10,
    auto_generate_extra_ipc11 INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 13. Planejamento Orçamentário PPA, LDO e LOA (finance.91 a finance.98, finance.129 a finance.142)
CREATE TABLE IF NOT EXISTS finance_budget_planning (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    piece_type TEXT NOT NULL, -- 'PPA', 'LDO', 'LOA'
    exercise INTEGER NOT NULL,
    year_index INTEGER DEFAULT 1,
    entity_id TEXT NOT NULL,
    organ_code TEXT NOT NULL,
    unit_code TEXT NOT NULL,
    function_code TEXT NOT NULL,
    subfunction_code TEXT NOT NULL,
    program_code TEXT NOT NULL,
    action_code TEXT NOT NULL,
    nature_code TEXT NOT NULL,
    source_code TEXT NOT NULL,
    physical_target REAL DEFAULT 0.0,
    physical_metric TEXT DEFAULT 'Unidade',
    physical_type TEXT DEFAULT 'Acumulativo',
    physical_periodicity TEXT DEFAULT 'Anual',
    fiscal_target_cents INTEGER DEFAULT 0,
    gross_revenue_cents INTEGER DEFAULT 0,
    deductions_fundeb_cents INTEGER DEFAULT 0,
    deductions_renunciation_cents INTEGER DEFAULT 0,
    deductions_restitution_cents INTEGER DEFAULT 0,
    net_revenue_cents INTEGER DEFAULT 0,
    legal_status TEXT DEFAULT 'Elaboracao',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 14. Alterações Legais no PPA e LDO (finance.99 a finance.101)
CREATE TABLE IF NOT EXISTS finance_legal_alterations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    piece_type TEXT NOT NULL,
    law_number TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT DEFAULT 'Elaboracao',
    amendment_notes TEXT,
    replicate_to_ldo INTEGER DEFAULT 1,
    history_log TEXT,
    approved_at TEXT,
    created_by TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 15. Decretos de Alteração Orçamentária Formatados (finance.155, finance.156)
CREATE TABLE IF NOT EXISTS finance_budget_decrees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    decree_number TEXT NOT NULL,
    decree_date TEXT NOT NULL,
    decree_type TEXT NOT NULL, -- 'Suplementar', 'Especial', 'Extraordinario', 'Anulacao', 'Superavit', 'Excesso'
    justification TEXT NOT NULL,
    total_amount_cents INTEGER NOT NULL,
    formatted_document TEXT,
    status TEXT DEFAULT 'Aprovado',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 16. Demonstrativos Fiscais da LDO (1 a 8 e Riscos Fiscais MDF) (finance.112 a finance.128)
CREATE TABLE IF NOT EXISTS finance_ldo_fiscal_targets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise INTEGER NOT NULL,
    target_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    explanatory_notes TEXT,
    reference_date TEXT NOT NULL,
    created_by TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 17. Contratos de Ordem Bancária Eletrônica (OBE) e PIX BB (finance.87, finance.192 a finance.194, finance.229)
CREATE TABLE IF NOT EXISTS finance_treasury_bank_contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_code TEXT NOT NULL,
    agency_code TEXT NOT NULL,
    account_number TEXT NOT NULL,
    contract_number TEXT NOT NULL,
    cnab_version TEXT DEFAULT '240',
    doc_limit_cents INTEGER DEFAULT 500000,
    pix_key TEXT,
    pix_client_id TEXT,
    active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 18. Ordens Bancárias e Pagamentos Eletrônicos (finance.193, finance.194, finance.204)
CREATE TABLE IF NOT EXISTS finance_treasury_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT NOT NULL UNIQUE,
    contract_id INTEGER NOT NULL,
    order_type TEXT NOT NULL,
    total_amount_cents INTEGER NOT NULL,
    payment_method TEXT DEFAULT 'OBE',
    status TEXT DEFAULT 'Gerada',
    remessa_content TEXT,
    retorno_content TEXT,
    rejected_amount_cents INTEGER DEFAULT 0,
    rejection_reason TEXT,
    auto_reversed INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 19. Talonários e Impressão de Cheques (finance.196)
CREATE TABLE IF NOT EXISTS finance_treasury_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    checkbook_series TEXT NOT NULL,
    check_number INTEGER NOT NULL,
    bank_account_code TEXT NOT NULL,
    bearer_name TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    issue_date TEXT NOT NULL,
    without_accounting_reflex INTEGER DEFAULT 0,
    status TEXT DEFAULT 'Emitido',
    cancellation_reason TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 20. Conciliação Bancária e Extratos OFX (finance.197, finance.219 a finance.222)
CREATE TABLE IF NOT EXISTS finance_bank_reconciliations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_account_id TEXT NOT NULL,
    product_id INTEGER,
    exercise INTEGER NOT NULL,
    reconciliation_date TEXT NOT NULL,
    bank_balance_cents INTEGER NOT NULL,
    system_balance_cents INTEGER NOT NULL,
    difference_cents INTEGER NOT NULL,
    status TEXT DEFAULT 'Pendente',
    created_by TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS finance_bank_statements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reconciliation_id INTEGER NOT NULL,
    movement_date TEXT NOT NULL,
    movement_type TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    description TEXT NOT NULL,
    fitid TEXT,
    is_manual INTEGER DEFAULT 0,
    adjustment_type TEXT,
    matched_journal_entry_id INTEGER,
    status TEXT DEFAULT 'Nao_Conciliado',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 21. Calendário de Bloqueio da Conciliação Bancária (finance.220)
CREATE TABLE IF NOT EXISTS finance_reconciliation_locks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise INTEGER NOT NULL,
    month INTEGER NOT NULL,
    is_locked INTEGER DEFAULT 1,
    locked_by TEXT,
    locked_at TEXT DEFAULT CURRENT_TIMESTAMP,
    reason TEXT
);

-- 22. Catálogo Oficial BACEN (Bancos, Agências e Postos com DV) (finance.212 a finance.216)
CREATE TABLE IF NOT EXISTS finance_bacen_catalog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_code TEXT NOT NULL,
    bank_name TEXT NOT NULL,
    agency_code TEXT NOT NULL,
    agency_dv TEXT NOT NULL,
    agency_name TEXT NOT NULL,
    agency_type TEXT NOT NULL,
    neighborhood TEXT,
    city TEXT NOT NULL,
    uf TEXT NOT NULL,
    active INTEGER DEFAULT 1,
    converted_from_agency INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 23. Produtos Financeiros Vinculados a Contas PCASP (finance.218)
CREATE TABLE IF NOT EXISTS finance_financial_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    product_type TEXT NOT NULL,
    bank_account_code TEXT,
    accounting_account_code TEXT,
    opening_date TEXT NOT NULL,
    active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 24. Recursos Antecipados / Suprimento de Fundos (finance.201, finance.202)
CREATE TABLE IF NOT EXISTS finance_advance_funds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_number TEXT NOT NULL UNIQUE,
    advance_type TEXT NOT NULL,
    server_name TEXT NOT NULL,
    server_cpf TEXT NOT NULL,
    commitment_id TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    max_days_accountability INTEGER DEFAULT 30,
    issue_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    returned_amount_cents INTEGER DEFAULT 0,
    spent_amount_cents INTEGER DEFAULT 0,
    return_accounting_account TEXT,
    status TEXT DEFAULT 'Aberto',
    accountability_receipt_number TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 25. Filas de Ordem Cronológica de Pagamentos (finance.205, finance.206)
CREATE TABLE IF NOT EXISTS finance_chronological_queues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    queue_name TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    law_basis TEXT NOT NULL,
    sort_criteria TEXT DEFAULT 'Data_Liquidacao',
    active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 26. Credenciamento SIAFIC por CPF e Termo de Responsabilidade (finance.70, finance.71, finance.152, finance.153)
CREATE TABLE IF NOT EXISTS finance_siafic_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cpf TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    authorized_by_cpf TEXT,
    responsibility_term_accepted INTEGER DEFAULT 1,
    responsibility_term_attachment TEXT,
    authorized_at TEXT DEFAULT CURRENT_TIMESTAMP,
    active INTEGER DEFAULT 1
);

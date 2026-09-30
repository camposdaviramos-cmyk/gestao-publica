-- ============================================================================
-- TRANSPARENCY MODULE SCHEMA — RIO GESTÃO / RIO DAS OSTRAS
-- Lei de Acesso à Informação (Lei 12.527/2011), LRF (LC 101/2000), LC 131/2009 e Lei 14.133/2021
-- ============================================================================

CREATE TABLE IF NOT EXISTS transparency_configs (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transparency_custom_menus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    icon TEXT DEFAULT 'link',
    category TEXT DEFAULT 'Geral',
    is_highlighted INTEGER DEFAULT 0,
    sort_order INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transparency_covid_themes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    theme_name TEXT NOT NULL,
    link_url TEXT NOT NULL,
    description TEXT,
    is_calamity INTEGER DEFAULT 0,
    sort_order INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transparency_active_debt (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    debtor_name TEXT NOT NULL,
    document TEXT NOT NULL, -- CPF ou CNPJ
    municipal_registration TEXT NOT NULL,
    cda_number TEXT NOT NULL, -- Certidão de Dívida Ativa
    process_number TEXT,
    debt_nature TEXT NOT NULL, -- Ex: IPTU, ISS, Taxas, Multas
    fiscal_year INTEGER NOT NULL,
    original_amount INTEGER NOT NULL, -- em centavos
    updated_amount INTEGER NOT NULL, -- em centavos
    status TEXT DEFAULT 'Inscrito', -- Inscrito, Ajuizado, Parcelado, Quitado
    enrollment_date TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transparency_parliamentary_amendments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sphere TEXT NOT NULL, -- Federal, Estadual, Municipal
    author TEXT NOT NULL, -- Nome do Parlamentar ou Bancada
    amendment_number TEXT NOT NULL,
    fiscal_year INTEGER NOT NULL,
    amendment_type TEXT NOT NULL, -- Individual, Bancada, Comissão
    indicated_amount INTEGER NOT NULL, -- em centavos
    committed_amount INTEGER DEFAULT 0, -- empenhado em centavos
    liquidated_amount INTEGER DEFAULT 0, -- liquidado em centavos
    paid_amount INTEGER DEFAULT 0, -- pago em centavos
    object TEXT NOT NULL,
    beneficiary TEXT NOT NULL, -- Órgão ou Fundo recebedor
    status TEXT DEFAULT 'Em execução', -- Proposta, Aprovada, Em execução, Concluída
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transparency_travel_expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_name TEXT NOT NULL,
    registration TEXT NOT NULL, -- Matrícula
    role TEXT NOT NULL, -- Cargo
    department TEXT NOT NULL, -- Lotação
    authorization_law TEXT NOT NULL,
    concession_act TEXT NOT NULL, -- Ato de concessão
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    destination TEXT NOT NULL,
    transport_type TEXT NOT NULL, -- Aéreo, Terrestre, Veículo Oficial, Próprio
    transport_cost INTEGER DEFAULT 0, -- em centavos
    objective TEXT NOT NULL,
    daily_allowance_qty REAL NOT NULL, -- Quantidade de diárias
    daily_allowance_unit_value INTEGER NOT NULL, -- em centavos
    total_amount INTEGER NOT NULL, -- em centavos
    expense_breakdown TEXT, -- Desdobramento da despesa (ex: 3.3.90.14.14)
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transparency_competitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    competition_type TEXT NOT NULL, -- Concurso Público, Processo Seletivo Simplificado
    number_year TEXT NOT NULL, -- Ex: 001/2026
    edict_law TEXT NOT NULL,
    publication_date TEXT NOT NULL,
    homologation_date TEXT,
    validity_date TEXT,
    extension_date TEXT,
    department TEXT NOT NULL,
    status TEXT NOT NULL, -- Em andamento, Homologado, Encerrado
    vacancies_created INTEGER DEFAULT 0,
    vacancies_filled INTEGER DEFAULT 0,
    vacancies_available INTEGER DEFAULT 0,
    attachment_url TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transparency_competition_appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    competition_id INTEGER NOT NULL REFERENCES transparency_competitions(id),
    candidate_name TEXT NOT NULL,
    document TEXT NOT NULL,
    role TEXT NOT NULL,
    ranking_position INTEGER NOT NULL,
    call_act TEXT NOT NULL,
    appointment_date TEXT NOT NULL,
    possession_date TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transparency_sic_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    protocol TEXT UNIQUE NOT NULL,
    requester_name TEXT NOT NULL,
    requester_document TEXT NOT NULL,
    requester_email TEXT,
    subject TEXT NOT NULL,
    description TEXT NOT NULL,
    department TEXT NOT NULL,
    opening_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    status TEXT DEFAULT 'Aberto', -- Aberto, Em análise, Respondido, Recurso, Concluído
    response TEXT,
    response_date TEXT,
    responder_name TEXT,
    appeal_text TEXT,
    appeal_response TEXT,
    appeal_status TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transparency_extra_transfers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transfer_type TEXT NOT NULL, -- Concedido, Recebido, Repasse entre Entidades
    granting_unit TEXT NOT NULL,
    receiving_unit TEXT NOT NULL,
    purpose TEXT NOT NULL,
    transfer_date TEXT NOT NULL,
    expected_amount INTEGER NOT NULL, -- centavos
    received_amount INTEGER NOT NULL, -- centavos
    document_reference TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transparency_faq (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_transp_debt_doc ON transparency_active_debt(document);
CREATE INDEX IF NOT EXISTS idx_transp_amend_year ON transparency_parliamentary_amendments(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_transp_sic_prot ON transparency_sic_requests(protocol);

-- Schema do Módulo de Controle Interno e Controladoria
-- Atende integralmente aos 85 itens do Anexo III e Edital PE 552/2026

CREATE TABLE IF NOT EXISTS control_ibge_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id INTEGER NOT NULL REFERENCES erp_entities(id),
    exercise INTEGER NOT NULL,
    municipio_nome TEXT NOT NULL DEFAULT 'Rio das Ostras',
    cod_ibge TEXT NOT NULL DEFAULT '3304524',
    populacao INTEGER NOT NULL DEFAULT 156491,
    limite_pessoal_executivo_pct REAL NOT NULL DEFAULT 54.0,
    limite_pessoal_legislativo_pct REAL NOT NULL DEFAULT 6.0,
    limite_repasse_camara_pct REAL NOT NULL DEFAULT 7.0,
    receita_corrente_liquida INTEGER NOT NULL DEFAULT 98540000000, -- em centavos
    updated_at TEXT NOT NULL,
    UNIQUE(entity_id, exercise)
);

CREATE TABLE IF NOT EXISTS control_obligation_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id INTEGER NOT NULL REFERENCES erp_entities(id),
    name TEXT NOT NULL,
    description TEXT,
    leader_name TEXT NOT NULL,
    leader_email TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS control_obligations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id INTEGER NOT NULL REFERENCES erp_entities(id),
    exercise INTEGER NOT NULL,
    code TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    legislation_type TEXT NOT NULL, -- 'Federal', 'Estadual', 'Municipal'
    subject_group TEXT NOT NULL,
    legislation TEXT NOT NULL,
    delivery_method TEXT NOT NULL,
    destination TEXT NOT NULL,
    source_url TEXT,
    notes TEXT,
    group_id INTEGER REFERENCES control_obligation_groups(id),
    owner_name TEXT NOT NULL,
    owner_email TEXT,
    frequency TEXT NOT NULL DEFAULT 'Mensal', -- 'Mensal', 'Bimestral', 'Quadrimestral', 'Semestral', 'Anual'
    interval_months INTEGER NOT NULL DEFAULT 1,
    first_due_date TEXT NOT NULL,
    total_occurrences INTEGER NOT NULL DEFAULT 12,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    UNIQUE(entity_id, exercise, code)
);

CREATE TABLE IF NOT EXISTS control_occurrences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    obligation_id INTEGER NOT NULL REFERENCES control_obligations(id) ON DELETE CASCADE,
    entity_id INTEGER NOT NULL REFERENCES erp_entities(id),
    exercise INTEGER NOT NULL,
    occurrence_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    competence TEXT NOT NULL, -- 'YYYY-MM'
    due_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'A Vencer', -- 'A Vencer', 'Vencida', 'Atendida', 'Dispensada'
    closed_at TEXT,
    closed_by TEXT,
    owner_name TEXT NOT NULL,
    owner_email TEXT,
    delay_justification TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS control_obligation_followups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    occurrence_id INTEGER NOT NULL REFERENCES control_occurrences(id) ON DELETE CASCADE,
    type TEXT NOT NULL, -- 'Justificativa', 'Comentário', 'Encerramento', 'Reabertura', 'Email'
    notes TEXT NOT NULL,
    attachment_name TEXT,
    attachment_url TEXT,
    author_name TEXT NOT NULL,
    recipient_email TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS control_siconfi_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id INTEGER NOT NULL REFERENCES erp_entities(id),
    rule_code TEXT NOT NULL,
    title TEXT NOT NULL,
    dimension INTEGER NOT NULL, -- 1=Gestão, 2=Contábil, 3=Fiscal, 4=Contábil x Fiscal
    power TEXT NOT NULL DEFAULT 'Executivo', -- 'Executivo', 'Legislativo', 'Consolidado'
    interval_type TEXT NOT NULL DEFAULT 'Mensal', -- 'Mensal', 'Bimestral', 'Quadrimestral', 'Semestral', 'Anual'
    description TEXT NOT NULL,
    formula TEXT,
    tolerance_cents INTEGER DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1,
    owner_name TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(entity_id, rule_code)
);

CREATE TABLE IF NOT EXISTS control_siconfi_evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id INTEGER NOT NULL REFERENCES erp_entities(id),
    exercise INTEGER NOT NULL,
    period TEXT NOT NULL, -- '2026-01', '2026-B1', etc.
    rule_id INTEGER NOT NULL REFERENCES control_siconfi_rules(id) ON DELETE CASCADE,
    status TEXT NOT NULL, -- 'Conforme', 'Não Conforme'
    verified_value TEXT,
    benchmark_value TEXT,
    notes TEXT,
    evaluated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS control_action_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id INTEGER NOT NULL REFERENCES erp_entities(id),
    exercise INTEGER NOT NULL,
    source_module TEXT NOT NULL, -- 'SICONFI', 'CAUC', 'Convenios', 'Obrigacao'
    reference_id TEXT NOT NULL, -- código da regra ou do item
    title TEXT NOT NULL,
    fact TEXT NOT NULL,
    cause TEXT NOT NULL,
    corrective_action TEXT NOT NULL,
    responsible_name TEXT NOT NULL,
    responsible_email TEXT,
    deadline TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Pendente', -- 'Pendente', 'Em Andamento', 'Respondido', 'Concluído'
    response_notes TEXT,
    response_evidence TEXT,
    responded_at TEXT,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS control_cauc_requirements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id INTEGER NOT NULL REFERENCES erp_entities(id),
    code TEXT NOT NULL,
    group_name TEXT NOT NULL, -- 'I - Obrigações Financeiras', 'II - Adimplência Financeira', 'III - Prestação de Contas', etc.
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Adimplente', -- 'Adimplente', 'Inadimplente'
    responsible_name TEXT NOT NULL,
    responsible_email TEXT,
    last_verified TEXT NOT NULL,
    valid_until TEXT,
    UNIQUE(entity_id, code)
);

CREATE TABLE IF NOT EXISTS control_agreements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id INTEGER NOT NULL REFERENCES erp_entities(id),
    exercise INTEGER NOT NULL,
    agreement_number TEXT NOT NULL,
    siconv_number TEXT,
    grantor TEXT NOT NULL, -- Concedente (ex: 'Ministério das Cidades', 'Governo do Estado do Rio de Janeiro')
    object TEXT NOT NULL,
    total_amount INTEGER NOT NULL, -- em centavos
    grantor_amount INTEGER NOT NULL,
    counterpart_amount INTEGER NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    accountability_status TEXT NOT NULL DEFAULT 'Adimplente', -- 'Adimplente', 'Inadimplente', 'Em Prestação de Contas'
    responsible_name TEXT NOT NULL,
    responsible_email TEXT,
    updated_at TEXT NOT NULL,
    UNIQUE(entity_id, agreement_number)
);

CREATE TABLE IF NOT EXISTS control_audit_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id INTEGER NOT NULL REFERENCES erp_entities(id),
    exercise INTEGER NOT NULL,
    report_type TEXT NOT NULL, -- 'Geral', 'SICONFI', 'CAUC', 'Convenios'
    period TEXT NOT NULL, -- '2026-01'
    scope_type TEXT NOT NULL DEFAULT 'Consolidado', -- 'Consolidado', 'Executivo', 'Legislativo'
    title TEXT NOT NULL,
    selected_verifications TEXT NOT NULL, -- JSON array de IDs
    selected_occurrences TEXT NOT NULL, -- JSON array de IDs
    opinion_text TEXT NOT NULL,
    conclusion_text TEXT NOT NULL,
    signatories TEXT NOT NULL, -- JSON array de {name, role, signature_date}
    sealed INTEGER NOT NULL DEFAULT 0,
    sealed_at TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    hash_digest TEXT,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS control_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    recipient_role TEXT, -- 'ADMINISTRADOR', 'CONTROLADOR', 'OPERADOR'
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    reference_type TEXT, -- 'obligation', 'action_plan', 'siconfi', 'cauc'
    reference_id TEXT,
    read INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

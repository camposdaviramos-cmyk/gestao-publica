-- procurement_schema.sql: Tabelas auxiliares e complementares do módulo de Compras, Licitações e Contratos (Lei 14.133/2021 e Lei 11.947/2009)

-- Atas de Registro de Preços (SRP - Art. 82 da Lei 14.133/2021)
CREATE TABLE IF NOT EXISTS procurement_price_agreements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    process_id INTEGER NOT NULL REFERENCES erp_objects(id) ON DELETE RESTRICT,
    supplier_id INTEGER NOT NULL REFERENCES erp_objects(id) ON DELETE RESTRICT,
    year INTEGER NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    total_amount INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1,
    carona_permitted INTEGER NOT NULL DEFAULT 1,
    carona_max_multiplier REAL NOT NULL DEFAULT 2.0,
    notes TEXT DEFAULT '',
    created_by INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Itens registrados na Ata de Registro de Preços
CREATE TABLE IF NOT EXISTS procurement_price_agreement_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agreement_id INTEGER NOT NULL REFERENCES procurement_price_agreements(id) ON DELETE CASCADE,
    item_code TEXT NOT NULL,
    description TEXT NOT NULL,
    unit TEXT NOT NULL,
    quantity_registered INTEGER NOT NULL, -- em milionésimos
    quantity_consumed INTEGER NOT NULL DEFAULT 0, -- em milionésimos
    unit_price INTEGER NOT NULL, -- em centavos
    discount_percent REAL DEFAULT 0.0,
    quota_type TEXT NOT NULL DEFAULT 'Principal', -- 'Principal' ou 'Reservada ME/EPP'
    linked_quota_item_id INTEGER REFERENCES procurement_price_agreement_items(id),
    ncm TEXT DEFAULT '',
    nbs TEXT DEFAULT '',
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

-- Sessão pública, lances e histórico de disputas (Arts. 17 e 29)
CREATE TABLE IF NOT EXISTS procurement_bids (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    process_id INTEGER NOT NULL REFERENCES erp_objects(id) ON DELETE CASCADE,
    item_id INTEGER NOT NULL REFERENCES erp_objects(id) ON DELETE CASCADE,
    supplier_id INTEGER NOT NULL REFERENCES erp_objects(id) ON DELETE RESTRICT,
    round_number INTEGER NOT NULL DEFAULT 1,
    bid_type TEXT NOT NULL DEFAULT 'Lance', -- 'Proposta Inicial', 'Lance', 'Negociação', 'Desempate'
    bid_amount INTEGER NOT NULL, -- em centavos (ou desconto calculado)
    discount_percent REAL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'Válido', -- 'Válido', 'Desclassificado', 'Vencedor', 'Recusado'
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL
);

-- Certidões Negativas de Débitos e Regularidade Fiscal/Trabalhista (CNDs)
CREATE TABLE IF NOT EXISTS procurement_supplier_certificates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id INTEGER NOT NULL REFERENCES erp_objects(id) ON DELETE CASCADE,
    certificate_type TEXT NOT NULL, -- 'Federal/INSS', 'Estadual', 'Municipal', 'Trabalhista CNDT', 'FGTS', 'Falência/Concordata'
    certificate_number TEXT NOT NULL,
    issue_date TEXT NOT NULL,
    expiration_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Válida', -- 'Válida', 'Vence em breve', 'Vencida'
    verification_url TEXT DEFAULT '',
    attachment_id INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Sanções e Penalidades Administrativas (CEIS, CNEP, TCU, TCE-RJ)
CREATE TABLE IF NOT EXISTS procurement_supplier_sanctions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id INTEGER NOT NULL REFERENCES erp_objects(id) ON DELETE CASCADE,
    sanction_type TEXT NOT NULL, -- 'Advertência', 'Multa', 'Impedimento de licitar', 'Declaração de inidoneidade'
    legal_basis TEXT NOT NULL,
    origin_process TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT,
    fine_amount INTEGER DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1,
    notes TEXT DEFAULT '',
    created_by INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL
);

-- Versionamento e aprovação do Plano de Contratações Anual (PCA)
CREATE TABLE IF NOT EXISTS procurement_pca_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise INTEGER NOT NULL,
    version_number INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'Rascunho', -- 'Rascunho', 'Aprovado', 'Reprovado', 'Publicado PNCP'
    total_estimated_amount INTEGER NOT NULL DEFAULT 0,
    items_count INTEGER NOT NULL DEFAULT 0,
    justification TEXT DEFAULT '',
    pncp_transmission_id TEXT,
    pncp_status TEXT,
    approved_by INTEGER REFERENCES users(id),
    approved_at TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL,
    UNIQUE(exercise, version_number)
);

-- Procedimentos Auxiliares (Credenciamento, Pré-qualificação, Chamada PNAE)
CREATE TABLE IF NOT EXISTS procurement_auxiliary_procedures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    type TEXT NOT NULL, -- 'Credenciamento', 'Pré-qualificação', 'Chamada Pública PNAE', 'PMI'
    legal_basis TEXT NOT NULL, -- ex: Art. 78 da Lei 14.133/2021, Art. 14 §1º da Lei 11.947/2009
    tce_modality TEXT DEFAULT 'CPP', -- 'CPP' para PNAE conforme instrução TCE-RJ
    notice_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Edital Publicado', -- 'Edital Publicado', 'Inscrições Abertas', 'Homologado', 'Encerrado'
    total_estimated INTEGER DEFAULT 0,
    notes TEXT DEFAULT '',
    created_by INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL
);

-- Convocação de Licitantes Remanescentes (Art. 90 §§ 2º, 4º e 7º da Lei 14.133/2021)
CREATE TABLE IF NOT EXISTS procurement_remaining_summons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    process_id INTEGER NOT NULL REFERENCES erp_objects(id) ON DELETE CASCADE,
    item_id INTEGER NOT NULL REFERENCES erp_objects(id) ON DELETE CASCADE,
    supplier_id INTEGER NOT NULL REFERENCES erp_objects(id) ON DELETE RESTRICT,
    rank_position INTEGER NOT NULL,
    summon_date TEXT NOT NULL,
    response_deadline TEXT NOT NULL,
    accepted_winner_conditions INTEGER NOT NULL DEFAULT 0, -- 1 se aceitou condições do vencedor, 0 se na sua própria proposta
    unit_price INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'Convocado', -- 'Convocado', 'Aceito', 'Recusado', 'Decorrido prazo'
    justification TEXT DEFAULT '',
    created_by INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL
);

-- Adesões (Caronas) a Atas de Registro de Preços de outros órgãos ou externos
CREATE TABLE IF NOT EXISTS procurement_carona_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agreement_id INTEGER NOT NULL REFERENCES procurement_price_agreements(id) ON DELETE CASCADE,
    external_entity_name TEXT NOT NULL,
    external_entity_cnpj TEXT NOT NULL,
    authorization_date TEXT NOT NULL,
    authorized_amount INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'Autorizada',
    created_by INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_proc_agreements_process ON procurement_price_agreements(process_id);
CREATE INDEX IF NOT EXISTS idx_proc_agreements_supplier ON procurement_price_agreements(supplier_id);
CREATE INDEX IF NOT EXISTS idx_proc_agreement_items_agr ON procurement_price_agreement_items(agreement_id);
CREATE INDEX IF NOT EXISTS idx_proc_bids_process ON procurement_bids(process_id);
CREATE INDEX IF NOT EXISTS idx_proc_bids_item ON procurement_bids(item_id);
CREATE INDEX IF NOT EXISTS idx_proc_certs_supplier ON procurement_supplier_certificates(supplier_id);
CREATE INDEX IF NOT EXISTS idx_proc_sanctions_supplier ON procurement_supplier_sanctions(supplier_id);
CREATE INDEX IF NOT EXISTS idx_proc_pca_exercise ON procurement_pca_versions(exercise);
CREATE INDEX IF NOT EXISTS idx_proc_aux_code ON procurement_auxiliary_procedures(code);
CREATE INDEX IF NOT EXISTS idx_proc_summons_process ON procurement_remaining_summons(process_id);

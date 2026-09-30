-- ==============================================================================
-- Schema do Módulo de Assistência Social e Cidadania (SUAS / CRAS / CREAS / CadÚnico)
-- Município de Rio das Ostras - Edital PE 552/2026 e Anexo III (410 Itens Normativos)
-- Compatível com SQLite 3 e PostgreSQL
-- ==============================================================================

-- 1. Unidades Socioassistenciais (CRAS, CREAS, Centro POP, Acolhimento, etc.)
CREATE TABLE IF NOT EXISTS social_units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    unit_type TEXT NOT NULL, -- 'CRAS', 'CREAS', 'CENTRO_POP', 'ACOLHIMENTO_INSTITUCIONAL', 'CASA_PASSAGEM', 'CONSELHO_TUTELAR', 'CENTRO_CONVIVENCIA'
    district TEXT NOT NULL,
    neighborhood TEXT NOT NULL,
    address TEXT NOT NULL,
    latitude REAL DEFAULT -22.5268,
    longitude REAL DEFAULT -41.9452,
    phone TEXT,
    email TEXT,
    manager_name TEXT,
    operating_hours TEXT DEFAULT '08:00 às 17:00',
    capacity_families INTEGER DEFAULT 500,
    active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 2. Equipes Técnicas e Profissionais (CRESS / CRP / OAB / Educador Social)
CREATE TABLE IF NOT EXISTS social_teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_id INTEGER NOT NULL REFERENCES social_units(id),
    name TEXT NOT NULL,
    cpf TEXT UNIQUE NOT NULL,
    role_type TEXT NOT NULL, -- 'ASSISTENTE_SOCIAL', 'PSICOLOGO', 'ADVOGADO', 'EDUCADOR_SOCIAL', 'COORDENADOR', 'ENTREVISTADOR_CADUNICO'
    council_type TEXT, -- 'CRESS', 'CRP', 'OAB', 'OUTRO'
    council_number TEXT,
    council_state TEXT DEFAULT 'RJ',
    email TEXT,
    phone TEXT,
    active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 3. Bairros e Territórios de Abrangência
CREATE TABLE IF NOT EXISTS social_territories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    district TEXT NOT NULL,
    cras_unit_id INTEGER REFERENCES social_units(id),
    high_risk_zone INTEGER DEFAULT 0,
    boundary_geojson TEXT,
    vulnerability_index_avg REAL DEFAULT 0.0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 4. Tabelas de Referência Geral SUAS
CREATE TABLE IF NOT EXISTS social_reference_vulnerabilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL, -- 'RISCO_PESSOAL', 'INSEGURANCA_ALIMENTAR', 'VIOLENCIA', 'HABITACIONAL', 'ISOLAMENTO'
    severity_level TEXT DEFAULT 'MEDIA', -- 'BAIXA', 'MEDIA', 'ALTA', 'MUITO_ALTA'
    active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS social_reference_pcd (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    accessibility_needs TEXT,
    active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS social_reference_sinase (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    infraction_type TEXT NOT NULL,
    gravity_level TEXT NOT NULL,
    active INTEGER DEFAULT 1
);

-- 5. Almoxarifados e Locais de Estoque Socioassistencial
CREATE TABLE IF NOT EXISTS social_warehouses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    unit_id INTEGER REFERENCES social_units(id),
    manager_name TEXT,
    address TEXT,
    active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 6. Catálogo de Insumos e Benefícios Eventuais
CREATE TABLE IF NOT EXISTS social_supplies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL, -- 'CESTA_BASICA', 'AUXILIO_NATALIDADE', 'AUXILIO_FUNERAL', 'KIT_ACOLHIMENTO', 'KIT_HIGIENE', 'COBERTORES', 'FILTROS_AGUA'
    unit_of_measure TEXT DEFAULT 'UN',
    minimum_stock INTEGER DEFAULT 10,
    current_stock INTEGER DEFAULT 0,
    is_perishable INTEGER DEFAULT 0,
    active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 7. Lotes de Suprimentos (Controle de Validade e Fabricação)
CREATE TABLE IF NOT EXISTS social_stock_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supply_id INTEGER NOT NULL REFERENCES social_supplies(id),
    warehouse_id INTEGER NOT NULL REFERENCES social_warehouses(id),
    batch_number TEXT NOT NULL,
    manufacture_date TEXT,
    expiration_date TEXT,
    supplier_name TEXT,
    initial_quantity INTEGER NOT NULL,
    current_quantity INTEGER NOT NULL,
    unit_cost REAL DEFAULT 0.0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 8. Movimentações de Estoque Socioassistencial
CREATE TABLE IF NOT EXISTS social_stock_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supply_id INTEGER NOT NULL REFERENCES social_supplies(id),
    batch_id INTEGER REFERENCES social_stock_batches(id),
    warehouse_id INTEGER NOT NULL REFERENCES social_warehouses(id),
    movement_type TEXT NOT NULL, -- 'ENTRADA', 'TRANSFERENCIA', 'SAIDA_BENEFICIO', 'PERDA_DESCARTE'
    quantity INTEGER NOT NULL,
    destination_warehouse_id INTEGER REFERENCES social_warehouses(id),
    benefit_grant_id INTEGER,
    reason TEXT,
    user_responsible TEXT NOT NULL,
    movement_date TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 9. Prontuário Eletrônico Familiar SUAS / CadÚnico
CREATE TABLE IF NOT EXISTS social_families (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    family_code TEXT UNIQUE NOT NULL, -- Código familiar CadÚnico (v7/v8)
    head_nis TEXT UNIQUE NOT NULL,
    head_name TEXT NOT NULL,
    head_cpf TEXT,
    head_birth_date TEXT,
    address TEXT NOT NULL,
    neighborhood TEXT NOT NULL,
    district TEXT NOT NULL DEFAULT 'Sede',
    cras_unit_id INTEGER REFERENCES social_units(id),
    latitude REAL DEFAULT -22.5268,
    longitude REAL DEFAULT -41.9452,
    total_income REAL DEFAULT 0.0,
    members_count INTEGER DEFAULT 1,
    per_capita_income REAL DEFAULT 0.0,
    income_bracket TEXT DEFAULT 'EXTREMA_POBREZA', -- 'EXTREMA_POBREZA', 'POBREZA', 'BAIXA_RENDA', 'ACIMA_MEIO_SM'
    ivs_score REAL DEFAULT 0.0, -- Índice de Vulnerabilidade Social (0 a 1)
    ivs_level TEXT DEFAULT 'MEDIA', -- 'MUITO_BAIXA', 'BAIXA', 'MEDIA', 'ALTA', 'MUITO_ALTA'
    housing_risk_zone INTEGER DEFAULT 0,
    female_headed INTEGER DEFAULT 0,
    has_elderly INTEGER DEFAULT 0,
    has_pcd INTEGER DEFAULT 0,
    cadastral_completeness_pct REAL DEFAULT 100.0,
    is_cadunico_synced INTEGER DEFAULT 1,
    status TEXT DEFAULT 'ATIVO', -- 'ATIVO', 'ACOMPANHAMENTO_PAIF', 'SUSPENSO', 'TRANSFERIDO'
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 10. Membros Familiares
CREATE TABLE IF NOT EXISTS social_family_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    family_id INTEGER NOT NULL REFERENCES social_families(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    nis TEXT,
    cpf TEXT,
    birth_date TEXT NOT NULL,
    gender TEXT,
    kinship TEXT NOT NULL, -- 'RESPONSAVEL_FAMILIAR', 'CONJUGE', 'FILHO', 'ENTEADO', 'PAI_MAE', 'IRMAO', 'OUTRO'
    schooling TEXT,
    cbo_occupation TEXT,
    individual_income REAL DEFAULT 0.0,
    is_pcd INTEGER DEFAULT 0,
    pcd_type_id INTEGER REFERENCES social_reference_pcd(id),
    is_pregnant INTEGER DEFAULT 0,
    is_lactating INTEGER DEFAULT 0,
    is_elderly INTEGER DEFAULT 0,
    scfv_enrolled INTEGER DEFAULT 0,
    active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 11. Concessões de Benefícios Eventuais
CREATE TABLE IF NOT EXISTS social_benefits_granted (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    family_id INTEGER NOT NULL REFERENCES social_families(id),
    member_id INTEGER REFERENCES social_family_members(id),
    benefit_type TEXT NOT NULL, -- 'CESTA_BASICA', 'AUXILIO_NATALIDADE', 'AUXILIO_FUNERAL', 'VULNERABILIDADE_TEMPORARIA', 'ALUGUEL_SOCIAL', 'PASSE_LIVRE'
    supply_id INTEGER REFERENCES social_supplies(id),
    batch_id INTEGER REFERENCES social_stock_batches(id),
    amount REAL DEFAULT 0.0,
    quantity INTEGER DEFAULT 1,
    request_date TEXT DEFAULT CURRENT_TIMESTAMP,
    technical_opinion TEXT,
    social_worker_cress TEXT NOT NULL,
    social_worker_name TEXT NOT NULL,
    status TEXT DEFAULT 'CONCEDIDO', -- 'SOLICITADO', 'APROVADO', 'CONCEDIDO', 'INDEFERIDO', 'ENTREGUE'
    delivery_date TEXT,
    recipient_signature_hash TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 12. Registro Mensal de Atendimento do CRAS (RMA CRAS)
CREATE TABLE IF NOT EXISTS social_rma_cras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_id INTEGER NOT NULL REFERENCES social_units(id),
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    -- Bloco I: Famílias em acompanhamento pelo PAIF
    paif_total_active INTEGER DEFAULT 0,
    paif_new_inserted INTEGER DEFAULT 0,
    paif_extreme_poverty INTEGER DEFAULT 0,
    paif_bolsa_familia INTEGER DEFAULT 0,
    paif_descumprimento_condicionalidade INTEGER DEFAULT 0,
    paif_bpc INTEGER DEFAULT 0,
    -- Bloco II: Atendimentos Particularizados e Coletivos
    atendimentos_total INTEGER DEFAULT 0,
    visitas_domiciliares INTEGER DEFAULT 0,
    reunioes_coletivas_paif INTEGER DEFAULT 0,
    encaminhamentos_cadunico INTEGER DEFAULT 0,
    encaminhamentos_bpc INTEGER DEFAULT 0,
    encaminhamentos_saude_educacao INTEGER DEFAULT 0,
    -- Bloco III: Benefícios Eventuais
    beneficios_natalidade INTEGER DEFAULT 0,
    beneficios_funeral INTEGER DEFAULT 0,
    beneficios_outros INTEGER DEFAULT 0,
    -- Controle e Fechamento
    status TEXT DEFAULT 'ABERTO', -- 'ABERTO', 'FECHADO', 'TRANSMITIDO_MDS'
    closed_at TEXT,
    closed_by TEXT,
    xml_mds_export TEXT,
    UNIQUE(unit_id, year, month)
);

-- 13. Registro Mensal de Atendimento do CREAS (RMA CREAS)
CREATE TABLE IF NOT EXISTS social_rma_creas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_id INTEGER NOT NULL REFERENCES social_units(id),
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    -- Bloco I: PAEFI (Proteção e Atendimento Especializado a Famílias e Indivíduos)
    paefi_total_active INTEGER DEFAULT 0,
    paefi_new_inserted INTEGER DEFAULT 0,
    paefi_child_violence INTEGER DEFAULT 0,
    paefi_elderly_violence INTEGER DEFAULT 0,
    paefi_woman_violence INTEGER DEFAULT 0,
    paefi_pcd_violence INTEGER DEFAULT 0,
    paefi_child_labor INTEGER DEFAULT 0,
    -- Bloco II: Atendimentos Especializados
    atendimentos_total INTEGER DEFAULT 0,
    orientacoes_juridicas INTEGER DEFAULT 0,
    relatorios_judiciais_emitidos INTEGER DEFAULT 0,
    -- Bloco III: Medidas Socioeducativas em Meio Aberto (SINASE)
    mse_total_adolescentes INTEGER DEFAULT 0,
    mse_liberdade_assistida INTEGER DEFAULT 0,
    mse_prestacao_servicos_comunidade INTEGER DEFAULT 0,
    -- Controle
    status TEXT DEFAULT 'ABERTO',
    closed_at TEXT,
    closed_by TEXT,
    xml_mds_export TEXT,
    UNIQUE(unit_id, year, month)
);

-- 14. Registro Mensal de Atendimento do Centro POP (RMA POP)
CREATE TABLE IF NOT EXISTS social_rma_pop (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_id INTEGER NOT NULL REFERENCES social_units(id),
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    -- Bloco I: Pessoas em Situação de Rua
    pessoas_atendidas_total INTEGER DEFAULT 0,
    homens_atendidos INTEGER DEFAULT 0,
    mulheres_atendidas INTEGER DEFAULT 0,
    migrantes_itinerantes INTEGER DEFAULT 0,
    -- Bloco II: Serviços Prestados
    refeicoes_servidas INTEGER DEFAULT 0,
    atendimentos_higiene INTEGER DEFAULT 0,
    guarda_pertences INTEGER DEFAULT 0,
    -- Bloco III: Encaminhamentos
    encaminhamentos_acolhimento INTEGER DEFAULT 0,
    encaminhamentos_documentacao INTEGER DEFAULT 0,
    encaminhamentos_trabalho_renda INTEGER DEFAULT 0,
    -- Controle
    status TEXT DEFAULT 'ABERTO',
    closed_at TEXT,
    closed_by TEXT,
    xml_mds_export TEXT,
    UNIQUE(unit_id, year, month)
);

-- 15. Acolhimento Institucional e Vagas
CREATE TABLE IF NOT EXISTS social_shelterings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_id INTEGER NOT NULL REFERENCES social_units(id),
    resident_name TEXT NOT NULL,
    resident_cpf_nis TEXT,
    birth_date TEXT,
    admission_date TEXT NOT NULL,
    reason TEXT NOT NULL, -- 'ABANDONO', 'NEGLIGENCIA_GRAVE', 'VIOLENCIA_DOMESTICA', 'SITUACAO_DE_RUA', 'DETERMINACAO_JUDICIAL'
    judicial_process_number TEXT,
    bed_number TEXT,
    discharge_date TEXT,
    discharge_reason TEXT,
    responsible_technician TEXT NOT NULL,
    active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 16. Atendimento com Sigilo Estrito a Mulheres em Situação de Violência
CREATE TABLE IF NOT EXISTS social_violence_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    secret_code TEXT UNIQUE NOT NULL, -- Código de identificação anônimo
    victim_initials TEXT NOT NULL,
    age INTEGER,
    has_children INTEGER DEFAULT 0,
    police_report_number TEXT, -- B.O.
    protective_measure_granted INTEGER DEFAULT 0,
    violence_types TEXT NOT NULL, -- 'FISICA,PSICOLOGICA,PATRIMONIAL,SEXUAL,MORAL'
    aggressor_relationship TEXT,
    shelter_required INTEGER DEFAULT 0,
    technician_cress_crp TEXT NOT NULL,
    date_registered TEXT DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'EM_ACOMPANHAMENTO' -- 'EM_ACOMPANHAMENTO', 'ENCAMINHADA_ABRIGO', 'CONCLUIDO'
);

-- 17. Plano de Acompanhamento Familiar (PAF)
CREATE TABLE IF NOT EXISTS social_paf (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    family_id INTEGER NOT NULL REFERENCES social_families(id),
    cras_unit_id INTEGER NOT NULL REFERENCES social_units(id),
    start_date TEXT DEFAULT CURRENT_TIMESTAMP,
    vulnerabilities_addressed TEXT,
    family_commitments TEXT,
    technical_commitments TEXT,
    agreed_goals TEXT,
    review_date TEXT,
    technician_cress TEXT NOT NULL,
    status TEXT DEFAULT 'EM_ANDAMENTO', -- 'EM_ANDAMENTO', 'METAS_ALCANCADAS', 'DESCONTINUADO'
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 18. Plano Individual de Atendimento (PIA - SINASE / Medidas Socioeducativas)
CREATE TABLE IF NOT EXISTS social_pia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    adolescent_name TEXT NOT NULL,
    adolescent_cpf_nis TEXT,
    judicial_process_number TEXT NOT NULL,
    measure_type TEXT NOT NULL, -- 'LIBERDADE_ASSISTIDA', 'PRESTACAO_SERVICO_COMUNIDADE'
    assigned_entity TEXT,
    educational_goals TEXT,
    community_service_hours INTEGER DEFAULT 0,
    start_date TEXT NOT NULL,
    expected_end_date TEXT NOT NULL,
    actual_end_date TEXT,
    orientator_name TEXT NOT NULL,
    status TEXT DEFAULT 'EM_CUMPRIMENTO',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 19. Catálogo de Cursos, Oficinas e Grupos do SCFV
CREATE TABLE IF NOT EXISTS social_courses_workshops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL, -- 'SCFV_CRIANCAS', 'SCFV_ADOLESCENTES', 'SCFV_IDOSOS', 'GERACAO_RENDA', 'INCLUSAO_DIGITAL'
    description TEXT,
    target_audience TEXT,
    workload_hours INTEGER DEFAULT 40,
    active INTEGER DEFAULT 1
);

-- 20. Turmas do SCFV e Oficinas
CREATE TABLE IF NOT EXISTS social_class_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL REFERENCES social_courses_workshops(id),
    unit_id INTEGER NOT NULL REFERENCES social_units(id),
    instructor_name TEXT NOT NULL,
    schedule_description TEXT NOT NULL, -- ex: 'Terças e Quintas, 14h às 16h'
    max_capacity INTEGER DEFAULT 25,
    start_date TEXT,
    end_date TEXT,
    active INTEGER DEFAULT 1
);

-- 21. Matrículas em Turmas
CREATE TABLE IF NOT EXISTS social_enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER NOT NULL REFERENCES social_class_groups(id),
    family_id INTEGER NOT NULL REFERENCES social_families(id),
    member_id INTEGER REFERENCES social_family_members(id),
    participant_name TEXT NOT NULL,
    enrollment_date TEXT DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'ATIVO' -- 'ATIVO', 'CONCLUIDO', 'EVADIDO'
);

-- 22. Registros de Frequência Diária
CREATE TABLE IF NOT EXISTS social_attendance_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER NOT NULL REFERENCES social_class_groups(id),
    enrollment_id INTEGER NOT NULL REFERENCES social_enrollments(id),
    attendance_date TEXT NOT NULL,
    status TEXT NOT NULL, -- 'PRESENTE', 'FALTA_JUSTIFICADA', 'FALTA_INJUSTIFICADA'
    justification TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 23. Averiguações Cadastrais e Denúncias Sigilosas
CREATE TABLE IF NOT EXISTS social_cadastral_verifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    protocol_number TEXT UNIQUE NOT NULL,
    family_id INTEGER REFERENCES social_families(id),
    source TEXT NOT NULL, -- 'DENUNCIA_SIGILOSA', 'AVERIGUACAO_MDS', 'AUDITORIA_INTERNA', 'DILIGENCIA_TERRITORIAL'
    description TEXT NOT NULL,
    is_confidential INTEGER DEFAULT 1,
    assigned_technician TEXT,
    findings TEXT,
    resolution_status TEXT DEFAULT 'PENDENTE', -- 'PENDENTE', 'EM_DILIGENCIA', 'CONFIRMADO_IRREGULAR', 'IMPROCEDENTE', 'REGULARIZADO'
    resolved_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 24. Despachos e Comunicações Internas entre Unidades
CREATE TABLE IF NOT EXISTS social_internal_dispatches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dispatch_number TEXT UNIQUE NOT NULL,
    origin_unit_id INTEGER NOT NULL REFERENCES social_units(id),
    destination_unit_id INTEGER NOT NULL REFERENCES social_units(id),
    family_id INTEGER REFERENCES social_families(id),
    subject TEXT NOT NULL,
    content TEXT NOT NULL,
    confidential INTEGER DEFAULT 0,
    author_name TEXT NOT NULL,
    status TEXT DEFAULT 'ENVIADO', -- 'ENVIADO', 'RECEBIDO', 'ATENDIDO'
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 25. Assinaturas Digitais ICP-Brasil de Documentos e Pareceres Técnicos
CREATE TABLE IF NOT EXISTS social_digital_signatures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_type TEXT NOT NULL, -- 'PARECER_SOCIAL', 'LAUDO_TECNICO', 'ENCAMINHAMENTO', 'RMA_FECHAMENTO'
    document_id INTEGER NOT NULL,
    signer_name TEXT NOT NULL,
    signer_cpf TEXT NOT NULL,
    signer_role TEXT NOT NULL,
    council_registration TEXT,
    certificate_serial TEXT NOT NULL,
    certificate_issuer TEXT DEFAULT 'Autoridade Certificadora Raiz Brasileira v5 - ICP-Brasil',
    sha256_hash TEXT NOT NULL,
    signature_p7s_mock TEXT,
    timestamp_token TEXT,
    validation_status TEXT DEFAULT 'VALIDO',
    signed_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 26. Programas Municipais de Habitação de Interesse Social
CREATE TABLE IF NOT EXISTS social_housing_programs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    legal_basis TEXT NOT NULL,
    funding_source TEXT DEFAULT 'Fundo Municipal de Habitação de Interesse Social (FMHIS)',
    target_population TEXT DEFAULT 'Famílias com renda de 0 a 3 salários mínimos',
    active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 27. Conjuntos Habitacionais
CREATE TABLE IF NOT EXISTS social_housing_complexes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_id INTEGER NOT NULL REFERENCES social_housing_programs(id),
    name TEXT NOT NULL,
    neighborhood TEXT NOT NULL,
    total_units INTEGER NOT NULL,
    available_units INTEGER NOT NULL,
    reserved_elderly_quota INTEGER DEFAULT 0, -- Cota legal de idosos (min 3%)
    reserved_pcd_quota INTEGER DEFAULT 0,     -- Cota legal PCD (min 3%)
    active INTEGER DEFAULT 1
);

-- 28. Critérios Objetivos de Pontuação Habitacional
CREATE TABLE IF NOT EXISTS social_housing_criteria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    description TEXT NOT NULL,
    points INTEGER NOT NULL,
    legal_mandatory INTEGER DEFAULT 0,
    active INTEGER DEFAULT 1
);

-- 29. Inscrições e Classificação Habitacional
CREATE TABLE IF NOT EXISTS social_housing_applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_number TEXT UNIQUE NOT NULL,
    program_id INTEGER NOT NULL REFERENCES social_housing_programs(id),
    complex_id INTEGER REFERENCES social_housing_complexes(id),
    family_id INTEGER NOT NULL REFERENCES social_families(id),
    auto_calculated_points INTEGER DEFAULT 0,
    manual_adjusted_points INTEGER DEFAULT 0,
    adjustment_reason TEXT,
    adjusted_by TEXT,
    final_points INTEGER DEFAULT 0,
    special_quota TEXT DEFAULT 'GERAL', -- 'GERAL', 'IDOSO', 'PCD'
    ranking_position INTEGER,
    status TEXT DEFAULT 'INSCRITO', -- 'INSCRITO', 'HABILITADO', 'CONTEMPLADO', 'RESERVA', 'DESQUALIFICADO'
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 30. Índice de Vulnerabilidade Social Inteligente (IVS)
CREATE TABLE IF NOT EXISTS social_ivs_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    family_id INTEGER NOT NULL REFERENCES social_families(id),
    infrastructure_score REAL NOT NULL, -- Coleta de lixo, esgoto, água encanada, energia
    human_capital_score REAL NOT NULL,  -- Escolaridade, gestante/idoso/PCD, crianças fora da escola
    income_labor_score REAL NOT NULL,   -- Renda per capita, desemprego, dependência financeira
    global_ivs REAL NOT NULL,           -- Média ponderada (0 a 1)
    vulnerability_tier TEXT NOT NULL,   -- 'MUITO_BAIXA', 'BAIXA', 'MEDIA', 'ALTA', 'MUITO_ALTA'
    calculation_details_json TEXT,
    calculated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 31. Organizações da Sociedade Civil (MROSC - Lei Federal 13.019/2014)
CREATE TABLE IF NOT EXISTS social_oscs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cnpj TEXT UNIQUE NOT NULL,
    corporate_name TEXT NOT NULL,
    trade_name TEXT,
    legal_representative TEXT NOT NULL,
    representative_cpf TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    address TEXT NOT NULL,
    cnd_federal_valid_until TEXT,
    cnd_state_valid_until TEXT,
    cnd_municipal_valid_until TEXT,
    fgts_crf_valid_until TEXT,
    cndt_labor_valid_until TEXT,
    registration_status TEXT DEFAULT 'REGULAR', -- 'REGULAR', 'PENDENTE_CERTIDAO', 'SUSPENSA'
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 32. Planos de Trabalho MROSC
CREATE TABLE IF NOT EXISTS social_osc_work_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    osc_id INTEGER NOT NULL REFERENCES social_oscs(id),
    title TEXT NOT NULL,
    object_summary TEXT NOT NULL,
    justification TEXT NOT NULL,
    target_public TEXT,
    goals_json TEXT, -- Metas físicas quantitativas e qualitativas
    financial_schedule_json TEXT, -- Cronograma de desembolso mensal
    total_requested_amount REAL NOT NULL,
    technical_opinion TEXT,
    approval_status TEXT DEFAULT 'EM_ANALISE', -- 'EM_ANALISE', 'APROVADO', 'REJEITADO', 'AJUSTES_SOLICITADOS'
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 33. Instrumentos de Parceria MROSC (Termo de Fomento / Colaboração)
CREATE TABLE IF NOT EXISTS social_osc_contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_plan_id INTEGER NOT NULL REFERENCES social_osc_work_plans(id),
    osc_id INTEGER NOT NULL REFERENCES social_oscs(id),
    partnership_type TEXT NOT NULL, -- 'TERMO_DE_COLABORACAO', 'TERMO_DE_FOMENTO', 'ACORDO_DE_COOPERACAO'
    contract_number TEXT UNIQUE NOT NULL,
    signature_date TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    global_value REAL NOT NULL,
    budget_allocation_code TEXT NOT NULL,
    dedicated_bank_account TEXT NOT NULL, -- Conta bancária vinculada e exclusiva
    public_manager_name TEXT NOT NULL,
    status TEXT DEFAULT 'VIGENTE', -- 'VIGENTE', 'CONCLUIDO', 'RESCINDIDO'
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 34. Prestações de Contas Mensais MROSC
CREATE TABLE IF NOT EXISTS social_osc_monthly_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL REFERENCES social_osc_contracts(id),
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    previous_balance REAL DEFAULT 0.0,
    disbursement_received REAL DEFAULT 0.0,
    financial_income REAL DEFAULT 0.0,
    expenses_total REAL DEFAULT 0.0,
    current_balance REAL DEFAULT 0.0,
    bank_reconciled INTEGER DEFAULT 1,
    expenses_details_json TEXT,
    review_status TEXT DEFAULT 'SUBMETIDA', -- 'SUBMETIDA', 'APROVADA', 'APROVADA_COM_RESSALVA', 'REJEITADA'
    review_notes TEXT,
    reviewer_name TEXT,
    reviewed_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(contract_id, year, month)
);

-- 35. Prestações de Contas Anuais e Finais MROSC
CREATE TABLE IF NOT EXISTS social_osc_annual_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL REFERENCES social_osc_contracts(id),
    year INTEGER NOT NULL,
    final_execution_report TEXT,
    goal_achievement_percentage REAL DEFAULT 100.0,
    unexpended_balance_returned REAL DEFAULT 0.0,
    audit_opinion TEXT,
    final_status TEXT DEFAULT 'EM_ANALISE', -- 'EM_ANALISE', 'APROVADA', 'REJEITADA_TOMADA_CONTAS'
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 36. Relatórios de Monitoramento e Avaliação das Parcerias
CREATE TABLE IF NOT EXISTS social_osc_monitoring_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL REFERENCES social_osc_contracts(id),
    report_number TEXT NOT NULL,
    visit_date TEXT NOT NULL,
    inspectors_names TEXT NOT NULL,
    beneficiaries_interviewed_count INTEGER DEFAULT 0,
    on_site_compliance_score REAL DEFAULT 10.0, -- Nota de 0 a 10
    recommendations TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 37. Conectores e Importadores de Bases Externas (CadÚnico, SICON, Sibec, CECAD, BPC)
CREATE TABLE IF NOT EXISTS social_external_imports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_system TEXT NOT NULL, -- 'CADUNICO_V7_V8', 'SICON_CONDICIONALIDADES', 'SIBEC_BOLSA_FAMILIA', 'CECAD_TABULADOR', 'BPC_LOAS'
    file_name TEXT NOT NULL,
    file_size_bytes INTEGER DEFAULT 0,
    file_sha256 TEXT,
    total_records INTEGER DEFAULT 0,
    records_imported INTEGER DEFAULT 0,
    records_with_inconsistency INTEGER DEFAULT 0,
    inconsistencies_summary_json TEXT,
    imported_by TEXT NOT NULL,
    imported_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Índices de Alta Performance
CREATE INDEX IF NOT EXISTS idx_social_units_type ON social_units(unit_type);
CREATE INDEX IF NOT EXISTS idx_social_teams_unit ON social_teams(unit_id);
CREATE INDEX IF NOT EXISTS idx_social_families_cras ON social_families(cras_unit_id);
CREATE INDEX IF NOT EXISTS idx_social_families_head_nis ON social_families(head_nis);
CREATE INDEX IF NOT EXISTS idx_social_members_family ON social_family_members(family_id);
CREATE INDEX IF NOT EXISTS idx_social_benefits_family ON social_benefits_granted(family_id);
CREATE INDEX IF NOT EXISTS idx_social_rma_cras_ym ON social_rma_cras(year, month);
CREATE INDEX IF NOT EXISTS idx_social_rma_creas_ym ON social_rma_creas(year, month);
CREATE INDEX IF NOT EXISTS idx_social_rma_pop_ym ON social_rma_pop(year, month);
CREATE INDEX IF NOT EXISTS idx_social_shelterings_unit ON social_shelterings(unit_id);
CREATE INDEX IF NOT EXISTS idx_social_housing_appl_fam ON social_housing_applications(family_id);
CREATE INDEX IF NOT EXISTS idx_social_osc_contracts_osc ON social_osc_contracts(osc_id);

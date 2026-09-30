-- ============================================================================
-- RIO GESTÃO / ERP RIO DAS OSTRAS - MÓDULO DE GESTÃO DE PESSOAS E RH
-- Conformidade Integral com o Anexo III do Edital PE 552/2026 (117 Itens)
-- ============================================================================

-- Cadastro Base de Cargos e Servidores
CREATE TABLE IF NOT EXISTS people_positions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  vacancies INTEGER NOT NULL DEFAULT 10,
  salary NUMERIC NOT NULL DEFAULT 3500.00,
  hours INTEGER NOT NULL DEFAULT 40,
  active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS people_employees (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  cpf TEXT NOT NULL,
  position TEXT NOT NULL DEFAULT 'Assistente Administrativo',
  department TEXT NOT NULL DEFAULT 'LOC-ADM',
  cost_center TEXT NOT NULL DEFAULT 'CC-ADM-01',
  admission TEXT NOT NULL DEFAULT '2020-01-15',
  regime TEXT NOT NULL DEFAULT 'RPPS',
  salary NUMERIC NOT NULL DEFAULT 3500.00,
  active INTEGER NOT NULL DEFAULT 1,
  email TEXT NOT NULL DEFAULT 'servidor@riodasostras.rj.gov.br',
  created_at TEXT NOT NULL
);

-- 1. Replicação e Multi-Entidades (Itens 1 a 4)
CREATE TABLE IF NOT EXISTS people_entities_replication (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_entity TEXT NOT NULL,
  target_simulation_entity TEXT NOT NULL,
  replicated_at TEXT NOT NULL,
  replicated_by TEXT NOT NULL,
  include_positions INTEGER NOT NULL DEFAULT 1,
  include_employees INTEGER NOT NULL DEFAULT 1,
  include_locations INTEGER NOT NULL DEFAULT 1,
  include_events INTEGER NOT NULL DEFAULT 1,
  status TEXT NOT NULL DEFAULT 'COMPLETED',
  notes TEXT
);

CREATE TABLE IF NOT EXISTS people_work_locations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  entity_id TEXT NOT NULL DEFAULT 'MUNICIPIO',
  code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  department TEXT,
  cost_centers TEXT NOT NULL DEFAULT '["CC-01","CC-02"]',
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS people_location_movements (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_id INTEGER NOT NULL,
  origin_location_code TEXT NOT NULL,
  destination_location_code TEXT NOT NULL,
  movement_date TEXT NOT NULL,
  reason TEXT,
  registered_by TEXT NOT NULL,
  created_at TEXT NOT NULL
);

-- 2. Fundos Previdenciários RPPS (Itens 5, 6, 11, 48)
CREATE TABLE IF NOT EXISTS people_rpps_funds (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  employee_rate NUMERIC NOT NULL DEFAULT 14.00,
  patronal_rate NUMERIC NOT NULL DEFAULT 22.00,
  supplementary_rate NUMERIC NOT NULL DEFAULT 6.50,
  is_progressive INTEGER NOT NULL DEFAULT 1,
  progressive_brackets TEXT NOT NULL DEFAULT '[]',
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS people_rpps_guides (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  fund_code TEXT NOT NULL,
  competence TEXT NOT NULL,
  total_base NUMERIC NOT NULL DEFAULT 0.00,
  total_employee_retained NUMERIC NOT NULL DEFAULT 0.00,
  total_patronal NUMERIC NOT NULL DEFAULT 0.00,
  total_supplementary NUMERIC NOT NULL DEFAULT 0.00,
  total_guide NUMERIC NOT NULL DEFAULT 0.00,
  due_date TEXT NOT NULL,
  barcode TEXT,
  status TEXT NOT NULL DEFAULT 'EMITIDA',
  generated_at TEXT NOT NULL,
  generated_by TEXT NOT NULL
);

-- 3. Consignações e eConsignado (Itens 7, 8, 19)
CREATE TABLE IF NOT EXISTS people_consignments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_id INTEGER NOT NULL,
  consignee_name TEXT NOT NULL,
  contract_number TEXT NOT NULL,
  event_code TEXT NOT NULL,
  installment_value NUMERIC NOT NULL,
  current_installment INTEGER NOT NULL DEFAULT 1,
  total_installments INTEGER NOT NULL DEFAULT 48,
  priority_order INTEGER NOT NULL DEFAULT 1,
  status TEXT NOT NULL DEFAULT 'ATIVO',
  start_competence TEXT NOT NULL,
  end_competence TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS people_consignable_margins (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_id INTEGER NOT NULL UNIQUE,
  gross_remuneration NUMERIC NOT NULL DEFAULT 0.00,
  mandatory_deductions NUMERIC NOT NULL DEFAULT 0.00,
  margin_base NUMERIC NOT NULL DEFAULT 0.00,
  max_margin_pct NUMERIC NOT NULL DEFAULT 35.00,
  max_card_margin_pct NUMERIC NOT NULL DEFAULT 5.00,
  used_margin NUMERIC NOT NULL DEFAULT 0.00,
  available_margin NUMERIC NOT NULL DEFAULT 0.00,
  last_updated TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS people_econsignado_batches (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  file_name TEXT NOT NULL,
  format TEXT NOT NULL, -- 'CSV', 'XLS', 'JSON'
  total_records INTEGER NOT NULL DEFAULT 0,
  imported_records INTEGER NOT NULL DEFAULT 0,
  divergent_records INTEGER NOT NULL DEFAULT 0,
  rejected_records INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'PROCESSADO',
  include_terminated INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  created_by TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS people_econsignado_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  batch_id INTEGER NOT NULL,
  registration TEXT NOT NULL,
  employee_name TEXT NOT NULL,
  cpf TEXT NOT NULL,
  event_code TEXT NOT NULL,
  discount_value NUMERIC NOT NULL,
  installments TEXT,
  status TEXT NOT NULL, -- 'OK', 'EXCEEDED_MARGIN', 'TERMINATED_EMPLOYEE', 'EMPLOYEE_NOT_FOUND'
  rejection_reason TEXT
);

-- 4. Quadro de Vagas e Cargos (Itens 9, 39, 41, 42)
CREATE TABLE IF NOT EXISTS people_positions_vacancies (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  position_id INTEGER NOT NULL,
  work_location_code TEXT NOT NULL,
  budgeted_vacancies INTEGER NOT NULL DEFAULT 10,
  filled_vacancies INTEGER NOT NULL DEFAULT 0,
  available_vacancies INTEGER NOT NULL DEFAULT 10,
  restriction_mode TEXT NOT NULL DEFAULT 'BLOQUEIO', -- 'BLOQUEIO', 'ADVERTENCIA', 'SEM_RESTRICAO'
  salary_floor NUMERIC NOT NULL DEFAULT 1412.00,
  salary_ceiling NUMERIC NOT NULL DEFAULT 35000.00,
  updated_at TEXT NOT NULL
);

-- 5. Multi-Vínculo, Cópia de Registro e Substituição (Itens 11, 12, 13, 24, 25)
CREATE TABLE IF NOT EXISTS people_substitutes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  original_employee_id INTEGER NOT NULL,
  substitute_employee_id INTEGER NOT NULL,
  new_registration TEXT NOT NULL UNIQUE,
  position_id INTEGER NOT NULL,
  start_date TEXT NOT NULL,
  end_date TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'ATIVO', -- 'ATIVO', 'ENCERRADO_AUTOMATICO'
  notes TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS people_external_employments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_id INTEGER NOT NULL,
  employer_cnpj TEXT NOT NULL,
  employer_name TEXT NOT NULL,
  monthly_contribution_base NUMERIC NOT NULL,
  esocial_category TEXT NOT NULL DEFAULT '101',
  valid_from TEXT NOT NULL,
  valid_to TEXT,
  inss_retained NUMERIC NOT NULL DEFAULT 0.00,
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL
);

-- 6. Reintegração Judicial e Beneficiários de Pensão (Itens 14, 15, 32)
CREATE TABLE IF NOT EXISTS people_reintegrations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_id INTEGER NOT NULL,
  reintegration_type TEXT NOT NULL, -- 'JUDICIAL', 'ANISTIA', 'ADMINISTRATIVA'
  legal_process_number TEXT NOT NULL,
  amnesty_law TEXT,
  judicial_remuneration_flag INTEGER NOT NULL DEFAULT 1,
  effective_date TEXT NOT NULL,
  retroactive_date TEXT,
  status TEXT NOT NULL DEFAULT 'EFETIVADA',
  created_at TEXT NOT NULL,
  created_by TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS people_judicial_alimonies (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_id INTEGER NOT NULL,
  beneficiary_name TEXT NOT NULL,
  beneficiary_cpf TEXT NOT NULL,
  birth_date TEXT NOT NULL,
  cutoff_age INTEGER NOT NULL DEFAULT 24, -- Limite de idade configurável
  calculation_mode TEXT NOT NULL DEFAULT 'PERCENTAGE_NET', -- 'PERCENTAGE_NET', 'PERCENTAGE_GROSS', 'FIXED'
  value_rate NUMERIC NOT NULL DEFAULT 20.00,
  bank_name TEXT,
  bank_account TEXT,
  status TEXT NOT NULL DEFAULT 'ATIVO', -- 'ATIVO', 'CESSADO_AUTOMATICO'
  cessation_date TEXT,
  created_at TEXT NOT NULL
);

-- 7. Operadoras de Plano de Saúde e Vale-Transporte (Itens 16, 17)
CREATE TABLE IF NOT EXISTS people_health_plans (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  operator_code TEXT NOT NULL UNIQUE,
  operator_name TEXT NOT NULL,
  cnpj TEXT NOT NULL,
  ans_register TEXT NOT NULL,
  calculation_mode TEXT NOT NULL DEFAULT 'AGE_BRACKET', -- 'FIXED', 'AGE_BRACKET', 'PERCENTAGE_BASE'
  fixed_value NUMERIC NOT NULL DEFAULT 0.00,
  base_percentage NUMERIC NOT NULL DEFAULT 0.00,
  entity_coparticipation_pct NUMERIC NOT NULL DEFAULT 50.00,
  spouse_coparticipation_pct NUMERIC NOT NULL DEFAULT 0.00,
  age_brackets TEXT NOT NULL DEFAULT '[]', -- JSON [{'min_age': 0, 'max_age': 18, 'value': 120.00}, ...]
  dirf_code TEXT NOT NULL DEFAULT '3568',
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS people_transport_vouchers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  company_code TEXT NOT NULL,
  company_name TEXT NOT NULL,
  line_code TEXT NOT NULL,
  line_name TEXT NOT NULL,
  fare_value NUMERIC NOT NULL,
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS people_employee_transport (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_id INTEGER NOT NULL,
  line_id INTEGER NOT NULL,
  daily_trips INTEGER NOT NULL DEFAULT 2,
  working_days INTEGER NOT NULL DEFAULT 22,
  monthly_total NUMERIC NOT NULL,
  employee_deduction NUMERIC NOT NULL, -- Max 6% base salary
  entity_burden NUMERIC NOT NULL,
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL
);

-- 8. Movimentações de Pessoal e Histórico Funcional (Itens 18, 20, 21, 22, 26, 37)
CREATE TABLE IF NOT EXISTS people_movements_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_id INTEGER NOT NULL,
  movement_type TEXT NOT NULL, -- 'ADMISSAO', 'DEMISSAO', 'PROMOCAO', 'PROGRESSAO', 'CEDENCIA', 'AFASTAMENTO', 'FALTA', 'REAJUSTE', 'SUBSTITUICAO'
  movement_date TEXT NOT NULL,
  effective_date TEXT NOT NULL,
  old_value TEXT,
  new_value TEXT,
  legal_act_id INTEGER,
  notes TEXT,
  registered_by TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS people_transfers_burden (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_id INTEGER NOT NULL,
  transfer_type TEXT NOT NULL, -- 'CEDIDO', 'RECEBIDO'
  partner_entity TEXT NOT NULL,
  partner_cnpj TEXT NOT NULL,
  burden_type TEXT NOT NULL, -- 'COM_ONUS_CEDENTE', 'COM_ONUS_CESSIONARIO', 'SEM_ONUS'
  start_date TEXT NOT NULL,
  end_date TEXT NOT NULL,
  auto_closed INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'ATIVO',
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS people_commission_assignments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_id INTEGER NOT NULL,
  commission_position_id INTEGER NOT NULL,
  salary_band TEXT NOT NULL,
  commission_salary NUMERIC NOT NULL,
  start_date TEXT NOT NULL,
  end_date TEXT NOT NULL,
  auto_reverted INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'ATIVO',
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS people_disciplinary_acts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_id INTEGER NOT NULL,
  act_type TEXT NOT NULL, -- 'ELOGIO', 'ADVERTENCIA', 'SUSPENSAO', 'DEMISSAO'
  description TEXT NOT NULL,
  legal_process TEXT,
  act_date TEXT NOT NULL,
  registered_by TEXT NOT NULL,
  created_at TEXT NOT NULL
);

-- 9. Reajustes Salariais e Simulações (Itens 23, 45)
CREATE TABLE IF NOT EXISTS people_salary_adjustments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  adjustment_mode TEXT NOT NULL, -- 'PERCENTUAL', 'VALOR_FIXO'
  adjustment_value NUMERIC NOT NULL,
  scope_type TEXT NOT NULL, -- 'GERAL', 'CARGO', 'FAIXA_SALARIAL', 'VERBA'
  scope_id TEXT,
  is_simulated INTEGER NOT NULL DEFAULT 1,
  status TEXT NOT NULL DEFAULT 'SIMULADO', -- 'SIMULADO', 'EFETIVADO', 'CANCELADO'
  effective_date TEXT,
  impacted_employees INTEGER NOT NULL DEFAULT 0,
  total_old_cost NUMERIC NOT NULL DEFAULT 0.00,
  total_new_cost NUMERIC NOT NULL DEFAULT 0.00,
  created_at TEXT NOT NULL,
  created_by TEXT NOT NULL
);

-- 10. Férias, 13º Salário e Rescisões (Itens 27, 28, 29, 30, 31)
CREATE TABLE IF NOT EXISTS people_vacations_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_id INTEGER NOT NULL,
  vesting_start TEXT NOT NULL,
  vesting_end TEXT NOT NULL,
  vesting_status TEXT NOT NULL DEFAULT 'FECHADO', -- 'ABERTO', 'FECHADO'
  enjoyment_start TEXT NOT NULL,
  enjoyment_end TEXT NOT NULL,
  days_enjoyed INTEGER NOT NULL DEFAULT 30,
  allowance_days INTEGER NOT NULL DEFAULT 0,
  advance_13th INTEGER NOT NULL DEFAULT 0,
  is_interrupted INTEGER NOT NULL DEFAULT 0,
  interruption_reason TEXT,
  interruption_start TEXT,
  interruption_end TEXT,
  new_resumption_date TEXT,
  status TEXT NOT NULL DEFAULT 'PROGRAMADA', -- 'PROGRAMADA', 'USUFRUIDA', 'INTERROMPIDA'
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS people_severance_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_id INTEGER NOT NULL,
  termination_date TEXT NOT NULL,
  termination_type TEXT NOT NULL, -- 'EXONERACAO_A_PEDIDO', 'DEMISSAO_JUSTA_CAUSA', 'DEMISSAO_SEM_JUSTA_CAUSA', 'APOSENTADORIA', 'FALECIMENTO'
  notice_type TEXT NOT NULL DEFAULT 'INDENIZADO', -- 'TRABALHADO', 'INDENIZADO', 'DISPENSADO'
  notice_date TEXT NOT NULL,
  notice_canceled INTEGER NOT NULL DEFAULT 0,
  gross_severance NUMERIC NOT NULL DEFAULT 0.00,
  deductions NUMERIC NOT NULL DEFAULT 0.00,
  net_severance NUMERIC NOT NULL DEFAULT 0.00,
  homolognet_xml TEXT,
  status TEXT NOT NULL DEFAULT 'CALCULADA',
  created_at TEXT NOT NULL
);

-- 11. Benefícios por Tempo de Serviço (Itens 40, 43)
CREATE TABLE IF NOT EXISTS people_service_benefits (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_id INTEGER NOT NULL,
  benefit_type TEXT NOT NULL, -- 'ANUENIO', 'TRIENIO', 'QUINQUENIO', 'LICENCA_PREMIO', 'PROGRESSAO'
  period_start TEXT NOT NULL,
  period_end TEXT NOT NULL,
  is_closed INTEGER NOT NULL DEFAULT 1,
  percentage NUMERIC NOT NULL DEFAULT 5.00,
  status TEXT NOT NULL DEFAULT 'CONCEDIDO', -- 'CONCEDIDO', 'SUSPENSO', 'PERDIDO', 'PRORROGADO'
  days_suspended INTEGER NOT NULL DEFAULT 0,
  suspension_reason TEXT,
  created_at TEXT NOT NULL
);

-- 12. Folha Complementar, Retroativa e Provisões Contábeis (Itens 46, 47, 51, 52, 53)
CREATE TABLE IF NOT EXISTS people_retroactive_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  competence_reference TEXT NOT NULL,
  employee_id INTEGER NOT NULL,
  reason TEXT NOT NULL,
  total_difference NUMERIC NOT NULL,
  installments_count INTEGER NOT NULL DEFAULT 1,
  installments_paid INTEGER NOT NULL DEFAULT 0,
  balance_remaining NUMERIC NOT NULL DEFAULT 0.00,
  status TEXT NOT NULL DEFAULT 'EM_ANDAMENTO',
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS people_monthly_locks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  competence TEXT NOT NULL UNIQUE,
  is_locked INTEGER NOT NULL DEFAULT 1,
  locked_at TEXT NOT NULL,
  locked_by TEXT NOT NULL,
  unlocked_at TEXT,
  unlocked_by TEXT
);

CREATE TABLE IF NOT EXISTS people_accounting_provisions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  competence TEXT NOT NULL,
  provision_type TEXT NOT NULL, -- 'FERIAS', '13_SALARIO', 'LICENCA_PREMIO'
  previous_balance NUMERIC NOT NULL DEFAULT 0.00,
  monthly_accrual NUMERIC NOT NULL DEFAULT 0.00,
  discharges NUMERIC NOT NULL DEFAULT 0.00,
  total_balance NUMERIC NOT NULL DEFAULT 0.00,
  patronal_charges NUMERIC NOT NULL DEFAULT 0.00,
  debit_account TEXT NOT NULL DEFAULT '3.1.1.1.1.01.00',
  credit_account TEXT NOT NULL DEFAULT '2.1.1.1.1.01.00',
  calculated_at TEXT NOT NULL
);

-- 13. Confronto com SISOBI (Item 61)
CREATE TABLE IF NOT EXISTS people_sisobi_batches (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  filename TEXT NOT NULL,
  import_date TEXT NOT NULL,
  total_records INTEGER NOT NULL DEFAULT 0,
  deaths_detected INTEGER NOT NULL DEFAULT 0,
  active_employees_dead INTEGER NOT NULL DEFAULT 0,
  pensioners_dead INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'AVERIGUADO',
  imported_by TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS people_sisobi_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  batch_id INTEGER NOT NULL,
  deceased_cpf TEXT NOT NULL,
  deceased_name TEXT NOT NULL,
  death_date TEXT NOT NULL,
  cartorio_certidao TEXT,
  matched_employee_id INTEGER,
  matched_registration TEXT,
  matched_status TEXT, -- 'ATIVO_BLOQUEADO', 'PENSIONISTA_BLOQUEADO', 'NAO_LOCALIZADO'
  created_at TEXT NOT NULL
);

-- 14. Portal do Servidor e Atualização Cadastral (Itens 70 a 82)
CREATE TABLE IF NOT EXISTS people_server_portal_users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_id INTEGER NOT NULL UNIQUE,
  cpf TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  email TEXT NOT NULL,
  reset_token TEXT,
  reset_token_expires TEXT,
  access_status TEXT NOT NULL DEFAULT 'ATIVO', -- 'ATIVO', 'BLOQUEADO', 'DIVERGENTE'
  last_login TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS people_server_portal_updates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_id INTEGER NOT NULL,
  field_name TEXT NOT NULL,
  old_value TEXT,
  new_value TEXT,
  proof_file TEXT,
  requires_proof INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'PENDENTE', -- 'PENDENTE', 'VALIDADO_RH', 'REJEITADO_RH'
  reviewed_by TEXT,
  reviewed_at TEXT,
  rejection_notes TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS people_payslip_settings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  entity_code TEXT NOT NULL UNIQUE,
  show_logo INTEGER NOT NULL DEFAULT 1,
  logo_url TEXT,
  watermark_text TEXT NOT NULL DEFAULT 'PREFEITURA MUNICIPAL DE RIO DAS OSTRAS',
  enable_qr_code INTEGER NOT NULL DEFAULT 1,
  secret_qr_key TEXT NOT NULL DEFAULT 'RIO-GESTAO-AUTH-KEY-2026',
  header_layout TEXT NOT NULL DEFAULT 'STANDARD',
  updated_at TEXT NOT NULL
);

-- 15. Atos Legais e Efetividade (Itens 82 a 86)
CREATE TABLE IF NOT EXISTS people_legal_acts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  act_type TEXT NOT NULL, -- 'PORTARIA', 'DECRETO', 'REQUISICAO', 'LEI'
  act_number TEXT NOT NULL,
  act_year INTEGER NOT NULL,
  publication_date TEXT NOT NULL,
  summary TEXT NOT NULL,
  content TEXT,
  is_effectiveness INTEGER NOT NULL DEFAULT 1,
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS people_service_certifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_id INTEGER NOT NULL,
  certification_number TEXT NOT NULL UNIQUE,
  issue_date TEXT NOT NULL,
  total_municipal_days INTEGER NOT NULL,
  total_previous_days INTEGER NOT NULL DEFAULT 0,
  total_effective_days INTEGER NOT NULL,
  effectiveness_grid TEXT NOT NULL, -- JSON detailed breakdown by year/month
  issued_by TEXT NOT NULL,
  sha256_hash TEXT NOT NULL
);

-- 16. eSocial S-1.3 - Parametrizações, Rubricas, Totalizadores e Diagnóstico (Itens 87 a 108)
CREATE TABLE IF NOT EXISTS people_esocial_configs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tp_amb INTEGER NOT NULL DEFAULT 2, -- 1=Produção, 2=Homologação/Sandbox
  proc_emi INTEGER NOT NULL DEFAULT 1, -- 1=App Empregador
  ver_proc TEXT NOT NULL DEFAULT 'S-1.3',
  cnpj_matriz TEXT NOT NULL DEFAULT '29.138.078/0001-50',
  responsible_name TEXT NOT NULL DEFAULT 'SECRETARIO DE ADMINISTRACAO',
  responsible_cpf TEXT NOT NULL DEFAULT '111.222.333-44',
  responsible_email TEXT NOT NULL DEFAULT 'rh@riodasostras.rj.gov.br',
  responsible_phone TEXT NOT NULL DEFAULT '(22) 2771-6000',
  token_enabled INTEGER NOT NULL DEFAULT 1,
  a1_cert_valid_until TEXT NOT NULL DEFAULT '2027-12-31',
  a1_cert_alias TEXT NOT NULL DEFAULT 'PMRO_CERT_2026',
  last_sync TEXT
);

CREATE TABLE IF NOT EXISTS people_esocial_rubrics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_code TEXT NOT NULL UNIQUE,
  rubric_name TEXT NOT NULL,
  nat_rubr TEXT NOT NULL, -- Tabela 03 do eSocial
  tp_rubr INTEGER NOT NULL DEFAULT 1, -- 1=Vencimento, 2=Desconto, 3=Informativa
  cod_inc_cprp TEXT NOT NULL DEFAULT '11', -- Tabela 21 incidência RPPS/RGPS
  cod_inc_irrf TEXT NOT NULL DEFAULT '11', -- Tabela 22 incidência IRRF
  cod_inc_fgts TEXT NOT NULL DEFAULT '00', -- Tabela 23 incidência FGTS
  active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS people_esocial_totalizers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  competence TEXT NOT NULL,
  system_inss_base NUMERIC NOT NULL DEFAULT 0.00,
  esocial_inss_base NUMERIC NOT NULL DEFAULT 0.00,
  system_inss_employee NUMERIC NOT NULL DEFAULT 0.00,
  esocial_inss_employee NUMERIC NOT NULL DEFAULT 0.00,
  system_inss_patronal NUMERIC NOT NULL DEFAULT 0.00,
  esocial_inss_patronal NUMERIC NOT NULL DEFAULT 0.00,
  system_maternity NUMERIC NOT NULL DEFAULT 0.00,
  esocial_maternity NUMERIC NOT NULL DEFAULT 0.00,
  system_family NUMERIC NOT NULL DEFAULT 0.00,
  esocial_family NUMERIC NOT NULL DEFAULT 0.00,
  system_fgts_base NUMERIC NOT NULL DEFAULT 0.00,
  esocial_fgts_base NUMERIC NOT NULL DEFAULT 0.00,
  system_fgts_value NUMERIC NOT NULL DEFAULT 0.00,
  esocial_fgts_value NUMERIC NOT NULL DEFAULT 0.00,
  system_irrf_base NUMERIC NOT NULL DEFAULT 0.00,
  esocial_irrf_base NUMERIC NOT NULL DEFAULT 0.00,
  system_irrf_value NUMERIC NOT NULL DEFAULT 0.00,
  esocial_irrf_value NUMERIC NOT NULL DEFAULT 0.00,
  employees_count INTEGER NOT NULL DEFAULT 0,
  divergence_count INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'CONCILIADO',
  reconciled_at TEXT NOT NULL
);

-- 17. SST - Saúde e Segurança do Trabalho / PPP (Itens 109 a 117)
CREATE TABLE IF NOT EXISTS people_sst_monitors (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  responsible_type TEXT NOT NULL, -- 'BIOLOGICA', 'AMBIENTAL'
  professional_name TEXT NOT NULL,
  professional_council TEXT NOT NULL, -- 'CRM', 'CREA'
  council_number TEXT NOT NULL,
  council_uf TEXT NOT NULL DEFAULT 'RJ',
  start_period TEXT NOT NULL,
  end_period TEXT,
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS people_sst_risks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_id INTEGER NOT NULL,
  risk_factor_code TEXT NOT NULL, -- Tabela 24 eSocial
  risk_description TEXT NOT NULL,
  risk_type TEXT NOT NULL, -- 'FISICO', 'QUIMICO', 'BIOLOGICO', 'ERGONOMICO', 'ACIDENTE'
  intensity_concentration TEXT,
  measurement_technique TEXT,
  epc_effective INTEGER NOT NULL DEFAULT 1,
  epi_effective INTEGER NOT NULL DEFAULT 1,
  start_date TEXT NOT NULL,
  end_date TEXT,
  active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS people_sst_aso (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_id INTEGER NOT NULL,
  aso_type TEXT NOT NULL, -- 'ADMISSIONAL', 'PERIODICO', 'RETORNO_TRABALHO', 'MUDANCA_FUNCAO', 'DEMISSIONAL'
  exam_date TEXT NOT NULL,
  result TEXT NOT NULL DEFAULT 'APTO', -- 'APTO', 'INAPTO'
  doctor_name TEXT NOT NULL,
  doctor_crm TEXT NOT NULL,
  doctor_uf TEXT NOT NULL DEFAULT 'RJ',
  complementary_exams TEXT NOT NULL DEFAULT '[]', -- JSON list of exams
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS people_sst_cat (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_id INTEGER NOT NULL,
  cat_number TEXT NOT NULL UNIQUE,
  cat_type TEXT NOT NULL DEFAULT 'INICIAL', -- 'INICIAL', 'REABERTURA', 'COMUNICACAO_OBITO'
  accident_date TEXT NOT NULL,
  accident_time TEXT NOT NULL,
  accident_type TEXT NOT NULL, -- 'TIPICO', 'TRAJETO', 'DOENCA'
  hours_worked_before NUMERIC NOT NULL DEFAULT 4.0,
  accident_location TEXT NOT NULL,
  cep TEXT NOT NULL,
  address_street TEXT NOT NULL,
  address_neighborhood TEXT NOT NULL,
  address_city TEXT NOT NULL DEFAULT 'Rio das Ostras',
  address_uf TEXT NOT NULL DEFAULT 'RJ',
  affected_body_part TEXT NOT NULL,
  causative_agent TEXT NOT NULL,
  medical_certificate_flag INTEGER NOT NULL DEFAULT 1,
  doctor_name TEXT NOT NULL,
  doctor_crm TEXT NOT NULL,
  doctor_uf TEXT NOT NULL DEFAULT 'RJ',
  status TEXT NOT NULL DEFAULT 'EMITIDA',
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS people_sst_epi (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  equipment_name TEXT NOT NULL,
  ca_number TEXT NOT NULL, -- Certificado de Aprovação
  ca_validity TEXT NOT NULL,
  protection_type TEXT NOT NULL, -- 'AUDITIVA', 'RESPIRATORIA', 'VISUAL', 'CABECA', 'MEMBROS'
  collective_measures TEXT,
  sanitization_instructions TEXT,
  replacement_interval_days INTEGER NOT NULL DEFAULT 180,
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS people_sst_epi_deliveries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_id INTEGER NOT NULL,
  epi_id INTEGER NOT NULL,
  delivery_date TEXT NOT NULL,
  expected_replacement_date TEXT NOT NULL,
  condition TEXT NOT NULL DEFAULT 'NOVO',
  employee_signed INTEGER NOT NULL DEFAULT 1,
  delivered_by TEXT NOT NULL,
  notes TEXT
);

-- 18. Tabelas e Configurações de Dependência Externa (Mock, Sandbox e Credenciais)
CREATE TABLE IF NOT EXISTS people_external_configs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  service_name TEXT NOT NULL UNIQUE, -- 'ESOCIAL', 'SISOBI', 'CORREIOS_CEP', 'CBO_MTE', 'ECONTRATO_CONSIGNADO', 'INSS_TABELA'
  api_endpoint TEXT NOT NULL,
  api_key TEXT,
  client_id TEXT,
  client_secret TEXT,
  environment TEXT NOT NULL DEFAULT 'SANDBOX', -- 'SANDBOX', 'PRODUCTION'
  is_mock_fallback INTEGER NOT NULL DEFAULT 1,
  active INTEGER NOT NULL DEFAULT 1,
  last_health_check TEXT,
  status TEXT NOT NULL DEFAULT 'ONLINE'
);

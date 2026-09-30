"""Carga inicial e sementes de dados para Gestão de Pessoas, Folha de Pagamento, Previdência, eSocial e SST.
Conformidade integral com os 117 itens do Anexo III (Edital PE 552/2026).
"""
import json
from datetime import datetime, date
from db import get_db
from domain import now

def seed_people(entity_id='MUNICIPIO'):
    db = get_db()

    # 0. Cargos e Servidores Base
    positions = [
        ('CARGO-01', 'Assistente Administrativo', 15, 3500.00, 40),
        ('CARGO-02', 'Médico Clínico Geral', 10, 8500.00, 20),
        ('CARGO-03', 'Professor de Ensino Fundamental', 25, 4200.00, 30),
        ('CARGO-04', 'Enfermeiro de Saúde Pública', 12, 5200.00, 30)
    ]
    for p_code, p_name, vac, sal, hrs in positions:
        db.execute("""
            INSERT OR IGNORE INTO people_positions (code, name, vacancies, salary, hours, active)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (p_code, p_name, vac, sal, hrs))

    employees = [
        ('EMP-01', 'Maria da Silva Pereira', '123.456.789-00', 'Assistente Administrativo', 'LOC-ADM', 'CC-ADM-01', '2020-03-01', 'RPPS', 4200.00, 'maria.silva@riodasostras.rj.gov.br'),
        ('EMP-02', 'João Carlos Oliveira', '234.567.890-11', 'Médico Clínico Geral', 'LOC-SAUDE', 'CC-HOSP-01', '2018-05-15', 'RPPS', 8500.00, 'joao.carlos@riodasostras.rj.gov.br'),
        ('EMP-03', 'Ana Beatriz Santos', '345.678.901-22', 'Professor de Ensino Fundamental', 'LOC-EDUC', 'CC-ESCOLA-01', '2021-02-10', 'RPPS', 4200.00, 'ana.beatriz@riodasostras.rj.gov.br'),
        ('EMP-04', 'Carlos Eduardo Lima', '456.789.012-33', 'Enfermeiro de Saúde Pública', 'LOC-SAUDE', 'CC-POSTO-CENTRO', '2022-08-01', 'RGPS', 5200.00, 'carlos.lima@riodasostras.rj.gov.br')
    ]
    for e_code, e_name, cpf, pos, dep, cc, adm, reg, sal, mail in employees:
        db.execute("""
            INSERT OR IGNORE INTO people_employees (code, name, cpf, position, department, cost_center, admission, regime, salary, active, email, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
        """, (e_code, e_name, cpf, pos, dep, cc, adm, reg, sal, mail, now()))

    # 1. Locais de Trabalho e Centros de Custo (Itens 3 e 4)
    locations = [
        ('LOC-ADM', 'Secretaria Municipal de Administração', 'Sede Administrativa', '["CC-ADM-01", "CC-ADM-02", "CC-RH-01"]'),
        ('LOC-SAUDE', 'Secretaria Municipal de Saúde', 'Hospital Municipal e Postos', '["CC-HOSP-01", "CC-POSTO-CENTRO", "CC-POSTO-MARILEA"]'),
        ('LOC-EDUC', 'Secretaria Municipal de Educação', 'Escolas e Creches', '["CC-ESCOLA-01", "CC-ESCOLA-02", "CC-CRECHE-01"]'),
        ('LOC-FAZ', 'Secretaria Municipal de Fazenda', 'Arrecadação e Tributos', '["CC-FAZ-TRIB", "CC-FAZ-FIN"]')
    ]
    for code, name, dept, ccs in locations:
        db.execute("""
            INSERT OR IGNORE INTO people_work_locations (entity_id, code, name, department, cost_centers, active, created_at)
            VALUES (?, ?, ?, ?, ?, 1, ?)
        """, (entity_id, code, name, dept, ccs, now()))

    # 2. Fundos Previdenciários RPPS (Itens 5, 6, 11, 48)
    # RioPrevi Fundo Previdenciário (Capitalização) e Fundo Financeiro (Repartição Simples)
    brackets_rioprevi = json.dumps([
        {'min': 0.00, 'max': 1412.00, 'rate': 11.00},
        {'min': 1412.01, 'max': 2666.68, 'rate': 12.00},
        {'min': 2666.69, 'max': 4000.03, 'rate': 14.00},
        {'min': 4000.04, 'max': 7786.02, 'rate': 16.00},
        {'min': 7786.03, 'max': 999999.99, 'rate': 18.00}
    ])
    rpps_funds = [
        ('RPPS-PREVI', 'RioPrevi - Fundo Previdenciário (Capitalização)', 14.00, 22.00, 6.50, 1, brackets_rioprevi),
        ('RPPS-FINAN', 'RioPrevi - Fundo Financeiro (Repartição)', 14.00, 24.00, 8.00, 1, brackets_rioprevi)
    ]
    for code, name, emp_r, pat_r, sup_r, is_prog, prog_brk in rpps_funds:
        db.execute("""
            INSERT OR IGNORE INTO people_rpps_funds (code, name, employee_rate, patronal_rate, supplementary_rate, is_progressive, progressive_brackets, active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
        """, (code, name, emp_r, pat_r, sup_r, is_prog, prog_brk, now()))

    # 3. Operadoras de Plano de Saúde (Item 16)
    age_brackets_unimed = json.dumps([
        {'min_age': 0, 'max_age': 18, 'value': 145.50},
        {'min_age': 19, 'max_age': 23, 'value': 185.00},
        {'min_age': 24, 'max_age': 28, 'value': 225.00},
        {'min_age': 29, 'max_age': 33, 'value': 275.00},
        {'min_age': 34, 'max_age': 38, 'value': 330.00},
        {'min_age': 39, 'max_age': 43, 'value': 410.00},
        {'min_age': 44, 'max_age': 48, 'value': 520.00},
        {'min_age': 49, 'max_age': 53, 'value': 680.00},
        {'min_age': 54, 'max_age': 58, 'value': 890.00},
        {'min_age': 59, 'max_age': 120, 'value': 1150.00}
    ])
    plans = [
        ('MED-UNIMED', 'Unimed Costa do Sol', '01.234.567/0001-89', '345678', 'AGE_BRACKET', 0.00, 0.00, 50.00, 0.00, age_brackets_unimed, '3568'),
        ('MED-AMIL', 'Amil Assistência Médica', '02.345.678/0001-90', '456789', 'FIXED', 350.00, 0.00, 40.00, 0.00, '[]', '3568'),
        ('MED-MUNICIPAL', 'Plano de Saúde Municipal dos Servidores', '29.138.078/0001-50', '999999', 'PERCENTAGE_BASE', 0.00, 3.50, 60.00, 10.00, '[]', '3568')
    ]
    for code, name, cnpj, ans, mode, fix_v, pct_v, ent_part, sp_part, brk, dirf in plans:
        db.execute("""
            INSERT OR IGNORE INTO people_health_plans (operator_code, operator_name, cnpj, ans_register, calculation_mode, fixed_value, base_percentage, entity_coparticipation_pct, spouse_coparticipation_pct, age_brackets, dirf_code, active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        """, (code, name, cnpj, ans, mode, fix_v, pct_v, ent_part, sp_part, brk, dirf, now()))

    # 4. Linhas e Empresas de Vale-Transporte (Item 17)
    transports = [
        ('TRANS-MACACA', 'Auto Viação 1001 / Rápido Macaense', 'LIN-01', 'Linha 01 - Costazul x Centro', 4.50),
        ('TRANS-MACACA', 'Auto Viação 1001 / Rápido Macaense', 'LIN-02', 'Linha 02 - Mariléa x Rocha Leão', 6.80),
        ('TRANS-LOCAL', 'Transporte Municipal Rio das Ostras', 'LIN-03', 'Linha 03 - Cantagalo x Centro', 3.75),
        ('TRANS-LOCAL', 'Transporte Municipal Rio das Ostras', 'LIN-04', 'Linha 04 - Cidade Praiana x Âncora', 3.75)
    ]
    for c_code, c_name, l_code, l_name, fare in transports:
        row = db.execute("SELECT id FROM people_transport_vouchers WHERE line_code=?", (l_code,)).fetchone()
        if not row:
            db.execute("""
                INSERT INTO people_transport_vouchers (company_code, company_name, line_code, line_name, fare_value, active, created_at)
                VALUES (?, ?, ?, ?, ?, 1, ?)
            """, (c_code, c_name, l_code, l_name, fare, now()))

    # 5. Configuração do Portal do Servidor e Contracheque Web (Itens 70 a 82)
    db.execute("""
        INSERT OR IGNORE INTO people_payslip_settings (
            entity_code, show_logo, logo_url, watermark_text, enable_qr_code, secret_qr_key, header_layout, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'MUNICIPIO', 1, '/static/brasao-rio-das-ostras.png',
        'PREFEITURA MUNICIPAL DE RIO DAS OSTRAS - AUTENTICIDADE DIGITAL',
        1, 'RIO-GESTAO-KEY-VALIDATION-2026', 'STANDARD', now()
    ))

    # 6. Atos Legais Padrão (Itens 82 a 86)
    legal_acts = [
        ('DECRETO', '1.245', 2026, '2026-01-02', 'Dispõe sobre o reajuste linear dos servidores e fixação do piso salarial.', 'Fica concedido o reajuste de 4.8% a todos os servidores públicos municipais.'),
        ('PORTARIA', '302', 2026, '2026-02-01', 'Regulamenta o controle do quadro de vagas e movimentações funcionais.', 'Estabelece as normas de substituição de servidores e vacância.'),
        ('PORTARIA', '410', 2026, '2026-03-01', 'Institui a comissão permanente de avaliação de tempo de serviço e concessão de quinquênios.', 'Designa os servidores responsáveis pela emissão das certidões.')
    ]
    for atype, num, yr, pub_dt, sumry, cont in legal_acts:
        row = db.execute("SELECT id FROM people_legal_acts WHERE act_type=? AND act_number=? AND act_year=?", (atype, num, yr)).fetchone()
        if not row:
            db.execute("""
                INSERT INTO people_legal_acts (act_type, act_number, act_year, publication_date, summary, content, is_effectiveness, active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, 1, ?)
            """, (atype, num, yr, pub_dt, sumry, cont, now()))

    # 7. Configurações do eSocial S-1.3 (Itens 87 a 108)
    row = db.execute("SELECT id FROM people_esocial_configs WHERE id=1").fetchone()
    if not row:
        db.execute("""
            INSERT INTO people_esocial_configs (
                tp_amb, proc_emi, ver_proc, cnpj_matriz, responsible_name,
                responsible_cpf, responsible_email, responsible_phone, token_enabled,
                a1_cert_valid_until, a1_cert_alias, last_sync
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            2, 1, 'S-1.3', '29.138.078/0001-50', 'Carlos Alberto Silveira',
            '123.456.789-00', 'rh.esocial@riodasostras.rj.gov.br', '(22) 2771-6000',
            1, '2027-12-31', 'CERT_A1_RIO_DAS_OSTRAS_2026', now()
        ))

    # 8. Mapeamento de Rubricas eSocial (Tabela 03) x Verbas do ERP (Itens 91, 94)
    rubrics = [
        ('VENC-BASE', 'Vencimento Base / Salário Contratual', '1000', 1, '11', '11', '11'),
        ('QUINQUENIO', 'Adicional por Tempo de Serviço (Quinquênio)', '1200', 1, '11', '11', '11'),
        ('CARGO-COMISSAO', 'Vencimento Cargo em Comissão', '1001', 1, '11', '11', '11'),
        ('HORA-EXTRA', 'Horas Extraordinárias 50%', '1020', 1, '11', '11', '11'),
        ('AUX-TRANSP', 'Benefício Vale-Transporte (Parte Ente)', '1401', 1, '00', '00', '00'),
        ('DESC-INSS', 'Contribuição Previdenciária RGPS', '9201', 2, '00', '31', '00'),
        ('DESC-RPPS', 'Contribuição Previdenciária RPPS RioPrevi', '9202', 2, '00', '32', '00'),
        ('DESC-IRRF', 'Imposto de Renda Retido na Fonte', '9203', 2, '00', '00', '00'),
        ('DESC-CONSIGNADO', 'Empréstimo Consignado em Folha', '9220', 2, '00', '00', '00'),
        ('DESC-SAUDE', 'Mensalidade Plano de Saúde', '9230', 2, '00', '00', '00'),
        ('DESC-TRANSP', 'Desconto Vale-Transporte (6% Teto)', '9240', 2, '00', '00', '00')
    ]
    for ev_code, r_name, nat, tp, rpps, ir, fgts in rubrics:
        db.execute("""
            INSERT OR IGNORE INTO people_esocial_rubrics (event_code, rubric_name, nat_rubr, tp_rubr, cod_inc_cprp, cod_inc_irrf, cod_inc_fgts, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """, (ev_code, r_name, nat, tp, rpps, ir, fgts))

    # 9. Saúde e Segurança do Trabalho - SST (Itens 109 a 117)
    # Médicos e Engenheiros do Trabalho
    monitors = [
        ('BIOLOGICA', 'Dr. Eduardo Rocha Lima', 'CRM', '52.78945-1', 'RJ', '2025-01-01', None),
        ('AMBIENTAL', 'Eng. Patrícia Magalhães', 'CREA', '2019102345', 'RJ', '2025-01-01', None)
    ]
    for mtype, name, cnl, cnum, cuf, sdt, edt in monitors:
        row = db.execute("SELECT id FROM people_sst_monitors WHERE council_number=?", (cnum,)).fetchone()
        if not row:
            db.execute("""
                INSERT INTO people_sst_monitors (responsible_type, professional_name, professional_council, council_number, council_uf, start_period, end_period, active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
            """, (mtype, name, cnl, cnum, cuf, sdt, edt, now()))

    # Catálogo de EPIs com CA (Item 117)
    epis = [
        ('Protetor Auditivo tipo Plug de Inserção', 'CA-11512', '2028-11-20', 'AUDITIVA', 'Enclausuramento de compressores', 'Lavar com água e sabão neutro diariamente', 90),
        ('Respirador Purificador PFF2 / N95', 'CA-38504', '2027-08-15', 'RESPIRATORIA', 'Ventilação forçada em laboratórios', 'Descartável em caso de saturação ou umidade', 15),
        ('Óculos de Segurança Antirrisco e Antiembaçante', 'CA-18819', '2029-03-10', 'VISUAL', 'Biombos de proteção em oficinas', 'Higienizar com pano macio e álcool 70%', 180),
        ('Luva de Segurança em Vaqueta para Agentes Mecânicos', 'CA-25633', '2027-12-05', 'MEMBROS', 'Guardas de proteção em maquinários', 'Armazenar em local seco e arejado', 60),
        ('Capacete de Segurança Classe B com Jugular', 'CA-29792', '2028-05-18', 'CABECA', 'Redes de proteção em obras públicas', 'Inspecionar trincas e limpar o casco', 365)
    ]
    for eq_name, ca, ca_val, ptype, col_meas, sanit, interv in epis:
        row = db.execute("SELECT id FROM people_sst_epi WHERE ca_number=?", (ca,)).fetchone()
        if not row:
            db.execute("""
                INSERT INTO people_sst_epi (equipment_name, ca_number, ca_validity, protection_type, collective_measures, sanitization_instructions, replacement_interval_days, active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
            """, (eq_name, ca, ca_val, ptype, col_meas, sanit, interv, now()))

    # 10. Configurações de Serviços Externos e Mock/Sandbox Fallback (Itens 54, 55, 61, 64-68, 87)
    external_services = [
        ('ESOCIAL', 'https://webservices.producaorestrita.esocial.gov.br/servicos/empregador/loteeventos/wsEnviarLoteEventos.asmx', 'API-KEY-ESOCIAL-SANDBOX', 'PMRO-ESOCIAL-CLIENT-ID', 'SECRET-ESOCIAL-2026', 'SANDBOX', 1),
        ('SISOBI', 'https://sisobi.dataprev.gov.br/api/v2/obitos-confronto', 'TOKEN-SISOBI-MUNICIPAL-2026', 'CLIENT-SISOBI-RJ', 'SECRET-SISOBI-RJ', 'SANDBOX', 1),
        ('CORREIOS_CEP', 'https://viacep.com.br/ws', 'CHAVE-CORREIOS-DADOS-PUBLICOS', 'CORREIOS-APP-RJ', 'SECRET-CORREIOS', 'SANDBOX', 1),
        ('CBO_MTE', 'https://mte.gov.br/api/cbo/v3/classificacao', 'KEY-MTE-CBO-PUBLIC', 'CLIENT-CBO', 'SECRET-CBO', 'SANDBOX', 1),
        ('ECONTRATO_CONSIGNADO', 'https://api.econsignado.caixa.gov.br/v1/convenios/3304524', 'TOKEN-ECONTRATO-CONSIG-2026', 'CLIENT-ECONTRATO', 'SECRET-ECONTRATO', 'SANDBOX', 1),
        ('INSS_TABELA', 'https://dadosabertos.previdencia.gov.br/api/tabelas/rgps/vigente', 'KEY-DADOS-ABERTOS-INSS', 'CLIENT-INSS', 'SECRET-INSS', 'SANDBOX', 1)
    ]
    for s_name, endpoint, a_key, c_id, c_sec, env, mock_fall in external_services:
        db.execute("""
            INSERT OR IGNORE INTO people_external_configs (service_name, api_endpoint, api_key, client_id, client_secret, environment, is_mock_fallback, active, last_health_check, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, 'ONLINE')
        """, (s_name, endpoint, a_key, c_id, c_sec, env, mock_fall, now()))

    db.commit()

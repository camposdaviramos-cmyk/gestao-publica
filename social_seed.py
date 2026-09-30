"""
Seed de Dados Socioassistenciais Oficiais do Município de Rio das Ostras (SUAS / CRAS / CREAS / CadÚnico)
Atendimento integral aos requisitos do Edital PE 552/2026 e Anexo III.
"""

import json
from db import get_db

def seed_social():
    db = get_db()

    # 1. Unidades Socioassistenciais
    units = [
        ('CRAS-CENTRAL', 'CRAS Central - Jardim Campomar', 'CRAS', 'Sede', 'Jardim Campomar', 'Rua Nova Iguaçu, 120', -22.5280, -41.9420, '(22) 2764-1001', 'cras.central@riodasostras.rj.gov.br', 'Fernanda de Souza (CRESS 34567-RJ)', 600),
        ('CRAS-SUL', 'CRAS Sul - Cidade Beiramar', 'CRAS', 'Sede', 'Cidade Beiramar', 'Av. Brasil, 450', -22.5450, -41.9550, '(22) 2764-1002', 'cras.sul@riodasostras.rj.gov.br', 'Mariana Pires (CRESS 28910-RJ)', 500),
        ('CRAS-PRAIAMAR', 'CRAS Praiamar', 'CRAS', 'Sede', 'Praiamar', 'Rua Guanabara, 89', -22.5120, -41.9250, '(22) 2764-1003', 'cras.praiamar@riodasostras.rj.gov.br', 'Carlos Eduardo Dias (CRESS 41230-RJ)', 550),
        ('CREAS-RIO-OSTRAS', 'CREAS - Centro de Referência Especializado de Assistência Social', 'CREAS', 'Sede', 'Extensão do Bosque', 'Rua Jane Maria Martins, 300', -22.5200, -41.9380, '(22) 2764-2001', 'creas@riodasostras.rj.gov.br', 'Dra. Beatriz Albuquerque (CRESS 19874-RJ)', 300),
        ('CENTRO-POP', 'Centro de Referência Especializado para Pessoas em Situação de Rua (Centro POP)', 'CENTRO_POP', 'Sede', 'Âncora', 'Rua das Casuarinas, 45', -22.5150, -41.9100, '(22) 2764-3001', 'centropop@riodasostras.rj.gov.br', 'Renato Carvalho (CRESS 50123-RJ)', 150),
        ('ACOLHIMENTO-INFANTIL', 'Unidade de Acolhimento Institucional Renascer (Crianças e Adolescentes)', 'ACOLHIMENTO_INSTITUCIONAL', 'Sede', 'Cantagalo', 'Estrada Velha de Cantagalo, s/n', -22.4900, -41.9600, '(22) 2764-4001', 'acolhimento@riodasostras.rj.gov.br', 'Cláudia Silveira (CRP 05/44321-RJ)', 25),
        ('CASA-ABRIGO-MULHER', 'Casa Abrigo Municipal Viva Mulher (Sigilo Estrito)', 'CASA_PASSAGEM', 'Sede', 'Centro', 'Endereço Protegido por Lei Federal', -22.5268, -41.9452, '(22) 2764-5001', 'abrigomulher@riodasostras.rj.gov.br', 'Juliana Rezende (CRESS 38712-RJ)', 20)
    ]

    for code, name, utype, dist, neigh, addr, lat, lng, phone, email, mgr, cap in units:
        db.execute('''
            INSERT OR IGNORE INTO social_units 
            (code, name, unit_type, district, neighborhood, address, latitude, longitude, phone, email, manager_name, capacity_families)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (code, name, utype, dist, neigh, addr, lat, lng, phone, email, mgr, cap))

    # 2. Equipes Técnicas
    cras_central_id = db.execute("SELECT id FROM social_units WHERE code = 'CRAS-CENTRAL'").fetchone()[0]
    creas_id = db.execute("SELECT id FROM social_units WHERE code = 'CREAS-RIO-OSTRAS'").fetchone()[0]
    pop_id = db.execute("SELECT id FROM social_units WHERE code = 'CENTRO-POP'").fetchone()[0]

    teams = [
        (cras_central_id, 'Fernanda de Souza', '111.222.333-44', 'ASSISTENTE_SOCIAL', 'CRESS', '34567', 'fernanda.souza@riodasostras.rj.gov.br'),
        (cras_central_id, 'Rodrigo Meirelles', '222.333.444-55', 'PSICOLOGO', 'CRP', '05/58921', 'rodrigo.psico@riodasostras.rj.gov.br'),
        (cras_central_id, 'Tatiana Mendes', '333.444.555-66', 'ENTREVISTADOR_CADUNICO', 'OUTRO', 'CAD-001', 'tatiana.cad@riodasostras.rj.gov.br'),
        (creas_id, 'Dra. Beatriz Albuquerque', '444.555.666-77', 'ASSISTENTE_SOCIAL', 'CRESS', '19874', 'beatriz.social@riodasostras.rj.gov.br'),
        (creas_id, 'Dr. Vinicius Prado', '555.666.777-88', 'ADVOGADO', 'OAB', '189432', 'vinicius.adv@riodasostras.rj.gov.br'),
        (pop_id, 'Renato Carvalho', '666.777.888-99', 'ASSISTENTE_SOCIAL', 'CRESS', '50123', 'renato.pop@riodasostras.rj.gov.br'),
        (pop_id, 'Luciana Barbosa', '777.888.999-00', 'EDUCADOR_SOCIAL', 'OUTRO', 'EDU-042', 'luciana.edu@riodasostras.rj.gov.br')
    ]

    for uid, name, cpf, role, ctype, cnum, email in teams:
        db.execute('''
            INSERT OR IGNORE INTO social_teams (unit_id, name, cpf, role_type, council_type, council_number, email)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (uid, name, cpf, role, ctype, cnum, email))

    # 3. Territórios de Abrangência
    territories = [
        ('Centro', 'Sede', cras_central_id, 0, 0.25),
        ('Jardim Campomar', 'Sede', cras_central_id, 0, 0.32),
        ('Cidade Beiramar', 'Sede', cras_central_id, 0, 0.40),
        ('Extensão do Bosque', 'Sede', cras_central_id, 0, 0.30),
        ('Praiamar', 'Sede', cras_central_id, 1, 0.65),
        ('Âncora', 'Sede', cras_central_id, 1, 0.72),
        ('Nova Esperança', 'Sede', cras_central_id, 1, 0.68),
        ('Cantagalo', 'Sede', cras_central_id, 0, 0.45),
        ('Costazul', 'Sede', cras_central_id, 0, 0.20),
        ('Mariléa', 'Sede', cras_central_id, 0, 0.28)
    ]

    for name, dist, uid, hr, ivs_avg in territories:
        db.execute('''
            INSERT OR IGNORE INTO social_territories (name, district, cras_unit_id, high_risk_zone, vulnerability_index_avg)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, dist, uid, hr, ivs_avg))

    # 4. Tabelas de Referência
    vulns = [
        ('EXTREMA_POBREZA', 'Extrema Pobreza / Insegurança Alimentar Grave', 'INSEGURANCA_ALIMENTAR', 'MUITO_ALTA'),
        ('VIOLENCIA_DOMESTICA', 'Violência Doméstica e Familiar contra a Mulher', 'VIOLENCIA', 'MUITO_ALTA'),
        ('TRABALHO_INFANTIL', 'Trabalho Infantil ou Exploração de Menor', 'VIOLENCIA', 'MUITO_ALTA'),
        ('AREA_DE_RISCO', 'Residência em Área de Risco Geológico ou Alagamento', 'HABITACIONAL', 'ALTA'),
        ('ISOLAMENTO_IDOSO', 'Pessoa Idosa sem Rede de Apoio Familiar', 'ISOLAMENTO', 'MEDIA'),
        ('DEPENDENCIA_QUIMICA', 'Membro da Família com Dependência Química Severa', 'RISCO_PESSOAL', 'ALTA')
    ]
    for code, name, cat, sev in vulns:
        db.execute('''
            INSERT OR IGNORE INTO social_reference_vulnerabilities (code, name, category, severity_level)
            VALUES (?, ?, ?, ?)
        ''', (code, name, cat, sev))

    pcds = [
        ('PCD_FISICA', 'Deficiência Física / Motora', 'Acessibilidade física e cadeiras de rodas'),
        ('PCD_VISUAL', 'Deficiência Visual (Cegueira ou Baixa Visão)', 'Textos em Braille e leitores de tela'),
        ('PCD_AUDITIVA', 'Deficiência Auditiva (Surdez)', 'Intérprete de Libras e recursos visuais'),
        ('PCD_INTELECTUAL', 'Deficiência Intelectual', 'Apoio pedagógico especializado e mediação'),
        ('PCD_AUTISMO', 'Transtorno do Espectro Autista (TEA)', 'Ambientes com baixo estímulo sensorial e previsibilidade')
    ]
    for code, name, acc in pcds:
        db.execute('''
            INSERT OR IGNORE INTO social_reference_pcd (code, name, accessibility_needs)
            VALUES (?, ?, ?)
        ''', (code, name, acc))

    sinases = [
        ('SINASE_PATRIMONIAL', 'Ato Infracional contra o Patrimônio (Furto/Dano)', 'LEVE'),
        ('SINASE_AMEACA', 'Ato Infracional de Ameaça ou Vias de Fato', 'MEDIA'),
        ('SINASE_ENTORPECENTES', 'Ato Infracional análogo ao Tráfico de Drogas', 'GRAVE'),
        ('SINASE_VIOLENCIA_PESSOA', 'Ato Infracional com Violência ou Grave Ameaça à Pessoa', 'MUITO_GRAVE')
    ]
    for code, desc, grav in sinases:
        db.execute('''
            INSERT OR IGNORE INTO social_reference_sinase (code, infraction_type, gravity_level)
            VALUES (?, ?, ?)
        ''', (code, desc, grav))

    # 5. Almoxarifados e Locais de Estoque
    warehouses = [
        ('ALMOX-CENTRAL-SEMAS', 'Almoxarifado Central da Secretaria de Assistência Social', cras_central_id, 'Marcos Vinicius Alves', 'Rua Nova Iguaçu, 130'),
        ('ESTOQUE-CRAS-CENTRAL', 'Depósito de Insumos - CRAS Central', cras_central_id, 'Fernanda de Souza', 'Rua Nova Iguaçu, 120'),
        ('ESTOQUE-CRAS-PRAIAMAR', 'Depósito de Insumos - CRAS Praiamar', cras_central_id, 'Carlos Eduardo Dias', 'Rua Guanabara, 89')
    ]
    for code, name, uid, mgr, addr in warehouses:
        db.execute('''
            INSERT OR IGNORE INTO social_warehouses (code, name, unit_id, manager_name, address)
            VALUES (?, ?, ?, ?, ?)
        ''', (code, name, uid, mgr, addr))

    # 6. Catálogo de Insumos e Benefícios
    supplies = [
        ('CESTA-FAMILIAR-PADRAO', 'Cesta Básica Familiar Padrão (28 itens, 30kg)', 'CESTA_BASICA', 'UN', 50, 180, 1),
        ('CESTA-EMERGENCIAL', 'Cesta de Alimentos Emergencial (15kg)', 'CESTA_BASICA', 'UN', 30, 95, 1),
        ('KIT-NATALIDADE-ENXOVAL', 'Auxílio Natalidade - Kit Enxoval Completo de Bebê', 'AUXILIO_NATALIDADE', 'UN', 20, 45, 0),
        ('AUXILIO-FUNERAL-URNA', 'Auxílio Funeral - Urna Funerária e Translado Padrão SUAS', 'AUXILIO_FUNERAL', 'UN', 10, 25, 0),
        ('COBERTOR-TERMICO', 'Cobertor Térmico Casal - Acolhimento Inverno', 'COBERTORES', 'UN', 40, 120, 0),
        ('KIT-HIGIENE-FAMILIAR', 'Kit de Higiene e Limpeza Familiar', 'KIT_HIGIENE', 'UN', 50, 150, 0),
        ('FILTRO-AGUA-BARRO', 'Filtro de Água de Barro Cerâmico com Vela Dupla', 'FILTROS_AGUA', 'UN', 15, 35, 0)
    ]
    for code, name, cat, um, min_st, cur_st, perish in supplies:
        db.execute('''
            INSERT OR IGNORE INTO social_supplies (code, name, category, unit_of_measure, minimum_stock, current_stock, is_perishable)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (code, name, cat, um, min_st, cur_st, perish))

    # 7. Lotes de Estoque
    wh_central_id = db.execute("SELECT id FROM social_warehouses WHERE code = 'ALMOX-CENTRAL-SEMAS'").fetchone()[0]
    cesta_id = db.execute("SELECT id FROM social_supplies WHERE code = 'CESTA-FAMILIAR-PADRAO'").fetchone()[0]
    enxoval_id = db.execute("SELECT id FROM social_supplies WHERE code = 'KIT-NATALIDADE-ENXOVAL'").fetchone()[0]

    db.execute('''
        INSERT OR IGNORE INTO social_stock_batches 
        (supply_id, warehouse_id, batch_number, manufacture_date, expiration_date, supplier_name, initial_quantity, current_quantity, unit_cost)
        VALUES (?, ?, 'LOTE-CB-2026-01', '2026-01-10', '2026-07-10', 'Distribuidora Costa do Sol Alimentos Ltda', 200, 180, 145.50)
    ''', (cesta_id, wh_central_id))

    db.execute('''
        INSERT OR IGNORE INTO social_stock_batches 
        (supply_id, warehouse_id, batch_number, manufacture_date, expiration_date, supplier_name, initial_quantity, current_quantity, unit_cost)
        VALUES (?, ?, 'LOTE-NX-2026-02', '2026-01-15', '2028-01-15', 'Indústria de Confecções Infantis Brasil Ltda', 50, 45, 230.00)
    ''', (enxoval_id, wh_central_id))

    # 8. Famílias e Prontuários SUAS / CadÚnico
    families = [
        ('FAM-RO-000101', '128.45678.90-1', 'Maria das Dores da Silva', '054.321.987-11', '1985-04-12', 'Rua Três, 45', 'Âncora', cras_central_id, -22.5160, -41.9120, 600.0, 4, 150.0, 'POBREZA', 0.68, 'ALTA', 1, 1, 0, 0, 100.0),
        ('FAM-RO-000102', '129.56789.01-2', 'Sebastião Antunes Pereira', '078.654.321-22', '1952-11-20', 'Rua Guanabara, 102', 'Praiamar', cras_central_id, -22.5110, -41.9240, 1412.0, 2, 706.0, 'BAIXA_RENDA', 0.42, 'MEDIA', 0, 0, 1, 0, 100.0),
        ('FAM-RO-000103', '130.67890.12-3', 'Ana Paula Nascimento', '099.888.777-33', '1998-07-08', 'Rua Nova Esperança, 15', 'Nova Esperança', cras_central_id, -22.5190, -41.9180, 200.0, 3, 66.67, 'EXTREMA_POBREZA', 0.85, 'MUITO_ALTA', 1, 1, 0, 1, 100.0),
        ('FAM-RO-000104', '131.78901.23-4', 'João Carlos de Oliveira', '111.444.777-44', '1979-02-14', 'Rua Amazonas, 55', 'Cidade Beiramar', cras_central_id, -22.5430, -41.9540, 2100.0, 4, 525.0, 'BAIXA_RENDA', 0.35, 'BAIXA', 0, 0, 0, 0, 100.0)
    ]

    for fcode, nis, name, cpf, bdate, addr, neigh, uid, lat, lng, tinc, mcnt, pcinc, ibrk, ivs, ilvl, hrisk, fhead, held, hpcd, comp in families:
        db.execute('''
            INSERT OR IGNORE INTO social_families
            (family_code, head_nis, head_name, head_cpf, head_birth_date, address, neighborhood, cras_unit_id,
             latitude, longitude, total_income, members_count, per_capita_income, income_bracket, ivs_score, ivs_level,
             housing_risk_zone, female_headed, has_elderly, has_pcd, cadastral_completeness_pct)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (fcode, nis, name, cpf, bdate, addr, neigh, uid, lat, lng, tinc, mcnt, pcinc, ibrk, ivs, ilvl, hrisk, fhead, held, hpcd, comp))

    # 9. Membros Familiares
    fam1_id = db.execute("SELECT id FROM social_families WHERE family_code = 'FAM-RO-000101'").fetchone()[0]
    fam2_id = db.execute("SELECT id FROM social_families WHERE family_code = 'FAM-RO-000102'").fetchone()[0]
    fam3_id = db.execute("SELECT id FROM social_families WHERE family_code = 'FAM-RO-000103'").fetchone()[0]

    members = [
        (fam1_id, 'Maria das Dores da Silva', '128.45678.90-1', '054.321.987-11', '1985-04-12', 'F', 'RESPONSAVEL_FAMILIAR', 600.0, 0, 0, 0, 0),
        (fam1_id, 'Lucas da Silva', '128.45678.90-2', None, '2010-09-14', 'M', 'FILHO', 0.0, 0, 0, 0, 1),
        (fam1_id, 'Camila da Silva', '128.45678.90-3', None, '2013-03-22', 'F', 'FILHO', 0.0, 0, 0, 0, 1),
        (fam1_id, 'Enzo da Silva', '128.45678.90-4', None, '2018-08-05', 'M', 'FILHO', 0.0, 0, 0, 0, 0),
        (fam2_id, 'Sebastião Antunes Pereira', '129.56789.01-2', '078.654.321-22', '1952-11-20', 'M', 'RESPONSAVEL_FAMILIAR', 1412.0, 0, 0, 1, 0),
        (fam2_id, 'Neuza Antunes Pereira', '129.56789.01-3', '089.765.432-33', '1955-05-18', 'F', 'CONJUGE', 0.0, 0, 0, 1, 0),
        (fam3_id, 'Ana Paula Nascimento', '130.67890.12-3', '099.888.777-33', '1998-07-08', 'F', 'RESPONSAVEL_FAMILIAR', 200.0, 0, 1, 0, 0),
        (fam3_id, 'Gabriel Nascimento (PCD)', '130.67890.12-4', None, '2020-01-15', 'M', 'FILHO', 0.0, 1, 0, 0, 0),
        (fam3_id, 'Sofia Nascimento', '130.67890.12-5', None, '2024-02-10', 'F', 'FILHO', 0.0, 0, 0, 0, 0)
    ]

    for fid, name, nis, cpf, bdate, sex, kin, inc, pcd, preg, eld, scfv in members:
        db.execute('''
            INSERT OR IGNORE INTO social_family_members
            (family_id, name, nis, cpf, birth_date, gender, kinship, individual_income, is_pcd, is_pregnant, is_elderly, scfv_enrolled)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (fid, name, nis, cpf, bdate, sex, kin, inc, pcd, preg, eld, scfv))

    # 10. Concessão de Benefício Eventual de Exemplo
    batch1_id = db.execute("SELECT id FROM social_stock_batches WHERE batch_number = 'LOTE-CB-2026-01'").fetchone()[0]
    db.execute('''
        INSERT OR IGNORE INTO social_benefits_granted
        (family_id, benefit_type, supply_id, batch_id, amount, quantity, technical_opinion, social_worker_cress, social_worker_name, status, delivery_date)
        VALUES (?, 'CESTA_BASICA', ?, ?, 145.50, 1, 'Família monoparental em extrema insegurança alimentar com 3 crianças.', '34567', 'Fernanda de Souza', 'ENTREGUE', '2026-01-20')
    ''', (fam1_id, cesta_id, batch1_id))

    # 11. RMAs Abertos para o Mês Corrente
    db.execute('''
        INSERT OR IGNORE INTO social_rma_cras
        (unit_id, year, month, paif_total_active, paif_new_inserted, paif_extreme_poverty, paif_bolsa_familia, 
         atendimentos_total, visitas_domiciliares, reunioes_coletivas_paif, beneficios_natalidade, beneficios_funeral, beneficios_outros, status)
        VALUES (?, 2026, 1, 142, 18, 45, 120, 310, 42, 8, 5, 2, 28, 'FECHADO')
    ''', (cras_central_id,))

    db.execute('''
        INSERT OR IGNORE INTO social_rma_creas
        (unit_id, year, month, paefi_total_active, paefi_new_inserted, paefi_woman_violence, paefi_child_violence, atendimentos_total, orientacoes_juridicas, mse_total_adolescentes, mse_liberdade_assistida, mse_prestacao_servicos_comunidade, status)
        VALUES (?, 2026, 1, 65, 9, 22, 14, 185, 45, 18, 12, 6, 'FECHADO')
    ''', (creas_id,))

    db.execute('''
        INSERT OR IGNORE INTO social_rma_pop
        (unit_id, year, month, pessoas_atendidas_total, homens_atendidos, mulheres_atendidas, refeicoes_servidas, atendimentos_higiene, encaminhamentos_acolhimento, status)
        VALUES (?, 2026, 1, 74, 58, 16, 1240, 310, 12, 'FECHADO')
    ''', (pop_id,))

    # 12. Programas e Conjuntos Habitacionais
    db.execute('''
        INSERT OR IGNORE INTO social_housing_programs (code, title, legal_basis, funding_source, target_population)
        VALUES ('HAB-RO-2026', 'Programa Morar Bem Rio das Ostras', 'Lei Municipal nº 2.450/2021', 'Fundo Municipal de Habitação (FMHIS)', 'Famílias com renda de até 3 salários mínimos')
    ''')
    prog_id = db.execute("SELECT id FROM social_housing_programs WHERE code = 'HAB-RO-2026'").fetchone()[0]

    db.execute('''
        INSERT OR IGNORE INTO social_housing_complexes (program_id, name, neighborhood, total_units, available_units, reserved_elderly_quota, reserved_pcd_quota)
        VALUES (?, 'Residencial Praiamar I', 'Praiamar', 120, 45, 6, 6)
    ''', (prog_id,))

    # Critérios de Pontuação Habitacional
    criteria = [
        ('CRIT-RISCO', 'Família residente em área de risco geológico ou insalubre', 30, 1),
        ('CRIT-MULHER-CHEFE', 'Família monoparental chefiada por mulher', 20, 1),
        ('CRIT-PCD', 'Família com membro com deficiência (PCD)', 25, 1),
        ('CRIT-IDOSO', 'Família com membro idoso', 20, 1),
        ('CRIT-TEMPO-MUNICIPIO', 'Tempo de residência em Rio das Ostras superior a 5 anos', 15, 0),
        ('CRIT-EXTREMA-POBREZA', 'Família cadastrada no CadÚnico em situação de extrema pobreza', 20, 0)
    ]
    for code, desc, pts, mand in criteria:
        db.execute('''
            INSERT OR IGNORE INTO social_housing_criteria (code, description, points, legal_mandatory)
            VALUES (?, ?, ?, ?)
        ''', (code, desc, pts, mand))

    # Inscrição habitacional de exemplo
    complex_id = db.execute("SELECT id FROM social_housing_complexes WHERE name = 'Residencial Praiamar I'").fetchone()[0]
    db.execute('''
        INSERT OR IGNORE INTO social_housing_applications
        (application_number, program_id, complex_id, family_id, auto_calculated_points, final_points, special_quota, ranking_position, status)
        VALUES ('HAB-2026-0001', ?, ?, ?, 70, 70, 'GERAL', 1, 'HABILITADO')
    ''', (prog_id, complex_id, fam1_id))

    # 13. MROSC - Organizações da Sociedade Civil Parceiras
    db.execute('''
        INSERT OR IGNORE INTO social_oscs
        (cnpj, corporate_name, trade_name, legal_representative, representative_cpf, phone, email, address,
         cnd_federal_valid_until, cnd_state_valid_until, cnd_municipal_valid_until, fgts_crf_valid_until, cndt_labor_valid_until, registration_status)
        VALUES ('29.123.456/0001-89', 'Associação de Pais e Amigos dos Excepcionais de Rio das Ostras - APAE', 'APAE Rio das Ostras',
                'Maria Helena Castilho', '234.567.890-12', '(22) 2764-8899', 'apae.riodasostras@gmail.com', 'Rua Beira Rio, 45 - Centro',
                '2026-12-31', '2026-12-31', '2026-12-31', '2026-12-31', '2026-12-31', 'REGULAR')
    ''')
    osc_id = db.execute("SELECT id FROM social_oscs WHERE cnpj = '29.123.456/0001-89'").fetchone()[0]

    db.execute('''
        INSERT OR IGNORE INTO social_osc_work_plans
        (osc_id, title, object_summary, justification, target_public, total_requested_amount, approval_status)
        VALUES (?, 'Projeto Autonomia e Inclusão SUAS', 'Atendimento socioassistencial especializado para 80 pessoas com deficiência intelectual e múltipla e suas famílias.',
                'Fortalecimento de vínculos familiares e inclusão comunitária no município.', 'Pessoas com deficiência intelectual e suas famílias', 240000.00, 'APROVADO')
    ''', (osc_id,))
    wp_id = db.execute("SELECT id FROM social_osc_work_plans WHERE osc_id = ?", (osc_id,)).fetchone()[0]

    db.execute('''
        INSERT OR IGNORE INTO social_osc_contracts
        (work_plan_id, osc_id, partnership_type, contract_number, signature_date, start_date, end_date, global_value,
         budget_allocation_code, dedicated_bank_account, public_manager_name, status)
        VALUES (?, ?, 'TERMO_DE_COLABORACAO', 'TC-001/2026-SEMAS', '2026-01-02', '2026-01-02', '2026-12-31', 240000.00,
                '08.244.0012.2045.335039', 'Banco do Brasil Agência 2345-0 C/C 12345-6', 'Fernanda de Souza', 'VIGENTE')
    ''', (wp_id, osc_id))

    db.commit()
    print("Módulo de Assistência Social (SUAS / CRAS / CREAS / CadÚnico) semeado com sucesso!")

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        seed_social()

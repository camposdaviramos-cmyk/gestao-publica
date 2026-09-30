import json
from db import get_db
from domain import now

def seed_transparency():
    db = get_db()
    
    # 1. Configurações padrão
    configs = [
        ('covid_enabled', '1', 'Habilita o menu em destaque e páginas do tema COVID-19 / Calamidade Pública'),
        ('show_liquidation_col', '1', 'Exibe a coluna "Em Liquidação" na consulta de despesas'),
        ('show_chronological_justification', '1', 'Exibe a coluna "Justificativa" na ordem cronológica de pagamentos'),
        ('show_chronological_order', '1', 'Exibe a coluna "Ordem de Pagamento" na ordem cronológica'),
        ('revenue_summary_text', 'Demonstrativo consolidado de arrecadação das receitas orçamentárias e transferências constitucionais do Município.', 'Texto explicativo do resumo de receitas'),
        ('expense_summary_text', 'Execução da despesa pública municipal por fases: empenho, liquidação e pagamento, atendendo à Lei 4.320/64 e LRF.', 'Texto explicativo do resumo de despesas'),
        ('sic_physical_location', 'Rua Campo de Albacora, 75 - Loteamento Atlântica, Rio das Ostras - RJ, CEP: 28895-664', 'Endereço físico do Serviço de Informações ao Cidadão (SIC)'),
        ('sic_responsible', 'Ouvidoria Geral do Município - Dra. Mariana Alencar', 'Responsável pelo SIC'),
        ('sic_hours', 'Segunda a Sexta-feira, das 09h às 17h', 'Horário de atendimento do SIC'),
        ('sic_phone', '(22) 2771-6000 / (22) 2771-6100', 'Telefone do SIC'),
        ('portal_maintainer', 'Secretaria Municipal de Gestão Pública e Tecnologia da Informação', 'Responsável pela manutenção do Portal')
    ]
    for k, v, desc in configs:
        db.execute("""
            INSERT INTO transparency_configs(key, value, description, updated_at)
            VALUES(?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value, description=excluded.description, updated_at=excluded.updated_at
        """, (k, v, desc, now()))

    # 2. Temas COVID-19 / Calamidade Pública em ordem alfabética (transparency.140)
    if not db.execute("SELECT 1 FROM transparency_covid_themes LIMIT 1").fetchone():
        themes = [
            ('Ações Sociais e Benefícios Emergenciais', '/portal#/covid?cat=social', 'Auxílios e cestas básicas distribuídas durante o período de emergência', 1, 1),
            ('Aquisições de Medicamentos e Insumos Hospitalares', '/portal#/covid?cat=medicamentos', 'Contratações emergenciais de insumos de saúde', 0, 2),
            ('Contratações Temporárias de Pessoal de Saúde', '/portal#/covid?cat=pessoal', 'Médicos, enfermeiros e técnicos contratados para combate à pandemia', 0, 3),
            ('Contratos Administrativos Emergenciais', '/portal#/covid?cat=contratos', 'Relação de contratos firmados com amparo no regime de emergência', 1, 4),
            ('Decretos Municipais de Calamidade Pública', '/portal#/covid?cat=legislacao', 'Atos normativos e decretos do Poder Executivo Municipal', 1, 5),
            ('Despesas Orçamentárias e Restos a Pagar COVID-19', '/portal#/covid?cat=despesas', 'Execução da despesa segregada em orçamentárias e restos a pagar', 0, 6),
            ('Doações e Transferências Recebidas', '/portal#/covid?cat=repasses', 'Recursos repassados pela União e Estado do Rio de Janeiro', 0, 7),
            ('Leitos e Estrutura Hospitalar', '/portal#/covid?cat=leitos', 'Aquisição de respiradores e custeio de leitos de UTI', 0, 8),
            ('Licitações e Compras Diretas COVID-19', '/portal#/covid?cat=licitacoes', 'Dispensas e processos com fundamentação legal destacada', 0, 9),
            ('Receitas e Fontes de Recursos Específicos', '/portal#/covid?cat=receitas', 'Receitas vinculadas ao enfrentamento de emergências em saúde', 0, 10),
        ]
        for t_name, l_url, desc, is_cal, s_ord in themes:
            db.execute("""
                INSERT INTO transparency_covid_themes(theme_name, link_url, description, is_calamity, sort_order, created_at)
                VALUES(?, ?, ?, ?, ?, ?)
            """, (t_name, l_url, desc, is_cal, s_ord, now()))

    # 3. Dívida Ativa da Fazenda Municipal (transparency.146)
    if not db.execute("SELECT 1 FROM transparency_active_debt LIMIT 1").fetchone():
        debts = [
            ('ATLÂNTICA EMPREENDIMENTOS IMOBILIÁRIOS LTDA', '12.345.678/0001-90', 'IM-045821', 'CDA-2024/00892', 'PA-012/2024', 'IPTU e Taxas Imobiliárias', 2024, 18500000, 21250000, 'Ajuizado', '2024-03-10'),
            ('AUTO POSTO COSTA AZUL DE RIO DAS OSTRAS LTDA', '98.765.432/0001-10', 'IM-012456', 'CDA-2025/00145', 'PA-088/2025', 'ISSQN Próprio e Retido', 2025, 6200000, 6750000, 'Inscrito', '2025-05-18'),
            ('MINERAÇÃO E COMÉRCIO DE AREIA MARILEA LTDA', '23.456.789/0001-22', 'IM-078912', 'CDA-2023/01140', 'PA-045/2023', 'Taxa de Fiscalização Ambiental', 2023, 3400000, 4200000, 'Parcelado', '2023-08-22'),
            ('HOTEL E POUSADA PRAIA DA TARTARUGA EIRELI', '34.567.890/0001-33', 'IM-033441', 'CDA-2025/00312', 'PA-102/2025', 'Taxa de Coleta de Lixo e IPTU', 2025, 4150000, 4390000, 'Inscrito', '2025-09-01'),
            ('TRANSLITORAL LOGÍSTICA E TRANSPORTES LTDA', '45.678.901/0001-44', 'IM-099882', 'CDA-2024/00714', 'PA-067/2024', 'Multas de Trânsito e Posturas', 2024, 1950000, 2280000, 'Inscrito', '2024-11-12')
        ]
        for nm, doc, im, cda, proc, nat, yr, orig, upd, st, dt in debts:
            db.execute("""
                INSERT INTO transparency_active_debt(debtor_name, document, municipal_registration, cda_number, process_number, debt_nature, fiscal_year, original_amount, updated_amount, status, enrollment_date, created_at)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (nm, doc, im, cda, proc, nat, yr, orig, upd, st, dt, now()))

    # 4. Emendas Parlamentares Impositivas (transparency.147)
    if not db.execute("SELECT 1 FROM transparency_parliamentary_amendments LIMIT 1").fetchone():
        amendments = [
            ('Federal', 'Deputado Federal Rodrigo Maia', 'EM-FED-2026/014', 2026, 'Individual', 150000000, 150000000, 120000000, 120000000, 'Aquisição de ambulâncias e equipamentos para Unidade de Pronto Atendimento (UPA)', 'Fundo Municipal de Saúde', 'Em execução'),
            ('Estadual', 'Deputada Estadual Marina do Vale', 'EM-EST-2026/008', 2026, 'Individual', 80000000, 80000000, 75000000, 60000000, 'Reforma e modernização da Escola Municipal Cidade Praiana', 'Secretaria Municipal de Educação', 'Em execução'),
            ('Municipal', 'Vereador Carlos Roberto (Beto da Saúde)', 'EM-MUN-2026/001', 2026, 'Individual', 35000000, 35000000, 35000000, 35000000, 'Pavimentação e drenagem de vias públicas no Bairro Mariléa', 'Secretaria Municipal de Obras', 'Concluída'),
            ('Municipal', 'Bancada Parlamentar Feminina', 'EM-MUN-2026/002', 2026, 'Bancada', 50000000, 50000000, 30000000, 20000000, 'Implantação do Centro de Referência e Atendimento à Mulher (CRAM)', 'Secretaria de Bem-Estar Social', 'Em execução'),
            ('Federal', 'Bancada do Rio de Janeiro', 'EM-FED-2026/089', 2026, 'Bancada', 300000000, 250000000, 180000000, 150000000, 'Macro-drenagem e contenção de encostas na Bacia de Costazul', 'Secretaria Municipal de Meio Ambiente', 'Em execução')
        ]
        for sph, aut, num, yr, tp, ind, com, liq, pd, obj, ben, st in amendments:
            db.execute("""
                INSERT INTO transparency_parliamentary_amendments(sphere, author, amendment_number, fiscal_year, amendment_type, indicated_amount, committed_amount, liquidated_amount, paid_amount, object, beneficiary, status, created_at)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (sph, aut, num, yr, tp, ind, com, liq, pd, obj, ben, st, now()))

    # 5. Diárias e Passagens (transparency.24, 135, 137)
    if not db.execute("SELECT 1 FROM transparency_travel_expenses LIMIT 1").fetchone():
        travels = [
            ('João Carlos Ferreira da Silva', 'MAT-01428', 'Auditor Fiscal de Tributos', 'Secretaria Municipal de Fazenda', 'Lei Municipal nº 1.450/2012', 'Portaria SMF nº 032/2026', '2026-04-10', '2026-04-13', 'Brasília - DF', 'Aéreo', 145000, 'Participação no Fórum Nacional de Secretários e Auditores de Finanças Municipais', 3.5, 45000, 157500, '3.3.90.14.14 - Diárias no País'),
            ('Dra. Vanessa Coutinho Santos', 'MAT-02190', 'Procuradora Geral do Município', 'Procuradoria Geral', 'Lei Municipal nº 1.450/2012', 'Portaria PGM nº 018/2026', '2026-05-02', '2026-05-03', 'Rio de Janeiro - RJ', 'Terrestre', 28000, 'Sustentação oral junto ao Tribunal de Contas do Estado do Rio de Janeiro (TCE-RJ)', 1.5, 38000, 57000, '3.3.90.14.14 - Diárias no País'),
            ('Eng. Marcelo Ramos de Oliveira', 'MAT-03114', 'Engenheiro Civil Fiscal', 'Secretaria Municipal de Obras', 'Lei Municipal nº 1.450/2012', 'Portaria SMO nº 044/2026', '2026-06-15', '2026-06-16', 'Niterói - RJ', 'Veículo Oficial', 0, 'Vistoria técnica de laboratório de controle tecnológico de pavimentação asfáltica', 1.0, 32000, 32000, '3.3.90.14.14 - Diárias no País')
        ]
        for nm, reg, rl, dp, lw, act, s_dt, e_dt, dst, tr_tp, tr_cst, obj, qty, u_val, tot, bk in travels:
            db.execute("""
                INSERT INTO transparency_travel_expenses(employee_name, registration, role, department, authorization_law, concession_act, start_date, end_date, destination, transport_type, transport_cost, objective, daily_allowance_qty, daily_allowance_unit_value, total_amount, expense_breakdown, created_at)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (nm, reg, rl, dp, lw, act, s_dt, e_dt, dst, tr_tp, tr_cst, obj, qty, u_val, tot, bk, now()))

    # 6. Concursos Públicos e Vagas (transparency.60, 61, 62, 63, 64)
    if not db.execute("SELECT 1 FROM transparency_competitions LIMIT 1").fetchone():
        comps = [
            ('Concurso Público', '001/2025', 'Edital nº 01/2025 / Lei Municipal nº 2.110/2019', '2025-01-15', '2025-07-20', '2027-07-20', None, 'Secretaria Municipal de Educação e Saúde', 'Homologado', 250, 180, 70, '/anexos/concursos/edital_001_2025.pdf'),
            ('Processo Seletivo Simplificado', '002/2026', 'Edital PSS nº 02/2026 / Lei Complementar nº 89/2022', '2026-02-10', '2026-03-30', '2027-03-30', None, 'Secretaria Municipal de Bem-Estar Social', 'Em andamento', 45, 0, 45, '/anexos/concursos/edital_002_2026.pdf'),
            ('Concurso Público', '001/2021', 'Edital nº 01/2021 / Lei Municipal nº 1.980/2018', '2021-08-01', '2022-02-15', '2024-02-15', '2026-02-15', 'Quadro Geral Administrativo', 'Encerrado', 120, 120, 0, '/anexos/concursos/edital_001_2021.pdf')
        ]
        for c_tp, num, lw, p_dt, h_dt, v_dt, ex_dt, dp, st, v_cr, v_fl, v_av, att in comps:
            db.execute("""
                INSERT INTO transparency_competitions(competition_type, number_year, edict_law, publication_date, homologation_date, validity_date, extension_date, department, status, vacancies_created, vacancies_filled, vacancies_available, attachment_url, created_at)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (c_tp, num, lw, p_dt, h_dt, v_dt, ex_dt, dp, st, v_cr, v_fl, v_av, att, now()))

    # 7. Perguntas Frequentes (FAQ) (transparency.91)
    if not db.execute("SELECT 1 FROM transparency_faq LIMIT 1").fetchone():
        faqs = [
            ('Geral', 'O que é o Portal da Transparência de Rio das Ostras?', 'É um canal de acesso público mantido pela Prefeitura Municipal para que qualquer cidadão acompanhe a arrecadação das receitas, a execução das despesas, as licitações, os contratos, as obras públicas e a folha de pagamento, em estrito cumprimento à Lei nº 12.527/2011 (LAI) e à Lei de Responsabilidade Fiscal.', 1),
            ('Acesso à Informação', 'Qual é o prazo legal para resposta de um pedido de informação pelo e-SIC?', 'De acordo com o Art. 11 da Lei nº 12.527/2011, caso a informação esteja disponível imediatamente, o acesso é concedido de pronto. Caso contrário, o órgão possui prazo de até 20 (vinte) dias, prorrogável justificadamente por mais 10 (dez) dias.', 2),
            ('Licitações', 'Onde posso consultar as Atas de Registro de Preços vigentes?', 'As Atas de Registro de Preços (SRP) regidas pela Lei nº 14.133/2021 podem ser consultadas na aba "Licitações & Contratos", com indicação do número da ata, objeto, fornecedor beneficiário, saldo remanescente e adesões autorizadas.', 3),
            ('Dívida Ativa', 'Como consultar a relação de contribuintes inscritos em Dívida Ativa?', 'Acesse o menu destacado "Dívida Ativa Municipal", onde é possível pesquisar devedores por nome, CPF/CNPJ, inscrição municipal ou número da Certidão de Dívida Ativa (CDA), com informações sobre o montante e a situação fiscal.', 4),
            ('COVID-19', 'Onde encontro as informações sobre contratações na pandemia e calamidades?', 'O Portal possui um menu em destaque denominado "COVID-19 & Calamidade Pública", com abas dedicadas para contratos, licitações, despesas orçamentárias e restos a pagar, além de receitas vinculadas.', 5)
        ]
        for cat, q, a, ord in faqs:
            db.execute("""
                INSERT INTO transparency_faq(category, question, answer, sort_order, created_at)
                VALUES(?, ?, ?, ?, ?)
            """, (cat, q, a, ord, now()))

    # 8. Menus customizados (transparency.100, 101)
    if not db.execute("SELECT 1 FROM transparency_custom_menus LIMIT 1").fetchone():
        menus = [
            ('Diário Oficial do Município', 'https://www.riodasostras.rj.gov.br/diario-oficial/', 'external', 'Publicações', 1, 1),
            ('Carta de Serviços ao Cidadão', '/portal#/services', 'book', 'Institucional', 0, 2),
            ('Conselhos Municipais', '/portal#/councils', 'users', 'Institucional', 0, 3),
            ('Prestação de Contas TCE-RJ', '/portal#/tcerj', 'shield', 'Controle', 1, 4)
        ]
        for tit, u, ic, cat, high, s_ord in menus:
            db.execute("""
                INSERT INTO transparency_custom_menus(title, url, icon, category, is_highlighted, sort_order, is_active, created_at)
                VALUES(?, ?, ?, ?, ?, ?, 1, ?)
            """, (tit, u, ic, cat, high, s_ord, now()))

    db.commit()

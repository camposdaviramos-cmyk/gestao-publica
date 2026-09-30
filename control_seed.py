"""Carga inicial e sementes de dados para o módulo de Controle Interno e Controladoria.
Atende aos requisitos de automação de obrigações, regras SICONFI, requisitos CAUC e dados IBGE.
"""
import calendar
from datetime import datetime, date
from db import get_db
from domain import now

def get_last_day_of_month(year, month):
    _, last_day = calendar.monthrange(year, month)
    return f"{year:04d}-{month:02d}-{last_day:02d}"

def seed_control(entity_id=1, exercise=2026):
    db = get_db()

    # 1. Dados do Município com base no IBGE e limites constitucionais
    db.execute("""
        INSERT OR IGNORE INTO control_ibge_data (
            entity_id, exercise, municipio_nome, cod_ibge, populacao,
            limite_pessoal_executivo_pct, limite_pessoal_legislativo_pct,
            limite_repasse_camara_pct, receita_corrente_liquida, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        entity_id, exercise, 'Rio das Ostras', '3304524', 156491,
        54.0, 6.0, 7.0, 98540000000, now()
    ))

    # 2. Grupos de Responsáveis
    groups = [
        ('Contabilidade Geral', 'Responsável pela elaboração de balanços, RREO, RGF e envio ao SICONFI', 'Contador Geral', 'contabilidade@riodasostras.rj.gov.br'),
        ('Recursos Humanos e Folha', 'Responsável pelo eSocial, EFD-Reinf, DCTFWeb e encargos trabalhistas', 'Gestor de RH', 'rh@riodasostras.rj.gov.br'),
        ('Secretaria de Fazenda e Tributação', 'Responsável por certidões negativas, CADIN e arrecadação própria', 'Secretário de Fazenda', 'fazenda@riodasostras.rj.gov.br'),
        ('Controladoria Geral do Município', 'Coordenação do controle interno, auditorias, CAUC e emissão de pareceres', 'Controlador Geral', 'controladoria@riodasostras.rj.gov.br'),
        ('Gestão de Convênios e Contratos', 'Acompanhamento de prestações de contas no Transferegov e SICONV', 'Gestor de Convênios', 'convenios@riodasostras.rj.gov.br')
    ]
    group_map = {}
    for g_name, g_desc, g_lead, g_mail in groups:
        row = db.execute("SELECT id FROM control_obligation_groups WHERE entity_id=? AND name=?", (entity_id, g_name)).fetchone()
        if not row:
            gid = db.execute("INSERT INTO control_obligation_groups(entity_id, name, description, leader_name, leader_email, created_at) VALUES(?,?,?,?,?,?)",
                             (entity_id, g_name, g_desc, g_lead, g_mail, now())).lastrowid
        else:
            gid = row['id']
        group_map[g_name] = gid

    # 3. Carga Automática de Obrigações Legais (Federais, Estaduais e Municipais)
    obligations = [
        # Federais
        ('OBR-FED-01', 'Envio do RREO ao SICONFI (Bimestral)', 'Relatório Resumido da Execução Orçamentária no SICONFI até 30 dias após encerramento do bimestre',
         'Federal', 'Contabilidade Pública', 'Lei de Responsabilidade Fiscal (LC 101/2000, art. 52)', 'Transmissão Eletrônica SICONFI', 'Secretaria do Tesouro Nacional',
         'https://siconfi.tesouro.gov.br', 'Obrigatório para manutenção do CAUC', 'Contabilidade Geral', 'Bimestral', 2, f"{exercise}-02-28", 6),

        ('OBR-FED-02', 'Envio do RGF ao SICONFI (Quadrimestral)', 'Relatório de Gestão Fiscal referente a limites de pessoal, dívida e garantias',
         'Federal', 'Gestão Fiscal', 'Lei de Responsabilidade Fiscal (LC 101/2000, arts. 54 e 55)', 'Transmissão Eletrônica SICONFI', 'Secretaria do Tesouro Nacional',
         'https://siconfi.tesouro.gov.br', 'Obrigatório para regularidade de transferências voluntárias', 'Contabilidade Geral', 'Quadrimestral', 4, f"{exercise}-04-30", 3),

        ('OBR-FED-03', 'Transmissão da DCTFWeb e EFD-Reinf', 'Declaração de Débitos e Créditos Tributários Federais Previdenciários e de Outras Entidades',
         'Federal', 'Tributário / Previdenciário', 'Instrução Normativa RFB nº 2005/2021', 'Portal e-CAC / SPED', 'Receita Federal do Brasil',
         'https://cav.receita.fazenda.gov.br', 'Vencimento mensal até o 15º dia do mês subsequente', 'Recursos Humanos e Folha', 'Mensal', 1, f"{exercise}-01-15", 12),

        ('OBR-FED-04', 'Fechamento dos Eventos Periódicos do eSocial', 'Envio dos eventos S-1200, S-1210 e fechamento S-1299 da folha de pagamento municipal',
         'Federal', 'Recursos Humanos', 'Decreto Federal nº 8.373/2014', 'Webservice eSocial / SPED', 'Comitê Diretivo do eSocial',
         'https://www.gov.br/esocial', 'Transmissão até o dia 15 de cada mês', 'Recursos Humanos e Folha', 'Mensal', 1, f"{exercise}-01-15", 12),

        ('OBR-FED-05', 'Alimentação e Transmissão do SIOPE (Educação)', 'Sistema de Informações sobre Orçamentos Públicos em Educação - Comprovação de 25% MDE e FUNDEB',
         'Federal', 'Educação', 'Lei Federal nº 9.394/1996 e Lei nº 14.113/2020', 'Transmissão SIOPE Web', 'FNDE / MEC',
         'https://www.fnde.gov.br/siope', 'Envio bimestral para manutenção de transferências de convênios', 'Contabilidade Geral', 'Bimestral', 2, f"{exercise}-02-28", 6),

        ('OBR-FED-06', 'Alimentação e Homologação do SIOPS (Saúde)', 'Sistema de Informações sobre Orçamentos Públicos em Saúde - Comprovação de 15% em ASPS',
         'Federal', 'Saúde', 'Lei Complementar nº 141/2012', 'Software Transmissor SIOPS', 'Ministério da Saúde',
         'https://siops.datasus.gov.br', 'Requisito direto do CAUC', 'Contabilidade Geral', 'Bimestral', 2, f"{exercise}-02-28", 6),

        ('OBR-FED-07', 'Monitoramento da Regularidade Fiscal no CAUC', 'Verificação mensal contínua dos Requisitos Fiscais do Cadastro Único de Convênios do Tesouro Nacional',
         'Federal', 'Controle da Regularidade Fiscal', 'Portaria STN nº 1.446/2022', 'Consulta Automática CAUC', 'Secretaria do Tesouro Nacional',
         'https://cauc.tesouro.gov.br', 'Prevenção de bloqueios para celebração de novos convênios', 'Controladoria Geral do Município', 'Mensal', 1, f"{exercise}-01-31", 12),

        # Estaduais
        ('OBR-EST-01', 'Remessa Mensal SIGFIS - Módulo Contábil e Folha (TCE-RJ)', 'Envio de balancetes mensais e demonstrativos contábeis e de pessoal ao Tribunal de Contas do RJ',
         'Estadual', 'Controle Externo', 'Deliberação TCE-RJ nº 278/2017 e Instruções Normativas', 'Portal e-TCE / SIGFIS', 'Tribunal de Contas do Estado do Rio de Janeiro',
         'https://www.tce.rj.gov.br', 'Envio impreterível até o último dia útil do mês subsequente', 'Contabilidade Geral', 'Mensal', 1, f"{exercise}-01-31", 12),

        ('OBR-EST-02', 'Prestação de Contas Anual de Governo do Prefeito (TCE-RJ)', 'Relatório formal com balanços consolidados, relatórios de controle interno e parecer prévio',
         'Estadual', 'Prestação de Contas Anual', 'Constituição Estadual do RJ e Lei Orgânica Municipal', 'Processo Eletrônico e-TCE', 'Tribunal de Contas do Estado do Rio de Janeiro',
         'https://www.tce.rj.gov.br', 'Prazo fatal: 31 de março do exercício subsequente', 'Controladoria Geral do Município', 'Anual', 12, f"{exercise}-03-31", 1),

        # Municipais
        ('OBR-MUN-01', 'Emissão do Relatório Conclusivo do Controle Interno', 'Relatório mensal com manifestação fundamentada sobre execução orçamentária, licitações e contratos',
         'Municipal', 'Controle Interno', 'Lei Orgânica Municipal e Resolução CGM nº 001/2026', 'Sistema ERP Integrado', 'Gabinete do Prefeito e Secretarias',
         'http://127.0.0.1:8080/#/control', 'Publicação interna e arquivamento para auditoria externa', 'Controladoria Geral do Município', 'Mensal', 1, f"{exercise}-01-31", 12),

        ('OBR-MUN-02', 'Publicação no Diário Oficial e Portal da Transparência', 'Publicação oficial do RREO em Diário Oficial do Município em até 30 dias após o bimestre',
         'Municipal', 'Publicidade Oficial', 'Art. 52 da LRF e Lei Municipal de Transparência', 'Portal da Transparência e Imprensa Oficial', 'Sociedade Civil',
         'http://127.0.0.1:8080/portal', 'Disponibilização integral em dados abertos', 'Controladoria Geral do Município', 'Bimestral', 2, f"{exercise}-02-28", 6)
    ]

    for (code, title, desc, leg_type, subj, leg, deliv, dest, url, notes, grp_name, freq, interval, first_due, total_occ) in obligations:
        gid = group_map.get(grp_name)
        lead_name = 'Responsável Designado'
        lead_email = 'controle@riodasostras.rj.gov.br'
        for g_n, _, g_l, g_m in groups:
            if g_n == grp_name:
                lead_name, lead_email = g_l, g_m
                break

        row = db.execute("SELECT id FROM control_obligations WHERE entity_id=? AND exercise=? AND code=?", (entity_id, exercise, code)).fetchone()
        if not row:
            ob_id = db.execute("""
                INSERT INTO control_obligations (
                    entity_id, exercise, code, title, description, legislation_type, subject_group,
                    legislation, delivery_method, destination, source_url, notes, group_id,
                    owner_name, owner_email, frequency, interval_months, first_due_date, total_occurrences, active, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            """, (
                entity_id, exercise, code, title, desc, leg_type, subj,
                leg, deliv, dest, url, notes, gid,
                lead_name, lead_email, freq, interval, first_due, total_occ, now()
            )).lastrowid
        else:
            ob_id = row['id']

        # Gerar Ocorrências caso ainda não existam
        occ_count = db.execute("SELECT COUNT(*) FROM control_occurrences WHERE obligation_id=?", (ob_id,)).fetchone()[0]
        if occ_count == 0:
            due_dt = datetime.strptime(first_due, '%Y-%m-%d')
            for i in range(1, total_occ + 1):
                # Calcular competência e vencimento
                if freq == 'Mensal':
                    comp_month = i
                    comp_year = exercise
                    occ_title = f"{title} - Competência {comp_year:04d}/{comp_month:02d}"
                    # Vencimento no mês subsequente
                    due_month = comp_month + 1
                    due_year = comp_year
                    if due_month > 12:
                        due_month = 1
                        due_year += 1
                    day = due_dt.day
                    if day > 28:
                        due_str = get_last_day_of_month(due_year, due_month)
                    else:
                        due_str = f"{due_year:04d}-{due_month:02d}-{day:02d}"
                elif freq == 'Bimestral':
                    b_num = i
                    occ_title = f"{title} - {b_num}º Bimestre/{exercise}"
                    end_b_month = b_num * 2
                    due_month = end_b_month + 1
                    due_year = exercise
                    if due_month > 12:
                        due_month = 1
                        due_year += 1
                    due_str = get_last_day_of_month(due_year, due_month)
                    comp_month = end_b_month
                elif freq == 'Quadrimestral':
                    q_num = i
                    occ_title = f"{title} - {q_num}º Quadrimestre/{exercise}"
                    end_q_month = q_num * 4
                    due_month = end_q_month + 1
                    due_year = exercise
                    if due_month > 12:
                        due_month = 1
                        due_year += 1
                    due_str = get_last_day_of_month(due_year, due_month)
                    comp_month = end_q_month
                else: # Anual
                    occ_title = f"{title} - Exercício {exercise}"
                    due_str = f"{exercise + 1}-03-31"
                    comp_month = 12

                competence = f"{exercise:04d}-{comp_month:02d}"
                # Determinar status preliminar: se data passada, marca atendida ou a vencer
                today_str = date.today().strftime('%Y-%m-%d')
                if due_str < today_str:
                    st = 'Atendida'
                    cl_at = due_str + "T10:00:00"
                    cl_by = lead_name
                else:
                    st = 'A Vencer'
                    cl_at = None
                    cl_by = None

                db.execute("""
                    INSERT INTO control_occurrences (
                        obligation_id, entity_id, exercise, occurrence_number, title, competence,
                        due_date, status, closed_at, closed_by, owner_name, owner_email, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ob_id, entity_id, exercise, i, occ_title, competence,
                    due_str, st, cl_at, cl_by, lead_name, lead_email, now(), now()
                ))

    # 4. Regras do Ranking da Qualidade da Informação Contábil e Fiscal (SICONFI - Dimensões 1, 2, 3 e 4)
    siconfi_rules = [
        # Dimensão 1: Gestão da Informação
        ('STN-D1-01', 'Envio Tempestivo da Matriz de Saldos Contábeis (MSC)', 1, 'Executivo', 'Mensal',
         'Averigua se a MSC foi enviada dentro do prazo regulamentar do SICONFI (até o último dia do mês subsequente).', 'data_envio <= prazo_limite', 0, 'Contador Geral'),
        ('STN-D1-02', 'Consistência de Envio dos Demonstrativos RREO e RGF', 1, 'Executivo', 'Bimestral',
         'Verifica a regularidade da entrega e homologação dos relatórios fiscais no sistema da STN.', 'status_homologacao == "Homologado"', 0, 'Contador Geral'),

        # Dimensão 2: Informações Contábeis
        ('STN-D2-01', 'Equilíbrio Fundamental do Balanço Patrimonial (Ativo = Passivo + PL)', 2, 'Executivo', 'Mensal',
         'O total do Ativo deve ser rigorosamente igual à soma do Passivo com o Patrimônio Líquido na MSC.', 'abs(total_ativo - (total_passivo + total_pl)) == 0', 0, 'Contador Geral'),
        ('STN-D2-02', 'Disponibilidade por Destinação de Recursos (DDR x Contas Caixa)', 2, 'Executivo', 'Mensal',
         'O saldo das disponibilidades financeiras na classe 7 e 8 (DDR) deve coincidir com os saldos das contas bancárias e caixa na classe 1.', 'saldo_ddr == saldo_caixa_bancos', 0, 'Contador Geral'),
        ('STN-D2-03', 'Resultado Patrimonial da Competência (VPA x VPD)', 2, 'Executivo', 'Mensal',
         'A diferença entre Variações Patrimoniais Aumentativas e Diminutivas deve coincidir com o superávit/déficit apurado no Balanço Patrimonial.', 'vpa - vpd == superavit_apurado', 0, 'Contador Geral'),
        ('STN-D2-04', 'Inexistência de Saldos Invertidos em Contas de Natureza Devedora/Credora', 2, 'Executivo', 'Mensal',
         'Contas do Ativo não podem apresentar saldo credor e contas do Passivo não podem apresentar saldo devedor.', 'contas_invertidas_count == 0', 0, 'Contador Geral'),

        # Dimensão 3: Informações Fiscais
        ('STN-D3-01', 'Limite da Despesa Total com Pessoal - Poder Executivo (Art. 19/20 LRF)', 3, 'Executivo', 'Quadrimestral',
         'A Despesa Total com Pessoal do Poder Executivo não pode ultrapassar o limite legal de 54,00% da Receita Corrente Líquida.', 'despesa_pessoal_pct <= 54.0', 0, 'Controlador Geral'),
        ('STN-D3-02', 'Limite da Despesa Total com Pessoal - Poder Legislativo (Art. 19/20 LRF)', 3, 'Legislativo', 'Quadrimestral',
         'A Despesa Total com Pessoal do Poder Legislativo não pode ultrapassar o limite legal de 6,00% da Receita Corrente Líquida.', 'despesa_pessoal_leg_pct <= 6.0', 0, 'Controlador Geral'),
        ('STN-D3-03', 'Aplicação Constitucional em Educação - MDE (Art. 212 CF/88)', 3, 'Executivo', 'Bimestral',
         'Aplicação mínima de 25,00% das receitas resultantes de impostos e transferências em Manutenção e Desenvolvimento do Ensino.', 'aplicacao_mde_pct >= 25.0', 0, 'Controlador Geral'),
        ('STN-D3-04', 'Aplicação Constitucional em Ações e Serviços Públicos de Saúde (LC 141/2012)', 3, 'Executivo', 'Bimestral',
         'Aplicação mínima de 15,00% da receita de impostos e transferências em Ações e Serviços Públicos de Saúde.', 'aplicacao_saude_pct >= 15.0', 0, 'Controlador Geral'),
        ('STN-D3-05', 'Equilíbrio da Disponibilidade de Caixa x Restos a Pagar (Art. 42 da LRF)', 3, 'Executivo', 'Quadrimestral',
         'Existência de suficiência de caixa para cobertura de restos a pagar inscritos nos dois últimos quadrimestres do mandato.', 'disponibilidade_liquida >= 0', 0, 'Controlador Geral'),

        # Dimensão 4: Informações Contábeis x Fiscais
        ('STN-D4-01', 'Confronto Despesa Liquidada no RREO x VPD Registrada no Razão Contábil', 4, 'Executivo', 'Bimestral',
         'A despesa orçamentária liquidada deve manter conformidade com as variações patrimoniais diminutivas registradas nas contas de resultado.', 'abs(liquidado_rreo - vpd_contabil) <= 1000', 1000, 'Contador Geral'),
        ('STN-D4-02', 'Confronto Receita Arrecadada no RREO x VPA Registrada no Razão Contábil', 4, 'Executivo', 'Bimestral',
         'A receita orçamentária arrecadada deve manter conformidade com as variações patrimoniais aumentativas registradas.', 'abs(arrecadado_rreo - vpa_contabil) <= 1000', 1000, 'Contador Geral')
    ]

    for r_code, r_title, r_dim, r_pow, r_interv, r_desc, r_form, r_tol, r_owner in siconfi_rules:
        row = db.execute("SELECT id FROM control_siconfi_rules WHERE entity_id=? AND rule_code=?", (entity_id, r_code)).fetchone()
        if not row:
            rule_id = db.execute("""
                INSERT INTO control_siconfi_rules (
                    entity_id, rule_code, title, dimension, power, interval_type,
                    description, formula, tolerance_cents, active, owner_name, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
            """, (
                entity_id, r_code, r_title, r_dim, r_pow, r_interv,
                r_desc, r_form, r_tol, r_owner, now(), now()
            )).lastrowid
        else:
            rule_id = row['id']

        # Avaliação de exemplo para a competência atual
        ev_count = db.execute("SELECT COUNT(*) FROM control_siconfi_evaluations WHERE rule_id=?", (rule_id,)).fetchone()[0]
        if ev_count == 0:
            # Regras da D2 e D3 com status majoritariamente Conforme (verde) e 1 em Não Conforme (vermelho) para evidenciar plano de ação
            st = 'Conforme'
            v_val = 'Consistente'
            b_val = 'Atendido 100%'
            notes = 'Validação aprovada sem divergências na MSC do exercício.'
            if r_code == 'STN-D2-02':
                st = 'Não Conforme'
                v_val = 'Divergência de R$ 1.450,20'
                b_val = 'Diferença Zero'
                notes = 'Divergência entre conciliação bancária da conta FUNDEB e classe 8 DDR.'
            elif r_code == 'STN-D3-05':
                st = 'Conforme'
                v_val = 'Superávit Financeiro de R$ 14.850.320,00'
                b_val = 'Positivo'
                notes = 'Disponibilidade de caixa suficiente para restos a pagar.'

            db.execute("""
                INSERT INTO control_siconfi_evaluations (
                    entity_id, exercise, period, rule_id, status, verified_value, benchmark_value, notes, evaluated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entity_id, exercise, f"{exercise}-01", rule_id, st, v_val, b_val, notes, now()
            ))

    # 5. Requisitos Fiscais do CAUC (Cadastro Único de Convênios do Tesouro Nacional)
    cauc_items = [
        ('CAUC-1.1', 'I - Obrigações Financeiras', 'Certidão Negativa de Débitos Federais e Dívida Ativa (RFB/PGFN)',
         'Comprovação de regularidade quanto aos tributos federais e à Dívida Ativa da União administrados pela Receita Federal e Procuradoria Geral da Fazenda Nacional.',
         'Adimplente', 'Secretário de Fazenda', 'fazenda@riodasostras.rj.gov.br', '2026-11-30'),

        ('CAUC-1.2', 'I - Obrigações Financeiras', 'Certificado de Regularidade do FGTS (CRF)',
         'Comprovação de regularidade com os depósitos do Fundo de Garantia do Tempo de Serviço perante a Caixa Econômica Federal.',
         'Adimplente', 'Gestor de RH', 'rh@riodasostras.rj.gov.br', '2026-10-15'),

        ('CAUC-1.3', 'I - Obrigações Financeiras', 'Cadastro Informativo de Créditos não Quitados do Setor Público Federal (CADIN)',
         'Inexistência de registros de pendências financeiras do Município perante órgãos da administração pública federal.',
         'Adimplente', 'Secretário de Fazenda', 'fazenda@riodasostras.rj.gov.br', '2026-12-31'),

        ('CAUC-2.1', 'II - Adimplência Financeira', 'Certificado de Regularidade Previdenciária (CRP - RPPS/RGPS)',
         'Comprovação do cumprimento dos critérios e exigências legais para a emissão do CRP pelo Ministério da Previdência Social.',
         'Adimplente', 'Controlador Geral', 'controladoria@riodasostras.rj.gov.br', '2026-12-10'),

        ('CAUC-3.1', 'III - Prestação de Contas', 'Prestação de Contas de Recursos Federais Recebidos (SICONV/Transferegov)',
         'Adimplência quanto à prestação de contas dos convênios e contratos de repasse com órgãos federais.',
         'Adimplente', 'Gestor de Convênios', 'convenios@riodasostras.rj.gov.br', '2026-09-30'),

        ('CAUC-4.1', 'IV - Transparência e Gestão Fiscal', 'Aplicação Mínima em Saúde - SIOPS',
         'Comprovação de transmissão bimestral tempestiva e atendimento do percentual mínimo constitucional de 15% em Saúde.',
         'Adimplente', 'Contador Geral', 'contabilidade@riodasostras.rj.gov.br', '2026-08-31'),

        ('CAUC-4.2', 'IV - Transparência e Gestão Fiscal', 'Aplicação Mínima em Educação - SIOPE',
         'Comprovação de transmissão bimestral tempestiva e atendimento do percentual mínimo de 25% em Manutenção e Desenvolvimento do Ensino.',
         'Adimplente', 'Contador Geral', 'contabilidade@riodasostras.rj.gov.br', '2026-08-31'),

        ('CAUC-4.3', 'IV - Transparência e Gestão Fiscal', 'Homologação do RREO e RGF no SICONFI',
         'Publicação e homologação tempestiva dos demonstrativos fiscais no Sistema de Informações Contábeis e Fiscais da STN.',
         'Adimplente', 'Controlador Geral', 'controladoria@riodasostras.rj.gov.br', '2026-09-30')
    ]

    for c_code, c_grp, c_name, c_desc, c_st, c_resp, c_mail, c_valid in cauc_items:
        row = db.execute("SELECT id FROM control_cauc_requirements WHERE entity_id=? AND code=?", (entity_id, c_code)).fetchone()
        if not row:
            db.execute("""
                INSERT INTO control_cauc_requirements (
                    entity_id, code, group_name, name, description, status,
                    responsible_name, responsible_email, last_verified, valid_until
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entity_id, c_code, c_grp, c_name, c_desc, c_st,
                c_resp, c_mail, now()[:10], c_valid
            ))

    # 6. Extrato de Convênios Federais e Estaduais da STN
    agreements = [
        ('CV-2026/001', '894120/2026', 'Ministério das Cidades', 'Drenagem e pavimentação asfáltica nos bairros Costazul e Âncora',
         450000000, 420000000, 30000000, f"{exercise}-01-10", f"{exercise + 1}-12-31", 'Adimplente', 'Gestor de Convênios', 'convenios@riodasostras.rj.gov.br'),

        ('CV-2026/002', '912340/2026', 'Ministério da Saúde', 'Aquisição de equipamentos de tomografia e ultrassonografia para o Hospital Municipal',
         185000000, 175000000, 10000000, f"{exercise}-02-15", f"{exercise}-12-31", 'Adimplente', 'Gestor de Convênios', 'convenios@riodasostras.rj.gov.br'),

        ('CV-2026/003', 'SEC-RJ-045/2026', 'Governo do Estado do Rio de Janeiro', 'Reforma e modernização da Escola Municipal Inayá',
         98000000, 90000000, 8000000, f"{exercise}-03-01", f"{exercise}-10-31", 'Adimplente', 'Gestor de Convênios', 'convenios@riodasostras.rj.gov.br')
    ]

    for a_num, a_siconv, a_grantor, a_obj, a_tot, a_grant, a_count, a_start, a_end, a_status, a_resp, a_mail in agreements:
        row = db.execute("SELECT id FROM control_agreements WHERE entity_id=? AND agreement_number=?", (entity_id, a_num)).fetchone()
        if not row:
            db.execute("""
                INSERT INTO control_agreements (
                    entity_id, exercise, agreement_number, siconv_number, grantor, object,
                    total_amount, grantor_amount, counterpart_amount, start_date, end_date,
                    accountability_status, responsible_name, responsible_email, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entity_id, exercise, a_num, a_siconv, a_grantor, a_obj,
                a_tot, a_grant, a_count, a_start, a_end,
                a_status, a_resp, a_mail, now()
            ))

    # 7. Plano de Ação de Amostra para Item Não Conforme (ex: Divergência de DDR)
    row = db.execute("SELECT id FROM control_action_plans WHERE entity_id=? AND reference_id=?", (entity_id, 'STN-D2-02')).fetchone()
    if not row:
        db.execute("""
            INSERT INTO control_action_plans (
                entity_id, exercise, source_module, reference_id, title, fact, cause,
                corrective_action, responsible_name, responsible_email, deadline, status,
                created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entity_id, exercise, 'SICONFI', 'STN-D2-02', 'Regularização da conciliação bancária FUNDEB na MSC',
            'Foi constatada uma divergência de R$ 1.450,20 entre a conta corrente do FUNDEB e a respectiva classe 8 na MSC de janeiro.',
            'Tarifa bancária estornada tardiamente pela agência sem o devido lançamento contábil de estorno no exercício.',
            'Lançamento contábil retificador no razão para reconciliação imediata da disponibilidade por destinação de recursos.',
            'Contador Geral', 'contabilidade@riodasostras.rj.gov.br', f"{exercise}-02-15", 'Pendente',
            'Controlador Geral', now(), now()
        ))

    db.commit()
    print(f"Seed do Controle Interno concluído com sucesso para entidade {entity_id}, exercício {exercise}!")

if __name__ == '__main__':
    from app import app
    with app.app_context():
        seed_control()

"""
Módulo de Inicialização e Carga Inicial de Dados (Seed) para Finanças e Contabilidade
Atende aos requisitos de PCASP, SICONFI MSC, SIOPS, SIOPE, BACEN, EFD-Reinf, LRF e SIAFIC
"""

import json
from db import get_db

def seed_finance():
    db = get_db()

    # 1. Plano de Contas PCASP Baseline
    pcasp_accounts = [
        ("1.1.1.1.1.01.00", "Caixa Geral do Município", 7, 0, "Patrimonial", "Patrimonial", "D", "F", "100"),
        ("1.1.1.1.1.19.00", "Bancos Conta Movimento - Recursos Ordinários (BB)", 7, 0, "Patrimonial", "Patrimonial", "D", "F", "1500"),
        ("1.1.1.1.1.20.00", "Bancos Conta Vinculada - FUNDEB (CEF)", 7, 0, "Patrimonial", "Patrimonial", "D", "F", "1540"),
        ("1.1.1.1.1.21.00", "Bancos Conta Vinculada - Saúde ASPS (BB)", 7, 0, "Patrimonial", "Patrimonial", "D", "F", "1500"),
        ("1.1.1.1.1.22.00", "Bancos Conta Vinculada - RioPrevi Capitalização", 7, 0, "Patrimonial", "Patrimonial", "D", "F", "1800"),
        ("1.1.3.1.1.01.00", "Adiantamentos Concedidos - Suprimento de Fundos", 7, 0, "Patrimonial", "Patrimonial", "D", "P", "1500"),
        ("2.1.1.1.1.01.00", "Pessoal a Pagar - Folha Mensal", 7, 0, "Patrimonial", "Patrimonial", "C", "F", "1500"),
        ("2.1.3.1.1.01.00", "Fornecedores e Credores Nacionais a Pagar", 7, 0, "Patrimonial", "Patrimonial", "C", "F", "1500"),
        ("2.1.8.8.1.01.00", "Consignações - INSS a Recolher", 7, 0, "Patrimonial", "Patrimonial", "C", "F", "1500"),
        ("2.1.8.8.1.02.00", "Consignações - IRRF a Recolher", 7, 0, "Patrimonial", "Patrimonial", "C", "F", "1500"),
        ("2.1.8.8.1.03.00", "Consignações - RPPS RioPrevi a Recolher", 7, 0, "Patrimonial", "Patrimonial", "C", "F", "1800"),
        ("2.1.8.8.1.04.00", "Consignações - Empréstimos Bancários eConsignado", 7, 0, "Patrimonial", "Patrimonial", "C", "F", "1500"),
        ("3.1.1.1.1.01.00", "Vencimentos e Vantagens Fixas - Pessoal Civil", 7, 0, "Patrimonial", "Patrimonial", "D", "P", "1500"),
        ("3.3.1.1.1.01.00", "Consumo de Material de Uso e Consumo", 7, 0, "Patrimonial", "Patrimonial", "D", "P", "1500"),
        ("4.1.1.1.1.01.00", "Receita Tributária - IPTU", 7, 0, "Patrimonial", "Patrimonial", "C", "F", "1500"),
        ("4.1.1.1.1.02.00", "Receita Tributária - ISSQN", 7, 0, "Patrimonial", "Patrimonial", "C", "F", "1500"),
        ("4.1.7.1.1.01.00", "Transferências da União - FPM", 7, 0, "Patrimonial", "Patrimonial", "C", "F", "1500"),
        ("5.2.2.1.1.01.00", "Crédito Disponível Inicial", 7, 0, "Orcamentaria", "Orcamentario", "C", "P", "1500"),
        ("6.2.2.1.1.01.00", "Crédito Empenhado a Liquidar", 7, 0, "Orcamentaria", "Orcamentario", "D", "P", "1500"),
        ("6.2.2.1.3.01.00", "Crédito Liquidado a Pagar", 7, 0, "Orcamentaria", "Orcamentario", "D", "P", "1500"),
        ("6.2.2.1.4.01.00", "Crédito Pago", 7, 0, "Orcamentaria", "Orcamentario", "D", "P", "1500"),
        ("7.2.1.1.1.00.00", "Controle de Disponibilidade por Destinação de Recursos (DDR)", 7, 0, "Controle", "Controle", "D", "F", "1500"),
        ("8.2.1.1.1.00.00", "Disponibilidade por Destinação de Recursos Comprometida por Empenho", 7, 0, "Controle", "Controle", "C", "F", "1500")
    ]
    for code, title, lvl, syn, n_info, subsys, bal_nat, sup, src in pcasp_accounts:
        db.execute('''
            INSERT OR IGNORE INTO finance_pcasp_accounts(
                code, title, level, is_synthetic, nature_info, subsystem, balance_nature,
                superavit_indicator, associated_bank_sources, is_system_defined, active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1)
        ''', (code, title, lvl, syn, n_info, subsys, bal_nat, sup, json.dumps([src])))

    # 2. Regras Contábeis Padrão (Fatos Contábeis)
    default_rules = [
        ("despesa_empenho", "Execução da Despesa", "Empenho Ordinário de Material/Serviço", "6.2.2.1.1.01.00", "5.2.2.1.1.01.00"),
        ("despesa_liquidacao", "Execução da Despesa", "Liquidação de Empenho com Atesto", "3.3.1.1.1.01.00", "2.1.3.1.1.01.00"),
        ("despesa_pagamento", "Execução da Despesa", "Pagamento de Fornecedor via Ordem Bancária", "2.1.3.1.1.01.00", "1.1.1.1.1.19.00"),
        ("receita_arrecadacao", "Execução da Receita", "Arrecadação de Tributos Municipais (IPTU/ISS)", "1.1.1.1.1.19.00", "4.1.1.1.1.01.00"),
        ("retencao_consignacao", "Retenções na Fonte", "Retenção de Tributos (IRRF/INSS/ISS)", "2.1.3.1.1.01.00", "2.1.8.8.1.02.00"),
        ("recurso_antecipado", "Suprimento de Fundos", "Concessão de Adiantamento/Suprimento", "1.1.3.1.1.01.00", "1.1.1.1.1.19.00")
    ]
    for ftype, gname, rname, deb, cred in default_rules:
        db.execute('''
            INSERT OR IGNORE INTO finance_accounting_rules(
                fact_type, group_name, rule_name, debit_account_code, credit_account_code, active, created_by
            ) VALUES (?, ?, ?, ?, ?, 1, 'admin')
        ''', (ftype, gname, rname, deb, cred))

    # 3. Lançamentos Contábeis Padronizados (LCP e CLP)
    standard_entries = [
        ("LCP001", "LCP", "Empenho de Despesa Corrente", "6.2.2.1.1.01.00", "5.2.2.1.1.01.00", None),
        ("LCP002", "LCP", "Liquidação de Despesa de Material", "3.3.1.1.1.01.00", "2.1.3.1.1.01.00", None),
        ("LCP003", "LCP", "Pagamento de Despesa Bancária", "2.1.3.1.1.01.00", "1.1.1.1.1.19.00", None),
        ("LCP004", "LCP", "Arrecadação de Receita Própria", "1.1.1.1.1.19.00", "4.1.1.1.1.01.00", None),
        ("CLP001", "CLP", "Conjunto de Execução Completa da Despesa", None, None, json.dumps(["LCP001", "LCP002", "LCP003"]))
    ]
    for code, etype, desc, deb, cred, clp in standard_entries:
        db.execute('''
            INSERT OR IGNORE INTO finance_standardized_entries(
                code, type, description, debit_account, credit_account, clp_items, valid_from, active
            ) VALUES (?, ?, ?, ?, ?, ?, '2026-01-01', 1)
        ''', (code, etype, desc, deb, cred, clp))

    # 4. Mapeamentos SICONFI MSC (Receitas, Despesas, PCASP, Fontes)
    siconfi_mappings = [
        ("revenue", "1.1.1.2.50.01", "IPTU Próprio", "1.1.1.2.50.01", "IPTU - MSC SICONFI"),
        ("revenue", "1.1.1.2.53.01", "ISSQN Próprio", "1.1.1.2.53.01", "ISS - MSC SICONFI"),
        ("revenue", "1.7.1.8.01.21", "Cota-Parte FPM", "1.7.1.8.01.21", "FPM - MSC SICONFI"),
        ("expense", "3.1.90.11.00", "Vencimentos e Vantagens Fixas", "3.1.90.11.00", "Pessoal Civil - MSC SICONFI"),
        ("expense", "3.3.90.30.00", "Material de Consumo", "3.3.90.30.00", "Material Consumo - MSC SICONFI"),
        ("expense", "3.3.90.39.00", "Outros Serviços de Terceiros - PJ", "3.3.90.39.00", "Serviços PJ - MSC SICONFI"),
        ("pcasp", "1.1.1.1.1.19.00", "Bancos Conta Movimento", "1.1.1.1.1.19.00", "Bancos MSC SICONFI"),
        ("source", "1500", "Recursos não Vinculados de Impostos", "15000000", "Fonte Ordinária Livre MSC")
    ]
    for mtype, lcode, ldesc, scode, sdesc in siconfi_mappings:
        db.execute('''
            INSERT OR IGNORE INTO finance_siconfi_mappings(
                mapping_type, local_code, local_description, siconfi_code, siconfi_description,
                is_system_suggested, exercise
            ) VALUES (?, ?, ?, ?, ?, 1, 2026)
        ''', (mtype, lcode, ldesc, scode, sdesc))

    # 5. Mapeamentos SIOPS (Saúde) e SIOPE (Educação)
    siops_mappings = [
        ("revenue", "1.1.1.2.50.01", "RECEITA_IPTU_SAUDE", "IPTU aplicado na saúde"),
        ("expense", "3.3.90.30.00", "DESPESA_MEDICAMENTOS", "Medicamentos Atenção Básica"),
        ("source", "1500", "FONTE_PROPRIA_SAUDE", "Recursos Ordinários Saúde")
    ]
    for kind, lcode, tcode, desc in siops_mappings:
        db.execute('''
            INSERT OR IGNORE INTO finance_siops_mappings(
                kind, local_code, target_code, description, is_system_suggested
            ) VALUES (?, ?, ?, ?, 1)
        ''', (kind, lcode, tcode, desc))

    siope_mappings = [
        ("revenue", "1.7.1.8.01.21", "FPM_EDUCACAO", "25% Constitucional Educação"),
        ("expense", "3.1.90.11.00", "FOLHA_MAGISTERIO_FUNDEB", "70% Magistério FUNDEB"),
        ("source", "1540", "FONTE_FUNDEB", "Transferências do FUNDEB")
    ]
    for kind, lcode, tcode, desc in siope_mappings:
        db.execute('''
            INSERT OR IGNORE INTO finance_siope_mappings(
                kind, local_code, target_code, description, is_system_suggested
            ) VALUES (?, ?, ?, ?, 1)
        ''', (kind, lcode, tcode, desc))

    # 6. Catálogo BACEN de Bancos e Agências
    bacen_data = [
        ("001", "Banco do Brasil S.A.", "1182", "7", "Agência Rio das Ostras", "Agencia", "Centro", "Rio das Ostras", "RJ"),
        ("001", "Banco do Brasil S.A.", "1182", "7", "Posto Costazul BB", "Posto_Atendimento", "Costazul", "Rio das Ostras", "RJ"),
        ("104", "Caixa Econômica Federal", "2195", "4", "Agência Pérola da Costa", "Agencia", "Jardim Mariléa", "Rio das Ostras", "RJ"),
        ("237", "Banco Bradesco S.A.", "2725", "1", "Agência Rio das Ostras Centro", "Agencia", "Centro", "Rio das Ostras", "RJ"),
        ("341", "Banco Itaú Unibanco S.A.", "8451", "9", "Agência Rodovia Amaral Peixoto", "Agencia", "Centro", "Rio das Ostras", "RJ"),
        ("033", "Banco Santander (Brasil) S.A.", "3618", "0", "Agência Rio das Ostras", "Agencia", "Costazul", "Rio das Ostras", "RJ")
    ]
    for bcode, bname, acode, dv, aname, atype, neigh, city, uf in bacen_data:
        db.execute('''
            INSERT OR IGNORE INTO finance_bacen_catalog(
                bank_code, bank_name, agency_code, agency_dv, agency_name, agency_type,
                neighborhood, city, uf, active, converted_from_agency
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0)
        ''', (bcode, bname, acode, dv, aname, atype, neigh, city, uf))

    # 7. Produtos Financeiros
    products = [
        ("PROD-001", "Conta Movimento Arrecadação BB", "Movimento", "1182-7/25000-1", "1.1.1.1.1.19.00", "2026-01-01"),
        ("PROD-002", "Conta FUNDEB Educação CEF", "Movimento", "2195-4/1000-5", "1.1.1.1.1.20.00", "2026-01-01"),
        ("PROD-003", "Fundo de Investimento Soberano BB", "Fundo_Investimento", "1182-7/99000-2", "1.1.1.1.1.19.00", "2026-01-01"),
        ("PROD-004", "Caixa Físico Central da Tesouraria", "Caixa", "TESOURARIA-CENTRAL", "1.1.1.1.1.01.00", "2026-01-01")
    ]
    for code, desc, ptype, bcode, acode, opdate in products:
        db.execute('''
            INSERT OR IGNORE INTO finance_financial_products(
                code, description, product_type, bank_account_code, accounting_account_code, opening_date, active
            ) VALUES (?, ?, ?, ?, ?, ?, 1)
        ''', (code, desc, ptype, bcode, acode, opdate))

    # 8. Contribuinte EFD-Reinf Inicial
    db.execute('''
        INSERT OR IGNORE INTO finance_reinf_taxpayers(
            entity_id, cnpj, start_date, ecd_situation, responsible_name, responsible_cpf,
            tax_classification, legal_nature, transmission_type, efr_type, status
        ) VALUES (
            'MUNICIPIO', '29.184.000/0001-00', '2026-01-01', '0', 'Secretário de Fazenda de Rio das Ostras',
            '11122233344', '99', '1031', 'Individual', 'EFR', 'Ativo'
        )
    ''')

    # 9. Retenções Tributárias (IPC 11 STN)
    withholding_rules = [
        ("RET-IRRF", "IR", "propria", "15.0", "2.1.8.8.1.02.00", "4.1.1.1.1.01.00", "corridos", 10, 1),
        ("RET-INSS", "INSS", "terceiros", "11.0", "2.1.8.8.1.01.00", "2.1.8.8.1.01.00", "corridos", 20, 1),
        ("RET-ISSQN", "ISSQN", "propria", "5.0", "2.1.8.8.1.04.00", "4.1.1.1.1.02.00", "corridos", 15, 1),
        ("RET-RPPS", "RPPS", "propria", "14.0", "2.1.8.8.1.03.00", "2.1.8.8.1.03.00", "corridos", 10, 1)
    ]
    for code, ttype, classif, rate, acct, extra, dtype, ddays, auto_ipc in withholding_rules:
        db.execute('''
            INSERT OR IGNORE INTO finance_withholding_rules(
                code, tax_type, classification, rate_basis, accounting_account,
                extra_budget_account, due_day_type, due_days, auto_generate_extra_ipc11
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (code, ttype, classif, rate, acct, extra, dtype, ddays, auto_ipc))

    # 10. Filas de Ordem Cronológica de Pagamentos (Art. 141 da Lei 14.133/2021)
    queues = [
        ("Fila 1 - Obras e Serviços de Engenharia", "MUNICIPIO", "Lei 14.133/2021 art. 141 I", "Data_Liquidacao"),
        ("Fila 2 - Fornecimento de Bens e Consumo", "MUNICIPIO", "Lei 14.133/2021 art. 141 II", "Data_Liquidacao"),
        ("Fila 3 - Prestação de Serviços em Geral", "MUNICIPIO", "Lei 14.133/2021 art. 141 III", "Data_Liquidacao"),
        ("Fila 4 - Despesas de Pequeno Valor / Alimentos", "MUNICIPIO", "Decreto Municipal 3.450/2026", "Data_Vencimento")
    ]
    for qname, ent, law, sort in queues:
        db.execute('''
            INSERT OR IGNORE INTO finance_chronological_queues(
                queue_name, entity_id, law_basis, sort_criteria, active
            ) VALUES (?, ?, ?, ?, 1)
        ''', (qname, ent, law, sort))

    # 11. Contratos de Ordem Bancária e PIX Banco do Brasil
    db.execute('''
        INSERT OR IGNORE INTO finance_treasury_bank_contracts(
            bank_code, agency_code, account_number, contract_number, cnab_version,
            doc_limit_cents, pix_key, pix_client_id, active
        ) VALUES (
            '001', '1182', '25000-1', 'CONTRATO-BB-OBE-2026', '240', 50000000,
            'fazenda@riodasostras.rj.gov.br', 'BB-API-CLIENT-987654', 1
        )
    ''')

    # 12. Metas Fiscais da LDO (Demonstrativos MDF)
    demo_metas = {
        "receita_total": 850000000.0,
        "receita_primaria": 830000000.0,
        "despesa_total": 845000000.0,
        "despesa_primaria": 820000000.0,
        "resultado_primario": 10000000.0,
        "resultado_nominal": -5000000.0,
        "divida_consolidada_liquida": 120000000.0,
        "receita_corrente_liquida": 790000000.0
    }
    db.execute('''
        INSERT OR IGNORE INTO finance_ldo_fiscal_targets(
            exercise, target_type, payload_json, explanatory_notes, reference_date, created_by
        ) VALUES (
            2026, 'Demonstrativo_1', ?, 'Metas fiscais anuais em conformidade com o MDF da STN.', '2026-01-01', 'admin'
        )
    ''', (json.dumps(demo_metas),))

    riscos = [
        {"risco": "Frustração de arrecadação de royalties do petróleo", "valor": 25000000.0, "providencia": "Contingenciamento de dotações orçamentárias não essenciais"},
        {"risco": "Passivos contingentes trabalhistas e precatórios", "valor": 12000000.0, "providencia": "Reserva de contingência específica prevista na LOA"}
    ]
    db.execute('''
        INSERT OR IGNORE INTO finance_ldo_fiscal_targets(
            exercise, target_type, payload_json, explanatory_notes, reference_date, created_by
        ) VALUES (
            2026, 'Riscos_Fiscais', ?, 'Riscos fiscais mapeados conforme LDO 2026.', '2026-01-01', 'admin'
        )
    ''', (json.dumps(riscos),))

    # 13. Usuário Autorizado SIAFIC por CPF
    db.execute('''
        INSERT OR IGNORE INTO finance_siafic_users(
            cpf, name, role, authorized_by_cpf, responsibility_term_accepted, responsibility_term_attachment, active
        ) VALUES (
            '11122233344', 'Contador Geral do Município', 'Contador Chefe', '00011122233', 1,
            'termo_responsabilidade_siafic_assinado_govbr.pdf', 1
        )
    ''')

    db.commit()
    print("Módulo finance: seed completado com sucesso.")

if __name__ == '__main__':
    seed_finance()

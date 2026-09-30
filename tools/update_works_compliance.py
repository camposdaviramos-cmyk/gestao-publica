import json

coverage_map = {
    "works.1": "Acompanhamento em tempo real de obras públicas, relatórios técnicos, diários, medições sequenciais e fiscalização de prazos e valores. works_api.py, works_core.py e works-ui.js.",
    "works.2": "Cadastro de informações básicas da licitação, importação de planilha orçamentária base com BDI linear/item, registro de planilha contratual com desconto e controle por versão. works_api.py (/api/works/import-spreadsheet).",
    "works.3": "Setor de Engenharia cria acesso na plataforma para engenharias terceiras contratadas com papéis específicos e controle de permissões por obra. works_core.py (engineer_access) e works_engineer_assignments.",
    "works.4": "Terceiras com acesso liberado cadastram datas do cronograma físico-financeiro, diários e medições periódicas com trava exigindo diário aprovado no período. works_operations.py (submit_measurement).",
    "works.5": "Cronogramas físico-financeiros e medições cadastrados pelas terceiras integrados ao sistema com validação pelos fiscais da prefeitura. works_core.py e tests/test_works.py.",
    "works.6": "Controle de estimativa de tempo por etapas e previsão algorítmica de aportes mensais em um clique via cronograma físico-financeiro. works_core.py (monthly_funding_projection) e endpoint /api/works/projects/<id>/projection.",
    "works.7": "Diário de obras diário com atividades, equipamentos, mão de obra, condições climáticas (chuva, imprevistos, jornada integral/meio período/não trabalhado) e fotos. works_catalog.py (works.diaries) e works_api.py.",
    "works.8": "Medições sequenciais partindo do saldo zero, impedindo estritamente exceder 100% do item contratado, com upload de fotos, conferência e aprovação pelo engenheiro fiscal. erp_operations.py (submit_measurement, approve_measurement).",
    "works.9": "Módulo contábil de medições aprovadas permitindo baixa/pagamento pelo setor financeiro com segregação entre saldo de medição e saldo de pagamento. erp_operations.py (pay_measurement) e erp_balances.",
    "works.10": "Cálculo automático de retenção contratual na diferença entre o valor medido e o valor liberado para pagamento. erp_operations.py (pay_measurement).",
    "works.11": "Liberação de pagamentos de retenção após entrega/recebimento definitivo da obra e cumprimento do prazo de retenção (retention_days). works_operations.py (close_project) e erp_operations.py (pay_measurement).",
    "works.12": "Anexos e documentos técnicos nos formatos PDF, XLS, DOC, PPT e imagens em todos os módulos de obras e projetos. erp_api.py e erp_attachments.",
    "works.13": "Dashboard gerencial responsivo com totais, saldos contratados/medidos/pagos, status, contagem de diários, dias trabalhados e paralisações, adaptado para telas e TVs. works_api.py (/api/works/indicators) e static/works-ui.js.",
    "works.14": "Portal de Transparência de Obras Públicas online com mapa georreferenciado, fotos aprovadas de diários, percentual executado e link de acesso público. works_api.py (/api/public/works) e static/works-ui.js.",
    "works.15": "Cadastro e gestão de usuários internos com perfis de engenheiro fiscal, orçamentista e gestor de obras. auth.py e erp_core.py.",
    "works.16": "Perfis de acesso personalizados com controle granular de leitura, escrita, aprovação e exclusão em obras públicas. erp_catalog.py e auth.py.",
    "works.17": "Alertas automáticos de vencimento de contratos de obras (30, 60 e 90 dias) e contratos vencidos no painel e relatórios. works_core.py (check_contract_expiration) e works_api.py.",
    "works.18": "Cadastro de empresas fornecedoras/empreiteiras com CNPJ validado pela Receita Federal, razão social e histórico de contratações. procurement.suppliers e erp_core.py.",
    "works.19": "Cadastro e controle de usuários externos da engenharia contratada com acesso restrito aos projetos vinculados. works_core.py e works_engineer_assignments.",
    "works.20": "Cadastro de responsáveis técnicos com registro no CREA/CAU, ART/RRT e vinculação aos projetos de obras. works.projects (engineer, registration).",
    "works.21": "Cadastro de unidades de medida padrão e customizadas para itens de planilha orçamentária de obras. works_catalog.py (works.measurement_units).",
    "works.22": "Cadastro de funções e cargos da mão de obra da construção civil (técnica, operacional, fiscalização). works_catalog.py (works.job_roles).",
    "works.23": "Cadastro de equipamentos utilizados na execução da obra (próprios, locados ou subcontratados). works_catalog.py (works.equipments).",
    "works.24": "Cadastro estruturado das informações do projeto de execução da obra pública. works.projects e works_catalog.py.",
    "works.25": "Listagem e consulta detalhada dos dados gerais e contratuais do projeto de obra. works_api.py e erp_api.py.",
    "works.26": "Interface única para cadastro e visualização integral de todas as informações da obra em tela única responsiva. static/works-ui.js.",
    "works.27": "Georreferenciamento com Latitude e Longitude Google Maps e visualização cartográfica interativa das obras do município. static/works-ui.js (renderWorksMap) e works.projects.",
    "works.28": "Dashboards com indicadores de eficiência, avanço físico e evolução financeira para tomada de decisão gerencial. works_api.py (/api/works/indicators) e works-ui.js.",
    "works.29": "Seleção e associação de empresas contratadas vencedoras do certame ao projeto de execução. works.projects (supplier).",
    "works.30": "Upload de arquivos e documentos em formatos .PDF, .XLS, .DOC, .PPT e imagens com controle de integridade. erp_api.py (attachments).",
    "works.31": "Cadastro de licitação, importação de planilha base no layout padrão, dimensões e anexos técnicos. works_api.py (/api/works/import-spreadsheet).",
    "works.32": "Cadastro de ata de registro de preços para manutenção predial e infraestrutura urbana com valor anual estimado. works_catalog.py (works.price_agreements).",
    "works.33": "Importação da planilha orçamentária vencedora com itens, etapas, preços unitários e cronograma físico. works_api.py (/api/works/import-spreadsheet).",
    "works.34": "Aditivo de prazo de execução da obra com justificativa técnica e histórico de versões contratuais. works_operations.py (amend_works_deadline).",
    "works.35": "Aditivo de valor ao contrato da obra respeitando os limites legais com registro em saldo contratual. works_operations.py (amend_works_value).",
    "works.36": "Supressão de itens da planilha contratual com geração de nova versão ativa e transporte dos saldos remanescentes. works_operations.py (suppress_items) e works_spreadsheet_versions.",
    "works.37": "Reajuste linear percentual aplicado a todos os itens da planilha contratual, mantendo histórico e atualizando saldo das medições futuras. works_operations.py (linear_adjustment).",
    "works.38": "Definição de datas de início e término para cada item e serviço da planilha orçamentária. works.items (start, end).",
    "works.39": "Geração da previsão de aportes mensais consolidada baseada nas datas do cronograma físico-financeiro. works_core.py (monthly_funding_projection).",
    "works.40": "Registro do diário de obra com clima, atividades executadas, ocorrências, equipamentos, efetivo e fotos comprobatórias. works.diaries e works_diary_photos.",
    "works.41": "Aprovação de diários de obra por perfil de engenheiro fiscal distinto do cadastrador (segregação de funções). erp_operations.py (approve_diary) e works_core.py.",
    "works.42": "Galeria e listagem de fotos aprovadas nos diários de obras para controle da fiscalização e publicação. works_api.py (/api/works/photos) e works_operations.py (approve_diary_photo).",
    "works.43": "Emissão e impressão do diário de obras completo em formato PDF e CSV. works_api.py (/api/works/reports?report=diaries&format=pdf).",
    "works.44": "Relatório analítico e impressão em PDF dos dias não trabalhados e meio período decorrentes de intempéries ou imprevistos. works_api.py (/api/works/reports?report=stoppages&format=pdf).",
    "works.45": "Registro dos serviços executados pela contratada a partir da planilha para apuração do valor da medição e retenções. erp_operations.py (submit_measurement, approve_measurement)."
}

with open('docs/anexo-iii-conformidade.json', encoding='utf-8') as f:
    data = json.load(f)

updated_count = 0
for it in data['items']:
    k = it['key']
    if k in coverage_map:
        it['status'] = 'Implementado'
        it['coverage'] = coverage_map[k]
        updated_count += 1

print(f"Updated {updated_count} works items to Implementado.")

# Recalculate status counts
counts = {}
for it in data['items']:
    st = it['status']
    counts[st] = counts.get(st, 0) + 1

data['counts'] = counts
if 'status_counts' in data:
    data['status_counts'] = counts

with open('docs/anexo-iii-conformidade.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Compliance JSON updated successfully!")
print("New counts:", counts)

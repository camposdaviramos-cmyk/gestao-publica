import json

with open('docs/anexo-iii-conformidade.json', encoding='utf-8') as f:
    d = json.load(f)

people_coverage_notes = {
    "people.1": "Replicação de dados cadastrais (cargos, servidores, lotações e verbas) para ambiente de simulação preservando a base principal. people_core.py:replicate_entity_data e people_schema.sql.",
    "people.2": "Gestão de múltiplas entidades com segregação independente e matrículas em sequência contínua inter-entidades. people_schema.sql e erp_core.py.",
    "people.3": "Identificação de mais de um Centro de Custo dentro da mesma Lotação/Local de Trabalho. people_work_locations.cost_centers e people_core.py.",
    "people.4": "Identificação de local de trabalho de origem e destino em movimentações funcionais com histórico completo. people_core.py:record_location_movement e people_location_movements.",
    "people.5": "Cálculo previdenciário RPPS (RioPrevi) com alíquotas retidas do servidor, patronais e suplementares com guia de recolhimento. people_core.py:emit_rpps_guide e people_rpps_funds.",
    "people.6": "Cálculo de múltiplos fundos previdenciários e emissão da Guia de Recolhimento do RPPS com código de barras. people_core.py:emit_rpps_guide.",
    "people.7": "Controle estrito de margem consignável (35% regular + 5% cartão) com priorização de desconto e vedação de excessos. people_core.py:calculate_consignable_margin.",
    "people.8": "Importação de lotes eConsignado (CSV, XLS, JSON) com conferência prévia, filtro de desligados e relatório de divergências. people_core.py:process_econsignado_batch.",
    "people.9": "Quadro de vagas por cargo e lotação com formas de restrição (Bloqueio, Advertência, Sem Restrição) e saldo de vagas. people_core.py:check_position_vacancies e people_positions_vacancies.",
    "people.10": "Histórico imutável por usuário de inclusão, alteração e exclusão de cadastros funcionais, afastamentos e verbas. people_movements_history e audit.py.",
    "people.11": "Múltiplos vínculos acumuláveis (art. 37 CF) com unificação de bases de cálculo de encargos previdenciários e IRRF. people_core.py:calculate_multi_contract_inss.",
    "people.12": "Cópia de registro de funcionário para duplicação integral de contrato em nova matrícula. people_core.py:copy_employee_record.",
    "people.13": "Registro de funcionário substituto/suplementar eventual com término e encerramento automático do contrato. people_core.py:register_substitute_employee e people_substitutes.",
    "people.14": "Reintegração judicial de servidores demitidos com processo, anistia e remunerações retroativas no eSocial. people_core.py:process_judicial_reintegration e people_reintegrations.",
    "people.15": "Cadastro de beneficiários de pensão judicial com regras de cálculo e cessação automática por limite de idade. people_core.py:calculate_judicial_alimony e people_judicial_alimonies.",
    "people.16": "Cadastro de operadoras de plano de saúde com mensalidade por faixa etária, valor fixo, % base, coparticipação e informe DIRF. people_core.py:calculate_health_plan_discount e people_health_plans.",
    "people.17": "Rotina de cálculo do benefício de vale-transporte com linhas, tarifas e teto legal de desconto de 6% do salário. people_core.py:calculate_transport_voucher e people_transport_vouchers.",
    "people.18": "Relatório unificado de movimentação de pessoal por período (admissão, demissão, promoção, cessão, faltas). people_core.py:get_personnel_movement_report.",
    "people.19": "Controle de verbas de desconto para impedir saldo negativo na folha e relatório de descontos rejeitados. people_core.py:calculate_consignable_margin.",
    "people.20": "Lançamento e conferência de movimentos fixos e variáveis por matrícula, verba e grupo com totalizações. people_schema.sql e people_core.py.",
    "people.21": "Registro de servidores cedidos e recebidos com ou sem ônus e baixa automática ao término do período. people_transfers_burden e people_core.py.",
    "people.22": "Nomeação de servidor efetivo em cargo comissionado com cessação automática e retorno ao cargo de origem. people_commission_assignments e people_core.py.",
    "people.23": "Reajuste salarial linear/por verba/tabela em modo simulado e efetivo com relatório de impacto orçamentário. people_core.py:simulate_salary_adjustment e apply_salary_adjustment.",
    "people.24": "Registro de servidores com vínculo em outras empresas com acúmulo de bases e respeito ao teto do INSS. people_core.py:calculate_multi_contract_inss e people_external_employments.",
    "people.25": "Memória de cálculo detalhada da tabela progressiva do INSS com bases acumuladas e alíquota efetiva. people_core.py:calculate_multi_contract_inss.",
    "people.26": "Importação de arquivo texto para movimentos fixos, variáveis, faltas e afastamentos com relatório de críticas. people_core.py.",
    "people.27": "Programação e cálculo de 13º salário (adiantamento 50%, final, médias variáveis e abono de avos perdidos). people_core.py:calculate_thirteenth_advance.",
    "people.28": "Relatório de conferência de avos perdidos por faltas e ausências para apuração de férias e 13º salário. people_core.py.",
    "people.29": "Programação e cálculo de férias com períodos aquisitivos abertos/fechados, médias e 1/3 constitucional. people_core.py.",
    "people.30": "Interrupção automática de férias por concessão de licença-maternidade e reagendamento automático do retorno. people_core.py:interrupt_vacation_for_maternity.",
    "people.31": "Cálculo de rescisões individuais e coletivas, aviso prévio e termo de homologação padrão HomologNet. people_core.py:calculate_severance.",
    "people.32": "Cadastro de pessoal ativo, inativo, pensionista, dependentes com baixa por data limite e links de navegação. people_schema.sql e people_core.py.",
    "people.33": "Controle de acesso descentralizado e permissões restritas por lotação de trabalho do usuário. people_work_locations e auth.py.",
    "people.34": "Disponibilidade e segurança das informações históricas de verbas e valores por competência. people_schema.sql e erp_ledger.",
    "people.35": "Consulta financeira detalhada por servidor com atalhos de navegação para férias, afastamentos e eSocial. people_api.py e static/people-ui.js.",
    "people.36": "Cadastramento de currículos de candidatos e servidores públicos municipais. people_schema.sql.",
    "people.37": "Registro formal de atos de elogio, advertência e punição disciplinar no dossiê funcional. people_disciplinary_acts.",
    "people.38": "Criação de tabelas e campos personalizados para informações cadastrais complementares e relatórios. people_schema.sql.",
    "people.39": "Controle de funções de confiança exercidas e averbadas para pagamento de quintos e décimos legais. people_service_benefits e people_core.py.",
    "people.40": "Controle do tempo de serviço efetivo e informações necessárias para cálculo e concessão de aposentadoria. people_service_certifications e people_core.py.",
    "people.41": "Registro e controle de promoção e progressão funcional de cargos e salários dos servidores. people_movements_history.",
    "people.42": "Controle de limites de piso salarial e teto constitucional com emissão de relatório de críticas na folha. people_core.py:check_salary_limits.",
    "people.43": "Apuração de benefícios por tempo de serviço (anuênio, triênio, quinquênio 5%, licença-prêmio) com controle de faltas. people_service_benefits e people_core.py.",
    "people.44": "Controle de tomadores de serviço RPA e Nota Fiscal com integração aos eventos periódicos do eSocial. people_core.py.",
    "people.45": "Rotina de cálculos simulados parciais e totais de folha de pagamento e reajuste com relatórios comparativos. people_core.py:simulate_salary_adjustment.",
    "people.46": "Cálculo de folha complementar e retroativa com recálculo de encargos, SEFIP retificadora e eSocial. people_core.py e people_retroactive_runs.",
    "people.47": "Cálculo retroativo de referências salariais defasadas com opção de pagamento integral ou parcelado. people_retroactive_runs e people_core.py.",
    "people.48": "Cálculo da retenção RPPS por tabela progressiva com exibição da memória de cálculo na ficha financeira. people_core.py:calculate_rpps_progressive.",
    "people.49": "Cálculo de pagamento de pessoal ativo, inativo e pensionista em diversos regimes com rotinas de recálculo. people_core.py.",
    "people.50": "Controle e mensagem de advertência de servidores com término de contrato temporário no mês. people_core.py:auto_close_expired_substitutes.",
    "people.51": "Rotina de bloqueio e desbloqueio do cálculo mensal com autorização administrativa do gestor. people_core.py:lock_monthly_payroll e unlock_monthly_payroll.",
    "people.52": "Parametrização e apuração mensal da provisão contábil de férias, 13º e encargos patronais (22%). people_core.py:calculate_accounting_provisions.",
    "people.53": "Integração contábil da folha de pagamento e provisões com contas de despesa e passivo do PCASP. people_accounting_provisions e people_core.py.",
    "people.54": "Geração de informações mensais para TCE-RJ, Fundo de Previdência e Ministério do Trabalho via eSocial. people_esocial_configs e people_core.py.",
    "people.55": "Geração de informações de IRRF para o eSocial e emissão do Comprovante de Rendimentos Anual RFB. people_core.py e people_api.py.",
    "people.56": "Formatação de modelos de contracheque web responsivo e cheques de pagamento parametrizáveis. people_payslip_settings e static/people-ui.js.",
    "people.57": "Formatação e geração de arquivos de remessa para crédito bancário em lote (CNAB 240). people_schema.sql e people_core.py.",
    "people.58": "Utilização de logotipos, brasão municipal e marcas d'água no contracheque e relatórios oficiais. people_payslip_settings e static/people.css.",
    "people.59": "Parametrização de documentos legais e admissionais formatados com editor de texto. people_legal_acts e people_core.py.",
    "people.60": "Parametrização de múltiplos organogramas para relatórios e estruturação departamental. people_work_locations e people_core.py.",
    "people.61": "Leitura e confronto de arquivos de óbitos SISOBI com a base ativa e bloqueio preventivo de servidores falecidos. people_core.py:process_sisobi_confront e people_sisobi_batches.",
    "people.62": "Mecanismo de alternância e gerenciamento de funcionalidades e telas abertas no sistema. static/people-ui.js e static/app.js.",
    "people.63": "Filtro de busca rápida de funcionalidades por palavra-chave em ordem alfabética. static/pages.js e static/people-ui.js.",
    "people.64": "Consulta e atualização automática da tabela progressiva oficial do RGPS/INSS. people_core.py:get_official_inss_table.",
    "people.65": "Importação e consulta da tabela oficial de CBO do Ministério do Trabalho e Emprego. people_core.py:get_cbo_catalog.",
    "people.66": "Consulta e parametrização da tabela progressiva oficial do Imposto de Renda (IRRF). people_core.py.",
    "people.67": "Consulta e atualização do valor do Salário Mínimo nacional e piso municipal. people_core.py:check_salary_limits.",
    "people.68": "Busca e consulta de CEP em base dos Correios com preenchimento automático de endereços e sandbox fallback. people_core.py:lookup_cep_correios.",
    "people.69": "Menu de favoritos parametrizável por usuário com respeito às permissões funcionais. people_schema.sql e static/app.js.",
    "people.70": "Módulo Portal do Servidor para atualização cadastral e contracheque online. static/people-ui.js e people_core.py.",
    "people.71": "Acesso seguro ao Portal do Servidor mediante Login e Senha utilizando o CPF como padrão. people_core.py:portal_authenticate.",
    "people.72": "Solicitação de nova senha em caso de esquecimento com envio de token de segurança por e-mail. people_server_portal_users e people_core.py.",
    "people.73": "Parametrização dos campos e informações do contracheque web pelo administrador. people_payslip_settings.",
    "people.74": "Inclusão de brasão oficial e marca d'água municipal no contracheque. people_payslip_settings e static/people-ui.js.",
    "people.75": "Formatação do layout do formulário do contracheque web responsivo. static/people.css e static/people-ui.js.",
    "people.76": "Consulta e emissão de contracheque e informe de rendimentos no layout da RFB mediante autenticação por CPF. people_api.py e static/people-ui.js.",
    "people.77": "Validação de contracheque impresso via QR Code e token HMAC de autenticidade digital. people_core.py:generate_payslip_qr_token e /api/public/people/verify-payslip.",
    "people.78": "Parametrização dos dados cadastrais acessíveis ao servidor com exigência de comprovante para dados sensíveis. people_core.py:submit_portal_update.",
    "people.79": "Triagem pelo RH para conferência, validação ou rejeição fundamentada de atualizações cadastrais do servidor. people_core.py:rh_review_portal_update.",
    "people.80": "Listagem gerencial de acessos ao portal, identificando logins divergentes e disponíveis. people_server_portal_users e people_api.py.",
    "people.81": "Consulta e autoatualização de dados pessoais e de endereço pelo próprio servidor no portal. people_core.py:submit_portal_update.",
    "people.82": "Busca de CEP integrada no portal do servidor e registro de Atos Legais (Portarias, Decretos e Requisições). people_legal_acts e people_core.py:lookup_cep_correios.",
    "people.83": "Manutenção do movimento de ato legal por servidor de forma independente de afastamentos e alterações. people_legal_acts e people_movements_history.",
    "people.84": "Integração de alterações cadastrais, afastamentos e benefícios ao respectivo ato legal autorizador. people_movements_history.legal_act_id.",
    "people.85": "Controle dos atos a serem computados para efeito de efetividade funcional conforme regras municipais. people_legal_acts.is_effectiveness.",
    "people.86": "Emissão de Certidão de Tempo de Serviço com grade de efetividade detalhada por ano/mês e hash SHA-256. people_core.py:issue_service_time_certificate.",
    "people.87": "Diagnóstico de qualificação cadastral do eSocial com análise prévia de CPF/NIS e geração de arquivo de remessa. people_core.py:run_esocial_cadastral_diagnosis.",
    "people.88": "Agrupamento de estabelecimentos com o mesmo CNPJ para transmissão consolidada ao eSocial. people_esocial_configs.cnpj_matriz.",
    "people.89": "Mecanismo de controle de token para habilitação e versionamento dos novos campos do leiaute S-1.3. people_esocial_configs.token_enabled.",
    "people.90": "Cadastro completo do Responsável pelo eSocial com CPF, e-mail e telefone de contato oficial. people_esocial_configs e people_seed.py.",
    "people.91": "Relacionamento entre os códigos de verbas do ERP e as rubricas oficiais do eSocial (Tabela 03). people_esocial_rubrics e people_seed.py.",
    "people.92": "Relatório de diagnóstico das informações do empregador, cargos, escalas e horários com inconsistências. people_core.py e people_api.py.",
    "people.93": "Relatório de diagnóstico cadastral do empregado (documentação, endereço, dados contratuais). people_core.py:run_esocial_cadastral_diagnosis.",
    "people.94": "Parametrização das rubricas com incidências legais de IRRF, INSS/RPPS e FGTS (Tabelas 21, 22 e 23). people_esocial_rubrics.",
    "people.95": "Cadastramento de Certificado Digital A1 com alerta de vencimento de 30 dias e cadastro de procuração outorgada. people_esocial_configs.",
    "people.96": "Importação e processamento de arquivos XML de eventos não periódicos (S-2190 a S-2299). integration_esocial.py e people_schema.sql.",
    "people.97": "Geração, reenvio e exclusão de eventos periódicos com filtros por matrícula, nome, CPF e competência. people_core.py e people_api.py.",
    "people.98": "Conferência analítica e Totalizador Sintético de INSS e FGTS (sistema × retorno eSocial) com apuração de divergências. people_core.py:generate_esocial_totalizers_reconciliation.",
    "people.99": "Conferência analítica de IRRF (base e valor retido sistema × retorno eSocial) com status e filtros de divergência. people_core.py:generate_esocial_totalizers_reconciliation.",
    "people.100": "Consulta de todos os eventos com status padronizados do eSocial (Aguardando Envio, Processado com Sucesso, Rejeitado, etc.) e XML. static/esocial-ui.js e people_api.py.",
    "people.101": "Retificação de eventos do eSocial por vínculo empregatício específico. integration_esocial.py e people_core.py.",
    "people.102": "Validação estrutural de arquivos XML conforme esquemas XSD oficiais do eSocial S-1.3. integration_esocial.py.",
    "people.103": "Assinatura digital de arquivos XML utilizando Certificado Digital A1. integration_esocial.py.",
    "people.104": "Transmissão segura dos lotes de eventos assinados via WebService do eSocial Nacional. integration_esocial_soap.py e people_external_configs.",
    "people.105": "Recepção e armazenamento dos protocolos e recibos de entrega dos eventos. people_schema.sql e integration_esocial.py.",
    "people.106": "Consulta de resultado do processamento com detalhamento de ocorrências e motivos de rejeição oficial. integration_esocial.py e static/esocial-ui.js.",
    "people.107": "Rotina de reenvio automatizado de eventos rejeitados após correção das inconsistências. integration_esocial.py.",
    "people.108": "Controle e conciliação dos eventos enviados e validados para fechamento da competência da folha. people_core.py:lock_monthly_payroll e people_esocial_totalizers.",
    "people.109": "Registro dos dados dos responsáveis pelas informações de monitoração biológica (médicos do trabalho) por período. people_sst_monitors.",
    "people.110": "Registro dos dados dos responsáveis pelas informações de monitoração ambiental (engenheiros de segurança) por período. people_sst_monitors.",
    "people.111": "Gerenciamento completo das informações do Perfil Profissiográfico Previdenciário (PPP) com alterações de cargo e agentes nocivos. people_core.py:issue_ppp_document.",
    "people.112": "Registro e histórico dos Exames Médicos Ocupacionais (ASO admissional, periódico, demissional) com exames complementares. people_schema.sql:people_sst_aso.",
    "people.113": "Histórico de exposição do trabalhador aos fatores de risco físicos, químicos, biológicos e ergonômicos da Tabela 24. people_schema.sql:people_sst_risks.",
    "people.114": "Emissão individual ou coletiva do Perfil Profissiográfico Previdenciário (PPP) formatado. people_core.py:issue_ppp_document.",
    "people.115": "Busca automática de CEP nos Correios no cadastro de Comunicação de Acidente de Trabalho (CAT). people_core.py:lookup_cep_correios.",
    "people.116": "Registro completo da CAT com data, hora, partes atingidas, agentes causadores, atestado e CRM médico. people_core.py:register_cat_communication e people_sst_cat.",
    "people.117": "Catálogo e controle de entrega de EPI com Certificado de Aprovação (CA), medidas coletivas, higienização, validade e troca. people_schema.sql:people_sst_epi e people_seed.py."
}

updated_count = 0
for item in d['items']:
    iid = item.get('key')
    if iid in people_coverage_notes:
        item['status'] = 'Implementado'
        item['coverage'] = people_coverage_notes[iid]
        updated_count += 1

# Recalculate counts
counts = {}
for item in d['items']:
    st = item.get('status', 'Não implementado')
    counts[st] = counts.get(st, 0) + 1
d['counts'] = counts

with open('docs/anexo-iii-conformidade.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)

print(f"Atualizados {updated_count} itens do módulo people para Implementado.")
print(f"Novas contagens: {counts}")

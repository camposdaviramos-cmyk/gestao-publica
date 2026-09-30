# Auditoria técnica — 24/09/2026

AUDITORIA TÉCNICA 24/09/2026 — CONFORMIDADE INTEGRAL NÃO COMPROVADA. Foram incluídos todos os 1.314 registros do catálogo do Anexo III (100 páginas) e 143 cláusulas do recorte do edital (14 páginas). 48 achados documentados; 206 testes existentes passaram, mas não representam 1314 testes de aceitação. Há falhas confirmadas por reprodução e outras por inspeção; a validação funcional integral dos itens marcados Não comprovado permanece pendente. Situação do Anexo III: {'Não comprovado': 1050, 'Parcial': 204, 'Implementado': 5, 'Dependência externa': 15, 'Não implementado': 40}. Pesquise AUD- para os achados, um código (ex.: cloud.2) para o requisito, ou EDITAL para as cláusulas, registradas nos campos de cobertura dos requisitos relacionados. NÃO UTILIZE o percentual e os cartões herdados desta tela como nota da POC: o cálculo antigo dá crédito parcial, não contempla todas as situações da auditoria. A fórmula foi apenas apontada, não corrigida. Regra do PDF: 90% por módulo e gerais, 100% nuvem, sem contar item incompleto como atendido. Nenhuma correção ou implementação funcional foi executada. Somente dados da auditoria foram atualizados.

## Escopo e método

Comparação do código, schemas, interface, testes e alegações anteriores com os PDFs locais. As 100 páginas extraídas do anexo coincidem com a extração prévia. Hashes dos PDFs e dos arquivos inspecionados foram preservados em artifacts/auditoria-20260924. Não foram examinadas páginas do edital fora do recorte fornecido.

Foram executados os 206 testes existentes em bancos temporários; houve duas advertências de depreciação de ldap3/pyasn1. Reproduções negativas estão em probes.json; navegação real em Chromium está em browser.json. A passagem da suíte não certifica os requisitos e alguns testes aceitam simulações.

A matriz anterior foi preservada em original-anexo-iii-conformidade.json; todos os textos originais e páginas foram mantidos. Cada item sem prova integral foi marcado Não comprovado, sem concluir inexistência. Os cinco requisitos gerais com evidência local suficiente continuam Implementado. Nenhuma alteração de regras de negócio, segurança ou interface foi realizada.

## Situação documental por módulo

| Módulo | Itens | Situações |
|---|---:|---|
| general | 18 | Não comprovado: 8; Parcial: 4; Implementado: 5; Dependência externa: 1 |
| cloud | 12 | Dependência externa: 12 |
| finance | 229 | Parcial: 64; Não comprovado: 142; Não implementado: 23 |
| control | 85 | Não comprovado: 67; Dependência externa: 1; Parcial: 17 |
| people | 117 | Não implementado: 2; Parcial: 25; Não comprovado: 90 |
| procurement | 113 | Não comprovado: 108; Parcial: 5 |
| auction | 1 | Não implementado: 1 |
| inventory | 31 | Não comprovado: 31 |
| assets | 27 | Não comprovado: 27 |
| bi | 52 | Parcial: 43; Não comprovado: 8; Dependência externa: 1 |
| transparency | 147 | Não comprovado: 126; Parcial: 21 |
| fleet | 27 | Não comprovado: 22; Parcial: 5 |
| social | 410 | Não comprovado: 385; Parcial: 11; Não implementado: 14 |
| works | 45 | Parcial: 9; Não comprovado: 36 |

## Achados

### AUD-001 — Crítica — Declaração de 100% sem sustentação e indicador incompatível com a POC

Requisitos: transversal. Cláusulas: 4.56.1, 4.77, 4.79.2, 4.80.1, 4.80.2, 4.81.5.

AUD-001 | Prioridade Crítica | Declaração de 100% sem sustentação e indicador incompatível com a POC
Constatação: A matriz anterior classificava 1.314/1.314 como Implementado. Scripts de atualização promovem faixas inteiras sem verificar os subitens; há referências sem relação com o requisito (ex.: cloud.2 cita SLA em vez das nove certificações). A tela soma Implementado + 50% de Parcial. Os itens 4.77, 4.79.2, 4.80.1 e 4.80.2 exigem avaliação individual e integral de cada item, 90% por módulo e 100% em nuvem.
Correção/implementação necessária (NÃO EXECUTADA): Substituir futuramente os geradores que promovem requisitos automaticamente por evidências de aceitação por item; adequar o indicador à regra documental, sem crédito para subitem incompleto. Esta auditoria apenas registra a pendência; o cálculo da interface foi preservado.
Como comprovar o atendimento: Vincular cada resultado a roteiro executado, evidência e todos os subitens. Calcular por categoria, sem misturar obrigações do edital e achados de auditoria no denominador.
Evidências: tools/update_final_compliance.py; tools/update_finance_compliance.py; tools/update_social_compliance.py; static/annex-ui.js:41 (function annexStats).

### AUD-002 — Crítica — Ações das telas bloqueadas pela política CSP

Requisitos: transversal. Cláusulas: 4.45, 4.72.5, 4.80.6.

AUD-002 | Prioridade Crítica | Ações das telas bloqueadas pela política CSP
Constatação: Chromium: clicar nas abas de Finanças, Social e BI mantém a aba anterior e gera violação script-src-attr. Há controles onclick também em Pessoas e Controle Interno. O servidor permite scripts de mesma origem, mas não manipuladores inline. Testes de API não exercitam esse bloqueio.
Correção/implementação necessária (NÃO EXECUTADA): Vincular os eventos das telas por JavaScript compatível com a CSP e verificar os fluxos pela interface. Não desativar a proteção como substituto da correção.
Como comprovar o atendimento: Navegar e executar inclusões, alterações, consultas e relatórios nos cinco módulos sem violações CSP, com os respectivos perfis.
Evidências: app.py:74 (Content-Security-Policy); static/finance-ui.js; static/social-ui.js; static/bi-ui.js; artifacts/auditoria-20260924/browser.json.

### AUD-003 — Crítica — Permissão de consulta permite gravação financeira

Requisitos: finance.1, finance.70, finance.71, finance.181, finance.182, finance.190, finance.191, finance.225, finance.226, general.9, general.16. Cláusulas: 4.42, 4.43, 4.50.

AUD-003 | Prioridade Crítica | Permissão de consulta permite gravação financeira
Constatação: Reprodução com conta temporária finance:[read], sem write: POST /api/finance/rules retornou 201 e persistiu regra. O decorador require_auth verifica somente finance/read, inclusive em várias rotas POST. Não equivale à dupla custódia dos cadastros administrativos antigos.
Correção/implementação necessária (NÃO EXECUTADA): Aplicar autorização por ação, entidade e operação financeira; garantir aprovação independente quando configurada e registrar autoria real.
Como comprovar o atendimento: Leitores recebem 403 em toda mutação; nenhuma linha é alterada; autores não aprovam as próprias operações.
Evidências: finance_api.py:10 (require_auth); finance_api.py:55 (handle_rules); artifacts/auditoria-20260924/probes.json.

### AUD-004 — Crítica — Consultas de pessoal sem permissão de módulo ou lotação

Requisitos: people.2, people.10, people.33, people.109, people.110, people.111, people.112, people.113, people.114. Cláusulas: 4.23, 4.28, 4.43.

AUD-004 | Prioridade Crítica | Consultas de pessoal sem permissão de módulo ou lotação
Constatação: Conta autenticada sem qualquer permissão recebeu 200 em employees, positions e sst/monitors. As consultas de people_api.py não exigem people/read, e get_work_locations ignora o parâmetro de entidade. A autenticação global não substitui autorização por lotação.
Correção/implementação necessária (NÃO EXECUTADA): Restringir todas as consultas de RH, SST e cadastro por módulo, entidade, lotação e titular; verificar também escrita e exportações.
Como comprovar o atendimento: Matriz de acessos negativos entre dois usuários, duas lotações e duas entidades, inclusive por ID direto, sem retorno de dados não autorizados.
Evidências: people_api.py:13 (list_employees); people_api.py:429 (list_monitors); people_core.py:57 (get_work_locations); artifacts/auditoria-20260924/probes.json.

### AUD-005 — Crítica — Cadastro público por CPF é apresentado como autenticação SIAFIC

Requisitos: finance.70, finance.71, finance.181, finance.182, finance.190, finance.191, finance.225, finance.226. Cláusulas: Anexo III.

AUD-005 | Prioridade Crítica | Cadastro público por CPF é apresentado como autenticação SIAFIC
Constatação: POST público /api/public/finance/siafic/auth aceitou CPF 000, criou cadastro ativo e marcou termo aceito sem senha, autorizador ou anexo. Esse endpoint tampouco estabelece autenticação CPF na sessão principal.
Correção/implementação necessária (NÃO EXECUTADA): Implementar autenticação efetiva por CPF, validação de identidade, autorização de acesso e termo real; não aceitar responsabilidade em nome do usuário.
Como comprovar o atendimento: CPF inválido, conta não autorizada e ausência de prova de identidade são rejeitados. A sessão autenticada é vinculada ao CPF e ao aceite comprovado.
Evidências: finance_core.py:1217 (authenticate_siafic_cpf); finance_api.py:501 (handle_siafic_auth); artifacts/auditoria-20260924/probes.json.

### AUD-006 — Crítica — Contracheque inexistente é declarado autêntico

Requisitos: people.77. Cláusulas: Anexo III.

AUD-006 | Prioridade Crítica | Contracheque inexistente é declarado autêntico
Constatação: A validação pública retornou autentico:true para token INVALIDO, matrícula 999999 e competência 1900-01. verify_payslip_public não verifica HMAC nem a existência do documento.
Correção/implementação necessária (NÃO EXECUTADA): Conferir assinatura/token, vínculo, competência e valores contra o documento persistido; usar chave protegida e URL institucional configurada.
Como comprovar o atendimento: Tokens inventados, adulterados ou de documentos inexistentes são rejeitados; documento íntegro é validado sem expor dados além dos necessários.
Evidências: people_api.py:378 (verify_payslip_public); people_core.py:1083 (generate_payslip_qr_token); artifacts/auditoria-20260924/probes.json.

### AUD-007 — Crítica — Demonstrativos, limites e apurações usam valores fixos

Requisitos: finance.19, finance.20, finance.21, finance.22, finance.23, finance.24, finance.25, finance.28, finance.45, finance.57, finance.151, finance.161, finance.162, finance.163, finance.164, finance.165, finance.166, finance.167, finance.168, finance.169, finance.170, finance.171, finance.172, finance.173, finance.174, finance.175, finance.176, finance.177, finance.178, finance.179. Cláusulas: Anexo III.

AUD-007 | Prioridade Crítica | Demonstrativos, limites e apurações usam valores fixos
Constatação: Balanço do exercício 2099, em base sem lançamentos financeiros, retornou receita realizada de 837.000.000. generate_anexo*, PASEP, duodécimo, RREO e RGF contêm valores literais; parâmetros de período e filtros não produzem apuração correspondente.
Correção/implementação necessária (NÃO EXECUTADA): Apurar cada demonstrativo a partir da escrituração real, com todos os quadros, filtros, comparativos e critérios previstos no respectivo item.
Como comprovar o atendimento: Base vazia não gera fatos; lançamentos controlados alteram os resultados exatos, conciliados com razão e balancete por entidade e período.
Evidências: finance_core.py:388 (generate_anexo12_balanco_orcamentario); finance_core.py:318 (calculate_pasep); finance_core.py:933 (generate_rreo_report); artifacts/auditoria-20260924/probes.json.

### AUD-008 — Alta — SIOPS e SIOPE não exportam a execução real

Requisitos: finance.14, finance.15, finance.16, finance.17, finance.18, finance.30, finance.31, finance.32. Cláusulas: Anexo III.

AUD-008 | Prioridade Alta | SIOPS e SIOPE não exportam a execução real
Constatação: As funções generate_siops_export e generate_siope_export devolvem pastas e montantes fixos. A existência de chaves no JSON não demonstra arquivos de terceiros importáveis nem atualização automática dos relacionamentos.
Correção/implementação necessária (NÃO EXECUTADA): Completar mapeamentos versionados, apuração, arquivos aceitos pelos destinatários e relatórios de conferência.
Como comprovar o atendimento: Importar arquivos gerados em ambiente oficial aplicável e conciliar cada total com movimentações de teste, registrando versões e críticas.
Evidências: finance_core.py:246 (generate_siops_export); finance_core.py:273 (generate_siope_export).

### AUD-009 — Crítica — MSC aceita texto inválido como XBRL validado

Requisitos: finance.8, finance.9, finance.10, finance.11, finance.12, finance.13, finance.53, finance.80. Cláusulas: Anexo III.

AUD-009 | Prioridade Crítica | MSC aceita texto inválido como XBRL validado
Constatação: Texto sem XML, contendo apenas matrizSaldosContabeis, foi aceito com status VALIDATED. O importador testa substrings; não carrega fatos importados na consulta. O gerador usa estrutura XML própria e informações complementares fixas.
Correção/implementação necessária (NÃO EXECUTADA): Validar conteúdo e estrutura oficiais, persistir os fatos, consolidar entidades e disponibilizar todas as críticas e filtros previstos.
Como comprovar o atendimento: XML malformado e arquivo fora do leiaute são rejeitados; arquivo válido consolida saldos e informações complementares com rastreabilidade.
Evidências: finance_core.py:176 (import_msc_file); finance_core.py:139 (generate_msc_file); finance_core.py:207 (query_msc_movements); artifacts/auditoria-20260924/probes.json.

### AUD-010 — Crítica — Transmissão EFD-Reinf simulada

Requisitos: finance.187, finance.188, finance.189. Cláusulas: Anexo III.

AUD-010 | Prioridade Crítica | Transmissão EFD-Reinf simulada
Constatação: validate_and_transmit_reinf_event monta xml_mock e recibo local sem transporte ao WebService. Não confundir com os conectores eSocial/PNCP existentes em outros arquivos.
Correção/implementação necessária (NÃO EXECUTADA): Completar geração por leiaute, validação, assinatura, envio, retorno e estados de erro/retificação da EFD-Reinf.
Como comprovar o atendimento: Guardar protocolo retornado pelo destinatário em homologação; indisponibilidade e rejeição não podem resultar em recibo de sucesso local.
Evidências: finance_core.py:752 (validate_and_transmit_reinf_event).

### AUD-011 — Crítica — OBE, PIX e retornos bancários simulados

Requisitos: finance.87, finance.192, finance.193, finance.194, finance.229. Cláusulas: Anexo III.

AUD-011 | Prioridade Crítica | OBE, PIX e retornos bancários simulados
Constatação: O lote calcula R$ 15.000 por ID de empenho, fabrica uma string CNAB e marca Remessa_Enviada. O retorno detecta a palavra REJEICAO e atribui rejeição de 10%, sem leitura de ocorrências e transações reais.
Correção/implementação necessária (NÃO EXECUTADA): Usar obrigações autorizadas e valores efetivos, leiautes bancários, transporte/arquivos, conciliação dos retornos e estornos contábeis correspondentes.
Como comprovar o atendimento: Lotes e PIX homologados por banco, com valores idênticos aos empenhos e rejeições por transação sem liquidação fictícia.
Evidências: finance_core.py:1005 (generate_obe_batch); finance_core.py:1029 (process_bank_return_file).

### AUD-012 — Crítica — Importação OFX ignora arquivo e conciliação força sucesso

Requisitos: finance.197, finance.219, finance.220, finance.221, finance.222. Cláusulas: Anexo III.

AUD-012 | Prioridade Crítica | Importação OFX ignora arquivo e conciliação força sucesso
Constatação: import_ofx_statement não utiliza o conteúdo para gerar os movimentos: grava três operações fixas e saldos fixos. auto_reconcile_ofx marca todas as linhas como conciliadas e zera a diferença sem pareamento.
Correção/implementação necessária (NÃO EXECUTADA): Ler o OFX real, preservar FITID/data/valor, comparar com movimentos internos, respeitar bloqueios e manter divergências visíveis.
Como comprovar o atendimento: Arquivos diferentes geram extratos diferentes; arquivo inválido é rejeitado; divergências não desaparecem e duplicidade de FITID é controlada.
Evidências: finance_core.py:1069 (import_ofx_statement); finance_core.py:1102 (auto_reconcile_ofx).

### AUD-013 — Alta — MANAD e SIGFIS não contêm prestação de contas completa

Requisitos: finance.183, finance.184. Cláusulas: Anexo III.

AUD-013 | Prioridade Alta | MANAD e SIGFIS não contêm prestação de contas completa
Constatação: MANAD contém apenas cabeçalho/rodapé; SIGFIS retorna um elemento XML sem os fatos da prestação e sem declaração do prefixo utilizado.
Correção/implementação necessária (NÃO EXECUTADA): Gerar leiautes completos, versionados e conciliados com os fatos contábeis e de pessoal, com validação apropriada.
Como comprovar o atendimento: Arquivos são aceitos pelos validadores aplicáveis e contêm todos os registros necessários, inclusive casos de cancelamento e retificação.
Evidências: finance_core.py:1201 (export_manad_file); finance_core.py:1207 (export_sigfis_tcerj).

### AUD-014 — Alta — Fluxos novos não demonstram integração com a escrituração ERP

Requisitos: finance.36, finance.37, finance.49, finance.50, finance.51, finance.52, finance.82, finance.143, finance.144, finance.145, finance.146, finance.185, finance.200, finance.207, finance.208, finance.209, finance.210. Cláusulas: Anexo III.

AUD-014 | Prioridade Alta | Fluxos novos não demonstram integração com a escrituração ERP
Constatação: A execução ERP grava erp_ledger/erp_objects; relatórios e MSC novos consultam finance_journal_entries e cadastros próprios. Não foi evidenciado vínculo automático completo entre essas duas bases funcionais.
Correção/implementação necessária (NÃO EXECUTADA): Integrar os registros e os relatórios ao mesmo conjunto de fatos, preservando identidade, entidade, exercício e atomicidade.
Como comprovar o atendimento: Um fluxo de compra, entrada, liquidação e pagamento aparece exatamente uma vez em razão, MSC, BI e transparência, incluindo estorno.
Evidências: erp_operations.py; inventory_core.py; finance_core.py:139 (generate_msc_file).

### AUD-015 — Alta — Resumo contratual agrega empenhos de outros contratos

Requisitos: procurement.21, procurement.22, procurement.50. Cláusulas: Anexo III.

AUD-015 | Prioridade Alta | Resumo contratual agrega empenhos de outros contratos
Constatação: get_contract_financial_summary lê process_id, mas seleciona empenhos apenas pelo fornecedor, sem filtrar processo, contrato, entidade ou exercício. Contratos do mesmo fornecedor podem receber totais alheios.
Correção/implementação necessária (NÃO EXECUTADA): Apurar saldo por vínculo contratual e contexto, considerando empenhos complementares, cancelamentos e instrumentos previstos.
Como comprovar o atendimento: Dois contratos do mesmo fornecedor em entidades/exercícios distintos mantêm totais independentes e conciliados.
Evidências: procurement_core.py:145 (get_contract_financial_summary).

### AUD-016 — Alta — Regularidade do fornecedor não comprova consulta tributária municipal

Requisitos: procurement.43, procurement.45. Cláusulas: Anexo III.

AUD-016 | Prioridade Alta | Regularidade do fornecedor não comprova consulta tributária municipal
Constatação: check_supplier_compliance consulta certidões locais e considera compliant quando não há vencidas, mesmo listando certidões ausentes. Não realiza consulta à situação tributária municipal.
Correção/implementação necessária (NÃO EXECUTADA): Completar a consulta tributária e distinguir regular, irregular e não comprovado; tratar a ausência de documentos conforme os controles exigidos.
Como comprovar o atendimento: Fornecedor sem certidões ou sem resposta da fonte não é apresentado como regularidade comprovada; relatório aplica os filtros do item 45.
Evidências: procurement_core.py:58 (check_supplier_compliance).

### AUD-017 — Crítica — Pregão: nove plataformas cadastradas, integração efetiva ausente

Requisitos: auction.1. Cláusulas: Anexo III.

AUD-017 | Prioridade Crítica | Pregão: nove plataformas cadastradas, integração efetiva ausente
Constatação: Mesmo simulate=False e endpoint inválido, transmit_exchange_package retorna TRANSMITIDO com recibo calculado localmente. import_exchange_results pode fabricar vencedores. Não há transporte nem recebimento comprovado de lances por item/lote, atas e resultado das nove plataformas.
Correção/implementação necessária (NÃO EXECUTADA): Implementar e homologar envio/recebimento de cada plataforma exigida, com contratos reais, autenticação, idempotência e validação de retornos.
Como comprovar o atendimento: Nove roteiros ponta a ponta, com recibos externos e conferência de propostas, lances, atas e resultado; nenhuma resposta local pode se passar por homologação externa.
Evidências: auction_core.py:143 (transmit_exchange_package); auction_core.py:169 (import_exchange_results); auction_api.py:74 (webhook); artifacts/auditoria-20260924/probes.json.

### AUD-018 — Crítica — Segredo de pregão persistido em texto claro

Requisitos: auction.1. Cláusulas: 4.27, 4.28, 4.32.

AUD-018 | Prioridade Crítica | Segredo de pregão persistido em texto claro
Constatação: configure_platform grava o token diretamente na coluna client_token_enc. Reproduzido com marcador fictício: conteúdo persistido idêntico à entrada.
Correção/implementação necessária (NÃO EXECUTADA): Usar cofre criptográfico, acesso restrito, mascaramento e rotação também neste caminho alternativo de integração.
Como comprovar o atendimento: Banco e logs não contêm token em claro; a rotina de transporte consegue utilizá-lo apenas sob autorização.
Evidências: auction_core.py:71 (configure_platform); artifacts/auditoria-20260924/probes.json.

### AUD-019 — Crítica — Datacenters e recuperação geográfica são registros simulados

Requisitos: cloud.1, cloud.4. Cláusulas: 4.53.5, 4.66.2, 4.79.2.

AUD-019 | Prioridade Crítica | Datacenters e recuperação geográfica são registros simulados
Constatação: init_cloud_db insere DC-RJ/DC-SP fictícios; simulate_dr_failover apenas inverte flags SQL e retorna RTO/RPO fixos. Não comprova residência selecionável, replicação ou snapshot entre regiões.
Correção/implementação necessária (NÃO EXECUTADA): Provisionar e comprovar provedor, regiões, residência dos dados, serviço relacional, cópias entre regiões e recuperação real.
Como comprovar o atendimento: Inventário do provedor e exercício de restauração/failover com dados conhecidos, tempos medidos e evidência de independência regional.
Evidências: cloud_core.py:13 (init_cloud_db); cloud_core.py:173 (simulate_dr_failover).

### AUD-020 — Crítica — As nove certificações do provedor não foram comprovadas

Requisitos: cloud.2. Cláusulas: Anexo III.

AUD-020 | Prioridade Crítica | As nove certificações do provedor não foram comprovadas
Constatação: O requisito pede ISO 27001, 27017, 27018, 27701, 22301, 9001 e SOC 1, 2, 3. A cobertura anterior citava apenas SLA 99,98%, que não comprova nenhuma dessas certificações. Não foi apresentado provedor contratado com esse conjunto documental.
Correção/implementação necessária (NÃO EXECUTADA): Apresentar documentos ou referências públicas em nome do provedor, com validade e escopo correspondentes ao serviço ofertado.
Como comprovar o atendimento: Conferência documental das nove certificações/acreditações e do vínculo com a infraestrutura efetivamente utilizada.
Evidências: tools/update_final_compliance.py; ANEXO III.pdf: página física 2, impressa 85.

### AUD-021 — Alta — HTTPS e acesso externo não comprovados na instalação local

Requisitos: cloud.3, general.6, control.2, bi.3. Cláusulas: 4.29, 4.38.

AUD-021 | Prioridade Alta | HTTPS e acesso externo não comprovados na instalação local
Constatação: A instalação examinada está em http://127.0.0.1:8080 e informa ambiente Local. SECURE_COOKIE/HSTS condicionais não provisionam TLS nem acesso por computador fora da rede.
Correção/implementação necessária (NÃO EXECUTADA): Implantar endpoint HTTPS institucional e testar o acesso externo aos produtos, com certificado válido, redirecionamento e configuração segura de cookies.
Como comprovar o atendimento: Acesso real de rede externa e validação TLS de todos os produtos; nenhuma alegação de TLS 1.3 somente por existência de cabeçalhos.
Evidências: app.py:22 (SECURE_COOKIE); artifacts/auditoria-20260924/browser.json.

### AUD-022 — Alta — Dashboard de usuários do provedor não demonstrado

Requisitos: cloud.5. Cláusulas: Anexo III.

AUD-022 | Prioridade Alta | Dashboard de usuários do provedor não demonstrado
Constatação: cloud.5 exige criação, inativação e reset de senha dos usuários do provedor. O status de CPU/RAM/NVMe descrito na cobertura anterior não atende esse objeto. Administração de usuários da aplicação é outro escopo.
Correção/implementação necessária (NÃO EXECUTADA): Demonstrar o painel de identidades do provedor e as três operações exigidas, com perfis e trilha de auditoria.
Como comprovar o atendimento: Criar conta de teste no painel do provedor, inativá-la, comprovar o bloqueio e realizar o reset de senha.
Evidências: cloud_api.py; ANEXO III.pdf: página física 2, impressa 85.

### AUD-023 — Alta — Escalabilidade e redimensionamento são flags fixas

Requisitos: cloud.6, cloud.7. Cláusulas: Anexo III.

AUD-023 | Prioridade Alta | Escalabilidade e redimensionamento são flags fixas
Constatação: get_cloud_infrastructure_status retorna auto_scaling_enabled=True, 4/16 nós e resizing=True sem comunicação com infraestrutura ou medição de carga.
Correção/implementação necessária (NÃO EXECUTADA): Configurar escalabilidade e redimensionamento do ambiente ofertado e demonstrar o comportamento sob carga e o prazo de resizing.
Como comprovar o atendimento: Medição antes/depois de CPU, memória, disco, nós e latência, com resizing médio de 5 minutos conforme o item.
Evidências: cloud_core.py:112 (get_cloud_infrastructure_status).

### AUD-024 — Crítica — Trinta backups de nuvem e integridade fictícios

Requisitos: cloud.8. Cláusulas: Anexo III.

AUD-024 | Prioridade Crítica | Trinta backups de nuvem e integridade fictícios
Constatação: São inseridas 30 linhas com tamanhos e hashes de dummy_content. verify_backup_integrity só atualiza o status para VERIFICADO_OK e não lê um arquivo. Há backup local real em backup.py, mas isso não comprova backup diário do provedor com retenção de 30 dias.
Correção/implementação necessária (NÃO EXECUTADA): Implementar política operacional comprovada no provedor, entrega ao contratante e testes periódicos de restauração dos arquivos efetivos.
Como comprovar o atendimento: Inventário de arquivos reais dos 30 dias, hashes verificados, download e restauração de amostras sem depender de tabelas simuladas.
Evidências: cloud_core.py:154 (verify_backup_integrity); cloud_core.py:13 (init_cloud_db); backup.py; artifacts/auditoria-20260924/probes.json.

### AUD-025 — Crítica — SOC, NOC, endpoint protection e WAF não comprovados

Requisitos: cloud.9, cloud.10, cloud.11, cloud.12. Cláusulas: Anexo III.

AUD-025 | Prioridade Crítica | SOC, NOC, endpoint protection e WAF não comprovados
Constatação: Eventos são semeados e respostas de monitoramento/EDR são literais. simulate_waf_block insere um registro e retorna status 403 em JSON; não demonstra bloqueio de tráfego na borda, DDoS, bots ou integração SOC. cloud.10 exige NOC, não apenas armazenamento de logs.
Correção/implementação necessária (NÃO EXECUTADA): Comprovar serviços e controles 24x7x365 do provedor, agentes, inteligência, resposta automatizada, monitoramento de rede e firewall profissional.
Como comprovar o atendimento: Documentação e teste autorizado de detecção/bloqueio real, escalonamento de incidente, correlação e resposta em cada componente requerido.
Evidências: cloud_api.py:61 (get_soc_dashboard); cloud_core.py:202 (simulate_waf_block).

### AUD-026 — Alta — Replicação de pessoal registra conclusão sem copiar dados

Requisitos: people.1. Cláusulas: Anexo III.

AUD-026 | Prioridade Alta | Replicação de pessoal registra conclusão sem copiar dados
Constatação: replicate_entity_data apenas insere people_entities_replication com COMPLETED. Não copia cargos, servidores, lotações ou verbas para uma base segregada de simulação.
Correção/implementação necessária (NÃO EXECUTADA): Executar replicação efetiva e segregada dos cadastros e permitir cálculos/relatórios na cópia preservando a origem.
Como comprovar o atendimento: Comparar contagens e vínculos na origem e destino, modificar e calcular a cópia e comprovar que a base principal não mudou.
Evidências: people_core.py:30 (replicate_entity_data).

### AUD-027 — Crítica — Conferência eSocial compara valores com cópia de si mesmos

Requisitos: people.99, people.108. Cláusulas: Anexo III.

AUD-027 | Prioridade Crítica | Conferência eSocial compara valores com cópia de si mesmos
Constatação: generate_esocial_totalizers_reconciliation calcula alíquotas fixas e copia o resultado para esoc_*, marcando divergências=0 e CONCILIADO_100_PORCENTO. Não lê totalizadores de retorno. O transporte real existente em integration_esocial_* não sana este comparativo.
Correção/implementação necessária (NÃO EXECUTADA): Relacionar apurações por trabalhador/competência aos eventos e totalizadores efetivamente recebidos, explicitando ausências e divergências.
Como comprovar o atendimento: Um retorno externo divergente gera crítica; ausência de retorno impede declaração de conciliação.
Evidências: people_core.py:1266 (generate_esocial_totalizers_reconciliation); integration_esocial.py.

### AUD-028 — Alta — Atualizações oficiais de pessoal não estão demonstradas

Requisitos: people.64, people.65, people.66, people.67, people.68, people.82, people.115. Cláusulas: Anexo III.

AUD-028 | Prioridade Alta | Atualizações oficiais de pessoal não estão demonstradas
Constatação: get_official_inss_table e get_cbo_catalog consultam tabelas locais. lookup_cep_correios contém fallback simulado. Não foi demonstrada atualização automática de RGPS/IR/salário mínimo nem integração efetiva com a base indicada no PDF.
Correção/implementação necessária (NÃO EXECUTADA): Completar aquisição, validação, vigência e atualização dos dados oficiais e exibir origem/data; não retornar endereço inventado.
Como comprovar o atendimento: Troca de versão oficial é refletida no cadastro e no cálculo; falha de fonte é sinalizada, com preservação da versão anterior validada.
Evidências: people_core.py:1409 (get_official_inss_table); people_core.py:1422 (get_cbo_catalog); people_core.py:1384 (lookup_cep_correios).

### AUD-029 — Alta — Portal do servidor possui autorização e consulta pendentes

Requisitos: people.71, people.72, people.76, people.78, people.79, people.80, people.81. Cláusulas: Anexo III.

AUD-029 | Prioridade Alta | Portal do servidor possui autorização e consulta pendentes
Constatação: Primeiro acesso provisiona senha para CPF conhecido sem verificação adicional; rotas usam employee_id fornecido pelo cliente sem vínculo de titularidade. A listagem de atualizações pendentes faz JOIN com erp_people_employees, tabela não criada pelos schemas consultados (cadastro usa people_employees).
Correção/implementação necessária (NÃO EXECUTADA): Estabelecer acesso do titular, recuperação verificada, validação de comprovantes e revisão RH sobre a tabela correta, com atualização auditada.
Como comprovar o atendimento: Servidor A não consulta nem propõe mudanças para B; fila RH carrega e permite validar/rejeitar com anexos; recuperação envia link real ao endereço cadastrado.
Evidências: people_core.py:1095 (portal_authenticate); people_api.py:335 (submit_portal_update); people_api.py:345 (list_pending_updates).

### AUD-030 — Crítica — RMA CRAS/CREAS/POP contém quantitativos artificiais

Requisitos: social.92, social.93, social.94, social.95, social.96, social.97, social.98, social.99, social.100, social.101, social.102. Cláusulas: Anexo III.

AUD-030 | Prioridade Crítica | RMA CRAS/CREAS/POP contém quantitativos artificiais
Constatação: RMA CREAS e POP inserem quantitativos fixos quando não existe apuração; CRAS utiliza constantes e proporções não derivadas de todos os atendimentos do período. O XML usa código IBGE divergente daquele empregado nas integrações municipais do projeto. Não há evidência de aceite oficial do leiaute gerado.
Correção/implementação necessária (NÃO EXECUTADA): Calcular cada campo dos formulários a partir dos fatos da unidade/mês, prover ajuda de origem, ajustes auditados e XML validado para o destinatário.
Como comprovar o atendimento: Unidade sem atendimentos não recebe valores fictícios; um atendimento controlado altera somente os campos correspondentes e fecha com conciliação analítica.
Evidências: social_core.py:540 (get_or_calculate_rma_cras); social_core.py:621 (get_or_calculate_rma_creas); social_core.py:682 (get_or_calculate_rma_pop); social_core.py:584 (export_rma_cras_xml).

### AUD-031 — Crítica — Assinatura social P7S e certificado são simulados

Requisitos: social.280, social.281, social.282, social.283, social.284, social.285, social.286, social.287, social.288, social.289, social.290. Cláusulas: Anexo III.

AUD-031 | Prioridade Crítica | Assinatura social P7S e certificado são simulados
Constatação: sign_document_icp concatena prefixo Base64 e hash, usa serial fixo ICP-BR-RO-2026-X509 e grava validade padrão. verify_digital_signature consulta a flag; não verifica chave, certificado, conteúdo ou prazo. Hash sozinho não é assinatura digital.
Correção/implementação necessária (NÃO EXECUTADA): Integrar a assinatura criptográfica dos documentos sociais, confirmação do certificado válido, formatos exigidos, verificação independente, alertas e consultas.
Como comprovar o atendimento: Documento adulterado e certificado vencido são rejeitados; P7S/PDF é verificável por ferramenta independente e preserva o conteúdo assinado.
Evidências: social_core.py:891 (sign_document_icp); social_core.py:909 (verify_digital_signature).

### AUD-032 — Alta — Georreferenciamento social não demonstra todos os modos exigidos

Requisitos: social.45, social.46, social.47, social.48, social.49, social.50, social.51, social.52, social.53, social.54, social.55, social.56, social.57. Cláusulas: Anexo III.

AUD-032 | Prioridade Alta | Georreferenciamento social não demonstra todos os modos exigidos
Constatação: As rotinas localizadas produzem pontos/diagnóstico; não foi comprovada a execução integral de mapa interativo, satélite, vistas 360°, delimitações e geocodificação automática do endereço. A nota anterior reutilizava a mesma referência para os 13 itens.
Correção/implementação necessária (NÃO EXECUTADA): Demonstrar cada modo e filtro em navegador; completar as funções ausentes, com fonte geográfica e configuração apropriadas.
Como comprovar o atendimento: Cadastrar endereço, obter coordenada correspondente e navegar em todos os modos exigidos, distinguindo pessoa/família e restrições de acesso.
Evidências: social_core.py:128 (get_territorial_heatmap); static/social-ui.js.

### AUD-033 — Alta — SMS de agendamento sem fluxo de envio comprovado

Requisitos: social.116, social.117, social.118. Cláusulas: 4.80.6.

AUD-033 | Prioridade Alta | SMS de agendamento sem fluxo de envio comprovado
Constatação: A cobertura anterior destes itens citava RMA, sem relação com SMS. Não foram localizados envio SMS, configuração de provedor, fila ou status de entrega/erro no fluxo social examinado.
Correção/implementação necessária (NÃO EXECUTADA): Implementar configuração, mensagens parametrizadas com dados do agendamento, envio efetivo e gerenciamento de falhas.
Como comprovar o atendimento: Mensagem de agendamento recebida em destino de homologação, com status real e erro/reenvio rastreável.
Evidências: tools/update_social_compliance.py; social_api.py; social_core.py.

### AUD-034 — Alta — Importadores sociais cobrem somente parte das bases exigidas

Requisitos: social.401, social.402, social.403, social.404, social.405, social.406, social.407, social.408, social.409, social.410, social.411, social.412, social.413, social.414, social.415, social.416, social.417, social.418, social.419. Cláusulas: Anexo III.

AUD-034 | Prioridade Alta | Importadores sociais cobrem somente parte das bases exigidas
Constatação: Foram localizados process_cadunico_import e process_sicon_import. Não há comprovação do conjunto de importações periódicas da folha do benefício, Sibec, BPC e CECAD com progresso, filtros e motivo por registro. A nota anterior atribuía o mesmo atendimento a todos os itens.
Correção/implementação necessária (NÃO EXECUTADA): Completar cada importador e os respectivos leiautes, periodicidade, progresso, críticas e vínculos; validar arquivos representativos fornecidos pelo município.
Como comprovar o atendimento: Para cada base, arquivo válido/importação repetida/registro inválido têm resultados rastreáveis por pessoa e família, sem duplicação.
Evidências: social_core.py:1152 (process_cadunico_import); social_core.py:1206 (process_sicon_import); social_api.py.

### AUD-035 — Alta — Sigilo por especialidade e unidade não comprovado no novo módulo social

Requisitos: social.178, social.180, social.254, social.279, social.328, social.329. Cláusulas: 4.23, 4.28, 4.43.

AUD-035 | Prioridade Alta | Sigilo por especialidade e unidade não comprovado no novo módulo social
Constatação: A proteção social_confidential existe no ERP genérico, mas as novas rotas /api/social usam permissões amplas de módulo. Não foi demonstrada política por especialidade, unidade e profissional em toda consulta, histórico, alteração e exportação.
Correção/implementação necessária (NÃO EXECUTADA): Unificar a política de sigilo nos caminhos novos e antigos, com autorização do objeto e campos sensíveis.
Como comprovar o atendimento: Profissional de outra especialidade/unidade não acessa o registro por ID, busca, relatório ou histórico; acessos autorizados ficam auditados.
Evidências: erp_core.py:83 (confidential_sql); social_api.py; social_core.py:337 (get_family_details).

### AUD-036 — Alta — E-mail de controladoria apenas registrado localmente

Requisitos: control.16, control.23, control.27. Cláusulas: Anexo III.

AUD-036 | Prioridade Alta | E-mail de controladoria apenas registrado localmente
Constatação: send_obligation_email grava acompanhamento e notificação interna; não chama transporte SMTP/API. Registrar destinatário e mensagem não comprova comunicação externa ou avisos de vencimento.
Correção/implementação necessária (NÃO EXECUTADA): Completar envio real, configuração, fila, agenda de vencimentos, erro e evidência de entrega; preservar o histórico.
Como comprovar o atendimento: Destinatário recebe a mensagem, tentativas e falhas ficam registradas e avisos respeitam os prazos da obrigação.
Evidências: control_core.py:232 (send_obligation_email).

### AUD-037 — Crítica — Ranking SICONFI reprocessado por resultado predefinido

Requisitos: control.30, control.31, control.32, control.33, control.34, control.35, control.36, control.37, control.38, control.39, control.40, control.45, control.46, control.47. Cláusulas: Anexo III.

AUD-037 | Prioridade Crítica | Ranking SICONFI reprocessado por resultado predefinido
Constatação: reprocess_siconfi_period marca regras como Conforme e força uma exceção para STN-D2-02, com divergência fixa. Não executa as verificações sobre a informação contábil/fiscal do período. O conector de extrato de obrigações existente tem outra finalidade.
Correção/implementação necessária (NÃO EXECUTADA): Executar regras oficiais versionadas sobre os dados do período, por dimensão e poder, com memória de cálculo e origem.
Como comprovar o atendimento: Alterar dados de entrada produz as divergências esperadas em cada regra, sem resultados definidos pelo código do requisito.
Evidências: control_core.py:450 (reprocess_siconfi_period); integration_siconfi.py.

### AUD-038 — Alta — Integrações CAUC e convênios dependem de comprovação

Requisitos: control.54, control.56, control.70, control.72. Cláusulas: Anexo III.

AUD-038 | Prioridade Alta | Integrações CAUC e convênios dependem de comprovação
Constatação: Os dashboards consultam control_cauc_requirements/control_agreements locais. Carga seed e painel não demonstram importação atualizada dos serviços de dados abertos pedidos nesses itens.
Correção/implementação necessária (NÃO EXECUTADA): Completar ou evidenciar os conectores, atualização, histórico da origem e falhas de sincronização.
Como comprovar o atendimento: Mudança controlada na fonte é refletida no painel com data de consulta e histórico, sem substituir falha por regularidade fictícia.
Evidências: control_core.py:597 (get_cauc_dashboard); control_core.py:652 (get_agreements_dashboard); control_seed.py.

### AUD-039 — Crítica — BI apresenta indicadores fixos ou sem vínculo com a execução

Requisitos: bi.1, bi.11, bi.12, bi.13, bi.14, bi.15, bi.16, bi.17, bi.18, bi.19, bi.20, bi.21, bi.22, bi.23, bi.24, bi.25, bi.26, bi.27, bi.28, bi.29, bi.30, bi.31, bi.32, bi.33, bi.34, bi.35, bi.36, bi.37, bi.38, bi.39, bi.40, bi.41, bi.42, bi.43, bi.44, bi.45, bi.46, bi.47, bi.48, bi.49, bi.50, bi.51, bi.52. Cláusulas: Anexo III.

AUD-039 | Prioridade Crítica | BI apresenta indicadores fixos ou sem vínculo com a execução
Constatação: Painel LRF usa percentuais/valores de fallback e indicadores literais de Legislativo, dívida e operações. As tabelas bi_* não demonstram atualização integrada de todos os fatos. Em exercício sem dados, há fallback de outro exercício. Não confundir com erp_insights, que possui consultas reais limitadas.
Correção/implementação necessária (NÃO EXECUTADA): Ligar cada indicador à fonte operacional, competência, entidade e filtros; sinalizar ausência de dados e completar comparativos e detalhamentos exigidos.
Como comprovar o atendimento: Inserir, alterar e estornar fatos controlados de finanças, pessoas, compras e patrimônio muda cada indicador correspondente; exercício vazio não reutiliza outro sem aviso.
Evidências: bi_core.py:27 (get_executive_lrf_dashboard); bi_seed.py; erp_insights.py; artifacts/auditoria-20260924/probes.json.

### AUD-040 — Crítica — Transparência publica dados demonstrativos e valores presumidos

Requisitos: transparency.45, transparency.46, transparency.47, transparency.48, transparency.49, transparency.50, transparency.51, transparency.52, transparency.53, transparency.54, transparency.55, transparency.56, transparency.57, transparency.58, transparency.59, transparency.80, transparency.132, transparency.133, transparency.134, transparency.146, transparency.147. Cláusulas: Anexo III.

AUD-040 | Prioridade Crítica | Transparência publica dados demonstrativos e valores presumidos
Constatação: seed_transparency é chamado incondicionalmente ao iniciar, inclusive demo=False, e insere dívidas/emendas fictícias. query_personnel acrescenta servidores de exemplo; patrimônio/estoque completam campos com valores, fornecedor, saldos e URLs inventados. As configurações padrão são sobrescritas em toda inicialização.
Correção/implementação necessária (NÃO EXECUTADA): Separar demonstração de dados publicáveis, remover fallback fictício de consultas reais, preservar configuração institucional e publicar somente informação efetiva e conferida.
Como comprovar o atendimento: Instalação sem demonstração não publica fatos inventados; reiniciar preserva parâmetros; saldos e anexos públicos correspondem às bases e arquivos reais.
Evidências: transparency_api.py:29 (install_transparency); transparency_seed.py:5 (seed_transparency); transparency_core.py:515 (query_personnel); transparency_core.py:585 (query_assets_detailed); transparency_core.py:628 (query_inventory_with_supplier).

### AUD-041 — Alta — Demonstrativos patrimoniais TCE-RJ não comprovados integralmente

Requisitos: assets.27. Cláusulas: Anexo III.

AUD-041 | Prioridade Alta | Demonstrativos patrimoniais TCE-RJ não comprovados integralmente
Constatação: report(tce) usa a mesma listagem patrimonial de depreciação/responsabilidade, com bens ativos e posição atual. Não há evidência de todos os demonstrativos, modelos e conciliação histórica necessários ao item. Os testes comprovam emissão da listagem, não homologação do modelo pelo TCE.
Correção/implementação necessária (NÃO EXECUTADA): Identificar e gerar cada demonstrativo aplicável à exigência do PDF, com período, saldos, responsáveis e conciliação validados.
Como comprovar o atendimento: Conferência dos demonstrativos por responsável contábil e confronto com saldos conhecidos, movimentações e modelo exigido.
Evidências: asset_api.py:47 (report); tests/test_assets.py.

### AUD-042 — Alta — Fotos de obras registram nome sem conteúdo ou arquivo vinculado

Requisitos: works.1, works.7, works.8, works.14, works.40, works.42. Cláusulas: Anexo III.

AUD-042 | Prioridade Alta | Fotos de obras registram nome sem conteúdo ou arquivo vinculado
Constatação: upload_diary_photo recebe filename/caption e insere metadados, mas não recebe imagem nem referencia anexo protegido existente. Aprovar essa linha não comprova foto disponível para o diário/portal.
Correção/implementação necessária (NÃO EXECUTADA): Vincular cada foto a conteúdo armazenado, validar tipo/tamanho/autorização e publicar apenas as fotos aprovadas.
Como comprovar o atendimento: Upload, download, prévia do diário e portal reproduzem a mesma imagem; nome sem arquivo é rejeitado e foto não aprovada fica protegida.
Evidências: works_api.py:144 (upload_diary_photo).

### AUD-043 — Média — Google Maps de obras abre fora do sistema

Requisitos: works.27. Cláusulas: Anexo III.

AUD-043 | Prioridade Média | Google Maps de obras abre fora do sistema
Constatação: worksProjectDetail renderiza coordenadas e link target=_blank. O PDF pede visualização numa tela Google Maps dentro do sistema.
Correção/implementação necessária (NÃO EXECUTADA): Disponibilizar a visualização interna exigida com configuração e restrições apropriadas, mantendo os vínculos das obras.
Como comprovar o atendimento: A obra aparece em mapa interativo dentro da tela da aplicação, nas coordenadas informadas.
Evidências: static/works-ui.js:59 (works-map-placeholder).

### AUD-044 — Alta — Mil almoxarifados: cadastro testado, simultaneidade não comprovada

Requisitos: inventory.1. Cláusulas: Anexo III.

AUD-044 | Prioridade Alta | Mil almoxarifados: cadastro testado, simultaneidade não comprovada
Constatação: test_more_than_one_thousand_interconnected_warehouses passou e cria 1.001 almoxarifados sequencialmente com uma transferência. Isso comprova capacidade cadastral, mas não operação simultânea acima de 1.000 unidades com disputa de saldo.
Correção/implementação necessária (NÃO EXECUTADA): Executar prova de carga concorrente representativa com transferências e rastreabilidade, mantendo consistência dos saldos.
Como comprovar o atendimento: Mais de 1.000 unidades operam no cenário simultâneo definido, com medição de latência, falhas, integridade e saldos em trânsito.
Evidências: tests/test_inventory_controls.py:49 (test_more_than_one_thousand_interconnected_warehouses); tools/performance_erp_check.py.

### AUD-045 — Alta — Relatórios históricos da frota usam localização atual

Requisitos: fleet.19, fleet.20, fleet.22, fleet.24, fleet.25. Cláusulas: Anexo III.

AUD-045 | Prioridade Alta | Relatórios históricos da frota usam localização atual
Constatação: fleet_api.report associa eventos antigos à localização e aos atributos patrimoniais atuais retornados por _vehicles. Uma transferência posterior pode alterar os agrupamentos de um período já encerrado. Falta prova histórica dessa situação.
Correção/implementação necessária (NÃO EXECUTADA): Definir e preservar localização e atributos na data do fato para os relatórios históricos; conciliar todos os custos por período.
Como comprovar o atendimento: Transferir veículo após o período não altera o relatório daquele período; custos por km/h incluem exatamente seus eventos e o agrupamento temporal correto.
Evidências: fleet_api.py:28 (_vehicles); fleet_api.py:61 (report).

### AUD-046 — Alta — Novas telas enviam POST sem token CSRF

Requisitos: transversal. Cláusulas: 4.45, 4.72.5.

AUD-046 | Prioridade Alta | Novas telas enviam POST sem token CSRF
Constatação: Os helpers/fetch de Pessoas, Finanças, Social e BI enviam JSON sem X-CSRF-Token em operações protegidas. A autenticação global exige o token; portanto, além do bloqueio CSP, esses fluxos têm impedimento adicional para gravar.
Correção/implementação necessária (NÃO EXECUTADA): Usar o cliente autenticado comum e tratar respostas de erro antes de informar sucesso, conservando a proteção CSRF.
Como comprovar o atendimento: Após resolver os eventos, cada operação pela tela envia token válido, grava quando autorizada e exibe falhas reais sem falso sucesso.
Evidências: static/people-ui.js:17 (async function apiCall); static/finance-ui.js:474 (fetch('/api/finance/journal/post'); static/social-ui.js:587 (fetch('/api/social/rma/cras/close'); static/bi-ui.js:807 (fetch('/api/bi/share'); auth.py:71 (X-CSRF-Token).

### AUD-047 — Alta — Reajuste de obras não preserva integralmente a planilha anterior

Requisitos: works.36, works.37. Cláusulas: Anexo III.

AUD-047 | Prioridade Alta | Reajuste de obras não preserva integralmente a planilha anterior
Constatação: linear_adjustment altera os dados dos mesmos itens de erp_objects e grava uma linha de versão com total; essa rotina não guarda snapshot completo dos itens anteriores nem desativa as versões anteriores. Falta demonstrar reconstrução fiel das planilhas e medições subsequentes.
Correção/implementação necessária (NÃO EXECUTADA): Preservar as versões completas da planilha e vincular medições à versão correta, sem reprecificar retroativamente fatos encerrados.
Como comprovar o atendimento: Após reajuste/supressão, recuperar cada versão anterior com quantidades e preços exatos, mantendo os valores de medições já aprovadas.
Evidências: works_operations.py:12 (linear_adjustment); works_schema.sql.

### AUD-048 — Média — Políticas de senha e bloqueio não têm toda a parametrização pedida

Requisitos: general.2, general.7. Cláusulas: 4.36, 4.36.1, 4.39.

AUD-048 | Prioridade Média | Políticas de senha e bloqueio não têm toda a parametrização pedida
Constatação: check_password aceita somente nível Forte. max_attempts/lock_minutes são globais em settings, embora o PDF mencione bloqueio com período definido por usuário. Classificação visual não comprova os três níveis configuráveis exigidos.
Correção/implementação necessária (NÃO EXECUTADA): Resolver a aderência da política de níveis e parametrização por usuário com a contratante, preservando segurança e formalizando a regra aceita.
Como comprovar o atendimento: Demonstrar as configurações previstas ou aceite formal da divergência; comprovar bloqueio, troca obrigatória e invalidação de sessões por usuário.
Evidências: auth.py:18 (check_password); auth.py:92 (login); db.py:9 (DEFAULTS).

## Cláusulas do recorte do edital

### edital.4.1.p35.1 — Operacional

A presente contratação orienta-se pelos seguintes requisitos de negócio: Requisitos de Capacitação

AUDITORIA 24/09/2026 — Cláusula 4.1, página impressa 35.
Comprovar treinamento presencial para 30 usuários, início após carga, máximo de 40h e 8h/dia, programa de conteúdos, responsáveis, local e aceites. content.py contém tutoriais textuais; não comprova vídeos EAD, participação ou execução contratual. Exigir registros de frequência e acesso ilimitado ao conteúdo previsto, conforme a cláusula específica.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.1.p35.2 — Operacional

O treinamento dos funcionários para operar os Softwares, durante a implantação deverá iniciar-se imediatamente após a carga e instalação dos dados, abrangendo, também, os procedimentos para a geração de backups diários para segurança dos dados. Este treinamento será ministrado nas dependências da CONTRATANTE, devendo todos os custos ser arcados pela empresa contratada tendo a duração máxima de 40 (quarenta) horas.

AUDITORIA 24/09/2026 — Cláusula 4.1, página impressa 35.
Comprovar treinamento presencial para 30 usuários, início após carga, máximo de 40h e 8h/dia, programa de conteúdos, responsáveis, local e aceites. content.py contém tutoriais textuais; não comprova vídeos EAD, participação ou execução contratual. Exigir registros de frequência e acesso ilimitado ao conteúdo previsto, conforme a cláusula específica.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.2.p35.3 — Operacional

Entende-se por implantação, o conjunto de serviços necessários para instalar, colocar em funcionamento e deixar em condições de uso para os usuários executarem suas tarefas, do sistema aplicativo (software) especificado nesse edital, com aprovação positiva dos usuários de cada departamento responsável.

AUDITORIA 24/09/2026 — Cláusula 4.2, página impressa 35.
Comprovar treinamento presencial para 30 usuários, início após carga, máximo de 40h e 8h/dia, programa de conteúdos, responsáveis, local e aceites. content.py contém tutoriais textuais; não comprova vídeos EAD, participação ou execução contratual. Exigir registros de frequência e acesso ilimitado ao conteúdo previsto, conforme a cláusula específica.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.3.p35.4 — Operacional

A empresa Contratada deverá oferecer treinamento, durante a implantação, para os servidores indicados pelo(a) Contratante de forma a garantir adequada e plena utilização do sistema.

AUDITORIA 24/09/2026 — Cláusula 4.3, página impressa 35.
Comprovar treinamento presencial para 30 usuários, início após carga, máximo de 40h e 8h/dia, programa de conteúdos, responsáveis, local e aceites. content.py contém tutoriais textuais; não comprova vídeos EAD, participação ou execução contratual. Exigir registros de frequência e acesso ilimitado ao conteúdo previsto, conforme a cláusula específica.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.4.p35.5 — Operacional

Os referidos treinamentos serão realizados na sede do Contratante s endo de inteira responsabilidade das Entidades Municipais a identificação e reserva de local e equipamentos para a realização do mesmo, a prestação de serviço será realizada dentro da sede da Prefeitura, na Secretaria Municipal de Fazenda.

AUDITORIA 24/09/2026 — Cláusula 4.4, página impressa 35.
Comprovar treinamento presencial para 30 usuários, início após carga, máximo de 40h e 8h/dia, programa de conteúdos, responsáveis, local e aceites. content.py contém tutoriais textuais; não comprova vídeos EAD, participação ou execução contratual. Exigir registros de frequência e acesso ilimitado ao conteúdo previsto, conforme a cláusula específica.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.5.p35.6 — Operacional

O treinamento presencial será destinado a 30 usuários, podendo ocorrer de forma individual ou em turmas, conforme listagem fornecida pela CONTRATANTE.

AUDITORIA 24/09/2026 — Cláusula 4.5, página impressa 35.
Comprovar treinamento presencial para 30 usuários, início após carga, máximo de 40h e 8h/dia, programa de conteúdos, responsáveis, local e aceites. content.py contém tutoriais textuais; não comprova vídeos EAD, participação ou execução contratual. Exigir registros de frequência e acesso ilimitado ao conteúdo previsto, conforme a cláusula específica.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.6.p35.7 — Operacional

A CONTRATADA deverá oferecer ambiente EAD com vídeos, tutoriais e conteúdos relacionados ao treinamento, com acesso ilimi tado e gratuito para todos os servidores públicos municipais envolvidos.

AUDITORIA 24/09/2026 — Cláusula 4.6, página impressa 35.
Comprovar treinamento presencial para 30 usuários, início após carga, máximo de 40h e 8h/dia, programa de conteúdos, responsáveis, local e aceites. content.py contém tutoriais textuais; não comprova vídeos EAD, participação ou execução contratual. Exigir registros de frequência e acesso ilimitado ao conteúdo previsto, conforme a cláusula específica.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.7.p35.8 — Operacional

O treinamento deverá ter no máximo, carga horária de 8 (oito) horas diárias, e dispor em sua programação o seguinte conteúdo mínimo:

AUDITORIA 24/09/2026 — Cláusula 4.7, página impressa 35.
Comprovar treinamento presencial para 30 usuários, início após carga, máximo de 40h e 8h/dia, programa de conteúdos, responsáveis, local e aceites. content.py contém tutoriais textuais; não comprova vídeos EAD, participação ou execução contratual. Exigir registros de frequência e acesso ilimitado ao conteúdo previsto, conforme a cláusula específica.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.7.1.p35.9 — Operacional

Operação do sistema para organização em programas das ações dos órgãos da administração, assegurando o alinhamento destes com a orientação estratégica do governo e com as previsões de disponibilidade de recursos;

AUDITORIA 24/09/2026 — Cláusula 4.7.1, página impressa 35.
Comprovar treinamento presencial para 30 usuários, início após carga, máximo de 40h e 8h/dia, programa de conteúdos, responsáveis, local e aceites. content.py contém tutoriais textuais; não comprova vídeos EAD, participação ou execução contratual. Exigir registros de frequência e acesso ilimitado ao conteúdo previsto, conforme a cláusula específica.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.7.2.p35.10 — Operacional

Operação do sistema para dispor o usuário de condições para avaliação e mensuração dos produtos das ações do governo e dos efeitos destas ações sobre a realidade de seu território;

AUDITORIA 24/09/2026 — Cláusula 4.7.2, página impressa 35.
Comprovar treinamento presencial para 30 usuários, início após carga, máximo de 40h e 8h/dia, programa de conteúdos, responsáveis, local e aceites. content.py contém tutoriais textuais; não comprova vídeos EAD, participação ou execução contratual. Exigir registros de frequência e acesso ilimitado ao conteúdo previsto, conforme a cláusula específica.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.7.3.p35.11 — Operacional

Operação do sistema para dotar os administradores públicos de um instrumento gerencial estruturado e atualizado, objetivando facilitar a tomada de decisões, corrigir desvios e direcionar a aplicação de recursos para a realização dos resultados pretendidos.

AUDITORIA 24/09/2026 — Cláusula 4.7.3, página impressa 35.
Comprovar treinamento presencial para 30 usuários, início após carga, máximo de 40h e 8h/dia, programa de conteúdos, responsáveis, local e aceites. content.py contém tutoriais textuais; não comprova vídeos EAD, participação ou execução contratual. Exigir registros de frequência e acesso ilimitado ao conteúdo previsto, conforme a cláusula específica.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.8.p35.12 — Operacional

As instalações físicas, equipamentos e materiais necessários para aplicação dos treinamentos serão providenciados e disponibilizados pela Entidade Municipal. Requisitos Legais

AUDITORIA 24/09/2026 — Cláusula 4.8, página impressa 35.
Comprovar treinamento presencial para 30 usuários, início após carga, máximo de 40h e 8h/dia, programa de conteúdos, responsáveis, local e aceites. content.py contém tutoriais textuais; não comprova vídeos EAD, participação ou execução contratual. Exigir registros de frequência e acesso ilimitado ao conteúdo previsto, conforme a cláusula específica.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.9.p35.13 — Dependência externa

O presente processo de contratação deve estar aderente à Constituição Federal, à Lei nº 14.133, de 01 de abril de 2021, à Instrução Normativa SGD/ME nº 94, de 2022, Instrução Normativa SEGES/ME nº 65, de 7 de julho de 2021, Lei nº 13.709, de 14 de agosto de 2018 (Lei Geral de 
Proteção de Dados Pessoais – LGPD), da Lei nº 14.133, de 01 de abril de 2021, Decreto Municipal 
nº 3884/2024 e demais legislações aplicáveis; 
Requisitos de Manutenção

AUDITORIA 24/09/2026 — Cláusula 4.9, página impressa 35.
Verificação jurídica/institucional não concluída. Exigir documentação e avaliação dos responsáveis quanto às referências expressas no PDF; esta auditoria de software não certifica aderência legal nem verifica alterações legislativas posteriores.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.10.p36.14 — Operacional

A prestação dos serviços de atualização de Softwares se dará nas seguintes modalidades:

AUDITORIA 24/09/2026 — Cláusula 4.10, página impressa 36.
Há chamados, prioridades, prazos e workaround em records.py/domain.py e testes/test_system.py. Isso não comprova equipe, atendimento remoto/presencial, garantia de 90 dias, manutenção preventiva/adaptativa/evolutiva ou prorrogação aceita pela fiscalização. Conferir a cláusula específica com contrato, calendário e evidências de operação. Tabela do PDF: crítico 2h/6h, alto 4h/8h úteis, médio 8h/24h úteis, baixo 24h/48h úteis.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.10.1.p36.15 — Operacional

Corretiva, que visa corrigir erros e defeitos de funcionamento do Software, podendo a critério da empresa, limitar -se à substituição da cópia com falhas por uma cópia corrigida, não incluindo nestas ações que se tornem necessárias por uso incorreto ou não autorizado, vandalismo, sinistros ou apropriações indébitas;

AUDITORIA 24/09/2026 — Cláusula 4.10.1, página impressa 36.
Há chamados, prioridades, prazos e workaround em records.py/domain.py e testes/test_system.py. Isso não comprova equipe, atendimento remoto/presencial, garantia de 90 dias, manutenção preventiva/adaptativa/evolutiva ou prorrogação aceita pela fiscalização. Conferir a cláusula específica com contrato, calendário e evidências de operação. Tabela do PDF: crítico 2h/6h, alto 4h/8h úteis, médio 8h/24h úteis, baixo 24h/48h úteis.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.10.2.p36.16 — Operacional

Adaptativa, visando adaptações legais para adequar o Software às alterações da Legislação, desde que não impliquem em desenvolvimento de novas telas, novas funções ou rotinas, ou, ainda, alterações na arquitetura do Software.

AUDITORIA 24/09/2026 — Cláusula 4.10.2, página impressa 36.
Há chamados, prioridades, prazos e workaround em records.py/domain.py e testes/test_system.py. Isso não comprova equipe, atendimento remoto/presencial, garantia de 90 dias, manutenção preventiva/adaptativa/evolutiva ou prorrogação aceita pela fiscalização. Conferir a cláusula específica com contrato, calendário e evidências de operação. Tabela do PDF: crítico 2h/6h, alto 4h/8h úteis, médio 8h/24h úteis, baixo 24h/48h úteis.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.10.3.p36.17 — Operacional

Evolutiva, que visa garantir a atualização do Software, através da adição de novas funcionalidades aos SOFTWARES não constantes no momento atual, isto é, não previstas nas especificações técnicas do instrumento convocatório, ou da proposta apresentada pela CONTRATADA, ou ainda inexistente no momento do recebimento do software, sempre obedecendo aos critérios da metodologia de desenvolvimento da CONTRATADA.

AUDITORIA 24/09/2026 — Cláusula 4.10.3, página impressa 36.
Há chamados, prioridades, prazos e workaround em records.py/domain.py e testes/test_system.py. Isso não comprova equipe, atendimento remoto/presencial, garantia de 90 dias, manutenção preventiva/adaptativa/evolutiva ou prorrogação aceita pela fiscalização. Conferir a cláusula específica com contrato, calendário e evidências de operação. Tabela do PDF: crítico 2h/6h, alto 4h/8h úteis, médio 8h/24h úteis, baixo 24h/48h úteis.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.10.4.p36.18 — Operacional

Para cumprimento, a CONTRATANTE deverá comunicar à CONTRATADA a alteração nas legislações federal, estadual e municipal, encaminhando o diploma legal anterior e o novo, informando a data de sua publicação e o início de sua vigência. A CONTRATADA de posse dessas informações fará uma anális e técnica e apresentará uma estimativa do esforço e prazo para a entrega da versão do software adequada à alteração, sempre respeitando sua metodologia de desenvolvimento. A CONTRATANTE se compromete, ainda, a atuar como interlocutora da CONTRATADA, quando necessário, junto aos órgãos reguladores / fiscalizadores, para dirimir dúvidas técnicas e / ou pedidos de esclarecimentos.

AUDITORIA 24/09/2026 — Cláusula 4.10.4, página impressa 36.
Há chamados, prioridades, prazos e workaround em records.py/domain.py e testes/test_system.py. Isso não comprova equipe, atendimento remoto/presencial, garantia de 90 dias, manutenção preventiva/adaptativa/evolutiva ou prorrogação aceita pela fiscalização. Conferir a cláusula específica com contrato, calendário e evidências de operação. Tabela do PDF: crítico 2h/6h, alto 4h/8h úteis, médio 8h/24h úteis, baixo 24h/48h úteis.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.11.p36.19 — Operacional

A segurança dos arquivos relacionados com o Software é de responsabilidade de quem o opera. A CONTRATADA não se responsabiliza, apó s a disponibilização do Software, por erros decorrentes de negligência, imprudência ou imperícia da CONTRATANTE, seus empregados ou prepostos na sua utilização, assim como problemas provenientes de “caso fortuito” ou “força maior”, contemplados pelo art. 3 93 do Novo Código Civil Brasileiro. A má utilização das técnicas operacionais de trabalho, como operações indevidas de “BACKUPS” (anormalidade nos meios magnéticos - utilização de mídias defeituosas), ou que possam gerar resultados equivocados, ou, ainda, danos causados por “vírus” de computador, são de exclusiva responsabilidade da CONTRATANTE.

AUDITORIA 24/09/2026 — Cláusula 4.11, página impressa 36.
Há chamados, prioridades, prazos e workaround em records.py/domain.py e testes/test_system.py. Isso não comprova equipe, atendimento remoto/presencial, garantia de 90 dias, manutenção preventiva/adaptativa/evolutiva ou prorrogação aceita pela fiscalização. Conferir a cláusula específica com contrato, calendário e evidências de operação. Tabela do PDF: crítico 2h/6h, alto 4h/8h úteis, médio 8h/24h úteis, baixo 24h/48h úteis.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.12.p36.20 — Operacional

A tolerância da CONTRATADA no cumprimento pela CONTRATANTE dos itens e das condições do presente Contrato, não caracteriza novação, podendo a qualquer momento ser exigido seu rigoroso cumprimento.

AUDITORIA 24/09/2026 — Cláusula 4.12, página impressa 36.
Há chamados, prioridades, prazos e workaround em records.py/domain.py e testes/test_system.py. Isso não comprova equipe, atendimento remoto/presencial, garantia de 90 dias, manutenção preventiva/adaptativa/evolutiva ou prorrogação aceita pela fiscalização. Conferir a cláusula específica com contrato, calendário e evidências de operação. Tabela do PDF: crítico 2h/6h, alto 4h/8h úteis, médio 8h/24h úteis, baixo 24h/48h úteis.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.13.p36.21 — Operacional

A CONTRATANTE reconhece e aceita que o estado da técnica não permite a elaboração de programas de computador totalmente isentos de defeitos, reconhece, ademais, que a obrigação da CONTRATADA sob este Contrato consiste em ap licar seus melhores esforços na correção ou reparação dos defeitos ou deficiências de funcionamento apresentados pelo Software. O Software objeto deste contrato é garantido por 90 (noventa) dias contra defeitos de funcionamento, a partir 
da data da emissão da Nota Fiscal correspondente à cessão da Licença de Uso.

AUDITORIA 24/09/2026 — Cláusula 4.13, página impressa 36.
Há chamados, prioridades, prazos e workaround em records.py/domain.py e testes/test_system.py. Isso não comprova equipe, atendimento remoto/presencial, garantia de 90 dias, manutenção preventiva/adaptativa/evolutiva ou prorrogação aceita pela fiscalização. Conferir a cláusula específica com contrato, calendário e evidências de operação. Tabela do PDF: crítico 2h/6h, alto 4h/8h úteis, médio 8h/24h úteis, baixo 24h/48h úteis.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.14.p37.22 — Operacional

Em nenhuma hipótese a CONTRATADA será responsável por qualquer erro, má interpretação ou pela aplicação ou utilização inadequada do Software. A CONTRATADA tampouco será responsabilizada por qualque r dano emergente, lucro cessante ou outros danos diretos ou indiretos sofridos pela CONTRATANTE ou por terceiros, decorrentes do erro, má interpretação ou pela aplicação ou utilização inadequada do Software.

AUDITORIA 24/09/2026 — Cláusula 4.14, página impressa 37.
Há chamados, prioridades, prazos e workaround em records.py/domain.py e testes/test_system.py. Isso não comprova equipe, atendimento remoto/presencial, garantia de 90 dias, manutenção preventiva/adaptativa/evolutiva ou prorrogação aceita pela fiscalização. Conferir a cláusula específica com contrato, calendário e evidências de operação. Tabela do PDF: crítico 2h/6h, alto 4h/8h úteis, médio 8h/24h úteis, baixo 24h/48h úteis.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.15.p37.23 — Operacional

Prazos de Atendimento: CLASSIFICAÇÃO PRAZO DE RESPOSTA PRAZO DE SOLUÇÃO Crítico 2 horas 6 horas Alto 4 horas 8 horas úteis Médio 8 horas úteis 24 horas úteis Baixo 24 horas úteis 48 horas úteis

AUDITORIA 24/09/2026 — Cláusula 4.15, página impressa 37.
Há chamados, prioridades, prazos e workaround em records.py/domain.py e testes/test_system.py. Isso não comprova equipe, atendimento remoto/presencial, garantia de 90 dias, manutenção preventiva/adaptativa/evolutiva ou prorrogação aceita pela fiscalização. Conferir a cláusula específica com contrato, calendário e evidências de operação. Tabela do PDF: crítico 2h/6h, alto 4h/8h úteis, médio 8h/24h úteis, baixo 24h/48h úteis.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.16.p37.24 — Operacional

Em casos excepcionais, a solução poderá ser prorrogada mediante justificativa aceita pela fiscalização.

AUDITORIA 24/09/2026 — Cláusula 4.16, página impressa 37.
Há chamados, prioridades, prazos e workaround em records.py/domain.py e testes/test_system.py. Isso não comprova equipe, atendimento remoto/presencial, garantia de 90 dias, manutenção preventiva/adaptativa/evolutiva ou prorrogação aceita pela fiscalização. Conferir a cláusula específica com contrato, calendário e evidências de operação. Tabela do PDF: crítico 2h/6h, alto 4h/8h úteis, médio 8h/24h úteis, baixo 24h/48h úteis.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.17.p37.25 — Operacional

Quando não for possível solução imediata, deverá ser fornecida solução provisória (workaround).

AUDITORIA 24/09/2026 — Cláusula 4.17, página impressa 37.
Há chamados, prioridades, prazos e workaround em records.py/domain.py e testes/test_system.py. Isso não comprova equipe, atendimento remoto/presencial, garantia de 90 dias, manutenção preventiva/adaptativa/evolutiva ou prorrogação aceita pela fiscalização. Conferir a cláusula específica com contrato, calendário e evidências de operação. Tabela do PDF: crítico 2h/6h, alto 4h/8h úteis, médio 8h/24h úteis, baixo 24h/48h úteis.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.18.p37.26 — Operacional

Resumo dos Serviços Técnicos: CATEGORIA DESCRIÇÃO Manutenção Preventiva Inspeção, atualização de softwares básicos, limpeza, testes, relatórios. Manutenção Corretiva Correção de falhas, substituição de peças, reinstalação de sistemas, ajuste de desempenho, substituição emergencial. Suporte Técnico Atendimento remoto e presencial, instalação/configuração de softwares e periféricos, ajustes de rede. Exclusões Sistemas de terceiros, backups de usuários, softwares não homologados. Horário Regular Segunda a sexta, das 08h00 às 17h00. Horário Extraordinário Sábados, domingos, feriados e fora do horário regular, mediante solicitação prévia. Requisitos Temporais

AUDITORIA 24/09/2026 — Cláusula 4.18, página impressa 37.
Há chamados, prioridades, prazos e workaround em records.py/domain.py e testes/test_system.py. Isso não comprova equipe, atendimento remoto/presencial, garantia de 90 dias, manutenção preventiva/adaptativa/evolutiva ou prorrogação aceita pela fiscalização. Conferir a cláusula específica com contrato, calendário e evidências de operação. Tabela do PDF: crítico 2h/6h, alto 4h/8h úteis, médio 8h/24h úteis, baixo 24h/48h úteis.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.19.p37.27 — Operacional

Os serviços de Implantação dos SOFTWARES terão início na data seguinte da assinatura do contrato e deverão ser implantados em até 90 (noventa) dias, a contar da assinatura do contrato e emissão de ordem de serviço, podendo, excepcionalmente, por fatos supervenientes, ser este prazo prorrogado por mais 30 (trinta) dias.

AUDITORIA 24/09/2026 — Cláusula 4.19, página impressa 37.
Exigir migração das bases legadas com reconciliação e aceite, início após assinatura, módulos prioritários disponíveis em 30 dias, implantação em 90 dias e eventual prorrogação formal de 30 dias. Não foi apresentada prova de conversão integral, execução paralela e continuidade sem impacto. Cadastro de implantação/OS não comprova execução.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.20.p37.28 — Operacional

A implantação do sistema e migração dos dados deverá ser iniciado pelos módulos Orçamentários, Contábeis, Folha de Pagamento e Portal de Tran sparência. Estes necessitam estarem disponíveis nos primeiros 30 (trinta) dias. Após, serão alinhados todos os outros módulos em decisão conjunta com a comissão definida pela prefeitura. 

AUDITORIA 24/09/2026 — Cláusula 4.20, página impressa 37.
Exigir migração das bases legadas com reconciliação e aceite, início após assinatura, módulos prioritários disponíveis em 30 dias, implantação em 90 dias e eventual prorrogação formal de 30 dias. Não foi apresentada prova de conversão integral, execução paralela e continuidade sem impacto. Cadastro de implantação/OS não comprova execução.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.21.p38.29 — Operacional

Os serviços de reprocessamento, conversão e dos elementos, informaçõe s e dados necessários para sua execução. Devem ser convertidos os dados disponíveis nas bases de dados disponibilizadas pela Prefeitura.

AUDITORIA 24/09/2026 — Cláusula 4.21, página impressa 38.
Exigir migração das bases legadas com reconciliação e aceite, início após assinatura, módulos prioritários disponíveis em 30 dias, implantação em 90 dias e eventual prorrogação formal de 30 dias. Não foi apresentada prova de conversão integral, execução paralela e continuidade sem impacto. Cadastro de implantação/OS não comprova execução.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.22.p38.30 — Operacional

Durante a implantação dos sistemas, a contratada deverá prestar os serviços que abrangem as tarefas descritas neste ins trumento, que devem ser agrupadas em etapas e realizadas em paralelo, ou seja, sem interrupção e nenhum impacto inerente às funcionalidades dos setores ou departamentos dependentes do sistema de gestão atualmente utilizado pelo Município. Requisitos de Segurança e Privacidade

AUDITORIA 24/09/2026 — Cláusula 4.22, página impressa 38.
Exigir migração das bases legadas com reconciliação e aceite, início após assinatura, módulos prioritários disponíveis em 30 dias, implantação em 90 dias e eventual prorrogação formal de 30 dias. Não foi apresentada prova de conversão integral, execução paralela e continuidade sem impacto. Cadastro de implantação/OS não comprova execução.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.23.p38.31 — Parcial

Todas as atividades, processos e dados realizados e/ou desenvolvidos no âmbito do MUNICÍPIO, relacionados aos serviços, são estritamente confidenciais e estão protegidos pelo sigilo fiscal. Em conformidade com as leis e regulamentos pe rtinentes, a Contratante e seus funcionários são obrigados a manter essa informação sob sigilo absoluto.

AUDITORIA 24/09/2026 — Cláusula 4.23, página impressa 38.
AUD-004 | Prioridade Crítica | Consultas de pessoal sem permissão de módulo ou lotação
Constatação: Conta autenticada sem qualquer permissão recebeu 200 em employees, positions e sst/monitors. As consultas de people_api.py não exigem people/read, e get_work_locations ignora o parâmetro de entidade. A autenticação global não substitui autorização por lotação.
Correção/implementação necessária (NÃO EXECUTADA): Restringir todas as consultas de RH, SST e cadastro por módulo, entidade, lotação e titular; verificar também escrita e exportações.
Como comprovar o atendimento: Matriz de acessos negativos entre dois usuários, duas lotações e duas entidades, inclusive por ID direto, sem retorno de dados não autorizados.
Evidências: people_api.py:13 (list_employees); people_api.py:429 (list_monitors); people_core.py:57 (get_work_locations); artifacts/auditoria-20260924/probes.json.

AUD-035 | Prioridade Alta | Sigilo por especialidade e unidade não comprovado no novo módulo social
Constatação: A proteção social_confidential existe no ERP genérico, mas as novas rotas /api/social usam permissões amplas de módulo. Não foi demonstrada política por especialidade, unidade e profissional em toda consulta, histórico, alteração e exportação.
Correção/implementação necessária (NÃO EXECUTADA): Unificar a política de sigilo nos caminhos novos e antigos, com autorização do objeto e campos sensíveis.
Como comprovar o atendimento: Profissional de outra especialidade/unidade não acessa o registro por ID, busca, relatório ou histórico; acessos autorizados ficam auditados.
Evidências: erp_core.py:83 (confidential_sql); social_api.py; social_core.py:337 (get_family_details).
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.24.p38.32 — Parcial

Qualquer divulgação não autorizada dessas informações é considerada uma violação grave e constitui crime, sujeita a medidas legais rigorosas. A quebra de sigilo é passível de penalidades severas, conforme estabelecido por lei. A Contratante e seus funcionários estão proibidos de compartilhar, reproduzir ou divulgar, de qualquer forma, qualquer informação confidencial relacionada aos serviços prestados ao MUNICÍPIO.

AUDITORIA 24/09/2026 — Cláusula 4.24, página impressa 38.
Existem hash de senha, sessões, CSRF, controle de acesso e backup local criptografado. Os achados AUD-003, AUD-004, AUD-005, AUD-006, AUD-018, AUD-021 e AUD-035 impedem declaração global de segurança. Faltam comprovações operacionais de sigilo, transporte, armazenamento, descarte e devolução conforme cada cláusula; verificar contratos, políticas e execução.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.25.p38.33 — Parcial

Essa obrigação de sigilo permanece em vigor mesmo após o término do contrato entre a Contratante e o MUNICÍPIO. A divulgação não autorizada de informações confidenciais pode resultar em consequências legais significativas para a Contratante e para os indivíduos envolvidos.

AUDITORIA 24/09/2026 — Cláusula 4.25, página impressa 38.
Existem hash de senha, sessões, CSRF, controle de acesso e backup local criptografado. Os achados AUD-003, AUD-004, AUD-005, AUD-006, AUD-018, AUD-021 e AUD-035 impedem declaração global de segurança. Faltam comprovações operacionais de sigilo, transporte, armazenamento, descarte e devolução conforme cada cláusula; verificar contratos, políticas e execução.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.26.p38.34 — Parcial

Portanto, é imprescindível que a Contratante e seus funcionários compreendam a gravidade dessa questão e adiram estritamente a essa política de confidencialidade. A divulgação de informações confidenciais só é permitida median te autorização expressa e por escrito do MUNICÍPIO. O descumprimento desta política resultará em medidas legais imediatas e pode prejudicar seriamente a reputação da Contratante.

AUDITORIA 24/09/2026 — Cláusula 4.26, página impressa 38.
Existem hash de senha, sessões, CSRF, controle de acesso e backup local criptografado. Os achados AUD-003, AUD-004, AUD-005, AUD-006, AUD-018, AUD-021 e AUD-035 impedem declaração global de segurança. Faltam comprovações operacionais de sigilo, transporte, armazenamento, descarte e devolução conforme cada cláusula; verificar contratos, políticas e execução.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.27.p38.35 — Parcial

A Contratante e seus profissionais estão estritamente comprometidos em zelar pela segurança da informação, aderindo às melhores práticas do mercado, bem como às diretrizes e políticas de segurança estabelecidas pelo MUNICÍPIO. Este compromisso abrange todo o ciclo de vida da informação e/ou dados, incluindo sua fase de armazenament o, transporte, descarte e devolução.

AUDITORIA 24/09/2026 — Cláusula 4.27, página impressa 38.
AUD-018 | Prioridade Crítica | Segredo de pregão persistido em texto claro
Constatação: configure_platform grava o token diretamente na coluna client_token_enc. Reproduzido com marcador fictício: conteúdo persistido idêntico à entrada.
Correção/implementação necessária (NÃO EXECUTADA): Usar cofre criptográfico, acesso restrito, mascaramento e rotação também neste caminho alternativo de integração.
Como comprovar o atendimento: Banco e logs não contêm token em claro; a rotina de transporte consegue utilizá-lo apenas sob autorização.
Evidências: auction_core.py:71 (configure_platform); artifacts/auditoria-20260924/probes.json.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.28.p38.36 — Parcial

Caso exista a necessidade de armazenamento de arquivos, os dados e informações devem ser protegidos por medidas de segurança robustas, garantindo sua integridade e confidencialidade. Isso inclui a implementação de siste mas de proteção, controle de acesso restrito e criptografia, conforme necessário para prevenir acessos não autorizados e vazamentos.

AUDITORIA 24/09/2026 — Cláusula 4.28, página impressa 38.
AUD-004 | Prioridade Crítica | Consultas de pessoal sem permissão de módulo ou lotação
Constatação: Conta autenticada sem qualquer permissão recebeu 200 em employees, positions e sst/monitors. As consultas de people_api.py não exigem people/read, e get_work_locations ignora o parâmetro de entidade. A autenticação global não substitui autorização por lotação.
Correção/implementação necessária (NÃO EXECUTADA): Restringir todas as consultas de RH, SST e cadastro por módulo, entidade, lotação e titular; verificar também escrita e exportações.
Como comprovar o atendimento: Matriz de acessos negativos entre dois usuários, duas lotações e duas entidades, inclusive por ID direto, sem retorno de dados não autorizados.
Evidências: people_api.py:13 (list_employees); people_api.py:429 (list_monitors); people_core.py:57 (get_work_locations); artifacts/auditoria-20260924/probes.json.

AUD-018 | Prioridade Crítica | Segredo de pregão persistido em texto claro
Constatação: configure_platform grava o token diretamente na coluna client_token_enc. Reproduzido com marcador fictício: conteúdo persistido idêntico à entrada.
Correção/implementação necessária (NÃO EXECUTADA): Usar cofre criptográfico, acesso restrito, mascaramento e rotação também neste caminho alternativo de integração.
Como comprovar o atendimento: Banco e logs não contêm token em claro; a rotina de transporte consegue utilizá-lo apenas sob autorização.
Evidências: auction_core.py:71 (configure_platform); artifacts/auditoria-20260924/probes.json.

AUD-035 | Prioridade Alta | Sigilo por especialidade e unidade não comprovado no novo módulo social
Constatação: A proteção social_confidential existe no ERP genérico, mas as novas rotas /api/social usam permissões amplas de módulo. Não foi demonstrada política por especialidade, unidade e profissional em toda consulta, histórico, alteração e exportação.
Correção/implementação necessária (NÃO EXECUTADA): Unificar a política de sigilo nos caminhos novos e antigos, com autorização do objeto e campos sensíveis.
Como comprovar o atendimento: Profissional de outra especialidade/unidade não acessa o registro por ID, busca, relatório ou histórico; acessos autorizados ficam auditados.
Evidências: erp_core.py:83 (confidential_sql); social_api.py; social_core.py:337 (get_family_details).
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.29.p38.37 — Parcial

No que diz respeito ao transporte, devem ser adotadas práticas seguras para evitar interceptações ou perdas durante a trans ferência de dados. Utilizar métodos de comunicação segura e redes protegidas são essenciais para proteger a informação durante seu trânsito entre diferentes locais ou sistemas.

AUDITORIA 24/09/2026 — Cláusula 4.29, página impressa 38.
AUD-021 | Prioridade Alta | HTTPS e acesso externo não comprovados na instalação local
Constatação: A instalação examinada está em http://127.0.0.1:8080 e informa ambiente Local. SECURE_COOKIE/HSTS condicionais não provisionam TLS nem acesso por computador fora da rede.
Correção/implementação necessária (NÃO EXECUTADA): Implantar endpoint HTTPS institucional e testar o acesso externo aos produtos, com certificado válido, redirecionamento e configuração segura de cookies.
Como comprovar o atendimento: Acesso real de rede externa e validação TLS de todos os produtos; nenhuma alegação de TLS 1.3 somente por existência de cabeçalhos.
Evidências: app.py:22 (SECURE_COOKIE); artifacts/auditoria-20260924/browser.json.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.30.p38.38 — Parcial

Para a fase de descarte, é fundamental seguir procedimentos adequados para assegurar a eliminação segura de dados e informações. Métodos de descarte seguros, como a destruição física de mídias ou a utilização de software especializado de eliminação de dados, são essenciais para 
prevenir qualquer possibilidade de recuperação indevida de informações sensíveis.

AUDITORIA 24/09/2026 — Cláusula 4.30, página impressa 38.
Existem hash de senha, sessões, CSRF, controle de acesso e backup local criptografado. Os achados AUD-003, AUD-004, AUD-005, AUD-006, AUD-018, AUD-021 e AUD-035 impedem declaração global de segurança. Faltam comprovações operacionais de sigilo, transporte, armazenamento, descarte e devolução conforme cada cláusula; verificar contratos, políticas e execução.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.31.p39.39 — Parcial

Quando se trata da devolução de equipamentos ou dados ao MUNICÍPIO, é necessário garantir que todos os dados e informações tenham sido removidos completamente dos dispositivos, para evitar qualquer risco de vazamento ou acesso não autorizado após a devolução.

AUDITORIA 24/09/2026 — Cláusula 4.31, página impressa 39.
Existem hash de senha, sessões, CSRF, controle de acesso e backup local criptografado. Os achados AUD-003, AUD-004, AUD-005, AUD-006, AUD-018, AUD-021 e AUD-035 impedem declaração global de segurança. Faltam comprovações operacionais de sigilo, transporte, armazenamento, descarte e devolução conforme cada cláusula; verificar contratos, políticas e execução.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.32.p39.40 — Parcial

Essas práticas, alinhadas às políticas de segurança do MUNICÍPIO, não apenas garantem a proteção da informação, mas também demonstram o comprometimento da Empresa e de seus profissionais com a integridade e a confidencialidade dos dados. Ao aderir a esses padrões elevados de segurança da informação, contribuímos para um ambiente digital seguro e protegido contra ameaças, promovendo a confiança e a segurança de todos os envolvidos. Requisitos Sociais, Ambientais e Culturais

AUDITORIA 24/09/2026 — Cláusula 4.32, página impressa 39.
AUD-018 | Prioridade Crítica | Segredo de pregão persistido em texto claro
Constatação: configure_platform grava o token diretamente na coluna client_token_enc. Reproduzido com marcador fictício: conteúdo persistido idêntico à entrada.
Correção/implementação necessária (NÃO EXECUTADA): Usar cofre criptográfico, acesso restrito, mascaramento e rotação também neste caminho alternativo de integração.
Como comprovar o atendimento: Banco e logs não contêm token em claro; a rotina de transporte consegue utilizá-lo apenas sob autorização.
Evidências: auction_core.py:71 (configure_platform); artifacts/auditoria-20260924/probes.json.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.33.p39.41 — Não comprovado

A so lução deverá atender a requisitos sociais, ambientais e culturais, garantindo acessibilidade digital conforme normas vigentes, inclusão de usuários com diferentes níveis de letramento digital e conformidade com a legislação de proteção de dados pessoais, especialmente a LGPD.

AUDITORIA 24/09/2026 — Cláusula 4.33, página impressa 39.
Interface em português e recursos responsivos existentes. Não foi executada avaliação completa de acessibilidade com tecnologias assistivas, diferentes perfis de usuário, inclusão, adequação institucional e sustentabilidade. Registrar critérios, resultados e correções necessárias por tela.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.34.p39.42 — Não comprovado

Deverá ainda observar princípios de sustentabilidade, priorizando eficiência no uso de recursos computacionais, redução de consumo energético e incentivo à digitalização de processos.

AUDITORIA 24/09/2026 — Cláusula 4.34, página impressa 39.
Interface em português e recursos responsivos existentes. Não foi executada avaliação completa de acessibilidade com tecnologias assistivas, diferentes perfis de usuário, inclusão, adequação institucional e sustentabilidade. Registrar critérios, resultados e correções necessárias por tela.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.35.p39.43 — Não comprovado

No aspecto cultural, a solução deverá estar adequad a ao contexto organizacional e local, contemplando idioma português (Brasil), usabilidade intuitiva, respeito à diversidade e possibilidade de parametrização conforme necessidades institucionais. Requisitos da Arquitetura Tecnológica

AUDITORIA 24/09/2026 — Cláusula 4.35, página impressa 39.
Interface em português e recursos responsivos existentes. Não foi executada avaliação completa de acessibilidade com tecnologias assistivas, diferentes perfis de usuário, inclusão, adequação institucional e sustentabilidade. Registrar critérios, resultados e correções necessárias por tela.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.36.p39.44 — Parcial

Requisitos obrigatórios:

AUDITORIA 24/09/2026 — Cláusula 4.36, página impressa 39.
AUD-048 | Prioridade Média | Políticas de senha e bloqueio não têm toda a parametrização pedida
Constatação: check_password aceita somente nível Forte. max_attempts/lock_minutes são globais em settings, embora o PDF mencione bloqueio com período definido por usuário. Classificação visual não comprova os três níveis configuráveis exigidos.
Correção/implementação necessária (NÃO EXECUTADA): Resolver a aderência da política de níveis e parametrização por usuário com a contratante, preservando segurança e formalizando a regra aceita.
Como comprovar o atendimento: Demonstrar as configurações previstas ou aceite formal da divergência; comprovar bloqueio, troca obrigatória e invalidação de sessões por usuário.
Evidências: auth.py:18 (check_password); auth.py:92 (login); db.py:9 (DEFAULTS).
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.36.1.p39.45 — Parcial

Prover recurso para utilização da senha do usuário, dispondo de níveis de segurança, divididos nos níveis Fraca (contendo apenas caracteres alfanuméricos), Média (número total de caracteres da senha maior que 8, contendo caracteres especiais, alfanuméricos e números) e Forte (número total de caracteres da senha superior a 10, contendo mais do que 1 caractere especial, alfanuméricos e números). Também deve impor uma quantidade mínima de caracteres da senha, sendo esta configuração flexível em termos de uso e da quantidade de caracteres.

AUDITORIA 24/09/2026 — Cláusula 4.36.1, página impressa 39.
AUD-048 | Prioridade Média | Políticas de senha e bloqueio não têm toda a parametrização pedida
Constatação: check_password aceita somente nível Forte. max_attempts/lock_minutes são globais em settings, embora o PDF mencione bloqueio com período definido por usuário. Classificação visual não comprova os três níveis configuráveis exigidos.
Correção/implementação necessária (NÃO EXECUTADA): Resolver a aderência da política de níveis e parametrização por usuário com a contratante, preservando segurança e formalizando a regra aceita.
Como comprovar o atendimento: Demonstrar as configurações previstas ou aceite formal da divergência; comprovar bloqueio, troca obrigatória e invalidação de sessões por usuário.
Evidências: auth.py:18 (check_password); auth.py:92 (login); db.py:9 (DEFAULTS).
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.37.p39.46 — Não comprovado

As aplicações devem disponibilizar ao usuário acesso fácil a uma funcionalidade de ajuda online, acessível a partir de qualquer tela da aplicação. O mesmo deve apresentar informações e orientações sobre o uso das funcionalidades existentes na tela exibida.

AUDITORIA 24/09/2026 — Cláusula 4.37, página impressa 39.
Conferir o requisito transversal integralmente. A matriz antiga possui evidência parcial preservada abaixo; os novos módulos não herdam automaticamente controles dos cadastros antigos. Verificar principalmente permissão por ação, dupla custódia, histórico de todas as operações, ajuda contextual, atualização automática, impressão e assinatura por relatório. Achados gerais AUD-002, AUD-003, AUD-004, AUD-046 e AUD-048.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.38.p39.47 — Parcial

O sistema deverá ser acessível a partir de qualquer dispositivo com conexão à Internet.

AUDITORIA 24/09/2026 — Cláusula 4.38, página impressa 39.
AUD-021 | Prioridade Alta | HTTPS e acesso externo não comprovados na instalação local
Constatação: A instalação examinada está em http://127.0.0.1:8080 e informa ambiente Local. SECURE_COOKIE/HSTS condicionais não provisionam TLS nem acesso por computador fora da rede.
Correção/implementação necessária (NÃO EXECUTADA): Implantar endpoint HTTPS institucional e testar o acesso externo aos produtos, com certificado válido, redirecionamento e configuração segura de cookies.
Como comprovar o atendimento: Acesso real de rede externa e validação TLS de todos os produtos; nenhuma alegação de TLS 1.3 somente por existência de cabeçalhos.
Evidências: app.py:22 (SECURE_COOKIE); artifacts/auditoria-20260924/browser.json.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.39.p39.48 — Parcial

Prover o bloqueio do acesso de um usuário a aplicação, após determinado número de tentativas de ações inválidas, com a definição de período de tempo determinado para bloqueio do acesso, por usuário. Também deverá prover recurso exigindo a troca da senha, no próximo acesso do usuário, a aplicação.

AUDITORIA 24/09/2026 — Cláusula 4.39, página impressa 39.
AUD-048 | Prioridade Média | Políticas de senha e bloqueio não têm toda a parametrização pedida
Constatação: check_password aceita somente nível Forte. max_attempts/lock_minutes são globais em settings, embora o PDF mencione bloqueio com período definido por usuário. Classificação visual não comprova os três níveis configuráveis exigidos.
Correção/implementação necessária (NÃO EXECUTADA): Resolver a aderência da política de níveis e parametrização por usuário com a contratante, preservando segurança e formalizando a regra aceita.
Como comprovar o atendimento: Demonstrar as configurações previstas ou aceite formal da divergência; comprovar bloqueio, troca obrigatória e invalidação de sessões por usuário.
Evidências: auth.py:18 (check_password); auth.py:92 (login); db.py:9 (DEFAULTS).
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.40.p39.49 — Não comprovado

Prover a definição de um período de tempo determinado, sendo este a definição dos dias da semana e períodos de horários para acesso a aplicação por usuário, bloqueando seu acesso ao sistema nos demais períodos. 

AUDITORIA 24/09/2026 — Cláusula 4.40, página impressa 39.
Conferir o requisito transversal integralmente. A matriz antiga possui evidência parcial preservada abaixo; os novos módulos não herdam automaticamente controles dos cadastros antigos. Verificar principalmente permissão por ação, dupla custódia, histórico de todas as operações, ajuda contextual, atualização automática, impressão e assinatura por relatório. Achados gerais AUD-002, AUD-003, AUD-004, AUD-046 e AUD-048.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.41.p40.50 — Não comprovado

Prover recurso de agrupamento de usuários, no qual seja possível gerenciar de forma única as permissões vinculadas a um determinado usuário, ou um grupo deles.

AUDITORIA 24/09/2026 — Cláusula 4.41, página impressa 40.
Conferir o requisito transversal integralmente. A matriz antiga possui evidência parcial preservada abaixo; os novos módulos não herdam automaticamente controles dos cadastros antigos. Verificar principalmente permissão por ação, dupla custódia, histórico de todas as operações, ajuda contextual, atualização automática, impressão e assinatura por relatório. Achados gerais AUD-002, AUD-003, AUD-004, AUD-046 e AUD-048.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.42.p40.51 — Parcial

Prover recurso de dupla custódia quando o acesso a uma determinada funcionalidade ou ações de exclusão, inclusão e alteração, dentro dela necessitam da autorização de outrem, utilizando o conceito de usuário ou grupo autorizador.

AUDITORIA 24/09/2026 — Cláusula 4.42, página impressa 40.
AUD-003 | Prioridade Crítica | Permissão de consulta permite gravação financeira
Constatação: Reprodução com conta temporária finance:[read], sem write: POST /api/finance/rules retornou 201 e persistiu regra. O decorador require_auth verifica somente finance/read, inclusive em várias rotas POST. Não equivale à dupla custódia dos cadastros administrativos antigos.
Correção/implementação necessária (NÃO EXECUTADA): Aplicar autorização por ação, entidade e operação financeira; garantir aprovação independente quando configurada e registrar autoria real.
Como comprovar o atendimento: Leitores recebem 403 em toda mutação; nenhuma linha é alterada; autores não aprovam as próprias operações.
Evidências: finance_api.py:10 (require_auth); finance_api.py:55 (handle_rules); artifacts/auditoria-20260924/probes.json.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.43.p40.52 — Parcial

Prover atribuição, para um usuário individualmente ou grupo de usuários, um conjunto de permissões específicas para executar as ações de gravar, consultar e excluir dados, configurações de dupla custódia, para todas as funções que contemplem entrada de dados.

AUDITORIA 24/09/2026 — Cláusula 4.43, página impressa 40.
AUD-003 | Prioridade Crítica | Permissão de consulta permite gravação financeira
Constatação: Reprodução com conta temporária finance:[read], sem write: POST /api/finance/rules retornou 201 e persistiu regra. O decorador require_auth verifica somente finance/read, inclusive em várias rotas POST. Não equivale à dupla custódia dos cadastros administrativos antigos.
Correção/implementação necessária (NÃO EXECUTADA): Aplicar autorização por ação, entidade e operação financeira; garantir aprovação independente quando configurada e registrar autoria real.
Como comprovar o atendimento: Leitores recebem 403 em toda mutação; nenhuma linha é alterada; autores não aprovam as próprias operações.
Evidências: finance_api.py:10 (require_auth); finance_api.py:55 (handle_rules); artifacts/auditoria-20260924/probes.json.

AUD-004 | Prioridade Crítica | Consultas de pessoal sem permissão de módulo ou lotação
Constatação: Conta autenticada sem qualquer permissão recebeu 200 em employees, positions e sst/monitors. As consultas de people_api.py não exigem people/read, e get_work_locations ignora o parâmetro de entidade. A autenticação global não substitui autorização por lotação.
Correção/implementação necessária (NÃO EXECUTADA): Restringir todas as consultas de RH, SST e cadastro por módulo, entidade, lotação e titular; verificar também escrita e exportações.
Como comprovar o atendimento: Matriz de acessos negativos entre dois usuários, duas lotações e duas entidades, inclusive por ID direto, sem retorno de dados não autorizados.
Evidências: people_api.py:13 (list_employees); people_api.py:429 (list_monitors); people_core.py:57 (get_work_locations); artifacts/auditoria-20260924/probes.json.

AUD-035 | Prioridade Alta | Sigilo por especialidade e unidade não comprovado no novo módulo social
Constatação: A proteção social_confidential existe no ERP genérico, mas as novas rotas /api/social usam permissões amplas de módulo. Não foi demonstrada política por especialidade, unidade e profissional em toda consulta, histórico, alteração e exportação.
Correção/implementação necessária (NÃO EXECUTADA): Unificar a política de sigilo nos caminhos novos e antigos, com autorização do objeto e campos sensíveis.
Como comprovar o atendimento: Profissional de outra especialidade/unidade não acessa o registro por ID, busca, relatório ou histórico; acessos autorizados ficam auditados.
Evidências: erp_core.py:83 (confidential_sql); social_api.py; social_core.py:337 (get_family_details).
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.44.p40.53 — Não comprovado

Registrar em arquivo de auditoria as tentativas de login efetuadas com sucesso, bem como as que não obtiveram sucesso, registrando um conjunto de informações sobre data, hora e o usuário.

AUDITORIA 24/09/2026 — Cláusula 4.44, página impressa 40.
Conferir o requisito transversal integralmente. A matriz antiga possui evidência parcial preservada abaixo; os novos módulos não herdam automaticamente controles dos cadastros antigos. Verificar principalmente permissão por ação, dupla custódia, histórico de todas as operações, ajuda contextual, atualização automática, impressão e assinatura por relatório. Achados gerais AUD-002, AUD-003, AUD-004, AUD-046 e AUD-048.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.45.p40.54 — Parcial

Realizar a validação dos dados digitados em um campo de um formulário, no momento da inclusão ou alteração de dados, no mesmo instante em que os mesmos estiverem sendo informados.

AUDITORIA 24/09/2026 — Cláusula 4.45, página impressa 40.
AUD-002 | Prioridade Crítica | Ações das telas bloqueadas pela política CSP
Constatação: Chromium: clicar nas abas de Finanças, Social e BI mantém a aba anterior e gera violação script-src-attr. Há controles onclick também em Pessoas e Controle Interno. O servidor permite scripts de mesma origem, mas não manipuladores inline. Testes de API não exercitam esse bloqueio.
Correção/implementação necessária (NÃO EXECUTADA): Vincular os eventos das telas por JavaScript compatível com a CSP e verificar os fluxos pela interface. Não desativar a proteção como substituto da correção.
Como comprovar o atendimento: Navegar e executar inclusões, alterações, consultas e relatórios nos cinco módulos sem violações CSP, com os respectivos perfis.
Evidências: app.py:74 (Content-Security-Policy); static/finance-ui.js; static/social-ui.js; static/bi-ui.js; artifacts/auditoria-20260924/browser.json.

AUD-046 | Prioridade Alta | Novas telas enviam POST sem token CSRF
Constatação: Os helpers/fetch de Pessoas, Finanças, Social e BI enviam JSON sem X-CSRF-Token em operações protegidas. A autenticação global exige o token; portanto, além do bloqueio CSP, esses fluxos têm impedimento adicional para gravar.
Correção/implementação necessária (NÃO EXECUTADA): Usar o cliente autenticado comum e tratar respostas de erro antes de informar sucesso, conservando a proteção CSRF.
Como comprovar o atendimento: Após resolver os eventos, cada operação pela tela envia token válido, grava quando autorizada e exibe falhas reais sem falso sucesso.
Evidências: static/people-ui.js:17 (async function apiCall); static/finance-ui.js:474 (fetch('/api/finance/journal/post'); static/social-ui.js:587 (fetch('/api/social/rma/cras/close'); static/bi-ui.js:807 (fetch('/api/bi/share'); auth.py:71 (X-CSRF-Token).
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.46.p40.55 — Não comprovado

Prover a atualização dos sistemas nas estações dos usuários finais de forma automática, transparente, a partir de um servidor.

AUDITORIA 24/09/2026 — Cláusula 4.46, página impressa 40.
Conferir o requisito transversal integralmente. A matriz antiga possui evidência parcial preservada abaixo; os novos módulos não herdam automaticamente controles dos cadastros antigos. Verificar principalmente permissão por ação, dupla custódia, histórico de todas as operações, ajuda contextual, atualização automática, impressão e assinatura por relatório. Achados gerais AUD-002, AUD-003, AUD-004, AUD-046 e AUD-048.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.47.p40.56 — Não comprovado

Prover que sejam configurados atalhos para ferramentas externas, para serem acessadas diretamente pelo sistema. Esses atalhos devem ser configurados pelo usuário, através de mecanismo flexível disponível no sistema.

AUDITORIA 24/09/2026 — Cláusula 4.47, página impressa 40.
Conferir o requisito transversal integralmente. A matriz antiga possui evidência parcial preservada abaixo; os novos módulos não herdam automaticamente controles dos cadastros antigos. Verificar principalmente permissão por ação, dupla custódia, histórico de todas as operações, ajuda contextual, atualização automática, impressão e assinatura por relatório. Achados gerais AUD-002, AUD-003, AUD-004, AUD-046 e AUD-048.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.48.p40.57 — Não comprovado

Disponibilizar recurso no sistema onde seja re alizada a execução de comandos de manutenção de dados (scripts) sem a necessidade de acessar diretamente o sistema de gerenciamento de banco de dados, e que esses scripts sejam criptografados.

AUDITORIA 24/09/2026 — Cláusula 4.48, página impressa 40.
Conferir o requisito transversal integralmente. A matriz antiga possui evidência parcial preservada abaixo; os novos módulos não herdam automaticamente controles dos cadastros antigos. Verificar principalmente permissão por ação, dupla custódia, histórico de todas as operações, ajuda contextual, atualização automática, impressão e assinatura por relatório. Achados gerais AUD-002, AUD-003, AUD-004, AUD-046 e AUD-048.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.49.p40.58 — Não comprovado

Prover a visualização de relatórios em tela, possibilitando que os mesmos sejam salvos em disco para posterior reimpressão, distribuição pela rede, inclusive permitindo selecionar a impressão de intervalos de páginas e o número de cópias a serem impressas, além de também permitir a seleção da impressora de rede desejada.

AUDITORIA 24/09/2026 — Cláusula 4.49, página impressa 40.
Conferir o requisito transversal integralmente. A matriz antiga possui evidência parcial preservada abaixo; os novos módulos não herdam automaticamente controles dos cadastros antigos. Verificar principalmente permissão por ação, dupla custódia, histórico de todas as operações, ajuda contextual, atualização automática, impressão e assinatura por relatório. Achados gerais AUD-002, AUD-003, AUD-004, AUD-046 e AUD-048.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.50.p40.59 — Parcial

Prover o registro do histórico de acessos às funcionalidades do sistema por usuário, registrando o momento em que ela aconteceu (data/hora), o nome do usuário e detalhes de ações efetuadas (inclusão, alteração e exclusão).

AUDITORIA 24/09/2026 — Cláusula 4.50, página impressa 40.
AUD-003 | Prioridade Crítica | Permissão de consulta permite gravação financeira
Constatação: Reprodução com conta temporária finance:[read], sem write: POST /api/finance/rules retornou 201 e persistiu regra. O decorador require_auth verifica somente finance/read, inclusive em várias rotas POST. Não equivale à dupla custódia dos cadastros administrativos antigos.
Correção/implementação necessária (NÃO EXECUTADA): Aplicar autorização por ação, entidade e operação financeira; garantir aprovação independente quando configurada e registrar autoria real.
Como comprovar o atendimento: Leitores recebem 403 em toda mutação; nenhuma linha é alterada; autores não aprovam as próprias operações.
Evidências: finance_api.py:10 (require_auth); finance_api.py:55 (handle_rules); artifacts/auditoria-20260924/probes.json.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.51.p40.60 — Não comprovado

Disponibilizar recurso para que seja configurado nos relatórios o uso da assinatura digital, de forma individual em cada relatório ou em todos de uma só vez.

AUDITORIA 24/09/2026 — Cláusula 4.51, página impressa 40.
Conferir o requisito transversal integralmente. A matriz antiga possui evidência parcial preservada abaixo; os novos módulos não herdam automaticamente controles dos cadastros antigos. Verificar principalmente permissão por ação, dupla custódia, histórico de todas as operações, ajuda contextual, atualização automática, impressão e assinatura por relatório. Achados gerais AUD-002, AUD-003, AUD-004, AUD-046 e AUD-048.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.52.p40.61 — Não comprovado

Disponibilizar recurso para acionamento de suporte técnico através da inclusão de chamados bem como o acompanhamento da evolução dos mesmos a partir dos próprios produtos / softwares utilizados pelos usuários (sem acesso a ferramenta externa para tal). Também deverá ter recurso de notificação ao usuário quando houver evolução de situação do chamado.

AUDITORIA 24/09/2026 — Cláusula 4.52, página impressa 40.
Conferir o requisito transversal integralmente. A matriz antiga possui evidência parcial preservada abaixo; os novos módulos não herdam automaticamente controles dos cadastros antigos. Verificar principalmente permissão por ação, dupla custódia, histórico de todas as operações, ajuda contextual, atualização automática, impressão e assinatura por relatório. Achados gerais AUD-002, AUD-003, AUD-004, AUD-046 e AUD-048.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.53.p40.62 — Dependência externa

Hospedagem em Nuvem:

AUDITORIA 24/09/2026 — Cláusula 4.53, página impressa 40.
Comprovar infraestrutura real, SSD, latência, redundância geográfica, segurança, continuidade e SLA no provedor contratado. AUD-019 a AUD-025 demonstram por que tabelas/indicadores simulados não servem como evidência.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.53.1.p40.63 — Dependência externa

A hospedagem em datacenter ou nuvem facilita de forma imediata a vida dos usuários e gestores de TI, não sendo à toa que essa tecnologia passou de uma tendência para uma realidade concreta em poucos anos, sendo utilizada no mercado em todos os segmentos. Nesse passo, não se trata do objeto ou do serviço, mas apenas do ambiente em que este será disponibilizado ao ente 
contratante, daí ser uma obrigação implícita de funcionamento dos sistemas;

AUDITORIA 24/09/2026 — Cláusula 4.53.1, página impressa 40.
Comprovar infraestrutura real, SSD, latência, redundância geográfica, segurança, continuidade e SLA no provedor contratado. AUD-019 a AUD-025 demonstram por que tabelas/indicadores simulados não servem como evidência.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.53.2.p41.64 — Dependência externa

Através da tecnologia de armazenamento em nuvem, com comodidade e a segurança, o órgão público reduz os custos com investimento em hardware para o armazenamento de dados e manutenção;

AUDITORIA 24/09/2026 — Cláusula 4.53.2, página impressa 41.
Comprovar infraestrutura real, SSD, latência, redundância geográfica, segurança, continuidade e SLA no provedor contratado. AUD-019 a AUD-025 demonstram por que tabelas/indicadores simulados não servem como evidência.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.53.3.p41.65 — Dependência externa

A exigência em referência, na realidade, trata do ambiente de utilização do objeto e visa apenas garantir a segurança e integridade dos da dos dos softwares licitados. Assim, os mesmos apenas terão uma proteção e disponibilidade de armazenamento, evitando que algum vírus ou pane traga a suspensão dos trabalhos ou perda de dados;

AUDITORIA 24/09/2026 — Cláusula 4.53.3, página impressa 41.
Comprovar infraestrutura real, SSD, latência, redundância geográfica, segurança, continuidade e SLA no provedor contratado. AUD-019 a AUD-025 demonstram por que tabelas/indicadores simulados não servem como evidência.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.53.4.p41.66 — Dependência externa

A solução licitada funcionará armazenando dados do município e informações, muitas delas inclusive sigilosas. Por isso, mostra -se imperioso garantir a segurança destes. E, de modo completamente abrangente e não intencionando qualquer restrição;

AUDITORIA 24/09/2026 — Cláusula 4.53.4, página impressa 41.
Comprovar infraestrutura real, SSD, latência, redundância geográfica, segurança, continuidade e SLA no provedor contratado. AUD-019 a AUD-025 demonstram por que tabelas/indicadores simulados não servem como evidência.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.53.5.p41.67 — Parcial

Feito esse importante esclarecimento, vale destacar, ainda, que, tecnicamente e na prática já se comprovou que a alta disponibilidade com redundância geográfica compatível com SLA é o meio adequado para se otimizar o desempenho e as taxas de transmissão na operação de objetos dessa natureza, já que serão demandados volumes de armazenamento que suportem mídias SSD (solid state drive) com o intuito de se alcançar latências da ordem de milissegundos;

AUDITORIA 24/09/2026 — Cláusula 4.53.5, página impressa 41.
AUD-019 | Prioridade Crítica | Datacenters e recuperação geográfica são registros simulados
Constatação: init_cloud_db insere DC-RJ/DC-SP fictícios; simulate_dr_failover apenas inverte flags SQL e retorna RTO/RPO fixos. Não comprova residência selecionável, replicação ou snapshot entre regiões.
Correção/implementação necessária (NÃO EXECUTADA): Provisionar e comprovar provedor, regiões, residência dos dados, serviço relacional, cópias entre regiões e recuperação real.
Como comprovar o atendimento: Inventário do provedor e exercício de restauração/failover com dados conhecidos, tempos medidos e evidência de independência regional.
Evidências: cloud_core.py:13 (init_cloud_db); cloud_core.py:173 (simulate_dr_failover).
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.54.p41.68 — Operacional

Evolução Tecnológica.

AUDITORIA 24/09/2026 — Cláusula 4.54, página impressa 41.
Obrigação contratual/documental: comprovar equipe qualificada, assessoria, manutenção/evolução, OS, atendimento, sustentabilidade e condições de subcontratação conforme o texto exato. Ausência de carta de solidariedade em 4.65 é dispensa documental, não funcionalidade faltante. Subcontratação: observar limite de 25% e autorização expressa indicados no PDF. Ao fim da implantação, 100% dos requisitos devem estar atendidos.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.54.1.p41.69 — Operacional

Sempre que houver uma evolução tecnológica no sistema, a CONTRATADA deverá realizar o aprimoramento técnico sem custos para a CONTRATANTE. Requisitos de Projeto e de Implementação

AUDITORIA 24/09/2026 — Cláusula 4.54.1, página impressa 41.
Obrigação contratual/documental: comprovar equipe qualificada, assessoria, manutenção/evolução, OS, atendimento, sustentabilidade e condições de subcontratação conforme o texto exato. Ausência de carta de solidariedade em 4.65 é dispensa documental, não funcionalidade faltante. Subcontratação: observar limite de 25% e autorização expressa indicados no PDF. Ao fim da implantação, 100% dos requisitos devem estar atendidos.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.55.p41.70 — Operacional

Conforme detalhado neste Termo de Referência. Requisitos de Implantação

AUDITORIA 24/09/2026 — Cláusula 4.55, página impressa 41.
Obrigação contratual/documental: comprovar equipe qualificada, assessoria, manutenção/evolução, OS, atendimento, sustentabilidade e condições de subcontratação conforme o texto exato. Ausência de carta de solidariedade em 4.65 é dispensa documental, não funcionalidade faltante. Subcontratação: observar limite de 25% e autorização expressa indicados no PDF. Ao fim da implantação, 100% dos requisitos devem estar atendidos.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.56.p41.71 — Operacional

Os requisitos pertencentes às categorias para as quais este Termo de Referência e o Anexo III – Prova de Conceito estabeleçam percentual mínimo de atendimento inferior a 100% (cem por cento), eventualmente não demonstrados pela licitante durante a Prova de Conceito, observado o percentual máximo de não atendimento admitido, deverão ser desenvolvidos, parametr izados, implantados, testados e disponibilizados em perfeito funcionamento pela CONTRATADA dentro dos respectivos prazos de implantação estabelecidos no tópico “Requisitos Temporais” deste Termo de Referência.

AUDITORIA 24/09/2026 — Cláusula 4.56, página impressa 41.
Obrigação contratual/documental: comprovar equipe qualificada, assessoria, manutenção/evolução, OS, atendimento, sustentabilidade e condições de subcontratação conforme o texto exato. Ausência de carta de solidariedade em 4.65 é dispensa documental, não funcionalidade faltante. Subcontratação: observar limite de 25% e autorização expressa indicados no PDF. Ao fim da implantação, 100% dos requisitos devem estar atendidos.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.56.1.p41.72 — Parcial

Ao término do prazo de implantação do respecti vo módulo ou solução, será exigido o atendimento integral de 100% (cem por cento) dos requisitos previstos neste Termo de Referência, inclusive daqueles cuja demonstração tenha sido dispensada em razão do percentual mínimo de atendimento admitido na Prova de Conceito.

AUDITORIA 24/09/2026 — Cláusula 4.56.1, página impressa 41.
AUD-001 | Prioridade Crítica | Declaração de 100% sem sustentação e indicador incompatível com a POC
Constatação: A matriz anterior classificava 1.314/1.314 como Implementado. Scripts de atualização promovem faixas inteiras sem verificar os subitens; há referências sem relação com o requisito (ex.: cloud.2 cita SLA em vez das nove certificações). A tela soma Implementado + 50% de Parcial. Os itens 4.77, 4.79.2, 4.80.1 e 4.80.2 exigem avaliação individual e integral de cada item, 90% por módulo e 100% em nuvem.
Correção/implementação necessária (NÃO EXECUTADA): Substituir futuramente os geradores que promovem requisitos automaticamente por evidências de aceitação por item; adequar o indicador à regra documental, sem crédito para subitem incompleto. Esta auditoria apenas registra a pendência; o cálculo da interface foi preservado.
Como comprovar o atendimento: Vincular cada resultado a roteiro executado, evidência e todos os subitens. Calcular por categoria, sem misturar obrigações do edital e achados de auditoria no denominador.
Evidências: tools/update_final_compliance.py; tools/update_finance_compliance.py; tools/update_social_compliance.py; static/annex-ui.js:41 (function annexStats).
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.56.2.p41.73 — Operacional

Não será admitida a implementação dos requisitos remanescentes em prazo posterior ao estabelecido para a implantação do respectivo módulo ou solução, ressalvada exclusivamente a hipótese de prorrogação do prazo de implantação expressamente pre vista neste Termo de Referência. Requisitos de Experiência Profissional 

AUDITORIA 24/09/2026 — Cláusula 4.56.2, página impressa 41.
Obrigação contratual/documental: comprovar equipe qualificada, assessoria, manutenção/evolução, OS, atendimento, sustentabilidade e condições de subcontratação conforme o texto exato. Ausência de carta de solidariedade em 4.65 é dispensa documental, não funcionalidade faltante. Subcontratação: observar limite de 25% e autorização expressa indicados no PDF. Ao fim da implantação, 100% dos requisitos devem estar atendidos.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.57.p42.74 — Operacional

Os serviços de assistência técnica e suporte deverão ser prestados por técnicos devidamente capacitados nos produtos em questão, bem como com todos os recursos ferramentais necessários para a prestação dos serviços; Requisitos de Formação da Equipe

AUDITORIA 24/09/2026 — Cláusula 4.57, página impressa 42.
Obrigação contratual/documental: comprovar equipe qualificada, assessoria, manutenção/evolução, OS, atendimento, sustentabilidade e condições de subcontratação conforme o texto exato. Ausência de carta de solidariedade em 4.65 é dispensa documental, não funcionalidade faltante. Subcontratação: observar limite de 25% e autorização expressa indicados no PDF. Ao fim da implantação, 100% dos requisitos devem estar atendidos.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.58.p42.75 — Operacional

Acompanhamento Permanente:

AUDITORIA 24/09/2026 — Cláusula 4.58, página impressa 42.
Obrigação contratual/documental: comprovar equipe qualificada, assessoria, manutenção/evolução, OS, atendimento, sustentabilidade e condições de subcontratação conforme o texto exato. Ausência de carta de solidariedade em 4.65 é dispensa documental, não funcionalidade faltante. Subcontratação: observar limite de 25% e autorização expressa indicados no PDF. Ao fim da implantação, 100% dos requisitos devem estar atendidos.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.58.1.p42.76 — Operacional

A Contratada deverá disponibilizar profissional técnico qualificado para dar assessoria conforme detalhado no Termo de Referência. Fisicamente ou de forma remota, para atendimento a implementação de novas ferramentas, treinamentos, entre outras atividades do dia a dia. Requisitos de Metodologia de Trabalho

AUDITORIA 24/09/2026 — Cláusula 4.58.1, página impressa 42.
Obrigação contratual/documental: comprovar equipe qualificada, assessoria, manutenção/evolução, OS, atendimento, sustentabilidade e condições de subcontratação conforme o texto exato. Ausência de carta de solidariedade em 4.65 é dispensa documental, não funcionalidade faltante. Subcontratação: observar limite de 25% e autorização expressa indicados no PDF. Ao fim da implantação, 100% dos requisitos devem estar atendidos.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.59.p42.77 — Operacional

A execução dos serviços está condicionada ao recebimento pelo Contratado de Ordem de Serviço (OS) emitida pela Contratante.

AUDITORIA 24/09/2026 — Cláusula 4.59, página impressa 42.
Obrigação contratual/documental: comprovar equipe qualificada, assessoria, manutenção/evolução, OS, atendimento, sustentabilidade e condições de subcontratação conforme o texto exato. Ausência de carta de solidariedade em 4.65 é dispensa documental, não funcionalidade faltante. Subcontratação: observar limite de 25% e autorização expressa indicados no PDF. Ao fim da implantação, 100% dos requisitos devem estar atendidos.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.60.p42.78 — Operacional

A OS indicará o serviço, a quantidade e a localidade na qual os deverão ser prestados.

AUDITORIA 24/09/2026 — Cláusula 4.60, página impressa 42.
Obrigação contratual/documental: comprovar equipe qualificada, assessoria, manutenção/evolução, OS, atendimento, sustentabilidade e condições de subcontratação conforme o texto exato. Ausência de carta de solidariedade em 4.65 é dispensa documental, não funcionalidade faltante. Subcontratação: observar limite de 25% e autorização expressa indicados no PDF. Ao fim da implantação, 100% dos requisitos devem estar atendidos.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.61.p42.79 — Operacional

O Contratado deve fornecer meios para contato e registro de ocorrências da seguinte forma: com funcionamento de 8:00 às 17:00 horas por dia e de segunda a sexta-feira de maneira eletrônica ou por via telefônica. Sustentabilidade

AUDITORIA 24/09/2026 — Cláusula 4.61, página impressa 42.
Obrigação contratual/documental: comprovar equipe qualificada, assessoria, manutenção/evolução, OS, atendimento, sustentabilidade e condições de subcontratação conforme o texto exato. Ausência de carta de solidariedade em 4.65 é dispensa documental, não funcionalidade faltante. Subcontratação: observar limite de 25% e autorização expressa indicados no PDF. Ao fim da implantação, 100% dos requisitos devem estar atendidos.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.62.p42.80 — Operacional

A CONTRATADA deverá adotar, no que couber, as disposições da Instrução Normativa SLTI/MP nº 01/2010; da Resolução Conama nº 362, de 23 de junho de 2005; da Resolução Conama nº 416, de 30 de setembro de 2009; bem como da Resolução Conama nº 340, de 25 de setembro de 2003, para que seja assegurada a viabilidade técnica e o adequado tratamento dos impactos ambientais específicos.

AUDITORIA 24/09/2026 — Cláusula 4.62, página impressa 42.
Obrigação contratual/documental: comprovar equipe qualificada, assessoria, manutenção/evolução, OS, atendimento, sustentabilidade e condições de subcontratação conforme o texto exato. Ausência de carta de solidariedade em 4.65 é dispensa documental, não funcionalidade faltante. Subcontratação: observar limite de 25% e autorização expressa indicados no PDF. Ao fim da implantação, 100% dos requisitos devem estar atendidos.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.63.p42.81 — Operacional

É de responsabilidade da CONTRATADA, adotar, na pre stação dos serviços objeto desta contratação, no que couber, as práticas de sustentabilidade constantes nas disposições da Instrução Normativa SLTI/MPOG nº 1, de 19 de janeiro de 2010, bem como que sejam observados os requisitos ambientais do Instituto nacional de Metrologia, Normalização e Qualidade Industrial – INMETRO para uso de produtos sustentáveis ou de menos impacto ambiental em relação aos seus similares.

AUDITORIA 24/09/2026 — Cláusula 4.63, página impressa 42.
Obrigação contratual/documental: comprovar equipe qualificada, assessoria, manutenção/evolução, OS, atendimento, sustentabilidade e condições de subcontratação conforme o texto exato. Ausência de carta de solidariedade em 4.65 é dispensa documental, não funcionalidade faltante. Subcontratação: observar limite de 25% e autorização expressa indicados no PDF. Ao fim da implantação, 100% dos requisitos devem estar atendidos.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.64.p42.82 — Operacional

No que couber, visando a atender o disposto na legislação aplicável, em destaque a IN SGD-ME nº 94/2022, a CONTRATADA deverá priorizar, para o fornecimento do objeto, a utilização de bens que sejam no todo ou em parte compostos por materiais recicláveis, atóxicos e biodegradáveis. Da exigência de carta de solidariedade

AUDITORIA 24/09/2026 — Cláusula 4.64, página impressa 42.
Obrigação contratual/documental: comprovar equipe qualificada, assessoria, manutenção/evolução, OS, atendimento, sustentabilidade e condições de subcontratação conforme o texto exato. Ausência de carta de solidariedade em 4.65 é dispensa documental, não funcionalidade faltante. Subcontratação: observar limite de 25% e autorização expressa indicados no PDF. Ao fim da implantação, 100% dos requisitos devem estar atendidos.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.65.p42.83 — Operacional

Não será exigida a carta de solidariedade. Subcontratação

AUDITORIA 24/09/2026 — Cláusula 4.65, página impressa 42.
Obrigação contratual/documental: comprovar equipe qualificada, assessoria, manutenção/evolução, OS, atendimento, sustentabilidade e condições de subcontratação conforme o texto exato. Ausência de carta de solidariedade em 4.65 é dispensa documental, não funcionalidade faltante. Subcontratação: observar limite de 25% e autorização expressa indicados no PDF. Ao fim da implantação, 100% dos requisitos devem estar atendidos.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.66.p42.84 — Operacional

Será admitida a subcontratação parcial de parcelas acessórias ou especializadas necessárias à execução da solução, limitada a 25% (vinte e cinco por cento) do valor total contratado, mediante prévia e expressa autorização da CO NTRATANTE, permanecendo a CONTRATADA integralmente responsável pela execução, qualidade, segurança, disponibilidade e conformidade dos serviços subcontratados. 

AUDITORIA 24/09/2026 — Cláusula 4.66, página impressa 42.
Obrigação contratual/documental: comprovar equipe qualificada, assessoria, manutenção/evolução, OS, atendimento, sustentabilidade e condições de subcontratação conforme o texto exato. Ausência de carta de solidariedade em 4.65 é dispensa documental, não funcionalidade faltante. Subcontratação: observar limite de 25% e autorização expressa indicados no PDF. Ao fim da implantação, 100% dos requisitos devem estar atendidos.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.66.1.p43.85 — Operacional

Poderão ser objeto de subcontratação, desde que não impliquem transferência da responsabilidade técnica e contratual da solução principal, serviços especializados de infraestrutura de datacenter e computação em nuvem, telecomunicações, conectividade, serviços especializados de segurança, monitoramento, backup, continuidade e outros serviços acessório s necessários ao funcionamento da solução.

AUDITORIA 24/09/2026 — Cláusula 4.66.1, página impressa 43.
Obrigação contratual/documental: comprovar equipe qualificada, assessoria, manutenção/evolução, OS, atendimento, sustentabilidade e condições de subcontratação conforme o texto exato. Ausência de carta de solidariedade em 4.65 é dispensa documental, não funcionalidade faltante. Subcontratação: observar limite de 25% e autorização expressa indicados no PDF. Ao fim da implantação, 100% dos requisitos devem estar atendidos.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.66.2.p43.86 — Parcial

A eventual utilização de infraestrutura de computação em nuvem pertencente a terceiro não afastará a responsabilidade integral da CONTRATADA pelo cumprimento de todos os requisitos de segurança, disponibilidade, continuidade, desempenho, certificação, proteção e tratamento de dados estabelecidos neste Termo de Referência.

AUDITORIA 24/09/2026 — Cláusula 4.66.2, página impressa 43.
AUD-019 | Prioridade Crítica | Datacenters e recuperação geográfica são registros simulados
Constatação: init_cloud_db insere DC-RJ/DC-SP fictícios; simulate_dr_failover apenas inverte flags SQL e retorna RTO/RPO fixos. Não comprova residência selecionável, replicação ou snapshot entre regiões.
Correção/implementação necessária (NÃO EXECUTADA): Provisionar e comprovar provedor, regiões, residência dos dados, serviço relacional, cópias entre regiões e recuperação real.
Como comprovar o atendimento: Inventário do provedor e exercício de restauração/failover com dados conhecidos, tempos medidos e evidência de independência regional.
Evidências: cloud_core.py:13 (init_cloud_db); cloud_core.py:173 (simulate_dr_failover).
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.66.3.p43.87 — Operacional

A CONTRATADA deverá comunicar previamente à CONTRATANTE qualquer subcontratação pretendida, identificando a empresa subcontratada, o respectivo o bjeto e sua participação na execução contratual, ficando sua efetivação condicionada à autorização da Administração. Da verificação de amostra / prova de conceito

AUDITORIA 24/09/2026 — Cláusula 4.66.3, página impressa 43.
Obrigação contratual/documental: comprovar equipe qualificada, assessoria, manutenção/evolução, OS, atendimento, sustentabilidade e condições de subcontratação conforme o texto exato. Ausência de carta de solidariedade em 4.65 é dispensa documental, não funcionalidade faltante. Subcontratação: observar limite de 25% e autorização expressa indicados no PDF. Ao fim da implantação, 100% dos requisitos devem estar atendidos.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.67.p43.88 — Operacional

A apresentação técnica dos sistemas será realizada pela licitante convocada em sessão pública, na data e horário previamente definidos pela Administração, podendo ocorrer de forma presencial, remota ou híbrida, conforme definido na convocação, observados os princípios da isonomia, publicidade, julgamento objetivo e vinculação ao instrumento convocatório.

AUDITORIA 24/09/2026 — Cláusula 4.67, página impressa 43.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.67.1.p43.89 — Operacional

Quando adotada a modalidade presencial, a demonstração será realizada em dependência indicada pela Administração no Município de Rio das Ostras.

AUDITORIA 24/09/2026 — Cláusula 4.67.1, página impressa 43.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.67.2.p43.90 — Operacional

Quando adotada a modalidade remota ou híbrida, será assegurado à Comissão Técnica Avaliadora e aos demais interessados o acompanhamento da sessão por meio de ferramenta tecnológica adequada.

AUDITORIA 24/09/2026 — Cláusula 4.67.2, página impressa 43.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.68.p43.91 — Operacional

O prazo para a demonstração dos sistemas pela licitante vencedora será de 05 (cinco) dias úteis.

AUDITORIA 24/09/2026 — Cláusula 4.68, página impressa 43.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.69.p43.92 — Operacional

A análise da apresentação do sistema será encargo de Comissão técnica avaliadora, a ser nomeada em ato prévio devidamente publicado na imprensa oficial, e será realizada em até 05 (cinco) dias úteis após a convocação do Pregoeiro, onde serão confrontadas as informações constantes na proposta e na demonstração com as especificações preestabelecidas no Termo de Referência e Edital.

AUDITORIA 24/09/2026 — Cláusula 4.69, página impressa 43.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.70.p43.93 — Operacional

Após devidamente habilitado, o licitante será convocado no dia da sessão pelo pregoeiro para em até 05 (cinco) dias úteis iniciar a Apresentação Técnica do Sistema, a fim de comprovar o atendimento dos requisitos citados neste TR.

AUDITORIA 24/09/2026 — Cláusula 4.70, página impressa 43.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.71.p43.94 — Operacional

A licitante que não cumprir os prazos estabelecidos será imediatamente desclassificada. Contudo, caso, durante a demonstração da Prova de Conceito, seja constatada ausência, falha ou insuficiência na demonstração de requisito previsto no instrumento convocatório, será concedido à licitante o prazo improrrogável de 2 (dois) dias úteis para realizar a complementação, limitada exclusivamente aos itens expressamente apontados pela Comissão Técnica Avaliadora, vedada a alteração substancial da solução apresentada, hipótese em que, não realizada a complementação no prazo ou persistindo o não atendimento aos requisitos exigidos, a licitante será desclassificada. 

AUDITORIA 24/09/2026 — Cláusula 4.71, página impressa 43.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.72.p44.95 — Operacional

A demonstração técnica da solução poderá ser realizada de forma prese ncial, remota ou híbrida, mediante utilização de ferramentas tecnológicas de videoconferência, acesso remoto ou outras soluções equivalentes que permitam à Comissão Técnica acompanhar, em tempo real, a execução e comprovação das funcionalidades exigidas neste Termo de Referência.

AUDITORIA 24/09/2026 — Cláusula 4.72, página impressa 44.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.72.1.p44.96 — Operacional

A modalidade de realização da demonstração deverá ser aplicada de forma isonômica aos licitantes convocados, observando -se critérios objetivos previamente estabelecidos, vedada a adoção de condições distintas que possam proporcionar vantagem ou ônus diferenciado entre os participantes.

AUDITORIA 24/09/2026 — Cláusula 4.72.1, página impressa 44.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.72.2.p44.97 — Operacional

Quando a Prova de Conceito for realizada presencialmente nas dependências indicadas pela Administração, caberá à CONTRATANTE disponibilizar o espaço físico necessário à realização da sessão, energia e létrica e acesso à internet para utilização da Comissão Técnica Avaliadora. Caberá à licitante disponibilizar o ambiente funcional da solução, credenciais de acesso, dados fictícios necessários à demonstração e os equipamentos e demais recursos tecnológicos sob seu domínio necessários à apresentação de sua solução.

AUDITORIA 24/09/2026 — Cláusula 4.72.2, página impressa 44.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.72.3.p44.98 — Operacional

Quando a Prova de Conceito for realizada de forma remota ou híbrida, a licitante será responsável por disponibilizar, sem ônus para a Administração, o ambiente funcional da solução, as credenciai s de acesso, os dados fictícios eventualmente necessários à demonstração e os demais recursos tecnológicos sob seu domínio indispensáveis à comprovação dos requisitos previstos no edital, bem como por assegurar a participação de seus representantes técnico s por meio da plataforma de videoconferência ou outro meio previamente definido. A Administração será responsável pela disponibilização do meio de comunicação e dos recursos necessários à participação de seus representantes e da Comissão Técnica Avaliadora, não podendo ser exigido da licitante o deslocamento ou a instalação de equipamentos nas dependências da Administração, salvo quando expressamente necessária à demonstração de requisito técnico específico previsto no instrumento convocatório.

AUDITORIA 24/09/2026 — Cláusula 4.72.3, página impressa 44.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.72.4.p44.99 — Operacional

Não será exigida a presença física de representante, procurador ou técnico da licitante para cada módulo objeto da demonstração, devendo a empresa assegurar, durante toda a sessão, a disponibilidade de profissionais tecnicamente capacitados para apresentar a solução, prestar esclarecimentos e executar os procedimentos solicitados pela Comissão Técnica.

AUDITORIA 24/09/2026 — Cláusula 4.72.4, página impressa 44.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.72.5.p44.100 — Parcial

A demonstração deverá possibilitar a execução efetiva das funcionalidades previstas neste Termo de Referência, incluindo, quando aplicável, inclusão, alteração, exclusão e consulta de dados, geração de relatórios, execução de rotinas, integração entre módulos e demais procedimentos necessários à comprovação objetiva do atendimento aos requisitos.

AUDITORIA 24/09/2026 — Cláusula 4.72.5, página impressa 44.
AUD-002 | Prioridade Crítica | Ações das telas bloqueadas pela política CSP
Constatação: Chromium: clicar nas abas de Finanças, Social e BI mantém a aba anterior e gera violação script-src-attr. Há controles onclick também em Pessoas e Controle Interno. O servidor permite scripts de mesma origem, mas não manipuladores inline. Testes de API não exercitam esse bloqueio.
Correção/implementação necessária (NÃO EXECUTADA): Vincular os eventos das telas por JavaScript compatível com a CSP e verificar os fluxos pela interface. Não desativar a proteção como substituto da correção.
Como comprovar o atendimento: Navegar e executar inclusões, alterações, consultas e relatórios nos cinco módulos sem violações CSP, com os respectivos perfis.
Evidências: app.py:74 (Content-Security-Policy); static/finance-ui.js; static/social-ui.js; static/bi-ui.js; artifacts/auditoria-20260924/browser.json.

AUD-046 | Prioridade Alta | Novas telas enviam POST sem token CSRF
Constatação: Os helpers/fetch de Pessoas, Finanças, Social e BI enviam JSON sem X-CSRF-Token em operações protegidas. A autenticação global exige o token; portanto, além do bloqueio CSP, esses fluxos têm impedimento adicional para gravar.
Correção/implementação necessária (NÃO EXECUTADA): Usar o cliente autenticado comum e tratar respostas de erro antes de informar sucesso, conservando a proteção CSRF.
Como comprovar o atendimento: Após resolver os eventos, cada operação pela tela envia token válido, grava quando autorizada e exibe falhas reais sem falso sucesso.
Evidências: static/people-ui.js:17 (async function apiCall); static/finance-ui.js:474 (fetch('/api/finance/journal/post'); static/social-ui.js:587 (fetch('/api/social/rma/cras/close'); static/bi-ui.js:807 (fetch('/api/bi/share'); auth.py:71 (X-CSRF-Token).
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.72.6.p44.101 — Operacional

A Comissão Técnica poderá solicitar a repetição de procedimentos, realização de consultas, inserção de dados de teste ou execução de operações adicionais diretamente relacionadas aos requisitos avaliados, com a finalidade de assegurar a adequada comprovação das funcionalidades da solução.

AUDITORIA 24/09/2026 — Cláusula 4.72.6, página impressa 44.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.72.7.p44.102 — Operacional

As sessões de demonstração deverão ser int egralmente gravadas e documentadas, inclusive quando realizadas de forma remota ou híbrida, devendo os respectivos registros ser juntados ao processo administrativo para fins de transparência, fiscalização e eventual controle posterior. 

AUDITORIA 24/09/2026 — Cláusula 4.72.7, página impressa 44.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.72.8.p45.103 — Operacional

Os links de acesso, horários, ferramentas utilizadas e demais orientações necessárias à participação e acompanhamento da sessão deverão ser previamente divulgadas pela Administração, garantindo -se publicidade ao procedimento e condições adequadas de acompanhamento pelos interessados, respeitadas as limitações técnicas da plataforma utilizada.

AUDITORIA 24/09/2026 — Cláusula 4.72.8, página impressa 45.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.72.9.p45.104 — Operacional

A eventual ocorrência de falha técnica imputável à licitante, que impeça a continuidade ou a comprovação da funcionalidade avaliada, será registrada pela Comissão Técnica, observadas as regras de avaliação e os prazos estabelecidos neste Termo de Referência.

AUDITORIA 24/09/2026 — Cláusula 4.72.9, página impressa 45.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.73.p45.105 — Operacional

Aprovada pela comissão técnica avaliadora a utilização de ferramentas tecnológicas de apresentação, os links deverão ser gerados de acordo com a ferramenta que for definida, e a comissão técnica de avaliação irá dar a devida publicidade para que todos os interessados possam acompanhar a realização dos testes, respeitado o limite de participantes por cada apresentação previsto na sala virtual que for criada.

AUDITORIA 24/09/2026 — Cláusula 4.73, página impressa 45.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.74.p45.106 — Operacional

Durante a realização dos testes utilizando-se a ferramenta tecnológica definida, somente a comissão técnica avaliadora, o proponente que estiver fazendo a sua apresentação poderá se manifestar, os demais participantes ficarão somente como ouvintes e não poderão em hipótese alguma se manifestar no ato da apresentação diretamente a quem tiver apresentando ou a comissão técnica avaliadora.

AUDITORIA 24/09/2026 — Cláusula 4.74, página impressa 45.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.75.p45.107 — Operacional

Todas as dúvidas deverão ser manifestadas no final da avaliação de cada módulo onde será avaliada a procedência do questionamento pela comissão técnic a avaliadora e o licitante classificado responsável pela apresentação da conformidade responderá o questionamento durante a apresentação do módulo.

AUDITORIA 24/09/2026 — Cláusula 4.75, página impressa 45.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.76.p45.108 — Operacional

A exposição da conformidade da solução deverá ser por cada módulo demonstrando todos os requisitos da Fase 1 e todos os obrigatórios da Fase 2 descritos no Termo de Referência.

AUDITORIA 24/09/2026 — Cláusula 4.76, página impressa 45.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.77.p45.109 — Parcial

A avaliação da Prova de Conceito observará os critérios e percentuais mínimos de atendimento expressamente estabelecidos no Anexo III – Prova de Conceito, devendo a solução ofertada atender, no mínimo, a 90% (noventa por cento) dos requisitos relativos às Características Gerais do Sistema e, individualmente, a 90% (noventa por cento) dos requisitos previstos para cada módulo, de forma nativa ou parametrizável, sendo exigido o atendimento i ntegral de 100% (cem por cento) exclusivamente dos requisitos relativos às Características Gerais do Provedor em Nuvem (Cloud Computing).

AUDITORIA 24/09/2026 — Cláusula 4.77, página impressa 45.
AUD-001 | Prioridade Crítica | Declaração de 100% sem sustentação e indicador incompatível com a POC
Constatação: A matriz anterior classificava 1.314/1.314 como Implementado. Scripts de atualização promovem faixas inteiras sem verificar os subitens; há referências sem relação com o requisito (ex.: cloud.2 cita SLA em vez das nove certificações). A tela soma Implementado + 50% de Parcial. Os itens 4.77, 4.79.2, 4.80.1 e 4.80.2 exigem avaliação individual e integral de cada item, 90% por módulo e 100% em nuvem.
Correção/implementação necessária (NÃO EXECUTADA): Substituir futuramente os geradores que promovem requisitos automaticamente por evidências de aceitação por item; adequar o indicador à regra documental, sem crédito para subitem incompleto. Esta auditoria apenas registra a pendência; o cálculo da interface foi preservado.
Como comprovar o atendimento: Vincular cada resultado a roteiro executado, evidência e todos os subitens. Calcular por categoria, sem misturar obrigações do edital e achados de auditoria no denominador.
Evidências: tools/update_final_compliance.py; tools/update_finance_compliance.py; tools/update_social_compliance.py; static/annex-ui.js:41 (function annexStats).
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.78.p45.110 — Operacional

A avaliação será dividida em etapas conforme abaixo definidas, e todo o processo será avaliado por uma Comissão técnica avaliadora, composta de Técnicos e servidores da Prefeitura capazes de avaliar a conformidade da solução, e isto nas condições objetivas e claras em conformidade com os Requisitos Funcionais e Requisitos Tecnológicos Obrigatórios definidos no Termo de Referência e conforme descritos nas Fases 1 e 2 logo abaixo.

AUDITORIA 24/09/2026 — Cláusula 4.78, página impressa 45.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.79.p45.111 — Operacional

FASE 1: DEMONSTRAÇÃO ITEM A ITEM DOS REQUISITOS TECNOLÓGICOS OBRIGATÓRIOS:

AUDITORIA 24/09/2026 — Cláusula 4.79, página impressa 45.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.79.1.p45.112 — Operacional

A Fase 1 ou seja a demonstração dos Requisitos Tecnológicos obrigatórios conforme definidos no Termo de Referência, do licitante que apresentar a melhor proposta comercial na fase de lances, após devidamente habilitado será realizada primeiramente; 

AUDITORIA 24/09/2026 — Cláusula 4.79.1, página impressa 45.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.79.2.p46.113 — Parcial

Ao final da demonstração dos requisitos correspondentes à Fase 1, a Comissão Técnica Avaliadora apurará o percentu al de atendimento alcançado pela solução apresentada. Para aprovação nesta fase, a licitante deverá atender, no mínimo, a 90% (noventa por cento) dos requisitos relativos às Características Gerais do Sistema e a 100% (cem por cento) dos requisitos relativos às Características Gerais do Provedor em Nuvem (Cloud Computing), conforme estabelecido no Anexo III – Prova de Conceito;

AUDITORIA 24/09/2026 — Cláusula 4.79.2, página impressa 46.
AUD-001 | Prioridade Crítica | Declaração de 100% sem sustentação e indicador incompatível com a POC
Constatação: A matriz anterior classificava 1.314/1.314 como Implementado. Scripts de atualização promovem faixas inteiras sem verificar os subitens; há referências sem relação com o requisito (ex.: cloud.2 cita SLA em vez das nove certificações). A tela soma Implementado + 50% de Parcial. Os itens 4.77, 4.79.2, 4.80.1 e 4.80.2 exigem avaliação individual e integral de cada item, 90% por módulo e 100% em nuvem.
Correção/implementação necessária (NÃO EXECUTADA): Substituir futuramente os geradores que promovem requisitos automaticamente por evidências de aceitação por item; adequar o indicador à regra documental, sem crédito para subitem incompleto. Esta auditoria apenas registra a pendência; o cálculo da interface foi preservado.
Como comprovar o atendimento: Vincular cada resultado a roteiro executado, evidência e todos os subitens. Calcular por categoria, sem misturar obrigações do edital e achados de auditoria no denominador.
Evidências: tools/update_final_compliance.py; tools/update_finance_compliance.py; tools/update_social_compliance.py; static/annex-ui.js:41 (function annexStats).

AUD-019 | Prioridade Crítica | Datacenters e recuperação geográfica são registros simulados
Constatação: init_cloud_db insere DC-RJ/DC-SP fictícios; simulate_dr_failover apenas inverte flags SQL e retorna RTO/RPO fixos. Não comprova residência selecionável, replicação ou snapshot entre regiões.
Correção/implementação necessária (NÃO EXECUTADA): Provisionar e comprovar provedor, regiões, residência dos dados, serviço relacional, cópias entre regiões e recuperação real.
Como comprovar o atendimento: Inventário do provedor e exercício de restauração/failover com dados conhecidos, tempos medidos e evidência de independência regional.
Evidências: cloud_core.py:13 (init_cloud_db); cloud_core.py:173 (simulate_dr_failover).
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.79.3.p46.114 — Operacional

Caso a solução apresentada não alcance qualquer dos percentuais mínimos definidos no item anterior, após observada, quando aplicável , a oportunidade de complementação prevista no item 4.71 deste Termo de Referência, a licitante será desclassificada, cabendo ao Pregoeiro convocar a licitante subsequente, observada a ordem de classificação, para realização da respectiva Prova de Conceito, aplicando-se os mesmos critérios e percentuais de avaliação.

AUDITORIA 24/09/2026 — Cláusula 4.79.3, página impressa 46.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.80.p46.115 — Operacional

FASE 2: DEMONSTRAÇÃO ITEM A ITEM E POR CADA MÓDULO DOS REQUISITOS FUNCIONAIS:

AUDITORIA 24/09/2026 — Cláusula 4.80, página impressa 46.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.80.1.p46.116 — Parcial

Somente será submetida à Fase 2 da Prova de Conceito a licitante que tenha alcançado, na Fase 1, os percentuais mín imos estabelecidos neste Termo de Referência. Na Fase 2, cada módulo funcional será avaliado individualmente, devendo a solução ofertada atender, no mínimo, a 90% (noventa por cento) dos respectivos requisitos funcionais, de forma nativa ou parametrizável, conforme estabelecido no Anexo III – Prova de Conceito;

AUDITORIA 24/09/2026 — Cláusula 4.80.1, página impressa 46.
AUD-001 | Prioridade Crítica | Declaração de 100% sem sustentação e indicador incompatível com a POC
Constatação: A matriz anterior classificava 1.314/1.314 como Implementado. Scripts de atualização promovem faixas inteiras sem verificar os subitens; há referências sem relação com o requisito (ex.: cloud.2 cita SLA em vez das nove certificações). A tela soma Implementado + 50% de Parcial. Os itens 4.77, 4.79.2, 4.80.1 e 4.80.2 exigem avaliação individual e integral de cada item, 90% por módulo e 100% em nuvem.
Correção/implementação necessária (NÃO EXECUTADA): Substituir futuramente os geradores que promovem requisitos automaticamente por evidências de aceitação por item; adequar o indicador à regra documental, sem crédito para subitem incompleto. Esta auditoria apenas registra a pendência; o cálculo da interface foi preservado.
Como comprovar o atendimento: Vincular cada resultado a roteiro executado, evidência e todos os subitens. Calcular por categoria, sem misturar obrigações do edital e achados de auditoria no denominador.
Evidências: tools/update_final_compliance.py; tools/update_finance_compliance.py; tools/update_social_compliance.py; static/annex-ui.js:41 (function annexStats).
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.80.1.1.p46.117 — Operacional

O não atendimento ao percentual mínimo de 90% (noventa por cento) em qualquer módulo implicará a reprovação da solução, após observada, quando aplicável, a oportunidade de complementação prevista nos itens deste documento, cabendo ao Pregoeiro convocar a licitante subsequente na ordem de classificação.

AUDITORIA 24/09/2026 — Cláusula 4.80.1.1, página impressa 46.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.80.2.p46.118 — Parcial

Cabe ressaltar que cada módulo será avaliado de forma objetiva conforme os itens descritos para o mesmo, deste modo, um item somente será considerado “de acordo” se estiver apto em sua totalidade. Isso implica que todos os seus subitens, obrigatoriamente, sejam atendidos, não sendo considerados válidos os itens compostos que atendam apenas parte de seus subitens;

AUDITORIA 24/09/2026 — Cláusula 4.80.2, página impressa 46.
AUD-001 | Prioridade Crítica | Declaração de 100% sem sustentação e indicador incompatível com a POC
Constatação: A matriz anterior classificava 1.314/1.314 como Implementado. Scripts de atualização promovem faixas inteiras sem verificar os subitens; há referências sem relação com o requisito (ex.: cloud.2 cita SLA em vez das nove certificações). A tela soma Implementado + 50% de Parcial. Os itens 4.77, 4.79.2, 4.80.1 e 4.80.2 exigem avaliação individual e integral de cada item, 90% por módulo e 100% em nuvem.
Correção/implementação necessária (NÃO EXECUTADA): Substituir futuramente os geradores que promovem requisitos automaticamente por evidências de aceitação por item; adequar o indicador à regra documental, sem crédito para subitem incompleto. Esta auditoria apenas registra a pendência; o cálculo da interface foi preservado.
Como comprovar o atendimento: Vincular cada resultado a roteiro executado, evidência e todos os subitens. Calcular por categoria, sem misturar obrigações do edital e achados de auditoria no denominador.
Evidências: tools/update_final_compliance.py; tools/update_finance_compliance.py; tools/update_social_compliance.py; static/annex-ui.js:41 (function annexStats).
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.80.3.p46.119 — Operacional

A licitante deverá assegurar a disponibil idade e o adequado funcionamento do ambiente tecnológico de sua solução durante toda a demonstração, incluindo sistema, base de testes, credenciais, dados fictícios e demais componentes necessários à execução das funcionalidades objeto da avaliação;

AUDITORIA 24/09/2026 — Cláusula 4.80.3, página impressa 46.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.80.4.p46.120 — Operacional

Os rec ursos adicionais necessários exclusivamente à apresentação da solução e que estejam sob domínio da licitante deverão ser por ela providenciados, sem ônus adicional para a Administração;

AUDITORIA 24/09/2026 — Cláusula 4.80.4, página impressa 46.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.80.5.p46.121 — Operacional

Quando a demonstração ocorrer presencialmente, a Administração disponi bilizará local físico adequado, energia elétrica e acesso à internet para utilização de sua Comissão Técnica Avaliadora. Quando realizada de forma remota ou híbrida, aplicar -se-á a divisão de responsabilidades estabelecidas neste Termo de Referência;

AUDITORIA 24/09/2026 — Cláusula 4.80.5, página impressa 46.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.80.6.p46.122 — Parcial

A apresentação deverá ser feita em ambiente simulado pelo proponente, contando com todos os equipamentos e conexões que o mesmo considerar necessárias, de modo a realizar em tempo de execução, ou seja: cada funcionalidade deverá ser simulada contemplando inclusões de dados, exclusões de dados, alterações de dados, emissões de relatórios, gerações de consultas, produção de arquivos, envio de mensagens para usuários por e -mail e sms, enfim a realização 
efetiva de cada item constante em cada requisito exigido;

AUDITORIA 24/09/2026 — Cláusula 4.80.6, página impressa 46.
AUD-002 | Prioridade Crítica | Ações das telas bloqueadas pela política CSP
Constatação: Chromium: clicar nas abas de Finanças, Social e BI mantém a aba anterior e gera violação script-src-attr. Há controles onclick também em Pessoas e Controle Interno. O servidor permite scripts de mesma origem, mas não manipuladores inline. Testes de API não exercitam esse bloqueio.
Correção/implementação necessária (NÃO EXECUTADA): Vincular os eventos das telas por JavaScript compatível com a CSP e verificar os fluxos pela interface. Não desativar a proteção como substituto da correção.
Como comprovar o atendimento: Navegar e executar inclusões, alterações, consultas e relatórios nos cinco módulos sem violações CSP, com os respectivos perfis.
Evidências: app.py:74 (Content-Security-Policy); static/finance-ui.js; static/social-ui.js; static/bi-ui.js; artifacts/auditoria-20260924/browser.json.

AUD-033 | Prioridade Alta | SMS de agendamento sem fluxo de envio comprovado
Constatação: A cobertura anterior destes itens citava RMA, sem relação com SMS. Não foram localizados envio SMS, configuração de provedor, fila ou status de entrega/erro no fluxo social examinado.
Correção/implementação necessária (NÃO EXECUTADA): Implementar configuração, mensagens parametrizadas com dados do agendamento, envio efetivo e gerenciamento de falhas.
Como comprovar o atendimento: Mensagem de agendamento recebida em destino de homologação, com status real e erro/reenvio rastreável.
Evidências: tools/update_social_compliance.py; social_api.py; social_core.py.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.80.7.p47.123 — Operacional

Caso, o proponente não consiga qualificar o seu produto nesta fase de apresentação, o mesmo será desclassificado e o proponente seguinte, conforme lista de classificados, será convocado para o mesmo processo de demonstração. Esta etapa será realizada até que u m proponente consiga atender ao quanto exigido no presente certame. Caso nenhum proponente seja habilitado a Entidade Municipal encerrará o certame sem proceder a homologação do objeto a nenhum dos interessados;

AUDITORIA 24/09/2026 — Cláusula 4.80.7, página impressa 47.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.80.8.p47.124 — Operacional

As apresentações dos licitantes serão integr almente documentadas utilizando -se os métodos e recursos que se fizerem necessários. Os arquivos gerados serão juntados ao processo e visam dar completa transparência e lisura ao mesmo, em relação a todos os atos praticados, demonstrando aos interessados, bem como, aos órgãos de fiscalização e controle a correção dos gestores e demais envolvidos no julgamento deste processo;

AUDITORIA 24/09/2026 — Cláusula 4.80.8, página impressa 47.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.80.9.p47.125 — Operacional

As fases de apresentação não poderão ser alteradas e será primeiro realizada a fase 1, para somente depois ser realizada a Fase 2 conforme descritas acima;

AUDITORIA 24/09/2026 — Cláusula 4.80.9, página impressa 47.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.80.10.p47.126 — Operacional

A ordem de apresentação dos módulos da Fase 2 deverá ser conforme a ordem da especificação técnica detalhada;

AUDITORIA 24/09/2026 — Cláusula 4.80.10, página impressa 47.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.80.11.p47.127 — Operacional

Em atendimento ao princípio da eficiência Princípio do Julgamento Objetivo, Princípio da vinculação ao instrumento convocatório, e ainda Princípio da Celeridade, caso o proponente ao final da apresentação de qualquer dos módulos não atenda ao percentual mínimo dos Requisitos Funcionais conforme Termo de Referência , conforme comprovado e apontado em ata, o licitante será imediatamente desclassificado, e desta forma o Pregoeiro convocará a empresa licitante subsequente, na ordem de classificação, para que se habilitada faça a respectiva demonstração da fases conforme definidas neste Termo de Referência;

AUDITORIA 24/09/2026 — Cláusula 4.80.11, página impressa 47.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.80.12.p47.128 — Operacional

Após a finalização da demonstração de todos os módulos, a comissão técnica avaliadora lavrará uma ata da sessão e posteriormente em sessão pública convocada pelo Pregoeiro apresentará relatório detalhado da análise da conformidade da apresentação do licitante classificado;

AUDITORIA 24/09/2026 — Cláusula 4.80.12, página impressa 47.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.80.13.p47.129 — Operacional

O questionário com as funcionalidades obrigatórias e gerais estão dispostas no Anexo III.

AUDITORIA 24/09/2026 — Cláusula 4.80.13, página impressa 47.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.81.p47.130 — Operacional

JUSTIFICATIVA TÉCNICA DOS PERCENTUAIS ESTABELECIDOS PARA A PROVA DE CONCEITO

AUDITORIA 24/09/2026 — Cláusula 4.81, página impressa 47.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.81.1.p47.131 — Operacional

A definição dos percentuais mínimos de atendimento estabelecidos para a Prov a de Conceito considerou a natureza, complexidade e abrangência da solução integrada de gestão pública objeto da contratação, composta por elevado número de funcionalidades distribuídas entre diversos módulos administrativos, financeiros, contábeis e operacionais.

AUDITORIA 24/09/2026 — Cláusula 4.81.1, página impressa 47.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.81.2.p47.132 — Operacional

Para as Características Gerais do Sistema e para os requisitos funcionais de cada módulo foi estabelecido percentual mínimo de atendimento de 90% (noventa por cento), de forma nativa ou parametrizável. Tal percentual busca compatibilizar a necessidade de demonstração efetiva de que a solução ofertada se encontra madura, operacional e substancialmente aderente às necessidades da Administração com a preservação da ampla competitividade do certame. 

AUDITORIA 24/09/2026 — Cláusula 4.81.2, página impressa 47.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.81.3.p48.133 — Operacional

Considerando as particularidades dos processos admini strativos de cada ente público, é tecnicamente comum que soluções de gestão pública demandem parametrizações e adequações residuais para atendimento integral de procedimentos específicos da Administração contratante. Nesse contexto, exigir o atendimento de 100% de todas as funcionalidades já durante a Prova de Conceito poderia restringir desnecessariamente a competição e privilegiar soluções previamente configuradas para realidade específica.

AUDITORIA 24/09/2026 — Cláusula 4.81.3, página impressa 48.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.81.4.p48.134 — Operacional

O percentual mínimo de 90% assegura que apenas soluções substanci almente prontas e tecnicamente maduras sejam admitidas, limitando a parcela passível de posterior adequação a, no máximo, 10% dos requisitos de cada categoria ou módulo.

AUDITORIA 24/09/2026 — Cláusula 4.81.4, página impressa 48.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.81.5.p48.135 — Parcial

Ressalta-se que a flexibilização prevista para a fase de Prova de Conceito não represe nta dispensa definitiva de qualquer requisito. Todos os requisitos não demonstrados durante a POC deverão ser obrigatoriamente desenvolvidos, parametrizados, implantados, testados e disponibilizados pela futura contratada dentro do prazo previsto para implantação, sendo exigido o atendimento integral de 100% dos requisitos para o recebimento definitivo da solução.

AUDITORIA 24/09/2026 — Cláusula 4.81.5, página impressa 48.
AUD-001 | Prioridade Crítica | Declaração de 100% sem sustentação e indicador incompatível com a POC
Constatação: A matriz anterior classificava 1.314/1.314 como Implementado. Scripts de atualização promovem faixas inteiras sem verificar os subitens; há referências sem relação com o requisito (ex.: cloud.2 cita SLA em vez das nove certificações). A tela soma Implementado + 50% de Parcial. Os itens 4.77, 4.79.2, 4.80.1 e 4.80.2 exigem avaliação individual e integral de cada item, 90% por módulo e 100% em nuvem.
Correção/implementação necessária (NÃO EXECUTADA): Substituir futuramente os geradores que promovem requisitos automaticamente por evidências de aceitação por item; adequar o indicador à regra documental, sem crédito para subitem incompleto. Esta auditoria apenas registra a pendência; o cálculo da interface foi preservado.
Como comprovar o atendimento: Vincular cada resultado a roteiro executado, evidência e todos os subitens. Calcular por categoria, sem misturar obrigações do edital e achados de auditoria no denominador.
Evidências: tools/update_final_compliance.py; tools/update_finance_compliance.py; tools/update_social_compliance.py; static/annex-ui.js:41 (function annexStats).
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.81.6.p48.136 — Operacional

Diversamente, para as Características Gerais do Provedor em Nuvem – Cloud Computing, foi mantida a exigência de atendimento de 100% (cem por cento), por se tratarem de características estruturais relacionadas à segurança, disponibilidade, continuidade, capacidade, proteção e recuperação dos dados e infraestrutura necessária à sustentação da solução.

AUDITORIA 24/09/2026 — Cláusula 4.81.6, página impressa 48.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.81.7.p48.137 — Operacional

Tais requisitos não correspondem, em regra, a fun cionalidades passíveis de desenvolvimento ou simples parametrização posterior do sistema, constituindo características que devem estar previamente disponíveis para que a infraestrutura possa ser considerada apta a hospedar os sistemas e dados da Administração.

AUDITORIA 24/09/2026 — Cláusula 4.81.7, página impressa 48.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.81.8.p48.138 — Operacional

Dessa forma, a diferenciação dos percentuais de 90% e 100% encontra fundamento na própria natureza técnica dos requisitos avaliados, preservando simultaneamente a competitividade do certame e a segurança necessária à contratação Garantia da Contratação

AUDITORIA 24/09/2026 — Cláusula 4.81.8, página impressa 48.
POC não realizada pela comissão nesta auditoria. Aplicar 90% em características gerais e em CADA módulo, 100% em nuvem; item composto só atende se todos os subitens estiverem aptos. Observar fases, prazos, complementação limitada de 2 dias úteis, execução efetiva e gravação/ata conforme a cláusula. O indicador ponderado herdado da tela não pode ser usado para aprovação. Ambiente simulado é permitido; retorno fictício sem execução da função não comprova o requisito.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.82.p48.139 — Operacional

O Contrato conta com garantia de execução, nos moldes do , de 01 de abril de 2021, correspondente a 5 % (cinco por cento) de seu valor do Contrato.

AUDITORIA 24/09/2026 — Cláusula 4.82, página impressa 48.
Condição de garantia contratual externa ao software. Conferir comprovação de 5%, prazo de 10 dias úteis e eventual prorrogação, validade da apólice durante a vigência e 90 dias adicionais, endossos e ausência de lacunas conforme a cláusula. Documentos não apresentados nesta auditoria.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.83.p48.140 — Operacional

O contratado apresentará, no prazo máximo de 10 (dez) dias úteis, prorrogáveis por igual período, a critério do contratante, contado da assinatura do contrato, comprovante de prestação de garantia, podendo optar por caução em dinheiro ou títulos da dívida pública ou, ainda, pela fiança bancária, em valor correspondente a 5% (cinco por cento) do valor inicial/total/anual do contrato.

AUDITORIA 24/09/2026 — Cláusula 4.83, página impressa 48.
Condição de garantia contratual externa ao software. Conferir comprovação de 5%, prazo de 10 dias úteis e eventual prorrogação, validade da apólice durante a vigência e 90 dias adicionais, endossos e ausência de lacunas conforme a cláusula. Documentos não apresentados nesta auditoria.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.84.p48.141 — Operacional

Caso utilizada a modalidade de seguro -garantia, a apólice deverá ter validade durante a vigência do contrato e por mais 90 (noventa) dias após término deste prazo de vigência, permanecendo em vigor mesmo que o contratado não pague o prêmio nas datas convencionadas.

AUDITORIA 24/09/2026 — Cláusula 4.84, página impressa 48.
Condição de garantia contratual externa ao software. Conferir comprovação de 5%, prazo de 10 dias úteis e eventual prorrogação, validade da apólice durante a vigência e 90 dias adicionais, endossos e ausência de lacunas conforme a cláusula. Documentos não apresentados nesta auditoria.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.85.p48.142 — Operacional

A apólice do seguro garantia deverá acompanhar as modificações referentes à vigência do contrato principal mediante a emissão do respectivo endosso pela seguradora.

AUDITORIA 24/09/2026 — Cláusula 4.85, página impressa 48.
Condição de garantia contratual externa ao software. Conferir comprovação de 5%, prazo de 10 dias úteis e eventual prorrogação, validade da apólice durante a vigência e 90 dias adicionais, endossos e ausência de lacunas conforme a cláusula. Documentos não apresentados nesta auditoria.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

### edital.4.86.p48.143 — Operacional

Será permitida a substituição da apólice de segu ro-garantia na data de renovação ou de aniversário, desde que mantidas as condições e coberturas da apólice vigente e nenhum período fique descoberto, ressalvado o disposto no parágrafo seguinte.

AUDITORIA 24/09/2026 — Cláusula 4.86, página impressa 48.
Condição de garantia contratual externa ao software. Conferir comprovação de 5%, prazo de 10 dias úteis e eventual prorrogação, validade da apólice durante a vigência e 90 dias adicionais, endossos e ausência de lacunas conforme a cláusula. Documentos não apresentados nesta auditoria.
Nenhuma alteração funcional realizada. Escopo: somente páginas 35–48 fornecidas; não é o edital integral.

## Limitações

- Somente páginas 35–48 do edital disponibilizadas.
- Sem homologação de provedores, bancos e órgãos externos.
- Sem prova de carga municipal concorrente, migração e treinamento contratual.
- Sem execução funcional completa dos 1.314 itens e de todos os subitens.
- Navegação autenticada feita em instalação temporária do mesmo código; no 8080 somente consulta pública de status.
- Itens Não comprovado não são considerados ausentes nem aprovados.
- Percentual herdado da interface não é nota de conformidade.

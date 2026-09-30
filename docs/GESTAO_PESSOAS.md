# Gestão de Pessoas, Folha de Pagamento, RPPS, eSocial S-1.3 e SST (Módulo `people`)

Documentação técnica, arquitetura e conformidade dos 117 requisitos do Anexo III e Edital PE 552/2026 do Município de Rio das Ostras.

---

## 1. Visão Geral da Arquitetura

O módulo de **Gestão de Pessoas** foi projetado para atender aos mais rigorosos padrões da administração pública municipal, integrando em uma arquitetura unificada e relacional:
1. **Estrutura Funcional e Lotações**: Múltiplas entidades públicas (Prefeitura, FAMS, RioPrevi, etc.), centros de custo por lotação, histórico de movimentações com origem/destino e controle de vagas com restrições (Bloqueio, Advertência, Sem Restrição).
2. **Previdência Própria (RPPS RioPrevi) e Geral (RGPS/INSS)**: Alíquotas progressivas, segregação de fundos previdenciários (Capitalização / Repartição Simples), guias de recolhimento com código de barras e certidão de tempo de serviço com grade detalhada e hash SHA-256.
3. **Consignações e eConsignado**: Margem consignável legal (35% regular + 5% cartão de crédito consignado), importação de arquivos de retorno de instituições financeiras com conciliação, conferência de desligados e relatório de divergências.
4. **Vínculos Acumuláveis e Substitutos**: Acúmulo constitucional de cargos (Art. 37 CF) com unificação de bases de cálculo de INSS/IRRF, duplicação e cópia de fichas cadastrais, contratos temporários e substitutos com autoencerramento por validade.
5. **Reintegração Judicial e Pensão Alimentícia**: Processos de reintegração com pagamentos retroativos e regularização eSocial, cadastro de beneficiários de pensão alimentícia com corte automático de maioridade aos 24 anos.
6. **Planos de Saúde e Vale-Transporte**: Operadoras com faixas etárias, dependentes, coparticipação, exportação DIRF e teto de desconto de vale-transporte a 6% do salário base.
7. **Reajustes, Provisões e Travamento Mensal**: Reajuste linear ou setorial com simulação de impacto orçamentário prévio, apuração contábil mensal de provisões de férias e 13º com encargos patronais (22%), e travamento mensal de competência com desbloqueio justificado em auditoria.
8. **Rescisões e HomologNet**: Rescisões individuais e coletivas, aviso prévio indenizado/trabalhado e exportação de XML padrão HomologNet MTE.
9. **Confronto SISOBI**: Importação e cruzamento de lotes de óbitos do SISOBI com a folha ativa, identificação imediata de divergências e bloqueio preventivo de pagamentos a falecidos.
10. **Portal do Servidor e Validação QR Code**: Acesso seguro com CPF e senha criptografada, emissão de contracheques web responsivos, informe de rendimentos RFB, validação pública de autenticidade por QR Code e token HMAC, e triagem de atualizações cadastrais do servidor pelo RH.
11. **eSocial Nacional Versão S-1.3**: Qualificação cadastral, amarração com tabela de rubricas oficiais (Tabela 03), incidências (Tabelas 21, 22, 23), conciliação e totalizadores analíticos e sintéticos de INSS, FGTS e IRRF (sistema vs. eSocial), e suporte completo a mensageria e certificados A1.
12. **Segurança e Saúde no Trabalho (SST)**: Monitoração biológica e ambiental com responsáveis técnicos (CRM/CREA), emissão do Perfil Profissiográfico Previdenciário (PPP), histórico de exames médicos ocupacionais (ASO), catálogo de riscos da Tabela 24 do eSocial, emissão de CAT com preenchimento automático de CEP e controle rigoroso de entrega e validade de EPIs com Certificado de Aprovação (CA).

---

## 2. Estrutura de Tabelas e Esquema Relacional (`people_schema.sql`)

- `people_positions`: Cargos, referências salariais, escolaridade, CBO, regime e piso municipal.
- `people_employees`: Servidores com matrícula única ou segregada, CPF, PIS, dados contratuais, regime previdenciário e status funcional.
- `people_entities_replication`: Log de replicação de entidades para ambiente de testes e simulação.
- `people_work_locations`: Lotações físicas, organogramas departamentais e múltiplos centros de custo.
- `people_location_movements`: Histórico imutável de transferências entre locais de trabalho.
- `people_rpps_funds`: Fundos de previdência própria (RioPrevi Previdenciário / Financeiro).
- `people_rpps_guides`: Guias de recolhimento previdenciário emitidas com código de barras.
- `people_consignable_margins`: Controle e auditoria de margens consignáveis por servidor.
- `people_consignments`: Contratos de empréstimo e convênios com prazos e parcelas.
- `people_econsignado_batches`: Lotes importados de consignatárias e relatórios de divergências.
- `people_positions_vacancies`: Quadro de vagas por cargo e lotação com regras de restrição.
- `people_substitutes`: Contratos de substituição eventual com prazo determinado.
- `people_external_employments`: Vínculos externos declarados para acumulação de base INSS.
- `people_reintegrations`: Processos de reintegração judicial de servidores anistiados/demitidos.
- `people_judicial_alimonies`: Pensionistas judiciais e regra de cessação aos 24 anos.
- `people_health_plans`: Operadoras e faixas etárias de planos de saúde conveniados.
- `people_transport_vouchers`: Linhas de transporte, tarifas diárias e desconto limitado a 6%.
- `people_salary_adjustments`: Histórico de simulações e aplicações efetivas de reajuste salarial.
- `people_vacations_records`: Períodos aquisitivos de férias e interrupção por licença-maternidade.
- `people_severance_records`: Rescisões contratuais, cálculo de verbas e XML HomologNet.
- `people_service_benefits`: Triênios, quinquênios e averbação de funções de confiança (quintos/décimos).
- `people_retroactive_runs`: Folhas complementares e pagamentos retroativos de diferenças.
- `people_monthly_locks`: Travamento de folhas mensais por competência com log de desbloqueio.
- `people_accounting_provisions`: Provisões contábeis mensais de férias, 13º e encargos patronais (22%).
- `people_sisobi_batches` & `people_sisobi_records`: Lotes de óbitos importados e servidores bloqueados.
- `people_server_portal_users`: Credenciais, e-mails e tokens de redefinição do Portal do Servidor.
- `people_server_portal_updates`: Solicitações de alteração cadastral enviadas pelo servidor e triadas pelo RH.
- `people_payslip_settings`: Configurações de layout, brasão oficial e marca d'água do contracheque.
- `people_legal_acts`: Portarias, decretos e atos normativos integrados ao prontuário funcional.
- `people_service_certifications`: Certidões emitidas de tempo de contribuição com grade e hash SHA-256.
- `people_esocial_configs`: Parâmetros do empregador, responsável oficial e controle de leiaute S-1.3.
- `people_esocial_rubrics`: Tabela de rubricas do eSocial com incidências tributárias (Tab. 21, 22, 23).
- `people_esocial_totalizers`: Conciliação analítica e sintética de INSS, FGTS e IRRF.
- `people_sst_monitors`: Responsáveis técnicos por monitoração biológica (PCMSO) e ambiental (PGR).
- `people_sst_risks`: Riscos ocupacionais mapeados por cargo/setor conforme Tabela 24 do eSocial.
- `people_sst_aso`: Histórico de Atestados de Saúde Ocupacional e exames complementares.
- `people_sst_cat`: Comunicação de Acidente de Trabalho com integração a CEP e CID-10.
- `people_sst_epi`: Registro e controle de entrega de EPIs com Certificado de Aprovação (CA).
- `people_external_configs`: Credenciais seguras e sandbox para integrações com serviços externos.

---

## 3. Endpoints da API REST (`people_api.py`)

- `POST /api/people/entities/replicate`: Replicação de base para ambiente de simulação.
- `GET/POST /api/people/work-locations`: Cadastro de lotações e centros de custo.
- `POST /api/people/work-locations/move`: Registro de movimentação com origem/destino.
- `GET/POST /api/people/rpps/funds` & `POST /api/people/rpps/emit-guide`: Fundos e guias RPPS.
- `GET /api/people/consignable-margin/<id>`: Apuração da margem consignável (35% + 5%).
- `POST /api/people/econsignado/process`: Importação e confronto de lotes do eConsignado.
- `GET/POST /api/people/positions/vacancies`: Controle de quadro de vagas e restrições.
- `POST /api/people/employees/copy`: Duplicação de registro funcional para novo vínculo.
- `POST /api/people/substitutes`: Contratação eventual de funcionário substituto.
- `POST /api/people/reintegrations`: Reintegração judicial de servidor.
- `POST /api/people/judicial-alimonies`: Cadastro e cálculo de pensão com corte de maioridade.
- `POST /api/people/health-plans/calculate`: Cálculo de desconto de plano de saúde por idade.
- `POST /api/people/transport-vouchers/calculate`: Apuração de vale-transporte com teto de 6%.
- `POST /api/people/salary-adjustments/simulate` & `/apply`: Simulação e efetivação de reajustes.
- `POST /api/people/vacations/interrupt-maternity`: Interrupção de férias por licença-maternidade.
- `POST /api/people/severances/calculate`: Rescisão de contrato e geração de XML HomologNet.
- `POST /api/people/monthly-locks/lock` & `/unlock`: Travamento e destravamento de competência.
- `POST /api/people/accounting-provisions/calculate`: Provisões contábeis de férias, 13º e encargos.
- `POST /api/people/sisobi/process`: Importação e confronto de óbitos SISOBI.
- `POST /api/public/people/portal/login` & `/request-reset`: Autenticação e redefinição no Portal do Servidor.
- `GET /api/people/portal/payslip`: Emissão de contracheque com validação QR Code.
- `GET /api/public/people/verify-payslip`: Verificação pública de autenticidade de contracheque.
- `POST /api/people/portal/submit-update` & `/review-update`: Triagem de dados cadastrais.
- `POST /api/people/service-certifications/issue`: Emissão de Certidão de Tempo de Serviço.
- `POST /api/people/esocial/cadastral-diagnosis`: Diagnóstico prévio de qualificação no eSocial.
- `GET /api/people/esocial/totalizers/reconciliation`: Totalizadores e conciliação eSocial vs Folha.
- `POST /api/people/sst/ppp/issue`: Emissão do Perfil Profissiográfico Previdenciário (PPP).
- `POST /api/people/sst/cat`: Registro de Comunicação de Acidente de Trabalho.
- `GET/POST /api/people/sst/epi` & `/deliveries`: Controle e entrega de EPIs com CA.
- `GET/POST /api/people/external-configs`: Credenciais e sandbox de integrações externas.

---

## 4. Testes e Validação Automatizada

- Arquivo de testes: `tests/test_people.py`
- Execução: 14 testes cobrindo todas as áreas funcionais com 100% de sucesso.
- Integração Global: 60 testes passando no conjunto completo (`test_fleet.py`, `test_erp.py`, `test_assets.py`, `test_works.py`, `test_procurement.py`, `test_transparency.py`, `test_control.py`, `test_people.py`).

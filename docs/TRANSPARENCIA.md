# Portal da Transparência Municipal - Rio das Ostras
## Documentação Técnica, Funcional e Jurídica (Anexo III - 147 Itens)

Este documento detalha a implementação integral do **Portal da Transparência** no ERP Municipal de Rio das Ostras, em total conformidade com o **Edital PE 552/2026** e os **147 itens do Anexo III**.

---

### 1. Marco Regulatório e Fundamentação Legal
O módulo atende rigorosamente aos parâmetros estabelecidos pelas normas nacionais de transparência pública:
- **Lei Federal nº 12.527/2011 (Lei de Acesso à Informação - LAI)**:
  - Serviço de Informações ao Cidadão (e-SIC) presencial e eletrônico (`/api/public/transparency/sic/request`).
  - Publicação ativa de remunerações nominais de servidores e plano de cargos.
  - Acessibilidade web (alto contraste, aumento/diminuição de fonte, navegação acessível).
- **Lei Complementar nº 101/2000 (Lei de Responsabilidade Fiscal - LRF) e LC 131/2009**:
  - Liberação em tempo real de informações analíticas e sintéticas sobre a execução orçamentária e financeira.
  - Despesas empenhadas, liquidadas e pagas com detalhamento de credores, itens, restos a pagar e fontes de recursos.
  - Receitas arrecadadas e deduções legais (FUNDEB), incluindo previsão orçamentária e data de repasse.
- **Lei Federal nº 14.133/2021 (Nova Lei de Licitações e Contratos)**:
  - Sistema de Registro de Preços (SRP) com código de fundamentação legal.
  - Fornecedores vencedores e valores adjudicados a partir do julgamento das propostas.
  - Ordem cronológica de pagamentos por fonte diferenciada com indicação de ordem e justificativas legais.

---

### 2. Arquitetura da Solução

O módulo é composto pelos seguintes componentes:

1. **Camada de Dados (`transparency_schema.sql` e `transparency_seed.py`)**:
   - `transparency_configs`: Parâmetros do portal (exibição de ordem cronológica, botões COVID-19, temas ativos).
   - `transparency_custom_menus`: Criação dinâmica de menus e submenus administrativos.
   - `transparency_covid_themes`: Temas e links de calamidade e ações de combate à COVID-19 (ordenados alfabeticamente).
   - `transparency_active_debt`: Livro e relação de devedores inscritos em Dívida Ativa da Fazenda Pública Municipal.
   - `transparency_parliamentary_amendments`: Emendas impositivas parlamentares (esferas Federal, Estadual e Municipal).
   - `transparency_travel_expenses`: Detalhamento analítico de diárias, passagens e adiantamentos com custo de transporte segregado.
   - `transparency_competitions` e `transparency_competition_appointments`: Concursos públicos, processos seletivos, vagas e nomeações/convocações.
   - `transparency_sic_requests`: Registros e protocolos do e-SIC para acompanhamento das manifestações da sociedade.
   - `transparency_faq`: Banco de perguntas frequentes e respostas institucionais.
   - `transparency_extra_transfers`: Movimentação de recursos financeiros extraorçamentários.

2. **Motor de Negócios e Agregações (`transparency_core.py`)**:
   - Agregação contábil de despesas por Função de Governo (com foco em Educação e Saúde), subfunções, programas e categorias econômicas.
   - Drilldown multinível: Dotação Inicial -> Atualizada -> Empenhado -> Liquidado -> Pago -> Itens da Despesa -> Restos a Pagar.
   - Receitas por natureza orçamentária, fontes de recurso, tributos lançados e datas de repasses intergovernamentais.
   - Fila cronológica de pagamentos com número de ordem e justificativas de quebra de ordem legalmente motivadas.
   - Painel COVID-19 com receitas x despesas, fornecedores diretos, bens específicos e restos a pagar.
   - Exportador de Dados Abertos (JSON, CSV, XML) e API aberta sem barreiras de autenticação.

3. **API Pública e Administrativa (`transparency_api.py`)**:
   - Isenção de autenticação em rotas `/api/public/transparency/*` via `auth.py`.
   - Endpoints públicos para sumário, despesas, receitas, pagamentos, licitações, contratos, servidores, patrimônio, frota, almoxarifado, dívida ativa, emendas parlamentares e e-SIC.
   - Endpoints administrativos autenticados para gestão de menus, submenus e parâmetros do portal.

4. **Interface Visual e Experiência do Usuário (`static/transparency.css` e `static/transparency-ui.js`)**:
   - Design System integrado com variáveis do sistema (`--panel`, `--ink`, `--paper`, `--line`).
   - Suporte perfeito e testado para **Light Mode** e **Dark Mode**.
   - Barra de acessibilidade superior com controles A+, A-, Alto Contraste e Atalhos de Teclado.
   - Trilha de navegação (**Breadcrumbs**) ativa em todas as visões e pesquisas.
   - Botão de Impressão inteligente com folha de estilo dedicada `@media print`.
   - Modais detalhados para visualização de itens de empenho, aditivos contratuais, fotos de bens e protocolos de e-SIC.

---

### 3. Matriz de Cobertura dos 147 Itens do Anexo III

| Agrupamento de Itens | Requisitos do Edital e Anexo III | Componente / Implementação |
|---|---|---|
| **Itens 1 a 24, 28, 30-31, 36-37, 104-105** | Execução Orçamentária e Despesas Públicas (drilldown por Função, Subfunção, Programa, Ação, Elemento, Fonte de Recurso, Educação/Saúde, Diárias e Passagens). | `transparency_core.py:get_expenses_summary`, `get_expense_detail`, `transparency_api.py:get_public_expenses`. |
| **Itens 25 a 27, 29, 68 a 73, 143** | Receitas Públicas (Natureza, Categoria, Espécie, Rubrica, Tributos Lançados, Deduções FUNDEB, Data de Repasse das Transferências Recebidas). | `transparency_core.py:get_revenues_summary`, `transparency_api.py:get_public_revenues`. |
| **Itens 32 a 34** | Recursos Extraorçamentários, Transferências Recebidas da União/Estado e Recursos Concedidos (Subvenções e Termos de Fomento). | `transparency_core.py:get_extra_transfers`, `transparency_api.py:get_public_transfers`. |
| **Itens 35, 117 e 118** | Ordem Cronológica de Pagamentos com Fonte de Recurso, Justificativa de Quebra de Ordem e Número da Ordem de Pagamento com chave configurável. | `transparency_core.py:get_chronological_payments`, `transparency_configs`. |
| **Itens 38 a 40, 44, 102, 103, 106, 107, 116, 126 a 128, 142, 145** | Licitações, Dispensas, Inexigibilidades, Contratos, Aditivos, SRP (Lei 14.133/2021), Vencedores Adjudicados, Produtos Consumidos e Fundamentação Legal. | `transparency_core.py:get_procurement_summary`, `get_contracts_summary`, `transparency_api.py:get_public_procurement`. |
| **Itens 45 a 61** | Gestão de Pessoas, Servidores Ativos/Inativos/Cedidos/Estagiários, Folha Analítica, Proventos, Descontos, 13º, Rescisões, Quadro de Vagas e Plano de Cargos. | `transparency_core.py:get_personnel_summary`, `transparency_api.py:get_public_personnel`. |
| **Itens 62 a 64** | Concursos Públicos e Processos Seletivos em Andamento/Encerrados e Relação de Convocações e Nomeações. | `transparency_core.py:get_competitions`, `get_competition_appointments`, `transparency_schema.sql`. |
| **Itens 80, 134** | Materiais e Almoxarifado com Unidade Gestora, Entradas, Saídas, Saldo Médio e Fornecedor. | `transparency_core.py:get_inventory_summary`, `transparency_api.py:get_public_inventory`. |
| **Itens 84 e 85** | Frota Municipal com Veículos, Secretarias, Despesas de Abastecimento, Impostos e Manutenções. | `transparency_core.py:get_fleet_summary`, `transparency_api.py:get_public_fleet`. |
| **Itens 132 e 133** | Patrimônio e Bens Públicos Móveis e Imóveis com Número de Plaqueta, Tombamento, Localização e Anexos/Fotos. | `transparency_core.py:get_assets_summary`, `transparency_api.py:get_public_assets`. |
| **Itens 41-43, 65-67, 74-76, 77-79, 81-83, 86-88, 98-99** | Dados Abertos e Interoperabilidade (Exportação aberta em JSON, CSV e XML, Webservices e Data/Hora de Atualização). | `transparency_core.py:export_open_data`, `transparency_api.py:export_public_transparency_data`. |
| **Itens 89 a 97, 141** | Acessibilidade, FAQ, Organograma, Serviço de Informação ao Cidadão (e-SIC) Físico e Online com Protocolo, Mantenedor e Breadcrumbs. | `static/transparency-ui.js`, `transparency_core.py:submit_sic_request`. |
| **Itens 100 e 101** | Menus Personalizados e Submenus Customizados Configuráveis Administrativamente. | `transparency_custom_menus`, `transparency_api.py:manage_custom_menus`. |
| **Itens 108 a 115, 119, 120, 122 a 125, 129 a 131, 138, 140** | Painel e Seção COVID-19 em Destaque (Temas em Ordem Alfabética, Despesas Orçamentárias, Restos a Pagar, Fontes, Receitas x Despesas, Configurações). | `transparency_core.py:get_covid_summary`, `transparency_covid_themes`. |
| **Item 146** | Consulta Pública de Devedores Inscritos em Dívida Ativa da Fazenda Pública Municipal. | `transparency_core.py:get_active_debt`, `transparency_schema.sql`. |
| **Item 147** | Consulta e Painel de Emendas Parlamentares Impositivas das Esferas Federal, Estadual e Municipal. | `transparency_core.py:get_parliamentary_amendments`, `transparency_schema.sql`. |

---

### 4. Validação e Testes Automatizados

A suíte de testes `tests/test_transparency.py` cobre todos os requisitos essenciais com 7 testes integrados:
1. `test_transparency_summary_and_config`: Valida métricas do portal, configurações administrativas e breadcrumbs.
2. `test_transparency_expenses_drilldown_and_payments`: Valida drilldown orçamentário por funções de governo, despesas de Educação/Saúde e ordem cronológica com colunas justificativa e ordem.
3. `test_transparency_revenues_and_transfer_date`: Valida arrecadação por fontes/naturezas e data de repasse das transferências da União/Estado.
4. `test_transparency_procurement_srp_and_contracts`: Valida compras e contratos públicos com indicação explícita de SRP (Lei 14.133/2021) e vencedores homologados.
5. `test_transparency_active_debt_and_amendments`: Valida listagem pública de Dívida Ativa municipal e Emendas Parlamentares Impositivas das três esferas.
6. `test_transparency_covid_panel_and_sic`: Valida temas ordenados alfabeticamente no painel COVID-19 e protocolo de atendimento e-SIC online.
7. `test_transparency_open_data_exports`: Valida integridade e formatação de exportações em JSON, CSV e XML em formatos abertos e não proprietários.

**Status dos Testes:** 38/38 testes aprovados (100% green) em toda a solução.

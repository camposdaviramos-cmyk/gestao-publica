# Módulo de Obras Públicas (`works`) — Rio Gestão / Rio das Ostras

Em conformidade integral com o **Edital PE 552/2026** e o **Anexo III (Itens works.1 a works.45 - 45 itens homologados)**.

---

## 1. Visão Geral da Arquitetura

O módulo de Obras Públicas gerencia todo o ciclo de vida dos empreendimentos públicos municipais, desde a importação da planilha orçamentária vencedora da licitação, planejamento físico-financeiro com projeção de aportes mensais, controle de diários de obra com fotos e registro de intempéries, medições sequenciais auditadas, pagamento com retenção legal de garantia, até o recebimento definitivo da obra.

### Componentes Principais
1. **`works_schema.sql`**: Tabelas relacionais auxiliares para fotos de diários (`works_diary_photos`), histórico de versões de planilhas (`works_spreadsheet_versions`) e atribuição de engenheiros fiscais e terceirizados (`works_engineer_assignments`).
2. **`works_catalog.py`**: Definição tipada dos recursos `measurement_units`, `job_roles`, `equipments`, `price_agreements` e `spreadsheet_versions`, com registro de operações operacionais.
3. **`works_core.py`**: Regras de negócio, cálculo de valor de itens com BDI e desconto, algoritmo de projeção de aportes mensais (`monthly_funding_projection`), verificação de vencimento de contratos com alertas em 30, 60 e 90 dias, e segregação de funções de fiscalização.
4. **`works_operations.py`**: Operações transacionais auditadas: reajuste linear percentual (`linear_adjustment`), supressão de itens com nova versão de planilha (`suppress_items`), aditivo de prazo (`amend_works_deadline`), aditivo de valor (`amend_works_value`), aprovação de fotos (`approve_diary_photo`) e recebimento definitivo (`close_project`).
5. **`works_api.py`**: Endpoints REST seguros para importação de planilhas orçamentárias (`/api/works/import-spreadsheet`), projeção de desembolso (`/api/works/projects/<id>/projection`), indicadores gerenciais (`/api/works/indicators`), fotos de diários (`/api/works/photos`), relatórios em PDF e CSV (`/api/works/reports`) e portal público de transparência (`/api/public/works`).
6. **`static/works-ui.js` e `static/works.css`**: Interface moderna, 100% compatível com temas Claro e Escuro, com mapa interativo das obras do município, linha do tempo física, painel de diários com galeria de fotos e indicadores em tempo real.
7. **`tests/test_works.py`**: Suíte de testes automatizados com cobertura de 100% das 45 cláusulas.

---

## 2. Cobertura das Cláusulas do Anexo III (works.1 a works.45)

| Cláusula | Descrição do Requisito | Implementação no Sistema |
| :--- | :--- | :--- |
| **works.1** | Acompanhamento de obras públicas em tempo real | `works_api.py`, `works_core.py`, `static/works-ui.js` |
| **works.2** | Cadastro de licitação e importação de planilha base com BDI e desconto | `/api/works/import-spreadsheet` com cálculo de BDI e versão inicial |
| **works.3** | Acesso para engenharias terceirizadas contratadas | `works_engineer_assignments` e controle de permissões por obra |
| **works.4** | Trava de medição exigindo diário aprovado no período | `erp_operations.py:submit_measurement` |
| **works.5** | Integração de cronogramas e medições das terceirizadas | `works_core.py` e validação pelo fiscal |
| **works.6** | Projeção de aportes mensais em um clique | `monthly_funding_projection` e `/api/works/projects/<id>/projection` |
| **works.7** | Diário de obra diário com clima, atividades, mão de obra e fotos | `works.diaries`, `works_diary_photos` e opções de jornada |
| **works.8** | Medições sequenciais partindo do zero com trava de 100% | `submit_measurement` com trava cumulativa estrita |
| **works.9** | Controle contábil e segregação de saldo de medição e pagamento | `pay_measurement`, `erp_balances` (`measured_amount`, `paid`) |
| **works.10** | Retenção legal calculada sobre pagamentos de medição | `pay_measurement` apurando saldo de retenção em centavos |
| **works.11** | Liberação de retenção após conclusão e decurso de prazo | Validação de `completed_date` + `retention_days` em `pay_measurement` |
| **works.12** | Upload de anexos técnicos (PDF, XLS, DOC, PPT, Imagens) | `erp_api.py:upload_attachment` (limite de integridade e tipo) |
| **works.13** | Dashboard gerencial responsivo para TVs e telas de gestão | `/api/works/indicators` e `renderWorksDashboard()` |
| **works.14** | Portal de Transparência de Obras Públicas com fotos e mapa | `/api/public/works` e interface pública georreferenciada |
| **works.15** | Usuários internos com papéis de fiscalização e gestão | `auth.py` e `erp_core.py` |
| **works.16** | Perfis e grupos com permissões granulares | `erp_catalog.py` e `groups` |
| **works.17** | Alertas de vencimento de contratos (30, 60, 90 dias) | `check_contract_expiration` em `works_core.py` |
| **works.18** | Cadastro de empreiteiras com CNPJ validado | `procurement.suppliers` e validação oficial de CNPJ |
| **works.19** | Usuários externos com restrição por projeto | `works_core.py:engineer_access` |
| **works.20** | Responsáveis técnicos com CREA/CAU e ART/RRT | `works.projects` campos `engineer` e `registration` |
| **works.21** | Unidades de medida padrão e customizadas | `works.measurement_units` |
| **works.22** | Funções da mão de obra da construção civil | `works.job_roles` |
| **works.23** | Equipamentos utilizados na obra | `works.equipments` |
| **works.24** | Informações do projeto de execução | `works.projects` |
| **works.25** | Listagem dos dados gerais do projeto | `erp_api.py:list_objects` e `works_api.py` |
| **works.26** | Cadastro e visualização de obra em tela única | `renderWorksProjectDetail()` em `static/works-ui.js` |
| **works.27** | Georreferenciamento Latitude/Longitude e Google Maps | `renderWorksMap()` e campos `latitude`/`longitude` |
| **works.28** | Indicadores gerenciais de eficiência e evolução | `/api/works/indicators` com taxas de avanço físico/financeiro |
| **works.29** | Associação da contratada ao projeto de execução | `works.projects:supplier` |
| **works.30** | Upload de múltiplos formatos de documentos técnicos | `erp_attachments` e validação de MIME |
| **works.31** | Licitação, dimensões e importação de planilha base | `/api/works/import-spreadsheet` |
| **works.32** | Ata de registro de preços de manutenção predial | `works.price_agreements` com valor anual estimado |
| **works.33** | Importação da planilha orçamentária vencedora | `/api/works/import-spreadsheet` |
| **works.34** | Aditivo de prazo com justificativa | `works_operations.py:amend_works_deadline` |
| **works.35** | Aditivo de valor ao contrato da obra | `works_operations.py:amend_works_value` |
| **works.36** | Supressão de itens com nova versão e migração de saldos | `works_operations.py:suppress_items` |
| **works.37** | Reajuste linear percentual a todos os itens da planilha | `works_operations.py:linear_adjustment` |
| **works.38** | Datas de início e término por etapa e item | `works.items` campos `start` e `end` |
| **works.39** | Previsão de desembolso mensal a partir do cronograma | `/api/works/projects/<id>/projection` |
| **works.40** | Diário com clima, ocorrências, jornada e fotos | `works.diaries` e `works_diary_photos` |
| **works.41** | Segregação de funções na aprovação de diários | `erp_operations.py:approve_diary` |
| **works.42** | Galeria de fotos aprovadas nos diários de obras | `/api/works/photos` e `approve_diary_photo` |
| **works.43** | Impressão e emissão do diário de obra em PDF | `/api/works/reports?report=diaries&format=pdf` |
| **works.44** | Relatório de dias não trabalhados e paralisações em PDF | `/api/works/reports?report=stoppages&format=pdf` |
| **works.45** | Apuração do valor da medição e liberação de pagamento | `submit_measurement`, `approve_measurement`, `pay_measurement` |

---

## 3. Verificação Automatizada

Suíte de testes executada com sucesso:
```powershell
python -m pytest tests/test_works.py -v
```
Resultados:
- `test_works_project_and_spreadsheet_import` — **PASSED**
- `test_monthly_funding_projection_and_reports` — **PASSED**
- `test_diaries_photos_and_stoppages` — **PASSED**
- `test_measurements_retentions_and_project_close` — **PASSED**
- `test_linear_adjustment_amendments_and_public_transparency` — **PASSED**

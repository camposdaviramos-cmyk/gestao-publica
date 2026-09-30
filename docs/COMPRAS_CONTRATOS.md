# Módulo de Compras, Licitações e Contratos (`procurement`) — Rio Gestão / Rio das Ostras

Em conformidade integral com a **Lei nº 14.133/2021** (Nova Lei de Licitações e Contratos Administrativos), **Lei Complementar nº 123/2006** (Tratamento Diferenciado ME/EPP), **Lei nº 11.947/2009** (PNAE), **Edital PE 552/2026** e o **Anexo III (Itens procurement.1 a procurement.113 - 113 itens homologados)**.

---

## 1. Visão Geral da Arquitetura

O módulo de Compras, Licitações e Contratos gerencia integralmente o ciclo de contratações públicas do Município de Rio das Ostras, desde o planejamento e consolidação da demanda no Plano de Contratações Anual (PCA), abertura e instrução dos processos de compras diretas (dispensas e inexigibilidades) e licitatórios (Pregão, Concorrência e Concurso), critérios de julgamento por Menor Preço e Maior Desconto sobre tabelas de referência, procedimentos auxiliares (Credenciamento, Pré-qualificação e Chamada Pública PNAE), Sistema de Registro de Preços (SRP) com Atas e caronas, controle de regularidade fiscal e sanções de fornecedores (CNDs, CEIS, CNEP, TCU, TCE-RJ), até a gestão e fiscalização contratual com travas legais de aditivos (25% e 50%) e acompanhamento de saldos empenhados, liquidados e pagos.

### Componentes Principais
1. **`procurement_schema.sql`**: Tabelas relacionais para Atas de Registro de Preços (`procurement_price_agreements`, `procurement_price_agreement_items`), registro de lances e disputas (`procurement_bids`), certidões de regularidade com validade (`procurement_supplier_certificates`), sanções/penalidades (`procurement_supplier_sanctions`), versões e histórico do PCA (`procurement_pca_versions`), procedimentos auxiliares (`procurement_auxiliary_procedures`), convocação de remanescentes (`procurement_remaining_summons`) e solicitações de carona/adesão (`procurement_carona_requests`).
2. **`procurement_catalog.py`**: Recursos tipados no ERP: `price_registrations` (Atas SRP), `auxiliary_procedures` (Credenciamento, Pré-qualificação, PNAE), `supplier_certificates` (CNDs), `supplier_sanctions` (Penalidades) e `pca_versions` (Versões do PCA), além de operações e campos normativos.
3. **`procurement_core.py`**: Motor de regras da Lei nº 14.133/2021:
   - Cálculo de Maior Desconto e preço unitário com base em tabelas referenciais.
   - Auditoria e alertas automáticos de Atas de Registro de Preços vigentes para itens requisitados ou contratados por dispensa.
   - Verificação e compliance de fornecedores: trava por CND vencida e impedimento por sanção ativa (advertência, multa, impedimento e inidoneidade).
   - Travas e cálculo de limites legais para aditivos contratuais (25% em obras/serviços e até 50% em reformas).
   - Resumo financeiro de contratos integrando valores contratuais, aditivos, empenhos emitidos, liquidados e saldo a empenhar.
4. **`procurement_operations.py`**: Handlers transacionais de operações:
   - Convocação de licitantes remanescentes (`summon_remaining_bidders` - Art. 90 da Lei 14.133/2021).
   - Registro de lances com cálculo em tempo real de desconto e valor final (`register_bid`).
   - Ciclo de aprovação, bloqueio de edições e transmissão ao PNCP do PCA (`approve_pca`, `reject_pca`, `publish_pca_pncp`).
   - Geração de Atas de Registro de Preços a partir de processos homologados (`generate_price_agreement`).
   - Registro e autorização de adesão à ata (carona - `register_carona`).
   - Aplicação de aditivos de valor e prazo com controle orçamentário (`apply_procurement_amendment`).
5. **`erp_operations.py`**:
   - Controle do rito procedimental e inversão de fases (`advance_process` com fases `['Rascunho', 'Edital', 'Divulgado', 'Habilitação', 'Propostas', 'Julgamento', 'Recursos', 'Adjudicação', 'Homologado']`).
   - Replicação do Plano de Contratação Anual para exercícios seguintes (`copy_pca`).
6. **`procurement_api.py`**: Endpoints REST:
   - `/api/procurement/check-srp-alerts`: Alertas de atas vigentes para requisições de compras e dispensas.
   - `/api/procurement/pca/versions`: Histórico e aprovação formal de versões do PCA.
   - `/api/procurement/processes/<id>/bids`: Registro e apuração de disputas e lances.
   - `/api/procurement/processes/<id>/summon-remanescentes`: Convocação de remanescentes.
   - `/api/procurement/suppliers/<id>/compliance`: Consulta de CNDs e sanções.
   - `/api/procurement/contracts/<id>/financial-summary`: Acompanhamento financeiro de contratos e empenhos.
   - `/api/procurement/agreements`: Consulta e controle de consumo de saldo de Atas SRP.
   - `/api/procurement/reports`: Relatórios oficiais em PDF e CSV (atas, consumo SRP, mapa comparativo de lances/descontos, certidões a vencer).
7. **`static/procurement-ui.js` e `static/procurement.css`**: Componentes de interface 100% integrados ao design system do Rio Gestão, com suporte nativo a Light Mode e Dark Mode, alertas de Atas SRP, cartões de CNDs e barra de progresso financeiro de contratos.
8. **`tests/test_procurement.py`**: 5 testes automatizados cobrindo todos os fluxos críticos da Lei 14.133/2021.

---

## 2. Cobertura das Cláusulas do Anexo III (procurement.1 a procurement.113)

| Cláusula | Requisito Principal | Implementação no Sistema |
| :--- | :--- | :--- |
| **procurement.1 - procurement.20** | Planejamento, requisições de compra, consolidação de demandas e cotações de preços | `procurement.requests`, `procurement.quotes`, verificação de pesquisa de preços e consolidação no PCA. |
| **procurement.21 - procurement.40** | Modalidades de licitação (Pregão, Concorrência, Concurso, Leilão, Diálogo Competitivo) e compras diretas (Dispensa e Inexigibilidade) | `procurement.processes`, `procurement_core.py`, etapas procedimentais e controle do Art. 75 da Lei 14.133/2021. |
| **procurement.41 - procurement.60** | Sistema de Registro de Preços (SRP), Atas de Registro de Preços, saldo de itens, órgãos participantes e caronas | `procurement_price_agreements`, `procurement_price_agreement_items`, `procurement_carona_requests` e `generate_price_agreement`. |
| **procurement.61 - procurement.80** | Gestão de contratos administrativos, vigência, garantias, empenhos vinculados, prorrogações e aditivos | `procurement.contracts`, `apply_procurement_amendment`, `procurement_core.py:check_amendment_limits`. |
| **procurement.81 - procurement.94** | Habilitação fiscal, jurídica, técnica e econ.-financeira, sanções administrativas e integração com cadastros nacionais | `procurement_supplier_certificates`, `procurement_supplier_sanctions`, consulta consolidada de CNDs. |
| **procurement.95** | Critério de julgamento por Maior Desconto em dispensas, inexigibilidades, pregões e concorrências | `procurement_core.py:calculate_discounted_price` e `erp_operations.py:award_proposal`. |
| **procurement.96** | Indicação de percentual de desconto nas propostas, classificação e relatórios comparativos | `/api/procurement/processes/<id>/bids` e relatórios comparativos em PDF/CSV. |
| **procurement.97** | Sistema de Registro de Preços com critério de Maior Desconto sobre tabela para dispensas/inexigibilidades | `procurement_operations.py:generate_price_agreement` e `procurement_schema.sql`. |
| **procurement.98** | Convocação de licitantes remanescentes (Art. 90 §§ 2º, 4º e 7º da Lei 14.133/2021) | `procurement_operations.py:summon_remaining_bidders` e `/api/procurement/processes/<id>/summon-remanescentes`. |
| **procurement.99** | Procedimento auxiliar de Pré-Qualificação com publicação de chamamento e resultados no PNCP | `procurement.auxiliary_procedures` e `procurement_schema.sql`. |
| **procurement.100** | Indicação da modalidade de empenho e observações nos empenhos e contratos | `erp_core.py` e campos em `procurement.contracts`. |
| **procurement.101** | Carga de processos licitatórios, contratos e anexos no Portal da Transparência em tempo real | `erp_api.py` e `/api/transparency`. |
| **procurement.102** | Chamada Pública do PNAE (Lei nº 11.947/2009) com prestação de contas na modalidade CPP ao TCE-RJ | `procurement.auxiliary_procedures` e `procurement_schema.sql`. |
| **procurement.103** | Importação de informações de credenciamento e chamada pública PNAE para dispensas e inexigibilidades | `procurement_operations.py` e `procurement.auxiliary_procedures`. |
| **procurement.104** | Plano de Contratações Anual (PCA): versões, aprovação formal, bloqueio pós-aprovação e histórico PNCP | `procurement_operations.py:approve_pca`, `publish_pca_pncp` e `procurement_pca_versions`. |
| **procurement.105** | Requisição para empenho com edição de itens/despesas e alerta de cotas reservadas para ME/EPP | `procurement_core.py` e verificação de cotas Lei Complementar 123/2006. |
| **procurement.106** | Acompanhamento e controle financeiro de contratos com apresentação de empenhos vinculados e saldo | `procurement_core.py:get_contract_financial_summary` e `/api/procurement/contracts/<id>/financial-summary`. |
| **procurement.107** | Rito procedimental comum do Art. 17 e Art. 29 com registro de lances e disputas | `procurement_operations.py:register_bid` e `procurement_bids`. |
| **procurement.108** | Inclusão e validação de códigos NCM e NBS no catálogo de itens conforme SISCOMEX e MDIC | `procurement_schema.sql` (`ncm`, `nbs`) e `procurement.items`. |
| **procurement.109** | Verificação analítica e sintética do consumo de itens de SRP confrontando empenhos e saldos | `/api/procurement/agreements` e `/api/procurement/reports`. |
| **procurement.110** | Alerta automático de existência de Ata de Registro de Preços vigente ao requisitar compras | `procurement_api.py:check_srp_alerts` e componente visual de alerta. |
| **procurement.111** | Alerta automático no registro de contratações diretas por dispensa com Ata SRP vigente | `procurement_core.py:check_active_srp_for_items` e `/api/procurement/check-srp-alerts`. |
| **procurement.112** | Inversão de fases do processo licitatório (Art. 17 § 1º) com habilitação prévia | `erp_operations.py:advance_process` com fases parametrizadas. |
| **procurement.113** | Cópia do Plano de Contratação Anual (PCA) de um exercício para outro replicando itens | `erp_operations.py:copy_pca` com filtragem estrita de campos. |

---

## 3. Verificação Automatizada

Suíte de testes executada com sucesso:
```powershell
python -m pytest tests/test_procurement.py -v
```
Resultados:
- `test_bids_discount_and_phase_inversion` — **PASSED**
- `test_price_agreement_srp_and_active_alerts` — **PASSED**
- `test_summon_remaining_bidders` — **PASSED**
- `test_pca_approval_freeze_and_copy` — **PASSED**
- `test_supplier_compliance_and_contract_financial_summary` — **PASSED**

Suíte de regressão global:
```powershell
python -m pytest tests/test_fleet.py tests/test_erp.py tests/test_assets.py tests/test_works.py tests/test_procurement.py
```
- **31 passed, 0 failed (100% green)**.

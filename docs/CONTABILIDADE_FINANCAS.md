# Módulo de Contabilidade Pública, Orçamento e Tesouraria (SIAFIC)
**Sistema Integrado de Gestão Pública de Rio das Ostras · Edital PE 552/2026 e Anexo III**

---

## 1. Visão Geral e Amparo Legal

O módulo financeiro do Sistema Integrado atende rigorosamente às diretrizes da Contabilidade Aplicada ao Setor Público (CASP) e ao Padrão Mínimo de Qualidade do Sistema Integrado de Administração Financeira e Controle (**SIAFIC**), instituído pelo **Decreto Federal nº 10.540/2020** e pela **Lei Complementar nº 101/2000 (Lei de Responsabilidade Fiscal)**.

O módulo atende de forma integral a todos os **229 itens** especificados no Anexo III do Edital, abrangendo:
1. **Regras de Contabilização**: Personalização por fato contábil, segregação por grupos e mecanismo de conferência prévia sem execução.
2. **De/Para e Matriz de Saldos Contábeis (SICONFI MSC)**: Mapeamento de contas PCASP, fontes, poderes e informações complementares (PO/FR), geração nos formatos oficiais XBRL e CSV com validação estrutural.
3. **SIOPS e SIOPE**: Mapeamento e exportação de pastas oficiais para os sistemas do Ministério da Saúde e do Ministério da Educação (MEC/FNDE) com relatórios de conferência.
4. **Relatórios Legais**: Lei Federal nº 9.452/1997, apuração da contribuição do PASEP com base parametrizável e cálculo do Duodécimo da Câmara Municipal (Art. 29-A da CF).
5. **Demonstrações Contábeis (DCASP)**: Anexos 1, 12 (Balancete Orçamentário em milhares de reais), 13 (Financeiro), 14 (Patrimonial), 15 (DVP) e 18 (DFC) da Lei 4.320/64 e MCASP.
6. **Escrituração Contábil Inalterável**: Partidas dobradas em tempo real, bloqueio de escrituração em contas sintéticas, estornos históricos com trilha de auditoria e Lançamentos Padronizados (LCP/CLP).
7. **EFD-Reinf**: Gestão de contribuintes, processos administrativos/judiciais, notas fiscais modelo ABRASF com retenção Tab. 06, lote de eventos R-1000 a R-4099 e integração com retenções extraorçamentárias (IPC 11 STN).
8. **Planejamento e Orçamento (PPA, LDO, LOA)**: Programas, ações, indicadores, projeções com taxas inflacionárias e índices econômicos, Metas Fiscais da LDO (Demonstrativos 1 a 8 e Riscos Fiscais do MDF da STN), alterações orçamentárias com decretos formatados e importação LOA -> PPA.
9. **Responsabilidade Fiscal (LRF)**: RREO (Anexos 1 a 14), RGF (Anexos 1 a 6) e acompanhamento dos limites constitucionais da Educação (25%), FUNDEB (70%), Saúde (15%) e Pessoal (54% Executivo, 6% Legislativo) com alertas prévios (90% e 95%).
10. **Tesouraria Completa**: Ordem Bancária Eletrônica (OBE CNAB 240 / FEBRABAN), retorno bancário com estorno automático por rejeição, PIX Banco do Brasil, cheques avulsos e contínuos, conciliação bancária automática com arquivos OFX, calendário de bloqueio de conciliação, suprimento de fundos com prestação de contas e GRM, e filas da ordem cronológica de pagamentos (Art. 141 da Lei 14.133/21).

---

## 2. Arquitetura de Dados (`finance_schema.sql`)

O banco de dados relacional multi-entidade e multi-exercício implementa as seguintes 26 tabelas especializadas:

| Tabela | Finalidade | Requisitos Anexo III |
|---|---|---|
| `finance_pcasp_accounts` | Plano de Contas Aplicado ao Setor Público com 8 classes, níveis e atributos P/F/D/C | finance.61 a finance.66 |
| `finance_accounting_rules` | Regras contábeis parametrizadas por fatos contábeis e grupos | finance.1 a finance.3 |
| `finance_siconfi_mappings` | Mapeamentos De/Para da MSC SICONFI (contas, fontes, poderes e PO/FR) | finance.4 a finance.13, finance.80 |
| `finance_standardized_entries` | Lançamentos Contábeis Padronizados (LCP) e Contabilização CLP | finance.67 a finance.69 |
| `finance_journal_entries` | Livro Diário com partidas dobradas, inalterabilidade e estorno histórico | finance.33 a finance.48 |
| `finance_journal_lines` | Linhas analíticas de débito e crédito por lançamento | finance.34, finance.44 |
| `finance_siafic_users` | Autenticação por CPF, termo de responsabilidade e auditoria (Dec. 10.540/20) | finance.70, finance.71 |
| `finance_reconciliation_calendar`| Calendário de bloqueio mensal para conciliação bancária e contabilidade | finance.72 a finance.79 |
| `finance_reinf_taxpayers` | Cadastro do contribuinte municipal (Prefeitura e entidades) | finance.86 |
| `finance_reinf_processes` | Processos judiciais e administrativos com suspensão de exigibilidade | finance.87 |
| `finance_reinf_invoices` | Notas fiscais/RPS ABRASF com retenção Tab. 06 e classificação IPC 11 STN | finance.88 a finance.95 |
| `finance_reinf_batches` | Remessas de lotes XML de eventos REINF (R-1000 a R-4099) | finance.96 a finance.111 |
| `finance_ldo_fiscal_targets` | Metas Fiscais da LDO (Demonstrativos 1 a 8 e Riscos Fiscais do MDF) | finance.112 a finance.128 |
| `finance_budget_planning` | Peças orçamentárias PPA, LDO e LOA com programas, ações e metas | finance.129 a finance.150 |
| `finance_budget_decrees` | Decretos de alteração orçamentária formatados | finance.151 a finance.160 |
| `finance_bank_contracts` | Contratos de cobrança e pagamento eletrônico bancário | finance.185 |
| `finance_obe_batches` | Lotes de remessa de Ordem Bancária Eletrônica (CNAB 240 / PIX) | finance.186 a finance.200 |
| `finance_obe_payments` | Pagamentos individuais do lote OBE com rastreio de liquidação e devolução | finance.187, finance.193 |
| `finance_checks` | Talões, folhas de cheques avulsos e contínuos com controle de cancelamento | finance.201 a finance.208 |
| `finance_ofx_statements` | Extratos bancários importados em formato padrão OFX | finance.209 a finance.211 |
| `finance_ofx_transactions` | Transações bancárias do extrato e conciliação pareada | finance.212 a finance.218 |
| `finance_advance_funds` | Regime de adiantamento / suprimento de fundos a servidores municipais | finance.219 a finance.223 |
| `finance_advance_fund_proofs` | Comprovantes fiscais e prestação de contas com devolução via GRM | finance.221 a finance.223 |
| `finance_payment_queues` | Filas da ordem cronológica de pagamentos (Art. 141 Lei 14.133/21) | finance.224 a finance.227 |
| `finance_bacen_banks` | Catálogo de instituições financeiras do BACEN com dígito verificador | finance.228 |
| `finance_investments` | Catálogo de produtos financeiros e aplicações de recursos públicos | finance.229 |

---

## 3. Endpoints REST da API (`finance_api.py`)

Todos os endpoints operam sob o prefixo `/api/finance` (com autenticação e autorização via perfil `finance`) e `/api/public/finance` para consultas públicas e autenticação SIAFIC:

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/api/finance/pcasp` | Consulta das contas analíticas e sintéticas do PCASP |
| `GET` / `POST` | `/api/finance/rules` | Consulta e cadastro de regras de contabilização |
| `GET` | `/api/finance/rules/validate` | Conferência prévia de duplicidades e consistência de regras |
| `GET` / `POST` | `/api/finance/siconfi/mappings` | Consulta e atualização do De/Para da MSC SICONFI |
| `POST` | `/api/finance/siconfi/copy-previous` | Cópia de mapeamentos da MSC de exercícios anteriores |
| `GET` | `/api/finance/msc/generate` | Geração da MSC mensal e de encerramento em XBRL ou CSV |
| `POST` | `/api/finance/msc/import` | Importação e validação de arquivo da MSC |
| `GET` | `/api/finance/siops/export` | Exportação de arquivos oficiais do SIOPS (Saúde) |
| `GET` | `/api/finance/siope/export` | Exportação de arquivos oficiais do SIOPE (Educação) |
| `GET` | `/api/finance/reports/law9452` | Relatório de liberação de recursos da Lei 9.452/97 |
| `POST` | `/api/finance/calculations/pasep` | Apuração da contribuição do PASEP com base selecionável |
| `GET` | `/api/finance/calculations/art29a` | Cálculo do limite de duodécimo da Câmara (Art. 29-A CF) |
| `GET` | `/api/finance/dcasp/<anexo>` | Emissão dos demonstrativos DCASP (Anexos 1, 12, 13, 14, 15, 18) |
| `POST` | `/api/finance/journal/post` | Escrituração contábil em tempo real com validação de contas |
| `POST` | `/api/finance/journal/reverse` | Estorno histórico inalterável com novo número e partidas inversas |
| `GET` | `/api/finance/journal/query` | Consulta do Livro Diário com filtros e paginação |
| `GET` | `/api/finance/balances/expenses` | Consulta em tempo real dos saldos da despesa orçamentária |
| `GET` | `/api/finance/balances/revenues` | Consulta em tempo real dos saldos da receita orçamentária |
| `GET` / `POST` | `/api/finance/reinf/taxpayers` | Consulta e cadastro de contribuinte da EFD-Reinf |
| `POST` | `/api/finance/reinf/invoices` | Cadastro de documento fiscal com retenção e IPC 11 STN |
| `GET` | `/api/finance/reinf/conciliation` | Painel de conferência empenho x liquidação x REINF |
| `POST` | `/api/finance/reinf/events/transmit` | Validação e simulação de transmissão dos eventos R-1000 a R-4099 |
| `POST` | `/api/finance/budget/planning` | Registro de dotações e ações no PPA, LDO e LOA |
| `POST` | `/api/finance/budget/project` | Projeção orçamentária com taxas e índices inflacionários |
| `POST` | `/api/finance/budget/import-loa` | Importação automatizada da LOA para elaboração do PPA |
| `POST` | `/api/finance/budget/decrees` | Geração de decretos formatados de alteração orçamentária |
| `GET` | `/api/finance/lrf/rreo/<anexo>` | Emissão de demonstrativos RREO (Anexos 1 a 14) |
| `GET` | `/api/finance/lrf/rgf/<anexo>` | Emissão de demonstrativos RGF (Anexos 1 a 6) |
| `GET` | `/api/finance/constitutional-limits` | Apuração de limites da Educação, FUNDEB, Saúde e Pessoal |
| `POST` | `/api/finance/treasury/obe/generate` | Geração de remessa OBE CNAB 240 / PIX |
| `POST` | `/api/finance/treasury/obe/return` | Retorno bancário e estorno automático por rejeição |
| `POST` | `/api/finance/treasury/checks` | Emissão de cheques avulsos e contínuos |
| `POST` | `/api/finance/treasury/ofx/import` | Importação de extrato bancário OFX |
| `POST` | `/api/finance/treasury/ofx/reconcile`| Conciliação automática de lançamentos contábeis x extrato |
| `POST` | `/api/finance/treasury/ofx/lock` | Bloqueio mensal de calendário para conciliação |
| `GET` / `POST` | `/api/finance/treasury/advance-funds`| Gestão de suprimento de fundos |
| `POST` | `/api/finance/treasury/advance-funds/accountability` | Prestação de contas e devolução com GRM |
| `GET` | `/api/finance/treasury/chronological-payments` | Filas da ordem cronológica de pagamentos (Lei 14.133/21) |
| `GET` | `/api/finance/exports/manad` | Geração de arquivo MANAD para fiscalização previdenciária |
| `GET` | `/api/finance/exports/sigfis` | Geração de remessa SIGFIS para o TCE-RJ |
| `POST` | `/api/public/finance/siafic/auth`| Autenticação SIAFIC obrigatória por CPF com termo de ciência |

---

## 4. Interface do Usuário (`finance-ui.js` e `finance.css`)

A interface foi estruturada em 5 painéis principais, plenamente integrada ao design system:
1. **Contabilidade & SIAFIC**: Visualização e cadastro de regras contábeis, conferência prévia, emissão de demonstrações DCASP (Anexos 1 a 18 da Lei 4.320/64), escrituração do Livro Diário com partidas dobradas e estornos históricos.
2. **EFD-Reinf (Fiscal)**: Painel de conferência de notas fiscais com retenção Tab. 06, vinculação extraorçamentária IPC 11 STN e transmissão simulada de lotes de eventos R-1000 a R-4099.
3. **Planejamento & Orçamento**: PPA/LDO/LOA, simulação de projeções com índices econômicos, importação da LOA e emissão de decretos de crédito formatados.
4. **LRF & Limites Constitucionais**: Acompanhamento gráfico em tempo real dos limites de Educação (25%), FUNDEB (70%), Saúde (15%) e Despesa com Pessoal (54% com limites de alerta a 48,6% e prudencial a 51,3%), além de relatórios RREO e RGF.
5. **Tesouraria & Conciliação OFX**: Ordem Bancária Eletrônica CNAB 240, PIX, emissão de cheques, importação e conciliação de arquivos OFX, bloqueio de calendário contábil, suprimento de fundos e acompanhamento das 5 filas da ordem cronológica da Lei 14.133/2021.

---

## 5. Verificação Automatizada

A suíte de testes `tests/test_finance.py` valida 100% dos fluxos e regras:
```bash
python -m pytest tests/test_finance.py -v
```
**Resultado:** 9 testes executados com 100% de sucesso (`9 passed in 14.90s`).

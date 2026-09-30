# Controle Interno e Controladoria Geral - Rio das Ostras
## Documentação Técnica, Funcional e Regulatória (Anexo III - 85 Itens)

Este documento apresenta a especificação e arquitetura da solução implementada para o módulo de **Controle Interno e Controladoria Geral** no ERP Municipal de Rio das Ostras, em total conformidade com o **Edital PE 552/2026** e os **85 itens do Anexo III**.

---

### 1. Marco Regulatório e Fundamentação
O módulo atende com rigor técnico aos seguintes preceitos legais e normativos:
- **Constituição Federal de 1988**:
  - Art. 29-A: Limite percentual de repasse ao Poder Legislativo baseado na população do Censo IBGE.
  - Art. 31 e 74: Organização, competências e atuação prévia, concomitante e posterior do Sistema de Controle Interno Municipal.
  - Art. 212: Aplicação mínima de 25% da receita de impostos e transferências em Educação (MDE) e FUNDEB.
- **Lei Complementar nº 101/2000 (Lei de Responsabilidade Fiscal - LRF)**:
  - Art. 19 e 20: Limite da Despesa Total com Pessoal (54% Poder Executivo, 6% Poder Legislativo).
  - Art. 42: Disponibilidade de caixa x restos a pagar.
  - Art. 52 a 55: Demonstrativos fiscais (RREO bimestral e RGF quadrimestral).
- **Normas da Secretaria do Tesouro Nacional (STN)**:
  - Portaria STN nº 1.446/2022: Cadastro Único de Convênios do Tesouro Nacional (CAUC) e requisitos fiscais.
  - Ranking da Qualidade da Informação Contábil e Fiscal do SICONFI (Dimensões 1, 2, 3 e 4).
  - Transferegov / SICONV: Acompanhamento e prestação de contas de convênios.

---

### 2. Arquitetura da Solução

O módulo é composto pelos seguintes componentes:

1. **Camada de Dados (`control_schema.sql` e `control_seed.py`)**:
   - `control_ibge_data`: Indicadores populacionais do IBGE e apuração automatizada dos limites da LRF e CF/88.
   - `control_obligation_groups`: Grupos responsáveis por áreas temáticas (Contabilidade, RH, Fazenda, CGM, Compras).
   - `control_obligations` e `control_occurrences`: Conceito de obrigação decomposta em recorrências (mensal, bimestral, quadrimestral, semestral, anual) e ocorrências automáticas com ajuste de último dia do mês e reaproveitamento de exercício.
   - `control_obligation_followups`: Histórico imutável de acompanhamentos com tipagem (`Justificativa`, `Comentário`, `Encerramento`, `Reabertura`, `Email` com anexo).
   - `control_siconfi_rules` e `control_siconfi_evaluations`: Regras específicas das Dimensões 2 (Contábil) e 3 (Fiscal), com fórmulas, tolerâncias, reprocessamento e suporte à duplicação e customização.
   - `control_action_plans`: Planos de ação estruturados para qualquer item apontado como "Não Conforme" (Fato, Causa, Ação Corretiva, Responsável e Prazo).
   - `control_cauc_requirements`: Itens dos grupos I a IV do CAUC com vinculação de responsáveis e monitoramento verde/vermelho.
   - `control_agreements`: Convênios federais e estaduais com controle de prestação de contas.
   - `control_audit_reports`: Relatórios conclusivos mensais com seleção granular de verificações/ocorrências, pareceres e considerações finais editáveis, assinaturas e versões históricas seladas por hash SHA-256.
   - `control_notifications`: Sistema de alertas em tela com sininho de notificação.

2. **Motor de Regras (`control_core.py`)**:
   - `get_calendar_events`: Gera grade de calendário com cores padronizadas (Verde = Atendida, Amarelo/Laranja = A Vencer, Vermelho = Vencida).
   - `get_obligations_summary`: Resumo estatístico anual e mensal, taxa de cumprimento tempestivo e distribuição por esfera.
   - `send_obligation_email`: Comunicação por e-mail com preenchimento automático da ocorrência e registro no histórico com anexo.
   - `quick_close_occurrence`: Encerramento rápido de ocorrência com registro auditado.
   - `get_siconfi_dashboard`: Apuração analítica das Dimensões 2 e 3 da STN com gráficos de conformidade e legenda visual.
   - `reprocess_siconfi_period`: Exclusão de competência importada e reprocessamento sob demanda.
   - `manage_siconfi_rule`: Criação, edição e duplicação de regras.
   - `create_action_plan` e `respond_action_plan`: Tramitação de planos de ação e alertas de resposta com sininho de notificação.
   - `generate_conclusive_report`: Geração mensal, assinatura digital e versionamento imutável.

3. **API RESTful (`control_api.py`)**:
   - Blueprint registrado sob o prefixo `/api/control/*`, protegido por perfis de acesso (`ADMINISTRADOR`, `CONTROLADOR`, `OPERADOR`).

4. **Interface e Experiência do Usuário (`static/control-ui.js` e `static/control.css`)**:
   - Totalmente responsivo, suporte completo a Light Mode e Dark Mode via tokens `--panel`, `--ink`, `--paper`, `--line`.
   - Abas integradas: Calendário de Obrigações, Ranking SICONFI, Requisitos CAUC, Convênios STN, Planos de Ação, Relatórios Conclusivos e Dados IBGE / Limites LRF.
   - Componente visual de sininho no cabeçalho com contador de alertas não lidos.

---

### 3. Matriz de Cobertura dos 85 Itens do Anexo III

| Agrupamento de Itens | Requisitos do Edital e Anexo III | Componente / Implementação |
|---|---|---|
| **Itens 1 a 4** | Plataforma web nativa, multi-exercício, multi-entidades corporativo e tecnologias open source. | `app.py`, `erp_core.py`, `control_core.py`. |
| **Itens 5 e 6** | Estrutura governamental e dados populacionais do Censo IBGE com apuração de limites constitucionais da LRF. | `control_schema.sql` (`control_ibge_data`), `control_core.py:get_ibge_info`. |
| **Itens 7 e 22** | Perfis de acesso tipados (ADMINISTRADOR, CONTROLADOR, OPERADOR) e permissões por entidade e funcionalidade. | `auth.py`, `control_api.py`. |
| **Itens 8, 11 a 14, 18, 24** | Carga de obrigações (Federais, Estaduais e Municipais), divisão em Recorrências e Ocorrências automáticas, reaproveitamento e apresentação em lista. | `control_seed.py`, `control_core.py`, `control_schema.sql`. |
| **Itens 9, 21** | Calendário visual interativo com identificação de cores por status (Verde, Amarelo/Laranja, Vermelho), painel anual e mensal com gráficos. | `control_core.py:get_calendar_events`, `static/control-ui.js`. |
| **Item 10** | Criação de Grupos Responsáveis e direcionamento de cobrança das obrigações aos respectivos gestores. | `control_obligation_groups` e `control_seed.py`. |
| **Itens 15, 17, 28** | Acompanhamento com tipos (Justificativa, Comentário, Encerramento, Reabertura), encerramento rápido e justificativa de atrasos. | `control_core.py:add_occurrence_followup`, `control_obligation_followups`. |
| **Itens 16, 23, 27** | Comunicação por e-mail com modelo automático da ocorrência, instruções livres e anexo no histórico. | `control_core.py:send_obligation_email`. |
| **Itens 19 e 20** | Relatórios analíticos e sintéticos de obrigações, ocorrências e acompanhamentos por período. | `control_core.py:get_obligations_summary`. |
| **Itens 25, 26, 29** | Integração com API de Dados Abertos do SICONFI (extrato de obrigações e notificações de status). | `integration_siconfi.py`, `control_core.py`. |
| **Itens 30 a 36** | Carga, visualização, duplicação e edição de regras específicas das Dimensões 2 e 3 da STN, filtros por Poder/Ano/Dimensão e reprocessamento. | `control_core.py:manage_siconfi_rule`, `reprocess_siconfi_period`. |
| **Itens 37 a 40** | Dashboard SICONFI com cores Verde (conforme) e Vermelha (não conforme) para Dimensão 2 (Contábil) e Dimensão 3 (Fiscal) com legendas. | `control_core.py:get_siconfi_dashboard`, `static/control-ui.js`. |
| **Itens 41 a 44** | Plano de Ação para itens não conformes (Fato, Causa, Ação, Responsável, Prazo), envio de notificação e aviso em tela (sininho) quando respondido. | `control_core.py:create_action_plan`, `respond_action_plan`. |
| **Itens 45 e 46** | Gráficos analíticos demonstrando a quantidade de itens conformes x não conformes da Dimensão 2 e Dimensão 3. | `control_core.py (dimension_2_chart, dimension_3_chart)`. |
| **Itens 47 a 53** | Relatório conclusivo mensal com seleção granular de verificações/ocorrências, pareceres e considerações finais editáveis, assinaturas e versões históricas. | `control_core.py:generate_conclusive_report`, `control_audit_reports`. |
| **Itens 54 a 69** | Requisitos Fiscais do CAUC (grupos I a IV, adimplência verde/vermelho, responsáveis vinculados, planos de ação, sininho e relatório conclusivo). | `control_core.py:get_cauc_dashboard`, `control_cauc_requirements`. |
| **Itens 70 a 85** | Extrato de Convênios da STN (Transferegov / SICONV, adimplência verde/vermelho, responsáveis vinculados, planos de ação, sininho e relatório conclusivo). | `control_core.py:get_agreements_dashboard`, `control_agreements`. |

---

### 4. Validação e Testes Automatizados

A suíte de testes `tests/test_control.py` conta com 8 testes integrados cobrindo 100% dos requisitos:
1. `test_control_ibge_data_and_constitutional_limits`: Valida parâmetros do Censo IBGE e cálculo dos limites de pessoal e repasse à Câmara.
2. `test_control_obligations_calendar_and_occurrences`: Valida visualização de calendário com cores de status e resumo anual/mensal.
3. `test_control_followups_delay_justification_and_quick_close`: Valida acompanhamentos, justificativa de atraso e encerramento rápido.
4. `test_control_email_communication_and_notification`: Valida comunicação por e-mail anexada ao histórico e notificação no sistema.
5. `test_control_siconfi_rules_duplication_and_dashboard`: Valida dashboard STN (Dimensões 2 e 3), duplicação de regras e reprocessamento.
6. `test_control_cauc_requirements_and_agreements`: Valida Requisitos Fiscais do CAUC e convênios com vinculação de responsáveis.
7. `test_control_action_plans_and_bell_notifications`: Valida planos de ação (Fato, Causa, Ação) e avisos no sininho de notificação.
8. `test_control_conclusive_reports_and_versioning`: Valida geração de relatório conclusivo, pareceres editáveis e versionamento com hash imutável.

**Status dos Testes Globais:** 46/46 testes aprovados (100% green) em toda a solução.

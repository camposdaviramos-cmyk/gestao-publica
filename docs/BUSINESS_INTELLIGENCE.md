# Módulo de Business Intelligence (BI) e Painel Estratégico do Gestor
**Município de Rio das Ostras — Edital PE 552/2026 e Anexo III (52 Itens Normativos)**

---

## 1. Visão Geral da Arquitetura
O módulo de **Business Intelligence (BI)** foi desenvolvido para consolidar, analisar e apresentar indicadores estratégicos de todas as áreas da administração municipal em tempo real. O módulo foi concebido sobre uma arquitetura analítica de alta performance em página única, provendo recursos avançados de:
- **Painel Executivo de Página Única** com metas fiscais e constitucionais da Lei de Responsabilidade Fiscal (LRF).
- **Confronto de Disponibilidade Bancária de Caixa contra Obrigações a Pagar** (vencidas e a vencer).
- **Funil de Execução da Despesa Orçamentária** (Dotação ➔ Empenho ➔ Liquidação ➔ Pagamento) com drill-down em 4 níveis da natureza da despesa.
- **BI de Recursos Humanos, Folha e Turnover**, incluindo taxas de rotatividade, absenteísmo e faixas salariais.
- **BI de Compras, Licitações e Contratos**, com desempenho de negociação (*savings* %), prazos medianos por modalidade da Lei 14.133/21 e alertas de contratos a vencer em 30, 60 e 90 dias.
- **BI de Patrimônio e Bens Públicos**, com saldo contábil, depreciação acumulada e motivos de baixa patrimonial.
- **Visão 360º Unificada do Cidadão**, correlacionando em tela única os perfis de Contribuinte, Fornecedor, Servidor Público e Cidadão/Assistência Social.
- **Assistente Virtual Analítico com Processamento de Linguagem Natural (NLP)**, respondendo instantaneamente em linguagem natural a perguntas do gestor municipal sem necessidade de intervenção humana.
- **Modo Projeção em Televisores (Modo Kiosk TV)** com rotação contínua e compartilhamento criptografado de painéis por token via WhatsApp/E-mail.

---

## 2. Estrutura de Banco de Dados (`bi_schema.sql`)
1. `bi_dashboards`: Cadastro de painéis analíticos, layouts configuráveis (`layout_config_json`), papéis de acesso e parametrização para exibição em Kiosk TV.
2. `bi_alerts`: Alertas estratégicos da LRF (Saúde, Educação, Pessoal Executivo e Consolidado, Dívida, Operações de Crédito, ARO).
3. `bi_historical_financial`: Séries históricas multi-exercício (2025 vs 2026) com receitas previstas/realizadas, despesas por estágio, saldos bancários, obrigações e resultado previdenciário RPPS.
4. `bi_people_metrics`: Métricas consolidadas de RH, folha bruta/líquida, admissões, demissões, horas esperadas vs trabalhadas e absenteísmo.
5. `bi_procurement_metrics`: Métricas de licitações, prazos medianos de tramitação, valores estimados vs adjudicados e economia gerada na disputa.
6. `bi_asset_metrics`: Métricas patrimoniais, tombamento, depreciação acumulada e inventários.
7. `bi_assistant_conversations`: Histórico de perguntas e respostas compiladas pelo Assistente Virtual em linguagem natural com identificação de domínio.
8. `bi_shared_links`: Tokens seguros para compartilhamento de visões analíticas com filtros e validade.

---

## 3. Endpoints REST da API de BI (`bi_api.py`)
- `GET /api/bi/dashboards`: Lista todos os painéis disponíveis e seus layouts.
- `POST /api/bi/dashboards`: Cria ou customiza o layout de um painel analítico.
- `GET /api/bi/alerts`: Retorna os alertas ativos da LRF com semáforos verde/amarelo/vermelho.
- `GET /api/bi/dashboards/executive-lrf`: Painel executivo consolidado da LRF e metas constitucionais.
- `GET /api/bi/dashboards/cash-availability`: Disponibilidade bancária confrontada com obrigações a pagar.
- `GET /api/bi/dashboards/budget-funnel`: Funil da despesa orçamentária e detalhamento da natureza em 4 níveis.
- `GET /api/bi/dashboards/hr`: Indicadores de folha, taxa de turnover, absenteísmo e afastamentos.
- `GET /api/bi/dashboards/procurement`: Desempenho de compras, economia de negociação e contratos a vencer.
- `GET /api/bi/dashboards/assets`: Saldo contábil de bens móveis/imóveis e análise de baixas.
- `GET /api/bi/person-360`: Visão 360º de pessoa física ou jurídica (contribuinte, fornecedor, servidor e cidadão).
- `POST /api/bi/assistant/query`: Consulta ao Assistente Virtual Inteligente (NLP).
- `GET /api/bi/assistant/history`: Histórico de perguntas e respostas dos gestores.
- `GET /api/bi/kiosk/slides`: Configuração de rotação para exibição em TV corporativa.
- `POST /api/bi/share`: Geração de link criptografado de compartilhamento.
- `GET /api/bi/shared/<token>` e `GET /api/public/bi/shared/<token>`: Visualização de painel compartilhado.

---

## 4. Conformidade Normativa (Anexo III)
Todos os 52 itens do módulo `bi` (itens `bi.1` a `bi.52`) foram homologados com status **Implementado** e validados através da suíte automatizada de testes `tests/test_bi.py` (10 testes 100% aprovados).

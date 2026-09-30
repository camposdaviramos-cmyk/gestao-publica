# Validação da ampliação — 23/09/2026

> Atualização de integrações em 23/09/2026: a central administrativa, os conectores PNCP/IBGE e o extrato Siconfi com agenda foram ampliados. Consulte [recursos, testes e pendências da prova de conceito](INTEGRACOES-E-PROVA-DE-CONCEITO.md). Descrições anteriores de ausência total dessas integrações são históricas; isso não significa atendimento integral do edital.

Ambiente: Windows, Python 3.12, Flask/SQLite e Chromium automatizado. Todos os dados de testes foram criados em diretórios temporários, separados do banco local do usuário.

## Resultados

- 57 testes passaram na suíte conjunta: `python -m pytest -q`.
- Mais 2 testes de concorrência/recuperação passaram: `python -m pytest tests/test_erp_recovery.py -q`. Total atual: **59 testes de servidor aprovados**.
- **55 verificações no navegador**: 25 da base original, 8 administrativas e 22 dos módulos integrados.
- Nenhum erro de JavaScript capturado nas três execuções.
- Temas claro/escuro e ausência de rolagem horizontal indevida verificados em 390, 768 e 1.440 px.

## Fluxos exercitados

Execução financeira com saldo insuficiente, liquidação e pagamento limitados, duplicidade e controle de versão; partidas dobradas/estorno; bloqueio de período; entidade não autorizada; sigilo social em lista/detalhe/exportação/BI; estoque negativo, validade, nota repetida, custo médio e transferência em trânsito; depreciação sequencial, residual e inventário; recorrência com último dia do mês; folha, tabelas aprovadas, margem, memória e duplicidade de competência; fases normais/invertidas, fornecedor impedido e contrato de fornecedor não adjudicado; combustível/placa; conflito de agenda e benefício; medições/diário/segregação/retenção; anexos criptografados e exportação que exige assinatura.

A concessão de benefício foi exercitada com baixa automática do insumo e rollback integral quando o estoque é insuficiente. O cancelamento da agenda libera o horário. A última pessoa que editou um parecer não pode aprová-lo.

Dois empenhos simultâneos de R$ 700,00 sobre dotação de R$ 1.000,00 resultaram em apenas um efetivado; o outro foi rejeitado e o saldo ficou correto. Uma restauração de backup preservou vínculos, eventos e partidas do núcleo ERP, com integridade referencial válida e sessões encerradas.

## Desempenho local

`tools/performance_erp_check.py` criou 10.000 fatos sintéticos e 1.200 almoxarifados em base temporária. Em 20 amostras sequenciais por consulta:

| Consulta | Mediana | p95 |
|---|---:|---:|
| Listagem de fatos | 27,35 ms | 34,48 ms |
| Busca textual | 48,86 ms | 57,91 ms |
| Página 60 de almoxarifados | 19,95 ms | 23,82 ms |
| Indicadores consolidados | 91,88 ms | 110,55 ms |

Resultados em `artifacts/performance-erp.json`. São medições locais sequenciais, sem latência de rede e sem concorrência municipal real; não comprovam o desempenho contratual da solução hospedada.

## Evidências

- `artifacts/browser-results.json`
- `artifacts/browser-admin-results.json`
- `artifacts/browser-erp-results.json`
- `artifacts/erp-light-desktop.png`
- `artifacts/erp-dark-desktop.png`
- `artifacts/erp-dark-mobile.png`
- `tests/test_erp.py`, `tests/test_erp_flows.py`, `tests/test_erp_social_stock.py` e `tests/test_erp_recovery.py`

O arquivo `backend-tests.xml` anterior é evidência da base original, não da ampliação.

## Limites

Testes aprovados comprovam os cenários exercitados. Não comprovam atendimento integral aos 1.314 itens do anexo. Permanecem pendentes implementações internas, certificação de infraestrutura, pentest, avaliação completa de acessibilidade, regras legais/tributárias oficiais, migração de bases reais e homologação institucional. Consulte `ANALISE-ANEXO-III.md` e a matriz por cláusula.

# Validação do módulo de estoque — 23/09/2026

- **118 testes de backend aprovados**, zero falhas: `artifacts/backend-inventory-tests.xml`.
- **10 verificações de navegador de estoque**: `artifacts/browser-inventory-results.json`.
- **22 verificações de regressão ERP**: `artifacts/browser-erp-results.json`.
- Nenhum erro JavaScript. Temas claro/escuro verificados em 390, 768 e 1440 pixels; capturas em `artifacts/inventory-light-reports.png` e `artifacts/inventory-dark-reports.png`.
- Cenário com 1.001 almoxarifados, transferência entre unidades e recebimento em competência posterior aprovado. É um teste funcional de quantidade de unidades, não uma certificação de carga concorrente municipal.
- Nenhuma dependência quebrada em `pip check`. Permanecem dois avisos internos de depreciação do pyasn1 utilizado por LDAP3, sem falhas nos testes.

## Instalação e preservação

Backup anterior ao reinício: `data/backups/rio-20260923-203024-966810.db.enc`.

Servidor atualizado em `http://127.0.0.1:8080`, PID 9944. Logs em `artifacts/server-inventory-20260923-203305.out.log` e `.err.log`. A primeira tentativa de smoke test antecedeu a abertura da porta; a repetição após a inicialização confirmou login disponível, scripts carregados e ausência de erro JavaScript.

A comparação com o backup confirmou hashes idênticos nas tabelas de negócio: um usuário, 17 registros originais e nenhuma operação ERP pré-existente. `integrity_check` retornou `ok` e não houve violações de chaves estrangeiras. Nenhuma credencial institucional foi cadastrada e nenhuma publicação ou mensagem externa foi enviada. Os novos cenários de teste utilizaram bases temporárias.

## Matriz

Os 31 requisitos da área de estoque receberam evidências específicas. A matriz geral passou a **82 implementados, 402 parciais, 90 dependências externas e 740 não implementados**. Isso não significa atendimento integral do edital; as outras áreas mantêm suas pendências.

Os parâmetros contábeis precisam ser configurados e aprovados pela administração. A instalação vazia não contém contas, empenhos ou regras contábeis fictícias. NCM e NBS utilizam tabelas públicas oficiais, com origem e versão documentadas no [roteiro de estoque](ESTOQUE-E-AQUISICOES.md).

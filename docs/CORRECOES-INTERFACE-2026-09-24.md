# Correções prioritárias de interface — 24/09/2026

Escopo: finance, control, people, social e bi. A entrega não comprova conformidade integral com o Edital ou o Anexo III.

- Cabeçalhos, abas, botões, tabelas, formulários e temas usam os tokens do sistema. Tabelas extensas rolam dentro do painel em telas menores.
- 154 eventos inline foram substituídos por um registro explícito de ações, sem eval e sem relaxar a CSP.
- Cliente autenticado comum: CSRF nas gravações, verificação de resposta HTTP, tratamento de erros e proteção contra cliques repetidos.
- Funções ausentes foram conectadas a formulários e consultas existentes: cópia/substituição/reintegração, detalhes, CAT/PPP/EPIs, pendências cadastrais, nota fiscal, cheque e adiantamento.
- Cadastros sociais deixam de inserir nomes, documentos, pareceres e responsáveis fictícios provenientes dos antigos prompts.
- Adiantamentos são lidos do banco e a prestação de contas usa o ID da linha. Os valores devem totalizar o adiantamento, sem registrar prestação duplicada ou de ID inexistente.
- BI: Enter no assistente, compartilhamento em modal, projeção por configuração dos painéis, saída por Esc e encerramento ao navegar.
- Leitores financeiros não podem gravar; consultas privadas de Pessoas requerem acesso ao módulo. A fila de atualizações do portal usa a tabela correta.
- A tela SIAFIC informa a pendência AUD-005, em vez de declarar autenticação e assinatura inexistentes.
- Anexo III: painel de progresso por módulo, histórico preservado e percentual sem crédito parcial, incluindo Não comprovado.

## Verificação

57 testes pytest distintos passaram nas suítes selecionadas e regressões finais (relatórios tests.xml e finance-final.xml). Os relatórios se sobrepõem e não devem ter suas contagens somadas.

Chromium em instalação temporária: 33 abas, 5 módulos, 1440 px e 390 px, temas claro/escuro; sem erros JavaScript ou violações CSP. Fluxos positivos: escrituração, nota fiscal, cheque, adiantamento/prestação de contas, cópia de servidor, cadastro familiar, plano de ação, compartilhamento, assistente por Enter e TV. Fluxo negativo: conta contábil inválida conserva o formulário e apresenta o erro retornado. Um HTTP 400 no log é esperado por esse teste negativo.

Evidências: artifacts/ui-revisao-20260924/browser.json, screenshots, tests.xml, finance-final.xml; script reproduzível browser_check.py. Testes não criam dados na instalação operacional.

## Pendências preservadas

AUD-002 e AUD-046 têm correção verificada no escopo de interface. AUD-001, AUD-003, AUD-004 e AUD-029 receberam correções parciais. Os cálculos demonstrativos, simulações de integrações externas, titularidade, assinatura, nuvem e demais pendências documentadas não foram convertidos em conformidade integral. Cada requisito mantém seu status de aceite; a evolução desta entrega está separada no painel da página annex.

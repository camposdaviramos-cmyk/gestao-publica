# Estoque, requisições e aquisições

O módulo **Gestão de estoque** inclui os cadastros, operações e relatórios dos 31 requisitos de estoque do Anexo III. A validação desta área não representa conclusão dos demais módulos do edital. A matriz geral preserva suas pendências.

## Configuração inicial

1. Cadastre as contas analíticas em Finanças. Em **Contabilização do estoque**, defina as contas de débito/crédito para Entrada, Saída, Trânsito de saída, Trânsito de entrada, Devolução, Ganho de inventário, Perda de inventário e Baixa de obsoleto. Outra pessoa com aprovação em estoque e finanças deve aprovar cada regra. Pode existir uma regra padrão da entidade e uma substituição por almoxarifado.
2. Cadastre almoxarifados, materiais e localizações. Uma unidade bloqueada não aceita registros vinculados ou movimentos. Administradores podem configurar **Autorizações por usuário** no detalhe de cada almoxarifado e órgão requisitante. Os acessos de módulo e entidade permanecem necessários.
3. Cadastre órgãos, responsáveis e centros de custo. A hierarquia de centros não aceita ciclos nem mistura órgãos. Defina cotas mensais por material ou grupo, em quantidade e/ou valor. A aprovação de uma requisição calcula também as cotas dos centros superiores e registra os alertas de excesso no histórico e nas notificações.
4. Configure reposição por quantidade ou consumo mensal no almoxarifado. Use **Regras de reposição por material** para substituir o padrão em casos específicos. Quantidade utiliza mínimo, médio, máximo e percentual sobre o máximo. Consumo utiliza meses completos anteriores à data final da consulta, quantidade de meses do histórico e meses de cobertura mínima/máxima.

As regras contábeis exigem definição e aprovação institucional. O sistema não escolhe contas públicas em nome do contador. Sem regra aprovada, uma movimentação não é efetivada.

## Requisição de material

Cadastre uma requisição da finalidade Material e seus itens. Outra pessoa aprova a requisição e os itens. No detalhe de cada item, **Entregar material** aceita entregas parciais e atualiza o saldo pendente. **Devolver material** exige a entrega original, data, quantidade e validade quando controlada. A devolução restaura o estoque pelo custo da entrega original e impede excesso ou duplicação. **Cancelar saldo pendente** exige justificativa. As entregas anteriores ficam preservadas.

## Pedido de compra e licitação

Cadastre a requisição da finalidade Compra e aprove-a. Em **Vínculos de compra e licitação**, associe seus itens aos itens de uma licitação em andamento e registre número/data da pesquisa de preços. A aprovação verifica os saldos do pedido e do item licitado. Esses quantitativos passam a integrar o saldo virtual.

Após homologação e empenho, cadastre a autorização de fornecimento e seus itens, incluindo o vínculo de compra quando existente. A aprovação confere fornecedor adjudicado, quantidade disponível, preço adjudicado e saldo financeiro do empenho. Uma autorização usada em fornecimento preserva sua vinculação ao pedido.

**Acompanhar aquisição**, no pedido, na autorização e na nota fiscal, apresenta pesquisa de preços, processo/modalidade, fases registradas, datas de solicitação de recursos e pareceres, empenho, quantidades autorizadas/recebidas/canceladas e notas fiscais. Datas não cadastradas são apresentadas como ausentes, sem preenchimento presumido.

## Recebimento de notas

Cadastre a nota por emitente, número, série e modelo. Chave eletrônica também é conferida contra duplicações. Notas de material exigem autorização de fornecimento; notas de serviço e patrimônio exigem empenho.

Na nota de material, **Sugerir itens da autorização** carrega o saldo autorizado. Confira quantidades, lote e validade. Outra pessoa com aprovação financeira efetiva o recebimento. A operação realiza, em uma única transação:

- liquidação do empenho;
- entrada física e valorização do estoque;
- partidas contábeis das entradas;
- baixa do saldo autorizado;
- registro dos vínculos e trilha de auditoria.

Uma falha em qualquer etapa desfaz todas elas. Uma nota já recebida não pode ser efetivada novamente. Notas de patrimônio geram fichas individuais dos bens; notas de serviço liquidam o empenho sem gerar material fictício. Entradas diretas de compra que informam fornecedor/documento/empenho também liquidam automaticamente, com aprovação por outro usuário.

## Transferência e inventário

A saída de uma transferência retira o material do estoque disponível e o mantém em trânsito. O recebimento no destino baixa esse trânsito uma única vez. A data do recebimento é informada na operação. Chamadas de API sem indicação utilizam a data do movimento. Não é permitido consumir material ainda em trânsito.

Para ajustar inventário, cadastre a portaria, publicação, vigência e integrantes com nome, CPF e cargo. Outra pessoa formaliza a comissão. Vincule a comissão ao inventário e submeta o ajuste a outro usuário. Comissões formalizadas não admitem alteração ou remoção dos integrantes.

Materiais obsoletos não podem ser movimentados nas rotinas comuns. **Baixar material obsoleto** exige aprovação separada, justificativa e regra contábil. As operações preservam a ordem cronológica do custo médio por material/almoxarifado.

## Consultas e relatórios

Em **Saldos de estoque**, selecione saldos/reposição, consumo/ABC, movimentos unificados ou balancete mensal. Os filtros de almoxarifado, material, grupo, subgrupo e período podem ser combinados. As consultas e os formulários funcionam nos temas claro e escuro. Os relatórios exportam CSV e PDF e respeitam a configuração institucional de assinatura.

O saldo virtual soma o físico às aquisições licitatórias pendentes, descontando quantidades já autorizadas para não contar duas vezes. Trânsito aparece separadamente. O saldo físico respeita a data final; os compromissos de compra utilizam a situação atual, indicada na consulta. O balancete apresenta saldo inicial, entradas, saídas e saldo final por mês; selecione janeiro a dezembro para o exercício completo.

A curva ABC considera consumo líquido pelo custo das saídas, descontadas devoluções vinculadas no período. A inclui até o item que alcança 80% do valor; B até 95%; C os demais. A média considera os meses civis abrangidos pelo período.

## Classificações oficiais

O cadastro permite buscar NCM e NBS por código ou descrição e selecionar o código oficial. A versão inicial foi obtida em 23/09/2026: 10.515 NCM de oito dígitos e 920 NBS de nove dígitos. São preservadas as descrições e vigências fornecidas pela fonte. A consulta **Tabelas oficiais NCM / NBS** mostra origem, versão e SHA-256; administradores podem atualizá-las sem credenciais externas. Falhas preservam a versão anterior.

- [NCM — Siscomex, download oficial](https://portalunico.siscomex.gov.br/classif/api/publico/nomenclatura/download/json).
- [NBS 2.0 — arquivos oficiais do MDIC](https://www.gov.br/mdic/pt-br/assuntos/sdic/comercio-e-servicos/nbs-nomenclatura-brasileira-de-servicos/arquivos).

Os arquivos oficiais desta versão estão em `schemas/classifications/`. Atualizações administrativas ficam versionadas no banco, com autor, data, origem e hash.

## Evidências de validação

`tests/test_inventory.py` e `tests/test_inventory_controls.py` verificam entrega parcial, devolução, cotas hierárquicas, permissões, comissões, notas de material/serviço/patrimônio, duplicidade, transações, saldo virtual, NCM/NBS, reposição e relatórios. O cenário de 1.001 almoxarifados verifica transferência entre unidades, trânsito e recebimento em meses diferentes.

`tools/browser_inventory_check.py` executa recebimento de nota, entrega, devolução, cancelamento, permissões, acompanhamento da compra, quatro relatórios, CSV/PDF e escolha de NCM pela interface. Verifica os temas claro/escuro em 390, 768 e 1440 pixels. Usa banco temporário e porta 8096; não altera os dados reais.

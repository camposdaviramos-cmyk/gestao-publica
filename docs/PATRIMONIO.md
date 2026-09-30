# Patrimônio — implementação do Anexo III

O módulo cobre integralmente os itens 1 a 27 da seção de Patrimônio do Anexo III. A operação usa eventos imutáveis, sequência diária por bem, posição derivada, partidas contábeis simultâneas, segregação entre preparação e aprovação e bloqueio por inventário físico em andamento.

## Base normativa usada

- MCASP vigente, 11ª edição: https://www.gov.br/tesouronacional/pt-br/contabilidade-e-custos/manuais/manual-de-contabilidade-aplicada-ao-setor-publico-mcasp-1
- PCASP vigente: https://www.gov.br/tesouronacional/pt-br/contabilidade-e-custos/federacao/plano-de-contas-aplicado-ao-setor-publico-pcasp-1
- TCE-RJ, PCA municipal 2025 analisada em 2026, Deliberação 277/17 e Anexo VII para responsáveis por bens patrimoniais, almoxarifado e tesouraria: https://www.tcerj.tc.br/portalnovo/pagina/prestacao_de_contas_anual_de_gestao_pca_2025
- Arquivo oficial do Anexo VII publicado pelo TCE-RJ: https://www.tcerj.tc.br/portal-tce-webapi/api/arquivos/fd7763f1-f948-44e3-9bd5-08de46d500f2/download

## Cadastros e controle físico

As classificações exigem conta analítica do ativo e conta de depreciação acumulada, vida útil em meses ou anos, percentual residual, natureza e critério de proporcionalidade. Responsáveis registram CPF, forma de ingresso e vínculo. Localizações apontam para responsáveis ativos. Comissões de Avaliação, Inventário e Recebimento possuem vigência, ato de designação e integrantes, e só podem ser formalizadas por outro usuário.

Os bens distinguem propriedade municipal, locação e comodato. O cadastro guarda placa, registro, matrícula, tombamento, localização, responsável, comissão, ingresso, valor, método, vida útil, residual, processo, empenho, fornecedor e nota fiscal. A efetivação cria a primeira posição e o evento de ingresso; aquisições validam processo homologado, empenho e fornecedor. Recebimentos marcados para conferência ficam impedidos de depreciar até confirmação segregada.

Cessões, comodatos, locações, seguros, planos e registros de manutenção, garantias e devoluções integram o histórico do bem. Transferências individuais ou em lote aceitam seleção explícita, localização, classificação e faixa de placas. Doações e cessões temporárias entre entidades criam o controle correspondente na unidade gestora de destino; cessões temporárias possuem retorno controlado.

## Valores, depreciação e contabilidade

Valores complementares aceitam vários empenhos cuja soma deve coincidir com o custo incorporado. Reavaliação e redução ao valor recuperável calculam a depreciação proporcional até a data, baixam o ciclo anterior e iniciam novo ciclo com método, vida útil, residual, situação e produção revisados.

A depreciação suporta quotas constantes e unidades produzidas. Em “Dias corridos”, o mês é proporcional aos dias disponíveis. Em “Mês integral”, a depreciação começa no primeiro dia do mês seguinte ao ingresso ou avaliação. Lotes mensais exibem valores bruto, acumulado, residual, depreciável, depreciação do período, líquido antes/depois, contas e totais antes de gerar eventos.

Regras patrimoniais aprovadas configuram contrapartidas por fato e classificação. Ingresso, depreciação, reavaliação, redução, complemento, baixa e doação geram partidas na mesma transação do evento. Reclassificações movem custo e depreciação entre as contas das classificações. Estornos só alcançam o último grupo vigente, exigem outro usuário, revertem todas as partidas e restauram o retrato anterior.

## Inventário, relatórios e alertas

A abertura do inventário seleciona bens por classificação, descrição, conservação, localização e situação. Cada linha permite registrar localização, responsável, conservação, situação, conformidade ou baixa. Enquanto a linha estiver aberta, o bem não recebe outros eventos. O encerramento exige todas as linhas conferidas e outro usuário.

A tela e a API fornecem:

- posição e histórico completo do bem, incluindo retratos antes/depois e partidas;
- depreciação e pendências;
- recebimentos aguardando conferência;
- visão contábil por conta, classificação e localização, com saldo inicial, ingressos, avaliações, depreciação, baixas, débitos, créditos e saldo final;
- histórico filtrado por período, ingresso, movimento e empenho;
- termos de responsabilidade por responsável, localização, situação e conservação;
- demonstrativo TCE-RJ de responsáveis por bens conforme o Anexo VII aplicável à Deliberação 277/17;
- CSV e PDF sujeitos às regras de assinatura configuradas.

Ao consultar a central de notificações, o sistema verifica automaticamente ingressos não efetivados, recebimentos pendentes e competências de depreciação atrasadas. A chave composta do alerta impede duplicidade para o mesmo bem, período, motivo e usuário.

## Evidências

- Regras e posições: asset_core.py
- Eventos contábeis e estornos: asset_accounting_operations.py
- Inventário, guarda e transferências: asset_management_operations.py
- Relatórios, alertas e lotes: asset_api.py
- Estrutura imutável: asset_schema.sql
- Interface light/dark: static/assets-ui.js e static/assets.css
- Testes: tests/test_assets.py e tests/test_erp.py
- Teste visual: tools/browser_assets_check.py

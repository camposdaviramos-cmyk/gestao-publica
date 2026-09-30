# Análise do Anexo III e ampliação do sistema

> Atualização de integrações em 23/09/2026: a central administrativa, PNCP/IBGE, Siconfi com agenda, LDAP, assinatura A1 e envio/consulta de XML eSocial foram ampliados. Consulte [recursos, testes e pendências da prova de conceito](INTEGRACOES-E-PROVA-DE-CONCEITO.md). Descrições anteriores de ausência total dessas integrações são históricas; isso não significa atendimento integral do edital.

Foram catalogadas as 100 páginas de `ANEXO III.pdf` (páginas impressas 84–183), junto ao recorte original de 14 páginas do edital. O catálogo preserva o texto de 1.314 linhas numeradas, incluindo cabeçalhos e subitens que recebem numeração no documento. A seção de assistência social salta de 290 para 300 no original; não foram inventados os itens ausentes dessa sequência.

**O sistema ainda não atende integralmente ao Anexo III.** A ampliação implementa fluxos operacionais verificáveis, mas não constitui solução homologada para produção municipal nem comprovação de aprovação na prova de conceito. A matriz é conservadora: um cadastro, campo ou botão isolado não comprova todos os requisitos de uma cláusula.

## Comparação com a base anterior

A base anterior possuía autenticação, permissões, dupla custódia de registros administrativos, auditoria, chamados, implantação, publicações, relatórios e backup. Orçamento, contabilidade e pessoal eram cadastros preliminares. Não existiam motores específicos de estoque, patrimônio, frota, assistência social, contratação ou medição de obras.

| Área nova | Funcionamento implementado | Limites relevantes |
|---|---|---|
| Execução financeira | Contas, fontes, planejamento, programas, dotações, créditos/reduções, empenhos, liquidações, pagamentos, receitas, partidas dobradas, estorno e fechamento de período | Sem execução contábil oficial completa, eventos contábeis automáticos entre todos os módulos, restos a pagar, conciliação bancária, PCASP/MSC e demonstrativos legais completos |
| Controle interno | Obrigações, recorrências mensais, ocorrências, justificativas, encerramento/reabertura, verificações, planos de ação, convênios e pareceres preservados após aprovação | Sem sincronização SICONFI/CAUC, catálogo oficial de regras, envio de e-mails ou calendário visual completo |
| Gestão de pessoas | Cargos/vagas, vínculos, dependentes, movimentos, afastamentos, parâmetros e faixas aprovadas; folha RPPS parametrizada, memória de cálculo, consignações e contribuições | Sem cálculo integral de RGPS, férias, rescisões, décimo terceiro, retroativos, eSocial, PPP/CAT, portal do servidor e atualização automática de tabelas oficiais |
| Compras e contratos | Fornecedores impedidos, processos, itens, propostas, fases com inversão motivada, abertura por dias úteis/feriados, adjudicação, contratos, aditivos e cópia de PCA | Sem motor completo para todas as modalidades e legislações, SRP, PNCP, documentos oficiais e integração orçamentária automática |
| Estoque | Almoxarifados, materiais, entradas, saídas, devoluções, transferências em trânsito, recebimento único, média de custo, contagem/ajuste, bloqueios e sugestão até o mínimo | Sem todos os filtros/controles por lote, permissões por almoxarifado, requisições completas e contabilização/liquidação automática |
| Patrimônio | Classes com contas e vida útil, bens próprios/alugados/comodato, depreciação por quotas ou produção, residual, transferência, baixa e bloqueio por inventário | Sem reavaliação/impairment, todos os movimentos em lote, transferência entre entidades, integração contábil e demonstrativos TCE/RJ |
| Frota | Motoristas, CNH, veículos vinculados ao patrimônio, reservas, viagens, abastecimentos, manutenção, cronologia de leituras, troca de placa e bloqueio temporal | Sem tanques próprios completos, cartões de combustível, acessórios, multas, todos os painéis e recortes por repartição |
| Assistência social | Pessoas, famílias, integrantes, programas, agenda, cancelamento/atendimento, prontuário sigiloso, benefícios, saída automática do estoque, habitação, OSC e prestação parametrizada | Sem todos os 410 itens: CadÚnico/CECAD/SICON/Sibec, RMA, rede de proteção, acolhimento, cursos, classificação habitacional/vulnerabilidade, georreferenciamento e assinatura ICP-Brasil completos |
| Obras públicas | Obra, itens, BDI/desconto, datas do cronograma, diário aprovado, medição sequencial limitada a 100%, pagamentos, retenção e documentos | Sem revisão/importação completa de planilhas, colaboração restrita por obra, mapas, projeção completa de aportes e portal público integrado |
| Pregão eletrônico | Registro da plataforma, identificador externo e preparação local do pacote | Não transmite dados às plataformas externas nem conduz disputa eletrônica |
| BI | Contagens autorizadas, execução financeira mensal, saldo bancário, obrigações liquidadas a pagar, folhas aprovadas e valores de obras | Não calcula todos os indicadores fiscais, comparações e alertas exigidos; não há assistente virtual ou projeção em TV |

## Regras transversais

- Entidade e exercício são parâmetros obrigatórios do núcleo integrado. Administradores têm acesso às entidades; outros usuários precisam de vínculo explícito e permissão de módulo. Permissões novas não foram concedidas automaticamente aos grupos operacionais antigos.
- Vínculos são validados por tipo e entidade. Movimentos financeiros não usam dotação/liquidação/conta bancária de outro exercício como substituto de uma rotina de restos a pagar.
- Operações escrevem em transação e verificam a versão do registro. Falhas desfazem alterações e saldos. O histórico de eventos não pode ser editado ou excluído pelos endpoints.
- Valores monetários são armazenados em centavos; quantidades, em milionésimos. Cálculos usam Decimal com arredondamento explícito. Depreciação ajusta a última parcela ao saldo residual.
- Autor e último editor/submissor não podem aprovar as operações que exigem outro responsável.
- Prontuários marcados como sigilosos são filtrados no servidor, inclusive em detalhes, exportações e indicadores. Não podem perder a marca de sigilo pela edição comum.
- Anexos são criptografados dentro do banco e entram no backup. O download exige autorização ao registro. Limite atual de 500 KB por documento; formatos PDF, JPG, PNG e Office. A verificação de assinatura de arquivo não substitui antivírus ou assinatura digital.
- Exportações novas em CSV/PDF respeitam bloqueio de assinatura digital obrigatória. Não geram assinatura simulada.
- O desenho utiliza as mesmas cores, componentes e temas claro/escuro da base, sem CDN. A navegação e as tabelas foram verificadas em 390, 768 e 1.440 pixels.

## Materiais para revisão

1. `anexo-iii-extraido.txt`: extração textual das 100 páginas.
2. `anexo-iii-paginas.json`: texto separado por página física do PDF.
3. `anexo-iii-itens.json`: cláusulas numeradas, texto completo e página de origem.
4. `anexo-iii-conformidade.json`: comparação anterior/atual, situação e pendências por item.
5. `MATRIZ-ANEXO-III.md`: matriz legível fora do sistema.
6. Menu **Anexo III · cobertura**: consulta e busca das mesmas cláusulas dentro da aplicação.

O percentual contratual de atendimento não deve ser deduzido simplesmente dos totais dessa matriz: há requisitos compostos, linhas que são subitens e critérios de avaliação da comissão. A documentação não é um laudo de conformidade.

## Trabalho ainda necessário

Há pendências internas de implementação e pendências externas. As internas incluem os fluxos especializados e relatórios listados acima; não se resumem a configuração ou credenciais. As externas incluem contratação e comprovação da nuvem, certificados, homologação das integrações, migração de bases reais, treinamento e aceite.

A infraestrutura local SQLite/Waitress não comprova redundância geográfica, certificações ISO/SOC, WAF, XDR, operação 24x7, recuperação regional ou desempenho com a carga municipal real. Também não foi enviado dado a banco, PNCP, eSocial, plataforma de pregão ou serviço de mensagens durante esta ampliação.

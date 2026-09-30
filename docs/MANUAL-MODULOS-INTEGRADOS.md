# Operação dos módulos integrados

Abra **Módulos integrados** no menu lateral. Escolha a entidade e o exercício antes de cadastrar. Os registros administrativos antigos continuam nas páginas originais; não são convertidos automaticamente em fatos contábeis, folha ou contratos.

## Acesso

Em **Grupos e permissões**, atribua leitura/escrita/exclusão/aprovação aos módulos necessários. Em **Módulos integrados → Entidades e acessos**, vincule cada usuário às entidades permitidas. Salvar esses vínculos encerra as sessões desse usuário, para que a nova autorização entre em vigor. O grupo administrativo acessa todas as entidades ativas.

Cadastros vinculados exigem leitura do módulo de origem. Por exemplo, quem opera estoque com fornecedor vinculado precisa consultar fornecedores em Compras e contratos. Aprovações segregadas exigem outra conta autorizada, diferente do criador e de quem realizou a última edição ou submissão.

## Cadastros e operações

Cada área apresenta abas para seus cadastros, busca por código/descrição, paginação e exportação. **Novo registro** abre os campos específicos. Os seletores de vínculo carregam até 100 opções; use a busca junto ao seletor para localizar outras.

Abra a seta de um registro para consultar campos, saldos, documentos e histórico. Rascunhos podem ser editados. A efetivação acontece pelos botões de operação. O servidor rejeita operação repetida, saldo insuficiente, situação incompatível e versão desatualizada. Registros com efeitos ou vínculos ativos não podem ser apagados pela exclusão comum.

## Execução financeira

Cadastre contas contábeis e fontes; depois fornecedores, dotações e contas bancárias. Cadastre o empenho e execute **Empenhar**. A liquidação exige empenho efetivado e saldo suficiente. O pagamento exige liquidação, conta com a mesma fonte e saldo bancário. Os valores pagos não podem superar a liquidação.

Lançamentos contábeis usam uma conta a débito e outra a crédito. A operação de estorno acrescenta partidas inversas e preserva o original. O balancete consolida essas partidas. **A execução financeira ainda não gera automaticamente toda a escrituração contábil requerida pelo edital.**

Um fechamento bloqueia fatos com data igual ou anterior ao limite dentro do exercício. Suplementações/reduções exigem justificativa. Não use estes cadastros como substitutos de prestação de contas oficial ou demonstrações fiscais ainda ausentes.

## Controle interno

Cadastre uma obrigação com vencimento inicial, intervalo em meses e número de ocorrências. A geração é única e trata meses curtos: uma recorrência iniciada em 31 de janeiro passa pelo último dia de fevereiro. As ocorrências podem ser justificadas, encerradas e reabertas. Pareceres conclusivos ficam bloqueados após aprovação por outro usuário.

## Pessoas e folha

Cadastre cargos/vagas, vínculos ativos, dependentes e movimentos. Configure parâmetros RPPS e faixas de IRRF para a competência, com fundamentação institucional. As faixas devem cobrir a base sem lacunas nem sobreposições, com a última faixa sem teto (limite superior zero). Outra pessoa aprova os parâmetros.

Crie a folha da competência, calcule e peça a aprovação. A memória preserva parâmetros, verbas, bases e consignações recusadas por margem. A competência calculada não aceita novos movimentos. O motor atual é RPPS parametrizado: não presume alíquotas vigentes nem implementa todas as incidências, reduções tributárias, benefícios e obrigações oficiais. Vínculos RGPS bloqueiam esse cálculo.

## Compras

Cadastre fornecedor, processo, itens e propostas. Informe todos os dados necessários antes de avançar o processo. O cálculo de abertura considera dias úteis e feriados institucionais. A ordem padrão passa pelo julgamento antes da habilitação; habilitar a inversão exige parecer técnico.

A adjudicação e a homologação exigem aprovação segregada. Cada item precisa de proposta adjudicada antes de homologar o processo. Um contrato só entra em vigência com processo homologado e fornecedor com item adjudicado. Impedimento do fornecedor e supressão acima do valor contratual são bloqueados.

## Estoque e patrimônio

Cadastre almoxarifados e materiais. A entrada informa quantidade, preço e validade quando controlada. A saída usa custo médio e não admite estoque negativo. Uma transferência retira o saldo da origem e permanece **Em trânsito** até o recebimento, que só ocorre uma vez.

O ajuste por contagem exige outro usuário. Almoxarifados bloqueados e materiais obsoletos não movimentam. As sugestões de compra recompõem até o mínimo cadastrado.

No patrimônio, configure classes, contas, vida útil e residual. A depreciação segue competências mensais consecutivas, por quotas constantes ou produção. O sistema preserva o residual e ajusta centavos na parcela final. Inventário aberto bloqueia movimentos do local. Transferência informa destino/responsável; baixa exige outro usuário. Reavaliação e outros fluxos completos ainda não estão disponíveis.

## Frota

Vincule o veículo a um bem patrimonial e cadastre seus motoristas. Registre viagens, reservas, abastecimentos e serviços. O sistema verifica cronologia do medidor, combustível, capacidade do tanque, bloqueio temporal e bem baixado. A viagem sinaliza CNH vencida. A troca de placa mantém o histórico.

## Assistência social

Cadastre pessoas, famílias, integrantes e programas. A agenda rejeita conflitos da pessoa ou do profissional e feriados cadastrados. Cancelar exige motivo e libera o horário; um atendimento cancelado não pode ser efetivado.

Um atendimento sigiloso exige a permissão adicional **Prontuário social sigiloso**. A mesma restrição vale para consultas e exportações.

Benefícios podem ter valor, carência, capacidade e insumo. Se houver insumo, configure a quantidade por concessão e escolha o almoxarifado na entrega. A aprovação exige outra pessoa com autorização social e de estoque. A saída e a concessão ocorrem na mesma transação: se faltar saldo, nenhuma das duas é efetivada.

Há cadastros básicos de inscrição habitacional, OSC, planos e prestações. Eles não substituem os fluxos completos de CadÚnico, RMA, acolhimentos, rede de proteção e classificação habitacional ainda pendentes.

## Obras

Cadastre obra e itens da planilha, com quantidade, preço, BDI/desconto e datas. Registre diários e peça aprovação. A medição precisa de diário aprovado no período, sequência de datas e saldo contratado suficiente. Uma medição submetida reserva a quantidade para impedir que outra ultrapasse 100% do item.

Após outra pessoa aprovar, registre o pagamento. A diferença fica como retenção. Liberações parciais ou totais exigem data de recebimento definitivo da obra e decurso do prazo configurado, sempre limitadas ao saldo.

## Documentos, BI e pregão

Anexe PDF, imagens ou Office de até 500 KB no detalhe do cadastro. O conteúdo é criptografado e protegido pelas permissões do registro. CSV/PDF novos são emitidos por cadastro; uma exigência de assinatura digital bloqueia a emissão até existir serviço homologado.

O BI calcula valores de fatos efetivados e folhas aprovadas, além de contagens autorizadas. Os números não são demonstrativos oficiais de limites fiscais. O módulo de pregão prepara registros locais; não envia dados para plataformas externas.

Consulte **Anexo III · cobertura** para identificar o que ainda falta em cada cláusula.

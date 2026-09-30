# Manual de uso

## Acesso e navegação

No primeiro acesso local, crie uma conta com nome, e-mail e senha forte. Use uma conta individual por servidor. A senha deve respeitar o mínimo configurado, conter letras, números e dois símbolos. Cinco tentativas inválidas bloqueiam a conta por quinze minutos na configuração inicial; a administração pode alterar esses parâmetros.

O menu lateral apresenta as páginas permitidas para o perfil. Use **Ctrl+K** (ou Cmd+K) para localizar uma página. No celular, abra o menu pelo botão do cabeçalho. O botão de sol/lua alterna o tema. A preferência é salva apenas neste navegador. A ajuda contextual está acessível pelo cabeçalho e pelo menu.

O perfil, no canto superior direito, permite trocar a senha e sair. Após trocar a senha, todas as sessões daquela conta são encerradas. O servidor valida os horários de acesso a cada solicitação, usando o fuso de Brasília.

## Planejamento, registros e implantação

1. Escolha um módulo e selecione **Novo registro** ou **Nova ação**.
2. Preencha título, unidade, situação e campos específicos. Valores têm duas casas decimais e são persistidos em centavos.
3. Salve. Se houver dupla custódia, a solicitação vai para Aprovações e ainda não altera o cadastro.
4. Use a busca, o filtro de situação e a paginação para consultar a base.
5. Os botões de visualização, edição e exclusão aparecem conforme o perfil. A exclusão exige conferência explícita no formulário.

Em planejamento, preencha programa, ação, exercício, meta física, indicador e prazo. O gráfico do painel mostra valores previstos por mês de cadastro, não execução contábil. Em registros contábeis, é possível vincular o ID de uma ação orçamentária aprovada. Não é permitido excluir uma ação vinculada.

Os cadastros originais de documentos contábeis e pessoal continuam preliminares. As novas rotinas estão em Módulos integrados: consulte `MANUAL-MODULOS-INTEGRADOS.md`. Há folha RPPS parametrizada e execução financeira básica; a matriz do Anexo III identifica as rotinas oficiais ainda pendentes.

Em implantação, registre marcos, responsáveis, fases e prazos. A agenda do painel exibe os próximos marcos em aberto. Em ordens de serviço, número, serviço, quantidade e localidade são obrigatórios.

## Dupla custódia

Outro usuário com permissão **Aprovar** no módulo deve abrir a solicitação, conferir o conteúdo, escolher a decisão e informar justificativa. Solicitantes não podem aprovar suas próprias solicitações. Aprovação efetiva executa a operação; rejeição preserva a base.

Caso um registro já tenha sido alterado desde a solicitação, a aprovação é bloqueada por conflito de versão. Rejeite a solicitação antiga e envie outra com os dados atualizados. Solicitações de usuários que perderam sua permissão de gravação/exclusão não podem ser efetivadas.

## Chamados

Ao abrir um chamado, descreva a ocorrência e selecione a prioridade. A aplicação calcula os prazos de resposta e solução conforme o edital. O limite de prioridade é mantido após a abertura para preservar o SLA original.

Abra os detalhes para acompanhar prazos e mensagens. Edite a situação para iniciar o atendimento. Use o campo de solução provisória quando não houver resolução imediata. Antes de marcar **Resolvido**, informe a solução definitiva com pelo menos dez caracteres. Atualizações e comentários geram notificações internas para o solicitante; o indicador é atualizado a cada trinta segundos enquanto a página está visível.

## Usuários e grupos

Crie grupos com permissões de consulta, gravação, exclusão e aprovação em cada módulo. As permissões individuais substituem as herdadas apenas quando a opção **Personalizar** estiver marcada. Personalização sem nenhuma operação marcada nega acesso ao módulo.

Dias da semana e faixa de horário podem limitar o acesso. Alterações do usuário encerram suas sessões e desbloqueiam tentativas anteriores. Senha redefinida pela administração exige troca. O grupo Administração é reservado. A aplicação preserva uma conta administrativa ativa sem restrições individuais.

## Relatórios

Escolha módulo e datas de criação, considerando o horário de Brasília. Consulte a prévia e exporte PDF, XLSX, CSV ou DOCX. Na impressão, use o diálogo do navegador para escolher impressora, número de cópias e páginas. Em consultas maiores que dez mil registros, reduza o período.

Configure o certificado em Integrações externas → Assinatura digital A1. A exigência pode abranger todos os relatórios, um módulo ou um relatório específico. PDFs recebem PAdES; outros formatos são entregues em ZIP com assinatura CMS destacada e original. Sem certificado ativo ou autorização do assinante, a emissão exigida permanece bloqueada. Consulte [LDAP, assinatura e eSocial](LDAP-ASSINATURA-ESOCIAL.md).

## Publicações

Crie o conteúdo no módulo Publicações. A situação **Publicado**, após aprovação quando exigida, disponibiliza o conteúdo em `/portal`. Rascunhos e conteúdos arquivados não aparecem. Confira cuidadosamente título, valor e descrição: tudo que for publicado nesse módulo será público. Não inclua dados pessoais ou conteúdo sigiloso destinado apenas à administração.

## Capacitação, atalhos e auditoria

Os tutoriais podem ser lidos quantas vezes forem necessárias. **Marcar como concluído** salva o progresso na conta do usuário. Vídeos e treinamento presencial permanecem etapas de implantação.

Em **Visão geral → Acesso rápido → Meus atalhos**, cadastre URLs HTTPS das ferramentas usadas na rotina. Atalhos são individuais e abrem em outra aba.

A Auditoria permite buscar por usuário, operação ou módulo e consultar os detalhes registrados. Não há botão de edição ou exclusão de eventos.

## Administração técnica

Use **Gerar backup** para criar uma cópia cifrada e o botão de download para guardá-la. A restauração é executada pelo operador do servidor, conforme o manual de implantação. As rotinas de manutenção disponíveis verificam a integridade e atualizam estatísticas dos índices; sua execução é registrada na auditoria.


## Estoque e aquisições

Requisições, cotas, permissões por unidade, comissões, vínculo com licitação, autorização, recebimento parcial de notas, liquidação/contabilização simultâneas, relatórios e tabelas oficiais NCM/NBS estão descritos no [roteiro de estoque e aquisições](ESTOQUE-E-AQUISICOES.md).

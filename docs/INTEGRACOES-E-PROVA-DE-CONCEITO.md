# Central de integrações — implementação e limites da prova de conceito

Atualização: 23/09/2026. Este documento registra os recursos efetivamente implementados. **O sistema ainda não atende integralmente ao edital e ao Anexo III e não deve ser apresentado como integralmente homologado.** Há pendências de implementação interna além das dependências de terceiros. A matriz por cláusula permanece em `MATRIZ-ANEXO-III.md`.

## Acesso e configuração

Entre com uma conta do grupo Administração e acesse **Configurações → Abrir central**, ou **Integrações externas** no menu. Selecione entidade e ambiente. Homologação e produção possuem registros e credenciais independentes; todos os conectores começam desativados. O exercício selecionado na central filtra os cadastros de origem das publicações e os extratos sincronizados.

Os campos variam por serviço. Senhas, chaves privadas e arquivos PFX/P12 são criptografados com a chave de instalação e nunca são devolvidos ao navegador. Deixar a senha vazia mantém o valor atual; preencher substitui; a opção Remover exclui a credencial. Alterações simultâneas verificam a versão da configuração. Auditoria registra nomes dos campos alterados, sem registrar os seus valores secretos. Segredos não são enviados para serviços cujo conector não esteja implementado.

| Serviço | Disponível | Ainda necessário |
|---|---|---|
| PNCP | Login/senha; token pelo cabeçalho Authorization; consulta do órgão; preparação de contratações e contratos vinculados aos cadastros, PDF, revisão, envio multipart e recibo | Credenciamento da plataforma e órgão; testes institucionais de homologação. Retificações, exclusões remotas, resultados dos itens, atas, PCA e outras espécies de ato ainda não implementados |
| IBGE | Consulta real de município e distritos pela API pública, sem chave | Importação territorial ampla, indicadores populacionais e cálculo dos limites constitucionais |
| Siconfi | Extrato de entregas oficial, sincronização local, vínculo com ocorrências da agenda e notificações de mudança de status | Regras do ranking, geração/consolidação/envio de MSC, XBRL, demonstrativos fiscais e agendamento periódico da sincronização |
| eSocial | Cofre A1, procuração, alertas, importação/validação XSD S-1.3, assinatura XML, revisão de lotes, SOAP/mTLS, protocolos, recibos, erros e correções | Certificado institucional e acesso externo; geração automática integral a partir da folha, diagnósticos negociais completos, conciliação e fechamento |
| AD/LDAP | LDAPS/StartTLS, CA institucional, conta de serviço, pesquisa/bind e vínculo com usuários locais | Endereço, DNs e credenciais do diretório da prefeitura |
| Assinatura A1 | PAdES em PDFs, CMS destacado nos demais formatos, assinantes autorizados, relatórios individuais ou globais e anexos | Certificado/senha institucionais; validação da cadeia e revogação no validador institucional |
| CadÚnico/Conecta | Cofre com código de usuário/chave pública e senha/chave privada | Autorização e elegibilidade do órgão, liberação de IP, contrato técnico de autenticação e conector de consulta/importação |
| CAUC | Referência ao serviço oficial | Contrato técnico validado e conector de consulta/sincronização |
| Nove plataformas de pregão do anexo | Registro institucional e indicação da situação técnica de cada plataforma | Documentação de parceiro, credenciais, implementação e homologação de envio de processos e recebimento de propostas, lances, atas e resultados |

As nove plataformas são BLL, Portal de Compras Públicas, BNC, Compras BR, AMM Licita, Licitar Digital, LicitaNet, BBMNET e Brconectado. Os links cadastrados apontam para os fornecedores identificados. Para Brconectado, não foi cadastrado um endereço técnico sem validação. Um registro institucional **não representa um conector implementado**. Por isso, as plataformas pendentes não apresentam botão de ativação nem campos de autenticação inventados.

## PNCP: procedimento disponível

1. Na central, configure o CNPJ do órgão e o login/senha fornecidos pelo PNCP para a plataforma credenciada. Ative o ambiente apropriado e execute Consultar. A consulta autentica e verifica o órgão; ela não publica atos.
2. Cadastre processo e itens na área de Compras e contratos. Os números dos itens precisam ser inteiros positivos. Para publicar contrato, conclua sua ativação conforme o fluxo de adjudicação e homologação existente.
3. Abra Publicações PNCP → Preparar publicação. Busque o cadastro pelo número ou objeto no exercício selecionado. Também há acesso a partir do detalhe do processo/contrato.
4. Preencha os códigos oficiais aplicáveis, unidade, datas e demais campos apresentados. Consulte a tabela de domínios no link fornecido. Os dados e valores de origem são conferidos com os cadastros; divergências devem ser corrigidas na origem. Datas de propostas usam horário de Brasília.
5. Escolha explicitamente um PDF válido sem senha, com até 500 KB, seu título e código de tipo de documento. Outros anexos internos não são transmitidos por esta ação. O pacote é imutável; dados, documento, origem e configuração ficam identificados por versões e hashes.
6. Outro administrador com permissão de aprovação em Compras e contratos deve conferir os dados e baixar o PDF antes de aprovar. O criador do pacote não pode aprová-lo. Alterar a configuração, o processo, os itens ou os vínculos relevantes invalida o pacote antes do envio.
7. Envie somente após conferir o ambiente. A confirmação é `ENVIAR PARA HOMOLOGACAO` ou `PUBLICAR EM PRODUCAO`. O envio usa o protocolo multipart da especificação OpenAPI consultada, com token de autenticação e cabeçalhos de documento.
8. O estado Publicado exige resposta HTTP 201 e endereço de recibo compatível com o órgão, ambiente e tipo de ato. O retorno é preservado. Consulte o recibo a partir do detalhe do processo/contrato. O estado local não é uma certificação jurídica da publicação.

O sistema grava Enviando antes da chamada externa e libera a transação do banco durante a rede. Envios concorrentes são bloqueados. Timeout, resposta ambígua ou falha após transmissão deixam **Resultado incerto**, sem reenvio automático. Após interrupção do processo, o botão de recuperação fica disponível depois de dois minutos e também marca o resultado como incerto. A conciliação desses casos ainda deve ocorrer diretamente com o PNCP; não há rotina implementada para liberar uma nova inclusão após essa conciliação. Uma rejeição inequívoca permite nova revisão ou cancelamento do pacote. Registro com publicação preparada preserva seu histórico e não pode ser excluído como simples rascunho.

Limites atuais: um PDF por inclusão; 500 KB por PDF; requisição JSON local limitada a 1 MB, incluindo a representação base64 do arquivo; até 2.000 itens sujeitos ao limite total do pedido. Não há comparação automática com publicações originadas em outro sistema. Não há validador local completo de todas as combinações legais de códigos PNCP: o serviço oficial executa as validações finais. Nenhuma publicação real foi enviada durante esta implementação.

## Siconfi: agenda e notificações

Configure o código IBGE do ente e exercício em Produção. A API pública não exige credenciais. **Agenda e extrato → Sincronizar extrato oficial** consulta o endpoint de extrato de entregas. A sincronização é solicitada pelo usuário; não há serviço agendado de atualização em segundo plano.

O resultado preserva separadamente a instituição, tipo de declaração, período e exercício. Antes de vincular, confira a instituição indicada: Prefeitura e Câmara podem aparecer para o mesmo município. Busque uma ocorrência da mesma entidade e exercício e confirme o vínculo. Os dados externos aparecem no detalhe da ocorrência.

Em uma nova sincronização, alterações de status/data geram evento na ocorrência e notificação ao administrador que criou o vínculo. Repetir a mesma sincronização não duplica notificações. Status nulo permanece identificado como não informado. O sistema **não interpreta um status externo isolado como cumprimento legal nem encerra automaticamente a obrigação**. Extratos de município/exercício diferente ou resposta paginada/incompleta são rejeitados sem atualização parcial da agenda.

A configuração de uma entidade deve apontar para o município correto. O vínculo do relatório à ocorrência é uma decisão administrativa, com confirmação explícita da instituição. Campos populacionais eventualmente retornados pelo extrato não substituem a validação das fontes e regras constitucionais exigida por outros itens do anexo.

## Evidências e testes

A versão atual passou em 104 testes de backend e 41 verificações de navegador, incluindo a central, os novos fluxos de LDAP/assinatura/eSocial e os módulos ERP. Consulte `VALIDACAO-INTEGRACOES.md` para evidências e limites.

- `tests/test_integrations.py`: cofre, permissões, versões, certificados, preparação/revisão, PDF, bloqueios de duplicação e protocolo HTTP.
- `tests/test_integration_resilience.py`: CNPJ alfanumérico, gzip e limite de descompressão, envios concorrentes, recuperação de interrupção, recibo ambíguo e contrato a partir do fluxo de compras.
- `tests/test_siconfi_agenda.py`: importação, segregação de instituições, vínculo, mudança de status, notificação, idempotência e rejeição de extrato inconsistente.
- `tools/browser_integrations_check.py`: interface em banco temporário, com resposta externa simulada. Inclui formulário PNCP, PDF, bloqueio de autorrevisão, cofre, Siconfi e ambos os temas em 390, 768 e 1.440 px.
- `tools/check_public_integrations.py`: consultas reais somente de leitura. IBGE confirmou o município 3304524, Rio das Ostras; o Siconfi retornou 19 registros no extrato de 2026 na consulta executada. Essa quantidade é uma observação datada, não uma regra fixa.
- Resultados e imagens: `artifacts/browser-integrations-results.json`, `artifacts/public-integrations-results.json` e `artifacts/integrations-{light,dark}.png`.

Respostas controladas validam o código local; não demonstram credenciamento ou homologação externa. A assinatura de relatórios e anexos possui certificado próprio em Assinatura digital A1; a transmissão eSocial usa a configuração e o certificado de eSocial. Ambos estão implementados e separados por finalidade. Consulte o roteiro atualizado em `LDAP-ASSINATURA-ESOCIAL.md`.

## Documentação oficial consultada

- [PNCP — acesso e autenticação, manual 2.6](https://pncp.gov.br/manual/pt-br/latest/acesso_ao_pncp/index.html).
- [PNCP — inclusão de contratação](https://pncp.gov.br/manual/pt-br/latest/contratacao/inserir_contratacao.html) e [inclusão de contratos](https://pncp.gov.br/manual/pt-br/latest/contrato_empenho/inserir_contratos_ou_empenhos.html).
- [PNCP — OpenAPI de treinamento](https://treina.pncp.gov.br/api/pncp/v3/api-docs). A especificação descreve multipart também para contratos, embora o exemplo cURL do manual textual mostre JSON simples; o conector segue a especificação e o requisito de documento anexo.
- [IBGE — localidades](https://servicodados.ibge.gov.br/api/docs/localidades).
- [Tesouro Nacional — Siconfi](https://apidatalake.tesouro.gov.br/docs/siconfi/) e [especificação publicada](https://apidatalake.tesouro.gov.br/docs/siconfi.yaml).
- [eSocial — documentação técnica](https://www.gov.br/esocial/pt-br/documentacao-tecnica) e [manual do desenvolvedor 1.16](https://www.gov.br/esocial/pt-br/documentacao-tecnica/manuais/996775-manualorientacaodesenvolvedoresocialv1-16.pdf).
- [Conecta — dados familiares do Cadastro Único](https://www.gov.br/conecta/catalogo/apis/cadunico-servicos-dados-familiares) e [manual do recebedor de dados](https://gerenciador-conecta.readthedocs.io/manual_recebedor_dados.html).
- [CAUC — consulta oficial](https://www.tesourotransparente.gov.br/consultas/cauc).
- [Receita Federal — cálculo do dígito do CNPJ alfanumérico](https://www.gov.br/receitafederal/pt-br/centrais-de-conteudo/publicacoes/documentos-tecnicos/cnpj). A validação mantém suporte ao CNPJ numérico e ao CPF, aceitando o exemplo oficial `12.ABC.345/01DE-35`.

Cópias das especificações obtidas estão em `docs/integracoes/fontes/`. Datas, versões e regras externas devem ser novamente conferidas na homologação institucional.

# Diretório institucional, assinatura A1 e eSocial

Atualização: 23/09/2026. Recursos disponíveis em **Integrações externas**. O grupo Administração configura as conexões por entidade; homologação e produção são independentes. Certificados e senhas ficam cifrados no servidor e não retornam ao navegador.

## AD/LDAP

1. Selecione Produção e abra **Active Directory / LDAP → Configurar**.
2. Informe servidor, porta, `ldaps` ou `starttls`, base DN, DN e senha da conta de serviço e atributo de pesquisa (`userPrincipalName`, `sAMAccountName`, `uid` ou `mail`). Conexões sem TLS são recusadas.
3. Se a autoridade certificadora for interna, cole sua cadeia PEM. Caso contrário, são usadas as autoridades confiáveis do sistema. O certificado do servidor precisa ser válido para o endereço informado.
4. Ative e teste a conexão/pesquisa. Em **Vincular usuários**, selecione a conta local e informe sua identidade no diretório.
5. O servidor entra com o e-mail local e a senha do diretório. Grupos, permissões, horários e bloqueios continuam aplicados. A senha local não funciona como alternativa para uma conta vinculada.

O sistema preserva um administrador local ativo para recuperação. Alterar a conexão ou o vínculo encerra as sessões afetadas. Remover um vínculo invalida a senha local anterior: outro administrador deve redefini-la. O sistema não armazena a senha pessoal usada no bind LDAP. A rede do diretório não mantém o banco bloqueado durante a autenticação; antes de criar a sessão, a aplicação reconfere a conta, o vínculo e a versão da conexão.

## Assinatura digital

1. Abra **Assinatura digital A1 → Configurar**, selecione o PFX/P12 e informe a senha e a finalidade. Informe os IDs dos usuários autorizados; se a lista ficar vazia, somente administradores podem usar o certificado.
2. Ative e use **Validar certificado e testar assinatura local**. O teste efetivamente assina um PDF e verifica a integridade e a assinatura criptográfica.
3. Em **Configurações → Assinatura digital de relatórios**, escolha todos os relatórios, um módulo ou relatórios específicos. PDFs recebem PAdES; CSV, XLSX e DOCX são entregues em ZIP com original, assinatura CMS destacada `.p7s`, certificado e metadados.
4. Para documentos anexados aos cadastros ERP, abra o registro, escolha **Assinar documento** e confirme. O original permanece intacto; as versões assinadas aparecem no mesmo detalhe para download.

O artefato assinado é cifrado e imutável, com usuário, versão da configuração, hashes SHA-256, finalidade e identidade do certificado. Relatórios assinados ficam acessíveis ao emissor e à administração, observadas as permissões. Documentos sigilosos mantêm a proteção do cadastro de origem.

O perfil PDF é PAdES-B-B, sem carimbo de tempo de uma ACT. A verificação local comprova a criptografia; não atesta cadeia ICP-Brasil, revogação ou validade jurídica por si só. A checagem institucional deve usar o certificado e o validador aplicáveis. Não há suporte a token físico A3 neste conector.

## eSocial

### Configuração

Informe CNPJ do empregador, inscrição usada no eSocial (raiz ou CNPJ completo conforme natureza jurídica), CPF/CNPJ do transmissor, certificado A1 e senha. Quando houver procuração, cadastre nome do outorgado, tipo de inscrição, número, início e fim de validade. Os campos da procuração devem estar completos e o envio é bloqueado fora do período informado.

A central verifica chave privada, senha e validade do certificado. O eSocial usa RSA de pelo menos 2.048 bits. A autorização institucional, a procuração registrada e a confiança do certificado são conferidas pelo serviço destinatário; cadastrar dados locais não cria autorização na Receita Federal.

Os administradores recebem aviso interno quando o certificado estiver a 30 dias do vencimento e quando vencer. O aviso é deduplicado por certificado, ambiente e administrador. A verificação ocorre ao carregar a conta e nas consultas de notificações da interface. Não há envio de e-mail ou tarefa independente do uso da aplicação.

### Preparação e envio

1. Selecione o ambiente e abra **eSocial → Eventos e recibos → Preparar lote de eventos**.
2. Importe de 1 a 50 XMLs S-1.3 individuais, sem assinatura, do mesmo empregador, ambiente e grupo. O painel aceita até 700 KB somados, dentro do limite da requisição local. Eventos já assinados não são silenciosamente alterados.
3. O sistema valida cada arquivo contra o XSD oficial, confere a identidade do evento/empregador, o grupo e o ambiente, assina em XMLDSig RSA-SHA256 e confere a assinatura. A assinatura inclui somente o certificado final, sem expor a chave privada.
4. Outro administrador, com permissão de aprovação em Pessoal, deve revisar o lote. Alterações na configuração exigem cancelar e preparar novamente o lote antes de enviar.
5. Confirme `ENVIAR PARA HOMOLOGACAO` ou `ENVIAR PARA PRODUCAO`. O envio usa SOAP 1.1 e TLS mútuo nos endereços oficiais. Não há redirecionamentos ou retransmissão automática.
6. Após a recepção, consulte o processamento pelo protocolo. O intervalo retornado pelo serviço é respeitado, com mínimo local de 30 segundos. A tela apresenta código, estado, recibo e motivo de rejeição por evento. Cada retorno validado fica preservado separadamente para download.

### Falhas, correções e histórico

- Uma falha de conexão antes da transmissão permite nova tentativa com a aprovação existente, desde que a configuração não tenha mudado.
- Falha ou resposta ambígua depois de iniciar o envio gera **Resultado incerto**. O lote e seus IDs não podem ser duplicados ou cancelados como se nada tivesse sido enviado. Localize o protocolo no serviço e use a consulta para conciliar o lote.
- Um envio interrompido pode ser registrado após dois minutos; passa a Resultado incerto.
- Lotes inequivocamente rejeitados e eventos rejeitados sem recibo podem ser corrigidos em novo lote, com nova assinatura e revisão. O histórico anterior permanece preservado. Eventos aceitos não são liberados por essa rotina.
- O XML eSocial de exclusão é um evento oficial distinto. Cancelar um lote local antes do envio não exclui eventos já aceitos pelo governo.

### Esquemas e limites funcionais

Estão versionados em `schemas/esocial/` os esquemas S-1.3 NT06 com CNPJ alfanumérico, pacotes de comunicação 1.6 e 1.6-Alfa, WSDLs, fontes e hashes. O conector usa o pacote Alfa compatível também com CNPJ numérico. A classificação dos grupos vem do código oficial dos eventos; totalizadores de retorno não são aceitos como eventos de envio.

O conector recebe XMLs e executa assinatura, transporte e consulta. Permanecem pendentes a geração automática integral de eventos a partir dos cadastros/folha, todos os diagnósticos condicionais do MOS, conciliação de bases/tributos com totalizadores, filtros completos por trabalhador e competência, retificação por vínculo e fechamento integrado. Os XSDs e verificações locais não substituem todas as regras negociais do eSocial.

## Evidências

- `tests/test_enterprise_integrations.py`: PAdES/CMS, autorização, anexos, LDAP/TLS e recuperação.
- `tests/test_enterprise_controls.py`: assinatura por relatório, avisos, procuração, eventos não periódicos e mensagens de rejeição.
- `tests/test_esocial.py` e `tests/test_esocial_recovery.py`: XSD, assinatura preservada no SOAP, revisão, envio, consulta, recibos, duplicidade, falhas, recuperação e correções.
- `tools/browser_enterprise_check.py`: interface completa, configuração de certificado, assinatura/download, vínculo LDAP e importação eSocial, nos dois temas e em três larguras.

Os testes utilizam certificados e bases fictícias, com respostas externas controladas. Nenhum evento real foi transmitido. O inventário integral de pendências permanece em `MATRIZ-ANEXO-III.md`.

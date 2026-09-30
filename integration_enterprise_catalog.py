"""Integrações institucionais com protocolo padronizado e credenciais administráveis."""
def register(providers,field):
 providers['ldap']=dict(label='Active Directory / LDAP',area='Identidade e acesso',status='Implementado · aguarda configuração',
  description='Autenticação LDAPS ou StartTLS com validação do certificado do servidor, busca de usuário e vínculo explícito com contas locais. As permissões permanecem administradas no sistema.',
  documentation='https://ldap3.readthedocs.io/en/latest/ssltls.html',version='LDAP v3 / TLS',environments={'producao':''},activatable=True,operations={'test':'Testar conexão e pesquisa'},
  fields={'host':field('Servidor LDAP (nome DNS ou IP institucional)'), 'port':field('Porta (636 LDAPS / 389 StartTLS)'),
   'tls_mode':field('Segurança: ldaps ou starttls'),'base_dn':field('Base de pesquisa (ex.: DC=municipio,DC=gov,DC=br)'),
   'bind_dn':field('DN da conta de serviço'),'bind_password':field('Senha da conta de serviço',secret=True),
   'login_attribute':field('Atributo de login: userPrincipalName, sAMAccountName, uid ou mail'),
   'ca_pem':field('CA institucional PEM (opcional; vazio usa autoridades do sistema)',secret=True,required=False,kind='pem')} )
 providers['signature']=dict(label='Assinatura digital A1',area='Documentos e relatórios',status='Implementado · aguarda certificado',
  description='Assina PDFs em PAdES e outros relatórios com assinatura CMS destacada. O original, o hash, o certificado e a evidência de assinatura ficam preservados. O administrador autoriza os usuários assinantes.',
  documentation='https://docs.pyhanko.eu/en/latest/lib-guide/signing.html',version='PAdES / CMS SHA-256',environments={'producao':''},activatable=True,operations={'test':'Validar certificado e testar assinatura local'},
  fields={'pfx':field('Certificado A1 (.pfx ou .p12)',secret=True,kind='certificate'),'pfx_password':field('Senha do certificado',secret=True),
   'allowed_users':field('IDs dos usuários autorizados (separados por vírgula; vazio = administradores)',required=False),
   'reason':field('Finalidade da assinatura institucional'),'location':field('Local da assinatura',required=False)})

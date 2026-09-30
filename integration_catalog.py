"""Protocolos documentados. Não confundir cadastro institucional com conector ativo."""
def field(label, *, secret=False, required=True, kind='text'):
 return dict(label=label,secret=secret,required=required,type=kind)

PROVIDERS={
 'pncp':dict(label='PNCP',area='Licitações e contratos',status='Conector disponível',
  description='Autenticação oficial, consulta do órgão e publicação de contratações e contratos com documento PDF e revisão por outro administrador.',
  documentation='https://pncp.gov.br/manual/pt-br/latest/acesso_ao_pncp/index.html',
  version='Manual 2.6 / OpenAPI consultado em 23/09/2026',
  environments={'homologacao':'https://treina.pncp.gov.br/api/pncp','producao':'https://pncp.gov.br/api/pncp'},
  fields={'cnpj':field('CNPJ do órgão',kind='cnpj'),'login':field('Login da plataforma credenciada'),'senha':field('Senha do PNCP',secret=True)},
  operations={'test':'Autenticar e consultar órgão'},activatable=True),
 'ibge':dict(label='IBGE · localidades',area='Cadastros territoriais',status='Conector disponível',
  description='Consulta pública de município e distritos. Não exige chave de API.',
  documentation='https://servicodados.ibge.gov.br/api/docs/localidades',version='API de localidades v1',
  environments={'producao':'https://servicodados.ibge.gov.br/api/v1/localidades'},
  fields={'municipio':field('Código IBGE do município',kind='municipio')},
  operations={'test':'Consultar município','districts':'Consultar distritos'},activatable=True),
 'siconfi':dict(label='Siconfi · Tesouro Nacional',area='Contabilidade',status='Conector de consulta disponível',
  description='Consulta e sincronização de extratos oficiais, vínculo com a agenda e notificação de mudanças de status. Não transmite declarações nem gera a MSC. Limite oficial: uma requisição por segundo.',
  documentation='https://apidatalake.tesouro.gov.br/docs/siconfi/',version='API 1.1.0',
  environments={'producao':'https://apidatalake.tesouro.gov.br/ords/cdwhprd/siconfi/tt'},
  fields={'municipio':field('Código IBGE do ente',kind='municipio'),'exercicio':field('Exercício de referência',kind='year')},
  operations={'test':'Consultar extrato de entregas'},activatable=True),
 'esocial':dict(label='eSocial',area='Pessoal e folha',status='Cofre de certificado disponível; transmissão pendente',
  description='Certificado A1 (PFX/P12) e senha armazenados com criptografia. Validade e correspondência da chave são conferidas. Cadeia ICP-Brasil, revogação, assinatura dos eventos e transmissão SOAP ainda exigem implementação e homologação.',
  documentation='https://www.gov.br/esocial/pt-br/documentacao-tecnica',version='Manual do desenvolvedor 1.16, agosto/2026',
  environments={'homologacao':'https://webservices.producaorestrita.esocial.gov.br','producao':'https://webservices.envio.esocial.gov.br'},
  fields={'cnpj':field('CNPJ do empregador',kind='cnpj'),'pfx':field('Certificado A1 (.pfx ou .p12)',secret=True,kind='certificate'),'pfx_password':field('Senha do certificado A1',secret=True)},
  operations={},activatable=False),
 'cadunico':dict(label='Cadastro Único · Conecta GOV.BR',area='Assistência social',status='Credenciamento e conector pendentes',
  description='Acesso depende de autorização do gestor da API e liberação de IP. A elegibilidade municipal deve ser confirmada. O cofre recebe o par de chaves oficial; consulta a dados pessoais ainda não está habilitada.',
  documentation='https://www.gov.br/conecta/catalogo/apis/cadunico-servicos-dados-familiares',version='Catálogo de serviços de dados familiares v1',
  environments={'homologacao':'https://h-apigateway.conectagov.np.estaleiro.serpro.gov.br','producao':'https://apigateway.conectagov.estaleiro.serpro.gov.br'},
  fields={'consumer_key':field('Código de usuário / chave pública'),'consumer_secret':field('Senha / chave privada',secret=True)},operations={},activatable=False),
 'cauc':dict(label='CAUC',area='Controle interno',status='Protocolo de integração pendente',
  description='Consulta institucional no serviço oficial. Não foi confirmado contrato público de API para implementar transmissão ou leitura automática.',
  documentation='https://www.tesourotransparente.gov.br/consultas/cauc',version='Consulta oficial',environments={'producao':''},fields={},operations={},activatable=False),
}
for code,label,url in [
 ('bll','BLL','https://bll.org.br/'),('pcp','Portal de Compras Públicas','https://ajuda.portaldecompraspublicas.com.br/hc/pt-br'),
 ('bnc','BNC','https://bnc.org.br/'),('comprasbr','Compras BR','https://comprasbr.com.br/'),
 ('ammlicita','AMM Licita','https://ammlicita.org.br/'),('licitardigital','Licitar Digital','https://licitar.digital/'),
 ('licitanet','LicitaNet','https://licitanet.com.br/'),('bbmnet','BBMNET','https://bbmnet.com.br/como-operar/'),
 ('brconectado','Brconectado','')]:
 PROVIDERS[code]=dict(label=label,area='Plataformas de pregão',status='Contrato técnico de integração pendente',
  description='Plataforma prevista no Anexo III. Envio de processos e retorno de propostas, lances e atas dependem da documentação de parceiro e da homologação do fornecedor. Não há transmissão implementada.',
  documentation=url,version='Documentação técnica de parceiro ainda não validada',environments={'homologacao':'','producao':''},
  fields={'registration':field('Número do credenciamento / contrato',required=False),'technical_contact':field('Contato técnico institucional',required=False)},operations={},activatable=False)

# Transmissão de XMLs oficiais; geração automática de todos os eventos da folha é requisito distinto.
PROVIDERS['esocial'].update(status='Conector SOAP disponível',activatable=True,
 description='Importação de eventos S-1.3 sem assinatura, validação XSD, assinatura XML A1, lotes por grupo, revisão, envio SOAP com TLS mútuo e consulta de recibos por evento. A geração automática de todos os eventos a partir da folha ainda exige ampliação.',
 fields={**PROVIDERS['esocial']['fields'],'employer_registration':field('Inscrição eSocial do empregador (CNPJ completo ou raiz, conforme natureza jurídica)'),'transmitter':field('CPF ou CNPJ do transmissor do certificado')})

PROVIDERS['esocial']['fields'].update({
 'attorney_name':field('Nome do outorgado (se houver procuração)',required=False),
 'attorney_type':field('Tipo de inscrição do outorgado: 1 = CNPJ; 2 = CPF',required=False),
 'attorney_registration':field('Inscrição do outorgado',required=False),
 'attorney_valid_from':field('Início da procuração (AAAA-MM-DD)',required=False),
 'attorney_valid_until':field('Fim da procuração (AAAA-MM-DD)',required=False)})

from integration_enterprise_catalog import register
register(PROVIDERS,field)

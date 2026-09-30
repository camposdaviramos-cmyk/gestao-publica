"""XML eSocial S-1.3: esquemas oficiais locais, assinatura e envelopes SOAP 1.1."""
import copy,re
from functools import lru_cache
from pathlib import Path
from datetime import datetime
from lxml import etree as ET
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding
from signxml import XMLSigner,XMLVerifier,methods,SignatureConfiguration
from auth import ApiError
from integration_signatures import load_material

ROOT=Path(__file__).parent/'schemas/esocial'
EVENTS=ROOT/'eventos-s1.3-nt06-alfa'
COMM=next((ROOT/'comunicacao-1.6-alfa').iterdir())/'XSD/LoteEventos'
DS='http://www.w3.org/2000/09/xmldsig#'
C14N='http://www.w3.org/TR/2001/REC-xml-c14n-20010315'
SOAP='http://schemas.xmlsoap.org/soap/envelope/'
ENVIO='http://www.esocial.gov.br/schema/lote/eventos/envio/v1_1_1'
CONSULTA='http://www.esocial.gov.br/schema/lote/eventos/envio/consulta/retornoProcessamento/v1_0_0'
SERVICES={
 'send':('http://www.esocial.gov.br/servicos/empregador/lote/eventos/envio/v1_1_0','EnviarLoteEventos','loteEventos','ServicoEnviarLoteEventos'),
 'query':('http://www.esocial.gov.br/servicos/empregador/lote/eventos/envio/consulta/retornoProcessamento/v1_1_0','ConsultarLoteEventos','consulta','ServicoConsultarLoteEventos')}

def parse(raw):
 if isinstance(raw,str):raw=raw.encode('utf-8')
 if not isinstance(raw,bytes) or not 1<=len(raw)<=5000000:raise ApiError('XML vazio ou acima do limite de 5 MB.')
 try:
  node=ET.fromstring(raw,ET.XMLParser(resolve_entities=False,no_network=True,load_dtd=False,huge_tree=False,remove_comments=True))
  if node.getroottree().docinfo.doctype or any(isinstance(n,ET._Entity) for n in node.iter()):raise ValueError()
  return node
 except (ET.XMLSyntaxError,ValueError):raise ApiError('XML inválido. DTD e entidades externas não são permitidos.') from None

@lru_cache(maxsize=60)
def schema(path):return ET.XMLSchema(ET.parse(str(path),ET.XMLParser(resolve_entities=False,no_network=True)))

def validate(node,path):
 try:schema(path).assertValid(node)
 except ET.DocumentInvalid as error:
  # Nomes dos campos bastam para localizar o erro; valores pessoais não vão ao log.
  last=error.error_log.last_error
  raise ApiError('XML não atende ao XSD oficial: '+(last.path if last and last.path else 'estrutura do documento')+'. Confira campos, tipos e ordem dos elementos.') from None

def sub(parent,name,text=None):
 node=ET.SubElement(parent,'{'+ET.QName(parent).namespace+'}'+name)
 if text is not None:node.text=str(text)
 return node

def text(node,path):return node.findtext(path,namespaces={'e':ET.QName(node).namespace})

@lru_cache(maxsize=52)
def event_code(name):
 document=ET.parse(str(EVENTS/(name+'.xsd')))
 docs=document.xpath('//*[local-name()="element"]/*[local-name()="annotation"]/*[local-name()="documentation"]/text()')
 code=next((re.search(r'S-(\d{4})',s) for s in docs if re.search(r'S-(\d{4})',s)),None)
 if not code:raise ApiError('Código de evento não identificado no esquema oficial.')
 return int(code.group(1))

def event_group(name):
 code=event_code(name)
 if 1000<=code<1200:return 1
 if 1200<=code<1300:return 3
 return 2

def prepare_event(raw,parameters,secrets,environment):
 node=parse(raw);ns=ET.QName(node).namespace
 if ET.QName(node).localname!='eSocial' or not ns or not ns.startswith('http://www.esocial.gov.br/schema/evt/'):raise ApiError('Envie um evento individual com raiz eSocial.')
 children=[n for n in node if isinstance(n.tag,str) and ET.QName(n).namespace!=DS]
 if len(children)!=1:raise ApiError('Cada arquivo deve conter exatamente um evento.')
 evt=children[0];name=ET.QName(evt).localname
 if not re.fullmatch(r'evt[A-Za-z]+',name) or not (EVENTS/(name+'.xsd')).is_file() or ns!='http://www.esocial.gov.br/schema/evt/'+name+'/v_S_01_03_00':raise ApiError('Evento ou versão não disponível nos esquemas S-1.3 instalados.')
 if event_code(name)>=5000:raise ApiError('Totalizadores são retornos do eSocial e não eventos de envio.')
 expected=parameters['employer_registration'];event_id=evt.get('Id','')
 if not re.fullmatch(r'ID1[A-Z0-9]{12}[0-9]{21}',event_id) or event_id[3:17]!=expected.ljust(14,'0'):raise ApiError('ID deve identificar o empregador e seguir as 36 posições oficiais.')
 try:datetime.strptime(event_id[17:31],'%Y%m%d%H%M%S')
 except ValueError:raise ApiError('Data/hora do ID de evento inválida.') from None
 if text(evt,'e:ideEmpregador/e:tpInsc')!='1' or text(evt,'e:ideEmpregador/e:nrInsc')!=expected:raise ApiError('Empregador do XML diverge da configuração desta entidade.')
 if text(evt,'e:ideEvento/e:tpAmb')!=('1' if environment=='producao' else '2'):raise ApiError('Ambiente do XML diverge do ambiente selecionado.')
 _,private,cert,_=load_material(secrets)
 if not isinstance(private,rsa.RSAPrivateKey) or private.key_size<2048:raise ApiError('eSocial exige certificado RSA com chave de pelo menos 2048 bits.')
 existing=node.find('{'+DS+'}Signature')
 if existing is not None:
  # Nunca remove silenciosamente uma assinatura recebida.
  raise ApiError('Importe o XML sem assinatura. A central assina com o certificado configurado e preserva essa evidência.')
 signer=XMLSigner(method=methods.enveloped,signature_algorithm='rsa-sha256',digest_algorithm='sha256',c14n_algorithm=C14N)
 signed=signer.sign(node,key=private,cert=cert.public_bytes(Encoding.PEM),reference_uri='#'+event_id,always_add_key_value=False)
 validate(signed,EVENTS/(name+'.xsd'));verify_signature(signed,cert.public_bytes(Encoding.PEM))
 return signed,{'event_id':event_id,'event_type':name,'group':event_group(name)}

def verify_signature(node,cert):
 try:XMLVerifier().verify(node,x509_cert=cert,expect_config=SignatureConfiguration(location='./',expect_references=1))
 except Exception:raise ApiError('Falha na verificação da assinatura XML.',409) from None

def batch(events,parameters,group):
 root=ET.Element('{'+ENVIO+'}eSocial',nsmap={None:ENVIO});lote=sub(root,'envioLoteEventos');lote.set('grupo',str(group))
 emp=sub(lote,'ideEmpregador');sub(emp,'tpInsc',1);sub(emp,'nrInsc',parameters['employer_registration'])
 transmitter=parameters['transmitter'];trans=sub(lote,'ideTransmissor');sub(trans,'tpInsc',2 if len(transmitter)==11 else 1);sub(trans,'nrInsc',transmitter)
 listing=sub(lote,'eventos')
 for node,meta in events:
  item=sub(listing,'evento');item.set('Id',meta['event_id']);item.append(copy.deepcopy(node))
 validate(root,COMM/'Envio/EnvioLoteEventos-v1_1_1.xsd');return root

def query(protocol):
 if not re.fullmatch(r'[12]\.[1-9]\.[0-9]{1,19}',protocol):raise ApiError('Protocolo eSocial inválido.')
 root=ET.Element('{'+CONSULTA+'}eSocial',nsmap={None:CONSULTA});sub(sub(root,'consultaLoteEventos'),'protocoloEnvio',protocol)
 validate(root,COMM/'Consulta/ConsultaLoteEventos-v1_0_0.xsd');return root

def envelope(operation,payload):
 ns,method,arg,service=SERVICES[operation]
 root=ET.Element('{'+SOAP+'}Envelope',nsmap={None:SOAP});body=sub(root,'Body')
 call=ET.SubElement(body,'{'+ns+'}'+method,nsmap={None:ns});sub(call,arg).append(copy.deepcopy(payload))
 return ET.tostring(root,encoding='utf-8',xml_declaration=True),ns+'/'+service+'/'+method

def parse_response(raw,operation):
 root=parse(raw);ns,method,_,_=SERVICES[operation]
 if root.tag!='{'+SOAP+'}Envelope' or root.find('.//{'+SOAP+'}Fault') is not None:raise ApiError('Resposta SOAP inválida ou falha do serviço eSocial.',502)
 wrapper=root.find('{'+SOAP+'}Body/{'+ns+'}'+method+'Response/{'+ns+'}'+method+'Result')
 if wrapper is None or len(wrapper)!=1:raise ApiError('Resposta eSocial sem resultado de processamento.',502)
 result=wrapper[0];path=COMM/('RetornoEnvio/RetornoEnvioLoteEventos-v1_1_0.xsd' if operation=='send' else 'RetornoProcessamento/RetornoProcessamentoLote-v1_3_0.xsd')
 validate(result,path);data=result[0];status=text(data,'e:status/e:cdResposta');description=text(data,'e:status/e:descResposta')
 items=[]
 if operation=='query':
  for item in data.findall('e:retornoEventos/e:evento',namespaces={'e':ET.QName(data).namespace}):
   # Retorno individual possui seu próprio namespace e assinatura.
   returned=item.find('e:retornoEvento',namespaces={'e':ET.QName(data).namespace})
   if returned is None or len(returned)!=1:raise ApiError('Retorno individual ausente.',502)
   validate(copy.deepcopy(returned[0]),COMM.parent/'Eventos/RetornoEvento/RetornoEvento-v1_3_0.xsd')
   inner=returned[0][0]
   if inner.get('Id')!=item.get('Id'):raise ApiError('ID do retorno individual diverge do lote.',502)
   if text(inner,'e:ideEmpregador/e:nrInsc')!=text(data,'e:ideEmpregador/e:nrInsc'):raise ApiError('Empregador do retorno individual diverge do lote.',502)
   code=returned.xpath('string(.//*[local-name()="processamento"]/*[local-name()="cdResposta"])')
   receipt=returned.xpath('string(.//*[local-name()="recibo"]/*[local-name()="nrRecibo"])')
   desc=returned.xpath('string(.//*[local-name()="processamento"]/*[local-name()="descResposta"])')
   reasons=returned.xpath('.//*[local-name()="ocorrencias"]/*[local-name()="ocorrencia"]')
   details=[' · '.join(o.xpath('./*[local-name()="codigo" or local-name()="descricao" or local-name()="localizacao"]/text()')) for o in reasons]
   desc='; '.join([desc]+details)
   items.append({'event_id':item.get('Id'),'code':code,'receipt':receipt,'description':desc[:1000]})
 return {'code':int(status),'description':description,'protocol':text(data,'e:dadosRecepcaoLote/e:protocoloEnvio'),
  'employer':text(data,'e:ideEmpregador/e:nrInsc'),'transmitter':text(data,'e:ideTransmissor/e:nrInsc'),
  'wait_seconds':max(30,min(86400,int(text(data,'e:status/e:tempoEstimadoConclusao') or 30))),'events':items}

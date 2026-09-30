"""SOAP eSocial em TLS mútuo, sem redirecionamentos nem repetição automática."""
import http.client,ssl,tempfile,secrets
from pathlib import Path
from cryptography.hazmat.primitives.serialization import Encoding,PrivateFormat,BestAvailableEncryption
from integration_signatures import load_material
from integration_transport import RemoteError
from integration_esocial_xml import envelope,parse_response
from auth import ApiError

ENDPOINTS={
 ('homologacao','send'):('webservices.producaorestrita.esocial.gov.br','/servicos/empregador/enviarloteeventos/WsEnviarLoteEventos.svc'),
 ('producao','send'):('webservices.envio.esocial.gov.br','/servicos/empregador/enviarloteeventos/WsEnviarLoteEventos.svc'),
 ('homologacao','query'):('webservices.producaorestrita.esocial.gov.br','/servicos/empregador/consultarloteeventos/WsConsultarLoteEventos.svc'),
 ('producao','query'):('webservices.consulta.esocial.gov.br','/servicos/empregador/consultarloteeventos/WsConsultarLoteEventos.svc')}

def tls_context(credentials):
 _,private,cert,chain=load_material(credentials);context=ssl.create_default_context();context.minimum_version=ssl.TLSVersion.TLSv1_2
 # A chave só vai ao arquivo temporário cifrada, com senha aleatória mantida em memória.
 password=secrets.token_bytes(32)
 with tempfile.TemporaryDirectory(prefix='rio-esocial-tls-') as temp:
  certpath=Path(temp)/'chain.pem';keypath=Path(temp)/'key.pem'
  certpath.write_bytes(cert.public_bytes(Encoding.PEM)+b''.join(c.public_bytes(Encoding.PEM) for c in chain))
  keypath.write_bytes(private.private_bytes(Encoding.PEM,PrivateFormat.PKCS8,BestAvailableEncryption(password)))
  context.load_cert_chain(str(certpath),str(keypath),password=password)
 return context

def exchange(environment,operation,payload,credentials):
 if (environment,operation) not in ENDPOINTS:raise RemoteError('Ambiente ou operação eSocial inválidos.')
 host,path=ENDPOINTS[environment,operation];body,action=envelope(operation,payload)
 if len(body)>5000000:raise RemoteError('Lote SOAP excede 5 MB.')
 context=tls_context(credentials);connection=http.client.HTTPSConnection(host,443,timeout=30,context=context);sent=False
 try:
  connection.connect() # Falha no TLS ocorre antes de qualquer transmissão de evento.
  sent=True
  connection.request('POST',path,body=body,headers={'Content-Type':'text/xml; charset=utf-8','SOAPAction':'"'+action+'"','Accept':'text/xml','User-Agent':'RioGestao-eSocial/1.0'})
  response=connection.getresponse();raw=response.read(5000001)
  if response.status!=200 or len(raw)>5000000:raise RemoteError('Serviço eSocial retornou resposta HTTP inesperada; consulte o histórico antes de tentar novamente.',uncertain=operation=='send')
  try:result=parse_response(raw,operation)
  except ApiError:raise RemoteError('Retorno SOAP fora do padrão oficial; resultado não confirmado.',uncertain=operation=='send') from None
  return result,raw
 except RemoteError:raise
 except (OSError,ValueError,http.client.HTTPException):raise RemoteError('Conexão eSocial não concluída. Verifique certificado, autorização e conectividade.',uncertain=sent and operation=='send') from None
 finally:connection.close()

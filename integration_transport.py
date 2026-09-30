"""HTTP com destinos oficiais fixos, TLS validado e sem redirecionar credenciais."""
import json, ssl, time, threading, re, gzip
from io import BytesIO
from urllib.request import Request, build_opener, HTTPSHandler, HTTPRedirectHandler, ProxyHandler
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit

class RemoteError(Exception):
 def __init__(self,message,status=None,uncertain=False):
  super().__init__(message);self.status=status;self.uncertain=uncertain

class NoRedirect(HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):return None

HOSTS={'pncp.gov.br','treina.pncp.gov.br','servicodados.ibge.gov.br','apidatalake.tesouro.gov.br'}
_rate_lock=threading.Lock();_last_siconfi=0

def request_official(url,method='GET',headers=None,body=None):
 global _last_siconfi
 parts=urlsplit(url)
 if parts.scheme!='https' or parts.hostname not in HOSTS or parts.port not in (None,443) or parts.username or parts.password or parts.fragment:
  raise RemoteError('Destino não autorizado.')
 if parts.hostname=='apidatalake.tesouro.gov.br':
  with _rate_lock:
   if time.monotonic()-_last_siconfi<1:raise RemoteError('Aguarde um segundo entre consultas ao Siconfi.',429)
   _last_siconfi=time.monotonic()
 opener=build_opener(ProxyHandler({}),HTTPSHandler(context=ssl.create_default_context()),NoRedirect())
 request=Request(url,data=body,headers={'Accept':'application/json','User-Agent':'RioGestao/1.0',**(headers or {})},method=method)
 try:
  with opener.open(request,timeout=20) as response:
   content=response.read(5*1024*1024+1)
   if len(content)>5*1024*1024:raise RemoteError('Resposta excede o limite de 5 MB.',uncertain=method!='GET')
   encoding=response.headers.get('Content-Encoding','').lower()
   if encoding=='gzip':
    try:
     with gzip.GzipFile(fileobj=BytesIO(content)) as compressed:content=compressed.read(5*1024*1024+1)
    except (OSError,EOFError):raise RemoteError('Resposta comprimida inválida.',uncertain=method!='GET') from None
    if len(content)>5*1024*1024:raise RemoteError('Resposta descomprimida excede 5 MB.',uncertain=method!='GET')
   elif encoding not in ('','identity'):raise RemoteError('Codificação de resposta não suportada.',uncertain=method!='GET')
   return response.status,dict(response.headers),content
 except HTTPError as error:
  code=error.code;error.close()
  messages={401:'Credenciais recusadas pelo serviço.',403:'Órgão ou plataforma sem autorização no serviço.',404:'Recurso não encontrado no serviço.',429:'Limite de consultas do serviço atingido.'}
  raise RemoteError(messages.get(code,f'Serviço retornou HTTP {code}. Confira os parâmetros na documentação oficial.'),code,method!='GET' and code>=500) from None
 except (URLError,TimeoutError,OSError):
  raise RemoteError('Não foi possível confirmar a resposta do serviço. Verifique disponibilidade e conectividade.',uncertain=method!='GET') from None

def decode_json(content):
 try:return json.loads(content)
 except (ValueError,UnicodeDecodeError):raise RemoteError('O serviço não retornou JSON válido.') from None

def pncp_login(base,parameters,secrets):
 _,headers,_=request_official(base+'/v1/usuarios/login','POST',{'Content-Type':'application/json'},json.dumps({'login':parameters['login'],'senha':secrets['senha']}).encode())
 token=next((v for k,v in headers.items() if k.lower()=='authorization'),'')
 if not token.startswith('Bearer ') or '\r' in token or '\n' in token:raise RemoteError('O PNCP não retornou o token no cabeçalho Authorization.')
 return token

def consult(provider,base,parameters,secrets,operation):
 headers={}
 if provider=='pncp':
  headers['Authorization']=pncp_login(base,parameters,secrets)
  url=base+'/v1/orgaos/'+parameters['cnpj']
 elif provider=='ibge':url=base+'/municipios/'+parameters['municipio']+('/distritos' if operation=='districts' else '')
 elif provider=='siconfi':url=base+'/extrato_entregas?id_ente='+parameters['municipio']+'&an_referencia='+str(parameters['exercicio'])
 else:raise RemoteError('Conector de consulta indisponível.')
 _,_,body=request_official(url,headers=headers)
 return decode_json(body)

def publish_pncp(base,parameters,secrets,job,pdf):
 import secrets as random
 # Autenticação falhada não é publicação incerta: nenhum documento foi enviado.
 try:token=pncp_login(base,parameters,secrets)
 except RemoteError as error:error.uncertain=False;raise
 boundary='RioBoundary'+random.token_hex(24)
 name='compra' if job['operation']=='compras' else 'contrato'
 data=(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; filename="{name}.json"\r\nContent-Type: application/json\r\n\r\n'.encode()+job['payload'].encode()+
  f'\r\n--{boundary}\r\nContent-Disposition: form-data; name="documento"; filename="documento.pdf"\r\nContent-Type: application/pdf\r\n\r\n'.encode()+pdf+f'\r\n--{boundary}--\r\n'.encode())
 status,headers,body=request_official(base+'/v1/orgaos/'+parameters['cnpj']+'/'+job['operation'],'POST',
  {'Authorization':token,'Content-Type':'multipart/form-data; boundary='+boundary,'Titulo-Documento':job['document_title'],'Tipo-Documento-Id':str(job['document_type'])},data)
 location=next((v for k,v in headers.items() if k.lower()=='location'),'')
 # A resposta original é preservada no recibo; nunca inclui headers de autorização.
 try:result=decode_json(body) if body else {}
 except RemoteError:raise RemoteError('Envio aceito por HTTP, mas recibo não interpretado. Consulte o PNCP antes de reenviar.',uncertain=True) from None
 receipt_url=location or (result.get('compraUri' if job['operation']=='compras' else 'contratoUri','') if isinstance(result,dict) else '')
 expected=base+'/v1/orgaos/'+parameters['cnpj']+'/'+job['operation']+'/'
 if status!=201 or not isinstance(receipt_url,str) or not receipt_url.startswith(expected) or not re.fullmatch(r'[0-9]{4}/[0-9]+',receipt_url[len(expected):]):raise RemoteError('Resposta recebida sem confirmação inequívoca da inclusão. Consulte o PNCP antes de reenviar.',uncertain=True)
 return {'http_status':status,'location':receipt_url,'response':result}

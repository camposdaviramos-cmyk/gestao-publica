import copy,io,json
import pytest
from lxml import etree as ET
from cryptography.hazmat.primitives.serialization import Encoding
from test_system import app,admin,login,user
from test_erp import ERP,erp,reviewer
from test_integrations import configure,certificate,CNPJ
from integration_signatures import load_material
from integration_esocial_xml import prepare_event,batch,envelope,parse,parse_response,verify_signature,SERVICES,SOAP,DS
from integration_transport import RemoteError
from db import get_db

PROTOCOL='1.2.0000000000000000001'
def xml(sequence=1,cnpj=CNPJ,environment='2'):
 return f'''<eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtInfoEmpregador/v_S_01_03_00"><evtInfoEmpregador Id="ID1{cnpj}20260923090000{sequence:05d}"><ideEvento><tpAmb>{environment}</tpAmb><procEmi>1</procEmi><verProc>RioGestao1</verProc></ideEvento><ideEmpregador><tpInsc>1</tpInsc><nrInsc>{cnpj}</nrInsc></ideEmpregador><infoEmpregador><inclusao><idePeriodo><iniValid>2026-09</iniValid></idePeriodo><infoCadastro><classTrib>85</classTrib><indCoop>0</indCoop><indConstr>0</indConstr><indDesFolha>0</indDesFolha><indOptRegEletron>0</indOptRegEletron><cnpjEFR>{cnpj}</cnpjEFR></infoCadastro></inclusao></infoEmpregador></evtInfoEmpregador></eSocial>'''

def configuration(session,**extra):
 return configure(session,provider='esocial',parameters={'cnpj':CNPJ,'employer_registration':CNPJ,'transmitter':CNPJ},secrets={'pfx':certificate(),'pfx_password':'senha-certificado'},**extra)

def prepare(e):
 assert configuration((e.client,e.headers)).status_code==200
 r=e.client.post('/api/esocial/batches',json={'entity':1,'environment':'homologacao','events':[xml()]},headers=e.headers);assert r.status_code==201,r.json
 return r.json['id']

def action(e,id,op,**extra):
 version=e.client.get('/api/esocial/batches/'+str(id)).json['item']['version']
 return e.client.post('/api/esocial/batches/'+str(id)+'/'+op,json={'version':version,**extra},headers=e.headers)

def reception(operation='send',code=201,ids=None):
 ns,method,_,_=SERVICES[operation]
 root=ET.Element('{'+SOAP+'}Envelope',nsmap={None:SOAP});body=ET.SubElement(root,'{'+SOAP+'}Body')
 response=ET.SubElement(body,'{'+ns+'}'+method+'Response',nsmap={None:ns});result=ET.SubElement(response,'{'+ns+'}'+method+'Result')
 schema_ns='http://www.esocial.gov.br/schema/lote/eventos/'+('envio/retornoEnvio/v1_1_0' if operation=='send' else 'envio/retornoProcessamento/v1_3_0')
 tag='retornoEnvioLoteEventos' if operation=='send' else 'retornoProcessamentoLoteEventos'
 events=''
 if ids:
  events='<retornoEventos>'+''.join(f'<evento Id="{i}"><retornoEvento><eSocial xmlns="http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0"><retornoEvento Id="{i}"><ideEmpregador><tpInsc>1</tpInsc><nrInsc>{CNPJ}</nrInsc></ideEmpregador><recepcao><tpAmb>2</tpAmb><dhRecepcao>2026-09-23T09:01:00</dhRecepcao><versaoAppRecepcao>1</versaoAppRecepcao><protocoloEnvioLote>{PROTOCOL}</protocoloEnvioLote></recepcao><processamento><cdResposta>201</cdResposta><descResposta>Sucesso</descResposta><versaoAppProcessamento>1</versaoAppProcessamento><dhProcessamento>2026-09-23T09:02:00</dhProcessamento></processamento><recibo><nrRecibo>1.1.0000001</nrRecibo><hash>teste</hash></recibo></retornoEvento></eSocial></retornoEvento></evento>' for i in ids)+'</retornoEventos>'
 data=f'<eSocial xmlns="{schema_ns}"><{tag}><ideEmpregador><tpInsc>1</tpInsc><nrInsc>{CNPJ}</nrInsc></ideEmpregador><ideTransmissor><tpInsc>1</tpInsc><nrInsc>{CNPJ}</nrInsc></ideTransmissor><status><cdResposta>{code}</cdResposta><descResposta>Retorno fictício de teste</descResposta></status><dadosRecepcaoLote><dhRecepcao>2026-09-23T09:01:00</dhRecepcao><versaoAplicativoRecepcao>1</versaoAplicativoRecepcao><protocoloEnvio>{PROTOCOL}</protocoloEnvio></dadosRecepcaoLote>{events}</{tag}></eSocial>'
 result.append(parse(data));return ET.tostring(root)

def test_xsd_signature_and_soap_namespace_integrity():
 params={'employer_registration':CNPJ,'transmitter':CNPJ};secrets={'pfx':certificate(),'pfx_password':'senha-certificado'}
 event,meta=prepare_event(xml(),params,secrets,'homologacao');assert meta['group']==1
 root=batch([(event,meta)],params,1);raw,soap_action=envelope('send',root);payload=parse(raw)
 embedded=payload.find('.//{http://www.esocial.gov.br/schema/evt/evtInfoEmpregador/v_S_01_03_00}eSocial')
 cert=load_material(secrets)[2];verify_signature(embedded,cert.public_bytes(Encoding.PEM))
 assert soap_action==SERVICES['send'][0]+'/ServicoEnviarLoteEventos/EnviarLoteEventos'
 assert len(embedded.findall('.//{'+DS+'}X509Certificate'))==1 and not embedded.findall('.//{'+DS+'}KeyValue')

def test_xsd_rejects_wrong_context_structure_and_entities():
 params={'employer_registration':CNPJ,'transmitter':CNPJ};secrets={'pfx':certificate(),'pfx_password':'senha-certificado'}
 from auth import ApiError
 for source in [xml().replace('<tpAmb>2</tpAmb>','<tpAmb>1</tpAmb>'),xml().replace('<classTrib>85</classTrib>','<classTrib>inválido</classTrib>'),xml().replace(CNPJ,'00000000000000'), '<!DOCTYPE x [<!ENTITY test SYSTEM "file:///C:/Windows/win.ini">]><x>&test;</x>']:
  with pytest.raises(ApiError):prepare_event(source,params,secrets,'homologacao')

def test_soap_responses_follow_official_xsd():
 sent=parse_response(reception(),'send');assert sent['protocol']==PROTOCOL and sent['code']==201
 eid=parse(xml())[0].get('Id');received=parse_response(reception('query',ids=[eid]),'query');assert received['events'][0]['receipt']=='1.1.0000001'

def test_queue_review_send_poll_and_per_event_receipts(erp,reviewer,app,monkeypatch):
 id=prepare(erp);assert action(erp,id,'approve').status_code==403;assert action(reviewer,id,'approve').status_code==200
 import integration_esocial
 calls=[]
 def exchange(env,operation,payload,secrets):
  calls.append(operation);raw=reception(operation,ids=[parse(xml())[0].get('Id')] if operation=='query' else None);return parse_response(raw,operation),raw
 monkeypatch.setattr(integration_esocial,'exchange',exchange)
 assert action(erp,id,'send',confirmation='PRODUCAO').status_code==400
 r=action(erp,id,'send',confirmation='ENVIAR PARA HOMOLOGACAO');assert r.json['state']=='Recebido',r.json
 assert action(erp,id,'send',confirmation='ENVIAR PARA HOMOLOGACAO').status_code==409
 assert action(erp,id,'query').status_code==429
 with app.app_context():get_db().execute('UPDATE esocial_batches SET next_query_at=NULL WHERE id=?',(id,));get_db().commit()
 r=action(erp,id,'query');assert r.json['state']=='Processado',r.json
 detail=erp.client.get('/api/esocial/batches/'+str(id)).json;assert detail['events'][0]['receipt']=='1.1.0000001'
 assert calls==['send','query'];assert 'encrypted_xml' not in detail['item']
 assert erp.client.get(f'/api/esocial/batches/{id}/download/xml').data.startswith(b'<?xml')
 assert erp.client.post('/api/esocial/batches',json={'entity':1,'environment':'homologacao','events':[xml()]},headers=erp.headers).status_code==409
 with app.app_context():assert b'eSocial' not in get_db().execute('SELECT encrypted_xml FROM esocial_batches').fetchone()[0]

def test_uncertain_submission_cannot_cancel_or_resend(erp,reviewer,monkeypatch):
 id=prepare(erp);action(reviewer,id,'approve');import integration_esocial
 def exchange(*a):raise RemoteError('Resposta não confirmada',uncertain=True)
 monkeypatch.setattr(integration_esocial,'exchange',exchange)
 assert action(erp,id,'send',confirmation='ENVIAR PARA HOMOLOGACAO').json['state']=='Resultado incerto'
 assert action(erp,id,'cancel',reason='Repetir lote indevidamente').status_code==409
 assert action(erp,id,'send',confirmation='ENVIAR PARA HOMOLOGACAO').status_code==409

def test_config_rotation_invalidates_prepared_signature_and_cancel_releases_ids(erp,reviewer):
 id=prepare(erp);assert configuration((erp.client,erp.headers),version=1).status_code==200
 assert action(reviewer,id,'approve').status_code==409
 assert action(erp,id,'cancel',reason='Certificado institucional alterado').status_code==200
 assert erp.client.post('/api/esocial/batches',json={'entity':1,'environment':'homologacao','events':[xml()]},headers=erp.headers).status_code==201

def test_mutual_tls_uses_verified_official_host_no_retry(monkeypatch):
 import integration_esocial_transport as t,ssl
 captures=[];secrets={'pfx':certificate(),'pfx_password':'senha-certificado'}
 class HTTPS:
  def __init__(self,host,port,timeout,context):assert context.verify_mode==ssl.CERT_REQUIRED and context.check_hostname;captures.append(host)
  def connect(self):pass
  def request(self,method,path,body,headers):assert method=='POST';captures.append(headers['SOAPAction'])
  def getresponse(self):raise TimeoutError()
  def close(self):pass
 monkeypatch.setattr(t.http.client,'HTTPSConnection',HTTPS)
 from integration_esocial_xml import query
 with pytest.raises(RemoteError) as exc:t.exchange('producao','send',query(PROTOCOL),secrets)
 assert exc.value.uncertain and captures[0]=='webservices.envio.esocial.gov.br' and len(captures)==2

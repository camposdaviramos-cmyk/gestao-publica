from test_system import app,admin
from test_erp import erp,reviewer
from test_esocial import prepare,action,xml,reception
from integration_esocial_xml import parse,parse_response
from integration_transport import RemoteError
from db import get_db

def test_rejected_event_can_be_corrected_but_original_history_stays(erp,reviewer,app,monkeypatch):
 id=prepare(erp);action(reviewer,id,'approve');import integration_esocial
 def exchange(env,operation,payload,secrets):
  raw=reception(operation,ids=[parse(xml())[0].get('Id')] if operation=='query' else None)
  if operation=='query':raw=raw.replace(b'<cdResposta>201</cdResposta><descResposta>Sucesso',b'<cdResposta>401</cdResposta><descResposta>Rubrica rejeitada').replace(b'<recibo><nrRecibo>1.1.0000001</nrRecibo><hash>teste</hash></recibo>',b'')
  return parse_response(raw,operation),raw
 monkeypatch.setattr(integration_esocial,'exchange',exchange)
 action(erp,id,'send',confirmation='ENVIAR PARA HOMOLOGACAO')
 with app.app_context():get_db().execute('UPDATE esocial_batches SET next_query_at=NULL WHERE id=?',(id,));get_db().commit()
 r=action(erp,id,'query');assert r.json['state']=='Processado com ocorrências',r.json
 detail=erp.client.get('/api/esocial/batches/'+str(id)).json;assert len(detail['responses'])==2 and detail['events'][0]['description']=='Rubrica rejeitada'
 for response in detail['responses']:assert erp.client.get('/api/esocial/responses/'+str(response['id'])+'/download').status_code==200
 body={'entity':1,'environment':'homologacao','events':[xml().replace('<verProc>RioGestao1</verProc>','<verProc>RioGestao2</verProc>')]}
 r=erp.client.post('/api/esocial/batches',json=body,headers=erp.headers);assert r.status_code==201,r.json
 assert erp.client.get('/api/esocial/batches/'+str(id)).json['item']['state']=='Processado com ocorrências'

def test_tls_failure_before_transmission_can_retry_with_existing_approval(erp,reviewer,monkeypatch):
 id=prepare(erp);action(reviewer,id,'approve');import integration_esocial
 def fail(*a):raise RemoteError('Falha TLS antes do envio.',uncertain=False)
 monkeypatch.setattr(integration_esocial,'exchange',fail)
 assert action(erp,id,'send',confirmation='ENVIAR PARA HOMOLOGACAO').json['state']=='Falha de conexão'
 monkeypatch.setattr(integration_esocial,'exchange',lambda *a:(parse_response(reception(),'send'),reception()))
 assert action(erp,id,'send',confirmation='ENVIAR PARA HOMOLOGACAO').json['state']=='Recebido'

def test_interrupted_send_is_frozen_and_cannot_be_duplicated(erp,app):
 id=prepare(erp)
 with app.app_context():get_db().execute("UPDATE esocial_batches SET state='Enviando',updated_at='2025-01-01T00:00:00+00:00' WHERE id=?",(id,));get_db().commit()
 assert action(erp,id,'recover').status_code==200
 assert action(erp,id,'send',confirmation='ENVIAR PARA HOMOLOGACAO').status_code==409
 assert action(erp,id,'cancel',reason='Tentar transmitir novamente').status_code==409

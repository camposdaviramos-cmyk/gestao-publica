import json
from test_system import app,admin,login,user
from test_erp import erp,reviewer
from test_enterprise_integrations import signature,verify_pdf
from test_esocial import xml,configuration,prepare,action,reception,CNPJ
from integration_esocial_xml import parse_response,parse
from db import get_db

def test_signature_requirement_is_specific_to_selected_report(admin):
 c,h=admin;assert signature(admin).status_code==200
 assert c.put('/api/settings',json={'signature_reports':['control:occurrences']},headers=h).status_code==200
 signed=c.get('/api/erp/control/occurrences/export?entity=1&exercise=2026&format=pdf')
 assert signed.status_code==200,signed.json;assert signed.headers.get('X-Signature-Record');verify_pdf(signed.data)
 unsigned=c.get('/api/reports/budget?format=pdf');assert unsigned.status_code==200 and not unsigned.headers.get('X-Signature-Record')
 assert c.put('/api/settings',json={'signature_reports':['control:inexistente']},headers=h).status_code==400

def test_cert_expiry_alert_is_deduplicated_and_per_administrator(admin,app):
 c,h=admin;assert signature(admin).status_code==200
 c.get('/api/me');c.get('/api/notifications');c.get('/api/notifications')
 items=c.get('/api/notifications').json['items'];assert len([i for i in items if i['title'].startswith('Certificado vence')])==1
 user(admin);other=app.test_client();login(other,'second@example.test');other.get('/api/me')
 items=other.get('/api/notifications').json['items'];assert len([i for i in items if i['title'].startswith('Certificado vence')])==1

def test_power_of_attorney_complete_dates_and_expired_send(erp,reviewer,app):
 id=prepare(erp);action(reviewer,id,'approve')
 with app.app_context():
  db=get_db();p=json.loads(db.execute("SELECT parameters FROM integration_configs WHERE provider='esocial'").fetchone()[0]);p.update(attorney_name='Outorgado de teste',attorney_type='1',attorney_registration=CNPJ,attorney_valid_from='2025-01-01',attorney_valid_until='2025-12-31')
 # Cadastro com datas completas é permitido para histórico; o envio fora da vigência é bloqueado.
 from test_integrations import configure,certificate
 c,h=erp.client,erp.headers
 r=configure((c,h),provider='esocial',version=1,parameters=p,secrets={});assert r.status_code==200,r.json
 assert action(erp,id,'cancel',reason='Repreparação com outorgado cadastrado').status_code==200
 r=c.post('/api/esocial/batches',json={'entity':1,'environment':'homologacao','events':[xml()]},headers=h);assert r.status_code==201
 id=r.json['id'];action(reviewer,id,'approve');r=action(erp,id,'send',confirmation='ENVIAR PARA HOMOLOGACAO');assert r.status_code==409 and 'Procuração' in r.json['error']
 p['attorney_valid_from']='2026-01-01';assert configure((c,h),provider='esocial',version=2,parameters=p,secrets={}).status_code==400

def test_nonperiodic_xml_import_and_mixed_group_rejection(erp):
 assert configuration((erp.client,erp.headers)).status_code==200
 source=f'<eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtExclusao/v_S_01_03_00"><evtExclusao Id="ID1{CNPJ}2026092309000000002"><ideEvento><tpAmb>2</tpAmb><procEmi>1</procEmi><verProc>RioGestao1</verProc></ideEvento><ideEmpregador><tpInsc>1</tpInsc><nrInsc>{CNPJ}</nrInsc></ideEmpregador><infoExclusao><tpEvento>S-2200</tpEvento><nrRecEvt>1.1.0000000000000000001</nrRecEvt><ideTrabalhador><cpfTrab>52998224725</cpfTrab></ideTrabalhador></infoExclusao></evtExclusao></eSocial>'
 body={'entity':1,'environment':'homologacao','events':[source,xml()]};r=erp.client.post('/api/esocial/batches',json=body,headers=erp.headers);assert r.status_code==400 and 'grupo' in r.json['error'],r.json
 body['events']=[source];r=erp.client.post('/api/esocial/batches',json=body,headers=erp.headers);assert r.status_code==201,r.json
 assert erp.client.get('/api/esocial/batches/'+str(r.json['id'])).json['item']['group_number']==2

def test_event_rejection_includes_occurrence_reason():
 eid=parse(xml())[0].get('Id');raw=reception('query',ids=[eid]).replace(b'<cdResposta>201</cdResposta><descResposta>Sucesso',b'<cdResposta>401</cdResposta><descResposta>Rejeitado')
 raw=raw.replace(b'</dhProcessamento>',b'</dhProcessamento><ocorrencias><ocorrencia><tipo>1</tipo><codigo>123</codigo><descricao>Rubrica inexistente</descricao><localizacao>/rubrica</localizacao></ocorrencia></ocorrencias>')
 result=parse_response(raw,'query');assert 'Rubrica inexistente' in result['events'][0]['description'] and result['events'][0]['code']=='401'

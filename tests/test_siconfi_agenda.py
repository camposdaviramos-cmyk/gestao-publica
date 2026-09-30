import copy
from test_integrations import app,admin,erp,configure
from db import get_db

def rows():
 return {'items':[{'exercicio':2026,'cod_ibge':3304524,'instituicao':institution,'entregavel':'RREO','periodo':1,'periodicidade':'B','tipo_relatorio':'RREO','status_relatorio':'Homologado','data_status':'2026-03-01T12:00:00Z'} for institution in ['Prefeitura de Rio das Ostras','Câmara de Rio das Ostras']],'hasMore':False}

def setup(erp,monkeypatch):
 assert configure((erp.client,erp.headers),provider='siconfi',environment='producao',parameters={'municipio':'3304524','exercicio':'2026'},secrets={}).status_code==200
 import integration_siconfi
 data=rows();monkeypatch.setattr(integration_siconfi,'consult',lambda *args:copy.deepcopy(data))
 def sync():return erp.client.post('/api/integrations/siconfi/sync',json={'entity':1},headers=erp.headers)
 return data,sync

def occurrence(erp,year=2026):
 ob=erp.make('control','obligations',description='Conferir entrega do relatório',legislation='Ato de teste',level='Municipal',owner='Controladoria',first_due='2026-03-30',interval_months=2,occurrences=6)
 return erp.make('control','occurrences',obligation=ob['id'],due_date='2026-03-30',owner='Controladoria')

def test_siconfi_sync_binding_change_notification_and_idempotence(erp,monkeypatch,app):
 data,sync=setup(erp,monkeypatch);assert sync().json['created']==2;assert sync().json['changed']==0
 report=erp.client.get('/api/integrations/siconfi/reports?entity=1&exercise=2026').json['items'][0];oc=occurrence(erp)
 url=f"/api/integrations/siconfi/reports/{report['id']}/link";body={'version':report['version'],'occurrence_id':oc['id'],'confirm_institution':'Câmara de Rio das Ostras'}
 assert erp.client.put(url,json=body,headers=erp.headers).status_code==400
 body['confirm_institution']='Prefeitura de Rio das Ostras';assert erp.client.put(url,json=body,headers=erp.headers).status_code==200
 assert sync().json['notifications']==0
 data['items'][0].update(status_relatorio='Retificado',data_status='2026-03-02T12:00:00Z')
 r=sync();assert r.json['notifications']==1 and r.json['changed']==1,r.json
 assert sync().json['notifications']==0
 detail=erp.client.get('/api/erp/object/'+str(oc['id'])).json
 assert detail['item']['state']=='Rascunho'
 assert detail['siconfi']['data']['status_relatorio']=='Retificado'
 assert any(e['operation']=='Status Siconfi atualizado' for e in detail['events'])
 assert erp.client.delete(f"/api/erp/object/{oc['id']}?version={detail['item']['version']}",headers=erp.headers).status_code==409
 with app.app_context():assert get_db().execute("SELECT COUNT(*) FROM notifications WHERE title='Atualização de obrigação no Siconfi'").fetchone()[0]==1

def test_wrong_municipality_or_incomplete_extract_rollback(erp,monkeypatch,app):
 data,sync=setup(erp,monkeypatch);data['items'][1]['cod_ibge']=1234567
 assert sync().status_code==409
 with app.app_context():assert get_db().execute('SELECT COUNT(*) FROM siconfi_reports').fetchone()[0]==0
 data['items'][1]['cod_ibge']=3304524;data['hasMore']=True
 assert sync().status_code==409

def test_duplicate_remote_versions_choose_latest_and_null_status_does_not_close(erp,monkeypatch):
 data,sync=setup(erp,monkeypatch);old=copy.deepcopy(data['items'][0]);old['data_status']='2026-01-01T12:00:00Z';data['items'].append(old);data['items'][0]['status_relatorio']=None
 assert sync().json['created']==2
 first=erp.client.get('/api/integrations/siconfi/reports?entity=1&exercise=2026').json['items'][0]
 assert first['data']['status_relatorio'] is None and first['data']['data_status']=='2026-03-01T12:00:00Z'

def test_stale_remote_response_does_not_regress_status(erp,monkeypatch):
 data,sync=setup(erp,monkeypatch);assert sync().json['created']==2
 data['items'][0].update(status_relatorio='Anterior',data_status='2026-02-01T12:00:00Z')
 assert sync().json['changed']==0
 result=erp.client.get('/api/integrations/siconfi/reports?entity=1&exercise=2026').json['items'][0]
 assert result['data']['status_relatorio']=='Homologado'

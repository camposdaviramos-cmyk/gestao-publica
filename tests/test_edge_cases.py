import json
from pathlib import Path
from app import create_app
from db import get_db

def prepare(tmp_path):
 app=create_app({'TESTING':True,'DATA_DIR':str(tmp_path),'DATABASE':str(tmp_path/'test.db')})
 client=app.test_client(); password='TesteSeguro2026!!'
 client.post('/api/setup',json={'name':'Admin Teste','email':'admin@example.test','password':password})
 response=client.post('/api/login',json={'email':'admin@example.test','password':password})
 return app,client,{'X-CSRF-Token':response.json['csrf']}

def test_malformed_payloads_return_client_errors(tmp_path):
 _,c,h=prepare(tmp_path)
 for path in ['/api/login','/api/users','/api/records/projects']:
  assert c.post(path,json=[],headers=h).status_code==400
 assert c.put('/api/settings',json={'dual_modules':[{}]},headers=h).status_code==400
 assert c.put('/api/settings',json={'max_attempts':True},headers=h).status_code==400
 assert c.post('/api/users',json={'name':'Teste Outro','email':'outro@example.test','password':'TesteSeguro2026!!','group_id':2,'active':'false'},headers=h).status_code==400

def test_report_day_uses_brasilia_timezone(tmp_path):
 app,c,h=prepare(tmp_path)
 for title in ['Anterior','Incluído']:
  response=c.post('/api/records/projects',json={'title':title,'status':'Planejado','data':{}},headers=h)
  assert response.status_code==201
 with app.app_context():
  db=get_db();db.execute("UPDATE records SET created_at='2026-09-22T02:59:59+00:00' WHERE title='Anterior'")
  db.execute("UPDATE records SET created_at='2026-09-22T03:00:00+00:00' WHERE title='Incluído'");db.commit()
 report=c.get('/api/reports/projects?from=2026-09-22&to=2026-09-22').json
 assert report['count']==1 and report['rows'][0][1]=='Incluído'

def test_dashboard_aggregates_and_permissions(tmp_path):
 app,c,h=prepare(tmp_path)
 c.put('/api/settings',json={'dual_modules':[]},headers=h)
 for amount,status in [('0.29','Planejado'),('100.01','Em execução')]:
  c.post('/api/records/budget',json={'title':'Ação agregada','department':'Fazenda','status':status,'amount':amount,'data':{}},headers=h)
 report=c.get('/api/dashboard').json
 assert report['budget_total']==100.3 and report['actions']==2 and report['active_actions']==1
 assert report['departments']['Fazenda']==100.3

def test_missing_key_does_not_silently_replace_existing_key(tmp_path):
 app,_,_=prepare(tmp_path);key_file=tmp_path/'encryption.key';original=key_file.read_bytes();key_file.unlink()
 try:
  try:create_app({'DATA_DIR':str(tmp_path),'DATABASE':app.config['DATABASE']})
  except RuntimeError as e:assert 'chave' in str(e)
  else:raise AssertionError('Deveria bloquear banco existente sem chave')
 finally:key_file.write_bytes(original)

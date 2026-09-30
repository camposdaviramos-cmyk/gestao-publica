import io
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import pytest
from app import create_app
from db import get_db
from domain import money, password_strength, business_deadline
from backup import restore_backup

PASSWORD='TesteSeguro2026!!'

@pytest.fixture
def app(tmp_path):
 return create_app({'TESTING':True,'DATA_DIR':str(tmp_path),'DATABASE':str(tmp_path/'test.db')})

def login(client,email='admin@example.test',password=PASSWORD):
 response=client.post('/api/login',json={'email':email,'password':password})
 assert response.status_code==200,response.json
 return {'X-CSRF-Token':response.json['csrf']}

@pytest.fixture
def admin(app):
 client=app.test_client()
 response=client.post('/api/setup',json={'name':'Administrador Teste','email':'admin@example.test','password':PASSWORD})
 assert response.status_code==201,response.json
 return client,login(client)

def user(admin,email='second@example.test',group=1,force=False,**extra):
 client,headers=admin
 response=client.post('/api/users',json={'name':'Segundo Servidor','email':email,'password':PASSWORD,'group_id':group,'active':True,'force_password':force,**extra},headers=headers)
 assert response.status_code==200,response.json
 return response.json['id']

def record(title='Ação de teste',**extra):
 return {'title':title,'department':'Fazenda','status':'Planejado','amount':'1234.56','data':{'year':'2026','goal':'10 unidades'},**extra}

def test_setup_single_use_and_password_hash(app,admin):
 client,_=admin
 assert client.post('/api/setup',json={}).status_code==409
 with app.app_context():
  password=get_db().execute('SELECT password FROM users').fetchone()[0]
  assert PASSWORD not in password and password.startswith('scrypt:')

def test_anonymous_and_csrf_blocked(app,admin):
 assert app.test_client().get('/api/dashboard').status_code==401
 client,_=admin
 assert client.post('/api/records/budget',json=record()).status_code==403
 assert client.post('/api/login',json={},headers={'Origin':'https://evil.example'}).status_code==403

def test_cookie_and_headers(admin):
 client,_=admin; response=client.post('/api/login',json={'email':'admin@example.test','password':PASSWORD})
 cookie=response.headers['Set-Cookie']
 assert 'HttpOnly' in cookie and 'SameSite=Strict' in cookie
 assert 'frame-ancestors' in response.headers['Content-Security-Policy']

def test_role_enforced_server_side(app,admin):
 user(admin,group=3); reader=app.test_client(); h=login(reader,'second@example.test')
 assert reader.get('/api/records/budget').status_code==200
 assert reader.get('/api/users').status_code==403
 assert reader.post('/api/records/budget',json=record(),headers=h).status_code==403
 assert reader.get('/api/backups').status_code==403

def test_individual_override(app,admin):
 user(admin,group=2,permissions={'budget':[]}); client=app.test_client(); login(client,'second@example.test')
 assert client.get('/api/records/budget').status_code==403
 assert client.get('/api/records/projects').status_code==200

def test_dual_custody_and_single_decision(app,admin):
 client,h=admin; user(admin)
 response=client.post('/api/records/budget',json=record(),headers=h)
 assert response.status_code==202; approval=response.json['id']
 assert client.get('/api/records/budget').json['total']==0
 decision={'decision':'Aprovado','reason':'Conferido pela equipe técnica'}
 assert client.post(f'/api/approvals/{approval}/decide',json=decision,headers=h).status_code==403
 reviewer=app.test_client(); rh=login(reviewer,'second@example.test')
 assert reviewer.post(f'/api/approvals/{approval}/decide',json=decision,headers=rh).status_code==200
 assert reviewer.post(f'/api/approvals/{approval}/decide',json=decision,headers=rh).status_code==409
 row=client.get('/api/records/budget').json['items'][0]
 assert row['amount']==1234.56
 assert client.get('/api/notifications').json['items'][0]['read']==0

def test_rejection_does_not_mutate(app,admin):
 client,h=admin; user(admin); reviewer=app.test_client(); rh=login(reviewer,'second@example.test')
 response=client.post('/api/records/budget',json=record(),headers=h)
 assert reviewer.post(f"/api/approvals/{response.json['id']}/decide",json={'decision':'Rejeitado','reason':'Ajustar os dados primeiro'},headers=rh).status_code==200
 assert client.get('/api/records/budget').json['total']==0

def test_stale_record_rejected(admin):
 client,h=admin; body=record(status='Planejado',amount=0,data={'owner':'Equipe'})
 res=client.post('/api/records/projects',json=body,headers=h); assert res.status_code==201
 rid=res.json['id']; body['version']=1; body['title']='Título atualizado'
 assert client.put(f'/api/records/projects/{rid}',json=body,headers=h).status_code==200
 assert client.put(f'/api/records/projects/{rid}',json=body,headers=h).status_code==409
 assert client.delete(f'/api/records/projects/{rid}?version=1',headers=h).status_code==409
 assert client.delete(f'/api/records/projects/{rid}?version=2',headers=h).status_code==200

def test_stale_approval_cannot_overwrite(app,admin):
 client,h=admin; user(admin); reviewer=app.test_client(); rh=login(reviewer,'second@example.test'); decision={'decision':'Aprovado','reason':'Conferido e autorizado'}
 created=client.post('/api/records/budget',json=record(),headers=h).json['id']
 reviewer.post(f'/api/approvals/{created}/decide',json=decision,headers=rh)
 row=client.get('/api/records/budget').json['items'][0]
 a=client.put(f"/api/records/budget/{row['id']}",json=record(title='Primeira alteração',version=1),headers=h).json['id']
 b=client.put(f"/api/records/budget/{row['id']}",json=record(title='Segunda alteração',version=1),headers=h).json['id']
 assert reviewer.post(f'/api/approvals/{a}/decide',json=decision,headers=rh).status_code==200
 assert reviewer.post(f'/api/approvals/{b}/decide',json=decision,headers=rh).status_code==409

def test_lockout_and_login_audit(app,admin):
 client,h=admin
 for _ in range(5): assert client.post('/api/login',json={'email':'admin@example.test','password':'wrong'}).status_code==401
 assert client.post('/api/login',json={'email':'admin@example.test','password':PASSWORD}).status_code==429
 with app.app_context(): assert get_db().execute("SELECT count(*) FROM audit WHERE action='Login recusado'").fetchone()[0]==6

def test_force_password_and_session_revocation(app,admin):
 user(admin,force=True); c=app.test_client(); h=login(c,'second@example.test')
 assert c.get('/api/dashboard').status_code==428
 result=c.post('/api/password',json={'current':PASSWORD,'password':'NovaSenhaSegura2026!!'},headers=h)
 assert result.status_code==200
 assert c.get('/api/dashboard').status_code==401
 login(c,'second@example.test','NovaSenhaSegura2026!!'); assert c.get('/api/dashboard').status_code==200

def test_schedule_blocks_login(app,admin):
 from domain import local_time
 excluded=(local_time().weekday()+1)%7
 user(admin,schedule={'days':[excluded],'start':'08:00','end':'17:00'})
 c=app.test_client(); response=c.post('/api/login',json={'email':'second@example.test','password':PASSWORD})
 assert response.status_code==403

def test_admin_recovery_preserved(admin):
 c,h=admin
 assert c.put('/api/groups/1',json={'name':'Restricted','permissions':{}},headers=h).status_code==400
 assert c.put('/api/users/1',json={'name':'Admin Teste','email':'admin@example.test','group_id':3,'active':False,'force_password':False},headers=h).status_code==400

def test_audit_is_append_only(app,admin):
 c,_=admin;c.get('/api/dashboard')
 with app.app_context():
  with pytest.raises(sqlite3.IntegrityError): get_db().execute('DELETE FROM audit')
  with pytest.raises(sqlite3.IntegrityError): get_db().execute("UPDATE audit SET actor='Alterado'")

def test_ticket_resolution_comments_and_notifications(admin):
 c,h=admin; payload={'title':'Falha de acesso ao módulo','department':'Fazenda','status':'Aberto','data':{'priority':'Médio','description':'Não foi possível acessar a consulta de registros.'}}
 res=c.post('/api/records/tickets',json=payload,headers=h); assert res.status_code==201
 rid=res.json['id']; row=c.get('/api/records/tickets').json['items'][0]
 assert row['data']['response_due'] and row['data']['resolution_due']
 assert c.post(f'/api/tickets/{rid}/comments',json={'body':'Equipe iniciou a análise da ocorrência.'},headers=h).status_code==201
 payload['version']=1;payload['status']='Resolvido'
 assert c.put(f'/api/records/tickets/{rid}',json=payload,headers=h).status_code==400
 payload['data']['resolution']='Permissões revisadas e acesso restabelecido.'
 assert c.put(f'/api/records/tickets/{rid}',json=payload,headers=h).status_code==200
 assert len(c.get(f'/api/tickets/{rid}/comments').json['items'])==1
 assert len(c.get('/api/notifications').json['items'])>=2

def test_business_hours_weekend_and_holiday():
 start=datetime(2026,9,25,19,0,tzinfo=timezone.utc) # sexta, 16h em Brasília
 assert business_deadline(start,2,True).startswith('2026-09-28T12:00')
 assert business_deadline(start,2,True,['2026-09-28']).startswith('2026-09-29T12:00')
 assert business_deadline(start,2,False).startswith('2026-09-25T21:00')

@pytest.mark.parametrize('value',['-1','NaN','Infinity','1.234','9999999999999'])
def test_money_rejects_invalid(value):
 with pytest.raises(ValueError):money(value)

def test_money_and_strength():
 assert money('0.29')==29
 assert password_strength('abcd123')=='Fraca'
 assert password_strength('abcd12345!')=='Média'
 assert password_strength(PASSWORD)=='Forte'

@pytest.mark.parametrize('fmt,signature',[('pdf',b'%PDF'),('xlsx',b'PK'),('docx',b'PK'),('csv',b'\xef\xbb\xbf')])
def test_real_report_formats(admin,fmt,signature):
 c,h=admin;c.post('/api/records/projects',json=record(amount=0,data={}),headers=h)
 result=c.get('/api/reports/projects?format='+fmt)
 assert result.status_code==200,result.json
 assert result.data.startswith(signature)

def test_csv_formula_injection_and_signature_block(admin):
 c,h=admin;c.post('/api/records/projects',json=record(title='=HYPERLINK("test")',amount=0,data={}),headers=h)
 result=c.get('/api/reports/projects?format=csv');assert "'=HYPERLINK" in result.data.decode('utf-8-sig')
 c.put('/api/settings',json={'signature_reports':['projects']},headers=h)
 assert c.get('/api/reports/projects?format=pdf').status_code==409
 assert c.get('/api/reports/projects?format=json').status_code==200

def test_backup_and_restore(app,admin,tmp_path):
 c,h=admin;c.post('/api/records/projects',json=record(amount=0,data={}),headers=h)
 backup=c.post('/api/backups',json={},headers=h);assert backup.status_code==201
 filename=backup.json['name']; encrypted=c.get('/api/backups/'+filename)
 assert encrypted.status_code==200 and not encrypted.data.startswith(b'SQLite format')
 destination=tmp_path/'restored.db'; restore_backup(Path(app.config['DATA_DIR'])/'backups'/filename,destination,app.config['FERNET_KEY'])
 with sqlite3.connect(destination) as db:
  assert db.execute('SELECT count(*) FROM records').fetchone()[0]==1
  assert db.execute('SELECT count(*) FROM sessions').fetchone()[0]==0

def test_maintenance_runs_only_registered_scripts(admin):
 c,h=admin; entries=c.get('/api/maintenance').json['items']
 for entry in entries:
  result=c.post(f"/api/maintenance/{entry['id']}/run",json={},headers=h);assert result.status_code==200
 assert c.post('/api/maintenance/999/run',json={},headers=h).status_code==404

def test_personal_shortcuts_isolated(app,admin):
 c,h=admin;user(admin,group=3);other=app.test_client();oh=login(other,'second@example.test')
 assert c.post('/api/shortcuts',json={'title':'Inseguro','url':'javascript:alert(1)'},headers=h).status_code==400
 assert c.post('/api/shortcuts',json={'title':'Ferramenta','url':'https://example.org'},headers=h).status_code==201
 assert other.get('/api/shortcuts').json['items']==[]
 other.delete('/api/shortcuts/1',headers=oh)
 assert len(c.get('/api/shortcuts').json['items'])==1

def test_training_progress_individual(app,admin):
 c,h=admin;user(admin,group=3)
 lesson=c.get('/api/training').json['lessons'][0]['id']
 assert c.post('/api/training/'+lesson+'/complete',json={},headers=h).status_code==200
 assert lesson in c.get('/api/training').json['completed']
 other=app.test_client();login(other,'second@example.test');assert other.get('/api/training').json['completed']==[]

def test_public_portal_only_published_and_no_user_data(app,admin):
 c,h=admin;c.put('/api/settings',json={'dual_modules':[]},headers=h)
 for status in ['Rascunho','Publicado']:
  assert c.post('/api/records/transparency',json=record(status=status,data={'description':'Conteúdo para publicação'}),headers=h).status_code==201
 public=app.test_client().get('/api/publications').json['items']
 assert len(public)==1 and 'created_by' not in public[0]

def test_database_persists_across_app_restart(app,admin):
 c,h=admin;c.post('/api/records/projects',json=record(amount=0,data={}),headers=h)
 second=create_app({'TESTING':True,'DATA_DIR':app.config['DATA_DIR'],'DATABASE':app.config['DATABASE']})
 new=second.test_client();login(new);assert new.get('/api/records/projects').json['total']==1

def test_input_validation_and_unknown_module(admin):
 c,h=admin
 assert c.post('/api/records/projects',json=record(title='x'),headers=h).status_code==400
 assert c.post('/api/records/budget',json=record(data={'year':'invalid'}),headers=h).status_code==400
 assert c.get('/api/records/not-real').status_code==404
 assert c.post('/api/records/projects',json=record(status='Inventado'),headers=h).status_code==400

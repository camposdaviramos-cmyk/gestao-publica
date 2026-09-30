import json
import re
from datetime import datetime
from urllib.parse import urlparse
from flask import g, request, jsonify
from werkzeug.security import generate_password_hash
from auth import ApiError, require, check_password, email_address, validate_permissions, validate_schedule
from db import get_db, settings, audit, key, DEFAULTS
from domain import SCOPES, ACTIONS, MODULES, now

def install_admin(app):
 @app.get('/api/users')
 def users():
  require('users'); rows=get_db().execute('SELECT u.id,u.name,u.email,u.department,u.group_id,u.active,u.force_password,u.locked_until,u.schedule,u.permissions,g.name group_name FROM users u JOIN groups g ON g.id=u.group_id ORDER BY u.name').fetchall()
  result=[]
  for r in rows:
   d=dict(r); d['schedule']=json.loads(d['schedule']); d['permissions']=json.loads(d['permissions']); result.append(d)
  audit('Consulta','users'); return jsonify(items=result)

 @app.post('/api/users')
 @app.put('/api/users/<int:user_id>')
 def save_user(user_id=None):
  require('users','write'); db=get_db(); db.execute('BEGIN IMMEDIATE'); data=request.get_json()
  name=str(data.get('name','')).strip(); email=email_address(data.get('email',''))
  if not 3<=len(name)<=120: raise ApiError('Nome deve conter de 3 a 120 caracteres.')
  try: group_id=int(data.get('group_id',0))
  except (ValueError,TypeError): raise ApiError('Selecione um grupo.')
  if not db.execute('SELECT 1 FROM groups WHERE id=?',(group_id,)).fetchone(): raise ApiError('Grupo não encontrado.')
  existing=db.execute('SELECT * FROM users WHERE id=?',(user_id,)).fetchone() if user_id else None
  if user_id and not existing: raise ApiError('Usuário não encontrado.',404)
  if any(k in data and type(data[k]) is not bool for k in ['active','force_password']): raise ApiError('Indicadores de conta devem ser verdadeiro ou falso.')
  active=bool(data.get('active',True)); force=bool(data.get('force_password',True)); department=str(data.get('department','')).strip()[:120]
  schedule=validate_schedule(data.get('schedule',{})); permissions=validate_permissions(data.get('permissions',{}))
  # Preserva uma conta administrativa recuperável; o grupo reservado é imutável.
  if existing and existing['group_id']==1 and (not active or group_id!=1 or schedule or permissions):
   if db.execute('SELECT count(*) FROM users WHERE group_id=1 AND active=1 AND id<>? AND schedule=\'{}\' AND permissions=\'{}\'',(user_id,)).fetchone()[0]==0: raise ApiError('Mantenha pelo menos um administrador ativo, sem restrições individuais.')
  if existing and existing['group_id']==1 and (not active or group_id!=1 or schedule or permissions):
   if not db.execute("SELECT 1 FROM users u WHERE group_id=1 AND active=1 AND id<>? AND schedule='{}' AND permissions='{}' AND NOT EXISTS(SELECT 1 FROM directory_bindings b WHERE b.user_id=u.id)",(user_id,)).fetchone():raise ApiError('Preserve um administrador local ativo para recuperação.',409)
  if user_id==g.user['id'] and (not active or group_id!=existing['group_id'] or schedule!=json.loads(existing['schedule']) or permissions!=json.loads(existing['permissions'])): raise ApiError('Peça a outro administrador para alterar seu próprio acesso.')
  password=data.get('password','')
  if existing and db.execute('SELECT 1 FROM directory_bindings WHERE user_id=?',(user_id,)).fetchone():
   if password or force:raise ApiError('Conta LDAP: altere a senha no diretório; não marque troca de senha local.')
  if not existing or password: check_password(password)
  if existing:
   db.execute('UPDATE users SET name=?,email=?,department=?,group_id=?,active=?,force_password=?,schedule=?,permissions=?,failures=0,locked_until=NULL WHERE id=?',(name,email,department,group_id,active,force,json.dumps(schedule),json.dumps(permissions),user_id))
   if password: db.execute('UPDATE users SET password=?,force_password=1 WHERE id=?',(generate_password_hash(password),user_id))
   db.execute('DELETE FROM sessions WHERE user_id=?',(user_id,))
  else:
   user_id=db.execute('INSERT INTO users(name,email,password,group_id,department,active,force_password,schedule,permissions,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)',(name,email,generate_password_hash(password),group_id,department,active,force,json.dumps(schedule),json.dumps(permissions),now())).lastrowid
  audit('Usuário atualizado' if existing else 'Usuário criado','users',user_id,{'email':email,'group':group_id})
  return jsonify(id=user_id,message='Usuário salvo. As sessões anteriores foram encerradas.')

 @app.get('/api/groups')
 def groups():
  if 'read' not in g.permissions.get('groups',[]) and 'read' not in g.permissions.get('users',[]): require('groups')
  return jsonify(items=[{**dict(r),'permissions':json.loads(r['permissions'])} for r in get_db().execute('SELECT * FROM groups ORDER BY id')],scopes=SCOPES,actions=ACTIONS)

 @app.post('/api/groups')
 @app.put('/api/groups/<int:group_id>')
 def save_group(group_id=None):
  require('groups','write'); data=request.get_json(); name=str(data.get('name','')).strip()
  if not 3<=len(name)<=80: raise ApiError('Nome do grupo deve conter de 3 a 80 caracteres.')
  permissions=validate_permissions(data.get('permissions',{})); db=get_db()
  if group_id==1: raise ApiError('O grupo Administração é reservado para recuperação e gestão do sistema.')
  if group_id:
   if not db.execute('SELECT 1 FROM groups WHERE id=?',(group_id,)).fetchone(): raise ApiError('Grupo não encontrado.',404)
   db.execute('UPDATE groups SET name=?,permissions=? WHERE id=?',(name,json.dumps(permissions),group_id))
   db.execute('DELETE FROM sessions WHERE user_id IN (SELECT id FROM users WHERE group_id=?)',(group_id,))
  else: group_id=db.execute('INSERT INTO groups(name,permissions) VALUES(?,?)',(name,json.dumps(permissions))).lastrowid
  audit('Grupo salvo','groups',group_id); return jsonify(message='Grupo e permissões salvos.')

 @app.get('/api/settings')
 def get_settings():
  require('settings'); return jsonify(settings())

 @app.put('/api/settings')
 def save_settings():
  require('settings','write'); body=request.get_json(); values=settings()
  for name in ['min_password','max_attempts','lock_minutes','session_minutes']:
   if name in body:
    low,high={'min_password':(11,64),'max_attempts':(3,20),'lock_minutes':(1,1440),'session_minutes':(5,480)}[name]
    if type(body[name])!=int or not low<=body[name]<=high: raise ApiError(f'{name}: informe um número entre {low} e {high}.')
    values[name]=body[name]
  for name in ['municipality','department','support_email','support_phone','contract_date']:
   if name in body:
    if not isinstance(body[name],str) or len(body[name])>200: raise ApiError('Configuração inválida.')
    values[name]=body[name].strip()
  if values['contract_date']:
   try: datetime.strptime(values['contract_date'],'%Y-%m-%d')
   except ValueError: raise ApiError('Data de contrato inválida.')
  for name in ['dual_modules','signature_reports','holidays']:
   if name in body:
    if not isinstance(body[name],list) or len(body[name])>500: raise ApiError('Lista de configuração inválida.')
    values[name]=body[name]
  from erp_catalog import CATALOG
  report_keys=set(MODULES)|set(CATALOG)|{m+':'+r for m,spec in CATALOG.items() for r in spec['resources']}
  if any(not isinstance(x,str) or x not in MODULES for x in values['dual_modules']) or any(not isinstance(x,str) or x not in report_keys for x in values['signature_reports']):raise ApiError('Módulo ou relatório inválido.')
  for day in values['holidays']:
   try: datetime.strptime(day,'%Y-%m-%d')
   except (ValueError,TypeError): raise ApiError('Feriado inválido; utilize AAAA-MM-DD.')
  if 'signature_required' in body:
   if type(body['signature_required'])!=bool: raise ApiError('Configuração de assinatura inválida.')
   values['signature_required']=body['signature_required']
  for k,v in values.items(): get_db().execute('INSERT OR REPLACE INTO settings VALUES(?,?)',(k,json.dumps(v,ensure_ascii=False)))
  audit('Configurações alteradas','settings',detail={'fields':list(body)})
  return jsonify(message='Configurações salvas.')

 @app.get('/api/audit')
 def audit_log():
  require('audit'); page=max(1,request.args.get('page',1,type=int)); q=request.args.get('q','')[:150]
  where='actor LIKE ? OR action LIKE ? OR module LIKE ?'; args=['%'+q+'%']*3
  total=get_db().execute('SELECT count(*) FROM audit WHERE '+where,args).fetchone()[0]
  rows=get_db().execute('SELECT * FROM audit WHERE '+where+' ORDER BY id DESC LIMIT 40 OFFSET ?',(*args,(page-1)*40)).fetchall()
  return jsonify(items=[dict(r) for r in rows],total=total,page=page,limit=40)

 @app.get('/api/notifications')
 def notifications(): return jsonify(items=[dict(r) for r in get_db().execute('SELECT * FROM notifications WHERE user_id=? ORDER BY id DESC LIMIT 60',(g.user['id'],))])

 @app.post('/api/notifications/read')
 def read_notifications():
  get_db().execute('UPDATE notifications SET read=1 WHERE user_id=?',(g.user['id'],)); return jsonify(message='Notificações lidas.')

 @app.get('/api/shortcuts')
 def shortcuts(): return jsonify(items=[dict(r) for r in get_db().execute('SELECT * FROM shortcuts WHERE user_id=? ORDER BY id',(g.user['id'],))])

 @app.post('/api/shortcuts')
 def add_shortcut():
  data=request.get_json(); title=str(data.get('title','')).strip(); url=str(data.get('url','')).strip()
  parsed=urlparse(url)
  if not 2<=len(title)<=60 or len(url)>1000 or parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password: raise ApiError('Informe um título e uma URL HTTPS válida, sem credenciais.')
  if get_db().execute('SELECT count(*) FROM shortcuts WHERE user_id=?',(g.user['id'],)).fetchone()[0]>=20: raise ApiError('Limite de 20 atalhos por usuário.')
  get_db().execute('INSERT INTO shortcuts(user_id,title,url) VALUES(?,?,?)',(g.user['id'],title,url)); return jsonify(message='Atalho adicionado.'),201

 @app.delete('/api/shortcuts/<int:item_id>')
 def delete_shortcut(item_id):
  get_db().execute('DELETE FROM shortcuts WHERE id=? AND user_id=?',(item_id,g.user['id'])); return jsonify(message='Atalho removido.')

 @app.get('/api/maintenance')
 def maintenance():
  require('maintenance'); return jsonify(items=[dict(r) for r in get_db().execute('SELECT id,name,created_at FROM maintenance')])

 @app.post('/api/maintenance/<int:script_id>/run')
 def run_script(script_id):
  require('maintenance','write'); db=get_db(); row=db.execute('SELECT * FROM maintenance WHERE id=?',(script_id,)).fetchone()
  if not row: raise ApiError('Rotina não encontrada.',404)
  script=key().decrypt(row['encrypted_script'].encode()).decode()
  if script not in ['ANALYZE','PRAGMA integrity_check']: raise ApiError('Rotina não autorizada.',403)
  result=[tuple(r) for r in db.execute(script).fetchall()]; audit('Rotina executada','maintenance',script_id,{'name':row['name'],'result':result})
  return jsonify(message='Rotina concluída.',result=result)

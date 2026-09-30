import hashlib
import json
import re
import secrets
from datetime import datetime, timedelta, timezone
from flask import g, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db, settings, audit
from domain import now, local_time, password_strength, SCOPES, ACTIONS

class ApiError(Exception):
 def __init__(self,message,status=400): self.message=message; self.status=status

def require(module,action='read'):
 if not getattr(g,'user',None): raise ApiError('Entre na sua conta para continuar.',401)
 if action not in g.permissions.get(module,[]): raise ApiError('Seu perfil não tem permissão para esta operação.',403)

def check_password(value):
 if not isinstance(value,str) or len(value)<settings()['min_password'] or len(value)>128:
  raise ApiError(f"A senha deve conter entre {settings()['min_password']} e 128 caracteres.")
 if password_strength(value)!='Forte': raise ApiError('Use letras, números e pelo menos dois caracteres especiais para uma senha forte.')

def email_address(value):
 value=str(value).strip().lower()
 if len(value)>200 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',value): raise ApiError('Informe um e-mail válido.')
 return value

def validate_permissions(value):
 if not isinstance(value,dict) or any(m not in SCOPES or not isinstance(a,list) or any(x not in ACTIONS for x in a) for m,a in value.items()): raise ApiError('Permissões inválidas.')
 return value

def validate_schedule(value):
 if not isinstance(value,dict): raise ApiError('Horários inválidos.')
 if not value: return {}
 if set(value)!={'days','start','end'} or not isinstance(value['days'],list) or not value['days'] or any(type(x)!=int or x not in range(7) for x in value['days']): raise ApiError('Informe os dias permitidos (0 = segunda-feira).')
 if not all(re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d',str(value[x])) for x in ['start','end']) or value['start']>=value['end']: raise ApiError('O término do acesso deve ser posterior ao início.')
 return value

def allowed_time(user):
 schedule=json.loads(user['schedule'])
 if not schedule: return True
 dt=local_time()
 return dt.weekday() in schedule['days'] and schedule['start']<=dt.strftime('%H:%M')<schedule['end']

def public_user(user):
 return {k:user[k] for k in ['id','name','email','department','group_id','active','force_password']}

def install_auth(app):
 @app.errorhandler(ApiError)
 def api_error(error): return jsonify(error=error.message),error.status

 @app.before_request
 def authenticate():
  g.user=None; g.permissions={}; g.csrf=None
  if not request.path.startswith('/api/'): return
  if request.method in ['POST','PATCH','PUT','DELETE']:
   if request.headers.get('Origin') and request.headers['Origin'].rstrip('/')!=request.host_url.rstrip('/'): raise ApiError('Origem da solicitação não autorizada.',403)
   if request.method!='DELETE' and not request.is_json: raise ApiError('Envie dados no formato JSON.',415)
   if request.method!='DELETE' and not isinstance(request.get_json(silent=True),dict): raise ApiError('Envie um objeto JSON válido.')
  token=request.cookies.get('rio_session','')
  if token:
   row=get_db().execute('SELECT s.csrf,s.expires_at,u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token=?',(hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
   if row and row['expires_at']>now() and row['active'] and allowed_time(row) and (not row['locked_until'] or row['locked_until']<=now()):
    g.user=dict(row); g.csrf=row['csrf']
    group=get_db().execute('SELECT permissions FROM groups WHERE id=?',(row['group_id'],)).fetchone()
    g.permissions={**json.loads(group['permissions']),**json.loads(row['permissions'])}
  public=['/api/status','/api/login','/api/setup','/api/publications']
  if request.path in public or request.path.startswith('/api/public/') or request.path.startswith('/api/help/') or request.path.startswith('/api/auction/webhook/'): return
  if not g.user: raise ApiError('Sua sessão terminou. Entre novamente.',401)
  if g.user['force_password'] and request.path not in ['/api/me','/api/password','/api/logout']: raise ApiError('Altere sua senha antes de continuar.',428)
  if request.method in ['POST','PATCH','PUT','DELETE'] and not secrets.compare_digest(request.headers.get('X-CSRF-Token',''),g.csrf): raise ApiError('Sessão de segurança inválida. Atualize a página.',403)

 @app.get('/api/status')
 def status(): return jsonify(setup_required=not bool(get_db().execute('SELECT 1 FROM users').fetchone()),version='1.0.0',environment='Local' if not current_app.config['SECURE_COOKIE'] else 'Servidor')

 @app.post('/api/setup')
 def setup():
  db=get_db(); db.execute('BEGIN IMMEDIATE')
  if db.execute('SELECT 1 FROM users').fetchone(): raise ApiError('A configuração inicial já foi concluída.',409)
  if request.remote_addr not in ['127.0.0.1','::1']: raise ApiError('Faça a configuração inicial no servidor local.',403)
  data=request.get_json(); name=str(data.get('name','')).strip()
  if not 3<=len(name)<=120: raise ApiError('Informe seu nome completo.')
  email=email_address(data.get('email','')); check_password(data.get('password',''))
  db.execute('INSERT INTO users(name,email,password,group_id,department,created_at) VALUES(?,?,?,?,?,?)',(name,email,generate_password_hash(data['password']),1,'Administração',now()))
  if data.get('demo') is True:
   from seed import seed_demo
   seed_demo(db)
  audit('Configuração inicial','settings',actor=name)
  return jsonify(message='Administrador criado. Entre com sua conta.'),201

 @app.post('/api/login')
 def login():
  db=get_db(); data=request.get_json(); email=str(data.get('email','')).strip().lower()[:200]
  user=db.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
  def denied(message='E-mail ou senha inválidos.',code=401):
   audit('Login recusado','auth',detail={'reason':message},actor=email or 'Não informado'); db.commit(); raise ApiError(message,code)
  if user and user['locked_until'] and user['locked_until']>now(): return denied('Acesso temporariamente bloqueado. Aguarde o prazo de desbloqueio.',429)
  password=data.get('password','')
  if not isinstance(password,str) or len(password)>128: password=''
  # Mesmo custo de hashing quando o e-mail não existe.
  password_hash=user['password'] if user else current_app.config['DUMMY_HASH']
  binding=db.execute("SELECT b.*,c.version config_version FROM directory_bindings b LEFT JOIN integration_configs c ON c.entity_id=b.entity_id AND c.provider='ldap' AND c.environment='producao' WHERE b.user_id=?",(user['id'],)).fetchone() if user else None
  valid=check_password_hash(password_hash,password)
  if user:
   from integration_directory import authenticate_directory
   directory_valid=authenticate_directory(user,password)
   if directory_valid is not None:valid=directory_valid
  db.execute('BEGIN IMMEDIATE')
  if user:
   fresh=db.execute('SELECT * FROM users WHERE id=?',(user['id'],)).fetchone()
   current_binding=db.execute("SELECT b.*,c.version config_version FROM directory_bindings b LEFT JOIN integration_configs c ON c.entity_id=b.entity_id AND c.provider='ldap' AND c.environment='producao' WHERE b.user_id=?",(user['id'],)).fetchone()
   if not fresh or fresh['password']!=user['password'] or (dict(binding) if binding else None)!=(dict(current_binding) if current_binding else None):return denied()
   user=fresh
   if user['locked_until'] and user['locked_until']>now():return denied('Acesso temporariamente bloqueado. Aguarde o prazo de desbloqueio.',429)
  if not user or not valid:
   if user:
    failures=(0 if user['locked_until'] and user['locked_until']<=now() else user['failures'])+1
    until=(datetime.now(timezone.utc)+timedelta(minutes=settings()['lock_minutes'])).isoformat(timespec='seconds') if failures>=settings()['max_attempts'] else None
    db.execute('UPDATE users SET failures=?,locked_until=? WHERE id=?',(failures,until,user['id']))
   return denied()
  if not user['active']: return denied()
  if not allowed_time(user): return denied('Acesso fora dos dias e horários permitidos.',403)
  db.execute('UPDATE users SET failures=0,locked_until=NULL WHERE id=?',(user['id'],))
  db.execute('DELETE FROM sessions WHERE expires_at<?',(now(),))
  token=secrets.token_urlsafe(48); csrf=secrets.token_urlsafe(32)
  expiry=(datetime.now(timezone.utc)+timedelta(minutes=settings()['session_minutes'])).isoformat(timespec='seconds')
  db.execute('INSERT INTO sessions VALUES(?,?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),user['id'],csrf,expiry))
  g.user=dict(user); audit('Login autorizado','auth')
  response=jsonify(user=public_user(user),csrf=csrf)
  response.set_cookie('rio_session',token,httponly=True,secure=current_app.config['SECURE_COOKIE'],samesite='Strict',max_age=settings()['session_minutes']*60)
  return response

 @app.get('/api/me')
 def me(): return jsonify(user=public_user(g.user),permissions=g.permissions,csrf=g.csrf,settings={k:v for k,v in settings().items() if k in ['municipality','department','demo','support_email','support_phone','dual_modules']},modules=__import__('domain').MODULES,erp=__import__('erp_catalog').CATALOG)

 @app.post('/api/logout')
 def logout():
  get_db().execute('DELETE FROM sessions WHERE token=?',(hashlib.sha256(request.cookies.get('rio_session','').encode()).hexdigest(),)); audit('Logout','auth')
  response=jsonify(message='Sessão encerrada.'); response.delete_cookie('rio_session'); return response

 @app.post('/api/password')
 def change_password():
  data=request.get_json()
  if get_db().execute('SELECT 1 FROM directory_bindings WHERE user_id=?',(g.user['id'],)).fetchone():raise ApiError('Altere a senha no diretório institucional. A senha LDAP não é mantida neste sistema.',409)
  if not check_password_hash(g.user['password'],str(data.get('current',''))): raise ApiError('A senha atual não confere.')
  check_password(data.get('password',''))
  if check_password_hash(g.user['password'],data['password']): raise ApiError('Escolha uma senha diferente da atual.')
  get_db().execute('UPDATE users SET password=?,force_password=0 WHERE id=?',(generate_password_hash(data['password']),g.user['id']))
  get_db().execute('DELETE FROM sessions WHERE user_id=?',(g.user['id'],)); audit('Senha alterada','auth')
  return jsonify(message='Senha alterada. Entre novamente.')

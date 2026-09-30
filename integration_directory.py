"""LDAP v3: TLS obrigatório, referências desabilitadas, identidades explicitamente vinculadas."""
import json,re,ssl,secrets
from werkzeug.security import generate_password_hash
from flask import g,request,jsonify
from ldap3 import Server,Connection,Tls,BASE,SUBTREE
from ldap3.utils.conv import escape_filter_chars
from ldap3.utils.dn import parse_dn
from ldap3.core.exceptions import LDAPException
from auth import ApiError,require
from db import get_db,audit
from domain import now
from erp_core import entity_access,integer
from integration_transport import RemoteError

def validate_settings(parameters,secrets,enabled):
 if not enabled:return
 host=parameters['host']
 if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9.\-]{0,252}',host):raise ApiError('Informe somente o nome DNS ou IPv4 do servidor LDAP.')
 integer(parameters['port'],'Porta',1,65535)
 if parameters['tls_mode'] not in ['ldaps','starttls']:raise ApiError('Use ldaps ou starttls; conexão sem TLS não é permitida.')
 if parameters['login_attribute'] not in ['userPrincipalName','sAMAccountName','uid','mail']:raise ApiError('Atributo de login LDAP inválido.')
 try:parse_dn(parameters['base_dn']);parse_dn(parameters['bind_dn'])
 except Exception:raise ApiError('Base ou DN de serviço inválido.') from None
 if secrets.get('ca_pem'):
  try:ssl.create_default_context(cadata=secrets['ca_pem'])
  except (ssl.SSLError,ValueError):raise ApiError('CA institucional PEM inválida.') from None

def connect(parameters,secrets,user=None,password=None):
 tls=Tls(validate=ssl.CERT_REQUIRED,version=ssl.PROTOCOL_TLS_CLIENT,ca_certs_data=secrets.get('ca_pem') or None)
 server=Server(parameters['host'],port=int(parameters['port']),use_ssl=parameters['tls_mode']=='ldaps',tls=tls,connect_timeout=8)
 connection=Connection(server,user=user or parameters['bind_dn'],password=secrets['bind_password'] if password is None else password,receive_timeout=10,auto_referrals=False,raise_exceptions=False)
 try:
  connection.open()
  if parameters['tls_mode']=='starttls' and not connection.start_tls():raise RemoteError('O servidor recusou StartTLS.')
  if not connection.bind():raise RemoteError('Autenticação recusada pelo diretório.')
  return connection
 except Exception:
  connection.unbind();raise RemoteError('Não foi possível autenticar no diretório com TLS validado.') from None

def directory_probe(parameters,secrets):
 connection=connect(parameters,secrets)
 try:
  if not connection.search(parameters['base_dn'],'(objectClass=*)',search_scope=BASE,attributes=['objectClass'],size_limit=1):raise RemoteError('Base de pesquisa não acessível pela conta de serviço.')
  return {'connected':True,'transport':parameters['tls_mode'],'base_accessible':True}
 finally:connection.unbind()

def authenticate_directory(user,password):
 from integrations import get_config,decrypt
 binding=get_db().execute('SELECT * FROM directory_bindings WHERE user_id=?',(user['id'],)).fetchone()
 if not binding:return None
 if not password:return False
 cfg=get_config(binding['entity_id'],'ldap','producao')
 if not cfg or not cfg['enabled']:return False
 parameters=json.loads(cfg['parameters']);secrets=decrypt(cfg);connection=None
 try:
  connection=connect(parameters,secrets)
  search=f"(&(objectClass=*)({parameters['login_attribute']}={escape_filter_chars(binding['login_name'])}))"
  connection.search(parameters['base_dn'],search,search_scope=SUBTREE,attributes=['objectClass'],size_limit=2)
  if connection.result.get('result')!=0 or len(connection.entries)!=1:return False
  dn=connection.entries[0].entry_dn;connection.unbind();connection=connect(parameters,secrets,dn,password)
  return bool(connection.bound)
 except (RemoteError,LDAPException,OSError):return False
 finally:
  if connection:connection.unbind()

def install_directory(app):
 with app.app_context():
  get_db().execute('CREATE TABLE IF NOT EXISTS directory_bindings(user_id INTEGER PRIMARY KEY REFERENCES users(id),entity_id INTEGER NOT NULL REFERENCES erp_entities(id),login_name TEXT NOT NULL COLLATE NOCASE,created_by INTEGER NOT NULL REFERENCES users(id),updated_at TEXT NOT NULL,UNIQUE(entity_id,login_name))');get_db().commit()
 @app.get('/api/integrations/ldap/bindings')
 def directory_bindings():
  from integrations import admin_access
  admin_access();require('users');entity=entity_access(request.args.get('entity','1'))
  return jsonify(items=[dict(r) for r in get_db().execute('SELECT b.*,u.name,u.email FROM directory_bindings b JOIN users u ON u.id=b.user_id WHERE b.entity_id=? ORDER BY u.name',(entity,))])
 @app.put('/api/integrations/ldap/bindings/<int:user_id>')
 def directory_binding(user_id):
  from integrations import admin_access,get_config
  admin_access('write');require('users','write');d=request.get_json();entity=entity_access(d.get('entity'));db=get_db();db.execute('BEGIN IMMEDIATE')
  user=db.execute('SELECT * FROM users WHERE id=?',(user_id,)).fetchone()
  if not user:raise ApiError('Usuário não encontrado.',404)
  if user_id==g.user['id']:raise ApiError('Solicite a outro administrador a alteração da sua autenticação.',409)
  login=d.get('login_name','')
  if not isinstance(login,str) or not 1<=len(login.strip())<=200 or any(ord(c)<32 for c in login):raise ApiError('Informe a identidade do usuário no diretório.')
  if not get_config(entity,'ldap','producao'):raise ApiError('Cadastre a conexão LDAP primeiro.',409)
  if user['group_id']==1 and not db.execute("SELECT 1 FROM users u WHERE u.group_id=1 AND u.active=1 AND u.id<>? AND u.schedule='{}' AND u.permissions='{}' AND NOT EXISTS(SELECT 1 FROM directory_bindings b WHERE b.user_id=u.id)",(user_id,)).fetchone():raise ApiError('Preserve um administrador local ativo para recuperação.',409)
  db.execute('INSERT INTO directory_bindings VALUES(?,?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET entity_id=excluded.entity_id,login_name=excluded.login_name,created_by=excluded.created_by,updated_at=excluded.updated_at',(user_id,entity,login.strip(),g.user['id'],now()))
  db.execute('UPDATE users SET force_password=0 WHERE id=?',(user_id,));db.execute('DELETE FROM sessions WHERE user_id=?',(user_id,));audit('Autenticação vinculada ao LDAP','users',user_id,{'entity':entity})
  return jsonify(message='Conta vinculada. Use o e-mail local e a senha do diretório. Não há fallback para a senha local.')
 @app.delete('/api/integrations/ldap/bindings/<int:user_id>')
 def remove_directory_binding(user_id):
  from integrations import admin_access
  admin_access('write');require('users','write');db=get_db();db.execute('BEGIN IMMEDIATE');row=db.execute('SELECT * FROM directory_bindings WHERE user_id=?',(user_id,)).fetchone()
  if not row:raise ApiError('Vínculo inexistente.',404)
  entity_access(row['entity_id'])
  if user_id==g.user['id']:raise ApiError('Outro administrador deve remover seu vínculo.',409)
  db.execute('DELETE FROM directory_bindings WHERE user_id=?',(user_id,));db.execute('UPDATE users SET force_password=1,password=? WHERE id=?',(generate_password_hash(secrets.token_urlsafe(48)),user_id));db.execute('DELETE FROM sessions WHERE user_id=?',(user_id,));audit('Vínculo LDAP removido','users',user_id)
  return jsonify(message='Vínculo removido. Redefina a senha local e entregue-a ao usuário pelo canal institucional.')

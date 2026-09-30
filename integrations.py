"""Central administrativa: configuração versionada e cofre de credenciais por entidade."""
import base64, json, re, time
from datetime import datetime, timezone
from pathlib import Path
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PublicFormat
from cryptography.hazmat.primitives import hashes
from flask import g, request, jsonify
from auth import ApiError, require
from db import get_db,key,audit
from domain import now
from erp_core import entity_access,integer,valid_document
from integration_catalog import PROVIDERS
from integration_transport import consult,RemoteError

def init_integrations():
 db=get_db();db.executescript((Path(__file__).parent/'integrations_schema.sql').read_text(encoding='utf-8'));db.commit()

def admin_access(action='read'):
 require('settings',action)
 if g.user['group_id']!=1:raise ApiError('A central de integrações é restrita à Administração.',403)

def context(provider,entity=None,environment=None):
 if provider not in PROVIDERS:raise ApiError('Integração não encontrada.',404)
 spec=PROVIDERS[provider];entity=entity_access(entity if entity is not None else request.args.get('entity','1'))
 environment=environment or request.args.get('environment','homologacao')
 if environment not in spec['environments']:raise ApiError('Ambiente não disponível para este serviço.')
 return spec,entity,environment

def get_config(entity,provider,environment):
 return get_db().execute('SELECT * FROM integration_configs WHERE entity_id=? AND provider=? AND environment=?',(entity,provider,environment)).fetchone()

def decrypt(row):return json.loads(key().decrypt(row['encrypted_secrets'].encode())) if row else {}

def public_config(row,spec):
 return {'version':row['version'] if row else 0,'enabled':bool(row['enabled']) if row else False,
  'parameters':json.loads(row['parameters']) if row else {},
  'secrets_set':{k:bool(decrypt(row).get(k)) for k,f in spec['fields'].items() if f['secret']},
  'certificate':json.loads(row['certificate_meta']) if row else {},'updated_at':row['updated_at'] if row else None}

def certificate_metadata(secrets):
 try:
  raw=base64.b64decode(secrets['pfx'],validate=True)
  if len(raw)>150000:raise ValueError()
  private,cert,chain=pkcs12.load_key_and_certificates(raw,secrets.get('pfx_password','').encode() or None)
  if not private or not cert:raise ValueError()
  if private.public_key().public_bytes(Encoding.DER,PublicFormat.SubjectPublicKeyInfo)!=cert.public_key().public_bytes(Encoding.DER,PublicFormat.SubjectPublicKeyInfo):raise ValueError()
 except Exception:raise ApiError('Certificado PFX/P12 ou senha inválidos; informe um certificado com chave privada (até 150 KB).') from None
 instant=datetime.now(timezone.utc)
 if not cert.not_valid_before_utc<=instant<cert.not_valid_after_utc:raise ApiError('Certificado expirado ou ainda não válido.')
 return {'subject':cert.subject.rfc4514_string(),'issuer':cert.issuer.rfc4514_string(),'expires_at':cert.not_valid_after_utc.isoformat(),
  'fingerprint_sha256':cert.fingerprint(hashes.SHA256()).hex(),'chain_validation':'Pendente: cadeia ICP-Brasil e revogação não verificadas'}

def install_integrations(app):
 with app.app_context():init_integrations()

 @app.get('/api/integrations')
 def list_integrations():
  admin_access();entity=entity_access(request.args.get('entity','1'));items=[]
  for provider,spec in PROVIDERS.items():
   configs={env:public_config(get_config(entity,provider,env),spec) for env in spec['environments']}
   items.append({'id':provider,**spec,'configs':configs})
  return jsonify(items=items)

 @app.put('/api/integrations/<provider>')
 def save_integration(provider):
  admin_access('write');data=request.get_json();spec,entity,environment=context(provider,data.get('entity'),data.get('environment'))
  if set(data)-{'entity','environment','version','enabled','parameters','secrets','clear_secrets'}:raise ApiError('Parâmetro de configuração desconhecido.')
  parameters=data.get('parameters',{});updates=data.get('secrets',{});clear=data.get('clear_secrets',[])
  if not isinstance(parameters,dict) or not isinstance(updates,dict) or not isinstance(clear,list) or any(not isinstance(x,str) for x in clear):raise ApiError('Configuração inválida.')
  enabled=data.get('enabled',False)
  if not isinstance(enabled,bool):raise ApiError('Informe se a integração está ativa.')
  if enabled and not spec['activatable']:raise ApiError('Este serviço ainda não dispõe de conector homologável. O cadastro não habilita transmissão.',409)
  db=get_db();db.execute('BEGIN IMMEDIATE');previous=get_config(entity,provider,environment)
  if integer(data.get('version',-1),'Versão')!=(previous['version'] if previous else 0):raise ApiError('Configuração alterada por outra pessoa. Reabra a tela.',409)
  fields=spec['fields'];public_fields={k for k,v in fields.items() if not v['secret']};secret_fields=set(fields)-public_fields
  if set(parameters)-public_fields or set(updates)-secret_fields or set(clear)-secret_fields:raise ApiError('Campo não previsto na configuração oficial.')
  secrets=decrypt(previous)
  for name in clear:secrets.pop(name,None)
  for name,value in updates.items():
   if not isinstance(value,str) or len(value)>(210000 if name=='pfx' else 100000 if name=='ca_pem' else 4096):raise ApiError('Credencial inválida ou excessivamente longa.')
   if value:secrets[name]=value
  clean={}
  for name,f in fields.items():
   value=secrets.get(name,'') if f['secret'] else parameters.get(name,'')
   if not isinstance(value,(str,int)) or isinstance(value,bool):raise ApiError(f['label']+': valor inválido.')
   if not f['secret']:
    value=str(value).strip()
    if len(value)>250 or any(ord(x)<32 for x in value):raise ApiError(f['label']+': valor inválido.')
    if value and f['type']=='cnpj':value=valid_document(value,'cnpj')
    if value and f['type']=='municipio' and not re.fullmatch(r'\d{7}',value):raise ApiError('Código IBGE deve conter sete dígitos.')
    if value and f['type']=='year':value=str(integer(value,'Exercício',2000,2100))
    clean[name]=value
   if enabled and f['required'] and not value:raise ApiError('Preencha '+f['label']+'.')
  if provider=='esocial':
   from integration_esocial import validate_settings
   validate_settings(clean,secrets,enabled)
  if provider=='ldap':
   from integration_directory import validate_settings
   validate_settings(clean,secrets,enabled)
  if provider=='signature' and clean.get('allowed_users'):
   if not re.fullmatch(r'[0-9]+(?:\s*,\s*[0-9]+)*',clean['allowed_users']):raise ApiError('Informe os IDs dos assinantes separados por vírgula.')
   for uid in clean['allowed_users'].split(','):
    if not db.execute('SELECT 1 FROM users WHERE id=? AND active=1',(int(uid),)).fetchone():raise ApiError('Usuário assinante não encontrado ou inativo.')
  meta={}
  if secrets.get('pfx'):meta=certificate_metadata(secrets)
  if provider=='ldap':db.execute('DELETE FROM sessions WHERE user_id IN (SELECT user_id FROM directory_bindings WHERE entity_id=?)',(entity,))
  version=(previous['version'] if previous else 0)+1
  db.execute('INSERT INTO integration_configs VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(entity_id,provider,environment) DO UPDATE SET enabled=excluded.enabled,parameters=excluded.parameters,encrypted_secrets=excluded.encrypted_secrets,certificate_meta=excluded.certificate_meta,version=excluded.version,updated_by=excluded.updated_by,updated_at=excluded.updated_at',
   (entity,provider,environment,int(enabled),json.dumps(clean),key().encrypt(json.dumps(secrets).encode()).decode(),json.dumps(meta),version,g.user['id'],now()))
  audit('Configuração de integração atualizada','settings',provider,{'entity':entity,'environment':environment,'version':version,'enabled':enabled,'rotated_fields':[k for k,v in updates.items() if v],'removed_fields':clear})
  return jsonify(message='Configuração salva. Credenciais protegidas.',config=public_config(get_config(entity,provider,environment),spec))

 @app.post('/api/integrations/<provider>/consult')
 def consult_integration(provider):
  admin_access('write');data=request.get_json();spec,entity,environment=context(provider,data.get('entity'),data.get('environment'))
  operation=data.get('operation','test')
  if operation not in spec['operations']:raise ApiError('Consulta não disponível para este serviço.',409)
  row=get_config(entity,provider,environment)
  if not row or not row['enabled']:raise ApiError('Salve e ative a configuração antes de consultar.',409)
  started=time.monotonic();result=None
  try:
   if provider=='ldap':
    from integration_directory import directory_probe
    result=directory_probe(json.loads(row['parameters']),decrypt(row))
   elif provider=='signature':
    from integration_signatures import signature_probe
    result=signature_probe(json.loads(row['parameters']),decrypt(row))
   else:result=consult(provider,spec['environments'][environment],json.loads(row['parameters']),decrypt(row),operation)
   success=True;message='Operação de verificação concluída.'
  except RemoteError as error:success=False;message=str(error)
  except ApiError as error:success=False;message=error.message
  db=get_db();db.execute('INSERT INTO integration_checks(entity_id,provider,environment,operation,success,message,duration_ms,actor_id,created_at) VALUES(?,?,?,?,?,?,?,?,?)',
   (entity,provider,environment,operation,int(success),message,round((time.monotonic()-started)*1000),g.user['id'],now()))
  audit('Consulta de integração','settings',provider,{'entity':entity,'environment':environment,'operation':operation,'success':success})
  # Falhas externas também precisam persistir no histórico, sem rollback do after_request.
  return jsonify(success=success,message=message,result=result)

 @app.get('/api/integrations/<provider>/history')
 def integration_history(provider):
  admin_access();_,entity,environment=context(provider)
  return jsonify(items=[dict(x) for x in get_db().execute('SELECT c.*,u.name AS actor FROM integration_checks c JOIN users u ON u.id=c.actor_id WHERE entity_id=? AND provider=? AND environment=? ORDER BY c.id DESC LIMIT 100',(entity,provider,environment))])

 from integration_publications import install_publications
 install_publications(app)
 from integration_siconfi import install_siconfi
 install_siconfi(app)
 from integration_directory import install_directory
 from integration_signatures import install_signatures
 install_directory(app);install_signatures(app)
 from integration_esocial import install_esocial
 install_esocial(app)
 from integration_certificate_alerts import install_certificate_alerts
 install_certificate_alerts(app)

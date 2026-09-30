"""Fila PNCP: pacote imutável, dupla custódia e envio explícito sem reenvio cego."""
import base64,hashlib,json
from datetime import datetime,timezone
from flask import g,request,jsonify,send_file
from io import BytesIO
from auth import ApiError,require
from db import get_db,key,audit
from domain import now
from erp_core import load,integer,entity_access
from integrations import admin_access,context,get_config,decrypt
from integration_catalog import PROVIDERS
from pncp_payloads import template,validate,canonical,fingerprint
from integration_transport import publish_pncp,RemoteError

def event(job,state,detail):
 get_db().execute('INSERT INTO integration_job_events(job_id,state,actor_id,detail,created_at) VALUES(?,?,?,?,?)',(job,state,g.user['id'],detail,now()))
 audit('Publicação PNCP: '+state,'procurement',job,{'detail':detail})

def job_load(id):
 row=get_db().execute('SELECT * FROM integration_jobs WHERE id=?',(id,)).fetchone()
 if not row:raise ApiError('Publicação não encontrada.',404)
 entity_access(row['entity_id']);require('procurement')
 return dict(row)

def snapshot_current(job):
 source=load(job['source_id'],'procurement')
 if source['version']!=job['source_version'] or fingerprint(source)!=job['source_fingerprint']:raise ApiError('Cadastro ou itens alterados. Cancele o pacote e prepare uma nova publicação.',409)
 row=get_config(job['entity_id'],'pncp',job['environment'])
 if not row or not row['enabled'] or row['version']!=job['config_version']:raise ApiError('Configuração alterada ou desativada. Prepare um novo pacote.',409)
 return row

def public_job(job):return {k:v for k,v in job.items() if k!='encrypted_document'}

def install_publications(app):
 @app.get('/api/integrations/pncp/template/<int:source_id>')
 def pncp_template(source_id):
  admin_access();require('procurement');source=load(source_id,'procurement')
  if source['kind'] not in ['contracts','processes']:raise ApiError('Selecione um contrato ou processo.')
  return jsonify(payload=template(source),source_name=source['name'],source_id=source_id,entity=source['entity_id'])

 @app.get('/api/integration-jobs')
 def jobs():
  admin_access();require('procurement');entity=entity_access(request.args.get('entity','1'));environment=request.args.get('environment','homologacao')
  return jsonify(items=[dict(r) for r in get_db().execute('SELECT j.id,j.source_id,j.operation,j.environment,j.state,j.version,j.created_at,j.updated_at,j.message,o.name AS source_name FROM integration_jobs j JOIN erp_objects o ON o.id=j.source_id WHERE j.entity_id=? AND j.environment=? ORDER BY j.id DESC LIMIT 100',(entity,environment))])

 @app.get('/api/integration-jobs/<int:id>')
 def job_detail(id):
  admin_access();job=job_load(id)
  return jsonify(item=public_job(job),events=[dict(r) for r in get_db().execute('SELECT e.*,u.name AS actor FROM integration_job_events e JOIN users u ON u.id=e.actor_id WHERE job_id=? ORDER BY e.id',(id,))])

 @app.get('/api/integration-jobs/<int:id>/document')
 def job_document(id):
  admin_access();job=job_load(id);audit('Documento da publicação consultado','procurement',id)
  return send_file(BytesIO(key().decrypt(job['encrypted_document'].encode())),mimetype='application/pdf',as_attachment=True,download_name=f'publicacao-{id}.pdf')

 @app.post('/api/integration-jobs')
 def create_job():
  admin_access('write');require('procurement','write');d=request.get_json();db=get_db();db.execute('BEGIN IMMEDIATE');spec,entity,environment=context('pncp',d.get('entity'),d.get('environment'))
  cfg=get_config(entity,'pncp',environment)
  if not cfg or not cfg['enabled']:raise ApiError('Configure e ative o PNCP neste ambiente.',409)
  source=load(d.get('source_id'),'procurement')
  if source['entity_id']!=entity or source['kind'] not in ['contracts','processes']:raise ApiError('Origem inválida para publicação.')
  if source['kind']=='contracts' and source['state']!='Vigente':raise ApiError('Ative o contrato antes de preparar sua publicação.',409)
  payload=d.get('payload');validate(source,payload)
  try:
   pdf=base64.b64decode(d.get('document',''),validate=True)
   if not pdf.startswith(b'%PDF-') or not 10<len(pdf)<=500000:raise ValueError()
   from pypdf import PdfReader
   reader=PdfReader(BytesIO(pdf),strict=False)
   if reader.is_encrypted or not len(reader.pages):raise ValueError()
  except Exception:raise ApiError('Anexe um PDF válido, sem senha, de até 500 KB.') from None
  title=d.get('document_title','')
  if not isinstance(title,str) or not 1<=len(title.strip())<=255 or any(ord(c)<32 or ord(c)>255 for c in title):raise ApiError('Título do documento inválido (até 255 caracteres latinos).')
  typ=integer(d.get('document_type'),'Tipo de documento PNCP',1);body=canonical(payload);fp=fingerprint(source)
  digest=hashlib.sha256((str(source['id'])+body+hashlib.sha256(pdf).hexdigest()+title+str(typ)).encode()).hexdigest()
  if db.execute("SELECT 1 FROM integration_jobs WHERE entity_id=? AND provider='pncp' AND environment=? AND source_id=? AND state NOT IN ('Cancelado','Rejeitado')",(entity,environment,source['id'])).fetchone():raise ApiError('Já existe um pacote pendente ou publicado para este cadastro e ambiente.',409)
  cursor=db.execute('INSERT INTO integration_jobs(entity_id,provider,environment,source_id,source_version,source_fingerprint,operation,payload,encrypted_document,document_title,document_type,digest,config_version,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
   (entity,'pncp',environment,source['id'],source['version'],fp,'contratos' if source['kind']=='contracts' else 'compras',body,key().encrypt(pdf).decode(),title,typ,digest,cfg['version'],g.user['id'],now(),now()))
  event(cursor.lastrowid,'Preparado','Pacote e documento fixados para revisão.')
  from erp_core import event as source_event
  source_event(source,'Publicação PNCP preparada',{'job_id':cursor.lastrowid,'environment':environment,'digest':digest})
  return jsonify(id=cursor.lastrowid,message='Pacote preparado; outro administrador deve revisar os dados e o PDF.'),201

 @app.post('/api/integration-jobs/<int:id>/<operation>')
 def job_operation(id,operation):
  admin_access('write');require('procurement','approve');d=request.get_json();db=get_db();db.execute('BEGIN IMMEDIATE');job=job_load(id)
  if integer(d.get('version'),'Versão',1)!=job['version']:raise ApiError('Pacote alterado. Atualize a tela.',409)
  receipt=None
  if operation=='approve':
   if job['state'] not in ['Preparado','Rejeitado']:raise ApiError('Pacote indisponível para aprovação.',409)
   if job['created_by']==g.user['id']:raise ApiError('Outro administrador deve revisar e aprovar.',403)
   snapshot_current(job);state='Aprovado';message='Dados e documento aprovados por outro administrador.'
   db.execute('UPDATE integration_jobs SET approved_by=? WHERE id=?',(g.user['id'],id))
  elif operation=='cancel':
   if job['state'] not in ['Preparado','Aprovado','Rejeitado']:raise ApiError('Pacote enviado ou em envio não pode ser cancelado localmente.',409)
   reason=d.get('reason','')
   if not isinstance(reason,str) or not 10<=len(reason.strip())<=1000:raise ApiError('Informe o motivo do cancelamento (10 a 1.000 caracteres).')
   state='Cancelado';message=reason.strip()
  elif operation=='send':
   if job['state']!='Aprovado':raise ApiError('Somente pacotes aprovados podem ser enviados.',409)
   if d.get('confirmation')!=('PUBLICAR EM PRODUCAO' if job['environment']=='producao' else 'ENVIAR PARA HOMOLOGACAO'):raise ApiError('Confirme explicitamente o ambiente de destino.')
   cfg=snapshot_current(job);parameters=json.loads(cfg['parameters']);secrets=decrypt(cfg)
   db.execute("UPDATE integration_jobs SET state='Enviando',version=version+1,updated_at=? WHERE id=?",(now(),id));event(id,'Enviando','Envio iniciado. Reenvio automático desabilitado.');db.commit()
   try:
    receipt=publish_pncp(PROVIDERS['pncp']['environments'][job['environment']],parameters,secrets,job,key().decrypt(job['encrypted_document'].encode()));state='Publicado';message='Recebimento confirmado pelo PNCP.'
   except RemoteError as error:state='Resultado incerto' if error.uncertain else 'Rejeitado';message=str(error)
   except Exception:state='Resultado incerto';message='Envio interrompido. Consulte o PNCP antes de qualquer nova inclusão.'
   db.execute('BEGIN IMMEDIATE')
  elif operation=='recover':
   if job['state']!='Enviando' or (datetime.now(timezone.utc)-datetime.fromisoformat(job['updated_at'])).total_seconds()<120:raise ApiError('Recuperação disponível para envios interrompidos há mais de dois minutos.',409)
   state='Resultado incerto';message='Envio interrompido. Concilie o recibo diretamente no PNCP; reenvio bloqueado.'
  else:raise ApiError('Operação não disponível.',404)
  db.execute('UPDATE integration_jobs SET state=?,message=?,receipt=?,version=version+1,updated_at=? WHERE id=?',(state,message,canonical(receipt) if receipt is not None else job['receipt'],now(),id));event(id,state,message)
  return jsonify(message=message,state=state)

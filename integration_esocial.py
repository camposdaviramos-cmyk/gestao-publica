"""Fila eSocial: preparação, revisão, envio explícito e retorno por evento."""
import hashlib,io,json,re
from pathlib import Path
from datetime import datetime,timedelta,timezone
from flask import g,request,jsonify,send_file
from cryptography.hazmat.primitives import hashes
from lxml import etree as ET
from auth import ApiError,require
from db import get_db,key,audit
from domain import now
from erp_core import entity_access,integer,valid_document
from integration_esocial_xml import prepare_event,batch,parse,query
from integration_esocial_transport import exchange
from integration_transport import RemoteError
from integration_signatures import load_material

def validate_settings(parameters,secrets,enabled):
 fields=['attorney_name','attorney_type','attorney_registration','attorney_valid_from','attorney_valid_until']
 if any(parameters.get(k) for k in fields):
  if not all(parameters.get(k) for k in fields):raise ApiError('Preencha nome, tipo, inscrição e validade completa da procuração.')
  if parameters['attorney_type'] not in ['1','2']:raise ApiError('Tipo de inscrição do outorgado inválido.')
  parameters['attorney_registration']=valid_document(parameters['attorney_registration'],'cnpj' if parameters['attorney_type']=='1' else 'cpf')
  try:
   start=datetime.strptime(parameters['attorney_valid_from'],'%Y-%m-%d');end=datetime.strptime(parameters['attorney_valid_until'],'%Y-%m-%d')
  except ValueError:raise ApiError('Datas da procuração inválidas.') from None
  if end<start:raise ApiError('Fim da procuração deve ser posterior ou igual ao início.')
 if not enabled:return
 cnpj=parameters['cnpj'];registration=parameters['employer_registration']
 if registration not in [cnpj,cnpj[:8]]:raise ApiError('Inscrição eSocial deve ser o CNPJ completo ou a raiz de oito posições do CNPJ cadastrado, conforme a natureza jurídica.')
 valid_document(parameters['transmitter'],'cpf_cnpj')
 from cryptography.hazmat.primitives.asymmetric import rsa
 _,private,_,_=load_material(secrets)
 if not isinstance(private,rsa.RSAPrivateKey) or private.key_size<2048:raise ApiError('Certificado eSocial deve possuir chave RSA de pelo menos 2048 bits.')

def access(action='read'):
 from integrations import admin_access
 admin_access('write' if action in ['write','approve'] else 'read');require('people',action)

def context(data):
 entity=entity_access(data.get('entity',1));environment=data.get('environment','homologacao')
 if environment not in ['homologacao','producao']:raise ApiError('Ambiente eSocial inválido.')
 return entity,environment

def history(id,action,details=None):
 get_db().execute('INSERT INTO esocial_history(batch_id,action,details,actor_id,created_at) VALUES(?,?,?,?,?)',(id,action,json.dumps(details or {},ensure_ascii=False),g.user['id'],now()))
 audit(action,'people',id,{'integration':'esocial'})

def load(id):
 row=get_db().execute('SELECT * FROM esocial_batches WHERE id=?',(id,)).fetchone()
 if not row:raise ApiError('Lote eSocial não encontrado.',404)
 entity_access(row['entity_id']);return row

def preserve_response(id,operation,result,raw):
 return get_db().execute('INSERT INTO esocial_responses(batch_id,operation,code,sha256,encrypted_xml,created_at) VALUES(?,?,?,?,?,?)',(id,operation,result['code'],hashlib.sha256(raw).hexdigest(),key().encrypt(raw),now())).lastrowid

def event_status(code,state):
 if code=='201':return 'Processado com sucesso'
 if code=='202':return 'Processado com advertência'
 if code and code.isdigit() and 400<=int(code)<500:return 'Rejeitado — corrigir XML'
 if code:return 'Erro de processamento — conferir retorno'
 return 'Aguardando processamento' if state in ['Recebido','Processando'] else state

def serialized(row):
 item={k:row[k] for k in row.keys() if k not in ['encrypted_xml','encrypted_response']}
 item['parameters']=json.loads(item['parameters']);item['response_summary']=json.loads(item['response_summary']);return item

def config(entity,environment):
 from integrations import get_config,decrypt
 cfg=get_config(entity,'esocial',environment)
 if not cfg or not cfg['enabled']:raise ApiError('Configure e ative o eSocial para a entidade e o ambiente selecionados.',409)
 return cfg,json.loads(cfg['parameters']),decrypt(cfg)

def transition(id,state,message,**extra):
 fields={'state':state,'last_message':message,'updated_at':now(),**extra}
 get_db().execute('UPDATE esocial_batches SET '+','.join(k+'=?' for k in fields)+',version=version+1 WHERE id=?',(*fields.values(),id))

def install_esocial(app):
 with app.app_context():get_db().executescript((Path(__file__).parent/'esocial_schema.sql').read_text(encoding='utf-8'));get_db().commit()

 @app.get('/api/esocial/batches')
 def list_batches():
  access();entity,environment=context(request.args)
  return jsonify(items=[serialized(r) for r in get_db().execute('SELECT * FROM esocial_batches WHERE entity_id=? AND environment=? ORDER BY id DESC LIMIT 100',(entity,environment))])

 @app.post('/api/esocial/batches')
 def create_batch():
  access('write');d=request.get_json();entity,environment=context(d);files=d.get('events')
  if not isinstance(files,list) or not 1<=len(files)<=50 or any(not isinstance(f,str) for f in files):raise ApiError('Envie de 1 a 50 arquivos XML de eventos sem assinatura.')
  if sum(len(f.encode('utf-8')) for f in files)>700000:raise ApiError('Este painel aceita até 700 KB de XML por lote. Divida os eventos em lotes menores.')
  db=get_db();db.execute('BEGIN IMMEDIATE');cfg,parameters,secrets=config(entity,environment)
  events=[prepare_event(f,parameters,secrets,environment) for f in files];groups={meta['group'] for _,meta in events};ids=[meta['event_id'] for _,meta in events]
  if len(groups)!=1:raise ApiError('O lote deve conter eventos do mesmo grupo: tabelas, não periódicos ou periódicos.')
  if len(set(ids))!=len(ids):raise ApiError('IDs de eventos repetidos no lote.')
  for eid in ids:
   existing=db.execute("SELECT 1 FROM esocial_events e JOIN esocial_batches b ON b.id=e.batch_id WHERE b.entity_id=? AND b.environment=? AND e.event_id=? AND b.state NOT IN ('Cancelado','Rejeitado') AND NOT (b.state='Processado com ocorrências' AND e.response_code BETWEEN '400' AND '499' AND COALESCE(e.receipt,'')='')",(entity,environment,eid)).fetchone()
   if existing:raise ApiError('Evento já está preparado, enviado ou com resultado incerto; reenvio bloqueado.',409)
  root=batch(events,parameters,next(iter(groups)));raw=ET.tostring(root,encoding='utf-8',xml_declaration=True)
  _,_,cert,_=load_material(secrets);stamp=now()
  id=db.execute('INSERT INTO esocial_batches(entity_id,environment,group_number,config_version,parameters,state,encrypted_xml,xml_hash,certificate_hash,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(entity,environment,next(iter(groups)),cfg['version'],json.dumps(parameters),'Preparado',key().encrypt(raw),hashlib.sha256(raw).hexdigest(),cert.fingerprint(hashes.SHA256()).hex(),g.user['id'],stamp,stamp)).lastrowid
  for _,meta in events:db.execute('INSERT INTO esocial_events(batch_id,event_id,event_type) VALUES(?,?,?)',(id,meta['event_id'],meta['event_type']))
  history(id,'Lote eSocial validado e assinado',{'events':len(events),'config_version':cfg['version']})
  return jsonify(id=id,message='XMLs validados e assinados. Revise o lote antes de transmitir.'),201

 @app.get('/api/esocial/batches/<int:id>')
 def batch_detail(id):
  access();row=load(id);db=get_db()
  return jsonify(item=serialized(row),responses=[dict(r) for r in db.execute('SELECT id,operation,code,sha256,created_at FROM esocial_responses WHERE batch_id=? ORDER BY id',(id,))],events=[{**dict(r),'status':event_status(r['response_code'],row['state'])} for r in db.execute('SELECT * FROM esocial_events WHERE batch_id=? ORDER BY id',(id,))],history=[dict(r) for r in db.execute('SELECT h.*,u.name actor FROM esocial_history h JOIN users u ON u.id=h.actor_id WHERE batch_id=? ORDER BY h.id DESC',(id,))])

 @app.get('/api/esocial/responses/<int:id>/download')
 def download_response(id):
  access();row=get_db().execute('SELECT * FROM esocial_responses WHERE id=?',(id,)).fetchone()
  if not row:raise ApiError('Retorno não encontrado.',404)
  load(row['batch_id']);audit('Retorno eSocial consultado','people',row['batch_id'],{'response':id})
  return send_file(io.BytesIO(key().decrypt(row['encrypted_xml'])),mimetype='application/xml',as_attachment=True,download_name=f'esocial-retorno-{id}.xml')

 @app.get('/api/esocial/batches/<int:id>/download/<kind>')
 def download_batch(id,kind):
  access();row=load(id)
  if kind not in ['xml','response']:raise ApiError('Documento não encontrado.',404)
  raw=row['encrypted_xml' if kind=='xml' else 'encrypted_response']
  if not raw:raise ApiError('Ainda não existe retorno do serviço.',404)
  audit('XML eSocial consultado','people',id,{'kind':kind})
  return send_file(io.BytesIO(key().decrypt(raw)),mimetype='application/xml',as_attachment=True,download_name=f'esocial-lote-{id}-{kind}.xml')

 @app.post('/api/esocial/batches/<int:id>/<operation>')
 def operate_batch(id,operation):
  if operation not in ['approve','cancel','send','query','recover']:raise ApiError('Operação eSocial inválida.',404)
  access('approve' if operation=='approve' else 'write');d=request.get_json();db=get_db();db.execute('BEGIN IMMEDIATE');row=load(id)
  if integer(d.get('version'),'Versão')!=row['version']:raise ApiError('Lote alterado; reabra os detalhes.',409)
  if operation=='approve':
   if row['state']!='Preparado':raise ApiError('Lote não está aguardando revisão.',409)
   if row['created_by']==g.user['id']:raise ApiError('Outro administrador deve revisar e aprovar este lote.',403)
   cfg,_,_=config(row['entity_id'],row['environment'])
   if cfg['version']!=row['config_version']:raise ApiError('Configuração alterada. Cancele e prepare novamente.',409)
   transition(id,'Aprovado','Lote revisado.',approved_by=g.user['id']);history(id,'Lote eSocial aprovado')
   return jsonify(message='Lote aprovado.')
  if operation=='cancel':
   if row['state'] not in ['Preparado','Aprovado','Falha de conexão']:raise ApiError('O lote já pode ter sido recebido. Cancelamento local bloqueado.',409)
   reason=d.get('reason','')
   if not isinstance(reason,str) or not 10<=len(reason.strip())<=1000:raise ApiError('Informe um motivo de 10 a 1.000 caracteres.')
   transition(id,'Cancelado','Lote cancelado antes da recepção.');history(id,'Lote eSocial cancelado',{'reason':reason.strip()});return jsonify(message='Lote cancelado. Os eventos podem ser preparados novamente.')
  if operation=='recover':
   if row['state']!='Enviando' or datetime.fromisoformat(row['updated_at'])>datetime.now(timezone.utc)-timedelta(minutes=2):raise ApiError('Somente um envio interrompido há mais de dois minutos pode ser recuperado.',409)
   transition(id,'Resultado incerto','Envio interrompido. Não reenviar sem localizar o resultado no eSocial.');history(id,'Interrupção eSocial registrada');return jsonify(message='Envio bloqueado para prevenir duplicidade.')
  cfg,parameters,secrets=config(row['entity_id'],row['environment'])
  if operation=='send':
   if row['state'] not in ['Aprovado','Falha de conexão']:raise ApiError('Lote não autorizado para envio.',409)
   if cfg['version']!=row['config_version']:raise ApiError('Configuração alterada. Cancele e prepare novamente.',409)
   if d.get('confirmation')!=('ENVIAR PARA PRODUCAO' if row['environment']=='producao' else 'ENVIAR PARA HOMOLOGACAO'):raise ApiError('Confirme expressamente o ambiente de transmissão.')
   if parameters.get('attorney_valid_until') and not parameters['attorney_valid_from']<=now()[:10]<=parameters['attorney_valid_until']:raise ApiError('Procuração cadastrada está fora do prazo de validade.',409)
   payload=parse(key().decrypt(row['encrypted_xml']));transition(id,'Enviando','Transmissão iniciada.');history(id,'Envio eSocial iniciado');db.commit()
   try:
    result,raw=exchange(row['environment'],'send',payload,secrets)
    if result.get('employer') and result['employer']!=parameters['employer_registration']:raise RemoteError('Retorno identifica outro empregador.',uncertain=True)
    if result.get('transmitter') and result['transmitter']!=parameters['transmitter']:raise RemoteError('Retorno identifica outro transmissor.',uncertain=True)
    if result['code'] in [201,202]:
     if not result.get('protocol'):raise RemoteError('Recepção sem protocolo; não reenviar.',uncertain=True)
     query(result['protocol']);state='Recebido'
    elif 400<=result['code']<=499:state='Rejeitado'
    else:raise RemoteError('Resposta de recepção sem resultado conclusivo; não reenviar.',uncertain=True)
    db.execute('BEGIN IMMEDIATE');transition(id,state,result['description'],protocol=result.get('protocol'),encrypted_response=key().encrypt(raw),response_summary=json.dumps(result),next_query_at=(datetime.now(timezone.utc)+timedelta(seconds=result['wait_seconds'])).isoformat(timespec='seconds'));history(id,'Retorno de recepção eSocial',{'code':result['code'],'state':state,'response_id':preserve_response(id,'send',result,raw)})
   except (RemoteError,ApiError) as error:
    db.execute('BEGIN IMMEDIATE');state='Resultado incerto' if isinstance(error,ApiError) or error.uncertain else 'Falha de conexão';transition(id,state,str(error));history(id,'Falha na transmissão eSocial',{'state':state})
   return jsonify(message=load(id)['last_message'],state=state)
  # Consultas são idempotentes; resultados incertos podem ser localizados por protocolo institucional.
  if row['state'] not in ['Recebido','Processando','Processado','Processado com ocorrências','Resultado incerto']:raise ApiError('Lote não disponível para consulta.',409)
  protocol=row['protocol'] or d.get('protocol','');payload=query(protocol)
  if row['next_query_at'] and row['next_query_at']>now():raise ApiError('Aguarde o prazo indicado pelo eSocial antes de consultar novamente.',429)
  original=json.loads(row['parameters'])
  if parameters['transmitter']!=original['transmitter'] or parameters['employer_registration']!=original['employer_registration']:raise ApiError('A consulta exige o transmissor e empregador originais.',409)
  # Reserva o intervalo de consulta antes da rede, sem manter bloqueio de escrita.
  next_time=(datetime.now(timezone.utc)+timedelta(seconds=30)).isoformat(timespec='seconds');db.execute('UPDATE esocial_batches SET next_query_at=? WHERE id=?',(next_time,id));db.commit()
  try:
   result,raw=exchange(row['environment'],'query',payload,secrets)
   if result.get('protocol') and result['protocol']!=protocol:raise RemoteError('Retorno com protocolo divergente.')
   if result.get('employer') and result['employer']!=original['employer_registration']:raise RemoteError('Retorno identifica outro empregador.')
   expected={r['event_id'] for r in db.execute('SELECT event_id FROM esocial_events WHERE batch_id=?',(id,))};returned=[r['event_id'] for r in result['events']]
   if len(set(returned))!=len(returned) or set(returned)-expected:raise RemoteError('Retorno contém eventos de outro lote ou eventos repetidos.')
   if result['code'] in [201,202] and set(returned)!=expected:raise RemoteError('Retorno concluído sem todos os eventos do lote; resultado preservado para conferência.')
   if result['code']==101:state='Processando'
   elif result['code'] in [201,202]:state='Processado' if all(e['code'] in ['201','202'] and e['receipt'] for e in result['events']) else 'Processado com ocorrências'
   else:raise RemoteError('Consulta não concluída: código '+str(result['code'])+'. Confira o retorno no portal eSocial.')
   db.execute('BEGIN IMMEDIATE');transition(id,state,result['description'],protocol=protocol,encrypted_response=key().encrypt(raw),response_summary=json.dumps(result),next_query_at=(datetime.now(timezone.utc)+timedelta(seconds=result['wait_seconds'])).isoformat(timespec='seconds'))
   for e in result['events']:db.execute('UPDATE esocial_events SET response_code=?,receipt=?,description=? WHERE batch_id=? AND event_id=?',(e['code'],e['receipt'],e['description'],id,e['event_id']))
   history(id,'Processamento eSocial consultado',{'code':result['code'],'state':state,'response_id':preserve_response(id,'query',result,raw)})
  except RemoteError as error:
   history(id,'Consulta eSocial não concluída',{'message':str(error)});return jsonify(success=False,message=str(error))
  return jsonify(success=True,state=state,message=result['description'])

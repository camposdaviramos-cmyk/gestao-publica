import base64,csv,hashlib,io,json,re
from pathlib import Path
from decimal import Decimal
from flask import g,request,jsonify,send_file
from auth import ApiError,require
from db import get_db,audit,key,settings
from domain import now
from erp_catalog import CATALOG,OP_LABELS,ERP_SCOPES
from erp_core import (entity_access,integer,spec,load,serialize,validate,create_object,event,confidential_sql,valid_document,balance)
from erp_rules import validate_business
from erp_operations import run_operation,OPERATIONS
from erp_payroll import approve_rules,calculate_payroll,approve_payroll
from erp_social_operations import attend_appointment,cancel_appointment
OPERATIONS.update(attend_appointment=attend_appointment,cancel_appointment=cancel_appointment)
OP_LABELS.update(attend_appointment='Registrar atendimento',cancel_appointment='Cancelar agendamento')
OPERATIONS.update(approve_rules=approve_rules,calculate_payroll=calculate_payroll,approve_payroll=approve_payroll)

def context_args(body=None):
 source=body or request.args
 return entity_access(source.get('entity')),integer(source.get('exercise'),'Exercício',2000,2100)

def query_objects(module,kind,entity,exercise):
 spec(module,kind);require(module)
 where='entity_id=? AND exercise=? AND module=? AND kind=? AND deleted=0'+confidential_sql();params=[entity,exercise,module,kind]
 q=request.args.get('q','').strip()[:120]
 if q:where+=' AND (name LIKE ? OR code LIKE ?)';params+=['%'+q+'%']*2
 if request.args.get('state'):where+=' AND state=?';params.append(request.args['state'])
 return where,params

from inventory_operations import OPERATIONS as INVENTORY_OPERATIONS
from inventory_core import approve_stock_accounting,retire_stock_accounting,seal_stock_commission
OPERATIONS.update(INVENTORY_OPERATIONS)
OPERATIONS.update(approve_stock_accounting=approve_stock_accounting,retire_stock_accounting=retire_stock_accounting,seal_stock_commission=seal_stock_commission)
from asset_accounting_operations import OPERATIONS as ASSET_ACCOUNTING_OPERATIONS
from asset_management_operations import OPERATIONS as ASSET_MANAGEMENT_OPERATIONS
OPERATIONS.update(ASSET_ACCOUNTING_OPERATIONS)
OPERATIONS.update(ASSET_MANAGEMENT_OPERATIONS)
from fleet_operations import OPERATIONS as FLEET_OPERATIONS
OPERATIONS.update(FLEET_OPERATIONS)
from works_operations import linear_adjustment
OPERATIONS.update(linear_adjustment=linear_adjustment, activate_version=lambda o, a: {'status': 'Ativado'})

def install_erp(app):
 @app.get('/api/erp/catalog')
 def catalog():return jsonify(modules=CATALOG,operations=OP_LABELS)

 @app.get('/api/erp/entities')
 def entities():
  db=get_db()
  rows=db.execute('SELECT * FROM erp_entities WHERE active=1 ORDER BY name').fetchall() if g.user['group_id']==1 else db.execute('SELECT e.* FROM erp_entities e JOIN erp_entity_access a ON a.entity_id=e.id WHERE a.user_id=? AND e.active=1 ORDER BY name',(g.user['id'],)).fetchall()
  return jsonify(items=[dict(r) for r in rows])

 @app.post('/api/erp/entities')
 def add_entity():
  require('entities','write');d=request.get_json();code=str(d.get('code','')).strip();name=str(d.get('name','')).strip()
  if not 2<=len(code)<=30 or not 3<=len(name)<=180:raise ApiError('Informe código e nome válidos para a entidade.')
  cnpj=valid_document(d['cnpj'],'cnpj') if d.get('cnpj') else ''
  if cnpj and get_db().execute('SELECT 1 FROM erp_entities WHERE cnpj=?',(cnpj,)).fetchone():raise ApiError('CNPJ já cadastrado.',409)
  rid=get_db().execute('INSERT INTO erp_entities(code,name,cnpj) VALUES(?,?,?)',(code,name,cnpj)).lastrowid;audit('Entidade criada','entities',rid);return jsonify(id=rid,message='Entidade cadastrada.'),201

 @app.get('/api/erp/access/<int:user_id>')
 def get_access(user_id):
  require('users');return jsonify(entities=[r[0] for r in get_db().execute('SELECT entity_id FROM erp_entity_access WHERE user_id=?',(user_id,))])

 @app.put('/api/erp/access/<int:user_id>')
 def set_access(user_id):
  require('users','write');require('entities','write');d=request.get_json();values=d.get('entities',[])
  if not isinstance(values,list) or len(values)>1000:raise ApiError('Entidades inválidas.')
  if not get_db().execute('SELECT 1 FROM users WHERE id=?',(user_id,)).fetchone():raise ApiError('Usuário não encontrado.',404)
  ids={entity_access(v) for v in values};db=get_db();db.execute('DELETE FROM erp_entity_access WHERE user_id=?',(user_id,))
  db.executemany('INSERT INTO erp_entity_access VALUES(?,?)',[(user_id,x) for x in ids]);db.execute('DELETE FROM sessions WHERE user_id=?',(user_id,));audit('Acesso por entidade atualizado','users',user_id,{'entities':list(ids)});return jsonify(message='Acesso atualizado. As sessões do usuário foram encerradas.')

 @app.get('/api/erp/<module>/<kind>')
 def listing(module,kind):
  entity,exercise=context_args();where,params=query_objects(module,kind,entity,exercise);page=integer(request.args.get('page',1),'Página',1,100000);limit=integer(request.args.get('limit',20),'Limite',1,100)
  total=get_db().execute('SELECT count(*) FROM erp_objects WHERE '+where,params).fetchone()[0]
  rows=get_db().execute('SELECT * FROM erp_objects WHERE '+where+' ORDER BY id DESC LIMIT ? OFFSET ?',(*params,limit,(page-1)*limit)).fetchall()
  items=[]
  for row in rows:
   obj=dict(row);obj['data']=json.loads(obj['data']);items.append(serialize(obj))
  audit('Consulta integrada',module,detail={'kind':kind,'entity':entity,'exercise':exercise});return jsonify(items=items,total=total,page=page,limit=limit)

 @app.post('/api/erp/<module>/<kind>')
 def create(module,kind):
  spec(module,kind);require(module,'write');get_db().execute('BEGIN IMMEDIATE');body=request.get_json();entity,exercise=context_args(body)
  if module=='inventory' and kind=='movements' and any(body.get('data',{}).get(k) for k in ['requisition_item','invoice_item']):raise ApiError('Movimentos vinculados devem ser gerados pela entrega, devolução ou nota fiscal.')
  obj=create_object(module,kind,entity,exercise,body.get('data',{}));return jsonify(item=serialize(obj),message='Cadastro salvo.'),201

 @app.get('/api/erp/object/<int:object_id>')
 def detail(object_id):
  obj=load(object_id);events=[dict(r) for r in get_db().execute('SELECT e.*,u.name actor_name FROM erp_events e JOIN users u ON u.id=e.actor WHERE object_id=? ORDER BY id DESC LIMIT 100',(object_id,))]
  for e in events:e['payload']=json.loads(e['payload'])
  attachments=[dict(r) for r in get_db().execute('SELECT id,name,size,created_at FROM erp_attachments WHERE object_id=?',(object_id,))]
  result={'item':serialize(obj),'events':events,'attachments':attachments}
  if obj['module']=='inventory':
   from inventory_api import detail as inventory_detail
   result['inventory']=inventory_detail(obj)
  if obj['module']=='assets':
   from asset_api import detail as asset_detail
   result['assets']=asset_detail(obj)
  if obj['module']=='fleet':
   from fleet_api import detail as fleet_detail
   result['fleet']=fleet_detail(obj)
  result['signatures']=[dict(r) for r in get_db().execute('SELECT s.id,s.name,s.metadata,s.created_at FROM document_signatures s JOIN erp_attachments a ON a.id=s.attachment_id WHERE a.object_id=? ORDER BY s.id DESC',(object_id,))]
  if obj['module']=='control' and obj['kind']=='occurrences':
   remote=get_db().execute('SELECT r.data,r.updated_at FROM siconfi_reports r JOIN siconfi_links l ON l.report_id=r.id WHERE l.occurrence_id=?',(object_id,)).fetchone()
   if remote:result['siconfi']={'data':json.loads(remote['data']),'updated_at':remote['updated_at']}
  if obj['module']=='procurement' and obj['kind'] in ['processes','contracts']:
   result['pncp']=[dict(r) for r in get_db().execute('SELECT id,state,environment,receipt,updated_at FROM integration_jobs WHERE source_id=? ORDER BY id DESC',(object_id,))]
  if obj['module']=='people' and obj['kind']=='runs':
   result['payroll']=[dict(r) for r in get_db().execute('SELECT l.*,o.name employee_name,o.code registration FROM erp_payroll_lines l JOIN erp_objects o ON o.id=l.employee_id WHERE run_id=?',(object_id,))]
  audit('Detalhes do registro',obj['module'],object_id);return jsonify(result)

 @app.put('/api/erp/object/<int:object_id>')
 def update(object_id):
  db=get_db();db.execute('BEGIN IMMEDIATE');o=load(object_id);require(o['module'],'write');b=request.get_json()
  if integer(b.get('version'),'Versão',1)!=o['version']:raise ApiError('Registro alterado por outra operação. Recarregue.',409)
  if o['state'] not in ['Rascunho','Reaberto']:raise ApiError('Registro efetivado: use a rotina específica para preservar os saldos.',409)
  if o['module']=='people' and o['kind']=='tax_bands' and load(o['data']['rules'])['state']=='Aprovado':raise ApiError('Parâmetros aprovados não podem ser alterados.',409)
  if o['module']=='social' and o['kind']=='visits' and o['data'].get('confidential'):
   require('social_confidential','write')
   if not b.get('data',{}).get('confidential'):raise ApiError('O histórico de um atendimento sigiloso não pode ser desclassificado nesta rotina.',409)
  if o['module']=='inventory' and o['kind']=='movements' and any(b.get('data',{}).get(k) for k in ['requisition_item','invoice_item']):raise ApiError('Vínculos de requisição e nota fiscal são mantidos pelo fluxo de recebimento.')
  data,links=validate(o['module'],o['kind'],b.get('data',{}),o['entity_id'],o['exercise']);before=o['data'];o['data']=data;validate_business(o)
  db.execute('UPDATE erp_objects SET code=?,name=?,data=?,version=version+1,updated_at=? WHERE id=?',(data['code'],data['name'],json.dumps(data,ensure_ascii=False),now(),object_id));db.execute('DELETE FROM erp_links WHERE source_id=?',(object_id,))
  db.executemany('INSERT INTO erp_links VALUES(?,?,?)',[(object_id,k,v) for k,v in links.items()]);event(o,'Cadastro alterado',{'before':before,'after':data});return jsonify(item=serialize(load(object_id)),message='Cadastro atualizado.')

 @app.delete('/api/erp/object/<int:object_id>')
 def delete(object_id):
  db=get_db();db.execute('BEGIN IMMEDIATE');o=load(object_id);require(o['module'],'delete')
  if integer(request.args.get('version'),'Versão',1)!=o['version']:raise ApiError('Registro alterado. Recarregue.',409)
  if (o['module']=='people' and o['kind']=='events') or (o['module']=='inventory' and o['kind'] in ['requisition_items','authorization_items','invoice_items','commission_members']) or (o['module']=='assets' and o['kind'] in ['commission_members','inventory_items','complement_commitments']):validate_business(o)
  if o['module']=='social' and o['kind']=='visits' and o['data'].get('confidential'):require('social_confidential','delete')
  if o['state']!='Rascunho' or db.execute("SELECT 1 FROM erp_events WHERE object_id=? AND operation NOT IN ('Cadastro criado','Cadastro alterado')",(object_id,)).fetchone():raise ApiError('Registro com operação efetivada não pode ser excluído.',409)
  if db.execute('SELECT 1 FROM erp_links l JOIN erp_objects o ON o.id=l.source_id WHERE l.target_id=? AND o.deleted=0',(object_id,)).fetchone():raise ApiError('Registro possui vínculos ativos; exclusão bloqueada.',409)
  if db.execute('SELECT 1 FROM erp_stock WHERE (warehouse_id=? OR material_id=?) AND quantity>0',(object_id,object_id)).fetchone():raise ApiError('Registro possui saldo de estoque.',409)
  if o['module']=='people' and o['kind']=='tax_bands' and load(o['data']['rules'])['state']=='Aprovado':raise ApiError('Faixa vinculada a parâmetros aprovados.')
  db.execute('UPDATE erp_objects SET deleted=1,version=version+1,updated_at=? WHERE id=?',(now(),object_id));event(o,'Cadastro excluído');return jsonify(message='Registro excluído; histórico preservado.')

 @app.post('/api/erp/object/<int:object_id>/operate')
 def operate(object_id):
  get_db().execute('BEGIN IMMEDIATE');o=load(object_id);b=request.get_json()
  if integer(b.get('version'),'Versão',1)!=o['version']:raise ApiError('Registro atualizado; recarregue antes de operar.',409)
  args=b.get('args',{})
  if not isinstance(args,dict):raise ApiError('Parâmetros inválidos.')
  result=run_operation(o,str(b.get('operation','')),args);return jsonify(item=serialize(load(object_id)),result=result,message='Operação concluída.')

 @app.post('/api/erp/object/<int:object_id>/attachments')
 def add_attachment(object_id):
  o=load(object_id);require(o['module'],'write')
  if o['module']=='social' and o['kind']=='visits' and o['data'].get('confidential'):require('social_confidential','write')
  d=request.get_json();name=Path(str(d.get('name',''))).name;allowed={'.pdf':b'%PDF','.png':b'\x89PNG','.jpg':b'\xff\xd8','.jpeg':b'\xff\xd8','.docx':b'PK','.xlsx':b'PK','.pptx':b'PK','.doc':b'\xd0\xcf','.xls':b'\xd0\xcf','.ppt':b'\xd0\xcf'}
  suffix=Path(name).suffix.lower()
  if suffix not in allowed or not 1<=len(name)<=200:raise ApiError('Use PDF, imagem JPG/PNG ou documento Office.')
  try:content=base64.b64decode(d.get('content',''),validate=True)
  except Exception:raise ApiError('Arquivo inválido.')
  if not 0<len(content)<=512000 or not content.startswith(allowed[suffix]):raise ApiError('Arquivo inválido ou maior que 500 KB.')
  digest=hashlib.sha256(content).hexdigest();db=get_db()
  if db.execute('SELECT 1 FROM erp_attachments WHERE object_id=? AND sha256=?',(object_id,digest)).fetchone():raise ApiError('Este arquivo já está anexado.',409)
  rid=db.execute('INSERT INTO erp_attachments(object_id,name,mime,size,sha256,encrypted,created_by,created_at) VALUES(?,?,?,?,?,?,?,?)',(object_id,name,'application/octet-stream',len(content),digest,key().encrypt(content),g.user['id'],now())).lastrowid;event(o,'Anexo incluído',{'name':name,'sha256':digest});return jsonify(id=rid,message='Anexo protegido e salvo.'),201

 @app.get('/api/erp/attachment/<int:attachment_id>')
 def attachment(attachment_id):
  row=get_db().execute('SELECT * FROM erp_attachments WHERE id=?',(attachment_id,)).fetchone()
  if not row:raise ApiError('Anexo não encontrado.',404)
  o=load(row['object_id']);event(o,'Anexo consultado',{'attachment':attachment_id});return send_file(io.BytesIO(key().decrypt(row['encrypted'])),as_attachment=True,download_name=row['name'],mimetype='application/octet-stream')

 @app.get('/api/erp/ledger')
 def ledger():
  require('finance');entity,exercise=context_args();rows=get_db().execute('SELECT o.code,o.name,sum(l.debit) debit,sum(l.credit) credit FROM erp_ledger l JOIN erp_objects o ON o.id=l.account_id WHERE l.entity_id=? AND l.exercise=? GROUP BY o.id ORDER BY o.code',(entity,exercise)).fetchall();return jsonify(items=[{**dict(r),'balance':r['debit']-r['credit']} for r in rows],debit=sum(r['debit'] for r in rows),credit=sum(r['credit'] for r in rows))

 @app.get('/api/erp/stock')
 def stock():
  require('inventory');entity,exercise=context_args();rows=get_db().execute("SELECT s.*,w.name warehouse,m.name material,m.code,json_extract(m.data,'$.minimum') minimum FROM erp_stock s JOIN erp_objects w ON w.id=s.warehouse_id JOIN erp_objects m ON m.id=s.material_id WHERE w.entity_id=? AND w.exercise=? AND w.deleted=0 AND m.deleted=0 ORDER BY w.name,m.name",(entity,exercise)).fetchall();return jsonify(items=[{**dict(r),'suggested':max(0,(r['minimum'] or 0)-r['quantity'])} for r in rows])

 @app.get('/api/erp/insights')
 def insights():
  require('bi');entity,exercise=context_args();modules=[m for m in CATALOG if 'read' in g.permissions.get(m,[])]
  marks=','.join('?' for _ in modules) or 'NULL';rows=get_db().execute('SELECT module,kind,state,count(*) count FROM erp_objects WHERE entity_id=? AND exercise=? AND deleted=0 AND module IN ('+marks+')'+confidential_sql()+' GROUP BY module,kind,state',(entity,exercise,*modules)).fetchall()
  from erp_insights import indicators
  return jsonify(items=[dict(r) for r in rows],total=sum(r['count'] for r in rows),indicators=indicators(entity,exercise))

 @app.get('/api/erp/<module>/<kind>/export')
 def export(module,kind):
  entity,exercise=context_args();where,params=query_objects(module,kind,entity,exercise);count=get_db().execute('SELECT count(*) FROM erp_objects WHERE '+where,params).fetchone()[0]
  if count>10000:raise ApiError('Refine a consulta: limite de 10.000 registros.')
  rows=get_db().execute('SELECT * FROM erp_objects WHERE '+where+' ORDER BY id',params).fetchall();resource=spec(module,kind);headers=['ID','Situação']+[x['label'] for x in resource['fields'].values()];values=[]
  for row in rows:
   obj=dict(row);obj['data']=json.loads(obj['data']);obj=serialize(obj);values.append([obj['id'],obj['state']]+[obj['data'].get(f,'') for f in resource['fields']])
  fmt=request.args.get('format','csv');cfg=settings()
  from integration_signatures import authorize_report,report_response
  authorize_report(module,entity,fmt,kind)
  if fmt=='json':return jsonify(headers=headers,rows=values)
  if fmt=='pdf':
   from reportlab.lib.pagesizes import A4,landscape
   from reportlab.lib.styles import getSampleStyleSheet
   from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
   from html import escape
   stream=io.BytesIO();styles=getSampleStyleSheet();story=[Paragraph(escape(resource['label']),styles['Title']),Paragraph(f'Entidade {entity} · Exercício {exercise}',styles['Normal']),Spacer(1,12)]
   for row in values:
    story.extend([Paragraph(escape(' | '.join(f'{h}: {v}' for h,v in zip(headers,row) if v not in [None,''])),styles['Normal']),Spacer(1,12)])
   SimpleDocTemplate(stream,pagesize=landscape(A4)).build(story);stream.seek(0);audit('Relatório integrado PDF',module,detail={'kind':kind,'rows':len(rows)});return report_response(stream,'application/pdf',f'{module}-{kind}.pdf',module,entity,kind)
  if fmt!='csv':raise ApiError('Formato inválido.')
  out=io.StringIO();writer=csv.writer(out,delimiter=';');writer.writerow(headers)
  for row in values:writer.writerow(["'"+str(v) if str(v).lstrip().startswith(('=','+','-','@')) else str(v) if v is not None else '' for v in row])
  audit('Relatório integrado CSV',module,detail={'kind':kind,'rows':len(rows)});return report_response(io.BytesIO(out.getvalue().encode('utf-8-sig')),'text/csv',f'{module}-{kind}.csv',module,entity,kind)

 @app.get('/api/erp/annex')
 def annex():
  require('compliance');p=Path(__file__).parent/'docs/anexo-iii-conformidade.json';return jsonify(json.loads(p.read_text(encoding='utf-8')))

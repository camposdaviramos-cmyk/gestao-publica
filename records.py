import json
from datetime import datetime, timezone
from flask import g, request, jsonify
from auth import ApiError, require
from db import get_db, audit, notify, settings
from domain import MODULES, SLA, now, validate_record, business_deadline

def serialized(row):
 item=dict(row); item['data']=json.loads(item['data']); item['amount']=item['amount']/100
 return item

def module_check(module):
 if module not in MODULES: raise ApiError('Módulo não encontrado.',404)

def apply_change(module,operation,record_id,payload,actor_id):
 db=get_db(); original=None
 if operation!='create':
  original=db.execute('SELECT * FROM records WHERE id=? AND module=?',(record_id,module)).fetchone()
  if not original: raise ApiError('Registro não encontrado.',404)
  if payload.get('version')!=original['version']: raise ApiError('Este registro foi alterado. Atualize os dados antes de continuar.',409)
 if operation=='delete':
  if module=='budget':
   if db.execute("SELECT 1 FROM records WHERE module='accounting' AND json_extract(data,'$.budget_id')=?",(str(record_id),)).fetchone(): raise ApiError('Esta ação está vinculada a um registro contábil.',409)
  db.execute('DELETE FROM ticket_comments WHERE record_id=?',(record_id,))
  db.execute('DELETE FROM records WHERE id=?',(record_id,))
 else:
  data=payload['data'].copy()
  if module=='accounting' and data.get('budget_id'):
   if not db.execute("SELECT 1 FROM records WHERE id=? AND module='budget'",(data['budget_id'],)).fetchone(): raise ApiError('A ação orçamentária vinculada não existe.')
  if module=='tickets':
   previous=json.loads(original['data']) if original else {}
   if original and data['priority']!=previous['priority']: raise ApiError('A prioridade do chamado é mantida para preservar o SLA original.')
   data.update({k:v for k,v in previous.items() if k in ['response_due','resolution_due','responded_at','resolved_at']})
   if not original:
    response,solution,rb,sb=SLA[data['priority']]; start=datetime.now(timezone.utc)
    data.update(response_due=business_deadline(start,response,rb,settings()['holidays']),resolution_due=business_deadline(start,solution,sb,settings()['holidays']))
   if payload['status']!='Aberto' and not data.get('responded_at'): data['responded_at']=now()
   if payload['status']=='Resolvido': data.setdefault('resolved_at',now())
   else: data.pop('resolved_at',None)
  args=(payload['title'],payload['department'],payload['status'],payload['amount'],json.dumps(data,ensure_ascii=False))
  if original:
   db.execute('UPDATE records SET title=?,department=?,status=?,amount=?,data=?,updated_at=?,version=version+1 WHERE id=?',(*args,now(),record_id))
  else:
   record_id=db.execute('INSERT INTO records(title,department,status,amount,data,updated_at,module,created_by,created_at) VALUES(?,?,?,?,?,?,?,?,?)',(*args,now(),module,actor_id,now())).lastrowid
  if module=='tickets' and original:
   notify(original['created_by'],'Chamado atualizado',f"#{record_id} · {payload['title']} — {payload['status']}")
 audit({'create':'Inclusão','update':'Alteração','delete':'Exclusão'}[operation],module,record_id,{'requester':actor_id,'title':original['title'] if operation=='delete' else payload['title']})
 return record_id

def install_records(app):
 @app.get('/api/records/<module>')
 def records(module):
  module_check(module); require(module)
  try: page=max(1,int(request.args.get('page',1))); limit=min(100,max(1,int(request.args.get('limit',20))))
  except ValueError: raise ApiError('Paginação inválida.')
  where='module=?'; args=[module]
  if request.args.get('q'):
   where+=' AND (title LIKE ? OR department LIKE ? OR data LIKE ?)'; args.extend(['%'+request.args['q'][:150]+'%']*3)
  if request.args.get('status'): where+=' AND status=?'; args.append(request.args['status'])
  db=get_db(); count=db.execute('SELECT count(*) FROM records WHERE '+where,args).fetchone()[0]
  rows=db.execute('SELECT * FROM records WHERE '+where+' ORDER BY updated_at DESC,id DESC LIMIT ? OFFSET ?',(*args,limit,(page-1)*limit)).fetchall()
  audit('Consulta',module,detail={'page':page,'results':len(rows)})
  return jsonify(items=[serialized(r) for r in rows],total=count,page=page,limit=limit)

 @app.route('/api/records/<module>',methods=['POST'])
 @app.route('/api/records/<module>/<int:record_id>',methods=['PUT','DELETE'])
 def mutate(module,record_id=None):
  module_check(module); operation='create' if request.method=='POST' else 'delete' if request.method=='DELETE' else 'update'; require(module,'delete' if operation=='delete' else 'write')
  db=get_db(); db.execute('BEGIN IMMEDIATE')
  try:
   payload={} if operation=='delete' else validate_record(module,request.get_json())
   if operation!='create': payload['version']=int(request.args.get('version',0)) if operation=='delete' else int(request.get_json().get('version',0))
  except (ValueError,TypeError) as e: raise ApiError(str(e))
  if record_id:
   original=db.execute('SELECT * FROM records WHERE id=? AND module=?',(record_id,module)).fetchone()
   if not original: raise ApiError('Registro não encontrado.',404)
   if original['version']!=payload['version']: raise ApiError('Registro atualizado por outro usuário. Recarregue a página.',409)
   if operation=='delete':
    payload.update(title=original['title'],department=original['department'],amount=original['amount'],status=original['status'],data=json.loads(original['data']))
  if module in settings()['dual_modules']:
   pending=db.execute('INSERT INTO approvals(module,operation,record_id,payload,requester,created_at) VALUES(?,?,?,?,?,?)',(module,operation,record_id,json.dumps(payload,ensure_ascii=False),g.user['id'],now())).lastrowid
   audit('Solicitação de dupla custódia',module,pending,{'operation':operation,'record_id':record_id})
   return jsonify(pending=True,id=pending,message='Enviado para aprovação de outro usuário autorizado.'),202
  result=apply_change(module,operation,record_id,payload,g.user['id'])
  return jsonify(id=result,message='Registro excluído.' if operation=='delete' else 'Registro salvo.'),201 if operation=='create' else 200

 @app.get('/api/approvals')
 def approvals():
  rows=get_db().execute('SELECT a.*,u.name requester_name,v.name reviewer_name FROM approvals a JOIN users u ON u.id=a.requester LEFT JOIN users v ON v.id=a.reviewer ORDER BY a.id DESC LIMIT 300').fetchall()
  result=[]
  for r in rows:
   if r['requester']==g.user['id'] or 'approve' in g.permissions.get(r['module'],[]):
    d=dict(r); d['payload']=json.loads(d['payload']); result.append(d)
  audit('Consulta','approvals'); return jsonify(items=result)

 @app.post('/api/approvals/<int:approval_id>/decide')
 def decide(approval_id):
  db=get_db(); db.execute('BEGIN IMMEDIATE'); row=db.execute('SELECT * FROM approvals WHERE id=?',(approval_id,)).fetchone()
  if not row: raise ApiError('Solicitação não encontrada.',404)
  require(row['module'],'approve')
  if row['requester']==g.user['id']: raise ApiError('A dupla custódia exige aprovação por outra pessoa.',403)
  if row['status']!='Pendente': raise ApiError('Esta solicitação já foi decidida.',409)
  data=request.get_json(); decision=data.get('decision'); reason=str(data.get('reason','')).strip()
  if decision not in ['Aprovado','Rejeitado'] or len(reason)<5 or len(reason)>1000: raise ApiError('Informe a decisão e uma justificativa de 5 a 1.000 caracteres.')
  if decision=='Aprovado':
   author=db.execute('SELECT u.*,gr.permissions group_permissions FROM users u JOIN groups gr ON gr.id=u.group_id WHERE u.id=?',(row['requester'],)).fetchone()
   permissions={**json.loads(author['group_permissions']),**json.loads(author['permissions'])}
   if not author['active'] or ('delete' if row['operation']=='delete' else 'write') not in permissions.get(row['module'],[]): raise ApiError('O solicitante não possui mais permissão para executar esta operação.',409)
   result=apply_change(row['module'],row['operation'],row['record_id'],json.loads(row['payload']),row['requester'])
  db.execute('UPDATE approvals SET status=?,reviewer=?,reason=?,decided_at=? WHERE id=?',(decision,g.user['id'],reason,now(),approval_id))
  notify(row['requester'],'Solicitação '+decision.lower(),f'Dupla custódia #{approval_id}: {reason}')
  audit(decision,'approvals',approval_id,{'reason':reason}); return jsonify(message='Decisão registrada.')

 @app.get('/api/tickets/<int:record_id>/comments')
 def comments(record_id):
  require('tickets'); return jsonify(items=[dict(r) for r in get_db().execute('SELECT c.*,u.name author FROM ticket_comments c JOIN users u ON u.id=c.user_id WHERE record_id=? ORDER BY c.id',(record_id,))])

 @app.post('/api/tickets/<int:record_id>/comments')
 def add_comment(record_id):
  require('tickets','write'); db=get_db(); record=db.execute("SELECT * FROM records WHERE id=? AND module='tickets'",(record_id,)).fetchone()
  if not record: raise ApiError('Chamado não encontrado.',404)
  body=str(request.get_json().get('body','')).strip()
  if not 3<=len(body)<=5000: raise ApiError('Escreva de 3 a 5.000 caracteres.')
  db.execute('INSERT INTO ticket_comments(record_id,user_id,body,created_at) VALUES(?,?,?,?)',(record_id,g.user['id'],body,now()))
  notify(record['created_by'],'Nova mensagem no chamado',f'#{record_id}: {body[:150]}'); audit('Comentário','tickets',record_id)
  return jsonify(message='Mensagem registrada.'),201

 @app.get('/api/publications')
 def publications():
  rows=get_db().execute("SELECT id,title,department,amount,data,updated_at FROM records WHERE module='transparency' AND status='Publicado' ORDER BY updated_at DESC LIMIT 500").fetchall()
  return jsonify(items=[{**dict(r),'amount':r['amount']/100,'data':json.loads(r['data'])} for r in rows])

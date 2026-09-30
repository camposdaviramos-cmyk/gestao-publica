"""API patrimonial: dossiê, relatórios, alertas e operações em lote."""
import csv,hashlib,io,json,uuid
from datetime import date,timedelta
from html import escape
from flask import g,request,jsonify
from auth import ApiError,require
from db import get_db,audit,notify
from domain import now,local_time
from erp_api import context_args
from erp_core import entity_access,integer,quantity,load,serialize,require_other
from asset_core import position,active_events,posting
from asset_accounting_operations import depreciate,reclassify_asset,writeoff_asset,depreciation_amount
from asset_management_operations import transfer_asset

HEADERS={'code':'Placa','name':'Bem','class':'Classificação','location':'Localização','owner':'Responsável','cpf':'CPF','condition':'Conservação','situation':'Situação','date':'Data','fact':'Fato','description':'Descrição','gross':'Valor bruto','accumulated':'Depreciação acumulada','net':'Valor líquido','debit':'Débitos','credit':'Créditos','account':'Conta','opening':'Saldo inicial','ingress':'Ingressos','valuation':'Avaliações','depreciation':'Depreciação','writeoff':'Baixas','ending':'Saldo final','state':'Situação cadastral','pending':'Pendência'}

def detail(o):
 p=position(o,False) if o['kind']=='items' else None;movements=[]
 if o['kind']=='items':
  for row in get_db().execute('SELECT m.*,u.name actor_name FROM asset_movements m JOIN users u ON u.id=m.actor_id WHERE m.asset_id=? ORDER BY m.date DESC,m.sequence DESC',(o['id'],)):
   x=dict(row)
   for k in ['before_snapshot','after_snapshot','metadata']:x[k]=json.loads(x[k])
   x['accounting']=[dict(e) for e in get_db().execute('SELECT l.date,a.class_id,a.location,l.account_id,l.debit,l.credit FROM asset_accounting_entries a JOIN erp_ledger l ON l.id=a.ledger_id WHERE a.movement_id=? ORDER BY l.id',(x['id'],))]
   movements.append(x)
 return {'position':p,'movements':movements}

def _assets(entity,exercise,args):
 rows=[]
 for r in get_db().execute("SELECT id FROM erp_objects WHERE module='assets' AND kind='items' AND entity_id=? AND deleted=0 ORDER BY code",(entity,)):
  o=load(r['id'],check_access=False);d=o['data']
  if args.get('class') and d.get('class')!=integer(args['class'],'Classificação',1):continue
  if args.get('location') and d.get('location')!=args['location']:continue
  if args.get('responsible') and d.get('responsible')!=integer(args['responsible'],'Responsável',1):continue
  if args.get('condition') and d.get('condition')!=args['condition']:continue
  if args.get('situation') and d.get('situation')!=args['situation']:continue
  if args.get('state') and o['state']!=args['state']:continue
  klass=load(d['class'],check_access=False)
  if args.get('nature') and klass['data'].get('nature')!=args['nature']:continue
  if args.get('account') and integer(args['account'],'Conta',1) not in [klass['data']['asset_account'],klass['data']['depreciation_account']]:continue
  if args.get('ingress_type') and d.get('ingress_type')!=args['ingress_type']:continue
  if args.get('commitment') and d.get('commitment')!=integer(args['commitment'],'Empenho',1):continue
  if args.get('supplier') and d.get('supplier')!=integer(args['supplier'],'Fornecedor',1):continue
  if args.get('invoice') and str(args['invoice']).casefold() not in str(d.get('invoice','')).casefold():continue
  rows.append(o)
 return rows

def report(entity,exercise,args):
 typ=args.get('report','depreciation');start=args.get('start',str(exercise)+'-01-01');end=args.get('end',str(exercise)+'-12-31')
 try:
  if date.fromisoformat(start)>date.fromisoformat(end):raise ValueError
 except ValueError:raise ApiError('Período patrimonial inválido.')
 assets=_assets(entity,exercise,args);ids={o['id'] for o in assets};items=[]
 if typ in ['depreciation','responsibility','tce','receipts']:
  for o in assets:
   d=o['data'];p=position(o,False)
   if typ=='tce' and o['state']!='Ativo':continue
   if typ=='receipts' and (not p or p.get('confirmed')):continue
   person=load(d['responsible'],check_access=False) if d.get('responsible') else None
   items.append({'code':o['code'],'name':o['name'],'class':load(d['class'],check_access=False)['name'],'location':d.get('location',''),'owner':d.get('owner',''),'cpf':person['data']['cpf'] if person else d.get('owner_cpf',''),'condition':d.get('condition',''),'situation':d.get('situation',''),'state':o['state'],'gross':p['gross'] if p else 0,'accumulated':p['accumulated'] if p else 0,'net':p['gross']-p['accumulated'] if p else 0,'pending':_pending(o,p)})
 elif typ=='history':
  for row in get_db().execute('SELECT * FROM asset_movements WHERE entity_id=? AND date BETWEEN ? AND ? ORDER BY date,sequence,id',(entity,start,end)):
   if row['asset_id'] not in ids:continue
   if args.get('movement') and row['fact']!=args['movement']:continue
   o=load(row['asset_id'],check_access=False);items.append({'code':o['code'],'name':o['name'],'date':row['date'],'fact':row['fact'],'description':row['description'],'location':json.loads(row['after_snapshot'])['data'].get('location','')})
 elif typ=='accounting':
  grouped={}
  for row in get_db().execute('SELECT m.asset_id,m.date,m.fact,l.account_id,l.debit,l.credit,a.class_id,a.location FROM asset_movements m JOIN asset_accounting_entries a ON a.movement_id=m.id JOIN erp_ledger l ON l.id=a.ledger_id WHERE m.entity_id=? AND m.date<=? ORDER BY m.date,m.id,l.id',(entity,end)):
   if row['asset_id'] not in ids:continue
   account=load(row['account_id'],check_access=False);klass=load(row['class_id'],check_access=False);key=(account['code'],account['name'],klass['name'],row['location'])
   x=grouped.setdefault(key,{'account':account['code']+' · '+account['name'],'class':klass['name'],'location':row['location'],'opening':0,'ingress':0,'valuation':0,'depreciation':0,'writeoff':0,'debit':0,'credit':0,'ending':0});net=row['debit']-row['credit']
   if row['date']<start:x['opening']+=net
   else:
    x['debit']+=row['debit'];x['credit']+=row['credit']
    if row['fact'] in ['Ingresso','Doação recebida','Valor complementar']:x['ingress']+=net
    elif row['fact'] in ['Reavaliação','Reavaliação positiva','Redução ao valor recuperável','Redução de valor']:x['valuation']+=net
    elif row['fact'].startswith('Depreciação'):x['depreciation']+=net
    elif row['fact'] in ['Baixa','Doação concedida']:x['writeoff']+=net
  for x in grouped.values():x['ending']=x['opening']+x['debit']-x['credit']
  items=list(grouped.values())
 else:raise ApiError('Relatório patrimonial inválido.')
 return {'report':typ,'start':start,'end':end,'items':items,'totals':{'gross':sum(x.get('gross',0) for x in items),'accumulated':sum(x.get('accumulated',0) for x in items),'net':sum(x.get('net',0) for x in items),'debit':sum(x.get('debit',0) for x in items),'credit':sum(x.get('credit',0) for x in items)}}

def _pending(o,p):
 if not p:return 'Ingresso não efetivado'
 if not p.get('confirmed'):return 'Recebimento pendente'
 if o['data']['type']!='Próprio' or o['data']['method']=='Não depreciável' or p['gross']-p['accumulated']<=p['residual']:return ''
 expected=(local_time().date().replace(day=1)-timedelta(days=1)).strftime('%Y-%m')
 return '' if (p.get('processed_through') or '')[:7]>=expected else 'Depreciação pendente até '+expected

def emit_asset_alerts(entity=None,exercise=None):
 db=get_db();period=local_time().date().strftime('%Y-%m');items=[];entities=[entity] if entity else ([r['id'] for r in db.execute('SELECT id FROM erp_entities WHERE active=1')] if g.user['group_id']==1 else [r['entity_id'] for r in db.execute('SELECT entity_id FROM erp_entity_access WHERE user_id=?',(g.user['id'],))])
 for entity_id in entities:
  for o in _assets(entity_id,exercise or local_time().year,{}):
   pending=_pending(o,position(o,False))
   if pending:
    inserted=db.execute('INSERT OR IGNORE INTO asset_alerts VALUES(?,?,?,?,?)',(o['id'],period,pending,g.user['id'],now())).rowcount
    if inserted:notify(g.user['id'],'Pendência patrimonial',o['code']+' · '+o['name']+': '+pending)
    items.append({'id':o['id'],'code':o['code'],'name':o['name'],'pending':pending})
 return items

def _render(data,fmt,entity):
 keys=[k for k in HEADERS if any(k in x for x in data['items'])]
 values=[[x.get(k,'') for k in keys] for x in data['items']]
 from integration_signatures import authorize_report,report_response
 authorize_report('assets',entity,fmt,data['report'])
 if fmt=='csv':
  out=io.StringIO();w=csv.writer(out,delimiter=';');w.writerow([HEADERS[k] for k in keys])
  for row in values:w.writerow(["'"+str(v) if str(v).lstrip().startswith(('=','+','-','@')) else str(v) for v in row])
  stream=io.BytesIO(out.getvalue().encode('utf-8-sig'));mime='text/csv'
 elif fmt=='pdf':
  from reportlab.lib.pagesizes import A4,landscape
  from reportlab.lib.styles import getSampleStyleSheet
  from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
  stream=io.BytesIO();styles=getSampleStyleSheet();story=[Paragraph('Relatório patrimonial · '+escape(data['report']),styles['Title']),Paragraph(escape('Período '+data['start']+' a '+data['end']),styles['Normal']),Spacer(1,12)]
  for row in values:story.extend([Paragraph(escape(' | '.join(HEADERS[k]+': '+str(v) for k,v in zip(keys,row))),styles['Normal']),Spacer(1,7)])
  SimpleDocTemplate(stream,pagesize=landscape(A4)).build(story);stream.seek(0);mime='application/pdf'
 else:raise ApiError('Formato de relatório inválido.')
 return report_response(stream,mime,'patrimonio-'+data['report']+'.'+fmt,'assets',entity,data['report'])

def _selection(entity,exercise,body):
 ids=body.get('selection',[])
 if not isinstance(ids,list):raise ApiError('Seleção de bens inválida.')
 if not ids:
  filters=body.get('filters') or {}
  if not isinstance(filters,dict):raise ApiError('Filtros do lote inválidos.')
  candidates=_assets(entity,exercise,filters);start=str(filters.get('code_from',''));end=str(filters.get('code_to',''))
  ids=[o['id'] for o in candidates if (not start or o['code']>=start) and (not end or o['code']<=end)]
 if not ids or len(ids)>1000:raise ApiError('O lote deve conter de 1 a 1.000 bens.')
 result=[]
 for value in dict.fromkeys(ids):
  o=load(integer(value,'Bem',1),'assets','items')
  if o['entity_id']!=entity:raise ApiError('Bem de outra entidade.')
  result.append(o)
 return result

def _preview(operation,assets,params):
 result=[]
 for o in assets:
  p=position(o);x={'id':o['id'],'code':o['code'],'name':o['name'],'location':o['data']['location'],'class':o['data']['class'],'gross':p['gross'],'accumulated':p['accumulated'],'net':p['gross']-p['accumulated']}
  if operation=='depreciate':
   try:until=date.fromisoformat(str(params.get('period'))+'-01');until=(until.replace(day=28)+timedelta(days=4)).replace(day=1)-timedelta(days=1)
   except (TypeError,ValueError):raise ApiError('Competência inválida.')
   amount=depreciation_amount(o,p,until.isoformat(),quantity(params.get('units',0)));entries,rule_id=posting(o,'Depreciação',amount,until.isoformat());x.update(period=params.get('period'),depreciation=amount,before=p['gross']-p['accumulated'],after=p['gross']-p['accumulated']-amount,debit_accounts=[e['account_id'] for e in entries if e['debit']],credit_accounts=[e['account_id'] for e in entries if e['credit']],rule_id=rule_id)
  elif operation=='transfer_asset':x['destination']=params.get('location')
  elif operation=='reclassify_asset':x['destination_class']=params.get('class')
  elif operation=='writeoff_asset':x['writeoff_type']=params.get('type')
  else:raise ApiError('Operação em lote inválida.')
  result.append(x)
 return result

def install_assets(app):
 @app.before_request
 def automatic_asset_alerts():
  if request.path=='/api/notifications' and g.user and 'read' in g.permissions.get('assets',[]):emit_asset_alerts()

 @app.get('/api/assets/reports')
 def asset_reports():
  require('assets');entity,exercise=context_args();data=report(entity,exercise,request.args);fmt=request.args.get('format','json');audit('Relatório patrimonial','assets',detail={'report':data['report'],'rows':len(data['items'])})
  return jsonify(data) if fmt=='json' else _render(data,fmt,entity)

 @app.post('/api/assets/alerts')
 def asset_alerts():
  require('assets','write');body=request.get_json() or {};entity=entity_access(body.get('entity'));exercise=integer(body.get('exercise'),'Exercício',2000,2100);items=emit_asset_alerts(entity,exercise)
  audit('Alertas patrimoniais atualizados','assets',detail={'count':len(items)});return jsonify(items=items,count=len(items))

 @app.post('/api/assets/batches/preview')
 def asset_batch_preview():
  require('assets','approve');body=request.get_json() or {};entity=entity_access(body.get('entity'));exercise=integer(body.get('exercise'),'Exercício',2000,2100);operation=str(body.get('operation',''));params=body.get('parameters') or {}
  if not isinstance(params,dict):raise ApiError('Parâmetros do lote inválidos.')
  assets=_selection(entity,exercise,body);preview=_preview(operation,assets,params);raw=json.dumps({'operation':operation,'parameters':params,'selection':[o['id'] for o in assets],'preview':preview},ensure_ascii=False,sort_keys=True,separators=(',',':'));digest=hashlib.sha256(raw.encode()).hexdigest()
  rid=get_db().execute('INSERT INTO asset_batches(entity_id,exercise,operation,parameters,selection,preview,sha256,state,created_by,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)',(entity,exercise,operation,json.dumps(params,ensure_ascii=False),json.dumps([o['id'] for o in assets]),json.dumps(preview,ensure_ascii=False),digest,'Aguardando aprovação',g.user['id'],now())).lastrowid
  totals={k:sum(x.get(k,0) for x in preview) for k in ['gross','accumulated','net','depreciation','before','after']};audit('Lote patrimonial preparado','assets',rid,{'operation':operation,'count':len(assets),'sha256':digest,'totals':totals});return jsonify(id=rid,version=1,sha256=digest,items=preview,totals=totals),201

 @app.post('/api/assets/batches/<int:batch_id>/execute')
 def asset_batch_execute(batch_id):
  require('assets','approve');require('finance','approve');db=get_db();db.execute('BEGIN IMMEDIATE');row=db.execute('SELECT * FROM asset_batches WHERE id=?',(batch_id,)).fetchone()
  if not row:raise ApiError('Lote patrimonial não encontrado.',404)
  if row['state']!='Aguardando aprovação':raise ApiError('Lote patrimonial já processado.',409)
  if row['created_by']==g.user['id']:raise ApiError('A execução do lote exige outro usuário autorizado.',403)
  body=request.get_json() or {}
  if integer(body.get('version'),'Versão',1)!=row['version']:raise ApiError('Lote atualizado; recarregue.',409)
  params=json.loads(row['parameters']);ids=json.loads(row['selection']);preview=json.loads(row['preview']);raw=json.dumps({'operation':row['operation'],'parameters':params,'selection':ids,'preview':preview},ensure_ascii=False,sort_keys=True,separators=(',',':'))
  if hashlib.sha256(raw.encode()).hexdigest()!=row['sha256']:raise ApiError('Integridade do lote inválida.',409)
  results=[]
  for asset_id in ids:
   o=load(asset_id,'assets','items');fn={'depreciate':depreciate,'transfer_asset':transfer_asset,'reclassify_asset':reclassify_asset,'writeoff_asset':writeoff_asset}[row['operation']];result=fn(o,params);db.execute('INSERT INTO asset_batch_results VALUES(?,?,?)',(batch_id,asset_id,json.dumps(result,ensure_ascii=False)));results.append({'asset_id':asset_id,'result':result})
  db.execute("UPDATE asset_batches SET state='Executado',version=version+1,reviewed_by=?,executed_at=? WHERE id=?",(g.user['id'],now(),batch_id));audit('Lote patrimonial executado','assets',batch_id,{'count':len(results)});return jsonify(items=results,count=len(results),message='Lote patrimonial executado.')

 @app.get('/api/assets/batches/<int:batch_id>')
 def asset_batch_detail(batch_id):
  require('assets');row=get_db().execute('SELECT * FROM asset_batches WHERE id=?',(batch_id,)).fetchone()
  if not row:raise ApiError('Lote patrimonial não encontrado.',404)
  entity_access(row['entity_id']);result=dict(row)
  for k in ['parameters','selection','preview']:result[k]=json.loads(result[k])
  result['results']=[{'asset_id':x['asset_id'],'result':json.loads(x['result'])} for x in get_db().execute('SELECT * FROM asset_batch_results WHERE batch_id=? ORDER BY asset_id',(batch_id,))]
  return jsonify(result)

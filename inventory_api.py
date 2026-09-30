"""Painéis, rastreabilidade e administração das autorizações do almoxarifado."""
import csv,io,json
from html import escape
from flask import request,jsonify,g
from auth import ApiError,require
from db import get_db,audit
from domain import now
from erp_core import load,serialize,integer,event
from inventory_core import children
from inventory_reports import report


def detail(o):
 result={};db=get_db();k=o['kind']
 if k=='requisition_items':
  result['deliveries']=[dict(r) for r in db.execute("SELECT f.*,u.name actor,COALESCE((SELECT SUM(quantity) FROM inventory_fulfillments r WHERE r.original_id=f.id),0) returned FROM inventory_fulfillments f JOIN users u ON u.id=f.actor_id WHERE f.item_id=? ORDER BY f.id",(o['id'],))]
 field,kind={'requisitions':('requisition','requisition_items'),'authorizations':('authorization','authorization_items'),'invoices':('invoice','invoice_items'),'commissions':('commission','commission_members')}.get(k,(None,None))
 if kind:result['items']=[serialize(x) for x in children(kind,field,o['id'])]
 if k=='movements':
  row=db.execute('SELECT settlement_id,amount FROM inventory_movement_postings WHERE movement_id=?',(o['id'],)).fetchone();result['posting']=dict(row) if row else None
 if k=='invoices':
  row=db.execute('SELECT settlement_id,amount FROM inventory_invoice_postings WHERE invoice_id=?',(o['id'],)).fetchone();result['posting']=dict(row) if row else None
 return result

HEADERS={'date':'Data','warehouse':'Almoxarifado','material':'Material','code':'Código','quantity':'Quantidade','value':'Valor (R$)','incoming':'Fornecimento pendente','in_procurement':'Compra solicitada','virtual':'Saldo virtual','transit':'Em trânsito','minimum':'Mínimo','maximum':'Máximo','monthly_average':'Consumo médio mensal','model':'Controle','suggested':'Reposição sugerida','abc':'Classe ABC','share_percent':'Participação (%)','cumulative_percent':'Acumulado (%)','average_quantity':'Média mensal','months':'Meses','document':'Documento','type':'Movimento','period':'Competência','opening_quantity':'Quantidade inicial','opening_value':'Valor inicial','in_quantity':'Entradas / quantidade','in_value':'Entradas / valor','out_quantity':'Saídas / quantidade','out_value':'Saídas / valor','closing_quantity':'Quantidade final','closing_value':'Valor final'}
QUANTITIES={'quantity','incoming','in_procurement','virtual','transit','minimum','maximum','monthly_average','suggested','average_quantity','opening_quantity','in_quantity','out_quantity','closing_quantity'}
VALUES={'value','opening_value','in_value','out_value','closing_value'}

def install_inventory(app):
 @app.get('/api/inventory/units/<int:object_id>/permissions')
 def permissions(object_id):
  require('users');o=load(object_id,'inventory')
  if o['kind'] not in ['warehouses','departments']:raise ApiError('Selecione um almoxarifado ou órgão requisitante.')
  rows=get_db().execute('SELECT u.id,u.name,u.email,u.group_id,p.allowed FROM users u LEFT JOIN inventory_permissions p ON p.user_id=u.id AND p.target_id=? ORDER BY u.name',(object_id,)).fetchall()
  return jsonify(version=o['version'],restricted=bool(o['data'].get('restricted')),items=[dict(r) for r in rows])

 @app.put('/api/inventory/units/<int:object_id>/permissions')
 def save_permissions(object_id):
  require('users','write');require('inventory','write')
  if g.user['group_id']!=1:raise ApiError('A configuração individual exige administrador.',403)
  db=get_db();db.execute('BEGIN IMMEDIATE');o=load(object_id,'inventory');b=request.get_json()
  if o['kind'] not in ['warehouses','departments']:raise ApiError('Unidade inválida.')
  if integer(b.get('version'),'Versão',1)!=o['version']:raise ApiError('Unidade alterada. Recarregue.',409)
  if not isinstance(b.get('restricted'),bool) or not isinstance(b.get('items'),list) or len(b['items'])>10000:raise ApiError('Permissões inválidas.')
  seen=set();values=[]
  for item in b['items']:
   if not isinstance(item,dict):raise ApiError('Permissão inválida.')
   uid=integer(item.get('user_id'),'Usuário',1)
   if uid in seen or not isinstance(item.get('allowed'),bool):raise ApiError('Permissão duplicada ou inválida.')
   if not db.execute('SELECT 1 FROM users WHERE id=?',(uid,)).fetchone():raise ApiError('Usuário não encontrado.')
   seen.add(uid);values.append((object_id,uid,int(item['allowed']),g.user['id'],now()))
  db.execute('DELETE FROM inventory_permissions WHERE target_id=?',(object_id,));db.executemany('INSERT INTO inventory_permissions VALUES(?,?,?,?,?)',values);o['data']['restricted']=b['restricted'];db.execute('UPDATE erp_objects SET data=?,version=version+1,updated_at=? WHERE id=?',(json.dumps(o['data'],ensure_ascii=False),now(),object_id));event(o,'Autorizações da unidade alteradas',{'restricted':b['restricted'],'users':b['items']});return jsonify(message='Autorizações salvas. Aplicação imediata nas próximas operações.')

 @app.get('/api/inventory/reports')
 def reports():
  from erp_api import context_args
  from integration_signatures import authorize_report,report_response
  require('inventory');entity,year=context_args();fmt=request.args.get('format','json');authorize_report('inventory',entity,fmt,'movements');data=report(entity,year,request.args)
  audit('Relatório de estoque','inventory',detail={'entity':entity,'exercise':year,'report':data['report'],'filters':data['filters']})
  if fmt=='json':return jsonify(data)
  if fmt not in ['csv','pdf']:raise ApiError('Formato de relatório inválido.')
  if len(data['items'])>10000:raise ApiError('Refine a consulta para exportar até 10.000 linhas.')
  keys=[k for k in HEADERS if any(k in x for x in data['items'])];values=[]
  from inventory_operations import units,reais
  for row in data['items']:values.append([units(row.get(k,0)) if k in QUANTITIES else reais(row.get(k,0)) if k in VALUES else str(row.get(k,'')) for k in keys])
  title={'balances':'Saldos e reposição','movements':'Movimentações de estoque','consumption':'Consumo e classificação ABC','monthly':'Balancete mensal de estoque'}[data['report']]
  if fmt=='csv':
   out=io.StringIO();w=csv.writer(out,delimiter=';');w.writerow([HEADERS[k] for k in keys])
   for row in values:w.writerow(["'"+v if v.lstrip().startswith(('=','+','-','@')) else v for v in row])
   stream=io.BytesIO(out.getvalue().encode('utf-8-sig'));mime='text/csv'
  else:
   from reportlab.lib.pagesizes import A4,landscape
   from reportlab.lib.styles import getSampleStyleSheet
   from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
   stream=io.BytesIO();styles=getSampleStyleSheet();story=[Paragraph(escape(title),styles['Title']),Paragraph(escape(f"Entidade {entity} · Exercício {year} · {data['filters']['start']} a {data['filters']['end']}"),styles['Normal']),Paragraph(escape(data.get('note','')),styles['Normal']),Spacer(1,12)]
   for row in values:story.extend([Paragraph(escape(' | '.join(HEADERS[k]+': '+v for k,v in zip(keys,row))),styles['Normal']),Spacer(1,8)])
   SimpleDocTemplate(stream,pagesize=landscape(A4)).build(story);stream.seek(0);mime='application/pdf'
  return report_response(stream,mime,'estoque-'+data['report']+'.'+fmt,'inventory',entity,'movements')

 @app.get('/api/inventory/dossier/<int:object_id>')
 def dossier(object_id):
  o=load(object_id,'inventory');req=None;authorizations=[]
  if o['kind']=='requisitions':req=o;authorizations=children('authorizations','requisition',o['id'])
  elif o['kind']=='authorizations':authorizations=[o];req=load(o['data']['requisition']) if o['data'].get('requisition') else None
  elif o['kind']=='invoices':authorizations=[load(o['data']['authorization'])] if o['data'].get('authorization') else []
  else:raise ApiError('Selecione requisição, autorização ou nota fiscal.')
  result=[];planning=[]
  if req:
   for line in children('requisition_items','requisition',req['id']):
    for link in children('purchase_links','requisition_item',line['id']):
     pitem=load(link['data']['procurement_item']);process=load(pitem['data']['process']);phases=[{**dict(e),'payload':json.loads(e['payload'])} for e in get_db().execute("SELECT operation,payload,created_at FROM erp_events WHERE object_id=? AND operation='advance_process' ORDER BY id",(process['id'],))];planning.append({'link':serialize(link),'process':serialize(process),'phases':phases})
  for a in authorizations:
   p=load(a['data']['process']);c=load(a['data']['commitment']);phase_events=[]
   for e in get_db().execute("SELECT operation,payload,created_at FROM erp_events WHERE object_id=? AND operation IN ('advance_process','award_proposal') ORDER BY id",(p['id'],)):phase_events.append({**dict(e),'payload':json.loads(e['payload'])})
   result.append({'authorization':serialize(a),'items':[serialize(i) for i in children('authorization_items','authorization',a['id'])],'process':serialize(p),'phases':phase_events,'commitment':serialize(c),'invoices':[serialize(i) for i in children('invoices','authorization',a['id'])]})
  audit('Rastreabilidade de aquisição','inventory',o['id']);return jsonify(requisition=serialize(req) if req else None,chains=result,planning=planning)

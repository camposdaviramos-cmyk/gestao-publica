"""API de frota: relatórios, cartões de combustível, permissões e alertas."""
import base64,csv,hashlib,io,json
from datetime import date,timedelta
from decimal import Decimal
from html import escape
from flask import g,request,jsonify
from auth import ApiError,require
from db import get_db,audit,notify
from domain import now,local_time
from erp_api import context_args
from erp_core import entity_access,integer,create_object,load,serialize,set_state
from fleet_core import location,location_access
from fleet_operations import register_refuel,tank_stock

HEADERS={'vehicle':'Veículo','code':'Placa','type':'Tipo','fuel':'Combustível','station':'Posto','location':'Localização','period':'Período','liters':'Litros','amount':'Valor','distance':'Distância / horas','unit_cost':'Custo por km/h','efficiency':'Km ou horas por litro','expected':'Referência','driver':'Motorista','event':'Evento','date':'Data','meter':'Medidor','quantity':'Quantidade','capacity':'Capacidade','utilization':'Utilização %','pending':'Pendência'}

def detail(o):
 result={}
 if o['kind']=='vehicles':
  result['asset']=serialize(load(o['data']['asset'],check_access=False));result['events']=[]
  for r in get_db().execute('SELECT e.*,u.name actor_name FROM fleet_events e JOIN users u ON u.id=e.actor_id WHERE e.vehicle_id=? ORDER BY e.occurred_at DESC,e.id DESC',(o['id'],)):
   x=dict(r);x['metadata']=json.loads(x['metadata']);result['events'].append(x)
  result['agenda']=agenda(o)
 if o['kind']=='tanks':
  s=tank_stock(o);result['stock']={'quantity':s['quantity'],'value':s['value'],'capacity':o['data']['capacity'],'utilization':round(s['quantity']*100/o['data']['capacity'],2) if o['data']['capacity'] else 0}
 return result

def _vehicles(entity,args):
 result=[]
 for row in get_db().execute("SELECT id FROM erp_objects WHERE module='fleet' AND kind='vehicles' AND entity_id=? AND deleted=0 ORDER BY code",(entity,)):
  v=load(row['id'],check_access=False)
  try:location_access(v,False)
  except ApiError:continue
  asset=load(v['data']['asset'],check_access=False);loc=asset['data']['location']
  if args.get('vehicle') and v['id']!=integer(args['vehicle'],'Veículo',1):continue
  if args.get('location') and loc!=args['location']:continue
  if args.get('fuel') and v['data']['fuel']!=args['fuel']:continue
  if args.get('vehicle_type') and v['data'].get('vehicle_type')!=integer(args['vehicle_type'],'Tipo',1):continue
  result.append((v,asset,loc))
 return result

def agenda(vehicle):
 today=local_time().date();meter=max(vehicle['data']['opening_meter'],get_db().execute("SELECT COALESCE(MAX(meter),0) FROM fleet_events WHERE vehicle_id=?",(vehicle['id'],)).fetchone()[0]);items=[]
 for kind,field in [('agendas','vehicle')]:
  for row in get_db().execute("SELECT id FROM erp_objects WHERE module='fleet' AND kind=? AND deleted=0 AND state='Rascunho' AND json_extract(data,?)=?",(kind,'$.'+field,vehicle['id'])):
   o=load(row['id'],check_access=False);d=o['data'];pending=(d.get('due_date') and d['due_date']<=today.isoformat()) or (d.get('due_meter') and d['due_meter']<=meter)
   items.append({'id':o['id'],'code':o['code'],'name':o['name'],'type':d['type'],'due_date':d.get('due_date'),'due_meter':d.get('due_meter'),'pending':bool(pending)})
 for row in get_db().execute("SELECT s.id FROM erp_objects s JOIN erp_objects a ON a.id=json_extract(s.data,'$.accessory') WHERE s.module='fleet' AND s.kind='accessory_schedules' AND s.deleted=0 AND s.state='Rascunho' AND json_extract(a.data,'$.vehicle')=?",(vehicle['id'],)):
  o=load(row['id'],check_access=False);d=o['data'];pending=(d.get('due_date') and d['due_date']<=today.isoformat()) or (d.get('due_meter') and d['due_meter']<=meter);items.append({'id':o['id'],'code':o['code'],'name':o['name'],'type':'Item agregado','due_date':d.get('due_date'),'due_meter':d.get('due_meter'),'pending':bool(pending)})
 return items


def excess_consumption(vehicle,start,end):
 events=get_db().execute("SELECT meter,quantity FROM fleet_events WHERE vehicle_id=? AND event_type='Abastecimento' AND occurred_at BETWEEN ? AND ? ORDER BY occurred_at,id",(vehicle['id'],start,end)).fetchall()
 if not events:return None
 before=get_db().execute("SELECT meter FROM fleet_events WHERE vehicle_id=? AND occurred_at<? AND meter>0 ORDER BY occurred_at DESC,id DESC LIMIT 1",(vehicle['id'],start)).fetchone();opening=before['meter'] if before else vehicle['data']['opening_meter'];distance=max(x['meter'] for x in events)-opening;liters=sum(x['quantity'] for x in events)
 if distance<=0 or liters<=0:return None
 efficiency=round(distance*1000000/liters,2);expected=vehicle['data'].get('consumption_limit',0)/1000000
 return {'distance':distance,'liters':liters,'efficiency':efficiency,'expected':expected,'exceeded':bool(expected and efficiency<expected)}

def report(entity,exercise,args):
 typ=args.get('report','consumption');start=args.get('start',str(exercise)+'-01-01');end=args.get('end',str(exercise)+'-12-31')+'T23:59'
 try:
  if date.fromisoformat(start[:10])>date.fromisoformat(end[:10]):raise ValueError
 except ValueError:raise ApiError('Período inválido.')
 vehicles=_vehicles(entity,args);ids={v['id']:(v,a,l) for v,a,l in vehicles};items=[]
 events=[dict(r) for r in get_db().execute('SELECT * FROM fleet_events WHERE entity_id=? AND occurred_at BETWEEN ? AND ? ORDER BY occurred_at,id',(entity,start,end)) if r['vehicle_id'] in ids]
 if typ in ['consumption','comparison']:
  groups={}
  for e in events:
   if e['event_type']!='Abastecimento':continue
   v,a,loc=ids[e['vehicle_id']];meta=json.loads(e['metadata'])
   if typ=='consumption' and a['data']['type']!='Próprio':continue
   vtype=load(v['data']['vehicle_type'],check_access=False)['name'] if v['data'].get('vehicle_type') else 'Não informado';key=(meta['fuel'],meta['station'],loc) if typ=='consumption' else (vtype,meta['fuel'])
   x=groups.setdefault(key,{'type':vtype if typ=='comparison' else '', 'fuel':meta['fuel'],'station':meta['station'] if typ=='consumption' else 'Todos','location':loc if typ=='consumption' else 'Todas','liters':0,'amount':0});x['liters']+=e['quantity'];x['amount']+=e['amount']
  total_q=sum(x['liters'] for x in groups.values()) or 1;total_v=sum(x['amount'] for x in groups.values()) or 1
  for x in groups.values():x['quantity_percent']=round(x['liters']*100/total_q,2);x['value_percent']=round(x['amount']*100/total_v,2)
  items=list(groups.values())
 elif typ in ['costs','expenses','balance']:
  for v,a,loc in vehicles:
   rows=[e for e in events if e['vehicle_id']==v['id']];cost=sum(e['amount'] for e in rows);meters=[v['data']['opening_meter']]+[e['meter'] for e in rows if e['meter']]
   distance=max(meters)-min(meters);unit=round(cost*1000000/distance) if distance else 0
   items.append({'vehicle':v['name'],'code':v['code'],'type':v['data']['meter_type'],'location':loc,'amount':cost,'distance':distance,'unit_cost':unit})
 elif typ=='drivers':
  driver=args.get('driver');driver_id=integer(driver,'Motorista',1) if driver else None
  for e in events:
   if driver_id and e['driver_id']!=driver_id:continue
   if not e['driver_id']:continue
   v=ids[e['vehicle_id']][0];items.append({'driver':load(e['driver_id'],check_access=False)['name'],'vehicle':v['name'],'code':v['code'],'event':e['event_type'],'date':e['occurred_at'],'meter':e['meter'],'amount':e['amount']})
 elif typ=='overconsumption':
  for v,a,loc in vehicles:
   x=excess_consumption(v,start,end)
   if x and x['exceeded']:items.append({'vehicle':v['name'],'code':v['code'],'type':v['data']['meter_type'],'fuel':v['data']['fuel'],'location':loc,**x})
 elif typ=='tanks':
  for row in get_db().execute("SELECT id FROM erp_objects WHERE module='fleet' AND kind='tanks' AND entity_id=? AND deleted=0 ORDER BY code",(entity,)):
   t=load(row['id'],check_access=False);s=tank_stock(t);items.append({'code':t['code'],'vehicle':t['name'],'fuel':t['data']['fuel'],'location':t['data']['location'],'quantity':s['quantity'],'amount':s['value'],'capacity':t['data']['capacity'],'utilization':round(s['quantity']*100/t['data']['capacity'],2) if t['data']['capacity'] else 0})
 elif typ=='alerts':
  for v,a,loc in vehicles:
   for x in agenda(v):
    if x['pending']:items.append({'vehicle':v['name'],'code':v['code'],'location':loc,'event':x['type'],'date':x.get('due_date'),'meter':x.get('due_meter'),'pending':x['name']})
 else:raise ApiError('Relatório de frota inválido.')
 return {'report':typ,'start':start[:10],'end':end[:10],'items':items,'totals':{'liters':sum(x.get('liters',0) for x in items),'amount':sum(x.get('amount',0) for x in items),'distance':sum(x.get('distance',0) for x in items)}}

def _render(data,fmt,entity):
 keys=[k for k in HEADERS if any(k in x for x in data['items'])];values=[[x.get(k,'') for k in keys] for x in data['items']]
 from integration_signatures import authorize_report,report_response
 authorize_report('fleet',entity,fmt,data['report'])
 if fmt=='csv':
  out=io.StringIO();w=csv.writer(out,delimiter=';');w.writerow([HEADERS[k] for k in keys]);w.writerows(values);stream=io.BytesIO(out.getvalue().encode('utf-8-sig'));mime='text/csv'
 elif fmt=='pdf':
  from reportlab.lib.pagesizes import A4,landscape
  from reportlab.lib.styles import getSampleStyleSheet
  from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
  stream=io.BytesIO();styles=getSampleStyleSheet();story=[Paragraph('Relatório de frota · '+escape(data['report']),styles['Title']),Paragraph(escape(data['start']+' a '+data['end']),styles['Normal']),Spacer(1,10)]
  for row in values:story.extend([Paragraph(escape(' | '.join(HEADERS[k]+': '+str(v) for k,v in zip(keys,row))),styles['Normal']),Spacer(1,6)])
  SimpleDocTemplate(stream,pagesize=landscape(A4)).build(story);stream.seek(0);mime='application/pdf'
 else:raise ApiError('Formato inválido.')
 return report_response(stream,mime,'frota-'+data['report']+'.'+fmt,'fleet',entity,data['report'])

def emit_alerts():
 db=get_db();items=[];pref=db.execute('SELECT * FROM fleet_user_preferences WHERE user_id=?',(g.user['id'],)).fetchone();today=local_time().date();period_days=pref['period_days'] if pref else 30;start=(today-timedelta(days=period_days)).isoformat();end=today.isoformat()+'T23:59';allowed_locations=set(json.loads(pref['locations'])) if pref else set()
 for entity in ([r['id'] for r in db.execute('SELECT id FROM erp_entities WHERE active=1')] if g.user['group_id']==1 else [r['entity_id'] for r in db.execute('SELECT entity_id FROM erp_entity_access WHERE user_id=?',(g.user['id'],))]):
  for v,a,loc in _vehicles(entity,{}):
   if pref and pref['consumption_alert'] and (not allowed_locations or loc in allowed_locations):
    excessive=excess_consumption(v,start,end)
    if excessive and excessive['exceeded']:
     title='Consumo de combustível acima do previsto';body='fleet-consumption:'+v['code']+':'+today.strftime('%Y-%m')+':'+str(g.user['id'])
     if not db.execute('SELECT 1 FROM notifications WHERE user_id=? AND body LIKE ?',(g.user['id'],body+'%')).fetchone():notify(g.user['id'],title,body+' · '+v['code']+' · apurado '+str(excessive['efficiency'])+' / referência '+str(excessive['expected']))
     items.append({'vehicle':v['id'],'pending':title,**excessive})
   for x in agenda(v):
    if x['pending']:
     title='Compromisso vencido da frota';body=v['code']+' · '+x['name'];key='fleet-alert:'+str(x['id'])+':'+str(g.user['id'])
     if not db.execute("SELECT 1 FROM notifications WHERE user_id=? AND body LIKE ?",(g.user['id'],key+'%')).fetchone():notify(g.user['id'],title,key+' · '+body)
     items.append(x)
 return items

def install_fleet(app):
 @app.before_request
 def automatic_fleet_alerts():
  if request.path=='/api/notifications' and g.user and 'read' in g.permissions.get('fleet',[]):emit_alerts()

 @app.get('/api/fleet/reports')
 def fleet_reports():
  require('fleet');entity,exercise=context_args();data=report(entity,exercise,request.args);fmt=request.args.get('format','json');audit('Relatório de frota','fleet',detail={'report':data['report'],'rows':len(data['items'])});return jsonify(data) if fmt=='json' else _render(data,fmt,entity)

 @app.get('/api/fleet/preferences')
 def fleet_preferences():
  require('fleet');row=get_db().execute('SELECT * FROM fleet_user_preferences WHERE user_id=?',(g.user['id'],)).fetchone();return jsonify(dict(row) if row else {'consumption_alert':0,'period_days':30,'locations':'[]','version':1})

 @app.put('/api/fleet/preferences')
 def save_fleet_preferences():
  require('fleet','write');d=request.get_json() or {};period=integer(d.get('period_days',30),'Período',1,366);locations=d.get('locations',[])
  if not isinstance(locations,list) or len(locations)>200:raise ApiError('Localizações inválidas.')
  db=get_db();row=db.execute('SELECT version FROM fleet_user_preferences WHERE user_id=?',(g.user['id'],)).fetchone()
  if row and integer(d.get('version'),'Versão',1)!=row['version']:raise ApiError('Preferência alterada; recarregue.',409)
  db.execute('INSERT INTO fleet_user_preferences(user_id,consumption_alert,period_days,locations,version) VALUES(?,?,?,?,1) ON CONFLICT(user_id) DO UPDATE SET consumption_alert=excluded.consumption_alert,period_days=excluded.period_days,locations=excluded.locations,version=fleet_user_preferences.version+1',(g.user['id'],int(bool(d.get('consumption_alert'))),period,json.dumps(locations,ensure_ascii=False)));return jsonify(message='Preferências salvas.')

 @app.get('/api/fleet/locations/permissions')
 def fleet_permissions():
  require('users');entity,_=context_args();users=get_db().execute('SELECT id,name,email,group_id FROM users WHERE active=1 ORDER BY name').fetchall();rows=get_db().execute('SELECT * FROM fleet_location_permissions WHERE entity_id=?',(entity,)).fetchall();return jsonify(items=[dict(x) for x in rows],users=[dict(x) for x in users])

 @app.put('/api/fleet/locations/permissions')
 def save_fleet_permissions():
  require('users','write');body=request.get_json() or {};entity=entity_access(body.get('entity'));items=body.get('items',[])
  if not isinstance(items,list) or len(items)>5000:raise ApiError('Permissões inválidas.')
  db=get_db();db.execute('DELETE FROM fleet_location_permissions WHERE entity_id=?',(entity,))
  for x in items:db.execute('INSERT INTO fleet_location_permissions VALUES(?,?,?,?)',(integer(x.get('user_id'),'Usuário',1),entity,str(x.get('location','')).strip(),int(bool(x.get('allowed')))))
  audit('Permissões da frota atualizadas','fleet',entity,{'count':len(items)});return jsonify(message='Permissões atualizadas.')

 @app.post('/api/fleet/import-card')
 def import_card():
  require('fleet','write');body=request.get_json() or {};entity=entity_access(body.get('entity'));exercise=integer(body.get('exercise'),'Exercício',2000,2100)
  try:raw=base64.b64decode(body.get('content',''),validate=True)
  except Exception:raise ApiError('Arquivo CSV inválido.')
  if not 0<len(raw)<=5000000:raise ApiError('Arquivo deve ter até 5 MB.')
  digest=hashlib.sha256(raw).hexdigest()
  if get_db().execute("SELECT 1 FROM erp_objects WHERE module='fleet' AND kind='fuel_imports' AND entity_id=? AND json_extract(data,'$.file_hash')=?",(entity,digest)).fetchone():raise ApiError('Arquivo de cartão já importado.',409)
  try:text=raw.decode('utf-8-sig');rows=list(csv.DictReader(io.StringIO(text),delimiter=';'))
  except Exception:raise ApiError('CSV deve estar em UTF-8 e separado por ponto e vírgula.')
  required={'plate','registration','cpf','station_cnpj','datetime','liters','unit_price','fuel','meter'}
  if not rows or not required.issubset(rows[0]):raise ApiError('Cabeçalho do cartão incompatível.')
  batch=create_object('fleet','fuel_imports',entity,exercise,{'code':'CARD-'+digest[:12].upper(),'name':'Importação cartão combustível','period_start':min(x['datetime'][:10] for x in rows),'period_end':max(x['datetime'][:10] for x in rows),'layout':'CSV padrão','file_hash':digest,'rows':len(rows)});accepted=[];rejected=[]
  for n,x in enumerate(rows,2):
   external=hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
   if get_db().execute('SELECT 1 FROM fleet_import_rows WHERE external_key=?',(external,)).fetchone():rejected.append({'line':n,'error':'Linha já importada'});continue
   try:
    vehicle_id=get_db().execute("SELECT id FROM erp_objects WHERE module='fleet' AND kind='vehicles' AND entity_id=? AND deleted=0 AND code=?",(entity,x['plate'].strip().upper())).fetchone();driver_id=get_db().execute("SELECT id FROM erp_objects WHERE module='fleet' AND kind='drivers' AND entity_id=? AND deleted=0 AND json_extract(data,'$.registration')=? AND json_extract(data,'$.cpf')=?",(entity,x['registration'].strip(),x['cpf'].strip())).fetchone()
    if not vehicle_id or not driver_id:raise ApiError('Veículo ou motorista não localizado.')
    refuel=create_object('fleet','refuels',entity,exercise,{'code':'CARD-'+external[:14].upper(),'name':'Abastecimento por cartão','vehicle':vehicle_id[0],'driver':driver_id[0],'date':x['datetime'],'meter':x['meter'],'fuel':x['fuel'],'liters':x['liters'],'unit_price':x['unit_price'],'station':'Terceiro','station_document':x['station_cnpj'],'card_reference':external,'import_batch':batch['id'],'invoice':x.get('invoice','')});register_refuel(refuel,{});get_db().execute('INSERT INTO fleet_import_rows VALUES(?,?,?,?,?,?,NULL)',(batch['id'],n,external,json.dumps(x,ensure_ascii=False),refuel['id'],'Importado'));accepted.append(refuel['id'])
   except ApiError as exc:get_db().execute('INSERT INTO fleet_import_rows VALUES(?,?,?,?,NULL,?,?)',(batch['id'],n,external,json.dumps(x,ensure_ascii=False),'Rejeitado',str(exc)));rejected.append({'line':n,'error':str(exc)})
  set_state(batch,'Processado com rejeições' if rejected else 'Processado');audit('Cartão combustível importado','fleet',batch['id'],{'accepted':len(accepted),'rejected':len(rejected),'sha256':digest});return jsonify(batch_id=batch['id'],accepted=accepted,rejected=rejected),201

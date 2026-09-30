"""Integridade, permissões e trilha imutável da frota."""
import json,re
from datetime import datetime,date
from flask import g
from auth import ApiError,require
from db import get_db
from domain import now,local_time
from erp_core import load,related,check_period,balance,change_balance,event

def vehicle_asset(vehicle):
 asset=load(vehicle['data']['asset'],'assets','items',check_access=False)
 if asset['entity_id']!=vehicle['entity_id']:raise ApiError('Bem patrimonial pertence a outra entidade.')
 if asset['state'] not in ['Ativo']:raise ApiError('Veículo vinculado a bem patrimonial indisponível.',409)
 return asset

def location(vehicle):
 return vehicle_asset(vehicle)['data']['location']

def location_access(vehicle,write=True):
 require('fleet','write' if write else 'read')
 if g.user['group_id']==1:return
 loc=location(vehicle);row=get_db().execute('SELECT allowed FROM fleet_location_permissions WHERE user_id=? AND entity_id=? AND location=?',(g.user['id'],vehicle['entity_id'],loc)).fetchone()
 if not row or not row['allowed']:raise ApiError('Seu usuário não possui autorização para a localização deste veículo.',403)

def occurred(value):
 try:d=datetime.fromisoformat(str(value))
 except (TypeError,ValueError):raise ApiError('Data e hora do movimento inválida.')
 if d>local_time().replace(tzinfo=None):raise ApiError('Movimento futuro não permitido.')
 return d.isoformat(timespec='minutes')

def vehicle_for(o,day):
 vehicle=related(o,'vehicle','fleet','vehicles');vehicle_asset(vehicle);location_access(vehicle);day=occurred(day)
 if vehicle['data'].get('blocked_through') and day[:10]<=vehicle['data']['blocked_through']:raise ApiError('Movimentação bloqueada nesse período.',409)
 check_period(o,day)
 return vehicle,day

def chronology(vehicle,day,meter):
 rows=get_db().execute('SELECT occurred_at,meter FROM fleet_events WHERE vehicle_id=? ORDER BY occurred_at,id',(vehicle['id'],)).fetchall();opening=vehicle['data']['opening_meter']
 if meter<opening:raise ApiError('Leitura inferior ao medidor inicial.')
 for row in rows:
  if row['occurred_at']<day and row['meter']>meter:raise ApiError('Leitura inferior a movimento anterior.',409)
  if row['occurred_at']>day and row['meter']<meter:raise ApiError('Leitura superior a movimento posterior.',409)
 if any(row['occurred_at']==day and row['meter']!=meter for row in rows):raise ApiError('Já existe evento no mesmo instante com leitura diferente.',409)

def record(o,vehicle,day,typ,meter=0,quantity=0,amount=0,driver=None,metadata=None):
 db=get_db();loc=location(vehicle);metadata=metadata or {};db.execute('INSERT INTO fleet_events(vehicle_id,source_id,entity_id,occurred_at,event_type,meter,quantity,amount,driver_id,location,metadata,actor_id,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(vehicle['id'],o['id'],o['entity_id'],day,typ,meter,quantity,amount,driver,loc,json.dumps(metadata,ensure_ascii=False),g.user['id'],now()))
 if meter:change_balance(vehicle['id'],'last_meter',meter-balance(vehicle['id'],'last_meter'))
 stamp=int(datetime.fromisoformat(day).strftime('%Y%m%d%H%M'));change_balance(vehicle['id'],'last_timestamp',stamp-balance(vehicle['id'],'last_timestamp'))
 if amount:change_balance(vehicle['id'],'cost',amount);change_balance(o['id'],'cost',amount)
 event(o,typ,{'vehicle':vehicle['id'],'occurred_at':day,'meter':meter,'quantity':quantity,'amount':amount,'location':loc,**metadata})

def validate_fleet(o):
 k,d=o['kind'],o['data'];db=get_db();id=o.get('id',0)
 if k=='drivers':
  if any(json.loads(x['data']).get('cpf')==d['cpf'] for x in db.execute("SELECT data FROM erp_objects WHERE module='fleet' AND kind='drivers' AND entity_id=? AND deleted=0 AND id<>?",(o['entity_id'],id))):raise ApiError('CPF já vinculado a outro motorista.',409)
 if k=='vehicles':
  asset=related(o,'asset','assets','items')
  if asset['data']['type'] not in ['Próprio','Alugado','Comodato']:raise ApiError('Tipo patrimonial incompatível com a frota.')
  if any(json.loads(x['data']).get('asset')==d['asset'] for x in db.execute("SELECT data FROM erp_objects WHERE module='fleet' AND kind='vehicles' AND entity_id=? AND deleted=0 AND id<>?",(o['entity_id'],id))):raise ApiError('Bem patrimonial já vinculado a outro veículo.',409)
  if d.get('manufacture_year') and d.get('model_year') and d['model_year']<d['manufacture_year']:raise ApiError('Ano do modelo anterior ao de fabricação.')
 if k=='vehicle_insurances' and d['end']<d['start']:raise ApiError('Fim da vigência anterior ao início.')
 if k=='tanks' and d['opening']>d['capacity']:raise ApiError('Saldo inicial superior à capacidade do tanque.')
 if k=='tank_movements':
  if d['liters']<=0:raise ApiError('Informe quantidade positiva.')
  if d['type']=='Transferência' and (not d.get('destination') or d['destination']==d['tank']):raise ApiError('Transferência exige outro tanque de destino.')
 if k in ['trips','reservations'] and d['departure' if k=='trips' else 'start']>=d['return' if k=='trips' else 'end']:raise ApiError('O término deve ser posterior ao início.')
 if k in ['trips','reservations']:
  start,end=(d['departure'],d['return']) if k=='trips' else (d['start'],d['end'])
  for other_kind,a,b in [('trips','departure','return'),('reservations','start','end')]:
   for row in db.execute("SELECT id,data,state FROM erp_objects WHERE module='fleet' AND kind=? AND deleted=0 AND id<>? AND json_extract(data,'$.vehicle')=?",(other_kind,id,d['vehicle'])):
    x=json.loads(row['data'])
    if row['state']!='Cancelado' and x[a]<end and start<x[b]:raise ApiError('Veículo já reservado ou em deslocamento no período.',409)
 if k=='service_lines':
  order=related(o,'service_order','fleet','services')
  if order['state']!='Rascunho':raise ApiError('Ordem encerrada não admite alteração de itens.',409)
  if bool(d.get('material'))!=bool(d.get('warehouse')):raise ApiError('Material de estoque exige almoxarifado, e vice-versa.')
 if k in ['accessory_schedules','agendas'] and not d.get('due_date') and not d.get('due_meter'):raise ApiError('Informe data ou leitura prevista.')
 if k=='oil_changes' and d['location_type']=='Terceiro' and (not d.get('invoice') or d['amount']<=0):raise ApiError('Troca em terceiro exige nota fiscal e valor.')
 if k=='infractions':
  if d.get('discount_amount') and d['discount_amount']>d['amount']:raise ApiError('Valor com desconto não pode superar o valor da infração.')
  related(o,'trip','fleet','trips')
 if k=='fuel_imports' and d['period_end']<d['period_start']:raise ApiError('Período de importação inválido.')

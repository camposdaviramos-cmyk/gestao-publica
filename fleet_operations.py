"""Operações transacionais da frota, combustível, custos e serviços."""
import json
from datetime import datetime
from decimal import Decimal
from flask import g
from auth import ApiError,require
from db import get_db,notify
from domain import now
from erp_core import load,related,require_draft,set_state,balance,change_balance,event,rounded,quantity
from fleet_core import vehicle_for,chronology,record,location_access,occurred

def positive(v,label):
 if v<=0:raise ApiError(label+' deve ser positivo.')
 return v

def register_trip(o,a):
 require_draft(o);d=o['data'];vehicle,departure=vehicle_for(o,d['departure']);returned=occurred(d['return']);driver=related(o,'driver','fleet','drivers');chronology(vehicle,departure,d['start_meter']);chronology(vehicle,returned,d['end_meter'])
 if d['end_meter']<d['start_meter']:raise ApiError('Leitura de retorno inferior à saída.')
 _overlap(vehicle,departure,returned,o['id'])
 warning=None
 if driver['data']['expiry']<departure[:10]:warning='CNH vencida na saída.';notify(g.user['id'],'CNH vencida',driver['name']+' estava com CNH vencida na saída '+o['code']+'.')
 record(o,vehicle,returned,'Deslocamento',d['end_meter'],driver=driver['id'],metadata={'departure':departure,'start_meter':d['start_meter'],'requester':d['requester'],'route':d['route'],'warning':warning});set_state(o,'Registrado');return {'distance':d['end_meter']-d['start_meter'],'warning':warning}

def _overlap(vehicle,start,end,ignore=0):
 for kind,a,b in [('trips','departure','return'),('reservations','start','end')]:
  for row in get_db().execute("SELECT id,data,state FROM erp_objects WHERE module='fleet' AND kind=? AND deleted=0 AND id<>? AND json_extract(data,'$.vehicle')=?",(kind,ignore,vehicle['id'])):
   d=json.loads(row['data'])
   if row['state']!='Cancelado' and d[a]<end and start<d[b]:raise ApiError('Veículo já reservado ou em deslocamento no período.',409)

def tank_stock(tank):
 db=get_db();db.execute('INSERT OR IGNORE INTO fleet_tank_stock(tank_id,quantity,value) VALUES(?,?,0)',(tank['id'],tank['data']['opening']))
 return db.execute('SELECT * FROM fleet_tank_stock WHERE tank_id=?',(tank['id'],)).fetchone()

def tank_change(source,tank,day,kind,qty,value):
 current=tank_stock(tank);new_q=current['quantity']+qty;new_v=current['value']+value
 if new_q<0 or new_v<0:raise ApiError('Saldo insuficiente no tanque '+tank['name']+'.',409)
 if new_q>tank['data']['capacity']:raise ApiError('Movimento excede a capacidade do tanque '+tank['name']+'.',409)
 get_db().execute('UPDATE fleet_tank_stock SET quantity=?,value=? WHERE tank_id=?',(new_q,new_v,tank['id']));get_db().execute('INSERT INTO fleet_tank_events(source_id,tank_id,occurred_at,kind,quantity,value,actor_id,created_at) VALUES(?,?,?,?,?,?,?,?)',(source['id'],tank['id'],day,kind,qty,value,g.user['id'],now()))
 return {'quantity':new_q,'value':new_v,'utilization':rounded(Decimal(new_q)*10000/tank['data']['capacity']) if tank['data']['capacity'] else 0}

def execute_tank_movement(o,a):
 require_draft(o);d=o['data'];day=occurred(d['date']);tank=related(o,'tank','fleet','tanks');positive(d['liters'],'Quantidade')
 if not tank['data']['active']:raise ApiError('Tanque inativo.',409)
 if d['type']=='Entrada':
  value=rounded(Decimal(d['liters'])*d['unit_price']/1000000);result=tank_change(o,tank,day,'Entrada',d['liters'],value)
 else:
  dest=related(o,'destination','fleet','tanks')
  if dest['data']['fuel']!=tank['data']['fuel']:raise ApiError('Tanques usam combustíveis diferentes.')
  current=tank_stock(tank);value=rounded(Decimal(current['value'])*d['liters']/current['quantity']) if current['quantity'] else 0;tank_change(o,tank,day,'Transferência de saída',-d['liters'],-value);result=tank_change(o,dest,day,'Transferência de entrada',d['liters'],value)
 set_state(o,'Efetivado');return result

def register_refuel(o,a):
 require_draft(o);d=o['data'];vehicle,day=vehicle_for(o,d['date']);driver=related(o,'driver','fleet','drivers');chronology(vehicle,day,d['meter']);allowed=['Gasolina','Etanol'] if vehicle['data']['fuel']=='Flex' else [vehicle['data']['fuel']]
 if d['fuel'] not in allowed:raise ApiError('Combustível incompatível com o veículo.')
 positive(d['liters'],'Litros');positive(d['unit_price'],'Preço unitário')
 if vehicle['data']['tank_capacity'] and d['liters']>vehicle['data']['tank_capacity']:raise ApiError('Volume superior à capacidade do tanque.')
 amount=rounded(Decimal(d['liters'])*d['unit_price']/1000000);utilization=None
 if d['station']=='Próprio':
  if not d.get('tank'):raise ApiError('Abastecimento próprio exige tanque de origem.')
  tank=related(o,'tank','fleet','tanks')
  if tank['data']['fuel']!=d['fuel']:raise ApiError('Combustível do tanque incompatível.')
  current=tank_stock(tank);value=rounded(Decimal(current['value'])*d['liters']/current['quantity']) if current['quantity'] else 0;result=tank_change(o,tank,day,'Abastecimento do veículo',-d['liters'],-value);utilization=result['utilization'];amount=value
 record(o,vehicle,day,'Abastecimento',d['meter'],d['liters'],amount,driver['id'],{'fuel':d['fuel'],'station':d['station'],'invoice':d.get('invoice'),'tank':d.get('tank'),'utilization':utilization});set_state(o,'Registrado');return {'amount':amount,'tank_utilization':utilization}

def post_fleet_expense(o,a):
 require_draft(o);d=o['data'];vehicle,day=vehicle_for(o,d['date']+'T00:00');account=related(o,'account','finance','accounts')
 if not account['data']['active'] or not account['data']['analytic']:raise ApiError('Conta de despesa deve ser analítica e ativa.')
 record(o,vehicle,day,'Despesa',balance(vehicle['id'],'last_meter'),amount=d['amount'],metadata={'event':d['event'],'account':account['id'],'commitment':d.get('commitment'),'document':d.get('document')});set_state(o,'Registrado');return {'amount':d['amount']}

def register_oil_change(o,a):
 require_draft(o);d=o['data'];vehicle,day=vehicle_for(o,d['date']);driver=related(o,'driver','fleet','drivers');chronology(vehicle,day,d['meter']);record(o,vehicle,day,'Troca de óleo',d['meter'],d['liters'],d['amount'],driver['id'],{'execution':d['location_type'],'invoice':d.get('invoice')});set_state(o,'Registrado');return {'amount':d['amount']}

def close_service(o,a):
 require_draft(o);d=o['data'];vehicle,day=vehicle_for(o,(d.get('closed_at') or d['date']+'T23:59'));meter=d.get('meter') or balance(vehicle['id'],'last_meter');chronology(vehicle,day,meter);lines=[];material_cost=0
 for row in get_db().execute("SELECT id FROM erp_objects WHERE module='fleet' AND kind='service_lines' AND deleted=0 AND json_extract(data,'$.service_order')=? ORDER BY id",(o['id'],)):
  line=load(row['id']);x=line['data'];cost=rounded(Decimal(x['quantity'])*x['unit_cost']/1000000);material_cost+=cost
  movement_id=None
  if x.get('material'):
   from inventory_operations import movement,units
   mov=movement(o,{'code':'OS-'+str(o['id'])+'-'+str(line['id']),'name':'Consumo na ordem '+o['code'],'warehouse':x['warehouse'],'material':x['material'],'type':'Saída','date':day[:10],'quantity':units(x['quantity'])});movement_id=mov['id']
  set_state(line,'Consumido');lines.append({'line':line['id'],'movement':movement_id,'cost':cost})
 total=d['amount']+material_cost;record(o,vehicle,day,'Ordem de serviço',meter,amount=total,driver=d.get('driver'),metadata={'type':d['type'],'plan':d.get('plan'),'invoice':d.get('invoice'),'lines':lines});set_state(o,'Concluído');return {'service_cost':d['amount'],'material_cost':material_cost,'total':total,'items':lines}

def change_plate(o,a):
 location_access(o);new=str(a.get('plate','')).strip().upper();why=str(a.get('reason','')).strip()
 if not re_plate(new) or len(why)<5:raise ApiError('Informe placa válida e justificativa.')
 if get_db().execute("SELECT 1 FROM erp_objects WHERE module='fleet' AND kind='vehicles' AND entity_id=? AND deleted=0 AND id<>? AND code=?",(o['entity_id'],o['id'],new)).fetchone():raise ApiError('Placa já cadastrada.',409)
 old=o['code'];o['data']['code']=new;get_db().execute('UPDATE erp_objects SET code=?,data=?,version=version+1,updated_at=? WHERE id=?',(new,json.dumps(o['data'],ensure_ascii=False),now(),o['id']));event(o,'Placa alterada',{'previous':old,'current':new,'reason':why,'actor_id':g.user['id'],'date':now()});return {'previous':old,'current':new,'reason':why}

def re_plate(value):
 import re
 return bool(re.fullmatch(r'[A-Z0-9-]{5,10}',value))

OPERATIONS={f.__name__:f for f in [register_trip,register_refuel,execute_tank_movement,post_fleet_expense,register_oil_change,close_service,change_plate]}

import base64
from test_erp import ERP,asset,erp,reviewer,stock
from test_system import app,admin,login,user
from db import get_db

def fleet(e,expiry='2027-12-31'):
 asset_item=asset(e);driver=e.make('fleet','drivers',cpf='11144477735',license='12345678901',category='B',expiry=expiry,relationship='Efetivo',registration='MOT-001',address='Rua de teste',phone='22999990000')
 typ=e.make('fleet','vehicle_types',locomotion='Automotora',running_gear='Pneu',consumption_measure='Quilômetro')
 vehicle=e.make('fleet','vehicles',code='ABC1D23',asset=asset_item['id'],vehicle_type=typ['id'],fuel='Gasolina',meter_type='Hodômetro',opening_meter='100',tank_capacity='50',consumption_limit='10',responsible_driver=driver['id'],renavam='12345678901',chassis='CHASSI123',manufacture_year=2024,model_year=2025,model='Sedan',color='Branco',adaptations='Rádio institucional',active=True)
 return vehicle,driver

def test_own_tank_refuel_reports_and_position(erp):
 vehicle,driver=fleet(erp);tank=erp.make('fleet','tanks',location='Garagem central',fuel='Gasolina',capacity='100',opening='20',active=True)
 entry=erp.make('fleet','tank_movements',type='Entrada',date='2026-01-01T08:00',tank=tank['id'],liters='50',unit_price='5',invoice='NF-T1');r=erp.op(entry,'execute_tank_movement')['result'];assert r['utilization']==7000
 refuel=erp.make('fleet','refuels',vehicle=vehicle['id'],driver=driver['id'],date='2026-01-02T09:00',meter='150',fuel='Gasolina',liters='10',unit_price='5',station='Próprio',tank=tank['id']);result=erp.op(refuel,'register_refuel')['result'];assert result['tank_utilization']==6000
 detail=erp.client.get('/api/erp/object/'+str(tank['id'])).json['fleet']['stock'];assert detail['quantity']==60000000
 for report in ['consumption','comparison','costs','balance','drivers','tanks']:
  response=erp.client.get('/api/fleet/reports?entity=1&exercise=2026&report='+report+'&start=2026-01-01&end=2026-12-31');assert response.status_code==200,response.json
 assert erp.client.get('/api/fleet/reports?entity=1&exercise=2026&report=consumption&format=pdf').status_code==200

def test_card_import_duplicate_and_driver_matching(erp):
 vehicle,driver=fleet(erp);raw=('plate;registration;cpf;station_cnpj;datetime;liters;unit_price;fuel;meter;invoice\nABC1D23;MOT-001;11144477735;11222333000181;2026-01-02T10:00;10;5.25;Gasolina;150;NF-CARD\n').encode()
 body={'entity':1,'exercise':2026,'content':base64.b64encode(raw).decode()};response=erp.client.post('/api/fleet/import-card',json=body,headers=erp.headers)
 assert response.status_code==201,response.json
 assert len(response.json['accepted'])==1 and not response.json['rejected']
 assert erp.client.post('/api/fleet/import-card',json=body,headers=erp.headers).status_code==409

def test_trip_expired_license_reservation_conflict_and_history(erp):
 vehicle,driver=fleet(erp,'2025-12-31');reservation=erp.make('fleet','reservations',vehicle=vehicle['id'],driver=driver['id'],start='2026-01-02T08:00',end='2026-01-02T12:00',requester='Secretaria')
 clash=erp.client.post('/api/erp/fleet/trips',json={'entity':1,'exercise':2026,'data':{'code':'TRIP-X','name':'Diligência','vehicle':vehicle['id'],'driver':driver['id'],'departure':'2026-01-02T09:00','return':'2026-01-02T10:00','start_meter':'100','end_meter':'110','requester':'Gabinete','route':'Centro'}},headers=erp.headers);assert clash.status_code==409
 trip=erp.make('fleet','trips',vehicle=vehicle['id'],driver=driver['id'],departure='2026-01-03T09:00',start_meter='100',end_meter='120',requester='Gabinete',route='Centro',**{'return':'2026-01-03T10:00'});result=erp.op(trip,'register_trip')['result'];assert 'vencida' in result['warning']
 history=erp.client.get('/api/fleet/reports?entity=1&exercise=2026&report=drivers&driver='+str(driver['id'])+'&start=2026-01-01&end=2026-12-31').json['items'];assert history[0]['event']=='Deslocamento'

def test_service_materials_expense_and_agenda_alert(erp,app):
 vehicle,driver=fleet(erp);warehouse_a,warehouse_b,material,movement=stock(erp);entry=movement('Entrada','10',expiry='2027-01-01');erp.op(entry,'execute_stock')
 service=erp.make('fleet','services',vehicle=vehicle['id'],date='2026-02-01',meter='130',amount='20',type='Preventiva',opened_at='2026-02-01T08:00',closed_at='2026-02-01T17:00',driver=driver['id'],location='Oficina própria')
 erp.make('fleet','service_lines',service_order=service['id'],material=material['id'],warehouse=warehouse_a['id'],quantity='2',unit_cost='3')
 result=erp.op(service,'close_service')['result'];assert result['material_cost']==600 and result['total']==2600
 rows=erp.client.get('/api/erp/stock?entity=1&exercise=2026').json['items'];assert rows[0]['quantity']==8000000
 account=erp.make('finance','accounts',nature='Devedora',active=True,analytic=True);expense=erp.make('fleet','expenses',vehicle=vehicle['id'],date='2026-02-02',event='Licenciamento anual',account=account['id'],amount='100');erp.op(expense,'post_fleet_expense')
 agenda=erp.make('fleet','agendas',vehicle=vehicle['id'],type='Imposto',due_date='2026-01-01',notes='IPVA')
 erp.client.get('/api/notifications')
 with app.app_context():assert get_db().execute("SELECT 1 FROM notifications WHERE title='Compromisso vencido da frota'").fetchone()

def test_location_permissions_for_non_admin(app,admin,erp):
 vehicle,driver=fleet(erp);uid=user(admin,email='fleet@example.test',group=2,permissions={'fleet':['read','write']});erp.client.put('/api/erp/access/'+str(uid),json={'entities':[1]},headers=erp.headers)
 c=app.test_client();limited=ERP((c,login(c,'fleet@example.test')));refuel=limited.make('fleet','refuels',vehicle=vehicle['id'],driver=driver['id'],date='2026-01-02T10:00',meter='110',fuel='Gasolina',liters='5',unit_price='5',station='Terceiro');limited.op(refuel,'register_refuel',403)
 location=erp.client.get('/api/erp/object/'+str(vehicle['data']['asset'])).json['item']['data']['location'];response=erp.client.put('/api/fleet/locations/permissions',json={'entity':1,'items':[{'user_id':uid,'location':location,'allowed':True}]},headers=erp.headers);assert response.status_code==200
 limited.op(refuel,'register_refuel')

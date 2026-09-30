import pytest
from test_system import app,admin,login,user
from test_erp import ERP,erp,reviewer,finance,asset

def process(e,**extra):
 return e.make('procurement','processes',modality='Pregão',judgment='Menor preço',legal_basis='Ato registrado para teste',publication='2026-01-01',opening='2026-01-05',business_days=2,estimated='1000',technical_opinion='Parecer técnico de teste',legal_opinion='Parecer jurídico de teste',**extra)

def test_procurement_phases_and_awarded_supplier(erp,reviewer):
 p=process(erp);supplier=erp.make('procurement','suppliers',document='52998224725');other=erp.make('procurement','suppliers',document='11144477735')
 item=erp.make('procurement','items',process=p['id'],unit='UN',quantity='10',unit_price='100')
 bid=erp.make('procurement','proposals',item=item['id'],supplier=supplier['id'],unit_price='90',qualified=True)
 for phase in ['Edital','Divulgado','Julgamento','Habilitação']:
  assert erp.op(p,'advance_process',reason='Fase documentada e conferida')['item']['state']==phase
 erp.op(p,'advance_process',403,reason='Solicitação de adjudicação');reviewer.op(p,'advance_process',reason='Autorizada após conferência')
 reviewer.op(p,'advance_process',400,reason='Homologação antes de adjudicar')
 reviewer.op(bid,'award_proposal',reason='Melhor proposta habilitada');reviewer.op(p,'advance_process',reason='Homologação autorizada')
 contract=erp.make('procurement','contracts',process=p['id'],supplier=other['id'],start='2026-02-01',end='2026-12-31',amount='900',manager='Gestor',inspector='Fiscal');reviewer.op(contract,'activate_contract',400)
 erp.edit(contract,supplier=supplier['id']);reviewer.op(contract,'activate_contract');assert erp.get(contract)['state']=='Vigente'
 amendment=erp.make('procurement','amendments',contract=contract['id'],type='Supressão',amount='901',justification='Redução de teste',legal_opinion='Parecer');reviewer.op(amendment,'apply_amendment',400)

def test_inverted_phases_and_supplier_block(erp,reviewer):
 p=process(erp,inverted=True)
 for phase in ['Edital','Divulgado','Habilitação','Julgamento']:
  assert erp.op(p,'advance_process',reason='Avanço de fase fundamentado')['item']['state']==phase
 f,dr,cr,s,a,b=finance(erp);erp.edit(s,blocked_from='2026-01-01',blocked_until='2026-12-31',block_reason='Impedimento de teste')
 commitment=erp.make('finance','commitments',appropriation=a['id'],supplier=s['id'],date='2026-02-01',amount='10',type='Ordinário');erp.op(commitment,'commit',409)

def test_bi_posted_facts_and_permissions(erp,app,admin):
 f,dr,cr,s,a,b=finance(erp)
 draft=erp.make('finance','receipts',date='2026-03-02',bank=b['id'],fund=f['id'],revenue_nature='Receita de teste',amount='100',deduction='10')
 before=erp.client.get('/api/erp/insights?entity=1&exercise=2026').json['indicators']['finance'];assert before['received']==0 and before['bank']==100000
 erp.op(draft,'receive');after=erp.client.get('/api/erp/insights?entity=1&exercise=2026').json['indicators']['finance'];assert after['received']==9000 and after['bank']==109000 and after['monthly'][2]['received']==9000
 uid=user(admin,group=2,permissions={'bi':['read'],'finance':[]});erp.client.put('/api/erp/access/'+str(uid),json={'entities':[1]},headers=erp.headers);c=app.test_client();login(c,'second@example.test')
 assert 'finance' not in c.get('/api/erp/insights?entity=1&exercise=2026').json['indicators']

def test_fleet_fuel_and_plate_history(erp):
 a=asset(erp);driver=erp.make('fleet','drivers',cpf='11144477735',license='123456789',category='B',expiry='2027-01-01',relationship='Efetivo',registration='MOT-001')
 vehicle_type=erp.make('fleet','vehicle_types',locomotion='Automotora',running_gear='Pneu',consumption_measure='Quilômetro')
 vehicle=erp.make('fleet','vehicles',code='ABC1D23',asset=a['id'],vehicle_type=vehicle_type['id'],fuel='Gasolina',meter_type='Hodômetro',opening_meter='100',tank_capacity='50',consumption_limit='10',active=True)
 wrong=erp.make('fleet','refuels',vehicle=vehicle['id'],driver=driver['id'],date='2026-01-01T12:00',meter='110',fuel='Diesel',liters='20',unit_price='5',station='Terceiro');erp.op(wrong,'register_refuel',400)
 erp.edit(wrong,fuel='Gasolina');erp.op(wrong,'register_refuel');assert erp.get(vehicle)['balances']['cost']==10000
 erp.op(vehicle,'change_plate',plate='XYZ1A23',reason='Alteração do registro oficial');assert erp.get(vehicle)['code']=='XYZ1A23'
 details=erp.client.get('/api/erp/object/'+str(vehicle['id'])).json;event=next(e for e in details['events'] if e['operation']=='change_plate');assert event['payload']['previous']=='ABC1D23'
 erp.edit(vehicle,blocked_through='2026-02-28');old=erp.make('fleet','services',vehicle=vehicle['id'],date='2026-02-01',meter='120',amount='20',type='Preventiva');erp.op(old,'close_service',409)

def test_benefit_interval_and_duplicate_scheduling(erp,reviewer):
 p=erp.make('social','persons',cpf='52998224725',birth='1990-01-01',address='Rua de teste')
 benefit=erp.make('social','benefits',amount='100',interval_days=30,capacity=10)
 grant=erp.make('social','concessions',person=p['id'],benefit=benefit['id'],date='2026-01-01',professional='Servidor');reviewer.op(grant,'grant_benefit')
 duplicate=erp.make('social','concessions',person=p['id'],benefit=benefit['id'],date='2026-01-15',professional='Servidor');reviewer.op(duplicate,'grant_benefit',409)
 erp.make('social','appointments',person=p['id'],professional='Equipe',unit='CRAS',start='2026-01-02T09:00',end='2026-01-02T10:00')
 response=erp.client.post('/api/erp/social/appointments',json={'entity':1,'exercise':2026,'data':{'code':'DUP','name':'Duplicidade','person':p['id'],'professional':'Equipe','unit':'CRAS','start':'2026-01-02T09:30','end':'2026-01-02T10:30'}},headers=erp.headers);assert response.status_code==409

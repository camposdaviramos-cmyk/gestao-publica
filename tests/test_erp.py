import base64,json,sqlite3
import pytest
from test_system import app,admin,login,user
from db import get_db
from erp_catalog import CATALOG

class ERP:
 def __init__(self,session,entity=1,exercise=2026):self.client,self.headers=session;self.entity=entity;self.exercise=exercise;self.n=0
 def make(self,module,kind,**values):
  self.n+=1;data={'code':f'{module}-{kind}-{self.n}','name':f'Registro de teste {self.n}',**values}
  response=self.client.post(f'/api/erp/{module}/{kind}',json={'entity':self.entity,'exercise':self.exercise,'data':data},headers=self.headers)
  assert response.status_code==201,(module,kind,response.json)
  return response.json['item']
 def get(self,obj):return self.client.get('/api/erp/object/'+str(obj['id'])).json['item']
 def op(self,obj,operation,status=200,**args):
  latest=self.get(obj);r=self.client.post(f"/api/erp/object/{obj['id']}/operate",json={'version':latest['version'],'operation':operation,'args':args},headers=self.headers)
  assert r.status_code==status,r.json
  return r.json
 def edit(self,obj,status=200,**values):
  latest=self.get(obj);r=self.client.put('/api/erp/object/'+str(obj['id']),json={'version':latest['version'],'data':{**latest['data'],**values}},headers=self.headers)
  assert r.status_code==status,r.json
  return r

@pytest.fixture
def erp(admin):return ERP(admin)

@pytest.fixture
def reviewer(app,admin):
 user(admin);c=app.test_client();return ERP((c,login(c,'second@example.test')))

def finance(e):
 fund=e.make('finance','funds')
 debit=e.make('finance','accounts',nature='Devedora',active=True,analytic=True)
 credit=e.make('finance','accounts',nature='Credora',active=True,analytic=True)
 supplier=e.make('procurement','suppliers',document='52998224725')
 appropriation=e.make('finance','appropriations',fund=fund['id'],expense_nature='339030',initial='1000')
 bank=e.make('finance','bank_accounts',bank_code='001',branch='1',number='12',fund=fund['id'],ledger_account=debit['id'],opening='1000')
 return fund,debit,credit,supplier,appropriation,bank

def test_execution_balances_transactions_and_versions(erp):
 f,dr,cr,s,ap,b=finance(erp)
 def commitment(amount):return erp.make('finance','commitments',appropriation=ap['id'],supplier=s['id'],date='2026-01-02',amount=amount,type='Ordinário')
 c=commitment('700');erp.op(c,'commit');erp.op(c,'commit',409)
 denied=commitment('301');erp.op(denied,'commit',409)
 assert erp.get(ap)['balances']['committed']==70000
 settlement=erp.make('finance','settlements',commitment=c['id'],date='2026-01-03',invoice='NF1',amount='701');erp.op(settlement,'settle',409)
 erp.edit(settlement,amount='700');erp.op(settlement,'settle')
 payment=erp.make('finance','payments',settlement=settlement['id'],bank=b['id'],date='2026-01-04',amount='600');erp.op(payment,'pay')
 payment2=erp.make('finance','payments',settlement=settlement['id'],bank=b['id'],date='2026-01-04',amount='101');erp.op(payment2,'pay',409)
 assert erp.get(b)['balances']['net']==-60000
 erp.op(c,'cancel_commitment',409,reason='Anulação de teste')
 assert erp.client.put('/api/erp/object/'+str(ap['id']),json={'version':1,'data':ap['data']},headers=erp.headers).status_code in [200,409]
 erp.edit(payment,status=409,amount='1')

def test_journal_reversal_period_lock_and_history(app,erp):
 f,dr,cr,s,ap,b=finance(erp)
 j=erp.make('finance','journals',date='2026-01-01',debit=dr['id'],credit=cr['id'],fund=f['id'],amount='100.23')
 erp.op(j,'post_journal');ledger=erp.client.get('/api/erp/ledger?entity=1&exercise=2026').json
 assert ledger['debit']==ledger['credit']==10023
 erp.op(j,'reverse_journal',date='2026-01-02',reason='Ajuste identificado na conferência')
 ledger=erp.client.get('/api/erp/ledger?entity=1&exercise=2026').json
 assert ledger['debit']==ledger['credit']==20046
 assert all(r['balance']==0 for r in ledger['items'])
 lock=erp.make('finance','locks',through='2026-01-31');erp.op(lock,'lock_period')
 j2=erp.make('finance','journals',date='2026-01-05',debit=dr['id'],credit=cr['id'],fund=f['id'],amount='1');erp.op(j2,'post_journal',409)
 with app.app_context():
  with pytest.raises(sqlite3.IntegrityError):get_db().execute('DELETE FROM erp_events')

def test_entity_boundary_and_module_permissions(app,admin,erp):
 obj=erp.make('finance','funds');uid=user(admin,group=2,permissions={'finance':['read','write'],'entities':[]})
 c=app.test_client();h=login(c,'second@example.test')
 assert c.get('/api/erp/finance/funds?entity=1&exercise=2026').status_code==403
 erp.client.put('/api/erp/access/'+str(uid),json={'entities':[1]},headers=erp.headers)
 h=login(c,'second@example.test');assert c.get('/api/erp/object/'+str(obj['id'])).status_code==200
 r=erp.client.post('/api/erp/entities',json={'code':'CAMARA','name':'Câmara Municipal'},headers=erp.headers);assert r.status_code==201
 foreign=ERP((erp.client,erp.headers),entity=r.json['id']).make('finance','funds')
 assert c.get('/api/erp/object/'+str(foreign['id'])).status_code==403
 assert c.get('/api/erp/finance/funds/export?entity=2&exercise=2026').status_code==403
 response=erp.client.post('/api/erp/finance/appropriations',json={'entity':1,'exercise':2026,'data':{'code':'X','name':'Outro fundo','fund':foreign['id'],'expense_nature':'33','initial':'1'}},headers=erp.headers)
 assert response.status_code==400

def stock_accounting(e):
 email='stockreview@example.test'
 user((e.client,e.headers),email=email)
 c=e.client.application.test_client();checker=ERP((c,login(c,email)),e.entity,e.exercise)
 debit=e.make('finance','accounts',nature='Devedora',active=True,analytic=True)
 credit=e.make('finance','accounts',nature='Credora',active=True,analytic=True)
 for fact in ['Entrada','Saída','Trânsito de saída','Trânsito de entrada','Devolução','Ganho de inventário','Perda de inventário','Baixa de obsoleto']:
  rule=e.make('inventory','accounting_rules',fact=fact,debit=debit['id'],credit=credit['id'],legal_basis='Configuração contábil exclusiva de testes')
  checker.op(rule,'approve_stock_accounting')
 return debit,credit

def stock(e):
 stock_accounting(e)
 a=e.make('inventory','warehouses',location='Sede',owner='Servidor')
 b=e.make('inventory','warehouses',location='Unidade',owner='Servidor')
 m=e.make('inventory','materials',unit='UN',minimum='2',maximum='100',expiry_control=True)
 def movement(typ,qty,**kw):return e.make('inventory','movements',warehouse=a['id'],material=m['id'],type=typ,date='2026-01-01',quantity=qty,unit_price='2.33',**kw)
 return a,b,m,movement

def test_stock_transfer_cost_expiry_and_duplicate_receipt(erp):
 a,b,m,mov=stock(erp);invalid=mov('Entrada','10',expiry='2025-12-31');erp.op(invalid,'execute_stock',400)
 f,dr,cr,s,ap,bank=finance(erp);commitment=erp.make('finance','commitments',appropriation=ap['id'],supplier=s['id'],date='2026-01-01',amount='100',type='Ordinário');erp.op(commitment,'commit')
 c=erp.client.application.test_client();checker=ERP((c,login(c,'stockreview@example.test')))
 entry=mov('Entrada','10',expiry='2027-01-01',invoice='NF001',supplier=s['id'],commitment=commitment['id']);checker.op(entry,'execute_stock');assert erp.get(commitment)['balances']['settled']==2330
 duplicate=mov('Entrada','10',expiry='2027-01-01',invoice='NF001',supplier=s['id'],commitment=commitment['id']);checker.op(duplicate,'execute_stock',409)
 out=mov('Saída','11');erp.op(out,'execute_stock',409)
 transfer=mov('Transferência','3',destination=b['id']);erp.op(transfer,'execute_stock')
 rows=erp.client.get('/api/erp/stock?entity=1&exercise=2026').json['items'];assert len(rows)==1 and rows[0]['quantity']==7000000 and rows[0]['value']==1631
 erp.op(transfer,'receive_transfer');erp.op(transfer,'receive_transfer',409)
 rows=erp.client.get('/api/erp/stock?entity=1&exercise=2026').json['items'];assert sum(r['quantity'] for r in rows)==10000000 and sum(r['value'] for r in rows)==2330
 out=mov('Saída','1');erp.edit(a,blocked=True);erp.op(out,'execute_stock',409)
 response=erp.client.post('/api/erp/inventory/movements',json={'entity':1,'exercise':2026,'data':{**out['data'],'code':'BLOCKED'}},headers=erp.headers);assert response.status_code==409

def asset(e,proration=None):
 f,dr,cr,s,ap,b=finance(e)
 cls=e.make('assets','classes',asset_account=dr['id'],depreciation_account=cr['id'],useful_months=3,residual_percent='0',**({'proration':proration} if proration else {}))
 responsible=e.make('assets','responsibles',cpf='52998224725',admission='Nomeação de cargo efetivo',relationship='Cargo efetivo',active=True)
 location=e.make('assets','locations',address='Sede administrativa',responsible=responsible['id'],active=True)
 commission=e.make('assets','commissions',type='Recebimento',created='2026-01-01',legal_basis='Portaria municipal de recebimento')
 e.make('assets','commission_members',commission=commission['id'],responsible=responsible['id'],role='Presidente')
 user((e.client,e.headers),email='assetreview@example.test');c=e.client.application.test_client();checker=ERP((c,login(c,'assetreview@example.test')))
 checker.op(commission,'seal_asset_commission')
 item=e.make('assets','items',**{'class':cls['id']},type='Próprio',location='Sede',owner='Responsável',condition='Bom',date='2026-01-01',amount='100',method='Quotas constantes',start='2026-01-01',responsible=responsible['id'],location_ref=location['id'],receipt_commission=commission['id'],ingress_type='Doação',capitalize=False,situation='Em uso')
 checker.op(item,'activate_asset');return item

def test_depreciation_residual_rounding_and_inventory_freeze(erp,reviewer):
 a=asset(erp);erp.op(a,'depreciate',period='2026-01');erp.op(a,'depreciate',409,period='2026-01')
 responsible=erp.make('assets','responsibles',cpf='11144477735',admission='Nomeação de cargo efetivo',relationship='Cargo efetivo',active=True)
 commission=erp.make('assets','commissions',type='Inventário',created='2026-01-01',legal_basis='Portaria municipal de inventário')
 erp.make('assets','commission_members',commission=commission['id'],responsible=responsible['id'],role='Presidente');reviewer.op(commission,'seal_asset_commission')
 inventory=erp.make('assets','inventories',location=erp.get(a)['data']['location'],date='2026-02-01',commission='Comissão oficial',commission_ref=commission['id'],type='Anual');reviewer.op(inventory,'open_inventory')
 erp.op(a,'depreciate',409,period='2026-02');reviewer.op(a,'transfer_asset',409,date='2026-02-01',location='Novo',owner='Responsável',reason='Transferência autorizada')
 line=erp.client.get('/api/erp/assets/inventory_items?entity=1&exercise=2026').json['items'][0];erp.edit(line,conformity='Conferência física sem divergência')
 third_client=erp.client.application.test_client();third=ERP((third_client,login(third_client,'assetreview@example.test')));third.op(line,'confirm_inventory_asset')
 reviewer.op(inventory,'close_inventory',reason='Conferência finalizada');erp.op(a,'depreciate',period='2026-02');erp.op(a,'depreciate',period='2026-03')
 assert erp.get(a)['balances']['depreciated']==10000
 erp.op(a,'depreciate',409,period='2026-04');erp.edit(a,409,amount='500')
 args={'date':'2026-04-01','reason':'Baixa autorizada','type':'Inservibilidade','legal_basis':'Ato administrativo de baixa'}
 erp.op(a,'writeoff_asset',403,**args);reviewer.op(a,'writeoff_asset',**args)

def test_obligation_recurrence_clamps_month_and_preserves_closing(erp):
 o=erp.make('control','obligations',description='Obrigação mensal',legislation='Ato de teste',level='Municipal',owner='Controlador',first_due='2026-01-31',interval_months=1,occurrences=3)
 result=erp.op(o,'generate_occurrences');ids=result['result']['occurrences']
 dates=[erp.client.get('/api/erp/object/'+str(i)).json['item']['data']['due_date'] for i in ids]
 assert dates==['2026-01-31','2026-02-28','2026-03-31']
 occurrence={'id':ids[0]};erp.op(occurrence,'close_occurrence',reason='Entregue dentro do prazo');erp.op(occurrence,'reopen_occurrence',reason='Revisão solicitada pela chefia')
 erp.op(o,'generate_occurrences',409)

def test_payroll_approved_tables_margin_and_immutable_memory(erp,reviewer):
 pos=erp.make('people','positions',vacancies=1,salary='1000',hours='40')
 employee=erp.make('people','employees',cpf='52998224725',position=pos['id'],department='Sede',admission='2026-01-01',regime='RPPS',salary='1000',active=True)
 rules=erp.make('people','rules',period='2026-01',pension_rate='10',employer_rate='20',supplementary_rate='2',margin='30',dependent_deduction='0',legal_basis='Parâmetros fictícios exclusivos deste teste')
 band=erp.make('people','tax_bands',rules=rules['id'],lower='0',upper='0',rate='0',deduction='0')
 erp.op(rules,'approve_rules',403);reviewer.op(rules,'approve_rules')
 erp.edit(band,409,rate='10')
 response=erp.client.post('/api/erp/people/tax_bands',json={'entity':1,'exercise':2026,'data':{'code':'EXTRA','name':'Faixa indevida','rules':rules['id'],'lower':'0','rate':'0'}},headers=erp.headers);assert response.status_code==409
 for amount,priority in [('200',1),('100',2)]:erp.make('people','events',employee=employee['id'],period='2026-01',type='Consignação',amount=amount,priority=priority)
 run=erp.make('people','runs',period='2026-01',rules=rules['id']);erp.op(run,'calculate_payroll');erp.op(run,'approve_payroll',403);reviewer.op(run,'approve_payroll')
 line=erp.client.get('/api/erp/object/'+str(run['id'])).json['payroll'][0]
 assert (line['gross'],line['pension'],line['consigned'],line['net'],line['employer'])==(100000,10000,20000,70000,22000)
 memory=json.loads(line['memory']);assert memory['rejected_consignments'][0]['amount']==10000
 erp.edit(employee,salary='2000');line2=erp.client.get('/api/erp/object/'+str(run['id'])).json['payroll'][0];assert line2['memory']==line['memory']
 duplicate=erp.make('people','runs',period='2026-01',rules=rules['id']);erp.op(duplicate,'calculate_payroll',409)

def test_social_confidentiality_in_details_list_export_and_bi(app,admin,erp):
 person=erp.make('social','persons',cpf='52998224725',birth='1990-01-01',mother='Nome da mãe',address='Rua de teste')
 visit=erp.make('social','visits',person=person['id'],date='2026-01-01',professional='Técnica',specialty='Assistência',unit='CRAS',notes='Informação sigilosa de teste',confidential=True)
 uid=user(admin,group=2,permissions={'social':['read','write'],'social_confidential':[],'bi':['read']})
 erp.client.put('/api/erp/access/'+str(uid),json={'entities':[1]},headers=erp.headers);c=app.test_client();login(c,'second@example.test')
 assert c.get('/api/erp/object/'+str(visit['id'])).status_code==403
 assert c.get('/api/erp/social/visits?entity=1&exercise=2026').json['total']==0
 assert 'Informação sigilosa de teste' not in c.get('/api/erp/social/visits/export?entity=1&exercise=2026').text
 assert not any(r['kind']=='visits' for r in c.get('/api/erp/insights?entity=1&exercise=2026').json['items'])

def test_works_sequential_measurement_dual_approval_and_retention(erp,reviewer):
 supplier=erp.make('procurement','suppliers',document='52998224725')
 p=erp.make('works','projects',supplier=supplier['id'],engineer='Engenheiro',registration='CREA de teste',address='Obra teste',start='2026-01-01',end='2026-06-01',retention_days=30,completed_date='2026-06-01')
 item=erp.make('works','items',project=p['id'],unit='M2',quantity='10',unit_price='100',bdi='20',discount='0',start='2026-01-01',end='2026-06-01')
 measurement=erp.make('works','measurements',project=p['id'],item=item['id'],start='2026-01-01',end='2026-01-31',quantity='10');erp.op(measurement,'submit_measurement',400)
 diary=erp.make('works','diaries',project=p['id'],date='2026-01-02',weather='Bom',worked='Integral',activities='Execução da etapa',equipment='Máquina',workforce='Equipe');erp.op(diary,'approve_diary',403);reviewer.op(diary,'approve_diary')
 erp.op(measurement,'submit_measurement');assert erp.get(measurement)['balances']['measured_amount']==120000
 reviewer.op(measurement,'approve_measurement')
 excess=erp.make('works','measurements',project=p['id'],item=item['id'],start='2026-02-01',end='2026-02-28',quantity='1');erp.op(excess,'submit_measurement',409)
 pay=erp.make('works','payments',measurement=measurement['id'],date='2026-02-01',amount='1000',type='Medição');erp.op(pay,'pay_measurement')
 retained=erp.make('works','payments',measurement=measurement['id'],date='2026-06-15',amount='200',type='Retenção');erp.op(retained,'pay_measurement',400)
 erp.edit(retained,date='2026-07-01');erp.op(retained,'pay_measurement');assert erp.get(measurement)['balances']['paid']==120000

def test_protected_attachment_and_export_signature(app,erp):
 o=erp.make('finance','funds',name='=Comando indevido');raw=b'%PDF-1.4\nconteudo de teste'
 body={'name':'documento.pdf','content':base64.b64encode(raw).decode()};url='/api/erp/object/'+str(o['id'])+'/attachments'
 r=erp.client.post(url,json=body,headers=erp.headers);assert r.status_code==201
 assert erp.client.post(url,json=body,headers=erp.headers).status_code==409
 assert erp.client.get('/api/erp/attachment/'+str(r.json['id'])).data==raw
 assert app.test_client().get('/api/erp/attachment/'+str(r.json['id'])).status_code==401
 with app.app_context():assert raw not in bytes(get_db().execute('SELECT encrypted FROM erp_attachments').fetchone()[0])
 export=erp.client.get('/api/erp/finance/funds/export?entity=1&exercise=2026');assert "'=Comando" in export.data.decode('utf-8-sig')
 with app.app_context():get_db().execute("INSERT OR REPLACE INTO settings(key,value) VALUES('signature_required','true')");get_db().commit()
 assert erp.client.get('/api/erp/finance/funds/export?entity=1&exercise=2026&format=pdf').status_code==409

def test_annex_complete_catalog_unique_items(erp):
 d=erp.client.get('/api/erp/annex');assert d.status_code==200
 assert len(d.json['items'])==1314
 assert len({x['key'] for x in d.json['items']})==1314
 assert all(x['text'] and x['coverage'] and x['before'] for x in d.json['items'])

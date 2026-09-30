import json,sqlite3
import pytest
from test_system import app,admin,user,login
from test_erp import ERP,erp,reviewer,stock,finance
from test_erp_flows import process
from db import get_db


def requisition(e,w,m,quantity='8',kind='Material'):
 dept=e.make('inventory','departments',group='Secretarias',subgroup='Saúde',owner='Responsável',active=True)
 center=e.make('inventory','cost_centers',department=dept['id'],owner='Chefia')
 req=e.make('inventory','requisitions',type=kind,department=dept['id'],cost_center=center['id'],warehouse=w['id'],date='2026-01-02',justification='Necessidade da unidade')
 line=e.make('inventory','requisition_items',requisition=req['id'],material=m['id'],quantity=quantity,unit_price='2.33')
 return dept,center,req,line

def report(e,kind,**kw):
 r=e.client.get('/api/inventory/reports',query_string={'entity':1,'exercise':2026,'report':kind,**kw});assert r.status_code==200,r.json;return r.json

def supply(e,checker):
 a,b,m,mov=stock(e);f,dr,cr,s,ap,bank=finance(e);p=process(e)
 pi=e.make('procurement','items',process=p['id'],unit='UN',quantity='10',unit_price='2.33')
 bid=e.make('procurement','proposals',item=pi['id'],supplier=s['id'],unit_price='2.33',qualified=True)
 for _ in range(4):e.op(p,'advance_process',reason='Fase conferida')
 checker.op(p,'advance_process',reason='Adjudicação autorizada');checker.op(bid,'award_proposal',reason='Proposta habilitada');checker.op(p,'advance_process',reason='Homologação autorizada')
 c=e.make('finance','commitments',appropriation=ap['id'],supplier=s['id'],date='2026-01-02',amount='100',type='Ordinário');e.op(c,'commit')
 dept,center,req,line=requisition(e,a,m,'10','Compra');checker.op(req,'approve_requisition')
 auth=e.make('inventory','authorizations',requisition=req['id'],process=p['id'],supplier=s['id'],commitment=c['id'],warehouse=a['id'],date='2026-01-06',research_number='PESQ-1',research_date='2026-01-01')
 ai=e.make('inventory','authorization_items',authorization=auth['id'],procurement_item=pi['id'],material=m['id'],quantity='10',unit_price='2.33');checker.op(auth,'approve_supply_authorization')
 return a,m,s,c,req,auth,ai

def invoice(e,s,auth,number='123'):
 return e.make('inventory','invoices',supplier=s['id'],number=number,series='1',model='55',type='Material',authorization=auth['id'],date='2026-01-07',issued_at='2026-01-06')

def test_delivery_return_cancel_quota_and_reports(app,erp,reviewer):
 a,b,m,mov=stock(erp);entry=mov('Implantação','10',expiry='2027-01-01');erp.op(entry,'execute_stock')
 dept,center,req,line=requisition(erp,a,m)
 quota=erp.make('inventory','quotas',cost_center=center['id'],material=m['id'],period='2026-01',quantity='5',amount='10')
 erp.op(req,'approve_requisition',403);result=reviewer.op(req,'approve_requisition');assert result['result']['alerts'][0]['quantity_requested']==8000000
 erp.edit(line,409,quantity='9')
 erp.op(line,'deliver_requisition',quantity='3',date='2026-01-03');erp.op(line,'deliver_requisition',409,quantity='6',date='2026-01-03')
 details=erp.client.get('/api/erp/object/'+str(line['id'])).json;delivery=details['inventory']['deliveries'][0];assert delivery['value']==699
 erp.op(line,'return_requisition',quantity='1',delivery=delivery['id'],date='2026-01-04',expiry='2027-01-01');erp.op(line,'return_requisition',409,quantity='3',delivery=delivery['id'],date='2026-01-04',expiry='2027-01-01')
 erp.op(line,'cancel_requisition_balance',reason='Saldo não necessário');assert erp.get(req)['state']=='Atendido';assert erp.get(line)['balances']['cancelled']==5000000
 consumption=report(erp,'consumption')['items'];assert consumption[0]['quantity']==2000000 and consumption[0]['value']==466 and consumption[0]['abc']=='A'
 monthly=report(erp,'monthly')['items'];assert monthly[0]['closing_quantity']==8000000 and monthly[0]['closing_value']==1864
 ledger=report(erp,'movements')['items'];assert len(ledger)==3 and all(x['rule_id'] for x in ledger)
 assert report(erp,'consumption',abc='C')['items']==[]
 with app.app_context():
  db=get_db();assert db.execute('SELECT SUM(debit)-SUM(credit) FROM erp_ledger').fetchone()[0]==0
  with pytest.raises(sqlite3.IntegrityError):db.execute('DELETE FROM inventory_fulfillments')
 for fmt in ['csv','pdf']:
  response=erp.client.get('/api/inventory/reports',query_string={'entity':1,'exercise':2026,'report':'monthly','format':fmt});assert response.status_code==200 and len(response.data)>100

def test_missing_accounting_rolls_back_stock(app,erp):
 w=erp.make('inventory','warehouses',location='Sede',owner='Servidor');m=erp.make('inventory','materials',unit='UN');o=erp.make('inventory','movements',warehouse=w['id'],material=m['id'],type='Implantação',date='2026-01-01',quantity='5',unit_price='7')
 erp.op(o,'execute_stock',409);assert erp.get(o)['state']=='Rascunho'
 with app.app_context():
  db=get_db();assert db.execute('SELECT COUNT(*) FROM erp_stock').fetchone()[0]==0;assert db.execute('SELECT COUNT(*) FROM erp_stock_ledger').fetchone()[0]==0;assert db.execute('SELECT COUNT(*) FROM erp_ledger').fetchone()[0]==0

def test_authorization_partial_invoice_simultaneous_settlement(app,erp,reviewer):
 w,m,s,c,req,auth,ai=supply(erp,reviewer)
 balances=report(erp,'balances',warehouse=w['id'])['items'];assert balances[0]['virtual']==10000000 and balances[0]['incoming']==10000000 and balances[0]['in_procurement']==0
 inv=invoice(erp,s,auth);result=erp.op(inv,'suggest_authorized_items');line={'id':result['result']['created_items'][0]};erp.edit(line,quantity='4',expiry='2027-01-01');erp.op(inv,'post_inventory_invoice',403)
 result=reviewer.op(inv,'post_inventory_invoice')['result'];assert result['amount']==932 and erp.get(c)['balances']['settled']==932;assert erp.get(auth)['state']=='Parcialmente recebido'
 erp.edit(line,409,quantity='5');reviewer.op(inv,'post_inventory_invoice',409)
 duplicate=erp.client.post('/api/erp/inventory/invoices',json={'entity':1,'exercise':2026,'data':{**erp.get(inv)['data'],'code':'DUP'}} ,headers=erp.headers);assert duplicate.status_code==409
 inv2=invoice(erp,s,auth,'124');result=erp.op(inv2,'suggest_authorized_items');line2={'id':result['result']['created_items'][0]};assert erp.get(line2)['data']['quantity']=='6';erp.edit(line2,quantity='7',expiry='2027-01-01');reviewer.op(inv2,'post_inventory_invoice',409)
 assert erp.get(c)['balances']['settled']==932
 with app.app_context():assert get_db().execute('SELECT COUNT(*) FROM inventory_invoice_postings').fetchone()[0]==1
 erp.edit(line2,quantity='6');reviewer.op(inv2,'post_inventory_invoice');assert erp.get(c)['balances']['settled']==2330 and erp.get(auth)['state']=='Recebido'
 dossier=erp.client.get('/api/inventory/dossier/'+str(req['id']));assert dossier.status_code==200 and len(dossier.json['chains'][0]['phases'])==6 and len(dossier.json['chains'][0]['invoices'])==2

def test_commission_and_obsolete_writeoff(erp,reviewer):
 w,b,m,mov=stock(erp);entry=mov('Implantação','10',expiry='2027-01-01');erp.op(entry,'execute_stock')
 count=erp.make('inventory','counts',warehouse=w['id'],material=m['id'],quantity='9',date='2026-01-03',ordinance='1/2026',commission='Comissão de teste');reviewer.op(count,'adjust_stock',400)
 commission=erp.make('inventory','commissions',publication='2026-01-01',start='2026-01-01',end='2026-12-31');reviewer.op(commission,'seal_stock_commission',400)
 member=erp.make('inventory','commission_members',commission=commission['id'],cpf='52998224725',position='Presidente');reviewer.op(commission,'seal_stock_commission');erp.edit(member,409,position='Membro')
 erp.edit(count,commission_order=commission['id']);reviewer.op(count,'adjust_stock');erp.edit(m,obsolete=True)
 out=mov('Saída','1');erp.op(out,'execute_stock',409);writeoff=mov('Baixa de obsoleto','9');erp.edit(writeoff,date='2026-01-04');erp.op(writeoff,'writeoff_obsolete',403,reason='Baixa autorizada');reviewer.op(writeoff,'writeoff_obsolete',reason='Baixa autorizada');assert report(erp,'balances',warehouse=w['id'])['items'][0]['quantity']==0

def test_individual_warehouse_and_department_permissions(app,admin,erp,reviewer):
 w,b,m,mov=stock(erp);dept,center,req,line=requisition(erp,w,m);uid=user(admin,email='warehouse@example.test',group=2,permissions={'inventory':['read','write','approve']})
 erp.client.put('/api/erp/access/'+str(uid),json={'entities':[1]},headers=erp.headers)
 c=app.test_client();h=login(c,'warehouse@example.test');employee=ERP((c,h));latest=erp.get(w)
 response=erp.client.put(f'/api/inventory/units/{w["id"]}/permissions',json={'version':latest['version'],'restricted':True,'items':[]},headers=erp.headers);assert response.status_code==200,response.json
 entry=mov('Implantação','5',expiry='2027-01-01');employee.op(entry,'execute_stock',403)
 response=erp.client.put(f'/api/inventory/units/{w["id"]}/permissions',json={'version':erp.get(w)['version'],'restricted':True,'items':[{'user_id':uid,'allowed':True}]},headers=erp.headers);assert response.status_code==200
 employee.op(entry,'execute_stock');assert c.put(f'/api/inventory/units/{w["id"]}/permissions',json={'version':erp.get(w)['version'],'restricted':False,'items':[]},headers=h).status_code==403
 response=erp.client.put(f'/api/inventory/units/{dept["id"]}/permissions',json={'version':erp.get(dept)['version'],'restricted':True,'items':[]},headers=erp.headers);assert response.status_code==200
 employee.op(req,'approve_requisition',403)

def test_replenishment_override_and_monthly_consumption(erp,reviewer):
 w,b,m,mov=stock(erp);entry=mov('Implantação','10',expiry='2027-01-01');erp.op(entry,'execute_stock');out=mov('Saída','6');erp.op(out,'execute_stock')
 erp.edit(w,model='Quantidade',minimum='5',average='7',maximum='10',reorder_percent='50');x=report(erp,'balances',warehouse=w['id'])['items'][0];assert x['quantity']==4000000 and x['suggested']==6000000
 rule=erp.make('inventory','policies',warehouse=w['id'],material=m['id'],model='Consumo mensal',history_months=1,minimum_months=1,maximum_months=2)
 x=report(erp,'balances',warehouse=w['id'],end='2026-02-28')['items'][0];assert x['monthly_average']==6000000 and x['suggested']==8000000
 assert report(erp,'movements',group='Outro')['items']==[]

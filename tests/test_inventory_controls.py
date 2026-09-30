import json,time
import pytest
from test_system import app,admin,user,login
from test_erp import ERP,erp,reviewer,stock,finance
from test_inventory import requisition,report,supply,invoice
from test_erp_flows import process
from db import get_db


def test_virtual_procurement_links_and_no_double_count(erp,reviewer):
 w,b,m,mov=stock(erp);dept,center,req,line=requisition(erp,w,m,'10','Compra');reviewer.op(req,'approve_requisition')
 assert report(erp,'balances',warehouse=w['id'])['items'][0]['virtual']==0
 p=process(erp);pi=erp.make('procurement','items',process=p['id'],unit='UN',quantity='10',unit_price='2.33');erp.op(p,'advance_process',reason='Edital conferido')
 link=erp.make('inventory','purchase_links',requisition_item=line['id'],procurement_item=pi['id'],warehouse=w['id'],quantity='10',date='2026-01-03',research_number='PP-123',research_date='2026-01-01');reviewer.op(link,'approve_purchase_link')
 x=report(erp,'balances',warehouse=w['id'])['items'][0];assert x['virtual']==x['in_procurement']==10000000
 erp.op(req,'cancel_requisition',409,reason='Pedido cancelado')
 f,dr,cr,s,ap,bank=finance(erp);bid=erp.make('procurement','proposals',item=pi['id'],supplier=s['id'],unit_price='2.33',qualified=True)
 for _ in range(3):erp.op(p,'advance_process',reason='Etapa documentada')
 reviewer.op(p,'advance_process',reason='Adjudicação autorizada');reviewer.op(bid,'award_proposal',reason='Vencedor habilitado');reviewer.op(p,'advance_process',reason='Homologação autorizada')
 c=erp.make('finance','commitments',appropriation=ap['id'],supplier=s['id'],date='2026-01-02',amount='100',type='Ordinário');erp.op(c,'commit')
 a=erp.make('inventory','authorizations',requisition=req['id'],process=p['id'],supplier=s['id'],commitment=c['id'],warehouse=w['id'],date='2026-01-06',research_number='PP-123',research_date='2026-01-01');ai=erp.make('inventory','authorization_items',authorization=a['id'],purchase_link=link['id'],procurement_item=pi['id'],material=m['id'],quantity='6',unit_price='2.33');reviewer.op(a,'approve_supply_authorization')
 x=report(erp,'balances',warehouse=w['id'])['items'][0];assert (x['virtual'],x['incoming'],x['in_procurement'])==(10000000,6000000,4000000)
 reviewer.op(link,'cancel_purchase_link',409,reason='Cancelar vínculo utilizado');erp.op(c,'cancel_commitment',409,reason='Cancelar empenho reservado')
 d=erp.client.get('/api/inventory/dossier/'+str(req['id']));assert d.status_code==200 and d.json['planning'][0]['link']['data']['research_number']=='PP-123'

def test_service_asset_invoices_duplicates_and_atomicity(app,erp,reviewer):
 f,dr,cr,s,ap,bank=finance(erp);c=erp.make('finance','commitments',appropriation=ap['id'],supplier=s['id'],date='2026-01-01',amount='500',type='Ordinário');erp.op(c,'commit')
 service=erp.make('inventory','invoices',supplier=s['id'],number='NF-S1',series='1',model='NFS-e',type='Serviço',commitment=c['id'],date='2026-01-02',issued_at='2026-01-01');line=erp.make('inventory','invoice_items',invoice=service['id'],quantity='2',unit_price='50');reviewer.op(service,'post_inventory_invoice');assert erp.get(c)['balances']['settled']==10000
 dup=erp.client.post('/api/erp/inventory/invoices',json={'entity':1,'exercise':2026,'data':{**erp.get(service)['data'],'code':'DUP-S'}} ,headers=erp.headers);assert dup.status_code==409
 cls=erp.make('assets','classes',asset_account=dr['id'],depreciation_account=cr['id'],useful_months=60,residual_percent='10');inv=erp.make('inventory','invoices',supplier=s['id'],number='NF-B1',series='1',model='55',type='Bem patrimonial',commitment=c['id'],date='2026-01-03',issued_at='2026-01-02');line=erp.make('inventory','invoice_items',invoice=inv['id'],quantity='2',unit_price='100',asset_class=cls['id'],asset_location='Secretaria',asset_owner='Responsável');r=reviewer.op(inv,'post_inventory_invoice')['result'];assert len(r['assets'])==2 and erp.get(c)['balances']['settled']==30000
 assert all(erp.get({'id':id})['data']['amount']=='100' for id in r['assets'])

def test_hierarchy_quota_and_commission_reparent_guard(erp,reviewer):
 w,b,m,mov=stock(erp);dept,parent,req,line=requisition(erp,w,m,'4');child=erp.make('inventory','cost_centers',parent=parent['id'],department=dept['id'],owner='Chefia subordinada');erp.edit(req,cost_center=child['id']);erp.edit(m,group='Limpeza')
 erp.make('inventory','quotas',cost_center=parent['id'],material_group='Limpeza',period='2026-01',quantity='3',amount='6');r=reviewer.op(req,'approve_requisition')['result'];assert r['alerts'][0]['quantity_requested']==4000000
 one=erp.make('inventory','commissions',publication='2026-01-01',start='2026-01-01',end='2026-12-31');two=erp.make('inventory','commissions',publication='2026-01-01',start='2026-01-01',end='2026-12-31');member=erp.make('inventory','commission_members',commission=one['id'],cpf='52998224725',position='Presidente');reviewer.op(one,'seal_stock_commission');erp.edit(member,409,commission=two['id'])
 response=erp.client.delete('/api/erp/object/'+str(member['id']),query_string={'version':erp.get(member)['version']},headers=erp.headers);assert response.status_code==409

def test_official_tables_search_validation_and_refresh(app,erp,monkeypatch):
 import inventory_classifications as ic
 for kind,code in [('ncm','0101.21.00'),('nbs','1.0101.11.00')]:
  r=erp.client.get('/api/inventory/classifications/'+kind,query_string={'q':code});assert r.status_code==200 and r.json['items'][0]['display']==code
  erp.make('inventory','materials',unit='UN',**{kind:code})
  raw=(ic.ROOT/ic.SOURCES[kind]['file']).read_bytes();monkeypatch.setattr(ic,'fetch',lambda k,raw=raw:(raw,ic.parse(k,raw)));r=erp.client.post('/api/inventory/classifications/'+kind+'/refresh',json={},headers=erp.headers);assert r.status_code==200,r.json
  r=erp.client.get('/api/inventory/classifications/'+kind,query_string={'q':code});assert r.status_code==200 and r.json['items'][0]['display']==code
 invalid=erp.client.post('/api/erp/inventory/materials',json={'entity':1,'exercise':2026,'data':{'code':'BAD','name':'NCM inválido','unit':'UN','ncm':'99999999'}},headers=erp.headers);assert invalid.status_code==400
 assert erp.client.get('/api/inventory/classifications/nbs',query_string={'q':'construcao'}).json['total']>0

def test_more_than_one_thousand_interconnected_warehouses(erp):
 w,b,m,mov=stock(erp);started=time.perf_counter()
 for index in range(999):last=erp.make('inventory','warehouses',code=f'ALM-{index+3:04d}',name=f'Almoxarifado {index+3}',location='Unidade de teste',owner='Responsável')
 assert erp.client.get('/api/erp/inventory/warehouses?entity=1&exercise=2026').json['total']==1001
 entry=mov('Implantação','10',expiry='2027-01-01');erp.op(entry,'execute_stock');transfer=mov('Transferência','2',destination=last['id']);erp.op(transfer,'execute_stock');before=report(erp,'balances',warehouse=last['id'])['items'][0];assert before['transit']==2000000 and before['quantity']==0
 erp.op(transfer,'receive_transfer',date='2026-02-01');before=report(erp,'balances',warehouse=last['id'],end='2026-01-31')['items'][0];after=report(erp,'balances',warehouse=last['id'],end='2026-02-01')['items'][0];assert before['transit']==2000000 and before['quantity']==0 and after['transit']==0 and after['quantity']==2000000
 print('1001 almoxarifados e transferência rastreável: %.2fs'%(time.perf_counter()-started))

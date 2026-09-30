import pytest
from test_system import app,admin
from test_erp import erp,reviewer
from test_inventory import supply,invoice
from db import get_db


def test_failed_inventory_posting_reverts_settlement_and_invoice(app,erp,reviewer):
 w,m,s,c,req,auth,ai=supply(erp,reviewer);inv=invoice(erp,s,auth);r=erp.op(inv,'suggest_authorized_items');line={'id':r['result']['created_items'][0]};erp.edit(line,expiry='2027-01-01')
 rules=erp.client.get('/api/erp/inventory/accounting_rules?entity=1&exercise=2026&limit=100').json['items'];rule=next(r for r in rules if r['data']['fact']=='Entrada');reviewer.op(rule,'retire_stock_accounting',reason='Regra pendente de revisão')
 reviewer.op(inv,'post_inventory_invoice',409)
 assert erp.get(inv)['state']=='Rascunho' and erp.get(c)['balances'].get('settled',0)==0 and erp.get(ai)['balances'].get('received',0)==0
 with app.app_context():
  db=get_db()
  for table in ['erp_stock','erp_stock_ledger','erp_ledger','inventory_invoice_postings']:assert db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0]==0
  assert db.execute("SELECT COUNT(*) FROM erp_objects WHERE module='finance' AND kind='settlements'").fetchone()[0]==0

def test_commitment_balance_reserved_for_authorized_deliveries(erp,reviewer):
 w,m,s,c,req,auth,ai=supply(erp,reviewer)
 settlement=erp.make('finance','settlements',commitment=c['id'],date='2026-01-07',invoice='OUTRA-NOTA',amount='90');erp.op(settlement,'settle',409)
 erp.edit(settlement,amount='76.70');erp.op(settlement,'settle')
 inv=invoice(erp,s,auth);r=erp.op(inv,'suggest_authorized_items');erp.edit({'id':r['result']['created_items'][0]},expiry='2027-01-01');reviewer.op(inv,'post_inventory_invoice');assert erp.get(c)['balances']['settled']==10000

def test_blocked_warehouse_rejects_invoice_items(erp,reviewer):
 w,m,s,c,req,auth,ai=supply(erp,reviewer);inv=invoice(erp,s,auth);erp.edit(w,blocked=True);erp.op(inv,'suggest_authorized_items',409)
 assert erp.client.get('/api/erp/object/'+str(inv['id'])).json['inventory']['items']==[]

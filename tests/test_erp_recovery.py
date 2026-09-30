import json,sqlite3
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from test_system import app,admin,login
from test_erp import ERP,erp,finance
from backup import create_backup,restore_backup
from db import get_db

def test_simultaneous_commitments_cannot_overspend(app,erp):
 f,dr,cr,s,a,b=finance(erp)
 commitments=[erp.make('finance','commitments',appropriation=a['id'],supplier=s['id'],date='2026-01-01',amount='700',type='Ordinário') for _ in range(2)]
 clients=[app.test_client(),app.test_client()];headers=[login(c) for c in clients]
 def post(i):return clients[i].post(f"/api/erp/object/{commitments[i]['id']}/operate",json={'version':1,'operation':'commit'},headers=headers[i]).status_code
 with ThreadPoolExecutor(max_workers=2) as pool:statuses=list(pool.map(post,range(2)))
 assert sorted(statuses)==[200,409]
 assert erp.get(a)['balances']['committed']==70000
 assert sorted(erp.get(c)['state'] for c in commitments)==['Empenhado','Rascunho']

def test_backup_restores_erp_links_and_history(app,erp,tmp_path):
 f,dr,cr,s,a,b=finance(erp)
 j=erp.make('finance','journals',date='2026-01-01',debit=dr['id'],credit=cr['id'],fund=f['id'],amount='123.45');erp.op(j,'post_journal')
 target=create_backup(app.config['DATABASE'],tmp_path/'snapshots',app.config['FERNET_KEY'])
 restored=tmp_path/'restored.db';restore_backup(target,restored,app.config['FERNET_KEY'])
 with sqlite3.connect(restored) as db:
  assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
  assert db.execute('PRAGMA foreign_key_check').fetchall()==[]
  assert db.execute('SELECT sum(debit),sum(credit) FROM erp_ledger').fetchone()==(12345,12345)
  assert db.execute('SELECT count(*) FROM erp_links').fetchone()[0]>0
  assert db.execute('SELECT count(*) FROM erp_events WHERE object_id=?',(j['id'],)).fetchone()[0]==2
  assert db.execute('SELECT count(*) FROM sessions').fetchone()[0]==0

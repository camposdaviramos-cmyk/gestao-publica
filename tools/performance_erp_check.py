"""Benchmark local sintético, sem inferência de capacidade municipal concorrente."""
import json,sys,tempfile,time,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app import create_app
from db import get_db
from domain import now

with tempfile.TemporaryDirectory(prefix='rio-erp-perf-') as directory:
 app=create_app({'DATA_DIR':directory,'DATABASE':str(Path(directory)/'rio.db')});client=app.test_client();password='TesteSeguro2026!!'
 client.post('/api/setup',json={'name':'Operador Teste','email':'teste@example.test','password':password});client.post('/api/login',json={'email':'teste@example.test','password':password})
 with app.app_context():
  db=get_db();stamp=now();rows=[]
  for n in range(10000):rows.append((1,2026,'finance','receipts',f'R{n}',f'Receita de teste {n}',json.dumps({'code':f'R{n}','name':f'Receita de teste {n}','date':f'2026-{n%12+1:02}-01','amount':10000+n,'deduction':0}),'Arrecadado',1,stamp,stamp))
  for n in range(1200):rows.append((1,2026,'inventory','warehouses',f'A{n}',f'Almoxarifado {n}',json.dumps({'code':f'A{n}','name':f'Almoxarifado {n}','location':'Sede','owner':'Equipe','blocked':False}),'Rascunho',1,stamp,stamp))
  db.executemany('INSERT INTO erp_objects(entity_id,exercise,module,kind,code,name,data,state,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',rows);db.commit()
 result={'environment':'Cliente Flask local, chamadas sequenciais, 10.000 fatos sintéticos e 1.200 almoxarifados. Não é teste de carga municipal.','endpoints':{}}
 for endpoint in ['/api/erp/finance/receipts?entity=1&exercise=2026','/api/erp/finance/receipts?entity=1&exercise=2026&q=999','/api/erp/inventory/warehouses?entity=1&exercise=2026&page=60','/api/erp/insights?entity=1&exercise=2026']:
  samples=[]
  for i in range(21):
   start=time.perf_counter();response=client.get(endpoint);elapsed=(time.perf_counter()-start)*1000;assert response.status_code==200,response.json
   if i:samples.append(elapsed)
  result['endpoints'][endpoint]={'median_ms':round(statistics.median(samples),2),'p95_ms':round(sorted(samples)[18],2),'samples':len(samples)}
 (ROOT/'artifacts'/'performance-erp.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))

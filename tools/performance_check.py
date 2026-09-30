"""Medição local e sequencial; não substitui teste de carga em produção."""
import json
import statistics
import sys
import tempfile
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app import create_app
from db import get_db
from domain import now

with tempfile.TemporaryDirectory(prefix='rio-perf-') as directory:
 app=create_app({'TESTING':True,'DATA_DIR':directory,'DATABASE':str(Path(directory)/'rio.db')})
 client=app.test_client();password='TesteSeguro2026!!'
 client.post('/api/setup',json={'name':'Operador Teste','email':'perf@example.test','password':password})
 client.post('/api/login',json={'email':'perf@example.test','password':password})
 with app.app_context():
  db=get_db();db.executemany('INSERT INTO records(module,title,department,status,amount,data,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)', [('budget',f'Ação de desempenho {i}','Unidade '+str(i%12),'Em execução' if i%2 else 'Planejado',10000+i,json.dumps({'year':'2026'}),1,now(),now()) for i in range(10000)]);db.commit()
 result={'environment':'Flask test client local; 10.000 registros; chamadas sequenciais; sem latência de rede','endpoints':{}}
 for endpoint in ['/api/dashboard','/api/records/budget?page=1','/api/records/budget?q=desempenho%2099']:
  times=[]
  for i in range(31):
   start=time.perf_counter();response=client.get(endpoint);elapsed=(time.perf_counter()-start)*1000;assert response.status_code==200
   if i:times.append(elapsed)
  result['endpoints'][endpoint]={'samples':len(times),'median_ms':round(statistics.median(times),2),'p95_ms':round(sorted(times)[28],2)}
 artifacts=ROOT/'artifacts';artifacts.mkdir(exist_ok=True);(artifacts/'performance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))

"""Consultas somente de leitura em dados públicos, sem credenciais ou publicação."""
import sys,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from integration_transport import consult,RemoteError
from integration_catalog import PROVIDERS
rows=[]
for provider,params in [('ibge',{'municipio':'3304524'}),('siconfi',{'municipio':'3304524','exercicio':'2026'})]:
 started=time.monotonic()
 try:
  result=consult(provider,PROVIDERS[provider]['environments']['producao'],params,{},'test')
  summary={'id':result.get('id'),'nome':result.get('nome')} if provider=='ibge' else {'items':len(result.get('items',[])),'hasMore':result.get('hasMore')}
  rows.append({'provider':provider,'success':True,'duration_ms':round((time.monotonic()-started)*1000),'summary':summary})
 except RemoteError as error:rows.append({'provider':provider,'success':False,'error':str(error)})
(ROOT/'artifacts'/'public-integrations-results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(rows,ensure_ascii=True))

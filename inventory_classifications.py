"""NCM/Siscomex e NBS/MDIC: tabelas oficiais versionadas e pesquisáveis."""
import csv,gzip,hashlib,html,io,json,re,unicodedata
from datetime import datetime
from functools import lru_cache
from pathlib import Path
import requests
from flask import request,jsonify,g
from auth import ApiError,require
from db import get_db,audit
from domain import now,local_time
from erp_core import integer

SOURCES={
 'ncm':{'name':'NCM · Siscomex','url':'https://portalunico.siscomex.gov.br/classif/api/publico/nomenclatura/download/json','file':'ncm.json','digits':8},
 'nbs':{'name':'NBS 2.0 · MDIC','url':'https://www.gov.br/mdic/pt-br/assuntos/sdic/comercio-e-servicos/nbs-nomenclatura-brasileira-de-servicos/arquivos/nbs2-0.csv/@@download/file','file':'nbs.csv','digits':9}}
ROOT=Path(__file__).parent/'schemas/classifications'

def normalized(value):return ''.join(c for c in unicodedata.normalize('NFKD',value.casefold()) if not unicodedata.combining(c))

@lru_cache(maxsize=8)
def parse(kind,raw):
 source=SOURCES[kind];items=[];seen=set();version='NBS 2.0'
 if kind=='ncm':
  try:d=json.loads(raw);rows=d['Nomenclaturas'];version=d['Data_Ultima_Atualizacao_NCM']+' · '+d.get('Ato','')
  except (ValueError,KeyError,TypeError):raise ApiError('Resposta NCM não corresponde ao formato oficial.',502)
  for r in rows:
   code=re.sub(r'\D','',str(r.get('Codigo','')))
   if len(code)!=source['digits']:continue
   try:start=datetime.strptime(r['Data_Inicio'],'%d/%m/%Y').date().isoformat();end=datetime.strptime(r['Data_Fim'],'%d/%m/%Y').date().isoformat()
   except (KeyError,ValueError,TypeError):raise ApiError('Tabela NCM contém vigência inválida.',502)
   items.append({'code':code,'display':r['Codigo'],'description':html.unescape(re.sub('<[^>]*>','',r.get('Descricao',''))).strip(),'start':start,'end':end})
 else:
  text=raw.decode('cp1252');rows=csv.reader(io.StringIO(text),delimiter=';');header=next(rows,[])
  if not header or 'NBS' not in header[0]:raise ApiError('Resposta NBS não corresponde ao CSV oficial.',502)
  for r in rows:
   if len(r)<2:continue
   code=re.sub(r'\D','',r[0])
   if len(code)==source['digits']:items.append({'code':code,'display':r[0].strip(),'description':r[1].strip(),'start':None,'end':None})
 if not 100<=len(items)<=50000:raise ApiError('Tabela oficial vazia, incompleta ou com tamanho inesperado.',502)
 for r in items:
  if r['code'] in seen or not r['description']:raise ApiError('Tabela oficial contém códigos duplicados ou descrições vazias.',502)
  seen.add(r['code']);r['_search']=normalized(r['description'])
 return {'version':version,'items':items,'by_code':{r['code']:r for r in items},'sha256':hashlib.sha256(raw).hexdigest()}

@lru_cache(maxsize=2)
def bundled(kind):return parse(kind,(ROOT/SOURCES[kind]['file']).read_bytes())

def table(kind):
 if kind not in SOURCES:raise ApiError('Classificação desconhecida.')
 row=get_db().execute('SELECT payload,imported_at FROM inventory_classification_imports WHERE kind=? ORDER BY id DESC LIMIT 1',(kind,)).fetchone()
 return (parse(kind,gzip.decompress(row['payload'])),row['imported_at']) if row else (bundled(kind),'2026-09-23')

def validate_material(d):
 for kind in SOURCES:
  if not d.get(kind):continue
  code=re.sub(r'\D','',d[kind]);data,_=table(kind);row=data['by_code'].get(code)
  if not row:raise ApiError(kind.upper()+': código inexistente na tabela oficial. Consulte pelo código ou descrição.')
  today=local_time().date().isoformat()
  if kind=='ncm' and not row['start']<=today<=row['end']:raise ApiError('Código NCM fora da vigência na tabela consultada.')
  d[kind]=row['display']

def fetch(kind):
 # Destinos fixos oficiais; nenhum endereço ou credencial é fornecido pelo cliente.
 url=SOURCES[kind]['url'];chunks=[];size=0
 try:
  with requests.Session() as session:
   session.trust_env=False
   with session.get(url,headers={'User-Agent':'RioGestao/1.0','Accept':'application/json,text/csv,*/*'},timeout=(5,25),stream=True,allow_redirects=False) as response:
    if response.status_code!=200:raise ApiError('Fonte oficial indisponível (HTTP '+str(response.status_code)+'). A tabela anterior foi preservada.',502)
    for chunk in response.iter_content(65536):
     size+=len(chunk)
     if size>16000000:raise ApiError('Fonte oficial excedeu o limite de 16 MB.',502)
     chunks.append(chunk)
 except requests.RequestException:raise ApiError('Não foi possível consultar a fonte oficial. A tabela anterior foi preservada.',502)
 raw=b''.join(chunks);return raw,parse(kind,raw)

def install_classifications(app):
 @app.get('/api/inventory/classifications/<kind>')
 def search(kind):
  require('inventory');data,updated=table(kind);q=normalized(request.args.get('q','').strip()[:160]);digits=re.sub(r'\D','',q);page=integer(request.args.get('page',1),'Página',1,10000);items=[r for r in data['items'] if not q or q in r['_search'] or (digits and digits in r['code'])];start=(page-1)*50
  return jsonify(items=[{k:v for k,v in r.items() if not k.startswith('_')} for r in items[start:start+50]],total=len(items),page=page,version=data['version'],sha256=data['sha256'],updated_at=updated,source=SOURCES[kind]['url'])

 @app.post('/api/inventory/classifications/<kind>/refresh')
 def refresh(kind):
  require('inventory','write');require('settings','write')
  if g.user['group_id']!=1:raise ApiError('Atualização de tabelas oficiais exige administrador.',403)
  if kind not in SOURCES:raise ApiError('Classificação desconhecida.')
  raw,data=fetch(kind);db=get_db();db.execute('BEGIN IMMEDIATE');db.execute('INSERT INTO inventory_classification_imports(kind,version,sha256,source,payload,imported_at,actor_id) VALUES(?,?,?,?,?,?,?)',(kind,data['version'],data['sha256'],SOURCES[kind]['url'],gzip.compress(raw),now(),g.user['id']));audit('Tabela oficial atualizada','inventory',detail={'kind':kind,'sha256':data['sha256'],'count':len(data['items']),'source':SOURCES[kind]['url']});return jsonify(message='Tabela oficial atualizada.',count=len(data['items']),version=data['version'],sha256=data['sha256'])

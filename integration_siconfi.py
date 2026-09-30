"""Extratos oficiais vinculados à agenda, sem inferir cumprimento legal pelo status remoto."""
import hashlib,json
from flask import g,request,jsonify
from auth import ApiError,require
from db import get_db,audit,notify
from domain import now
from erp_core import entity_access,load,integer,event
from integrations import admin_access,get_config
from integration_catalog import PROVIDERS
from integration_transport import consult,RemoteError

SCHEMA='''
CREATE TABLE IF NOT EXISTS siconfi_reports (
 id INTEGER PRIMARY KEY,entity_id INTEGER NOT NULL REFERENCES erp_entities(id),
 report_key TEXT NOT NULL,exercise INTEGER NOT NULL,municipio TEXT NOT NULL,
 data TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1,updated_at TEXT NOT NULL,
 UNIQUE(entity_id,report_key)
);
CREATE TABLE IF NOT EXISTS siconfi_links (
 report_id INTEGER PRIMARY KEY REFERENCES siconfi_reports(id),
 occurrence_id INTEGER NOT NULL UNIQUE REFERENCES erp_objects(id),
 watcher_id INTEGER NOT NULL REFERENCES users(id),created_at TEXT NOT NULL
);
'''

def prepare_reports(result,parameters):
 if not isinstance(result,dict) or not isinstance(result.get('items'),list) or result.get('hasMore'):raise ApiError('Extrato incompleto ou paginado. Nenhum dado da agenda foi alterado.',409)
 reports={}
 for item in result['items']:
  if not isinstance(item,dict) or str(item.get('cod_ibge'))!=parameters['municipio'] or str(item.get('exercicio'))!=parameters['exercicio']:raise ApiError('Extrato de outro município ou exercício. Sincronização interrompida.',409)
  for f in ['instituicao','entregavel','periodicidade']:
   if not isinstance(item.get(f),str) or not item[f].strip():raise ApiError('Extrato sem identificação suficiente. Nenhuma atualização aplicada.',409)
  integer(item.get('periodo'),'Período',0,12)
  identity=[item.get(x) for x in ['exercicio','cod_ibge','instituicao','entregavel','periodo','periodicidade','tipo_relatorio']]
  digest=hashlib.sha256(json.dumps(identity,ensure_ascii=False).encode()).hexdigest()
  if digest not in reports or str(item.get('data_status') or '')>str(reports[digest].get('data_status') or ''):reports[digest]=item
 return reports

def install_siconfi(app):
 with app.app_context():get_db().executescript(SCHEMA);get_db().commit()

 @app.get('/api/integrations/siconfi/reports')
 def siconfi_reports():
  admin_access();entity=entity_access(request.args.get('entity','1'));exercise=integer(request.args.get('exercise'),'Exercício',2000,2100)
  result=[]
  for row in get_db().execute('SELECT r.*,l.occurrence_id FROM siconfi_reports r LEFT JOIN siconfi_links l ON l.report_id=r.id WHERE r.entity_id=? AND r.exercise=? ORDER BY r.id',(entity,exercise)):
   item=dict(row);item['data']=json.loads(item['data']);result.append(item)
  return jsonify(items=result)

 @app.post('/api/integrations/siconfi/sync')
 def siconfi_sync():
  admin_access('write');require('control','write');d=request.get_json();entity=entity_access(d.get('entity','1'))
  cfg=get_config(entity,'siconfi','producao')
  if not cfg or not cfg['enabled']:raise ApiError('Configure e ative o Siconfi em produção.',409)
  parameters=json.loads(cfg['parameters'])
  try:result=consult('siconfi',PROVIDERS['siconfi']['environments']['producao'],parameters,{},'test')
  except RemoteError as error:raise ApiError(str(error),502) from None
  reports=prepare_reports(result,parameters);db=get_db();db.execute('BEGIN IMMEDIATE')
  latest=get_config(entity,'siconfi','producao')
  if latest['version']!=cfg['version']:raise ApiError('Configuração alterada durante a consulta. Atualize novamente.',409)
  created=changed=notifications=0
  for digest,item in reports.items():
   row=db.execute('SELECT * FROM siconfi_reports WHERE entity_id=? AND report_key=?',(entity,digest)).fetchone()
   data=json.dumps(item,ensure_ascii=False,sort_keys=True)
   if not row:
    db.execute('INSERT INTO siconfi_reports(entity_id,report_key,exercise,municipio,data,updated_at) VALUES(?,?,?,?,?,?)',(entity,digest,int(parameters['exercicio']),parameters['municipio'],data,now()));created+=1
   elif row['data']!=data:
    previous=json.loads(row['data'])
    if str(item.get('data_status') or '')<str(previous.get('data_status') or ''):continue
    db.execute('UPDATE siconfi_reports SET data=?,version=version+1,updated_at=? WHERE id=?',(data,now(),row['id']));changed+=1
    link=db.execute('SELECT * FROM siconfi_links WHERE report_id=?',(row['id'],)).fetchone()
    if link and any(previous.get(k)!=item.get(k) for k in ['status_relatorio','data_status']):
     occurrence=load(link['occurrence_id'],'control','occurrences')
     event(occurrence,'Status Siconfi atualizado',{'previous':previous.get('status_relatorio'),'current':item.get('status_relatorio'),'remote_date':item.get('data_status'),'institution':item['instituicao']})
     notify(link['watcher_id'],'Atualização de obrigação no Siconfi',f"{occurrence['code']}: status externo atualizado. Confira o extrato na central de integrações.");notifications+=1
  audit('Extrato Siconfi sincronizado','control',entity,{'exercise':parameters['exercicio'],'created':created,'changed':changed,'notifications':notifications})
  return jsonify(message='Extrato sincronizado. A situação local da obrigação é encerrada mediante análise do responsável.',created=created,changed=changed,notifications=notifications,exercise=int(parameters['exercicio']))

 @app.put('/api/integrations/siconfi/reports/<int:id>/link')
 def siconfi_link(id):
  admin_access('write');require('control','write');d=request.get_json();db=get_db();db.execute('BEGIN IMMEDIATE');row=db.execute('SELECT * FROM siconfi_reports WHERE id=?',(id,)).fetchone()
  if not row:raise ApiError('Extrato não encontrado.',404)
  entity_access(row['entity_id'])
  if integer(d.get('version'),'Versão',1)!=row['version']:raise ApiError('Extrato alterado. Atualize a consulta.',409)
  occurrence=load(d.get('occurrence_id'),'control','occurrences')
  if occurrence['entity_id']!=row['entity_id'] or occurrence['exercise']!=row['exercise']:raise ApiError('A ocorrência deve pertencer à mesma entidade e exercício.')
  if d.get('confirm_institution')!=json.loads(row['data'])['instituicao']:raise ApiError('Confirme a instituição do extrato: Prefeitura e Câmara são entes distintos.')
  if db.execute('SELECT 1 FROM siconfi_links WHERE report_id=? OR occurrence_id=?',(id,occurrence['id'])).fetchone():raise ApiError('O relatório ou a ocorrência já possui vínculo.',409)
  db.execute('INSERT INTO siconfi_links VALUES(?,?,?,?)',(id,occurrence['id'],g.user['id'],now()));event(occurrence,'Vínculo com Siconfi criado',{'report_id':id,'institution':d['confirm_institution']})
  return jsonify(message='Vínculo criado. Alterações de status serão notificadas ao administrador que criou o vínculo.')

 @app.get('/api/erp/object/<int:object_id>/siconfi')
 def occurrence_report(object_id):
  load(object_id,'control','occurrences')
  row=get_db().execute('SELECT r.data,r.updated_at FROM siconfi_reports r JOIN siconfi_links l ON l.report_id=r.id WHERE l.occurrence_id=?',(object_id,)).fetchone()
  return jsonify(report=json.loads(row['data']) if row else None,updated_at=row['updated_at'] if row else None)

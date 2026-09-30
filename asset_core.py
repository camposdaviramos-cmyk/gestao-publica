"""Eventos patrimoniais, saldos derivados e partidas contábeis indivisíveis."""
import calendar,copy,json,uuid
from datetime import date
from decimal import Decimal
from flask import g
from auth import ApiError,require
from db import get_db
from domain import now,local_time
from erp_core import load,related,check_period,require_other,require_draft,event,rounded,integer,quantity,cents,change_balance,balance


def rows(kind,field,id):
 return [load(r[0]) for r in get_db().execute("SELECT id FROM erp_objects WHERE module='assets' AND kind=? AND deleted=0 AND json_extract(data,?)=? ORDER BY id",(kind,'$.'+field,id))]

def same_entity(o,other):
 if o['entity_id']!=other['entity_id']:raise ApiError('Vínculo patrimonial de outra entidade.')

def day_value(value):
 try:d=date.fromisoformat(value)
 except (TypeError,ValueError):raise ApiError('Data patrimonial inválida.')
 if d>local_time().date():raise ApiError('O fato patrimonial não pode ser registrado com data futura.')
 return d.isoformat()

def commission(o,field,typ,day):
 if not o['data'].get(field):raise ApiError('Selecione uma comissão de '+typ.lower()+' formalizada.')
 c=related(o,field,'assets','commissions');d=c['data']
 if c['state']!='Formalizada' or d['type']!=typ or day<d['created'] or (d.get('extinguished') and day>d['extinguished']):raise ApiError('Comissão incompatível, não formalizada ou fora da vigência.')
 return c

def position(o,required=True):
 row=get_db().execute('SELECT data FROM asset_positions WHERE asset_id=?',(o['id'],)).fetchone()
 if not row and required:raise ApiError('Efetive o ingresso do bem antes de registrar eventos patrimoniais.',409)
 return json.loads(row[0]) if row else None

def active_events(asset_id):
 return get_db().execute('SELECT m.* FROM asset_movements m WHERE m.asset_id=? AND m.reversal_of IS NULL AND NOT EXISTS(SELECT 1 FROM asset_movements r WHERE r.reversal_of=m.id) ORDER BY m.date,m.id',(asset_id,)).fetchall()

def snapshot(o):return {'data':copy.deepcopy(o['data']),'code':o['code'],'name':o['name'],'state':o['state'],'position':position(o,False)}

def locked(o,inventory_id=None):
 db=get_db()
 return db.execute("SELECT 1 FROM erp_objects line JOIN erp_objects h ON h.id=json_extract(line.data,'$.inventory') WHERE line.module='assets' AND line.kind='inventory_items' AND line.deleted=0 AND h.deleted=0 AND h.state='Em andamento' AND json_extract(line.data,'$.asset')=? AND h.id<>?",(o['id'],inventory_id or 0)).fetchone() is not None

def available(o,day,inventory_id=None):
 day=day_value(day);check_period({**o,'exercise':int(day[:4])},day)
 if locked(o,inventory_id):raise ApiError('Bem bloqueado por inventário patrimonial em andamento.',409)
 if o['state'] in ['Baixado','Doado']:raise ApiError('Bem baixado ou doado não admite novos movimentos.',409)
 events=active_events(o['id'])
 if events and day<events[-1]['date']:raise ApiError('Evento anterior a movimento vigente. Estorne primeiro os eventos posteriores.',409)
 return day

def parameters(o):
 d=o['data'];c=related(o,'class','assets','classes')['data'];years=d.get('useful_years') or c.get('useful_years');months=rounded(Decimal(years)*12/1000000) if years else c.get('useful_months',0)
 residual=d.get('residual_percent') if d.get('residual_percent') is not None else c['residual_percent']
 if months<=0:raise ApiError('Vida útil deve ser positiva.')
 return {'months':months,'residual_percent':str(residual),'proration':c.get('proration') or 'Dias corridos'}

def new_position(o,gross=None,start=None,months=None,residual_percent=None):
 p=parameters(o);d=o['data'];gross=d['amount'] if gross is None else gross;rate=p['residual_percent'] if residual_percent is None else residual_percent
 return {'gross':gross,'accumulated':0,'residual':rounded(Decimal(gross)*Decimal(rate)/100),'cycle_base':gross,'cycle_accumulated':0,'cycle_residual':rounded(Decimal(gross)*Decimal(rate)/100),'cycle_start':start or d['start'],'cycle_months':months or p['months'],'cycle_units':d.get('total_units',0),'produced_units':0,'processed_through':None,'proration':p['proration'],'confirmed':not d.get('requires_confirmation',False)}

def account(id,o):
 a=load(id,'finance','accounts',check_access=False);same_entity(o,a)
 if a['exercise']!=o['exercise']:
  row=get_db().execute("SELECT id FROM erp_objects WHERE module='finance' AND kind='accounts' AND entity_id=? AND exercise=? AND code=? AND deleted=0",(o['entity_id'],o['exercise'],a['code'])).fetchone()
  if not row:raise ApiError('Cadastre a conta '+a['code']+' no exercício da operação.',409)
  a=load(row[0],'finance','accounts',check_access=False)
 if not a['data']['active'] or not a['data']['analytic']:raise ApiError('A contabilização patrimonial exige conta analítica ativa do exercício.',409)
 return a['id']

def rule(o,fact):
 row=get_db().execute("SELECT id FROM erp_objects WHERE module='assets' AND kind='accounting_rules' AND entity_id=? AND exercise=? AND deleted=0 AND state='Aprovado' AND json_extract(data,'$.fact')=? AND (json_extract(data,'$.class')=? OR json_extract(data,'$.class') IS NULL) ORDER BY json_extract(data,'$.class') IS NULL LIMIT 1",(o['entity_id'],o['exercise'],fact,o['data']['class'])).fetchone()
 if not row:raise ApiError('Configure e aprove a regra patrimonial para '+fact+'.',409)
 r=load(row[0]);return account(r['data']['counterpart'],o),r['id']

def pair(o,debit,credit,amount,class_id=None,location=None):
 if amount<0:raise ApiError('Partida patrimonial negativa.')
 if not amount:return []
 debit=account(debit,o);credit=account(credit,o)
 if debit==credit:raise ApiError('Partida patrimonial exige contas distintas.')
 return [{'account_id':debit,'debit':amount,'credit':0,'class_id':class_id or o['data']['class'],'location':location or o['data']['location']},{'account_id':credit,'debit':0,'credit':amount,'class_id':class_id or o['data']['class'],'location':location or o['data']['location']}]

def posting(o,fact,amount,day=None):
 if day:o={**o,'exercise':int(day[:4])}
 if not o['data'].get('capitalize'):return [],None
 c=related(o,'class','assets','classes')['data'];counter,rule_id=rule(o,fact)
 if fact=='Depreciação':return pair(o,counter,c['depreciation_account'],amount),rule_id
 if fact in ['Redução de valor','Baixa','Doação concedida']:return pair(o,counter,c['asset_account'],amount),rule_id
 return pair(o,c['asset_account'],counter,amount),rule_id

def save_position(o,p):
 db=get_db()
 if p is None:db.execute('DELETE FROM asset_positions WHERE asset_id=?',(o['id'],))
 else:db.execute('INSERT INTO asset_positions VALUES(?,?) ON CONFLICT(asset_id) DO UPDATE SET data=excluded.data',(o['id'],json.dumps(p,ensure_ascii=False)))
 desired=0 if p is None else p['accumulated'];change_balance(o['id'],'depreciated',desired-balance(o['id'],'depreciated'))
 produced=0 if p is None else p.get('produced_units',0);change_balance(o['id'],'produced_units',produced-balance(o['id'],'produced_units'))

def save_object(o):
 from erp_catalog import CATALOG
 db=get_db();d=o['data'];o['code']=d['code'];o['name']=d['name'];db.execute('UPDATE erp_objects SET code=?,name=?,data=?,state=?,version=version+1,updated_at=? WHERE id=?',(o['code'],o['name'],json.dumps(d,ensure_ascii=False),o['state'],now(),o['id']));db.execute('DELETE FROM erp_links WHERE source_id=?',(o['id'],))
 for name,f in CATALOG['assets']['resources']['items']['fields'].items():
  if f['type']=='reference' and d.get(name):db.execute('INSERT INTO erp_links VALUES(?,?,?)',(o['id'],name,d[name]))

def record(o,source,day,fact,description,before,p,entries=None,metadata=None,group_id=None,reversal_of=None):
 db=get_db();entries=entries or [];metadata=metadata or {};day=day_value(day);check_period({**o,'exercise':int(day[:4])},day)
 if sum(e['debit'] for e in entries)!=sum(e['credit'] for e in entries):raise ApiError('Partidas patrimoniais não estão equilibradas.',409)
 save_position(o,p);save_object(o);after=snapshot(o);seq=db.execute('SELECT COALESCE(MAX(sequence),0)+1 FROM asset_movements WHERE asset_id=? AND date=?',(o['id'],day)).fetchone()[0];group_id=group_id or uuid.uuid4().hex
 id=db.execute('INSERT INTO asset_movements(asset_id,source_id,entity_id,exercise,date,sequence,fact,description,before_snapshot,after_snapshot,metadata,group_id,reversal_of,actor_id,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(o['id'],source['id'],o['entity_id'],int(day[:4]),day,seq,fact,description,json.dumps(before,ensure_ascii=False),json.dumps(after,ensure_ascii=False),json.dumps(metadata,ensure_ascii=False),group_id,reversal_of,g.user['id'],now())).lastrowid
 for e in entries:
  account_id=account(e['account_id'],{**o,'exercise':int(day[:4])});ledger=db.execute('INSERT INTO erp_ledger(source_id,entity_id,exercise,date,account_id,debit,credit,reversal,created_at) VALUES(?,?,?,?,?,?,?,?,?)',(o['id'],o['entity_id'],int(day[:4]),day,account_id,e['debit'],e['credit'],int(reversal_of is not None),now())).lastrowid;db.execute('INSERT INTO asset_accounting_entries VALUES(?,?,?,?)',(id,ledger,e['class_id'],e['location']))
 event(o,fact,{'movement_id':id,'source_id':source['id'],'date':day,'sequence':seq,'description':description,'position':p,'metadata':metadata});return {'movement_id':id,'position':p,'sequence':seq}

def class_life(d):
 if d.get('useful_years'):
  months=Decimal(d['useful_years'])*12/1000000
  if months!=int(months) or months<1:raise ApiError('Vida útil em anos deve corresponder a uma quantidade inteira positiva de meses.')
  if d.get('useful_months') and d['useful_months']!=int(months):raise ApiError('Vida útil em anos diverge da quantidade de meses.')
  d['useful_months']=int(months)
 if not d.get('useful_months'):raise ApiError('Informe vida útil positiva em anos ou meses.')

def validate_asset(o):
 k,d=o['kind'],o['data'];db=get_db();id=o.get('id',0)
 if k=='classes':
  class_life(d)
  if d['asset_account']==d['depreciation_account']:raise ApiError('Contas patrimonial e depreciação devem ser distintas.')
  for field in ['asset_account','depreciation_account']:account(d[field],o)
  if id and db.execute("SELECT 1 FROM asset_positions p JOIN erp_objects a ON a.id=p.asset_id WHERE json_extract(a.data,'$.class')=?",(id,)).fetchone():
   old=json.loads(db.execute('SELECT data FROM erp_objects WHERE id=?',(id,)).fetchone()[0])
   if any(old.get(f)!=d.get(f) for f in ['asset_account','depreciation_account','useful_months','residual_percent','proration']):raise ApiError('Classificação em uso: ajuste o bem pela avaliação ou reclassificação para preservar os eventos.',409)
 if k=='responsibles' and db.execute("SELECT 1 FROM erp_objects WHERE module='assets' AND kind='responsibles' AND entity_id=? AND deleted=0 AND id<>? AND json_extract(data,'$.cpf')=?",(o['entity_id'],id,d['cpf'])).fetchone():raise ApiError('CPF de responsável já cadastrado.',409)
 if k=='commissions' and d.get('extinguished') and d['extinguished']<d['created']:raise ApiError('Extinção anterior à criação da comissão.')
 if k=='commission_members':
  c=related(o,'commission','assets','commissions')
  if c['state']!='Rascunho':raise ApiError('Comissão formalizada não admite alteração de integrantes.',409)
  if id:
   old=json.loads(db.execute('SELECT data FROM erp_objects WHERE id=?',(id,)).fetchone()[0])
   if load(old['commission'])['state']!='Rascunho':raise ApiError('Integrante de comissão formalizada não pode ser transferido.',409)
  if any(x['id']!=id and x['data']['responsible']==d['responsible'] for x in rows('commission_members','commission',c['id'])):raise ApiError('Integrante já incluído nesta comissão.',409)
 if k=='accounting_rules':require('finance','write');account(d['counterpart'],o)
 if k=='items':
  if d['start']<d['date']:raise ApiError('A depreciação não pode começar antes do ingresso.')
  if d['method']=='Unidades produzidas' and d['total_units']<=0:raise ApiError('Informe a produção total estimada.')
  if id and db.execute('SELECT 1 FROM asset_positions WHERE asset_id=?',(id,)).fetchone():raise ApiError('Bem efetivado: utilize a operação patrimonial específica para preservar o histórico.',409)
  if d.get('type')!='Próprio' and d.get('capitalize'):raise ApiError('Bens alugados ou recebidos em comodato devem permanecer no controle de terceiros.')
  for field in ['responsible','location_ref']:
   if d.get(field):
    target=load(d[field]);same_entity(o,target)
    if not target['data'].get('active'):raise ApiError('Responsável ou localização inativo.')
    d['owner' if field=='responsible' else 'location']=target['name']
    if field=='responsible':d['owner_cpf']=target['data']['cpf']
  if d.get('useful_years') and Decimal(d['useful_years'])*12/1000000!=int(Decimal(d['useful_years'])*12/1000000):raise ApiError('Vida útil deve corresponder a meses inteiros.')
 if k=='complement_commitments':
  c=related(o,'complement','assets','complements')
  if c['state']!='Rascunho':raise ApiError('Valor complementar efetivado não aceita alteração dos empenhos.',409)
  if d['amount']<=0:raise ApiError('Valor vinculado deve ser positivo.')
 if k=='maintenance_plans' and d['interval_months']<1:raise ApiError('Periodicidade de manutenção deve ser positiva.')
 if k=='maintenance_records' and d.get('warranty_through') and d['warranty_through']<d['date']:raise ApiError('Garantia não pode anteceder a manutenção.')
 if k=='inventory_items':
  inv=related(o,'inventory','assets','inventories')
  if inv['state']!='Em andamento':raise ApiError('Inventário não está aberto.',409)
  if any(x['id']!=id and x['data']['asset']==d['asset'] for x in rows('inventory_items','inventory',inv['id'])):raise ApiError('Bem já incluído neste inventário.',409)

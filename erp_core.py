import calendar
import json
import re
from datetime import date,datetime
from decimal import Decimal,InvalidOperation,ROUND_HALF_UP
from pathlib import Path
from flask import g
from auth import ApiError,require
from db import get_db,audit,settings
from domain import now,money
from erp_catalog import CATALOG,ERP_SCOPES

def init_erp():
 db=get_db();db.executescript((Path(__file__).parent/'erp_schema.sql').read_text(encoding='utf-8'))
 db.executescript((Path(__file__).parent/'inventory_schema.sql').read_text(encoding='utf-8'))
 db.executescript((Path(__file__).parent/'asset_schema.sql').read_text(encoding='utf-8'))
 db.executescript((Path(__file__).parent/'fleet_schema.sql').read_text(encoding='utf-8'))
 db.executescript((Path(__file__).parent/'works_schema.sql').read_text(encoding='utf-8'))
 db.executescript((Path(__file__).parent/'procurement_schema.sql').read_text(encoding='utf-8'))
 db.executescript((Path(__file__).parent/'transparency_schema.sql').read_text(encoding='utf-8'))
 db.executescript((Path(__file__).parent/'control_schema.sql').read_text(encoding='utf-8'))
 db.executescript((Path(__file__).parent/'people_schema.sql').read_text(encoding='utf-8'))
 db.executescript((Path(__file__).parent/'finance_schema.sql').read_text(encoding='utf-8'))
 db.executescript((Path(__file__).parent/'social_schema.sql').read_text(encoding='utf-8'))
 db.executescript((Path(__file__).parent/'bi_schema.sql').read_text(encoding='utf-8'))
 if not db.execute('SELECT 1 FROM erp_migrations WHERE version=1').fetchone():
  db.execute('INSERT OR IGNORE INTO erp_entities(code,name) VALUES(?,?)',('MUNICIPIO',settings()['municipality']))
  admin=db.execute('SELECT permissions FROM groups WHERE id=1').fetchone()
  perms=json.loads(admin['permissions'])
  for scope in ERP_SCOPES:perms[scope]=['read','write','delete','approve']
  db.execute('UPDATE groups SET permissions=? WHERE id=1',(json.dumps(perms),))
  db.execute('INSERT INTO erp_migrations VALUES(1,?)',(now(),));db.commit()

def integer(value,label='Valor',minimum=0,maximum=999999999):
 if isinstance(value,bool):raise ApiError(label+': número inválido.')
 try:n=int(str(value))
 except (ValueError,TypeError):raise ApiError(label+': informe um inteiro.')
 if not minimum<=n<=maximum:raise ApiError(label+': fora do intervalo permitido.')
 return n

def decimal(value,label='Valor',minimum=Decimal('0'),maximum=Decimal('999999999999')):
 try:n=Decimal(str(value))
 except (InvalidOperation,ValueError,TypeError):raise ApiError(label+': número inválido.')
 if not n.is_finite() or not minimum<=n<=maximum:raise ApiError(label+': fora do intervalo permitido.')
 return n

def quantity(value):
 n=decimal(value,'Quantidade')
 if n.as_tuple().exponent < -6:raise ApiError('Quantidade aceita até seis casas decimais.')
 return int(n*1000000)

def cents(value):
 try:return money(value)
 except ValueError as e:raise ApiError(str(e))

def rounded(value):return int(Decimal(value).quantize(Decimal('1'),rounding=ROUND_HALF_UP))

def valid_document(value,kind):
 value=re.sub(r'[. /\-]','',str(value).strip()).upper()
 if not re.fullmatch(r'[0-9]{11}|[0-9A-Z]{12}[0-9]{2}',value):raise ApiError('CPF/CNPJ inválido.')
 if len(value) not in ([11] if kind=='cpf' else [14] if kind=='cnpj' else [11,14]) or len(set(value))==1:raise ApiError('CPF/CNPJ inválido.')
 if len(value)==11:
  for size in [9,10]:
   digit=(sum(int(value[i])*(size+1-i) for i in range(size))*10)%11
   if digit==10:digit=0
   if digit!=int(value[size]):raise ApiError('CPF inválido.')
 else:
  for size,weights in [(12,[5,4,3,2,9,8,7,6,5,4,3,2]),(13,[6,5,4,3,2,9,8,7,6,5,4,3,2])]:
   rest=sum((ord(value[i])-48)*weights[i] for i in range(size))%11;digit=0 if rest<2 else 11-rest
   if digit!=int(value[size]):raise ApiError('CNPJ inválido.')
 return value

def spec(module,kind):
 if module not in CATALOG or kind not in CATALOG[module]['resources']:raise ApiError('Cadastro não encontrado.',404)
 return CATALOG[module]['resources'][kind]

def entity_access(entity_id):
 entity_id=integer(entity_id,'Entidade',1)
 if not get_db().execute('SELECT 1 FROM erp_entities WHERE id=? AND active=1',(entity_id,)).fetchone():raise ApiError('Entidade indisponível.',404)
 if g.user['group_id']!=1 and not get_db().execute('SELECT 1 FROM erp_entity_access WHERE user_id=? AND entity_id=?',(g.user['id'],entity_id)).fetchone():raise ApiError('Acesso não autorizado à entidade.',403)
 return entity_id

def confidential_sql():
 return '' if 'read' in g.permissions.get('social_confidential',[]) else " AND NOT (module='social' AND kind='visits' AND json_extract(data,'$.confidential')=1)"

def load(object_id,module=None,kind=None,check_access=True):
 row=get_db().execute('SELECT * FROM erp_objects WHERE id=? AND deleted=0',(integer(object_id,'Registro',1),)).fetchone()
 if not row or (module and row['module']!=module) or (kind and row['kind']!=kind):raise ApiError('Registro ou vínculo não encontrado.',404)
 obj=dict(row);obj['data']=json.loads(obj['data'])
 if check_access:
  entity_access(obj['entity_id']);require(obj['module'])
  if obj['module']=='social' and obj['kind']=='visits' and obj['data'].get('confidential'):require('social_confidential')
 return obj

def balance(object_id,name):
 row=get_db().execute('SELECT value FROM erp_balances WHERE object_id=? AND name=?',(object_id,name)).fetchone()
 return row[0] if row else 0

def change_balance(object_id,name,delta):
 get_db().execute('INSERT INTO erp_balances VALUES(?,?,?) ON CONFLICT(object_id,name) DO UPDATE SET value=value+excluded.value',(object_id,name,int(delta)))

def event(obj,operation,payload=None):
 get_db().execute('INSERT INTO erp_events(object_id,operation,payload,actor,created_at) VALUES(?,?,?,?,?)',(obj['id'],operation,json.dumps(payload or {},ensure_ascii=False),g.user['id'],now()))
 audit(operation,obj['module'],obj['id'],{'kind':obj['kind'],'entity':obj['entity_id'],'exercise':obj['exercise']})

def set_state(obj,state):
 get_db().execute('UPDATE erp_objects SET state=?,version=version+1,updated_at=? WHERE id=?',(state,now(),obj['id']));obj['state']=state;obj['version']+=1

def require_draft(obj):
 if obj['state']!='Rascunho':raise ApiError('Operação já efetivada ou registro em situação incompatível.',409)

def require_other(obj):
 require(obj['module'],'approve')
 if obj['created_by']==g.user['id']:raise ApiError('A aprovação exige outro usuário autorizado.',403)
 last=get_db().execute("SELECT actor FROM erp_events WHERE object_id=? AND operation IN ('Cadastro criado','Cadastro alterado','submit_measurement','calculate_payroll') ORDER BY id DESC LIMIT 1",(obj['id'],)).fetchone()
 if last and last['actor']==g.user['id']:raise ApiError('A última alteração ou submissão foi feita por você. Solicite aprovação de outro usuário.',403)

def check_period(obj,day):
 if str(day)[:4]!=str(obj['exercise']):raise ApiError('O movimento deve pertencer ao exercício selecionado.')
 lock=get_db().execute("SELECT max(json_extract(data,'$.through')) FROM erp_objects WHERE entity_id=? AND exercise=? AND module='finance' AND kind='locks' AND state='Fechado' AND deleted=0",(obj['entity_id'],obj['exercise'])).fetchone()[0]
 if lock and str(day)[:10]<=lock:raise ApiError('Período fechado para movimentações.',409)

def related(obj,field,module,kind):
 target=load(obj['data'].get(field),module,kind)
 if target['entity_id']!=obj['entity_id']:raise ApiError('Vínculo pertence a outra entidade.')
 return target

def serialize(obj):
 result={k:v for k,v in obj.items() if k!='data'};data=obj['data'].copy()
 for name,field in spec(obj['module'],obj['kind'])['fields'].items():
  if data.get(name) is not None and field['type'] in ['money','quantity']:
   data[name]=format(Decimal(data[name])/(100 if field['type']=='money' else 1000000),'f')
 result['data']=data;result['balances']={r['name']:r['value'] for r in get_db().execute('SELECT name,value FROM erp_balances WHERE object_id=?',(obj['id'],))}
 return result

def validate(module,kind,raw,entity,exercise):
 fields=spec(module,kind)['fields'];data={};links={}
 if not isinstance(raw,dict) or set(raw)-set(fields):raise ApiError('Campos não reconhecidos neste cadastro.')
 for name,f in fields.items():
  value=raw.get(name);typ=f['type']
  if value in [None,'']:
   if f['required']:raise ApiError(f['label']+': campo obrigatório.')
   data[name]=False if typ=='boolean' else 0 if typ in ['money','quantity','integer'] else None;continue
  if typ=='boolean':
   if type(value)!=bool:raise ApiError(f['label']+': valor inválido.')
   data[name]=value
  elif typ=='reference':
   target=load(value,*f['reference'].split('.'))
   if target['entity_id']!=entity:raise ApiError(f['label']+': vínculo de outra entidade.')
   if module=='finance' and target['module']=='finance' and target['kind'] in ['appropriations','commitments','settlements','bank_accounts'] and target['exercise']!=exercise:raise ApiError(f['label']+': vínculo de outro exercício; utilize a rotina de restos a pagar.')
   data[name]=target['id'];links[name]=target['id']
  elif typ=='money':data[name]=cents(value)
  elif typ=='quantity':data[name]=quantity(value)
  elif typ=='integer':data[name]=integer(value,f['label'])
  elif typ in ['percent','decimal']:
   data[name]=str(decimal(value,f['label'],Decimal('-180') if typ=='decimal' else Decimal('0'),Decimal('180') if typ=='decimal' else Decimal('100')))
  else:
   if not isinstance(value,str) or len(value)> (12000 if typ=='textarea' else 250):raise ApiError(f['label']+': conteúdo inválido ou muito longo.')
   value=value.strip()
   if f['required'] and not value:raise ApiError(f['label']+': campo obrigatório.')
   if typ in ['date','month','datetime']:
    try:datetime.strptime(value,{'date':'%Y-%m-%d','month':'%Y-%m','datetime':'%Y-%m-%dT%H:%M'}[typ])
    except ValueError:raise ApiError(f['label']+': data inválida.')
   if typ=='select' and value not in f['options']:raise ApiError(f['label']+': opção inválida.')
   if typ in ['cpf','cnpj','document']:value=valid_document(value,typ)
   if typ=='url' and not re.match(r'^https://[^\s/]+(?:/.*)?$',value):raise ApiError('Use um endereço HTTPS válido.')
   if typ=='email' and not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$',value):raise ApiError('E-mail inválido.')
   data[name]=value
 for start,end in [('start','end'),('departure','return'),('blocked_from','blocked_until')]:
  if data.get(start) and data.get(end) and data[start]>data[end]:raise ApiError('O término não pode ser anterior ao início.')
 if module=='social' and kind=='visits' and data.get('confidential'):require('social_confidential','write')
 return data,links

def create_object(module,kind,entity,exercise,data):
 fields,links=validate(module,kind,data,entity,exercise)
 obj={'entity_id':entity,'exercise':exercise,'module':module,'kind':kind,'data':fields,'state':'Rascunho','created_by':g.user['id'],'version':1}
 from erp_rules import validate_business
 validate_business(obj)
 obj['id']=get_db().execute('INSERT INTO erp_objects(entity_id,exercise,module,kind,code,name,data,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)',(entity,exercise,module,kind,fields['code'],fields['name'],json.dumps(fields,ensure_ascii=False),g.user['id'],now(),now())).lastrowid
 for field,target in links.items():get_db().execute('INSERT INTO erp_links VALUES(?,?,?)',(obj['id'],field,target))
 event(obj,'Cadastro criado',{'data':fields});return load(obj['id'])

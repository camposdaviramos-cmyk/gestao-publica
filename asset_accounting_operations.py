"""Eventos de valor, ciclos de depreciação e estornos patrimoniais."""
import calendar,copy,json,uuid
from datetime import date,timedelta
from decimal import Decimal
from flask import g
from auth import ApiError,require
from db import get_db
from domain import local_time
from erp_core import load,related,require_draft,require_other,set_state,event,rounded,quantity,integer,cents
from asset_core import (rows,same_entity,commission,position,snapshot,available,new_position,posting,pair,record,account,validate_asset,active_events,day_value)


def justification(a):
 from erp_operations import reason
 return reason(a)

def approve_asset_rule(o,a):
 require_draft(o);require_other(o);require('finance','approve');validate_asset(o);d=o['data']
 if get_db().execute("SELECT 1 FROM erp_objects WHERE module='assets' AND kind='accounting_rules' AND entity_id=? AND exercise=? AND state='Aprovado' AND deleted=0 AND json_extract(data,'$.fact')=? AND json_extract(data,'$.class') IS ?",(o['entity_id'],o['exercise'],d['fact'],d.get('class'))).fetchone():raise ApiError('Já existe regra vigente para este fato e classificação.',409)
 set_state(o,'Aprovado');return {'fact':d['fact']}

def retire_asset_rule(o,a):
 require_other(o);require('finance','approve');why=justification(a)
 if o['state']!='Aprovado':raise ApiError('Regra não está vigente.',409)
 set_state(o,'Encerrado');return {'reason':why}

def seal_asset_commission(o,a):
 require_draft(o);require_other(o);members=rows('commission_members','commission',o['id'])
 if not members:raise ApiError('Inclua os integrantes da comissão.')
 result=[]
 for member in members:
  require_other(member);person=related(member,'responsible','assets','responsibles')
  if not person['data']['active']:raise ApiError('Comissão contém responsável inativo.')
  result.append({'responsible_id':person['id'],'name':person['name'],'cpf':person['data']['cpf'],'role':member['data']['role']})
 set_state(o,'Formalizada');return {'members':result}

def activate_asset(o,a,approved_source=None):
 require_draft(o)
 if approved_source is None:require_other(o)
 else:require_other(approved_source)
 if o['data'].get('capitalize'):require('finance','approve')
 validate_asset(o);d=o['data'];day=available(o,d['date']);before=snapshot(o)
 if d['type']=='Próprio':
  commission(o,'receipt_commission','Recebimento',day)
  if not d.get('responsible') or not d.get('location_ref'):raise ApiError('Selecione responsável e localização cadastrados antes de efetivar o ingresso.')
  if not d.get('ingress_type'):raise ApiError('Informe o tipo de ingresso.')
  if d['ingress_type']=='Aquisição':
   if not d.get('process') or not d.get('commitment') or not d.get('supplier') or not d.get('invoice'):raise ApiError('Aquisição exige processo, empenho, fornecedor e nota fiscal.')
   process=related(o,'process','procurement','processes');commitment=related(o,'commitment','finance','commitments')
   if process['state']!='Homologado' or commitment['state']!='Empenhado' or commitment['data']['supplier']!=d['supplier']:raise ApiError('Processo ou empenho incompatível com a aquisição.')
 p=new_position(o)
 if p['proration']=='Mês integral':
  acquired=date.fromisoformat(day);first_next=(month_last(acquired)+timedelta(days=1)).isoformat();p['cycle_start']=max(p['cycle_start'],first_next)
 o['state']='Ativo';entries,rule_id=posting(o,'Ingresso',p['gross'],day)
 return record(o,approved_source or o,day,'Ingresso','Ingresso patrimonial',before,p,entries,{'rule_id':rule_id,'approved_source':approved_source['id'] if approved_source else None})

def confirm_asset_receipt(o,a):
 p=position(o);day=available(o,a.get('date'));why=justification(a)
 if p['confirmed']:raise ApiError('Recebimento já conferido.',409)
 require_other(o);before=snapshot(o);p['confirmed']=True
 return record(o,o,day,'Conferência de recebimento',why,before,p,metadata={'responsible_id':g.user['id']})

def month_last(day):return day.replace(day=calendar.monthrange(day.year,day.month)[1])

def depreciation_amount(o,p,until,units=0):
 method=o['data']['method'];start=date.fromisoformat(p['cycle_start']);end=date.fromisoformat(until)
 if end<start:return 0
 available_value=max(0,p['gross']-p['residual']-p['accumulated']);base=p['cycle_base']-p['cycle_residual']
 if method=='Não depreciável' or o['data']['type']!='Próprio':return 0
 if method=='Unidades produzidas':
  if p['cycle_units']<=0 or units<0 or p['produced_units']+units>p['cycle_units']:raise ApiError('Produção excede o total estimado do ciclo.')
  target=rounded(Decimal(base)*(p['produced_units']+units)/p['cycle_units'])
 else:
  cursor=start.replace(day=1);weight=Decimal(0)
  while cursor<=end:
   last=month_last(cursor);first=max(start,cursor);cut=min(end,last)
   if p['proration']=='Mês integral':
    if cut==last:weight+=Decimal(1)
   else:weight+=Decimal((cut-first).days+1)/last.day
   cursor=(last+timedelta(days=1)).replace(day=1)
  target=rounded(Decimal(base)*min(weight,Decimal(p['cycle_months']))/p['cycle_months'])
 return min(available_value,max(0,target-p['cycle_accumulated']))

def depreciate_until(o,until,units=0,source=None,group_id=None,proportional=False):
 p=position(o);until=available(o,until)
 if not p['confirmed']:raise ApiError('Conclua a conferência do recebimento antes de depreciar.',409)
 if o['data']['type']!='Próprio' or o['data']['method']=='Não depreciável':raise ApiError('Bem não sujeito a depreciação.')
 if p.get('processed_through') and until<=p['processed_through']:raise ApiError('Data já depreciada no ciclo vigente.',409)
 if until<p['cycle_start']:raise ApiError('Data anterior ao início da depreciação.')
 before=snapshot(o);amount=depreciation_amount(o,p,until,units);p['accumulated']+=amount;p['cycle_accumulated']+=amount;p['produced_units']+=units;p['processed_through']=until;entries,rule_id=posting(o,'Depreciação',amount,until)
 return record(o,source or o,until,'Depreciação proporcional' if proportional else 'Depreciação','Depreciação de '+until[:7],before,p,entries,{'period':until[:7],'amount':amount,'units':units,'rule_id':rule_id},group_id=group_id)

def depreciate(o,a):
 p=position(o)
 if p['gross']-p['residual']-p['accumulated']<=0:raise ApiError('Bem atingiu o valor residual.',409)
 try:first=date.fromisoformat(str(a.get('period',''))+'-01')
 except ValueError:raise ApiError('Competência inválida.')
 today=local_time().date()
 if first>today:raise ApiError('Competência futura.')
 next_day=date.fromisoformat(p['processed_through'])+timedelta(days=1) if p.get('processed_through') else date.fromisoformat(p['cycle_start'])
 if first.strftime('%Y-%m')!=next_day.strftime('%Y-%m'):raise ApiError('Próxima competência: '+next_day.strftime('%Y-%m'),409)
 units=quantity(a.get('units','0'))
 if o['data']['method']=='Unidades produzidas' and units<=0:raise ApiError('Informe a produção do período.')
 end=min(month_last(first),today).isoformat();result=depreciate_until(o,end,units);p=result['position'];return {**result,'period':first.strftime('%Y-%m'),'amount':get_db().execute('SELECT metadata FROM asset_movements WHERE id=?',(result['movement_id'],)).fetchone()[0] and json.loads(get_db().execute('SELECT metadata FROM asset_movements WHERE id=?',(result['movement_id'],)).fetchone()[0])['amount'],'residual':p['residual'],'net':p['gross']-p['accumulated']}

def apply_asset_valuation(o,a):
 require_draft(o);require_other(o);require('finance','approve');d=o['data'];asset=related(o,'asset','assets','items');day=available(asset,d['date']);commission(o,'commission','Avaliação',day);p=position(asset);group=uuid.uuid4().hex
 if d['amount']<0 or d['useful_months']<=0:raise ApiError('Valor e vida útil da avaliação inválidos.')
 if asset['data']['type']!='Próprio':raise ApiError('Avaliação restrita a bens próprios.')
 if asset['data']['method']!='Não depreciável' and (not p.get('processed_through') or p['processed_through']<day) and day>=p['cycle_start']:
  depreciate_until(asset,day,d['units'],source=o,group_id=group,proportional=True);p=position(asset)
 before=snapshot(asset);old_net=p['gross']-p['accumulated'];delta=d['amount']-old_net
 if d['type']=='Redução ao valor recuperável' and delta>0:raise ApiError('Redução ao valor recuperável não admite aumento de valor.')
 c=related(asset,'class','assets','classes')['data'];entries=[]
 if asset['data'].get('capitalize'):entries+=pair(asset,c['depreciation_account'],c['asset_account'],p['accumulated'])
 extra,rule_id=posting(asset,'Reavaliação positiva' if delta>=0 else 'Redução de valor',abs(delta),day);entries+=extra
 asset['data'].update(amount=d['amount'],method=d['method'],total_units=d['total_units'],situation=d['situation'],residual_percent=d['residual_percent']);start=(date.fromisoformat(day)+timedelta(days=1)).isoformat();asset['data']['start']=start
 fresh=new_position(asset,gross=d['amount'],start=start,months=d['useful_months'],residual_percent=d['residual_percent']);fresh['confirmed']=p['confirmed']
 if fresh['proration']=='Mês integral':fresh['cycle_start']=(month_last(date.fromisoformat(day))+timedelta(days=1)).isoformat()
 if d['method']=='Unidades produzidas' and d['total_units']<=0:raise ApiError('Informe a produção estimada do novo ciclo.')
 result=record(asset,o,day,d['type'],d['report'],before,fresh,entries,{'old_gross':p['gross'],'old_accumulated':p['accumulated'],'old_net':old_net,'new_value':d['amount'],'delta':delta,'rule_id':rule_id},group_id=group);set_state(o,'Aplicado');return result

def apply_asset_complement(o,a):
 require_draft(o);require_other(o);require('finance','approve');d=o['data'];asset=related(o,'asset','assets','items');day=available(asset,d['date']);p=position(asset);before=snapshot(asset)
 if asset['data']['type']!='Próprio' or d['amount']<=0:raise ApiError('Complemento exige bem próprio e valor positivo.')
 links=rows('complement_commitments','complement',o['id'])
 if d['ingress_type']=='Aquisição' and (not links or not d.get('supplier') or not d.get('process')):raise ApiError('Aquisição exige fornecedor, processo e empenhos vinculados.')
 total=0
 for link in links:
  require_other(link);c=related(link,'commitment','finance','commitments')
  if c['state']!='Empenhado' or c['data']['supplier']!=d.get('supplier') or c['data']['date']>day:raise ApiError('Empenho incompatível com o valor complementar.')
  total+=link['data']['amount']
 if links and total!=d['amount']:raise ApiError('Valores vinculados aos empenhos devem somar o custo complementar.')
 # Preserve elapsed life: subsequent costs are distributed over the remaining useful life.
 elapsed=(date.fromisoformat(day).year-date.fromisoformat(p['cycle_start']).year)*12+date.fromisoformat(day).month-date.fromisoformat(p['cycle_start']).month
 remaining_months=max(1,p['cycle_months']-elapsed);new_net=p['gross']-p['accumulated']+d['amount'];cycle_start=(date.fromisoformat(day)+timedelta(days=1)).isoformat()
 if p['proration']=='Mês integral':cycle_start=(month_last(date.fromisoformat(day))+timedelta(days=1)).isoformat()
 p['gross']+=d['amount'];p.update(cycle_base=new_net,cycle_residual=p['residual'],cycle_start=cycle_start,cycle_months=remaining_months,cycle_accumulated=0,processed_through=None,cycle_units=max(0,p['cycle_units']-p['produced_units']),produced_units=0);asset['data']['amount']=p['gross'];entries,rule_id=posting(asset,'Valor complementar',d['amount'],day)
 result=record(asset,o,day,'Valor complementar',d['reason'],before,p,entries,{'amount':d['amount'],'rule_id':rule_id,'commitments':[{'id':l['data']['commitment'],'amount':l['data']['amount']} for l in links]});set_state(o,'Aplicado');return result

def reclassify_asset(o,a):
 require_other(o);require('finance','approve');day=available(o,a.get('date'));why=justification(a);p=position(o);before=snapshot(o);old=related(o,'class','assets','classes');new=load(integer(a.get('class'),'Classificação',1),'assets','classes');same_entity(o,new)
 if old['id']==new['id']:raise ApiError('Escolha outra classificação patrimonial.')
 entries=[]
 if o['data'].get('capitalize'):
  # Each leg keeps the accounting classification of its source or destination.
  for debit,credit,value,dr_class,cr_class in [(new['data']['asset_account'],old['data']['asset_account'],p['gross'],new['id'],old['id']),(old['data']['depreciation_account'],new['data']['depreciation_account'],p['accumulated'],old['id'],new['id'])]:
   if value:
    dr=account(debit,o);cr=account(credit,o)
    if dr!=cr:entries.extend([{'account_id':dr,'debit':value,'credit':0,'class_id':dr_class,'location':o['data']['location']},{'account_id':cr,'debit':0,'credit':value,'class_id':cr_class,'location':o['data']['location']}])
 o['data']['class']=new['id'];return record(o,o,day,'Reclassificação',why,before,p,entries,{'from':old['id'],'to':new['id']})

def writeoff_asset(o,a,source=None,inventory_id=None,group_id=None,fact='Baixa'):
 require_other(source or o);require('finance','approve');day=available(o,a.get('date'),inventory_id);why=justification(a);legal=str(a.get('legal_basis','')).strip();typ=str(a.get('type','')).strip()
 if len(legal)<5 or not typ:raise ApiError('Informe tipo da baixa e fundamento legal.')
 p=position(o);before=snapshot(o);entries=[];c=related(o,'class','assets','classes')['data']
 if o['data'].get('capitalize'):entries+=pair(o,c['depreciation_account'],c['asset_account'],p['accumulated'])
 extra,rule_id=posting(o,fact,p['gross']-p['accumulated'],day);entries+=extra;metadata={'type':typ,'legal_basis':legal,'gross':p['gross'],'accumulated':p['accumulated'],'net':p['gross']-p['accumulated'],'rule_id':rule_id};p['gross']=0;p['accumulated']=0;p['residual']=0;o['state']='Doado' if fact=='Doação concedida' else 'Baixado'
 return record(o,source or o,day,fact,why,before,p,entries,metadata,group_id=group_id)

def reverse_asset_event(o,a):
 require('assets','approve');require('finance','approve');why=justification(a);day=day_value(a.get('date'));events=active_events(o['id'])
 if not events:raise ApiError('Nenhum evento vigente para estornar.',409)
 last=events[-1];requested=integer(a.get('movement',last['id']),'Evento',1)
 if requested!=last['id']:raise ApiError('Estorne os eventos posteriores antes de corrigir este evento.',409)
 group=last['group_id'];members=get_db().execute('SELECT m.* FROM asset_movements m WHERE m.group_id=? AND m.reversal_of IS NULL AND NOT EXISTS(SELECT 1 FROM asset_movements r WHERE r.reversal_of=m.id) ORDER BY m.id DESC',(group,)).fetchall();ids={m['id'] for m in members};objects={};result=[];documents=set()
 for m in members:
  asset=load(m['asset_id'],'assets','items');objects[asset['id']]=asset
  from asset_core import locked
  if locked(asset):raise ApiError('Bem bloqueado por inventário.',409)
  if m['actor_id']==g.user['id']:raise ApiError('Estorno exige outro usuário autorizado, distinto do autor do evento.',403)
  active=active_events(asset['id'])
  if active[-1]['id'] not in ids:raise ApiError('Outro bem do evento possui movimento posterior; estorne-o primeiro.',409)
  if day<m['date']:raise ApiError('Estorno não pode anteceder o evento original.')
 for m in members:
  asset=objects[m['asset_id']];before=snapshot(asset);restore=json.loads(m['before_snapshot']);entries=[]
  for row in get_db().execute('SELECT l.*,a.class_id,a.location FROM asset_accounting_entries a JOIN erp_ledger l ON l.id=a.ledger_id WHERE a.movement_id=? ORDER BY l.id',(m['id'],)):entries.append({'account_id':row['account_id'],'debit':row['credit'],'credit':row['debit'],'class_id':row['class_id'],'location':row['location']})
  asset['data']=restore['data'];asset['state']=restore['state'];res=record(asset,asset,day,'Estorno',why,before,restore['position'],entries,{'original_event':m['id'],'original_source':m['source_id']},group_id=group+'-reversal',reversal_of=m['id']);result.append(res['movement_id'])
  if m['source_id']!=m['asset_id']:documents.add(m['source_id'])
 for id in documents:
  source=load(id)
  if source['module']=='assets' and source['kind'] not in ['items','inventories','inventory_items']:set_state(source,'Rascunho');event(source,'Evento estornado',{'asset':o['id'],'reason':why})
 return {'reversals':result}

OPERATIONS={f.__name__:f for f in [approve_asset_rule,retire_asset_rule,seal_asset_commission,activate_asset,confirm_asset_receipt,depreciate,apply_asset_valuation,apply_asset_complement,reclassify_asset,writeoff_asset,reverse_asset_event]}

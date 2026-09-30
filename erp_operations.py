import calendar,json
from datetime import date,datetime,timedelta
from decimal import Decimal
from flask import g
from auth import ApiError,require
from db import get_db,settings
from domain import now,local_time
from erp_core import (load,related,balance,change_balance,event,set_state,require_draft,require_other,check_period,cents,quantity,integer,rounded,decimal,create_object)
from erp_rules import supplier_allowed,inventory_locked

def positive(value):
 if value<=0:raise ApiError('O valor ou quantidade deve ser maior que zero.')
 return value

def run_operation(obj,op,args):
 from erp_catalog import CATALOG
 if op not in CATALOG[obj['module']]['resources'][obj['kind']].get('operations',[]):raise ApiError('Operação não disponível neste cadastro.')
 require(obj['module'],'write')
 handler=OPERATIONS[op];result=handler(obj,args) or {}
 # Operações que mantêm a situação também mudam a versão, evitando dupla execução concorrente.
 get_db().execute('UPDATE erp_objects SET version=version+1,updated_at=? WHERE id=?',(now(),obj['id']))
 event(obj,op,result);return result

def supplement(o,a):
 amount=positive(cents(a.get('amount')));change_balance(o['id'],'adjustment',amount);return {'amount':amount,'reason':reason(a)}
def reduce(o,a):
 amount=positive(cents(a.get('amount')))
 if amount>o['data']['initial']+balance(o['id'],'adjustment')-balance(o['id'],'committed'):raise ApiError('Redução maior que o saldo disponível.')
 change_balance(o['id'],'adjustment',-amount);return {'amount':amount,'reason':reason(a)}
def reason(a):
 text=str(a.get('reason','')).strip()
 if not 5<=len(text)<=2000:raise ApiError('Informe uma justificativa de 5 a 2.000 caracteres.')
 return text
def commit(o,a):
 require_draft(o);d=o['data'];check_period(o,d['date']);app=related(o,'appropriation','finance','appropriations');positive(d['amount']);supplier_allowed(related(o,'supplier','procurement','suppliers'),d['date'])
 if app['exercise']!=o['exercise']:raise ApiError('A dotação pertence a outro exercício.')
 available=app['data']['initial']+balance(app['id'],'adjustment')-balance(app['id'],'committed')
 if d['amount']>available:raise ApiError('Saldo orçamentário insuficiente.',409)
 change_balance(app['id'],'committed',d['amount']);set_state(o,'Empenhado');return {'amount':d['amount'],'remaining':available-d['amount']}
def cancel_commitment(o,a):
 if o['state']!='Empenhado' or balance(o['id'],'settled') or balance(o['id'],'supply_authorized'):raise ApiError('Somente empenhos sem liquidação podem ser anulados.',409)
 check_period(o,local_time().date().isoformat());why=reason(a);change_balance(o['data']['appropriation'],'committed',-o['data']['amount']);set_state(o,'Anulado');return {'reason':why}
def settle(o,a,supply_authorization=None):
 require_draft(o);d=o['data'];check_period(o,d['date']);c=related(o,'commitment','finance','commitments');positive(d['amount'])
 if c['state']!='Empenhado' or c['data']['date']>d['date']:raise ApiError('Empenho não efetivado ou posterior à liquidação.')
 if d['amount']>c['data']['amount']-balance(c['id'],'settled'):raise ApiError('Liquidação superior ao saldo do empenho.',409)
 from inventory_core import received_supply_value
 reserved=max(0,balance(c['id'],'supply_authorized')-received_supply_value(c['id']))
 if supply_authorization is None and d['amount']>c['data']['amount']-balance(c['id'],'settled')-reserved:raise ApiError('O saldo do empenho está reservado a autorizações de fornecimento pendentes.',409)
 if supply_authorization is not None and supply_authorization['data']['commitment']!=c['id']:raise ApiError('Autorização incompatível com o empenho.')
 duplicate=get_db().execute("SELECT 1 FROM erp_objects WHERE module='finance' AND kind='settlements' AND entity_id=? AND state='Liquidado' AND json_extract(data,'$.commitment')=? AND json_extract(data,'$.invoice')=?",(o['entity_id'],c['id'],d['invoice'])).fetchone()
 if duplicate:raise ApiError('Documento fiscal já liquidado neste empenho.',409)
 change_balance(c['id'],'settled',d['amount']);set_state(o,'Liquidado');return {'amount':d['amount']}
def pay(o,a):
 require_draft(o);d=o['data'];check_period(o,d['date']);s=related(o,'settlement','finance','settlements');b=related(o,'bank','finance','bank_accounts');positive(d['amount'])
 if s['state']!='Liquidado' or s['data']['date']>d['date']:raise ApiError('Liquidação inválida para pagamento.')
 if d['amount']>s['data']['amount']-balance(s['id'],'paid'):raise ApiError('Pagamento superior ao saldo da liquidação.',409)
 commitment=related(s,'commitment','finance','commitments');appropriation=related(commitment,'appropriation','finance','appropriations')
 if b['data']['fund']!=appropriation['data']['fund']:raise ApiError('Fonte da conta bancária divergente da despesa.')
 if d['amount']>b['data']['opening']+balance(b['id'],'net'):raise ApiError('Saldo bancário insuficiente.',409)
 change_balance(s['id'],'paid',d['amount']);change_balance(b['id'],'net',-d['amount']);set_state(o,'Pago');return {'amount':d['amount']}
def receive(o,a):
 require_draft(o);d=o['data'];check_period(o,d['date']);b=related(o,'bank','finance','bank_accounts')
 if b['data']['fund']!=d['fund']:raise ApiError('Fonte da receita divergente da conta bancária.')
 positive(d['amount']);net=d['amount']-d['deduction'];change_balance(b['id'],'net',net);set_state(o,'Arrecadado');return {'gross':d['amount'],'net':net}
def post_pair(o,day,debit,credit,amount,reversal=False):
 for account_id in [debit,credit]:
  account=load(account_id,'finance','accounts')
  if account['entity_id']!=o['entity_id'] or not account['data']['analytic'] or not account['data']['active']:raise ApiError('Contabilização exige contas analíticas ativas da entidade.')
 if debit==credit:raise ApiError('Débito e crédito não podem ser iguais.')
 for account,dr,cr in [(debit,amount,0),(credit,0,amount)]:get_db().execute('INSERT INTO erp_ledger(source_id,entity_id,exercise,date,account_id,debit,credit,reversal,created_at) VALUES(?,?,?,?,?,?,?,?,?)',(o['id'],o['entity_id'],o['exercise'],day,account,dr,cr,int(reversal),now()))
def post_journal(o,a):
 require_draft(o);d=o['data'];check_period(o,d['date']);positive(d['amount']);post_pair(o,d['date'],d['debit'],d['credit'],d['amount']);set_state(o,'Contabilizado');return {'debit':d['amount'],'credit':d['amount']}
def reverse_journal(o,a):
 if o['state']!='Contabilizado':raise ApiError('Lançamento não está disponível para estorno.',409)
 why=reason(a);day=str(a.get('date',''));check_day(day);check_period(o,day)
 if day<o['data']['date']:raise ApiError('O estorno não pode anteceder o fato original.')
 post_pair(o,day,o['data']['credit'],o['data']['debit'],o['data']['amount'],True);set_state(o,'Estornado');return {'reason':why,'date':day}
def check_day(day):
 try:date.fromisoformat(day)
 except (ValueError,TypeError):raise ApiError('Data inválida.')
def lock_period(o,a):require_draft(o);require(o['module'],'approve');check_period(o,o['data']['through']);set_state(o,'Fechado');return {'through':o['data']['through']}

def generate_occurrences(o,a):
 require_draft(o);d=o['data'];interval=integer(d['interval_months'],'Intervalo',1,120);count=integer(d['occurrences'],'Quantidade',1,120);first=date.fromisoformat(d['first_due']);ids=[]
 for i in range(count):
  year,month=divmod(first.year*12+first.month-1+i*interval,12);month+=1;day=min(first.day,calendar.monthrange(year,month)[1]);due=date(year,month,day).isoformat()
  occurrence=create_object('control','occurrences',o['entity_id'],year,{'code':f"{d['code']}-{i+1}",'name':d['name'],'obligation':o['id'],'due_date':due,'owner':d['owner']});ids.append(occurrence['id'])
 set_state(o,'Gerada');return {'occurrences':ids}
def close_occurrence(o,a):
 if o['state']=='Encerrado':raise ApiError('Ocorrência já encerrada.',409)
 why=reason(a);set_state(o,'Encerrado');return {'reason':why}
def reopen_occurrence(o,a):
 if o['state']!='Encerrado':raise ApiError('A ocorrência não está encerrada.',409)
 why=reason(a);set_state(o,'Reaberto');return {'reason':why}
def seal_report(o,a):require_draft(o);require_other(o);set_state(o,'Fechado');return {'snapshot':o['data']}

def calculate_opening(o,a):
 d=o['data'];require_draft(o)
 if not d.get('publication'):raise ApiError('Informe a data da publicação.')
 count=integer(d['business_days'],'Dias úteis',1,365);day=date.fromisoformat(d['publication']);holidays=settings()['holidays']
 while count:
  day+=timedelta(days=1)
  if day.weekday()<5 and day.isoformat() not in holidays:count-=1
 d['opening']=day.isoformat();get_db().execute('UPDATE erp_objects SET data=? WHERE id=?',(json.dumps(d,ensure_ascii=False),o['id']));return {'opening':d['opening']}
def advance_process(o,a):
 phases=['Habilitação','Julgamento'] if o['data'].get('inverted') else ['Julgamento','Habilitação']
 stages=['Rascunho','Edital','Divulgado',*phases,'Adjudicação','Homologado'];index=stages.index(o['state']) if o['state'] in stages else -1
 if index<0 or index==len(stages)-1:raise ApiError('Processo não pode avançar nesta situação.')
 target=stages[index+1];d=o['data']
 if target=='Divulgado' and (not d.get('publication') or not d.get('opening')):raise ApiError('Informe publicação e abertura.')
 if target in ['Adjudicação','Homologado']:
  require_other(o)
  if not d.get('legal_opinion'):raise ApiError('Parecer jurídico obrigatório antes da adjudicação.')
 if target=='Homologado':
  items=get_db().execute("SELECT id FROM erp_objects WHERE module='procurement' AND kind='items' AND json_extract(data,'$.process')=? AND deleted=0",(o['id'],)).fetchall()
  if not items:raise ApiError('O processo não contém itens.')
  for item in items:
   if not get_db().execute("SELECT 1 FROM erp_objects WHERE module='procurement' AND kind='proposals' AND state='Adjudicado' AND json_extract(data,'$.item')=?",(item['id'],)).fetchone():raise ApiError('Todos os itens devem ter uma proposta adjudicada.')
 set_state(o,target);return {'phase':target,'reason':reason(a)}
def award_proposal(o,a):
 require_draft(o);require_other(o);d=o['data'];item=related(o,'item','procurement','items');p=related(item,'process','procurement','processes');supplier_allowed(related(o,'supplier','procurement','suppliers'),local_time().date().isoformat())
 if p['state']!='Adjudicação' or not d['qualified']:raise ApiError('Processo deve estar em adjudicação e fornecedor habilitado.')
 if get_db().execute("SELECT 1 FROM erp_objects WHERE module='procurement' AND kind='proposals' AND state='Adjudicado' AND json_extract(data,'$.item')=?",(item['id'],)).fetchone():raise ApiError('Item já adjudicado.',409)
 value=d['unit_price'] if p['data']['judgment']=='Menor preço' else rounded(Decimal(item['data']['unit_price'])*(1-Decimal(d['discount'] or 0)/100))
 change_balance(o['id'],'awarded_value',rounded(Decimal(value)*item['data']['quantity']/1000000));set_state(o,'Adjudicado');return {'unit_price':value,'reason':reason(a)}
def activate_contract(o,a):
 require_draft(o);require_other(o);p=related(o,'process','procurement','processes')
 if p['state']!='Homologado':raise ApiError('O processo deve estar homologado.')
 if not get_db().execute("SELECT 1 FROM erp_objects proposal JOIN erp_objects item ON item.id=json_extract(proposal.data,'$.item') WHERE proposal.module='procurement' AND proposal.kind='proposals' AND proposal.state='Adjudicado' AND proposal.deleted=0 AND json_extract(proposal.data,'$.supplier')=? AND json_extract(item.data,'$.process')=?",(o['data']['supplier'],p['id'])).fetchone():raise ApiError('O fornecedor não possui item adjudicado neste processo.')
 supplier_allowed(related(o,'supplier','procurement','suppliers'),o['data']['start']);set_state(o,'Vigente');return {'value':o['data']['amount']}
def apply_amendment(o,a):
 require_draft(o);require_other(o);d=o['data'];c=related(o,'contract','procurement','contracts')
 if c['state']!='Vigente':raise ApiError('Contrato não está vigente.')
 delta=d['amount'] if d['type']=='Acréscimo' else -d['amount'] if d['type']=='Supressão' else 0
 if c['data']['amount']+balance(c['id'],'amendments')+delta<0:raise ApiError('Supressão superior ao valor do contrato.')
 if d['type']=='Prazo':
  if not d.get('end') or d['end']<=c['data']['end']:raise ApiError('O novo término deve ser posterior ao vigente.')
  c['data']['end']=d['end'];get_db().execute('UPDATE erp_objects SET data=?,version=version+1,updated_at=? WHERE id=?',(json.dumps(c['data']),now(),c['id']))
 change_balance(c['id'],'amendments',delta);set_state(o,'Aplicado');event(c,'Aditivo aplicado',{'amendment':o['id'],'delta':delta});return {'delta':delta}
def copy_pca(o,a):
 year=integer(a.get('exercise'),'Exercício de destino',2000,2100)
 if year==o['exercise']:raise ApiError('Escolha outro exercício.')
 from erp_core import serialize,spec
 fields=spec('procurement','pca')['fields']
 data={k:v for k,v in serialize(o)['data'].items() if k in fields}
 data['due_date']=None
 new=create_object('procurement','pca',o['entity_id'],year,data);return {'created_id':new['id'],'exercise':year}

def stock_row(warehouse,material):
 r=get_db().execute('SELECT quantity,value FROM erp_stock WHERE warehouse_id=? AND material_id=?',(warehouse,material)).fetchone();return dict(r) if r else {'quantity':0,'value':0}
def move_stock(o,warehouse,material,qty,value):
 old=stock_row(warehouse,material)
 last=get_db().execute('SELECT MAX(date) FROM erp_stock_ledger WHERE warehouse_id=? AND material_id=?',(warehouse,material)).fetchone()[0]
 if last and o['data']['date']<last:raise ApiError('Há movimento posterior deste material no almoxarifado. A nova movimentação deve preservar a ordem cronológica do custo médio.',409)
 if old['quantity']+qty<0 or old['value']+value<0:raise ApiError('Saldo de estoque insuficiente.',409)
 get_db().execute('INSERT INTO erp_stock VALUES(?,?,?,?) ON CONFLICT(warehouse_id,material_id) DO UPDATE SET quantity=excluded.quantity,value=excluded.value',(warehouse,material,old['quantity']+qty,old['value']+value))
 ledger_id=get_db().execute('INSERT INTO erp_stock_ledger(source_id,warehouse_id,material_id,date,quantity,value,created_at) VALUES(?,?,?,?,?,?,?)',(o['id'],warehouse,material,o['data']['date'],qty,value,now())).lastrowid
 from inventory_core import account_stock
 account_stock(o,warehouse,material,qty,value,ledger_id)
def stock_checks(o):
 d=o['data'];w=related(o,'warehouse','inventory','warehouses');m=related(o,'material','inventory','materials');check_period(o,d['date'])
 from inventory_core import object_access
 object_access(w)
 if w['data']['blocked'] or m['data']['obsolete']:raise ApiError('Almoxarifado bloqueado ou material obsoleto.',409)
 return w,m
def execute_stock(o,a):
 require_draft(o);d=o['data'];w,m=stock_checks(o);q=positive(d['quantity']);old=stock_row(w['id'],m['id']);amount=rounded(Decimal(q)*d['unit_price']/1000000)
 if d['type']=='Baixa de obsoleto':raise ApiError('Utilize a baixa de obsoleto com autorização e justificativa.')
 if d['type'] in ['Entrada','Devolução','Implantação']:
  if m['data']['expiry_control'] and (not d.get('expiry') or d['expiry']<d['date']):raise ApiError('Validade ausente ou anterior à entrada.')
  if d['type']=='Entrada' and d.get('invoice') and get_db().execute("SELECT 1 FROM erp_objects WHERE module='inventory' AND kind='movements' AND state='Efetivado' AND entity_id=? AND json_extract(data,'$.invoice')=? AND json_extract(data,'$.supplier') IS ? AND json_extract(data,'$.material')=?",(o['entity_id'],d['invoice'],d.get('supplier'),m['id'])).fetchone():raise ApiError('Documento/material já recebido.',409)
  if d['type']=='Entrada':
   from inventory_purchases import settle_purchase_movement
   settle_purchase_movement(o,amount)
  move_stock(o,w['id'],m['id'],q,amount);set_state(o,'Efetivado')
 else:
  if q>old['quantity']:raise ApiError('Quantidade superior ao saldo físico disponível.',409)
  amount=old['value'] if q==old['quantity'] else rounded(Decimal(old['value'])*q/old['quantity'])
  if d['type']=='Transferência':
   target=related(o,'destination','inventory','warehouses')
   if target['id']==w['id'] or target['data']['blocked']:raise ApiError('Destino inválido ou bloqueado.')
   change_balance(o['id'],'transit_quantity',q);change_balance(o['id'],'transit_value',amount);set_state(o,'Em trânsito')
  else:set_state(o,'Efetivado')
  move_stock(o,w['id'],m['id'],-q,-amount)
 return {'quantity':q,'value':amount,'state':o['state']}
def receive_transfer(o,a):
 if o['state']!='Em trânsito':raise ApiError('Transferência não está em trânsito.',409)
 target=related(o,'destination','inventory','warehouses');m=related(o,'material','inventory','materials')
 if target['data']['blocked'] or m['data']['obsolete']:raise ApiError('Destino bloqueado ou material obsoleto.')
 day=a.get('date') or o['data']['date'];check_day(day);check_period(o,day)
 if day<o['data']['date']:raise ApiError('Recebimento não pode anteceder a saída da transferência.')
 q=balance(o['id'],'transit_quantity');v=balance(o['id'],'transit_value');receipt={**o,'data':{**o['data'],'date':day}};move_stock(receipt,target['id'],m['id'],q,v);change_balance(o['id'],'transit_quantity',-q);change_balance(o['id'],'transit_value',-v);set_state(o,'Recebido');return {'quantity':q,'value':v,'received_at':day}
def adjust_stock(o,a):
 require_draft(o);require_other(o)
 from inventory_core import check_inventory_commission
 check_inventory_commission(o)
 w,m=stock_checks(o);old=stock_row(w['id'],m['id']);q=o['data']['quantity'];delta=q-old['quantity']
 if not old['quantity'] and q:raise ApiError('Implante uma entrada com valor unitário antes do ajuste positivo.')
 value=-old['value'] if q==0 else rounded(Decimal(old['value'])*q/old['quantity'])-old['value'] if old['quantity'] else 0
 move_stock(o,w['id'],m['id'],delta,value);set_state(o,'Ajustado');return {'quantity_difference':delta,'value_difference':value}

def depreciate(o,a):
 d=o['data'];period=str(a.get('period',''))
 try:month=datetime.strptime(period,'%Y-%m').date()
 except ValueError:raise ApiError('Competência inválida.')
 if inventory_locked(o):raise ApiError('Bem bloqueado por inventário em andamento.')
 if o['state']=='Baixado' or d['type']!='Próprio' or d['method']=='Não depreciável':raise ApiError('Bem não disponível para depreciação.')
 if period<d['start'][:7] or period>local_time().strftime('%Y-%m'):raise ApiError('Competência anterior ao início ou futura.')
 check_period(o,month.isoformat());c=related(o,'class','assets','classes');previous=get_db().execute('SELECT max(period) FROM erp_depreciation WHERE asset_id=?',(o['id'],)).fetchone()[0]
 if previous:
  y,m=map(int,previous.split('-'));expected=f'{y+(m==12):04}-{1 if m==12 else m+1:02}'
 else:expected=d['start'][:7]
 if period!=expected:raise ApiError('A depreciação deve seguir a sequência mensal; próxima competência: '+expected,409)
 residual=rounded(Decimal(d['amount'])*Decimal(c['data']['residual_percent'])/100);base=d['amount']-residual;remaining=base-balance(o['id'],'depreciated');units=0
 if remaining<=0:raise ApiError('Bem atingiu o valor residual.',409)
 if d['method']=='Quotas constantes':
  count=get_db().execute('SELECT count(*) FROM erp_depreciation WHERE asset_id=?',(o['id'],)).fetchone()[0]
  amount=remaining if count+1>=c['data']['useful_months'] else min(remaining,rounded(Decimal(base)/c['data']['useful_months']))
 else:
  units=positive(quantity(a.get('units')))
  if units+balance(o['id'],'produced_units')>d['total_units']:raise ApiError('Produção superior ao total estimado.')
  amount=remaining if units+balance(o['id'],'produced_units')==d['total_units'] else min(remaining,rounded(Decimal(base)*units/d['total_units']));change_balance(o['id'],'produced_units',units)
 if amount<=0:raise ApiError('Depreciação inferior a um centavo; revisar os parâmetros.')
 get_db().execute('INSERT INTO erp_depreciation(asset_id,period,amount,units,actor,created_at) VALUES(?,?,?,?,?,?)',(o['id'],period,amount,units,g.user['id'],now()));change_balance(o['id'],'depreciated',amount)
 return {'period':period,'amount':amount,'residual':residual,'net':d['amount']-balance(o['id'],'depreciated')}
def transfer_asset(o,a):
 if inventory_locked(o) or o['state']=='Baixado':raise ApiError('Bem indisponível para transferência.')
 location=str(a.get('location','')).strip();owner=str(a.get('owner','')).strip();why=reason(a)
 if not location or not owner or len(location)>250 or len(owner)>250:raise ApiError('Informe localização e responsável.')
 before=o['data']['location'];o['data'].update(location=location,owner=owner);get_db().execute('UPDATE erp_objects SET data=? WHERE id=?',(json.dumps(o['data'],ensure_ascii=False),o['id']));return {'from':before,'to':location,'owner':owner,'reason':why}
def writeoff_asset(o,a):
 require_other(o)
 if inventory_locked(o) or o['state']=='Baixado':raise ApiError('Bem indisponível para baixa.')
 why=reason(a);set_state(o,'Baixado');return {'reason':why,'net':o['data']['amount']-balance(o['id'],'depreciated')}
def open_inventory(o,a):
 require_draft(o)
 for row in get_db().execute("SELECT data FROM erp_objects WHERE entity_id=? AND module='assets' AND kind='inventories' AND state='Em andamento'",(o['entity_id'],)):
  if json.loads(row['data'])['location']==o['data']['location']:raise ApiError('Já existe inventário aberto na localização.')
 set_state(o,'Em andamento');return {'location':o['data']['location']}
def close_inventory(o,a):
 if o['state']!='Em andamento':raise ApiError('Inventário não está aberto.')
 why=reason(a);set_state(o,'Concluído');return {'reason':why}

def fleet_checks(o,day):
 v=related(o,'vehicle','fleet','vehicles');asset=related(v,'asset','assets','items')
 if asset['state']=='Baixado':raise ApiError('Veículo vinculado a bem baixado.')
 if v['data'].get('blocked_through') and day[:10]<=v['data']['blocked_through']:raise ApiError('Movimentação bloqueada nesse período.')
 check_period(o,day);return v
def register_trip(o,a):
 require_draft(o);d=o['data'];v=fleet_checks(o,d['departure']);driver=related(o,'driver','fleet','drivers');meter=max(v['data']['opening_meter'],balance(v['id'],'last_meter'))
 if d['start_meter']<meter or d['end_meter']<d['start_meter']:raise ApiError('Leitura incompatível com a cronologia do veículo.')
 if balance(v['id'],'last_timestamp') and int(datetime.fromisoformat(d['departure']).strftime('%Y%m%d%H%M'))<balance(v['id'],'last_timestamp'):raise ApiError('Movimento anterior ao último registro do veículo.')
 change_balance(v['id'],'last_meter',d['end_meter']-balance(v['id'],'last_meter'));change_balance(v['id'],'last_timestamp',int(datetime.fromisoformat(d['return']).strftime('%Y%m%d%H%M'))-balance(v['id'],'last_timestamp'));set_state(o,'Registrado');return {'distance':d['end_meter']-d['start_meter'],'warning':'CNH vencida na saída.' if driver['data']['expiry']<d['departure'][:10] else None}
def register_refuel(o,a):
 require_draft(o);d=o['data'];v=fleet_checks(o,d['date']);allowed=['Gasolina','Etanol'] if v['data']['fuel']=='Flex' else [v['data']['fuel']]
 if d['fuel'] not in allowed:raise ApiError('Combustível incompatível com o veículo.')
 positive(d['liters']);positive(d['unit_price'])
 if v['data']['tank_capacity'] and d['liters']>v['data']['tank_capacity']:raise ApiError('Volume superior à capacidade do tanque.')
 if d['meter']<max(v['data']['opening_meter'],balance(v['id'],'last_meter')):raise ApiError('Leitura anterior ao último movimento.')
 timestamp=int(datetime.fromisoformat(d['date']).strftime('%Y%m%d%H%M'))
 if timestamp<balance(v['id'],'last_timestamp'):raise ApiError('Data anterior ao último movimento.')
 amount=rounded(Decimal(d['liters'])*d['unit_price']/1000000);change_balance(v['id'],'last_meter',d['meter']-balance(v['id'],'last_meter'));change_balance(v['id'],'last_timestamp',timestamp-balance(v['id'],'last_timestamp'));change_balance(v['id'],'cost',amount);change_balance(o['id'],'cost',amount);set_state(o,'Registrado');return {'amount':amount}
def change_plate(o,a):
 new=str(a.get('plate','')).strip().upper();why=reason(a)
 if not new or len(new)>30:raise ApiError('Placa inválida.')
 old=o['code'];o['data']['code']=new;get_db().execute('UPDATE erp_objects SET code=?,data=? WHERE id=?',(new,json.dumps(o['data']),o['id']));return {'previous':old,'current':new,'reason':why}
def close_service(o,a):
 require_draft(o);v=fleet_checks(o,o['data']['date']);change_balance(v['id'],'cost',o['data']['amount']);set_state(o,'Concluído');return {'cost':o['data']['amount']}

def grant_benefit(o,a):
 require_draft(o);require_other(o);d=o['data'];b=related(o,'benefit','social','benefits');day=date.fromisoformat(d['date']);count=0
 for r in get_db().execute("SELECT data FROM erp_objects WHERE entity_id=? AND module='social' AND kind='concessions' AND state='Concedido' AND deleted=0",(o['entity_id'],)):
  x=json.loads(r['data'])
  if x['benefit']!=b['id']:continue
  count+=1
  if x['person']==d['person'] and (day-date.fromisoformat(x['date'])).days<b['data']['interval_days']:raise ApiError('Intervalo mínimo do benefício não cumprido.',409)
 if b['data']['capacity'] and count>=b['data']['capacity']:raise ApiError('Limite de concessões atingido.')
 from erp_social_operations import issue_benefit_stock
 movement=issue_benefit_stock(o,b)
 change_balance(o['id'],'granted_value',b['data']['amount']);set_state(o,'Concedido');return {'amount':b['data']['amount'],'stock_movement':movement}
def review_accounts(o,a):
 require_draft(o);require_other(o);d=o['data']
 if not d.get('opinion'):raise ApiError('Registre o parecer técnico antes da homologação.')
 remaining=d['opening']+d['transfers']+d['interest']+d['counterpart']-d['expenses'];change_balance(o['id'],'remaining',remaining);set_state(o,'Homologado');return {'remaining':remaining}

def approve_diary(o,a):require_draft(o);require_other(o);set_state(o,'Aprovado');return {'date':o['data']['date']}
def measurement_value(item,q):
 d=item['data'];return rounded(Decimal(q)*d['unit_price']/1000000*(1+Decimal(d['bdi'] or 0)/100)*(1-Decimal(d['discount'] or 0)/100))
def submit_measurement(o,a):
 require_draft(o);d=o['data'];item=related(o,'item','works','items');project=related(o,'project','works','projects')
 if item['data']['project']!=project['id']:raise ApiError('Item pertence a outra obra.')
 if d['quantity']+balance(item['id'],'measured_quantity')>item['data']['quantity']:raise ApiError('A medição excede 100% do item contratado.',409)
 if not get_db().execute("SELECT 1 FROM erp_objects WHERE module='works' AND kind='diaries' AND state='Aprovado' AND json_extract(data,'$.project')=? AND json_extract(data,'$.date') BETWEEN ? AND ?",(project['id'],d['start'],d['end'])).fetchone():raise ApiError('O período precisa de diário de obra aprovado.')
 previous=get_db().execute("SELECT max(json_extract(data,'$.end')) FROM erp_objects WHERE module='works' AND kind='measurements' AND state IN ('Submetido','Aprovado') AND json_extract(data,'$.item')=?",(item['id'],)).fetchone()[0]
 if previous and d['start']<=previous:raise ApiError('A medição deve ser posterior ao período anterior do item.')
 change_balance(item['id'],'measured_quantity',d['quantity']);amount=measurement_value(item,d['quantity']);change_balance(o['id'],'measured_amount',amount);change_balance(project['id'],'measured_amount',amount);set_state(o,'Submetido');return {'amount':amount,'cumulative_quantity':balance(item['id'],'measured_quantity')}
def approve_measurement(o,a):
 if o['state']!='Submetido':raise ApiError('Submeta a medição antes da aprovação.')
 require_other(o);set_state(o,'Aprovado');return {'amount':balance(o['id'],'measured_amount')}
def pay_measurement(o,a):
 require_draft(o);require(o['module'],'approve');d=o['data'];m=related(o,'measurement','works','measurements');p=related(m,'project','works','projects');positive(d['amount']);check_period(o,d['date'])
 if m['state']!='Aprovado' or d['date']<m['data']['end']:raise ApiError('A medição não está aprovada ou a data antecede o período medido.')
 paid=balance(m['id'],'paid');measured=balance(m['id'],'measured_amount')
 if d['amount']>measured-paid:raise ApiError('Pagamento superior ao saldo da medição.',409)
 if d['type']=='Medição' and paid:raise ApiError('A medição já teve pagamento; utilize liberação de retenção.')
 if d['type']=='Retenção':
  if not paid or not p['data'].get('completed_date'):raise ApiError('Liberação de retenção exige pagamento anterior e recebimento definitivo da obra.')
  due=date.fromisoformat(str(p['data']['completed_date'])[:10])+timedelta(days=int(p['data'].get('retention_days') or 0))
  if date.fromisoformat(d['date'])<due:raise ApiError('Prazo de liberação da retenção ainda não cumprido.')
 change_balance(m['id'],'paid',d['amount']);change_balance(p['id'],'paid',d['amount']);set_state(o,'Pago');return {'amount':d['amount'],'retention':measured-paid-d['amount']}
def prepare_exchange(o,a):
 require_draft(o);p=related(o,'process','procurement','processes');set_state(o,'Preparado');return {'provider':o['data']['provider'],'process':p['data'],'delivery':'Não transmitido. Conector homologado e credenciais necessários.'}

from works_operations import linear_adjustment, close_project
from procurement_operations import summon_remaining_bidders, register_bid, approve_pca, reject_pca, publish_pca_pncp, generate_price_agreement, register_carona, apply_procurement_amendment
OPERATIONS={name:globals()[name] for name in ['supplement','reduce','commit','cancel_commitment','settle','pay','receive','post_journal','reverse_journal','lock_period','generate_occurrences','close_occurrence','reopen_occurrence','seal_report','calculate_opening','advance_process','award_proposal','activate_contract','apply_amendment','copy_pca','execute_stock','receive_transfer','adjust_stock','depreciate','transfer_asset','writeoff_asset','open_inventory','close_inventory','register_trip','register_refuel','change_plate','close_service','grant_benefit','review_accounts','approve_diary','submit_measurement','approve_measurement','pay_measurement','prepare_exchange','linear_adjustment','close_project','summon_remaining_bidders','register_bid','approve_pca','reject_pca','publish_pca_pncp','generate_price_agreement','register_carona','apply_procurement_amendment']}

"""Regras de integridade dos cadastros; nenhum cálculo tributário é presumido."""
import json
from datetime import date
from auth import ApiError
from db import get_db
from erp_core import related,load,balance

def others(obj,module=None,kind=None):
 return get_db().execute('SELECT * FROM erp_objects WHERE entity_id=? AND module=? AND kind=? AND deleted=0 AND id<>?',(obj['entity_id'],module or obj['module'],kind or obj['kind'],obj.get('id',0))).fetchall()

def supplier_allowed(supplier,day):
 d=supplier['data']
 if d.get('blocked_from') and d['blocked_from']<=day and (not d.get('blocked_until') or day<=d['blocked_until']):raise ApiError('Fornecedor impedido de contratar na data da operação.',409)

def validate_business(obj):
 m,k,d=obj['module'],obj['kind'],obj['data']
 if m=='inventory':
  from inventory_core import validate_inventory
  validate_inventory(obj)
 if m=='assets':
  from asset_core import validate_asset
  validate_asset(obj)
 if m=='fleet':
  from fleet_core import validate_fleet
  validate_fleet(obj)
 if m=='finance':
  if k in ['commitments','settlements','payments','receipts','journals'] and d['date'][:4]!=str(obj['exercise']):raise ApiError('A data deve pertencer ao exercício do registro.')
  if k=='plans' and (d['end_year']<d['start_year'] or (d['type']=='PPA' and d['end_year']-d['start_year']!=3)):raise ApiError('O PPA deve abranger quatro exercícios; confira o período.')
  if k=='appropriations' and obj.get('id') and balance(obj['id'],'committed')>d['initial']+balance(obj['id'],'adjustment'):raise ApiError('Valor inicial inferior ao total já comprometido.')
  if k=='bank_accounts' and obj.get('id') and d['opening']+balance(obj['id'],'net')<0:raise ApiError('Saldo inicial não pode deixar a conta negativa.')
  if k=='journals' and d['debit']==d['credit']:raise ApiError('Débito e crédito devem utilizar contas diferentes.')
  if k=='receipts' and d['deduction']>d['amount']:raise ApiError('A dedução não pode superar a arrecadação.')
 if m=='people':
  if k=='employees':
   position=related(obj,'position','people','positions')
   count=sum(json.loads(r['data']).get('active') and json.loads(r['data']).get('position')==position['id'] for r in others(obj))
   if d['active'] and count>=position['data']['vacancies']:raise ApiError('Não há vaga disponível para este cargo.',409)
  if k=='events' and get_db().execute("SELECT 1 FROM erp_objects WHERE entity_id=? AND module='people' AND kind='runs' AND state IN ('Calculado','Aprovado') AND json_extract(data,'$.period')=?",(obj['entity_id'],d['period'])).fetchone():raise ApiError('Competência já calculada: novos movimentos exigem reabertura controlada.',409)
  if k=='tax_bands' and related(obj,'rules','people','rules')['state']=='Aprovado':raise ApiError('Parâmetros aprovados não aceitam inclusão ou alteração de faixas.',409)
  if k=='tax_bands' and d['upper'] and d['upper']<=d['lower']:raise ApiError('Limites da faixa inválidos.')
  if k=='leaves':
   for row in others(obj):
    x=json.loads(row['data'])
    if x['employee']==d['employee'] and x['start']<=d['end'] and d['start']<=x['end']:raise ApiError('Já existe afastamento no período para o servidor.',409)
 if m=='procurement':
  if k=='processes' and d.get('inverted') and not d.get('technical_opinion'):raise ApiError('A inversão de fases exige motivação no parecer técnico.')
  if k=='suppliers':
   if any(json.loads(r['data'])['document']==d['document'] for r in others(obj)):raise ApiError('CPF/CNPJ já cadastrado nesta entidade.',409)
  if k=='items':
   process=related(obj,'process','procurement','processes')
   if process['state'] in ['Adjudicação','Homologado']:raise ApiError('Itens bloqueados após a adjudicação.',409)
  if k=='contracts':supplier_allowed(related(obj,'supplier','procurement','suppliers'),d['start'])
 if m=='social':
  if k=='persons' and d.get('cpf') and any(json.loads(r['data']).get('cpf')==d['cpf'] for r in others(obj)):raise ApiError('CPF já cadastrado nesta entidade.',409)
  if k=='members' and any(json.loads(r['data'])['person']==d['person'] for r in others(obj)):raise ApiError('Pessoa já vinculada a uma família.',409)
  if k=='benefits' and d.get('material') and d.get('units',0)<=0:raise ApiError('Benefício com insumo exige quantidade positiva.')
  if k=='appointments':
   from db import settings
   if d['start'][:10] in settings()['holidays']:raise ApiError('Agendamento bloqueado por feriado cadastrado.')
   if d['start']>=d['end']:raise ApiError('Informe um intervalo válido.')
   for row in others(obj):
    x=json.loads(row['data'])
    if row['state']=='Cancelado':continue
    if (x['professional']==d['professional'] or x['person']==d['person']) and x['start']<d['end'] and d['start']<x['end']:raise ApiError('Profissional ou pessoa já possui agendamento neste horário.',409)
  if k=='accounts' and d['expenses']>d['opening']+d['transfers']+d['interest']+d['counterpart']:raise ApiError('Despesas superiores aos recursos disponíveis.')
 if m=='works':
  if k=='projects':
   if d.get('latitude') and not -90<=float(d['latitude'])<=90:raise ApiError('Latitude inválida.')
  if k=='measurements':
   item=related(obj,'item','works','items')
   if item['data']['project']!=d['project']:raise ApiError('O item da planilha pertence a outra obra.')
   if d['quantity']<=0:raise ApiError('A quantidade executada deve ser positiva.')
  if k=='items' and obj.get('id') and balance(obj['id'],'measured_quantity'):raise ApiError('Item com medição: alteração depende de revisão de planilha com preservação dos saldos.',409)

def inventory_locked(asset):
 for r in get_db().execute("SELECT data FROM erp_objects WHERE entity_id=? AND module='assets' AND kind='inventories' AND state='Em andamento' AND deleted=0",(asset['entity_id'],)):
  if json.loads(r['data'])['location']==asset['data']['location']:return True
 return False

"""Integridade, autorização e contabilização transacional do almoxarifado."""
import json,re
from decimal import Decimal
from flask import g
from auth import ApiError,require
from db import get_db
from domain import now
from erp_core import load,related,check_period,require_draft,require_other,set_state,event,balance,rounded

def children(kind,field,id):
 rows=get_db().execute("SELECT id FROM erp_objects WHERE module='inventory' AND kind=? AND deleted=0 AND json_extract(data,?)=? ORDER BY id",(kind,'$.'+field,id)).fetchall()
 return [load(r['id']) for r in rows]

def object_access(target,blocked=True):
 if target['module']!='inventory' or target['kind'] not in ['warehouses','departments']:raise ApiError('Unidade de estoque inválida.')
 if target['kind']=='warehouses' and blocked and target['data']['blocked']:raise ApiError('Almoxarifado bloqueado para registros e movimentações.',409)
 if target['kind']=='departments' and not target['data'].get('active'):raise ApiError('Órgão requisitante inativo.',409)
 if g.user['group_id']==1:return
 row=get_db().execute('SELECT allowed FROM inventory_permissions WHERE target_id=? AND user_id=?',(target['id'],g.user['id'])).fetchone()
 if (row and not row['allowed']) or (not row and target['data'].get('restricted')):raise ApiError('Usuário sem autorização para movimentar ou requisitar nesta unidade.',403)

def same_year(o,target):
 if target['entity_id']!=o['entity_id'] or target['exercise']!=o['exercise']:raise ApiError('Vínculo de outra entidade ou exercício.')

def ancestors(center):
 result=[];seen=set()
 while center:
  if center['id'] in seen:raise ApiError('Hierarquia de centros de custo possui ciclo.')
  seen.add(center['id']);result.append(center['id']);center=load(center['data']['parent']) if center['data'].get('parent') else None
 return result

def validate_policy(d):
 if d.get('model')=='Consumo mensal':
  if not 1<=d['history_months']<=120 or not 1<=d['minimum_months']<=d['maximum_months']<=120:raise ApiError('Configure de 1 a 120 meses de histórico e cobertura, com máximo maior ou igual ao mínimo.')
 elif d.get('model')=='Quantidade':
  if not d['minimum']<=d['average']<=d['maximum']:raise ApiError('Estoque mínimo, médio e máximo devem estar em ordem crescente.')

def validate_inventory(o):
 k,d=o['kind'],o['data'];db=get_db();id=o.get('id',0)
 if k=='materials':
  from inventory_classifications import validate_material
  validate_material(d)
 if k in ['requisition_items','authorization_items','invoice_items','commission_members'] and id:
  old=json.loads(db.execute('SELECT data FROM erp_objects WHERE id=?',(id,)).fetchone()[0]);field={'requisition_items':'requisition','authorization_items':'authorization','invoice_items':'invoice','commission_members':'commission'}[k]
  if load(old[field])['state']!='Rascunho':raise ApiError('Documento já formalizado: não é permitido trocar o vínculo de seus itens.',409)
 from erp_catalog import CATALOG
 for field,spec in CATALOG['inventory']['resources'][k]['fields'].items():
  if spec['type']=='reference' and d.get(field):same_year(o,load(d[field]))
 if k in ['movements','counts','locations','policies','requisitions','authorizations','purchase_links']:object_access(related(o,'warehouse','inventory','warehouses'))
 if k in ['warehouses','departments'] and not id and d.get('restricted'):require('users','write')
 if k in ['warehouses','departments'] and id:
  old=json.loads(db.execute('SELECT data FROM erp_objects WHERE id=?',(id,)).fetchone()[0])
  if old.get('restricted',False)!=d.get('restricted',False):require('users','write')
 if k in ['warehouses','policies']:validate_policy(d)
 if k=='movements' and d.get('destination') and load(d['destination'])['data']['blocked']:raise ApiError('Destino bloqueado para registro de transferência.',409)
 if k=='policies' and db.execute("SELECT 1 FROM erp_objects WHERE module='inventory' AND kind='policies' AND deleted=0 AND id<>? AND json_extract(data,'$.warehouse')=? AND json_extract(data,'$.material')=?",(id,d['warehouse'],d['material'])).fetchone():raise ApiError('Já existe regra para este material neste almoxarifado.',409)
 if k=='cost_centers' and d.get('parent'):
  parent=load(d['parent']);same_year(o,parent)
  if id in ancestors(parent) or parent['data']['department']!=d['department']:raise ApiError('Centro superior inválido ou vinculado a outro órgão.')
 if k=='commissions' and (d['publication']>d['end'] or d['start']>d['end']):raise ApiError('Publicação posterior ao fim da vigência.')
 if k=='commission_members':
  commission=related(o,'commission','inventory','commissions')
  if commission['state']!='Rascunho':raise ApiError('Comissão formalizada não admite alteração dos integrantes.',409)
  if any(x['id']!=id and x['data']['cpf']==d['cpf'] for x in children('commission_members','commission',commission['id'])):raise ApiError('Integrante já cadastrado nesta comissão.',409)
 if k=='accounting_rules':
  require('finance','write')
  if d['debit']==d['credit']:raise ApiError('Contas contábeis devem ser distintas.')
  for field in ['debit','credit']:
   a=related(o,field,'finance','accounts');same_year(o,a)
   if not a['data']['analytic'] or not a['data']['active']:raise ApiError('Selecione contas analíticas ativas.')
 if k=='quotas':
  if bool(d.get('material'))==bool(d.get('material_group')):raise ApiError('Defina a cota por material ou por grupo, exclusivamente.')
  if not d['quantity'] and not d['amount']:raise ApiError('Informe limite quantitativo ou financeiro.')
  if d['period'][:4]!=str(o['exercise']):raise ApiError('Competência da cota fora do exercício.')
 if k=='requisitions':
  object_access(related(o,'department','inventory','departments'))
  if related(o,'cost_center','inventory','cost_centers')['data']['department']!=d['department']:raise ApiError('Centro de custo de outro órgão requisitante.')
  check_period(o,d['date'])
 if k in ['requisition_items','authorization_items','invoice_items']:
  field={'requisition_items':'requisition','authorization_items':'authorization','invoice_items':'invoice'}[k]
  parent=load(d[field]);same_year(o,parent)
  if parent['state']!='Rascunho':raise ApiError('Documento já aprovado ou efetivado: itens não podem ser alterados.',409)
  if parent['kind']=='requisitions':object_access(load(parent['data']['department']))
  if parent['data'].get('warehouse'):object_access(load(parent['data']['warehouse']))
  if parent['kind']=='invoices' and parent['data'].get('authorization'):object_access(load(load(parent['data']['authorization'])['data']['warehouse']))
  if d['quantity']<=0:raise ApiError('Quantidade deve ser positiva.')
  if k!='requisition_items' and d['unit_price']<=0:raise ApiError('Preço unitário deve ser positivo.')
 if k=='requisition_items' and any(x['id']!=id and x['data']['material']==d['material'] for x in children('requisition_items','requisition',d['requisition'])):raise ApiError('Material já consta nesta requisição. Ajuste a quantidade do item existente.',409)
 if k=='authorization_items':
  authorization=load(d['authorization']);item=related(o,'procurement_item','procurement','items')
  if item['data']['process']!=authorization['data']['process']:raise ApiError('Item não pertence ao processo da autorização.')
  if any(x['id']!=id and x['data']['procurement_item']==d['procurement_item'] for x in children('authorization_items','authorization',d['authorization'])):raise ApiError('Item da contratação já consta nesta autorização.',409)
 if k=='invoices':
  if d['issued_at']>d['date']:raise ApiError('Recebimento não pode anteceder a emissão da nota.')
  check_period(o,d['date'])
  if d.get('access_key') and not re.fullmatch(r'[0-9]{44}',d['access_key']):raise ApiError('Chave eletrônica deve conter 44 dígitos.')
  if db.execute("SELECT 1 FROM erp_objects WHERE module='inventory' AND kind='invoices' AND deleted=0 AND entity_id=? AND id<>? AND json_extract(data,'$.supplier')=? AND json_extract(data,'$.number')=? AND json_extract(data,'$.series')=? AND json_extract(data,'$.model')=?",(o['entity_id'],id,d['supplier'],d['number'],d['series'],d['model'])).fetchone():raise ApiError('Nota fiscal já registrada para este emitente, número, série e modelo.',409)
  if d.get('access_key') and db.execute("SELECT 1 FROM erp_objects WHERE module='inventory' AND kind='invoices' AND deleted=0 AND entity_id=? AND id<>? AND json_extract(data,'$.access_key')=?",(o['entity_id'],id,d['access_key'])).fetchone():raise ApiError('Chave de nota fiscal já registrada.',409)
  if d['type']=='Material' and not d.get('authorization'):raise ApiError('Nota de materiais exige autorização de fornecimento.')
  if d['type']!='Material' and not d.get('commitment'):raise ApiError('Informe o empenho do serviço ou bem patrimonial.')
  if d.get('authorization'):
   if d['type']!='Material':raise ApiError('Autorização de materiais não pode ser usada para serviço ou bem patrimonial.')
   a=related(o,'authorization','inventory','authorizations');object_access(load(a['data']['warehouse']))
   if d['date']<a['data']['date']:raise ApiError('Recebimento anterior à autorização de fornecimento.')
   if a['state'] not in ['Autorizado','Parcialmente recebido'] or a['data']['supplier']!=d['supplier']:raise ApiError('Autorização indisponível ou de outro fornecedor.')
 if k=='invoice_items':
  inv=load(d['invoice'])
  if inv['data']['type']=='Material':
   if not d.get('authorization_item'):raise ApiError('Selecione o item autorizado.')
   item=related(o,'authorization_item','inventory','authorization_items')
   if item['data']['authorization']!=inv['data']['authorization'] or d.get('material')!=item['data']['material']:raise ApiError('Material ou item não corresponde à autorização da nota.')
   if d['unit_price']!=item['data']['unit_price']:raise ApiError('Preço diverge do item autorizado.')
  if inv['data']['type']=='Bem patrimonial' and (not d.get('asset_class') or not d.get('asset_owner') or not d.get('asset_location') or d['quantity']%1000000):raise ApiError('Bem patrimonial exige classificação, responsável, localização e quantidade inteira.')

def approve_stock_accounting(o,a):
 require_draft(o);require_other(o);require('finance','approve');validate_inventory(o);d=o['data']
 if get_db().execute("SELECT 1 FROM erp_objects WHERE module='inventory' AND kind='accounting_rules' AND deleted=0 AND entity_id=? AND exercise=? AND state='Aprovado' AND json_extract(data,'$.fact')=? AND json_extract(data,'$.warehouse') IS ?",(o['entity_id'],o['exercise'],d['fact'],d.get('warehouse'))).fetchone():raise ApiError('Encerre a regra vigente antes de aprovar sua substituição.',409)
 set_state(o,'Aprovado');return {'fact':d['fact']}

def retire_stock_accounting(o,a):
 require('finance','approve');require_other(o)
 if o['state']!='Aprovado':raise ApiError('Regra não está vigente.',409)
 from erp_operations import reason
 why=reason(a);set_state(o,'Encerrado');return {'reason':why}

def seal_stock_commission(o,a):
 require_draft(o);require_other(o);members=children('commission_members','commission',o['id'])
 if not members:raise ApiError('Cadastre os integrantes da comissão.')
 for member in members:require_other(member)
 set_state(o,'Formalizada');return {'members':[{'name':m['name'],'cpf':m['data']['cpf'],'position':m['data']['position']} for m in members]}

def received_supply_value(commitment_id):
 return get_db().execute("SELECT COALESCE(SUM(p.amount),0) FROM inventory_invoice_postings p JOIN erp_objects i ON i.id=p.invoice_id JOIN erp_objects a ON a.id=json_extract(i.data,'$.authorization') WHERE json_extract(a.data,'$.commitment')=?",(commitment_id,)).fetchone()[0]

def account_stock(o,warehouse,material,qty,value,ledger_id):
 check_period(o,o['data']['date']);db=get_db();w=load(warehouse,'inventory','warehouses');object_access(w)
 typ=o['data'].get('type')
 fact=('Ganho de inventário' if value>0 else 'Perda de inventário') if o['kind']=='counts' else 'Trânsito de saída' if typ=='Transferência' and qty<0 else 'Trânsito de entrada' if typ=='Transferência' else 'Entrada' if typ=='Implantação' else typ
 if fact not in ['Entrada','Saída','Trânsito de saída','Trânsito de entrada','Devolução','Ganho de inventário','Perda de inventário','Baixa de obsoleto']:raise ApiError('Fato de estoque sem classificação contábil.')
 row=db.execute("SELECT id FROM erp_objects WHERE entity_id=? AND exercise=? AND module='inventory' AND kind='accounting_rules' AND state='Aprovado' AND deleted=0 AND json_extract(data,'$.fact')=? AND (json_extract(data,'$.warehouse')=? OR json_extract(data,'$.warehouse') IS NULL) ORDER BY json_extract(data,'$.warehouse') IS NULL LIMIT 1",(o['entity_id'],o['exercise'],fact,warehouse)).fetchone()
 if not row:raise ApiError('Configure e aprove a regra contábil de estoque para '+fact+'. Nenhuma movimentação foi efetivada.',409)
 rule=load(row['id']);d=rule['data'];entries=[]
 for field in ['debit','credit']:
  account=load(d[field],'finance','accounts',check_access=False);same_year(o,account)
  if not account['data']['analytic'] or not account['data']['active']:raise ApiError('Conta da regra contábil está inativa ou não analítica.',409)
  entries.append(db.execute('INSERT INTO erp_ledger(source_id,entity_id,exercise,date,account_id,debit,credit,reversal,created_at) VALUES(?,?,?,?,?,?,?,?,?)',(o['id'],o['entity_id'],o['exercise'],o['data']['date'],account['id'],abs(value) if field=='debit' else 0,abs(value) if field=='credit' else 0,0,now())).lastrowid)
 db.execute('INSERT INTO inventory_accounting VALUES(?,?,?,?,?)',(ledger_id,rule['id'],*entries,now()))

def check_inventory_commission(o):
 if not o['data'].get('commission_order'):raise ApiError('Vincule uma comissão formalizada com portaria, vigência e integrantes.')
 commission=related(o,'commission_order','inventory','commissions');d=commission['data']
 if commission['state']!='Formalizada' or not d['start']<=o['data']['date']<=d['end'] or d['publication']>o['data']['date']:raise ApiError('Comissão não formalizada ou fora da vigência do inventário.')
 return commission

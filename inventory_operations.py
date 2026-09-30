"""Entrega, devolução e recebimento financeiro com quantidades e valores exatos."""
import json
from decimal import Decimal
from flask import g
from auth import ApiError,require
from db import get_db,notify
from domain import now
from erp_core import load,related,balance,change_balance,set_state,require_draft,require_other,create_object,event,rounded,quantity,integer,check_period
from inventory_core import children,object_access,same_year,ancestors
from inventory_purchases import approve_purchase_link,cancel_purchase_link,check_authorization_link,check_cancellation

def units(q):return str(Decimal(q)/1000000)
def reais(v):return str(Decimal(v)/100)
def total(d):return rounded(Decimal(d['quantity'])*d['unit_price']/1000000)
def remaining(item,prefix):return item['data']['quantity']-balance(item['id'],prefix)-balance(item['id'],'cancelled')

def quota_alerts(request,items):
 centers=ancestors(related(request,'cost_center','inventory','cost_centers'));db=get_db();alerts=[]
 quotas=db.execute("SELECT id FROM erp_objects WHERE entity_id=? AND exercise=? AND module='inventory' AND kind='quotas' AND deleted=0 AND json_extract(data,'$.period')=?",(request['entity_id'],request['exercise'],request['data']['date'][:7])).fetchall()
 for row in quotas:
  quota=load(row['id']);q=quota['data']
  if q['cost_center'] not in centers:continue
  current_q=current_v=0;used_q=used_v=0
  def matches(item):
   material=load(item['data']['material'])
   return material['id']==q['material'] if q.get('material') else material['data'].get('group')==q['material_group']
  for line in items:
   if matches(line):current_q+=line['data']['quantity'];current_v+=total(line['data'])
  for row in db.execute("SELECT id FROM erp_objects WHERE entity_id=? AND exercise=? AND module='inventory' AND kind='requisitions' AND deleted=0 AND state<>'Rascunho' AND id<>? AND substr(json_extract(data,'$.date'),1,7)=?",(request['entity_id'],request['exercise'],request['id'],q['period'])):
   previous=load(row['id'])
   if q['cost_center'] not in ancestors(load(previous['data']['cost_center'])):continue
   for line in children('requisition_items','requisition',previous['id']):
    if matches(line):
     amount=line['data']['quantity']-balance(line['id'],'cancelled');used_q+=amount;used_v+=rounded(Decimal(amount)*line['data']['unit_price']/1000000)
  if (q['quantity'] and current_q+used_q>q['quantity']) or (q['amount'] and current_v+used_v>q['amount']):alerts.append({'quota_id':quota['id'],'quota':quota['name'],'quantity_requested':current_q+used_q,'quantity_limit':q['quantity'],'amount_requested':current_v+used_v,'amount_limit':q['amount']})
 return alerts

def approve_requisition(o,a):
 require_draft(o);require_other(o)
 from inventory_core import validate_inventory
 validate_inventory(o)
 object_access(related(o,'department','inventory','departments'));object_access(related(o,'warehouse','inventory','warehouses'));items=children('requisition_items','requisition',o['id'])
 if not items:raise ApiError('Inclua os materiais solicitados.')
 for item in items:
  require_other(item)
  if load(item['data']['material'])['data']['obsolete']:raise ApiError('Requisição contém material obsoleto.')
 alerts=quota_alerts(o,items)
 for item in items:set_state(item,'Aprovado');event(item,'Item de requisição aprovado',{'requisition':o['id']})
 set_state(o,'Aprovado')
 if alerts:notify(o['created_by'],'Cota de materiais excedida','A requisição '+o['code']+' excedeu '+str(len(alerts))+' cota(s). Confira quantidade e valor no histórico.');event(o,'Alerta de cotas excedidas',{'alerts':alerts})
 return {'items':len(items),'alerts':alerts,'warning':'Requisição aprovada com alerta de cota excedida.' if alerts else None}

def refresh_requisition(o):
 items=children('requisition_items','requisition',o['id']);pending=sum(remaining(i,'delivered') for i in items)
 state='Atendido' if not pending else 'Parcialmente entregue' if any(balance(i['id'],'delivered') for i in items) else 'Aprovado'
 set_state(o,state);event(o,'Saldo de requisição atualizado',{'pending':pending})

def movement(parent,data):
 from erp_operations import run_operation
 obj=create_object('inventory','movements',parent['entity_id'],parent['exercise'],data);run_operation(obj,'execute_stock',{})
 return load(obj['id'])

def deliver_requisition(o,a):
 from erp_operations import positive,check_day
 req=related(o,'requisition','inventory','requisitions');d=req['data'];object_access(load(d['warehouse']))
 if req['state'] not in ['Aprovado','Parcialmente entregue'] or d['type']!='Material':raise ApiError('A requisição de material deve estar aprovada e com saldo pendente.',409)
 q=positive(quantity(a.get('quantity')));day=a.get('date');check_day(day);check_period(req,day)
 if day<d['date'] or q>remaining(o,'delivered'):raise ApiError('Entrega anterior à requisição ou superior ao saldo pendente.',409)
 sequence=get_db().execute('SELECT COUNT(*) FROM inventory_fulfillments WHERE item_id=?',(o['id'],)).fetchone()[0]+1
 mov=movement(o,{'code':f'REQ-{o["id"]}-{sequence}','name':'Entrega da requisição '+req['code'],'warehouse':d['warehouse'],'material':o['data']['material'],'type':'Saída','date':day,'quantity':units(q),'requisition_item':o['id']})
 value=-get_db().execute('SELECT value FROM erp_stock_ledger WHERE source_id=?',(mov['id'],)).fetchone()[0]
 get_db().execute('INSERT INTO inventory_fulfillments(item_id,movement_id,kind,quantity,value,date,actor_id,created_at) VALUES(?,?,?,?,?,?,?,?)',(o['id'],mov['id'],'Entrega',q,value,day,g.user['id'],now()))
 change_balance(o['id'],'delivered',q);change_balance(o['id'],'delivered_value',value);set_state(o,'Atendido' if not remaining(o,'delivered') else 'Parcialmente entregue');refresh_requisition(req)
 return {'movement_id':mov['id'],'quantity':q,'value':value,'pending':remaining(o,'delivered')}

def return_requisition(o,a):
 from erp_operations import positive,check_day,stock_checks,move_stock
 req=related(o,'requisition','inventory','requisitions');object_access(load(req['data']['warehouse']));id=integer(a.get('delivery'),'Entrega',1);db=get_db()
 delivery=db.execute("SELECT * FROM inventory_fulfillments WHERE id=? AND item_id=? AND kind='Entrega'",(id,o['id'])).fetchone()
 if not delivery:raise ApiError('Selecione uma entrega deste item.')
 q=positive(quantity(a.get('quantity')));day=a.get('date');check_day(day);check_period(req,day)
 if day<delivery['date']:raise ApiError('Devolução não pode anteceder a entrega.')
 returned=db.execute("SELECT COALESCE(SUM(quantity),0) q,COALESCE(SUM(value),0) v FROM inventory_fulfillments WHERE original_id=?",(id,)).fetchone()
 if q>delivery['quantity']-returned['q']:raise ApiError('Devolução superior ao saldo da entrega.',409)
 value=delivery['value']-returned['v'] if q==delivery['quantity']-returned['q'] else rounded(Decimal(delivery['value'])*q/delivery['quantity'])
 material=load(o['data']['material']);expiry=a.get('expiry')
 if material['data']['expiry_control'] and (not expiry or expiry<day):raise ApiError('Informe validade compatível com a devolução. Materiais vencidos não retornam ao estoque disponível.')
 seq=db.execute('SELECT COUNT(*) FROM inventory_fulfillments WHERE item_id=?',(o['id'],)).fetchone()[0]+1
 mov=create_object('inventory','movements',o['entity_id'],o['exercise'],{'code':f'DEV-{o["id"]}-{seq}','name':'Devolução da entrega '+str(id),'warehouse':req['data']['warehouse'],'material':material['id'],'type':'Devolução','date':day,'quantity':units(q),'expiry':expiry,'requisition_item':o['id']})
 stock_checks(mov);move_stock(mov,req['data']['warehouse'],material['id'],q,value);set_state(mov,'Efetivado');event(mov,'Devolução vinculada à entrega',{'delivery':id,'value':value})
 db.execute('INSERT INTO inventory_fulfillments(item_id,movement_id,kind,original_id,quantity,value,date,actor_id,created_at) VALUES(?,?,?,?,?,?,?,?,?)',(o['id'],mov['id'],'Devolução',id,q,value,day,g.user['id'],now()))
 change_balance(o['id'],'returned',q);change_balance(o['id'],'returned_value',value)
 return {'movement_id':mov['id'],'quantity':q,'value':value,'delivery_pending_return':delivery['quantity']-returned['q']-q}

def cancel_requisition_balance(o,a):
 from erp_operations import reason
 req=related(o,'requisition','inventory','requisitions');object_access(load(req['data']['department']));q=remaining(o,'delivered');why=reason(a);check_cancellation(o)
 if req['state'] not in ['Aprovado','Parcialmente entregue'] or q<=0:raise ApiError('Não há saldo aprovado pendente de entrega.',409)
 change_balance(o['id'],'cancelled',q);set_state(o,'Saldo cancelado');refresh_requisition(req);return {'cancelled':q,'reason':why}

def cancel_requisition(o,a):
 from erp_operations import reason
 why=reason(a);object_access(load(o['data']['department']))
 if o['state'] not in ['Rascunho','Aprovado','Parcialmente entregue']:raise ApiError('Requisição indisponível para cancelamento.',409)
 for item in children('requisition_items','requisition',o['id']):
  check_cancellation(item);q=remaining(item,'delivered')
  if q>0:change_balance(item['id'],'cancelled',q);set_state(item,'Saldo cancelado');event(item,'Saldo cancelado com a requisição',{'quantity':q,'reason':why})
 set_state(o,'Cancelado');return {'reason':why}

def approve_supply_authorization(o,a):
 require_draft(o);require_other(o)
 from inventory_core import validate_inventory
 validate_inventory(o)
 d=o['data'];object_access(load(d['warehouse']));process=related(o,'process','procurement','processes');commitment=related(o,'commitment','finance','commitments');same_year(o,commitment);check_period(o,d['date'])
 if process['state']!='Homologado' or commitment['state']!='Empenhado' or commitment['data']['supplier']!=d['supplier']:raise ApiError('Exige processo homologado e empenho efetivado para o fornecedor.')
 if d['date']<commitment['data']['date'] or d['research_date']>d['date']:raise ApiError('Datas da autorização, empenho ou pesquisa incompatíveis.')
 if d.get('requisition'):
  req=load(d['requisition'])
  if req['data']['type']!='Compra' or req['state']!='Aprovado':raise ApiError('Requisição de compra deve estar aprovada.')
 items=children('authorization_items','authorization',o['id']);value=0;db=get_db()
 if not items:raise ApiError('Inclua os itens do fornecimento.')
 for item in items:
  require_other(item);validate_inventory(item);check_authorization_link(o,item);x=item['data'];pitem=load(x['procurement_item']);same_year(o,pitem)
  if load(x['material'])['data']['obsolete']:raise ApiError('Material obsoleto não pode ser adquirido.')
  proposal=db.execute("SELECT data FROM erp_objects WHERE module='procurement' AND kind='proposals' AND state='Adjudicado' AND deleted=0 AND json_extract(data,'$.item')=? AND json_extract(data,'$.supplier')=?",(pitem['id'],d['supplier'])).fetchone()
  if not proposal:raise ApiError('Fornecedor não possui proposta adjudicada para o item.')
  proposal=json.loads(proposal['data']);price=proposal['unit_price'] if process['data']['judgment']=='Menor preço' else rounded(Decimal(pitem['data']['unit_price'])*(1-Decimal(proposal.get('discount') or 0)/100))
  if x['unit_price']!=price:raise ApiError('Preço deve corresponder à proposta adjudicada após desconto.')
  previous=db.execute("SELECT i.id,i.data FROM erp_objects i JOIN erp_objects h ON h.id=json_extract(i.data,'$.authorization') WHERE i.module='inventory' AND i.kind='authorization_items' AND i.deleted=0 AND h.deleted=0 AND h.state<>'Rascunho' AND h.id<>? AND json_extract(i.data,'$.procurement_item')=?",(o['id'],pitem['id'])).fetchall()
  authorized=sum(json.loads(r['data'])['quantity']-balance(r['id'],'cancelled') for r in previous)
  if x['quantity']+authorized>pitem['data']['quantity']:raise ApiError('Autorização excede o quantitativo adjudicado ainda disponível.',409)
  value+=total(x)
 from inventory_core import received_supply_value
 unrelated=max(0,balance(commitment['id'],'settled')-received_supply_value(commitment['id']))
 if value>commitment['data']['amount']-balance(commitment['id'],'supply_authorized')-unrelated:raise ApiError('Autorizações excedem o valor empenhado.',409)
 change_balance(commitment['id'],'supply_authorized',value);change_balance(o['id'],'authorized_value',value)
 for item in items:set_state(item,'Autorizado');event(item,'Fornecimento autorizado',{'authorization':o['id']})
 set_state(o,'Autorizado');event(commitment,'Fornecimento vinculado',{'authorization':o['id'],'amount':value});return {'amount':value,'items':len(items)}

def cancel_supply_balance(o,a):
 from erp_operations import reason
 require_other(o);why=reason(a)
 if o['state'] not in ['Autorizado','Parcialmente recebido']:raise ApiError('Autorização sem saldo disponível.',409)
 cancelled_value=0
 for item in children('authorization_items','authorization',o['id']):
  q=remaining(item,'received');v=max(0,total(item['data'])-balance(item['id'],'received_value'))
  if q>0:change_balance(item['id'],'cancelled',q);set_state(item,'Saldo cancelado');event(item,'Saldo de fornecimento cancelado',{'quantity':q,'reason':why});cancelled_value+=v
 change_balance(o['data']['commitment'],'supply_authorized',-cancelled_value);set_state(o,'Saldo cancelado');return {'cancelled_value':cancelled_value,'reason':why}

def suggest_authorized_items(o,a):
 require_draft(o)
 if o['data']['type']!='Material' or not o['data'].get('authorization'):raise ApiError('Informe a autorização na nota de materiais.')
 existing={i['data'].get('authorization_item') for i in children('invoice_items','invoice',o['id'])};created=[]
 for item in children('authorization_items','authorization',o['data']['authorization']):
  q=remaining(item,'received')
  if q<=0 or item['id'] in existing:continue
  new=create_object('inventory','invoice_items',o['entity_id'],o['exercise'],{'code':f'NF-{o["id"]}-{item["id"]}','name':load(item['data']['material'])['name'],'invoice':o['id'],'authorization_item':item['id'],'material':item['data']['material'],'quantity':units(q),'unit_price':reais(item['data']['unit_price'])});created.append(new['id'])
 return {'created_items':created,'notice':'Quantidades sugeridas pelo saldo autorizado. Confira as quantidades efetivamente recebidas e as validades antes da aprovação.'}

def post_inventory_invoice(o,a):
 from erp_operations import settle,check_day
 require_draft(o);require_other(o);require('finance','approve')
 from inventory_core import validate_inventory
 validate_inventory(o)
 d=o['data'];items=children('invoice_items','invoice',o['id'])
 if not items:raise ApiError('Inclua os itens recebidos.')
 for item in items:require_other(item);validate_inventory(item)
 authorization=load(d['authorization']) if d.get('authorization') else None;commitment=load(authorization['data']['commitment'] if authorization else d['commitment'],'finance','commitments');same_year(o,commitment)
 if commitment['data']['supplier']!=d['supplier'] or commitment['state']!='Empenhado':raise ApiError('Empenho inválido para este emitente.')
 value=sum(total(i['data']) for i in items)
 if value<=0:raise ApiError('Nota fiscal deve possuir valor positivo.')
 settlement=create_object('finance','settlements',o['entity_id'],o['exercise'],{'code':'NF-'+str(o['id']),'name':'Liquidação da nota '+d['number']+'/'+d['series'],'commitment':commitment['id'],'date':d['date'],'invoice':d['number']+'/'+d['series']+'/'+d['model'],'amount':reais(value)})
 settle(settlement,{},authorization);event(settlement,'Liquidação simultânea ao recebimento',{'invoice':o['id'],'amount':value})
 movements=[];assets=[]
 for item in items:
  x=item['data'];amount=total(x)
  if d['type']=='Material':
   source=load(x['authorization_item']);warehouse=load(authorization['data']['warehouse']);object_access(warehouse)
   if authorization['state'] not in ['Autorizado','Parcialmente recebido'] or source['data']['authorization']!=authorization['id'] or x['material']!=source['data']['material'] or x['unit_price']!=source['data']['unit_price']:raise ApiError('Item não corresponde ao fornecimento vigente.')
   if balance(source['id'],'received_value')+amount>total(source['data']):raise ApiError('Valor acumulado das notas supera o valor autorizado do item. Confira arredondamentos e quantidades.',409)
   if x['quantity']>remaining(source,'received'):raise ApiError('Recebimento excede o saldo autorizado.',409)
   mov=movement(o,{'code':'NF-ITEM-'+str(item['id']),'name':'Recebimento da nota '+d['number'],'warehouse':warehouse['id'],'material':x['material'],'type':'Entrada','date':d['date'],'quantity':units(x['quantity']),'unit_price':reais(x['unit_price']),'batch':x.get('batch'),'expiry':x.get('expiry'),'invoice_item':item['id'],'supplier':d['supplier']})
   movements.append(mov['id']);change_balance(source['id'],'received',x['quantity']);change_balance(source['id'],'received_value',amount);set_state(source,'Recebido' if not remaining(source,'received') else 'Parcialmente recebido');event(source,'Quantidade recebida',{'invoice':o['id'],'quantity':x['quantity']})
  elif d['type']=='Bem patrimonial':
   require('assets','write');count=x['quantity']//1000000
   if count>1000:raise ApiError('Divida o recebimento em itens de até 1.000 bens para geração das fichas patrimoniais.')
   for index in range(count):
    asset=create_object('assets','items',o['entity_id'],o['exercise'],{'code':f'NF-{item["id"]}-{index+1}','name':item['name'],'class':x['asset_class'],'type':'Próprio','location':x['asset_location'],'owner':x['asset_owner'],'condition':'Bom','date':d['date'],'amount':reais(x['unit_price']),'method':'Quotas constantes','start':d['date'],'supplier':d['supplier']});event(asset,'Ingresso por nota fiscal',{'invoice':o['id'],'settlement':settlement['id']});assets.append(asset['id'])
  set_state(item,'Recebido');event(item,'Item de nota recebido',{'invoice':o['id'],'value':amount})
 if authorization:
  pending=sum(remaining(i,'received') for i in children('authorization_items','authorization',authorization['id']));set_state(authorization,'Recebido' if pending==0 else 'Parcialmente recebido');event(authorization,'Nota fiscal incorporada',{'invoice':o['id'],'pending':pending})
 get_db().execute('INSERT INTO inventory_invoice_postings VALUES(?,?,?,?)',(o['id'],settlement['id'],value,now()));set_state(o,'Recebido')
 return {'settlement_id':settlement['id'],'amount':value,'movements':movements,'assets':assets}

def writeoff_obsolete(o,a):
 from erp_operations import stock_row,move_stock,positive,reason
 require_draft(o);require_other(o);d=o['data'];object_access(load(d['warehouse']));material=load(d['material']);check_period(o,d['date']);why=reason(a)
 if d['type']!='Baixa de obsoleto' or not material['data']['obsolete']:raise ApiError('Esta rotina é exclusiva para baixa autorizada de material obsoleto.')
 q=positive(d['quantity']);old=stock_row(d['warehouse'],d['material'])
 if q>old['quantity']:raise ApiError('Baixa superior ao saldo disponível.',409)
 value=old['value'] if q==old['quantity'] else rounded(Decimal(old['value'])*q/old['quantity']);move_stock(o,d['warehouse'],d['material'],-q,-value);set_state(o,'Baixado');return {'quantity':q,'value':value,'reason':why}

OPERATIONS={f.__name__:f for f in [approve_purchase_link,cancel_purchase_link,approve_requisition,cancel_requisition,deliver_requisition,return_requisition,cancel_requisition_balance,approve_supply_authorization,cancel_supply_balance,suggest_authorized_items,post_inventory_invoice,writeoff_obsolete]}

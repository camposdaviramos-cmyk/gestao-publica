"""Vincula a demanda aprovada à licitação antes da emissão do fornecimento."""
from auth import ApiError
from erp_core import load,related,balance,require_draft,require_other,check_period,set_state
from inventory_core import children,object_access,same_year

def approve_purchase_link(o,a):
 require_draft(o);require_other(o);d=o['data'];check_period(o,d['date']);object_access(load(d['warehouse']));line=related(o,'requisition_item','inventory','requisition_items');req=load(line['data']['requisition']);pitem=related(o,'procurement_item','procurement','items');process=load(pitem['data']['process']);same_year(o,req);same_year(o,pitem)
 if req['data']['type']!='Compra' or req['state']!='Aprovado' or req['data']['warehouse']!=d['warehouse']:raise ApiError('Vincule um pedido de compra aprovado do almoxarifado selecionado.')
 if process['state']=='Rascunho' or d['quantity']<=0:raise ApiError('Processo deve estar em andamento e quantidade deve ser positiva.')
 if d['date']<req['data']['date'] or d['research_date']>d['date']:raise ApiError('Datas do pedido, pesquisa e vinculação incompatíveis.')
 object_access(load(req['data']['department']))
 linked=children('purchase_links','requisition_item',line['id']);q=sum(x['data']['quantity'] for x in linked if x['state']=='Vinculado')
 if q+d['quantity']>line['data']['quantity']-balance(line['id'],'cancelled'):raise ApiError('Vínculos excedem a quantidade solicitada.',409)
 other=children('purchase_links','procurement_item',pitem['id']);q=sum(x['data']['quantity'] for x in other if x['state']=='Vinculado')
 if q+d['quantity']>pitem['data']['quantity']:raise ApiError('Vínculos excedem a quantidade do item licitado.',409)
 set_state(o,'Vinculado');return {'process_id':process['id'],'quantity':d['quantity']}

def cancel_purchase_link(o,a):
 from erp_operations import reason
 require_other(o);why=reason(a)
 if o['state']!='Vinculado':raise ApiError('Vínculo não está ativo.',409)
 if any(x['state']!='Rascunho' for x in children('authorization_items','purchase_link',o['id'])):raise ApiError('Vínculo já utilizado em autorização de fornecimento.',409)
 set_state(o,'Cancelado');return {'reason':why}

def check_authorization_link(o,item):
 d=o['data'];x=item['data']
 if not x.get('purchase_link'):return
 link=load(x['purchase_link']);line=load(link['data']['requisition_item']);same_year(o,link)
 if link['state']!='Vinculado' or link['data']['procurement_item']!=x['procurement_item'] or link['data']['warehouse']!=d['warehouse'] or line['data']['material']!=x['material'] or line['data']['requisition']!=d.get('requisition'):raise ApiError('Vínculo de compra incompatível com a autorização.')
 allocated=sum(z['data']['quantity']-balance(z['id'],'cancelled') for z in children('authorization_items','purchase_link',link['id']) if z['state']!='Rascunho')
 if allocated+x['quantity']>link['data']['quantity']:raise ApiError('Fornecimento excede o saldo do vínculo de compra.',409)

def check_cancellation(line):
 if any(x['state']=='Vinculado' for x in children('purchase_links','requisition_item',line['id'])):raise ApiError('Cancele os vínculos licitatórios ativos antes de cancelar o saldo do pedido.',409)


def settle_purchase_movement(o,amount):
 from auth import require
 from erp_core import create_object,event
 from erp_operations import settle
 from inventory_operations import reais
 from db import get_db
 from domain import now
 d=o['data']
 if d.get('invoice_item') or not any(d.get(k) for k in ['supplier','invoice','commitment']):return
 require_other(o);require('finance','approve')
 if not d.get('supplier') or not d.get('invoice') or not d.get('commitment'):raise ApiError('Entrada de compra exige fornecedor, documento fiscal e empenho; ou utilize Notas fiscais e recebimentos.')
 c=related(o,'commitment','finance','commitments');same_year(o,c)
 if c['data']['supplier']!=d['supplier']:raise ApiError('Fornecedor do movimento diverge do empenho.')
 settlement=create_object('finance','settlements',o['entity_id'],o['exercise'],{'code':'EST-'+str(o['id']),'name':'Ingresso de compra '+o['code'],'commitment':c['id'],'date':d['date'],'invoice':d['invoice'],'amount':reais(amount)})
 settle(settlement,{});event(settlement,'Liquidação simultânea à entrada',{'movement':o['id'],'amount':amount});get_db().execute('INSERT INTO inventory_movement_postings VALUES(?,?,?,?)',(o['id'],settlement['id'],amount,now()))

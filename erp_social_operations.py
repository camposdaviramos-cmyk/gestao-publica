"""Operações de agenda e integração de benefícios com estoque."""
from auth import ApiError,require
from erp_core import load,create_object,require_draft,event,set_state,related
from erp_operations import execute_stock,reason
from db import get_db

def issue_benefit_stock(concession,benefit):
 material=benefit['data'].get('material')
 if not material:return None
 require('inventory','write')
 warehouse=concession['data'].get('warehouse')
 if not warehouse:raise ApiError('Selecione o almoxarifado para conceder este benefício.')
 if not benefit['data'].get('units'):raise ApiError('Configure a quantidade do insumo por benefício.')
 from decimal import Decimal
 data={'code':'BEN-'+str(concession['id']),'name':'Saída por benefício '+concession['code'],'warehouse':warehouse,'material':material,'type':'Saída','date':concession['data']['date'],'quantity':str(Decimal(benefit['data']['units'])/1000000)}
 movement=create_object('inventory','movements',concession['entity_id'],concession['exercise'],data)
 result=execute_stock(movement,{})
 event(movement,'Saída por concessão',{'concession':concession['id'],**result})
 get_db().execute('INSERT INTO erp_links VALUES(?,?,?)',(concession['id'],'stock_movement',movement['id']))
 return movement['id']

def attend_appointment(o,a):
 require_draft(o);set_state(o,'Atendido');return {'reason':reason(a)}

def cancel_appointment(o,a):
 require_draft(o);set_state(o,'Cancelado');return {'reason':reason(a)}

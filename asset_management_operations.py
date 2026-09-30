"""Movimentação física, guarda, manutenção e inventário patrimonial."""
import json
from flask import g
from auth import ApiError,require
from db import get_db
from erp_core import load,related,require_draft,require_other,set_state,event,create_object,integer
from asset_core import same_entity,position,snapshot,available,record,commission,rows,new_position,posting
from asset_accounting_operations import justification,writeoff_asset
import uuid

def transfer_asset(o,a):
 require_other(o);day=available(o,a.get('date'));why=justification(a);before=snapshot(o);p=position(o)
 location=str(a.get('location','')).strip();owner=str(a.get('owner','')).strip()
 if len(location)<2 or len(owner)<2:raise ApiError('Informe localização e responsável de destino.')
 location_ref=a.get('location_ref');responsible=a.get('responsible')
 if location_ref:
  place=load(integer(location_ref,'Localização',1),'assets','locations');same_entity(o,place)
  if not place['data']['active']:raise ApiError('Localização de destino inativa.',409)
 if responsible:
  person=load(integer(responsible,'Responsável',1),'assets','responsibles');same_entity(o,person)
  if not person['data']['active']:raise ApiError('Responsável de destino inativo.',409)
 old={k:o['data'].get(k) for k in ['location','owner','location_ref','responsible']}
 o['data'].update(location=location,owner=owner,location_ref=location_ref,responsible=responsible)
 return record(o,o,day,'Transferência física',why,before,p,metadata={'from':old,'to':{k:o['data'].get(k) for k in old}})

def revise_asset_identity(o,a):
 require_other(o);day=available(o,a.get('date'));why=justification(a);before=snapshot(o);p=position(o);changed={}
 for field in ['code','name','registry','registration','tombamento','condition','situation']:
  if field in a and a[field] not in [None,''] and a[field]!=o['data'].get(field):changed[field]={'from':o['data'].get(field),'to':a[field]};o['data'][field]=a[field]
 if not changed:raise ApiError('Informe ao menos uma alteração de identificação ou situação.')
 return record(o,o,day,'Revisão cadastral patrimonial',why,before,p,metadata={'changes':changed})

def start_asset_loan(o,a):
 require_draft(o);require_other(o);d=o['data'];asset=related(o,'asset','assets','items');same_entity(o,asset);day=available(asset,d['start']);p=position(asset);before=snapshot(asset)
 if d['end']<d['start']:raise ApiError('O término previsto não pode anteceder o início.')
 if get_db().execute("SELECT 1 FROM erp_objects WHERE module='assets' AND kind='loans' AND state='Vigente' AND deleted=0 AND json_extract(data,'$.asset')=?",(asset['id'],)).fetchone():raise ApiError('Bem já possui cessão, comodato ou locação vigente.',409)
 expected={'Próprio':['Cessão em comodato'],'Alugado':['Recebimento em locação'],'Comodato':['Recebimento em comodato']}
 if d['type'] not in expected.get(asset['data']['type'],[]):raise ApiError('A operação não corresponde ao tipo de propriedade do bem.')
 set_state(o,'Vigente');return record(asset,o,day,'Início de '+d['type'],d['legal_basis'],before,p,metadata={'party':d['party'],'document':d['document'],'end':d['end']})

def return_asset_loan(o,a):
 if o['state']!='Vigente':raise ApiError('Operação patrimonial não está vigente.',409)
 require_other(o);asset=related(o,'asset','assets','items');day=available(asset,a.get('date'));why=justification(a);before=snapshot(asset);p=position(asset)
 if day<o['data']['start']:raise ApiError('Retorno anterior ao início da operação.')
 set_state(o,'Encerrado');return record(asset,o,day,'Retorno de '+o['data']['type'],why,before,p,metadata={'party':o['data']['party']})

def complete_asset_maintenance(o,a):
 require_draft(o);require_other(o);plan=related(o,'plan','assets','maintenance_plans');asset=related(plan,'asset','assets','items');day=available(asset,o['data']['date']);before=snapshot(asset);p=position(asset)
 if o['data']['date']<plan['data']['first_due']:raise ApiError('Manutenção anterior à primeira data prevista.')
 o['state']='Concluído';asset['data']['situation']=str(a.get('situation') or 'Em uso')
 return record(asset,o,day,'Manutenção '+plan['data']['type'],o['data']['report'],before,p,metadata={'supplier':o['data']['supplier'],'amount':o['data']['amount'],'warranty_through':o['data'].get('warranty_through')})

def _matches(asset,inv):
 d=asset['data'];f=inv['data']
 return (not f.get('location') or d.get('location')==f['location']) and (not f.get('class_filter') or d.get('class')==f['class_filter']) and (not f.get('description_filter') or f['description_filter'].casefold() in asset['name'].casefold()) and (not f.get('condition_filter') or d.get('condition')==f['condition_filter']) and (not f.get('situation_filter') or d.get('situation')==f['situation_filter'])

def inventory_day(o,day):
 from asset_core import day_value
 day=day_value(day)
 for row in get_db().execute("SELECT id,data FROM erp_objects WHERE module='assets' AND kind='inventories' AND entity_id=? AND state='Em andamento' AND deleted=0 AND id<>?",(o['entity_id'],o['id'])):
  if json.loads(row['data']).get('location')==o['data'].get('location'):raise ApiError('Já existe inventário em andamento para esta localização.',409)
 return day

def open_inventory(o,a):
 require_draft(o);require_other(o);d=o['data'];day=inventory_day(o,d['date']);commission(o,'commission_ref','Inventário',day);assets=[]
 for row in get_db().execute("SELECT id FROM erp_objects WHERE module='assets' AND kind='items' AND entity_id=? AND deleted=0 AND state='Ativo' ORDER BY id",(o['entity_id'],)):
  asset=load(row['id'])
  if _matches(asset,o):assets.append(asset)
 if not assets:raise ApiError('Nenhum bem ativo corresponde aos filtros do inventário.',409)
 set_state(o,'Em andamento');ids=[]
 for asset in assets:
  x=asset['data'];line=create_object('assets','inventory_items',o['entity_id'],o['exercise'],{'code':o['code']+'-'+asset['code'],'name':asset['name'],'inventory':o['id'],'asset':asset['id'],'date':day,'location':x['location'],'responsible':x.get('responsible'),'condition':x['condition'],'situation':x.get('situation') or 'Em uso','conformity':'Pendente de conferência','writeoff':False,'writeoff_type':'','legal_basis':''});ids.append(line['id'])
 event(o,'Inventário aberto',{'assets':ids,'filters':{k:v for k,v in d.items() if k.endswith('_filter') or k=='location'}});return {'items':ids,'count':len(ids)}

def confirm_inventory_asset(o,a):
 require_draft(o);require_other(o);inv=related(o,'inventory','assets','inventories');asset=related(o,'asset','assets','items')
 if inv['state']!='Em andamento':raise ApiError('Inventário não está em andamento.',409)
 day=available(asset,o['data']['date'],inv['id']);d=o['data'];p=position(asset)
 if d['conformity']=='Pendente de conferência':raise ApiError('Registre o resultado da conferência física antes de aprovar.')
 if d.get('writeoff'):
  result=writeoff_asset(asset,{'date':day,'reason':d['conformity'],'type':d.get('writeoff_type'),'legal_basis':d.get('legal_basis')},source=o,inventory_id=inv['id']);set_state(o,'Conferido');return result
 before=snapshot(asset);changes={}
 for field in ['location','responsible','condition','situation']:
  if d.get(field) not in [None,''] and d.get(field)!=asset['data'].get(field):changes[field]={'from':asset['data'].get(field),'to':d[field]};asset['data'][field]=d[field]
 if d.get('responsible'):asset['data']['owner']=related(o,'responsible','assets','responsibles')['name']
 if changes:result=record(asset,o,day,'Conferência de inventário',d['conformity'],before,p,metadata={'inventory':inv['id'],'changes':changes})
 else:event(asset,'Conferência de inventário sem divergência',{'inventory':inv['id'],'line':o['id'],'conformity':d['conformity']});result={'unchanged':True}
 set_state(o,'Conferido');return result

def close_inventory(o,a):
 if o['state']!='Em andamento':raise ApiError('Inventário não está em andamento.',409)
 require_other(o);why=justification(a);lines=rows('inventory_items','inventory',o['id']);pending=[x['id'] for x in lines if x['state']!='Conferido']
 if pending:raise ApiError('Conclua todos os itens do inventário antes do encerramento.',409)
 set_state(o,'Concluído');event(o,'Inventário encerrado',{'reason':why,'items':len(lines),'responsible_id':g.user['id']});return {'items':len(lines)}

def transfer_asset_entity(o,a):
 require_draft(o);require_other(o);require('finance','approve');d=o['data'];source=related(o,'asset','assets','items');day=available(source,d['date']);dest_entity=integer(d['destination_entity'],'Entidade de destino',1)
 from erp_core import entity_access
 entity_access(dest_entity);klass=load(integer(d['destination_class'],'Classificação de destino',1),'assets','classes')
 if klass['entity_id']!=dest_entity or klass['exercise']!=o['exercise']:raise ApiError('Classificação incompatível com a entidade de destino.')
 p=position(source);net=p['gross']-p['accumulated'];group=uuid.uuid4().hex;before=snapshot(source);copied={**source['data'],'code':source['code']+'-'+str(o['id']),'name':source['name'],'class':klass['id'],'type':'Próprio' if d['type']=='Doação' else 'Comodato','location':d['destination_location'],'owner':d['destination_owner'],'owner_cpf':'','date':day,'amount':net,'start':day,'responsible':None,'location_ref':None,'receipt_commission':None,'ingress_type':'Doação' if d['type']=='Doação' else 'Comodato','capitalize':bool(source['data'].get('capitalize') and d['type']=='Doação'),'process':None,'commitment':None,'supplier':None,'invoice':'','requires_confirmation':False}
 dest=create_object('assets','items',dest_entity,o['exercise'],copied);dest['state']='Ativo';fresh=new_position(dest);entries,rule_id=posting(dest,'Doação recebida',net,day) if d['type']=='Doação' else ([],None)
 if d['type']=='Doação':writeoff_asset(source,{'date':day,'reason':d['legal_basis'],'type':'Doação entre entidades','legal_basis':d['legal_basis']},source=o,group_id=group,fact='Doação concedida')
 else:
  source['data']['situation']='Em reserva';source['data']['location']='Cedido temporariamente à entidade '+str(dest_entity);record(source,o,day,'Transferência temporária',d['legal_basis'],before,p,metadata={'destination_entity':dest_entity},group_id=group)
 record(dest,o,day,'Doação recebida' if d['type']=='Doação' else 'Recebimento temporário',d['legal_basis'],snapshot(dest),fresh,entries,{'origin_asset':source['id'],'origin_entity':source['entity_id'],'rule_id':rule_id},group_id=group);set_state(o,'Efetivada');return {'destination_asset':dest['id'],'group_id':group,'net':net}


def return_asset_entity(o,a):
 if o['state']!='Efetivada' or o['data']['type']!='Temporária':raise ApiError('Somente transferência temporária efetivada admite retorno.',409)
 require_other(o);why=justification(a);day=str(a.get('date',''));moves=get_db().execute("SELECT * FROM asset_movements WHERE source_id=? AND fact IN ('Transferência temporária','Recebimento temporário') AND reversal_of IS NULL ORDER BY id",(o['id'],)).fetchall()
 if len(moves)!=2:raise ApiError('Histórico da transferência temporária inconsistente.',409)
 origin=load(moves[0]['asset_id'],'assets','items');dest=load(moves[1]['asset_id'],'assets','items');available(origin,day);available(dest,day);group=uuid.uuid4().hex
 restore=json.loads(moves[0]['before_snapshot']);before=snapshot(origin);origin['data'].update(location=restore['data']['location'],owner=restore['data']['owner'],responsible=restore['data'].get('responsible'),location_ref=restore['data'].get('location_ref'),situation=restore['data'].get('situation'));record(origin,o,day,'Retorno entre entidades',why,before,position(origin),metadata={'destination_asset':dest['id']},group_id=group)
 before_dest=snapshot(dest);p=position(dest);p.update(gross=0,accumulated=0,residual=0);dest['state']='Baixado';record(dest,o,day,'Retorno de bem de terceiro',why,before_dest,p,metadata={'origin_asset':origin['id']},group_id=group);set_state(o,'Retornada');return {'origin_asset':origin['id'],'destination_asset':dest['id']}

OPERATIONS={f.__name__:f for f in [transfer_asset,revise_asset_identity,start_asset_loan,return_asset_loan,complete_asset_maintenance,open_inventory,confirm_inventory_asset,close_inventory,transfer_asset_entity,return_asset_entity]}

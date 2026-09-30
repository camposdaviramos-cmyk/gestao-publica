"""Consultas de estoque calculadas a partir dos lançamentos efetivados."""
import calendar,json
from datetime import date
from decimal import Decimal
from auth import ApiError
from db import get_db
from erp_core import integer,load,rounded,balance


def records(entity,year,kind,module='inventory'):
 rows=get_db().execute('SELECT * FROM erp_objects WHERE entity_id=? AND exercise=? AND module=? AND kind=? AND deleted=0',(entity,year,module,kind)).fetchall()
 return {r['id']:{**dict(r),'data':json.loads(r['data'])} for r in rows}

def filters(args,year):
 start=args.get('start') or f'{year}-01-01';end=args.get('end') or f'{year}-12-31'
 try:a=date.fromisoformat(start);b=date.fromisoformat(end)
 except (ValueError,TypeError):raise ApiError('Informe datas válidas para o relatório.')
 if a.year!=year or b.year!=year or a>b:raise ApiError('Período deve ser crescente e pertencer ao exercício.')
 return {'start':start,'end':end,'warehouse':integer(args['warehouse'],'Almoxarifado',1) if args.get('warehouse') else None,'material':integer(args['material'],'Material',1) if args.get('material') else None,'group':str(args.get('group','')).strip(),'subgroup':str(args.get('subgroup','')).strip(),'abc':str(args.get('abc','')).upper()}

def ledger(entity,year,f):
 where=['o.entity_id=?','o.exercise=?','l.date<=?'];args=[entity,year,f['end']]
 for field,column in [('warehouse','l.warehouse_id'),('material','l.material_id')]:
  if f[field]:where.append(column+'=?');args.append(f[field])
 for field in ['group','subgroup']:
  if f[field]:where.append("json_extract(m.data,'$."+field+"')=?");args.append(f[field])
 return [dict(r) for r in get_db().execute("SELECT l.*,o.code document,o.kind,o.data source,w.name warehouse,m.name material,m.code,m.data material_data,a.rule_id FROM erp_stock_ledger l JOIN erp_objects o ON o.id=l.source_id JOIN erp_objects w ON w.id=l.warehouse_id JOIN erp_objects m ON m.id=l.material_id LEFT JOIN inventory_accounting a ON a.stock_ledger_id=l.id WHERE "+' AND '.join(where)+' ORDER BY l.date,l.id',args)]

def consumption(rows,start,end):
 totals={}
 for r in rows:
  if not start<=r['date']<=end:continue
  d=json.loads(r['source']);typ=d.get('type')
  if typ!='Saída' and not (typ=='Devolução' and d.get('requisition_item')):continue
  key=r['material_id'];x=totals.setdefault(key,{'material_id':key,'code':r['code'],'material':r['material'],'quantity':0,'value':0})
  x['quantity']-=r['quantity'];x['value']-=r['value']
 months=(int(end[:4])-int(start[:4]))*12+int(end[5:7])-int(start[5:7])+1
 ordered=sorted(totals.values(),key=lambda x:(-x['value'],x['code']));total=sum(max(0,x['value']) for x in ordered);acc=0
 for x in ordered:
  x['abc']='A' if total and acc*100<total*80 else 'B' if total and acc*100<total*95 else 'C'
  acc+=max(0,x['value']);x['share_percent']=str((Decimal(max(0,x['value']))*100/total).quantize(Decimal('.01'))) if total else '0';x['cumulative_percent']=str((Decimal(acc)*100/total).quantize(Decimal('.01'))) if total else '0';x['average_quantity']=rounded(Decimal(max(0,x['quantity']))/months);x['months']=months
 return ordered

def stock_report(entity,year,f):
 rows=ledger(entity,year,f);materials=records(entity,year,'materials');warehouses=records(entity,year,'warehouses');policies=records(entity,year,'policies');authorizations=records(entity,year,'authorizations');auth_items=records(entity,year,'authorization_items');request_items=records(entity,year,'requisition_items')
 pairs={};incoming={};pending_purchase={};transit={}
 def pair(w,m):
  if w not in warehouses or m not in materials:return False
  d=materials[m]['data']
  return not ((f['warehouse'] and w!=f['warehouse']) or (f['material'] and m!=f['material']) or (f['group'] and d.get('group')!=f['group']) or (f['subgroup'] and d.get('subgroup')!=f['subgroup']))
 def add(w,m):
  if pair(w,m):pairs.setdefault((w,m),{'warehouse_id':w,'warehouse':warehouses[w]['name'],'material_id':m,'code':materials[m]['code'],'material':materials[m]['name'],'quantity':0,'value':0})
 for row in rows:
  key=(row['warehouse_id'],row['material_id']);add(*key)
  if key in pairs:pairs[key]['quantity']+=row['quantity'];pairs[key]['value']+=row['value']
 # A selected warehouse includes materials with no stock so first purchases can be suggested.
 if f['warehouse']:
  for m in materials:add(f['warehouse'],m)
 for p in policies.values():add(p['data']['warehouse'],p['data']['material'])
 for item in auth_items.values():
  d=item['data'];a=authorizations.get(d['authorization'])
  if not a or a['state'] not in ['Autorizado','Parcialmente recebido'] or a['data']['date']>f['end']:continue
  key=(a['data']['warehouse'],d['material']);add(*key);incoming[key]=incoming.get(key,0)+max(0,d['quantity']-balance(item['id'],'received')-balance(item['id'],'cancelled'))
 for link in records(entity,year,'purchase_links').values():
  d=link['data'];line=request_items.get(d['requisition_item'])
  if link['state']!='Vinculado' or not line or d['date']>f['end']:continue
  allocated=sum(x['data']['quantity']-balance(x['id'],'cancelled') for x in auth_items.values() if x['data'].get('purchase_link')==link['id'] and authorizations.get(x['data']['authorization'],{}).get('state') not in [None,'Rascunho'])
  key=(d['warehouse'],line['data']['material']);add(*key);pending_purchase[key]=pending_purchase.get(key,0)+max(0,d['quantity']-allocated)
 all_transfers=get_db().execute("SELECT l.quantity,l.material_id,o.data FROM erp_stock_ledger l JOIN erp_objects o ON o.id=l.source_id WHERE o.entity_id=? AND o.exercise=? AND l.date<=? AND json_extract(o.data,'$.type')='Transferência'",(entity,year,f['end']))
 transit={}
 for row in all_transfers:
  d=json.loads(row['data']);key=(d['destination'],row['material_id']);add(*key);transit[key]=transit.get(key,0)-row['quantity']
 overrides={(p['data']['warehouse'],p['data']['material']):p['data'] for p in policies.values()};result=[]
 for key,x in pairs.items():
  w,m=key;wd=warehouses[w]['data'];md=materials[m]['data'];p=overrides.get(key) or (wd if wd.get('model') else {**md,'model':'Quantidade','average':0,'reorder_percent':0})
  minimum=p.get('minimum',0);maximum=p.get('maximum',0);average=0
  if p['model']=='Consumo mensal':
   count=p['history_months'];month=date.fromisoformat(f['end']).replace(day=1);index=month.year*12+month.month-1-count;begin=date(index//12,index%12+1,1).isoformat();last=date.fromordinal(month.toordinal()-1).isoformat()
   history=get_db().execute("SELECT l.quantity,o.data FROM erp_stock_ledger l JOIN erp_objects o ON o.id=l.source_id WHERE l.warehouse_id=? AND l.material_id=? AND l.date BETWEEN ? AND ?",(w,m,begin,last)).fetchall();consumed=0
   for h in history:
    source=json.loads(h['data'])
    if source.get('type')=='Saída' or (source.get('type')=='Devolução' and source.get('requisition_item')):consumed-=h['quantity']
   average=rounded(Decimal(max(0,consumed))/count);minimum=average*p['minimum_months'];maximum=average*p['maximum_months']
  maximum=max(maximum,minimum)
  threshold=max(minimum,rounded(Decimal(maximum)*Decimal(p.get('reorder_percent') or 0)/100));virtual=x['quantity']+incoming.get(key,0)+pending_purchase.get(key,0)
  x.update(incoming=incoming.get(key,0),in_procurement=pending_purchase.get(key,0),virtual=virtual,transit=max(0,transit.get(key,0)),minimum=minimum,maximum=maximum,monthly_average=average,model=p['model'],suggested=max(0,maximum-virtual) if virtual<threshold and not md['obsolete'] and not wd['blocked'] else 0);result.append(x)
 return sorted(result,key=lambda x:(x['warehouse'],x['code']))

def report(entity,year,args):
 f=filters(args,year);kind=args.get('report','balances')
 if kind=='balances':return {'report':kind,'filters':f,'items':stock_report(entity,year,f),'note':'Saldo virtual = físico + fornecimentos pendentes + quantidades vinculadas a licitações ainda não autorizadas. Trânsito não integra saldo disponível. Cálculo de pendências usa situação atual; movimentos físicos respeitam a data final.'}
 rows=ledger(entity,year,f)
 if kind=='consumption':
  items=consumption(rows,f['start'],f['end'])
  if f['abc']:
   if f['abc'] not in ['A','B','C']:raise ApiError('Classificação ABC inválida.')
   items=[x for x in items if x['abc']==f['abc']]
  return {'report':kind,'filters':f,'items':items,'note':'ABC por valor líquido consumido: A até o item que atinge 80%; B até 95%; C restante. Devoluções vinculadas reduzem o consumo no período em que ocorreram. Média por mês civil abrangido.'}
 if kind=='movements':
  items=[]
  for r in rows:
   if r['date']<f['start']:continue
   d=json.loads(r.pop('source'));r.pop('material_data');r['type']='Ajuste de inventário' if r['kind']=='counts' else 'Requisição' if d.get('requisition_item') and d.get('type')=='Saída' else 'Nota fiscal' if d.get('invoice_item') else d.get('type');items.append(r)
  return {'report':kind,'filters':f,'items':items}
 if kind=='monthly':
  groups={}
  for r in rows:
   key=(r['warehouse_id'],r['material_id']);x=groups.setdefault(key,{'warehouse':r['warehouse'],'material':r['material'],'code':r['code'],'opening_quantity':0,'opening_value':0,'months':{}})
   if r['date']<f['start']:x['opening_quantity']+=r['quantity'];x['opening_value']+=r['value'];continue
   period=r['date'][:7];m=x['months'].setdefault(period,{'in_quantity':0,'out_quantity':0,'in_value':0,'out_value':0});direction='in' if r['quantity']>=0 else 'out';m[direction+'_quantity']+=abs(r['quantity']);m[direction+'_value']+=abs(r['value'])
  items=[]
  for x in groups.values():
   q=x['opening_quantity'];v=x['opening_value']
   for month in range(int(f['start'][5:7]),int(f['end'][5:7])+1):
    period=f'{year}-{month:02d}';m=x['months'].get(period,dict(in_quantity=0,out_quantity=0,in_value=0,out_value=0));row={k:x[k] for k in ['warehouse','material','code']};row.update(period=period,opening_quantity=q,opening_value=v,**m);q+=m['in_quantity']-m['out_quantity'];v+=m['in_value']-m['out_value'];row.update(closing_quantity=q,closing_value=v);items.append(row)
  return {'report':kind,'filters':f,'items':items,'note':'Saldo inicial, entradas, saídas e saldo final por mês. Períodos parciais respeitam as datas informadas.'}
 raise ApiError('Relatório de estoque desconhecido.')

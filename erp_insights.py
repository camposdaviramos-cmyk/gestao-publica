"""Indicadores derivados de fatos efetivados; não são índices fiscais oficiais."""
from flask import g
from db import get_db

def indicators(entity,exercise):
 db=get_db();result={}
 if 'read' in g.permissions.get('finance',[]):
  rows=db.execute("SELECT kind,substr(json_extract(data,'$.date'),1,7) month,sum(json_extract(data,'$.amount')) amount,sum(coalesce(json_extract(data,'$.deduction'),0)) deduction FROM erp_objects WHERE entity_id=? AND exercise=? AND module='finance' AND deleted=0 AND ((kind='commitments' AND state='Empenhado') OR (kind='settlements' AND state='Liquidado') OR (kind='payments' AND state='Pago') OR (kind='receipts' AND state='Arrecadado')) GROUP BY kind,month",(entity,exercise)).fetchall()
  monthly=[{'month':f'{exercise}-{m:02}','committed':0,'settled':0,'paid':0,'received':0} for m in range(1,13)]
  names={'commitments':'committed','settlements':'settled','payments':'paid','receipts':'received'}
  for r in rows:
   idx=int(r['month'][-2:])-1;monthly[idx][names[r['kind']]]=r['amount']-(r['deduction'] if r['kind']=='receipts' else 0)
  bank=db.execute("SELECT coalesce(sum(json_extract(o.data,'$.opening')+coalesce(b.value,0)),0) FROM erp_objects o LEFT JOIN erp_balances b ON b.object_id=o.id AND b.name='net' WHERE o.entity_id=? AND o.exercise=? AND o.module='finance' AND o.kind='bank_accounts' AND o.deleted=0",(entity,exercise)).fetchone()[0]
  totals={k:sum(x[k] for x in monthly) for k in names.values()}
  result['finance']={'monthly':monthly,**totals,'bank':bank,'payable':totals['settled']-totals['paid'],'cash_result':totals['received']-totals['paid']}
 if 'read' in g.permissions.get('people',[]):
  rows=db.execute("SELECT json_extract(o.data,'$.period') period,count(*) employees,sum(l.gross) gross,sum(l.net) net,sum(l.employer) employer FROM erp_payroll_lines l JOIN erp_objects o ON o.id=l.run_id WHERE o.entity_id=? AND o.exercise=? AND o.state='Aprovado' GROUP BY period ORDER BY period",(entity,exercise)).fetchall()
  result['people']=[dict(r) for r in rows]
 if 'read' in g.permissions.get('works',[]):
  rows=db.execute("SELECT o.id,o.code,o.name,coalesce(m.value,0) measured,coalesce(p.value,0) paid FROM erp_objects o LEFT JOIN erp_balances m ON m.object_id=o.id AND m.name='measured_amount' LEFT JOIN erp_balances p ON p.object_id=o.id AND p.name='paid' WHERE o.entity_id=? AND o.exercise=? AND o.module='works' AND o.kind='projects' AND o.deleted=0 ORDER BY o.name",(entity,exercise)).fetchall()
  result['works']=[dict(r) for r in rows]
 return result

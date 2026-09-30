"""Agregações no banco para que o painel não carregue todos os registros em memória."""
import json
from datetime import datetime, timezone
from flask import g
from db import get_db
from domain import MODULES

def dashboard_data():
 db=get_db(); permissions=g.permissions
 readable=[m for m in MODULES if 'read' in permissions.get(m,[])]
 where='module IN ('+','.join('?'*len(readable))+')' if readable else '0'
 groups=db.execute('SELECT module,status,count(*) count,coalesce(sum(amount),0) amount FROM records WHERE '+where+' GROUP BY module,status',readable).fetchall()
 budget=[r for r in groups if r['module']=='budget']; statuses={r['status']:r['count'] for r in budget}
 departments={}; monthly_values={}
 if 'budget' in readable:
  departments={r['department'] or 'Não informada':r['amount']/100 for r in db.execute("SELECT department,sum(amount) amount FROM records WHERE module='budget' GROUP BY department")}
  monthly_values={r['month']:dict(r) for r in db.execute("SELECT substr(created_at,1,7) month,sum(amount) amount,count(*) count FROM records WHERE module='budget' GROUP BY substr(created_at,1,7)")}
 monthly=[]; today=datetime.now(timezone.utc)
 for offset in range(5,-1,-1):
  index=today.year*12+today.month-1-offset; year,month=divmod(index,12); prefix=f'{year:04}-{month+1:02}'; item=monthly_values.get(prefix,{})
  monthly.append({'month':prefix,'amount':item.get('amount',0)/100,'count':item.get('count',0)})
 approvable=[m for m in MODULES if 'approve' in permissions.get(m,[])]
 condition='requester=?'; args=[g.user['id']]
 if approvable:condition+=' OR module IN ('+','.join('?'*len(approvable))+')'; args+=approvable
 pending=db.execute("SELECT count(*) FROM approvals WHERE status='Pendente' AND ("+condition+')',args).fetchone()[0]
 recent=[{**dict(r),'amount':r['amount']/100} for r in db.execute('SELECT id,module,title,department,status,amount,updated_at FROM records WHERE '+where+' ORDER BY updated_at DESC,id DESC LIMIT 6',readable)]
 activities=db.execute('SELECT actor,action,module,created_at FROM audit '+('' if 'read' in permissions.get('audit',[]) else 'WHERE user_id=? ')+'ORDER BY id DESC LIMIT 5',[] if 'read' in permissions.get('audit',[]) else [g.user['id']]).fetchall()
 deadlines=[]
 if 'projects' in readable:
  for row in db.execute("SELECT id,title,status,data FROM records WHERE module='projects' AND status!='Concluído' AND coalesce(json_extract(data,'$.due_date'),'')!='' ORDER BY json_extract(data,'$.due_date') LIMIT 4"):
   data=json.loads(row['data']);deadlines.append({'id':row['id'],'title':row['title'],'due_date':data['due_date'],'owner':data.get('owner',''),'status':row['status']})
 return {'budget_total':sum(r['amount'] for r in budget)/100,'actions':sum(r['count'] for r in budget),'active_actions':statuses.get('Em execução',0),'open_tickets':sum(r['count'] for r in groups if r['module']=='tickets' and r['status']!='Resolvido'),'pending_approvals':pending,'departments':departments,'statuses':statuses,'monthly':monthly,'recent':recent,'activities':[dict(r) for r in activities],'deadlines':deadlines,'record_count':sum(r['count'] for r in groups)}

"""Cálculo RPPS parametrizado; tabelas devem ser cadastradas e aprovadas pela entidade.
Não presume alíquotas legais nem implementa eventos oficiais do eSocial.
"""
import calendar,json
from decimal import Decimal
from auth import ApiError
from db import get_db
from erp_core import related,load,require_draft,require_other,set_state,rounded

def bands_for(rules):
 rows=get_db().execute("SELECT data FROM erp_objects WHERE module='people' AND kind='tax_bands' AND deleted=0 AND json_extract(data,'$.rules')=?",(rules['id'],)).fetchall()
 return sorted([json.loads(r['data']) for r in rows],key=lambda d:d['lower'])

def approve_rules(o,a):
 require_draft(o);require_other(o);bands=bands_for(o)
 if not bands or bands[0]['lower']!=0 or bands[-1]['upper']!=0:raise ApiError('Cadastre todas as faixas de IRRF, iniciando em zero e terminando sem teto.')
 for i,b in enumerate(bands):
  if i and bands[i-1]['upper']!=b['lower']:raise ApiError('As faixas devem ser contínuas, sem lacunas ou sobreposição.')
  if not b['upper'] and i!=len(bands)-1:raise ApiError('Somente a última faixa pode não ter teto.')
 set_state(o,'Aprovado');return {'bands':bands,'rules':o['data']}

def calculate_payroll(o,a):
 require_draft(o);d=o['data'];r=related(o,'rules','people','rules');rules=r['data'];db=get_db()
 if r['state']!='Aprovado' or rules['period']!=d['period']:raise ApiError('Selecione parâmetros aprovados para a mesma competência.')
 if d['period'][:4]!=str(o['exercise']):raise ApiError('Competência fora do exercício.')
 if db.execute("SELECT 1 FROM erp_objects WHERE entity_id=? AND module='people' AND kind='runs' AND state IN ('Calculado','Aprovado') AND json_extract(data,'$.period')=?",(o['entity_id'],d['period'])).fetchone():raise ApiError('Já existe folha calculada nesta competência. Não será gerado pagamento duplicado.',409)
 bands=bands_for(r);employees=db.execute("SELECT id,data FROM erp_objects WHERE entity_id=? AND module='people' AND kind='employees' AND deleted=0 AND json_extract(data,'$.active')=1",(o['entity_id'],)).fetchall();count=0;total=0
 for row in employees:
  emp=json.loads(row['data'])
  if emp['admission'][:7]>d['period']:continue
  if emp['regime']!='RPPS':raise ApiError('Há vínculo RGPS: o cálculo exige o motor progressivo e tabelas oficiais homologadas. Esta rotina é exclusiva de RPPS parametrizado.')
  events=[json.loads(x['data']) for x in db.execute("SELECT data FROM erp_objects WHERE module='people' AND kind='events' AND deleted=0 AND json_extract(data,'$.employee')=? AND json_extract(data,'$.period')=? ORDER BY id",(row['id'],d['period']))]
  earnings=[x for x in events if x['type']=='Provento'];gross=emp['salary']+sum(x['amount'] for x in earnings)
  pension_base=emp['salary']+sum(x['amount'] for x in earnings if x['pension_base']);pension=rounded(Decimal(pension_base)*Decimal(rules['pension_rate'])/100)
  employer=rounded(Decimal(pension_base)*(Decimal(rules['employer_rate'])+Decimal(rules['supplementary_rate'] or 0))/100)
  dependents=db.execute("SELECT count(*) FROM erp_objects WHERE module='people' AND kind='dependents' AND deleted=0 AND json_extract(data,'$.employee')=? AND json_extract(data,'$.income_tax')=1",(row['id'],)).fetchone()[0]
  tax_base=max(0,emp['salary']+sum(x['amount'] for x in earnings if x['tax_base'])-pension-dependents*rules['dependent_deduction'])
  band=next((b for b in bands if tax_base>=b['lower'] and (not b['upper'] or tax_base<b['upper'])),None)
  if not band:raise ApiError('Base sem faixa tributária configurada.')
  tax=max(0,rounded(Decimal(tax_base)*Decimal(band['rate'])/100)-band['deduction']);other=sum(x['amount'] for x in events if x['type']=='Desconto');margin_base=gross-pension-tax-other
  if margin_base<0:raise ApiError('Descontos superiores aos proventos da matrícula '+emp['code'])
  available=rounded(Decimal(margin_base)*Decimal(rules['margin'])/100);consigned=0;denied=[]
  for discount in sorted([x for x in events if x['type']=='Consignação'],key=lambda x:x['priority']):
   if consigned+discount['amount']<=available:consigned+=discount['amount']
   else:denied.append({'code':discount['code'],'amount':discount['amount'],'reason':'Margem excedida'})
  net=margin_base-consigned;memory={'employee':emp,'rules':rules,'bands':bands,'pension_base':pension_base,'tax_base':tax_base,'margin_base':margin_base,'margin_limit':available,'rejected_consignments':denied,'events':events,'dependent_count':dependents}
  db.execute('INSERT INTO erp_payroll_lines(run_id,employee_id,gross,pension,tax,other,consigned,net,employer,memory) VALUES(?,?,?,?,?,?,?,?,?,?)',(o['id'],row['id'],gross,pension,tax,other,consigned,net,employer,json.dumps(memory,ensure_ascii=False)));count+=1;total+=net
 if not count:raise ApiError('Não há servidores elegíveis para esta competência.')
 set_state(o,'Calculado');return {'employees':count,'net_total':total,'notice':'Cálculo parametrizado. Homologar incidências e regras institucionais antes do uso oficial.'}

def approve_payroll(o,a):
 if o['state']!='Calculado':raise ApiError('Calcule a folha antes da aprovação.')
 require_other(o);set_state(o,'Aprovado');return {'period':o['data']['period']}

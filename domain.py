"""Regras compartilhadas; valores monetários são armazenados em centavos."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import re
from zoneinfo import ZoneInfo

MODULES = {
 'budget': {'label':'Planejamento e orçamento','fields':{'code':'Código','program':'Programa','action':'Ação','year':'Exercício','goal':'Meta física','indicator':'Indicador','due_date':'Prazo'},'statuses':['Planejado','Em execução','Concluído','Suspenso']},
 'accounting': {'label':'Registros contábeis','fields':{'code':'Documento','account':'Conta de referência','type':'Tipo de registro','date':'Competência','budget_id':'Ação orçamentária vinculada'},'statuses':['Rascunho','Em análise','Validado','Cancelado']},
 'payroll': {'label':'Registros de pessoal','fields':{'registration':'Matrícula','position':'Cargo','competence':'Competência','description':'Observações'},'statuses':['Rascunho','Em análise','Conferido','Cancelado']},
 'transparency': {'label':'Publicações','fields':{'category':'Categoria','reference':'Referência','date':'Data de referência','description':'Conteúdo público'},'statuses':['Rascunho','Publicado','Arquivado']},
 'tickets': {'label':'Central de atendimento','fields':{'priority':'Prioridade','description':'Descrição','workaround':'Solução provisória','resolution':'Solução definitiva'},'statuses':['Aberto','Em atendimento','Aguardando','Resolvido']},
 'projects': {'label':'Implantação','fields':{'owner':'Responsável','due_date':'Prazo','phase':'Fase','description':'Descrição'},'statuses':['Planejado','Em andamento','Concluído','Bloqueado']},
 'orders': {'label':'Ordens de serviço','fields':{'code':'Número da OS','quantity':'Quantidade','location':'Localidade','date':'Data de emissão','description':'Serviço solicitado'},'statuses':['Emitida','Em execução','Concluída','Cancelada']},
}
from erp_catalog import ERP_SCOPES
SCOPES = ERP_SCOPES + list(MODULES) + ['users','groups','audit','settings','maintenance','backups','compliance']
ACTIONS = ['read','write','delete','approve']
SLA = {'Crítico': (2,6,False,False), 'Alto':(4,8,False,True), 'Médio':(8,24,True,True), 'Baixo':(24,48,True,True)}

def now():
 return datetime.now(timezone.utc).isoformat(timespec='seconds')

def local_time(value=None):
 return (value or datetime.now(timezone.utc)).astimezone(ZoneInfo('America/Sao_Paulo'))

def password_strength(password):
 special = sum(not c.isalnum() for c in password)
 mixed = any(c.isalpha() for c in password) and any(c.isdigit() for c in password)
 if len(password)>10 and special>1 and mixed: return 'Forte'
 if len(password)>8 and special and mixed: return 'Média'
 return 'Fraca'

def money(value):
 try:
  amount=Decimal(str(value or 0))
  if not amount.is_finite() or amount<0 or amount>Decimal('999999999999.99') or amount.as_tuple().exponent < -2: raise ValueError()
  return int(amount*100)
 except (InvalidOperation,ValueError,TypeError): raise ValueError('Informe um valor positivo com até duas casas decimais.')

def business_deadline(start,hours,business,holidays=()):
 if not business: return (start+timedelta(hours=hours)).isoformat(timespec='seconds')
 current=local_time(start); remaining=hours*60
 while remaining>0:
  if current.weekday()>=5 or current.date().isoformat() in holidays:
   current=(current+timedelta(days=1)).replace(hour=8,minute=0,second=0,microsecond=0); continue
  if current.hour<8: current=current.replace(hour=8,minute=0,second=0,microsecond=0)
  if current.hour>=17:
   current=(current+timedelta(days=1)).replace(hour=8,minute=0,second=0,microsecond=0); continue
  end=current.replace(hour=17,minute=0,second=0,microsecond=0)
  minutes=min(remaining,(end-current).total_seconds()/60)
  current+=timedelta(minutes=minutes); remaining-=minutes
 return current.astimezone(timezone.utc).isoformat(timespec='seconds')

def validate_record(module,body):
 if not isinstance(body,dict): raise ValueError('Registro inválido.')
 spec=MODULES[module]; title=str(body.get('title','')).strip()
 if len(title)<3 or len(title)>180: raise ValueError('O título deve conter de 3 a 180 caracteres.')
 status=body.get('status',spec['statuses'][0])
 if status not in spec['statuses']: raise ValueError('Situação inválida para este módulo.')
 department=str(body.get('department','')).strip()
 if len(department)>120: raise ValueError('Unidade muito longa.')
 raw=body.get('data',{})
 if not isinstance(raw,dict): raise ValueError('Campos inválidos.')
 data={key:str(raw.get(key,'')).strip() for key in spec['fields']}
 if any(len(v)>5000 for v in data.values()): raise ValueError('Limite de 5.000 caracteres por campo.')
 for key in ['date','due_date']:
  if data.get(key):
   try: datetime.strptime(data[key],'%Y-%m-%d')
   except ValueError: raise ValueError('Data inválida. Use dia, mês e ano.')
 if module=='tickets':
  if data['priority'] not in SLA: raise ValueError('Selecione uma prioridade.')
  if len(data['description'])<10: raise ValueError('Descreva a solicitação em pelo menos 10 caracteres.')
  if status=='Resolvido' and len(data['resolution'])<10: raise ValueError('Registre a solução definitiva antes de resolver o chamado.')
 if module=='orders':
  if not data['code'] or not data['location'] or not data['description']: raise ValueError('Número, serviço e localidade são obrigatórios na OS.')
  try:
   if int(data['quantity'])<=0: raise ValueError()
  except ValueError: raise ValueError('A quantidade deve ser um inteiro maior que zero.')
 if module=='budget' and data['year'] and not re.fullmatch(r'20\d{2}',data['year']): raise ValueError('Exercício inválido.')
 return {'title':title,'department':department,'status':status,'amount':money(body.get('amount',0)),'data':data}

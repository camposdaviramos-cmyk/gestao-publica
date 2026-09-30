import json
from datetime import datetime, timezone, timedelta
from domain import now, business_deadline, SLA

def seed_demo(db):
 """Somente dados fictícios, incluídos por escolha explícita na instalação."""
 db.execute('INSERT OR REPLACE INTO settings VALUES(?,?)',('demo','true'))
 today=datetime.now(timezone.utc)
 def add(module,title,dept,status,amount,data,days=0):
  date=(today-timedelta(days=days)).isoformat(timespec='seconds')
  return db.execute('INSERT INTO records(module,title,department,status,amount,data,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)',(module,title,dept,status,round(amount*100),json.dumps(data,ensure_ascii=False),1,date,date)).lastrowid
 actions=[('Modernização das unidades de saúde','Saúde',2850000,'Em execução'),('Requalificação de espaços públicos','Obras e Urbanismo',1740000,'Em execução'),('Educação digital nas escolas','Educação',1260000,'Planejado'),('Proteção da orla e áreas verdes','Meio Ambiente',840000,'Em execução'),('Fortalecimento da assistência social','Assistência Social',680000,'Concluído'),('Transformação digital do município','Fazenda',430000,'Em execução')]
 for i,(title,dept,amount,status) in enumerate(actions):
  add('budget',title,dept,status,amount,{'code':f'2026.{1001+i}','program':'Desenvolvimento municipal','action':str(2001+i),'year':str(today.year),'goal':str((i+1)*10)+' unidades atendidas','indicator':'Unidades atendidas','due_date':(today+timedelta(days=30+i*5)).date().isoformat()},i*27)
 add('accounting','Aquisição de equipamentos — referência de teste','Fazenda','Em análise',125000,{'code':'REF-001','account':'Referência demonstrativa','type':'Registro preliminar','date':today.date().isoformat(),'budget_id':'1'})
 add('payroll','Conferência de competência — equipe de demonstração','Administração','Rascunho',12800,{'registration':'DEMO-001','position':'Exemplo fictício','competence':today.strftime('%Y-%m'),'description':'Registro fictício. Não representa cálculo de folha.'})
 for i,(title,priority,dept) in enumerate([('Orientação sobre exportação de relatório','Baixo','Fazenda'),('Acesso de nova equipe ao sistema','Médio','Educação'),('Revisão de permissões de consulta','Alto','Saúde')]):
  r,s,rb,sb=SLA[priority]
  add('tickets',title,dept,'Aberto' if i!=1 else 'Em atendimento',0,{'priority':priority,'description':'Solicitação fictícia para demonstração do atendimento integrado.','workaround':'','resolution':'','response_due':business_deadline(today,r,rb),'resolution_due':business_deadline(today,s,sb)})
 for i,(title,phase) in enumerate([('Validar bases para migração','Preparação'),('Homologar módulos prioritários','Primeiros 30 dias'),('Treinar equipes municipais','Capacitação'),('Concluir aceite das unidades','Até 90 dias')]):
  add('projects',title,'Fazenda','Em andamento' if i==0 else 'Planejado',0,{'owner':'Equipe de implantação','phase':phase,'due_date':(today+timedelta(days=3+i*7)).date().isoformat(),'description':'Marco demonstrativo; ajustar após emissão da ordem de serviço.'})
 add('orders','Preparação do ambiente de homologação','Fazenda','Emitida',0,{'code':'OS-DEMO-001','quantity':'1','location':'Secretaria Municipal de Fazenda','date':today.date().isoformat(),'description':'Ordem de serviço fictícia para demonstração.'})
 add('transparency','Cronograma de implantação — demonstração','Fazenda','Publicado',0,{'category':'Institucional','reference':'DEMO-001','date':today.date().isoformat(),'description':'Conteúdo fictício disponibilizado apenas para demonstração do portal público.'})

import json
import os
import sqlite3
from pathlib import Path
from flask import current_app, g, request
from cryptography.fernet import Fernet
from domain import MODULES, SCOPES, ACTIONS, now

DEFAULTS = {
 'municipality':'Rio das Ostras', 'department':'Secretaria Municipal de Fazenda',
 'min_password':12, 'max_attempts':5, 'lock_minutes':15, 'session_minutes':60,
 'dual_modules':['budget','accounting','payroll','transparency'],
 'holidays':[], 'signature_required':False, 'signature_reports':[],
 'support_email':'', 'support_phone':'', 'contract_date':'', 'demo':False,
}

def get_db():
 if 'db' not in g:
  g.db=sqlite3.connect(current_app.config['DATABASE'],timeout=15)
  g.db.row_factory=sqlite3.Row
  g.db.execute('PRAGMA foreign_keys=ON')
 return g.db

def settings():
 return {**DEFAULTS,**{r['key']:json.loads(r['value']) for r in get_db().execute('SELECT * FROM settings')}}

def key():
 return Fernet(current_app.config['FERNET_KEY'])

def audit(action,module,target='',detail=None,actor=None):
 user=getattr(g,'user',None)
 get_db().execute('INSERT INTO audit(user_id,actor,action,module,target,detail,ip,created_at) VALUES(?,?,?,?,?,?,?,?)',
  (user['id'] if user else None,actor or (user['name'] if user else 'Visitante'),action,module,str(target),json.dumps(detail or {},ensure_ascii=False),request.remote_addr or '',now()))

def notify(user_id,title,body):
 get_db().execute('INSERT INTO notifications(user_id,title,body,created_at) VALUES(?,?,?,?)',(user_id,title,body,now()))

def init_db(app):
 directory=Path(app.config['DATA_DIR']); directory.mkdir(parents=True,exist_ok=True)
 key_file=directory/'encryption.key'
 if not key_file.exists():
  if Path(app.config['DATABASE']).exists() and not os.environ.get('RIO_ENCRYPTION_KEY'):
   raise RuntimeError('A chave de criptografia está ausente. Recupere a chave original antes de iniciar o sistema.')
  try:
   with key_file.open('xb') as f: f.write(Fernet.generate_key())
  except FileExistsError: pass
 app.config['FERNET_KEY']=os.environ.get('RIO_ENCRYPTION_KEY') or key_file.read_bytes()
 with app.app_context():
  db=get_db(); db.executescript((Path(__file__).parent/'schema.sql').read_text(encoding='utf-8'))
  if not db.execute('SELECT 1 FROM groups').fetchone():
   all_permissions={m:ACTIONS for m in SCOPES}
   operator={m:['read','write'] for m in MODULES}
   reader={m:['read'] for m in MODULES}
   db.executemany('INSERT INTO groups(name,permissions) VALUES(?,?)',[(name,json.dumps(p)) for name,p in [('Administração',all_permissions),('Operação',operator),('Consulta',reader)]])
  for name,script in [('Otimizar índices','ANALYZE'),('Verificar integridade','PRAGMA integrity_check')]:
   if not db.execute('SELECT 1 FROM maintenance WHERE name=?',(name,)).fetchone():
    db.execute('INSERT INTO maintenance(name,encrypted_script,created_at) VALUES(?,?,?)',(name,key().encrypt(script.encode()).decode(),now()))
  db.commit()
  from erp_core import init_erp
  init_erp()

def close_db(error=None):
 db=g.pop('db',None)
 if db is not None: db.close()

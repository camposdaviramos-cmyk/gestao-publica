"""Backup consistente e comparação de dados existentes; não imprime conteúdo dos registros."""
import sys,json,hashlib,sqlite3,tempfile,os
from pathlib import Path
from contextlib import closing
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from backup import create_backup
from cryptography.fernet import Fernet
TABLES=['users','records','approvals','erp_objects','erp_balances','erp_stock','erp_ledger','erp_payroll_lines','erp_attachments']
def digest(dbpath):
 with closing(sqlite3.connect(dbpath)) as db:
  result={}
  for table in TABLES:
   rows=db.execute('SELECT * FROM '+table+' ORDER BY rowid').fetchall()
   result[table]={'count':len(rows),'sha256':hashlib.sha256(repr(rows).encode()).hexdigest()}
  return result
baseline=ROOT/'artifacts/integration-upgrade-baseline.json'
if sys.argv[1:] == ['before']:
 directory=ROOT/'data';secret=os.environ.get('RIO_ENCRYPTION_KEY') or (directory/'encryption.key').read_bytes()
 backup=create_backup(directory/'rio.db',directory/'backups',secret)
 with tempfile.TemporaryDirectory(prefix='rio-verify-upgrade-') as tmp:
  snapshot=Path(tmp)/'snapshot.db';snapshot.write_bytes(Fernet(secret).decrypt(backup.read_bytes()));facts=digest(snapshot)
 baseline.write_text(json.dumps({'backup':backup.name,'tables':facts},indent=2),encoding='utf-8');print('Backup:',backup.name);print('Contagens anteriores:',{k:v['count'] for k,v in facts.items()})
elif sys.argv[1:] == ['after']:
 expected=json.loads(baseline.read_text(encoding='utf-8'));facts=digest(ROOT/'data/rio.db')
 assert facts==expected['tables'],'Dados de negócio divergem do backup: investigar alterações concorrentes antes de concluir.'
 with closing(sqlite3.connect(ROOT/'data/rio.db')) as db:
  assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
  assert db.execute('PRAGMA foreign_key_check').fetchall()==[]
  for name in ['integration_configs','integration_jobs','integration_checks','siconfi_reports','siconfi_links']:assert db.execute('SELECT COUNT(*) FROM '+name).fetchone()[0]==0
 result={'preserved':True,'integrity':'ok','tables':{k:v['count'] for k,v in facts.items()},'backup':expected['backup'],'external_credentials':'Nenhuma credencial real cadastrada ou publicação enviada.'}
 (ROOT/'artifacts/integration-upgrade-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=True))
else:raise SystemExit('Use before ou after.')

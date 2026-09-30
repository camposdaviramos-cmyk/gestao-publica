"""Confere preservação da base anterior sem imprimir dados pessoais."""
import hashlib,json,os,sqlite3,tempfile
from contextlib import closing
from pathlib import Path
from cryptography.fernet import Fernet
ROOT=Path(__file__).resolve().parents[1]
backup=ROOT/'data/backups/rio-20260923-161127-107616.db.enc'
key=os.environ.get('RIO_ENCRYPTION_KEY') or (ROOT/'data/encryption.key').read_bytes()
def digest(db,table):
 rows=db.execute('SELECT * FROM '+table+' ORDER BY id').fetchall()
 return len(rows),hashlib.sha256(json.dumps(rows,sort_keys=True,default=str).encode()).hexdigest()
with tempfile.TemporaryDirectory(prefix='rio-migration-check-') as tmp:
 snapshot=Path(tmp)/'before.db';snapshot.write_bytes(Fernet(key).decrypt(backup.read_bytes()))
 with closing(sqlite3.connect(snapshot)) as before,closing(sqlite3.connect(ROOT/'data/rio.db')) as current:
  results={}
  for table in ['records','approvals','users']:
   a,b=digest(before,table),digest(current,table);assert a==b,table+' sofreu alteração inesperada';results[table]={'rows':b[0],'preserved':True}
  assert current.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
  assert not current.execute('PRAGMA foreign_key_check').fetchall()
  assert current.execute('SELECT version FROM erp_migrations').fetchone()[0]==1
  results['migration']=1;results['integrity']='ok'
 (ROOT/'artifacts/migration-annex.json').write_text(json.dumps(results,indent=2),encoding='utf-8');print(json.dumps(results))

import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
from datetime import datetime, timezone
from cryptography.fernet import Fernet

def create_backup(database,directory,encryption_key):
 directory=Path(directory); directory.mkdir(parents=True,exist_ok=True)
 stamp=datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')
 target=directory/f'rio-{stamp}.db.enc'
 with tempfile.TemporaryDirectory() as temp:
  snapshot=Path(temp)/'snapshot.db'
  with closing(sqlite3.connect(database)) as source, closing(sqlite3.connect(snapshot)) as destination:
   source.backup(destination)
  target.write_bytes(Fernet(encryption_key).encrypt(snapshot.read_bytes()))
 return target

def restore_backup(source,database,encryption_key):
 payload=Fernet(encryption_key).decrypt(Path(source).read_bytes())
 with tempfile.TemporaryDirectory() as temp:
  snapshot=Path(temp)/'snapshot.db'; snapshot.write_bytes(payload)
  with closing(sqlite3.connect(snapshot)) as check:
   if check.execute('PRAGMA integrity_check').fetchone()[0]!='ok': raise ValueError('O backup não passou pela verificação de integridade.')
   expected={'users','groups','records','audit','settings','sessions'}
   tables={r[0] for r in check.execute("SELECT name FROM sqlite_master WHERE type='table'")}
   if not expected<=tables: raise ValueError('Este arquivo não é um backup do Rio Gestão.')
   if check.execute('PRAGMA foreign_key_check').fetchall(): raise ValueError('O backup contém referências inválidas.')
   check.execute('DELETE FROM sessions'); check.commit()
   with closing(sqlite3.connect(database)) as destination: check.backup(destination)

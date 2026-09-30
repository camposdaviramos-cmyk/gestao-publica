"""Snapshot consistente sem inicializar aplicação nem executar migrações."""
import os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from backup import create_backup
directory=ROOT/'data';key=os.environ.get('RIO_ENCRYPTION_KEY') or (directory/'encryption.key').read_bytes()
target=create_backup(directory/'rio.db',directory/'backups',key)
print('Backup antes da atualização:',target.name)

"""Ferramentas operacionais. Restauração exige serviço interrompido."""
import argparse
import getpass
import os
import sqlite3
from pathlib import Path
from app import create_app
from backup import create_backup, restore_backup
from db import get_db
from domain import now

def main():
 parser=argparse.ArgumentParser(description='Administração do Rio Gestão')
 sub=parser.add_subparsers(dest='command',required=True)
 sub.add_parser('backup',help='Criar backup criptografado para execução pelo agendador')
 sub.add_parser('check',help='Verificar integridade da base')
 restore=sub.add_parser('restore',help='Restaurar cópia com o serviço interrompido'); restore.add_argument('file'); restore.add_argument('--confirm-service-stopped',action='store_true',required=True)
 reset=sub.add_parser('reset-password',help='Recuperação local de conta administrativa'); reset.add_argument('email')
 args=parser.parse_args(); app=create_app()
 if args.command=='backup':
  target=create_backup(app.config['DATABASE'],Path(app.config['DATA_DIR'])/'backups',app.config['FERNET_KEY']); print('Backup criado:',target)
 elif args.command=='check':
  with sqlite3.connect(app.config['DATABASE']) as db:
   print('Integridade:',db.execute('PRAGMA integrity_check').fetchone()[0]); errors=db.execute('PRAGMA foreign_key_check').fetchall(); print('Referências inválidas:',len(errors))
   if errors: raise SystemExit(1)
 elif args.command=='restore':
  safety=create_backup(app.config['DATABASE'],Path(app.config['DATA_DIR'])/'backups',app.config['FERNET_KEY']); print('Cópia anterior preservada:',safety)
  restore_backup(args.file,app.config['DATABASE'],app.config['FERNET_KEY']); print('Base restaurada. Todas as sessões foram encerradas.')
 elif args.command=='reset-password':
  from auth import check_password
  from werkzeug.security import generate_password_hash
  with app.app_context():
   db=get_db(); user=db.execute('SELECT id FROM users WHERE email=?',(args.email.lower(),)).fetchone()
   if not user: raise SystemExit('Conta não encontrada.')
   password=getpass.getpass('Nova senha: '); check_password(password)
   if password!=getpass.getpass('Confirme: '): raise SystemExit('Senhas diferentes.')
   db.execute('UPDATE users SET password=?,force_password=1,failures=0,locked_until=NULL WHERE id=?',(generate_password_hash(password),user['id']))
   db.execute('DELETE FROM sessions WHERE user_id=?',(user['id'],))
   db.execute('INSERT INTO audit(user_id,actor,action,module,target,detail,ip,created_at) VALUES(?,?,?,?,?,?,?,?)',(user['id'],'Operador local','Recuperação de senha','auth',str(user['id']),'{}','CLI',now())); db.commit(); print('Senha redefinida; troca obrigatória no próximo acesso.')

if __name__=='__main__': main()

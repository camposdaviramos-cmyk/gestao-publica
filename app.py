import json
import os
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, timezone
from flask import Flask, g, request, jsonify, send_from_directory, send_file
from werkzeug.security import generate_password_hash
from werkzeug.exceptions import HTTPException
from auth import install_auth, ApiError, require
from db import init_db, get_db, close_db, settings, audit
from domain import MODULES, now
from records import install_records
from admin import install_admin
from reports import install_reports
from content import LESSONS
from backup import create_backup

ROOT=Path(__file__).parent

def create_app(config=None):
 app=Flask(__name__,static_folder='static'); data_dir=Path(os.environ.get('RIO_DATA_DIR',ROOT/'data'))
 app.config.update(DATA_DIR=str(data_dir),DATABASE=str(data_dir/'rio.db'),SECURE_COOKIE=os.environ.get('RIO_SECURE_COOKIE')=='1',MAX_CONTENT_LENGTH=1024*1024,TRUSTED_HOSTS=os.environ.get('RIO_TRUSTED_HOSTS','localhost,127.0.0.1').split(','),DUMMY_HASH=generate_password_hash('nonexistent-'+os.urandom(16).hex()))
 if config: app.config.update(config)
 app.json.ensure_ascii=False;app.json.sort_keys=False
 app.teardown_appcontext(close_db); init_db(app); install_auth(app); install_records(app); install_admin(app); install_reports(app)
 from erp_api import install_erp
 install_erp(app)
 from inventory_api import install_inventory
 install_inventory(app)
 from asset_api import install_assets
 install_assets(app)
 from fleet_api import install_fleet
 install_fleet(app)
 from inventory_classifications import install_classifications
 install_classifications(app)
 from integrations import install_integrations
 install_integrations(app)
 from works_api import install_works
 install_works(app)
 from procurement_api import install_procurement
 install_procurement(app)
 from transparency_api import install_transparency
 install_transparency(app)
 from control_api import install_control
 install_control(app)
 from people_api import install_people
 install_people(app)
 from finance_api import install_finance
 install_finance(app)
 from social_api import install_social
 install_social(app)
 from bi_api import install_bi
 install_bi(app)
 from help_api import install_help
 install_help(app)
 from auction_api import install_auction
 install_auction(app)
 from cloud_api import install_cloud
 install_cloud(app)

 @app.after_request
 def finish(response):
  db=getattr(g,'db',None)
  if db:
   if response.status_code<400:
    if getattr(g,'user',None) and request.method=='GET' and request.path in ['/api/settings','/api/groups','/api/training','/api/audit','/api/backups','/api/maintenance','/api/compliance','/api/shortcuts']:
     audit('Consulta de funcionalidade',request.path.rsplit('/',1)[-1])
    db.commit()
   else: db.rollback()
  response.headers['X-Content-Type-Options']='nosniff'
  response.headers['X-Frame-Options']='DENY'
  response.headers['Referrer-Policy']='same-origin'
  response.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
  response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
  response.headers['Cache-Control']='no-store' if request.path.startswith('/api/') else 'no-cache'
  if app.config['SECURE_COOKIE']: response.headers['Strict-Transport-Security']='max-age=31536000'
  return response

 @app.errorhandler(sqlite3.IntegrityError)
 def constraint(error):
  return jsonify(error='Não foi possível salvar: registro duplicado ou referência inválida.'),409

 @app.errorhandler(HTTPException)
 def http_error(error):
  if request.path.startswith('/api/'): return jsonify(error='Solicitação inválida.' if error.code!=404 else 'Recurso não encontrado.'),error.code
  return error

 @app.errorhandler(Exception)
 def unexpected(error):
  app.logger.exception('Falha de processamento')
  return jsonify(error='Não foi possível concluir a operação. Tente novamente ou acione o suporte.'),500

 @app.get('/')
 @app.get('/portal')
 def index(): return send_from_directory(ROOT/'static','index.html')

 @app.get('/api/dashboard')
 def dashboard():
  from dashboard import dashboard_data
  result=dashboard_data(); audit('Acesso ao painel','dashboard'); return jsonify(result)

 @app.get('/api/training')
 def training():
  completed=[r[0] for r in get_db().execute('SELECT lesson FROM training_progress WHERE user_id=?',(g.user['id'],))]
  return jsonify(lessons=LESSONS,completed=completed)

 @app.post('/api/training/<lesson_id>/complete')
 def complete(lesson_id):
  if lesson_id not in [x['id'] for x in LESSONS]: raise ApiError('Conteúdo não encontrado.',404)
  get_db().execute('INSERT OR REPLACE INTO training_progress VALUES(?,?,?)',(g.user['id'],lesson_id,now())); audit('Tutorial concluído','training',lesson_id)
  return jsonify(message='Conclusão registrada.')

 @app.get('/api/compliance')
 def compliance():
  require('compliance'); path=ROOT/'docs'/'requisitos.json'
  return jsonify(json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'items':[]})

 @app.get('/api/backups')
 def backups():
  require('backups'); directory=Path(app.config['DATA_DIR'])/'backups'; files=sorted(directory.glob('*.enc'),reverse=True) if directory.exists() else []
  return jsonify(items=[{'name':p.name,'size':p.stat().st_size,'created_at':datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).isoformat()} for p in files[:50]])

 @app.post('/api/backups')
 def backup():
  require('backups','write'); target=create_backup(app.config['DATABASE'],Path(app.config['DATA_DIR'])/'backups',app.config['FERNET_KEY']); audit('Backup criado','backups',target.name)
  return jsonify(message='Backup criptografado criado.',name=target.name),201

 @app.get('/api/backups/<filename>')
 def download_backup(filename):
  require('backups'); directory=Path(app.config['DATA_DIR'])/'backups'
  if not filename.startswith('rio-') or not filename.endswith('.db.enc') or '/' in filename or '\\' in filename: raise ApiError('Arquivo inválido.')
  path=directory/filename
  if not path.is_file(): raise ApiError('Backup não encontrado.',404)
  audit('Backup exportado','backups',filename); return send_file(path,as_attachment=True,download_name=filename)

 return app

if __name__=='__main__':
 from waitress import serve
 app=create_app(); port=int(os.environ.get('RIO_PORT','8080')); host=os.environ.get('RIO_HOST','127.0.0.1')
 print(f'Rio Gestão iniciado em http://{host}:{port}',flush=True)
 serve(app,host=host,port=port,threads=8)

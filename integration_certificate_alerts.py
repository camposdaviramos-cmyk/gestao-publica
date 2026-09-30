"""Vencimento de certificados: avisos internos deduplicados por certificado e destinatário."""
import json
from datetime import datetime,timezone
from flask import g,request
from db import get_db,notify
from domain import now

def emit_certificate_alerts():
 db=get_db();instant=datetime.now(timezone.utc)
 for row in db.execute("SELECT * FROM integration_configs WHERE certificate_meta<>'{}'").fetchall():
  meta=json.loads(row['certificate_meta'])
  if not meta.get('expires_at'):continue
  expires=datetime.fromisoformat(meta['expires_at']);days=(expires.date()-instant.date()).days
  if days>30:continue
  phase='expirado' if expires<=instant else '30-dias';fingerprint=meta['fingerprint_sha256']
  inserted=db.execute('INSERT OR IGNORE INTO integration_certificate_alerts(entity_id,provider,environment,fingerprint,phase,user_id,created_at) VALUES(?,?,?,?,?,?,?)',(row['entity_id'],row['provider'],row['environment'],fingerprint,phase,g.user['id'],now())).rowcount
  if inserted:
   from integration_catalog import PROVIDERS
   label=PROVIDERS[row['provider']]['label'];entity=db.execute('SELECT name FROM erp_entities WHERE id=?',(row['entity_id'],)).fetchone()[0]
   title='Certificado vencido' if phase=='expirado' else f'Certificado vence em {days} dias'
   notify(g.user['id'],title,f'{label} · {entity} · {row["environment"]}. Validade: {expires.date().isoformat()}. Atualize o certificado na central de integrações.')

def install_certificate_alerts(app):
 with app.app_context():
  get_db().execute('CREATE TABLE IF NOT EXISTS integration_certificate_alerts(entity_id INTEGER NOT NULL,provider TEXT NOT NULL,environment TEXT NOT NULL,fingerprint TEXT NOT NULL,phase TEXT NOT NULL,user_id INTEGER NOT NULL REFERENCES users(id),created_at TEXT NOT NULL,PRIMARY KEY(entity_id,provider,environment,fingerprint,phase,user_id))');get_db().commit()
 @app.before_request
 def certificate_alerts():
  if request.path in ['/api/notifications','/api/me'] and g.user and g.user['group_id']==1:emit_certificate_alerts()

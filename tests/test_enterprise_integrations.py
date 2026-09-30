import base64,io,json,sqlite3,zipfile
from types import SimpleNamespace
import pytest
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign.validation import validate_pdf_signature
from pyhanko_certvalidator import ValidationContext
from test_system import app,admin,login,user,PASSWORD
from test_erp import ERP,erp
from test_integrations import configure,certificate,pdf
from db import get_db

def signature(session,**overrides):
 return configure(session,provider='signature',environment='producao',parameters={'reason':'Emissão institucional','allowed_users':''},secrets={'pfx':certificate(),'pfx_password':'senha-certificado'},**overrides)

def ldap(session,**overrides):
 return configure(session,provider='ldap',environment='producao',parameters={'host':'diretorio.example.test','port':'636','tls_mode':'ldaps','base_dn':'DC=example,DC=test','bind_dn':'CN=servico,DC=example,DC=test','login_attribute':'sAMAccountName'},secrets={'bind_password':'SenhaServicoExterno'},**overrides)

def verify_pdf(body):
 reader=PdfFileReader(io.BytesIO(body));assert len(reader.embedded_signatures)==1
 sig=reader.embedded_signatures[0]
 result=validate_pdf_signature(sig,signer_validation_context=ValidationContext(trust_roots=[sig.signer_cert],allow_fetching=False))
 assert result.intact and result.valid

def test_pdf_report_signed_and_original_format_preserved(admin,app):
 c,h=admin;assert signature(admin).status_code==200
 assert c.put('/api/settings',json={'signature_reports':['budget']},headers=h).status_code==200
 r=c.get('/api/reports/budget?format=pdf');assert r.status_code==200,r.json;verify_pdf(r.data)
 sid=r.headers['X-Signature-Record'];assert c.get('/api/signatures/'+sid+'/download').data==r.data
 with app.app_context():
  row=get_db().execute('SELECT * FROM document_signatures').fetchone();assert b'%PDF-' not in row['encrypted_document']
  with pytest.raises(sqlite3.IntegrityError):get_db().execute('DELETE FROM document_signatures')
 assert c.get('/api/reports/budget?format=json').is_json

def test_cms_report_contains_original_and_detached_signature(admin):
 c,h=admin;assert signature(admin).status_code==200
 c.put('/api/settings',json={'signature_reports':['budget']},headers=h)
 r=c.get('/api/reports/budget?format=xlsx');assert r.status_code==200
 from asn1crypto import cms
 from cryptography import x509
 from cryptography.hazmat.primitives.asymmetric import padding
 from cryptography.hazmat.primitives import hashes
 with zipfile.ZipFile(io.BytesIO(r.data)) as z:
  original=next(x for x in z.namelist() if x.endswith('.xlsx'));content=z.read(original)
  sig=cms.ContentInfo.load(z.read(original+'.p7s'))['content'];signer=sig['signer_infos'][0]
  attrs=signer['signed_attrs'];attrs_data=attrs.untag().dump();cert=x509.load_pem_x509_certificate(z.read('certificado.pem'))
  cert.public_key().verify(signer['signature'].native,attrs_data,padding.PKCS1v15(),hashes.SHA256())
  import hashlib
  digest=next(a['values'][0].native for a in attrs if a['type'].native=='message_digest');assert digest==hashlib.sha256(content).digest()
  assert content.startswith(b'PK')

def test_signature_authorization_and_attachment_evidence(erp,app):
 assert signature((erp.client,erp.headers)).status_code==200
 from test_siconfi_agenda import occurrence
 obj=occurrence(erp)
 r=erp.client.post('/api/erp/object/'+str(obj['id'])+'/attachments',json={'name':'documento.pdf','content':pdf()},headers=erp.headers);assert r.status_code==201,r.json
 aid=r.json['id'];url='/api/erp/attachments/'+str(aid)+'/sign'
 assert erp.client.post(url,json={},headers=erp.headers).status_code==400
 r=erp.client.post(url,json={'confirm':True},headers=erp.headers);assert r.status_code==201,r.json
 verify_pdf(erp.client.get('/api/signatures/'+str(r.json['id'])+'/download').data)
 detail=erp.client.get('/api/erp/object/'+str(obj['id'])).json;assert len(detail['signatures'])==1
 assert app.test_client().get('/api/signatures/'+str(r.json['id'])+'/download').status_code==401
 assert signature((erp.client,erp.headers),version=1,enabled=False).status_code==200
 assert erp.client.post(url,json={'confirm':True},headers=erp.headers).status_code==409

def test_certificate_probe_checks_real_pdf_signature(admin):
 c,h=admin;assert signature(admin).status_code==200
 r=c.post('/api/integrations/signature/consult',json={'entity':1,'environment':'producao'},headers=h)
 assert r.json['success'],r.json;assert r.json['result']['signature_valid']

def test_ldap_user_bind_and_no_local_fallback(admin,app,monkeypatch):
 c,h=admin;uid=user(admin,group=3);assert ldap(admin).status_code==200
 assert c.put('/api/integrations/ldap/bindings/'+str(uid),json={'entity':1,'login_name':'servidor*)(uid=*)'},headers=h).status_code==200
 import integration_directory as directory
 calls=[]
 class Connection:
  bound=True;result={'result':0};entries=[SimpleNamespace(entry_dn='CN=Servidor,DC=example,DC=test')]
  def search(self,base,query,**kwargs):calls.append(query)
  def unbind(self):pass
 def connect(parameters,secrets,user=None,password=None):
  if user:
   calls.append((user,password))
   if password!='SenhaADTeste!!':raise directory.RemoteError('Recusado')
  return Connection()
 monkeypatch.setattr(directory,'connect',connect)
 client=app.test_client();assert client.post('/api/login',json={'email':'second@example.test','password':PASSWORD}).status_code==401
 response=client.post('/api/login',json={'email':'second@example.test','password':'SenhaADTeste!!'});assert response.status_code==200
 assert '\\2a\\29\\28uid=\\2a\\29' in calls[0]
 assert client.get('/api/users').status_code==403
 assert client.post('/api/password',json={'current':'SenhaADTeste!!','password':'OutraSenhaForte2026!!'},headers={'X-CSRF-Token':response.json['csrf']}).status_code==409
 assert c.delete('/api/integrations/ldap/bindings/'+str(uid),headers=h).status_code==200
 assert client.get('/api/me').status_code==401
 assert client.post('/api/login',json={'email':'second@example.test','password':PASSWORD}).status_code==401

def test_ldap_tls_certificate_validation_and_starttls_order(monkeypatch):
 import integration_directory as directory,ssl
 calls=[]
 class Connection:
  def __init__(self,*a,**k):assert not k['auto_referrals']
  def open(self):calls.append('open')
  def start_tls(self):calls.append('tls');return True
  def bind(self):calls.append('bind');return True
  def unbind(self):pass
 def server(host,**kwargs):assert kwargs['tls'].validate==ssl.CERT_REQUIRED;return object()
 monkeypatch.setattr(directory,'Server',server);monkeypatch.setattr(directory,'Connection',Connection)
 directory.connect({'host':'dir.example.test','port':'389','tls_mode':'starttls','bind_dn':'CN=service'},{'bind_password':'secret'})
 assert calls==['open','tls','bind']

def test_ldap_preserves_local_admin_and_rotation_ends_sessions(admin,app,monkeypatch):
 c,h=admin;uid=user(admin);assert ldap(admin).status_code==200
 assert c.put('/api/integrations/ldap/bindings/1',json={'entity':1,'login_name':'admin'},headers=h).status_code==409
 assert c.put('/api/integrations/ldap/bindings/'+str(uid),json={'entity':1,'login_name':'second'},headers=h).status_code==200
 import integration_directory
 monkeypatch.setattr(integration_directory,'authenticate_directory',lambda *a:True)
 client=app.test_client();dh=login(client,'second@example.test')
 r=client.put('/api/users/1',json={'name':'Administrador Teste','email':'admin@example.test','group_id':3,'active':True,'force_password':False},headers=dh);assert r.status_code==409
 assert ldap(admin,version=1).status_code==200
 assert client.get('/api/me').status_code==401

def test_legacy_unsigned_report_keeps_existing_read_permissions(admin,app):
 user(admin,group=3);c=app.test_client();login(c,'second@example.test');assert c.get('/api/reports/budget?format=pdf').status_code==200

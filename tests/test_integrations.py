import base64,json,sqlite3
from io import BytesIO
from datetime import datetime,timedelta,timezone
import pytest
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from reportlab.pdfgen.canvas import Canvas
from test_system import app,admin,login,user
from test_erp import ERP,erp,reviewer
from db import get_db
from integration_transport import RemoteError

CNPJ='11222333000181'
def configure(session,provider='pncp',environment='homologacao',**extra):
 c,h=session
 d={'entity':1,'environment':environment,'version':0,'enabled':True,'parameters':{'cnpj':CNPJ,'login':'usuario-plataforma'},'secrets':{'senha':'SENHA-EXTERNA-SEGREDO'},**extra}
 return c.put('/api/integrations/'+provider,json=d,headers=h)

def pdf():
 stream=BytesIO();doc=Canvas(stream);doc.drawString(40,700,'Documento ficticio para testes locais');doc.save();return base64.b64encode(stream.getvalue()).decode()

def job_request(e):
 process=e.make('procurement','processes',code='12/2026',name='Compra de papel',modality='Pregão',judgment='Menor preço',legal_basis='Lei 14.133/2021')
 item=e.make('procurement','items',code='1',name='Papel A4',process=process['id'],unit='Resma',quantity='10',unit_price='20.25')
 payload=e.client.get('/api/integrations/pncp/template/'+str(process['id'])).json['payload']
 payload.update(codigoUnidadeCompradora='1',tipoInstrumentoConvocatorioId=1,modalidadeId=6,modoDisputaId=1,amparoLegalId=1,dataAberturaProposta='2026-10-01T08:00:00',dataEncerramentoProposta='2026-10-15T08:00:00')
 payload['itensCompra'][0].update(materialOuServico='M',tipoBeneficioId=4,criterioJulgamentoId=1)
 return process,item,{'entity':1,'environment':'homologacao','source_id':process['id'],'payload':payload,'document':pdf(),'document_title':'Edital para testes','document_type':1}

def create_job(e):
 assert configure((e.client,e.headers)).status_code==200
 source,item,data=job_request(e);r=e.client.post('/api/integration-jobs',json=data,headers=e.headers)
 assert r.status_code==201,r.json
 return r.json['id'],source,item,data

def action(e,id,op,**values):
 j=e.client.get('/api/integration-jobs/'+str(id)).json['item']
 return e.client.post(f'/api/integration-jobs/{id}/{op}',json={'version':j['version'],**values},headers=e.headers)

def test_secrets_encrypted_redacted_rotation_and_optimistic_lock(app,admin):
 c,h=admin;r=configure(admin);assert r.status_code==200,r.json
 assert r.json['config']['secrets_set']['senha'] is True
 assert 'SENHA-EXTERNA' not in r.get_data(as_text=True)
 listing=c.get('/api/integrations?entity=1');assert 'SENHA-EXTERNA' not in listing.get_data(as_text=True)
 with app.app_context():
  db=get_db();row=db.execute('SELECT * FROM integration_configs').fetchone();assert 'SENHA-EXTERNA' not in row['encrypted_secrets']
  assert 'SENHA-EXTERNA' not in str([tuple(x) for x in db.execute('SELECT detail FROM audit')])
 assert configure(admin).status_code==409
 assert configure(admin,version=1,secrets={}).json['config']['secrets_set']['senha']
 assert configure(admin,version=2,enabled=False,secrets={},clear_secrets=['senha']).json['config']['secrets_set']['senha'] is False
 assert configure(admin,version=3,secrets={}).status_code==400
 assert configure(admin,environment='producao').json['config']['version']==1

def test_central_admin_only_even_with_settings_override(app,admin):
 user(admin,group=3,permissions={'settings':['read','write']});c=app.test_client();h=login(c,'second@example.test')
 assert c.get('/api/integrations').status_code==403
 assert configure((c,h)).status_code==403
 assert admin[0].put('/api/integrations/pncp',json={}).status_code==403
 assert app.test_client().get('/api/integration-jobs').status_code==401

def test_unknown_parameters_and_unsupported_activation(admin):
 assert configure(admin,parameters={'cnpj':CNPJ,'login':'u','endpoint':'http://127.0.0.1'}).status_code==400
 assert configure(admin,provider='bll',parameters={},secrets={}).status_code==409
 assert configure(admin,provider='ibge',environment='producao',parameters={'municipio':'123'},secrets={}).status_code==400
 assert configure(admin,provider='ibge',environment='homologacao',parameters={'municipio':'3304524'},secrets={}).status_code==400

def test_consult_success_failure_and_history_persist(admin,monkeypatch,app):
 c,h=admin;assert configure(admin,provider='ibge',environment='producao',parameters={'municipio':'3304524'},secrets={}).status_code==200
 import integrations
 monkeypatch.setattr(integrations,'consult',lambda *a:{'id':3304524,'nome':'Rio das Ostras'})
 body={'entity':1,'environment':'producao'}
 r=c.post('/api/integrations/ibge/consult',json=body,headers=h);assert r.json['result']['nome']=='Rio das Ostras'
 def failed(*args):raise RemoteError('Serviço indisponível.')
 monkeypatch.setattr(integrations,'consult',failed)
 r=c.post('/api/integrations/ibge/consult',json=body,headers=h);assert not r.json['success']
 rows=c.get('/api/integrations/ibge/history?entity=1&environment=producao').json['items'];assert len(rows)==2 and rows[0]['success']==0
 with app.app_context():
  with pytest.raises(sqlite3.IntegrityError):get_db().execute('DELETE FROM integration_checks')

def certificate(expired=False):
 private=rsa.generate_private_key(public_exponent=65537,key_size=2048);name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'Certificado de teste local')]);instant=datetime.now(timezone.utc)
 cert=x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(private.public_key()).serial_number(x509.random_serial_number()).not_valid_before(instant-timedelta(days=10)).not_valid_after(instant+timedelta(days=-1 if expired else 30)).sign(private,hashes.SHA256())
 return base64.b64encode(pkcs12.serialize_key_and_certificates(b'Teste',private,cert,None,serialization.BestAvailableEncryption(b'senha-certificado'))).decode()

def test_certificate_vault_validates_password_and_expiry(admin):
 params={'provider':'esocial','enabled':False,'parameters':{'cnpj':CNPJ}}
 assert configure(admin,**params,secrets={'pfx':certificate(),'pfx_password':'errada'}).status_code==400
 assert configure(admin,**params,secrets={'pfx':certificate(True),'pfx_password':'senha-certificado'}).status_code==400
 r=configure(admin,**params,secrets={'pfx':certificate(),'pfx_password':'senha-certificado'});assert r.status_code==200,r.json
 assert 'Pendente' in r.json['config']['certificate']['chain_validation']
 assert 'senha-certificado' not in r.get_data(as_text=True)

def test_publication_dual_control_send_receipt_and_duplicate_block(erp,reviewer,monkeypatch,app):
 id,source,item,data=create_job(erp)
 assert action(erp,id,'approve').status_code==403
 assert action(reviewer,id,'approve').status_code==200
 assert action(erp,id,'send',confirmation='PRODUCAO').status_code==400
 import integration_publications
 calls=[]
 def publish(*args):calls.append(args);return {'http_status':201,'location':'https://treina.pncp.gov.br/api/pncp/v1/orgaos/'+CNPJ+'/compras/2026/1','response':{'compraUri':'confirmado'}}
 monkeypatch.setattr(integration_publications,'publish_pncp',publish)
 r=action(erp,id,'send',confirmation='ENVIAR PARA HOMOLOGACAO');assert r.json['state']=='Publicado',r.json
 assert len(calls)==1 and calls[0][-1].startswith(b'%PDF-')
 assert action(erp,id,'send',confirmation='ENVIAR PARA HOMOLOGACAO').status_code==409
 assert erp.client.post('/api/integration-jobs',json=data,headers=erp.headers).status_code==409
 detail=erp.client.get('/api/integration-jobs/'+str(id)).json
 assert len(detail['events'])==4 and 'encrypted_document' not in detail['item']
 assert erp.client.get(f'/api/integration-jobs/{id}/document').data.startswith(b'%PDF-')
 with app.app_context():
  with pytest.raises(sqlite3.IntegrityError):get_db().execute("UPDATE integration_jobs SET payload='{}' WHERE id=?",(id,))

def test_item_change_invalidates_review_and_cancel_allows_new_package(erp,reviewer):
 id,source,item,data=create_job(erp);erp.edit(item,quantity='11')
 assert action(reviewer,id,'approve').status_code==409
 assert action(erp,id,'cancel',reason='Valores do item foram corrigidos.').status_code==200
 data['payload']['itensCompra'][0].update(quantidade=11,valorTotal=222.75)
 assert erp.client.post('/api/integration-jobs',json=data,headers=erp.headers).status_code==201

def test_credential_rotation_invalidates_approved_package(erp,reviewer):
 id,*_=create_job(erp);assert action(reviewer,id,'approve').status_code==200
 assert configure((erp.client,erp.headers),version=1).status_code==200
 assert action(erp,id,'send',confirmation='ENVIAR PARA HOMOLOGACAO').status_code==409

def test_timeout_never_automatically_resends(erp,reviewer,monkeypatch):
 id,source,item,data=create_job(erp);assert action(reviewer,id,'approve').status_code==200
 import integration_publications
 def uncertain(*args):raise RemoteError('Resposta não confirmada.',uncertain=True)
 monkeypatch.setattr(integration_publications,'publish_pncp',uncertain)
 assert action(erp,id,'send',confirmation='ENVIAR PARA HOMOLOGACAO').json['state']=='Resultado incerto'
 assert action(erp,id,'send',confirmation='ENVIAR PARA HOMOLOGACAO').status_code==409
 assert action(erp,id,'cancel',reason='Tentar novamente sem confirmar.').status_code==409
 assert erp.client.post('/api/integration-jobs',json=data,headers=erp.headers).status_code==409

def test_payload_mismatch_and_invalid_pdf_rejected(erp):
 configure((erp.client,erp.headers));source,item,data=job_request(erp)
 data['payload']['itensCompra'][0]['valorTotal']=1
 assert erp.client.post('/api/integration-jobs',json=data,headers=erp.headers).status_code==400
 data['payload']['itensCompra'][0]['valorTotal']=202.5;data['document']=base64.b64encode(b'%PDF-1.4 fake').decode()
 assert erp.client.post('/api/integration-jobs',json=data,headers=erp.headers).status_code==400

def test_official_transport_fixed_hosts_and_no_redirect():
 from integration_transport import request_official,NoRedirect
 for url in ['http://pncp.gov.br/','https://127.0.0.1/','https://pncp.gov.br.evil.test/','https://user:pass@pncp.gov.br/','https://pncp.gov.br:444/']:
  with pytest.raises(RemoteError):request_official(url)
 assert NoRedirect().redirect_request(None,None,302,'',{},'https://evil.test') is None

def test_pncp_auth_header_and_multipart_protocol(monkeypatch):
 import integration_transport as transport
 calls=[]
 def request(url,method='GET',headers=None,body=None):
  calls.append((url,method,headers,body))
  if url.endswith('/login'):return 200,{'Authorization':'Bearer token-ficticio'},b''
  return 201,{'Location':'https://treina.pncp.gov.br/api/pncp/v1/orgaos/'+CNPJ+'/compras/2026/1'},b'{"compraUri":"https://treina.pncp.gov.br/api/pncp/v1/orgaos/11222333000181/compras/2026/1"}'
 monkeypatch.setattr(transport,'request_official',request)
 result=transport.publish_pncp('https://treina.pncp.gov.br/api/pncp',{'cnpj':CNPJ,'login':'u'},{'senha':'s'},{'operation':'compras','payload':'{}','document_title':'Edital','document_type':1},b'%PDF-test')
 assert json.loads(calls[0][3])=={'login':'u','senha':'s'}
 assert calls[1][2]['Authorization']=='Bearer token-ficticio'
 assert b'name="compra"' in calls[1][3] and b'name="documento"' in calls[1][3]
 assert 'token-ficticio' not in str(result)

"""Assinatura A1 real: PAdES para PDF e CMS destacado para os demais documentos."""
import base64,hashlib,io,json,uuid,zipfile
from datetime import datetime,timezone
from flask import g,request,jsonify,send_file
from cryptography import x509
from cryptography.hazmat.primitives.serialization import pkcs12,pkcs7,Encoding
from cryptography.hazmat.primitives import hashes
from auth import ApiError,require
from db import get_db,key,settings,audit
from domain import now
from erp_core import entity_access,load,event

def load_material(secrets):
 try:
  raw=base64.b64decode(secrets['pfx'],validate=True);private,cert,chain=pkcs12.load_key_and_certificates(raw,secrets['pfx_password'].encode())
  if private is None or cert is None:raise ValueError()
 except Exception:raise ApiError('Certificado A1 ou senha indisponíveis/inválidos.',409) from None
 if not cert.not_valid_before_utc<=datetime.now(timezone.utc)<cert.not_valid_after_utc:raise ApiError('Certificado fora do prazo de validade.',409)
 try:
  if not cert.extensions.get_extension_for_class(x509.KeyUsage).value.digital_signature:raise ApiError('Certificado não autoriza assinatura digital.',409)
 except x509.ExtensionNotFound:pass
 return raw,private,cert,chain or []

def sign_bytes(content,mime,secrets,parameters):
 raw,private,cert,chain=load_material(secrets)
 if mime=='application/pdf':
  from pyhanko.sign import signers
  from pyhanko.sign.fields import SigSeedSubFilter
  from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
  signer=signers.SimpleSigner.load_pkcs12_data(raw,other_certs=[],passphrase=secrets['pfx_password'].encode())
  if not signer:raise ApiError('Não foi possível carregar o assinante A1.',409)
  try:
   output=signers.sign_pdf(IncrementalPdfFileWriter(io.BytesIO(content)),signers.PdfSignatureMetadata(field_name='RioGestao_'+uuid.uuid4().hex,md_algorithm='sha256',subfilter=SigSeedSubFilter.PADES,reason=parameters.get('reason') or 'Documento institucional',location=parameters.get('location') or None),signer=signer)
   signed=output.getvalue()
  except Exception:raise ApiError('PDF não pôde ser assinado. Verifique integridade, senha e permissões de assinatura do documento.',409) from None
  return signed,'PAdES-B-B',cert
 builder=pkcs7.PKCS7SignatureBuilder().set_data(content).add_signer(cert,private,hashes.SHA256())
 for ca in chain:builder=builder.add_certificate(ca)
 return builder.sign(Encoding.DER,[pkcs7.PKCS7Options.DetachedSignature,pkcs7.PKCS7Options.Binary]),'CMS destacado',cert

def signer_config(entity):
 from integrations import get_config,decrypt
 row=get_config(entity,'signature','producao')
 if not row or not row['enabled']:raise ApiError('Configure e ative o certificado A1 de assinatura desta entidade na central de integrações.',409)
 parameters=json.loads(row['parameters']);allowed={x.strip() for x in parameters.get('allowed_users','').split(',') if x.strip()}
 if str(g.user['id']) not in allowed and not (not allowed and g.user['group_id']==1):raise ApiError('Seu usuário não está autorizado a utilizar o certificado institucional.',403)
 return row,parameters,decrypt(row)

def required_for(module,report_id=None):
 cfg=settings();return cfg['signature_required'] or module in cfg['signature_reports'] or (report_id is not None and module+':'+report_id in cfg['signature_reports'])

def authorize_report(module,entity,fmt,report_id=None):
 if fmt!='json' and required_for(module,report_id):signer_config(entity)

def signed_document(content,mime,filename,module,entity,attachment_id=None):
 row,parameters,secrets=signer_config(entity);signed,profile,cert=sign_bytes(content,mime,secrets,parameters)
 digest=hashlib.sha256(content).hexdigest();fingerprint=cert.fingerprint(hashes.SHA256()).hex()
 metadata={'profile':profile,'original_sha256':digest,'signature_sha256':hashlib.sha256(signed).hexdigest(),'certificate_sha256':fingerprint,'subject':cert.subject.rfc4514_string(),'issuer':cert.issuer.rfc4514_string(),'expires_at':cert.not_valid_after_utc.isoformat(),'signed_at':now(),'actor_id':g.user['id'],'config_version':row['version'],'trust_status':'Assinatura criptográfica; confiança ICP-Brasil e revogação devem ser conferidas no validador institucional.'}
 if mime=='application/pdf':artifact=signed;output_mime=mime;output_name=filename
 else:
  buffer=io.BytesIO()
  with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED) as z:
   z.writestr(filename,content);z.writestr(filename+'.p7s',signed);z.writestr('assinatura.json',json.dumps(metadata,ensure_ascii=False,indent=2));z.writestr('certificado.pem',cert.public_bytes(Encoding.PEM))
  artifact=buffer.getvalue();output_mime='application/zip';output_name=filename+'.assinado.zip'
 db=get_db();id=db.execute('INSERT INTO document_signatures(entity_id,module,attachment_id,name,mime,original_hash,metadata,encrypted_document,created_by,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)',(entity,module,attachment_id,output_name,output_mime,digest,json.dumps(metadata,ensure_ascii=False),key().encrypt(artifact),g.user['id'],now())).lastrowid
 audit('Documento assinado digitalmente',module,id,{'entity':entity,'profile':profile,'original_sha256':digest,'certificate_sha256':fingerprint})
 return artifact,output_mime,output_name,id

def report_response(buffer,mime,filename,module,entity,report_id=None):
 if required_for(module,report_id):
  body,mime,filename,id=signed_document(buffer.getvalue(),mime,filename,module,entity)
  response=send_file(io.BytesIO(body),mimetype=mime,as_attachment=True,download_name=filename);response.headers['X-Signature-Record']=str(id);return response
 buffer.seek(0);return send_file(buffer,mimetype=mime,as_attachment=True,download_name=filename)

def signature_probe(parameters,secrets):
 from reportlab.pdfgen.canvas import Canvas
 b=io.BytesIO();c=Canvas(b);c.drawString(40,700,'Teste local de assinatura institucional');c.save()
 signed,profile,cert=sign_bytes(b.getvalue(),'application/pdf',secrets,parameters)
 from pyhanko.pdf_utils.reader import PdfFileReader
 from pyhanko.sign.validation import validate_pdf_signature
 from pyhanko_certvalidator import ValidationContext
 from asn1crypto import x509 as asn1_x509
 embedded=PdfFileReader(io.BytesIO(signed)).embedded_signatures[-1]
 # Confere a criptografia usando o próprio certificado, sem atribuir confiança ICP-Brasil.
 result=validate_pdf_signature(embedded,signer_validation_context=ValidationContext(trust_roots=[asn1_x509.Certificate.load(cert.public_bytes(Encoding.DER))],allow_fetching=False))
 if not result.intact or not result.valid:raise ApiError('Falha na verificação criptográfica da assinatura de teste.',409)
 return {'profile':profile,'signature_valid':True,'certificate_subject':cert.subject.rfc4514_string(),'expires_at':cert.not_valid_after_utc.isoformat(),'trust_status':'Teste criptográfico local; não certifica cadeia ICP-Brasil ou revogação.'}

def install_signatures(app):
 with app.app_context():
  get_db().executescript('''CREATE TABLE IF NOT EXISTS document_signatures(id INTEGER PRIMARY KEY,entity_id INTEGER NOT NULL REFERENCES erp_entities(id),module TEXT NOT NULL,attachment_id INTEGER REFERENCES erp_attachments(id),name TEXT NOT NULL,mime TEXT NOT NULL,original_hash TEXT NOT NULL,metadata TEXT NOT NULL,encrypted_document BLOB NOT NULL,created_by INTEGER NOT NULL REFERENCES users(id),created_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS document_signatures_entity ON document_signatures(entity_id,module,id DESC);
CREATE TRIGGER IF NOT EXISTS document_signatures_immutable_update BEFORE UPDATE ON document_signatures BEGIN SELECT RAISE(ABORT,'Assinatura imutável'); END;
CREATE TRIGGER IF NOT EXISTS document_signatures_immutable_delete BEFORE DELETE ON document_signatures BEGIN SELECT RAISE(ABORT,'Assinatura imutável'); END;''');get_db().commit()
 @app.post('/api/erp/attachments/<int:id>/sign')
 def sign_attachment(id):
  db=get_db();db.execute('BEGIN IMMEDIATE');attachment=db.execute('SELECT * FROM erp_attachments WHERE id=?',(id,)).fetchone()
  if not attachment:raise ApiError('Documento não encontrado.',404)
  obj=load(attachment['object_id']);require(obj['module'],'write')
  if obj['module']=='social' and obj['kind']=='visits' and obj['data'].get('confidential'):require('social_confidential','write')
  if request.get_json().get('confirm') is not True:raise ApiError('Confirme a assinatura institucional do documento.')
  content=key().decrypt(attachment['encrypted']);mime='application/pdf' if content.startswith(b'%PDF-') else attachment['mime']
  _,_,_,signature_id=signed_document(content,mime,attachment['name'],obj['module'],obj['entity_id'],id)
  event(obj,'Documento assinado digitalmente',{'attachment_id':id,'signature_id':signature_id})
  return jsonify(message='Documento assinado e preservado no histórico.',id=signature_id),201
 @app.get('/api/signatures/<int:id>/download')
 def signature_download(id):
  row=get_db().execute('SELECT * FROM document_signatures WHERE id=?',(id,)).fetchone()
  if not row:raise ApiError('Assinatura não encontrada.',404)
  entity_access(row['entity_id']);require(row['module'])
  if row['attachment_id']:
   attachment=get_db().execute('SELECT object_id FROM erp_attachments WHERE id=?',(row['attachment_id'],)).fetchone();load(attachment['object_id'])
  elif row['created_by']!=g.user['id'] and g.user['group_id']!=1:raise ApiError('Relatório assinado disponível somente ao emissor e à administração.',403)
  audit('Documento assinado consultado',row['module'],id)
  return send_file(io.BytesIO(key().decrypt(row['encrypted_document'])),mimetype=row['mime'],as_attachment=True,download_name=row['name'])

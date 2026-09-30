import gzip,json,threading
from datetime import datetime,timedelta,timezone
import pytest
from test_integrations import app,admin,erp,reviewer,create_job,action,configure,CNPJ,pdf
from test_system import login
from test_erp import ERP
from db import get_db
from auth import ApiError
from erp_core import valid_document
from integration_transport import RemoteError

def test_cnpj_alphanumeric_official_example_and_strict_characters():
 assert valid_document('12.ABC.345/01DE-35','cnpj')=='12ABC34501DE35'
 assert valid_document('12abc34501de35','document')=='12ABC34501DE35'
 assert valid_document('11.222.333/0001-81','cnpj')==CNPJ
 assert valid_document('529.982.247-25','cpf')=='52998224725'
 for value,kind in [('12ABC34501DE34','cnpj'),('52998224725abc','cpf'),('11222333000181!','cnpj'),('1122233300018A','cnpj'),('０００００００００００','cpf')]:
  with pytest.raises(ApiError):valid_document(value,kind)

def test_gzip_response_real_protocol_and_bomb_limit(monkeypatch):
 import integration_transport as t
 content=gzip.compress(json.dumps({'nome':'Rio das Ostras'}).encode())
 class Response:
  status=200;headers={'Content-Encoding':'gzip'}
  def __enter__(self):return self
  def __exit__(self,*args):pass
  def read(self,size):return content[:size]
 class Opener:
  def open(self,*args,**kwargs):return Response()
 monkeypatch.setattr(t,'build_opener',lambda *args:Opener())
 assert t.decode_json(t.request_official('https://servicodados.ibge.gov.br/api/v1/localidades/municipios/3304524')[2])['nome']=='Rio das Ostras'
 content=gzip.compress(b'x'*(5*1024*1024+5))
 with pytest.raises(RemoteError,match='excede'):t.request_official('https://servicodados.ibge.gov.br/')

def test_two_concurrent_sends_publish_once(app,erp,reviewer,monkeypatch):
 id,*_=create_job(erp);action(reviewer,id,'approve');entered=threading.Event();release=threading.Event();calls=[];result=[]
 c=app.test_client();other=ERP((c,login(c)))
 import integration_publications
 def publish(*args):
  calls.append(1);entered.set();assert release.wait(5);return {'http_status':201,'response':{}}
 monkeypatch.setattr(integration_publications,'publish_pncp',publish)
 def first():result.append(action(other,id,'send',confirmation='ENVIAR PARA HOMOLOGACAO'))
 thread=threading.Thread(target=first);thread.start()
 try:
  assert entered.wait(5)
  assert action(erp,id,'send',confirmation='ENVIAR PARA HOMOLOGACAO').status_code==409
 finally:release.set();thread.join(timeout=6)
 assert result[0].json['state']=='Publicado' and len(calls)==1

def test_crash_recovery_does_not_resend(app,erp):
 id,*_=create_job(erp)
 with app.app_context():
  db=get_db();db.execute("UPDATE integration_jobs SET state='Enviando',updated_at=? WHERE id=?",((datetime.now(timezone.utc)-timedelta(minutes=5)).isoformat(),id));db.commit()
 assert action(erp,id,'recover').json['state']=='Resultado incerto'
 assert action(erp,id,'send',confirmation='ENVIAR PARA HOMOLOGACAO').status_code==409

def test_success_without_receipt_is_uncertain(monkeypatch):
 import integration_transport as t
 def request(url,*args,**kwargs):
  if url.endswith('login'):return 200,{'Authorization':'Bearer fake'},b''
  return 200,{},b'{}'
 monkeypatch.setattr(t,'request_official',request)
 with pytest.raises(RemoteError) as e:t.publish_pncp('https://treina.pncp.gov.br/api/pncp',{'cnpj':CNPJ,'login':'u'},{'senha':'s'},{'operation':'compras','payload':'{}','document_title':'Edital','document_type':1},b'pdf')
 assert e.value.uncertain

def test_real_contract_flow_template_and_preparation(erp,reviewer):
 from test_erp_flows import process
 p=process(erp);supplier=erp.make('procurement','suppliers',document='12ABC34501DE35')
 item=erp.make('procurement','items',process=p['id'],unit='UN',quantity='10',unit_price='100')
 proposal=erp.make('procurement','proposals',item=item['id'],supplier=supplier['id'],unit_price='90',qualified=True)
 for _ in range(4):erp.op(p,'advance_process',reason='Fase conferida e documentada')
 reviewer.op(p,'advance_process',reason='Adjudicação autorizada');reviewer.op(proposal,'award_proposal',reason='Melhor proposta habilitada');reviewer.op(p,'advance_process',reason='Homologação autorizada')
 contract=erp.make('procurement','contracts',code='15/2026',process=p['id'],supplier=supplier['id'],start='2026-02-01',end='2026-12-31',amount='900',manager='Gestor',inspector='Fiscal');reviewer.op(contract,'activate_contract')
 assert configure((erp.client,erp.headers)).status_code==200
 data=erp.client.get('/api/integrations/pncp/template/'+str(contract['id'])).json['payload'];assert data['niFornecedor']=='12ABC34501DE35'
 data.update(cnpjCompra=CNPJ,sequencialCompra=1,tipoContratoId=1,categoriaProcessoId=2,codigoUnidade='1',dataAssinatura='2026-01-31')
 response=erp.client.post('/api/integration-jobs',json={'entity':1,'environment':'homologacao','source_id':contract['id'],'payload':data,'document':pdf(),'document_title':'Contrato','document_type':12},headers=erp.headers)
 assert response.status_code==201,response.json

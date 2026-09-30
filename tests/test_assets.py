from test_erp import asset,erp,reviewer
from test_system import app,admin
from db import get_db

def test_asset_dossier_reports_alerts_and_dual_approval_batch(erp,reviewer,app):
 item=asset(erp)
 detail=erp.client.get('/api/erp/object/'+str(item['id']))
 assert detail.status_code==200 and detail.json['assets']['position']['gross']==10000
 assert detail.json['assets']['movements'][0]['fact']=='Ingresso'
 for report in ['depreciation','history','responsibility','tce','accounting']:
  response=erp.client.get('/api/assets/reports?entity=1&exercise=2026&report='+report+'&start=2026-01-01&end=2026-12-31')
  assert response.status_code==200,response.json
 assert erp.client.get('/api/assets/reports?entity=1&exercise=2026&report=tce&format=csv').status_code==200
 alerts=erp.client.post('/api/assets/alerts',json={'entity':1,'exercise':2026},headers=erp.headers)
 assert alerts.status_code==200 and alerts.json['count']==1
 with app.app_context():
  assert get_db().execute("SELECT COUNT(*) FROM notifications WHERE title='Pendência patrimonial'").fetchone()[0]==1
  assert erp.client.get('/api/notifications').status_code==200
  assert get_db().execute("SELECT COUNT(*) FROM notifications WHERE title='Pendência patrimonial'").fetchone()[0]==1
 preview=erp.client.post('/api/assets/batches/preview',json={'entity':1,'exercise':2026,'operation':'depreciate','parameters':{'period':'2026-01','units':'0'},'selection':[item['id']]},headers=erp.headers)
 assert preview.status_code==201,preview.json
 denied=erp.client.post('/api/assets/batches/'+str(preview.json['id'])+'/execute',json={'version':1},headers=erp.headers)
 assert denied.status_code==403
 executed=reviewer.client.post('/api/assets/batches/'+str(preview.json['id'])+'/execute',json={'version':1},headers=reviewer.headers)
 assert executed.status_code==200,executed.json
 assert erp.get(item)['balances']['depreciated']==3333
 history=erp.client.get('/api/assets/reports?entity=1&exercise=2026&report=history&start=2026-01-01&end=2026-12-31').json['items']
 assert [x['fact'] for x in history]==['Ingresso','Depreciação']

def test_month_integral_starts_in_following_month(erp):
 item=asset(erp,'Mês integral')
 detail=erp.client.get('/api/erp/object/'+str(item['id'])).json
 assert detail['assets']['position']['cycle_start']=='2026-02-01'
 erp.op(item,'depreciate',409,period='2026-01')
 erp.op(item,'depreciate',period='2026-02')
 assert erp.get(item)['balances']['depreciated']==3333

def test_asset_history_is_immutable_in_database(erp,app):
 item=asset(erp);erp.op(item,'depreciate',period='2026-01')
 import sqlite3
 with app.app_context():
  movement=get_db().execute('SELECT id FROM asset_movements WHERE asset_id=? ORDER BY id DESC',(item['id'],)).fetchone()[0]
  try:get_db().execute("UPDATE asset_movements SET description='alterado' WHERE id=?",(movement,))
  except sqlite3.IntegrityError:pass
  else:raise AssertionError('Movimento patrimonial deveria ser imutável')

def test_temporary_transfer_between_entities_and_return(erp,reviewer):
 source=asset(erp)
 response=erp.client.post('/api/erp/entities',json={'code':'CAMARA','name':'Câmara Municipal'},headers=erp.headers);assert response.status_code==201
 from test_erp import ERP
 destination=ERP((erp.client,erp.headers),response.json['id'])
 debit=destination.make('finance','accounts',nature='Devedora',active=True,analytic=True)
 credit=destination.make('finance','accounts',nature='Credora',active=True,analytic=True)
 klass=destination.make('assets','classes',asset_account=debit['id'],depreciation_account=credit['id'],useful_months=60,residual_percent='0')
 transfer=erp.make('assets','entity_transfers',asset=source['id'],type='Temporária',date='2026-02-01',destination_entity=response.json['id'],destination_class=klass['id'],destination_location='Sede da Câmara',destination_owner='Responsável da Câmara',expected_return='2026-12-31',legal_basis='Termo formal de cessão temporária')
 result=reviewer.op(transfer,'transfer_asset_entity')['result'];dest_id=result['destination_asset']
 assert erp.client.get('/api/erp/object/'+str(dest_id)).json['item']['state']=='Ativo'
 reviewer.op(transfer,'return_asset_entity',date='2026-03-01',reason='Devolução conferida pela comissão')
 assert erp.get(source)['state']=='Ativo'
 assert erp.client.get('/api/erp/object/'+str(dest_id)).json['item']['state']=='Baixado'

def test_donation_between_entities_is_definitive(erp,reviewer):
 source=asset(erp)
 response=erp.client.post('/api/erp/entities',json={'code':'AUTARQUIA','name':'Autarquia Municipal'},headers=erp.headers);assert response.status_code==201
 from test_erp import ERP
 destination=ERP((erp.client,erp.headers),response.json['id'])
 debit=destination.make('finance','accounts',nature='Devedora',active=True,analytic=True);credit=destination.make('finance','accounts',nature='Credora',active=True,analytic=True)
 klass=destination.make('assets','classes',asset_account=debit['id'],depreciation_account=credit['id'],useful_months=60,residual_percent='0')
 transfer=erp.make('assets','entity_transfers',asset=source['id'],type='Doação',date='2026-02-01',destination_entity=response.json['id'],destination_class=klass['id'],destination_location='Sede da autarquia',destination_owner='Gestor patrimonial',legal_basis='Lei autorizativa e termo de doação')
 result=reviewer.op(transfer,'transfer_asset_entity')['result']
 assert erp.get(source)['state']=='Doado'
 assert erp.client.get('/api/erp/object/'+str(result['destination_asset'])).json['item']['state']=='Ativo'
 reviewer.op(transfer,'return_asset_entity',409,date='2026-03-01',reason='Retorno indevido')

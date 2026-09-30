import pytest
from test_system import app,admin
from test_erp import erp,reviewer,stock

def test_grant_creates_stock_exit_atomically(erp,reviewer):
 a,b,material,mov=stock(erp)
 entry=mov('Entrada','5',expiry='2027-01-01');erp.op(entry,'execute_stock')
 person=erp.make('social','persons',address='Rua de teste',birth='1990-01-01')
 benefit=erp.make('social','benefits',amount='10',interval_days=0,capacity=10,material=material['id'],units='3')
 grant=erp.make('social','concessions',person=person['id'],benefit=benefit['id'],date='2026-01-02',professional='Responsável',warehouse=a['id'])
 result=reviewer.op(grant,'grant_benefit');assert result['result']['stock_movement']
 rows=erp.client.get('/api/erp/stock?entity=1&exercise=2026').json['items'];assert rows[0]['quantity']==2000000
 grant2=erp.make('social','concessions',person=person['id'],benefit=benefit['id'],date='2026-01-03',professional='Responsável',warehouse=a['id']);reviewer.op(grant2,'grant_benefit',409)
 assert erp.get(grant2)['state']=='Rascunho' and erp.get(grant2)['balances']=={}
 movements=erp.client.get('/api/erp/inventory/movements?entity=1&exercise=2026').json['items'];assert len(movements)==2

def test_cancelled_appointment_releases_time_and_cannot_attend(erp):
 p=erp.make('social','persons',address='Rua de teste',birth='1990-01-01')
 data={'person':p['id'],'professional':'Técnica','unit':'CRAS','start':'2026-02-02T09:00','end':'2026-02-02T10:00'}
 appointment=erp.make('social','appointments',**data);erp.op(appointment,'cancel_appointment',reason='Cancelado a pedido do cidadão')
 erp.make('social','appointments',**data)
 erp.op(appointment,'attend_appointment',409,reason='Atendimento indevido após cancelamento')

def test_last_editor_cannot_approve(erp,reviewer):
 report=erp.make('control','reports',period='2026-01',opinion='Parecer inicial',conclusion='Conclusão inicial',signatory='Controlador')
 reviewer.edit(report,opinion='Parecer alterado pelo segundo servidor')
 reviewer.op(report,'seal_report',403)

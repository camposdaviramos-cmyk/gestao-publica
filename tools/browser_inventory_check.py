"""Exercita recebimento, entrega, devolução, permissões e relatórios pela interface."""
import json,sys,tempfile,threading,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
from app import create_app
from test_system import PASSWORD,login,user
from test_erp import ERP
from test_inventory import supply,invoice,requisition
from waitress import create_server
from playwright.sync_api import sync_playwright,expect

with tempfile.TemporaryDirectory(prefix='rio-inventory-browser-') as directory:
 app=create_app({'TESTING':True,'DATA_DIR':directory,'DATABASE':str(Path(directory)/'rio.db')});client=app.test_client();response=client.post('/api/setup',json={'name':'Administradora de Testes','email':'admin@example.test','password':PASSWORD});assert response.status_code==201
 headers=login(client);e=ERP((client,headers));user((client,headers));c=app.test_client();checker=ERP((c,login(c,'second@example.test')))
 w,m,s,commitment,req,auth,ai=supply(e,checker);e.edit(m,name='Material da prova de conceito',group='Consumo',subgroup='Expediente')
 inv=invoice(e,s,auth);result=e.op(inv,'suggest_authorized_items');line={'id':result['result']['created_items'][0]};e.edit(line,quantity='4',expiry='2027-01-01')
 dept,center,request,item=requisition(e,w,m,'3');checker.op(request,'approve_requisition')
 user((client,headers),email='warehouse@example.test',group=2,permissions={'inventory':['read','write']})
 server=create_server(app,host='127.0.0.1',port=8096,threads=4);thread=threading.Thread(target=server.run,daemon=True);thread.start();errors=[];checks=[]
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch();page=browser.new_page(locale='pt-BR',viewport={'width':1440,'height':1000},reduced_motion='reduce');page.on('pageerror',lambda error:errors.append(str(error)))
   def sign_in(email):
    page.goto('http://127.0.0.1:8096');page.locator('[name=email]').fill(email);page.locator('[name=password]').fill(PASSWORD);page.get_by_role('button',name='Entrar no sistema').click();expect(page.locator('.stats')).to_be_visible();page.goto('http://127.0.0.1:8096/#/inventory');expect(page.locator('[data-action=inv-reports]')).to_be_visible()
   def open_object(obj):
    page.evaluate('(id)=>erpView(id)',obj['id']);expect(page.locator('#modal')).to_be_visible()
   def operate(op):
    page.locator('[data-operation='+op+']').click();expect(page.locator('#erp-operate')).to_be_visible()
   def submit():
    page.locator('#erp-operate').get_by_role('button',name='Efetivar operação').click();expect(page.locator('#modal')).not_to_be_visible()
   sign_in('second@example.test');open_object(inv);operate('post_inventory_invoice');submit();open_object(inv);expect(page.locator('#modal')).to_contain_text('Nota efetivada com liquidação');checks.append('Recebimento de nota com liquidação e estoque pela interface');page.get_by_role('button',name='Fechar janela',exact=True).click()
   page.evaluate('()=>api("/logout","POST",{})');page.reload();sign_in('admin@example.test')
   open_object(item);operate('deliver_requisition');page.locator('#erp-operate [name=date]').fill('2026-01-08');page.locator('#erp-operate [name=quantity]').fill('2');submit();open_object(item);expect(page.locator('#modal')).to_contain_text('Entregas e devoluções');operate('return_requisition');page.locator('#erp-operate [name=date]').fill('2026-01-09');page.locator('#erp-operate [name=quantity]').fill('1');page.locator('#erp-operate [name=expiry]').fill('2027-01-01');submit();checks.append('Entrega parcial e devolução vinculada pela interface')
   open_object(item);operate('cancel_requisition_balance');page.locator('#erp-operate [name=reason]').fill('Saldo não necessário para a unidade');submit();checks.append('Cancelamento do saldo pendente')
   open_object(w);page.locator('[data-action=inv-permissions]').click();form=page.locator('#inv-permissions-form');expect(form).to_be_visible();form.locator('[name=restricted]').check();form.get_by_role('button',name='Salvar autorizações').click();expect(page.locator('#modal')).not_to_be_visible();checks.append('Configuração de autorização individual')
   open_object(req);page.locator('[data-action=inv-dossier]').click();expect(page.locator('#modal')).to_contain_text('Pesquisa PESQ-1');expect(page.locator('#modal')).to_contain_text('Homologado');expect(page.locator('#modal')).to_contain_text('Solicitação de recursos orçamentários');page.get_by_role('button',name='Fechar janela',exact=True).click();checks.append('Rastreabilidade de pedido, licitação, autorização e notas')
   page.locator('[data-action=inv-reports]').click();expect(page.locator('#inv-report-results tbody tr')).to_have_count(1)
   for kind in ['balances','consumption','movements','monthly']:
    page.locator('#inv-report-form [name=report]').select_option(kind);page.locator('#inv-report-form').get_by_role('button',name='Consultar',exact=True).click();expect(page.locator('#inv-report-results tbody tr').first).to_be_visible()
   with page.expect_download() as result:page.locator('[data-action=inv-csv]').click()
   assert result.value.suggested_filename.endswith('.csv')
   with page.expect_download() as result:page.locator('[data-action=inv-pdf]').click()
   assert result.value.suggested_filename.endswith('.pdf');checks.append('Quatro relatórios com exportações CSV e PDF')
   for theme in ['light','dark']:
    page.get_by_role('button',name='Fechar janela',exact=True).click()
    if page.locator('html').get_attribute('data-theme')!=theme:page.locator('[data-action=theme]').click()
    page.locator('[data-action=inv-reports]').click()
    for width in [390,768,1440]:
     page.set_viewport_size({'width':width,'height':1000});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(theme,width)
    page.screenshot(path=str(ROOT/'artifacts'/f'inventory-{theme}-reports.png'),full_page=True)
    checks.append('Relatórios no tema '+theme+' em 390, 768 e 1440 px')
   page.get_by_role('button',name='Fechar janela',exact=True).click();page.locator('[data-kind=materials]').click();page.locator('[data-action=erp-new]').click();f=page.locator('#erp-editor');f.locator('[name=code]').fill('MAT-NCM-POC');f.locator('[name=name]').fill('Material com classificação oficial');f.locator('[name=unit]').fill('UN');f.locator('[name=ncm]').fill('01012100');f.locator('[data-action=ic-search][data-kind=ncm]').click();expect(f.locator('[data-classification=ncm]')).to_be_visible();f.locator('[data-classification=ncm]').select_option('0101.21.00');f.get_by_role('button',name='Salvar',exact=True).click();expect(page.locator('#modal')).not_to_be_visible();expect(page.locator('table').get_by_text('Material com classificação oficial')).to_be_visible();checks.append('Consulta e vínculo de NCM oficial no cadastro')
   page.locator('[data-action=ic-tables]').click();expect(page.locator('#modal')).to_contain_text('10.515');expect(page.locator('#modal')).to_contain_text('920');checks.append('Versões e fontes oficiais de NCM e NBS')
   browser.close()
  assert not errors,errors
  result={'passed':len(checks),'checks':checks,'javascript_errors':errors};(ROOT/'artifacts/browser-inventory-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))
 finally:server.close();thread.join(timeout=3)

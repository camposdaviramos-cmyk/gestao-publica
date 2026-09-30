"""Valida a interface patrimonial, relatórios, histórico, lote e temas."""
import json,sys,tempfile,threading
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
from app import create_app
from test_system import PASSWORD,login
from test_erp import ERP,asset
from waitress import create_server
from playwright.sync_api import sync_playwright,expect

with tempfile.TemporaryDirectory(prefix='rio-assets-browser-') as directory:
 app=create_app({'TESTING':True,'DATA_DIR':directory,'DATABASE':str(Path(directory)/'rio.db')});client=app.test_client();assert client.post('/api/setup',json={'name':'Administradora de Testes','email':'admin@example.test','password':PASSWORD}).status_code==201
 headers=login(client);e=ERP((client,headers));item=asset(e)
 server=create_server(app,host='127.0.0.1',port=8095,threads=4);thread=threading.Thread(target=server.run,daemon=True);thread.start();errors=[];checks=[]
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch();page=browser.new_page(locale='pt-BR',viewport={'width':1440,'height':1000},reduced_motion='reduce');page.on('pageerror',lambda error:errors.append(str(error)))
   page.goto('http://127.0.0.1:8095');page.locator('[name=email]').fill('admin@example.test');page.locator('[name=password]').fill(PASSWORD);page.get_by_role('button',name='Entrar no sistema').click();expect(page.locator('.stats')).to_be_visible();page.goto('http://127.0.0.1:8095/#/assets');expect(page.locator('[data-action=asset-reports]')).to_be_visible();checks.append('Módulo patrimonial carregado')
   page.evaluate('(id)=>erpView(id)',item['id']);expect(page.locator('#modal')).to_contain_text('Posição patrimonial atual');expect(page.locator('#modal')).to_contain_text('Histórico patrimonial completo');page.get_by_role('button',name='Fechar janela',exact=True).click();checks.append('Dossiê e histórico do bem')
   page.locator('[data-action=asset-reports]').click();expect(page.locator('#asset-report-results tbody tr')).to_have_count(1)
   for kind in ['depreciation','history','responsibility','tce']:
    page.locator('#asset-report-form [name=report]').select_option(kind);page.locator('#asset-report-form').get_by_role('button',name='Consultar',exact=True).click();expect(page.locator('#asset-report-results tbody tr').first).to_be_visible()
   with page.expect_download() as result:page.locator('[data-action=asset-csv]').click()
   assert result.value.suggested_filename.endswith('.csv');checks.append('Relatórios patrimoniais e exportação')
   page.get_by_role('button',name='Fechar janela',exact=True).click();page.locator('[data-action=asset-batch]').click();expect(page.locator('#asset-batch-form')).to_be_visible();expect(page.locator('#asset-batch-form [name=asset]')).to_have_count(1);checks.append('Preparação de lote com seleção de bens')
   for theme in ['light','dark']:
    page.get_by_role('button',name='Fechar janela',exact=True).click()
    if page.locator('html').get_attribute('data-theme')!=theme:page.locator('[data-action=theme]').click()
    page.locator('[data-action=asset-reports]').click()
    for width in [390,768,1440]:
     page.set_viewport_size({'width':width,'height':1000});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(theme,width)
    page.screenshot(path=str(ROOT/'artifacts'/('assets-'+theme+'-reports.png')),full_page=True);checks.append('Patrimônio '+theme+' responsivo')
   browser.close()
  assert not errors,errors
  result={'passed':len(checks),'checks':checks,'javascript_errors':errors};(ROOT/'artifacts/browser-assets-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))
 finally:server.close();thread.join(timeout=3)

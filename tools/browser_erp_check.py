import json,sys,tempfile,threading,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app import create_app
from erp_catalog import CATALOG
from waitress import create_server
from playwright.sync_api import sync_playwright,expect

with tempfile.TemporaryDirectory(prefix='rio-erp-browser-') as directory:
 app=create_app({'DATA_DIR':directory,'DATABASE':str(Path(directory)/'rio.db')})
 c=app.test_client();password='TesteSeguro2026!!';c.post('/api/setup',json={'name':'Administradora de Testes','email':'admin@example.test','password':password})
 server=create_server(app,host='127.0.0.1',port=8099,threads=4);thread=threading.Thread(target=server.run,daemon=True);thread.start();errors=[];checks=[];timings={}
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch();page=browser.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce');page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto('http://127.0.0.1:8099');page.locator('[name=email]').fill('admin@example.test');page.locator('[name=password]').fill(password);page.get_by_role('button',name='Entrar no sistema').click();expect(page.locator('.stats')).to_be_visible()
   for module in ['modulehub',*CATALOG,'annex']:
    started=time.perf_counter();page.goto('http://127.0.0.1:8099/#/'+module);expect(page.locator('#main h1')).to_be_visible();expect(page.locator('#main .loading-panel')).to_have_count(0)
    assert page.locator('#main').get_by_text('Não foi possível abrir a página',exact=True).count()==0,module
    timings[module]=round((time.perf_counter()-started)*1000);checks.append('Rota '+module)
   page.goto('http://127.0.0.1:8099/#/finance');page.locator('[data-kind=funds]').click();page.locator('[data-action=erp-new]').click();form=page.locator('#erp-editor');form.locator('[name=code]').fill('1500');form.locator('[name=name]').fill('Recursos ordinários');form.get_by_role('button',name='Salvar',exact=True).click();expect(page.locator('table').get_by_text('Recursos ordinários')).to_be_visible();checks.append('Cadastro de fonte pelo formulário')
   page.locator('[data-action=erp-view]').click();expect(page.locator('#modal').get_by_text('Cadastro criado',exact=True)).to_be_visible();page.locator('[data-action=erp-edit]').click();page.locator('#erp-editor [name=name]').fill('Recursos ordinários atualizados');page.locator('#erp-editor').get_by_role('button',name='Salvar',exact=True).click();expect(page.locator('table').get_by_text('Recursos ordinários atualizados')).to_be_visible();checks.append('Edição versionada e histórico')
   with page.expect_download() as download:page.locator('[data-action=erp-csv]').click()
   assert download.value.suggested_filename.endswith('.csv');checks.append('Exportação CSV real')
   page.locator('[data-action=erp-view]').click();page.locator('#erp-upload [name=file]').set_input_files({'name':'evidencia.pdf','mimeType':'application/pdf','buffer':b'%PDF-1.4\nTeste navegador'});page.locator('#erp-upload').get_by_role('button',name='Anexar documento',exact=True).click();expect(page.locator('[data-action=erp-attachment]')).to_be_visible();page.get_by_role('button',name='Fechar janela',exact=True).click();checks.append('Upload de documento protegido')
   page.goto('http://127.0.0.1:8099/#/control');page.locator('[data-kind=obligations]').click();page.locator('[data-action=erp-new]').click();f=page.locator('#erp-editor');f.locator('[name=code]').fill('OBR1');f.locator('[name=name]').fill('Entrega mensal');f.locator('[name=description]').fill('Descrição de obrigação de teste');f.locator('[name=legislation]').fill('Ato fictício de teste');f.locator('[name=level]').select_option('Municipal');f.locator('[name=owner]').fill('Controladoria');f.locator('[name=first_due]').fill('2026-01-31');f.locator('[name=interval_months]').fill('1');f.locator('[name=occurrences]').fill('3');f.get_by_role('button',name='Salvar',exact=True).click();expect(page.locator('table').get_by_text('Entrega mensal')).to_be_visible();page.locator('[data-action=erp-view]').click();page.locator('[data-operation=generate_occurrences]').click();page.get_by_role('button',name='Efetivar operação').click();expect(page.locator('#modal')).not_to_be_visible();page.locator('[data-kind=occurrences]').click();expect(page.locator('tbody tr')).to_have_count(3);checks.append('Geração de ocorrências pela interface')
   page.goto('http://127.0.0.1:8099/#/modulehub');page.locator('[data-action=erp-entities]').click();page.locator('#erp-entity-form [name=code]').fill('CAMARA');page.locator('#erp-entity-form [name=name]').fill('Câmara Municipal de Teste');page.locator('#erp-entity-form').get_by_role('button',name='Cadastrar entidade').click();expect(page.locator('#modal').get_by_text('CAMARA · Câmara Municipal de Teste',exact=False)).to_be_visible();page.get_by_role('button',name='Fechar janela',exact=True).click();checks.append('Cadastro de entidade e formulário de vínculos')
   page.goto('http://127.0.0.1:8099/#/annex');expect(page.locator('.erp-requirement')).to_have_count(50);expect(page.locator('.toolbar')).to_contain_text('1.314 itens');first=page.locator('.erp-requirement summary strong').first.inner_text();page.locator('[data-action=ann-next]').click();assert page.locator('.erp-requirement summary strong').first.inner_text()!=first;page.locator('[data-action=ann-prev]').click();expect(page.locator('.erp-requirement summary strong').first).to_have_text(first);page.locator('#erp-annex-search').fill('works.45');expect(page.locator('.erp-requirement:visible')).to_have_count(1);page.locator('.erp-requirement:visible summary').click();expect(page.locator('.erp-requirement:visible .erp-clause')).to_be_visible();checks.append('Matriz completa pesquisável')
   for theme in ['light','dark']:
    page.goto('http://127.0.0.1:8099/#/modulehub');expect(page.locator('.erp-module-grid')).to_be_visible()
    if page.locator('html').get_attribute('data-theme')!=theme:page.locator('[data-action=theme]').click()
    page.screenshot(path=str(ROOT/'artifacts'/f'erp-{theme}-desktop.png'),full_page=True)
    for width in [390,768,1440]:
     page.set_viewport_size({'width':width,'height':900})
     for module in ['modulehub','finance','social','works','annex']:
      page.goto('http://127.0.0.1:8099/#/'+module);expect(page.locator('#main h1')).to_be_visible();expect(page.locator('#main .loading-panel')).to_have_count(0)
      assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1'),(theme,width,module)
    checks.append('Tema '+theme+' em 390, 768 e 1440 px')
   page.set_viewport_size({'width':390,'height':844});page.goto('http://127.0.0.1:8099/#/works');expect(page.locator('.erp-tabs')).to_be_visible();page.screenshot(path=str(ROOT/'artifacts'/'erp-dark-mobile.png'),full_page=True)
   browser.close()
  assert not errors,errors
  result={'passed':len(checks),'checks':checks,'javascript_errors':errors,'route_load_ms':timings};(ROOT/'artifacts'/'browser-erp-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))
 finally:server.close();thread.join(timeout=3)

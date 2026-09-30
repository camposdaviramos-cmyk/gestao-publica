"""Teste real em Chromium, usando uma instância temporária isolada."""
import json
import sys
import tempfile
import threading
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from app import create_app
from waitress import create_server
from playwright.sync_api import sync_playwright, expect

def main():
 artifacts=ROOT/'artifacts'; artifacts.mkdir(exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='rio-browser-') as temp:
  app=create_app({'DATA_DIR':temp,'DATABASE':str(Path(temp)/'rio.db')})
  server=create_server(app,host='127.0.0.1',port=8097,threads=4)
  worker=threading.Thread(target=server.run,daemon=True);worker.start()
  errors=[]; results=[]
  try:
   with sync_playwright() as p:
    browser=p.chromium.launch(); context=browser.new_context(viewport={'width':1440,'height':1080},color_scheme='light',reduced_motion='reduce');page=context.new_page()
    page.on('pageerror',lambda error: errors.append(str(error)))
    page.goto('http://127.0.0.1:8097',wait_until='networkidle')
    expect(page.get_by_role('heading',name='Configure seu ambiente')).to_be_visible()
    page.screenshot(path=str(artifacts/'setup-light.png'),full_page=True)
    page.locator('input[name=name]').fill('Marina Almeida')
    page.locator('input[name=email]').fill('marina@example.test')
    page.locator('input[name=password]').fill('TesteSeguro2026!!')
    page.locator('input[name=demo]').check()
    page.get_by_role('button',name='Criar ambiente').click()
    expect(page.locator('.stats')).to_be_visible(timeout=15000)
    results.append('Configuração inicial, login e dashboard')
    page.screenshot(path=str(artifacts/'dashboard-light.png'),full_page=True)
    page.get_by_role('button',name='Alternar tema',exact=True).click()
    expect(page.locator('html')).to_have_attribute('data-theme','dark')
    page.screenshot(path=str(artifacts/'dashboard-dark.png'),full_page=True)
    page.reload();expect(page.locator('html')).to_have_attribute('data-theme','dark');expect(page.locator('.stats')).to_be_visible()
    page.get_by_role('button',name='Alternar tema',exact=True).click();results.append('Temas claro/escuro e persistência da preferência')
    routes=['budget','accounting','payroll','transparency','approvals','projects','orders','reports','tickets','training','users','groups','audit','compliance','technical','settings']
    for route in routes:
     page.goto('http://127.0.0.1:8097/#/'+route)
     expect(page.locator('#main h1')).to_be_visible()
     expect(page.get_by_text('Não foi possível abrir a página',exact=True)).to_have_count(0)
     results.append('Página '+route)
    page.goto('http://127.0.0.1:8097/#/projects');page.get_by_role('button',name='Novo registro',exact=True).click()
    page.locator('#record-form input[name=title]').fill('Homologação criada pelo navegador')
    page.locator('#record-form input[name=owner]').fill('Equipe de validação')
    page.locator('#record-form input[name=due_date]').fill('2026-12-20')
    page.get_by_role('button',name='Salvar registro',exact=True).click()
    expect(page.locator('dialog')).not_to_be_visible();expect(page.locator('table').get_by_text('Homologação criada pelo navegador',exact=True)).to_be_visible()
    page.get_by_role('button',name='Editar Homologação criada pelo navegador',exact=True).click()
    page.locator('#record-form select[name=status]').select_option('Em andamento')
    page.get_by_role('button',name='Salvar registro',exact=True).click();expect(page.locator('dialog')).not_to_be_visible()
    results.append('Inclusão e edição de registros pela interface')
    page.goto('http://127.0.0.1:8097/#/budget');page.get_by_role('button',name='Nova ação',exact=True).click()
    page.locator('#record-form input[name=title]').fill('Ação pendente criada no navegador')
    page.locator('#record-form input[name=amount]').fill('1500.75')
    page.get_by_role('button',name='Enviar para aprovação',exact=True).click();expect(page.locator('dialog')).not_to_be_visible()
    page.goto('http://127.0.0.1:8097/#/approvals');expect(page.locator('table').get_by_text('Ação pendente criada no navegador')).to_be_visible()
    page.get_by_role('button',name='Revisar',exact=True).first.click();expect(page.get_by_text('Aguardando outra pessoa',exact=False)).to_be_visible();page.get_by_role('button',name='Fechar janela').click()
    results.append('Dupla custódia e impedimento de autoaprovação na interface')
    page.goto('http://127.0.0.1:8097/#/reports');page.locator('#report-form select[name=module]').select_option('projects');page.get_by_role('button',name='Consultar relatório').click()
    expect(page.locator('#report-preview table')).to_be_visible()
    with page.expect_download() as info: page.get_by_role('button',name='PDF',exact=True).click()
    download=info.value;download.save_as(str(artifacts/'report-browser.pdf'));assert (artifacts/'report-browser.pdf').read_bytes().startswith(b'%PDF')
    results.append('Consulta e download real de PDF')
    page.goto('http://127.0.0.1:8097/#/training');page.get_by_role('button',name='Começar tutorial',exact=True).first.click();page.get_by_role('button',name='Marcar como concluído').click();expect(page.get_by_text('1 de 8 tutoriais concluídos')).to_be_visible();results.append('Capacitação com progresso persistido')
    page.goto('http://127.0.0.1:8097/#/dashboard');expect(page.locator('.stats')).to_be_visible();page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(artifacts/'dashboard-mobile.png'),full_page=True)
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'Rolagem horizontal indevida no celular'
    page.get_by_role('button',name='Abrir menu',exact=True).click();expect(page.locator('.sidebar')).to_have_class('sidebar open');page.locator('.sidebar').get_by_role('link',name='Central de atendimento').click();expect(page.locator('#main h1')).to_have_text('Central de atendimento');results.append('Layout móvel e navegação por menu')
    page.goto('http://127.0.0.1:8097/portal');expect(page.get_by_role('heading',name='Informação que aproxima.')).to_be_visible();expect(page.get_by_text('Cronograma de implantação — demonstração',exact=True)).to_be_visible();results.append('Portal público')
    page.locator('#public-search').fill('termo inexistente');expect(page.locator('#public-empty')).to_be_visible();results.append('Filtro de publicações')
    browser.close()
   assert not errors,errors
   report={'passed':len(results),'checks':results,'javascript_errors':errors}
   (artifacts/'browser-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
   print(json.dumps(report,ensure_ascii=False,indent=2))
  finally: server.close();worker.join(timeout=3)

if __name__=='__main__':main()

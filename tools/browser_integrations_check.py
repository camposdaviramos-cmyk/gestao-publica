"""Exercita interface real em banco temporário; rede externa substituída somente neste teste."""
import json,sys,tempfile,threading
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
from app import create_app
from waitress import create_server
from playwright.sync_api import sync_playwright,expect
from test_integrations import job_request
from test_erp import ERP
import integrations
import integration_siconfi
from test_siconfi_agenda import rows,occurrence

with tempfile.TemporaryDirectory(prefix='rio-integrations-browser-') as directory:
 app=create_app({'DATA_DIR':directory,'DATABASE':str(Path(directory)/'rio.db')})
 c=app.test_client();password='TesteSeguro2026!!';c.post('/api/setup',json={'name':'Administradora de Testes','email':'admin@example.test','password':password})
 h={'X-CSRF-Token':c.post('/api/login',json={'email':'admin@example.test','password':password}).json['csrf']}
 _,_,data=job_request(ERP((c,h)))
 oc=occurrence(ERP((c,h)));integration_siconfi.consult=lambda *args:rows()
 integrations.consult=lambda *args:{'id':3304524,'nome':'Rio das Ostras','teste_local':True}
 server=create_server(app,host='127.0.0.1',port=8098,threads=8);thread=threading.Thread(target=server.run,daemon=True);thread.start();errors=[];checks=[]
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch();page=browser.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce');page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto('http://127.0.0.1:8098');page.locator('[name=email]').fill('admin@example.test');page.locator('[name=password]').fill(password);page.get_by_role('button',name='Entrar no sistema').click();expect(page.locator('.stats')).to_be_visible()
   page.goto('http://127.0.0.1:8098/#/integrations');expect(page.locator('.int-card')).to_have_count(17);checks.append('Central com 17 serviços e plataformas')
   page.locator('[data-provider=pncp] [data-action=int-config]').click();f=page.locator('#int-config');f.locator('[name=cnpj]').fill('11222333000181');f.locator('[name=login]').fill('plataforma-teste');f.locator('[name=senha]').fill('SegredoExternoParaTeste');f.locator('[name=enabled]').check();f.get_by_role('button',name='Salvar',exact=True).click();expect(page.locator('#modal')).not_to_be_visible()
   page.locator('[data-provider=pncp] [data-action=int-config]').click();expect(page.locator('[name=senha]')).to_have_value('');expect(page.locator('#int-config')).not_to_contain_text('SegredoExternoParaTeste');page.get_by_role('button',name='Fechar janela').click();checks.append('Cadastro de credenciais e senha nunca retornada')
   page.locator('[data-action=int-jobs]').click();page.locator('[data-action=int-new-job]').click();page.locator('#int-source [type=submit]').click();page.locator('[data-action=int-prepare]').click();expect(page.locator('#int-prepare')).to_be_visible()
   f=page.locator('#int-prepare')
   for key in ['codigoUnidadeCompradora','tipoInstrumentoConvocatorioId','modalidadeId','modoDisputaId','amparoLegalId','dataAberturaProposta','dataEncerramentoProposta']:f.locator('[name='+key+']').fill(str(data['payload'][key])[:16] if key.startswith('data') else str(data['payload'][key]))
   f.locator('.int-item summary').click();f.locator('[name=item0_materialOuServico]').select_option('M');f.locator('[name=item0_tipoBeneficioId]').fill('4');f.locator('[name=item0_criterioJulgamentoId]').fill('1')
   f.locator('[name=document_title]').fill('Edital teste');f.locator('[name=document_type]').fill('1')
   import base64
   f.locator('[name=document]').set_input_files({'name':'edital.pdf','mimeType':'application/pdf','buffer':base64.b64decode(data['document'])});f.get_by_role('button',name='Preparar para revisão').click();expect(page.locator('#modal-title')).to_have_text('Pacote PNCP #1');checks.append('Formulário PNCP gera pacote e PDF sem transmissão')
   page.locator('[data-action=int-approve]').click();expect(page.locator('#toasts')).to_contain_text('Outro administrador');page.get_by_role('button',name='Fechar janela').click();checks.append('Autorrevisão bloqueada também pela interface')
   page.locator('#int-environment').select_option('producao');expect(page.locator('[data-provider=ibge] [data-action=int-config]')).to_be_visible();page.locator('[data-provider=ibge] [data-action=int-config]').click();f=page.locator('#int-config');f.locator('[name=municipio]').fill('3304524');f.locator('[name=enabled]').check();f.get_by_role('button',name='Salvar',exact=True).click();expect(page.locator('#modal')).not_to_be_visible();page.locator('[data-provider=ibge] [data-action=int-consult]').click();expect(page.locator('.int-json')).to_contain_text('Rio das Ostras');page.get_by_role('button',name='Fechar janela').click();checks.append('Consulta IBGE e resultado em janela')
   page.locator('[data-provider=ibge] [data-action=int-history]').click();expect(page.locator('.int-history')).to_contain_text('Concluída');page.get_by_role('button',name='Fechar janela').click();checks.append('Histórico de consulta com ator e resultado')
   page.locator('[data-provider=siconfi] [data-action=int-config]').click();f=page.locator('#int-config');f.locator('[name=municipio]').fill('3304524');f.locator('[name=exercicio]').fill('2026');f.locator('[name=enabled]').check();f.get_by_role('button',name='Salvar',exact=True).click();expect(page.locator('#modal')).not_to_be_visible()
   page.locator('[data-action=sic-reports]').click();page.locator('[data-action=sic-sync]').click();expect(page.locator('.int-history article')).to_have_count(2);page.locator('[data-action=sic-link]').first.click();page.locator('#sic-search [type=submit]').click();page.locator('[data-action=sic-confirm]').click();expect(page.locator('.int-history')).to_contain_text('Vinculado à ocorrência');page.get_by_role('button',name='Fechar janela').click();checks.append('Sincronização Siconfi e vínculo com a agenda pela interface')
   page.goto('http://127.0.0.1:8098/#/control');page.locator('[data-kind=occurrences]').click();page.locator('[data-action=erp-view]').click();expect(page.locator('#modal')).to_contain_text('Extrato oficial do Siconfi');page.get_by_role('button',name='Fechar janela').click();page.goto('http://127.0.0.1:8098/#/integrations');expect(page.locator('.int-card')).to_have_count(17);checks.append('Status externo visível na ocorrência vinculada')
   for theme in ['light','dark']:
    if page.locator('html').get_attribute('data-theme')!=theme:page.locator('[data-action=theme]').click()
    for width in [390,768,1440]:
     page.set_viewport_size({'width':width,'height':950});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(theme,width)
     page.locator('[data-provider=esocial] [data-action=int-config]').click();expect(page.locator('#int-config [name=pfx]')).to_be_visible();assert page.locator('#int-config [name=enabled]').count()==1;page.get_by_role('button',name='Fechar janela').click()
    page.evaluate("scrollTo(0,0);document.activeElement?.blur();document.querySelector('#toasts').innerHTML=''")
    page.screenshot(path=str(ROOT/'artifacts'/f'integrations-{theme}.png'),full_page=True)
    checks.append('Tema '+theme+' responsivo em 390, 768 e 1440 px; cofre A1 disponível')
   page.goto('http://127.0.0.1:8098/#/settings');expect(page.get_by_role('link',name='Abrir central')).to_be_visible();checks.append('Acesso à central nas configurações')
   browser.close()
  assert not errors,errors
  result={'passed':len(checks),'checks':checks,'javascript_errors':errors,'external_network':'Substituída por resposta fictícia neste teste; nenhuma publicação enviada.'};(ROOT/'artifacts'/'browser-integrations-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=True))
 finally:server.close();thread.join(timeout=3)

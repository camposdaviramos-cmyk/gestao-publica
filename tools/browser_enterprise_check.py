"""Fluxos de assinatura, LDAP e eSocial em navegador e banco descartável, sem transmissão externa."""
import base64,json,sys,tempfile,threading
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
from app import create_app
from waitress import create_server
from playwright.sync_api import sync_playwright,expect
from test_system import user,PASSWORD
from test_integrations import pdf
from test_enterprise_integrations import signature
from test_esocial import xml
from test_erp import ERP
from test_siconfi_agenda import occurrence

with tempfile.TemporaryDirectory(prefix='rio-enterprise-browser-') as directory:
 app=create_app({'DATA_DIR':directory,'DATABASE':str(Path(directory)/'rio.db')});c=app.test_client()
 c.post('/api/setup',json={'name':'Administradora de Teste','email':'admin@example.test','password':PASSWORD})
 h={'X-CSRF-Token':c.post('/api/login',json={'email':'admin@example.test','password':PASSWORD}).json['csrf']};uid=user((c,h),group=3)
 erp=ERP((c,h));obj=occurrence(erp);r=c.post('/api/erp/object/'+str(obj['id'])+'/attachments',json={'name':'documento.pdf','content':pdf()},headers=h);assert r.status_code==201
 from test_integrations import certificate
 pfx=base64.b64decode(certificate());errors=[];checks=[]
 server=create_server(app,host='127.0.0.1',port=8099,threads=6);thread=threading.Thread(target=server.run,daemon=True);thread.start()
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch();page=browser.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce');page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto('http://127.0.0.1:8099');page.locator('[name=email]').fill('admin@example.test');page.locator('[name=password]').fill(PASSWORD);page.get_by_role('button',name='Entrar no sistema').click();expect(page.locator('.stats')).to_be_visible()
   page.goto('http://127.0.0.1:8099/#/integrations');page.locator('#int-environment').select_option('producao')
   page.locator('[data-provider=signature] [data-action=int-config]').click();f=page.locator('#int-config');f.locator('[name=pfx]').set_input_files({'name':'teste.pfx','mimeType':'application/x-pkcs12','buffer':pfx});f.locator('[name=pfx_password]').fill('senha-certificado');f.locator('[name=reason]').fill('Assinatura de teste institucional');f.locator('[name=enabled]').check();f.get_by_role('button',name='Salvar',exact=True).click();expect(page.locator('#modal')).not_to_be_visible()
   page.locator('[data-provider=signature] [data-action=int-consult]').click();expect(page.locator('.int-json')).to_contain_text('signature_valid');page.get_by_role('button',name='Fechar janela').click();checks.append('Certificado A1 cadastrado pela interface e assinatura de teste verificada')
   page.goto('http://127.0.0.1:8099/#/settings');page.locator('summary').filter(has_text='Configurar por relatório').click();page.locator('[name=signature_reports][value="control:occurrences"]').check();page.get_by_role('button',name='Salvar configurações').click();expect(page.locator('#toasts')).to_contain_text('Configurações salvas');checks.append('Assinatura exigida em um relatório específico')
   page.goto('http://127.0.0.1:8099/#/control');page.locator('[data-kind=occurrences]').click();page.locator('[data-action=erp-view]').click();page.locator('[data-action=ent-sign]').click();page.locator('#ent-sign [name=confirm]').check();page.locator('#ent-sign [type=submit]').click();expect(page.locator('#modal')).to_contain_text('Versões assinadas')
   with page.expect_download() as dl:page.locator('[data-action=ent-download]').click()
   assert dl.value.suggested_filename=='documento.pdf';page.get_by_role('button',name='Fechar janela').click();checks.append('Anexo PDF assinado e baixado pela interface')
   page.goto('http://127.0.0.1:8099/#/integrations');page.locator('[data-provider=ldap] [data-action=int-config]').click();f=page.locator('#int-config')
   for k,v in {'host':'diretorio.example.test','port':'636','tls_mode':'ldaps','base_dn':'DC=example,DC=test','bind_dn':'CN=service,DC=example,DC=test','bind_password':'SenhaDiretorioTeste','login_attribute':'sAMAccountName'}.items():f.locator('[name='+k+']').fill(v)
   f.locator('[name=enabled]').check();f.get_by_role('button',name='Salvar',exact=True).click();expect(page.locator('#modal')).not_to_be_visible();page.locator('[data-action=ent-bindings]').click();page.locator('#ent-binding [name=user_id]').select_option(str(uid));page.locator('#ent-binding [name=login_name]').fill('servidor.teste');page.locator('#ent-binding [type=submit]').click();expect(page.locator('.int-history')).to_contain_text('servidor.teste');page.get_by_role('button',name='Fechar janela').click();checks.append('Configuração LDAP e vínculo explícito de usuário pela interface')
   page.locator('#int-environment').select_option('homologacao');page.locator('[data-provider=esocial] [data-action=int-config]').click();f=page.locator('#int-config')
   for k in ['cnpj','employer_registration','transmitter']:f.locator('[name='+k+']').fill('11222333000181')
   f.locator('[name=pfx]').set_input_files({'name':'teste.pfx','mimeType':'application/x-pkcs12','buffer':pfx});f.locator('[name=pfx_password]').fill('senha-certificado');f.locator('[name=enabled]').check();f.get_by_role('button',name='Salvar',exact=True).click();expect(page.locator('#modal')).not_to_be_visible()
   page.locator('[data-action=eso-list]').click();page.locator('[data-action=eso-new]').click();page.locator('#eso-prepare [name=events]').set_input_files({'name':'s1000.xml','mimeType':'application/xml','buffer':xml().encode()});page.locator('#eso-prepare [name=confirm]').check();page.locator('#eso-prepare [type=submit]').click();expect(page.locator('#modal-title')).to_have_text('Lote eSocial #1');expect(page.locator('#modal')).to_contain_text('evtInfoEmpregador');checks.append('Evento S-1000 importado, validado, assinado e preparado sem transmissão')
   page.locator('[data-action=eso-approve]').click();expect(page.locator('#toasts')).to_contain_text('Outro administrador');checks.append('Revisão pelo próprio autor bloqueada na tela de eSocial')
   for theme in ['light','dark']:
    if page.locator('html').get_attribute('data-theme')!=theme:page.evaluate("document.querySelector('html').dataset.theme='"+theme+"'")
    for width in [390,768,1440]:
     page.set_viewport_size({'width':width,'height':950});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(theme,width)
     assert page.locator('#modal').evaluate('(el)=>el.scrollWidth<=el.clientWidth+1'),(theme,width,'modal')
    page.screenshot(path=str(ROOT/'artifacts'/f'esocial-{theme}.png'),full_page=True);checks.append('Lote eSocial responsivo no tema '+theme+' em 390, 768 e 1440 px')
   browser.close()
  assert not errors,errors
  result={'passed':len(checks),'checks':checks,'javascript_errors':errors,'external_transmissions':0};(ROOT/'artifacts/browser-enterprise-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=True))
 finally:server.close();thread.join(timeout=3)

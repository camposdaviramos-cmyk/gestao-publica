import json
import sys
import tempfile
import threading
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app import create_app
from waitress import create_server
from playwright.sync_api import sync_playwright,expect

with tempfile.TemporaryDirectory(prefix='rio-admin-browser-') as directory:
 app=create_app({'DATA_DIR':directory,'DATABASE':str(Path(directory)/'rio.db')})
 client=app.test_client();password='TesteSeguro2026!!'
 client.post('/api/setup',json={'name':'Primeiro Administrador','email':'admin@example.test','password':password})
 login=client.post('/api/login',json={'email':'admin@example.test','password':password});headers={'X-CSRF-Token':login.json['csrf']}
 client.post('/api/records/budget',json={'title':'Ação para segunda aprovação','status':'Planejado','amount':'5000.25','data':{}},headers=headers)
 server=create_server(app,host='127.0.0.1',port=8098,threads=4);worker=threading.Thread(target=server.run,daemon=True);worker.start();checks=[];errors=[]
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch();context=browser.new_context(viewport={'width':1440,'height':1080},reduced_motion='reduce');page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
   def enter(email):
    page.locator('#auth-form input[name=email]').fill(email);page.locator('#auth-form input[name=password]').fill(password);page.get_by_role('button',name='Entrar no sistema').click();expect(page.locator('.stats')).to_be_visible()
   page.goto('http://127.0.0.1:8098');enter('admin@example.test')
   page.goto('http://127.0.0.1:8098/#/users');page.get_by_role('button',name='Novo usuário',exact=True).click()
   form=page.locator('#user-form');form.locator('input[name=name]').fill('Segundo Administrador');form.locator('input[name=email]').fill('second@example.test');form.locator('input[name=password]').fill(password);form.locator('select[name=group_id]').select_option('1');form.locator('input[name=force_password]').uncheck();form.get_by_role('button',name='Salvar usuário',exact=True).click();expect(page.locator('table').get_by_text('Segundo Administrador')).to_be_visible();checks.append('Criação de usuário pela interface')
   page.locator('[data-action=profile]').click();page.get_by_role('button',name='Sair da conta').click();enter('second@example.test')
   page.goto('http://127.0.0.1:8098/#/approvals');page.get_by_role('button',name='Revisar',exact=True).click();page.locator('#approval-form textarea[name=reason]').fill('Conferência realizada pelo segundo responsável.');page.get_by_role('button',name='Registrar decisão').click();expect(page.locator('table').get_by_text('Aprovado',exact=True)).to_be_visible();checks.append('Aprovação efetiva por segundo usuário')
   page.goto('http://127.0.0.1:8098/#/budget');expect(page.locator('table').get_by_text('Ação para segunda aprovação',exact=True)).to_be_visible();checks.append('Registro aprovado visível no módulo')
   page.goto('http://127.0.0.1:8098/#/groups');page.get_by_role('button',name='Novo grupo',exact=True).click();page.locator('#group-form input[name=name]').fill('Equipe de consulta');page.locator('#group-form input[data-permission=budget][value=read]').check();page.get_by_role('button',name='Salvar grupo').click();expect(page.get_by_role('heading',name='Equipe de consulta',exact=True)).to_be_visible();checks.append('Cadastro de grupo com permissão de consulta')
   page.goto('http://127.0.0.1:8098/#/settings');page.locator('input[name=support_phone]').fill('(22) 0000-0000');page.get_by_role('button',name='Salvar configurações').click();expect(page.locator('input[name=support_phone]')).to_have_value('(22) 0000-0000');checks.append('Persistência dos parâmetros institucionais')
   page.goto('http://127.0.0.1:8098/#/tickets');page.get_by_role('button',name='Abrir chamado',exact=True).click();page.locator('#record-form input[name=title]').fill('Ocorrência validada no navegador');page.locator('#record-form textarea[name=description]').fill('Verificação completa do fluxo de atendimento integrado.');page.get_by_role('button',name='Salvar registro',exact=True).click();expect(page.locator('table').get_by_text('Ocorrência validada no navegador')).to_be_visible()
   page.get_by_role('button',name='Ver Ocorrência validada no navegador',exact=True).click();page.locator('#comment-form textarea[name=body]').fill('Ocorrência recebida pela equipe de atendimento.');page.get_by_role('button',name='Enviar mensagem',exact=True).click();expect(page.locator('#ticket-comments').get_by_text('Ocorrência recebida pela equipe de atendimento.')).to_be_visible();page.get_by_role('button',name='Fechar janela').click()
   page.get_by_role('button',name='Editar Ocorrência validada no navegador',exact=True).click();page.locator('#record-form select[name=status]').select_option('Resolvido');page.locator('#record-form textarea[name=resolution]').fill('Fluxo verificado e ocorrência solucionada com sucesso.');page.get_by_role('button',name='Salvar registro',exact=True).click();expect(page.locator('table').get_by_text('Resolvido',exact=True)).to_be_visible();checks.append('Chamado com comentário e solução definitiva')
   page.goto('http://127.0.0.1:8098/#/dashboard');page.get_by_role('button',name='Meus atalhos',exact=True).click();page.locator('#shortcut-form input[name=title]').fill('Ferramenta institucional');page.locator('#shortcut-form input[name=url]').fill('https://example.org');page.get_by_role('button',name='Adicionar atalho').click();expect(page.get_by_role('link',name='Ferramenta institucional')).to_be_visible();page.get_by_role('button',name='Fechar janela').click();checks.append('Atalho HTTPS personalizado')
   page.goto('http://127.0.0.1:8098/#/technical');page.get_by_role('button',name='Gerar backup').click();expect(page.get_by_role('button',name='Baixar backup')).to_be_visible();checks.append('Geração de backup pela interface')
   browser.close()
  assert not errors,errors
  result={'passed':len(checks),'checks':checks,'javascript_errors':errors};(ROOT/'artifacts'/'browser-admin-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))
 finally:server.close();worker.join(timeout=3)
